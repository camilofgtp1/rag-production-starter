import base64
import logging
from uuid import uuid4

from fastapi import APIRouter, Depends

from app.auth import verify_api_key
from app.governance import versioning
from app.ingestion import chunker, embedder, loader
from app.models.schemas import IngestRequest
from app.retrieval import qdrant_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ingest", tags=["ingestion"])


@router.post("")
async def ingest_document(
    request: IngestRequest,
    _: str = Depends(verify_api_key),
):
    doc_id = request.doc_id or str(uuid4())
    
    if request.mime_type in ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]:
        content_bytes = base64.b64decode(request.content)
    else:
        content_bytes = request.content.encode("utf-8")
    
    text = loader.load_document(content_bytes, request.mime_type)
    
    chunks = chunker.chunk_document(text, strategy="semantic")
    
    vectors = await embedder.embed_texts([c.text for c in chunks])
    
    current_version = versioning.get_current_version(doc_id)
    
    if current_version > 0 and versioning.should_reindex(doc_id, request.version):
        await versioning.reindex_document(
            doc_id,
            chunks,
            vectors,
            request.filename,
            request.version,
        )
    else:
        qdrant_client.upsert_chunks(chunks, vectors, doc_id, request.filename, request.version)
    
    return {
        "doc_id": doc_id,
        "chunk_count": len(chunks),
        "version": request.version,
        "strategy": "semantic",
    }