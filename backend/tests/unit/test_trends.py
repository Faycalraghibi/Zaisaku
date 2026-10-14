import pytest
from fastapi.testclient import TestClient

from zaisaku.api.app import create_app
from zaisaku.forensics.trends import CompanyTrendsResponse, TrendsAnalyzer


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)

def test_trends_analyzer_nvda():
    analyzer = TrendsAnalyzer()
    res = analyzer.analyze("NVDA")
    assert isinstance(res, CompanyTrendsResponse)
    assert res.ticker == "NVDA"
    assert len(res.history) == 5
    # Verify chronological order
    years = [h.year for h in res.history]
    assert years == sorted(years)
    # Check fields
    last_year = res.history[-1]
    assert last_year.revenue > 0
    assert last_year.operating_cash_flow > 0
    assert last_year.accrual_gap is not None
    assert isinstance(res.anomalies, list)

def test_trends_analyzer_anomaly_detection():
    analyzer = TrendsAnalyzer()
    res = analyzer.analyze("FRAUD")
    assert len(res.anomalies) > 0
    # FRAUD should trigger at least one HIGH or CRITICAL anomaly
    severities = [a.severity for a in res.anomalies]
    assert any(s in ("HIGH", "CRITICAL") for s in severities)

def test_trends_api_endpoint(client):
    res = client.get("/api/forensics/trends/NVDA")
    assert res.status_code == 200
    data = res.json()
    assert data["ticker"] == "NVDA"
    assert len(data["history"]) == 5
    assert "anomalies" in data
