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
