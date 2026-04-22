# Hybrid Search

> *"Hybrid search is what you reach for when you're not sure whether your users speak your documents' language. Which is most of the time."*

This document explains how the hybrid search works and why we made the implementation choices we did.

---

## The Problem Hybrid Search Solves

Vector search and keyword search fail in complementary ways:

| Approach | Strength | Failure Mode |
|----------|----------|--------------|
| **Dense (vector)** | Semantic similarity, synonyms, paraphrase | Misses exact matches, unreliable with jargon and codes |
| **Sparse (BM25)** | Exact term matching, predictable | Misses semantic intent, no synonym understanding |

Hybrid search tries to get the benefits of both. But it adds complexity and a parameter to tune — which means it can also add a new failure mode if you set it wrong and don't measure.

**The question to ask before implementing this**: Do you actually know which failure mode is hurting you?

If your users ask conversational questions ("what is the return policy"), pure vector search probably works. If they search by identifier ("order SKU-12345", "API endpoint /v1/users/me"), BM25 probably works. If they do both — which is the default assumption for a general-purpose knowledge base — hybrid is the right default.

We included it because the general case is mixed queries. If you know your use case is more specific, you can simplify.

---

## How Our Implementation Works

We use **Reciprocal Rank Fusion (RRF)** to combine results.

### Why RRF and Not Learned Weights?

You could train a small model to predict the optimal blend per query type. We chose RRF for three reasons that matter in practice:

1. **No training data required.** Learned weights need query-result relevance pairs. You don't have those at the start of a project. RRF works correctly on day one.
2. **Robust to score distribution differences.** BM25 and dense search produce scores on completely different scales. RRF operates on ranks, not raw scores — it's immune to the "one signal dominates because its scores are bigger" problem that plagues naive weighted averaging.
3. **Debuggable.** When a result ranks unexpectedly, you can explain exactly why: its rank in each signal and how those combined. Learned weights are a black box.

### The Formula

```
fused_score = alpha * dense_rrf + (1 - alpha) * bm25_rrf
```

where:
```
rrf_score = 1 / (rank + 60)
```

The `60` is a standard constant. It softens the penalty for lower ranks — a result at rank 5 is still quite good, not nearly as bad as rank 5 in a linear scheme. You can tune it, but you'll rarely need to.

### What Alpha Actually Does

- **alpha = 1.0**: Pure vector search. BM25 is ignored entirely.
- **alpha = 0.0**: Pure BM25. Vectors are ignored entirely.
- **alpha = 0.5**: Equal weight to both signals. Our default.

---

## When to Tune Alpha

### Move Toward 1.0 (More Semantic) When:

- Queries are conversational or abstractly phrased
- Users rephrase the same concept in different words
- Your documents use formal language and users use casual language — or vice versa

**Example**: "What does the company say about using personal AI tools at work?" benefits from semantic understanding. The document might say "usage of third-party AI applications" and BM25 would miss the connection entirely.

### Move Toward 0.0 (More Keyword) When:

- Your domain has non-negotiable terminology: product codes, API endpoints, legal citations, identifiers
- Users search by quoting exact phrases from documents
- You're seeing vector search confidently returning semantically similar but factually wrong results

**Example**: "Clause 12.3(b) obligations" or "error code E4502" — these require exact matching. Semantic search will return documents about similar clauses or similar errors, which is worse than returning nothing.

---

## The Truth About Alpha Tuning

Here's what doesn't get said enough:

> **Most queries perform acceptably at alpha=0.5. The gains from tuning are real but marginal for typical mixed-query workloads.**

The cases where alpha matters significantly are the edges of your query distribution. The question is whether those edge cases are important enough to justify the added complexity of per-query alpha selection.

**The honest advice**:

1. **Start at 0.5.** It's a reasonable default.
2. **Don't tune without eval evidence.** Run a set of queries at 0.3, 0.5, and 0.7. If there's no meaningful difference in your metrics, don't complicate your system.
3. **Consider query classification only if you've proven it helps.** Routing keyword-heavy queries to low alpha and semantic queries to high alpha is a reasonable optimization — but it's extra code to maintain, and it requires a reliable classifier. Prove the gain first.
4. **Watch for regression.** Tuning alpha for one query type almost always affects others. Check overall eval scores, not just the queries you were optimizing for.

---

## Implementation Details

### BM25

We use `rank_bm25.BM25Okapi` with simple whitespace tokenization. This is the "good enough" choice for a starter project.

**Known limitations**:
- Doesn't handle hyphenated terms well
- Case-insensitive (we lowercase everything before indexing)
- No phrase query support — "machine learning" is treated as two separate terms

For production-grade keyword search on large corpora with complex terminology, you'd want a proper inverted index — Elasticsearch or OpenSearch with a real analyzer. But for most starter use cases, BM25Okapi with whitespace tokenization gets you 80% of the benefit at 5% of the complexity.

### Why We Build BM25 In-Memory

We rebuild the BM25 index from Qdrant payloads at query time. This is the correct choice at starter scale — the alternative (maintaining a separate BM25 index) introduces synchronization problems. At large scale (millions of documents), you'd want a persistent BM25 index or a dedicated keyword search layer. You're not there yet.

### Normalization

Both BM25 and dense scores are normalized to [0,1] before fusion. This is not optional — without normalization, whichever signal produces larger raw values dominates the fusion regardless of the alpha setting. Dense cosine similarity scores might range from 0.7 to 0.95. BM25 scores might range from 0.1 to 15.0. Naive fusion would be pure BM25.

### The k=60 Constant in RRF

Higher k = rank position matters less (more forgiving of being ranked 5th vs 1st).
Lower k = rank position matters more (steep penalty for not being first).

60 is the standard value from the original RRF paper. It works well for typical retrieval workloads. You're unlikely to need to change it unless you're seeing specific rank sensitivity issues in eval.

---

## When Hybrid Search Isn't Enough

If you've implemented hybrid search and retrieval quality still isn't where it needs to be, the fix is almost never "tune alpha more."

In order of what to try:
1. **Review chunking first.** This is the most common root cause of retrieval failures that look like search strategy problems. A chunk that splits a concept across two boundaries won't be retrieved reliably regardless of how you combine BM25 and dense scores.
2. **Add reranking.** Retrieve 30-50 candidates with hybrid search, then rerank with a cross-encoder model. More expensive but substantially more accurate for ambiguous queries.
3. **Query expansion.** Rewrite the user's query before retrieval — expand abbreviations, decompose compound questions, add synonyms. This is a prompt engineering problem as much as a retrieval problem.
4. **Evaluate your corpus.** Sometimes retrieval fails because the answer isn't in the documents, not because the search is broken. Make sure you're distinguishing retrieval failures from corpus gaps.

---

## What Matters Most

Fix chunking before tuning alpha. Improve your eval set before adding reranking. Understand your failure modes before adding complexity.

Hybrid search is a good default for mixed-query workloads. It's not a solution to retrieval problems caused by other parts of the pipeline — and it's one of the first places engineers look when they should be looking elsewhere.

> **Measure first. Tune second. Add complexity only when measurement tells you to.**