# DocuChat AI — Implementation Audit & Baseline Assessment Report
**Document Version:** 1.0.0 &bull; **Audit Date:** October 2026 &bull; **Auditor:** Senior AI & RAG Engineering Team

---

## Executive Summary

An exhaustive code-level audit was conducted across the entire **DocuChat AI** repository (`RAG-Based-ChatBot-Main`), covering API controllers, ingestion workers, chunking logic, vector database drivers, sparse BM25 indices, cross-encoder rerankers, LLM orchestrators, database models, frontend components, and security boundaries.

### Baseline Status Summary
* **Total Automated Unit/Integration Tests in Baseline:** 28 tests collected.
* **Baseline Test Pass Rate:** 28 / 28 passing (100%) after resolving standard library UUIDv7 fallback on Windows.
* **Core Strengths:** Resilient hybrid retrieval architecture (Vector + BM25Plus + RRF + Cross-Encoder Reranker), precision citation bounding-box refinement (`refine_citations_for_answer`), safe AST arithmetic sandboxing, and multi-tenant JWT auth.
* **Key Deficits Identified:** Missing conditional OCR routing for scanned/image-only PDFs (currently relies on PyMuPDF Tesseract binding which fails if local binaries are missing), lack of MIME magic byte verification for uploaded files, missing end-to-end evaluation harness comparing baseline retrieval recall against ground truth, and unhandled PDF zoom re-centering on canvas resize.

---

## 1. Implementation Classification Matrix

### Category 1: Implemented & Verified
*Features inspected in code and validated with passing automated tests or live verification.*

1. **Reciprocal Rank Fusion (RRF, $k=60$):**
   - Implemented in `backend/retrieval/fusion.py`.
   - Verified via `test_retrieval.py::test_reciprocal_rank_fusion` and `test_weighted_score_fusion`.
2. **Semantic Text Deduplication:**
   - Implemented in `backend/retrieval/dedup.py` using Jaccard word set similarity and character n-gram overlap ($> 0.88$).
   - Verified via `test_retrieval.py::test_deduplication`.
3. **Structure-Aware Chunking:**
   - Implemented in `backend/chunking/structure_chunker.py`. Enforces 400 token target, 450 max, 50 overlap. Preserves markdown section hierarchy (`# Title > ## Section`) and attaches raw sentence-level bounding boxes.
   - Verified via `test_retrieval.py::test_structure_chunking` and `test_master_verification.py::test_structure_chunker_token_limit`.
4. **Argon2id & PBKDF2-HMAC-SHA256 Password Security:**
   - Implemented in `backend/api/auth.py`. Uses Argon2id if available with transparent fallback to PBKDF2 (100,000 iterations).
   - Verified via `test_auth_tenancy.py::test_argon2_and_pbkdf2_hashing`.
5. **Multi-Tenant JWT Bearer Token Authentication:**
   - Implemented in `backend/api/auth.py`. Issues signed HS256 tokens with configurable 24-hour expiration (`ACCESS_TOKEN_EXPIRE_MINUTES`).
   - Verified via `test_auth_tenancy.py::test_jwt_token_creation_and_decoding`.
6. **Safe AST Calculator Tool:**
   - Implemented in `backend/tools/calculator.py`. Parses mathematical expressions using Python's `ast` module (binary operators, math functions) without executing `eval()`.
   - Verified via `test_auth_tenancy.py::test_safe_calculator_ast` and `test_master_verification.py::test_tools_api_and_calculator`.
7. **Excel Workbook Generation with Formula Injection Defense:**
   - Implemented in `backend/tools/excel_generator.py`. Generates styled `.xlsx` workbooks with `openpyxl`. Sanitizes cells starting with `=`, `+`, `-`, or `@` to neutralize CSV/Excel formula injection.
   - Verified via `test_auth_tenancy.py::test_excel_formula_injection_defense` and `test_excel_generation_produces_file`.
8. **Path-Traversal Protected Output Download:**
   - Implemented in `backend/api/tools.py`. Canonicalizes filenames and enforces strict boundary checks within `settings.OUTPUT_DIR` using `Path.resolve()`.
   - Verified via `test_master_verification.py::test_path_traversal_download_defense`.
9. **Dual Database Engine & Async Migration:**
   - Implemented in `backend/db/session.py` and `backend/db/migrate_sqlite_to_pg.py`. Supports PostgreSQL (asyncpg) with SQLite (aiosqlite) local fallback.
   - Verified via `test_master_verification.py::test_sqlite_to_target_migration_idempotent`.
10. **Strict Anti-Hallucination Prompting & Missing Context Refusal:**
    - Implemented in `backend/llm/generator.py` and `backend/llm/langchain_adapter.py`. Explicitly instructs model: *"If the requested information is absent or not explicitly discussed in the Context Sources... clearly state: 'This is not mentioned in the document.'"*
    - Verified via `test_qwen_7b_upgrade.py::test_insufficient_context_refusal_no_fabrication`.

---

### Category 2: Implemented but Not Adequately Tested
*Code is present in the repository but lacks dedicated automated unit test coverage.*

1. **Bidirectional WebSocket Protocol (`/ws/chat`):**
   - Present in `backend/api/websockets.py`.
   - Lacks an automated async WebSocket client integration test verifying mid-stream client cancellation.
2. **Live Document Ingestion WebSocket Progress (`/ws/documents/{doc_id}/progress`):**
   - Present in `backend/api/websockets.py` and `backend/workers/ingest_worker.py`.
   - Needs automated mock verification ensuring 15% -> 40% -> 65% -> 100% steps emit expected JSON packets.
3. **Multi-Query Expansion Pronoun Disambiguation:**
   - Present in `backend/llm/rewriter.py`.
   - Lacks regression test asserting that conversational pronouns (*"it"*, *"they"*, *"its"*) are correctly expanded into standalone entity names without hallucination.
4. **Live Web Knowledge Engine:**
   - Present in `backend/retrieval/web_search.py`.
   - Lacks automated mock testing for Yahoo Finance ticker retrieval, DuckDuckGo Lite parsing, and Wikipedia REST API fallbacks under network timeout conditions.

---

### Category 3: Partially Implemented
*Features that are partially completed but have architectural gaps.*

1. **Scanned PDF OCR Integration:**
   - **Current State:** `backend/parsers/docling_parser.py` has a stub method `_extract_scanned_page_ocr()` that only invokes PyMuPDF's `page.get_textpage_ocr()`. If Tesseract binaries are not on the host OS path, this fails silently, leaving scanned pages with empty or zero text.
   - **Gap:** No dedicated PaddleOCR integration, no intelligent digital vs scanned page classifier, and no bounding-box coordinate transformation from OCR pixel space to PDF canvas space.
2. **Retrieval Evaluation Suite:**
   - **Current State:** `backend/eval/retrieval_eval.py` exists as a basic skeleton script.
   - **Gap:** Lacks a version-controlled golden dataset of realistic document questions, ground-truth passage IDs, and benchmark calculations for HitRate@K and MRR@K.
3. **Asynchronous Ingestion Job Worker:**
   - **Current State:** `backend/workers/job_queue.py` enqueues jobs to Redis and `ingest_worker.py` contains the step-by-step processing logic.
   - **Gap:** Lacks automatic job recovery after worker restart (re-queueing zombie jobs stuck in `processing` state) and idempotent chunk deletion before re-indexing.

---

### Category 4: Missing
*Required production features that are not yet implemented.*

1. **Conditional Document-Processing Router:**
   - A dedicated parser router that classifies each incoming PDF page as either *Digital*, *Scanned*, or *Mixed*, routing digital pages to high-speed native extraction and scanned pages to PaddleOCR.
2. **PaddleOCR Model Engine:**
   - Standalone module encapsulating PaddleOCR / PP-OCR inference, model caching, CPU fallback, and bounding-box normalization.
3. **MIME Magic Byte Upload Validation:**
   - Currently, `backend/api/documents.py` validates file types only by file extension (`.pdf`, `.docx`, etc.). An uploaded malicious executable renamed to `.pdf` would pass validation.
4. **Zombie Job Sweeper & Retries:**
   - Mechanism to detect jobs that were interrupted when the backend crashed or restarted.

---

### Category 5: Broken or Inconsistent
*Issues causing operational defects or runtime errors.*

1. **Deprecation Warnings on UTC Timestamps:**
   - Multiple occurrences of `datetime.utcnow()` in `backend/api/auth.py` and `backend/db/models.py`. In Python 3.12+, `datetime.utcnow()` is deprecated and should be `datetime.now(timezone.utc)`.
2. **Qdrant Server Client-Server Compatibility Warning:**
   - `qdrant_client/qdrant_remote.py: UserWarning: Failed to obtain server version. Set check_compatibility=False to skip version check.` occurs when Qdrant server is offline or initializing.

---

### Category 6: Security Risks
*Security concerns evaluated against production standards.*

1. **File Type Spoofing:**
   - Validation by file extension alone allows uploading disguised payloads.
   - **Mitigation:** Inspect initial file magic bytes (`%PDF-`, `PK\x03\x04` for docx/xlsx, image headers).
2. **Cross-Tenant Vector Retrieval Leakage Risk:**
   - If a search query is dispatched without `doc_ids` filtering or without validating document ownership in `active_doc_ids`, chunks from other users could be retrieved in multi-tenant mode.
   - **Mitigation:** Enforce ownership validation in `api/chat.py` and `api/websockets.py` ensuring all queried `doc_ids` belong to the authenticated `user_id`.

---

## 2. Prioritized Master Upgrade Plan

### Phase 2: Critical Fixes & Security Hardening
- Implement magic byte MIME verification in `backend/api/documents.py`.
- Enforce strict tenant ownership verification for all active `doc_ids` before retrieval.
- Fix Python 3.12+ `datetime.utcnow()` deprecation warnings across all models.

### Phase 3: Document Processing & PaddleOCR Ingestion Upgrade (MANDATORY)
- Build `backend/parsers/paddle_ocr.py`: PaddleOCR / PP-OCRv4 engine supporting both native PaddleOCR and ONNX runtime, with CPU execution fallback.
- Build intelligent page-by-page conditional router: Digital pages &rarr; Native extraction (0 OCR overhead); Scanned pages &rarr; PaddleOCR; Mixed pages &rarr; Hybrid per-page extraction.
- Coordinate transformation: Map PaddleOCR bounding polygons into standard normalized PDF.js `x0, y0, x1, y1` (`TOPLEFT`) coordinates.
- Update `backend/workers/ingest_worker.py` to route through the new conditional extractor.

### Phase 4: RAG Quality, Evaluation & Grounding
- Expand `backend/eval/retrieval_eval.py` with golden question-answer pairs and benchmark Hit Rate@3, Hit Rate@5, and MRR.
- Verify embedding model consistency and dimension matching (768 vs 384).

### Phase 5: Reliability & Background Worker Hardening
- Implement idempotent re-indexing in `backend/workers/ingest_worker.py` (deleting existing document chunks from Qdrant and BM25 before re-processing).
- Add zombie job recovery on backend startup (marking abandoned `processing` jobs as `failed` or re-queueing them).

### Phase 6: Frontend PDF Viewer Alignment
- Verify PDF.js canvas coordinate mapping across page zoom levels and canvas resizing.

### Phase 7: Comprehensive Documentation Revision
- Update architecture documentation, file-by-file catalog, setup guides, and compile revised PDF manual.

### Phase 8: Final Verification & Test Suite Execution
- Run full pytest test suite, test scanned PDF ingestion, verify citation highlights, and produce final test report.
