import logging
from typing import Dict, List

try:
    from ragas import evaluate
    from ragas.metrics import answer_relevancy, faithfulness, context_recall

    RAGAS_AVAILABLE = True
    Dataset = None
except ImportError:
    RAGAS_AVAILABLE = False
    evaluate = None
    Dataset = None
    faithfulness = None
    answer_relevancy = None
    context_recall = None

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

    logger.warning("Ragas evaluation disabled due to API changes")
    return {
        "faithfulness": 0.0,
        "answer_relevancy": 0.0,
        "context_recall": 0.0,
    }
