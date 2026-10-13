
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
                try:
                    tabs = page.find_tables()
                    if tabs and tabs.tables:
                        table_mds = [t.to_markdown() for t in tabs.tables if t.to_markdown().strip()]
                        if table_mds:
                            p_text = f"{p_text}\n\n" + "\n\n".join(table_mds)
                except Exception:
                    pass

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
    def _table_to_markdown(table_tag) -> str:
        rows = table_tag.find_all("tr")
        if not rows:
            return ""

        table_data = []
        for tr in rows:
            cells = [
                c.get_text(strip=True).replace("\n", " ").replace("|", "/")
                for c in tr.find_all(["th", "td"])
            ]
            if cells:
                table_data.append(cells)

        if not table_data:
            return ""

        max_cols = max(len(r) for r in table_data)
        normalized = [r + [""] * (max_cols - len(r)) for r in table_data]

        header = normalized[0]
        md_lines = ["\n| " + " | ".join(header) + " |"]
        md_lines.append("| " + " | ".join(["---"] * max_cols) + " |")
        for row in normalized[1:]:
            md_lines.append("| " + " | ".join(row) + " |")
        md_lines.append("\n")
        return "\n".join(md_lines)

    @staticmethod
    def _load_pdf(path: Path) -> Document:
        doc = fitz.open(str(path))
        page_texts = []
        for page in doc:
            t = page.get_text()
            try:
                tabs = page.find_tables()
                if tabs and tabs.tables:
                    table_mds = [tab.to_markdown() for tab in tabs.tables if tab.to_markdown().strip()]
                    if table_mds:
                        t = f"{t}\n\n" + "\n\n".join(table_mds)
            except Exception:
                pass
            page_texts.append(t)

        text = "\n".join(page_texts)
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
        for table in soup.find_all("table"):
            md = DocumentLoader._table_to_markdown(table)
            if md:
                table.replace_with(soup.new_string(md))
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
