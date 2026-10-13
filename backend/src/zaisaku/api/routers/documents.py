
import asyncio
import contextlib
import os
from pathlib import Path

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse
from pydantic import BaseModel

from zaisaku.api.dependencies import ConfigDep, StoreDep

router = APIRouter(tags=["documents"])


class DiscoveredDocumentsResponse(BaseModel):
    documents: list[dict]


class DeleteResponse(BaseModel):
    deleted_chunks: int


@router.get("/documents", response_model=DiscoveredDocumentsResponse)
async def list_documents(store: StoreDep):
    docs = await asyncio.to_thread(store.list_documents)
    return DiscoveredDocumentsResponse(documents=docs)


@router.get("/documents/{doc_id}/raw")
async def get_raw_document(doc_id: str, settings: ConfigDep):
    storage_dir = Path(settings.upload_dir) / "documents"
    matches = list(storage_dir.glob(f"{doc_id}_*")) if storage_dir.exists() else []
    if not matches:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document file for {doc_id} not found.",
        )
    target = matches[0]
    filename = target.name.split("_", 1)[1] if "_" in target.name else target.name
    media_type = "application/pdf" if target.suffix.lower() == ".pdf" else None
    return FileResponse(
        path=target,
        filename=filename,
        media_type=media_type,
    )


@router.delete("/documents/{doc_id}", response_model=DeleteResponse)
async def delete_document(doc_id: str, store: StoreDep, settings: ConfigDep):
    count = await asyncio.to_thread(store.delete, doc_id)
    if count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {doc_id} not found."
        )

    # Clean up physical document file
    storage_dir = Path(settings.upload_dir) / "documents"
    if storage_dir.exists():
        for target in storage_dir.glob(f"{doc_id}_*"):
            with contextlib.suppress(OSError):
                os.remove(target)

    return DeleteResponse(deleted_chunks=count)
