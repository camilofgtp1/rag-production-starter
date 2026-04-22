import logging
from typing import List

from rank_bm25 import BM25Okapi

from app.retrieval import qdrant_client

logger = logging.getLogger(__name__)


async def hybrid_search(
    query: str,
    query_vector: List[float],
    top_k: int = 5,
    alpha: float = 0.5,
) -> List[dict]:
    """
    Hybrid search combining BM25 and dense vector retrieval.
    
    Alpha tuning guidance:
    - Increase alpha (closer to 1.0) for abstract/semantic queries where meaning matters more than exact matches
    - Decrease alpha (closer to 0.0) for keyword-heavy queries, product names, code identifiers, exact term matching
    - Default alpha=0.5 provides balanced fusion for mixed queries
    """
    all_chunks = qdrant_client.get_all_chunks()
    
    if not all_chunks:
        return []
    
    corpus = [chunk["text"] for chunk in all_chunks]
    corpus_ids = [chunk["chunk_id"] for chunk in all_chunks]
    
    tokenized_corpus = [doc.lower().split() for doc in corpus]
    bm25 = BM25Okapi(tokenized_corpus)
    
    query_tokens = query.lower().split()
    bm25_scores = bm25.get_scores(query_tokens)
    
    max_bm25 = float(max(bm25_scores)) if len(bm25_scores) > 0 else 1.0
    if max_bm25 > 0:
        bm25_scores = [float(s / max_bm25) for s in bm25_scores]
    bm25_scores = list(bm25_scores)
    
    dense_results = qdrant_client.dense_search(query_vector, top_k=50)
    
    max_dense = float(max([r["score"] for r in dense_results])) if dense_results else 1.0
    
    dense_scores_map = {}
    for r in dense_results:
        normalized = r["score"] / max_dense if max_dense > 0 else 0.0
        dense_scores_map[r["chunk_id"]] = normalized
    
    bm25_ranking = sorted(
        [(chunk_id, score) for chunk_id, score in zip(corpus_ids, bm25_scores)],
        key=lambda x: x[1],
        reverse=True
    )
    
    dense_ranking = sorted(
        dense_results,
        key=lambda x: x["score"],
        reverse=True
    )
    
    rrf_scores = {}
    k = 60
    
    for rank, (chunk_id, _) in enumerate(bm25_ranking):
        rrf_scores[chunk_id] = rrf_scores.get(chunk_id, 0) + (1 - alpha) * (1.0 / (rank + k))
    
    for rank, result in enumerate(dense_ranking):
        chunk_id = result["chunk_id"]
        dense_score = dense_scores_map.get(chunk_id, 0.0)
        rrf_scores[chunk_id] = rrf_scores.get(chunk_id, 0) + alpha * (1.0 / (rank + k)) * (float(dense_score) if float(dense_score) > 0 else 1.0)
    
    sorted_chunks = sorted(
        [(cid, score) for cid, score in rrf_scores.items()],
        key=lambda x: x[1],
        reverse=True
    )[:top_k]
    
    chunk_map = {chunk["chunk_id"]: chunk for chunk in all_chunks}
    
    results = []
    for chunk_id, fused_score in sorted_chunks:
        if chunk_id in chunk_map:
            chunk = chunk_map[chunk_id]
            results.append({
                "chunk_id": chunk["chunk_id"],
                "doc_id": chunk["doc_id"],
                "filename": chunk["filename"],
                "version": chunk["version"],
                "text": chunk["text"],
                "score": fused_score,
            })
    
    return results