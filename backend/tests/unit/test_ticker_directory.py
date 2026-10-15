"""Unit tests for Institutional Market Index Directory and Universal Ticker Search."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from zaisaku.api.app import create_app
from zaisaku.forensics.ticker_directory import (
    MarketIndexSummary,
    TickerDirectoryService,
    TickerEntry,
    TickerSearchResponse,
)


@pytest.fixture
def service() -> TickerDirectoryService:
    return TickerDirectoryService()


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


def test_get_indices_benchmarks(service: TickerDirectoryService):
    """Verify all major institutional macro benchmarks are retrieved."""
    indices = service.get_indices()
    assert len(indices) == 7

    tickers = [idx.ticker for idx in indices]
    assert "SPY" in tickers
    assert "QQQ" in tickers
    assert "DIA" in tickers
    assert "IWM" in tickers
    assert "SMH" in tickers
    assert "XLK" in tickers
    assert "XLF" in tickers

    for idx in indices:
        assert isinstance(idx, MarketIndexSummary)
        assert len(idx.top_constituents) > 0
        assert 0.0 <= idx.composite_fragility <= 100.0
        assert len(idx.description) > 10


def test_search_curated_tickers(service: TickerDirectoryService):
    """Verify curated query matches both ticker and full name."""
    # Search by ticker
    res_nvda = service.search_tickers(query="NVDA")
    assert isinstance(res_nvda, TickerSearchResponse)
    assert res_nvda.total_matches >= 1
    nvda_entry = next(r for r in res_nvda.results if r.ticker == "NVDA")
    assert "Semiconductors" in nvda_entry.index_tags
    assert nvda_entry.cik == "0001045810"

    # Search by company name
    res_apple = service.search_tickers(query="Apple")
    assert any(r.ticker == "AAPL" for r in res_apple.results)


def test_index_filtering(service: TickerDirectoryService):
    """Verify filtering by market index tags."""
    # Macro indices filter
    res_macro = service.search_tickers(query="", index_filter="Macro Indices")
    assert res_macro.total_matches >= 4
    for r in res_macro.results:
        assert "Macro Indices" in r.index_tags

    # Semiconductors filter
    res_semi = service.search_tickers(query="", index_filter="Semiconductors")
    semi_tickers = [r.ticker for r in res_semi.results]
    assert "SMH" in semi_tickers
    assert "NVDA" in semi_tickers
    assert "AMD" in semi_tickers


def test_get_ticker_entry(service: TickerDirectoryService):
    """Verify retrieving specific ticker entries, with dynamic fallback for unknown."""
    # Curated entry
    msft = service.get_ticker_entry("MSFT")
    assert msft.ticker == "MSFT"
    assert "Microsoft" in msft.name
    assert msft.cik == "0000789019"

    # Dynamic fallback entry
    unknown = service.get_ticker_entry("XYZ_CORP")
    assert isinstance(unknown, TickerEntry)
    assert unknown.ticker == "XYZ_CORP"
    assert "XYZ_CORP" in unknown.name
    assert unknown.cik == "0000000000"


def test_sec_directory_search_mock(service: TickerDirectoryService):
    """Verify SEC fallback searches work with cached/mocked SEC directory."""
    service._sec_cache = {
        "TESTCO": {"title": "Test Corporation Inc", "cik_str": 12345},
        "BARCO": {"title": "Bar Enterprises Ltd", "cik_str": 67890},
    }

    results = service._search_sec_directory("TEST", max_count=5, exclude={"OTHER"})
    assert len(results) == 1
    assert results[0].ticker == "TESTCO"
    assert results[0].cik == "0000012345"
    assert results[0].exchange == "SEC EDGAR"


def test_api_indices_endpoint(client: TestClient):
    """Verify GET /api/forensics/indices returns 200 and valid schema."""
    res = client.get("/api/forensics/indices")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) == 7
    first = data[0]
    assert "index_id" in first
    assert "composite_fragility" in first
    assert "top_constituents" in first


def test_api_tickers_search_endpoint(client: TestClient):
    """Verify GET /api/forensics/tickers/search with various query parameters."""
    # Query with q
    res_q = client.get("/api/forensics/tickers/search?q=NVDA")
    assert res_q.status_code == 200
    data_q = res_q.json()
    assert data_q["query"] == "NVDA"
    assert any(r["ticker"] == "NVDA" for r in data_q["results"])

    # Query with index_filter
    res_filter = client.get("/api/forensics/tickers/search?index_filter=Dow%2030")
    assert res_filter.status_code == 200
    data_filter = res_filter.json()
    assert data_filter["index_filter"] == "Dow 30"
    assert any(r["ticker"] == "DIA" or "Dow 30" in r["index_tags"] for r in data_filter["results"])

    # Limit parameter
    res_lim = client.get("/api/forensics/tickers/search?limit=3")
    assert res_lim.status_code == 200
    data_lim = res_lim.json()
    assert len(data_lim["results"]) <= 3
