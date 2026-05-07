from fastapi import APIRouter, Depends

from app.auth import verify_api_key
from app.evaluation import ragas_eval
from app.mlflow.tracker import tracker
from app.models.schemas import EvalRequest, EvalResponse
from app.observability.metrics import EVALUATION_SCORES
from app.tracking.mlflow_tracker import log_eval_run

router = APIRouter(prefix="/evaluate", tags=["evaluation"])


@router.post("")
async def evaluate_answer(
    request: EvalRequest,
    _: str = Depends(verify_api_key),
) -> EvalResponse:
    eval_scores = await ragas_eval.run_evaluation(
        request.query,
        request.answer,
        request.contexts,
    )

    tracker.log_evaluation(
        request.query,
        request.answer,
        eval_scores["faithfulness"],
        eval_scores["answer_relevancy"],
        eval_scores["context_recall"],
    )

    if "error" not in eval_scores:
        log_eval_run(
            query=request.query,
            faithfulness=eval_scores["faithfulness"],
            answer_relevancy=eval_scores["answer_relevancy"],
            context_recall=eval_scores["context_recall"],
        )
        EVALUATION_SCORES.labels(metric="faithfulness").set(eval_scores["faithfulness"])
        EVALUATION_SCORES.labels(metric="answer_relevancy").set(
            eval_scores["answer_relevancy"]
        )
        EVALUATION_SCORES.labels(metric="context_recall").set(
            eval_scores["context_recall"]
        )

    return EvalResponse(
        faithfulness=eval_scores["faithfulness"],
        answer_relevancy=eval_scores["answer_relevancy"],
        context_recall=eval_scores["context_recall"],
    )
