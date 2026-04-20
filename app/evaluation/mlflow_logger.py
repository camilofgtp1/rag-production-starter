import logging
from typing import Dict

import mlflow

from app.config import settings

logger = logging.getLogger(__name__)

mlflow.set_tracking_uri(settings.MLFLOW_TRACKING_URI)


def log_eval_to_mlflow(query: str, eval_scores: Dict) -> None:
    mlflow.set_experiment("rag-evaluation")
    
    with mlflow.start_run():
        truncated_query = query[:200] if len(query) > 200 else query
        mlflow.log_param("query", truncated_query)
        mlflow.log_metric("faithfulness", eval_scores.get("faithfulness", 0.0))
        mlflow.log_metric("answer_relevancy", eval_scores.get("answer_relevancy", 0.0))
        mlflow.log_metric("context_recall", eval_scores.get("context_recall", 0.0))
    
    logger.info(f"Logged evaluation results to MLflow for query: {truncated_query}")