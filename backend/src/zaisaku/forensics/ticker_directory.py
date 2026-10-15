"""Institutional Index Directory & Universal SEC Equities Catalog.

Provides comprehensive coverage across major macro market indices (S&P 500 SPY,
Nasdaq-100 QQQ, Dow Jones DIA, Russell 2000 IWM, Sector ETFs), index constituents,
and dynamic SEC EDGAR company directory search.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class TickerEntry(BaseModel):
    """Catalog record for a company or market index."""

    ticker: str
    name: str
    cik: str
    exchange: str
    sector: str
    index_tags: list[str] = Field(default_factory=list)
    ffi_score: float = 20.0
    risk_tier: str = "LOW_RISK"
    is_macro_index: bool = False


class MarketIndexSummary(BaseModel):
    """Macro benchmark or sector index summary."""

    index_id: str
    name: str
    ticker: str
    asset_class: str
    composite_fragility: float
    top_constituents: list[str]
    description: str


class TickerSearchResponse(BaseModel):
    """Search response payload for autocomplete and directory exploration."""

    query: str
    index_filter: str | None = None
    total_matches: int
    results: list[TickerEntry] = Field(default_factory=list)


class TickerDirectoryService:
    """Institutional directory service mapping macro indices, constituents, and SEC filers."""

    SEC_TICKERS_URL: str = "https://www.sec.gov/files/company_tickers.json"

    # Pre-calculated Macro Indices
    INDEX_BENCHMARKS: list[MarketIndexSummary] = [
        MarketIndexSummary(
            index_id="SPY",
            name="S&P 500 Large-Cap Core Benchmark",
            ticker="SPY",
            asset_class="Large-Cap US Equities",
            composite_fragility=22.5,
            top_constituents=["MSFT", "AAPL", "NVDA", "AMZN", "GOOGL", "META", "BRK.B"],
            description=(
                "The premier benchmark for institutional US equity performance across 500 leading corporations."
            ),
        ),
        MarketIndexSummary(
            index_id="QQQ",
            name="Nasdaq-100 High-Growth & Tech Benchmark",
            ticker="QQQ",
            asset_class="Technology & Growth Equities",
            composite_fragility=24.8,
            top_constituents=["NVDA", "AAPL", "MSFT", "AMZN", "AVGO", "META", "TSLA"],
            description=(
                "Tracks 100 of the largest non-financial corporations with heavy exposure to generative AI and tech."
            ),
        ),
        MarketIndexSummary(
            index_id="DIA",
            name="Dow Jones Industrial Average Mega-Cap",
            ticker="DIA",
            asset_class="Blue-Chip US Equities",
            composite_fragility=19.4,
            top_constituents=["UNH", "GS", "MSFT", "HD", "CAT", "MCD", "BA"],
            description=(
                "30 prominent US blue-chip institutions across finance, consumer retail, and industrial defense."
            ),
        ),
        MarketIndexSummary(
            index_id="IWM",
            name="Russell 2000 Small-Cap US Equity Index",
            ticker="IWM",
            asset_class="Small-Cap US Equities",
            composite_fragility=44.2,
            top_constituents=["FTAI", "VRT", "SMCI", "MEDP", "ENSG", "SAIA"],
            description=(
                "2,000 small-cap domestic corporations sensitive to regional bank credit and macro interest rates."
            ),
        ),
        MarketIndexSummary(
            index_id="SMH",
            name="VanEck Semiconductor Sector Benchmark",
            ticker="SMH",
            asset_class="Semiconductor Hardware",
            composite_fragility=31.0,
            top_constituents=["NVDA", "TSM", "AVGO", "AMD", "QCOM", "ASML", "TXN"],
            description=(
                "Leading 25 global semiconductor designers and fabrication foundries powering artificial intelligence."
            ),
        ),
        MarketIndexSummary(
            index_id="XLK",
            name="Technology Select Sector SPDR",
            ticker="XLK",
            asset_class="Enterprise Tech",
            composite_fragility=21.8,
            top_constituents=["MSFT", "NVDA", "AAPL", "AVGO", "CRM", "AMD", "ORCL"],
            description=(
                "Pure-play information technology companies encompassing cloud software, silicon, and IT services."
            ),
        ),
        MarketIndexSummary(
            index_id="XLF",
            name="Financial Select Sector SPDR",
            ticker="XLF",
            asset_class="Money Center Banks & Insurance",
            composite_fragility=27.2,
            top_constituents=["BRK.B", "JPM", "V", "MA", "BAC", "WFC", "GS"],
            description=(
                "Diversified money center banks, insurance underwriters, broker-dealers, and payment rails."
            ),
        ),
    ]

    # Curated institutional universe covering all key S&P 500 / Nasdaq / Dow leadership
    CURATED_ENTRIES: list[TickerEntry] = [
        # Macro Index ETFs
        TickerEntry(
            ticker="SPY",
            name="SPDR S&P 500 ETF Trust",
            cik="0000884394",
            exchange="NYSE Arca",
            sector="Macro Market Benchmark",
            index_tags=["S&P 500", "Macro Indices"],
            ffi_score=22.5,
            risk_tier="LOW_RISK",
            is_macro_index=True,
        ),
        TickerEntry(
            ticker="QQQ",
            name="Invesco QQQ Trust",
            cik="0001067839",
            exchange="NASDAQ",
            sector="Technology Growth Benchmark",
            index_tags=["Nasdaq 100", "Macro Indices"],
            ffi_score=24.8,
            risk_tier="LOW_RISK",
            is_macro_index=True,
        ),
        TickerEntry(
            ticker="DIA",
            name="SPDR Dow Jones Industrial Average ETF",
            cik="0001064641",
            exchange="NYSE Arca",
            sector="Blue-Chip Mega-Cap Benchmark",
            index_tags=["Dow 30", "Macro Indices"],
            ffi_score=19.4,
            risk_tier="LOW_RISK",
            is_macro_index=True,
        ),
        TickerEntry(
            ticker="IWM",
            name="iShares Russell 2000 ETF",
            cik="0001100663",
            exchange="NYSE Arca",
            sector="Small-Cap Risk Benchmark",
            index_tags=["Russell 2000", "Macro Indices"],
            ffi_score=44.2,
            risk_tier="MODERATE_RISK",
            is_macro_index=True,
        ),
        TickerEntry(
            ticker="SMH",
            name="VanEck Semiconductor ETF",
            cik="0001524316",
            exchange="NASDAQ",
            sector="Semiconductors",
            index_tags=["Semiconductors", "Sector ETFs"],
            ffi_score=31.0,
            risk_tier="MODERATE_RISK",
            is_macro_index=True,
        ),
        # Mega-Cap Technology & AI
        TickerEntry(
            ticker="NVDA",
            name="NVIDIA Corporation",
            cik="0001045810",
            exchange="NASDAQ",
            sector="Semiconductors & AI Hardware",
            index_tags=["S&P 500", "Nasdaq 100", "Semiconductors"],
            ffi_score=18.0,
            risk_tier="LOW_RISK",
        ),
        TickerEntry(
            ticker="AAPL",
            name="Apple Inc.",
            cik="0000320193",
            exchange="NASDAQ",
            sector="Consumer Electronics & Software",
            index_tags=["S&P 500", "Nasdaq 100", "Dow 30"],
            ffi_score=14.0,
            risk_tier="LOW_RISK",
        ),
        TickerEntry(
            ticker="MSFT",
            name="Microsoft Corporation",
            cik="0000789019",
            exchange="NASDAQ",
            sector="Enterprise Cloud & Productivity",
            index_tags=["S&P 500", "Nasdaq 100", "Dow 30"],
            ffi_score=22.0,
            risk_tier="LOW_RISK",
        ),
        TickerEntry(
            ticker="GOOGL",
            name="Alphabet Inc.",
            cik="0001652044",
            exchange="NASDAQ",
            sector="Internet Services & Generative AI",
            index_tags=["S&P 500", "Nasdaq 100"],
            ffi_score=16.5,
            risk_tier="LOW_RISK",
        ),
        TickerEntry(
            ticker="META",
            name="Meta Platforms, Inc.",
            cik="0001326801",
            exchange="NASDAQ",
            sector="Social Technologies & Digital Advertising",
            index_tags=["S&P 500", "Nasdaq 100"],
            ffi_score=21.0,
            risk_tier="LOW_RISK",
        ),
        TickerEntry(
            ticker="AMZN",
            name="Amazon.com, Inc.",
            cik="0001018724",
            exchange="NASDAQ",
            sector="E-Commerce & Cloud Infrastructure (AWS)",
            index_tags=["S&P 500", "Nasdaq 100", "Dow 30"],
            ffi_score=28.0,
            risk_tier="LOW_RISK",
        ),
        TickerEntry(
            ticker="TSLA",
            name="Tesla, Inc.",
            cik="0001318605",
            exchange="NASDAQ",
            sector="Automotive & Clean Energy",
            index_tags=["S&P 500", "Nasdaq 100"],
            ffi_score=42.0,
            risk_tier="MODERATE_RISK",
        ),
        TickerEntry(
            ticker="AVGO",
            name="Broadcom Inc.",
            cik="0001730168",
            exchange="NASDAQ",
            sector="Semiconductors & Infrastructure Software",
            index_tags=["S&P 500", "Nasdaq 100", "Semiconductors"],
            ffi_score=24.5,
            risk_tier="LOW_RISK",
        ),
        TickerEntry(
            ticker="AMD",
            name="Advanced Micro Devices, Inc.",
            cik="0000002488",
            exchange="NASDAQ",
            sector="Semiconductors & Heterogeneous Compute",
            index_tags=["S&P 500", "Nasdaq 100", "Semiconductors"],
            ffi_score=27.0,
            risk_tier="LOW_RISK",
        ),
        TickerEntry(
            ticker="ORCL",
            name="Oracle Corporation",
            cik="0001341439",
            exchange="NYSE",
            sector="Cloud Database & Enterprise Infrastructure",
            index_tags=["S&P 500"],
            ffi_score=29.0,
            risk_tier="LOW_RISK",
        ),
        TickerEntry(
            ticker="PLTR",
            name="Palantir Technologies Inc.",
            cik="0001321655",
            exchange="NASDAQ",
            sector="Data Analytics & Defense AI",
            index_tags=["S&P 500"],
            ffi_score=35.0,
            risk_tier="MODERATE_RISK",
        ),
        TickerEntry(
            ticker="CRM",
            name="Salesforce, Inc.",
            cik="0001108524",
            exchange="NYSE",
            sector="Enterprise CRM & Agentic Automation",
            index_tags=["S&P 500", "Dow 30"],
            ffi_score=23.0,
            risk_tier="LOW_RISK",
        ),
        TickerEntry(
            ticker="INTC",
            name="Intel Corporation",
            cik="0000050863",
            exchange="NASDAQ",
            sector="Semiconductors & Foundry Services",
            index_tags=["S&P 500", "Nasdaq 100", "Semiconductors"],
            ffi_score=48.5,
            risk_tier="MODERATE_RISK",
        ),
        # Financial Services & Money Center Banking
        TickerEntry(
            ticker="JPM",
            name="JPMorgan Chase & Co.",
            cik="0000019617",
            exchange="NYSE",
            sector="Investment Banking & Wealth Management",
            index_tags=["S&P 500", "Dow 30", "Financials"],
            ffi_score=19.0,
            risk_tier="LOW_RISK",
        ),
        TickerEntry(
            ticker="BAC",
            name="Bank of America Corporation",
            cik="0000070858",
            exchange="NYSE",
            sector="Commercial & Investment Banking",
            index_tags=["S&P 500", "Financials"],
            ffi_score=23.5,
            risk_tier="LOW_RISK",
        ),
        TickerEntry(
            ticker="GS",
            name="The Goldman Sachs Group, Inc.",
            cik="0000886982",
            exchange="NYSE",
            sector="Global Investment Banking & Markets",
            index_tags=["S&P 500", "Dow 30", "Financials"],
            ffi_score=26.0,
            risk_tier="LOW_RISK",
        ),
        TickerEntry(
            ticker="BRK.B",
            name="Berkshire Hathaway Inc.",
            cik="0001067983",
            exchange="NYSE",
            sector="Conglomerate & Insurance Holdings",
            index_tags=["S&P 500", "Financials"],
            ffi_score=13.0,
            risk_tier="LOW_RISK",
        ),
        TickerEntry(
            ticker="V",
            name="Visa Inc.",
            cik="0001403161",
            exchange="NYSE",
            sector="Global Payments Technology",
            index_tags=["S&P 500", "Dow 30", "Financials"],
            ffi_score=15.0,
            risk_tier="LOW_RISK",
        ),
        # Healthcare & Life Sciences
        TickerEntry(
            ticker="LLY",
            name="Eli Lilly and Company",
            cik="0000059478",
            exchange="NYSE",
            sector="Pharmaceuticals & Metabolic Therapeutics",
            index_tags=["S&P 500", "Healthcare"],
            ffi_score=22.0,
            risk_tier="LOW_RISK",
        ),
        TickerEntry(
            ticker="JNJ",
            name="Johnson & Johnson",
            cik="0000200406",
            exchange="NYSE",
            sector="Pharmaceuticals & MedTech Devices",
            index_tags=["S&P 500", "Dow 30", "Healthcare"],
            ffi_score=18.0,
            risk_tier="LOW_RISK",
        ),
        TickerEntry(
            ticker="UNH",
            name="UnitedHealth Group Incorporated",
            cik="0000731766",
            exchange="NYSE",
            sector="Managed Healthcare Services",
            index_tags=["S&P 500", "Dow 30", "Healthcare"],
            ffi_score=25.0,
            risk_tier="LOW_RISK",
        ),
        # Industrial, Aerospace & Consumer
        TickerEntry(
            ticker="BA",
            name="The Boeing Company",
            cik="0000012927",
            exchange="NYSE",
            sector="Aerospace & Commercial Aviation",
            index_tags=["S&P 500", "Dow 30", "Industrials"],
            ffi_score=58.0,
            risk_tier="ELEVATED_WATCH",
        ),
        TickerEntry(
            ticker="CAT",
            name="Caterpillar Inc.",
            cik="0000018230",
            exchange="NYSE",
            sector="Heavy Construction & Mining Machinery",
            index_tags=["S&P 500", "Dow 30", "Industrials"],
            ffi_score=20.0,
            risk_tier="LOW_RISK",
        ),
        TickerEntry(
            ticker="WMT",
            name="Walmart Inc.",
            cik="0000104169",
            exchange="NYSE",
            sector="Omnichannel Retail & Grocery",
            index_tags=["S&P 500", "Dow 30", "Consumer"],
            ffi_score=16.0,
            risk_tier="LOW_RISK",
        ),
        TickerEntry(
            ticker="COST",
            name="Costco Wholesale Corporation",
            cik="0000909832",
            exchange="NASDAQ",
            sector="Membership Warehouse Club Retail",
            index_tags=["S&P 500", "Nasdaq 100", "Consumer"],
            ffi_score=14.5,
            risk_tier="LOW_RISK",
        ),
        # Energy & Utilities
        TickerEntry(
            ticker="XOM",
            name="Exxon Mobil Corporation",
            cik="0000034088",
            exchange="NYSE",
            sector="Integrated Oil & Gas Exploration",
            index_tags=["S&P 500", "Energy"],
            ffi_score=21.0,
            risk_tier="LOW_RISK",
        ),
        # Forensic Radar & High-Risk Case Studies
        TickerEntry(
            ticker="SMCI",
            name="Super Micro Computer, Inc.",
            cik="0001375365",
            exchange="NASDAQ",
            sector="Server Hardware & AI Datacenters",
            index_tags=["Nasdaq 100", "Russell 2000", "High-Risk Radar"],
            ffi_score=84.0,
            risk_tier="CRITICAL_ALERT",
        ),
        TickerEntry(
            ticker="COIN",
            name="Coinbase Global, Inc.",
            cik="0001679788",
            exchange="NASDAQ",
            sector="Crypto Economy Exchange Platform",
            index_tags=["High-Risk Radar"],
            ffi_score=62.0,
            risk_tier="ELEVATED_WATCH",
        ),
        TickerEntry(
            ticker="RIVN",
            name="Rivian Automotive, Inc.",
            cik="0001874178",
            exchange="NASDAQ",
            sector="Electric Vehicle OEM",
            index_tags=["Nasdaq 100", "High-Risk Radar"],
            ffi_score=68.0,
            risk_tier="ELEVATED_WATCH",
        ),
    ]

    def __init__(self) -> None:
        self._sec_cache: dict[str, dict[str, Any]] | None = None

    def get_indices(self) -> list[MarketIndexSummary]:
        """Return all supported institutional macro market and sector indices."""
        return self.INDEX_BENCHMARKS

    def search_tickers(
        self,
        query: str,
        index_filter: str | None = None,
        limit: int = 20,
    ) -> TickerSearchResponse:
        """Search tickers across curated indices, constituents, and SEC EDGAR database."""
        q = query.strip().upper()
        norm_filter = index_filter.strip() if index_filter else None

        results: list[TickerEntry] = []
        seen: set[str] = set()

        # Step 1: Match against curated index universe
        for entry in self.CURATED_ENTRIES:
            if norm_filter and norm_filter != "All" and norm_filter not in entry.index_tags:
                continue

            # Match query against ticker or company name
            if not q or q in entry.ticker.upper() or q.lower() in entry.name.lower():
                results.append(entry)
                seen.add(entry.ticker.upper())
                if len(results) >= limit:
                    break

        # Step 2: If query given and room remains, fallback to SEC EDGAR company directory
        if q and len(results) < limit:
            sec_matches = self._search_sec_directory(q, limit - len(results), seen)
            results.extend(sec_matches)

        return TickerSearchResponse(
            query=query,
            index_filter=index_filter,
            total_matches=len(results),
            results=results,
        )

    def _search_sec_directory(
        self, query: str, max_count: int, exclude: set[str]
    ) -> list[TickerEntry]:
        """Query or pull from cached SEC company tickers directory."""
        if self._sec_cache is None:
            self._sec_cache = self._fetch_sec_tickers()

        matched: list[TickerEntry] = []
        for symbol, info in self._sec_cache.items():
            if symbol in exclude:
                continue
            name = info.get("title", "")
            if query in symbol or query.lower() in name.lower():
                matched.append(
                    TickerEntry(
                        ticker=symbol,
                        name=name,
                        cik=str(info.get("cik_str", "")).zfill(10),
                        exchange="SEC EDGAR",
                        sector="Public Reporting Entity",
                        index_tags=["SEC Universe"],
                        ffi_score=25.0,
                        risk_tier="LOW_RISK",
                    )
                )
                if len(matched) >= max_count:
                    break
        return matched

    def _fetch_sec_tickers(self) -> dict[str, dict[str, Any]]:
        """Fetch SEC company tickers dictionary or fallback to core baseline."""
        try:
            headers = {"User-Agent": "ZaisakuFinancialBot/1.0 (contact@zaisaku.internal)"}
            r = httpx.get(self.SEC_TICKERS_URL, headers=headers, timeout=5.0)
            if r.status_code == 200:
                data = r.json()
                cache: dict[str, dict[str, Any]] = {}
                for entry in data.values():
                    sym = str(entry.get("ticker", "")).strip().upper()
                    if sym:
                        cache[sym] = entry
                return cache
        except Exception as e:
            logger.info("SEC tickers online fetch skipped, using static catalog: %s", e)

        # Static fallback if SEC website is unreachable
        return {
            entry.ticker: {"title": entry.name, "cik_str": entry.cik}
            for entry in self.CURATED_ENTRIES
        }

    def get_ticker_entry(self, ticker: str) -> TickerEntry:
        """Retrieve or build a TickerEntry for any ticker symbol."""
        t = ticker.strip().upper()
        for entry in self.CURATED_ENTRIES:
            if entry.ticker.upper() == t:
                return entry

        # Fallback for dynamic ticker
        return TickerEntry(
            ticker=t,
            name=f"{t} Corporation",
            cik="0000000000",
            exchange="NYSE/NASDAQ",
            sector="Diversified Commercial Enterprise",
            index_tags=["SEC Universe"],
            ffi_score=25.0,
            risk_tier="LOW_RISK",
        )
