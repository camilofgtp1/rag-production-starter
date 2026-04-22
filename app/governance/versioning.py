import logging
from typing import List

from app.ingestion.chunker import Chunk
from app.retrieval import qdrant_client

logger = logging.getLogger(__name__)


def get_current_version(doc_id: str) -> int:
    chunks = qdrant_client.get_chunks_by_doc_id(doc_id)
    if not chunks:
        return 0
    versions = [chunk.get("version", 0) for chunk in chunks]
    return max(versions)


def should_reindex(doc_id: str, new_version: int) -> bool:
    current = get_current_version(doc_id)
    return new_version > current


async def reindex_document(
    doc_id: str,
    new_chunks: List[Chunk],
    new_vectors: List[List[float]],
    filename: str,
    new_version: int,
) -> None:
    qdrant_client.delete_by_doc_id(doc_id)
    qdrant_client.upsert_chunks(new_chunks, new_vectors, doc_id, filename, new_version)
    logger.info(f"Reindexed document {doc_id} to version {new_version}")