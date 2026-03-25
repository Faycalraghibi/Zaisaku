"""FastAPI Dependency Injection providers."""

from __future__ import annotations

from typing import Annotated
from fastapi import Depends

import chromadb

from zaisaku.config import Settings, get_settings
from zaisaku.ingestion.embedder import Embedder, SentenceTransformerEmbedder
from zaisaku.retrieval.reranker import CrossEncoderReranker, Reranker
from zaisaku.retrieval.store import ChromaVectorStore, VectorStore
from zaisaku.generation.llm import LLMBackend, LLMRouter

# ---------------------------------------------------------------------------
# Singleton instances to prevent reloading models per-request
# ---------------------------------------------------------------------------
_embedder_instance: Embedder | None = None
_reranker_instance: Reranker | None = None
_vector_store_instance: VectorStore | None = None
_llm_backend_instance: LLMBackend | None = None


def get_embedder(settings: Annotated[Settings, Depends(get_settings)]) -> Embedder:
    global _embedder_instance
    if _embedder_instance is None:
        _embedder_instance = SentenceTransformerEmbedder(settings.embedding_model)
    return _embedder_instance


def get_reranker(settings: Annotated[Settings, Depends(get_settings)]) -> Reranker:
    global _reranker_instance
    if _reranker_instance is None:
        _reranker_instance = CrossEncoderReranker()
    return _reranker_instance


def get_vector_store(settings: Annotated[Settings, Depends(get_settings)]) -> VectorStore:
    global _vector_store_instance
    if _vector_store_instance is None:
        client = chromadb.HttpClient(host=settings.chroma_host, port=settings.chroma_port)
        _vector_store_instance = ChromaVectorStore(settings.chroma_collection, client)
    return _vector_store_instance


def get_llm_backend(settings: Annotated[Settings, Depends(get_settings)]) -> LLMBackend:
    global _llm_backend_instance
    if _llm_backend_instance is None:
        _llm_backend_instance = LLMRouter(settings).backend
    return _llm_backend_instance


# ---------------------------------------------------------------------------
# Annotated type hints for concise dependency injection in routes
# ---------------------------------------------------------------------------
ConfigDep = Annotated[Settings, Depends(get_settings)]
EmbedderDep = Annotated[Embedder, Depends(get_embedder)]
RerankerDep = Annotated[Reranker, Depends(get_reranker)]
StoreDep = Annotated[VectorStore, Depends(get_vector_store)]
LLMDep = Annotated[LLMBackend, Depends(get_llm_backend)]
