"""Unit tests for Adversarial SEC / Big 4 Auditor Cross-Examination Studio."""

from zaisaku.forensics.auditor_inquiry import (
    AuditorCrossExaminer,
    AuditorCrossExamineResponse,
    CrossExamineRequest,
)


def test_auditor_cross_examiner_nvda():
    """Verify adversarial cross-examination inquiries generated for NVDA."""
    examiner = AuditorCrossExaminer()
    req = CrossExamineRequest(ticker="NVDA")
    res = examiner.cross_examine(req)

    assert isinstance(res, AuditorCrossExamineResponse)
    assert res.ticker == "NVDA"
    assert len(res.inquiries) >= 4
    assert 0 <= res.risk_index <= 100
    assert len(res.overall_posture) > 5

    # Check inquiry anatomy
    for inq in res.inquiries:
        assert len(inq.interrogation_prompt) > 30
        assert len(inq.statutory_rule_citation) > 3
        assert len(inq.required_evidentiary_documents) >= 2
        assert inq.severity in [
            "CRITICAL_DEFICIENCY",
            "MATERIAL_WEAKNESS_RISK",
            "SUBPOENA_VULNERABILITY",
            "SIGNIFICANT_SCRUTINY",
        ]


def test_auditor_cross_examiner_fallback():
    """Verify fallback response for unknown ticker."""
    examiner = AuditorCrossExaminer()
    req = CrossExamineRequest(ticker="XYZ_UNKNOWN")
    res = examiner.cross_examine(req)
    assert res.ticker == "XYZ_UNKNOWN"
    assert len(res.inquiries) >= 3


def test_auditor_api_endpoint():
    """Verify POST /api/forensics/auditor/cross-examine endpoint."""
    from fastapi.testclient import TestClient

    from zaisaku.api.app import create_app

    client = TestClient(create_app())
    res = client.post("/api/forensics/auditor/cross-examine", json={"ticker": "NVDA"})
    assert res.status_code == 200
    data = res.json()
    assert data["ticker"] == "NVDA"
    assert len(data["inquiries"]) >= 4
    assert "risk_index" in data
