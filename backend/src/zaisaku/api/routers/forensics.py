"""API router for forensic financial intelligence — filing diffs and language drift."""

from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from zaisaku.api.dependencies import ConfigDep, RouterDep
from zaisaku.forensics.diff_engine import DiffEngine
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
