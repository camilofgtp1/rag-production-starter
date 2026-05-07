import logging
from typing import Dict, List, Optional

try:
    from ragas import evaluate
    from ragas import EvaluationDataset, SingleTurnSample
    from ragas.metrics import answer_relevancy, context_recall, faithfulness

    RAGAS_AVAILABLE = True
except ImportError:
    RAGAS_AVAILABLE = False
    evaluate = None
    faithfulness = None
    answer_relevancy = None
    context_recall = None
    EvaluationDataset = None
    SingleTurnSample = None

from app.config import settings

logger = logging.getLogger(__name__)


async def run_evaluation(
    query: str,
    answer: str,
    contexts: List[str],
    reference: Optional[str] = None,
) -> Dict:
    if not RAGAS_AVAILABLE:
        logger.warning("Ragas not installed, returning default scores")
        return {
            "faithfulness": -1.0,
            "answer_relevancy": -1.0,
            "context_recall": -1.0,
            "error": "Ragas not installed",
        }

    try:
        from ragas.llms import LangchainLLMWrapper
        from ragas.embeddings import LangchainEmbeddingsWrapper
        from langchain_openai import ChatOpenAI, OpenAIEmbeddings

        llm = LangchainLLMWrapper(
            ChatOpenAI(
                model="gpt-4o-mini",
                api_key=settings.OPENAI_API_KEY,
            )
        )
        embeddings = LangchainEmbeddingsWrapper(
            OpenAIEmbeddings(
                model="text-embedding-3-small",
                api_key=settings.OPENAI_API_KEY,
            )
        )

        sample_kwargs = {
            "user_input": query,
            "response": answer,
            "retrieved_contexts": contexts,
        }
        metrics = [faithfulness, answer_relevancy]
        if reference is not None:
            sample_kwargs["reference"] = reference
            metrics.append(context_recall)

        sample = SingleTurnSample(**sample_kwargs)
        dataset = EvaluationDataset(samples=[sample])

        result = evaluate(
            dataset,
            metrics=metrics,
            llm=llm,
            embeddings=embeddings,
        )

        scores = result.to_pandas()
        response = {
            "faithfulness": float(scores["faithfulness"].mean()),
            "answer_relevancy": float(scores["answer_relevancy"].mean()),
        }
        if reference is not None:
            response["context_recall"] = float(scores["context_recall"].mean())
        else:
            response["context_recall"] = -1.0
        return response
    except Exception as e:
        logger.error("Ragas evaluation failed: %s", e)
        return {
            "faithfulness": -1.0,
            "answer_relevancy": -1.0,
            "context_recall": -1.0,
            "error": str(e),
        }
