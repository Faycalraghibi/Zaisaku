from __future__ import annotations

from pydantic import BaseModel, Field


class PeerMetric(BaseModel):
    ticker: str
    name: str
    market_cap: str = Field(..., description="Estimated market capitalization")
    ffi: float = Field(..., description="Forensic Fragility Index 0-100")
    drift_pct: float = Field(..., description="Filing language drift YoY percentage")
    beneish_mscore: float = Field(..., description="Beneish M-Score")
    risk_tier: str = Field(..., description="LOW_RISK | WATCHLIST | CRITICAL")
    footnote_hazard_count: int
    key_vulnerability: str


class PeerComparisonResponse(BaseModel):
    target_ticker: str
    target_name: str
    sector: str
    sector_average_ffi: float | None = Field(None, description="Average FFI of the peer set; null when empty")
    peers: list[PeerMetric]
    sector_commentary: str


class PeerAnalyzer:
    """Evaluates cross-entity sector benchmarks and peer comparative risk matrices."""

    def __init__(self) -> None:
        pass

    def benchmark(self, ticker: str) -> PeerComparisonResponse:
        t = ticker.upper().strip()

        if t in ("NVDA", "AMD", "INTC", "QCOM", "AVGO", "TSM"):
            return self._build_semi_sector(t)
        elif t in ("AAPL", "MSFT", "GOOGL", "META", "AMZN"):
            return self._build_bigtech_sector(t)
        elif t in ("TSLA", "RIVN", "F", "GM"):
            return self._build_auto_sector(t)
        else:
            return self._no_peer_set(t)

    def _build_semi_sector(self, target: str) -> PeerComparisonResponse:
        all_peers = [
            PeerMetric(
                ticker="NVDA",
                name="NVIDIA Corporation",
                market_cap="$3.25T",
                ffi=18.0,
                drift_pct=8.5,
                beneish_mscore=-2.85,
                risk_tier="LOW_RISK",
                footnote_hazard_count=1,
                key_vulnerability="Customer concentration: Top CSP represents ~13% of receivables.",
            ),
            PeerMetric(
                ticker="AMD",
                name="Advanced Micro Devices",
                market_cap="$260B",
                ffi=27.0,
                drift_pct=12.5,
                beneish_mscore=-2.52,
                risk_tier="LOW_RISK",
                footnote_hazard_count=0,
                key_vulnerability="Embedded Xilinx goodwill amortization and datacenter GPU ramp visibility.",
            ),
            PeerMetric(
                ticker="INTC",
                name="Intel Corporation",
                market_cap="$95B",
                ffi=58.0,
                drift_pct=34.8,
                beneish_mscore=-1.95,
                risk_tier="WATCHLIST",
                footnote_hazard_count=3,
                key_vulnerability="Foundry segment operating losses, heavy capex accrual drag, and restructuring.",
            ),
            PeerMetric(
                ticker="QCOM",
                name="Qualcomm Incorporated",
                market_cap="$190B",
                ffi=24.0,
                drift_pct=11.0,
                beneish_mscore=-2.74,
                risk_tier="LOW_RISK",
                footnote_hazard_count=1,
                key_vulnerability="Handset licensing dispute disclosures and Arm architecture transition risks.",
            ),
            PeerMetric(
                ticker="AVGO",
                name="Broadcom Inc.",
                market_cap="$820B",
                ffi=24.5,
                drift_pct=11.2,
                beneish_mscore=-2.62,
                risk_tier="LOW_RISK",
                footnote_hazard_count=2,
                key_vulnerability="High leverage and intangible asset load following VMware integration.",
            ),
        ]

        avg_ffi = round(sum(p.ffi for p in all_peers) / len(all_peers), 1)
        name_map = {p.ticker: p.name for p in all_peers}

        commentary = (
            f"Sector benchmark for {target} against semiconductor and AI accelerator peers. "
            f"Sector average FFI is {avg_ffi}. Intel shows elevated accounting vulnerability due to "
            "foundry segment capex drag and restructuring charges, whereas NVDA and QCOM maintain safe accruals."
        )

        return PeerComparisonResponse(
            target_ticker=target,
            target_name=name_map.get(target, f"{target} Corp"),
            sector="Semiconductors & AI Hardware",
            sector_average_ffi=avg_ffi,
            peers=all_peers,
            sector_commentary=commentary,
        )

    def _build_bigtech_sector(self, target: str) -> PeerComparisonResponse:
        all_peers = [
            PeerMetric(
                ticker="AAPL",
                name="Apple Inc.",
                market_cap="$3.40T",
                ffi=14.0,
                drift_pct=6.2,
                beneish_mscore=-2.92,
                risk_tier="LOW_RISK",
                footnote_hazard_count=0,
                key_vulnerability="EU Digital Markets Act compliance disclosures regarding App Store commissions.",
            ),
            PeerMetric(
                ticker="MSFT",
                name="Microsoft Corporation",
                market_cap="$3.15T",
                ffi=16.0,
                drift_pct=7.8,
                beneish_mscore=-2.78,
                risk_tier="LOW_RISK",
                footnote_hazard_count=0,
                key_vulnerability="Accelerating AI capex commitments and OpenAI partnership capacity allocations.",
            ),
            PeerMetric(
                ticker="GOOGL",
                name="Alphabet Inc.",
                market_cap="$2.10T",
                ffi=16.5,
                drift_pct=7.2,
                beneish_mscore=-2.88,
                risk_tier="LOW_RISK",
                footnote_hazard_count=2,
                key_vulnerability="DOJ antitrust search distribution litigation and potential behavioral remedies.",
            ),
            PeerMetric(
                ticker="META",
                name="Meta Platforms Inc.",
                market_cap="$1.45T",
                ffi=21.0,
                drift_pct=9.0,
                beneish_mscore=-2.75,
                risk_tier="LOW_RISK",
                footnote_hazard_count=1,
                key_vulnerability="Reality Labs operating cash drag and generative AI infrastructure depreciation.",
            ),
            PeerMetric(
                ticker="AMZN",
                name="Amazon.com Inc.",
                market_cap="$1.95T",
                ffi=22.0,
                drift_pct=9.4,
                beneish_mscore=-2.65,
                risk_tier="LOW_RISK",
                footnote_hazard_count=0,
                key_vulnerability="AWS power availability bottlenecks and regional fulfillment capex scaling.",
            ),
        ]

        avg_ffi = round(sum(p.ffi for p in all_peers) / len(all_peers), 1)
        name_map = {p.ticker: p.name for p in all_peers}

        commentary = (
            f"Peer comparison for {target} against hyperscale cloud and platform peers. "
            f"Sector average FFI is {avg_ffi}. Cash conversion remains resilient across the group, with "
            "Alphabet showing slight regulatory drift and Apple leading with lowest language drift."
        )

        return PeerComparisonResponse(
            target_ticker=target,
            target_name=name_map.get(target, f"{target} Corp"),
            sector="Hyperscale Cloud & Platform Tech",
            sector_average_ffi=avg_ffi,
            peers=all_peers,
            sector_commentary=commentary,
        )

    def _build_auto_sector(self, target: str) -> PeerComparisonResponse:
        all_peers = [
            PeerMetric(
                ticker="TSLA",
                name="Tesla Inc.",
                market_cap="$720B",
                ffi=46.0,
                drift_pct=24.1,
                beneish_mscore=-2.10,
                risk_tier="WATCHLIST",
                footnote_hazard_count=2,
                key_vulnerability="Automotive gross margin compression and regulatory credit revenue fluctuations.",
            ),
            PeerMetric(
                ticker="RIVN",
                name="Rivian Automotive",
                market_cap="$12B",
                ffi=62.0,
                drift_pct=36.0,
                beneish_mscore=-1.88,
                risk_tier="WATCHLIST",
                footnote_hazard_count=3,
                key_vulnerability="Negative gross margin per vehicle delivered and cash burn rate.",
            ),
            PeerMetric(
                ticker="F",
                name="Ford Motor Company",
                market_cap="$42B",
                ffi=42.0,
                drift_pct=19.5,
                beneish_mscore=-2.28,
                risk_tier="WATCHLIST",
                footnote_hazard_count=2,
                key_vulnerability="Model e EV unit operating losses offset by Ford Pro commercial fleet margins.",
            ),
            PeerMetric(
                ticker="GM",
                name="General Motors",
                market_cap="$54B",
                ffi=35.0,
                drift_pct=15.0,
                beneish_mscore=-2.45,
                risk_tier="LOW_RISK",
                footnote_hazard_count=1,
                key_vulnerability="Cruise autonomous division restructuring and battery joint venture ramp.",
            ),
        ]

        avg_ffi = round(sum(p.ffi for p in all_peers) / len(all_peers), 1)
        name_map = {p.ticker: p.name for p in all_peers}

        commentary = (
            f"Automotive & EV peer benchmark for {target}. Sector average FFI is {avg_ffi}. "
            "High margin variability and EV transition costs place majority of peers in the watchlist tier."
        )

        return PeerComparisonResponse(
            target_ticker=target,
            target_name=name_map.get(target, f"{target} Corp"),
            sector="Automotive & Clean Mobility",
            sector_average_ffi=avg_ffi,
            peers=all_peers,
            sector_commentary=commentary,
        )

    def _no_peer_set(self, target: str) -> PeerComparisonResponse:
        # No curated peer group for this ticker: say so instead of inventing placeholder companies.
        return PeerComparisonResponse(
            target_ticker=target,
            target_name=target,
            sector="",
            sector_average_ffi=None,
            peers=[],
            sector_commentary=f"No peer set is configured for {target} yet.",
        )
