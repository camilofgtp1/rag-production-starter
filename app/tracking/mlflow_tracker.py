import logging
from typing import Optional

import mlflow

from app.config import settings

logger = logging.getLogger(__name__)


def log_query_run(
    query: str,
    alpha: float,
    top_k: int,
    chunking_strategy: str,
    model: str,
    retrieval_latency_ms: float,
    generation_latency_ms: float,
    total_latency_ms: float,
    chunks_retrieved: int,
    prompt_tokens: int,
    completion_tokens: int,
    estimated_cost_usd: float,
) -> None:
    try:
        mlflow.set_tracking_uri(settings.MLFLOW_TRACKING_URI)
        mlflow.set_experiment("rag-queries")

        with mlflow.start_run():
            mlflow.log_params(
                {
                    "query": query[:200],
                    "alpha": alpha,
                    "top_k": top_k,
                    "chunking_strategy": chunking_strategy,
                    "model": model,
                }
            )
            mlflow.log_metrics(
                {
                    "retrieval_latency_ms": retrieval_latency_ms,
                    "generation_latency_ms": generation_latency_ms,
                    "total_latency_ms": total_latency_ms,
                    "chunks_retrieved": chunks_retrieved,
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "estimated_cost_usd": estimated_cost_usd,
                }
            )
    except Exception:
        logger.warning("Failed to log query run to MLflow", exc_info=True)


def log_eval_run(
    query: str,
    faithfulness: float,
    answer_relevancy: float,
    context_recall: float,
) -> None:
    try:
        mlflow.set_tracking_uri(settings.MLFLOW_TRACKING_URI)
        mlflow.set_experiment("rag-evaluation")

        with mlflow.start_run():
            mlflow.log_param("query", query[:200])
            mlflow.log_metrics(
                {
                    "faithfulness": faithfulness,
                    "answer_relevancy": answer_relevancy,
                    "context_recall": context_recall,
                }
            )
    except Exception:
        logger.warning("Failed to log eval run to MLflow", exc_info=True)


def log_ingest_run(
    doc_id: str,
    filename: str,
    chunk_count: int,
    chunking_strategy: str,
    ingest_latency_ms: float,
) -> None:
    try:
        mlflow.set_tracking_uri(settings.MLFLOW_TRACKING_URI)
        mlflow.set_experiment("rag-ingestion")

        with mlflow.start_run():
            mlflow.log_params(
                {
                    "doc_id": doc_id,
                    "filename": filename,
                    "chunking_strategy": chunking_strategy,
                }
            )
            mlflow.log_metrics(
                {
                    "chunk_count": chunk_count,
                    "ingest_latency_ms": ingest_latency_ms,
                }
            )
    except Exception:
        logger.warning("Failed to log ingest run to MLflow", exc_info=True)
