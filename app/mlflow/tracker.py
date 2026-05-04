import logging
from datetime import datetime
from typing import Optional

import mlflow

from app.config import settings

logger = logging.getLogger(__name__)


class MLflowTracker:
    def __init__(self):
        mlflow.set_tracking_uri(settings.MLFLOW_TRACKING_URI)
        mlflow.set_experiment("rag-production-starter")

    def log_ingestion(
        self,
        filename: str,
        doc_id: str,
        num_chunks: int,
        strategy: str,
        token_count: int,
        version: int,
    ) -> None:
        mlflow.log_params(
            {
                "filename": filename,
                "doc_id": doc_id,
                "strategy": strategy,
                "version": version,
            }
        )
        mlflow.log_metrics(
            {
                "num_chunks": num_chunks,
                "total_tokens": token_count,
            }
        )
        mlflow.log_param("ingested_at", datetime.utcnow().isoformat())

    def log_query(
        self,
        query: str,
        alpha: float,
        top_k: int,
        num_results: int,
        latency_ms: float,
        model: str = "gpt-4o-mini",
    ) -> None:
        mlflow.log_params(
            {
                "query": query[:200],
                "alpha": alpha,
                "top_k": top_k,
                "model": model,
            }
        )
        mlflow.log_metrics(
            {
                "num_results": num_results,
                "latency_ms": latency_ms,
            }
        )

    def log_evaluation(
        self,
        query: str,
        answer: str,
        faithfulness: float,
        answer_relevancy: float,
        context_recall: float,
    ) -> None:
        mlflow.log_params(
            {
                "query": query[:200],
                "answer": answer[:200],
            }
        )
        mlflow.log_metrics(
            {
                "faithfulness": faithfulness,
                "answer_relevancy": answer_relevancy,
                "context_recall": context_recall,
            }
        )

    def log_drift_detection(
        self, days_threshold: int, num_stale: int, stale_doc_ids: list
    ) -> None:
        mlflow.log_params(
            {
                "days_threshold": days_threshold,
            }
        )
        mlflow.log_metrics(
            {
                "num_stale_documents": num_stale,
            }
        )
        mlflow.log_param(
            "stale_doc_ids", ",".join(stale_doc_ids) if stale_doc_ids else "none"
        )
        mlflow.set_tag("event_type", "drift_detection")

    def log_deletion(self, doc_id: str, vectors_deleted: int) -> None:
        mlflow.log_params(
            {
                "doc_id": doc_id,
                "vectors_deleted": vectors_deleted,
            }
        )
        mlflow.set_tag("event_type", "document_deletion")
        mlflow.log_param("deleted_at", datetime.utcnow().isoformat())

    def log_version_change(
        self, doc_id: str, old_version: int, new_version: int
    ) -> None:
        mlflow.log_params(
            {
                "doc_id": doc_id,
                "old_version": old_version,
                "new_version": new_version,
            }
        )
        mlflow.set_tag("event_type", "version_change")
        mlflow.log_param("changed_at", datetime.utcnow().isoformat())

    def start_run(self, run_name: Optional[str] = None) -> None:
        mlflow.start_run(run_name=run_name)

    def end_run(self) -> None:
        if mlflow.active_run():
            mlflow.end_run()


tracker = MLflowTracker()
