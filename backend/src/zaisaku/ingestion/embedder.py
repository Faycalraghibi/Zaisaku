"""Provides a Protocol for swappability."""


from __future__ import annotations

import logging
from typing import Protocol, runtime_checkable

# We import sentence_transformers lazily in the implementation class
# to avoid heavy imports simply by importing this module.

logger = logging.getLogger(__name__)


@runtime_checkable
class Embedder(Protocol):
    """Interface for text embedding models."""

    def embed(self, texts: list[str]) -> list[list[float]]:
        ...

    def embed_one(self, text: str) -> list[float]:
        ...


class SentenceTransformerEmbedder:
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> None:
        """Initialize the embedder, downloading the model if necessary.

        Args:
            model_name: HuggingFace model identifier.
        """
        self.model_name = model_name
        self._model = None

    def _get_model(self):
        """Lazy load the model so it doesn't block startup unless used."""
        if self._model is None:
            logger.info(f"Loading embedding model: {self.model_name}")
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.model_name)
        return self._model

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        model = self._get_model()
        # sentence-transformers encode() returns a numpy array or tensor.
        # We convert to a standard python list of floats for downstream JSON/DB compatibility.
        embeddings = model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()

    def embed_one(self, text: str) -> list[float]:
        return self.embed([text])[0]
