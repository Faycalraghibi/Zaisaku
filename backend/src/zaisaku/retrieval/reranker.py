"""Reranker module.

Provides a Protocol for swappability and a default CrossEncoder implementation.
"""

from __future__ import annotations

import logging
from typing import Protocol, runtime_checkable

logger = logging.getLogger(__name__)


@runtime_checkable
class Reranker(Protocol):
    """Interface for document rerankers."""

    def rerank(self, query: str, candidates: list[dict], top_k: int) -> list[dict]:
        """Rescore and sort a list of candidate chunks based on the query.

        Args:
            query: The user's search query.
            candidates: List of chunk dictionaries (must contain 'text' key).
            top_k: Maximum number of reranked results to return.

        Returns:
            The sorted list of candidate dicts, sliced to top_k,
            with an added 'rerank_score' float field.
        """
        ...


class CrossEncoderReranker:
    """Reranker implementation using sentence-transformers CrossEncoder."""

    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2") -> None:
        """Initialize the reranker, downloading the model if necessary.

        Args:
            model_name: HuggingFace model identifier.
        """
        self.model_name = model_name
        self._model = None

    def _get_model(self):
        """Lazy load the model so it doesn't block startup unless used."""
        if self._model is None:
            logger.info(f"Loading reranker model: {self.model_name}")
            from sentence_transformers import CrossEncoder
            self._model = CrossEncoder(self.model_name)
        return self._model

    def rerank(self, query: str, candidates: list[dict], top_k: int) -> list[dict]:
        """Rescore and sort candidates."""
        if not candidates:
            return []

        # Prepare pairs for the cross-encoder: [(query, doc1), (query, doc2), ...]
        texts = [doc["text"] for doc in candidates]
        pairs = [[query, text] for text in texts]

        model = self._get_model()
        scores = model.predict(pairs)

        # Inject the new scores into the candidate dicts
        # (We make shallow copies so we don't mutate the caller's objects)
        scored_candidates = []
        for doc, score in zip(candidates, scores, strict=False):
            new_doc = dict(doc)
            new_doc["rerank_score"] = float(score)
            scored_candidates.append(new_doc)

        # Sort descending by the new rerank_score
        scored_candidates.sort(key=lambda d: d["rerank_score"], reverse=True)

        return scored_candidates[:top_k]
