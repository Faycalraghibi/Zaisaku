from __future__ import annotations

from zaisaku.forensics.report_generator import ForensicReportGenerator
from zaisaku.forensics.scorecard import ForensicScorecard


class TestForensicReportGenerator:
    def test_generate_memo_minimal(self):
        memo = ForensicReportGenerator.generate_memo(ticker="AAPL")
        assert "FORENSIC FINANCIAL DUE DILIGENCE MEMORANDUM" in memo
        assert "AAPL" in memo
        assert "METADATA & SUMMARY RISK CLASSIFICATION" in memo
        assert "QUANTITATIVE FORENSIC ACCOUNTING" in memo
        assert "DEEP FOOTNOTE HAZARDS" in memo
        assert "FILING LANGUAGE DRIFT" in memo
        assert "CONTRADICTION RADAR" in memo
        assert "INVESTMENT COMMITTEE ACTION CHECKLIST" in memo

    def test_generate_memo_with_scorecard(self):
        scorecard = ForensicScorecard.calculate(
            ticker="NVDA",
            company_name="NVIDIA Corporation",
            language_drift_score=45.0,
            beneish_m_score=-1.65,
            footnote_hazards_count=2,
            call_contradictions_score=40.0,
            contradiction_count=1,
        )
        memo = ForensicReportGenerator.generate_memo(
            ticker="NVDA",
            company_name="NVIDIA Corporation",
            scorecard=scorecard.to_dict(),
        )
        assert "NVIDIA Corporation (NVDA)" in memo
        assert "Composite Forensic Fragility Index (FFI):" in memo
        assert "Beneish M-Score of -1.65 exceeds the -1.78 manipulation threshold" in memo
        assert "Detected 2 critical buried footnote hazard(s)" in memo
        assert "40.0 / 100" in memo or "45.0 / 100" in memo

    def test_generate_memo_with_full_details(self):
        beneish_details = {
            "m_score": -1.45,
            "is_manipulator": True,
            "risk_level": "HIGH_MANIPULATION_RISK",
            "indices": {
                "DSRI": {"value": 1.45, "flagged": True, "description": "Days Sales in Receivables Index"},
                "GMI": {"value": 1.25, "flagged": True, "description": "Gross Margin Index"},
                "AQI": {"value": 0.95, "flagged": False, "description": "Asset Quality Index"},
                "SGI": {"value": 1.60, "flagged": True, "description": "Sales Growth Index"},
                "DEPI": {"value": 0.85, "flagged": False, "description": "Depreciation Index"},
                "SGAI": {"value": 1.05, "flagged": False, "description": "SGAI Index"},
                "LVGI": {"value": 1.10, "flagged": False, "description": "Leverage Index"},
                "TATA": {"value": 0.08, "flagged": True, "description": "Total Accruals to Total Assets"},
            },
        }
        footnote_findings = [
            {
                "category": "SOX_404_MATERIAL_WEAKNESS",
                "title": "Internal Control Material Weakness",
                "severity": "CRITICAL",
                "quote": "Management identified a material weakness in internal control over revenue cutoff.",
            },
            {
                "category": "CUSTOMER_CONCENTRATION",
                "title": "Major Customer Concentration",
                "severity": "HIGH",
                "quote": "Customer A accounted for 24% of consolidated total revenue.",
            },
        ]
        diff_result = {
            "overall_drift_score": 62.5,
            "overall_severity": "HIGH",
            "forensic_summary": "Substantial removal of supply chain liability warranties.",
            "sections": {
                "item_1a_risk_factors": {
                    "similarity_ratio": 0.75,
                    "drift_score": 25.0,
                    "severity": "ELEVATED",
                    "added_paragraphs": ["New sovereign export controls imposed in Q3."],
                    "removed_paragraphs": ["Guaranteed minimum purchase commitments from tier-1 suppliers."],
                }
            },
        }
        contradiction_result = {
            "tone_divergence_score": 48.0,
            "call_sentiment": "BULLISH",
            "filing_sentiment": "BEARISH",
            "divergence_severity": "HIGH",
            "contradictions_count": 1,
            "contradictions": [
                {
                    "topic": "DEMAND_GUIDANCE",
                    "severity": "HIGH",
                    "call_statement": "Demand visibility is unprecedented through next fiscal year.",
                    "filing_statement": "Backlog cancellation rates increased significantly.",
                    "divergence_analysis": "Executive confidence contrasts with audited cancellation surge.",
                }
            ],
        }

        memo = ForensicReportGenerator.generate_memo(
            ticker="SMCI",
            company_name="Super Micro Computer",
            beneish=beneish_details,
            footnote_findings=footnote_findings,
            diff_result=diff_result,
            contradiction_result=contradiction_result,
        )

        assert "SMCI" in memo
        assert "HIGH_MANIPULATION_RISK" in memo
        assert "DSRI" in memo
        assert "1.45" in memo
        assert "Internal Control Material Weakness" in memo
        assert "Customer A accounted for 24%" in memo
        assert "New sovereign export controls imposed in Q3." in memo
        assert "Demand visibility is unprecedented through next fiscal year." in memo
        assert "Backlog cancellation rates increased significantly." in memo
