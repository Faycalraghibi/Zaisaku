"""Vector store implementation for document retrieval.

Provides a Protocol for swappability and a default ChromaDB implementation.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from chromadb.api import ClientAPI

logger = logging.getLogger(__name__)


@runtime_checkable
class VectorStore(Protocol):
    """Interface for vector database interactions."""

    def upsert(
        self, doc_id: str, chunks: list[str], embeddings: list[list[float]], metadatas: list[dict]
    ) -> int:
        """Insert or update chunks for a document.

        Args:
            doc_id: Unique identifier for the parent document.
            chunks: List of text chunks.
            embeddings: List of embedding vectors corresponding to the chunks.
            metadatas: List of metadata dicts corresponding to the chunks.

        Returns:
            The number of chunks affected.
        """
        ...

    def search(self, query_embedding: list[float], top_k: int) -> list[dict]:
        """Search for the most similar chunks.

        Args:
            query_embedding: The vector to search with.
            top_k: Maximum number of results to return.

        Returns:
            A list of dicts with keys: `text`, `score` (0.0 to 1.0), and `metadata`.
        """
        ...

    def delete(self, doc_id: str) -> int:
        """Delete all chunks belonging to a document.

        Args:
            doc_id: The identifier of the document to delete.

        Returns:
            The number of chunks deleted.
        """
        ...

    def list_documents(self) -> list[dict]:
        """List all unique indexed documents.

        Returns:
            A list of dicts with document metadata.
        """
        ...


class ChromaVectorStore:
    """VectorStore implementation using ChromaDB via HTTP or ephemeral client."""

    def __init__(self, collection_name: str, client: ClientAPI) -> None:
        """Initialize with an existing Chroma client.

        Args:
            collection_name: Name of the collection to use/create.
            client: Pre-configured chromadb client (HttpClient or EphemeralClient).
        """
        self.collection_name = collection_name
        self.client = client
        # Use cosine distance space
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name, metadata={"hnsw:space": "cosine"}
        )

    def upsert(
        self, doc_id: str, chunks: list[str], embeddings: list[list[float]], metadatas: list[dict]
    ) -> int:
        if not chunks:
            return 0

        # Generate deterministic chunk IDs
        ids = [f"{doc_id}_chunk_{i}" for i in range(len(chunks))]

        # Inject doc_id into each metadata dictionary to group them later
        for meta in metadatas:
            meta["doc_id"] = doc_id

        self.collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=chunks,
            metadatas=metadatas,
        )
        return len(chunks)

    def search(self, query_embedding: list[float], top_k: int) -> list[dict]:
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )

        if not results["documents"] or not results["documents"][0]:
            return []

        out = []
        # results structure is a list of lists because you can pass multiple query_embeddings
        docs = results["documents"][0]
        metas = results["metadatas"][0]
        distances = results["distances"][0]

        for text, meta, dist in zip(docs, metas, distances, strict=False):
            # Convert cosine distance to a similarity score (1 = identical, 0 = opposite)
            score = max(0.0, 1.0 - float(dist))
            out.append({"text": text, "score": score, "metadata": meta})

        return out

    def delete(self, doc_id: str) -> int:
        # We need to find all chunks matching this doc_id to count them, then delete
        result = self.collection.get(
            where={"doc_id": doc_id},
            include=["metadatas"]
        )
        chunk_ids = result.get("ids", [])
        count = len(chunk_ids)

        if count > 0:
            self.collection.delete(ids=chunk_ids)

        return count

    def list_documents(self) -> list[dict]:
        # Getting all metadata to aggregate unique doc_ids
        result = self.collection.get(include=["metadatas"])
        metadatas = result.get("metadatas", [])
        
        docs = {}
        for m in metadatas:
            if not m:
                continue
            did = m.get("doc_id")
            if not did:
                continue
            if did not in docs:
                # Store basic doc-level properties. We assume these are consistent across chunks.
                docs[did] = {k: v for k, v in m.items() if k not in ("chunk_index", "page")}
            
        return list(docs.values())
