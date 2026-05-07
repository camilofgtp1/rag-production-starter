from typing import Literal, Optional

from pydantic import BaseModel, Field


class IngestRequest(BaseModel):
    filename: str
    content: str
    mime_type: str = Field(
        ...,
        description="One of: application/pdf, text/markdown, text/plain, application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
    doc_id: Optional[str] = None
    version: int = 1
    chunking_strategy: Literal["fixed", "semantic", "late"] = Field(
        default="semantic",
        description="Chunking strategy: fixed, semantic, or late",
    )


class QueryRequest(BaseModel):
    query: str
    top_k: int = 5
    alpha: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Hybrid search blend: 0.0 = keyword only, 1.0 = dense only",
    )


class ChunkSource(BaseModel):
    doc_id: str
    chunk_id: str
    filename: str
    version: int
    score: float
    text: str = ""


class QueryResponse(BaseModel):
    answer: str
    sources: list[ChunkSource]
    eval_scores: Optional[dict] = None
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    estimated_cost_usd: Optional[float] = None
    retrieval_latency_ms: Optional[float] = None
    generation_latency_ms: Optional[float] = None


class EvalRequest(BaseModel):
    query: str
    answer: str
    contexts: list[str]


class EvalResponse(BaseModel):
    faithfulness: float
    answer_relevancy: float
    context_recall: float
