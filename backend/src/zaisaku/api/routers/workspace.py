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
