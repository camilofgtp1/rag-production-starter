# rag-production-starter

[![pipeline status](https://gitlab.com/camilofgtp1/rag-production-starter/badges/master/pipeline.svg)](https://gitlab.com/camilofgtp1/rag-production-starter/-/pipelines)

*Most RAG tutorials get you to a working demo. This is what comes after.*

A production-ready RAG starter kit for teams who've outgrown tutorials. We cover the parts that tutorials skip: chunking strategy, hybrid search, governance, and evaluation. Built to be understood, not just run.

## The Pitch

If you're a senior engineer building your company's first RAG system, you've noticed something: the tutorials all end at "here's how to query a vector DB."

They don't tell you:
- What chunking strategy actually works for your documents
- When to use keyword search vs vector search (and why the answer is "both")
- How to handle stale content and compliance requirements
- How to measure if your system is actually working

This project does. It's the skeleton of a production system — opinionated, documented, and extensible.

## Quickstart

```bash
# 1. Configure
cp .env.example .env
# Edit .env with your API keys (OpenAI minimum)

# 2. Start infrastructure
docker compose up -d

# 3. Run the demo
python scripts/seed_demo.py
```

The demo ingests sample documents, runs a query, and shows evaluation scores. You'll see exactly what's happening at each step.

## What You Get

| Component | Implementation | Senior Take |
|-----------|---------------|-------------|
| **Vector DB** | Qdrant | Simplest path to production. Local Docker to managed with no code change. |
| **Embeddings** | text-embedding-3-small | Good enough for most cases. The model matters less than chunking. |
| **Chunking** | Fixed, semantic, late | We made choices. Read the docs to understand why. |
| **Retrieval** | Hybrid BM25 + dense | We default to alpha=0.5. Tune if you have evidence it matters. |
| **Generation** | GPT-4o-mini | Cost-effective. Switch to GPT-4o if you need more capability. |
| **Evaluation** | Ragas + MLflow | Metrics are proxies, not truth. Track trends, not thresholds. |
| **Governance** | Versioning, drift, GDPR | Minimum viable. Extend as compliance requires. |

## What We Deliberately Left Out

These are all reasonable features. We left them out because they'd make this starter project too complex, or because they're problems for later:

- **Multi-tenancy**: Massive complexity increase. Wait until you need it.
- **Streaming**: Nice-to-have, but adds significant infrastructure complexity.
- **Async ingestion**: Synchronous is simpler and sufficient for most starter use cases.
- **Custom embedding models**: Requires GPU infrastructure. Out of scope.
- **Fine-tuning**: Not a retrieval problem. Different project entirely.

## Documentation

Start with [ARCHITECTURE.md](ARCHITECTURE.md) — it explains why we made the decisions we did, including what we traded off.

Then the deep dives:

- [Chunking Strategy](docs/chunking-strategy.md) — The hardest problem in RAG, explained
- [Hybrid Search](docs/hybrid-search.md) — Why hybrid, when to tune alpha
- [Data Governance](docs/data-governance.md) — Versioning, drift detection, GDPR
- [Evaluation](docs/evaluation.md) — What metrics actually measure

## API Reference

All endpoints require `X-API-Key` header except `/health`.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/ingest` | Ingest a document |
| POST | `/query` | Query with RAG |
| POST | `/evaluate` | Run evaluation |
| GET | `/governance/drift` | Get drift report |
| DELETE | `/governance/documents/{doc_id}` | Delete document |

## Running Locally

```bash
# Install dependencies (we use uv or pip)
pip install -e .

# Run the API
uvicorn app.main:app --reload

# Run tests
pytest

# Run the seed demo
python scripts/seed_demo.py
```

## Contributing

This is a starter kit, not a product. Pull requests welcome for:

- Bug fixes
- Documentation improvements
- Additional chunking strategies
- Evaluation metrics

If you're considering a major feature addition: open an issue first to discuss. We want to keep this focused.

## The Philosophy

1. **Operational simplicity over theoretical elegance.** The system should be debuggable at 2am.
2. **Default to explicitness.** Don't surprise users with hidden behavior.
3. **Document the tradeoffs.** Every decision has costs. We try to make those explicit.
4. **Measure what matters.** Eval metrics are signals, not destinations.

## License

MIT. Use it. Modify it. Don't blame us if it doesn't work for your specific use case.

---

*This project was built to solve a real problem: bridging the gap between "hello world" RAG tutorials and production systems that don't embarrass you in front of your team.*
