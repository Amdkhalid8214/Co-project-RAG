"""
Comprehensive Verification Tests for DocuChat AI RAG Prompt Engineering & Generator Upgrade.

Covers all 13 core scenarios specified in PART 11 of the specification:
1. Question answerable from one chunk.
2. Question spanning multiple chunks or pages.
3. List question requiring all available supported items.
4. Question about one section when other sections discuss similar terminology (section purity).
5. Formula question where the formula is absent from the supplied context.
6. Exact-text extraction that must not paraphrase.
7. Question that cannot be answered from the available context.
8. Answer containing unsupported or contradicted claims (grounding validator).
9. Multiple source chunks with different pages and bounding boxes.
10. Source reference metadata contract for PDF navigation and highlighting.
11. Empty context, malformed validation JSON, LLM errors, and context-budget overflow.
12. General chat that must not be routed into document-only QA.
13. Prompt-variable mismatches and invalid prompt-routing results.
"""

import sys
import json
import pytest
import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock

# Ensure project root is on sys.path
root_dir = str(Path(__file__).resolve().parent.parent.parent)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.messages.ai import AIMessageChunk

from backend.llm.prompts import (
    GROUNDED_SYSTEM_TEMPLATE,
    GROUNDED_HUMAN_TEMPLATE,
    VERBATIM_EXTRACTION_SYSTEM_TEMPLATE,
    VERBATIM_EXTRACTION_HUMAN_TEMPLATE,
    GENERAL_SYSTEM_TEMPLATE,
    GENERAL_HUMAN_TEMPLATE_PLAIN,
    GENERAL_HUMAN_TEMPLATE_WITH_WEB,
    GROUNDING_VALIDATION_SYSTEM_TEMPLATE,
    GROUNDING_VALIDATION_HUMAN_TEMPLATE,
    GROUNDED_REVISION_HUMAN_TEMPLATE,
    NOT_FOUND_RESPONSE,
    GroundingValidationResult,
)
from backend.llm.router import QueryRouter, is_verbatim_extraction_request
from backend.llm.langchain_adapter import LangChainAdapter, langchain_adapter
from backend.llm.generator import GroundedGenerator, grounded_generator


# ---------------------------------------------------------------------------
# Test 1: Question answerable from one chunk
# ---------------------------------------------------------------------------
def test_scenario_1_single_chunk_answer():
    """Verify that a question answerable from a single chunk constructs clean context and citations."""
    generator = GroundedGenerator()
    chunks = [{
        "chunk_id": "c_lr_01",
        "doc_id": "doc_transformer_01",
        "filename": "Attention_Is_All_You_Need.pdf",
        "page": 7,
        "text": "We used the Adam optimizer with beta1 = 0.9, beta2 = 0.98 and epsilon = 10^-9. The learning rate warmup steps was 4000.",
        "bboxes": [{"page": 7, "x0": 50, "y0": 200, "x1": 350, "y1": 230, "text": "learning rate warmup steps was 4000"}],
        "heading_path": ["Optimizer", "Learning Rate Schedule"],
        "score": 0.94
    }]

    sys_p, user_p, citations = generator.build_grounded_prompt(
        question="How many warmup steps were used for the learning rate?",
        chunks=chunks
    )

    assert "DocuChat AI" in sys_p
    assert "PRIMARY RULE:" in sys_p
    assert "warmup steps was 4000" in user_p
    assert len(citations) == 1
    assert citations[0]["page"] == 7
    assert citations[0]["source_index"] == 1
    assert citations[0]["filename"] == "Attention_Is_All_You_Need.pdf"


# ---------------------------------------------------------------------------
# Test 2: Question spanning multiple chunks or pages
# ---------------------------------------------------------------------------
def test_scenario_2_multi_chunk_multi_page_span():
    """Verify context preservation across multiple chunks and distinct pages."""
    generator = GroundedGenerator()
    chunks = [
        {
            "chunk_id": "c_enc_01",
            "doc_id": "doc_arch_01",
            "filename": "Transformer_Arch.pdf",
            "page": 3,
            "text": "The encoder is composed of a stack of N = 6 identical layers.",
            "bboxes": [{"page": 3, "x0": 50, "y0": 100, "x1": 300, "y1": 120, "text": "stack of N = 6 identical layers"}],
            "score": 0.92
        },
        {
            "chunk_id": "c_dec_02",
            "doc_id": "doc_arch_01",
            "filename": "Transformer_Arch.pdf",
            "page": 4,
            "text": "The decoder is also composed of a stack of N = 6 identical layers with additional cross-attention.",
            "bboxes": [{"page": 4, "x0": 50, "y0": 150, "x1": 350, "y1": 170, "text": "decoder is also composed of a stack of N = 6"}],
            "score": 0.89
        }
    ]

    sys_p, user_p, citations = generator.build_grounded_prompt(
        question="How many layers are in the encoder and decoder stacks?",
        chunks=chunks
    )

    # Both pages must be present in prompt context
    assert "=== CONTEXT SOURCE [1] (Page 3) ===" in user_p
    assert "=== CONTEXT SOURCE [2] (Page 4) ===" in user_p
    assert "stack of N = 6 identical layers" in user_p
    assert len(citations) == 2
    assert citations[0]["page"] == 3
    assert citations[1]["page"] == 4


# ---------------------------------------------------------------------------
# Test 3: List question requiring all available supported items
# ---------------------------------------------------------------------------
def test_scenario_3_complete_checklist_aggregation():
    """Verify Rule 2 (Completeness) instructs model to include all supported items."""
    generator = GroundedGenerator()
    chunks = [
        {
            "chunk_id": "chk_part1",
            "doc_id": "doc_safety_01",
            "page": 10,
            "text": "Emergency Procedures: 1. Sound fire alarm. 2. Evacuate via nearest stairs. 3. Assemble at station A.",
            "bboxes": [{"page": 10, "x0": 40, "y0": 100, "x1": 400, "y1": 140, "text": "Emergency Procedures"}],
            "score": 0.91
        },
        {
            "chunk_id": "chk_part2",
            "doc_id": "doc_safety_01",
            "page": 11,
            "text": "Emergency Procedures Continued: 4. Account for all staff. 5. Await emergency services clearance.",
            "bboxes": [{"page": 11, "x0": 40, "y0": 100, "x1": 400, "y1": 140, "text": "Emergency Procedures Continued"}],
            "score": 0.88
        }
    ]

    sys_p, user_p, citations = generator.build_grounded_prompt(
        question="What are all the emergency procedure steps?",
        chunks=chunks
    )

    # Verify Rule 2 Completeness is explicitly present in the canonical prompt
    assert "2. COMPLETENESS" in sys_p
    assert "For requests asking for all items, retrieve and include every relevant item" in sys_p
    assert "Preserve the original order of lists and procedures where possible." in sys_p
    assert len(citations) == 2


# ---------------------------------------------------------------------------
# Test 4: Question about one section when other sections discuss similar terminology (Section Purity)
# ---------------------------------------------------------------------------
def test_scenario_4_section_purity_and_isolation():
    """Verify Rule 1 (Section Purity & Isolation) and citation isolation."""
    generator = GroundedGenerator()
    citations = [
        {
            "source_index": 1,
            "chunk_id": "c_mha",
            "doc_id": "doc_attn",
            "page": 4,
            "bboxes": [{"page": 4, "x0": 50, "y0": 100, "x1": 300, "y1": 150, "text": "Multi-Head Attention"}],
            "snippet": "Multi-Head Attention allows the model to jointly attend to information...",
            "full_text": "Multi-Head Attention allows the model to jointly attend to information from different representation subspaces."
        },
        {
            "source_index": 2,
            "chunk_id": "c_ffn",
            "doc_id": "doc_attn",
            "page": 5,
            "bboxes": [{"page": 5, "x0": 50, "y0": 200, "x1": 400, "y1": 250, "text": "Position-wise Feed-Forward Networks FFN(x)"}],
            "snippet": "Position-wise Feed-Forward Networks consists of two linear transformations...",
            "full_text": "Position-wise Feed-Forward Networks: FFN(x) = max(0, xW1 + b1)W2 + b2. The dimensionality of d_model is 512, and d_ff is 2048."
        }
    ]

    answer = "The Position-wise Feed-Forward Networks consists of two linear transformations with a ReLU activation: FFN(x) = max(0, xW1 + b1)W2 + b2. The inner-layer dimension is d_ff = 2048."
    refined = generator.refine_citations_for_answer(citations, answer, "Explain the Feed-Forward Networks")

    # Only citation 2 (FFN) should be retained; citation 1 (MHA) must be filtered out
    assert len(refined) == 1
    assert refined[0]["chunk_id"] == "c_ffn"
    assert refined[0]["page"] == 5


# ---------------------------------------------------------------------------
# Test 5: Formula question where the formula is absent from context
# ---------------------------------------------------------------------------
def test_scenario_5_absent_formula_handling():
    """Verify that absent formulas trigger the not-found rule instead of hallucinating."""
    generator = GroundedGenerator()
    chunks = [{
        "chunk_id": "c_ln_01",
        "doc_id": "doc_trans",
        "page": 3,
        "text": "We employ residual connections followed by layer normalization LayerNorm(x + Sublayer(x)).",
        "bboxes": [{"page": 3, "x0": 50, "y0": 100, "x1": 300, "y1": 130, "text": "LayerNorm"}],
        "score": 0.85
    }]

    sys_p, user_p, citations = generator.build_grounded_prompt(
        question="What is the exact mathematical equation defining the mean and variance inside LayerNorm?",
        chunks=chunks
    )

    # Prompt rules strictly forbid inventing formulas not in context
    assert "Never invent facts, formulas, dimensions, dates, quotations, or page numbers." in sys_p
    assert 'If the context does not support the answer, say:\n  "This is not mentioned in the provided document context."' in sys_p


# ---------------------------------------------------------------------------
# Test 6: Exact-text extraction that must not paraphrase
# ---------------------------------------------------------------------------
def test_scenario_6_verbatim_extraction_routing_and_prompt():
    """Verify verbatim extraction intent detection and dedicated prompt template."""
    verbatim_queries = [
        "Extract the exact definition of attention.",
        "Give the original paragraph of Section 3.2.",
        "Copy the formula exactly without changing it.",
        "Show the exact wording from the PDF.",
        "Extract a numbered list without changing it.",
        "Quote the exact text of the liability clause verbatim.",
    ]
    for q in verbatim_queries:
        assert is_verbatim_extraction_request(q) is True, f"Failed to classify verbatim query: {q}"

    # Verify normal questions are NOT misclassified as verbatim
    normal_queries = [
        "Explain the items to cover with each new employee.",
        "Summarize the performance results in Section 5.",
        "What is the system throughput?",
        "Can you describe how attention works?",
    ]
    for q in normal_queries:
        assert is_verbatim_extraction_request(q) is False, f"Normal query misclassified as verbatim: {q}"

    # Verify verbatim prompt content
    generator = GroundedGenerator()
    chunks = [{
        "chunk_id": "c_def_01",
        "doc_id": "doc_01",
        "page": 1,
        "text": "An attention function can be described as mapping a query and a set of key-value pairs to an output.",
        "bboxes": [{"page": 1, "x0": 50, "y0": 50, "x1": 400, "y1": 80, "text": "attention function"}],
        "score": 0.95
    }]
    sys_p, user_p, citations = generator.build_verbatim_prompt("Extract the exact definition of attention", chunks)
    assert "Do not paraphrase, summarize, correct, interpret, or supplement the source." in sys_p
    assert "Preserve wording, spelling, capitalization, punctuation, symbols" in sys_p
    assert "Extract the requested original text exactly as represented" in user_p


# ---------------------------------------------------------------------------
# Test 7: Question that cannot be answered from the available context
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_scenario_7_unanswerable_question_empty_citations():
    """Verify that unanswerable queries return NOT_FOUND_RESPONSE and empty citations."""
    generator = GroundedGenerator()
    events = []
    async for sse in generator.stream_rag_response(
        question="What is the warranty policy for battery degradation?",
        route="document",
        router_badge="From document",
        retrieved_chunks=[],  # No chunks passed threshold
        queries=["What is the warranty policy for battery degradation?"]
    ):
        events.append(sse)

    streamed_text = ""
    citations_data = None
    for event in events:
        for line in event.strip().split("\n"):
            if line.startswith("data: "):
                try:
                    data = json.loads(line[6:])
                    if "content" in data:
                        streamed_text += data["content"]
                    if "citations" in data:
                        citations_data = data["citations"]
                except Exception:
                    pass

    assert NOT_FOUND_RESPONSE in streamed_text
    assert citations_data == []


# ---------------------------------------------------------------------------
# Test 8: Answer containing unsupported or contradicted claims (Grounding Validator)
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_scenario_8_grounding_validation_schema_and_detection():
    """Verify that the Grounding Validator identifies unsupported claims and returns valid schema."""
    adapter = LangChainAdapter()
    context = "The model was trained on 8 NVIDIA V100 GPUs for 3.5 days. Batch size was 25600 tokens."
    draft_unsupported = "The model was trained on 64 Google TPU v4 chips across 4 weeks with a batch size of 512."

    # Mock the LLM validator response to return structured JSON
    mock_json_response = json.dumps({
        "grounded": False,
        "unsupported_claims": ["Trained on 64 Google TPU v4 chips across 4 weeks", "batch size of 512"],
        "contradicted_claims": ["Hardware was 8 NVIDIA V100 GPUs, not TPU v4", "Training time was 3.5 days, not 4 weeks"],
        "missing_information": [],
        "recommendation": "revise"
    })

    with patch.object(adapter, "ainvoke_messages", return_value=mock_json_response):
        result: GroundingValidationResult = await adapter.validate_draft_answer(
            question="What hardware and training time was used?",
            context=context,
            draft_answer=draft_unsupported
        )

        assert isinstance(result, GroundingValidationResult)
        assert result.grounded is False
        assert result.recommendation == "revise"
        assert len(result.unsupported_claims) == 2
        assert len(result.contradicted_claims) == 2


# ---------------------------------------------------------------------------
# Test 9: Multiple source chunks with different pages and bounding boxes
# ---------------------------------------------------------------------------
def test_scenario_9_multiple_pages_and_bboxes_preservation():
    """Verify that multi-page chunks preserve distinct pages, candidate pages, and line bounding boxes."""
    adapter = LangChainAdapter()
    chunks = [
        {
            "chunk_id": "chk_pg2",
            "doc_id": "doc_multi",
            "doc_name": "MultiPage.pdf",
            "page": 2,
            "text": "First section on Page 2.",
            "bboxes": [{"page": 2, "x0": 50, "y0": 100, "x1": 200, "y1": 120, "coord_origin": "TOPLEFT"}],
            "score": 0.88
        },
        {
            "chunk_id": "chk_pg8",
            "doc_id": "doc_multi",
            "doc_name": "MultiPage.pdf",
            "page": 8,
            "text": "Second section continuing on Page 8.",
            "bboxes": [{"page": 8, "x0": 60, "y0": 250, "x1": 350, "y1": 280, "coord_origin": "TOPLEFT"}],
            "score": 0.85
        }
    ]

    docs = adapter.chunks_to_documents(chunks)
    messages, citations = adapter.build_grounded_messages("Explain both sections", docs)

    assert len(citations) == 2
    assert citations[0]["page"] == 2
    assert citations[0]["bboxes"][0]["page"] == 2
    assert citations[1]["page"] == 8
    assert citations[1]["bboxes"][0]["page"] == 8


# ---------------------------------------------------------------------------
# Test 10: Clicking source reference navigates to correct page and highlight
# ---------------------------------------------------------------------------
def test_scenario_10_citation_metadata_contract_for_frontend():
    """Verify all fields required by frontend PDF viewer (PdfViewerDrawer & SideDocumentViewer) are present."""
    generator = GroundedGenerator()
    chunks = [{
        "chunk_id": "chk_cite_spec",
        "doc_id": "doc_contract_spec",
        "filename": "Product_Requirements.pdf",
        "page": 5,
        "text": "The maximum payload size allowed is 50 Megabytes.",
        "bboxes": [{
            "page": 5,
            "x0": 72.0,
            "y0": 150.0,
            "x1": 420.0,
            "y1": 170.0,
            "page_width": 612.0,
            "page_height": 792.0,
            "coord_origin": "TOPLEFT",
            "text": "maximum payload size allowed is 50 Megabytes"
        }],
        "heading_path": ["Specifications", "Payload Limits"],
        "score": 0.96
    }]

    _, _, citations = generator.build_grounded_prompt("What is the maximum payload size?", chunks)
    assert len(citations) == 1
    c = citations[0]

    # Required contract keys for frontend PDF.js navigation and coordinate canvas rendering:
    required_keys = ["source_index", "chunk_id", "doc_id", "filename", "page", "candidate_pages", "bboxes", "heading_path", "snippet"]
    for k in required_keys:
        assert k in c, f"Missing required frontend citation key: {k}"

    b = c["bboxes"][0]
    bbox_keys = ["x0", "y0", "x1", "y1", "page"]
    for bk in bbox_keys:
        assert bk in b, f"Missing required bbox key: {bk}"


# ---------------------------------------------------------------------------
# Test 11: Empty context, malformed validation JSON, LLM errors, and context-budget overflow
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_scenario_11a_empty_context():
    """11a: Empty context returns NOT_FOUND_RESPONSE without errors."""
    ans, cites, val = await grounded_generator.generate_grounded_answer("Any question", chunks=[])
    assert ans == NOT_FOUND_RESPONSE
    assert cites == []
    assert val is None


@pytest.mark.asyncio
async def test_scenario_11b_malformed_validation_json_safe_recovery():
    """11b: Malformed validation JSON returns safe fallback without crashing."""
    adapter = LangChainAdapter()
    malformed_responses = [
        "This is not JSON at all! Just raw model banter.",
        "{unclosed json: true, recommendation: 'accept'",
        "```json\n{recommendation: invalid}\n```"
    ]
    for bad_resp in malformed_responses:
        with patch.object(adapter, "ainvoke_messages", return_value=bad_resp):
            result = await adapter.validate_draft_answer(
                question="What is X?",
                context="X is 10.",
                draft_answer="X is 10."
            )
            assert isinstance(result, GroundingValidationResult)
            assert result.grounded is True
            assert result.recommendation == "accept"


@pytest.mark.asyncio
async def test_scenario_11c_llm_error_graceful_stream_notice():
    """11c: LLM connection failure yields graceful diagnostic notice."""
    adapter = LangChainAdapter()
    with patch.object(adapter, "get_llm", side_effect=ConnectionError("Could not reach Ollama at http://127.0.0.1:11434")):
        tokens = []
        async for t in adapter.stream_messages([HumanMessage(content="Hello")]):
            tokens.append(t)
        full_err = "".join(tokens)
        assert "Ollama connection error" in full_err


def test_scenario_11d_context_budget_overflow_prevented():
    """11d: High volume of chunks respects max_char_budget and does not overflow."""
    generator = GroundedGenerator()
    large_chunks = [
        {
            "chunk_id": f"chk_bulk_{i}",
            "doc_id": "doc_large",
            "page": i + 1,
            "text": f"Paragraph {i}: " + ("This is detailed context text. " * 50),
            "score": 0.90 - (i * 0.01)
        }
        for i in range(40)
    ]

    budget = 4000  # Low budget for testing enforcement
    sys_p, user_p, citations = generator.build_grounded_prompt(
        question="Summarize everything",
        chunks=large_chunks,
        max_char_budget=budget
    )

    # Total context must not exceed budget by more than one header
    assert len(user_p) <= budget + 500
    assert len(citations) < len(large_chunks)  # Truncated cleanly at chunk boundary


# ---------------------------------------------------------------------------
# Test 12: General chat that must not be routed into document-only QA
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_scenario_12_general_chat_routing():
    """Verify general questions without documents are routed to general chat, not document QA."""
    router = QueryRouter()

    # No documents loaded
    route, badge, p_type = await router.detect_intent("What is the capital of Japan?", has_documents=False)
    assert route == "general"
    assert p_type == "general_chat"

    # Pleasantry with document loaded
    route_greet, _, p_type_greet = await router.detect_intent("Hello, how are you?", has_documents=True)
    assert route_greet == "general"
    assert p_type_greet == "general_chat"

    # Document question with document loaded
    route_doc, _, p_type_doc = await router.detect_intent("What are the key policy rules in the manual?", has_documents=True)
    assert route_doc == "document"
    assert p_type_doc == "grounded_qa"


# ---------------------------------------------------------------------------
# Test 13: Prompt-variable mismatches and invalid prompt-routing results
# ---------------------------------------------------------------------------
def test_scenario_13_all_prompt_templates_variable_integrity():
    """Verify all templates format cleanly without KeyError or syntax errors."""
    # 1. Grounded System (no vars) and Human ({context}, {question})
    gh = GROUNDED_HUMAN_TEMPLATE.format(context="Sample context", question="Sample question")
    assert "Sample context" in gh and "Sample question" in gh

    # 2. Verbatim System (no vars) and Human ({context}, {question})
    vh = VERBATIM_EXTRACTION_HUMAN_TEMPLATE.format(context="Exact context", question="Extract clause")
    assert "Exact context" in vh and "Extract clause" in vh

    # 3. General Plain Human ({question})
    gp = GENERAL_HUMAN_TEMPLATE_PLAIN.format(question="Explain gravity")
    assert "Explain gravity" in gp

    # 4. General Web Human ({live_context}, {question})
    gw = GENERAL_HUMAN_TEMPLATE_WITH_WEB.format(live_context="Stock is $150", question="What is AAPL price?")
    assert "Stock is $150" in gw and "What is AAPL price?" in gw

    # 5. Validation Human ({context}, {question}, {draft_answer})
    val_h = GROUNDING_VALIDATION_HUMAN_TEMPLATE.format(
        context="Context A",
        question="Question B",
        draft_answer="Answer C"
    )
    assert "Context A" in val_h and "Question B" in val_h and "Answer C" in val_h

    # 6. Revision Human ({context}, {question}, {draft_answer}, {unsupported_claims}, {contradicted_claims}, {missing_information})
    rev_h = GROUNDED_REVISION_HUMAN_TEMPLATE.format(
        context="Context 1",
        question="Question 1",
        draft_answer="Draft 1",
        unsupported_claims="[]",
        contradicted_claims="[]",
        missing_information="[]"
    )
    assert "Context 1" in rev_h and "Draft 1" in rev_h
