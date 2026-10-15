# Analyst Workspace Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a watchlist, flag triage with notes, a screener, compare, and keyboard shortcuts, backed by a SQLite workspace API. Spec: `docs/superpowers/specs/2026-10-15-analyst-workspace-design.md`.

**Architecture:** A FastAPI `workspace` router over a stdlib-`sqlite3` `WorkspaceStore` (a singleton dependency; tests override it with `:memory:`). The frontend uses a fetch client plus singleton composables with optimistic writes, rollback, and toasts. Pure `.js` utils (csv, portfolio, screen, compare, shortcut matcher) are unit tested. New portfolio views reuse the `components/ui` primitives.

**Tech Stack:** FastAPI, Pydantic 2, sqlite3, pytest; Vue 3.5, Tailwind v4 tokens, Vitest 5.

**Conventions:**
- Each `**File:** \`path\`` line is followed by that file's complete content. Backend paths are relative to `backend/`, frontend paths to `frontend/`.
- Files are written with LF line endings.

**Per-PR ship loop:**

```bash
git checkout main && git pull --ff-only && git checkout -b <branch>
(cd backend && pytest tests/unit -q && ruff check src tests)   # backend PRs
(cd frontend && npm test && npm run build)
git push -u origin <branch>; gh pr create ...; gh pr checks --watch
gh pr merge --squash --delete-branch    # only when all checks are green
```

---

## PR 1 — `feat/workspace-api`

### Task 1.1: Store (TDD)

**File:** `backend/tests/unit/test_workspace_store.py`
```python
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
```

- [ ] Run `pytest tests/unit/test_workspace_store.py -q` → FAIL (module missing).

**File:** `backend/src/zaisaku/workspace/__init__.py`
```python
"""Analyst workspace: watchlist, saved screens, flag reviews, and notes."""
```

**File:** `backend/src/zaisaku/workspace/store.py`
```python
"""SQLite-backed analyst workspace store."""

from __future__ import annotations

import json
import sqlite3
import threading
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

FLAG_STATUSES = ("open", "reviewed", "escalated", "dismissed")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS watchlist (
    ticker TEXT PRIMARY KEY,
    added_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS screens (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    criteria TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS flag_reviews (
    ticker TEXT NOT NULL,
    flag_id TEXT NOT NULL,
    status TEXT NOT NULL,
    note TEXT NOT NULL DEFAULT '',
    updated_at TEXT NOT NULL,
    PRIMARY KEY (ticker, flag_id)
);
CREATE TABLE IF NOT EXISTS notes (
    id TEXT PRIMARY KEY,
    ticker TEXT NOT NULL,
    body TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS notes_by_ticker ON notes (ticker);
"""


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


class WorkspaceStore:
    """Thread-safe wrapper around a single SQLite connection."""

    def __init__(self, db_path: str | Path) -> None:
        self.db_path = str(db_path)
        if self.db_path != ":memory:":
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        with self._lock:
            self._conn.executescript(_SCHEMA)
            self._conn.commit()

    def close(self) -> None:
        with self._lock:
            self._conn.close()

    def _query(self, sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
        with self._lock:
            return [dict(row) for row in self._conn.execute(sql, params).fetchall()]

    def _write(self, sql: str, params: tuple[Any, ...] = ()) -> int:
        with self._lock:
            cursor = self._conn.execute(sql, params)
            self._conn.commit()
            return cursor.rowcount

    # --- Watchlist -------------------------------------------------------
    def list_watchlist(self) -> list[dict[str, Any]]:
        return self._query("SELECT ticker, added_at FROM watchlist ORDER BY added_at, rowid")

    def add_to_watchlist(self, ticker: str) -> dict[str, Any]:
        self._write("INSERT OR IGNORE INTO watchlist (ticker, added_at) VALUES (?, ?)", (ticker, _now()))
        return self._query("SELECT ticker, added_at FROM watchlist WHERE ticker = ?", (ticker,))[0]

    def remove_from_watchlist(self, ticker: str) -> bool:
        return self._write("DELETE FROM watchlist WHERE ticker = ?", (ticker,)) > 0

    # --- Saved screens ---------------------------------------------------
    @staticmethod
    def _screen(row: dict[str, Any]) -> dict[str, Any]:
        return {**row, "criteria": json.loads(row["criteria"])}

    def list_screens(self) -> list[dict[str, Any]]:
        rows = self._query("SELECT id, name, criteria, created_at FROM screens ORDER BY created_at, rowid")
        return [self._screen(r) for r in rows]

    def create_screen(self, name: str, criteria: dict[str, Any]) -> dict[str, Any]:
        screen_id = uuid.uuid4().hex
        self._write(
            "INSERT INTO screens (id, name, criteria, created_at) VALUES (?, ?, ?, ?)",
            (screen_id, name, json.dumps(criteria, sort_keys=True), _now()),
        )
        rows = self._query("SELECT id, name, criteria, created_at FROM screens WHERE id = ?", (screen_id,))
        return self._screen(rows[0])

    def delete_screen(self, screen_id: str) -> bool:
        return self._write("DELETE FROM screens WHERE id = ?", (screen_id,)) > 0

    # --- Flag reviews ----------------------------------------------------
    _REVIEW_COLUMNS = "ticker, flag_id, status, note, updated_at"

    def list_all_flag_reviews(self) -> list[dict[str, Any]]:
        return self._query(f"SELECT {self._REVIEW_COLUMNS} FROM flag_reviews ORDER BY ticker, flag_id")

    def list_flag_reviews(self, ticker: str) -> list[dict[str, Any]]:
        return self._query(
            f"SELECT {self._REVIEW_COLUMNS} FROM flag_reviews WHERE ticker = ? ORDER BY flag_id", (ticker,)
        )

    def set_flag_review(self, ticker: str, flag_id: str, status: str, note: str) -> dict[str, Any]:
        if status not in FLAG_STATUSES:
            raise ValueError(f"Unknown flag status: {status}")
        self._write(
            """
            INSERT INTO flag_reviews (ticker, flag_id, status, note, updated_at) VALUES (?, ?, ?, ?, ?)
            ON CONFLICT (ticker, flag_id) DO UPDATE SET
                status = excluded.status, note = excluded.note, updated_at = excluded.updated_at
            """,
            (ticker, flag_id, status, note, _now()),
        )
        return self._query(
            f"SELECT {self._REVIEW_COLUMNS} FROM flag_reviews WHERE ticker = ? AND flag_id = ?", (ticker, flag_id)
        )[0]

    # --- Notes -----------------------------------------------------------
    _NOTE_COLUMNS = "id, ticker, body, created_at, updated_at"

    def list_notes(self, ticker: str) -> list[dict[str, Any]]:
        return self._query(
            f"SELECT {self._NOTE_COLUMNS} FROM notes WHERE ticker = ? ORDER BY created_at DESC, rowid DESC", (ticker,)
        )

    def add_note(self, ticker: str, body: str) -> dict[str, Any]:
        note_id = uuid.uuid4().hex
        now = _now()
        self._write(
            "INSERT INTO notes (id, ticker, body, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
            (note_id, ticker, body, now, now),
        )
        return self._query(f"SELECT {self._NOTE_COLUMNS} FROM notes WHERE id = ?", (note_id,))[0]

    def update_note(self, ticker: str, note_id: str, body: str) -> dict[str, Any] | None:
        changed = self._write(
            "UPDATE notes SET body = ?, updated_at = ? WHERE id = ? AND ticker = ?", (body, _now(), note_id, ticker)
        )
        if not changed:
            return None
        return self._query(f"SELECT {self._NOTE_COLUMNS} FROM notes WHERE id = ?", (note_id,))[0]

    def delete_note(self, ticker: str, note_id: str) -> bool:
        return self._write("DELETE FROM notes WHERE id = ? AND ticker = ?", (note_id, ticker)) > 0
```

- [ ] Run → PASS.

### Task 1.2: Memo section (TDD)

**File:** `backend/tests/unit/test_workspace_memo.py`
```python
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
```

**File:** `backend/src/zaisaku/workspace/memo.py`
```python
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
```

### Task 1.3: Config, dependency, router, memo wiring

- [ ] `config.py`: add `workspace_db_path: str = ""  # empty → {upload_dir}/workspace.db` after `upload_dir`.
- [ ] `api/dependencies.py`: add

```python
from pathlib import Path

from zaisaku.workspace.store import WorkspaceStore

_workspace_store_instance: WorkspaceStore | None = None


def get_workspace_store(settings: Annotated[Settings, Depends(get_settings)]) -> WorkspaceStore:
    global _workspace_store_instance
    if _workspace_store_instance is None:
        path = settings.workspace_db_path or str(Path(settings.upload_dir) / "workspace.db")
        _workspace_store_instance = WorkspaceStore(path)
    return _workspace_store_instance
```

  and `WorkspaceDep = Annotated[WorkspaceStore, Depends(get_workspace_store)]` in the alias block.

**File:** `backend/src/zaisaku/api/routers/workspace.py`
```python
"""Analyst workspace API: watchlist, saved screens, flag reviews, and notes."""

from __future__ import annotations

import re
from typing import Literal

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, ConfigDict, Field, field_validator

from zaisaku.api.dependencies import WorkspaceDep

router = APIRouter(prefix="/workspace", tags=["workspace"])

_TICKER_RE = re.compile(r"^[A-Z0-9.\-]{1,10}$")
_FLAG_ID_RE = re.compile(r"^[a-z0-9_-]{1,40}$")

FlagStatus = Literal["open", "reviewed", "escalated", "dismissed"]


def _ticker(raw: str) -> str:
    ticker = raw.strip().upper()
    if not _TICKER_RE.fullmatch(ticker):
        raise HTTPException(status_code=422, detail=f"Invalid ticker: {raw!r}")
    return ticker


def _flag_id(raw: str) -> str:
    if not _FLAG_ID_RE.fullmatch(raw):
        raise HTTPException(status_code=422, detail=f"Invalid flag id: {raw!r}")
    return raw


class WatchlistEntry(BaseModel):
    ticker: str
    added_at: str


class ScreenCriteria(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ffi_min: float | None = Field(default=None, ge=0, le=100)
    ffi_max: float | None = Field(default=None, ge=0, le=100)
    mscore_above: float | None = Field(default=None, ge=-10, le=10)
    drift_min: float | None = Field(default=None, ge=0, le=100)
    sector: str | None = Field(default=None, max_length=120)
    kind: Literal["all", "company", "index"] = "all"
    critical_only: bool = False


class ScreenCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    criteria: ScreenCriteria

    @field_validator("name")
    @classmethod
    def _strip_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("name must not be blank")
        return value


class Screen(BaseModel):
    id: str
    name: str
    criteria: ScreenCriteria
    created_at: str


class FlagReviewUpdate(BaseModel):
    status: FlagStatus
    note: str = Field(default="", max_length=5000)


class FlagReview(BaseModel):
    ticker: str
    flag_id: str
    status: FlagStatus
    note: str
    updated_at: str


class NoteBody(BaseModel):
    body: str = Field(min_length=1, max_length=5000)

    @field_validator("body")
    @classmethod
    def _not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("body must not be blank")
        return value


class Note(BaseModel):
    id: str
    ticker: str
    body: str
    created_at: str
    updated_at: str


# --- Watchlist -------------------------------------------------------------
@router.get("/watchlist", response_model=list[WatchlistEntry])
def list_watchlist(store: WorkspaceDep):
    return store.list_watchlist()


@router.put("/watchlist/{ticker}", response_model=WatchlistEntry)
def add_to_watchlist(ticker: str, store: WorkspaceDep):
    return store.add_to_watchlist(_ticker(ticker))


@router.delete("/watchlist/{ticker}", status_code=204, response_class=Response)
def remove_from_watchlist(ticker: str, store: WorkspaceDep) -> Response:
    if not store.remove_from_watchlist(_ticker(ticker)):
        raise HTTPException(status_code=404, detail="Ticker is not on the watchlist")
    return Response(status_code=204)


# --- Saved screens ---------------------------------------------------------
@router.get("/screens", response_model=list[Screen])
def list_screens(store: WorkspaceDep):
    return store.list_screens()


@router.post("/screens", response_model=Screen, status_code=201)
def create_screen(payload: ScreenCreate, store: WorkspaceDep):
    return store.create_screen(payload.name, payload.criteria.model_dump())


@router.delete("/screens/{screen_id}", status_code=204, response_class=Response)
def delete_screen(screen_id: str, store: WorkspaceDep) -> Response:
    if not store.delete_screen(screen_id):
        raise HTTPException(status_code=404, detail="Screen not found")
    return Response(status_code=204)


# --- Flag reviews ----------------------------------------------------------
@router.get("/flags", response_model=list[FlagReview])
def list_all_flag_reviews(store: WorkspaceDep):
    return store.list_all_flag_reviews()


@router.get("/flags/{ticker}", response_model=list[FlagReview])
def list_flag_reviews(ticker: str, store: WorkspaceDep):
    return store.list_flag_reviews(_ticker(ticker))


@router.put("/flags/{ticker}/{flag_id}", response_model=FlagReview)
def set_flag_review(ticker: str, flag_id: str, payload: FlagReviewUpdate, store: WorkspaceDep):
    return store.set_flag_review(_ticker(ticker), _flag_id(flag_id), payload.status, payload.note)


# --- Notes -----------------------------------------------------------------
@router.get("/notes/{ticker}", response_model=list[Note])
def list_notes(ticker: str, store: WorkspaceDep):
    return store.list_notes(_ticker(ticker))


@router.post("/notes/{ticker}", response_model=Note, status_code=201)
def add_note(ticker: str, payload: NoteBody, store: WorkspaceDep):
    return store.add_note(_ticker(ticker), payload.body)


@router.patch("/notes/{ticker}/{note_id}", response_model=Note)
def update_note(ticker: str, note_id: str, payload: NoteBody, store: WorkspaceDep):
    note = store.update_note(_ticker(ticker), note_id, payload.body)
    if note is None:
        raise HTTPException(status_code=404, detail="Note not found")
    return note


@router.delete("/notes/{ticker}/{note_id}", status_code=204, response_class=Response)
def delete_note(ticker: str, note_id: str, store: WorkspaceDep) -> Response:
    if not store.delete_note(_ticker(ticker), note_id):
        raise HTTPException(status_code=404, detail="Note not found")
    return Response(status_code=204)
```

- [ ] `api/app.py`: import `workspace` with the other routers, then `app.include_router(workspace.router, prefix="/api")`.
- [ ] `api/routers/forensics.py`, `download_forensic_memo`: add parameter `store: WorkspaceDep`, and after building `memo_md`:

```python
    memo_md += render_analyst_review(store.list_flag_reviews(ticker), store.list_notes(ticker))
```

  with imports `from zaisaku.api.dependencies import WorkspaceDep` and `from zaisaku.workspace.memo import render_analyst_review`.

- [ ] `tests/conftest.py`: append

```python
@pytest.fixture(autouse=True)
def workspace_store(monkeypatch):
    """Point the workspace dependency at an in-memory DB so tests never write into uploads/."""
    from zaisaku.api import dependencies
    from zaisaku.workspace.store import WorkspaceStore

    store = WorkspaceStore(":memory:")
    monkeypatch.setattr(dependencies, "_workspace_store_instance", store)
    yield store
    store.close()
```

### Task 1.4: API tests

**File:** `backend/tests/unit/test_workspace_api.py`
```python
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from zaisaku.api.app import create_app


@pytest.fixture
def client():
    return TestClient(create_app())


def test_watchlist_crud(client):
    assert client.get("/api/workspace/watchlist").json() == []
    res = client.put("/api/workspace/watchlist/nvda")
    assert res.status_code == 200
    assert res.json()["ticker"] == "NVDA"
    assert [r["ticker"] for r in client.get("/api/workspace/watchlist").json()] == ["NVDA"]
    assert client.delete("/api/workspace/watchlist/NVDA").status_code == 204
    assert client.delete("/api/workspace/watchlist/NVDA").status_code == 404


def test_invalid_ticker_is_rejected(client):
    assert client.put("/api/workspace/watchlist/NOT_A_TICKER!").status_code == 422


def test_screens_validate_criteria(client):
    ok = client.post("/api/workspace/screens", json={"name": " High risk ", "criteria": {"ffi_min": 50}})
    assert ok.status_code == 201
    body = ok.json()
    assert body["name"] == "High risk"
    assert body["criteria"]["ffi_min"] == 50
    assert body["criteria"]["kind"] == "all"
    assert client.post("/api/workspace/screens", json={"name": "x", "criteria": {"bogus": 1}}).status_code == 422
    assert client.post("/api/workspace/screens", json={"name": "x", "criteria": {"ffi_min": 500}}).status_code == 422
    assert client.post("/api/workspace/screens", json={"name": "  ", "criteria": {}}).status_code == 422
    assert client.delete(f"/api/workspace/screens/{body['id']}").status_code == 204
    assert client.get("/api/workspace/screens").json() == []


def test_flag_reviews(client):
    res = client.put("/api/workspace/flags/smci/drift", json={"status": "escalated", "note": "Ask IR"})
    assert res.status_code == 200
    assert res.json()["ticker"] == "SMCI"
    assert client.get("/api/workspace/flags/SMCI").json()[0]["status"] == "escalated"
    assert len(client.get("/api/workspace/flags").json()) == 1
    assert client.put("/api/workspace/flags/SMCI/drift", json={"status": "maybe"}).status_code == 422
    assert client.put("/api/workspace/flags/SMCI/Bad Id", json={"status": "open"}).status_code == 422


def test_notes_crud(client):
    created = client.post("/api/workspace/notes/NVDA", json={"body": "  Check customer A  "})
    assert created.status_code == 201
    note = created.json()
    assert note["body"] == "Check customer A"
    assert client.post("/api/workspace/notes/NVDA", json={"body": "   "}).status_code == 422
    patched = client.patch(f"/api/workspace/notes/NVDA/{note['id']}", json={"body": "Edited"})
    assert patched.json()["body"] == "Edited"
    assert client.patch(f"/api/workspace/notes/SMCI/{note['id']}", json={"body": "x"}).status_code == 404
    assert client.delete(f"/api/workspace/notes/NVDA/{note['id']}").status_code == 204
    assert client.get("/api/workspace/notes/NVDA").json() == []


def test_memo_download_includes_analyst_review(client):
    client.put("/api/workspace/flags/SMCI/footnotes", json={"status": "escalated", "note": "Auditor resigned"})
    client.post("/api/workspace/notes/SMCI", json={"body": "Wait for 10-K"})
    res = client.post("/api/forensics/report/download", json={"ticker": "SMCI", "company_name": "Super Micro"})
    assert res.status_code == 200
    text = res.text
    assert "## Analyst review" in text
    assert "| Footnote disclosures | escalated | Auditor resigned |" in text
    assert "Wait for 10-K" in text


def test_memo_download_without_workspace_data_has_no_review_section(client):
    res = client.post("/api/forensics/report/download", json={"ticker": "NVDA"})
    assert "## Analyst review" not in res.text
```

- [ ] `cd backend && pytest tests/unit -q && ruff check src tests` → pass.
- [ ] Commit `feat(api): analyst workspace store and endpoints`.

---

## PR 2 — `feat/watchlist`

### Task 2.1: API client, toasts, CSV, portfolio utils

**File:** `frontend/src/api/workspace.js`
```js
const BASE = '/api/workspace'
const enc = encodeURIComponent

async function request (path, { method = 'GET', body } = {}) {
  const res = await fetch(`${BASE}${path}`, {
    method,
    headers: body === undefined ? undefined : { 'Content-Type': 'application/json' },
    body: body === undefined ? undefined : JSON.stringify(body)
  })
  if (!res.ok) {
    let detail = ''
    try {
      const data = await res.json()
      detail = typeof data.detail === 'string' ? data.detail : ''
    } catch {
      // Non-JSON error body; fall back to the status code.
    }
    throw new Error(detail || `Workspace request failed (${res.status})`)
  }
  return res.status === 204 ? null : res.json()
}

export const workspaceApi = {
  listWatchlist: () => request('/watchlist'),
  addToWatchlist: (ticker) => request(`/watchlist/${enc(ticker)}`, { method: 'PUT' }),
  removeFromWatchlist: (ticker) => request(`/watchlist/${enc(ticker)}`, { method: 'DELETE' }),
  listScreens: () => request('/screens'),
  createScreen: (name, criteria) => request('/screens', { method: 'POST', body: { name, criteria } }),
  deleteScreen: (id) => request(`/screens/${enc(id)}`, { method: 'DELETE' }),
  listAllFlagReviews: () => request('/flags'),
  setFlagReview: (ticker, flagId, status, note) =>
    request(`/flags/${enc(ticker)}/${enc(flagId)}`, { method: 'PUT', body: { status, note } }),
  listNotes: (ticker) => request(`/notes/${enc(ticker)}`),
  addNote: (ticker, body) => request(`/notes/${enc(ticker)}`, { method: 'POST', body: { body } }),
  updateNote: (ticker, id, body) => request(`/notes/${enc(ticker)}/${enc(id)}`, { method: 'PATCH', body: { body } }),
  deleteNote: (ticker, id) => request(`/notes/${enc(ticker)}/${enc(id)}`, { method: 'DELETE' })
}
```

**File:** `frontend/src/composables/useToasts.js`
```js
import { ref } from 'vue'

const DEFAULT_TIMEOUT_MS = 5000

const toasts = ref([])
let seq = 0

const dismiss = (id) => {
  toasts.value = toasts.value.filter((t) => t.id !== id)
}

// action: { label, run } renders a button (e.g. Undo) inside the toast.
const push = (message, { tone = 'info', action = null, timeout = DEFAULT_TIMEOUT_MS } = {}) => {
  const id = ++seq
  toasts.value = [...toasts.value, { id, message, tone, action }]
  if (timeout) setTimeout(() => dismiss(id), timeout)
  return id
}

export function useToasts () {
  return { toasts, push, dismiss }
}
```

**File:** `frontend/src/components/shell/ToastHost.vue`
```vue
<script setup>
import { X } from 'lucide-vue-next'
import { useToasts } from '../../composables/useToasts.js'

const { toasts, dismiss } = useToasts()

const runAction = (toast) => {
  dismiss(toast.id)
  toast.action.run()
}
</script>

<template>
  <div class="fixed bottom-4 right-4 z-[70] flex flex-col gap-2 w-80 max-w-[calc(100vw-2rem)]" role="status" aria-live="polite">
    <div
      v-for="toast in toasts"
      :key="toast.id"
      class="flex items-center gap-2 pl-3 pr-1 py-1.5 rounded-md border bg-panel text-fg shadow-lg text-xs"
      :class="toast.tone === 'error' ? 'border-critical' : 'border-line'"
    >
      <span class="flex-1">{{ toast.message }}</span>
      <button v-if="toast.action" type="button" class="btn-ghost text-accent" @click="runAction(toast)">{{ toast.action.label }}</button>
      <button type="button" class="btn-icon w-6 h-6" aria-label="Dismiss notification" @click="dismiss(toast.id)">
        <X class="w-3 h-3" />
      </button>
    </div>
  </div>
</template>
```

**File:** `frontend/src/utils/csv.test.js`
```js
import { describe, it, expect } from 'vitest'
import { toCsv } from './csv.js'

describe('toCsv', () => {
  const columns = [
    { key: 'ticker', label: 'Ticker' },
    { key: 'name', label: 'Name, full' },
    { key: 'mscore', label: 'M-Score' },
    { label: 'Computed', value: (r) => r.ffi * 2 }
  ]

  it('writes a header and quoted rows with CRLF', () => {
    const csv = toCsv(columns, [{ ticker: 'NVDA', name: 'NVIDIA "Corp"', mscore: -2.85, ffi: 9 }])
    expect(csv).toBe('Ticker,"Name, full",M-Score,Computed\r\nNVDA,"NVIDIA ""Corp""",-2.85,18\r\n')
  })

  it('leaves blanks for null and undefined', () => {
    expect(toCsv([{ key: 'a', label: 'A' }], [{ a: null }, {}])).toBe('A\r\n\r\n\r\n')
  })

  it('neutralises spreadsheet formula injection in text but not negative numbers', () => {
    const csv = toCsv([{ key: 'v', label: 'V' }], [{ v: '=HYPERLINK("x")' }, { v: '@cmd' }, { v: '-2.85' }, { v: '-x' }])
    expect(csv.split('\r\n').slice(1, 5)).toEqual(['"\'=HYPERLINK(""x"")"', "'@cmd", '-2.85', "'-x"])
  })
})
```

**File:** `frontend/src/utils/csv.js`
```js
// Spreadsheet apps execute cells starting with these characters as formulas.
const FORMULA_START = /^[=+@\t\r]/

const toCell = (value) => {
  if (value === null || value === undefined) return ''
  let text = String(value)
  if (typeof value === 'string' && (FORMULA_START.test(text) || (text.startsWith('-') && Number.isNaN(Number(text))))) {
    text = `'${text}`
  }
  return /[",\r\n]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text
}

// columns: [{ label, key } | { label, value: (row) => any }]
export function toCsv (columns, rows) {
  const header = columns.map((c) => toCell(c.label)).join(',')
  const body = rows.map((row) => columns.map((c) => toCell(c.value ? c.value(row) : row[c.key])).join(','))
  return `${[header, ...body].join('\r\n')}\r\n`
}

export function downloadCsv (filename, text) {
  const url = URL.createObjectURL(new Blob([text], { type: 'text/csv;charset=utf-8' }))
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(url)
}
```

**File:** `frontend/src/utils/portfolio.test.js`
```js
import { describe, it, expect } from 'vitest'
import { portfolioRow, isUnresolved, unresolvedCount } from './portfolio.js'
import { companyProfiles } from '../data/companyProfiles.js'

const smci = companyProfiles.SMCI
const nvda = companyProfiles.NVDA

describe('isUnresolved', () => {
  it('ignores low-severity flags', () => {
    expect(isUnresolved({ severity: 'good' }, null)).toBe(false)
  })
  it('treats missing, open and escalated reviews as unresolved', () => {
    expect(isUnresolved({ severity: 'critical' }, null)).toBe(true)
    expect(isUnresolved({ severity: 'watch' }, { status: 'open' })).toBe(true)
    expect(isUnresolved({ severity: 'watch' }, { status: 'escalated' })).toBe(true)
    expect(isUnresolved({ severity: 'critical' }, { status: 'reviewed' })).toBe(false)
    expect(isUnresolved({ severity: 'critical' }, { status: 'dismissed' })).toBe(false)
  })
})

describe('portfolioRow', () => {
  it('summarises a covered company', () => {
    const row = portfolioRow('SMCI', smci, [])
    expect(row).toMatchObject({ ticker: 'SMCI', covered: true, ffi: smci.ffi, critical: 4, watch: 0, unresolved: 4 })
  })
  it('counts reviewed flags as resolved', () => {
    const reviews = [{ flag_id: 'drift', status: 'reviewed' }, { flag_id: 'footnotes', status: 'dismissed' }]
    expect(unresolvedCount(smci, reviews)).toBe(2)
  })
  it('reports zero unresolved for a clean company', () => {
    expect(portfolioRow('NVDA', nvda, []).unresolved).toBe(0)
  })
  it('marks tickers outside coverage without inventing metrics', () => {
    expect(portfolioRow('ZZZZ', undefined, [])).toEqual({
      ticker: 'ZZZZ', name: 'Not in coverage', covered: false,
      ffi: null, critical: null, watch: null, mscore: null, drift: null, unresolved: null
    })
  })
})
```

**File:** `frontend/src/utils/portfolio.js`
```js
import { buildRedFlags } from '../components/overview/overviewModel.js'

const UNRESOLVED_STATUSES = new Set(['open', 'escalated'])

// A flag needs attention when it is watch/critical and nobody has closed it out.
export const isUnresolved = (flag, review) =>
  flag.severity !== 'good' && (!review || UNRESOLVED_STATUSES.has(review.status))

export function unresolvedCount (profile, reviews = []) {
  const byFlag = new Map(reviews.map((r) => [r.flag_id, r]))
  return buildRedFlags(profile).filter((f) => isUnresolved(f, byFlag.get(f.id))).length
}

export function portfolioRow (ticker, profile, reviews = []) {
  if (!profile) {
    return {
      ticker, name: 'Not in coverage', covered: false,
      ffi: null, critical: null, watch: null, mscore: null, drift: null, unresolved: null
    }
  }
  const flags = buildRedFlags(profile)
  return {
    ticker,
    name: profile.name,
    covered: true,
    ffi: profile.ffi,
    critical: flags.filter((f) => f.severity === 'critical').length,
    watch: flags.filter((f) => f.severity === 'watch').length,
    mscore: profile.mscore ?? null,
    drift: profile.driftScore ?? null,
    unresolved: unresolvedCount(profile, reviews)
  }
}
```

### Task 2.2: Composables (TDD with mocked fetch)

**File:** `frontend/src/composables/workspace.test.js`
```js
import { describe, it, expect, vi, beforeEach } from 'vitest'

const jsonResponse = (status, body) => ({ ok: status < 400, status, json: async () => body })

describe('useWatchlist', () => {
  beforeEach(() => vi.resetModules())

  it('loads tickers', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => jsonResponse(200, [{ ticker: 'NVDA', added_at: 'x' }])))
    const { useWatchlist } = await import('./useWatchlist.js')
    const w = useWatchlist()
    await w.load()
    expect(w.tickers.value).toEqual(['NVDA'])
    expect(w.state.value).toBe('ready')
  })

  it('adds optimistically and rolls back with an error toast on failure', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => jsonResponse(500, { detail: 'disk full' })))
    const { useWatchlist } = await import('./useWatchlist.js')
    const { useToasts } = await import('./useToasts.js')
    const w = useWatchlist()
    const pending = w.toggle('smci')
    expect(w.tickers.value).toEqual(['SMCI'])
    await pending
    expect(w.tickers.value).toEqual([])
    expect(useToasts().toasts.value.at(-1)).toMatchObject({ tone: 'error' })
    expect(useToasts().toasts.value.at(-1).message).toContain('disk full')
  })

  it('offers undo after removal', async () => {
    const fetchMock = vi.fn(async (url, opts) => jsonResponse(opts?.method === 'DELETE' ? 204 : 200, opts?.method === 'DELETE' ? null : { ticker: 'NVDA', added_at: 'x' }))
    vi.stubGlobal('fetch', fetchMock)
    const { useWatchlist } = await import('./useWatchlist.js')
    const { useToasts } = await import('./useToasts.js')
    const w = useWatchlist()
    w.tickers.value = ['NVDA']
    await w.toggle('NVDA')
    expect(w.tickers.value).toEqual([])
    const toast = useToasts().toasts.value.at(-1)
    expect(toast.action.label).toBe('Undo')
    await toast.action.run()
    expect(w.tickers.value).toEqual(['NVDA'])
  })
})

describe('useFlagReviews', () => {
  beforeEach(() => vi.resetModules())

  it('sets a review optimistically and keeps the server row', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => jsonResponse(200, { ticker: 'SMCI', flag_id: 'drift', status: 'reviewed', note: 'ok', updated_at: 'srv' })))
    const { useFlagReviews } = await import('./useFlagReviews.js')
    const r = useFlagReviews()
    await r.setReview('SMCI', 'drift', 'reviewed', 'ok')
    expect(r.reviewFor('SMCI', 'drift')).toMatchObject({ status: 'reviewed', updated_at: 'srv' })
  })

  it('rolls back a failed review', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => jsonResponse(500, {})))
    const { useFlagReviews } = await import('./useFlagReviews.js')
    const r = useFlagReviews()
    await r.setReview('SMCI', 'drift', 'reviewed', '')
    expect(r.reviewFor('SMCI', 'drift')).toBeNull()
  })
})
```

**File:** `frontend/src/composables/useWatchlist.js`
```js
import { ref } from 'vue'
import { workspaceApi } from '../api/workspace.js'
import { useToasts } from './useToasts.js'

const tickers = ref([])
const state = ref('idle') // idle | loading | ready | error

const load = async () => {
  state.value = 'loading'
  try {
    const rows = await workspaceApi.listWatchlist()
    tickers.value = rows.map((r) => r.ticker)
    state.value = 'ready'
  } catch {
    state.value = 'error'
  }
}

const isWatched = (ticker) => tickers.value.includes(String(ticker).toUpperCase())

const toggle = async (ticker) => {
  const { push } = useToasts()
  const t = String(ticker).toUpperCase()
  const before = tickers.value
  const removing = before.includes(t)
  tickers.value = removing ? before.filter((x) => x !== t) : [...before, t]
  try {
    if (removing) {
      await workspaceApi.removeFromWatchlist(t)
      push(`${t} removed from watchlist`, { action: { label: 'Undo', run: () => toggle(t) } })
    } else {
      await workspaceApi.addToWatchlist(t)
      push(`${t} added to watchlist`)
    }
  } catch (err) {
    tickers.value = before
    push(`Could not update watchlist: ${err.message}`, { tone: 'error' })
  }
}

export function useWatchlist () {
  return { tickers, state, load, isWatched, toggle }
}
```

**File:** `frontend/src/composables/useFlagReviews.js`
```js
import { ref } from 'vue'
import { workspaceApi } from '../api/workspace.js'
import { useToasts } from './useToasts.js'

const reviews = ref([])
const state = ref('idle')

const load = async () => {
  state.value = 'loading'
  try {
    reviews.value = await workspaceApi.listAllFlagReviews()
    state.value = 'ready'
  } catch {
    state.value = 'error'
  }
}

const reviewFor = (ticker, flagId) =>
  reviews.value.find((r) => r.ticker === ticker && r.flag_id === flagId) ?? null

const reviewsFor = (ticker) => reviews.value.filter((r) => r.ticker === ticker)

const upsertLocal = (list, row) => [
  ...list.filter((r) => !(r.ticker === row.ticker && r.flag_id === row.flag_id)),
  row
]

const setReview = async (ticker, flagId, status, note = '') => {
  const before = reviews.value
  reviews.value = upsertLocal(before, { ticker, flag_id: flagId, status, note, updated_at: new Date().toISOString() })
  try {
    const saved = await workspaceApi.setFlagReview(ticker, flagId, status, note)
    reviews.value = upsertLocal(reviews.value, saved)
    return true
  } catch (err) {
    reviews.value = before
    useToasts().push(`Could not save review: ${err.message}`, { tone: 'error' })
    return false
  }
}

export function useFlagReviews () {
  return { reviews, state, load, reviewFor, reviewsFor, setReview }
}
```

### Task 2.3: Watchlist view, star, nav sections

- [ ] `style.css`: append `disabled:opacity-50 disabled:cursor-not-allowed` to the `.btn-primary` and `.btn-ghost` `@apply` lists, and add

```css
  .field {
    @apply h-7 w-full rounded border border-line bg-bg px-2 text-xs text-fg outline-none focus:border-accent placeholder:text-faint;
  }
```

**File:** `frontend/src/components/portfolio/WatchlistView.vue`
```vue
<script setup>
import { computed } from 'vue'
import { Download } from 'lucide-vue-next'
import Panel from '../ui/Panel.vue'
import DataTable from '../ui/DataTable.vue'
import { useWatchlist } from '../../composables/useWatchlist.js'
import { useFlagReviews } from '../../composables/useFlagReviews.js'
import { useCompany } from '../../composables/useCompany.js'
import { companyProfiles } from '../../data/companyProfiles.js'
import { portfolioRow } from '../../utils/portfolio.js'
import { toCsv, downloadCsv } from '../../utils/csv.js'

const emit = defineEmits(['open-company'])

const { tickers, state, load } = useWatchlist()
const { reviewsFor } = useFlagReviews()
const { selectCompany } = useCompany()

const coverageCount = Object.keys(companyProfiles).length
const rows = computed(() => tickers.value.map((t) => portfolioRow(t, companyProfiles[t], reviewsFor(t))))

const dash = (v, fmt = (x) => x) => (v === null || v === undefined ? '—' : fmt(v))

const columns = [
  { key: 'ticker', label: 'Ticker', sortable: true },
  { key: 'name', label: 'Company', sortable: true },
  { key: 'ffi', label: 'FFI', align: 'right', sortable: true, format: (v) => dash(v) },
  { key: 'critical', label: 'Critical', align: 'right', sortable: true },
  { key: 'watch', label: 'Watch', align: 'right', sortable: true, format: (v) => dash(v) },
  { key: 'mscore', label: 'M-Score', align: 'right', sortable: true, format: (v) => dash(v, (x) => x.toFixed(2)) },
  { key: 'drift', label: 'Drift', align: 'right', sortable: true, format: (v) => dash(v, (x) => `${x}%`) },
  { key: 'unresolved', label: 'Unresolved', align: 'right', sortable: true }
]

const panelState = computed(() => {
  if (state.value === 'loading' || state.value === 'idle') return 'loading'
  if (state.value === 'error') return 'error'
  return rows.value.length ? 'ready' : 'empty'
})

const open = (row) => {
  selectCompany(row.ticker)
  emit('open-company')
}

const exportCsv = () => {
  const csvColumns = columns.map((c) => ({ label: c.label, key: c.key }))
  downloadCsv('zaisaku-watchlist.csv', toCsv(csvColumns, rows.value))
}
</script>

<template>
  <div class="p-3 space-y-2">
    <Panel
      :title="`Watchlist · ${tickers.length}`"
      :state="panelState"
      empty-text="No companies on your watchlist yet. Use the star in the company strip to add one."
      error-text="Could not load the watchlist."
      @retry="load"
    >
      <template #actions>
        <button type="button" class="btn-ghost" :disabled="!rows.length" @click="exportCsv">
          <Download class="w-3.5 h-3.5" /> CSV
        </button>
      </template>
      <DataTable :columns="columns" :rows="rows" row-key="ticker" clickable :initial-sort="{ key: 'ffi', dir: 'desc' }" @row-click="open">
        <template #cell-ticker="{ value }"><span class="font-mono font-semibold">{{ value }}</span></template>
        <template #cell-name="{ row }"><span :class="row.covered ? '' : 'text-faint italic'">{{ row.name }}</span></template>
        <template #cell-critical="{ value }"><span :class="value ? 'text-critical font-semibold' : 'text-muted'">{{ value ?? '—' }}</span></template>
        <template #cell-unresolved="{ value }"><span :class="value ? 'text-fg font-semibold' : 'text-muted'">{{ value ?? '—' }}</span></template>
      </DataTable>
    </Panel>
    <p class="px-1 text-[11px] text-faint">Metrics cover the {{ coverageCount }} companies in Zaisaku's research coverage. Other tickers are listed but not scored.</p>
  </div>
</template>
```

- [ ] `CompanyStrip.vue`: add props `watched: { type: Boolean, default: false }`, emit `'toggle-watch'`, import `Star`, and before the risk chip:

```html
      <button
        type="button"
        class="btn-icon"
        :aria-pressed="watched"
        :aria-label="watched ? `Remove ${company.ticker} from watchlist` : `Add ${company.ticker} to watchlist`"
        :title="watched ? 'On watchlist' : 'Add to watchlist'"
        @click="emit('toggle-watch')"
      >
        <Star class="w-3.5 h-3.5" :class="watched ? 'fill-current text-watch' : ''" />
      </button>
```

- [ ] `TopBar.vue`: replace `<li v-for="tab in tabs" ...>` with a `<template v-for="(tab, i) in tabs" :key="tab.id">` that first renders `<li v-if="i > 0 && tab.section !== tabs[i - 1].section" aria-hidden="true" class="w-px h-4 bg-line mx-1 self-center" />` and then the existing `<li>` (key moves to the template).
- [ ] `CompanyHub.vue`:
  - Imports: `WatchlistView`, `useWatchlist`, `useFlagReviews`.
  - Give every existing tab `section: 'company'` and append `{ id: 'watchlist', label: 'Watchlist', section: 'portfolio', count: watchlist.tickers.value.length || null }`.
  - `const PORTFOLIO_TABS = ['watchlist', 'screener', 'compare']` and `const isPortfolioView = computed(() => PORTFOLIO_TABS.includes(currentTab.value))`.
  - The strip becomes `<CompanyStrip v-if="!isPortfolioView" :company="currentCompany" :watched="watchlist.isWatched(currentCompany.ticker)" @toggle-watch="watchlist.toggle(currentCompany.ticker)" @tool="handleTool" />`.
  - After `<OverviewDashboard …/>` in the transition: `<WatchlistView v-else-if="currentTab === 'watchlist'" key="watchlist" @open-company="currentTab = 'overview'" />`.
  - In `onMounted`: `watchlist.load(); flagReviews.load()`.
  - Declare `const watchlist = useWatchlist()` and `const flagReviews = useFlagReviews()`.
- [ ] `App.vue`: import and render `<ToastHost />` as the last child.

**File:** `frontend/src/components/portfolio/WatchlistView.test.js`
```js
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'

describe('WatchlistView', () => {
  beforeEach(() => vi.resetModules())

  it('lists watched companies riskiest first and flags uncovered tickers', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => ({ ok: true, status: 200, json: async () => [] })))
    const { useWatchlist } = await import('../../composables/useWatchlist.js')
    const w = useWatchlist()
    w.tickers.value = ['NVDA', 'SMCI', 'ZZZZ']
    w.state.value = 'ready'
    const { default: WatchlistView } = await import('./WatchlistView.vue')
    const wrapper = mount(WatchlistView)
    await flushPromises()
    const order = wrapper.findAll('tbody tr').map((tr) => tr.attributes('data-row'))
    expect(order).toEqual(['SMCI', 'NVDA', 'ZZZZ'])
    expect(wrapper.find('[data-row="ZZZZ"]').text()).toContain('Not in coverage')
  })

  it('opens a company on row click', async () => {
    const { useWatchlist } = await import('../../composables/useWatchlist.js')
    const w = useWatchlist()
    w.tickers.value = ['SMCI']
    w.state.value = 'ready'
    const { default: WatchlistView } = await import('./WatchlistView.vue')
    const { useCompany } = await import('../../composables/useCompany.js')
    const wrapper = mount(WatchlistView)
    await wrapper.find('[data-row="SMCI"]').trigger('click')
    expect(useCompany().currentCompany.value.ticker).toBe('SMCI')
    expect(wrapper.emitted('open-company')).toHaveLength(1)
  })
})
```

- [ ] `npm test && npm run build`. Browser check with the backend running: star NVDA and SMCI, open the Watchlist tab, check sort and row click; remove a ticker, use Undo; export CSV. Then stop the backend: the star shows an error toast and rolls back.
- [ ] Commit `feat(ui): watchlist with portfolio risk table`.

---

## PR 3 — `feat/flag-triage-notes`

### Task 3.1: DataTable row class + flag labels

- [ ] `DataTable.vue`: add prop `rowClass: { type: Function, default: null }` and append `rowClass ? rowClass(row) : ''` to the `<tr>` `:class` array. Add a test to `primitives.test.js`:

```js
  it('applies rowClass per row', () => {
    const w = mount(DataTable, { props: { columns, rows, rowKey: 'ticker', rowClass: (r) => (r.ticker === 'AMD' ? 'opacity-50' : '') } })
    expect(w.find('[data-row="AMD"]').classes()).toContain('opacity-50')
    expect(w.find('[data-row="NVDA"]').classes()).not.toContain('opacity-50')
  })
```

- [ ] `overviewModel.js`: add

```js
export const FLAG_LABELS = {
  drift: 'Language drift',
  accruals: 'Accruals / M-Score',
  contradictions: 'Call vs 10-Q',
  footnotes: 'Footnote disclosures'
}

export const REVIEW_STATUSES = ['open', 'reviewed', 'escalated', 'dismissed']
```

### Task 3.2: useNotes (TDD)

Append to `frontend/src/composables/workspace.test.js`:

```js
describe('useNotes', () => {
  beforeEach(() => vi.resetModules())

  it('adds a note to the front and supports undoing a delete', async () => {
    let n = 0
    const fetchMock = vi.fn(async (url, opts = {}) => {
      if (opts.method === 'POST') {
        n += 1
        return jsonResponse(201, { id: `id${n}`, ticker: 'NVDA', body: JSON.parse(opts.body).body, created_at: `t${n}`, updated_at: `t${n}` })
      }
      if (opts.method === 'DELETE') return jsonResponse(204, null)
      return jsonResponse(200, [])
    })
    vi.stubGlobal('fetch', fetchMock)
    const { useNotes } = await import('./useNotes.js')
    const { useToasts } = await import('./useToasts.js')
    const notes = useNotes()
    await notes.load('NVDA')
    await notes.add('NVDA', 'one')
    await notes.add('NVDA', 'two')
    expect(notes.notesFor('NVDA').map((x) => x.body)).toEqual(['two', 'one'])
    await notes.remove('NVDA', 'id1')
    expect(notes.notesFor('NVDA').map((x) => x.body)).toEqual(['two'])
    await useToasts().toasts.value.at(-1).action.run()
    expect(notes.notesFor('NVDA').map((x) => x.body)).toEqual(['one', 'two'])
  })

  it('restores a note when the delete fails', async () => {
    vi.stubGlobal('fetch', vi.fn(async (url, opts = {}) => (opts.method === 'DELETE' ? jsonResponse(500, {}) : jsonResponse(200, [{ id: 'a', ticker: 'NVDA', body: 'keep', created_at: 't', updated_at: 't' }]))))
    const { useNotes } = await import('./useNotes.js')
    const notes = useNotes()
    await notes.load('NVDA')
    await notes.remove('NVDA', 'a')
    expect(notes.notesFor('NVDA').map((x) => x.body)).toEqual(['keep'])
  })
})
```

**File:** `frontend/src/composables/useNotes.js`
```js
import { reactive } from 'vue'
import { workspaceApi } from '../api/workspace.js'
import { useToasts } from './useToasts.js'

// ticker -> { state: 'loading'|'ready'|'error', items: Note[] (newest first) }
const byTicker = reactive({})

const entry = (ticker) => {
  if (!byTicker[ticker]) byTicker[ticker] = { state: 'idle', items: [] }
  return byTicker[ticker]
}

const load = async (ticker) => {
  const e = entry(ticker)
  e.state = 'loading'
  try {
    e.items = await workspaceApi.listNotes(ticker)
    e.state = 'ready'
  } catch {
    e.state = 'error'
  }
}

const notesFor = (ticker) => byTicker[ticker]?.items ?? []
const stateFor = (ticker) => byTicker[ticker]?.state ?? 'idle'

const add = async (ticker, body) => {
  try {
    const note = await workspaceApi.addNote(ticker, body)
    const e = entry(ticker)
    e.items = [note, ...e.items]
    return true
  } catch (err) {
    useToasts().push(`Could not save note: ${err.message}`, { tone: 'error' })
    return false
  }
}

const update = async (ticker, id, body) => {
  const e = entry(ticker)
  const before = e.items
  e.items = before.map((n) => (n.id === id ? { ...n, body } : n))
  try {
    const saved = await workspaceApi.updateNote(ticker, id, body)
    e.items = e.items.map((n) => (n.id === id ? saved : n))
    return true
  } catch (err) {
    e.items = before
    useToasts().push(`Could not update note: ${err.message}`, { tone: 'error' })
    return false
  }
}

const remove = async (ticker, id) => {
  const e = entry(ticker)
  const before = e.items
  const removed = before.find((n) => n.id === id)
  e.items = before.filter((n) => n.id !== id)
  try {
    await workspaceApi.deleteNote(ticker, id)
    if (removed) {
      // Undo re-creates the note (new id and timestamp; same text).
      useToasts().push('Note deleted', { action: { label: 'Undo', run: () => add(ticker, removed.body) } })
    }
  } catch (err) {
    e.items = before
    useToasts().push(`Could not delete note: ${err.message}`, { tone: 'error' })
  }
}

export function useNotes () {
  return { load, notesFor, stateFor, add, update, remove }
}
```

### Task 3.3: Note editor + Notes panel

**File:** `frontend/src/components/overview/FlagNoteEditor.vue`
```vue
<script setup>
import { ref, nextTick, onMounted, onUnmounted } from 'vue'
import { MessageSquare, MessageSquareText } from 'lucide-vue-next'

const props = defineProps({
  note: { type: String, default: '' },
  label: { type: String, required: true }
})

const emit = defineEmits(['save'])

const POPOVER_WIDTH = 288

const open = ref(false)
const draft = ref('')
const trigger = ref(null)
const popover = ref(null)
const area = ref(null)
const position = ref({ top: 0, left: 0 })

// Fixed positioning so the popover is not clipped by the panel's scroll container.
const place = () => {
  const rect = trigger.value.getBoundingClientRect()
  position.value = {
    top: rect.bottom + 4,
    left: Math.max(8, Math.min(window.innerWidth - POPOVER_WIDTH - 8, rect.right - POPOVER_WIDTH))
  }
}

const openEditor = async () => {
  draft.value = props.note
  place()
  open.value = true
  await nextTick()
  area.value?.focus()
}

const close = () => { open.value = false }

const save = () => {
  emit('save', draft.value.trim())
  close()
}

const onPointer = (e) => {
  if (!open.value) return
  if (popover.value?.contains(e.target) || trigger.value?.contains(e.target)) return
  close()
}

onMounted(() => {
  document.addEventListener('mousedown', onPointer)
  window.addEventListener('resize', close)
})
onUnmounted(() => {
  document.removeEventListener('mousedown', onPointer)
  window.removeEventListener('resize', close)
})
</script>

<template>
  <span class="inline-block" @click.stop @keydown.stop>
    <button
      ref="trigger"
      type="button"
      class="btn-icon w-6 h-6"
      :class="note ? 'text-accent' : ''"
      :aria-label="note ? `Edit note: ${label}` : `Add note: ${label}`"
      :aria-expanded="open"
      :title="note || 'Add note'"
      @click="open ? close() : openEditor()"
    >
      <component :is="note ? MessageSquareText : MessageSquare" class="w-3.5 h-3.5" />
    </button>
    <Teleport to="body">
      <div
        v-if="open"
        ref="popover"
        role="dialog"
        :aria-label="`Note: ${label}`"
        class="fixed z-[65] rounded-md border border-line bg-panel shadow-lg p-2 space-y-2"
        :style="{ top: `${position.top}px`, left: `${position.left}px`, width: `${POPOVER_WIDTH}px` }"
        @keydown.esc="close"
      >
        <textarea
          ref="area"
          v-model="draft"
          rows="4"
          maxlength="5000"
          class="w-full resize-y rounded border border-line bg-bg text-xs text-fg p-2 outline-none focus:border-accent placeholder:text-faint"
          placeholder="Evidence, follow-ups, why this status… (Ctrl+Enter to save)"
          @keydown.ctrl.enter.prevent="save"
          @keydown.meta.enter.prevent="save"
        />
        <div class="flex justify-end gap-1">
          <button type="button" class="btn-ghost" @click="close">Cancel</button>
          <button type="button" class="btn-primary" @click="save">Save</button>
        </div>
      </div>
    </Teleport>
  </span>
</template>
```

**File:** `frontend/src/components/overview/NotesPanel.vue`
```vue
<script setup>
import { ref, computed, watch } from 'vue'
import Panel from '../ui/Panel.vue'
import { useNotes } from '../../composables/useNotes.js'

const props = defineProps({
  ticker: { type: String, required: true }
})

const { load, notesFor, stateFor, add, update, remove } = useNotes()

watch(() => props.ticker, (t) => load(t), { immediate: true })

const notes = computed(() => notesFor(props.ticker))
const panelState = computed(() => {
  const s = stateFor(props.ticker)
  return s === 'loading' || s === 'idle' ? 'loading' : s === 'error' ? 'error' : 'ready'
})

const draft = ref('')
const editingId = ref(null)
const editDraft = ref('')

const submit = async () => {
  const body = draft.value.trim()
  if (!body) return
  if (await add(props.ticker, body)) draft.value = ''
}

const startEdit = (note) => {
  editingId.value = note.id
  editDraft.value = note.body
}

const saveEdit = async (note) => {
  const body = editDraft.value.trim()
  if (!body) return
  if (await update(props.ticker, note.id, body)) editingId.value = null
}

const formatDate = (iso) =>
  new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
</script>

<template>
  <Panel title="Notes" :state="panelState" error-text="Could not load notes." @retry="load(ticker)">
    <div class="p-3 space-y-3">
      <form class="space-y-2" @submit.prevent="submit">
        <textarea
          v-model="draft"
          rows="2"
          maxlength="5000"
          :aria-label="`New note for ${ticker}`"
          :placeholder="`Add a note on ${ticker}… (Ctrl+Enter to save)`"
          class="w-full resize-y rounded border border-line bg-bg text-xs text-fg p-2 outline-none focus:border-accent placeholder:text-faint"
          @keydown.ctrl.enter.prevent="submit"
          @keydown.meta.enter.prevent="submit"
        />
        <div class="flex justify-end">
          <button type="submit" class="btn-primary" :disabled="!draft.trim()">Add note</button>
        </div>
      </form>

      <p v-if="!notes.length" class="text-xs text-muted">No notes yet.</p>
      <ul v-else class="space-y-2">
        <li v-for="note in notes" :key="note.id" class="border-t border-line pt-2 space-y-1" :data-note="note.id">
          <div class="flex items-center justify-between gap-2 text-[11px] text-faint">
            <time :datetime="note.created_at">{{ formatDate(note.created_at) }}</time>
            <span v-if="editingId !== note.id" class="flex gap-0.5">
              <button type="button" class="btn-ghost h-5" @click="startEdit(note)">Edit</button>
              <button type="button" class="btn-ghost h-5" @click="remove(ticker, note.id)">Delete</button>
            </span>
          </div>
          <template v-if="editingId === note.id">
            <textarea
              v-model="editDraft"
              rows="3"
              maxlength="5000"
              aria-label="Edit note"
              class="w-full resize-y rounded border border-line bg-bg text-xs text-fg p-2 outline-none focus:border-accent"
              @keydown.ctrl.enter.prevent="saveEdit(note)"
              @keydown.meta.enter.prevent="saveEdit(note)"
              @keydown.esc="editingId = null"
            />
            <div class="flex justify-end gap-1">
              <button type="button" class="btn-ghost" @click="editingId = null">Cancel</button>
              <button type="button" class="btn-primary" :disabled="!editDraft.trim()" @click="saveEdit(note)">Save</button>
            </div>
          </template>
          <p v-else class="text-xs text-fg whitespace-pre-wrap break-words">{{ note.body }}</p>
        </li>
      </ul>
    </div>
  </Panel>
</template>
```

### Task 3.4: Triage in the Red flags panel

`OverviewDashboard.vue` changes:
- Imports: `useFlagReviews`, `FlagNoteEditor`, `NotesPanel`, and `REVIEW_STATUSES` from `./overviewModel.js`.
- Script:

```js
const { reviewFor, setReview } = useFlagReviews()
const hideDismissed = ref(false)

const flagRows = computed(() =>
  flags.value
    .map((f) => {
      const review = reviewFor(props.company.ticker, f.id)
      return { ...f, status: review?.status ?? 'open', note: review?.note ?? '' }
    })
    .filter((row) => !hideDismissed.value || row.status !== 'dismissed')
)

const onStatus = (row, status) => setReview(props.company.ticker, row.id, status, row.note)
const onNote = (row, note) => setReview(props.company.ticker, row.id, row.status, note)
const flagRowClass = (row) => (row.status === 'dismissed' ? 'opacity-50' : '')
```

- `flagColumns`:

```js
const flagColumns = [
  { key: 'severity', label: '', width: '28px' },
  { key: 'finding', label: 'Finding' },
  { key: 'status', label: 'Status', width: '116px' },
  { key: 'note', label: '', width: '36px' },
  { key: 'source', label: 'Source', align: 'right', width: '120px' }
]
```

- Red flags `<Panel>`:
  - `:state`: `flags.length ? (flagRows.length ? 'ready' : 'empty') : 'empty'`.
  - `:empty-text`: `flags.length ? 'All flags dismissed.' : 'No findings for this period.'`.
  - Actions slot gets a toggle before "Anomaly radar": `<button type="button" class="btn-ghost" :aria-pressed="hideDismissed" @click="hideDismissed = !hideDismissed">{{ hideDismissed ? 'Show dismissed' : 'Hide dismissed' }}</button>`.
- DataTable uses `:rows="flagRows"` and `:row-class="flagRowClass"`, with new cells:

```html
        <template #cell-status="{ row }">
          <select
            :value="row.status"
            class="h-6 rounded border border-line bg-panel text-xs text-fg px-1 cursor-pointer"
            :aria-label="`Review status: ${row.source}`"
            @click.stop
            @keydown.stop
            @change="onStatus(row, $event.target.value)"
          >
            <option v-for="s in REVIEW_STATUSES" :key="s" :value="s">{{ s[0].toUpperCase() + s.slice(1) }}</option>
          </select>
        </template>
        <template #cell-note="{ row }">
          <FlagNoteEditor :note="row.note" :label="row.source" @save="(text) => onNote(row, text)" />
        </template>
```

- Peers panel class: `md:col-span-2` (was `md:col-span-2 xl:col-span-3`). After it add `<NotesPanel :ticker="company.ticker" />`.

Append to `OverviewDashboard.test.js`:

```js
  it('saves a status change for a flag without opening its modal', async () => {
    const fetchMock = vi.fn(async (url, opts = {}) => {
      if (opts.method === 'PUT') return { ok: true, status: 200, json: async () => ({ ticker: 'NVDA', flag_id: 'drift', status: 'escalated', note: '', updated_at: 't' }) }
      return { ok: false, status: 500, json: async () => ({}) }
    })
    vi.stubGlobal('fetch', fetchMock)
    const w = mount(OverviewDashboard, { props: { company } })
    await flushPromises()
    const flagsPanel = w.findAll('section').find((sec) => sec.find('h2').text() === 'Red flags')
    await flagsPanel.find('[data-row="drift"] select').setValue('escalated')
    await flushPromises()
    expect(fetchMock).toHaveBeenCalledWith('/api/workspace/flags/NVDA/drift', expect.objectContaining({ method: 'PUT' }))
    expect(w.emitted('flag-action')).toBeUndefined()
  })
```

### Task 3.5: Unresolved chip + memo preview

- [ ] `CompanyStrip.vue`: prop `unresolved: { type: Number, default: 0 }`, emit `'show-flags'`, and before the star:

```html
      <button v-if="unresolved" type="button" class="btn text-watch" @click="emit('show-flags')">
        {{ unresolved }} unresolved {{ unresolved === 1 ? 'flag' : 'flags' }}
      </button>
```

- [ ] `CompanyHub.vue`: `import { unresolvedCount } from '../utils/portfolio.js'` and `const unresolvedForCurrent = computed(() => unresolvedCount(currentCompany.value, flagReviews.reviewsFor(currentCompany.value.ticker)))`. Pass `:unresolved="unresolvedForCurrent" @show-flags="currentTab = 'overview'"` to the strip.
- [ ] `InstitutionalReportModal.vue`:
  - Import `useFlagReviews`, `useNotes`, and `FLAG_LABELS` from `./overview/overviewModel.js`, plus `watch`.
  - `const { reviewsFor } = useFlagReviews()` and `const notesApi = useNotes()`.
  - `watch(() => props.isOpen, (open) => { if (open) notesApi.load(props.ticker) })`.
  - `const reviewRows = computed(() => reviewsFor(props.ticker).map((r) => ({ ...r, label: FLAG_LABELS[r.flag_id] ?? r.flag_id })))` and `const memoNotes = computed(() => notesApi.notesFor(props.ticker))`.
  - Insert before `<!-- Section 3: Sign-Off -->`:

```html
          <!-- Section 3: Analyst review (only when the analyst recorded something) -->
          <div v-if="reviewRows.length || memoNotes.length" class="space-y-2">
            <h3 class="text-xs font-semibold text-blue-400 border-b border-neutral-800 pb-1 print:text-black print:border-black">
              3. Analyst review
            </h3>
            <table v-if="reviewRows.length" class="w-full text-[11px] text-neutral-300 print:text-neutral-800">
              <thead><tr class="text-left text-neutral-500"><th class="py-1 pr-3 font-medium">Flag</th><th class="py-1 pr-3 font-medium">Status</th><th class="py-1 font-medium">Note</th></tr></thead>
              <tbody>
                <tr v-for="r in reviewRows" :key="r.flag_id" class="border-t border-neutral-800 print:border-neutral-300">
                  <td class="py-1 pr-3">{{ r.label }}</td>
                  <td class="py-1 pr-3 capitalize">{{ r.status }}</td>
                  <td class="py-1 whitespace-pre-wrap">{{ r.note || '—' }}</td>
                </tr>
              </tbody>
            </table>
            <ul v-if="memoNotes.length" class="space-y-1 text-[11px] text-neutral-300 print:text-neutral-800">
              <li v-for="n in memoNotes" :key="n.id" class="whitespace-pre-wrap"><span class="text-neutral-500">{{ n.created_at.slice(0, 10) }}</span> — {{ n.body }}</li>
            </ul>
          </div>
```

- [ ] `npm test && npm run build`. Browser check with the backend running:
  - change SMCI drift → Escalated, add a note, reload: both persist;
  - "Hide dismissed" works;
  - the strip count drops as flags get reviewed;
  - the memo preview shows section 3;
  - the exported Markdown contains "Analyst review".
- [ ] Commit `feat(ui): flag triage, analyst notes, and review section in memo`.

---

## PR 4 — `feat/screener`

**File:** `frontend/src/utils/screen.test.js`
```js
import { describe, it, expect } from 'vitest'
import { applyScreen, sectorsOf, describeCriteria, EMPTY_CRITERIA } from './screen.js'
import { companyProfiles } from '../data/companyProfiles.js'

const all = Object.values(companyProfiles)
const tickers = (list) => list.map((p) => p.ticker).sort()

describe('applyScreen', () => {
  it('returns everything for empty criteria', () => {
    expect(applyScreen(all, EMPTY_CRITERIA)).toHaveLength(all.length)
  })
  it('filters by FFI range inclusively', () => {
    const out = applyScreen(all, { ffi_min: 60, ffi_max: 100 })
    expect(out.every((p) => p.ffi >= 60)).toBe(true)
    expect(tickers(out)).toContain('SMCI')
  })
  it('filters M-Score strictly above a threshold', () => {
    expect(applyScreen(all, { mscore_above: -1.78 }).every((p) => p.mscore > -1.78)).toBe(true)
  })
  it('separates companies and indices', () => {
    expect(applyScreen(all, { kind: 'index' }).every((p) => p.is_macro_index)).toBe(true)
    expect(applyScreen(all, { kind: 'company' }).some((p) => p.is_macro_index)).toBe(false)
  })
  it('keeps only companies with a critical red flag', () => {
    expect(tickers(applyScreen(all, { critical_only: true }))).toContain('SMCI')
    expect(tickers(applyScreen(all, { critical_only: true }))).not.toContain('NVDA')
  })
  it('treats blank form values as unset', () => {
    expect(applyScreen(all, { ffi_min: '', sector: '' })).toHaveLength(all.length)
  })
})

describe('sectorsOf / describeCriteria', () => {
  it('lists unique sorted sectors', () => {
    const s = sectorsOf(all)
    expect(s).toEqual([...new Set(s)].sort((a, b) => a.localeCompare(b)))
  })
  it('summarises active criteria', () => {
    expect(describeCriteria({ ffi_min: 50, mscore_above: -1.78, critical_only: true, kind: 'company' }))
      .toBe('FFI ≥ 50 · M-Score > -1.78 · Companies · Critical flag')
    expect(describeCriteria(EMPTY_CRITERIA)).toBe('All companies')
  })
})
```

**File:** `frontend/src/utils/screen.js`
```js
import { buildRedFlags } from '../components/overview/overviewModel.js'
import { isIndexTicker } from '../data/companyProfiles.js'

export const EMPTY_CRITERIA = Object.freeze({
  ffi_min: null, ffi_max: null, mscore_above: null, drift_min: null, sector: null, kind: 'all', critical_only: false
})

const toNumber = (v) => (v === null || v === undefined || v === '' || Number.isNaN(Number(v)) ? null : Number(v))

// Form inputs give strings; the API and filters want numbers or null.
export function normalizeCriteria (criteria = {}) {
  const c = { ...EMPTY_CRITERIA, ...criteria }
  return {
    ffi_min: toNumber(c.ffi_min),
    ffi_max: toNumber(c.ffi_max),
    mscore_above: toNumber(c.mscore_above),
    drift_min: toNumber(c.drift_min),
    sector: c.sector ? String(c.sector) : null,
    kind: ['company', 'index'].includes(c.kind) ? c.kind : 'all',
    critical_only: Boolean(c.critical_only)
  }
}

const isIndex = (p) => Boolean(p.is_macro_index) || isIndexTicker(p.ticker)

export function applyScreen (profiles, criteria) {
  const c = normalizeCriteria(criteria)
  return profiles.filter((p) => {
    if (c.kind === 'company' && isIndex(p)) return false
    if (c.kind === 'index' && !isIndex(p)) return false
    if (c.ffi_min !== null && !(p.ffi >= c.ffi_min)) return false
    if (c.ffi_max !== null && !(p.ffi <= c.ffi_max)) return false
    if (c.mscore_above !== null && !(p.mscore > c.mscore_above)) return false
    if (c.drift_min !== null && !(p.driftScore >= c.drift_min)) return false
    if (c.sector && p.sector !== c.sector) return false
    if (c.critical_only && !buildRedFlags(p).some((f) => f.severity === 'critical')) return false
    return true
  })
}

export const sectorsOf = (profiles) =>
  [...new Set(profiles.map((p) => p.sector).filter(Boolean))].sort((a, b) => a.localeCompare(b))

export function describeCriteria (criteria) {
  const c = normalizeCriteria(criteria)
  const parts = []
  if (c.ffi_min !== null) parts.push(`FFI ≥ ${c.ffi_min}`)
  if (c.ffi_max !== null) parts.push(`FFI ≤ ${c.ffi_max}`)
  if (c.mscore_above !== null) parts.push(`M-Score > ${c.mscore_above}`)
  if (c.drift_min !== null) parts.push(`Drift ≥ ${c.drift_min}%`)
  if (c.sector) parts.push(c.sector)
  if (c.kind === 'company') parts.push('Companies')
  if (c.kind === 'index') parts.push('Indices')
  if (c.critical_only) parts.push('Critical flag')
  return parts.length ? parts.join(' · ') : 'All companies'
}
```

**File:** `frontend/src/composables/useScreens.js`
```js
import { ref } from 'vue'
import { workspaceApi } from '../api/workspace.js'
import { useToasts } from './useToasts.js'

const screens = ref([])
const state = ref('idle')

const load = async () => {
  state.value = 'loading'
  try {
    screens.value = await workspaceApi.listScreens()
    state.value = 'ready'
  } catch {
    state.value = 'error'
  }
}

const save = async (name, criteria) => {
  const { push } = useToasts()
  try {
    const screen = await workspaceApi.createScreen(name, criteria)
    screens.value = [...screens.value, screen]
    push(`Saved screen “${screen.name}”`)
    return screen
  } catch (err) {
    push(`Could not save screen: ${err.message}`, { tone: 'error' })
    return null
  }
}

const remove = async (id) => {
  const { push } = useToasts()
  const before = screens.value
  const removed = before.find((s) => s.id === id)
  screens.value = before.filter((s) => s.id !== id)
  try {
    await workspaceApi.deleteScreen(id)
    if (removed) push(`Deleted “${removed.name}”`, { action: { label: 'Undo', run: () => save(removed.name, removed.criteria) } })
  } catch (err) {
    screens.value = before
    push(`Could not delete screen: ${err.message}`, { tone: 'error' })
  }
}

export function useScreens () {
  return { screens, state, load, save, remove }
}
```

**File:** `frontend/src/components/portfolio/ScreenerView.vue`
```vue
<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { Download, Trash2 } from 'lucide-vue-next'
import Panel from '../ui/Panel.vue'
import DataTable from '../ui/DataTable.vue'
import { useScreens } from '../../composables/useScreens.js'
import { useCompany } from '../../composables/useCompany.js'
import { companyProfiles } from '../../data/companyProfiles.js'
import { applyScreen, sectorsOf, describeCriteria, normalizeCriteria, EMPTY_CRITERIA } from '../../utils/screen.js'
import { buildRedFlags } from '../overview/overviewModel.js'
import { MSCORE_THRESHOLD } from '../../utils/ffi.js'
import { toCsv, downloadCsv } from '../../utils/csv.js'

const emit = defineEmits(['open-company'])

const { screens, state: screensState, load, save, remove } = useScreens()
const { selectCompany } = useCompany()

onMounted(() => { if (screensState.value === 'idle') load() })

const universe = Object.values(companyProfiles)
const sectors = sectorsOf(universe)

const criteria = reactive({ ...EMPTY_CRITERIA })
const reset = () => Object.assign(criteria, EMPTY_CRITERIA)

const results = computed(() =>
  applyScreen(universe, criteria).map((p) => ({
    ticker: p.ticker,
    name: p.name,
    sector: p.sector,
    ffi: p.ffi,
    mscore: p.mscore,
    drift: p.driftScore,
    critical: buildRedFlags(p).filter((f) => f.severity === 'critical').length
  }))
)

const columns = [
  { key: 'ticker', label: 'Ticker', sortable: true },
  { key: 'name', label: 'Company', sortable: true },
  { key: 'sector', label: 'Sector', sortable: true },
  { key: 'ffi', label: 'FFI', align: 'right', sortable: true },
  { key: 'mscore', label: 'M-Score', align: 'right', sortable: true, format: (v) => v?.toFixed(2) ?? '—' },
  { key: 'drift', label: 'Drift', align: 'right', sortable: true, format: (v) => (v == null ? '—' : `${v}%`) },
  { key: 'critical', label: 'Critical', align: 'right', sortable: true }
]

const naming = ref(false)
const screenName = ref('')
const startSave = () => { naming.value = true; screenName.value = '' }
const confirmSave = async () => {
  const name = screenName.value.trim()
  if (!name) return
  if (await save(name, normalizeCriteria(criteria))) naming.value = false
}

const loadScreen = (screen) => Object.assign(criteria, EMPTY_CRITERIA, screen.criteria)

const open = (row) => {
  selectCompany(row.ticker)
  emit('open-company')
}

const exportCsv = () =>
  downloadCsv('zaisaku-screen.csv', toCsv(columns.map((c) => ({ label: c.label, key: c.key })), results.value))

const kinds = [
  { id: 'all', label: 'All' },
  { id: 'company', label: 'Companies' },
  { id: 'index', label: 'Indices' }
]
</script>

<template>
  <div class="grid grid-cols-1 xl:grid-cols-[300px_1fr] gap-3 p-3 items-start">
    <div class="space-y-3">
      <Panel title="Filters">
        <template #actions>
          <button type="button" class="btn-ghost" @click="reset">Reset</button>
        </template>
        <form class="p-3 space-y-3 text-xs" @submit.prevent>
          <fieldset class="space-y-1">
            <legend class="text-muted mb-1">Forensic fragility index</legend>
            <div class="flex items-center gap-2">
              <input v-model="criteria.ffi_min" type="number" min="0" max="100" class="field" placeholder="Min" aria-label="Minimum FFI" />
              <span class="text-faint">–</span>
              <input v-model="criteria.ffi_max" type="number" min="0" max="100" class="field" placeholder="Max" aria-label="Maximum FFI" />
            </div>
          </fieldset>
          <label class="block space-y-1">
            <span class="text-muted">M-Score above</span>
            <div class="flex items-center gap-2">
              <input v-model="criteria.mscore_above" type="number" step="0.01" min="-10" max="10" class="field" placeholder="e.g. -1.78" />
              <button type="button" class="btn shrink-0" @click="criteria.mscore_above = MSCORE_THRESHOLD">{{ MSCORE_THRESHOLD }}</button>
            </div>
          </label>
          <label class="block space-y-1">
            <span class="text-muted">Language drift at least (%)</span>
            <input v-model="criteria.drift_min" type="number" min="0" max="100" class="field" placeholder="e.g. 15" />
          </label>
          <label class="block space-y-1">
            <span class="text-muted">Sector</span>
            <select v-model="criteria.sector" class="field cursor-pointer">
              <option :value="null">All sectors</option>
              <option v-for="s in sectors" :key="s" :value="s">{{ s }}</option>
            </select>
          </label>
          <fieldset>
            <legend class="text-muted mb-1">Type</legend>
            <div class="inline-flex rounded border border-line overflow-hidden" role="radiogroup">
              <button
                v-for="k in kinds"
                :key="k.id"
                type="button"
                role="radio"
                :aria-checked="criteria.kind === k.id"
                class="h-7 px-2.5 text-xs cursor-pointer"
                :class="criteria.kind === k.id ? 'bg-accent text-white' : 'bg-panel text-muted hover:text-fg'"
                @click="criteria.kind = k.id"
              >{{ k.label }}</button>
            </div>
          </fieldset>
          <label class="flex items-center gap-2 cursor-pointer">
            <input v-model="criteria.critical_only" type="checkbox" class="accent-[var(--accent)]" />
            <span>Has a critical red flag</span>
          </label>
        </form>
      </Panel>

      <Panel title="Saved screens" :state="screensState === 'error' ? 'error' : screensState === 'ready' && !screens.length ? 'empty' : screensState === 'ready' ? 'ready' : 'loading'" empty-text="No saved screens yet." error-text="Could not load saved screens." @retry="load">
        <ul class="divide-y divide-[var(--border)]">
          <li v-for="s in screens" :key="s.id" class="flex items-center gap-2 px-3 py-2">
            <button type="button" class="flex-1 text-left min-w-0 cursor-pointer" :aria-label="`Load screen ${s.name}: ${describeCriteria(s.criteria)}`" @click="loadScreen(s)">
              <span class="block text-xs font-medium text-fg truncate">{{ s.name }}</span>
              <span class="block text-[11px] text-muted truncate">{{ describeCriteria(s.criteria) }}</span>
            </button>
            <button type="button" class="btn-icon w-6 h-6" :aria-label="`Delete screen ${s.name}`" @click="remove(s.id)">
              <Trash2 class="w-3.5 h-3.5" />
            </button>
          </li>
        </ul>
      </Panel>
    </div>

    <Panel :title="`Results · ${results.length} of ${universe.length}`" :state="results.length ? 'ready' : 'empty'" empty-text="No companies match these filters.">
      <template #actions>
        <form v-if="naming" class="flex items-center gap-1" @submit.prevent="confirmSave">
          <input v-model="screenName" class="field h-6 w-40" maxlength="80" placeholder="Screen name" aria-label="Screen name" @keydown.esc="naming = false" />
          <button type="submit" class="btn-primary h-6" :disabled="!screenName.trim()">Save</button>
          <button type="button" class="btn-ghost" @click="naming = false">Cancel</button>
        </form>
        <template v-else>
          <span class="hidden lg:inline text-[11px] text-faint mr-1">{{ describeCriteria(criteria) }}</span>
          <button type="button" class="btn-ghost" @click="startSave">Save screen</button>
          <button type="button" class="btn-ghost" :disabled="!results.length" @click="exportCsv"><Download class="w-3.5 h-3.5" /> CSV</button>
        </template>
      </template>
      <DataTable :columns="columns" :rows="results" row-key="ticker" clickable :initial-sort="{ key: 'ffi', dir: 'desc' }" @row-click="open">
        <template #cell-ticker="{ value }"><span class="font-mono font-semibold">{{ value }}</span></template>
        <template #cell-sector="{ value }"><span class="text-muted">{{ value }}</span></template>
        <template #cell-critical="{ value }"><span :class="value ? 'text-critical font-semibold' : 'text-muted'">{{ value }}</span></template>
      </DataTable>
    </Panel>
  </div>
</template>
```

**File:** `frontend/src/components/portfolio/ScreenerView.test.js`
```js
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'

describe('ScreenerView', () => {
  beforeEach(() => {
    vi.resetModules()
    vi.stubGlobal('fetch', vi.fn(async () => ({ ok: true, status: 200, json: async () => [] })))
  })

  it('narrows results as filters change', async () => {
    const { default: ScreenerView } = await import('./ScreenerView.vue')
    const w = mount(ScreenerView)
    await flushPromises()
    const before = w.findAll('tbody tr').length
    await w.find('input[type="checkbox"]').setValue(true)
    const after = w.findAll('tbody tr').map((tr) => tr.attributes('data-row'))
    expect(after.length).toBeLessThan(before)
    expect(after).toContain('SMCI')
  })

  it('saves the current criteria under a name', async () => {
    const fetchMock = vi.fn(async (url, opts = {}) =>
      opts.method === 'POST'
        ? { ok: true, status: 201, json: async () => ({ id: 's1', ...JSON.parse(opts.body), created_at: 't' }) }
        : { ok: true, status: 200, json: async () => [] })
    vi.stubGlobal('fetch', fetchMock)
    const { default: ScreenerView } = await import('./ScreenerView.vue')
    const w = mount(ScreenerView)
    await flushPromises()
    await w.find('input[aria-label="Minimum FFI"]').setValue('50')
    await w.findAll('button').find((b) => b.text() === 'Save screen').trigger('click')
    await w.find('input[aria-label="Screen name"]').setValue('High risk')
    await w.find('input[aria-label="Screen name"]').element.form.dispatchEvent(new Event('submit'))
    await flushPromises()
    const post = fetchMock.mock.calls.find(([, o]) => o?.method === 'POST')
    expect(JSON.parse(post[1].body)).toMatchObject({ name: 'High risk', criteria: { ffi_min: 50, kind: 'all' } })
    expect(w.text()).toContain('High risk')
  })
})
```

- [ ] `CompanyHub.vue`: add tab `{ id: 'screener', label: 'Screener', section: 'portfolio' }` and `<ScreenerView v-else-if="currentTab === 'screener'" key="screener" @open-company="currentTab = 'overview'" />`.
- [ ] `npm test && npm run build`. Browser: filter to critical flags → SMCI/COIN; save the screen, reload, load it, delete it, Undo.
- [ ] Commit `feat(ui): screener with saved screens`.

---

## PR 5 — `feat/compare`

**File:** `frontend/src/utils/compare.test.js`
```js
import { describe, it, expect } from 'vitest'
import { compareRows, parseCompareHash, formatCompareHash, MAX_COMPARE } from './compare.js'
import { companyProfiles } from '../data/companyProfiles.js'

const { NVDA, SMCI } = companyProfiles

describe('compareRows', () => {
  it('marks the worst numeric value per row', () => {
    const rows = compareRows([NVDA, SMCI])
    const ffi = rows.find((r) => r.key === 'ffi')
    expect(ffi.values).toEqual([String(NVDA.ffi), String(SMCI.ffi)])
    expect(ffi.worstIndex).toBe(1)
    expect(rows.find((r) => r.key === 'mscore').worstIndex).toBe(1)
  })
  it('does not mark text rows or ties', () => {
    const rows = compareRows([NVDA, NVDA])
    expect(rows.find((r) => r.key === 'ffi').worstIndex).toBeNull()
    expect(rows.find((r) => r.key === 'auditor').worstIndex).toBeNull()
  })
  it('shows a dash for missing values', () => {
    const rows = compareRows([{ ...NVDA, mscore: null }, SMCI])
    expect(rows.find((r) => r.key === 'mscore').values[0]).toBe('—')
  })
})

describe('compare hash', () => {
  it('parses, normalises, dedupes and caps tickers', () => {
    expect(parseCompareHash('#compare=nvda,SMCI,nvda,amd,aapl,msft')).toEqual(['NVDA', 'SMCI', 'AMD', 'AAPL'].slice(0, MAX_COMPARE))
  })
  it('ignores other hashes', () => {
    expect(parseCompareHash('#other')).toBeNull()
    expect(parseCompareHash('')).toBeNull()
  })
  it('formats', () => {
    expect(formatCompareHash(['NVDA', 'SMCI'])).toBe('#compare=NVDA,SMCI')
  })
})
```

**File:** `frontend/src/utils/compare.js`
```js
import { buildRedFlags } from '../components/overview/overviewModel.js'

export const MAX_COMPARE = 4

const criticalCount = (p) => buildRedFlags(p).filter((f) => f.severity === 'critical').length
const footnoteFlags = (p) => (p.footnotesClean === false ? (p.footnoteCount ?? 0) : 0)

// worse: 'high' marks the largest value as worst; null = descriptive row.
const METRICS = [
  { key: 'ffi', label: 'Forensic fragility index', get: (p) => p.ffi, worse: 'high' },
  { key: 'mscore', label: 'Beneish M-Score', get: (p) => p.mscore, worse: 'high', format: (v) => v.toFixed(2) },
  { key: 'drift', label: 'Language drift', get: (p) => p.driftScore, worse: 'high', format: (v) => `${v}%` },
  { key: 'decoupling', label: 'Call vs 10-Q decoupling', get: (p) => p.divergenceScore, worse: 'high' },
  { key: 'footnotes', label: 'Footnote flags', get: footnoteFlags, worse: 'high' },
  { key: 'critical', label: 'Critical red flags', get: criticalCount, worse: 'high' },
  { key: 'auditor', label: 'Auditor', get: (p) => p.auditor, worse: null },
  { key: 'period', label: 'Period', get: (p) => p.period, worse: null }
]

export function compareRows (profiles) {
  return METRICS.map((m) => {
    const raw = profiles.map((p) => m.get(p) ?? null)
    const values = raw.map((v) => (v === null ? '—' : m.format ? m.format(v) : String(v)))
    let worstIndex = null
    if (m.worse) {
      const nums = raw.map((v) => (typeof v === 'number' ? v : null))
      const valid = nums.filter((v) => v !== null)
      if (valid.length > 1 && Math.max(...valid) !== Math.min(...valid)) worstIndex = nums.indexOf(Math.max(...valid))
    }
    return { key: m.key, label: m.label, values, worstIndex, numeric: Boolean(m.worse) }
  })
}

export function parseCompareHash (hash) {
  const match = /^#compare=([A-Za-z0-9.,-]*)$/.exec(hash || '')
  if (!match) return null
  const tickers = match[1].split(',').map((t) => t.trim().toUpperCase()).filter(Boolean)
  return [...new Set(tickers)].slice(0, MAX_COMPARE)
}

export const formatCompareHash = (tickers) => `#compare=${tickers.join(',')}`
```

**File:** `frontend/src/components/portfolio/CompareView.vue`
```vue
<script setup>
import { ref, computed, watch, onUnmounted } from 'vue'
import { X } from 'lucide-vue-next'
import Panel from '../ui/Panel.vue'
import DataTable from '../ui/DataTable.vue'
import SeverityDot from '../ui/SeverityDot.vue'
import { useCompany } from '../../composables/useCompany.js'
import { useWatchlist } from '../../composables/useWatchlist.js'
import { companyProfiles } from '../../data/companyProfiles.js'
import { buildRedFlags } from '../overview/overviewModel.js'
import { compareRows, parseCompareHash, formatCompareHash, MAX_COMPARE } from '../../utils/compare.js'

const emit = defineEmits(['open-company'])

const { currentCompany, selectCompany } = useCompany()
const { tickers: watched } = useWatchlist()

const covered = (t) => Boolean(companyProfiles[t])

const initial = () => {
  const fromHash = (parseCompareHash(window.location.hash) ?? []).filter(covered)
  if (fromHash.length) return fromHash
  return covered(currentCompany.value.ticker) ? [currentCompany.value.ticker] : []
}

const selected = ref(initial())

watch(selected, (list) => {
  window.history.replaceState(null, '', `${window.location.pathname}${window.location.search}${formatCompareHash(list)}`)
}, { immediate: true, deep: true })

onUnmounted(() => {
  window.history.replaceState(null, '', `${window.location.pathname}${window.location.search}`)
})

const suggestions = computed(() => {
  const preferred = [currentCompany.value.ticker, ...watched.value].filter(covered)
  return [...new Set(preferred)].filter((t) => !selected.value.includes(t))
})
const others = computed(() =>
  Object.keys(companyProfiles).filter((t) => !selected.value.includes(t) && !suggestions.value.includes(t))
)

const addTicker = (event) => {
  const t = event.target.value
  event.target.value = ''
  if (t && selected.value.length < MAX_COMPARE && !selected.value.includes(t)) selected.value = [...selected.value, t]
}
const removeTicker = (t) => { selected.value = selected.value.filter((x) => x !== t) }

const profiles = computed(() => selected.value.map((t) => companyProfiles[t]))
const rows = computed(() =>
  compareRows(profiles.value).map((r) => ({
    key: r.key,
    label: r.label,
    worstIndex: r.worstIndex,
    numeric: r.numeric,
    ...Object.fromEntries(r.values.map((v, i) => [`v${i}`, v]))
  }))
)
const columns = computed(() => [
  { key: 'label', label: 'Metric' },
  ...selected.value.map((t, i) => ({ key: `v${i}`, label: t, align: 'right' }))
])

const flagsFor = (p) => buildRedFlags(p)

const openCompany = (t) => {
  selectCompany(t)
  emit('open-company')
}
</script>

<template>
  <div class="p-3 space-y-3">
    <div class="flex flex-wrap items-center gap-2">
      <span v-for="t in selected" :key="t" class="inline-flex items-center gap-1 h-7 pl-2.5 pr-1 rounded border border-line bg-panel text-xs">
        <button type="button" class="font-mono font-semibold hover:text-accent cursor-pointer" :title="`Open ${companyProfiles[t].name}`" @click="openCompany(t)">{{ t }}</button>
        <button type="button" class="btn-icon w-5 h-5" :aria-label="`Remove ${t} from comparison`" @click="removeTicker(t)"><X class="w-3 h-3" /></button>
      </span>
      <select
        v-if="selected.length < MAX_COMPARE"
        class="field w-48 cursor-pointer"
        aria-label="Add company to comparison"
        @change="addTicker"
      >
        <option value="">Add company…</option>
        <optgroup v-if="suggestions.length" label="Current & watchlist">
          <option v-for="t in suggestions" :key="t" :value="t">{{ t }} · {{ companyProfiles[t].name }}</option>
        </optgroup>
        <optgroup label="Coverage">
          <option v-for="t in others" :key="t" :value="t">{{ t }} · {{ companyProfiles[t].name }}</option>
        </optgroup>
      </select>
      <span class="text-[11px] text-faint">Up to {{ MAX_COMPARE }} companies. The worst value in each row is highlighted.</span>
    </div>

    <Panel title="Comparison" :state="selected.length >= 2 ? 'ready' : 'empty'" empty-text="Add at least two companies to compare.">
      <DataTable :columns="columns" :rows="rows" row-key="key">
        <template #cell-label="{ value }"><span class="text-muted">{{ value }}</span></template>
        <template v-for="(t, i) in selected" :key="t" #[`cell-v${i}`]="{ row, value }">
          <span :class="[row.worstIndex === i ? 'text-critical font-semibold' : '', row.numeric ? '' : '[font-variant-numeric:normal]']" :data-worst="row.worstIndex === i || undefined">{{ value }}</span>
        </template>
      </DataTable>
    </Panel>

    <div v-if="selected.length >= 2" class="grid gap-3" :class="selected.length === 2 ? 'md:grid-cols-2' : selected.length === 3 ? 'md:grid-cols-3' : 'md:grid-cols-2 xl:grid-cols-4'">
      <Panel v-for="p in profiles" :key="p.ticker" :title="`${p.ticker} red flags`">
        <ul class="divide-y divide-[var(--border)]">
          <li v-for="f in flagsFor(p)" :key="f.id" class="flex items-start gap-2 px-3 py-2 text-xs">
            <SeverityDot :level="f.severity" class="mt-1" />
            <span class="flex-1">{{ f.finding }}</span>
          </li>
        </ul>
      </Panel>
    </div>
  </div>
</template>
```

**File:** `frontend/src/components/portfolio/CompareView.test.js`
```js
import { describe, it, expect, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import CompareView from './CompareView.vue'

describe('CompareView', () => {
  beforeEach(() => window.history.replaceState(null, '', '/#compare=NVDA,SMCI'))

  it('reads tickers from the hash and highlights the worst value', () => {
    const w = mount(CompareView)
    expect(w.findAll('thead th').map((th) => th.text())).toEqual(['Metric', 'NVDA', 'SMCI'])
    const ffiRow = w.find('[data-row="ffi"]')
    expect(ffiRow.findAll('[data-worst]')).toHaveLength(1)
    expect(ffiRow.find('[data-worst]').text()).toBe(String(84))
  })

  it('keeps the hash in sync when removing a company', async () => {
    const w = mount(CompareView)
    await w.find('button[aria-label="Remove SMCI from comparison"]').trigger('click')
    expect(window.location.hash).toBe('#compare=NVDA')
    expect(w.text()).toContain('Add at least two companies to compare.')
  })
})
```

- [ ] `CompanyHub.vue`:
  - Add tab `{ id: 'compare', label: 'Compare', section: 'portfolio' }` and `<CompareView v-else-if="currentTab === 'compare'" key="compare" @open-company="currentTab = 'overview'" />`.
  - Initial tab: `const currentTab = ref(parseCompareHash(window.location.hash) ? 'compare' : 'overview')` with `import { parseCompareHash } from '../utils/compare.js'`.
- [ ] `npm test && npm run build`. Browser: open `/#compare=NVDA,SMCI,COIN`, add AMD, remove one, copy the URL into a new tab and check it restores; open a chip → Overview, and the hash is cleared.
- [ ] Commit `feat(ui): side-by-side company compare`.

---

## PR 6 — `feat/shortcuts`

**File:** `frontend/src/composables/useShortcuts.test.js`
```js
import { describe, it, expect, vi } from 'vitest'
import { createShortcutMatcher, installShortcuts, onShortcut, SHORTCUTS } from './useShortcuts.js'

const clock = () => {
  let t = 0
  return { now: () => t, advance: (ms) => { t += ms } }
}

describe('createShortcutMatcher', () => {
  it('matches single keys and two-key sequences', () => {
    const c = clock()
    const match = createShortcutMatcher(SHORTCUTS, { now: c.now })
    expect(match('j')).toBe('flag-next')
    expect(match('g')).toBeNull()
    expect(match('o')).toBe('go-overview')
  })
  it('drops a pending prefix after the timeout', () => {
    const c = clock()
    const match = createShortcutMatcher(SHORTCUTS, { now: c.now, timeout: 1000 })
    match('g')
    c.advance(1500)
    expect(match('o')).toBeNull()
  })
  it('recovers when a prefix is followed by an unrelated key', () => {
    const match = createShortcutMatcher(SHORTCUTS, { now: () => 0 })
    match('g')
    expect(match('j')).toBe('flag-next')
    expect(match('x')).toBeNull()
  })
})

describe('installShortcuts', () => {
  it('dispatches to subscribers, ignores typing and modifiers', () => {
    const target = document.createElement('div')
    document.body.appendChild(target)
    const uninstall = installShortcuts(target)
    const spy = vi.fn()
    const off = onShortcut('flag-next', spy)

    target.dispatchEvent(new KeyboardEvent('keydown', { key: 'j', bubbles: true }))
    expect(spy).toHaveBeenCalledTimes(1)

    const input = document.createElement('input')
    target.appendChild(input)
    input.dispatchEvent(new KeyboardEvent('keydown', { key: 'j', bubbles: true }))
    target.dispatchEvent(new KeyboardEvent('keydown', { key: 'j', ctrlKey: true, bubbles: true }))
    expect(spy).toHaveBeenCalledTimes(1)

    off()
    uninstall()
  })
})
```

**File:** `frontend/src/composables/useShortcuts.js`
```js
export const SHORTCUTS = [
  { keys: 'g o', action: 'go-overview', label: 'Go to Overview' },
  { keys: 'g w', action: 'go-watchlist', label: 'Go to Watchlist' },
  { keys: 'g s', action: 'go-screener', label: 'Go to Screener' },
  { keys: 'g c', action: 'go-compare', label: 'Go to Compare' },
  { keys: 'g f', action: 'go-filings', label: 'Go to Filings' },
  { keys: '/', action: 'open-switcher', label: 'Switch company' },
  { keys: 'j', action: 'flag-next', label: 'Next red flag' },
  { keys: 'k', action: 'flag-prev', label: 'Previous red flag' },
  { keys: 'r', action: 'flag-reviewed', label: 'Mark selected flag reviewed' },
  { keys: '?', action: 'help', label: 'Show keyboard shortcuts' }
]

export function createShortcutMatcher (bindings, { timeout = 1000, now = () => Date.now() } = {}) {
  const sequences = bindings.map((b) => ({ keys: b.keys.split(' '), action: b.action }))
  let buffer = []
  let last = 0

  const exactMatch = (keys) => sequences.find((s) => s.keys.length === keys.length && s.keys.every((k, i) => k === keys[i]))
  const isPrefix = (keys) => sequences.some((s) => s.keys.length > keys.length && keys.every((k, i) => s.keys[i] === k))

  return (key) => {
    const t = now()
    if (t - last > timeout) buffer = []
    last = t

    const candidate = [...buffer, key]
    const exact = exactMatch(candidate)
    if (exact) {
      buffer = []
      return exact.action
    }
    if (isPrefix(candidate)) {
      buffer = candidate
      return null
    }
    // Not part of the pending sequence: start over from this key alone.
    buffer = []
    const single = exactMatch([key])
    if (single) return single.action
    if (isPrefix([key])) buffer = [key]
    return null
  }
}

const isTyping = (el) => {
  if (!el || !el.tagName) return false
  return ['INPUT', 'TEXTAREA', 'SELECT'].includes(el.tagName) || el.isContentEditable
}

const handlers = new Map()

export function onShortcut (action, fn) {
  if (!handlers.has(action)) handlers.set(action, new Set())
  handlers.get(action).add(fn)
  return () => handlers.get(action)?.delete(fn)
}

export function dispatchShortcut (action) {
  const set = handlers.get(action)
  if (!set || !set.size) return false
  set.forEach((fn) => fn())
  return true
}

export function installShortcuts (target = window) {
  const match = createShortcutMatcher(SHORTCUTS)
  const onKeydown = (e) => {
    if (e.ctrlKey || e.metaKey || e.altKey || e.key === 'Shift' || isTyping(e.target)) return
    const action = match(e.key)
    if (action && dispatchShortcut(action)) e.preventDefault()
  }
  target.addEventListener('keydown', onKeydown)
  return () => target.removeEventListener('keydown', onKeydown)
}
```

**File:** `frontend/src/components/shell/ShortcutHelp.vue`
```vue
<script setup>
import { ref, watch, nextTick } from 'vue'
import { X } from 'lucide-vue-next'
import { SHORTCUTS } from '../../composables/useShortcuts.js'

const props = defineProps({ open: { type: Boolean, default: false } })
const emit = defineEmits(['close'])

const closeButton = ref(null)
watch(() => props.open, async (isOpen) => {
  if (isOpen) {
    await nextTick()
    closeButton.value?.focus()
  }
})
</script>

<template>
  <div v-if="open" class="fixed inset-0 z-[60] flex items-center justify-center bg-[rgb(0_0_0/0.5)] p-4" @click.self="emit('close')" @keydown.esc="emit('close')">
    <div role="dialog" aria-modal="true" aria-labelledby="shortcut-help-title" class="w-full max-w-md rounded-md border border-line bg-panel text-fg shadow-xl">
      <header class="flex items-center justify-between h-10 px-4 border-b border-line">
        <h2 id="shortcut-help-title" class="text-sm font-semibold">Keyboard shortcuts</h2>
        <button ref="closeButton" type="button" class="btn-icon" aria-label="Close" @click="emit('close')"><X class="w-3.5 h-3.5" /></button>
      </header>
      <dl class="p-4 grid grid-cols-[auto_1fr] gap-x-6 gap-y-2 text-xs">
        <template v-for="s in SHORTCUTS" :key="s.action">
          <dt class="flex gap-1">
            <kbd v-for="k in s.keys.split(' ')" :key="k" class="min-w-6 h-6 px-1.5 inline-flex items-center justify-center rounded border border-line bg-raised font-mono text-[11px]">{{ k }}</kbd>
          </dt>
          <dd class="self-center text-muted">{{ s.label }}</dd>
        </template>
        <dt class="flex gap-1"><kbd class="h-6 px-1.5 inline-flex items-center rounded border border-line bg-raised font-mono text-[11px]">⌘K</kbd></dt>
        <dd class="self-center text-muted">Command palette</dd>
      </dl>
    </div>
  </div>
</template>
```

Wiring:
- [ ] `CompanyHub.vue`:
  - `import { installShortcuts, onShortcut } from '../composables/useShortcuts.js'` and `import ShortcutHelp from './shell/ShortcutHelp.vue'`.
  - `const showShortcutHelp = ref(false)`.
  - In `onMounted`: `const uninstall = installShortcuts()` and register `onShortcut('go-overview', () => { currentTab.value = 'overview' })`, the same for watchlist, screener, compare and filings, plus `onShortcut('help', () => { showShortcutHelp.value = true })`. Collect the unsubscribe functions and the `uninstall` and call them all in `onUnmounted`.
  - Render `<ShortcutHelp :open="showShortcutHelp" @close="showShortcutHelp = false" />` next to the other modals.
- [ ] `CompanySwitcher.vue`: in `onMounted`, `const off = onShortcut('open-switcher', openMenu)`; call it in `onUnmounted`.
- [ ] `OverviewDashboard.vue`:
  - `const selectedFlag = ref(0)`.
  - `const selectedFlagId = computed(() => flagRows.value[selectedFlag.value]?.id ?? null)`.
  - Register `onShortcut('flag-next', () => { selectedFlag.value = Math.min(selectedFlag.value + 1, flagRows.value.length - 1) })` and `onShortcut('flag-prev', () => { selectedFlag.value = Math.max(selectedFlag.value - 1, 0) })`.
  - Register `onShortcut('flag-reviewed', () => { const row = flagRows.value[selectedFlag.value]; if (row) { setReview(props.company.ticker, row.id, 'reviewed', row.note); useToasts().push(`Marked “${FLAG_LABELS[row.id]}” reviewed`) } })`.
  - Register all three in `onMounted` and unregister in `onUnmounted`; reset `selectedFlag` to 0 when `company.ticker` changes.
  - Pass `:highlight="selectedFlagId"` to the red flags DataTable.
- [ ] Peers panel action: `<button type="button" class="btn-ghost" :disabled="!peers.length" @click="exportPeers"><Download class="w-3.5 h-3.5" /> CSV</button>` with `const exportPeers = () => downloadCsv(\`zaisaku-peers-${props.company.ticker}.csv\`, toCsv(peerColumns.map((c) => ({ label: c.label, key: c.key })), peers.value))`.
- [ ] TopBar ⌘K button title becomes `"Command palette (⌘K) · Press ? for shortcuts"`.
- [ ] `npm test && npm run build`. Browser: `?` opens help, `g w` → Watchlist, `g o` → Overview, `j j r` marks the second flag reviewed with a toast, `/` opens the switcher, and typing in the note textarea doesn't trigger shortcuts.
- [ ] Commit `feat(ui): keyboard shortcuts, help overlay, and peers CSV`.

---

## Self-review

- **Spec coverage:**
  - §1 backend → PR 1 ✔ (including `/flags` list-all, needed for portfolio counts)
  - §2 composables and utils → PRs 2–6 ✔
  - §3 UI views → PRs 2–6 ✔ (switcher stars dropped, as the spec states)
  - §4 tests → each PR ✔
  - §5 delivery order → ✔
- **Placeholders:** none. Wiring steps name exact files, props and handlers.
- **Name consistency:**
  - `workspaceApi.*`, `useWatchlist().toggle/isWatched`, `useFlagReviews().reviewFor/reviewsFor/setReview`, `useNotes().notesFor/stateFor`
  - `portfolioRow`/`unresolvedCount`, `applyScreen`/`normalizeCriteria`/`describeCriteria`, `compareRows`/`parseCompareHash`/`formatCompareHash`
  - `onShortcut`/`installShortcuts`, `FLAG_LABELS`/`REVIEW_STATUSES`
