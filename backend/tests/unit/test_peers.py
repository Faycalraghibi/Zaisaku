from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from zaisaku.api.app import create_app
from zaisaku.forensics.peers import PeerAnalyzer, PeerComparisonResponse


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


def test_peer_analyzer_nvda():
    analyzer = PeerAnalyzer()
    res = analyzer.benchmark("NVDA")
    assert isinstance(res, PeerComparisonResponse)
    assert res.target_ticker == "NVDA"
    assert len(res.peers) >= 4
    # Check that NVDA is in the list or is the target
    tickers = [p.ticker for p in res.peers]
    assert "AMD" in tickers
    assert "INTC" in tickers
    assert res.sector_average_ffi > 0


def test_peer_analyzer_sector_average():
    analyzer = PeerAnalyzer()
    res = analyzer.benchmark("AAPL")
    avg = sum(p.ffi for p in res.peers) / len(res.peers)
    assert pytest.approx(res.sector_average_ffi, 0.1) == avg


def test_peer_api_endpoint(client):
    res = client.get("/api/forensics/peers/NVDA")
    assert res.status_code == 200
    data = res.json()
    assert data["target_ticker"] == "NVDA"
    assert len(data["peers"]) >= 4
    assert "sector_average_ffi" in data
