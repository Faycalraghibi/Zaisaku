"""Unified Forensic Risk Scorecard and Composite Fragility Index (FFI) engine."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass
class PillarScore:
    name: str
    weight: float
    raw_score: float
    weighted_score: float
    status: str  # CLEAN, ELEVATED, CRITICAL
    key_findings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ScorecardResult:
    ticker: str
    company_name: str
    composite_ffi: float  # 0.0 to 100.0 (Forensic Fragility Index)
    risk_level: str  # CLEAN, WATCHLIST, HIGH_RISK, CRITICAL_ALERT
    recommendation: str
    pillars: dict[str, PillarScore]
    red_flags: list[str] = field(default_factory=list)
    summary: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


class ForensicScorecard:
    """Synthesizes Language Drift, Beneish Accounting Quality, and Call Contradictions into an FFI score."""

    DRIFT_WEIGHT: float = 0.30
    ACCOUNTING_WEIGHT: float = 0.40
    CONTRADICTION_WEIGHT: float = 0.30

    @classmethod
    def calculate(
        cls,
        ticker: str,
        company_name: str = "",
        language_drift_score: float = 0.0,
        beneish_m_score: float = -2.50,
        footnote_hazards_count: int = 0,
        call_contradictions_score: float = 0.0,
        contradiction_count: int = 0,
    ) -> ScorecardResult:
        ticker = ticker.strip().upper() or "CUSTOM"
        company_name = company_name.strip() or ticker

        # 1. Pillar 1: Language Drift & Silent Edits (30%)
        p1_raw = max(0.0, min(100.0, float(language_drift_score)))
        p1_status = "CRITICAL" if p1_raw >= 50.0 else ("ELEVATED" if p1_raw >= 25.0 else "CLEAN")
        p1_findings: list[str] = []
        if p1_raw >= 50.0:
            p1_findings.append(f"Severe language drift ({p1_raw}%): Substantial modifications in SEC risk sections.")
        elif p1_raw >= 25.0:
            p1_findings.append(f"Moderate language drift ({p1_raw}%): Notable risk clause additions or omissions.")
        else:
            p1_findings.append("Consistent disclosure language between consecutive filings.")

        # 2. Pillar 2: Forensic Accounting & Beneish M-Score (40%)
        # Normal baseline M-score is -2.50 to -3.0. Threshold is -1.78.
        if beneish_m_score <= -2.50:
            base_acc = 10.0
        elif beneish_m_score >= -1.49:
            base_acc = 85.0 + min(15.0, (beneish_m_score - (-1.49)) * 30.0)
        else:
            # Linear interpolation between -2.50 (10.0) and -1.49 (85.0)
            ratio = (beneish_m_score - (-2.50)) / (-1.49 - (-2.50))
            base_acc = 10.0 + (ratio * 75.0)

        footnote_penalty = min(40.0, footnote_hazards_count * 15.0)
        p2_raw = max(0.0, min(100.0, round(base_acc + footnote_penalty, 1)))
        p2_status = "CRITICAL" if p2_raw >= 60.0 else ("ELEVATED" if p2_raw >= 35.0 else "CLEAN")
        p2_findings: list[str] = []
        if beneish_m_score > -1.78:
            p2_findings.append(f"Beneish M-Score of {beneish_m_score} exceeds the -1.78 manipulation threshold.")
        if footnote_hazards_count > 0:
            p2_findings.append(f"Detected {footnote_hazards_count} critical buried footnote hazard(s).")
        if not p2_findings:
            p2_findings.append(f"Beneish M-Score of {beneish_m_score} indicates normal earnings quality.")

        # 3. Pillar 3: Call vs 10-Q Contradictions (30%)
        call_penalty = min(40.0, contradiction_count * 15.0)
        p3_raw = max(0.0, min(100.0, round(float(call_contradictions_score) + call_penalty, 1)))
        p3_status = "CRITICAL" if p3_raw >= 50.0 else ("ELEVATED" if p3_raw >= 25.0 else "CLEAN")
        p3_findings: list[str] = []
        if contradiction_count > 0:
            p3_findings.append(f"Identified {contradiction_count} direct guidance/operational contradiction(s).")
        if call_contradictions_score >= 35.0:
            p3_findings.append(f"Tone decoupling of {call_contradictions_score}% between spoken call and 10-Q.")
        if not p3_findings:
            p3_findings.append("Spoken executive guidance aligns with regulatory filing disclosures.")

        # Composite Forensic Fragility Index (FFI)
        p1_weighted = round(p1_raw * cls.DRIFT_WEIGHT, 2)
        p2_weighted = round(p2_raw * cls.ACCOUNTING_WEIGHT, 2)
        p3_weighted = round(p3_raw * cls.CONTRADICTION_WEIGHT, 2)
        composite_ffi = round(p1_weighted + p2_weighted + p3_weighted, 1)

        # Risk level categorization
        if composite_ffi >= 65.0:
            risk_level = "CRITICAL_ALERT"
            recommendation = "IMMEDIATE_FRAUD_RISK"
        elif composite_ffi >= 45.0:
            risk_level = "HIGH_RISK"
            recommendation = "AVOID_OR_SHORT"
        elif composite_ffi >= 25.0:
            risk_level = "WATCHLIST"
            recommendation = "MONITOR_CLOSELY"
        else:
            risk_level = "CLEAN"
            recommendation = "SAFE_FOR_INVESTMENT"

        # Compile red flags
        red_flags: list[str] = []
        if p1_raw >= 35.0:
            red_flags.append(f"Stealth disclosure modifications: {p1_raw}% drift in SEC risk items.")
        if beneish_m_score > -1.78:
            red_flags.append(f"Earnings manipulation red flag: Beneish M-Score of {beneish_m_score} > -1.78.")
        if footnote_hazards_count > 0:
            red_flags.append(f"Footnote landmines: {footnote_hazards_count} hazardous disclosures detected.")
        if contradiction_count > 0:
            red_flags.append(f"Guidance traps: {contradiction_count} call vs 10-Q contradiction(s) flagged.")

        summary = (
            f"{company_name} receives a Forensic Fragility Index (FFI) of {composite_ffi}/100 ({risk_level}). "
            f"Accounting quality score is {p2_raw}/100, language drift is {p1_raw}/100, "
            f"and call divergence is {p3_raw}/100."
        )

        pillars = {
            "language_drift": PillarScore(
                name="Filing Language Drift",
                weight=cls.DRIFT_WEIGHT,
                raw_score=p1_raw,
                weighted_score=p1_weighted,
                status=p1_status,
                key_findings=p1_findings,
            ),
            "forensic_accounting": PillarScore(
                name="Forensic Accounting & Footnotes",
                weight=cls.ACCOUNTING_WEIGHT,
                raw_score=p2_raw,
                weighted_score=p2_weighted,
                status=p2_status,
                key_findings=p2_findings,
            ),
            "call_contradictions": PillarScore(
                name="Call vs 10-Q Contradictions",
                weight=cls.CONTRADICTION_WEIGHT,
                raw_score=p3_raw,
                weighted_score=p3_weighted,
                status=p3_status,
                key_findings=p3_findings,
            ),
        }

        return ScorecardResult(
            ticker=ticker,
            company_name=company_name,
            composite_ffi=composite_ffi,
            risk_level=risk_level,
            recommendation=recommendation,
            pillars=pillars,
            red_flags=red_flags,
            summary=summary,
        )
