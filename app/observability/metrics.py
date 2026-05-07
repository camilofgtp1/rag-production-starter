from prometheus_client import Counter, Gauge, Histogram

REQUESTS_TOTAL = Counter(
    "rag_requests_total",
    "Total HTTP requests",
    ["endpoint", "method", "status_code"],
)

REQUEST_DURATION = Histogram(
    "rag_request_duration_seconds",
    "HTTP request duration",
    ["endpoint"],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0],
)

RETRIEVAL_DURATION = Histogram(
    "rag_retrieval_duration_seconds",
    "Retrieval pipeline duration",
    buckets=[0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

GENERATION_DURATION = Histogram(
    "rag_generation_duration_seconds",
    "LLM generation duration",
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0],
)

CHUNKS_RETRIEVED = Histogram(
    "rag_chunks_retrieved_total",
    "Number of chunks retrieved per query",
    buckets=[1, 2, 3, 5, 8, 10, 15, 20, 30, 50],
)

TOKENS_TOTAL = Counter(
    "rag_tokens_total",
    "Total tokens used",
    ["type"],
)

COST_USD_TOTAL = Counter(
    "rag_cost_usd_total",
    "Total estimated cost in USD",
)

DOCUMENTS_INGESTED = Counter(
    "rag_documents_ingested_total",
    "Total documents ingested",
    ["chunking_strategy"],
)

EVALUATION_SCORES = Gauge(
    "rag_evaluation_scores",
    "Latest evaluation scores",
    ["metric"],
)
