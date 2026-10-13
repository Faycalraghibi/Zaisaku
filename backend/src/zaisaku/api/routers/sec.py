from __future__ import annotations

import asyncio
import os
import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from zaisaku.api.dependencies import ConfigDep, EmbedderDep, StoreDep
from zaisaku.ingestion.chunker import Chunker
from zaisaku.ingestion.loader import DocumentLoader
from zaisaku.ingestion.sec_edgar import SECEdgarClient
from zaisaku.models import IngestResponse

router = APIRouter(prefix="/sec", tags=["sec"])


class SECIngestRequest(BaseModel):
    ticker: str = Field(..., description="Stock ticker symbol, e.g. NVDA or AAPL")
    form: str = Field(default="10-K", description="Filing form, e.g. 10-K, 10-Q, 8-K")


@router.post("/ingest", response_model=IngestResponse)
async def ingest_sec_filing(
    request: SECIngestRequest,
    settings: ConfigDep,
    embedder: EmbedderDep,
    store: StoreDep,
):
    ticker = request.ticker.strip().upper()
    form = request.form.strip().upper()
    if not ticker:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ticker cannot be empty.",
        )

    client = SECEdgarClient(timeout=30.0)
    try:
        filename, content = await asyncio.to_thread(client.fetch_recent_filing, ticker, form)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to fetch filing from SEC EDGAR: {str(e)}",
        ) from e

    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    temp_path = upload_dir / f"{uuid.uuid4()}_{filename}"

    try:
        temp_path.write_bytes(content)

        try:
            pages = await asyncio.to_thread(DocumentLoader.load_pages, temp_path)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Failed to parse SEC document: {str(e)}",
            ) from e

        doc_id = str(uuid.uuid4())
        chunks: list[str] = []
        metadatas: list[dict] = []

        for p in pages:
            p_chunks = Chunker.chunk(
                p.text,
                chunk_size=settings.chunk_size,
                overlap=settings.chunk_overlap,
            )
            for c_text in p_chunks:
                chunks.append(c_text)
                meta = p.metadata.copy()
                meta["source"] = filename
                meta["doc_id"] = doc_id
                meta["ticker"] = ticker
                meta["form"] = form
                metadatas.append(meta)

        if not chunks:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Extracted text resulted in 0 chunks.",
            )

        try:
            embeddings = await asyncio.to_thread(embedder.embed, chunks)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate embeddings: {str(e)}",
            ) from e

        try:
            count = await asyncio.to_thread(
                store.upsert,
                doc_id=doc_id,
                chunks=chunks,
                embeddings=embeddings,
                metadatas=metadatas,
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to store vectors: {str(e)}",
            ) from e

        storage_dir = Path(settings.upload_dir) / "documents"
        storage_dir.mkdir(parents=True, exist_ok=True)
        permanent_path = storage_dir / f"{doc_id}_{filename}"
        shutil.copyfile(temp_path, permanent_path)

        return IngestResponse(
            doc_id=doc_id,
            filename=filename,
            chunks=count,
            status="indexed",
        )
    finally:
        if temp_path.exists():
            os.remove(temp_path)
