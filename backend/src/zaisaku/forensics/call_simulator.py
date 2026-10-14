from __future__ import annotations

from pydantic import BaseModel, Field


class CallUtterance(BaseModel):
    id: str
    speaker: str
    speaker_role: str = Field(..., description="CEO | CFO | ANALYST")
    timestamp_seconds: float
    timestamp_label: str
    duration_seconds: float
    text: str
    sentiment_score: float = Field(..., description="Sentiment from -1.0 (bearish) to +1.0 (bullish)")
    is_discrepancy: bool = False
    discrepancy_explanation: str | None = None
    waveform_peaks: list[float] = Field(default_factory=list, description="Audio peak values 0.0-1.0")


class EarningsCallSession(BaseModel):
    ticker: str
    company_name: str
    quarter: str
    date: str
    total_duration_seconds: float
    overall_executive_sentiment: float
    utterances: list[CallUtterance]
    tone_summary: str


class CallSimulator:
    """Simulates multimodal earnings conference calls with synchronized speech waveforms and tone sentiment."""

    def __init__(self) -> None:
        pass

    def get_call_session(self, ticker: str) -> EarningsCallSession:
        t = ticker.upper().strip()

        if t == "NVDA":
            return self._build_nvda()
        elif t == "TSLA":
            return self._build_tsla()
        elif t in ("FRAUD", "RISK"):
            return self._build_fraud(t)
        else:
            return self._build_generic(t)

    def _build_nvda(self) -> EarningsCallSession:
        utterances = [
            CallUtterance(
                id="u1",
                speaker="Jensen Huang",
                speaker_role="CEO",
                timestamp_seconds=15.0,
                timestamp_label="00:15",
                duration_seconds=32.0,
                text=(
                    "Accelerated computing and generative AI have reached the tipping point. "
                    "Demand is surging worldwide across companies, industries and nations. "
                    "Our Data Center platform is powered by increasingly diverse drivers — "
                    "demand for data processing, training and inference from large cloud-service providers."
                ),
                sentiment_score=0.88,
                is_discrepancy=False,
                waveform_peaks=[0.2, 0.5, 0.8, 0.9, 0.7, 0.85, 0.6, 0.4, 0.75, 0.9, 0.65, 0.3],
            ),
            CallUtterance(
                id="u2",
                speaker="Colette Kress",
                speaker_role="CFO",
                timestamp_seconds=50.0,
                timestamp_label="00:50",
                duration_seconds=28.0,
                text=(
                    "Fourth quarter revenue was twenty-two point one billion dollars, "
                    "up twenty-two percent sequentially and up two hundred sixty-five percent from a year ago. "
                    "For fiscal twenty-twenty-four, total revenue grew one hundred twenty-six percent "
                    "to sixty point nine billion."
                ),
                sentiment_score=0.74,
                is_discrepancy=False,
                waveform_peaks=[0.3, 0.6, 0.7, 0.65, 0.8, 0.75, 0.7, 0.6, 0.55, 0.65, 0.4, 0.2],
            ),
            CallUtterance(
                id="u3",
                speaker="Timothy Arcuri",
                speaker_role="ANALYST",
                timestamp_seconds=82.0,
                timestamp_label="01:22",
                duration_seconds=20.0,
                text=(
                    "Jensen, can you talk about the transition from Hopper to Blackwell? "
                    "Are you seeing any customers pausing or deferring purchases in Q2 or Q3 ahead of the B200 ramp?"
                ),
                sentiment_score=0.05,
                is_discrepancy=False,
                waveform_peaks=[0.2, 0.4, 0.5, 0.6, 0.45, 0.55, 0.4, 0.3, 0.35, 0.4, 0.25, 0.1],
            ),
            CallUtterance(
                id="u4",
                speaker="Jensen Huang",
                speaker_role="CEO",
                timestamp_seconds=105.0,
                timestamp_label="01:45",
                duration_seconds=35.0,
                text=(
                    "The demand for Hopper remains exceptionally strong. "
                    "Whenever we introduce new products, it ramps from zero to a very large number. "
                    "Blackwell allocation is already constrained into next year, and Hopper supply is improving "
                    "so we can satisfy current enterprise pipelines."
                ),
                sentiment_score=0.82,
                is_discrepancy=True,
                discrepancy_explanation=(
                    "CEO remarks emphasize boundless demand with no transition pauses, whereas Form 10-K Item 1A "
                    "discloses risks of quarterly volatility and inventory commitments during architecture "
                    "generational shifts."
                ),
                waveform_peaks=[0.4, 0.7, 0.85, 0.95, 0.8, 0.9, 0.75, 0.85, 0.6, 0.7, 0.5, 0.3],
            ),
        ]

        return EarningsCallSession(
            ticker="NVDA",
            company_name="NVIDIA Corporation",
            quarter="Q4 FY2024 Earnings Conference Call",
            date="February 21, 2024",
            total_duration_seconds=145.0,
            overall_executive_sentiment=0.81,
            utterances=utterances,
            tone_summary=(
                "Highly confident and bullish executive tone. CEO sentiment (+0.82) reflects unprecedented "
                "hyperscaler demand. One minor hedging discrepancy flagged on product transition timing."
            ),
        )

    def _build_tsla(self) -> EarningsCallSession:
        utterances = [
            CallUtterance(
                id="u1",
                speaker="Elon Musk",
                speaker_role="CEO",
                timestamp_seconds=10.0,
                timestamp_label="00:10",
                duration_seconds=30.0,
                text=(
                    "We are between two major growth waves. The first wave was driven by the global expansion of "
                    "the Model 3 and Y platform. The next wave will be initiated by the next-generation vehicle "
                    "architecture and full autonomous robotaxi deployment."
                ),
                sentiment_score=0.42,
                is_discrepancy=False,
                waveform_peaks=[0.3, 0.5, 0.6, 0.55, 0.65, 0.5, 0.4, 0.45, 0.35, 0.4, 0.3, 0.2],
            ),
            CallUtterance(
                id="u2",
                speaker="Vaibhav Taneja",
                speaker_role="CFO",
                timestamp_seconds=42.0,
                timestamp_label="00:42",
                duration_seconds=25.0,
                text=(
                    "Auto gross margin excluding regulatory credits was seventeen point two percent. "
                    "We continue to focus on cost reductions across our supply chain and factory footprint."
                ),
                sentiment_score=-0.12,
                is_discrepancy=True,
                discrepancy_explanation=(
                    "CFO acknowledges margin compression while CEO remarks forecast imminent hyper-growth."
                ),
                waveform_peaks=[0.2, 0.4, 0.45, 0.5, 0.4, 0.35, 0.3, 0.25, 0.3, 0.25, 0.2, 0.1],
            ),
        ]

        return EarningsCallSession(
            ticker="TSLA",
            company_name="Tesla Inc.",
            quarter="Q4 FY2023 Earnings Call",
            date="January 24, 2024",
            total_duration_seconds=70.0,
            overall_executive_sentiment=0.15,
            utterances=utterances,
            tone_summary="Cautious tone marked by divergence between CEO long-term AI vision and CFO margin headwinds.",
        )

    def _build_fraud(self, ticker: str) -> EarningsCallSession:
        utterances = [
            CallUtterance(
                id="u1",
                speaker="Executive CEO",
                speaker_role="CEO",
                timestamp_seconds=10.0,
                timestamp_label="00:10",
                duration_seconds=30.0,
                text="We are accelerating faster than any competitor in our sector. Backlog is at an all-time record.",
                sentiment_score=0.92,
                is_discrepancy=True,
                discrepancy_explanation=(
                    "CRITICAL CONTRADICTION: Executive claims record backlog and acceleration, while 10-Q MD&A "
                    "reports negative cash flows and customers requesting contract deferrals."
                ),
                waveform_peaks=[0.5, 0.8, 0.95, 0.9, 0.85, 0.8, 0.7, 0.6, 0.75, 0.8, 0.6, 0.3],
            )
        ]
        return EarningsCallSession(
            ticker=ticker,
            company_name=f"{ticker} Technologies",
            quarter="FY2024 Earnings Call",
            date="October 2026",
            total_duration_seconds=45.0,
            overall_executive_sentiment=0.92,
            utterances=utterances,
            tone_summary="Severe contradiction between executive spoken optimism and audited financial deterioration.",
        )

    def _build_generic(self, ticker: str) -> EarningsCallSession:
        utterances = [
            CallUtterance(
                id="u1",
                speaker=f"{ticker} Chief Executive",
                speaker_role="CEO",
                timestamp_seconds=15.0,
                timestamp_label="00:15",
                duration_seconds=30.0,
                text=(
                    f"Welcome to the quarterly update for {ticker}. Our operational execution remained steady "
                    "across enterprise business units with solid cash generation."
                ),
                sentiment_score=0.55,
                is_discrepancy=False,
                waveform_peaks=[0.3, 0.5, 0.65, 0.6, 0.55, 0.5, 0.4, 0.45, 0.35, 0.4, 0.3, 0.2],
            )
        ]
        return EarningsCallSession(
            ticker=ticker,
            company_name=f"{ticker} Corporation",
            quarter="Quarterly Financial Update",
            date="Recent Quarter",
            total_duration_seconds=50.0,
            overall_executive_sentiment=0.55,
            utterances=utterances,
            tone_summary="Disciplined executive guidance aligning with standard regulatory filings.",
        )
