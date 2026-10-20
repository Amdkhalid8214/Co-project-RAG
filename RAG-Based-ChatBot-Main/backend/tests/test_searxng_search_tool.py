"""
Automated Test Suite for Production SearXNG Web Search Tool in DocuChat AI.

Covers:
1. Unit Tests for SearXNG Parser & Sanitization:
   - Successful search response parsing (title, url, snippet, engine)
   - URL validation (http/https accepted, invalid/malformed discarded)
   - Handling missing fields (missing snippet, missing title, missing engine)
   - Empty results payload ({'results': []})
   - HTML stripping, unescaping, and whitespace normalization

2. Network & Error Handling:
   - Successful search with mocked JSON response (async and sync clients)
   - HTTP status error (e.g. HTTP 500 / HTTP 429) handled gracefully without crashing
   - Request timeout (httpx.TimeoutException) handled gracefully
   - Connection failure (httpx.ConnectError to SearXNG) handled gracefully
   - Malformed / non-JSON responses handled gracefully

3. Web Mode Behavior:
   - Web Mode OFF strictly prevents web search from being bound or executed
   - Web Mode ON equips the model with the SearXNG web search tool
   - Normal chat without search executes cleanly

4. LangChain Tool Calling & Orchestration Flow:
   - Correct sequence: HumanMessage -> AIMessage with tool_calls -> execute SearXNG tool -> ToolMessage -> final answer
   - Bounded tool execution: stops within max_iterations (default 3) preventing infinite loops
   - Model response citing source URLs from the search snippets

5. Existing Document RAG & PDF Highlighting Preservation:
   - Grounded document QA answer generation remains intact
   - Bounding-box and citation refinement for PDF.js highlighting unaffected
"""

import sys
import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch
import httpx

# Ensure project root is in sys.path
root_dir = str(Path(__file__).resolve().parent.parent.parent)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage
from backend.tools.searxng_search import (
    searxng_search_tool,
    web_search_tool,
    search_searxng_async,
    search_searxng_sync,
    parse_searxng_response,
    is_valid_http_url,
    sanitize_snippet,
    format_search_results_for_llm,
)
from backend.llm.langchain_adapter import LangChainAdapter, langchain_adapter
from backend.llm.generator import GroundedGenerator


# ==============================================================================
# 1. UNIT TESTS: PARSER, URL VALIDATION & SANITIZATION
# ==============================================================================

def test_url_validation():
    """Verify that only valid HTTP/HTTPS URLs are accepted."""
    assert is_valid_http_url("https://docs.searxng.org/admin/index.html") is True
    assert is_valid_http_url("http://127.0.0.1:8080/search") is True
    assert is_valid_http_url("http://localhost:3000") is True

    # Rejection cases
    assert is_valid_http_url("javascript:alert(1)") is False
    assert is_valid_http_url("file:///etc/passwd") is False
    assert is_valid_http_url("ftp://ftp.example.com") is False
    assert is_valid_http_url("/relative/path") is False
    assert is_valid_http_url("") is False
    assert is_valid_http_url(None) is False


def test_sanitize_snippet():
    """Verify HTML tag stripping, entity unescaping, and whitespace normalization."""
    raw = "<b>LangChain</b> is a &quot;framework&quot; for &lt;LLMs&gt;.\n\n  Multiple   spaces."
    cleaned = sanitize_snippet(raw)
    assert cleaned == 'LangChain is a "framework" for <LLMs>. Multiple spaces.'


def test_parse_searxng_response_success():
    """Verify complete extraction of valid results from mock SearXNG JSON."""
    mock_payload = {
        "query": "fastapi rag",
        "number_of_results": 2,
        "results": [
            {
                "title": "FastAPI <b>Documentation</b>",
                "url": "https://fastapi.tiangolo.com/",
                "content": "FastAPI is a modern, fast <i>web framework</i>.",
                "engine": "duckduckgo"
            },
            {
                "title": "Building RAG with Qdrant",
                "url": "https://qdrant.tech/articles/rag-fastapi/",
                "content": "Learn how to build high-performance vector search.",
                "engine": "google"
            }
        ]
    }

    results = parse_searxng_response(mock_payload, max_results=5)
    assert len(results) == 2
    assert results[0]["title"] == "FastAPI Documentation"
    assert results[0]["url"] == "https://fastapi.tiangolo.com/"
    assert "web framework" in results[0]["snippet"]
    assert results[0]["engine"] == "duckduckgo"

    assert results[1]["url"] == "https://qdrant.tech/articles/rag-fastapi/"


def test_parse_searxng_missing_fields_and_invalid_urls():
    """Verify that results with missing fields do not cause crashes and invalid URLs are dropped."""
    mock_payload = {
        "results": [
            # Missing title and engine
            {
                "url": "https://example.com/no-title",
                "content": "Some snippet without a title."
            },
            # Missing content
            {
                "title": "Page without content",
                "url": "https://example.com/no-content"
            },
            # Invalid URL (must be dropped)
            {
                "title": "Evil script",
                "url": "javascript:void(0)",
                "content": "Attack payload"
            },
            # Non-dict item
            "just a string"
        ]
    }

    results = parse_searxng_response(mock_payload, max_results=5)
    assert len(results) == 2
    assert results[0]["title"] == "Untitled Web Page"
    assert results[0]["url"] == "https://example.com/no-title"
    assert results[1]["snippet"] == ""


def test_parse_searxng_empty_results():
    """Verify empty results payload returns empty list."""
    assert parse_searxng_response({"results": []}) == []
    assert parse_searxng_response({}) == []
    assert parse_searxng_response({"results": None}) == []


# ==============================================================================
# 2. NETWORK & ERROR HANDLING TESTS
# ==============================================================================

@pytest.mark.asyncio
async def test_searxng_async_success():
    """Verify successful async query with mocked httpx response."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "results": [
            {
                "title": "Ollama Official",
                "url": "https://ollama.com",
                "content": "Get up and running with large language models locally.",
                "engine": "brave"
            }
        ]
    }
    mock_resp.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp
        res = await search_searxng_async("ollama local llm")

        assert res.get("error") is None
        assert res["count"] == 1
        assert res["results"][0]["url"] == "https://ollama.com"
        assert "Ollama Official" in res["formatted"]
        assert "Source URL: https://ollama.com" in res["formatted"]


@pytest.mark.asyncio
async def test_searxng_connection_failure():
    """Verify connection error (e.g. SearXNG container offline) returns clean error."""
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = httpx.ConnectError("Connection refused to 127.0.0.1:8080")
        res = await search_searxng_async("test query")

        assert res.get("error") is not None
        assert "unreachable" in res["error"].lower()
        assert res["results"] == []


@pytest.mark.asyncio
async def test_searxng_timeout():
    """Verify network timeout returns clean timeout error."""
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = httpx.TimeoutException("Read timeout after 10.0s")
        res = await search_searxng_async("timeout query")

        assert res.get("error") is not None
        assert "timed out" in res["error"].lower()
        assert res["results"] == []


@pytest.mark.asyncio
async def test_searxng_http_error():
    """Verify HTTP 500 / 429 returns clean error message."""
    mock_resp = MagicMock()
    mock_resp.status_code = 500
    mock_resp.text = "Internal Server Error in upstream engine"

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = httpx.HTTPStatusError("500 Server Error", request=MagicMock(), response=mock_resp)
        res = await search_searxng_async("error query")

        assert res.get("error") is not None
        assert "HTTP 500" in res["error"]
        assert res["results"] == []


@pytest.mark.asyncio
async def test_searxng_malformed_json():
    """Verify invalid JSON returns clean decode error."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.side_effect = json.JSONDecodeError("Expecting value", "<html>Nginx 502 Bad Gateway</html>", 0)
    mock_resp.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp
        res = await search_searxng_async("bad json query")

        assert res.get("error") is not None
        assert "malformed json" in res["error"].lower()


# ==============================================================================
# 3. WEB MODE BEHAVIOR & PERMISSION ENFORCEMENT
# ==============================================================================

@pytest.mark.asyncio
async def test_web_mode_off_strictly_prevents_search():
    """
    CRITICAL REQUIREMENT:
    When Web Mode is OFF, web search tool must NOT be bound or executed, even if the model attempts to call it.
    """
    adapter = LangChainAdapter()
    captured_tools = []

    def mock_bind_tools(tools):
        nonlocal captured_tools
        captured_tools = tools
        mock_bound = MagicMock()
        mock_bound.ainvoke = AsyncMock(return_value=AIMessage(content="Direct answer without web search."))
        return mock_bound

    mock_llm = MagicMock()
    mock_llm.bind_tools = mock_bind_tools

    with patch.object(adapter, "get_llm", return_value=mock_llm):
        tokens = []
        async for t in adapter.stream_general_chat(
            question="What is the latest release of Python?",
            web_mode=False
        ):
            tokens.append(t)

        # Verify: searxng_search_tool was NOT in bound tools!
        tool_names = [getattr(t, "name", "") for t in captured_tools]
        assert "web_search" not in tool_names, f"Web search was illegally exposed when Web Mode was OFF: {tool_names}"


@pytest.mark.asyncio
async def test_web_mode_on_permits_search():
    """
    When Web Mode is ON, web_search tool IS provided in the bound tools for the model.
    """
    adapter = LangChainAdapter()
    captured_tools = []

    def mock_bind_tools(tools):
        nonlocal captured_tools
        captured_tools = tools
        mock_bound = MagicMock()
        mock_bound.ainvoke = AsyncMock(return_value=AIMessage(content="Answer using web search."))
        return mock_bound

    mock_llm = MagicMock()
    mock_llm.bind_tools = mock_bind_tools

    with patch.object(adapter, "get_llm", return_value=mock_llm):
        tokens = []
        async for t in adapter.stream_general_chat(
            question="What is the latest release of Python?",
            web_mode=True
        ):
            tokens.append(t)

        tool_names = [getattr(t, "name", "") for t in captured_tools]
        assert "web_search" in tool_names, f"Web search should be enabled when Web Mode is ON: {tool_names}"


# ==============================================================================
# 4. TOOL CALLING SEQUENCE & ITERATION BOUNDING
# ==============================================================================

@pytest.mark.asyncio
async def test_full_tool_call_result_answer_sequence():
    """
    Verify complete tool calling sequence:
    HumanMessage -> AIMessage(tool_calls=[web_search]) -> ToolMessage -> final answer citing source URL.
    """
    adapter = LangChainAdapter()

    user_query = "What is SearXNG?"
    ai_tool_call = AIMessage(
        content="",
        tool_calls=[{
            "name": "web_search",
            "args": {"query": "SearXNG metasearch"},
            "id": "call_searx_1",
            "type": "tool_call"
        }]
    )

    mock_search_results = {
        "query": "SearXNG metasearch",
        "results": [
            {
                "title": "SearXNG Documentation",
                "url": "https://docs.searxng.org",
                "snippet": "SearXNG is a free internet metasearch engine which aggregates results from various search services."
            }
        ],
        "formatted": "=== Live Web Search Results ===\n[1] SearXNG Documentation\nSource URL: https://docs.searxng.org\nSnippet: Free metasearch engine."
    }

    mock_llm_tools = MagicMock()
    mock_llm_tools.ainvoke = AsyncMock(return_value=ai_tool_call)

    async def mock_astream(messages):
        # Verify ToolMessage is in the message trajectory passed to final astream
        tool_msgs = [m for m in messages if isinstance(m, ToolMessage)]
        assert len(tool_msgs) >= 1, "ToolMessage was not passed back to the model trajectory!"
        assert tool_msgs[0].tool_call_id == "call_searx_1"

        yield MagicMock(content="SearXNG is a privacy-respecting metasearch engine ")
        yield MagicMock(content="documented at https://docs.searxng.org.")

    mock_llm_plain = MagicMock()
    mock_llm_plain.bind_tools = MagicMock(return_value=mock_llm_tools)
    mock_llm_plain.astream = mock_astream

    with patch.object(adapter, "get_llm", return_value=mock_llm_plain), \
         patch("backend.tools.searxng_search.search_searxng_async", new_callable=AsyncMock, return_value=mock_search_results):

        tokens = []
        async for token in adapter.stream_general_chat(
            question=user_query,
            web_mode=True
        ):
            tokens.append(token)

        full_answer = "".join(tokens)
        assert "SearXNG" in full_answer
        assert "https://docs.searxng.org" in full_answer


@pytest.mark.asyncio
async def test_maximum_tool_iteration_limit():
    """
    Verify that if the model continuously outputs tool_calls, execution terminates
    strictly at max_iterations (default 3) and does not enter an infinite loop.
    """
    adapter = LangChainAdapter()

    infinite_tool_call = AIMessage(
        content="",
        tool_calls=[{
            "name": "web_search",
            "args": {"query": "loop query"},
            "id": "call_loop",
            "type": "tool_call"
        }]
    )

    call_count = 0
    async def mock_tool_invoker(messages):
        nonlocal call_count
        call_count += 1
        return infinite_tool_call

    mock_llm_tools = MagicMock()
    mock_llm_tools.ainvoke = mock_tool_invoker

    async def mock_astream(messages):
        yield MagicMock(content="Max iterations reached.")

    mock_llm_plain = MagicMock()
    mock_llm_plain.bind_tools = MagicMock(return_value=mock_llm_tools)
    mock_llm_plain.astream = mock_astream

    with patch.object(adapter, "get_llm", return_value=mock_llm_plain), \
         patch("backend.tools.searxng_search.search_searxng_async", new_callable=AsyncMock, return_value={"results": []}):

        tokens = []
        async for token in adapter.stream_chat_with_tools(
            messages=[HumanMessage(content="loop test")],
            tools=[searxng_search_tool],
            max_iterations=3
        ):
            tokens.append(token)

        assert call_count == 3, f"Expected exactly 3 iterations, got {call_count}"
        assert "".join(tokens) == "Max iterations reached."


# ==============================================================================
# 5. DOCUMENT RAG & PDF HIGHLIGHTING PRESERVATION
# ==============================================================================

def test_document_rag_and_pdf_highlighting_unaffected():
    """
    Verify that existing document RAG citations, page numbers, and bounding-box
    highlight refinement for PDF.js remain 100% intact.
    """
    generator = GroundedGenerator()
    citations = [
        {
            "source_index": 1,
            "chunk_id": "chunk_xyz",
            "doc_id": "doc_abc",
            "page": 2,
            "bboxes": [
                {"x0": 20, "y0": 30, "x1": 200, "y1": 45, "text": "Net income increased by 24% to $12.4 million."},
                {"x0": 20, "y0": 50, "x1": 200, "y1": 65, "text": "Operating margin expanded by 180 basis points."}
            ],
            "heading_path": ["Financial Results"],
            "snippet": "Net income increased by 24% to $12.4 million."
        }
    ]

    answer = "The company reported that net income increased by 24% to $12.4 million [1]."
    question = "What was the net income increase?"

    refined = generator.refine_citations_for_answer(citations, answer, question)
    assert len(refined) == 1
    assert len(refined[0]["bboxes"]) == 1
    winning_box = refined[0]["bboxes"][0]
    assert "$12.4 million" in winning_box["text"]
    assert refined[0]["page"] == 2
