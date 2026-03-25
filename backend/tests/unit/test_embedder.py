"""Unit tests for zaisaku.ingestion.embedder — Vector embeddings."""

from __future__ import annotations

import pytest
import numpy as np

from zaisaku.ingestion.embedder import Embedder, SentenceTransformerEmbedder


class FakeEmbedder(Embedder):
    """Fake minimal implementation for protocol compliance testing."""

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [[0.1, 0.2] for _ in texts]

    def embed_one(self, text: str) -> list[float]:
        return [0.1, 0.2]


class TestEmbedderProtocol:
    """Ensure the Protocol and basic abstraction works without loading models."""

    def test_protocol_compliance(self):
        # Python type checkers ensure this, but we test instantiation
        embedder: Embedder = FakeEmbedder()
        assert embedder.embed(["test"]) == [[0.1, 0.2]]
        assert embedder.embed_one("test") == [0.1, 0.2]


@pytest.mark.requires_embedder
class TestSentenceTransformerEmbedder:
    """Tests that require the actual sentence-transformers model (auto-skips if unavailable)."""

    @pytest.fixture(scope="class")
    def embedder(self) -> SentenceTransformerEmbedder:
        return SentenceTransformerEmbedder("sentence-transformers/all-MiniLM-L6-v2")

    def test_embed_one_dimensionality(self, embedder: SentenceTransformerEmbedder):
        vec = embedder.embed_one("Hello world")
        assert len(vec) == 384
        assert isinstance(vec[0], float)

    def test_embed_batch_consistency(self, embedder: SentenceTransformerEmbedder):
        texts = ["First line", "Second line", "Third line"]
        vecs = embedder.embed(texts)
        assert len(vecs) == 3
        assert len(vecs[0]) == 384

        # Verify that embedding one by one matches the batch
        single_vec = embedder.embed_one(texts[0])
        assert np.allclose(vecs[0], single_vec, atol=1e-5)

    def test_cosine_similarity_ordering(self, embedder: SentenceTransformerEmbedder):
        """Two similar sentences should have higher similarity than completely different ones."""
        query = "A cat sits on the mat."
        similar = "The feline is resting on the rug."
        different = "Nuclear physics is a complex subject."

        v_q, v_s, v_d = embedder.embed([query, similar, different])

        # Compute cosine similarity
        def cos_sim(a, b):
            return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

        sim_similar = cos_sim(v_q, v_s)
        sim_different = cos_sim(v_q, v_d)

        assert sim_similar > sim_different
        assert sim_similar > 0.5  # Expect reasonable correlation
