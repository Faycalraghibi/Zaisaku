"""Footnote risk scanner for detecting hidden financial red flags in SEC filings and notes."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from enum import StrEnum


class FootnoteRiskCategory(StrEnum):
    RELATED_PARTY = "related_party"
    CUSTOMER_CONCENTRATION = "customer_concentration"
    HTM_UNREALIZED_LOSSES = "htm_unrealized_losses"
    GOODWILL_IMPAIRMENT = "goodwill_impairment"
    AUDITOR_MATERIAL_WEAKNESS = "auditor_material_weakness"


@dataclass
class FootnoteFinding:
    category: str
    title: str
    severity: str  # HIGH, MEDIUM, LOW
    matched_phrase: str
    excerpt: str
    explanation: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class FootnoteScanResult:
    total_findings: int
    high_risk_count: int
    medium_risk_count: int
    findings: list[FootnoteFinding] = field(default_factory=list)
    summary: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


class FootnoteScanner:
    """Detects critical accounting hazards and buried footnote disclosures in financial documents."""

    RULE_SETS = [
        {
            "category": FootnoteRiskCategory.RELATED_PARTY.value,
            "title": "Related-Party Transactions & Insider Dealings",
            "severity": "HIGH",
            "patterns": [
                r"\brelated[- ]party\s+(?:transactions?|agreements?|leases?|loans?|notes?|borrowings?|entities)\b",
                r"\bloans?\s+to\s+(?:executives?|officers?|directors?|insiders?|affiliates?)\b",
                r"\bconsulting\s+(?:agreements?|fees?)\s+with\s+(?:directors?|affiliates?|former\s+officers?)\b",
                r"\bvariable\s+interest\s+entit(?:y|ies)\b",
                r"\boff[- ]balance[- ]sheet\s+(?:arrangements?|entities|obligations?)\b",
            ],
            "explanation": (
                "Related-party transactions and off-balance sheet entities obscure true economic transfer of value "
                "and have historically served as conduits for aggressive earnings management."
            ),
        },
        {
            "category": FootnoteRiskCategory.CUSTOMER_CONCENTRATION.value,
            "title": "Severe Customer Revenue Concentration",
            "severity": "HIGH",
            "patterns": [
                r"(?:accounted\s+for|represented|generated)\s+(?:approximately\s+)?(?:\d{1,2}(?:\.\d+)?%|(?:ten|fifteen|twenty|twenty-five|thirty|forty|fifty)\s+percent)\s+of\s+(?:our\s+)?(?:total\s+)?(?:consolidated\s+)?(?:net\s+)?(?:revenue|sales)",
                r"(?:single|major|significant|one|two|three)\s+customers?\s+(?:account(?:ed)?\s+for|represent(?:ed)?)\s+(?:more\s+than|\d{1,2}%|ten\s+percent)",
                r"\bconcentration\s+of\s+credit\s+risk\b",
                r"\bcustomers?\s+represented\s+greater\s+than\s+10\s*%\b",
            ],
            "explanation": (
                "Heavy dependency on a single customer (>10% revenue) creates catastrophic revenue fragility "
                "should the customer terminate contracts, delay payments, or demand severe pricing concessions."
            ),
        },
        {
            "category": FootnoteRiskCategory.HTM_UNREALIZED_LOSSES.value,
            "title": "Held-to-Maturity (HTM) Unrealized Losses / AOCI Deficit",
            "severity": "HIGH",
            "patterns": [
                r"\bheld[- ]to[- ]maturity\b[^\.\n]{0,80}\b(?:unrealized\s+loss(?:es)?|fair\s+value\s+less\s+than)\b",
                r"\bunrealized\s+loss(?:es)?\s+on\s+(?:held[- ]to[- ]maturity|available[- ]for[- ]sale|investments?)\b",
                r"\baccumulated\s+other\s+comprehensive\s+(?:loss|loss\s+of|income\s+\(loss\))\b",
                r"\bgross\s+unrealized\s+loss(?:es)?\b",
                r"\bsecurities\s+held[- ]to[- ]maturity[^\.\n]{0,60}\bfair\s+value\b",
            ],
            "explanation": (
                "Unrealized losses buried in Held-to-Maturity portfolios or AOCI are not marked to market on income, "
                "masking substantial economic capital depletion (the catalyst behind Silicon Valley Bank's collapse)."
            ),
        },
        {
            "category": FootnoteRiskCategory.GOODWILL_IMPAIRMENT.value,
            "title": "Goodwill Impairment & Valuation Fragility",
            "severity": "MEDIUM",
            "patterns": [
                r"\bgoodwill\s+impairment\s+(?:charge|charges|test|testing|loss|losses|risk)\b",
                r"(?:carrying\s+value|carrying\s+amount)\s+of\s+goodwill\s+exceeded\s+(?:its\s+)?implied\s+fair\s+value",
                r"\breporting\s+units?\s+(?:at\s+risk\s+of\s+impairment|fair\s+value\s+approximated\s+carrying\s+value)\b",
                r"\bquantitative\s+goodwill\s+impairment\b",
                r"\baccumulated\s+impairment\s+losses?\b",
            ],
            "explanation": (
                "Goodwill carrying values heavily rely on optimistic management discount rates and growth forecasts. "
                "Impairment signals past overpriced acquisitions and write-downs directly eroding shareholder equity."
            ),
        },
        {
            "category": FootnoteRiskCategory.AUDITOR_MATERIAL_WEAKNESS.value,
            "title": "Auditor Friction & Internal Control Material Weaknesses",
            "severity": "HIGH",
            "patterns": [
                r"\bmaterial\s+weakness(?:es)?\s+in\s+internal\s+control\s+over\s+financial\s+reporting\b",
                r"\binternal\s+controls?\s+(?:were|was)\s+not\s+effective\b",
                r"(?:dismissed|resigned|replaced)\s+as\s+(?:the\s+)?independent\s+registered\s+public\s+accounting\s+firm",
                r"\bdisagreements?\s+with\s+(?:former\s+)?(?:accountants?|auditors?)\b",
                r"\bgoing\s+concern\s+uncertaint(?:y|ies)\b",
                r"\bexplanatory\s+paragraph\s+(?:regarding|relating\s+to)\s+going\s+concern\b",
            ],
            "explanation": (
                "Material weaknesses under SOX Section 404 or mid-cycle auditor resignation indicate defective "
                "financial controls, greatly elevating the likelihood of retroactive earnings restatements or fraud."
            ),
        },
    ]

    @classmethod
    def scan(cls, text: str) -> FootnoteScanResult:
        if not text or not text.strip():
            return FootnoteScanResult(
                total_findings=0,
                high_risk_count=0,
                medium_risk_count=0,
                findings=[],
                summary="No text provided for forensic footnote scanning.",
            )

        findings: list[FootnoteFinding] = []
        seen_snippets: set[str] = set()

        # Split text into paragraphs and sentences
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]

        for p_idx, para in enumerate(paragraphs):
            for rule in cls.RULE_SETS:
                for pat in rule["patterns"]:
                    match = re.search(pat, para, re.IGNORECASE)
                    if match:
                        matched_str = match.group(0)
                        start_pos = match.start()
                        end_pos = match.end()

                        # Extract surrounding sentence or context
                        left_bound = max(0, start_pos - 120)
                        right_bound = min(len(para), end_pos + 150)
                        excerpt = para[left_bound:right_bound].strip()
                        if left_bound > 0:
                            excerpt = "..." + excerpt
                        if right_bound < len(para):
                            excerpt = excerpt + "..."

                        # Prevent duplicate findings within same paragraph and category
                        snippet_key = f"{rule['category']}_{p_idx}_{matched_str.lower()}"
                        if snippet_key in seen_snippets:
                            continue
                        seen_snippets.add(snippet_key)

                        findings.append(
                            FootnoteFinding(
                                category=rule["category"],
                                title=rule["title"],
                                severity=rule["severity"],
                                matched_phrase=matched_str,
                                excerpt=excerpt,
                                explanation=rule["explanation"],
                            )
                        )
                        break  # Found match for this rule in this paragraph, move to next rule

        high_count = sum(1 for f in findings if f.severity == "HIGH")
        med_count = sum(1 for f in findings if f.severity == "MEDIUM")

        if high_count > 0:
            summary = (
                f"Forensic scan identified {len(findings)} footnote risk disclosure(s), "
                f"including {high_count} HIGH-SEVERITY red flags requiring immediate scrutiny."
            )
        elif med_count > 0:
            summary = (
                f"Forensic scan identified {len(findings)} moderate footnote risk disclosure(s) "
                "warranting accounting review."
            )
        else:
            summary = "No critical footnote hazards or accounting landmines detected in the provided text."

        return FootnoteScanResult(
            total_findings=len(findings),
            high_risk_count=high_count,
            medium_risk_count=med_count,
            findings=findings,
            summary=summary,
        )
