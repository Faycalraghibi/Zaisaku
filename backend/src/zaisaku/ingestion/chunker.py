"""Sliding window chunker for raw text.

Splits text into token-sized chunks (currently word-based for simplicity)
with a configurable overlap to preserve context across boundaries.
"""

from __future__ import annotations

import re


class Chunker:
    """Stateless chunker for splitting text into overlapping chunks."""

    @classmethod
    def chunk(cls, text: str, chunk_size: int, overlap: int) -> list[str]:
        """Split *text* into chunks of up to *chunk_size* words, overlapping by *overlap*.

        Args:
            text: Raw text to split.
            chunk_size: Maximum number of words (tokens) per chunk.
            overlap: Number of words to overlap between consecutive chunks.

        Returns:
            List of text chunks.
        """
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
            # i is the start index in the `words`list
            chunk_words = words[i : i + chunk_size]
            chunk_spaces = spaces[i : i + chunk_size]
            
            # Reconstruct the string for this block
            chunk_str = "".join(w + s for w, s in zip(chunk_words, chunk_spaces))
            chunks.append(chunk_str.strip())
            
            # If we've reached the end of the text, stop
            if i + chunk_size >= len(words):
                break

        return chunks
