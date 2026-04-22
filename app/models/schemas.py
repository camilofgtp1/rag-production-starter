from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class IngestRequest(BaseModel):
    filename: str
    content: str
    mime_type: str = Field(
        ...,
        description="One of: application/pdf, text/markdown, text/plain, application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
    doc_id: Optional[str] = None
    version: int = 1


class QueryRequest(BaseModel):
    query: str
    top_k: int = 5
    alpha: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Hybrid search blend: 0.0 = keyword only, 1.0 = dense only"
    )


class ChunkSource(BaseModel):
    doc_id: str
    chunk_id: str
    filename: str
    version: int
    score: float


class QueryResponse(BaseModel):
    answer: str
    sources: list[ChunkSource]
    eval_scores: Optional[dict] = None


class EvalRequest(BaseModel):
    query: str
    answer: str
    contexts: list[str]


class EvalResponse(BaseModel):
    faithfulness: float
    answer_relevancy: float
    context_recall: float