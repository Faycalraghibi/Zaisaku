"""Document ingestion endpoint."""

from __future__ import annotations

import os
import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from zaisaku.api.dependencies import ConfigDep, EmbedderDep, StoreDep
from zaisaku.ingestion.chunker import Chunker
from zaisaku.ingestion.loader import DocumentLoader
from zaisaku.models import IngestResponse

router = APIRouter(tags=["ingestion"])

# Temp directory for saving uploads before parsing
_UPLOAD_DIR = Path("uploads")


@router.post("/ingest", response_model=IngestResponse)
async def ingest_document(
    settings: ConfigDep,
    embedder: EmbedderDep,
    store: StoreDep,
    file: UploadFile = File(...),
):
    """Upload a file, parse it, chunk it, embed it, and store it in the vector DB."""
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No filename provided in upload.",
        )

    # Pre-validate extension
    suffix = Path(file.filename).suffix.lower()
    if suffix not in DocumentLoader.SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type. Must be one of: {DocumentLoader.SUPPORTED_EXTENSIONS}",
        )

    _UPLOAD_DIR.mkdir(exist_ok=True)
    temp_path = _UPLOAD_DIR / f"{uuid.uuid4()}_{file.filename}"

    try:
        # Save file to disk
        with temp_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 1. Load document
        try:
            doc = DocumentLoader.load(temp_path)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Failed to parse document: {str(e)}",
            )

        # 2. Chunk text
        chunks: list[str] = Chunker.chunk(
            doc.text,
            chunk_size=settings.chunk_size,
            overlap=settings.chunk_overlap,
        )

        if not chunks:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Extracted text resulted in 0 chunks (file might be empty or unreadable).",
            )

        # 3. Embed chunks (batch processing)
        try:
            embeddings = embedder.embed(chunks)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate embeddings: {str(e)}",
            )

        # 4. Upsert to Vector Store
        doc_id = str(uuid.uuid4())
        # Replicate base document metadata for each chunk
        metadatas = [doc.metadata.copy() for _ in chunks]
        
        # Override source with original filename natively rather than the temp uuid path
        for m in metadatas:
            m["source"] = file.filename

        try:
            count = store.upsert(
                doc_id=doc_id,
                chunks=chunks,
                embeddings=embeddings,
                metadatas=metadatas,
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to store vectors: {str(e)}",
            )

        return IngestResponse(
            doc_id=doc_id,
            filename=file.filename,
            chunks=count,
            status="indexed",
        )

    finally:
        # Cleanup temp file
        if temp_path.exists():
            os.remove(temp_path)
