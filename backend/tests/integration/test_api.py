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
        def generate(self, prompt, system_prompt): 
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


def test_query_markdown_wrapped_json(client, app):
    from zaisaku.api.dependencies import get_llm_backend

    class MarkdownLLM:
        def generate(self, prompt, system_prompt):
            return {
                "text": '```json\n{"answer": "fenced answer", "confidence": 0.95, "sources_used": ["doc1.pdf"]}\n```',
                "model": "mock",
                "env": "test",
            }

    app.dependency_overrides[get_llm_backend] = lambda: MarkdownLLM()
    response = client.post("/api/query", json={"question": "What is revenue?"})
    assert response.status_code == 200
    data = response.json()
    assert data["answer"] == "fenced answer"
    assert data["confidence"] == 0.95
    assert data["sources"] == ["doc1.pdf"]


def test_query_unadorned_backticks_json(client, app):
    from zaisaku.api.dependencies import get_llm_backend

    class PlainBackticksLLM:
        def generate(self, prompt, system_prompt):
            return {
                "text": '```\n{"answer": "unadorned answer", "confidence": 0.85, "sources_used": []}\n```',
                "model": "mock",
                "env": "test",
            }

    app.dependency_overrides[get_llm_backend] = lambda: PlainBackticksLLM()
    response = client.post("/api/query", json={"question": "What is net income?"})
    assert response.status_code == 200
    data = response.json()
    assert data["answer"] == "unadorned answer"
    assert data["confidence"] == 0.85


def test_query_non_numeric_confidence(client, app):
    from zaisaku.api.dependencies import get_llm_backend

    class NonNumericConfidenceLLM:
        def generate(self, prompt, system_prompt):
            return {
                "text": '{"answer": "fallback confidence", "confidence": "high", "sources_used": ["doc1.txt"]}',
                "model": "mock",
                "env": "test",
            }

    app.dependency_overrides[get_llm_backend] = lambda: NonNumericConfidenceLLM()
    response = client.post("/api/query", json={"question": "What is net income?"})
    assert response.status_code == 200
    data = response.json()
    assert data["answer"] == "fallback confidence"
    assert data["confidence"] == 0.0


def test_ingest_file_exceeds_max_size(client, app, test_settings):
    from zaisaku.api.dependencies import get_settings

    custom_settings = test_settings.model_copy(update={"max_upload_size": 10})
    app.dependency_overrides[get_settings] = lambda: custom_settings

    files = {"file": ("oversized.txt", b"This file content definitely exceeds 10 bytes.", "text/plain")}
    response = client.post("/api/ingest", files=files)
    assert response.status_code == 413
    assert "File exceeds maximum allowed upload size" in response.json()["detail"]


def test_query_stream_empty_question(client):
    response = client.post("/api/query/stream", json={"question": ""})
    assert response.status_code == 400
    assert response.json()["detail"] == "Question cannot be empty."


def test_query_stream_success(client, app):
    from zaisaku.api.dependencies import get_llm_backend

    class StreamingMockLLM:
        def generate_stream(self, prompt, system_prompt):
            yield "Revenue was "
            yield "$100 million."

    app.dependency_overrides[get_llm_backend] = lambda: StreamingMockLLM()
    response = client.post("/api/query/stream", json={"question": "What is revenue?"})
    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]
    body = response.text
    assert "event: stage" in body
    assert "event: token" in body
    assert "Revenue was " in body
    assert "$100 million." in body
    assert "event: complete" in body


def test_get_raw_document_not_found(client):
    response = client.get("/api/documents/non-existent-id/raw")
    assert response.status_code == 404
    assert "Document file for non-existent-id not found" in response.json()["detail"]


def test_get_raw_document_success(client, app, test_settings, tmp_path):
    from zaisaku.api.dependencies import get_settings

    upload_dir = tmp_path / "uploads"
    docs_dir = upload_dir / "documents"
    docs_dir.mkdir(parents=True)
    file_path = docs_dir / "test-doc-id_financial_report.pdf"
    file_path.write_bytes(b"%PDF-1.4 sample pdf content")

    custom_settings = test_settings.model_copy(update={"upload_dir": str(upload_dir)})
    app.dependency_overrides[get_settings] = lambda: custom_settings

    response = client.get("/api/documents/test-doc-id/raw")
    assert response.status_code == 200
    assert response.content == b"%PDF-1.4 sample pdf content"
    assert "application/pdf" in response.headers["content-type"]


def test_sec_ingest_empty_ticker(client):
    response = client.post("/api/sec/ingest", json={"ticker": "", "form": "10-K"})
    assert response.status_code == 400
    assert response.json()["detail"] == "Ticker cannot be empty."


def test_sec_ingest_success(client, monkeypatch):
    from zaisaku.ingestion.sec_edgar import SECEdgarClient

    def mock_fetch(self, ticker, form):
        return f"{ticker}_{form}.htm", b"<html><body>NVIDIA Revenue grew by 122 percent YoY.</body></html>"

    monkeypatch.setattr(SECEdgarClient, "fetch_recent_filing", mock_fetch)

    response = client.post("/api/sec/ingest", json={"ticker": "NVDA", "form": "10-K"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "indexed"
    assert data["filename"] == "NVDA_10-K.htm"
    assert data["chunks"] >= 1


def test_forensic_report_generate_endpoint(client):
    payload = {
        "ticker": "TSLA",
        "company_name": "Tesla, Inc.",
        "scorecard": {
            "composite_ffi": 42.5,
            "risk_level": "WATCHLIST",
            "recommendation": "MONITOR_CLOSELY",
            "summary": "Tesla exhibits moderate language drift.",
            "pillars": {
                "language_drift": {"raw_score": 35.0, "weighted_score": 10.5, "status": "ELEVATED"},
                "forensic_accounting": {"raw_score": 25.0, "weighted_score": 10.0, "status": "CLEAN"},
                "call_contradictions": {"raw_score": 40.0, "weighted_score": 12.0, "status": "ELEVATED"},
            },
        },
    }
    response = client.post("/api/forensics/report/generate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["ticker"] == "TSLA"
    assert data["company_name"] == "Tesla, Inc."
    assert "FORENSIC FINANCIAL DUE DILIGENCE MEMORANDUM" in data["markdown"]
    assert data["composite_ffi"] == 42.5
    assert data["risk_level"] == "WATCHLIST"


def test_forensic_report_download_endpoint(client):
    payload = {
        "ticker": "AAPL",
        "company_name": "Apple Inc.",
    }
    response = client.post("/api/forensics/report/download", json=payload)
    assert response.status_code == 200
    assert "attachment; filename=\"forensic_due_diligence_aapl.md\"" in response.headers["content-disposition"]
    assert b"FORENSIC FINANCIAL DUE DILIGENCE MEMORANDUM" in response.content
    assert b"Apple Inc. (AAPL)" in response.content
