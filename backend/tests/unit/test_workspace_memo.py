from __future__ import annotations

from zaisaku.workspace.memo import render_analyst_review


def test_empty_workspace_renders_nothing():
    assert render_analyst_review([], []) == ""


def test_reviews_table_and_notes():
    md = render_analyst_review(
        [{"flag_id": "drift", "status": "escalated", "note": "Ask IR | follow up\nnext week"}],
        [{"body": "Auditor change\nmatters", "created_at": "2026-10-15T10:00:00+00:00"}],
    )
    assert "## Analyst review" in md
    assert "| Language drift | escalated | Ask IR \\| follow up next week |" in md
    assert "### Notes" in md
    assert "- _2026-10-15_ — Auditor change\n  matters" in md


def test_unknown_flag_id_falls_back_to_id_and_blank_note_to_dash():
    md = render_analyst_review([{"flag_id": "custom", "status": "open", "note": ""}], [])
    assert "| custom | open | — |" in md
