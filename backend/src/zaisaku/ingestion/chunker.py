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

        # Split by whitespace, preserving the exact whitespace characters
        # so we can rebuild the raw string accurately.
        # re.split(r'(\s+)') returns: [word, space, word, space, ...]
        tokens = re.split(r'(\s+)', text.strip())
        
        # Filter out empty strings that re.split might produce at the ends
        tokens = [t for t in tokens if t]

        # Extract only the word tokens (even indices) for length counting
        # Note: tokens list looks like: ['Word', ' ', 'Word', '\n', 'Word']
        # Thus, len(tokens) // 2 + 1 is roughly the word count.
        
        words = []
        spaces = []
        for i, t in enumerate(tokens):
            if i % 2 == 0:
                words.append(t)
            else:
                spaces.append(t)
        
        # If there are N words, there are N-1 spaces
        if len(spaces) < len(words):
            spaces.append("")

        chunks = []
        step = chunk_size - overlap
        
        for i in range(0, len(words), step):
            chunk_words = words[i : i + chunk_size]
            chunk_spaces = spaces[i : i + chunk_size]
            
            chunk_str = "".join(w + s for w, s in zip(chunk_words, chunk_spaces, strict=False))
            chunks.append(chunk_str.strip())
            
            if i + chunk_size >= len(words):
                break

        return chunks
