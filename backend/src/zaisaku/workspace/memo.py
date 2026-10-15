"""Render workspace reviews and notes as a Markdown memo section."""

from __future__ import annotations

from typing import Any

FLAG_LABELS = {
    "drift": "Language drift",
    "accruals": "Accruals / M-Score",
    "contradictions": "Call vs 10-Q",
    "footnotes": "Footnote disclosures",
}


def _cell(text: str) -> str:
    return text.replace("|", "\\|").replace("\r", " ").replace("\n", " ").strip() or "—"


def render_analyst_review(reviews: list[dict[str, Any]], notes: list[dict[str, Any]]) -> str:
    if not reviews and not notes:
        return ""
    lines = ["", "---", "", "## Analyst review", ""]
    if reviews:
        lines += ["| Flag | Status | Note |", "|---|---|---|"]
        for review in sorted(reviews, key=lambda r: r["flag_id"]):
            label = FLAG_LABELS.get(review["flag_id"], review["flag_id"])
            lines.append(f"| {label} | {review['status']} | {_cell(review.get('note', ''))} |")
        lines.append("")
    if notes:
        lines += ["### Notes", ""]
        for note in notes:
            body = note["body"].strip().replace("\r\n", "\n").replace("\n", "\n  ")
            lines.append(f"- _{note['created_at'][:10]}_ — {body}")
        lines.append("")
    return "\n".join(lines)
