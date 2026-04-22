import logging
from typing import Dict, List

try:
    from ragas import evaluate
    from ragas.dataset import Dataset
    from ragas.metrics import answer_relevancy, faithfulness, context_recall
    RAGAS_AVAILABLE = True
except ImportError:
    RAGAS_AVAILABLE = False
    evaluate = None
    Dataset = None

from openai import AsyncOpenAI

from app.config import settings

logger = logging.getLogger(__name__)

client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)


async def run_evaluation(
    query: str,
    answer: str,
    contexts: List[str],
) -> Dict:
    if not RAGAS_AVAILABLE:
        logger.warning("Ragas not installed, returning default scores")
        return {
            "faithfulness": 0.0,
            "answer_relevancy": 0.0,
            "context_recall": 0.0,
        }
    
    dataset = Dataset.from_list([
        {
            "question": query,
            "answer": answer,
            "contexts": contexts,
        }
    ])
    
    result = evaluate(
        dataset=dataset,
        metrics=[faithfulness, answer_relevancy, context_recall],
    )
    
    return {
        "faithfulness": result["faithfulness"],
        "answer_relevancy": result["answer_relevancy"],
        "context_recall": result["context_recall"],
    }
