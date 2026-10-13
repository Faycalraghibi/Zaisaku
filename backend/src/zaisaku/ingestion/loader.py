
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

    @classmethod
    def load_pages(cls, path: str | Path) -> list[Document]:
        path = Path(path)

        suffix = path.suffix.lower()
        if suffix not in cls.SUPPORTED_EXTENSIONS:
            raise ValueError(f"Unsupported file type: {suffix}")

        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        if suffix == ".pdf":
            doc = fitz.open(str(path))
            pages = []
            total = len(doc)
            for idx, page in enumerate(doc, 1):
                p_text = page.get_text()
                if p_text.strip():
                    pages.append(
                        Document(
                            text=p_text,
                            metadata={
                                "source": str(path),
                                "filetype": "pdf",
                                "page": idx,
                                "pages": total,
                            },
                        )
                    )
            doc.close()
            return pages or [
                Document(
                    text="",
                    metadata={
                        "source": str(path),
                        "filetype": "pdf",
                        "page": 1,
                        "pages": total,
                    },
                )
            ]
        else:
            single = cls.load(path)
            single.metadata["page"] = 1
            return [single]

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
        raw = path.read_text(encoding="utf-8-sig", errors="replace")
        soup = BeautifulSoup(raw, "html.parser")
        text = soup.get_text(separator="\n", strip=True)
        return Document(
            text=text,
            metadata={"source": str(path), "filetype": "html"},
        )

    @staticmethod
    def _load_txt(path: Path) -> Document:
        text = path.read_text(encoding="utf-8-sig", errors="replace")
        return Document(
            text=text,
            metadata={"source": str(path), "filetype": "txt"},
        )
