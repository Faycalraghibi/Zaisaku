"""Unit tests for zaisaku.forensics — Filing Diff and Language Drift Engine."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from zaisaku.api.app import create_app
from zaisaku.config import Settings
from zaisaku.forensics.diff_engine import DiffEngine, FilingDiffResult
from zaisaku.forensics.section_extractor import SectionExtractor


class TestSectionExtractor:
    """Testing SectionExtractor on SEC text."""

    def test_clean_boilerplate(self):
        dirty = "Page 14\n\n\nSome important text.\n\n25 of 100\n\nMore text."
        cleaned = SectionExtractor.clean_boilerplate(dirty)
        assert "Page 14" not in cleaned
        assert "25 of 100" not in cleaned
        assert "Some important text." in cleaned
        assert "More text." in cleaned

    def test_extract_risk_factors(self):
        sample = (
            "TABLE OF CONTENTS\nItem 1A. Risk Factors ... 12\n\n"
            "PART I\nITEM 1. BUSINESS\nOur company makes hardware products.\n\n"
            "ITEM 1A. RISK FACTORS\n"
            "Our operations face severe supply chain shortages and export controls.\n"
            "Competition from hyperscalers is increasing rapidly.\n\n"
            "ITEM 1B. UNRESOLVED STAFF COMMENTS\nNone."
        )
        extracted = SectionExtractor.extract_section(sample, "item_1a_risk_factors")
        assert "supply chain shortages" in extracted
        assert "hyperscalers" in extracted
        assert "TABLE OF CONTENTS" not in extracted

    def test_extract_mda(self):
        sample = (
            "ITEM 7. MANAGEMENT'S DISCUSSION AND ANALYSIS\n"
            "Revenue grew 45% year over year driven by datacenter demand.\n"
            "Gross margin expanded by 200 basis points.\n\n"
            "ITEM 7A. QUANTITATIVE AND QUALITATIVE DISCLOSURES\nMarket risk is minimal."
        )
        extracted = SectionExtractor.extract_section(sample, "item_7_mda")
        assert "Revenue grew 45%" in extracted
        assert "ITEM 7A" not in extracted

    def test_extract_missing_section(self):
        sample = "Short text with no standard SEC items."
        assert SectionExtractor.extract_section(sample, "item_3_legal") == ""


class TestDiffEngine:
    """Testing DiffEngine semantic comparison and drift scoring."""

    def test_compare_sections_identical(self):
        text = "This is a standard risk disclosure regarding macroeconomic interest rates."
        diff = DiffEngine.compare_sections(text, text, "item_1a_risk_factors")
        assert diff.similarity_ratio == 1.0
        assert diff.drift_score == 0.0
        assert diff.severity == "LOW"
        assert len(diff.added_paragraphs) == 0
        assert len(diff.removed_paragraphs) == 0

    def test_compare_sections_completely_different(self):
        text_a = "We operate exclusively in cloud semiconductor design with major foundry partners."
        text_b = "We operate real estate commercial properties across the Midwestern United States."
        diff = DiffEngine.compare_sections(text_a, text_b, "item_1a_risk_factors")
        assert diff.drift_score > 60.0
        assert diff.severity in ("HIGH", "CRITICAL")
        assert len(diff.added_paragraphs) > 0

    def test_compare_sections_added_and_removed_paragraphs(self):
        prior = (
            "We rely on a single third-party foundry for manufacturing wafers.\n\n"
            "We have guaranteed customer warranty obligations for five years."
        )
        current = (
            "We rely on a single third-party foundry for manufacturing wafers.\n\n"
            "We are subject to newly introduced export control restrictions on advanced accelerators."
        )
        diff = DiffEngine.compare_sections(current, prior, "item_1a_risk_factors")
        assert diff.drift_score > 15.0
        assert any("export control restrictions" in p for p in diff.added_paragraphs)
        assert any("warranty obligations" in p for p in diff.removed_paragraphs)

    def test_compare_filings_structure(self):
        curr = (
            "ITEM 1A. RISK FACTORS\n"
            "New severe risks regarding geopolitics and trade tariffs are emerging.\n\n"
            "ITEM 1B. UNRESOLVED"
        )
        prior = (
            "ITEM 1A. RISK FACTORS\n"
            "Standard baseline operational risks apply to our business.\n\n"
            "ITEM 1B. UNRESOLVED"
        )
        res = DiffEngine.compare_filings(
            ticker="TEST",
            form="10-K",
            current_text=curr,
            prior_text=prior,
        )
        assert isinstance(res, FilingDiffResult)
        assert res.ticker == "TEST"
        assert "item_1a_risk_factors" in res.sections
        assert res.overall_drift_score > 0.0
        assert "TEST" in res.forensic_summary


class TestForensicsAPI:
    """Testing forensics API endpoints."""

    @pytest.fixture
    def client(self):
        settings = Settings(env="dev", llm_provider="")
        app = create_app(settings)
        return TestClient(app)

    def test_diff_text_endpoint(self, client):
        curr_text = "ITEM 1A. RISK FACTORS\nForeign exchange headwinds may impact European gross margins.\n\nITEM 1B"
        prior_text = "ITEM 1A. RISK FACTORS\nForeign exchange headwinds are negligible in Europe.\n\nITEM 1B"
        payload = {
            "ticker": "AAPL",
            "form": "10-K",
            "current_text": curr_text,
            "prior_text": prior_text,
            "section_name": "item_1a_risk_factors",
        }
        res = client.post("/api/forensics/diff/text", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["ticker"] == "AAPL"
        assert "sections" in data
        assert "overall_drift_score" in data
        assert data["overall_drift_score"] >= 0.0

    def test_diff_sec_empty_ticker(self, client):
        res = client.post("/api/forensics/diff", json={"ticker": "", "form": "10-K"})
        assert res.status_code == 400
        assert "Ticker cannot be empty" in res.json()["detail"]

    def test_diff_sec_mocked_success(self, client, monkeypatch):
        mock_html_curr = b"<html><body>ITEM 1A. RISK FACTORS\nNew tariff restrictions apply.</body></html>"
        mock_html_prior = b"<html><body>ITEM 1A. RISK FACTORS\nOld tariff provisions apply.</body></html>"

        def mock_fetch(self, ticker, form, count=2):
            return [("test_2024.htm", mock_html_curr), ("test_2023.htm", mock_html_prior)]

        from zaisaku.ingestion.sec_edgar import SECEdgarClient

        monkeypatch.setattr(SECEdgarClient, "fetch_consecutive_filings", mock_fetch)

        res = client.post("/api/forensics/diff", json={"ticker": "NVDA", "form": "10-K", "use_llm": False})
        assert res.status_code == 200
        data = res.json()
        assert data["ticker"] == "NVDA"
        assert data["current_filing"] == "test_2024.htm"
        assert data["prior_filing"] == "test_2023.htm"
        assert data["overall_drift_score"] >= 0.0
