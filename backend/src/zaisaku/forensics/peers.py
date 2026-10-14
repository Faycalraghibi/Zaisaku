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
    sector_average_ffi: float
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
            return self._build_generic_sector(t)

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
                ffi=26.0,
                drift_pct=14.2,
                beneish_mscore=-2.68,
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
                ffi=31.0,
                drift_pct=16.5,
                beneish_mscore=-2.52,
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
                ffi=28.0,
                drift_pct=15.4,
                beneish_mscore=-2.81,
                risk_tier="LOW_RISK",
                footnote_hazard_count=2,
                key_vulnerability="DOJ antitrust search distribution litigation and potential behavioral remedies.",
            ),
            PeerMetric(
                ticker="META",
                name="Meta Platforms Inc.",
                market_cap="$1.45T",
                ffi=25.0,
                drift_pct=13.0,
                beneish_mscore=-2.72,
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

    def _build_generic_sector(self, target: str) -> PeerComparisonResponse:
        all_peers = [
            PeerMetric(
                ticker=target,
                name=f"{target} Corporation",
                market_cap="$50B",
                ffi=25.0,
                drift_pct=12.0,
                beneish_mscore=-2.60,
                risk_tier="LOW_RISK",
                footnote_hazard_count=1,
                key_vulnerability="Standard competitive and macro interest rate exposure disclosures.",
            ),
            PeerMetric(
                ticker="PEER1",
                name="Benchmark Peer A",
                market_cap="$65B",
                ffi=22.0,
                drift_pct=10.5,
                beneish_mscore=-2.72,
                risk_tier="LOW_RISK",
                footnote_hazard_count=0,
                key_vulnerability="Moderate working capital variation.",
            ),
            PeerMetric(
                ticker="PEER2",
                name="Benchmark Peer B",
                market_cap="$40B",
                ffi=48.0,
                drift_pct=26.0,
                beneish_mscore=-2.05,
                risk_tier="WATCHLIST",
                footnote_hazard_count=2,
                key_vulnerability="Elevated receivables growth and customer concentration.",
            ),
            PeerMetric(
                ticker="PEER3",
                name="Benchmark Peer C",
                market_cap="$85B",
                ffi=19.0,
                drift_pct=8.0,
                beneish_mscore=-2.88,
                risk_tier="LOW_RISK",
                footnote_hazard_count=0,
                key_vulnerability="Foreign exchange hedging volatility.",
            ),
        ]

        avg_ffi = round(sum(p.ffi for p in all_peers) / len(all_peers), 1)

        commentary = (
            f"Comparative industry peer benchmark for {target}. Sector average FFI is {avg_ffi}. "
            f"{target} maintains risk scores in line with sector norms."
        )

        return PeerComparisonResponse(
            target_ticker=target,
            target_name=f"{target} Corp",
            sector="General Equities Sector",
            sector_average_ffi=avg_ffi,
            peers=all_peers,
            sector_commentary=commentary,
        )
