"""Extracts and cleans standard sections from SEC 10-K and 10-Q filings."""

from __future__ import annotations

import re


class SectionExtractor:
    """Extracts standard SEC items (Risk Factors, MD&A, Legal Proceedings) from raw filing text."""

    # Patterns matching start of standard items (case-insensitive)
    PATTERNS = {
        "item_1a_risk_factors": (
            r"(?:item\s+1a[\.\:\s\-\—]+risk\s+factors)",
            r"(?:item\s+1b[\.\:\s\-\—]+unresolved|item\s+2[\.\:\s\-\—]+properties|part\s+ii|item\s+1b)",
        ),
        "item_7_mda": (
            r"(?:item\s+7[\.\:\s\-\—]+management(?:[\'’]s)?\s+discussion\s+and\s+analysis)",
            r"(?:item\s+7a[\.\:\s\-\—]+quantitative|item\s+8[\.\:\s\-\—]+financial\s+statements)",
        ),
        "item_3_legal": (
            r"(?:item\s+3[\.\:\s\-\—]+legal\s+proceedings)",
            r"(?:item\s+4[\.\:\s\-\—]+mine\s+safety|item\s+4[\.\:\s\-\—]+[a-z]+|part\s+ii)",
        ),
    }

    @staticmethod
    def clean_boilerplate(text: str) -> str:
        """Removes recurring page numbers, dates, and whitespace noise from filing text."""
        if not text:
            return ""
        # Remove repeated page number lines like "Page 45", "45 of 120"
        text = re.sub(r"(?im)^\s*(?:page\s+)?\d+(?:\s+of\s+\d+)?\s*$", "", text)
        # Remove multiple newlines
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    @classmethod
    def extract_section(cls, full_text: str, section_key: str) -> str:
        """Extract a specific section by key (e.g. 'item_1a_risk_factors').

        If markers cannot be cleanly isolated or text is short, returns the best-effort extracted block.
        """
        if section_key not in cls.PATTERNS or not full_text:
            return ""

        start_pat, end_pat = cls.PATTERNS[section_key]

        start_matches = list(re.finditer(start_pat, full_text, flags=re.IGNORECASE))
        if not start_matches:
            return ""

        # Avoid Table of Contents: pick the match that is followed by the largest content block
        candidates: list[str] = []
        for match in start_matches:
            start_pos = match.end()
            remainder = full_text[start_pos:]
            end_match = re.search(end_pat, remainder, flags=re.IGNORECASE)
            extracted = remainder[: end_match.start()] if end_match else remainder[:80000]
            cleaned = cls.clean_boilerplate(extracted)
            if len(cleaned) >= 20:
                candidates.append(cleaned)

        if not candidates:
            # Fall back to first match after start, respecting end pattern if found
            remainder = full_text[start_matches[-1].end():]
            end_match = re.search(end_pat, remainder, flags=re.IGNORECASE)
            fallback = remainder[: end_match.start()] if end_match else remainder[:20000]
            return cls.clean_boilerplate(fallback)

        # Return the longest candidate block (the real body section rather than TOC entry)
        return max(candidates, key=len)

    @classmethod
    def extract_all(cls, full_text: str) -> dict[str, str]:
        """Extract all standard sections from a filing."""
        result: dict[str, str] = {}
        for key in cls.PATTERNS:
            content = cls.extract_section(full_text, key)
            if content:
                result[key] = content
        return result
