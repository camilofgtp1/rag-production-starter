# Hybrid Search

> *"Hybrid search is the hedge against your own uncertainty. It's easier than choosing between keyword and semantic search, but it adds complexity. Is it worth it? Probably. Probably not. It depends."*

This document explains how the hybrid search works and why we made the implementation choices we did.

---

## The Problem Hybrid Search Solves

Vector search (dense) and keyword search (sparse) have complementary failure modes:

| Approach | Strength | Weakness |
|----------|----------|----------|
| **Dense** | Semantic similarity, synonyms | Misses exact matches, poor with jargon |
| **Sparse (BM25)** | Exact term matching | Misses semantic intent |

Hybrid search tries to get the benefits of both. But it's not free — it adds complexity, latency, and more parameters to tune.

**The honest question to ask**: Do you actually need hybrid search?

If your queries are mostly semantic questions ("what is the policy on..."), pure vector search might work fine. If your queries are heavily terminology-based (product names, codes, exact phrases), BM25 might be sufficient.

We included hybrid search because **the default case is unclear**. In practice, users ask a mix. But if you're building for a specific use case, measure whether you actually need both signals before adding this complexity.

---

## How Our Implementation Works

We use **Reciprocal Rank Fusion (RRF)** to combine results. Here's why not something else:

### Why RRF, Not Learned Weights?

You could train a small model to predict optimal weights per query type. We chose RRF because:

1. **No training data required**: Learned weights need query-result pairs to learn from. RRF works out of the box.
2. **Robust to different query types**: RRF handles the long tail reasonably well without tuning.
3. **Interpretable**: You can explain exactly why a result ranked highly. This matters for debugging.

### The RRF Formula

```
fused_score = alpha * dense_rrf + (1 - alpha) * bm25_rrf
```

where:
```
rrf = 1 / (rank + 60)
```

The `60` is an arbitrary constant (commonly used). It determines how much rank position matters. Higher = rank position matters more.

### What Alpha Actually Does

- **alpha = 1.0**: Pure vector search. BM25 contributes nothing.
- **alpha = 0.0**: Pure keyword search. Vectors contribute nothing.
- **alpha = 0.5**: Equal weight to both signals.

---

## When to Tune Alpha

### Increase Alpha (Toward 1.0) When:

- Your queries are conversational or abstract
- Users phrase questions in their own words
- Synonym variations matter more than exact terms

**Example**: "What does the company policy say about using AI tools?" — This benefits from semantic understanding. The exact words "AI" might appear as "artificial intelligence" or "machine learning" in documents.

### Decrease Alpha (Toward 0.0) When:

- Your domain has specific terminology
- Product names, codes, identifiers matter
- Users typically search for exact phrases

**Example**: "SKU-12345 specifications" or "API endpoint /v1/users" — These require exact matching. Semantic search might find related but wrong results.

---

## The Truth About Alpha Tuning

Here's what nobody tells you:

> **Most queries perform reasonably well at alpha=0.5. The marginal improvement from tuning is usually small.**

The cases where alpha matters significantly are the edges of your query distribution. The question is whether those edge cases matter for your use case.

### Practical Advice

1. **Start at 0.5.** It's a reasonable default that works for mixed query types.

2. **Don't tune without evidence.** Run eval queries at different alpha values. If there's no meaningful improvement, don't complicate your system.

3. **Consider query classification.** If you can classify queries as "keyword-heavy" vs "semantic" at query time, you could route to different alpha values. But that's added complexity — only do it if eval proves it helps.

4. **Watch for regression.** Tuning for one query type can hurt others. Check your overall eval scores, not just the cases you're optimizing for.

---

## Implementation Details

### BM25

We use `rank_bm25.BM25Okapi` with whitespace tokenization. This is simpler than alternatives but works well enough.

**Limitation**: BM25 with whitespace tokenization doesn't handle:
- Hyphenated words well
- Case variations (we lowercase everything)
- Phrase queries

For production-grade keyword search, you'd want something more sophisticated. But for a starter project, this is sufficient.

### Normalization

Both BM25 and dense scores are normalized to [0,1] before fusion. This is critical — without normalization, the fusion would be dominated by whichever signal has larger raw values.

### K Parameter in RRF

The `k=60` constant in the RRF formula determines how much position matters:
- Higher k = less position sensitivity
- Lower k = position matters more

60 is a common default. It works reasonably for typical information retrieval workloads.

---

## When Hybrid Search Isn't Enough

If you're finding that hybrid search still doesn't give you the retrieval quality you need, consider:

1. **Reranking**: Retrieve more candidates (20-50) with hybrid search, then rerank with a cross-encoder model. This is expensive but more accurate.

2. **Query expansion**: Rewrite the user query (expand with synonyms, decompose compound questions) before retrieval.

3. **Chunking review**: Honestly, your chunking strategy is more likely the bottleneck. Review that before over-tuning hybrid search.

4. **Training data**: If you have enough query-result pairs, you could train a learning-to-rank model. But that's significant investment.

---

## What Matters Most

> **Fix chunking before you obsess over alpha tuning.**

In our experience, chunking quality problems manifest as retrieval failures. Tuning alpha can sometimes compensate, but it's treating the symptom, not the cause.

Hybrid search is a reasonable hedge. It's not a silver bullet. Measure, don't assume.
