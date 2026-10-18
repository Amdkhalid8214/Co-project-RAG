# Engineering Memory & Lessons Learned
## DocuChat AI — Technical Decisions, Gotchas & Rationale

---

## 1. Key Architectural Decisions & Rationale

### Decision 1.1: Ollama with Qwen 2.5 (1.5B) as Default LLM
- **Rationale:** High reasoning capabilities, strong structured JSON compliance, multilingual support, and native 32k context window in a compact parameter footprint that runs at 40+ tokens/sec on standard consumer CPU/GPUs without requiring cloud API subscriptions.

### Decision 1.2: FastEmbed ONNX Runtime for Embeddings (`BAAI/bge-small-en-v1.5`)
- **Rationale:** Pure ONNX C++ runtime without heavyweight PyTorch dependencies. Generates 384-dimensional dense vectors in $< 5\text{ ms}$ per query, perfectly matching Qdrant cosine similarity search.

### Decision 1.3: BM25Plus Over BM25Okapi
- **Rationale:** Standard BM25Okapi computes negative IDF scores when document frequency $n$ approaches corpus size $N$ (e.g. $N=2$ chunks). In contrast, `BM25Plus` uses a lower-bounded IDF formulation that guarantees strictly positive, well-calibrated scores for single-document and multi-document retrieval alike.

### Decision 1.4: Max-Scaling Over Min-Max Normalization
- **Rationale:** Min-max normalization:
  $$\text{norm} = \frac{s - \min(s)}{\max(s) - \min(s)}$$
  mathematically forces the lowest candidate chunk to $0.0$. In a two-chunk document, Chunk 2 always becomes $0.0$ and gets dropped by `score_threshold >= 0.25`. Max-scaling:
  $$\text{norm} = \frac{s}{\max(s)}$$
  preserves relative strength and allows all relevant chunks to pass to the LLM.

---

## 2. Critical Gotchas Solved

### Gotcha 2.1: The 900-Character Context Truncation Bug
- **Symptom:** AI abruptly stopped listing technical skills at "Oracle", missing ML, Generative AI, and tools.
- **Root Cause:** In `generator.py`, `snippet = text[:900]` truncated Chunk 0 right in the middle of the Technical Skills line at character 900.
- **Fix:** Increased chunk snippet limit to 3,500 characters, allowing complete sections to be passed to the LLM.

### Gotcha 2.2: The "Blue Screen" 20-Box Highlighting Bug
- **Symptom:** Entire page covered with blue boxes instead of just the answer.
- **Root Cause:** The parser attached all element boxes to the chunk, and the backend passed all 20 chunk boxes directly to the citation payload.
- **Fix:** Implemented `refine_citations_for_answer()` in `generator.py` to evaluate bounding boxes against generated answer keywords and return **only the single highest-scoring box** (`allBoxes.slice(0, 1)`).

### Gotcha 2.3: BM25 Zero Hits on Small Resume PDF
- **Symptom:** Vector search worked, but BM25 returned 0 hits for exact words like "technical skills".
- **Root Cause:** BM25Okapi produced negative scores (`-0.044`), triggering `if score > 0` to discard all chunks.
- **Fix:** Upgraded to `BM25Plus` in `retrieval/bm25.py`.

### Gotcha 2.4: Ollama 404 Model Not Found
- **Symptom:** Generation requests returned HTTP 404 from Ollama.
- **Root Cause:** Container `docuchat_ollama` on port 11434 did not have `qwen2.5:7b` pre-pulled.
- **Fix:** Executed `docker exec docuchat_ollama ollama pull qwen2.5:7b` (or `ollama pull qwen2.5:7b`) and added automated model readiness verification.

### Gotcha 2.5: Windows Console `cp1252` Encoding Error
- **Symptom:** Python terminal crashed with `UnicodeEncodeError: 'charmap' codec can't encode character '\u025b'`.
- **Root Cause:** Wikipedia search results contained phonetic symbols (IPA) that Windows command prompt CP1252 could not display.
- **Fix:** Added `clean_snippet()` with `html.unescape` and safe string normalization in `retrieval/web_search.py`.

### Gotcha 2.6: Unrequested Context Dumping & Multi-Box Highlighting
- **Symptom:** Asking about "Embeddings and Softmax" caused the AI to dump unrequested sections ("Applications of Attention in Our Model") and Table 1, and the PDF viewer drew 10+ evidence boxes across the entire page.
- **Root Cause:**
  1. Prompt templates lacked strict query relevance boundaries and explicitly prompted for tables (`include Markdown tables where applicable`), causing the LLM to regurgitate all surrounding headings and tables from the chunk.
  2. In `generator.py`, `refine_citations_for_answer()` had an overly loose cutoff (`best['score'] * 0.08`) and no box count limit, highlighting every paragraph on the page.
- **Fix:**
  1. Updated `GROUNDED_SYSTEM_TEMPLATE` and `GROUNDED_HUMAN_TEMPLATE` with strict query relevance: answer ONLY the requested topic and never dump unrequested neighboring sections or tables.
  2. Added token containment filtering (`containment < 0.20`), boosted query token weighting, set cutoff to `max(45.0, best['score'] * 0.75)`, and capped evidence highlights to at most the top 2 exact matching boxes.

### Gotcha 2.7: Cross-Page Section Severance & Table Omission (Regularization Page 7/8)
- **Symptom:** Querying "regularization" returned only: "We employ three types of regularization during training. The specific details are not provided in the given context.", missing the three methods (Residual Dropout, Label Smoothing) and Table 2.
- **Root Cause:**
  1. Section 5.4 started at the very bottom of Page 7 (Chunk 9) with "We employ three types of regularization during training:". Its continuation (Residual Dropout, Label Smoothing, and Table 2) was on Page 8 (Chunk 10).
  2. Because Chunk 10 lacked the keyword "regularization" (its heading path was empty), only Chunk 9 was retrieved.
  3. Strict prompt rules suppressed Table 2 as an "unrequested table".
- **Fix:**
  1. Added sequential context window expansion in `retrieval/pipeline.py` using `bm25_index.get_document_chunks()` to automatically retrieve the continuation chunk ($i+1$) across page boundaries and split tables.
  2. Added targeted query expansion in `rewriter.py` for regularization, dropout, and label smoothing.
  3. Updated prompt templates to explicitly instruct the model to detail all components of multi-part concepts and include relevant performance/benchmark tables in clean Markdown.

### Gotcha 2.8: Cross-Section Blending & Stray PDF Highlights (Position-wise Feed-Forward Networks)
- **Symptom:** Querying "What is position-wise-feed-forward Network" generated an answer mixing in decoder self-attention masking from Section 3.2.3, and the PDF viewer drew a stray orange box over Section 3.2.3 (`Applications of Attention in our Model`) in addition to Section 3.3.
- **Root Cause:**
  1. Chunk boundary bleed: In `Attention.pdf`, Chunk 7 contained the end of Section 3.2.3, followed by Section 3.3 and Section 3.4. Without strict section purity rules, the LLM hallucinated that self-attention masking belonged to the feed-forward network.
  2. Overly loose 3-word n-gram search: In `_locate_pinpoint_answer_boxes()`, 3-word search windows lacked stopword filtering, causing generic n-grams like `"layer of the encoder"` to match random lines in Section 3.2.3.
  3. Missing block dominance filter: Even when Section 3.2.3 produced only a 2-line stray hit with 76pt width while Section 3.3 had 8+ lines and 2,600+pt width, both blocks were returned as separate bounding boxes.
- **Fix:**
  1. Added **Section Purity & Isolation Rules** in `backend/llm/generator.py` and `backend/llm/langchain_adapter.py`: when asked for a specific topic/component, the LLM answers strictly and solely from that numbered section without cross-section blending, preserving exact formulas (`FFN(x) = max(0, xW1 + b1)W2 + b2`) and parameters (`d_model = 512, d_ff = 2048`).
  2. Required candidate 3-word and 4-word search n-grams in `_locate_pinpoint_answer_boxes()` to contain at least 2 content words (length $\ge 3$ and not in `stop_words`).
  3. Added **Block Dominance & Density Filtering**: when multiple blocks form on a page, discard weak stray blocks with $< 180\text{ pt}$ width or $< 35\%$ of dominant block width, and discard any block with $< 50\%$ lines of max block.
  4. Added cross-page density filtering to eliminate single-line fragmented mentions on other pages when a complete dominant answer block exists.

---

## 3. Key File & Responsibility Map

| File Path | Primary Responsibility |
| :--- | :--- |
| [`main.py`](file:///C:/Users/AMD/OneDrive/Desktop/Git%20rag/RAG-Based-ChatBot-Main/backend/main.py) | FastAPI app entry point, CORS, lifespan database initialization |
| [`config.py`](file:///C:/Users/AMD/OneDrive/Desktop/Git%20rag/RAG-Based-ChatBot-Main/backend/config.py) | Centralized Pydantic settings, model paths, port numbers, tuning parameters |
| [`parsers/docling_parser.py`](file:///C:/Users/AMD/OneDrive/Desktop/Git%20rag/RAG-Based-ChatBot-Main/backend/parsers/docling_parser.py) | Docling client with PyMuPDF fallback, coordinate extraction |
| [`chunking/structure_chunker.py`](file:///C:/Users/AMD/OneDrive/Desktop/Git%20rag/RAG-Based-ChatBot-Main/backend/chunking/structure_chunker.py) | Structural chunking respecting headings, table preservation |
| [`retrieval/pipeline.py`](file:///C:/Users/AMD/OneDrive/Desktop/Git%20rag/RAG-Based-ChatBot-Main/backend/retrieval/pipeline.py) | Parallel hybrid retrieval orchestrator (Vector + BM25Plus + RRF + Reranker) |
| [`retrieval/bm25.py`](file:///C:/Users/AMD/OneDrive/Desktop/Git%20rag/RAG-Based-ChatBot-Main/backend/retrieval/bm25.py) | Disk-persisted BM25Plus sparse index |
| [`retrieval/reranker.py`](file:///C:/Users/AMD/OneDrive/Desktop/Git%20rag/RAG-Based-ChatBot-Main/backend/retrieval/reranker.py) | Cross-encoder rescoring with Max-scaling normalization |
| [`retrieval/web_search.py`](file:///C:/Users/AMD/OneDrive/Desktop/Git%20rag/RAG-Based-ChatBot-Main/backend/retrieval/web_search.py) | Real-time live data for stocks (Yahoo Finance), movies, sports, politics (DDG/Wiki) |
| [`llm/router.py`](file:///C:/Users/AMD/OneDrive/Desktop/Git%20rag/RAG-Based-ChatBot-Main/backend/llm/router.py) | Query intent classifier (Document Mode vs ChatGPT Real-World Mode) |
| [`llm/generator.py`](file:///C:/Users/AMD/OneDrive/Desktop/Git%20rag/RAG-Based-ChatBot-Main/backend/llm/generator.py) | Grounded prompt construction, SSE streaming, global best-box answer refinement |
| [`frontend/src/App.jsx`](file:///C:/Users/AMD/OneDrive/Desktop/Git%20rag/RAG-Based-ChatBot-Main/frontend/src/App.jsx) | React 18 UI, PDF.js canvas, SSE consumer, single-box answer highlighting |
