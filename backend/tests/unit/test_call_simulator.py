from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from zaisaku.api.app import create_app
from zaisaku.forensics.call_simulator import CallSimulator, EarningsCallSession


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


def test_call_simulator_nvda():
    simulator = CallSimulator()
    res = simulator.get_call_session("NVDA")
    assert isinstance(res, EarningsCallSession)
    assert res.ticker == "NVDA"
    assert len(res.utterances) >= 4

    # Verify timestamps are ordered
    timestamps = [u.timestamp_seconds for u in res.utterances]
    assert timestamps == sorted(timestamps)

    # Verify speakers
    speakers = [u.speaker_role for u in res.utterances]
    assert "CEO" in speakers
    assert "CFO" in speakers

    # Check waveform data present
    assert len(res.utterances[0].waveform_peaks) > 0


def test_call_simulator_discrepancies():
    simulator = CallSimulator()
    res = simulator.get_call_session("FRAUD")
    assert any(u.is_discrepancy for u in res.utterances)


def test_call_api_endpoint(client):
    res = client.get("/api/forensics/calls/NVDA")
    assert res.status_code == 200
    data = res.json()
    assert data["ticker"] == "NVDA"
    assert len(data["utterances"]) >= 4
    assert "overall_executive_sentiment" in data
