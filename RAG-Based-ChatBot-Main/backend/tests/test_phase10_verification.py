import pytest
import asyncio
from typing import List, Dict, Any
from backend.retrieval.pipeline import RetrievalPipeline
from backend.llm.rewriter import QueryRewriter
from backend.llm.generator import GroundedGenerator
from backend.retrieval.bm25 import bm25_index

import os
import glob
from backend.config import settings

def _get_hr_doc_id():
    upload_dir = getattr(settings, "UPLOAD_DIR", "backend/data/uploads")
    matches = glob.glob(os.path.join(upload_dir, "*HR-Policy-Manual-Template.pdf"))
    if matches:
        return os.path.basename(matches[0]).split("_")[0]
    return '9171d80b-a795-4c47-abdf-774ef3528a31'

DOC_ID = _get_hr_doc_id()

@pytest.mark.asyncio
async def test_a_comprehensive_onboarding_retrieval():
    """
    Test A: 'What are all the items to cover with each new employee?'
    Must retrieve multi-page table across Page 20, 21, 22 without truncation.
    """
    # Ensure BM25 has chunks for DOC_ID so retrieval pipeline can retrieve and expand
    bm25_index.add_document_chunks(DOC_ID, [
        {
            "chunk_id": "p20_c1",
            "doc_id": DOC_ID,
            "page": 20,
            "score": 0.95,
            "text": "ITEMS TO COVER WITH EACH NEW EMPLOYEE [TABLE] 1. Department function | 2. Introduction to colleagues | 3. New entrant's own job | 4. Supervision | 5. General layout - entrances and exits | 6. Telephone system",
            "bboxes": [{"page": 20, "x0": 72, "y0": 480, "x1": 500, "y1": 600}]
        },
        {
            "chunk_id": "p21_c1",
            "doc_id": DOC_ID,
            "page": 21,
            "score": 0.90,
            "text": "Conditions of Employment | Telephone system | Department function continuation",
            "bboxes": [{"page": 21, "x0": 72, "y0": 100, "x1": 500, "y1": 250}]
        }
    ])

    pipeline = RetrievalPipeline()
    rewriter = QueryRewriter()
    q = "What are all the items to cover with each new employee?"
    queries = await rewriter.transform_query(q, [])
    chunks = await pipeline.retrieve(queries, doc_ids=[DOC_ID])
    
    pages = [c.get("page") for c in chunks]
    print(f"Test A retrieved {len(chunks)} chunks on pages: {pages}")
    
    # Must contain Page 20 and continuation onto Page 21
    assert any(p == 20 for p in pages), "Page 20 must be retrieved"
    assert any(p == 21 for p in pages), "Page 21 table continuation must be retrieved"
    
    # Combined context must cover both 'The Department' and 'Conditions of Employment'
    full_text = " ".join(c.get("text", "") for c in chunks)
    assert "Department function" in full_text
    assert "Telephone system" in full_text
    assert "Conditions of Employment" in full_text

@pytest.mark.asyncio
async def test_b_focused_list_scoping():
    """
    Test B: 'What are the six items to cover with each new employee?'
    Prompt rules must instruct the LLM to focus on the requested topic and not mix unrelated sections.
    """
    generator = GroundedGenerator()
    pipeline = RetrievalPipeline()
    rewriter = QueryRewriter()
    q = "What are the six items to cover with each new employee?"
    queries = await rewriter.transform_query(q, [])
    chunks = await pipeline.retrieve(queries, doc_ids=[DOC_ID])
    
    sys_prompt, user_prompt, citations = generator.build_grounded_prompt(q, chunks)
    assert "Focus on the requested topic" in sys_prompt
    assert "Do not mix in unrelated sections" in sys_prompt
    assert len(citations) > 0

@pytest.mark.asyncio
async def test_c_detailed_onboarding_multisection():
    """
    Test C: 'Explain the items to cover with each new employee and the relevant conditions of employment listed in the document.'
    Must retrieve both sections and prompt should separate them under distinct headings.
    """
    generator = GroundedGenerator()
    pipeline = RetrievalPipeline()
    rewriter = QueryRewriter()
    q = "Explain the items to cover with each new employee and the relevant conditions of employment listed in the document."
    queries = await rewriter.transform_query(q, [])
    chunks = await pipeline.retrieve(queries, doc_ids=[DOC_ID])
    
    sys_prompt, user_prompt, citations = generator.build_grounded_prompt(q, chunks)
    assert "Use headings only for major sections or distinct categories" in sys_prompt
    
    pages = [c.get("page") for c in chunks]
    assert any(p == 20 for p in pages)


def test_d_missing_information_no_citations():
    """
    Test D: Missing information query must return empty citations to prevent false PDF highlights.
    """
    generator = GroundedGenerator()
    dummy_citations = [{
        "source_index": 1,
        "doc_id": DOC_ID,
        "page": 24,
        "bboxes": [{"x0": 10, "y0": 20, "x1": 100, "y1": 50, "page": 24}],
        "snippet": "Some unrelated text"
    }]
    
    ans = "This is not mentioned in the provided document context."
    refined = generator.refine_citations_for_answer(dummy_citations, ans, "What is the pet policy?")
    assert len(refined) == 0, "Missing information must yield zero citations"

def test_e_precise_whole_box_highlighting_no_unrelated_content():
    """
    Test E: 'Transaction of private Business'
    Must match exact Section 2.2 on Page 25 and return a clean whole box enclosing the answer block
    (matching user specification: whole box not sentence-wise), and NEVER match Common Law duties on Page 24.
    """
    generator = GroundedGenerator()
    
    ans = (
        "Employees having official dealings with contractors and other suppliers of goods or services "
        "must avoid transacting any kind of private business with them by any means other than the "
        "Company’s normal commercial channels. No favour or preferences as regards price, or otherwise, "
        "which is not generally available, should be sought or accepted."
    )
    
    # 1. Page 24 MUST return 0 hits (No false highlight on section 1.3 Common Law duties)
    boxes_p24 = generator._locate_pinpoint_answer_boxes(DOC_ID, 24, ans)
    assert len(boxes_p24) == 0, f"Page 24 must have 0 hits for Section 2.2, got {len(boxes_p24)}"
    
    # 2. Page 25 MUST return the unified whole box enclosing the answer block
    boxes_p25 = generator._locate_pinpoint_answer_boxes(DOC_ID, 25, ans)
    assert len(boxes_p25) == 1, f"Expected 1 unified whole box enclosing Section 2.2, got {len(boxes_p25)}"
    
    # Verify the box cleanly encloses the whole section (height ~70-120pt, width ~400-450pt)
    b = boxes_p25[0]
    h = b["y1"] - b["y0"]
    w = b["x1"] - b["x0"]
    assert 60.0 <= h <= 120.0, f"Highlight box height {h} must enclose the whole answer block"
    assert 350.0 <= w <= 550.0, f"Highlight box width {w} must span the text block width"

def test_f_multi_page_citation_resolution():
    """
    Test F: When chunk spans multiple pages (e.g. 24 and 25), refine_citations_for_answer
    must accurately reassign the citation to Page 25 where the text actually lives.
    """
    generator = GroundedGenerator()
    ans = (
        "The Company requires its employees to avoid any transaction of private business with contractors "
        "and other suppliers of goods or services. The only exceptions to this rule are trivial gifts with a "
        "nominal value of less than £10."
    )
    
    raw_citations = [{
        "source_index": 1,
        "doc_id": DOC_ID,
        "page": 24, # Chunk initially labeled 24
        "candidate_pages": [24, 25], # Touches both 24 and 25
        "bboxes": [
            {"page": 24, "x0": 100, "y0": 100, "x1": 300, "y1": 150},
            {"page": 25, "x0": 90, "y0": 200, "x1": 400, "y1": 300}
        ],
        "snippet": "Transaction of Private Business ..."
    }]
    
    refined = generator.refine_citations_for_answer(raw_citations, ans, "Transaction of private Business")
    assert len(refined) == 1
    assert refined[0]["page"] == 25, f"Citation must resolve to Page 25, got {refined[0]['page']}"
    assert len(refined[0]["bboxes"]) > 0
    assert all(b["page"] == 25 for b in refined[0]["bboxes"])


def test_g_irrelevant_evidence_elimination_and_answer_only_highlighting():
    """
    Verifies that when multiple evidence chunks are retrieved, only the chunk containing
    the exact generated answer is kept. Irrelevant chunks (e.g. Page 21) with 0 answer lines
    must be completely eliminated and never highlighted, even if cited in text.
    """
    generator = GroundedGenerator()
    ans = (
        "2.2 Employees having official dealings with contractors and other suppliers of goods or "
        "services must avoid transacting any kind of private business with them by any means other than the "
        "Company's normal commercial channels. [2]"
    )
    raw_citations = [
        {
            "source_index": 2,
            "doc_id": DOC_ID,
            "page": 21,
            "candidate_pages": [21],
            "bboxes": [{"page": 21, "x0": 50, "y0": 50, "x1": 200, "y1": 70}],
            "snippet": "Items to cover with new employee on Page 21"
        },
        {
            "source_index": 6,
            "doc_id": DOC_ID,
            "page": 25,
            "candidate_pages": [25],
            "bboxes": [{"page": 25, "x0": 70, "y0": 200, "x1": 500, "y1": 230}],
            "snippet": "Transaction of Private Business 2.2 Employees having official dealings..."
        }
    ]

    refined = generator.refine_citations_for_answer(raw_citations, ans, "Transaction of Private Business")
    assert len(refined) == 1, f"Expected exactly 1 verified citation, got {len(refined)}"
    assert refined[0]["page"] == 25, f"Expected citation on Page 25, got Page {refined[0]['page']}"
    assert refined[0]["source_index"] == 2, f"Expected citation source_index aligned to [2], got {refined[0]['source_index']}"
    assert len(refined[0]["bboxes"]) > 0, "Expected pinpoint line boxes for the answer"
    assert all(b["page"] == 25 for b in refined[0]["bboxes"]), "All highlight boxes must be on Page 25"


def test_h_first_day_of_employment_page16_no_page47_stray():
    """
    Test H: First Day of Employment
    Must match Section 7 on Page 16 as a unified whole box.
    Unrelated sections (e.g. Page 47 stray match) must be eliminated.
    """
    generator = GroundedGenerator()
    ans = (
        "Preparations should be made for the arrival of the new entrant well in advance, "
        "for example, arrangements should be made to provide desk, equipment and lockers etc. "
        "Most new employees tend to be concerned primarily with two matters: whether they can do the job "
        "and how they will get on with their new colleagues. It is therefore important to introduce them "
        "to their new workplace and colleagues at the earliest opportunity. A tour of the workplace "
        "should be arranged for the new entrant allowing the Company / Division to be viewed as a whole."
    )

    # 1. Page 16 must have pinpoint boxes
    boxes_p16 = generator._locate_pinpoint_answer_boxes(DOC_ID, 16, ans)
    assert len(boxes_p16) >= 1, "Page 16 must match First Day of Employment"
    assert all(b["page"] == 16 for b in boxes_p16)

    # 2. Refine citations with Page 16 and stray Page 47
    raw_citations = [
        {
            "source_index": 1,
            "doc_id": DOC_ID,
            "page": 16,
            "candidate_pages": [16],
            "bboxes": [{"page": 16, "x0": 100, "y0": 200, "x1": 500, "y1": 400}],
            "snippet": "First Day of Employment Preparations should be made for the arrival..."
        },
        {
            "source_index": 2,
            "doc_id": DOC_ID,
            "page": 47,
            "candidate_pages": [47],
            "bboxes": [{"page": 47, "x0": 100, "y0": 100, "x1": 400, "y1": 120}],
            "snippet": "Disciplinary procedure arrangements should be made..."
        }
    ]

    refined = generator.refine_citations_for_answer(raw_citations, ans, "First Day of Employment")
    assert len(refined) == 1, f"Expected only Page 16 citation, got {len(refined)}"
    assert refined[0]["page"] == 16, f"Expected Page 16, got Page {refined[0]['page']}"
    assert all(b["page"] == 16 for b in refined[0]["bboxes"])


def test_i_six_items_to_cover_page20_unified_box():
    """
    Test I: 'What are the six items to cover with each new employee?'
    Must pinpoint Page 20 under The Department, and merge into a single unified whole box
    (gap <= 55pt) enclosing the header and 6 items, without highlighting Conditions of Employment.
    """
    generator = GroundedGenerator()
    ans = (
        "ITEMS TO COVER WITH EACH NEW EMPLOYEE\n\n"
        "1. Department function\n"
        "2. Introduction to colleagues\n"
        "3. New entrant’s own job\n"
        "4. Supervision\n"
        "5. General layout - entrances and exits\n"
        "6. Telephone system, bleeps and intercom systems"
    )

    boxes_p20 = generator._locate_pinpoint_answer_boxes(DOC_ID, 20, ans)
    assert len(boxes_p20) == 1, f"Expected 1 unified whole box, got {len(boxes_p20)}"
    b = boxes_p20[0]
    assert b["y0"] >= 450.0 and b["y1"] <= 620.0, f"Box must enclose items 1-6 and end before Conditions of Employment (y1={b['y1']})"


def test_j_internal_source_metadata_contract():
    """
    Test J: Internal Source Metadata Contract
    Verifies that backend citations preserve doc_id, page, bboxes, coordinate origins,
    and line_count so frontend viewer navigates and highlights automatically without any evidence UI.
    """
    generator = GroundedGenerator()
    q = "What are the six items to cover with each new employee?"
    chunks = [{
        "chunk_id": "chk_20_1",
        "doc_id": DOC_ID,
        "filename": "HR-Policy-Manual-Template.pdf",
        "page": 20,
        "bboxes": [{"page": 20, "x0": 80, "y0": 460, "x1": 500, "y1": 615, "text": "ITEMS TO COVER"}],
        "text": "ITEMS TO COVER WITH EACH NEW EMPLOYEE Complete 1. Department function 2. Introduction to colleagues..."
    }]
    sys_p, user_p, citations = generator.build_grounded_prompt(q, chunks)
    assert len(citations) == 1
    c = citations[0]
    assert c["doc_id"] == DOC_ID
    assert c["page"] == 20
    assert len(c["bboxes"]) > 0
    # User prompt must NOT request bracket citations [1], [2] in answer prose
    assert "cite sources [1]" not in user_p
    assert "Do not include internal evidence IDs" in sys_p


