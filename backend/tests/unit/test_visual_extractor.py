"""Unit tests for SEC Filing Visual & Waterfall Exhibit Analyzer."""

from zaisaku.forensics.visual_extractor import (
    FilingVisualExtractor,
    FilingVisualsResponse,
)


def test_visual_extractor_nvda():
    """Verify visual exhibits are extracted for NVDA with waterfall steps and geographic slices."""
    extractor = FilingVisualExtractor()
    res = extractor.get_visual_exhibits("NVDA")
    assert isinstance(res, FilingVisualsResponse)
    assert res.ticker == "NVDA"
    assert len(res.exhibits) >= 3

    # Check Waterfall Bridge
    bridge = next(e for e in res.exhibits if e.exhibit_type == "waterfall_bridge")
    assert len(bridge.steps) >= 4
    assert bridge.non_gaap_divergence_pct is not None
    assert bridge.audit_warning is not None
    assert any(s.is_total for s in bridge.steps)

    # Check Geographic Exposure
    geo = next(e for e in res.exhibits if e.exhibit_type == "geographic_exposure")
    assert len(geo.pie_slices) >= 4
    total_pct = sum(slice_["percentage"] for slice_ in geo.pie_slices)
    assert 99.0 <= total_pct <= 101.0


def test_visual_extractor_fallback():
    """Verify fallback for generic tickers."""
    extractor = FilingVisualExtractor()
    res = extractor.get_visual_exhibits("CUSTOM_TICKER")
    assert res.ticker == "CUSTOM_TICKER"
    assert len(res.exhibits) >= 2


def test_visual_api_endpoint():
    """Verify GET /api/forensics/visuals/{ticker} endpoint."""
    from fastapi.testclient import TestClient

    from zaisaku.api.app import create_app

    client = TestClient(create_app())
    res = client.get("/api/forensics/visuals/NVDA")
    assert res.status_code == 200
    data = res.json()
    assert data["ticker"] == "NVDA"
    assert len(data["exhibits"]) >= 3
