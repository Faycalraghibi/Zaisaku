"""Contradiction Radar: Detects discrepancies between spoken earnings calls and written SEC 10-Q filings."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from zaisaku.generation.llm import LLMRouter


class ContradictionTopic(StrEnum):
    DEMAND_GUIDANCE = "demand_and_guidance"
    MARGINS_PRICING = "margins_and_pricing"
    SUPPLY_CHAIN_OPS = "supply_chain_operations"
    CUSTOMER_RETENTION = "customer_retention"
    REGULATORY_LEGAL = "regulatory_and_litigation"


class ContradictionSeverity(StrEnum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MODERATE = "MODERATE"


@dataclass
class ContradictionItem:
    topic: str
    severity: str  # CRITICAL, HIGH, MODERATE
    call_statement: str
    filing_statement: str
    divergence_analysis: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ContradictionRadarResult:
    ticker: str
    tone_divergence_score: float  # 0.0 to 100.0%
    call_sentiment: str  # BULLISH, NEUTRAL, CAUTIOUS
    filing_sentiment: str  # CAUTIOUS, BEARISH, NEUTRAL
    divergence_severity: str  # LOW, MODERATE, HIGH, CRITICAL
    contradictions_count: int
    contradictions: list[ContradictionItem] = field(default_factory=list)
    executive_summary: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


class ContradictionRadar:
    """Analyzes tone decoupling and extracts semantic contradictions between earnings calls and 10-Q filings."""

    BULLISH_CUES = [
        r"\brobust\b",
        r"\bunprecedented\b",
        r"\baccelerating\b",
        r"\btailwinds?\b",
        r"\bstrong\s+demand\b",
        r"\bconfident\b",
        r"\bpricing\s+power\b",
        r"\bexpanding\s+margins?\b",
        r"\bhealthy\s+pipeline\b",
        r"\brecord\b",
        r"\boptimistic\b",
        r"\bbacklog\s+(?:growth|expansion|strength)\b",
    ]

    CAUTIOUS_CUES = [
        r"\bheadwinds?\b",
        r"\bsoftness\b",
        r"\bdeceleration\b",
        r"\bpressures?\b",
        r"\buncertaint(?:y|ies)\b",
        r"\bmacro\s+environment\b",
        r"\blengthening\s+sales\s+cycles?\b",
        r"\bscrutiny\b",
    ]

    RISK_FILING_CUES = [
        r"\bmaterial\s+adverse\s+effects?\b",
        r"\bcannot\s+assure\b",
        r"\bmargin\s+compression\b",
        r"\bdecreased?\b",
        r"\bimpairments?\b",
        r"\bvolatilit(?:y|ies)\b",
        r"\bcancellations?\b",
        r"\bpushouts?\b",
        r"\bconcessions?\b",
        r"\bdelays?\b",
        r"\bdeteriorat(?:e|ion)\b",
        r"\bshortages?\b",
    ]

    TOPIC_RULES = [
        {
            "topic": ContradictionTopic.DEMAND_GUIDANCE.value,
            "title": "Demand & Backlog Visibility",
            "severity": ContradictionSeverity.CRITICAL.value,
            "call_patterns": [
                r"\b(?:record|strong|robust|accelerating|expanding)\s+(?:demand|backlog|pipeline|orders?)\b",
                r"\bdemand\s+(?:has\s+never\s+been\s+stronger|remains\s+resilient|exceeds\s+supply)\b",
                r"\bvisibility\s+(?:into\s+our\s+pipeline\s+is\s+strong|remains\s+excellent)\b",
            ],
            "filing_patterns": [
                r"\b(?:reduced|limited|lowered|impaired)\s+(?:order\s+)?visibility\b",
                r"\border\s+(?:cancellations?|delays?|pushouts?)\b",
                r"\bdecline\s+in\s+customer\s+(?:demand|orders?|spending)\b",
                r"\blengthening\s+sales\s+cycles?\b",
                r"\bcustomers?\s+(?:delaying|deferring|reducing)\s+(?:purchases?|commitments?)\b",
            ],
            "divergence_analysis": (
                "Management painted a picture of resilient, accelerating demand on the conference call, "
                "yet the regulatory 10-Q disclosed customer pushouts, cancellations, and order deterioration."
            ),
        },
        {
            "topic": ContradictionTopic.MARGINS_PRICING.value,
            "title": "Gross Margins & Pricing Power",
            "severity": ContradictionSeverity.HIGH.value,
            "call_patterns": [
                r"\bpricing\s+power\s+(?:is\s+intact|remains\s+strong)\b",
                r"\b(?:expanding|stable|healthy)\s+gross\s+margins?\b",
                r"\bdisciplined\s+pricing\b",
            ],
            "filing_patterns": [
                r"\bgross\s+margins?\s+(?:compressed|decreased|declined)\b",
                r"\bpricing\s+(?:concessions?|pressures?|discounts?)\b",
                r"\bunfavorable\s+product\s+mix\b",
                r"\bcost\s+inflation\s+(?:eroding|reducing)\s+profitabilit(?:y|ies)\b",
            ],
            "divergence_analysis": (
                "Spoken remarks claimed firm pricing power and stable margins, while the official 10-Q filing "
                "acknowledged customer price concessions, discounting pressure, and gross margin compression."
            ),
        },
        {
            "topic": ContradictionTopic.SUPPLY_CHAIN_OPS.value,
            "title": "Supply Chain & Manufacturing Bottlenecks",
            "severity": ContradictionSeverity.HIGH.value,
            "call_patterns": [
                r"\bsupply\s+chain\s+(?:bottlenecks?\s+(?:are\s+)?(?:easing|normalizing|resolved|fully\s+resolved)|normalizing|fully\s+resolved)\b",
                r"\bfoundry\s+allocations?\s+(?:have\s+)?(?:normalized|sufficient)\b",
                r"\binventory\s+(?:levels?\s+are\s+balanced|optimized)\b",
            ],
            "filing_patterns": [
                r"\bsupply\s+chain\s+(?:disruptions?|constraints?|bottlenecks?)\b",
                r"\bcomponent\s+shortages?\b",
                r"\bsole[- ]source\s+suppliers?\b",
                r"\bexcess\s+inventory\s+write[- ]downs?\b",
            ],
            "divergence_analysis": (
                "Executives assured analysts that supply disruptions were largely resolved, but the 10-Q explicitly "
                "warned of persistent component shortages, sole-supplier exposure, and inventory write-downs."
            ),
        },
        {
            "topic": ContradictionTopic.CUSTOMER_RETENTION.value,
            "title": "Customer Concentration & Retention",
            "severity": ContradictionSeverity.HIGH.value,
            "call_patterns": [
                r"\bnet\s+retention\s+(?:is\s+at\s+record\s+highs?|accelerated)\b",
                r"\bno\s+notable\s+customer\s+(?:losses?|churn)\b",
                r"\bexpanding\s+our\s+customer\s+base\b",
            ],
            "filing_patterns": [
                r"\bloss\s+of\s+(?:a\s+)?(?:major|significant|key)\s+customer\b",
                r"\belevated\s+customer\s+churn\b",
                r"\bcustomer\s+consolidation\s+(?:adversely\s+affecting|reducing)\b",
            ],
            "divergence_analysis": (
                "Management boasted of record retention on the call, while the regulatory filing disclosed the "
                "defection or consolidation of significant revenue-generating customers."
            ),
        },
        {
            "topic": ContradictionTopic.REGULATORY_LEGAL.value,
            "title": "Regulatory Investigations & Litigation Exposure",
            "severity": ContradictionSeverity.CRITICAL.value,
            "call_patterns": [
                r"\broutine\s+regulatory\s+(?:inquir(?:y|ies)|matters?)\b",
                r"\bconfident\s+in\s+our\s+legal\s+position\b",
                r"\bno\s+material\s+litigation\s+impact\b",
            ],
            "filing_patterns": [
                r"\bformal\s+investigation\s+by\s+the\s+(?:SEC|DOJ|FTC)\b",
                r"\bsubpoenas?\s+received\b",
                r"\bmaterial\s+unaccrued\s+contingenc(?:y|ies)\b",
                r"\bclass\s+action\s+lawsuit\b",
            ],
            "divergence_analysis": (
                "Executive remarks dismissed legal inquiries as routine administrative matters, but the 10-Q disclosed "
                "formal government subpoenas and potential material liabilities under active investigation."
            ),
        },
    ]

    @classmethod
    def calculate_sentiment_score(cls, text: str, is_call: bool = True) -> float:
        """Calculates a normalized tone score between -1.0 (deeply cautious/bearish) and +1.0 (hyper-bullish)."""
        if not text:
            return 0.0

        pos_count = sum(len(re.findall(p, text, re.IGNORECASE)) for p in cls.BULLISH_CUES)
        neg_cues = cls.CAUTIOUS_CUES if is_call else cls.RISK_FILING_CUES
        neg_count = sum(len(re.findall(p, text, re.IGNORECASE)) for p in neg_cues)

        total = pos_count + neg_count
        if total == 0:
            return 0.0
        return round((pos_count - neg_count) / total, 3)

    @classmethod
    def _extract_snippet(cls, text: str, pattern: str) -> str:
        """Extracts context surrounding a pattern match."""
        m = re.search(pattern, text, re.IGNORECASE)
        if not m:
            return ""
        start = max(0, m.start() - 100)
        end = min(len(text), m.end() + 120)
        snippet = text[start:end].strip()
        if start > 0:
            snippet = "..." + snippet
        if end < len(text):
            snippet = snippet + "..."
        return snippet

    @classmethod
    def detect_contradictions_deterministic(
        cls,
        call_text: str,
        filing_text: str,
    ) -> list[ContradictionItem]:
        items: list[ContradictionItem] = []

        for rule in cls.TOPIC_RULES:
            call_match_pat = None
            for p in rule["call_patterns"]:
                if re.search(p, call_text, re.IGNORECASE):
                    call_match_pat = p
                    break

            filing_match_pat = None
            for p in rule["filing_patterns"]:
                if re.search(p, filing_text, re.IGNORECASE):
                    filing_match_pat = p
                    break

            if call_match_pat and filing_match_pat:
                call_quote = cls._extract_snippet(call_text, call_match_pat)
                filing_quote = cls._extract_snippet(filing_text, filing_match_pat)

                items.append(
                    ContradictionItem(
                        topic=rule["title"],
                        severity=rule["severity"],
                        call_statement=call_quote,
                        filing_statement=filing_quote,
                        divergence_analysis=rule["divergence_analysis"],
                    )
                )

        return items

    @classmethod
    def analyze(
        cls,
        ticker: str,
        call_text: str,
        filing_text: str,
        llm: LLMRouter | None = None,
    ) -> ContradictionRadarResult:
        ticker = ticker.strip().upper() or "CUSTOM"
        call_score = cls.calculate_sentiment_score(call_text, is_call=True)
        filing_score = cls.calculate_sentiment_score(filing_text, is_call=False)

        # Tone divergence formula: difference between optimistic call and guarded filing
        divergence_delta = abs(call_score - filing_score) / 2.0  # normalized 0.0 to 1.0
        divergence_pct = round(divergence_delta * 100.0, 1)

        call_sent = "BULLISH" if call_score > 0.2 else ("CAUTIOUS" if call_score < -0.2 else "NEUTRAL")
        filing_sent = "BEARISH" if filing_score < -0.4 else ("CAUTIOUS" if filing_score < -0.1 else "NEUTRAL")

        if divergence_pct >= 50.0:
            severity = "CRITICAL"
        elif divergence_pct >= 30.0:
            severity = "HIGH"
        elif divergence_pct >= 15.0:
            severity = "MODERATE"
        else:
            severity = "LOW"

        contradictions = cls.detect_contradictions_deterministic(call_text, filing_text)

        # If LLM is provided and no or few contradictions found, run an LLM semantic extraction
        if llm and len(contradictions) == 0:
            try:
                system_prompt = (
                    "You are an expert financial forensic analyst. Compare the spoken earnings call transcript against "
                    "the official SEC 10-Q filing. Identify direct contradictions where management made optimistic or "
                    "reassuring claims on the call while the 10-Q revealed conflicting negative disclosures or risks.\n"
                    "Output valid JSON array of objects: [{\"topic\": \"...\", \"severity\": \"HIGH|CRITICAL\", "
                    "\"call_statement\": \"...\", \"filing_statement\": \"...\", \"divergence_analysis\": \"...\"}]"
                )
                user_msg = (
                    f"Ticker: {ticker}\n\n"
                    f"--- EARNINGS CALL TRANSCRIPT EXCERPT ---\n{call_text[:2000]}\n\n"
                    f"--- SEC 10-Q FILING EXCERPT ---\n{filing_text[:2000]}"
                )
                raw_resp = llm.generate(prompt=user_msg, system_prompt=system_prompt)
                raw_text = raw_resp.get("text", "") if isinstance(raw_resp, dict) else str(raw_resp)
                # Attempt to parse json
                json_match = re.search(r"\[\s*\{.*\}\s*\]", raw_text, re.DOTALL)
                if json_match:
                    parsed = json.loads(json_match.group(0))
                    for item in parsed:
                        contradictions.append(
                            ContradictionItem(
                                topic=item.get("topic", "Guidance & Execution"),
                                severity=item.get("severity", "HIGH"),
                                call_statement=item.get("call_statement", ""),
                                filing_statement=item.get("filing_statement", ""),
                                divergence_analysis=item.get("divergence_analysis", ""),
                            )
                        )
            except Exception:
                pass  # Fall back gracefully to deterministic analysis

        if len(contradictions) > 0:
            summary = (
                f"Contradiction Radar identified {len(contradictions)} high-conviction divergence(s) "
                f"between {ticker}'s spoken remarks and 10-Q disclosures, accompanied by a {divergence_pct}% "
                "tone decoupling."
            )
        else:
            summary = (
                f"{ticker}'s spoken remarks and regulatory filings exhibit aligned sentiment with no direct "
                f"guidance or operational contradictions identified."
            )

        return ContradictionRadarResult(
            ticker=ticker,
            tone_divergence_score=divergence_pct,
            call_sentiment=call_sent,
            filing_sentiment=filing_sent,
            divergence_severity=severity,
            contradictions_count=len(contradictions),
            contradictions=contradictions,
            executive_summary=summary,
        )
