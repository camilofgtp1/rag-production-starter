from fastapi import APIRouter, Depends, Query

from app.auth import verify_api_key
from app.governance import deletion, drift
from app.mlflow import tracker

router = APIRouter(prefix="/governance", tags=["governance"])


@router.get("/drift")
async def get_drift_report(
    days_threshold: int = Query(default=30, ge=1),
    _: str = Depends(verify_api_key),
):
    report = await drift.drift_report()
    stale_docs = await drift.get_stale_docs(days_threshold)

    tracker.start_run(run_name="drift-detection")
    try:
        tracker.log_drift_detection(days_threshold, len(stale_docs), stale_docs)
    finally:
        tracker.end_run()

    return {
        "drift_report": report,
        "stale_doc_ids": stale_docs,
    }


@router.delete("/documents/{doc_id}")
async def delete_doc(
    doc_id: str,
    _: str = Depends(verify_api_key),
):
    result = await deletion.delete_document(doc_id)

    tracker.start_run(run_name=f"delete-{doc_id}")
    try:
        tracker.log_deletion(doc_id, result.get("vectors_deleted", 0))
    finally:
        tracker.end_run()

    return result
