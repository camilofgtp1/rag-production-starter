import logging
import time

from fastapi import APIRouter, Depends, Query

from app.auth import verify_api_key
from app.evaluation import ragas_eval
from app.generation import llm
from app.ingestion import embedder
from app.models.schemas import ChunkSource, QueryRequest, QueryResponse
from app.observability.metrics import (
    CHUNKS_RETRIEVED,
    COST_USD_TOTAL,
    GENERATION_DURATION,
    RETRIEVAL_DURATION,
    TOKENS_TOTAL,
)
from app.retrieval import hybrid_search
from app.tracking.mlflow_tracker import log_query_run

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/query", tags=["query"])

COST_PER_INPUT_TOKEN = 0.00000015
COST_PER_OUTPUT_TOKEN = 0.0000006


@router.post("")
async def query_document(
    request: QueryRequest,
    run_eval: bool = Query(default=False),
    _: str = Depends(verify_api_key),
) -> QueryResponse:
    query_vectors = await embedder.embed_texts([request.query])
    query_vector = query_vectors[0]

    retrieval_start = time.perf_counter()
    results = await hybrid_search.hybrid_search(
        request.query,
        query_vector,
        top_k=request.top_k,
        alpha=request.alpha,
    )
    retrieval_latency_ms = (time.perf_counter() - retrieval_start) * 1000
    RETRIEVAL_DURATION.observe(retrieval_latency_ms / 1000)
    CHUNKS_RETRIEVED.observe(len(results))

    generation_start = time.perf_counter()
    answer, usage = await llm.generate_answer(request.query, results)
    generation_latency_ms = (time.perf_counter() - generation_start) * 1000

    prompt_tokens = usage.get("prompt_tokens", 0)
    completion_tokens = usage.get("completion_tokens", 0)
    estimated_cost_usd = (
        prompt_tokens * COST_PER_INPUT_TOKEN + completion_tokens * COST_PER_OUTPUT_TOKEN
    )

    GENERATION_DURATION.observe(generation_latency_ms / 1000)
    TOKENS_TOTAL.labels(type="prompt").inc(prompt_tokens)
    TOKENS_TOTAL.labels(type="completion").inc(completion_tokens)
    COST_USD_TOTAL.inc(estimated_cost_usd)

    total_latency_ms = retrieval_latency_ms + generation_latency_ms

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
    log_query_run(
        query=request.query,
        alpha=request.alpha,
        top_k=request.top_k,
        chunking_strategy="n/a (set at ingestion)",
        model=llm.MODEL,
        retrieval_latency_ms=retrieval_latency_ms,
        generation_latency_ms=generation_latency_ms,
        total_latency_ms=total_latency_ms,
        chunks_retrieved=len(results),
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        estimated_cost_usd=estimated_cost_usd,
    )

    return QueryResponse(
        answer=answer,
        sources=sources,
        eval_scores=eval_scores,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        estimated_cost_usd=estimated_cost_usd,
        retrieval_latency_ms=retrieval_latency_ms,
        generation_latency_ms=generation_latency_ms,
    )
