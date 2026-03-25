"""Unit tests for zaisaku.ingestion.chunker — Sliding window chunking."""

from zaisaku.ingestion.chunker import Chunker


class TestChunker:
    """Sliding window chunker tests."""

    def test_empty_string(self):
        chunks = Chunker.chunk("", chunk_size=50, overlap=10)
        assert chunks == []

    def test_short_text_single_chunk(self):
        text = "This is a very short text."
        chunks = Chunker.chunk(text, chunk_size=50, overlap=10)
        assert len(chunks) == 1
        assert chunks[0] == text

    def test_exact_chunk_size(self):
        # 10 words
        text = "One two three four five six seven eight nine ten."
        chunks = Chunker.chunk(text, chunk_size=10, overlap=2)
        assert len(chunks) == 1
        assert chunks[0] == text

    def test_sliding_window_overlap(self):
        # 10 words
        text = "One two three four five six seven eight nine ten."
        # Size 6, overlap 2
        # Expected:
        # C1: One two three four five six
        # C2: five six seven eight nine ten
        chunks = Chunker.chunk(text, chunk_size=6, overlap=2)
        assert len(chunks) == 2
        assert chunks[0] == "One two three four five six"
        assert chunks[1] == "five six seven eight nine ten."
        
    def test_zero_overlap(self):
        text = "One two three four"
        chunks = Chunker.chunk(text, chunk_size=2, overlap=0)
        assert len(chunks) == 2
        assert chunks[0] == "One two"
        assert chunks[1] == "three four"

    def test_preserves_spacing(self):
        text = "Space   between   words."
        chunks = Chunker.chunk(text, chunk_size=5, overlap=0)
        assert chunks[0] == text
