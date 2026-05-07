import base64
import logging
import time
from uuid import uuid4

from fastapi import APIRouter, Depends

from app.auth import verify_api_key
from app.governance import versioning
from app.ingestion import chunker, embedder, loader
from app.mlflow.tracker import tracker
from app.models.schemas import IngestRequest
from app.observability.metrics import DOCUMENTS_INGESTED
from app.retrieval import qdrant_client
from app.tracking.mlflow_tracker import log_ingest_run

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ingest", tags=["ingestion"])


@router.post("")
async def ingest_document(
    request: IngestRequest,
    _: str = Depends(verify_api_key),
):
    ingest_start = time.perf_counter()
    doc_id = request.doc_id or str(uuid4())

    if request.mime_type in [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ]:
        content_bytes = base64.b64decode(request.content)
    else:
        content_bytes = request.content.encode("utf-8")

    text = loader.load_document(content_bytes, request.mime_type)

    chunks = chunker.chunk_document(text, strategy=request.chunking_strategy)

    vectors = await embedder.embed_texts([c.text for c in chunks])

    current_version = versioning.get_current_version(doc_id)

    total_tokens = sum(c.token_count for c in chunks)

    tracker.start_run(run_name=f"ingest-{request.filename}")
    try:
        if current_version > 0 and versioning.should_reindex(doc_id, request.version):
            tracker.log_version_change(doc_id, current_version, request.version)
            await versioning.reindex_document(
                doc_id,
                chunks,
                vectors,
                request.filename,
                request.version,
            )
        else:
            qdrant_client.upsert_chunks(
                chunks, vectors, doc_id, request.filename, request.version
            )

        tracker.log_ingestion(
            request.filename,
            doc_id,
            len(chunks),
            request.chunking_strategy,
            total_tokens,
            request.version,
        )
    finally:
        tracker.end_run()

    ingest_latency_ms = (time.perf_counter() - ingest_start) * 1000
    DOCUMENTS_INGESTED.labels(chunking_strategy=request.chunking_strategy).inc()

    log_ingest_run(
        doc_id=doc_id,
        filename=request.filename,
        chunk_count=len(chunks),
        chunking_strategy=request.chunking_strategy,
        ingest_latency_ms=ingest_latency_ms,
    )

    return {
        "doc_id": doc_id,
        "chunk_count": len(chunks),
        "version": request.version,
        "strategy": request.chunking_strategy,
        "total_tokens": total_tokens,
    }
