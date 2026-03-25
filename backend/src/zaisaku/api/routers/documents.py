
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from zaisaku.api.dependencies import StoreDep

router = APIRouter(tags=["documents"])


class DiscoveredDocumentsResponse(BaseModel):
    documents: list[dict]


class DeleteResponse(BaseModel):
    deleted_chunks: int


@router.get("/documents", response_model=DiscoveredDocumentsResponse)
async def list_documents(store: StoreDep):
    docs = store.list_documents()
    return DiscoveredDocumentsResponse(documents=docs)


@router.delete("/documents/{doc_id}", response_model=DeleteResponse)
async def delete_document(doc_id: str, store: StoreDep):
    count = store.delete(doc_id)
    if count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {doc_id} not found."
        )
    return DeleteResponse(deleted_chunks=count)
