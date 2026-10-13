"""API router for forensic financial intelligence — filing diffs and language drift."""

from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from zaisaku.api.dependencies import ConfigDep, RouterDep
from zaisaku.forensics.beneish import BeneishCalculator, BeneishMetrics
from zaisaku.forensics.diff_engine import DiffEngine
from zaisaku.forensics.footnote_scanner import FootnoteScanner
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
