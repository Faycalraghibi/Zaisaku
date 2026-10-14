"""API router for forensic financial intelligence — filing diffs and language drift."""

from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path

from fastapi import APIRouter, HTTPException, Response, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from zaisaku.api.dependencies import ConfigDep, RerankerDep, RouterDep
from zaisaku.forensics.beneish import BeneishCalculator, BeneishMetrics
from zaisaku.forensics.call_simulator import CallSimulator, EarningsCallSession
from zaisaku.forensics.contradiction_radar import ContradictionRadar
from zaisaku.forensics.diff_engine import DiffEngine
from zaisaku.forensics.footnote_scanner import FootnoteScanner
from zaisaku.forensics.investigation import InvestigationOrchestrator
from zaisaku.forensics.peers import PeerAnalyzer, PeerComparisonResponse
from zaisaku.forensics.report_generator import ForensicReportGenerator
from zaisaku.forensics.sandbox import BenchmarkRequest, BenchmarkResponse, SandboxBenchmark
from zaisaku.forensics.scorecard import ForensicScorecard
from zaisaku.forensics.table_extractor import FinancialStatementsResponse, TableExtractor
from zaisaku.forensics.trends import CompanyTrendsResponse, TrendsAnalyzer
from zaisaku.ingestion.loader import DocumentLoader
from zaisaku.ingestion.sec_edgar import SECEdgarClient

router = APIRouter(prefix="/forensics", tags=["forensics"])


class FilingDiffRequest(BaseModel):
    ticker: str = Field(..., description="Stock ticker symbol, e.g. NVDA, AAPL")
    form: str = Field(default="10-K", description="SEC filing form, e.g. 10-K or 10-Q")
    use_llm: bool = Field(default=False, description="Whether to generate an LLM forensic executive summary")


class TextDiffRequest(BaseModel):
    ticker: str = Field(default="CUSTOM")
    form: str = Field(default="10-K")
    current_text: str
    prior_text: str
    section_name: str = Field(default="item_1a_risk_factors")


class SectionDiffResponse(BaseModel):
    section_name: str
    similarity_ratio: float
    drift_score: float
    severity: str
    added_paragraphs: list[str] = []
    removed_paragraphs: list[str] = []
    modified_paragraphs: list[dict[str, str]] = []
    opcodes: list[dict] = []


class FilingDiffResponse(BaseModel):
    ticker: str
    form: str
    current_filing: str
    prior_filing: str
    overall_drift_score: float
    overall_severity: str
    sections: dict[str, SectionDiffResponse]
    forensic_summary: str


@router.post("/diff", response_model=FilingDiffResponse)
async def compare_sec_filings(
    request: FilingDiffRequest,
    settings: ConfigDep,
    llm: RouterDep,
):
    """Download the two most recent consecutive filings for a ticker and quantify language drift."""
    ticker = request.ticker.strip().upper()
    form = request.form.strip().upper()
    if not ticker:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ticker cannot be empty.",
        )

    client = SECEdgarClient(timeout=45.0)
    try:
        consecutive = await asyncio.to_thread(client.fetch_consecutive_filings, ticker, form, count=2)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to fetch filings from SEC EDGAR: {str(e)}",
        ) from e

    if len(consecutive) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Need at least 2 consecutive {form} filings for {ticker} "
                f"to compute diff, found {len(consecutive)}."
            ),
        )

    curr_name, curr_bytes = consecutive[0]
    prior_name, prior_bytes = consecutive[1]

    # Parse filings into clean text using DocumentLoader
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        curr_file = tmp_path / curr_name
        prior_file = tmp_path / prior_name

        curr_file.write_bytes(curr_bytes)
        prior_file.write_bytes(prior_bytes)

        curr_doc = await asyncio.to_thread(DocumentLoader.load, curr_file)
        prior_doc = await asyncio.to_thread(DocumentLoader.load, prior_file)

    llm_to_use = llm if request.use_llm else None
    diff_result = await asyncio.to_thread(
        DiffEngine.compare_filings,
        ticker,
        form,
        curr_doc.text,
        prior_doc.text,
        curr_name,
        prior_name,
        llm_to_use,
    )

    return diff_result.to_dict()


@router.post("/diff/text", response_model=FilingDiffResponse)
async def compare_raw_texts(
    request: TextDiffRequest,
):
    """Compare two raw texts directly without calling external SEC APIs."""
    diff_result = DiffEngine.compare_filings(
        ticker=request.ticker,
        form=request.form,
        current_text=request.current_text,
        prior_text=request.prior_text,
        current_name="Current Text",
        prior_name="Prior Text",
    )
    return diff_result.to_dict()


class BeneishRequest(BaseModel):
    sales_t: float = Field(..., description="Sales for current period t")
    sales_t_prev: float = Field(..., description="Sales for previous period t-1")
    cogs_t: float = Field(..., description="Cost of Goods Sold for current period t")
    cogs_t_prev: float = Field(..., description="Cost of Goods Sold for previous period t-1")
    receivables_t: float = Field(..., description="Accounts Receivable for period t")
    receivables_t_prev: float = Field(..., description="Accounts Receivable for period t-1")
    current_assets_t: float = Field(..., description="Current Assets for period t")
    current_assets_t_prev: float = Field(..., description="Current Assets for period t-1")
    ppe_t: float = Field(..., description="Property, Plant & Equipment (net) for period t")
    ppe_t_prev: float = Field(..., description="Property, Plant & Equipment (net) for period t-1")
    total_assets_t: float = Field(..., description="Total Assets for period t")
    total_assets_t_prev: float = Field(..., description="Total Assets for period t-1")
    depreciation_t: float = Field(..., description="Depreciation expense for period t")
    depreciation_t_prev: float = Field(..., description="Depreciation expense for period t-1")
    sga_t: float = Field(..., description="SG&A expense for period t")
    sga_t_prev: float = Field(..., description="SG&A expense for period t-1")
    long_term_debt_t: float = Field(..., description="Long-term debt for period t")
    long_term_debt_t_prev: float = Field(..., description="Long-term debt for period t-1")
    net_income_t: float = Field(..., description="Net Income for period t")
    operating_cash_flow_t: float = Field(..., description="Operating Cash Flow for period t")


class BeneishResponse(BaseModel):
    m_score: float
    is_manipulator_probable: bool
    risk_level: str
    indices: dict[str, float]
    flagged_indices: list[str] = []
    interpretation: str


@router.post("/mscore", response_model=BeneishResponse)
async def calculate_beneish_mscore(request: BeneishRequest):
    """Calculate the 8-variable Beneish M-Score to detect earnings manipulation probability."""
    metrics = BeneishMetrics(**request.model_dump())
    result = BeneishCalculator.calculate(metrics)
    return result.to_dict()


class FootnoteScanRequest(BaseModel):
    text: str = Field(..., description="Financial filing text, footnote disclosures, or auditor notes")


class FootnoteFindingResponse(BaseModel):
    category: str
    title: str
    severity: str
    matched_phrase: str
    excerpt: str
    explanation: str


class FootnoteScanResponse(BaseModel):
    total_findings: int
    high_risk_count: int
    medium_risk_count: int
    findings: list[FootnoteFindingResponse]
    summary: str


@router.post("/footnotes/scan", response_model=FootnoteScanResponse)
async def scan_footnotes(request: FootnoteScanRequest):
    """Scan financial text for 5 high-impact accounting hazards and buried footnote risks."""
    result = FootnoteScanner.scan(request.text)
    return result.to_dict()


class ContradictionRequest(BaseModel):
    ticker: str = Field(default="CUSTOM", description="Stock ticker symbol")
    call_text: str = Field(..., description="Earnings call transcript or management prepared remarks")
    filing_text: str = Field(..., description="SEC 10-Q/10-K filing text or MD&A / Risk disclosures")
    use_llm: bool = Field(default=False, description="Whether to invoke LLM for semantic contradiction detection")


class ContradictionItemResponse(BaseModel):
    topic: str
    severity: str
    call_statement: str
    filing_statement: str
    divergence_analysis: str


class ContradictionResponse(BaseModel):
    ticker: str
    tone_divergence_score: float
    call_sentiment: str
    filing_sentiment: str
    divergence_severity: str
    contradictions_count: int
    contradictions: list[ContradictionItemResponse]
    executive_summary: str


@router.post("/contradictions", response_model=ContradictionResponse)
async def analyze_contradictions(
    request: ContradictionRequest,
    llm: RouterDep,
    reranker: RerankerDep,
):
    """Detect tone decoupling and semantic contradictions between spoken earnings calls and written 10-Q filings."""
    llm_to_use = llm if request.use_llm else None
    result = await asyncio.to_thread(
        ContradictionRadar.analyze,
        request.ticker,
        request.call_text,
        request.filing_text,
        llm_to_use,
        reranker,
    )
    return result.to_dict()


class ScorecardRequest(BaseModel):
    ticker: str = Field(default="CUSTOM", description="Stock ticker symbol")
    company_name: str = Field(default="", description="Company name")
    language_drift_score: float = Field(default=0.0, description="Filing Language Drift Score (0-100)")
    beneish_m_score: float = Field(default=-2.50, description="Beneish M-Score (-3.0 to 0.0)")
    footnote_hazards_count: int = Field(default=0, description="Number of high-severity footnote risks detected")
    call_contradictions_score: float = Field(default=0.0, description="Earnings call tone decoupling score (0-100)")
    contradiction_count: int = Field(default=0, description="Number of call vs 10-Q contradictions flagged")


class PillarScoreResponse(BaseModel):
    name: str
    weight: float
    raw_score: float
    weighted_score: float
    status: str
    key_findings: list[str] = []


class ScorecardResponse(BaseModel):
    ticker: str
    company_name: str
    composite_ffi: float
    risk_level: str
    recommendation: str
    pillars: dict[str, PillarScoreResponse]
    red_flags: list[str] = []
    summary: str


@router.post("/scorecard", response_model=ScorecardResponse)
async def generate_forensic_scorecard(request: ScorecardRequest):
    """Compute composite Forensic Fragility Index (FFI) synthesizing all 3 forensic intelligence pillars."""
    result = ForensicScorecard.calculate(
        ticker=request.ticker,
        company_name=request.company_name,
        language_drift_score=request.language_drift_score,
        beneish_m_score=request.beneish_m_score,
        footnote_hazards_count=request.footnote_hazards_count,
        call_contradictions_score=request.call_contradictions_score,
        contradiction_count=request.contradiction_count,
    )
    return result.to_dict()


class ForensicReportRequest(BaseModel):
    ticker: str = Field(default="CUSTOM", description="Stock ticker symbol")
    company_name: str = Field(default="", description="Company name")
    scorecard: dict | None = Field(default=None, description="Scorecard data")
    beneish: dict | None = Field(default=None, description="Beneish M-Score metrics")
    footnote_findings: list[dict] | None = Field(default=None, description="Footnote hazard findings")
    diff_result: dict | None = Field(default=None, description="Filing diff analysis")
    contradiction_result: dict | None = Field(default=None, description="Call vs filing contradiction analysis")


class ForensicReportResponse(BaseModel):
    ticker: str
    company_name: str
    markdown: str
    composite_ffi: float
    risk_level: str
    summary: str


@router.post("/report/generate", response_model=ForensicReportResponse)
async def generate_forensic_memo(request: ForensicReportRequest):
    """Generate an institutional-grade Forensic Due Diligence Memorandum in Markdown."""
    ticker = request.ticker.strip().upper() or "CUSTOM"
    company_name = request.company_name.strip() or ticker
    memo_md = ForensicReportGenerator.generate_memo(
        ticker=ticker,
        company_name=company_name,
        scorecard=request.scorecard,
        beneish=request.beneish,
        footnote_findings=request.footnote_findings,
        diff_result=request.diff_result,
        contradiction_result=request.contradiction_result,
    )
    scorecard = request.scorecard or {}
    return {
        "ticker": ticker,
        "company_name": company_name,
        "markdown": memo_md,
        "composite_ffi": float(scorecard.get("composite_ffi", 0.0)),
        "risk_level": str(scorecard.get("risk_level", "CLEAN")),
        "summary": str(scorecard.get("summary", "")),
    }


@router.post("/report/download")
async def download_forensic_memo(request: ForensicReportRequest):
    """Download the generated Forensic Due Diligence Memorandum as a markdown file."""
    ticker = request.ticker.strip().upper() or "CUSTOM"
    company_name = request.company_name.strip() or ticker
    memo_md = ForensicReportGenerator.generate_memo(
        ticker=ticker,
        company_name=company_name,
        scorecard=request.scorecard,
        beneish=request.beneish,
        footnote_findings=request.footnote_findings,
        diff_result=request.diff_result,
        contradiction_result=request.contradiction_result,
    )
    filename = f"forensic_due_diligence_{ticker.lower()}.md"
    return Response(
        content=memo_md.encode("utf-8"),
        media_type="text/markdown",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/trends/{ticker}", response_model=CompanyTrendsResponse)
async def get_company_trends(ticker: str):
    """Retrieve multi-year financial trends and AI-detected accrual anomaly flags."""
    analyzer = TrendsAnalyzer()
    return analyzer.analyze(ticker)


@router.get("/peers/{ticker}", response_model=PeerComparisonResponse)
async def get_sector_peers(ticker: str):
    """Retrieve sector peer comparative risk matrix and benchmark commentary."""
    analyzer = PeerAnalyzer()
    return analyzer.benchmark(ticker)


class InvestigationRequest(BaseModel):
    ticker: str = Field(..., description="Stock ticker symbol, e.g. NVDA")
    form: str = Field(default="10-K", description="SEC filing form")


@router.post("/investigate/stream")
async def run_investigation_stream(request: InvestigationRequest):
    """Execute an autonomous 4-stage multi-agent forensic investigation via SSE stream."""
    orchestrator = InvestigationOrchestrator()
    return StreamingResponse(
        orchestrator.run_investigation_stream(ticker=request.ticker, form=request.form),
        media_type="text/event-stream",
    )


@router.get("/tables/{ticker}", response_model=FinancialStatementsResponse)
async def get_financial_tables(ticker: str):
    """Retrieve structured financial statements with YoY variance calculations."""
    extractor = TableExtractor()
    return extractor.extract_tables(ticker)


@router.get("/calls/{ticker}", response_model=EarningsCallSession)
async def get_earnings_call(ticker: str):
    """Retrieve simulated multimodal earnings call audio session and synchronized transcript."""
    simulator = CallSimulator()
    return simulator.get_call_session(ticker)


@router.post("/sandbox/benchmark", response_model=BenchmarkResponse)
async def run_sandbox_benchmark(request: BenchmarkRequest):
    """Execute AI prompt and RAG benchmark across frontier LLM architectures."""
    benchmark = SandboxBenchmark()
    return benchmark.run_benchmark(request)






