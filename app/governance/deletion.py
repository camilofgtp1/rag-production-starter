import logging
from datetime import datetime
from typing import Dict

from app.retrieval import qdrant_client

logger = logging.getLogger(__name__)


async def delete_document(doc_id: str) -> Dict:
    chunks = qdrant_client.get_chunks_by_doc_id(doc_id)
    count = len(chunks)
    
    qdrant_client.delete_by_doc_id(doc_id)
    
    deleted_at = datetime.utcnow().isoformat()
    logger.info(f"DELETION EVENT: doc_id={doc_id} vectors_deleted={count} at={deleted_at}")
    
    return {
        "doc_id": doc_id,
        "vectors_deleted": count,
        "deleted_at": deleted_at,
    }