import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.auth import verify_api_key
from app.evaluation import mlflow_logger, ragas_eval
from app.generation import llm
from app.ingestion import embedder
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
    query_vectors = await embedder.embed_texts([request.query])
    query_vector = query_vectors[0]
    
    results = await hybrid_search.hybrid_search(
        request.query,
        query_vector,
        top_k=request.top_k,
        alpha=request.alpha,
    )
    
    answer = await llm.generate_answer(request.query, results)
    
    sources = [
        ChunkSource(
            doc_id=r["doc_id"],
            chunk_id=r["chunk_id"],
            filename=r["filename"],
            version=r["version"],
            score=r["score"],
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
        mlflow_logger.log_eval_to_mlflow(request.query, eval_scores)
    
    return QueryResponse(
        answer=answer,
        sources=sources,
        eval_scores=eval_scores,
    )