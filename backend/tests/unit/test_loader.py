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

    def test_loads_txt_with_bom_and_non_utf8(self, tmp_path: Path):
        file = tmp_path / "bom_encoded.txt"
        # Write UTF-8 BOM followed by invalid UTF-8 bytes
        file.write_bytes(b"\xef\xbb\xbfFinancial Report \xff\xfe\x99")
        doc = DocumentLoader.load(file)
        assert "Financial Report" in doc.text
        assert not doc.text.startswith("\ufeff")


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

    def test_loads_html_with_bom(self, tmp_path: Path):
        file = tmp_path / "bom_encoded.html"
        file.write_bytes(b"\xef\xbb\xbf<html><body><p>Quarterly Report</p></body></html>")
        doc = DocumentLoader.load(file)
        assert "Quarterly Report" in doc.text
        assert not doc.text.startswith("\ufeff")


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


class TestDocumentLoaderPages:
    """Loading documents with page awareness."""

    def test_load_pages_pdf(self):
        pages = DocumentLoader.load_pages(FIXTURES / "sample.pdf")
        assert len(pages) >= 1
        for p in pages:
            assert "page" in p.metadata
            assert p.metadata["page"] >= 1
            assert p.metadata["filetype"] == "pdf"

    def test_load_pages_txt(self):
        pages = DocumentLoader.load_pages(FIXTURES / "sample.txt")
        assert len(pages) == 1
        assert pages[0].metadata["page"] == 1
