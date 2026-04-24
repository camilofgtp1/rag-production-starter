# rag-production-starter — Requirements & Agent Working Plan

> **Purpose:** Showcase project for AI platform advisory consulting.
> Target audience: Mid-sized companies building their first RAG system.
> Thesis: *"Most RAG tutorials get you to a working demo. This is what comes after."*

---

## Project Overview

A production-ready RAG starter kit that covers the parts tutorials skip:
chunking strategy, hybrid search, data ownership/drift, and evaluation.
Designed to be cloned and running in one command, with enough architecture
to survive real workloads.

**Stack:**
- Vector DB: Qdrant
- LLM Provider: OpenAI
- Evaluation: Ragas
- Serving: FastAPI (API key auth)
- Ingestion formats: PDF, Markdown, plain text, DOCX
- Local dev: Docker Compose
- Experiment tracking: MLflow

---

## Folder Structure (target)

```
rag-production-starter/
├── docker-compose.yml
├── .env.example
├── README.md
├── ARCHITECTURE.md
├── app/
│   ├── main.py                   # FastAPI entrypoint
│   ├── auth.py                   # API key middleware
│   ├── config.py                 # Settings via pydantic-settings
│   ├── api/
│   │   ├── ingest.py             # Ingest endpoints
│   │   ├── query.py              # Query/retrieve endpoints
│   │   └── eval.py              # Evaluation trigger endpoint
│   ├── ingestion/
│   │   ├── loader.py             # Format router (PDF/MD/TXT/DOCX)
│   │   ├── chunker.py            # Chunking strategies
│   │   └── embedder.py           # OpenAI embedding wrapper
│   ├── retrieval/
│   │   ├── qdrant_client.py      # Qdrant wrapper
│   │   ├── hybrid_search.py      # BM25 + dense fusion
│   │   └── reranker.py           # Optional reranking layer
│   ├── generation/
│   │   └── llm.py                # OpenAI chat completion wrapper
│   ├── governance/
│   │   ├── drift.py              # Chunk staleness / drift detection
│   │   ├── versioning.py         # Document versioning + re-index triggers
│   │   └── deletion.py           # GDPR-compliant vector deletion
│   ├── evaluation/
│   │   ├── ragas_eval.py         # Ragas pipeline (faithfulness, relevance, recall)
│   │   └── mlflow_logger.py      # Log eval results to MLflow
│   └── models/
│       └── schemas.py            # Pydantic request/response models
├── tests/
│   ├── test_chunker.py
│   ├── test_hybrid_search.py
│   ├── test_ingest.py
│   └── test_eval.py
├── scripts/
│   └── seed_demo.py              # Load sample docs and run demo query
├── docs/
│   ├── chunking-strategy.md      # Decision guide: when to use which strategy
│   ├── hybrid-search.md          # How BM25+dense fusion works and why
│   ├── data-governance.md        # Versioning, drift, GDPR deletion
│   └── evaluation.md             # How to interpret Ragas scores
└── mlflow/
    └── mlflow.dockerfile         # Lightweight MLflow server for local tracking
```

---

## Features & TODO Tracker

Each item below has a status, a scope description, and a self-contained agent prompt.
An agent should work one TODO at a time, mark it `[done]`, and stop before starting the next.

---

### PHASE 1 — Project Scaffold

---

#### TODO-01 · Project scaffold and Docker Compose
**Status:** `[ ] not started`

**Scope:**
- Initialize Python project with `pyproject.toml` (use `uv` or `pip`)
- Dependencies: fastapi, uvicorn, pydantic-settings, qdrant-client, openai, python-dotenv, ragas, mlflow, rank-bm25, pypdf, python-docx, markdown-it-py, tiktoken
- `docker-compose.yml` with services: `app`, `qdrant`, `mlflow`
- `.env.example` with all required env vars documented
- `app/config.py` using pydantic-settings to load from env
- `app/main.py` with FastAPI app, health check endpoint `/health`
- Verify: `docker compose up` starts all services without errors

**Agent prompt:**
```
You are building a Python FastAPI project called rag-production-starter.

Task: Create the full project scaffold.

Requirements:
- pyproject.toml with these dependencies: fastapi, uvicorn, pydantic-settings,
  qdrant-client, openai, python-dotenv, ragas, mlflow, rank-bm25, pypdf,
  python-docx, markdown-it-py, tiktoken
- docker-compose.yml with three services:
    - app: FastAPI server on port 8000, depends on qdrant and mlflow
    - qdrant: use qdrant/qdrant image, port 6333
    - mlflow: lightweight mlflow server on port 5000, stores artifacts locally
- .env.example documenting every env var the app needs (OPENAI_API_KEY,
  QDRANT_URL, QDRANT_API_KEY, MLFLOW_TRACKING_URI, API_KEY, COLLECTION_NAME)
- app/config.py: pydantic-settings Settings class loading all vars from env
- app/main.py: FastAPI app with a GET /health endpoint returning {"status": "ok"}

Output the full content of each file. Do not summarize.
```

---

#### TODO-02 · API key authentication middleware
**Status:** `[ ] not started`

**Scope:**
- `app/auth.py`: FastAPI dependency that reads `X-API-Key` header
- Returns 401 if missing or invalid, compared against `settings.API_KEY`
- Apply as a global dependency on all non-health routes
- Test: request without key returns 401, with correct key returns 200

**Agent prompt:**
```
You are working on rag-production-starter, a FastAPI project.

Task: Implement API key authentication.

Requirements:
- Create app/auth.py with a FastAPI dependency function `verify_api_key`
- It reads the X-API-Key header from the request
- Compares it to settings.API_KEY loaded from config.py
- Raises HTTP 401 with message "Invalid or missing API key" if invalid
- In app/main.py, apply this dependency globally to all routes EXCEPT /health
- Do not use FastAPI's APIKeyHeader from fastapi.security — use a plain Header dependency

Output the full content of app/auth.py and the updated app/main.py.
```

---

#### TODO-03 · Pydantic request/response schemas
**Status:** `[ ] not started`

**Scope:**
- `app/models/schemas.py`
- `IngestRequest`: filename, content (base64 or raw text), mime_type, doc_id (optional, auto-generated if missing), version (int, default 1)
- `QueryRequest`: query (str), top_k (int, default 5), alpha (float 0.0–1.0, default 0.5, controls hybrid search blend)
- `QueryResponse`: answer (str), sources (list of chunk metadata), eval_scores (optional dict)
- `EvalRequest`: query (str), answer (str), contexts (list of str)
- `EvalResponse`: faithfulness, answer_relevancy, context_recall (all float)

**Agent prompt:**
```
You are working on rag-production-starter, a FastAPI project.

Task: Define all Pydantic request and response schemas.

Create app/models/schemas.py with these models:

- IngestRequest:
    - filename: str
    - content: str (raw text or base64-encoded bytes depending on mime_type)
    - mime_type: str (one of: application/pdf, text/markdown, text/plain, application/vnd.openxmlformats-officedocument.wordprocessingml.document)
    - doc_id: Optional[str] = None (auto-generate UUID if missing)
    - version: int = 1

- QueryRequest:
    - query: str
    - top_k: int = 5
    - alpha: float = 0.5 (hybrid search blend: 0.0 = keyword only, 1.0 = dense only)

- ChunkSource:
    - doc_id: str
    - chunk_id: str
    - filename: str
    - version: int
    - score: float

- QueryResponse:
    - answer: str
    - sources: list[ChunkSource]
    - eval_scores: Optional[dict] = None

- EvalRequest:
    - query: str
    - answer: str
    - contexts: list[str]

- EvalResponse:
    - faithfulness: float
    - answer_relevancy: float
    - context_recall: float

Output the full content of app/models/schemas.py.
```

---

### PHASE 2 — Ingestion Pipeline

---

#### TODO-04 · Document loader (format router)
**Status:** `[ ] not started`

**Scope:**
- `app/ingestion/loader.py`
- Accepts raw bytes + mime_type, returns plain text string
- PDF: use pypdf
- DOCX: use python-docx
- Markdown: strip to plain text using markdown-it-py
- Plain text: decode UTF-8
- Raise `ValueError` for unsupported mime types
- No external subprocess calls

**Agent prompt:**
```
You are working on rag-production-starter, a FastAPI project.

Task: Implement the document loader that converts uploaded files to plain text.

Create app/ingestion/loader.py with a single function:
    def load_document(content_bytes: bytes, mime_type: str) -> str

Requirements:
- PDF (application/pdf): extract text using pypdf (PdfReader)
- DOCX (application/vnd.openxmlformats-officedocument.wordprocessingml.document):
  extract text using python-docx (Document)
- Markdown (text/markdown): strip markdown syntax to plain text using markdown-it-py
- Plain text (text/plain): decode as UTF-8
- Any other mime_type: raise ValueError("Unsupported mime type: {mime_type}")
- No subprocess calls. No file I/O — work only with bytes in memory.

Output the full content of app/ingestion/loader.py.
```

---

#### TODO-05 · Chunking strategies
**Status:** `[ ] not started`

**Scope:**
- `app/ingestion/chunker.py`
- Three strategies selectable via config: `fixed`, `semantic`, `late`
- `fixed`: split by token count with overlap (default: 512 tokens, 50 overlap, using tiktoken)
- `semantic`: split on paragraph/sentence boundaries, respect a max token ceiling
- `late`: produce large parent chunks + small child chunks (parent for context, child for retrieval)
- Each chunk returns: `chunk_id` (UUID), `text`, `strategy_used`, `token_count`, `parent_chunk_id` (for late chunking, else None)
- Default strategy set in config, overridable per request

**Agent prompt:**
```
You are working on rag-production-starter, a FastAPI project.

Task: Implement the chunking module with three strategies.

Create app/ingestion/chunker.py.

Define a dataclass or Pydantic model called Chunk:
    chunk_id: str (UUID)
    text: str
    strategy_used: str
    token_count: int
    parent_chunk_id: Optional[str] = None

Implement a function:
    def chunk_document(text: str, strategy: str = "semantic") -> list[Chunk]

Strategies:
1. "fixed": split by token count using tiktoken (model: text-embedding-3-small).
   Default: 512 tokens per chunk, 50 token overlap. Slide a window over tokens.

2. "semantic": split on double newlines (paragraphs) first, then on sentence
   boundaries if a paragraph exceeds 512 tokens. Never split mid-sentence.
   Each chunk must be under 512 tokens.

3. "late": first produce large parent chunks (~1500 tokens, split on paragraphs).
   Then split each parent into small child chunks (~150 tokens).
   Child chunks carry the parent_chunk_id of their parent.
   Return BOTH parent and child chunks in the output list.

All chunk_ids must be UUID4 strings. Log the strategy used per chunk.

Output the full content of app/ingestion/chunker.py.
```

---

#### TODO-06 · Embedder (OpenAI)
**Status:** `[ ] not started`

**Scope:**
- `app/ingestion/embedder.py`
- Wraps OpenAI embeddings API (`text-embedding-3-small`)
- Accepts list of strings, returns list of float vectors
- Batch calls to stay under API limits (max 100 texts per call)
- Retry on rate limit with exponential backoff (max 3 retries)

**Agent prompt:**
```
You are working on rag-production-starter, a FastAPI project.

Task: Implement the OpenAI embeddings wrapper.

Create app/ingestion/embedder.py with a function:
    async def embed_texts(texts: list[str]) -> list[list[float]]

Requirements:
- Use OpenAI's async client with model: text-embedding-3-small
- Batch input into groups of 100 (API limit)
- On RateLimitError: retry up to 3 times with exponential backoff (1s, 2s, 4s)
- Return vectors in the same order as input texts
- Load API key from settings (app/config.py)

Output the full content of app/ingestion/embedder.py.
```

---

#### TODO-07 · Qdrant client wrapper
**Status:** `[ ] not started`

**Scope:**
- `app/retrieval/qdrant_client.py`
- Initialize collection if not exists (vector size 1536 for text-embedding-3-small)
- `upsert_chunks(chunks, vectors, doc_id, filename, version)`: store chunks with full metadata payload
- `delete_by_doc_id(doc_id)`: delete all vectors for a document (for GDPR deletion and re-indexing)
- `dense_search(query_vector, top_k)`: pure vector search
- `get_all_doc_ids()`: list all unique doc_ids in collection (for drift checking)
- Payload fields per point: chunk_id, doc_id, filename, version, text, strategy_used, token_count, parent_chunk_id, ingested_at (ISO timestamp)

**Agent prompt:**
```
You are working on rag-production-starter, a FastAPI project.

Task: Implement the Qdrant client wrapper.

Create app/retrieval/qdrant_client.py using the qdrant-client library.

Implement these functions:

1. init_collection() -> None
   - Connect to Qdrant using settings.QDRANT_URL and settings.QDRANT_API_KEY
   - Create collection settings.COLLECTION_NAME if it does not exist
   - Vector size: 1536, distance: Cosine

2. upsert_chunks(chunks: list[Chunk], vectors: list[list[float]], doc_id: str, filename: str, version: int) -> None
   - Each PointStruct id = chunk.chunk_id (UUID string)
   - Payload: chunk_id, doc_id, filename, version, text, strategy_used,
     token_count, parent_chunk_id, ingested_at (current UTC ISO string)

3. delete_by_doc_id(doc_id: str) -> None
   - Delete all points where payload.doc_id == doc_id using a filter

4. dense_search(query_vector: list[float], top_k: int = 5) -> list[dict]
   - Return list of dicts with: chunk_id, doc_id, filename, version, text, score

5. get_all_doc_ids() -> list[str]
   - Scroll through all points and return unique doc_id values from payloads

Call init_collection() on module import so the collection is always ready.

Output the full content of app/retrieval/qdrant_client.py.
```

---

### PHASE 3 — Hybrid Search

---

#### TODO-08 · BM25 index + hybrid fusion
**Status:** `[ ] not started`

**Scope:**
- `app/retrieval/hybrid_search.py`
- In-memory BM25 index built from Qdrant payload at query time (acceptable for starter scale)
- `hybrid_search(query, query_vector, top_k, alpha)`:
  - alpha=1.0 → pure dense, alpha=0.0 → pure BM25
  - Normalize both score sets to [0,1] before fusion
  - RRF (Reciprocal Rank Fusion) as the merge method
  - Return merged ranked list with fused score
- Document in code comments: when to increase alpha (semantic queries) vs decrease (keyword-heavy, code, product names)

**Agent prompt:**
```
You are working on rag-production-starter, a FastAPI project.

Task: Implement hybrid search combining BM25 and dense vector retrieval.

Create app/retrieval/hybrid_search.py.

Implement:
    async def hybrid_search(
        query: str,
        query_vector: list[float],
        top_k: int = 5,
        alpha: float = 0.5
    ) -> list[dict]

Steps:
1. Fetch all chunks from Qdrant using get_all_doc_ids + scroll (or a helper),
   building a list of (chunk_id, text, metadata) tuples as the BM25 corpus.
   Build a rank_bm25.BM25Okapi index over tokenized texts (split on whitespace).

2. Score the query against BM25. Normalize scores to [0, 1].

3. Score the query_vector against Qdrant dense search (top 50 candidates).
   Normalize scores to [0, 1].

4. Fuse using Reciprocal Rank Fusion:
   fused_score = alpha * dense_rrf + (1 - alpha) * bm25_rrf
   where rrf = 1 / (rank + 60)

5. Return top_k results sorted by fused_score descending.
   Each result dict: chunk_id, doc_id, filename, version, text, score.

Add inline comments explaining:
- When to increase alpha (abstract/semantic queries)
- When to decrease alpha (exact terms, product names, code identifiers)

Output the full content of app/retrieval/hybrid_search.py.
```

---

### PHASE 4 — Governance Layer

---

#### TODO-09 · Document versioning and re-index trigger
**Status:** `[ ] not started`

**Scope:**
- `app/governance/versioning.py`
- `get_current_version(doc_id)`: query Qdrant for max version of a doc_id
- `should_reindex(doc_id, new_version)`: returns True if new_version > current
- `reindex_document(doc_id, new_chunks, new_vectors, filename, new_version)`:
  - Delete old vectors for doc_id
  - Upsert new chunks with incremented version
- Called by the ingest endpoint when doc_id already exists

**Agent prompt:**
```
You are working on rag-production-starter, a FastAPI project.

Task: Implement document versioning and re-indexing logic.

Create app/governance/versioning.py.

Implement these functions:

1. get_current_version(doc_id: str) -> int
   - Scroll Qdrant for all points with payload.doc_id == doc_id
   - Return max(payload.version) across results, or 0 if doc not found

2. should_reindex(doc_id: str, new_version: int) -> bool
   - Return True if new_version > get_current_version(doc_id)

3. async def reindex_document(
       doc_id: str,
       new_chunks: list[Chunk],
       new_vectors: list[list[float]],
       filename: str,
       new_version: int
   ) -> None
   - Call delete_by_doc_id(doc_id) to remove old vectors
   - Call upsert_chunks with new data and new_version

Import Chunk from app/ingestion/chunker.py.
Import delete_by_doc_id and upsert_chunks from app/retrieval/qdrant_client.py.

Output the full content of app/governance/versioning.py.
```

---

#### TODO-10 · Stale chunk / drift detection
**Status:** `[ ] not started`

**Scope:**
- `app/governance/drift.py`
- `get_stale_docs(days_threshold)`: returns list of doc_ids where `ingested_at` is older than threshold
- `drift_report()`: returns summary dict — total docs, stale docs, oldest doc, newest doc
- Accessible via a GET `/governance/drift` endpoint (add to `app/api/` in this TODO)
- Purpose: lets operators know which documents may need re-ingestion

**Agent prompt:**
```
You are working on rag-production-starter, a FastAPI project.

Task: Implement stale document / drift detection.

Create app/governance/drift.py with:

1. async def get_stale_docs(days_threshold: int = 30) -> list[str]
   - Scroll all Qdrant points and read payload.ingested_at (ISO UTC string)
   - Return unique doc_ids where ingested_at is older than days_threshold days from now

2. async def drift_report() -> dict
   - Scroll all points, collect ingested_at per doc_id (take earliest per doc)
   - Return:
     {
       "total_docs": int,
       "stale_docs": int,   # older than 30 days
       "oldest_doc": {"doc_id": str, "ingested_at": str},
       "newest_doc": {"doc_id": str, "ingested_at": str}
     }

Then create app/api/governance.py with a FastAPI router:
- GET /governance/drift?days_threshold=30 → calls drift_report() + get_stale_docs()
- Returns combined response
- Protected by verify_api_key dependency

Register this router in app/main.py.

Output full content of app/governance/drift.py and app/api/governance.py.
```

---

#### TODO-11 · GDPR-compliant vector deletion
**Status:** `[ ] not started`

**Scope:**
- `app/governance/deletion.py`
- `delete_document(doc_id)`: hard delete all vectors for a doc_id from Qdrant
- Expose as `DELETE /documents/{doc_id}` endpoint
- Log deletion event with timestamp and doc_id (to stdout/logger, not stored — no PII retained)
- Return confirmation with count of deleted vectors

**Agent prompt:**
```
You are working on rag-production-starter, a FastAPI project.

Task: Implement GDPR-compliant document deletion.

Create app/governance/deletion.py with:

    async def delete_document(doc_id: str) -> dict
    - Count points in Qdrant with payload.doc_id == doc_id before deleting
    - Call delete_by_doc_id(doc_id) from qdrant_client.py
    - Log to Python logger: "DELETION EVENT: doc_id={doc_id} vectors_deleted={count} at={utc_timestamp}"
    - Return {"doc_id": doc_id, "vectors_deleted": count, "deleted_at": utc_timestamp}

Then add to app/api/governance.py (from TODO-10):
    DELETE /documents/{doc_id}
    - Calls delete_document(doc_id)
    - Protected by verify_api_key
    - Returns the dict from delete_document

Output updated app/governance/deletion.py and app/api/governance.py.
```

---

### PHASE 5 — Generation & Query API

---

#### TODO-12 · LLM generation wrapper
**Status:** `[ ] not started`

**Scope:**
- `app/generation/llm.py`
- `generate_answer(query, context_chunks)`: build a system prompt + context, call OpenAI chat completion
- Model: `gpt-4o-mini` (cost-efficient default)
- System prompt instructs the model to answer only from provided context, cite sources, and say "I don't know" if context is insufficient — this is a governance signal
- Returns: answer string

**Agent prompt:**
```
You are working on rag-production-starter, a FastAPI project.

Task: Implement the LLM generation wrapper.

Create app/generation/llm.py with:

    async def generate_answer(query: str, context_chunks: list[dict]) -> str

Requirements:
- Use OpenAI async client, model: gpt-4o-mini
- Build context string from context_chunks (each chunk dict has "text", "filename", "chunk_id")
- System prompt (use this exactly):
    "You are a precise assistant. Answer the user's question using ONLY the provided
     context. If the context does not contain enough information to answer, respond
     with: 'I don't have enough information in the provided documents to answer this.'
     Always reference the source filename when you use information from it."
- User message: context block + query
- Max tokens: 1000
- Return the assistant message content as a string

Output the full content of app/generation/llm.py.
```

---

#### TODO-13 · Ingest and query endpoints
**Status:** `[ ] not started`

**Scope:**
- `app/api/ingest.py`: POST `/ingest`
  - Accept IngestRequest
  - Decode content, load document, chunk, embed, check versioning, upsert
  - Return: doc_id, chunk_count, version, strategy_used
- `app/api/query.py`: POST `/query`
  - Accept QueryRequest
  - Embed query, hybrid search, generate answer
  - Return QueryResponse with answer + sources
- Both protected by API key

**Agent prompt:**
```
You are working on rag-production-starter, a FastAPI project.

Task: Implement the ingest and query API endpoints.

Create app/api/ingest.py with a FastAPI router and endpoint:
    POST /ingest
    - Accepts IngestRequest from app/models/schemas.py
    - If content is base64 (for PDF/DOCX): decode with base64.b64decode
    - If text (markdown/plain): encode to bytes
    - Call load_document(bytes, mime_type) from app/ingestion/loader.py
    - Call chunk_document(text, strategy="semantic") from app/ingestion/chunker.py
    - Call embed_texts([c.text for c in chunks]) from app/ingestion/embedder.py
    - If doc_id exists and new version > current: call reindex_document()
    - Else: call upsert_chunks()
    - Return: {"doc_id": str, "chunk_count": int, "version": int, "strategy": str}

Create app/api/query.py with a FastAPI router and endpoint:
    POST /query
    - Accepts QueryRequest from app/models/schemas.py
    - Embed query.query using embed_texts()
    - Call hybrid_search(query, vector, top_k, alpha)
    - Call generate_answer(query, context_chunks)
    - Return QueryResponse: answer, sources (list of ChunkSource), eval_scores=None

Register both routers in app/main.py. Both are protected by verify_api_key.

Output full content of app/api/ingest.py, app/api/query.py, and updated app/main.py.
```

---

### PHASE 6 — Evaluation

---

#### TODO-14 · Ragas evaluation pipeline + MLflow logging
**Status:** `[ ] not started`

**Scope:**
- `app/evaluation/ragas_eval.py`
- `run_evaluation(query, answer, contexts)`: run Ragas metrics — faithfulness, answer_relevancy, context_recall
- `app/evaluation/mlflow_logger.py`: log eval results as an MLflow run (metrics + params)
- Expose as POST `/evaluate` endpoint in `app/api/eval.py`
- Also callable internally from POST `/query` if `run_eval=true` query param is set

**Agent prompt:**
```
You are working on rag-production-starter, a FastAPI project.

Task: Implement the Ragas evaluation pipeline with MLflow logging.

Create app/evaluation/ragas_eval.py with:

    async def run_evaluation(
        query: str,
        answer: str,
        contexts: list[str]
    ) -> dict

- Use Ragas to evaluate: faithfulness, answer_relevancy, context_recall
- Build a Ragas Dataset from the inputs (single row)
- Use OpenAI as the LLM judge (load key from settings)
- Return: {"faithfulness": float, "answer_relevancy": float, "context_recall": float}

Create app/evaluation/mlflow_logger.py with:

    def log_eval_to_mlflow(query: str, eval_scores: dict) -> None
- Start an MLflow run under experiment "rag-evaluation"
- Log params: query (truncated to 200 chars)
- Log metrics: faithfulness, answer_relevancy, context_recall
- End the run

Create app/api/eval.py with:
    POST /evaluate
    - Accepts EvalRequest, calls run_evaluation(), calls log_eval_to_mlflow()
    - Returns EvalResponse
    - Protected by API key

Update app/api/query.py:
- Add optional query param run_eval: bool = False
- If True: after generation, call run_evaluation() and log_eval_to_mlflow()
- Include scores in QueryResponse.eval_scores

Output full content of app/evaluation/ragas_eval.py, app/evaluation/mlflow_logger.py,
app/api/eval.py, and updated app/api/query.py.
```

---

### PHASE 7 — Developer Experience & Documentation

---

#### TODO-15 · Demo seed script
**Status:** `[ ] not started`

**Scope:**
- `scripts/seed_demo.py`
- Loads 2–3 sample documents (include small sample docs in `scripts/samples/`)
- Ingests them via the API (calls POST /ingest)
- Runs a sample query and prints the answer + sources
- Runs evaluation and prints scores
- Purpose: `python scripts/seed_demo.py` = working demo in under 2 minutes

**Agent prompt:**
```
You are working on rag-production-starter, a FastAPI project.

Task: Create a demo seed script and sample documents.

Create scripts/samples/ with three small text files:
- company_policy.txt: ~300 words of plausible company AI usage policy
- technical_overview.md: ~300 words markdown doc about a fictional ML platform
- product_faq.txt: ~200 words FAQ about a fictional product

Create scripts/seed_demo.py:
- Uses httpx (or requests) to call the local API at http://localhost:8000
- Sets X-API-Key header from env var API_KEY (default: "dev-key")
- Ingests all three sample files via POST /ingest
- Runs POST /query with query: "What is the company policy on AI usage?"
- Prints the answer and sources in a readable format
- Runs POST /evaluate on the result and prints scores

Add a __main__ guard. The script should be runnable as:
    API_KEY=dev-key python scripts/seed_demo.py

Output all sample files and the full seed script.
```

---

#### TODO-16 · README and ARCHITECTURE docs
**Status:** `[ ] not started`

**Scope:**
- `README.md`: thesis statement, quickstart (3 commands), what's included, what's out of scope, link to docs/
- `ARCHITECTURE.md`: decision log — why Qdrant, why hybrid search, why these chunking strategies, why Ragas, GDPR deletion design, drift detection rationale
- `docs/chunking-strategy.md`: decision guide with comparison table
- `docs/hybrid-search.md`: how the fusion works, when to tune alpha
- `docs/data-governance.md`: versioning, drift, deletion walkthrough
- `docs/evaluation.md`: how to interpret Ragas scores, what scores to aim for

**Agent prompt:**
```
You are working on rag-production-starter, a FastAPI project.
This is a portfolio/showcase project for AI platform consulting.
The target audience is a mid-sized company's technical lead evaluating
whether to hire a consultant to build their first RAG system.

Task: Write all documentation files.

README.md must:
- Open with: "Most RAG tutorials get you to a working demo. This is what comes after."
- Quickstart section: exactly 3 commands to go from clone to running demo
- "What this covers" section (chunking, hybrid search, governance, eval)
- "What this intentionally does NOT cover" section (fine-tuning, auth beyond API key, multi-tenancy)
- Link to docs/ for deeper reading

ARCHITECTURE.md must:
- Be written as a decision log, not a description
- For each major decision (Qdrant, hybrid search, chunking strategies, Ragas, GDPR deletion):
  explain WHAT was chosen, WHY, and what was explicitly rejected and why

docs/chunking-strategy.md: include a comparison table of fixed vs semantic vs late chunking
with columns: strategy, best for, worst for, retrieval quality, complexity

docs/hybrid-search.md: explain BM25 + dense fusion, RRF, alpha tuning guidance

docs/data-governance.md: explain versioning flow, drift detection, and GDPR deletion
with a sequence diagram in ASCII or mermaid

docs/evaluation.md: explain each Ragas metric, what a "good" score looks like,
and how to act on low scores

Output the full content of all 6 files.
```

---

### PHASE 8 — Tests

---

#### TODO-17 · Core unit tests
**Status:** `[ ] not started`

**Scope:**
- `tests/test_chunker.py`: test all three strategies produce valid Chunk objects, token counts within bounds, late chunking produces parent+child
- `tests/test_hybrid_search.py`: test alpha=1.0 produces dense-only ordering, alpha=0.0 BM25-only, fusion produces merged results
- `tests/test_ingest.py`: test loader handles all four formats, raises on unsupported mime
- `tests/test_eval.py`: mock Ragas call, assert EvalResponse fields are floats in [0,1]

**Agent prompt:**
```
You are working on rag-production-starter, a FastAPI project.

Task: Write unit tests for the core modules.

Use pytest. Mock all external calls (Qdrant, OpenAI, Ragas) using unittest.mock or pytest-mock.

tests/test_chunker.py:
- Test "fixed" strategy: output chunks have token_count <= 512
- Test "semantic" strategy: no chunk exceeds 512 tokens, no mid-sentence splits
- Test "late" strategy: output contains both parent and child chunks,
  children have non-null parent_chunk_id

tests/test_ingest.py (loader):
- Test PDF loading returns non-empty string (use a minimal PDF fixture)
- Test markdown loading strips markdown syntax
- Test plain text returns decoded string
- Test unsupported mime raises ValueError

tests/test_hybrid_search.py:
- Mock dense_search and BM25 results
- Test alpha=1.0 ranks dense results first
- Test alpha=0.0 ranks BM25 results first
- Test alpha=0.5 produces a merged ranking

tests/test_eval.py:
- Mock ragas evaluate() to return known scores
- Test run_evaluation returns dict with faithfulness, answer_relevancy, context_recall
- Assert all values are floats

Output all test files with full content.
```

---

## Non-Goals (explicitly out of scope)

- Model fine-tuning
- Multi-tenancy or per-user isolation
- Auth beyond API key (no OAuth, no JWT)
- Streaming responses
- Frontend UI
- Async ingestion queue (synchronous is fine for starter scale)
- Custom embedding models

---

## Agent Working Rules

1. Work one TODO at a time. Do not start the next until the current is marked `[done]`.
2. Mark status as `[in progress]` when starting, `[done]` when complete.
3. Output full file contents — no summaries, no diffs unless asked.
4. Do not invent features not listed in the TODO scope.
5. If a TODO depends on a previous one, read that file first before writing.
6. After completing all TODOs in a phase, run the seed script or relevant tests to verify integration before moving to the next phase.
