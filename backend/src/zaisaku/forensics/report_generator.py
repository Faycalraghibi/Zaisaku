"""Institutional Forensic Due Diligence Memorandum generator."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from zaisaku.forensics.scorecard import ForensicScorecard


class ForensicReportGenerator:
    """Generates comprehensive, investment-committee-grade Forensic Due Diligence Memorandums."""

    @classmethod
    def generate_memo(
        cls,
        ticker: str,
        company_name: str = "",
        scorecard: dict[str, Any] | None = None,
        beneish: dict[str, Any] | None = None,
        footnote_findings: list[dict[str, Any]] | None = None,
        diff_result: dict[str, Any] | None = None,
        contradiction_result: dict[str, Any] | None = None,
    ) -> str:
        ticker = ticker.strip().upper() or "CUSTOM"
        company_name = company_name.strip() or ticker
        date_str = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")

        # Fallback scorecard if not provided
        if not scorecard:
            m_val = float(beneish.get("m_score", -2.50)) if beneish else -2.50
            hazards_count = len(footnote_findings) if footnote_findings else 0
            drift_val = float(diff_result.get("overall_drift_score", 0.0)) if diff_result else 0.0
            contra_val = float(contradiction_result.get("tone_divergence_score", 0.0)) if contradiction_result else 0.0
            contra_cnt = int(contradiction_result.get("contradictions_count", 0)) if contradiction_result else 0

            sc_obj = ForensicScorecard.calculate(
                ticker=ticker,
                company_name=company_name,
                language_drift_score=drift_val,
                beneish_m_score=m_val,
                footnote_hazards_count=hazards_count,
                call_contradictions_score=contra_val,
                contradiction_count=contra_cnt,
            )
            scorecard = sc_obj.to_dict()

        ffi_score = scorecard.get("composite_ffi", 0.0)
        risk_level = scorecard.get("risk_level", "CLEAN")
        recommendation = scorecard.get("recommendation", "Standard monitoring")
        summary = scorecard.get("summary", "No summary provided.")
        pillars = scorecard.get("pillars", {})

        p1 = pillars.get("language_drift", {})
        p2 = pillars.get("forensic_accounting") or pillars.get("accounting_quality") or {}
        p3 = pillars.get("call_contradictions") or pillars.get("call_divergence") or {}

        p1_raw = p1.get("raw_score", 0.0)
        p1_wt = p1.get("weighted_score", 0.0)
        p1_st = p1.get("status", "CLEAN")
        p1_findings = "; ".join(p1.get("key_findings", [])) or "No material drift detected."

        p2_raw = p2.get("raw_score", 0.0)
        p2_wt = p2.get("weighted_score", 0.0)
        p2_st = p2.get("status", "CLEAN")
        p2_findings = "; ".join(p2.get("key_findings", [])) or "Normal accounting parameters."

        p3_raw = p3.get("raw_score", 0.0)
        p3_wt = p3.get("weighted_score", 0.0)
        p3_st = p3.get("status", "CLEAN")
        p3_findings = "; ".join(p3.get("key_findings", [])) or "Executive remarks aligned with filing."

        # Risk indicator badge
        risk_badges = {
            "CLEAN": "🟢 LOW RISK",
            "WATCHLIST": "🟡 ELEVATED RISK",
            "HIGH_RISK": "🟠 HIGH FRAGILITY RISK",
            "CRITICAL_ALERT": "🔴 SEVERE FRAGILITY RISK",
        }
        badge = risk_badges.get(risk_level, f"⚪ {risk_level}")

        # Beneish section
        beneish_section = cls._render_beneish_section(beneish)

        # Footnotes section
        footnotes_section = cls._render_footnotes_section(footnote_findings)

        # Filing Diff section
        diff_section = cls._render_diff_section(diff_result)

        # Contradictions section
        contradictions_section = cls._render_contradictions_section(contradiction_result)

        # Action checklist
        checklist_section = cls._render_checklist(risk_level, p1_st, p2_st, p3_st)

        memo = f"""# 🕵️ FORENSIC FINANCIAL DUE DILIGENCE MEMORANDUM
**Confidential | Institutional Forensic Risk Assessment**

---

### METADATA & SUMMARY RISK CLASSIFICATION
- **Target Company / Ticker:** {company_name} ({ticker})
- **Date Generated:** {date_str}
- **Composite Forensic Fragility Index (FFI):** **{ffi_score:.1f} / 100**
- **Risk Classification:** **{badge}**
- **Committee Directive:** *{recommendation}*

---

### 1. EXECUTIVE SUMMARY & FRAGILITY SYNTHESIS
{summary}

#### Fragility Pillar Weightings:
| Forensic Intelligence Pillar | Weight | Raw Risk Score | Weighted Impact | Status | Key Signals |
|:---|:---:|:---:|:---:|:---:|:---|
| 📉 **Language Drift & Silent De-Risking** | 30% | {p1_raw:.1f} / 100 | {p1_wt:.1f} pts | `{p1_st}` | {p1_findings} |
| ⚖️ **Forensic Accounting & Accrual Quality** | 40% | {p2_raw:.1f} / 100 | {p2_wt:.1f} pts | `{p2_st}` | {p2_findings} |
| 🎙️ **Call vs 10-Q Contradictions** | 30% | {p3_raw:.1f} / 100 | {p3_wt:.1f} pts | `{p3_st}` | {p3_findings} |

---

### 2. QUANTITATIVE FORENSIC ACCOUNTING (BENEISH M-SCORE ANALYSIS)
{beneish_section}

---

### 3. DEEP FOOTNOTE HAZARDS & BURIED LIABILITIES
{footnotes_section}

---

### 4. FILING LANGUAGE DRIFT & SILENT DE-RISKING ("LAZY PRICES" ANALYSIS)
{diff_section}

---

### 5. EARNINGS CALL VS REGULATORY FILING CONTRADICTION RADAR
{contradictions_section}

---

### 6. INVESTMENT COMMITTEE ACTION CHECKLIST & TARGETED INQUIRIES
{checklist_section}

---
*Notice: This forensic audit memorandum was generated automatically by Zaisaku 2.0 AI Forensic*
*Financial Intelligence Platform for research, risk modeling, and investigative due diligence purposes.*
"""
        return memo.strip()

    @classmethod
    def _render_beneish_section(cls, beneish: dict[str, Any] | None) -> str:
        if not beneish:
            return "_No raw Beneish balance-sheet metrics ingested for this run. Normal baseline applied._"

        m_score = beneish.get("m_score", -2.50)
        is_manip = beneish.get("is_manipulator", False)
        risk = beneish.get("risk_level", "NORMAL")
        status_text = (
            "🚨 **HIGH PROBABILITY OF FINANCIAL MANIPULATION** (Threshold: > -1.78)"
            if is_manip or m_score > -1.78
            else "✅ **LOW PROBABILITY OF MANIPULATION** (Baseline: < -1.78)"
        )

        indices = beneish.get("indices", {})
        metric_meta = {
            "DSRI": ("Days Sales in Receivables", 1.00, "Receivables vs Sales velocity (Channel Stuffing check)"),
            "GMI": ("Gross Margin Index", 1.00, "Margin deterioration creating pressure to manipulate"),
            "AQI": ("Asset Quality Index", 1.00, "Capitalization of routine operating costs into non-current assets"),
            "SGI": ("Sales Growth Index", 1.00, "Decelerating growth momentum pressure"),
            "DEPI": ("Depreciation Index", 1.00, "Artificial slowing of depreciation to lift net income"),
            "SGAI": ("SG&A Expense Index", 1.00, "Operational overhead creep and administrative leverage"),
            "LVGI": ("Leverage Index", 1.00, "Debt-to-assets expansion and covenant default risks"),
            "TATA": ("Total Accruals to Total Assets", 0.00, "Net income vs Operating Cash Flow divergence"),
        }

        rows = []
        for code, (name, bench, imp) in metric_meta.items():
            item = indices.get(code, {})
            val = item.get("value", 1.00)
            flagged = item.get("flagged", False)
            flag_badge = "🚩 RED FLAG" if flagged else "✅ Normal"
            rows.append(f"| **{code}** | {name} | `{val:.3f}` | `{bench:.2f}` | {imp} | {flag_badge} |")

        table_body = "\n".join(rows)

        return f"""- **Calculated Beneish M-Score:** **`{m_score:.2f}`**
- **Classification:** {status_text}
- **Assessed Risk Level:** `{risk}`

#### Detailed 8-Variable Index Breakdown:
| Index | Metric Name | Calculated Value | Benchmark | Forensic Implication | Status |
|:---|:---|:---:|:---:|:---|:---:|
{table_body}
"""

    @classmethod
    def _render_footnotes_section(cls, findings: list[dict[str, Any]] | None) -> str:
        if not findings:
            return (
                "✅ *No critical buried accounting hazards or material weakness disclosures identified.*"
            )

        items = []
        for idx, f in enumerate(findings, 1):
            category = f.get("category", "HAZARD")
            title = f.get("title", "Accounting Hazard")
            sev = f.get("severity", "MEDIUM")
            quote = f.get("quote", "").strip()
            items.append(
                f"{idx}. **[{sev}] {title}** (`{category}`)\n"
                f"   > *\"{quote}\"*"
            )

        return "\n\n".join(items)

    @classmethod
    def _render_diff_section(cls, diff_result: dict[str, Any] | None) -> str:
        if not diff_result:
            return "_Filing diff comparison was not executed for this run._"

        drift_score = diff_result.get("overall_drift_score", 0.0)
        sev = diff_result.get("overall_severity", "LOW")
        forensic_summary = diff_result.get("forensic_summary", "")
        sections = diff_result.get("sections", {})

        sec_blocks = []
        for sec_name, sec_data in sections.items():
            sim = sec_data.get("similarity_ratio", 1.0)
            sec_drift = sec_data.get("drift_score", 0.0)
            added = sec_data.get("added_paragraphs", [])
            removed = sec_data.get("removed_paragraphs", [])

            block = (
                f"#### Section: `{sec_name}`\n"
                f"- **Similarity:** `{sim:.1%}` | **Drift Score:** `{sec_drift:.1f}%`\n"
            )
            if added:
                block += f"- **Newly Inserted Disclosures ({len(added)}):**\n"
                for p in added[:3]:
                    block += f"  - 🟢 *\"{p[:200]}...\"*\n"
            if removed:
                block += f"- **Removed Disclosures ({len(removed)}):**\n"
                for p in removed[:3]:
                    block += f"  - 🔴 *\"{p[:200]}...\"*\n"
            sec_blocks.append(block)

        sections_md = "\n".join(sec_blocks) if sec_blocks else "_No individual section deviations flagged._"

        return f"""- **Overall Filing Language Drift Score:** **`{drift_score:.1f}%`**
- **Stealth Alteration Severity:** `{sev}`
- **Executive Forensic Finding:** {forensic_summary or "Filing language showed standard annual updates."}

{sections_md}
"""

    @classmethod
    def _render_contradictions_section(cls, contradiction_result: dict[str, Any] | None) -> str:
        if not contradiction_result:
            return "_Earnings call vs regulatory filing contradiction analysis was not performed._"

        divergence = contradiction_result.get("tone_divergence_score", 0.0)
        call_sent = contradiction_result.get("call_sentiment", "NEUTRAL")
        filing_sent = contradiction_result.get("filing_sentiment", "NEUTRAL")
        sev = contradiction_result.get("divergence_severity", "LOW")
        contra_count = contradiction_result.get("contradictions_count", 0)
        items = contradiction_result.get("contradictions", [])

        contra_blocks = []
        for c in items:
            topic = c.get("topic", "GUIDANCE")
            c_sev = c.get("severity", "MEDIUM")
            call_stmt = c.get("call_statement", "")
            filing_stmt = c.get("filing_statement", "")
            analysis = c.get("divergence_analysis", "")

            contra_blocks.append(
                f"- **[{c_sev}] Topic: `{topic}`**\n"
                f"  - 🎙️ **Executive Call Claim:** *\"{call_stmt}\"*\n"
                f"  - 📄 **Audited Filing Reality:** *\"{filing_stmt}\"*\n"
                f"  - 🔍 **Divergence Analysis:** {analysis}\n"
            )

        items_md = "\n".join(contra_blocks) if contra_blocks else "✅ *No direct semantic contradictions detected.*"

        return f"""- **Tone Decoupling Divergence Score:** **`{divergence:.1f}%`**
- **Divergence Severity:** `{sev}`
- **Tone Spectrum:** Executive Remarks: `{call_sent}` vs Audited Disclosures: `{filing_sent}`
- **Flagged Contradictions:** `{contra_count}`

{items_md}
"""

    @classmethod
    def _render_checklist(cls, risk_level: str, p1_st: str, p2_st: str, p3_st: str) -> str:
        checks = []
        if risk_level in ("HIGH_RISK", "CRITICAL_ALERT") or p2_st == "CRITICAL":
            checks.append(
                "1. **Audit Committee Accruals Cross-Examination:** Request full reconciliations "
                "of unbilled receivables and verify revenue recognition milestones with external auditors."
            )
            checks.append(
                "2. **Cash Conversion Cycle Audit:** Scrutinize the growing gap between Operating Cash Flow "
                "and Reported Net Income."
            )
        else:
            checks.append(
                "1. **Routine Accrual Verification:** Confirm working capital metrics "
                "track historical seasonal averages."
            )

        if p1_st in ("ELEVATED", "CRITICAL"):
            checks.append(
                "3. **Silent Risk Disclosure Scrutiny:** Require management to explain unannounced "
                "clause deletions in Item 1A Risk Factors."
            )
        else:
            checks.append(
                "3. **Boilerplate Risk Review:** Maintain periodic tracking of standard annual risk factor updates."
            )

        if p3_st in ("ELEVATED", "CRITICAL"):
            checks.append(
                "4. **Guidance Reality Check:** Question CFO directly on divergences between oral conference "
                "call backlog optimism and 10-Q cancellation clauses."
            )
        else:
            checks.append(
                "4. **Transcript Monitoring:** Continue monitoring quarterly Q&A sentiment consistency."
            )

        return "\n".join(checks)
