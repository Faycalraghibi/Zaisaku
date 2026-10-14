"""Unit tests for Beneish M-Score and FootnoteScanner forensic modules."""

from __future__ import annotations

import pytest

from zaisaku.forensics.beneish import BeneishCalculator, BeneishMetrics
from zaisaku.forensics.footnote_scanner import FootnoteRiskCategory, FootnoteScanner


@pytest.fixture
def clean_metrics() -> BeneishMetrics:
    """Financial profile of a clean, high-quality company with healthy cash flow."""
    return BeneishMetrics(
        sales_t=1000.0,
        sales_t_prev=950.0,
        cogs_t=600.0,
        cogs_t_prev=575.0,
        receivables_t=100.0,
        receivables_t_prev=105.0,
        current_assets_t=400.0,
        current_assets_t_prev=380.0,
        ppe_t=500.0,
        ppe_t_prev=480.0,
        total_assets_t=1200.0,
        total_assets_t_prev=1150.0,
        depreciation_t=50.0,
        depreciation_t_prev=48.0,
        sga_t=150.0,
        sga_t_prev=145.0,
        long_term_debt_t=200.0,
        long_term_debt_t_prev=220.0,
        net_income_t=120.0,
        operating_cash_flow_t=160.0,  # Cash flow > Net income (negative accruals)
    )


@pytest.fixture
def manipulator_metrics() -> BeneishMetrics:
    """Financial profile exhibiting aggressive accruals, channel stuffing, and margin compression."""
    return BeneishMetrics(
        sales_t=2500.0,
        sales_t_prev=1500.0,  # High growth
        cogs_t=1800.0,
        cogs_t_prev=900.0,  # Margin collapsed from 40% to 28% (GMI > 1)
        receivables_t=850.0,  # Receivables spiked (DSRI >> 1)
        receivables_t_prev=200.0,
        current_assets_t=1200.0,
        current_assets_t_prev=600.0,
        ppe_t=600.0,
        ppe_t_prev=500.0,
        total_assets_t=3200.0,
        total_assets_t_prev=1600.0,
        depreciation_t=20.0,  # Depreciation slowed (DEPI > 1)
        depreciation_t_prev=40.0,
        sga_t=300.0,
        sga_t_prev=180.0,
        long_term_debt_t=1400.0,  # Surging leverage
        long_term_debt_t_prev=400.0,
        net_income_t=350.0,  # Accounting profit positive
        operating_cash_flow_t=-120.0,  # Cash bleeding (TATA massive positive accruals)
    )


def test_beneish_clean_profile(clean_metrics: BeneishMetrics):
    result = BeneishCalculator.calculate(clean_metrics)

    assert result.m_score < -1.78
    assert result.is_manipulator_probable is False
    assert result.risk_level == "SAFE"
    assert "DSRI" in result.indices
    assert "TATA" in result.indices
    assert result.indices["TATA"] < 0  # Negative accruals because OCF > Net Income


def test_beneish_manipulator_profile(manipulator_metrics: BeneishMetrics):
    result = BeneishCalculator.calculate(manipulator_metrics)

    assert result.m_score > -1.78
    assert result.is_manipulator_probable is True
    assert result.risk_level in ("ELEVATED", "HIGH_RISK")
    assert len(result.flagged_indices) > 0
    # Flagged indices should capture accounts receivable surge and accrual anomaly
    flagged_text = " ".join(result.flagged_indices)
    assert "DSRI" in flagged_text or "TATA" in flagged_text


def test_beneish_zero_division_safety():
    zero_data = BeneishMetrics(
        sales_t=0.0,
        sales_t_prev=0.0,
        cogs_t=0.0,
        cogs_t_prev=0.0,
        receivables_t=0.0,
        receivables_t_prev=0.0,
        current_assets_t=0.0,
        current_assets_t_prev=0.0,
        ppe_t=0.0,
        ppe_t_prev=0.0,
        total_assets_t=0.0,
        total_assets_t_prev=0.0,
        depreciation_t=0.0,
        depreciation_t_prev=0.0,
        sga_t=0.0,
        sga_t_prev=0.0,
        long_term_debt_t=0.0,
        long_term_debt_t_prev=0.0,
        net_income_t=0.0,
        operating_cash_flow_t=0.0,
    )
    result = BeneishCalculator.calculate(zero_data)
    assert isinstance(result.m_score, float)
    assert result.m_score == result.m_score  # Not NaN


def test_footnote_scanner_empty():
    res = FootnoteScanner.scan("")
    assert res.total_findings == 0
    assert res.high_risk_count == 0

    res_none = FootnoteScanner.scan("   ")
    assert res_none.total_findings == 0


def test_footnote_scanner_detects_all_categories():
    sample_filing = """
    Note 14. Related Party Transactions
    During fiscal 2023, the Company entered into consulting agreements with an affiliate of our CEO,
    and extended unsecured loans to executive officers amounting to $12.5 million. Additionally,
    the Company guarantees debt of variable interest entities.

    Note 18. Concentrations of Risk
    In 2023, a single customer accounted for 24.5% of net sales. The loss of this major customer
    would have an immediate material adverse effect on operating results.

    Note 7. Held-to-Maturity Investments
    The Company's held-to-maturity securities portfolio had gross unrealized losses of $1.8 billion
    due to prevailing interest rate shocks, resulting in significant accumulated other comprehensive loss.

    Note 10. Goodwill and Other Intangibles
    As of year-end, the carrying value of goodwill exceeded its implied fair value in the cloud software
    division, requiring a quantitative goodwill impairment charge.

    Item 9A. Controls and Procedures
    Management evaluated the effectiveness of our internal control over financial reporting and identified
    a material weakness in internal control over financial reporting related to revenue recognition controls.
    Separately, our independent registered public accounting firm resigned following disagreements with auditors.
    """

    res = FootnoteScanner.scan(sample_filing)

    assert res.total_findings >= 5
    assert res.high_risk_count >= 3

    categories = {f.category for f in res.findings}
    assert FootnoteRiskCategory.RELATED_PARTY.value in categories
    assert FootnoteRiskCategory.CUSTOMER_CONCENTRATION.value in categories
    assert FootnoteRiskCategory.HTM_UNREALIZED_LOSSES.value in categories
    assert FootnoteRiskCategory.GOODWILL_IMPAIRMENT.value in categories
    assert FootnoteRiskCategory.AUDITOR_MATERIAL_WEAKNESS.value in categories


def test_footnote_scanner_clean_text():
    clean_text = """
    Item 1. Business.
    We are a leading provider of enterprise productivity software solutions.
    Our operations are diversified across over 10,000 customers globally, with no single customer
    exceeding 2% of annual revenues. Our cash reserves are held strictly in short-term US Treasury bills.
    """
    res = FootnoteScanner.scan(clean_text)
    assert res.total_findings == 0
    assert "No critical footnote hazards" in res.summary


def test_footnote_scanner_negations_and_thresholds():
    compliant_filing = """
    Item 9A. Controls and Procedures
    Management evaluated internal controls and concluded that no material weakness in internal control
    over financial reporting was identified.
    Separately, there were no disagreements with former accountants on any matter of accounting principles.
    In addition, one customer accounted for 3.5% of net sales during the fiscal year.
    The company performed its annual goodwill impairment test in the fourth quarter.
    """
    res = FootnoteScanner.scan(compliant_filing)
    assert res.total_findings == 0
    assert res.high_risk_count == 0


def test_beneish_api_endpoint(clean_metrics: BeneishMetrics):
    from dataclasses import asdict

    from fastapi.testclient import TestClient

    from zaisaku.api.app import create_app
    from zaisaku.config import Settings

    settings = Settings(env="dev", llm_provider="")
    app = create_app(settings)
    client = TestClient(app)

    payload = asdict(clean_metrics)
    res = client.post("/api/forensics/mscore", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "m_score" in data
    assert data["risk_level"] == "SAFE"
    assert data["is_manipulator_probable"] is False
    assert "indices" in data


def test_footnote_scan_api_endpoint():
    from fastapi.testclient import TestClient

    from zaisaku.api.app import create_app
    from zaisaku.config import Settings

    settings = Settings(env="dev", llm_provider="")
    app = create_app(settings)
    client = TestClient(app)

    payload = {
        "text": (
            "We discovered a material weakness in internal control over financial reporting. "
            "Also, a single customer accounted for 30% of total revenue."
        )
    }
    res = client.post("/api/forensics/footnotes/scan", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["total_findings"] >= 2
    assert data["high_risk_count"] >= 1
    assert len(data["findings"]) >= 2

