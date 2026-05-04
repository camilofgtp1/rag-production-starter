import logging
import time

from fastapi import APIRouter, Depends, Query

from app.auth import verify_api_key
from app.evaluation import ragas_eval
from app.generation import llm
from app.ingestion import embedder
from app.mlflow import tracker
from app.models.schemas import ChunkSource, QueryRequest, QueryResponse
from app.retrieval import hybrid_search

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/query", tags=["query"])


@router.post("")
async def query_document(
    request: QueryRequest,
    run_eval: bool = Query(default=False),
    _: str = Depends(verify_api_key),
) -> QueryResponse:
    start_time = time.time()
    query_vectors = await embedder.embed_texts([request.query])
    query_vector = query_vectors[0]

    results = await hybrid_search.hybrid_search(
        request.query,
        query_vector,
        top_k=request.top_k,
        alpha=request.alpha,
    )

    answer = await llm.generate_answer(request.query, results)

    latency_ms = (time.time() - start_time) * 1000

    sources = [
        ChunkSource(
            doc_id=r["doc_id"],
            chunk_id=r["chunk_id"],
            filename=r["filename"],
            version=r["version"],
            score=r["score"],
            text=r.get("text", ""),
        )
        for r in results
    ]

    eval_scores = None
    if run_eval:
        contexts = [r["text"] for r in results]
        eval_scores = await ragas_eval.run_evaluation(
            request.query,
            answer,
            contexts,
        )
        tracker.log_evaluation(
            request.query,
            answer,
            eval_scores["faithfulness"],
            eval_scores["answer_relevancy"],
            eval_scores["context_recall"],
        )

    tracker.log_query(
        request.query, request.alpha, request.top_k, len(results), latency_ms, llm.MODEL
    )

    return QueryResponse(
        answer=answer,
        sources=sources,
        eval_scores=eval_scores,
    )
