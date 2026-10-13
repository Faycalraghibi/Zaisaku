"""All magic values live here — nothing is hardcoded inline."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent  # zaisaku/


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    env: str = "dev"
    app_host: str = "127.0.0.1"
    app_port: int = 8000
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "mistral:7b"
    openrouter_api_key: str = "sk-or-change-me"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_model: str = "google/gemini-flash-1.5"
    llm_timeout: float = 60.0
    chroma_host: str = "chromadb"
    chroma_port: int = 8000
    chroma_collection: str = "zaisaku_docs"
    chroma_mode: str = "http"
    chroma_persist_path: str = "./data/chroma"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    chunk_size: int = 512
    chunk_overlap: int = 64
    retrieval_top_k: int = 10
    rerank_top_k: int = 3
    upload_dir: str = "uploads"
    max_upload_size: int = 50 * 1024 * 1024  # 50 MB
    llm_max_tokens: int = 1024
    secret_key: str = "change-me-in-production"
    cors_origin: str = "http://localhost:5173"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Cached singleton — call this everywhere instead of constructing Settings()."""
    return Settings()
