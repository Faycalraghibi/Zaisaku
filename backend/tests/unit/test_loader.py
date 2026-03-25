"""Unit tests for zaisaku.ingestion.loader — Document loading and parsing."""

from __future__ import annotations

from pathlib import Path

import pytest

from zaisaku.ingestion.loader import DocumentLoader
from zaisaku.models import Document

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"


class TestDocumentLoaderTXT:
    """Loading plain text files."""

    def test_loads_txt_content(self):
        doc = DocumentLoader.load(FIXTURES / "sample.txt")
        assert isinstance(doc, Document)
        assert "financial report" in doc.text.lower()

    def test_txt_metadata_has_source(self):
        doc = DocumentLoader.load(FIXTURES / "sample.txt")
        assert "source" in doc.metadata
        assert doc.metadata["source"].endswith("sample.txt")

    def test_txt_metadata_has_filetype(self):
        doc = DocumentLoader.load(FIXTURES / "sample.txt")
        assert doc.metadata["filetype"] == "txt"


class TestDocumentLoaderHTML:
    """Loading HTML files — should strip tags and return clean text."""

    def test_loads_html_content(self):
        doc = DocumentLoader.load(FIXTURES / "sample.html")
        assert isinstance(doc, Document)
        assert "quarterly earnings" in doc.text.lower()

    def test_html_strips_tags(self):
        doc = DocumentLoader.load(FIXTURES / "sample.html")
        assert "<p>" not in doc.text
        assert "<html>" not in doc.text

    def test_html_metadata_has_filetype(self):
        doc = DocumentLoader.load(FIXTURES / "sample.html")
        assert doc.metadata["filetype"] == "html"


class TestDocumentLoaderPDF:
    """Loading PDF files."""

    def test_loads_pdf_content(self):
        doc = DocumentLoader.load(FIXTURES / "sample.pdf")
        assert isinstance(doc, Document)
        assert len(doc.text) > 0

    def test_pdf_metadata_has_filetype(self):
        doc = DocumentLoader.load(FIXTURES / "sample.pdf")
        assert doc.metadata["filetype"] == "pdf"

    def test_pdf_metadata_has_page_count(self):
        doc = DocumentLoader.load(FIXTURES / "sample.pdf")
        assert "pages" in doc.metadata
        assert doc.metadata["pages"] >= 1


class TestDocumentLoaderErrors:
    """Edge cases and error handling."""

    def test_unsupported_extension_raises(self):
        with pytest.raises(ValueError, match="Unsupported file type"):
            DocumentLoader.load(FIXTURES / "fake.docx")

    def test_nonexistent_file_raises(self):
        with pytest.raises(FileNotFoundError):
            DocumentLoader.load(FIXTURES / "does_not_exist.txt")

    def test_empty_text_file(self, tmp_path: Path):
        empty = tmp_path / "empty.txt"
        empty.write_text("")
        doc = DocumentLoader.load(empty)
        assert doc.text == ""
