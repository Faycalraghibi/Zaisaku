from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from zaisaku.api.app import create_app
from zaisaku.forensics.investigation import InvestigationOrchestrator


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


@pytest.mark.asyncio
async def test_investigation_orchestrator_stream():
    orchestrator = InvestigationOrchestrator()
    events = []
    async for sse_chunk in orchestrator.run_investigation_stream("NVDA"):
        events.append(sse_chunk)

    assert len(events) >= 5
    # Verify events format
    assert any("event: step" in e for e in events)
    assert any("event: complete" in e for e in events)

    # Check complete event payload
    complete_event = next(e for e in events if "event: complete" in e)
    for line in complete_event.split("\n"):
        if line.startswith("data: "):
            payload = json.loads(line[6:])
            assert payload["ticker"] == "NVDA"
            assert "composite_ffi" in payload
            assert "memo_markdown" in payload


def test_investigation_api_endpoint(client):
    res = client.post("/api/forensics/investigate/stream", json={"ticker": "NVDA"})
    assert res.status_code == 200
    assert "text/event-stream" in res.headers["content-type"]
    text = res.text
    assert "event: step" in text
    assert "event: complete" in text
