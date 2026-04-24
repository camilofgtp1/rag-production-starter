# rag-production-starter

[![GitHub lint](https://github.com/camilofgtp1/rag-production-starter/actions/workflows/ci.yml/badge.svg?branch=main&job=lint)](https://github.com/camilofgtp1/rag-production-starter/actions)
[![GitHub test](https://github.com/camilofgtp1/rag-production-starter/actions/workflows/ci.yml/badge.svg?branch=main&job=test)](https://github.com/camilofgtp1/rag-production-starter/actions)
[![GitHub docker](https://github.com/camilofgtp1/rag-production-starter/actions/workflows/ci.yml/badge.svg?branch=main&job=docker)](https://github.com/camilofgtp1/rag-production-starter/actions)
[![GitLab lint](https://gitlab.com/camilofgtp1/rag-production-starter/badges/main/pipeline.svg?stage=lint)](https://gitlab.com/camilofgtp1/rag-production-starter/-/pipelines)
[![GitLab test](https://gitlab.com/camilofgtp1/rag-production-starter/badges/main/pipeline.svg?stage=test)](https://gitlab.com/camilofgtp1/rag-production-starter/-/pipelines)
[![GitLab build](https://gitlab.com/camilofgtp1/rag-production-starter/badges/main/pipeline.svg?stage=build)](https://gitlab.com/camilofgtp1/rag-production-starter/-/pipelines)

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
