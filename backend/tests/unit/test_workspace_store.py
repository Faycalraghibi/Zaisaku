from __future__ import annotations

import pytest

from zaisaku.workspace.store import WorkspaceStore


@pytest.fixture
def store():
    s = WorkspaceStore(":memory:")
    yield s
    s.close()


def test_watchlist_add_is_idempotent_and_listed(store):
    first = store.add_to_watchlist("NVDA")
    again = store.add_to_watchlist("NVDA")
    assert first == again
    store.add_to_watchlist("SMCI")
    assert [r["ticker"] for r in store.list_watchlist()] == ["NVDA", "SMCI"]


def test_watchlist_remove_reports_whether_it_existed(store):
    store.add_to_watchlist("NVDA")
    assert store.remove_from_watchlist("NVDA") is True
    assert store.remove_from_watchlist("NVDA") is False
    assert store.list_watchlist() == []


def test_screens_round_trip_criteria(store):
    created = store.create_screen("High risk", {"ffi_min": 50, "critical_only": True})
    assert created["name"] == "High risk"
    assert store.list_screens() == [created]
    assert created["criteria"] == {"ffi_min": 50, "critical_only": True}
    assert store.delete_screen(created["id"]) is True
    assert store.delete_screen(created["id"]) is False


def test_flag_review_upserts(store):
    store.set_flag_review("SMCI", "drift", "escalated", "Ask IR")
    updated = store.set_flag_review("SMCI", "drift", "reviewed", "Answered")
    assert updated["status"] == "reviewed"
    assert updated["note"] == "Answered"
    assert len(store.list_flag_reviews("SMCI")) == 1
    store.set_flag_review("NVDA", "footnotes", "open", "")
    assert {r["ticker"] for r in store.list_all_flag_reviews()} == {"SMCI", "NVDA"}


def test_flag_review_rejects_unknown_status(store):
    with pytest.raises(ValueError):
        store.set_flag_review("SMCI", "drift", "maybe", "")


def test_notes_are_scoped_by_ticker_and_newest_first(store):
    a = store.add_note("NVDA", "first")
    b = store.add_note("NVDA", "second")
    store.add_note("SMCI", "other")
    assert [n["id"] for n in store.list_notes("NVDA")] == [b["id"], a["id"]]
    assert store.update_note("SMCI", a["id"], "nope") is None
    edited = store.update_note("NVDA", a["id"], "first, edited")
    assert edited["body"] == "first, edited"
    assert store.delete_note("SMCI", a["id"]) is False
    assert store.delete_note("NVDA", a["id"]) is True
    assert [n["body"] for n in store.list_notes("NVDA")] == ["second"]


def test_data_persists_across_reopen(tmp_path):
    path = tmp_path / "nested" / "workspace.db"
    s1 = WorkspaceStore(path)
    s1.add_to_watchlist("AAPL")
    s1.add_note("AAPL", "kept")
    s1.close()
    s2 = WorkspaceStore(path)
    assert [r["ticker"] for r in s2.list_watchlist()] == ["AAPL"]
    assert s2.list_notes("AAPL")[0]["body"] == "kept"
    s2.close()
