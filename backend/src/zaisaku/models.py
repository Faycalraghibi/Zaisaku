"""Shared Pydantic models used across the application."""

from __future__ import annotations

from pydantic import BaseModel, Field


class Document(BaseModel):
    """Parsed document with extracted text and metadata."""

    text: str
    metadata: dict = Field(default_factory=dict)


class Chunk(BaseModel):
    """A text chunk with its embedding and metadata."""

    text: str
    embedding: list[float] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)


class SearchResult(BaseModel):
    """A single search result from the vector store."""

    text: str
    score: float
    metadata: dict = Field(default_factory=dict)
    rerank_score: float | None = None


class QueryResponse(BaseModel):
    """Structured response from the RAG pipeline."""

    answer: str
    confidence: float
    sources: list[str] = Field(default_factory=list)
    model: str
    env: str


class IngestResponse(BaseModel):
    """Response after ingesting a document."""

    doc_id: str
    filename: str
    chunks: int
    status: str = "indexed"


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = "ok"
    env: str = "dev"
