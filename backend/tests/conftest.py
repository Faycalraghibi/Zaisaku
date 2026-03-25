"""Pytest configuration — fixtures, markers, and model-availability checks.

Tests decorated with @pytest.mark.requires_embedder, @pytest.mark.requires_reranker,
@pytest.mark.requires_ollama, or @pytest.mark.requires_chromadb are automatically
skipped when the corresponding service/model is not available.
"""

from __future__ import annotations

import os
import pytest
import httpx


# ---------------------------------------------------------------------------
# Availability probes — called once per session, cached
# ---------------------------------------------------------------------------

def _ollama_available() -> bool:
    """Return True if Ollama is reachable at the expected URL."""
    url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    try:
        r = httpx.get(f"{url}/api/tags", timeout=2)
        return r.status_code == 200
    except Exception:
        return False


def _chromadb_available() -> bool:
    """Return True if ChromaDB is reachable."""
    host = os.getenv("CHROMA_HOST", "localhost")
    port = os.getenv("CHROMA_PORT", "8000")
    try:
        r = httpx.get(f"http://{host}:{port}/api/v1/heartbeat", timeout=2)
        return r.status_code == 200
    except Exception:
        return False


def _embedder_available() -> bool:
    """Return True if the sentence-transformers model can be loaded (from cache)."""
    try:
        from sentence_transformers import SentenceTransformer
        SentenceTransformer(
            os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"),
        )
        return True
    except Exception:
        return False


def _reranker_available() -> bool:
    """Return True if the cross-encoder model can be loaded (from cache)."""
    try:
        from sentence_transformers import CrossEncoder
        CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
        return True
    except Exception:
        return False


# Cache results so probes run at most once per session
_AVAILABILITY_CACHE: dict[str, bool] = {}

_CHECKS: dict[str, callable] = {
    "requires_ollama": _ollama_available,
    "requires_chromadb": _chromadb_available,
    "requires_embedder": _embedder_available,
    "requires_reranker": _reranker_available,
}


def _is_available(marker_name: str) -> bool:
    if marker_name not in _AVAILABILITY_CACHE:
        _AVAILABILITY_CACHE[marker_name] = _CHECKS[marker_name]()
    return _AVAILABILITY_CACHE[marker_name]


# ---------------------------------------------------------------------------
# Auto-skip hook
# ---------------------------------------------------------------------------

def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Skip tests whose required services/models are unavailable."""
    for item in items:
        for marker_name in _CHECKS:
            if marker_name in item.keywords and not _is_available(marker_name):
                item.add_marker(
                    pytest.mark.skip(reason=f"{marker_name}: service/model not available")
                )


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def test_settings():
    """Return a Settings instance with test-friendly overrides."""
    from zaisaku.config import Settings

    return Settings(
        env="dev",
        chroma_host="localhost",
        chroma_port=8000,
        chunk_size=128,
        chunk_overlap=16,
        retrieval_top_k=5,
        rerank_top_k=2,
    )
