
from __future__ import annotations

import asyncio
import os
import shutil
import uuid
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from zaisaku.api.dependencies import ConfigDep, EmbedderDep, StoreDep
from zaisaku.ingestion.chunker import Chunker
from zaisaku.ingestion.loader import DocumentLoader
from zaisaku.models import IngestResponse

router = APIRouter(tags=["ingestion"])

@router.post("/ingest", response_model=IngestResponse)
async def ingest_document(
    settings: ConfigDep,
    embedder: EmbedderDep,
    store: StoreDep,
    file: Annotated[UploadFile, File(...)],
):
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No filename provided in upload.",
        )

    suffix = Path(file.filename).suffix.lower()
    if suffix not in DocumentLoader.SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type. Must be one of: {DocumentLoader.SUPPORTED_EXTENSIONS}",
        )

    if file.size is not None and file.size > settings.max_upload_size:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=f"File exceeds maximum allowed upload size of {settings.max_upload_size} bytes.",
        )

    safe_filename = Path(file.filename).name
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    temp_path = upload_dir / f"{uuid.uuid4()}_{safe_filename}"

    try:
        total_bytes = 0
        chunk_buffer_size = 1024 * 1024  # 1MB
        with temp_path.open("wb") as buffer:
            while True:
                chunk = await file.read(chunk_buffer_size)
                if not chunk:
                    break
                total_bytes += len(chunk)
                if total_bytes > settings.max_upload_size:
                    raise HTTPException(
                        status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                        detail=f"File exceeds maximum allowed upload size of {settings.max_upload_size} bytes.",
                    )
                buffer.write(chunk)

        try:
            pages = await asyncio.to_thread(DocumentLoader.load_pages, temp_path)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Failed to parse document: {str(e)}",
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
                meta["source"] = file.filename
                meta["doc_id"] = doc_id
                metadatas.append(meta)

        if not chunks:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Extracted text resulted in 0 chunks (file might be empty or unreadable).",
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

        # Persist raw document for viewing and citations
        storage_dir = Path(settings.upload_dir) / "documents"
        storage_dir.mkdir(parents=True, exist_ok=True)
        permanent_path = storage_dir / f"{doc_id}_{safe_filename}"
        shutil.copyfile(temp_path, permanent_path)

        return IngestResponse(
            doc_id=doc_id,
            filename=file.filename,
            chunks=count,
            status="indexed",
        )

    finally:
        if temp_path.exists():
            os.remove(temp_path)
