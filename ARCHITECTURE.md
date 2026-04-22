# Architecture Decision Log

> *"Every non-obvious decision is a tradeoff. Here's why we made the calls we did — and why you might make different ones."*

This document explains the key architectural decisions made in this project, the reasoning behind them, and the tradeoffs we explicitly accepted. This is written for senior engineers evaluating whether to adopt pieces of this architecture.

---

## Vector Database: Qdrant

**Decision**: Use Qdrant as the vector database.

### Why This, Not Something Else?

We chose Qdrant because it hits the specific sweet spot of **operational simplicity + production features** without forcing you into a cloud contract immediately. Let me be direct about what matters:

**What Qdrant gets right:**
- The Python client actually works well. This sounds trivial but try managing Pinecone's client updates across 12 microservices sometime.
- Local Docker development is first-class. You can run the entire stack on a laptop. For a starter project, this dramatically lowers the barrier to debugging.
- The hybrid filtering (vector + metadata) is built-in. No gluing together separate systems.
- Migration path to cloud is trivial — just change the URL. This is worth more than you'd think when you're negotiating vendor contracts.

**What we traded away:**
- **Managed infrastructure options**: Pinecone and Weaviate have more mature managed offerings. If you absolutely cannot operate your own vector DB and don't want to use cloud Qdrant, this is a real consideration.
- **Ecosystem maturity**: Pinecone has better integrations with LangChain, LlamaIndex out of the box. You'll write slightly more glue code.
- **Some advanced features**: Qdrant's dense-only approach means sparse embeddings (like SPADE) require workarounds. If you need those, look elsewhere.

**The honest take**: For 90% of companies building their first RAG, Qdrant is the right call. The "right" answer is usually "whatever your team can debug at 2am." We chose for operability, not theoretical performance.

---

## Embedding Model: OpenAI text-embedding-3-small

**Decision**: Use OpenAI's text-embedding-3-small for embeddings.

### The Tradeoff Nobody Talks About

This is the part of RAG systems that's actually **easy**. Embedding model choice matters far less than chunking strategy and retrieval quality. Let me say that again because it's counterintuitive:

> **Chunking quality >> Embedding model choice**

Here's what we accepted:

**What works:**
- The quality-to-cost ratio of text-embedding-3-small is exceptional. It's roughly 5x cheaper than ada-002 with comparable quality.
- 1536 dimensions plays nicely with Qdrant's defaults.
- Latency is acceptable for synchronous APIs (50-200ms typically).

**What we traded:**
- **No control over the model**: If OpenAI changes the model, your embeddings drift. This has real implications for systems that need deterministic behavior.
- **Vendor lock-in**: Your embeddings only work with OpenAI-compatible endpoints. This matters if you want to swap to local models later.
- **Latency**: For truly real-time applications, local embeddings (BGE, E5) beat OpenAI. But they introduce infrastructure complexity.

**When to care about this decision**: Honestly? Almost never, for most use cases. The bigger risk is choosing a chunking strategy that destroys your context boundaries.

---

## Chunking: The Decision That Actually Matters

**Decision**: Implement fixed, semantic, and late chunking strategies.

### This Is Where Senior Engineers Disagree

Chunking is where most RAG tutorials completely fail to provide guidance. The reason is simple: **there's no universally correct answer, and the right choice depends on your data shape.**

**Fixed Chunking — The Practical Default**

```python
chunk_size=512, overlap=50
```

This works when:
- Your documents are relatively uniform
- You don't have complex hierarchies
- You want predictable behavior and easy debugging

The downside? You will absolutely split sentences mid-way. If your documents have any nuance, you're losing it. But for code, structured data, and homogeneous documents, this is fine.

**Semantic Chunking — The Better Default for Text**

We chose this as the default for a reason. Splitting on paragraph boundaries **before** applying a token limit preserves more signal. You're less likely to break a coherent argument in half.

The tradeoff: It's slower and slightly less predictable. You also need to handle edge cases where paragraphs exceed your token limit (we handle this by falling back to sentence-splitting).

**Late Chunking — Only If You Need It**

This is the "advanced" option that sounds great in architecture reviews and fails in practice. Here's the honest assessment:

- Parent-child chunking makes sense when you have **very large documents** (>10k tokens) where small chunks lose context
- It doubles your storage and retrieval complexity
- The retrieval logic needs to know to fetch the parent chunk for generation

We included it because some use cases genuinely need it. We also included it because senior engineers on your team will ask "what about parent-child?" and this gives you an answer. But if you're reaching for this as your first choice, pause and ask whether your documents are actually that large.

**The meta-decision**: Three strategies is probably one too many for a starter project. We could have picked one. But the cost of adding options is low, and the cost of telling a senior engineer "you can't do that" is high.

---

## Hybrid Search: BM25 + Dense Fusion

**Decision**: Combine BM25 keyword search with dense vector search using Reciprocal Rank Fusion.

### Why RRF Over Learned Weights?

You could train a small model to weight BM25 vs dense scores. We chose not to because:

1. **You need training data to get right**. Without query-result pairs to learn from, you're guessing.
2. **RRF is robust**. It works reasonably well across query types without tuning.
3. **Interpretability**. You can explain to PMs exactly what happened: "the result ranked high because it matched semantically OR it matched by keyword."

### The Alpha Parameter

We made `alpha` configurable (0.0 to 1.0). Here's the unopinionated version: tune it.

Here's the opinionated version from experience:

> **Default to 0.5. Change it only when you have evidence.**

The reason is simple: most queries benefit from both signal types. The cases where you want pure keyword (alpha=0.0) or pure semantic (alpha=1.0) are rare and tend to be discoverable through eval.

The queries where you want pure keyword:
- Product codes ("SKU-12345")
- Exact identifiers
- Proper nouns in specialized domains

The queries where you want pure semantic:
- Conversational, ambiguous questions
- When your BM25 index is poor quality

**Practical advice**: Don't obsess over alpha tuning. Fix your chunking first. The biggest retrieval failures are almost always due to bad chunk boundaries, not suboptimal fusion weights.

---

## Evaluation: Ragas + MLflow

**Decision**: Use Ragas for evaluation metrics, logged to MLflow.

### The Uncomfortable Truth About RAG Evaluation

We included evaluation because **you need it to improve systematically**. But let's be honest about what these metrics actually measure:

| Metric | What It Actually Measures |
|--------|--------------------------|
| Faithfulness | Does the answer stay grounded? (Low score = hallucination) |
| Answer Relevancy | Does the answer address the question? (Low score = question answered poorly) |
| Context Recall | Did we retrieve relevant context? (Low score = bad retrieval) |

**What they DON'T measure:**
- Answer correctness (is the information actually true?)
- User satisfaction
- Latency and cost

**Why we chose Ragas**:
- It's the closest thing to a standard in RAG evaluation
- It integrates with the LLM you already have (OpenAI)
- The metrics map to actionable improvements

**Tradeoffs we accepted:**
- **Cost**: Each evaluation costs OpenAI credits. Don't run eval on every query. Sample periodically.
- **Latency**: Evaluation adds 2-5 seconds. Again, don't run on every request.
- **Metric instability**: These scores can fluctuate. Track trends, not absolute values.

### The More Important Question Nobody Asks

If you want to evaluate RAG seriously, ask yourself:

1. **What's your accuracy requirement?** (e.g., "90% of queries must have faithfulness > 0.8")
2. **What queries matter most?** (Your evaluation set should weight these higher)
3. **Who acts on these scores?** (If the answer is "nobody," save yourself the trouble and skip eval)

---

## Data Governance: Versioning, Drift, GDPR

**Decision**: Implement document versioning, drift detection, and hard deletion.

### Why This Matters More Than You Think

In our experience, governance is where production RAG systems die. Not from retrieval failures, but from:

- **Stale content**: The system keeps serving old answers to new questions
- **Uncontrolled growth**: Nobody knows what's in the index anymore
- **Compliance risk**: GDPR deletion requests come in and you can't fulfill them

We made deliberate choices to address these:

**Versioning**: Every document gets a version number. Re-ingesting increments it. This seems simple but it's the foundation for everything else.

**Drift Detection**: Documents older than 30 days are flagged. This is arbitrary but functional. You need to review them periodically.

**Hard Delete**: GDPR requires you actually delete data. Soft-delete or tombstoning doesn't cut it. We log deletions for audit purposes but don't retain any trace.

**What we explicitly didn't do:**
- Automatic re-indexing of stale documents (too risky without human review)
- ML-based drift detection (false positives in our experience)
- Version diffing (complexity not justified at starter scale)

---

## What We Left Out (And Why)

These are all reasonable choices that other projects make. We're explicit about why we said no:

| Feature | Why We Left It Out |
|---------|-------------------|
| Multi-tenancy | Enormous complexity. Different collection-per-tenant strategies have tradeoffs. Wait until you need it. |
| Streaming | Nice-to-have but adds significant complexity. Non-streaming works fine for most RAG. |
| Async ingestion | Synchronous is simpler and sufficient for starter scale. Add a queue when you need one. |
| Custom embedding models | Would require infrastructure (GPU hosting). Not worth the operational burden yet. |
| Fine-tuning | Out of scope for retrieval. If you need this, you're past "starter" scale. |

---

## The Senior Take

Here's what actually matters when you're building this for production:

1. **Start simple. Add complexity only when data proves it's necessary.** The default should be "this works and I can debug it."

2. **Measure what you fix.** If you're tuning alpha, you should have eval data showing the previous value was suboptimal.

3. **Operationalize governance early.** The time to add versioning is at the start, not after you have 50 documents you can't account for.

4. **Chunking is the hardest problem.** More effort goes into chunking than any other single decision. Don't let anyone tell you otherwise.

5. **Your eval set defines your system.** What queries you test against determines what gets optimized. Make sure your eval set represents production traffic.

This project gives you a functional starting point. The decisions embedded here represent our best judgment for a general case. Your specific use case almost certainly has factors that would lead to different choices. That's fine — the important part is understanding why you made them.

---

*This document is a living artifact. As we learn more, we'll update it. If you disagree with a decision, that's not a bug — it's an opportunity to make a different tradeoff that fits your context better.*
