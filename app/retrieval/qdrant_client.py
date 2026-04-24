import logging
from datetime import datetime

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    PointStruct,
    VectorParams,
    Filter,
    FieldCondition,
    MatchValue,
)

from app.config import settings
from app.ingestion.chunker import Chunk

logger = logging.getLogger(__name__)

VECTOR_SIZE = 1536

client = QdrantClient(
    url=settings.QDRANT_URL,
    api_key=settings.QDRANT_API_KEY if settings.QDRANT_API_KEY else None,
)


def init_collection() -> None:
    collections = client.get_collections().collections
    collection_names = [c.name for c in collections]

    if settings.COLLECTION_NAME not in collection_names:
        client.create_collection(
            collection_name=settings.COLLECTION_NAME,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
        )
        logger.info(f"Created collection: {settings.COLLECTION_NAME}")
    else:
        logger.info(f"Collection {settings.COLLECTION_NAME} already exists")


def upsert_chunks(
    chunks: list[Chunk],
    vectors: list[list[float]],
    doc_id: str,
    filename: str,
    version: int,
) -> None:
    points = []
    for chunk, vector in zip(chunks, vectors):
        points.append(
            PointStruct(
                id=chunk.chunk_id,
                vector=vector,
                payload={
                    "chunk_id": chunk.chunk_id,
                    "doc_id": doc_id,
                    "filename": filename,
                    "version": version,
                    "text": chunk.text,
                    "strategy_used": chunk.strategy_used,
                    "token_count": chunk.token_count,
                    "parent_chunk_id": chunk.parent_chunk_id,
                    "ingested_at": datetime.utcnow().isoformat(),
                },
            )
        )

    client.upsert(
        collection_name=settings.COLLECTION_NAME,
        points=points,
    )
    logger.info(f"Upserted {len(points)} chunks for doc_id: {doc_id}")


def delete_by_doc_id(doc_id: str) -> None:
    client.delete(
        collection_name=settings.COLLECTION_NAME,
        points_selector=Filter(
            must=[FieldCondition(key="doc_id", match=MatchValue(value=doc_id))]
        ),
    )
    logger.info(f"Deleted all vectors for doc_id: {doc_id}")


def dense_search(query_vector: list[float], top_k: int = 5) -> list[dict]:
    results = client.query_points(
        collection_name=settings.COLLECTION_NAME,
        query=query_vector,
        limit=top_k,
    )

    return [
        {
            "chunk_id": r.id,
            "doc_id": r.payload.get("doc_id"),
            "filename": r.payload.get("filename"),
            "version": r.payload.get("version"),
            "text": r.payload.get("text"),
            "score": r.score,
        }
        for r in results.points
    ]


def get_all_doc_ids() -> list[str]:
    results = client.scroll(
        collection_name=settings.COLLECTION_NAME,
        limit=10000,
        with_payload=True,
    )

    doc_ids = set()
    for point in results[0]:
        if point.payload and "doc_id" in point.payload:
            doc_ids.add(point.payload["doc_id"])

    return list(doc_ids)


def get_chunks_by_doc_id(doc_id: str) -> list[dict]:
    results = client.scroll(
        collection_name=settings.COLLECTION_NAME,
        scroll_filter=Filter(
            must=[FieldCondition(key="doc_id", match=MatchValue(value=doc_id))]
        ),
        limit=10000,
        with_payload=True,
    )

    return [
        {
            "chunk_id": point.payload.get("chunk_id"),
            "doc_id": point.payload.get("doc_id"),
            "filename": point.payload.get("filename"),
            "version": point.payload.get("version"),
            "text": point.payload.get("text"),
            "strategy_used": point.payload.get("strategy_used"),
            "token_count": point.payload.get("token_count"),
            "parent_chunk_id": point.payload.get("parent_chunk_id"),
            "ingested_at": point.payload.get("ingested_at"),
        }
        for point in results[0]
    ]


def get_all_chunks() -> list[dict]:
    results = client.scroll(
        collection_name=settings.COLLECTION_NAME,
        limit=10000,
        with_payload=True,
        with_vectors=False,
    )

    return [
        {
            "chunk_id": point.payload.get("chunk_id"),
            "doc_id": point.payload.get("doc_id"),
            "filename": point.payload.get("filename"),
            "version": point.payload.get("version"),
            "text": point.payload.get("text"),
            "strategy_used": point.payload.get("strategy_used"),
            "token_count": point.payload.get("token_count"),
            "parent_chunk_id": point.payload.get("parent_chunk_id"),
            "ingested_at": point.payload.get("ingested_at"),
        }
        for point in results[0]
    ]


def ensure_collection():
    """Ensure collection exists, call this on startup."""
    init_collection()
