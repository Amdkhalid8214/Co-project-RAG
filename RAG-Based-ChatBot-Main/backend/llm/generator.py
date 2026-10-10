import json
import logging
import asyncio
from typing import List, Dict, Any, AsyncGenerator, Optional, Tuple
from backend.config import settings
from backend.llm.client import ollama_client
from backend.llm.langchain_adapter import langchain_adapter
from backend.retrieval.web_search import live_web_search

logger = logging.getLogger(__name__)

class GroundedGenerator:
    def __init__(self):
        pass

    def build_grounded_prompt(
        self,
        question: str,
        chunks: List[Dict[str, Any]]
    ) -> Tuple[str, str, List[Dict[str, Any]]]:
        """
        Builds compact numbered context and maps citations for frontend highlighting.
        Returns: (system_prompt, user_prompt, citations_payload)
        """
        from datetime import datetime
        now = datetime.now()
        current_date_str = now.strftime("%A, %B %d, %Y")

        system_prompt = (
            f"Today's real-world current date is {current_date_str}.\n"
            "You are a document-grounded AI assistant. You answer questions strictly based on the provided document sources.\n\n"
            "CRITICAL GROUNDING RULES:\n"
            "1. Answer ONLY using the exact facts and statements directly present in the provided Context Sources.\n"
            "2. Do not use unsupported external knowledge. Do NOT hallucinate or add outside explanations, tutorials, definitions, or formulas not present in the context.\n"
            "3. If the context describes items, sections, or lists (e.g. 'in three different ways'), you MUST extract those exact points directly from the document without fabricating or expanding with external commentary.\n"
            "4. If the requested information is absent or not explicitly discussed in the Context Sources:\n"
            "   - You MUST NOT answer using pre-trained knowledge or guess.\n"
            "   - You MUST clearly state: 'This is not mentioned in the document.'\n"
            "5. Base every factual claim strictly on the retrieved context and cite the sources using [1], [2], etc., corresponding to the provided sources.\n"
            "6. Provide a direct, concise, and factually accurate answer containing ONLY what is actually written in the document."
        )

        context_blocks = []
        citations_payload = []

        for idx, chunk in enumerate(chunks):
            source_num = idx + 1
            page = chunk.get("page", 1)
            text = chunk.get("text", "").strip()
            # Preserve full structured text up to 3500 chars so sections are not sliced in half
            snippet = text[:3500]

            context_blocks.append(f"[{source_num}] (Page {page}):\n{snippet}")
            citations_payload.append({
                "source_index": source_num,
                "chunk_id": chunk.get("chunk_id", ""),
                "doc_id": chunk.get("doc_id", ""),
                "page": page,
                "bboxes": chunk.get("bboxes", []),
                "heading_path": chunk.get("heading_path", []),
                "snippet": text[:250],
            })

        formatted_context = "\n\n".join(context_blocks)
        user_prompt = f"Context Sources:\n{formatted_context}\n\nQuestion: {question}\n\nAnswer:"
        return system_prompt, user_prompt, citations_payload

    def build_general_prompt(self, question: str, live_context: str = "") -> Tuple[str, str]:
        """
        Builds a comprehensive ChatGPT-style prompt with real-time live data for movies,
        stocks, sports, politics, and general queries.
        """
        from datetime import datetime
        now = datetime.now()
        current_date_str = now.strftime("%A, %B %d, %Y")
        current_time_str = now.strftime("%I:%M %p")

        system_prompt = (
            f"Today's real-world current date is {current_date_str} (current time: {current_time_str}).\n"
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
        if live_context:
            user_prompt = f"Live Real-Time Web Context:\n{live_context}\n\nUser Question: {question}\n\nHelpful & Detailed Answer:"
        else:
            user_prompt = f"User Question: {question}\n\nHelpful & Detailed Answer:"
        return system_prompt, user_prompt

    async def stream_rag_response(
        self,
        question: str,
        route: str,
        router_badge: str,
        retrieved_chunks: List[Dict[str, Any]],
        queries: List[str]
    ) -> AsyncGenerator[str, None]:
        """
        Yields Server-Sent Events (SSE) lines:
        - meta event (route badge, transformed queries)
        - token events (streaming LLM tokens orchestrated via LangChain)
        - citations event (list of cited sources with bboxes for PDF.js highlighting)
        - done event
        """
        # 1. Send meta event first
        meta_data = {
            "badge": router_badge,
            "route": route,
            "queries": queries,
        }
        yield f"event: meta\ndata: {json.dumps(meta_data)}\n\n"

        # Check if question is a date/time/clock query to bypass slow web scraping
        q_lower = question.lower()
        date_keywords = ["today", "date", "year", "month", "what day", "what time", "current time", "clock"]
        is_date_query = any(k in q_lower for k in date_keywords)

        # Case A: General chat route (no documents active or ChatGPT mode)
        if route != "document":
            live_context = ""
            if not is_date_query:
                live_context = await asyncio.to_thread(live_web_search.get_live_context, question)

            async for token in langchain_adapter.stream_general_chat(
                question=question,
                live_context=live_context,
                temperature=0.7,
                max_tokens=settings.LLM_MAX_TOKENS
            ):
                yield f"event: token\ndata: {json.dumps({'content': token})}\n\n"

            yield f"event: citations\ndata: {json.dumps({'citations': []})}\n\n"
            yield f"event: done\ndata: {json.dumps({'status': 'complete'})}\n\n"
            return

        # Case B: Document route but nothing retrieved or passed threshold
        # (e.g. low relevance, off-topic question asked while document is loaded)
        if not retrieved_chunks:
            notice = "This is not mentioned in the document.\n"
            for word in notice.split(" "):
                yield f"event: token\ndata: {json.dumps({'content': word + ' '})}\n\n"

            yield f"event: citations\ndata: {json.dumps({'citations': []})}\n\n"
            yield f"event: done\ndata: {json.dumps({'status': 'complete'})}\n\n"
            return

        # Case C: Document route with retrieved context chunks
        # Orchestrate generation via LangChain (ChatPromptTemplate + SystemMessage/HumanMessage + ChatOllama)
        token_stream, citations = await langchain_adapter.stream_grounded_chat(
            question=question,
            chunks=retrieved_chunks,
            temperature=settings.LLM_TEMPERATURE,
            max_tokens=settings.LLM_MAX_TOKENS
        )

        accumulated_tokens = []
        async for token in token_stream:
            accumulated_tokens.append(token)
            yield f"event: token\ndata: {json.dumps({'content': token})}\n\n"

        full_text = "".join(accumulated_tokens).strip()
        full_text_lower = full_text.lower()

        # Check if the document did not contain the answer
        not_found_markers = [
            "not mentioned in the document",
            "not contain this information",
            "not found in the document",
            "not mentioned in the provided",
            "does not contain sufficient information",
            "not available in the document",
            "insufficient information",
            "couldn't find enough relevant information",
            "not mentioned in the context",
            "not mentioned in",
            "not found in",
            "not present in",
        ]
        is_not_found = any(m in full_text_lower for m in not_found_markers)

        if is_not_found:
            # The model identified that this info is missing in the document.
            # Cleanly return empty citations to prevent drawing any highlights on the PDF.
            citations = []
        else:
            # Fact found! Score all bounding boxes across all citations against the generated answer!
            logger.info("[CITATION] Evidence refinement started")
            citations = self.refine_citations_for_answer(
                citations=citations,
                answer_text=full_text,
                question_text=question
            )
            logger.info(f"[CITATION] Evidence refinement completed: {len(citations)} citations")

        # Send citations event (only containing the exact answer highlight boxes)
        yield f"event: citations\ndata: {json.dumps({'citations': citations})}\n\n"
        yield f"event: done\ndata: {json.dumps({'status': 'complete'})}\n\n"

    def refine_citations_for_answer(
        self,
        citations: List[Dict[str, Any]],
        answer_text: str,
        question_text: str
    ) -> List[Dict[str, Any]]:
        """
        Scores candidate bounding boxes across citations against the generated answer.
        Uses density-normalized n-gram phrase matching and query alignment to guarantee
        that highlights ONLY appear on the precise factual text answering the question,
        preventing generic background paragraphs from overriding specific definitions.
        """
        if not citations or not answer_text:
            return []

        import re
        ans_lower = answer_text.lower()
        not_found_markers = [
            "not mentioned in the document",
            "not contain this information",
            "not found in the document",
            "not mentioned in the provided",
            "does not contain sufficient information",
            "not available in the document",
            "insufficient information",
            "couldn't find enough relevant information",
            "not mentioned in the context",
            "not mentioned in",
            "not found in",
            "not present in",
            "there is no",
        ]
        if any(m in ans_lower for m in not_found_markers):
            return []

        cited_indices = [int(m) for m in re.findall(r"\[(\d+)\]", answer_text)]

        stop_words = {
            'the', 'is', 'in', 'of', 'and', 'a', 'an', 'to', 'for', 'with', 'on', 'at',
            'by', 'from', 'this', 'that', 'are', 'was', 'were', 'document', 'resume',
            'candidate', 'answer', 'according', 'mentioned', 'based', 'context', 'listed', 'include', 'as', 'it'
        }

        def clean_tokens(text: str) -> List[str]:
            return [w for w in re.findall(r'[a-zA-Z0-9%]+', text.lower()) if len(w) >= 3 and w not in stop_words]

        def get_ngrams(tokens: List[str], n: int) -> set:
            return set(" ".join(tokens[i:i+n]) for i in range(len(tokens) - n + 1))

        q_tokens = clean_tokens(question_text or "")
        q_bigrams = get_ngrams(q_tokens, 2)

        ans_tokens = clean_tokens(answer_text)
        ans_unique_kws = set(ans_tokens)
        ans_bigrams = get_ngrams(ans_tokens, 2)
        ans_trigrams = get_ngrams(ans_tokens, 3)

        if not ans_unique_kws:
            return []

        scored_candidates = []

        for c_idx, cite in enumerate(citations):
            src_idx = cite.get("source_index", c_idx + 1)
            for b in cite.get("bboxes", []):
                btext = (b.get("text") or "").strip()
                if not btext:
                    continue

                bt_tokens = clean_tokens(btext)
                if not bt_tokens:
                    continue

                bt_unique = set(bt_tokens)
                bt_bigrams = get_ngrams(bt_tokens, 2)
                bt_trigrams = get_ngrams(bt_tokens, 3)

                # 1. Unique answer keyword overlap
                matched_kws = ans_unique_kws.intersection(bt_unique)
                kw_score = len(matched_kws) * 3.0

                # 2. Bigram phrase overlap
                matched_bigrams = ans_bigrams.intersection(bt_bigrams)
                bigram_score = len(matched_bigrams) * 6.0

                # 3. Trigram phrase overlap
                matched_trigrams = ans_trigrams.intersection(bt_trigrams)
                trigram_score = len(matched_trigrams) * 12.0

                # 4. Question alignment bonus (ensures the bbox is directly addressing the question)
                matched_q_kws = set(q_tokens).intersection(bt_unique)
                q_score = len(matched_q_kws) * 4.0
                matched_q_bi = q_bigrams.intersection(bt_bigrams)
                q_score += len(matched_q_bi) * 8.0

                raw_score = kw_score + bigram_score + trigram_score + q_score

                # 5. Density normalization to prevent long generic background blocks from winning
                density = raw_score / max(len(bt_tokens), 10)

                # 6. Source rank prior (higher ranked chunks from hybrid search receive a prior)
                rank_boost = max(0.0, (5.0 - float(src_idx))) * 2.0

                final_score = raw_score * 0.4 + density * 10.0 + rank_boost
                box_page = b.get("page", cite.get("page", 1))

                scored_candidates.append({
                    "score": final_score,
                    "page": box_page,
                    "cite_idx": c_idx,
                    "box": b
                })

        if not scored_candidates:
            return []

        # Sort candidate boxes by match score
        scored_candidates.sort(key=lambda x: x["score"], reverse=True)
        best = scored_candidates[0]

        # Require meaningful confidence (score >= 20.0) before drawing highlights
        min_score_required = 20.0
        if best["score"] < min_score_required:
            logger.info(f"[CITATION] Bounding box match score {best['score']} below required {min_score_required}. Clearing highlights.")
            return []

        winning_page = best["page"]
        winning_cite_idx = best["cite_idx"]
        score_cutoff = max(35.0, best["score"] * 0.08)

        # Collect all confident matching bounding boxes on the winning page so the entire answer is highlighted
        winning_boxes = []
        seen_texts = set()
        for item in scored_candidates:
            if item["page"] == winning_page and item["score"] >= score_cutoff:
                box_txt = item["box"].get("text", "").strip()
                if box_txt not in seen_texts:
                    seen_texts.add(box_txt)
                    winning_boxes.append(item["box"])

        # Fallback to at least the top box if cutoff was strict
        if not winning_boxes:
            winning_boxes = [best["box"]]

        refined = []
        for c_idx, cite in enumerate(citations):
            cite_copy = dict(cite)
            if c_idx == winning_cite_idx:
                cite_copy["bboxes"] = winning_boxes
                cite_copy["page"] = winning_page
                cite_copy["page_number"] = winning_page
            else:
                cite_copy["bboxes"] = []
            refined.append(cite_copy)

        # Place the winning citation first so the frontend automatically opens and focuses it
        if winning_cite_idx > 0:
            winner = refined.pop(winning_cite_idx)
            refined.insert(0, winner)

        return refined

grounded_generator = GroundedGenerator()
