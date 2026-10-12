"""Configurable overlap to preserve context across boundaries."""


from __future__ import annotations

import re


class Chunker:

    @classmethod
    def chunk(cls, text: str, chunk_size: int, overlap: int) -> list[str]:
        if not text.strip():
            return []

        if overlap >= chunk_size:
            raise ValueError("Overlap must be strictly less than chunk_size")

        # Extract pairs of (word, trailing_spaces) to preserve formatting
        # without fragile alternating even/odd parity assumptions.
        pairs: list[tuple[str, str]] = re.findall(r"(\S+)(\s*)", text.strip())
        if not pairs:
            return []

        chunks = []
        step = chunk_size - overlap

        for i in range(0, len(pairs), step):
            window = pairs[i : i + chunk_size]
            chunk_str = "".join(w + s for w, s in window).strip()
            chunks.append(chunk_str)

            if i + chunk_size >= len(pairs):
                break

        return chunks
