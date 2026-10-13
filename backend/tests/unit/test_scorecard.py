"""Unit tests for ForensicScorecard composite risk engine and API."""

from __future__ import annotations

from fastapi.testclient import TestClient

from zaisaku.api.app import create_app
from zaisaku.config import Settings
from zaisaku.forensics.scorecard import ForensicScorecard


def test_scorecard_clean_profile():
    res = ForensicScorecard.calculate(
        ticker="AAPL",
        company_name="Apple Inc.",
        language_drift_score=6.5,
        beneish_m_score=-2.85,
        footnote_hazards_count=0,
        call_contradictions_score=12.0,
        contradiction_count=0,
    )

    assert res.ticker == "AAPL"
    assert res.company_name == "Apple Inc."
    assert res.composite_ffi < 25.0
    assert res.risk_level == "CLEAN"
    assert res.recommendation == "SAFE_FOR_INVESTMENT"
    assert len(res.red_flags) == 0
    assert "language_drift" in res.pillars
    assert "forensic_accounting" in res.pillars
    assert "call_contradictions" in res.pillars


def test_scorecard_critical_alert_profile():
    res = ForensicScorecard.calculate(
        ticker="ENRN",
        company_name="Enron Corporation",
        language_drift_score=72.0,
        beneish_m_score=-1.15,
        footnote_hazards_count=3,
        call_contradictions_score=68.0,
        contradiction_count=3,
    )

    assert res.composite_ffi >= 65.0
    assert res.risk_level == "CRITICAL_ALERT"
    assert res.recommendation == "IMMEDIATE_FRAUD_RISK"
    assert len(res.red_flags) >= 3
    assert any("Beneish" in rf for rf in res.red_flags)
    assert any("drift" in rf.lower() for rf in res.red_flags)


def test_scorecard_clamping_and_weights():
    res = ForensicScorecard.calculate(
        ticker="TEST",
        language_drift_score=150.0,  # Clamped to 100
        beneish_m_score=5.0,  # Clamped to 100
        footnote_hazards_count=10,
        call_contradictions_score=200.0,
        contradiction_count=10,
    )
    assert res.composite_ffi <= 100.0
    assert res.pillars["language_drift"].raw_score == 100.0
    assert res.pillars["forensic_accounting"].raw_score == 100.0
    assert res.pillars["call_contradictions"].raw_score == 100.0


def test_scorecard_api_endpoint():
    settings = Settings(env="dev", llm_provider="")
    app = create_app(settings)
    client = TestClient(app)

    payload = {
        "ticker": "MSFT",
        "company_name": "Microsoft Corporation",
        "language_drift_score": 14.5,
        "beneish_m_score": -2.40,
        "footnote_hazards_count": 0,
        "call_contradictions_score": 18.0,
        "contradiction_count": 0,
    }

    res = client.post("/api/forensics/scorecard", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["ticker"] == "MSFT"
    assert "composite_ffi" in data
    assert "risk_level" in data
    assert "pillars" in data
    assert len(data["pillars"]) == 3
