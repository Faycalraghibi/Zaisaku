"""Unit tests for Institutional Filing Anomaly Radar & Red-Flag Audit Alert Engine."""

from __future__ import annotations

import pytest

from zaisaku.forensics.anomaly_detector import (
    AnomalyCategory,
    AnomalyDetector,
    AnomalySeverity,
)


@pytest.fixture
def detector() -> AnomalyDetector:
    return AnomalyDetector()


def test_smci_critical_governance_anomalies(detector: AnomalyDetector):
    result = detector.detect_anomalies("SMCI")

    assert result.ticker == "SMCI"
    assert result.overall_anomaly_tier == "CRITICAL_ALERT"
    assert result.anomaly_score >= 80.0
    assert result.critical_count >= 2
    assert len(result.findings) >= 3

    categories = [f.category for f in result.findings]
    assert AnomalyCategory.EXECUTIVE_TURNOVER.value in categories
    assert AnomalyCategory.LATE_FILING_NT.value in categories

    severities = [f.severity for f in result.findings]
    assert AnomalySeverity.CRITICAL.value in severities


def test_nvda_low_risk_anomalies(detector: AnomalyDetector):
    result = detector.detect_anomalies("NVDA")

    assert result.ticker == "NVDA"
    assert result.overall_anomaly_tier == "LOW_RISK"
    assert result.anomaly_score <= 20.0
    assert result.critical_count == 0
    assert len(result.findings) >= 2


def test_aapl_low_risk_anomalies(detector: AnomalyDetector):
    result = detector.detect_anomalies("aapl")  # Case insensitive

    assert result.ticker == "AAPL"
    assert result.overall_anomaly_tier == "LOW_RISK"
    assert result.anomaly_score < 15.0
    assert result.critical_count == 0


def test_tsla_elevated_watch_anomalies(detector: AnomalyDetector):
    result = detector.detect_anomalies("TSLA")

    assert result.ticker == "TSLA"
    assert result.overall_anomaly_tier == "ELEVATED_WATCH"
    assert 20.0 <= result.anomaly_score <= 50.0
    assert result.elevated_count >= 1


def test_generic_ticker_fallback(detector: AnomalyDetector):
    result = detector.detect_anomalies("UNKNOWN_CO")

    assert result.ticker == "UNKNOWN_CO"
    assert result.overall_anomaly_tier == "LOW_RISK"
    assert result.critical_count == 0
    assert len(result.findings) >= 1
    assert "UNKNOWN_CO" in result.company_name

    # Check serialization
    res_dict = result.to_dict()
    assert res_dict["ticker"] == "UNKNOWN_CO"
    assert isinstance(res_dict["findings"], list)
    assert len(res_dict["findings"]) > 0
