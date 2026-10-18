"""
Test Suite: Qwen 2.5 7B Model Upgrade Verification
Covers:
1. Configuration & environment verification (LLM_MODEL=qwen2.5:7b, embeddings unchanged)
2. LangChain message structure and ChatOllama integration
3. Calculator / math reasoning handling
4. Live web search and tool-result handling (no fabrication)
5. Excel / structured markdown table generation
6. Grounded document answers with citations
7. Insufficient-context refusal (no hallucinations)
8. PDF citation and bounding-box provenance preservation
9. Streaming and SSE protocol compliance
10. Error resilience (model missing, out of memory, timeout, connection failure)
"""

import sys
import json
import asyncio
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add project root to sys.path
root_dir = str(Path(__file__).resolve().parent.parent.parent)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.messages.ai import AIMessageChunk
from langchain_core.documents import Document

from backend.config import settings
from backend.llm.langchain_adapter import LangChainAdapter, langchain_adapter
from backend.llm.client import OllamaClient, ollama_client
from backend.llm.generator import GroundedGenerator, grounded_generator
from backend.retrieval.web_search import live_web_search


def test_model_configuration_and_environment():
    """Verify default model is in qwen2.5 family, embedding model is untouched, and model name is configurable."""
    # 1. Config supports qwen2.5 family (7b or 3b)
    assert settings.LLM_MODEL in ["qwen2.5:7b", "qwen2.5:3b"], f"Expected qwen2.5:7b or 3b, got {settings.LLM_MODEL}"

    # 2. Embedding model is NOT changed (remains BAAI or nomic)
    assert "bge" in settings.EMBEDDING_MODEL.lower() or "nomic" in settings.EMBEDDING_MODEL.lower()

    # 3. LangChain adapter defaults to configured model
    adapter = LangChainAdapter()
    assert adapter.model_name in ["qwen2.5:7b", "qwen2.5:3b"]

    # 4. OllamaClient defaults to configured model
    client = OllamaClient()
    assert client.model in ["qwen2.5:7b", "qwen2.5:3b"]

    # 5. Configurable override works
    custom_adapter = LangChainAdapter(model="qwen2.5:14b")
    assert custom_adapter.model_name == "qwen2.5:14b"
    print("test_model_configuration_and_environment passed!")


def test_calculator_and_math_reasoning():
    """Verify that calculator/mathematical queries with Qwen 2.5 7B construct proper prompts and handle calculation outputs."""
    adapter = LangChainAdapter()

    # Document containing numeric financial figures
    doc = Document(
        page_content="Q3 Revenue was $150,000,000 with total operating expenses of $90,000,000. Tax rate is 20%.",
        metadata={
            "document_id": "doc_fin",
            "chunk_id": "c_fin_1",
            "page_number": 4,
            "section": "Financials > Income Statement",
            "source_index": 1,
            "bbox": [{"x0": 10, "y0": 20, "x1": 200, "y1": 40, "text": "Q3 Revenue was $150,000,000"}]
        }
    )

    question = "Calculate the net operating profit after tax (NOPAT) based on the figures in the document."
    messages, citations = adapter.build_grounded_messages(question, [doc])

    assert len(messages) == 2
    assert "qwen2.5:7b" in adapter.model_name or adapter.model_name == settings.LLM_MODEL
    assert "Q3 Revenue was $150,000,000" in messages[1].content
    assert "Calculate the net operating profit" in messages[1].content

    # Mock Qwen 7B performing the calculation
    async def mock_math_stream(msgs):
        calc_tokens = [
            "Based ", "on ", "the ", "document ", "[1]:\n",
            "- Operating Profit = $150,000,000 - $90,000,000 = $60,000,000.\n",
            "- Tax (20%) = $12,000,000.\n",
            "- Net Operating Profit After Tax (NOPAT) = $48,000,000."
        ]
        for t in calc_tokens:
            yield AIMessageChunk(content=t)

    mock_llm = MagicMock()
    mock_llm.astream = mock_math_stream

    async def run_calc():
        with patch.object(adapter, "get_llm", return_value=mock_llm):
            stream = adapter.stream_messages(messages)
            collected = []
            async for token in stream:
                collected.append(token)
            return "".join(collected)

    answer = asyncio.run(run_calc())
    assert "$48,000,000" in answer
    assert "[1]" in answer
    print("test_calculator_and_math_reasoning passed!")


def test_live_web_search_and_tool_result_handling():
    """Verify live web search tool returns formatted context and model synthesizes tool results without fabricating them."""
    # Test stock lookup logic
    stock_context = live_web_search.get_stock_data("What is the stock price of Apple?")
    # Either returns live formatted ticker data or None gracefully if offline
    if stock_context:
        assert "AAPL" in stock_context
        assert "trading at" in stock_context

    # Verify formatting of tool result into general prompt
    adapter = LangChainAdapter()
    simulated_tool_result = "[LIVE STOCK DATA] NVDA is currently trading at 135.50 USD (+3.20 / +2.42% from previous close)."
    messages = adapter.build_general_messages(
        question="How is Nvidia stock performing today?",
        live_context=simulated_tool_result
    )

    assert len(messages) == 2
    human_content = messages[1].content
    assert "Supplied Live or External Context:" in human_content
    assert "135.50 USD" in human_content
    assert "How is Nvidia stock performing today?" in human_content

    # Verify that stream yields answer faithful to tool result
    async def mock_web_stream(msgs):
        tokens = ["Nvidia ", "(NVDA) ", "is ", "currently ", "trading ", "at ", "$135.50, ", "up ", "2.42%."]
        for t in tokens:
            yield AIMessageChunk(content=t)

    mock_llm = MagicMock()
    mock_llm.astream = mock_web_stream

    async def run_tool_synth():
        with patch.object(adapter, "get_llm", return_value=mock_llm):
            stream = adapter.stream_messages(messages)
            collected = []
            async for token in stream:
                collected.append(token)
            return "".join(collected)

    res = asyncio.run(run_tool_synth())
    assert "$135.50" in res
    assert "2.42%" in res
    print("test_live_web_search_and_tool_result_handling passed!")


def test_excel_and_structured_table_generation():
    """Verify that Qwen 7B prompt structure supports generating clean Markdown/Excel table rows for the frontend table renderer."""
    adapter = LangChainAdapter()

    doc = Document(
        page_content="Candidate: John Doe. Languages: Python, Go, C++. Frameworks: FastAPI, React. Database: PostgreSQL, Qdrant.",
        metadata={"source_index": 1, "page_number": 1, "document_id": "resume_1", "chunk_id": "c1", "bbox": []}
    )

    question = "Generate a table summarizing John's technical skills by category."
    messages, _ = adapter.build_grounded_messages(question, [doc])

    async def mock_table_stream(msgs):
        table_output = [
            "| Category | Technologies |\n",
            "| --- | --- |\n",
            "| Languages | Python, Go, C++ |\n",
            "| Frameworks | FastAPI, React |\n",
            "| Databases | PostgreSQL, Qdrant |"
        ]
        for row in table_output:
            yield AIMessageChunk(content=row)

    mock_llm = MagicMock()
    mock_llm.astream = mock_table_stream

    async def run_table():
        with patch.object(adapter, "get_llm", return_value=mock_llm):
            stream = adapter.stream_messages(messages)
            collected = []
            async for token in stream:
                collected.append(token)
            return "".join(collected)

    table_res = asyncio.run(run_table())
    assert "| Category | Technologies |" in table_res
    assert "| Languages | Python, Go, C++ |" in table_res
    print("test_excel_and_structured_table_generation passed!")


def test_insufficient_context_refusal_no_fabrication():
    """Verify that when information is absent from the document, the model outputs refusal and does not fabricate fake tool/document results."""
    adapter = LangChainAdapter()

    doc = Document(
        page_content="This document covers the employee vacation and PTO policy. Employees receive 15 days PTO per year.",
        metadata={"source_index": 1, "page_number": 2, "document_id": "pto_doc", "chunk_id": "c_pto", "bbox": []}
    )

    question = "What is the corporate severance formula for executive departures?"
    messages, citations = adapter.build_grounded_messages(question, [doc])

    # Ensure grounding rules instruct refusal
    assert "This is not mentioned in the provided document context" in messages[0].content

    # Simulate strict refusal from Qwen 7B
    async def mock_refusal_stream(msgs):
        yield AIMessageChunk(content="This is not mentioned in the document.")

    mock_llm = MagicMock()
    mock_llm.astream = mock_refusal_stream

    async def run_refusal():
        with patch.object(langchain_adapter, "get_llm", return_value=mock_llm):
            events = []
            async for sse_chunk in grounded_generator.stream_rag_response(
                question=question,
                route="document",
                router_badge="From document",
                retrieved_chunks=[{
                    "chunk_id": "c_pto",
                    "doc_id": "pto_doc",
                    "text": doc.page_content,
                    "page": 2,
                    "bboxes": []
                }],
                queries=[question]
            ):
                events.append(sse_chunk)
            return events

    sse_events = asyncio.run(run_refusal())
    combined = "".join(sse_events)

    # Must contain refusal text
    assert "not mentioned in the document" in combined.lower()

    # Citations must be emptied so the frontend does NOT paint false highlights
    for evt in sse_events:
        if "event: citations" in evt:
            data_line = [l for l in evt.split("\n") if l.startswith("data:")][0]
            cites = json.loads(data_line.replace("data:", "").strip()).get("citations", [])
            assert cites == [], f"Expected empty citations on refusal, got {cites}"
    print("test_insufficient_context_refusal_no_fabrication passed!")


def test_pdf_citation_and_bbox_preservation():
    """Verify that answer citations with Qwen 7B correctly isolate the winning bounding box for PDF.js highlighting."""
    generator = GroundedGenerator()
    citations = [
        {
            "source_index": 1,
            "chunk_id": "c_1",
            "doc_id": "doc_1",
            "page": 3,
            "bboxes": [
                {"x0": 10, "y0": 20, "x1": 150, "y1": 35, "text": "Annual recurring revenue reached $85 million in FY24"},
                {"x0": 10, "y0": 40, "x1": 150, "y1": 55, "text": "Headcount increased to 450 full-time employees"}
            ],
            "heading_path": ["Performance Highlights"],
            "snippet": "Annual recurring revenue reached $85 million in FY24."
        }
    ]

    answer = "According to the report, annual recurring revenue reached $85 million in FY24 [1]."
    question = "What was the annual recurring revenue?"

    refined = generator.refine_citations_for_answer(citations, answer, question)
    assert len(refined) == 1
    assert len(refined[0]["bboxes"]) == 1
    winning_box = refined[0]["bboxes"][0]
    assert "$85 million" in winning_box["text"]
    print("test_pdf_citation_and_bbox_preservation passed!")


def test_resource_and_error_handling_graceful_diagnostics():
    """Verify that model unavailability, insufficient VRAM, timeouts, and connection errors yield clear diagnostics and do not crash."""
    adapter = LangChainAdapter()

    # 1. Model Not Found
    async def mock_not_found(msgs):
        raise Exception("model 'qwen2.5:7b' not found, try pulling it first (status code: 404)")
        yield

    mock_llm_nf = MagicMock()
    mock_llm_nf.astream = mock_not_found
    with patch.object(adapter, "get_llm", return_value=mock_llm_nf):
        tokens = asyncio.run(asyncio.to_thread(lambda: list()))
        async def run_nf():
            res = []
            async for t in adapter.stream_messages([HumanMessage(content="test")]):
                res.append(t)
            return "".join(res)
        msg_nf = asyncio.run(run_nf())
        assert "not found" in msg_nf.lower()
        assert f"ollama pull {adapter.model_name}" in msg_nf

    # 2. Out of Memory / Insufficient VRAM
    async def mock_oom(msgs):
        raise Exception("CUDA out of memory. Tried to allocate 4.8 GiB for qwen2.5:7b")
        yield

    mock_llm_oom = MagicMock()
    mock_llm_oom.astream = mock_oom
    with patch.object(adapter, "get_llm", return_value=mock_llm_oom):
        async def run_oom():
            res = []
            async for t in adapter.stream_messages([HumanMessage(content="test")]):
                res.append(t)
            return "".join(res)
        msg_oom = asyncio.run(run_oom())
        assert "insufficient" in msg_oom.lower() or "memory" in msg_oom.lower()

    # 3. Request Timeout
    async def mock_timeout(msgs):
        raise TimeoutError("The read operation timed out after 180.0 seconds")
        yield

    mock_llm_to = MagicMock()
    mock_llm_to.astream = mock_timeout
    with patch.object(adapter, "get_llm", return_value=mock_llm_to):
        async def run_to():
            res = []
            async for t in adapter.stream_messages([HumanMessage(content="test")]):
                res.append(t)
            return "".join(res)
        msg_to = asyncio.run(run_to())
        assert "timed out" in msg_to.lower() or "timeout" in msg_to.lower()

    # 4. Connection Refused
    async def mock_conn(msgs):
        raise ConnectionError("Failed to connect to Ollama at http://localhost:11434")
        yield

    mock_llm_conn = MagicMock()
    mock_llm_conn.astream = mock_conn
    with patch.object(adapter, "get_llm", return_value=mock_llm_conn):
        async def run_conn():
            res = []
            async for t in adapter.stream_messages([HumanMessage(content="test")]):
                res.append(t)
            return "".join(res)
        msg_conn = asyncio.run(run_conn())
        assert "connection" in msg_conn.lower()

    print("test_resource_and_error_handling_graceful_diagnostics passed!")


if __name__ == "__main__":
    test_model_configuration_and_environment()
    test_calculator_and_math_reasoning()
    test_live_web_search_and_tool_result_handling()
    test_excel_and_structured_table_generation()
    test_insufficient_context_refusal_no_fabrication()
    test_pdf_citation_and_bbox_preservation()
    test_resource_and_error_handling_graceful_diagnostics()
    print("\nAll Qwen 2.5 7B Upgrade tests passed successfully!")
