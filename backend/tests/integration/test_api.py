"""Integration tests for the FastAPI application."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from zaisaku.api.app import create_app
from zaisaku.api.dependencies import get_embedder, get_llm_backend, get_reranker, get_vector_store


# ---------------------------------------------------------------------------
# Fixtures & Overrides
# ---------------------------------------------------------------------------
@pytest.fixture
def app():
    app = create_app()

    # Create dummy mocks
    class DummyEmbedder:
        def embed_one(self, text): return [0.1, 0.2, 0.3]
        def embed(self, texts): return [[0.1, 0.2, 0.3] for _ in texts]

    class DummyReranker:
        def rerank(self, q, candidates, top_k): return candidates[:top_k]

    class DummyStore:
        def list_documents(self): return []
        def search(self, emb, top_k): return []
        def delete(self, doc_id): return 0
        def upsert(self, doc_id, chunks, embeddings, metadatas): return len(chunks)

    class DummyLLM:
        def generate(self, prompt, sys_prompt): 
            return {
                "text": '{"answer": "mock answer", "confidence": 1.0, "sources_used": []}',
                "model": "mock",
                "env": "test"
            }

    # Apply overrides
    app.dependency_overrides[get_embedder] = lambda: DummyEmbedder()
    app.dependency_overrides[get_reranker] = lambda: DummyReranker()
    app.dependency_overrides[get_vector_store] = lambda: DummyStore()
    app.dependency_overrides[get_llm_backend] = lambda: DummyLLM()

    yield app
    app.dependency_overrides.clear()


@pytest.fixture
def client(app):
    return TestClient(app)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
def test_health_check(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "env" in data


def test_list_documents(client):
    """Test retrieving documents."""
    # Since we are not overriding the DI container with a mocked store,
    # it will use the real Ephemeral ChromaClient which starts empty.
    response = client.get("/api/documents")
    assert response.status_code == 200
    assert response.json()["documents"] == []


def test_delete_missing_document(client):
    """Test deleting a document that doesn't exist."""
    response = client.delete("/api/documents/fake-doc-id")
    assert response.status_code == 404
    assert response.json()["detail"] == "Document fake-doc-id not found."


def test_query_empty_question(client):
    """Test that an empty query returns a 400."""
    response = client.post("/api/query", json={"question": ""})
    assert response.status_code == 400
    assert response.json()["detail"] == "Question cannot be empty."


# Because integration test for ingest requires heavy mocking or actual model downloading,
# we test route input validation primarily to ensure FastAPI Pydantic parsing works.
def test_ingest_no_file(client):
    response = client.post("/api/ingest")
    # File is a required body parameter
    assert response.status_code == 422
