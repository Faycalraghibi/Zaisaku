"""Unit tests for zaisaku.retrieval.reranker — Cross-encoder reranking."""

from __future__ import annotations

import pytest

from zaisaku.retrieval.reranker import CrossEncoderReranker, Reranker


class FakeReranker(Reranker):
    """Fake minimal implementation for protocol compliance testing."""

    def rerank(self, query: str, candidates: list[dict], top_k: int) -> list[dict]:
        # Just return the first top_k
        return candidates[:top_k]


class TestRerankerProtocol:
    def test_protocol_compliance(self):
        reranker: Reranker = FakeReranker()
        res = reranker.rerank("q", [{"text": "a"}], 1)
        assert len(res) == 1


@pytest.mark.requires_reranker
class TestCrossEncoderReranker:
    """Tests that require the actual cross-encoder model (auto-skips if unavailable)."""

    @pytest.fixture(scope="class")
    def reranker(self) -> CrossEncoderReranker:
        return CrossEncoderReranker("cross-encoder/ms-marco-MiniLM-L-6-v2")

    def test_reranking_order(self, reranker: CrossEncoderReranker):
        query = "What is the capital of France?"
        candidates = [
            {"text": "Berlin is the capital of Germany."},
            {"text": "Paris is the capital of France, known for the Eiffel Tower."},
            {"text": "The weather is nice today."},
            {"text": "France is a country in Europe."},
        ]

        # Rerank all 4
        results = reranker.rerank(query, candidates, top_k=4)

        assert len(results) == 4
        # The most relevant one should be first
        assert "Paris" in results[0]["text"]
        # Each result should now have a rerank_score
        assert "rerank_score" in results[0]
        assert isinstance(results[0]["rerank_score"], float)

    def test_top_k_slicing(self, reranker: CrossEncoderReranker):
        query = "Apple stock price"
        candidates = [{"text": f"Doc {i}"} for i in range(10)]

        results = reranker.rerank(query, candidates, top_k=3)
        assert len(results) == 3

    def test_empty_candidates(self, reranker: CrossEncoderReranker):
        results = reranker.rerank("Query", [], top_k=5)
        assert results == []
