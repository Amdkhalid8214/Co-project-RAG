"""
LangChain Adapter for DocuChat AI.

Architectural Separation:
=========================
1. Custom RAG Pipeline (Remains Custom & Fully Under Control):
   - Ingestion & Docling parsing (with PyMuPDF fallback)
   - Structure-aware chunking with token estimation and bbox tracking
   - Nomic / BGE embeddings via FastEmbed & SentenceTransformers
   - Qdrant vector database storage and ANN search
   - BM25Plus lexical indexing and BM25 search
   - Hybrid retrieval with Reciprocal Rank Fusion (RRF) / weighted fusion
   - Jaccard & token-ngram deduplication
   - Cross-encoder reranking (BAAI/bge-reranker-base)
   - Score thresholding and top-k selection
   - Citation refinement and bounding-box matching for PDF.js highlighting
   - FastAPI server with SSE streaming endpoints

2. LangChain Orchestration Layer (Focused, Well-Isolated Integration):
   - Document metadata preservation via langchain_core.documents.Document
   - Grounded prompt templates via langchain_core.prompts.ChatPromptTemplate
   - Message abstraction via SystemMessage and HumanMessage
   - LLM Orchestration via langchain_ollama.ChatOllama with qwen2.5:7b (configurable via settings.LLM_MODEL)
   - Asynchronous token streaming integration with SSE pipeline
   - Robust error handling and diagnostics for Ollama/Qwen availability
"""

import json
import logging
import re
from datetime import datetime
from typing import List, Dict, Any, AsyncGenerator, Optional, Tuple

from langchain_core.documents import Document
from langchain_core.messages import SystemMessage, HumanMessage, BaseMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama

from backend.config import settings

logger = logging.getLogger(__name__)


def clean_pdf_text(text: str) -> str:
    """
    Cleans PDF column line breaks, hyphenated split words, and whitespace artifacts
    while strictly preserving true paragraphs, headers, and bulleted lists.
    """
    if not text:
        return ""

    # 1. Fix hyphenated word breaks at line ends: e.g. "transfor-\n mation" -> "transformation"
    text = re.sub(r'(\b[a-zA-Z]+)-\s*\n\s*([a-zA-Z]+\b)', r'\1\2', text)

    # 2. Normalize horizontal spaces/tabs
    text = re.sub(r'[ \t]+', ' ', text)

    # 3. Handle line breaks:
    # Preserve double newlines (paragraphs, headers, equations)
    # Join single newlines if they are inside a normal sentence
    lines = text.split('\n')
    cleaned_lines: List[str] = []

    for line in lines:
        line_s = line.strip()
        if not line_s:
            cleaned_lines.append("")
            continue

        # Bullet point or list item
        is_bullet = bool(re.match(r'^([•\-\*]|\d+\.|\d+\.\d+)', line_s))
        # Standalone numeric section or title
        is_heading = bool(re.match(r'^\d+(\.\d+)*\s*$', line_s)) or bool(
            re.match(r'^[A-Z][a-zA-Z0-9\s]{2,40}$', line_s) and len(line_s) < 45
        )

        if cleaned_lines and cleaned_lines[-1] != "" and not is_bullet and not is_heading:
            prev = cleaned_lines[-1]
            # If previous line did not end with a sentence-ending punctuation or if current line continues lowercased
            if not prev.endswith(('.', ':', '?', '!')) or (len(line_s) > 0 and line_s[0].islower()):
                cleaned_lines[-1] = prev + " " + line_s
                continue

        cleaned_lines.append(line_s)

    # Reconstruct text with clean paragraph breaks
    result: List[str] = []
    for l in cleaned_lines:
        if l == "":
            if result and result[-1] != "":
                result.append("")
        else:
            result.append(l)

    return "\n\n".join([r for r in "\n".join(result).split("\n\n") if r.strip()])


# Grounded prompt templates enforcing strict verbatim factual extraction and zero hallucinations
GROUNDED_SYSTEM_TEMPLATE = (
    "Today's real-world current date is {current_date}.\n\n"
    "You are a strict, verbatim document extraction system.\n\n"
    "CRITICAL GROUNDING RULES:\n"
    "1. Answer ONLY by extracting the exact sentences directly present in the Document Context.\n"
    "2. DO NOT paraphrase. DO NOT summarize. DO NOT write conversational commentary, introductory filler, or textbook explanations.\n"
    "3. Every single sentence you output must be a direct excerpt from the text. Not a single word absent from the document is allowed in your answer.\n"
    "4. If the requested information or term is absent or not explicitly discussed in the Document Context, reply EXACTLY:\n"
    "   'This is not mentioned in the document.'\n"
    "   Do NOT speculate or use pre-trained external knowledge.\n"
    "5. Cite the source numbers [1], [2] where the text appears.\n"
    "6. FORMATTING: Present your answer in smooth, continuous, well-formed sentences and paragraphs. Do NOT insert awkward mid-sentence line breaks or split words across lines (e.g. write 'transformation' instead of 'transfor- mation')."
)

GROUNDED_HUMAN_TEMPLATE = (
    "Document Context:\n\n"
    "{context}\n\n"
    "---\n\n"
    "Question: {question}\n\n"
    "Verbatim Document Answer (extract only exact text present in the document, cite [1], [2]):"
)

# General chat prompt templates for out-of-document or conversational queries
GENERAL_SYSTEM_TEMPLATE = (
    "Today's real-world current date is {current_date} (current time: {current_time}).\n\n"
    "You are an intelligent, versatile, and up-to-date AI assistant like ChatGPT.\n"
    "When asked about today's date, day, month, year, or current time, ALWAYS answer with today's date and time provided above.\n"
    "You provide accurate, well-structured, and helpful answers on all topics including:\n"
    "- Movies, entertainment, and pop culture\n"
    "- Stock market prices, financial analysis, and companies\n"
    "- Sports scores, teams, tournaments, and athletes\n"
    "- Politics, government, and world events\n"
    "- Technology, coding, science, and history\n"
    "When live web or market data is provided, use it to give exact, real-time answers."
)

GENERAL_HUMAN_TEMPLATE_WITH_WEB = (
    "Live Real-Time Web Context:\n"
    "{live_context}\n\n"
    "User Question:\n"
    "{question}\n\n"
    "Helpful & Detailed Answer:"
)

GENERAL_HUMAN_TEMPLATE_PLAIN = (
    "User Question:\n"
    "{question}\n\n"
    "Helpful & Detailed Answer:"
)


class LangChainAdapter:
    """
    Isolated LangChain orchestration component for DocuChat AI.
    Handles message structure, prompt templating, and Ollama/Qwen interaction.
    """

    def __init__(
        self,
        base_url: str = settings.LLM_BASE_URL,
        model: str = settings.LLM_MODEL,
        temperature: float = settings.LLM_TEMPERATURE,
        max_tokens: int = settings.LLM_MAX_TOKENS,
    ):
        self.base_url = base_url.rstrip("/")
        self.model_name = model
        self.temperature = temperature
        self.max_tokens = max_tokens

        # Precompile ChatPromptTemplates
        self.grounded_prompt_template = ChatPromptTemplate.from_messages([
            ("system", GROUNDED_SYSTEM_TEMPLATE),
            ("human", GROUNDED_HUMAN_TEMPLATE),
        ])

        self.general_prompt_template_web = ChatPromptTemplate.from_messages([
            ("system", GENERAL_SYSTEM_TEMPLATE),
            ("human", GENERAL_HUMAN_TEMPLATE_WITH_WEB),
        ])

        self.general_prompt_template_plain = ChatPromptTemplate.from_messages([
            ("system", GENERAL_SYSTEM_TEMPLATE),
            ("human", GENERAL_HUMAN_TEMPLATE_PLAIN),
        ])

        logger.info(
            f"[LANGCHAIN] Adapter initialized for model='{self.model_name}' at '{self.base_url}'"
        )

    def get_llm(
        self,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        timeout: Optional[float] = None,
    ) -> ChatOllama:
        """
        Creates or returns a ChatOllama instance configured for the specified generation parameters.
        """
        temp = self.temperature if temperature is None else temperature
        num_predict = self.max_tokens if max_tokens is None else max_tokens
        client_timeout = getattr(settings, "LLM_TIMEOUT", 180.0) if timeout is None else timeout
        num_threads = getattr(settings, "LLM_NUM_THREADS", 8)
        num_ctx = getattr(settings, "LLM_NUM_CTX", 8192)

        return ChatOllama(
            base_url=self.base_url,
            model=self.model_name,
            temperature=temp,
            num_predict=num_predict,
            timeout=client_timeout,
            num_thread=num_threads,
            num_ctx=num_ctx,
        )

    def chunks_to_documents(self, chunks: List[Dict[str, Any]]) -> List[Document]:
        """
        Converts custom RAG chunk dictionaries into LangChain Document objects
        while strictly preserving all structural provenance and citation metadata.
        """
        documents: List[Document] = []
        for idx, chunk in enumerate(chunks):
            source_num = idx + 1
            page = chunk.get("page", 1)
            text = chunk.get("text", "").strip()
            doc_id = chunk.get("doc_id", "")
            doc_name = (
                chunk.get("doc_name")
                or chunk.get("document_name")
                or chunk.get("metadata", {}).get("doc_name", "")
            )
            chunk_id = chunk.get("chunk_id", "")
            heading_path = chunk.get("heading_path", [])
            section_str = " > ".join(heading_path) if heading_path else f"Page {page}"
            bboxes = chunk.get("bboxes", [])
            retrieval_score = float(chunk.get("score", 0.0))
            reranker_score = float(chunk.get("reranker_score", retrieval_score))

            metadata = {
                "document_id": doc_id,
                "document_name": doc_name,
                "chunk_id": chunk_id,
                "page_number": page,
                "section": section_str,
                "heading_path": heading_path,
                "bbox": bboxes,
                "text": text,
                "source": f"[{source_num}]",
                "retrieval_score": retrieval_score,
                "reranker_score": reranker_score,
                "source_index": source_num,
            }

            doc = Document(page_content=text, metadata=metadata)
            documents.append(doc)

        logger.info(f"[LANGCHAIN] Converted {len(documents)} chunks to LangChain Document objects")
        return documents

    def build_grounded_messages(
        self,
        question: str,
        documents: List[Document],
    ) -> Tuple[List[BaseMessage], List[Dict[str, Any]]]:
        """
        Builds structured LangChain messages (SystemMessage + HumanMessage)
        and extracts the citations payload required by PDF.js highlighting.
        """
        now = datetime.now()
        current_date_str = now.strftime("%A, %B %d, %Y")

        context_blocks: List[str] = []
        citations_payload: List[Dict[str, Any]] = []

        for doc in documents:
            source_idx = doc.metadata.get("source_index", 1)
            page = doc.metadata.get("page_number", 1)
            section = doc.metadata.get("section", "")
            content = doc.page_content[:3500]

            header = f"[{source_idx}] (Page {page})"
            if section:
                header += f" - Section: {section}"
            context_blocks.append(f"{header}:\n{content}")

            citations_payload.append({
                "source_index": source_idx,
                "chunk_id": doc.metadata.get("chunk_id", ""),
                "doc_id": doc.metadata.get("document_id", ""),
                "page": page,
                "bboxes": doc.metadata.get("bbox", []),
                "heading_path": doc.metadata.get("heading_path", []),
                "snippet": doc.page_content[:250],
            })

        formatted_context = "\n\n".join(context_blocks)

        messages = self.grounded_prompt_template.format_messages(
            current_date=current_date_str,
            context=formatted_context,
            question=question,
        )

        logger.info("[LANGCHAIN] Grounded prompt constructed with SystemMessage and HumanMessage")
        return messages, citations_payload

    def build_general_messages(
        self,
        question: str,
        live_context: str = "",
    ) -> List[BaseMessage]:
        """
        Builds LangChain messages for general real-world / conversational queries.
        """
        now = datetime.now()
        current_date_str = now.strftime("%A, %B %d, %Y")
        current_time_str = now.strftime("%I:%M %p")

        if live_context:
            messages = self.general_prompt_template_web.format_messages(
                current_date=current_date_str,
                current_time=current_time_str,
                live_context=live_context,
                question=question,
            )
        else:
            messages = self.general_prompt_template_plain.format_messages(
                current_date=current_date_str,
                current_time=current_time_str,
                question=question,
            )

        logger.info("[LANGCHAIN] General prompt constructed with SystemMessage and HumanMessage")
        return messages

    async def stream_messages(
        self,
        messages: List[BaseMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Asynchronously streams generation tokens from ChatOllama for SSE events.
        Catches Ollama connection or model availability issues and yields diagnostics.
        """
        logger.info(f"[LLM] Model: {self.model_name}")
        logger.info("[LLM] Generation started")
        logger.info("[LLM] Streaming response")

        try:
            llm = self.get_llm(temperature=temperature, max_tokens=max_tokens)
            async for chunk in llm.astream(messages):
                token = chunk.content
                if isinstance(token, str) and token:
                    yield token
                elif isinstance(token, list):
                    for item in token:
                        if isinstance(item, str):
                            yield item
                        elif isinstance(item, dict) and "text" in item:
                            yield item["text"]
        except Exception as e:
            err_str = str(e)
            logger.error(f"[LLM] Error during LangChain generation: {e}")
            if "not found" in err_str.lower():
                yield (
                    f"\n[Ollama error: Model '{self.model_name}' not found at {self.base_url}. "
                    f"Please run 'ollama pull {self.model_name}' to download it.]"
                )
            elif "memory" in err_str.lower() or "cuda" in err_str.lower():
                yield (
                    f"\n[Ollama resource error: Insufficient system memory/VRAM to load '{self.model_name}'. "
                    f"Please close background applications, free VRAM, or allocate additional swap/RAM for 7B inference.]"
                )
            elif "timeout" in err_str.lower() or "timed out" in err_str.lower():
                yield (
                    f"\n[Ollama timeout error: Request to '{self.model_name}' timed out. "
                    f"Inference on CPU with a 7B model can take longer; consider GPU offloading or increasing LLM_TIMEOUT.]"
                )
            elif "connection" in err_str.lower() or "connect" in err_str.lower():
                yield (
                    f"\n[Ollama connection error: Could not reach Ollama at {self.base_url}. "
                    f"Please ensure Ollama is running.]"
                )
            else:
                yield f"\n[Generation error: {err_str}]"

    async def ainvoke_messages(
        self,
        messages: List[BaseMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Non-streaming generation via LangChain ainvoke.
        """
        try:
            llm = self.get_llm(temperature=temperature, max_tokens=max_tokens)
            response = await llm.ainvoke(messages)
            return str(response.content).strip()
        except Exception as e:
            err_str = str(e)
            logger.error(f"[LLM] ainvoke error: {e}")
            if "not found" in err_str.lower():
                return f"[Ollama error: Model '{self.model_name}' not found. Please run 'ollama pull {self.model_name}']"
            elif "memory" in err_str.lower() or "cuda" in err_str.lower():
                return f"[Ollama resource error: Insufficient memory/VRAM to load '{self.model_name}']"
            elif "timeout" in err_str.lower():
                return f"[Ollama timeout error: Request to '{self.model_name}' timed out]"
            return ""

    async def stream_grounded_chat(
        self,
        question: str,
        chunks: List[Dict[str, Any]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> Tuple[AsyncGenerator[str, None], List[Dict[str, Any]]]:
        """
        End-to-end grounded RAG orchestration:
        1. Chunks -> LangChain Documents
        2. Documents -> SystemMessage + HumanMessage Prompt
        3. Messages -> ChatOllama token stream
        Returns: (token_stream_generator, citations_payload)
        """
        documents = self.chunks_to_documents(chunks)
        messages, citations = self.build_grounded_messages(question, documents)

        async def token_generator():
            async for token in self.stream_messages(
                messages,
                temperature=temperature,
                max_tokens=max_tokens,
            ):
                yield token

        return token_generator(), citations

    async def stream_general_chat(
        self,
        question: str,
        live_context: str = "",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Streams response for conversational / real-world queries via LangChain.
        """
        messages = self.build_general_messages(question, live_context=live_context)
        async for token in self.stream_messages(
            messages,
            temperature=temperature,
            max_tokens=max_tokens,
        ):
            yield token


langchain_adapter = LangChainAdapter()
