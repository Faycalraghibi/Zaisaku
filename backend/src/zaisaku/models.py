
from __future__ import annotations

from pydantic import BaseModel, Field


class Document(BaseModel):
    text: str
    metadata: dict = Field(default_factory=dict)

class Chunk(BaseModel):
    text: str
    embedding: list[float] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)

class SearchResult(BaseModel):
    text: str
    score: float
    metadata: dict = Field(default_factory=dict)
    rerank_score: float | None = None

class QueryResponse(BaseModel):
    answer: str
    confidence: float
    sources: list[str] = Field(default_factory=list)
    model: str
    env: str

class IngestResponse(BaseModel):
    doc_id: str
    filename: str
    chunks: int
    status: str = "indexed"

class HealthResponse(BaseModel):

    status: str = "ok"
    env: str = "dev"
