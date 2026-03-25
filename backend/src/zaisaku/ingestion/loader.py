"""Document loader — parses PDF, HTML, and TXT into Document models.

Supported formats:
- .pdf  → PyMuPDF (fitz)
- .html → BeautifulSoup
- .txt  → plain read
"""

from __future__ import annotations

from pathlib import Path

import fitz  # PyMuPDF
from bs4 import BeautifulSoup

from zaisaku.models import Document


class DocumentLoader:
    """Stateless loader — all methods are classmethods."""

    SUPPORTED_EXTENSIONS = {".pdf", ".html", ".htm", ".txt"}

    @classmethod
    def load(cls, path: str | Path) -> Document:
        """Load a document from *path* and return a ``Document``.

        Raises:
            FileNotFoundError: if *path* does not exist.
            ValueError: if the file extension is not supported.
        """
        path = Path(path)

        suffix = path.suffix.lower()
        if suffix not in cls.SUPPORTED_EXTENSIONS:
            raise ValueError(f"Unsupported file type: {suffix}")

        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        loader = {
            ".pdf": cls._load_pdf,
            ".html": cls._load_html,
            ".htm": cls._load_html,
            ".txt": cls._load_txt,
        }[suffix]

        return loader(path)

    # ── Private loaders ──────────────────────────

    @staticmethod
    def _load_pdf(path: Path) -> Document:
        doc = fitz.open(str(path))
        text = "\n".join(page.get_text() for page in doc)
        metadata = {
            "source": str(path),
            "filetype": "pdf",
            "pages": len(doc),
        }
        doc.close()
        return Document(text=text, metadata=metadata)

    @staticmethod
    def _load_html(path: Path) -> Document:
        raw = path.read_text(encoding="utf-8")
        soup = BeautifulSoup(raw, "html.parser")
        text = soup.get_text(separator="\n", strip=True)
        return Document(
            text=text,
            metadata={"source": str(path), "filetype": "html"},
        )

    @staticmethod
    def _load_txt(path: Path) -> Document:
        text = path.read_text(encoding="utf-8")
        return Document(
            text=text,
            metadata={"source": str(path), "filetype": "txt"},
        )
