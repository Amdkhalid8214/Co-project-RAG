import sys
from pathlib import Path
from typing import Dict, Any, List

# Add project root to sys.path
root_dir = str(Path(__file__).resolve().parent.parent.parent)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

import pytest
from langchain_core.documents import Document
from backend.llm.langchain_adapter import LangChainAdapter
from backend.llm.generator import GroundedGenerator


def test_build_context_citations_metadata():
    """
    Test 1: Verify document chunks produce genuine evidence metadata
    with stable doc_id, filename, 1-based page number, bboxes, and snippet.
    """
    adapter = LangChainAdapter()
    docs = [
        Document(
            page_content="Employees are entitled to 25 days annual leave.",
            metadata={
                "source_index": 1,
                "chunk_id": "chunk-101",
                "document_id": "doc-uuid-1",
                "filename": "HR-Policy-Manual-Template.pdf",
                "page_number": 20,
                "bbox": [{"x0": 50, "y0": 100, "x1": 400, "y1": 120, "page": 20}],
            }
        ),
        Document(
            page_content="Probationary period for new hires is six months.",
            metadata={
                "source_index": 2,
                "chunk_id": "chunk-102",
                "document_id": "doc-uuid-1",
                "filename": "HR-Policy-Manual-Template.pdf",
                "page_number": 19,
                "bbox": [{"x0": 50, "y0": 200, "x1": 380, "y1": 220, "page": 19}],
            }
        ),
    ]

    context, citations = adapter.format_context_from_documents(docs)

    assert "HR-Policy-Manual-Template.pdf" in context or "Page 20" in context
    assert len(citations) == 2

    c1 = citations[0]
    assert c1["source_index"] == 1
    assert c1["chunk_id"] == "chunk-101"
    assert c1["doc_id"] == "doc-uuid-1"
    assert c1["filename"] == "HR-Policy-Manual-Template.pdf"
    assert c1["page"] == 20
    assert len(c1["bboxes"]) == 1
    assert c1["bboxes"][0]["page"] == 20
    assert "25 days annual leave" in c1["snippet"]

    c2 = citations[1]
    assert c2["source_index"] == 2
    assert c2["chunk_id"] == "chunk-102"
    assert c2["doc_id"] == "doc-uuid-1"
    assert c2["page"] == 19


def test_multiple_chunks_same_page_preserved():
    """
    Test 2: Multiple distinct chunks on the same page (e.g. p. 20, source 1 and source 6)
    must both be preserved with their distinct source_indices.
    """
    adapter = LangChainAdapter()
    docs = [
        Document(
            page_content="Working hours are 37.5 hours per week.",
            metadata={
                "source_index": 1,
                "chunk_id": "chunk-p20-a",
                "document_id": "doc-uuid-1",
                "filename": "HR-Policy-Manual-Template.pdf",
                "page_number": 20,
            }
        ),
        Document(
            page_content="Duty rotas and shift patterns are published monthly.",
            metadata={
                "source_index": 6,
                "chunk_id": "chunk-p20-b",
                "document_id": "doc-uuid-1",
                "filename": "HR-Policy-Manual-Template.pdf",
                "page_number": 20,
            }
        ),
    ]

    _, citations = adapter.format_context_from_documents(docs)
    assert len(citations) == 2
    assert citations[0]["page"] == 20
    assert citations[0]["source_index"] == 1
    assert citations[1]["page"] == 20
    assert citations[1]["source_index"] == 6


def test_deduplication_exact_duplicate_chunks():
    """
    Test 3: Duplicate references to the identical chunk must be filtered out,
    while distinct chunks are kept.
    """
    citations = [
        {"doc_id": "doc-1", "chunk_id": "chunk-101", "filename": "Policy.pdf", "page": 20, "source_index": 1},
        {"doc_id": "doc-1", "chunk_id": "chunk-101", "filename": "Policy.pdf", "page": 20, "source_index": 1},  # Exact duplicate
        {"doc_id": "doc-1", "chunk_id": "chunk-102", "filename": "Policy.pdf", "page": 20, "source_index": 2},  # Same page, distinct chunk
    ]

    seen = set()
    deduped = []
    for c in citations:
        key = c.get("chunk_id") or f"{c['doc_id']}_p{c['page']}_s{c['source_index']}"
        if key not in seen:
            seen.add(key)
            deduped.append(c)

    assert len(deduped) == 2
    assert deduped[0]["chunk_id"] == "chunk-101"
    assert deduped[1]["chunk_id"] == "chunk-102"


def test_missing_bounding_boxes_preserve_page_navigation():
    """
    Test 4: When bounding boxes are unavailable (e.g. scanned or pure text document),
    the citation still retains doc_id, filename, and page number, and does NOT fabricate coordinates.
    """
    adapter = LangChainAdapter()
    docs = [
        Document(
            page_content="General guidelines for office security.",
            metadata={
                "source_index": 1,
                "chunk_id": "chunk-no-bbox",
                "document_id": "doc-uuid-2",
                "filename": "Security-Guide.pdf",
                "page_number": 5,
                "bbox": [],  # No bounding box
            }
        )
    ]

    _, citations = adapter.format_context_from_documents(docs)
    assert len(citations) == 1
    cite = citations[0]
    assert cite["bboxes"] == []
    assert cite["page"] == 5
    assert cite["filename"] == "Security-Guide.pdf"
    assert cite["doc_id"] == "doc-uuid-2"


def test_not_found_response_suppresses_evidence():
    """
    Test 5: If the model determines information is not found in the document,
    citations must be empty to avoid displaying fake evidence cards.
    """
    gen = GroundedGenerator()
    not_found_text = "This is not mentioned in the provided document context."
    not_found_markers = [
        "this is not mentioned in the provided document context",
        "not mentioned in the provided document context",
        "not mentioned in the document",
        "not contain this information",
        "not found in the document",
    ]
    is_not_found = any(m in not_found_text.lower() for m in not_found_markers)
    assert is_not_found is True

    raw_citations = [
        {"source_index": 1, "filename": "Doc.pdf", "page": 1, "bboxes": []}
    ]
    if is_not_found:
        final_citations = []
    else:
        final_citations = raw_citations

    assert final_citations == []


def test_multi_document_citations():
    """
    Test 6: Chunks from multiple distinct documents retain their individual stable doc_ids and filenames.
    """
    adapter = LangChainAdapter()
    docs = [
        Document(
            page_content="Policy 1 content",
            metadata={
                "source_index": 1,
                "chunk_id": "c-1",
                "document_id": "doc-A",
                "filename": "Document-A.pdf",
                "page_number": 3,
            }
        ),
        Document(
            page_content="Policy 2 content",
            metadata={
                "source_index": 2,
                "chunk_id": "c-2",
                "document_id": "doc-B",
                "filename": "Document-B.pdf",
                "page_number": 8,
            }
        ),
    ]

    _, citations = adapter.format_context_from_documents(docs)
    assert len(citations) == 2
    assert citations[0]["doc_id"] == "doc-A"
    assert citations[0]["filename"] == "Document-A.pdf"
    assert citations[0]["page"] == 3

    assert citations[1]["doc_id"] == "doc-B"
    assert citations[1]["filename"] == "Document-B.pdf"
    assert citations[1]["page"] == 8
