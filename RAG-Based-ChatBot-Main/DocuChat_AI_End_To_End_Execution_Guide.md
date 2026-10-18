# DocuChat AI System Manual — Release 2.0
## End-to-End Execution & File-by-File Order Guide

> A comprehensive, chronological engineering walkthrough of the entire DocuChat production RAG platform: what happens step by step when you upload a document, which server process runs, which background worker is dispatched, which AI model executes, how hybrid retrieval fuses with cross-encoder reranking, how agentic tools are evaluated, and the exact role of all 35 source code files in the repository.

---

### Core Operational Metrics
* **8 Servers & Microservices:** React 18, FastAPI 0.141+, Ingestion Worker, Qdrant Vector DB, Docling-serve, Ollama LLM Engine, PostgreSQL 16, Redis 7.
* **4 AI / ML Models:** Qwen 2.5 (`3b`/`7b`), Nomic Embed / BGE-Small, BAAI/bge-reranker-base, Docling Layout/TableFormer.
* **35+ Source Code Files:** Fully cataloged across API, Workers, Ingestion, Embeddings, Retrieval, Tools, and Database.
* **100% Private & Air-Gapped Capable Architecture.**

---

## 1. System Topology: Servers, Services & AI Models

### 1.1 The 8 Servers & Services in Execution

| Server / Service | Port | Technology / Container Image | Host / URL | Primary Role & Operational Lifecycle |
| :--- | :---: | :--- | :--- | :--- |
| **1. Frontend Web App** | `3000` | React 18 SPA (Vite / Dev / Nginx) | `http://localhost:3000` | User interface, drag-and-drop zone, SSE stream reader, WebSocket client, PDF.js canvas bounding box highlighter. |
| **2. Backend API Gateway** | `5000` | FastAPI / Uvicorn (Python 3.11+) | `http://localhost:5000` | Core API gateway. Handles JWT auth, upload validation, query routing, SSE token streaming, safe tool execution, and database sessions. |
| **3. Background Ingestion Worker** | `Internal` | Python Worker (`backend.workers.ingest_worker`) | `Container / Subprocess` | Decoupled background worker. Consumes jobs from Redis queue (`docuchat_ingest_queue`), runs Docling extraction, structure chunking, embeddings, and Qdrant upserts. |
| **4. Docling Layout Engine** | `5001` | `quay.io/docling-project/docling-serve` | `http://localhost:5001` | IBM Docling layout vision microservice. Extracts headings, tables, reading order, and exact PDF bounding box coordinates (`x0, y0, x1, y1`). PyMuPDF fallback. |
| **5. Local LLM Service** | `11434` | Ollama Runtime | `http://localhost:11434` | Locally hosted LLM runtime. Serves `qwen2.5:3b` / `qwen2.5:7b` for generation, query rewriting, and Nomic dense embeddings. |
| **6. Vector Database** | `6333` / `6334` | Qdrant Vector DB Engine | `http://localhost:6333` | Stores dense vector chunks with Cosine distance indexing. Performs sub-millisecond Approximate Nearest Neighbor (ANN) vector search. |
| **7. Relational Database** | `5432` | PostgreSQL 16 Alpine / SQLite fallback | `postgres:5432` / `rag_app.db` | Persists multi-tenant users, sessions, documents, ingest jobs, and chat messages with SQLAlchemy async session pooling. |
| **8. Redis Broker & Cache** | `6379` | Redis 7 Alpine | `redis://localhost:6379/0` | In-memory message broker for ingestion jobs (`docuchat_ingest_queue`) and pub/sub broadcaster for real-time WebSocket progress updates. |

### 1.2 The 4 Machine Learning Models in the Pipeline

| Model Name | Architecture | Dimensions / Parameters | Serving Engine | Execution Stage & Specific Responsibility |
| :--- | :--- | :---: | :--- | :--- |
| **Qwen 2.5** (`qwen2.5:3b` / `7b`) | Decoder-Only Transformer | 3.09B / 7.61B | Ollama (`:11434`) | **Reasoning & Generation:** Pronoun resolution, search query expansion, tool evaluations, and grounded token generation with citations. |
| **Nomic Embed / BGE-Small** | Encoder Transformer | 768d / 384d | Ollama / FastEmbed ONNX | **Dense Semantic Vectorization:** Converts chunks and queries into normalized dense vectors. |
| **BAAI/bge-reranker-base** | Cross-Encoder Transformer | 278M params | SentenceTransformers | **Precision Relevance Reranking:** Evaluates `[Query, Passage]` pairs with full cross-attention and max-scaling normalization. |
| **Docling Vision / TableFormer** | Multi-Modal Vision Transformer | Proprietary OCR | Docling-Serve (`:5001`) | **Structural Layout Parsing:** Segments multi-column layouts, reconstructs markdown tables, and maps exact bounding box coordinates. |

---

## 2. Visual End-to-End Pipeline Diagrams

### 2.1 Document Ingestion & Background Indexing Pipeline

```
[Browser UI: Port 3000] --(POST /api/documents)--> [FastAPI: Port 5000]
                                                          |
                                            (Validates Auth & Stages Raw File)
                                                          v
                                             [backend/data/uploads/]
                                                          |
                               +--------------------------+--------------------------+
                               |                                                     |
                 (Enqueues Ingest Job)                              (Subscribes Live Progress)
                               v                                                     v
                 [workers/job_queue.py]                            [WS: /ws/documents/{id}/progress]
                               |                                                     ^
                 (Redis: docuchat_ingest_queue)                                      |
                               v                                                     |
                [workers/ingest_worker.py] --(Broadcasts: 15% -> 40% -> 65% -> 100%)-+
                               |
                               +-- 15% --> [parsers/converter.py] (Converts to PDF via LibreOffice/PyMuPDF)
                               |
                               +-- 40% --> [parsers/docling_parser.py] --(POST :5001)--> [Docling-Serve]
                               |                                                               |
                               |                                                (Fallback: PyMuPDF Fitz)
                               |
                               +-- 65% --> [chunking/structure_chunker.py] (~400 Tokens + Phrase BBoxes)
                               |
                               +-- 80% --> [embeddings/embedder.py] (Dense Vectors: Nomic 768d / BGE 384d)
                               |
          +--------------------+--------------------+
          |                                         |
          v (Port 6333)                             v (Disk: backend/data/bm25/{id}.json)
 [Qdrant Vector DB]                         [BM25Plus Lexical Index]
(Collection: doc_chunks)                 (Inverted Sparse Term Table)
          |                                         |
          +--------------------+--------------------+
                               |
                               v (Progress 100%)
                 [PostgreSQL / SQLite Database]
           (DocumentModel: status="ready", chunks=N)
                               |
                [Browser UI Shows Active Document]
```

### 2.2 Query, Agentic Routing, Hybrid Retrieval & Grounded Generation Pipeline

```
[Browser UI: Port 3000] --(POST /api/chat [SSE] OR WS: /ws/chat)--> [FastAPI: Port 5000]
                                                                            |
                                                      (Validates JWT Bearer & Tenant Scoping)
                                                                            v
                                                       [backend/api/chat.py / websockets.py]
                                                                            |
                                                      (Checks Agentic Tools: Calculator / Excel)
                                                                            v
                                                             [backend/llm/router.py]
                                                                            |
                                            +-------------------------------+-------------------------------+
                                            |                                                               |
                              (Route == "document")                                           (Route == "general")
                                            v                                                               v
                             [backend/llm/rewriter.py]                                     [backend/retrieval/web_search.py]
                         (Ollama Port 11434: 3 Expansions)                              (Yahoo Finance / DDG / Wikipedia)
                                            |                                                               |
                       +--------------------+--------------------+                                          |
                       |                                         |                                          |
                       v (Port 6333)                             v (Disk / RAM)                             |
             [Qdrant Vector Store]                       [BM25Plus Index]                                   |
           (Dense Semantic: Top 30)                   (Sparse Lexical: Top 30)                              |
                       |                                         |                                          |
                       +--------------------+--------------------+                                          |
                                            |                                                               |
                                            v                                                               |
                             [backend/retrieval/fusion.py]                                                  |
                          (Reciprocal Rank Fusion: k = 60)                                                  |
                                            |                                                               |
                                            v                                                               |
                             [backend/retrieval/dedup.py]                                                   |
                          (Jaccard & N-Gram Text Filter)                                                    |
                                            |                                                               |
                                            v                                                               |
                            [backend/retrieval/reranker.py]                                                 |
                       (BAAI/bge-reranker-base: Max-Scaled Top 40)                                          |
                                            |                                                               |
                           (Score >= 0.25 Threshold -> Top 3)                                               |
                                            |                                                               |
                                            +-------------------------------+-------------------------------+
                                                                            |
                                                                            v
                                                        [backend/llm/generator.py]
                                                  [backend/llm/langchain_adapter.py]
                                                                            |
                                                        (Constructs Grounded Numbered Sources)
                                                                            v
                                                        [Ollama: qwen2.5:3b / 7b Engine]
                                                                            |
                                                         (Streaming Tokens via SSE / WS)
                                                                            v
                                                    [refine_citations_for_answer()]
                                                 (Global Scoring Isolates Exact Single BBox)
                                                                            v
[Browser UI Receives: Token Stream + Citations Payload] <-------------------+
           |
(Renders Live Markdown Response & Paints Fluorescent Pulsing Highlight Box on PDF.js Canvas)
```

### 2.3 Safe Agentic Tool Execution Pipeline

```
[Browser UI] --(POST /api/tools/execute: {tool, arguments})--> [backend/api/tools.py]
                                                                      |
                                                          (Validates Against Pydantic Schema)
                                                                      v
                                                         [backend/tools/registry.py]
                                                                      |
                     +----------------------------+-------------------+----------------------------+
                     |                            |                                                |
                     v                            v                                                v
            [calculator.py]              [web_search.py]                                 [excel_generator.py]
        (Safe AST Tree Eval)         (DuckDuckGo / Yahoo / Wiki)                     (OpenPyXL Formatted Tables)
        (No eval() execution)        (Zero API Key Required)                         (Saves to data/output/*.xlsx)
                     |                            |                                                |
                     +----------------------------+-------------------+----------------------------+
                                                                      |
                                                                      v
                                                   [Returns Structured JSON Result]
                                                                      |
                                                    (If File Generated: Download via)
                                            [GET /api/tools/download/{file}: Path-Traversed Safe]
```

---

## 3. Step-by-Step Order: When You Upload a Document

### Step 1: Frontend Selection & Multipart HTTP Dispatch
* **File:** `frontend/src/App.jsx`, `frontend/src/services/api.js`
* **Network:** React (Port 3000) &rarr; FastAPI (Port 5000)
* **What Happens:** The user drops or selects a document file in the UI dropzone. `handleFileUpload(file)` validates the file, creates a `FormData` multipart payload with optional JWT authorization headers, and sends `POST /api/documents`.

### Step 2: FastAPI Upload Validation, Multi-Tenant Auth & Disk Staging
* **File:** `backend/api/documents.py`, `backend/api/auth.py`
* **What Happens:** `upload_document()` inspects the bearer token to identify `user_id`. It validates the file extension against `ALLOWED_EXTENSIONS`, generates a random UUID (`doc_id`), and streams the raw bytes to `backend/data/uploads/{doc_id}_{filename}`.

### Step 3: Relational DB Row & Ingest Job Record Creation
* **File:** `backend/db/models.py`, `backend/db/session.py`
* **What Happens:** Two database records are committed: `DocumentModel(id=doc_id, user_id=user_id, status="queued")` and `IngestJobModel(id=job_id, document_id=doc_id, status="queued", progress=5)`.

### Step 4: Asynchronous Job Enqueuing & WebSocket Subscription
* **File:** `backend/workers/job_queue.py`, `backend/api/websockets.py`
* **What Happens:** `enqueue_document_ingestion()` pushes the payload to Redis list `docuchat_ingest_queue` (with fallback to an in-memory async task pool). FastAPI immediately returns HTTP 200 with document metadata. The client connects to `/ws/documents/{doc_id}/progress` to receive real-time progress events.

### Step 5: Format Normalization to Visual PDF
* **File:** `backend/parsers/converter.py`
* **What Happens:** Background worker runs `convert_to_pdf()`. PDF files are verified with PyMuPDF. Office documents (DOCX, PPTX, XLSX, TXT) are converted via headless LibreOffice. Images (PNG, JPG) are wrapped into a PDF canvas by PyMuPDF. Progress broadcasts: **15%**.

### Step 6: Docling Microservice Extraction & Structure Parsing
* **File:** `backend/parsers/docling_parser.py`
* **Network:** Worker &rarr; Docling-Serve (Port 5001)
* **What Happens:** Worker posts the document to Docling (Port 5001). Docling extracts paragraphs, section headers, tables, and bounding box coordinates (`x0, y0, x1, y1`). If Docling is offline, `docling_parser.py` catches the error and executes its native PyMuPDF block extractor with zero downtime. Progress broadcasts: **40%**.

### Step 7: Structure-Aware Token Chunking & Provenance Retention
* **File:** `backend/chunking/structure_chunker.py`
* **What Happens:** Elements are segmented into token windows (`CHUNK_TARGET_TOKENS = 400`, max 450, overlap 50). Preserves markdown heading paths (`# Title > ## Subtitle`) and attaches exact phrase bounding boxes to every chunk. Progress broadcasts: **65%**.

### Step 8: Dense Vector Embedding Generation
* **File:** `backend/embeddings/embedder.py`
* **Model:** `nomic-embed-text:v1.5` (768d) or `BAAI/bge-small-en-v1.5` (384d)
* **What Happens:** Chunks are vectorized using Ollama embeddings or FastEmbed ONNX runtime. Progress broadcasts: **80%**.

### Step 9: Vector Storage Upsert & Collection Indexing
* **File:** `backend/retrieval/vector_store.py`
* **Network:** Worker &rarr; Qdrant (Port 6333)
* **What Happens:** Vectors and payloads (`doc_id`, `chunk_id`, `page`, `text`, `bboxes`, `heading_path`) are upserted into Qdrant collection `doc_chunks`. Progress broadcasts: **90%**.

### Step 10: BM25Plus Lexical Inverted Indexing
* **File:** `backend/retrieval/bm25.py`
* **Storage:** Disk `backend/data/bm25/{doc_id}.json`
* **What Happens:** Tokenizes text into stemmed n-grams, computes IDF tables, and writes the BM25Plus index to disk. Progress broadcasts: **95%**.

### Step 11: Relational DB Finalization & Real-Time WebSocket Completion
* **File:** `backend/workers/ingest_worker.py`
* **What Happens:** Worker updates `DocumentModel(status="ready", chunk_count=N)` and `IngestJobModel(status="completed", progress=100)`. Publishes completion over WebSocket and Redis pub/sub. The React UI displays the document as ready and mounts the PDF canvas.

---

## 4. Step-by-Step Order: When You Ask a Question / Chat

### Step 1: User Message Input & SSE / WebSocket Dispatch
* **File:** `frontend/src/components/Chat/ChatInput.jsx`, `frontend/src/services/api.js`
* **What Happens:** User types a question. The frontend sends an SSE `POST /api/chat` or emits a WebSocket payload over `/ws/chat`.

### Step 2: Multi-Tenant Session Validation & Context Window Assembly
* **File:** `backend/api/chat.py`, `backend/api/websockets.py`
* **What Happens:** Validates JWT bearer token, checks conversation ownership, stores user prompt into `MessageModel`, and retrieves the last 6 conversational turns from the database.

### Step 3: Agentic Tool Intent Evaluation
* **File:** `backend/tools/registry.py`, `backend/llm/router.py`
* **What Happens:** Checks if query requires a vetted agentic tool: `calculator` (safe AST math), `export_excel` (OpenPyXL reports), or `web_search`. Executes sandbox tool if matched.

### Step 4: Intent Routing: Document Mode vs ChatGPT Real-World Mode
* **File:** `backend/llm/router.py`
* **What Happens:** If no documents are active or the query is a pleasantry, routes to `general` mode. If documents are active, routes to `document` mode to enforce strict document grounding.

### Step 5: Multi-Query Rewriting & Pronoun Disambiguation
* **File:** `backend/llm/rewriter.py`
* **Model:** Ollama `qwen2.5:3b` / `7b` (Port 11434)
* **What Happens:** Resolves pronouns based on conversation history and generates 3 distinct query variants with special expansions for tables and financial summaries.

### Step 6: Parallel Hybrid Retrieval: Dense Vectors + Sparse BM25Plus
* **File:** `backend/retrieval/pipeline.py`
* **What Happens:** Executes parallel async retrieval: Dense ANN search against Qdrant (Top 30) + Sparse keyword search against BM25Plus index (Top 30) for each query variant.

### Step 7: Reciprocal Rank Fusion (RRF) & Semantic Deduplication
* **File:** `backend/retrieval/fusion.py`, `backend/retrieval/dedup.py`
* **What Happens:** Merges search rankings using $RRF(d) = \sum rac{1}{60 + rank(d)}$. Deduplicates redundant candidate chunks using Jaccard text similarity and n-gram overlap ($> 0.88$).

### Step 8: Cross-Encoder Deep Reranking & Max-Scaling Normalization
* **File:** `backend/retrieval/reranker.py`
* **Model:** `BAAI/bge-reranker-base`
* **What Happens:** Cross-Encoder rescores the top 40 candidates. Max-scaling normalization (`raw / max_s`) ensures secondary valid chunks are retained. Filters out chunks below 0.25 threshold, selecting Top 3 candidates.

### Step 9: Grounded Prompt Assembly, LangChain Orchestration & Token Streaming
* **File:** `backend/llm/generator.py`, `backend/llm/langchain_adapter.py`
* **Model:** Ollama `qwen2.5:3b` / `7b` (Port 11434)
* **What Happens:** Assembles numbered context sources `[1]` with strict anti-hallucination instructions. Invokes Ollama or LangChain ChatOllama, streaming tokens character-by-character to the client UI.

### Step 10: Real-Time Live Web Knowledge Fallback
* **File:** `backend/retrieval/web_search.py`
* **What Happens:** If the document does not contain the answer, seamlessly queries Yahoo Finance, DuckDuckGo Lite, or Wikipedia REST API to provide accurate real-world context with zero external API key requirements.

### Step 11: Global Best-Box Refinement & Synchronized Canvas Highlighting
* **File:** `backend/llm/generator.py`, `frontend/src/components/PdfViewer/PdfViewerDrawer.jsx`
* **What Happens:** `refine_citations_for_answer()` scores answer tokens against chunk bounding box text to isolate the single winning bounding box. Emits citation payload to frontend, painting a pulsing highlight on the PDF.js canvas viewer.

---

## 5. Complete File-by-File Codebase Catalog

### 5.1 API Gateway & Application Layer
1. `backend/main.py`: FastAPI application entrypoint, lifespan startup, CORS, request correlation ID middleware, router mounting.
2. `backend/config.py`: Centralized Pydantic settings singleton defining ports, models, thresholds, and auto-detecting embedding dimensions.
3. `backend/api/documents.py`: Document upload, file deletion, raw file serving, and background ingestion dispatch.
4. `backend/api/chat.py`: SSE streaming chat endpoint with history logging, multi-tenant auth, and citation streaming.
5. `backend/api/conversations.py`: CRUD endpoints for conversation sessions, title updates, and cascading history deletion.
6. `backend/api/auth.py`: Multi-tenant user auth, Argon2id/PBKDF2 password hashing, JWT creation/validation, and RBAC roles.
7. `backend/api/websockets.py`: Bidirectional WebSocket endpoints for chat (`/ws/chat`) and document ingestion progress (`/ws/documents/{doc_id}/progress`).
8. `backend/api/tools.py`: Safe agentic tool discovery, execution endpoints, and path-traversal-defended file downloads (`/tools/download/{filename}`).

### 5.2 Background Workers & Asynchronous Job Layer
9. `backend/workers/ingest_worker.py`: Decoupled background ingestion worker running format conversion, Docling extraction, chunking, embeddings, and Qdrant upserts.
10. `backend/workers/job_queue.py`: Ingestion job queue dispatcher managing `IngestJobModel` persistent state and Redis list dispatch.

### 5.3 Parsing, Chunking & Ingestion Layer
11. `backend/parsers/converter.py`: Multi-format visual normalizer converting DOCX, PPTX, XLSX, TXT, and images into visual PDFs via LibreOffice or PyMuPDF.
12. `backend/parsers/docling_parser.py`: IBM Docling-serve REST client for layout vision and table extraction, with offline PyMuPDF Fitz fallback.
13. `backend/chunking/structure_chunker.py`: Structure-aware token chunker preserving markdown sections and attaching phrase bounding boxes.

### 5.4 Embedding & Vector Storage Layer
14. `backend/embeddings/embedder.py`: Dual embedding engine supporting Nomic Embed (768d via Ollama) and BGE-Small (384d via FastEmbed ONNX).
15. `backend/retrieval/vector_store.py`: Qdrant vector database client managing collection initialization, batch upserts, and Cosine ANN search.

### 5.5 Retrieval, Fusion, Deduplication & Live Web Layer
16. `backend/retrieval/bm25.py`: BM25Plus sparse lexical index with per-document disk persistence in `data/bm25/{doc_id}.json`.
17. `backend/retrieval/fusion.py`: Reciprocal Rank Fusion ($k=60$) and weighted score fusion engine.
18. `backend/retrieval/dedup.py`: Semantic text deduplication using Jaccard word similarity and character n-gram overlap.
19. `backend/retrieval/reranker.py`: Deep cross-attention reranker with `BAAI/bge-reranker-base` and max-scaling score normalization.
20. `backend/retrieval/pipeline.py`: Master retrieval pipeline orchestrating parallel dense + sparse retrieval, fusion, deduplication, and reranking.
21. `backend/retrieval/web_search.py`: Zero-API-key live web knowledge engine (Yahoo Finance, DuckDuckGo Lite, Wikipedia REST API).

### 5.6 LLM Reasoning, Generation, LangChain & Agentic Tools Layer
22. `backend/llm/client.py`: Asynchronous HTTP client for Ollama LLM runtime with streaming and health checks.
23. `backend/llm/router.py`: Rule-based and semantic query router distinguishing between document mode and general ChatGPT mode.
24. `backend/llm/rewriter.py`: Multi-query rewriting and pronoun resolution engine with fast expansions for tables and summaries.
25. `backend/llm/generator.py`: Grounded prompt assembler, anti-hallucination guardrail enforcer, SSE streamer, and citation bounding box refiner.
26. `backend/llm/langchain_adapter.py`: LangChain ChatOllama orchestration adapter and PDF text cleaner (`clean_pdf_text`).
27. `backend/tools/registry.py`: Central safe tool registry with Pydantic JSON schemas (`calculator`, `web_search`, `export_excel`).
28. `backend/tools/calculator.py`: Safe arithmetic engine using Python's `ast` parser without executing `eval()`.
29. `backend/tools/excel_generator.py`: Automated styled Excel workbook builder via `openpyxl`.
30. `backend/eval/retrieval_eval.py`: RAG retrieval evaluation harness computing Hit Rate@K, MRR@K, and NDCG.

### 5.7 Database, Frontend & Orchestration Layer
31. `backend/db/models.py`: SQLAlchemy 2.0 ORM models (`UserModel`, `UserSessionModel`, `DocumentModel`, `IngestJobModel`, `ConversationModel`, `MessageModel`).
32. `backend/db/session.py`: Async database session factory with dual PostgreSQL (`asyncpg`) and SQLite (`aiosqlite`) support.
33. `backend/db/migrate_sqlite_to_pg.py`: Migration utility to transfer schemas and records from SQLite to PostgreSQL.
34. `backend/alembic/`: Alembic database migration scripts for production schema versioning.
35. `frontend/src/App.jsx` & `frontend/src/App.css`: React SPA container managing multi-panel layouts, SSE streams, and WebSocket events.
36. `frontend/src/services/api.js` & `frontend/src/services/websocket.js`: Frontend networking layer for REST API calls and WebSocket streaming.
37. `frontend/src/components/PdfViewer/PdfViewerDrawer.jsx`: PDF.js canvas viewer rendering normalized fluorescent highlights over cited bounding boxes.
38. `docker-compose.yml`: Microservices orchestration stack defining all 8 services, volumes, networks, and healthchecks.

---

## 6. Data Schemas, Resiliency & Quick Reference

### 6.1 Summary Matrix: What Server & Model Runs at Each Step

| Pipeline Stage | Primary Source File | Caller &rarr; Target | Model / Technology | Primary Artifact / Output Created |
| :--- | :--- | :--- | :--- | :--- |
| **1. Upload** | `api/documents.py` | React (3000) &rarr; FastAPI (5000) | HTTP Multipart POST | `backend/data/uploads/{id}_{file}` |
| **2. Job Enqueue** | `workers/job_queue.py` | FastAPI &rarr; Redis (6379) | Redis RPUSH / Task Pool | `IngestJobModel(status="queued")` |
| **3. Format Normalization** | `parsers/converter.py` | Worker Process &rarr; CLI | LibreOffice / PyMuPDF | `backend/data/converted/{id}.pdf` |
| **4. Layout Parsing** | `parsers/docling_parser.py` | Worker &rarr; Docling (5001) | Docling / TableFormer / Fitz | `List[ParsedElement]` with exact BBoxes |
| **5. Token Chunking** | `chunking/structure_chunker.py` | In-Process (Worker) | Tiktoken Structure Slicing | `List[Chunk]` (~400 tokens + bboxes) |
| **6. Embeddings** | `embeddings/embedder.py` | Worker &rarr; Ollama / FastEmbed | Nomic 768d / BGE-small 384d | Normalized floating-point vectors |
| **7. Vector Upsert** | `retrieval/vector_store.py` | Worker &rarr; Qdrant (6333) | Qdrant HNSW Graph Index | Points in collection `doc_chunks` |
| **8. BM25 Index** | `retrieval/bm25.py` | In-Process (Worker) | BM25Plus Inverted Index | `backend/data/bm25/{doc_id}.json` |
| **9. User Query** | `api/chat.py` / `websockets.py` | React (3000) &rarr; FastAPI (5000) | SSE Stream / WebSocket | User message record in database |
| **10. Tool Check** | `tools/registry.py` | FastAPI &rarr; AST Sandbox | Safe AST / OpenPyXL / DDG | Calculated result or downloadable Excel |
| **11. Query Rewriting** | `llm/rewriter.py` | FastAPI &rarr; Ollama (11434) | `qwen2.5:3b` / `7b` Model | 3 pronoun-resolved search queries |
| **12. Hybrid Search** | `retrieval/pipeline.py` | FastAPI &rarr; Qdrant & BM25 | Cosine ANN + BM25 Lexical | Top 60 candidate chunks |
| **13. Fusion & Dedup** | `retrieval/fusion.py` & `dedup.py` | In-Process | RRF ($k=60$) + Jaccard 3-Gram | Top 40 non-duplicate candidate chunks |
| **14. Cross-Rerank** | `retrieval/reranker.py` | In-Process &rarr; PyTorch/ONNX | `BAAI/bge-reranker-base` | Top 3 chunks with score $\ge 0.25$ |
| **15. Generation** | `llm/generator.py` | FastAPI &rarr; Ollama (11434) | `qwen2.5:3b` / `7b` via LangChain | Streamed token response + citations |
| **16. Highlight** | `generator.py` & `PdfViewerDrawer.jsx` | FastAPI &rarr; React Canvas | `refine_citations_for_answer` | Pulsing fluorescent highlight on PDF.js |

### 6.2 Resiliency & Built-in Automatic Fallbacks

| Component / Fault Point | Primary Execution Engine | Automatic Fallback Mechanism | User / System Impact |
| :--- | :--- | :--- | :--- |
| **Document Parser** | Docling-serve container (Port 5001) | Local `pymupdf` (Fitz) structural parser | Zero downtime. Automatically extracts text blocks and coordinates offline. |
| **Vector Database** | Qdrant Server (Port 6333) | Embedded local Qdrant (`data/qdrant_storage`) | Full vector search operates locally without Docker container. |
| **Relational Database** | PostgreSQL 16 (Port 5432) | SQLite local database (`data/rag_app.db`) | Complete persistence for users, jobs, and chat histories without Postgres. |
| **Job Message Broker** | Redis 7 Broker (Port 6379) | FastAPI asynchronous background task pool | Ingestion jobs execute seamlessly in-process with persistent DB tracking. |
| **Embeddings Engine** | Ollama (`nomic-embed-text`) | FastEmbed ONNX (`bge-small-en-v1.5`) | Sub-second local CPU embeddings if Ollama is busy or unreachable. |
| **Office File Converter** | Headless LibreOffice CLI | PyMuPDF text-canvas generation | Converts text and images to PDF without external office software. |
| **Password Hashing** | Argon2id (`argon2_cffi`) | PBKDF2-HMAC-SHA256 (100k rounds) | Zero dependency breaks; constant-time hash verification. |
| **Live Web Search** | Yahoo Finance & DuckDuckGo Lite | Wikipedia REST API | Factual lookups succeed without third-party API keys or rate limits. |

---

*DocuChat AI System Manual &bull; Release 2.0 &bull; Maintained by Engineering Team*
