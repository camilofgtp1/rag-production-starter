# rag-production-starter

[![GitHub CI](https://github.com/camilofgtp1/rag-production-starter/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/camilofgtp1/rag-production-starter/actions)
[![GitLab CI](https://gitlab.com/camilofgtp1/rag-production-starter/badges/main/pipeline.svg)](https://gitlab.com/camilofgtp1/rag-production-starter/-/pipelines)

*Most RAG tutorials get you to a working demo. This is what comes after.*

A production-ready RAG starter kit for teams who've outgrown tutorials. We cover the parts that tutorials skip: chunking strategy, hybrid search, governance, evaluation, observability, and tracking. Built to be understood, not just run.

## The Pitch

If you're a senior engineer building your company's first RAG system, you've noticed something: the tutorials all end at "here's how to query a vector DB."

They don't tell you:
- What chunking strategy actually works for your documents
- When to use keyword search vs vector search (and why the answer is "both")
- How to handle stale content and compliance requirements
- How to measure if your system is actually working
- How to observe, monitor, and track your system over time

This project does. It's the skeleton of a production system — opinionated, documented, and extensible.

## Quickstart

```bash
# 1. Configure
cp .env.example .env
# Edit .env with your API keys (OpenAI minimum)

# 2. Install dependencies (required for the seed demo script)
pip install -e .

# 3. Start all services
docker compose up -d

# 4. Run the demo
python scripts/seed_demo.py
```

`docker compose up -d` starts five services: **app**, **Qdrant**, **MLflow**, **Prometheus**, and **Grafana** on a shared Docker network. No manual configuration needed.

Grafana opens at [localhost:3000](http://localhost:3000) with a pre-provisioned dashboard. MLflow at [localhost:5000](http://localhost:5000) shows runs with latency, cost, and evaluation metrics.

## What You Get

| Component | Implementation | Senior Take |
|-----------|---------------|-------------|
| **Vector DB** | Qdrant | Simplest path to production. Local Docker to managed cloud with no code change. |
| **Embeddings** | text-embedding-3-small | Good enough for most cases. The model matters less than chunking. |
| **Chunking** | Fixed, semantic, late | Selectable per-ingest request. Read the docs to understand the tradeoffs. |
| **Retrieval** | Hybrid BM25 + dense (RRF fusion) | We default to alpha=0.5. Tune if you have evidence it matters. |
| **Generation** | GPT-4o-mini | Cost-effective. Provider abstraction makes switching trivial. |
| **Evaluation** | Ragas + MLflow | Real scores on every eval run. Metrics are proxies, not truth. Track trends, not thresholds. |
| **Governance** | Versioning, drift, GDPR | Minimum viable. Extend as compliance requires. |
| **Metrics** | Prometheus | Request rate, error rate, latencies p50/p95, token usage, cost, eval scores. |
| **Dashboards** | Grafana | Pre-provisioned dashboard — open localhost:3000, zero setup. |
| **Tracking** | MLflow (experiments) | All queries, ingestions, and evaluations logged with latency and cost metrics. |
| **Provider** | ModelProvider protocol | Swap OpenAI for any provider by implementing the protocol. |

## What We Deliberately Left Out

These are all reasonable features. We left them out because they'd make this starter project too complex, or because they're problems for later:

- **Multi-tenancy**: Massive complexity increase. Wait until you need it.
- **Streaming**: Nice-to-have, but adds significant infrastructure complexity.
- **Async ingestion**: Synchronous is simpler and sufficient for most starter use cases.
- **Custom embedding models**: Requires GPU infrastructure. Out of scope.
- **Fine-tuning**: Not a retrieval problem. Different project entirely.

## Common Failures This Prevents

These aren't hypothetical. They're the things that broke in production before this project existed.

**Retrieval that works in demos, fails on real queries**
Keyword search misses synonyms. Vector search misses product codes and exact identifiers. Neither alone is sufficient. The hybrid search with tunable alpha lets you slide the balance toward what your data actually needs — without rewriting your retrieval logic when you discover the default was wrong.

**Chunks that destroy meaning at boundaries**
Fixed-size chunking splits sentences mid-thought. You get chunks like "the threshold for triggering an alert is" and "15 percent above baseline" — two separate vectors that each retrieve nonsense in isolation. Semantic chunking respects paragraph boundaries. This one change moves eval scores more than any retrieval tuning.

**Stale documents that nobody notices**
A policy changes. The new version gets uploaded. Without versioning, the old and new vectors coexist in the index. Queries return whichever chunks score higher — sometimes old, sometimes new, always unpredictable. Document versioning with hard re-indexing on version bump fixes this silently.

**GDPR deletion requests with no implementation**
Someone asks for their data to be deleted. You grep for their name in the codebase and realize vectors aren't keyed by anything useful. Hard deletion by doc_id with a logged audit trail is the minimum you need before this becomes a legal problem, not an engineering problem.

**Evaluation theater**
Running Ragas once at project launch and calling it "evaluated." Evaluation without MLflow tracking means you have no idea if last week's chunking change improved or degraded retrieval quality. Metrics logged per run give you actual signal on what changed and why.

**The demo that doesn't survive first contact with real documents**
Sample documents are clean, short, and well-structured. Production documents are PDFs with tables, DOCX files with tracked changes, Markdown with code blocks. The ingestion pipeline handles all four formats with a single interface — so the format your client actually uses doesn't become a week-long integration project.

**Observability that requires a second project**
Prometheus scrapes metrics from the app, Grafana serves a pre-provisioned dashboard, and MLflow tracks every operation. All three start with a single `docker compose up -d`. No separate setup, no configuration wrestling.

## Documentation

Start with [ARCHITECTURE.md](ARCHITECTURE.md) — it explains why we made the decisions we did, including what we traded off.

Then the deep dives:

- [Chunking Strategy](docs/chunking-strategy.md) — The hardest problem in RAG, explained
- [Hybrid Search](docs/hybrid-search.md) — Why hybrid, when to tune alpha
- [Data Governance](docs/data-governance.md) — Versioning, drift detection, GDPR
- [Evaluation](docs/evaluation.md) — What metrics actually measure

## API Reference

All endpoints require `X-API-Key` header except `/health` and `/metrics`.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/metrics` | Prometheus metrics endpoint |
| POST | `/ingest` | Ingest a document (with selectable chunking strategy) |
| POST | `/query` | Query with RAG (returns latency, token counts, cost) |
| POST | `/evaluate` | Run Ragas evaluation |
| GET | `/governance/drift` | Get drift report |
| DELETE | `/governance/documents/{doc_id}` | Delete document |

## Running Locally

```bash
# Install dependencies (we use uv or pip)
pip install -e .

# Start all services (app, Qdrant, MLflow, Prometheus, Grafana)
docker compose up -d

# Run the API standalone (for development with hot reload)
uvicorn app.main:app --reload

# Run tests
pytest

# Run the seed demo
python scripts/seed_demo.py

# Access services:
# - App API:      http://localhost:8001
# - MLflow UI:    http://localhost:5000
# - Prometheus:   http://localhost:9090
# - Grafana:      http://localhost:3000
```

## MLflow Tracking

Every operation logs to MLflow for observability and audit. MLflow failures never raise exceptions — tracking is fire-and-forget:

| Operation | Tracked |
|-----------|---------|
| Ingestion | filename, strategy, chunk count, tokens, version, latency_ms |
| Query | query, alpha, top_k, model, retrieval_latency_ms, generation_latency_ms, token counts, cost |
| Evaluation | faithfulness, answer_relevancy, context_recall |
| Drift Detection | threshold, stale doc count, stale doc IDs |
| Deletion | doc_id, vectors deleted, timestamp |
| Version Change | doc_id, old/new version, timestamp |

Open the MLflow UI at [localhost:5000](http://localhost:5000) to compare runs and track trends.

## Prometheus Metrics

Available at `/metrics` and scraped automatically by the bundled Prometheus instance:

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `rag_requests_total` | Counter | endpoint, method, status_code | Total HTTP requests |
| `rag_request_duration_seconds` | Histogram | endpoint | Request latency |
| `rag_retrieval_duration_seconds` | Histogram | | Retrieval pipeline latency |
| `rag_generation_duration_seconds` | Histogram | | LLM generation latency |
| `rag_chunks_retrieved_total` | Histogram | | Chunks retrieved per query |
| `rag_tokens_total` | Counter | type (prompt/completion) | Token usage |
| `rag_cost_usd_total` | Counter | | Estimated cost in USD |
| `rag_documents_ingested_total` | Counter | chunking_strategy | Documents ingested |
| `rag_evaluation_scores` | Gauge | metric | Latest evaluation scores |

## Grafana Dashboard

Grafana starts pre-configured with a Prometheus datasource and a pre-provisioned RAG Platform dashboard. Open [localhost:3000](http://localhost:3000) — no login required (anonymous access enabled).

Panels include: request rate, error rate, latency p50/p95, retrieval vs generation latency, chunks retrieved, token usage, estimated cost, and evaluation score gauges.

## Contributing

This is a starter kit, not a product. Pull requests welcome for:

- Bug fixes
- Documentation improvements
- Additional chunking strategies
- Evaluation metrics
- New model providers

If you're considering a major feature addition: open an issue first to discuss. We want to keep this focused.

## The Philosophy

1. **Operational simplicity over theoretical elegance.** The system should be debuggable at 2am.
2. **Default to explicitness.** Don't surprise users with hidden behavior.
3. **Document the tradeoffs.** Every decision has costs. We try to make those explicit.
4. **Measure what matters.** Eval metrics, latency, and cost are signals, not destinations.

## License

MIT. Use it. Modify it. Don't blame us if it doesn't work for your specific use case.

---

*This project was built to solve a real problem: bridging the gap between "hello world" RAG tutorials and production systems that don't embarrass you in front of your team.*
