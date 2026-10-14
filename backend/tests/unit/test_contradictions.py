"""Unit tests for ContradictionRadar forensic module and API."""

from __future__ import annotations

from fastapi.testclient import TestClient

from zaisaku.api.app import create_app
from zaisaku.config import Settings
from zaisaku.forensics.contradiction_radar import ContradictionRadar


def test_sentiment_score_calculation():
    bullish_text = (
        "We are seeing robust, unprecedented accelerating demand with strong pricing power and record pipeline."
    )
    score = ContradictionRadar.calculate_sentiment_score(bullish_text, is_call=True)
    assert score > 0.5

    cautious_text = "We face macroeconomic headwinds, softness in enterprise IT, and severe deceleration."
    call_neg = ContradictionRadar.calculate_sentiment_score(cautious_text, is_call=True)
    assert call_neg < -0.3

    filing_risk = "Material adverse effects, gross margin compression, order cancellations, and severe shortages."
    filing_neg = ContradictionRadar.calculate_sentiment_score(filing_risk, is_call=False)
    assert filing_neg < -0.3

    empty_score = ContradictionRadar.calculate_sentiment_score("", is_call=True)
    assert empty_score == 0.0


def test_detect_contradictions_demand_and_margins():
    call_text = """
    CEO Remarks:
    We are thrilled with our execution this quarter. We are seeing unprecedented demand and record backlog growth
    across our data center products. Furthermore, our pricing power remains strong, enabling expanding gross margins.
    """

    filing_text = """
    Item 7. Management's Discussion and Analysis
    During the three months ended June 30, we experienced customer pushouts and order cancellations.
    Gross margins compressed by 340 basis points due to aggressive pricing concessions required to retain deal volume.
    """

    contradictions = ContradictionRadar.detect_contradictions_deterministic(call_text, filing_text)

    assert len(contradictions) >= 2
    topics = {c.topic for c in contradictions}
    assert "Demand & Backlog Visibility" in topics
    assert "Gross Margins & Pricing Power" in topics

    demand_item = next(c for c in contradictions if c.topic == "Demand & Backlog Visibility")
    assert demand_item.severity == "CRITICAL"
    assert "demand" in demand_item.call_statement.lower()
    assert "cancellations" in demand_item.filing_statement.lower() or "pushouts" in demand_item.filing_statement.lower()


def test_detect_contradictions_supply_chain_and_legal():
    call_text = """
    COO Remarks:
    Our supply chain bottlenecks are fully resolved and foundry allocations have normalized.
    Regarding the trade inquiry, these are routine regulatory matters and we are completely confident in our position.
    """

    filing_text = """
    Item 1A. Risk Factors
    We continue to experience severe supply chain disruptions and critical component shortages.
    Item 3. Legal Proceedings
    Subpoenas received from the DOJ regarding an investigation, posing material unaccrued contingencies.
    """

    contradictions = ContradictionRadar.detect_contradictions_deterministic(call_text, filing_text)

    assert len(contradictions) >= 2
    topics = {c.topic for c in contradictions}
    assert "Supply Chain & Manufacturing Bottlenecks" in topics
    assert "Regulatory Investigations & Litigation Exposure" in topics


def test_contradiction_radar_full_analyze_aligned():
    call_text = "We had a balanced quarter in line with expectations with steady product adoption."
    filing_text = "Business operations proceeded in line with historical baseline seasonality."

    res = ContradictionRadar.analyze("TEST", call_text, filing_text)
    assert res.ticker == "TEST"
    assert res.contradictions_count == 0
    assert res.divergence_severity in ("LOW", "MODERATE")


def test_contradictions_api_endpoint():
    settings = Settings(env="dev", llm_provider="")
    app = create_app(settings)
    client = TestClient(app)

    payload = {
        "ticker": "TECH",
        "call_text": "We are experiencing record demand and expanding our pipeline significantly.",
        "filing_text": "Customer order cancellations and reduced visibility materially affected bookings.",
        "use_llm": False,
    }

    res = client.post("/api/forensics/contradictions", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["ticker"] == "TECH"
    assert data["contradictions_count"] >= 1
    assert "Demand" in data["contradictions"][0]["topic"]
    assert data["tone_divergence_score"] > 0.0


def test_bearish_filing_sentiment_reachability():
    call_text = "We remain optimistic about our market position."
    filing_text = (
        "Material adverse effect on our business. Decreased gross margins, margin compression, "
        "severe cancellations, pushouts, supply shortages, and massive asset impairments."
    )
    res = ContradictionRadar.analyze("RISK", call_text, filing_text)
    assert res.filing_sentiment == "BEARISH"


def test_contradiction_radar_with_mocked_llm():
    class MockLLMRouter:
        def generate(self, prompt: str, system_prompt: str) -> dict:
            assert "system_prompt" in system_prompt.lower() or "forensic" in system_prompt.lower()
            assert "EXCERPT" in prompt
            return {
                "text": (
                    '[{"topic": "Custom Guidance Mismatch", "severity": "HIGH", '
                    '"call_statement": "Growth is steady.", "filing_statement": "Sales dropped.", '
                    '"divergence_analysis": "Management claimed growth while filing disclosed drop."}]'
                )
            }

    # Text that produces 0 deterministic contradictions
    call_text = "General remarks about our cloud operations."
    filing_text = "General corporate reporting disclosures."
    res = ContradictionRadar.analyze("MOCK", call_text, filing_text, llm=MockLLMRouter())

    assert res.contradictions_count == 1
    assert res.contradictions[0].topic == "Custom Guidance Mismatch"
    assert res.contradictions[0].severity == "HIGH"

