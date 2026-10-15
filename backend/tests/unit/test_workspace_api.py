from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from zaisaku.api.app import create_app


@pytest.fixture
def client():
    return TestClient(create_app())


def test_watchlist_crud(client):
    assert client.get("/api/workspace/watchlist").json() == []
    res = client.put("/api/workspace/watchlist/nvda")
    assert res.status_code == 200
    assert res.json()["ticker"] == "NVDA"
    assert [r["ticker"] for r in client.get("/api/workspace/watchlist").json()] == ["NVDA"]
    assert client.delete("/api/workspace/watchlist/NVDA").status_code == 204
    assert client.delete("/api/workspace/watchlist/NVDA").status_code == 404


def test_invalid_ticker_is_rejected(client):
    assert client.put("/api/workspace/watchlist/NOT_A_TICKER!").status_code == 422


def test_screens_validate_criteria(client):
    ok = client.post("/api/workspace/screens", json={"name": " High risk ", "criteria": {"ffi_min": 50}})
    assert ok.status_code == 201
    body = ok.json()
    assert body["name"] == "High risk"
    assert body["criteria"]["ffi_min"] == 50
    assert body["criteria"]["kind"] == "all"
    assert client.post("/api/workspace/screens", json={"name": "x", "criteria": {"bogus": 1}}).status_code == 422
    assert client.post("/api/workspace/screens", json={"name": "x", "criteria": {"ffi_min": 500}}).status_code == 422
    assert client.post("/api/workspace/screens", json={"name": "  ", "criteria": {}}).status_code == 422
    assert client.delete(f"/api/workspace/screens/{body['id']}").status_code == 204
    assert client.get("/api/workspace/screens").json() == []


def test_flag_reviews(client):
    res = client.put("/api/workspace/flags/smci/drift", json={"status": "escalated", "note": "Ask IR"})
    assert res.status_code == 200
    assert res.json()["ticker"] == "SMCI"
    assert client.get("/api/workspace/flags/SMCI").json()[0]["status"] == "escalated"
    assert len(client.get("/api/workspace/flags").json()) == 1
    assert client.put("/api/workspace/flags/SMCI/drift", json={"status": "maybe"}).status_code == 422
    assert client.put("/api/workspace/flags/SMCI/Bad Id", json={"status": "open"}).status_code == 422


def test_notes_crud(client):
    created = client.post("/api/workspace/notes/NVDA", json={"body": "  Check customer A  "})
    assert created.status_code == 201
    note = created.json()
    assert note["body"] == "Check customer A"
    assert client.post("/api/workspace/notes/NVDA", json={"body": "   "}).status_code == 422
    patched = client.patch(f"/api/workspace/notes/NVDA/{note['id']}", json={"body": "Edited"})
    assert patched.json()["body"] == "Edited"
    assert client.patch(f"/api/workspace/notes/SMCI/{note['id']}", json={"body": "x"}).status_code == 404
    assert client.delete(f"/api/workspace/notes/NVDA/{note['id']}").status_code == 204
    assert client.get("/api/workspace/notes/NVDA").json() == []


def test_memo_download_includes_analyst_review(client):
    client.put("/api/workspace/flags/SMCI/footnotes", json={"status": "escalated", "note": "Auditor resigned"})
    client.post("/api/workspace/notes/SMCI", json={"body": "Wait for 10-K"})
    res = client.post("/api/forensics/report/download", json={"ticker": "SMCI", "company_name": "Super Micro"})
    assert res.status_code == 200
    text = res.text
    assert "## Analyst review" in text
    assert "| Footnote disclosures | escalated | Auditor resigned |" in text
    assert "Wait for 10-K" in text


def test_memo_download_without_workspace_data_has_no_review_section(client):
    res = client.post("/api/forensics/report/download", json={"ticker": "NVDA"})
    assert "## Analyst review" not in res.text
