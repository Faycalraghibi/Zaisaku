"""Unit tests for zaisaku.retrieval.store — ChromaDB Vector Store."""

from __future__ import annotations

import chromadb
import pytest

from zaisaku.retrieval.store import ChromaVectorStore, VectorStore


class FakeVectorStore(VectorStore):
    """Fake minimal implementation for protocol compliance testing."""

    def upsert(self, doc_id, chunks, embeddings, metadatas):
        return len(chunks)

    def search(self, query_embedding, top_k):
        return [{"text": "test", "score": 0.9, "metadata": {}}]

    def delete(self, doc_id):
        return 1
        
    def list_documents(self):
        return [{"doc_id": "doc1"}]


class TestVectorStoreProtocol:
    def test_protocol_compliance(self):
        store: VectorStore = FakeVectorStore()
        assert store.upsert("d1", ["a"], [[0.1]], [{}]) == 1
        assert store.search([0.1], 5)[0]["score"] == 0.9
        assert store.delete("d1") == 1
        assert len(store.list_documents()) == 1


class TestChromaVectorStore:
    """Tests using an ephemeral, in-memory ChromaDB client."""

    @pytest.fixture
    def store(self, request):
        # EphemeralClient runs completely in-memory, no external service needed
        client = chromadb.EphemeralClient()
        collection_name = f"test_{request.node.name}"
        return ChromaVectorStore(collection_name=collection_name, client=client)

    def test_upsert_and_search(self, store: ChromaVectorStore):
        doc_id = "doc123"
        chunks = ["chunk one", "chunk two"]
        embeddings = [[0.1, 0.2, 0.3], [0.9, 0.8, 0.7]]
        metadatas = [{"source": "test.txt", "type": "A"}, {"source": "test.txt", "type": "B"}]

        # Upsert
        count = store.upsert(doc_id, chunks, embeddings, metadatas)
        assert count == 2

        # Search for exact match of the first chunk
        results = store.search(query_embedding=[0.11, 0.2, 0.3], top_k=1)
        
        assert len(results) == 1
        assert results[0]["text"] == "chunk one"
        # Score should be a float near 1.0 (since it's a very similar vector)
        assert isinstance(results[0]["score"], float)
        assert results[0]["score"] > 0.8
        assert results[0]["metadata"]["doc_id"] == "doc123"
        assert results[0]["metadata"]["type"] == "A"

    def test_delete(self, store: ChromaVectorStore):
        store.upsert("d1", ["a", "b"], [[0.1, 0.1, 0.1], [0.2, 0.2, 0.2]], [{"m": 1}, {"m": 2}])
        store.upsert("d2", ["c"], [[0.3, 0.3, 0.3]], [{"m": 3}])

        # Delete d1
        deleted = store.delete("d1")
        assert deleted == 2

        # Verify d1 is gone
        res = store.search([0.1, 0.1, 0.1], top_k=5)
        texts = [r["text"] for r in res]
        assert "a" not in texts
        assert "c" in texts

    def test_list_documents(self, store: ChromaVectorStore):
        store.upsert("d1", ["a", "b"], [[0.1, 0.1, 0.1], [0.2, 0.2, 0.2]], [{"title": "T1"}, {"title": "T1"}])
        store.upsert("d2", ["c"], [[0.3, 0.3, 0.3]], [{"title": "T2"}])

        docs = store.list_documents()
        assert len(docs) == 2
        
        # Exact order is not guaranteed, but both doc_ids should be present
        doc_ids = {d.get("doc_id") for d in docs}
        assert doc_ids == {"d1", "d2"}

    def test_empty_search_returns_empty_list(self, store: ChromaVectorStore):
        results = store.search([0.1, 0.2, 0.3], top_k=5)
        assert results == []

    def test_empty_upsert_returns_zero(self, store: ChromaVectorStore):
        assert store.upsert("empty", [], [], []) == 0
