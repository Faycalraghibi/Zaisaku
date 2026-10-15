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


@pytest.mark.parametrize("ticker", ["SMCI", "COIN", "SPY", "ZZZZ"])
def test_uncovered_ticker_gets_no_fabricated_peers(ticker):
    res = PeerAnalyzer().benchmark(ticker)
    assert res.target_ticker == ticker
    assert res.peers == []
    assert res.sector_average_ffi is None
    assert "no peer set" in res.sector_commentary.lower()


def test_no_placeholder_peers_in_any_sector():
    for ticker in ["NVDA", "AAPL", "TSLA", "SMCI", "JPM"]:
        for peer in PeerAnalyzer().benchmark(ticker).peers:
            assert not peer.ticker.startswith("PEER")
            assert "Benchmark Peer" not in peer.name


def test_peer_api_returns_empty_set_for_uncovered_ticker(client):
    data = client.get("/api/forensics/peers/SMCI").json()
    assert data["peers"] == []
    assert data["sector_average_ffi"] is None
