"""Centralized configuration via Pydantic Settings.

Reads from environment variables and .env file.
All magic values live here — nothing is hardcoded inline.
"""

from __future__ import annotations

from pathlib import Path
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent  # zaisaku/


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=str(_PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Environment ──────────────────────────────
    env: str = "dev"

    # ── Ollama (dev) ─────────────────────────────
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "mistral:7b"

    # ── OpenRouter (prod) ────────────────────────
    openrouter_api_key: str = "sk-or-change-me"
    openrouter_model: str = "google/gemini-flash-1.5"

    # ── ChromaDB ─────────────────────────────────
    chroma_host: str = "chromadb"
    chroma_port: int = 8000
    chroma_collection: str = "zaisaku_docs"

    # ── Embeddings ───────────────────────────────
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    # ── Chunking ─────────────────────────────────
    chunk_size: int = 512
    chunk_overlap: int = 64

    # ── Retrieval ────────────────────────────────
    retrieval_top_k: int = 10
    rerank_top_k: int = 3

    # ── FastAPI ──────────────────────────────────
    app_port: int = 5000
    secret_key: str = "change-me-in-production"
    cors_origin: str = "http://localhost:5173"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Cached singleton — call this everywhere instead of constructing Settings()."""
    return Settings()
