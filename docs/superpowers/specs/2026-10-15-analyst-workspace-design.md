# Analyst Workspace Features — Design

**Date:** 2026-10-15
**Status:** Approved in brainstorming

## Problem

After the phase 1 redesign, Zaisaku looks professional but feels "pale". It is read-only: the analyst can look at a company but can't track companies, filter the universe, compare companies, or record their own judgement. Competitors (Hudson Labs, Ideagen AQRM, Koyfin, AlphaSense, Transparently.AI) all offer watchlists, screening, comparison, and annotation workflows.

## Scope (approved)

1. Backend workspace store + API (SQLite, no new dependency).
2. Watchlist with a portfolio risk table.
3. Flag triage (status + note per red flag) and company notes, both included in the memo.
4. Screener with saved screens.
5. Compare (2–4 companies side by side).
6. Small things: keyboard shortcuts with a help overlay, CSV export, and toasts with undo.

Out of scope:
- **Score alerts.** Fixture scores never change, so alerts would never fire.
- **Score history.** No historical data exists.
- **User accounts.**

## Data honesty rules

- Watchlist, Screener, and Compare metrics come only from the 20 profiled companies in `src/data/companyProfiles.js` ("coverage universe").
- Tickers outside coverage show `—` and the label "Not in coverage". Synthetic search profiles never feed portfolio views.
- Everything the analyst writes is user data and is stored as entered.

## 1. Backend

**Package `zaisaku/workspace/`:**
- `store.py`: `WorkspaceStore(db_path)` on stdlib `sqlite3`. One connection with `check_same_thread=False`, guarded by a `threading.Lock`. Schema is created on open.
- `memo.py`: `render_analyst_review(reviews, notes) -> str`, the Markdown section appended to memo export.

**Tables:**

| Table | Columns |
|---|---|
| `watchlist` | `ticker` PK, `added_at` |
| `screens` | `id` (uuid hex) PK, `name`, `criteria` (JSON), `created_at` |
| `flag_reviews` | (`ticker`, `flag_id`) PK, `status` ∈ open/reviewed/escalated/dismissed, `note`, `updated_at` |
| `notes` | `id` (uuid hex) PK, `ticker`, `body`, `created_at`, `updated_at` |

**Config:** `workspace_db_path` (env `WORKSPACE_DB_PATH`). When empty, it defaults to `{upload_dir}/workspace.db`, which is already in the Docker volume.

**Routes** (prefix `/api/workspace`):

| Method & path | Result |
|---|---|
| `GET /watchlist` | list |
| `PUT /watchlist/{ticker}` | entry (idempotent) |
| `DELETE /watchlist/{ticker}` | 204, or 404 if absent |
| `GET /screens` | list |
| `POST /screens` | 201 |
| `DELETE /screens/{id}` | 204 or 404 |
| `GET /flags` | all reviews |
| `GET /flags/{ticker}` | reviews for one ticker |
| `PUT /flags/{ticker}/{flag_id}` | upsert |
| `GET /notes/{ticker}` | newest first |
| `POST /notes/{ticker}` | 201 |
| `PATCH /notes/{ticker}/{id}` | updated note, or 404 |
| `DELETE /notes/{ticker}/{id}` | 204 or 404 |

**Validation:**
- Tickers are uppercased and must match `^[A-Z0-9.\-]{1,10}$`.
- `flag_id` must match `^[a-z0-9_-]{1,40}$`.
- Note and review note are at most 5,000 characters; note body must not be blank.
- Screen name is 1–80 characters.
- Screen criteria use a strict schema with `extra="forbid"`:
  - `ffi_min` / `ffi_max` 0–100
  - `mscore_above` −10…10
  - `drift_min` 0–100
  - `sector` ≤ 120 characters
  - `kind` ∈ all/company/index
  - `critical_only` bool

**Memo:** `POST /api/forensics/report/download` appends `render_analyst_review(...)` for the ticker. The section is omitted when there are no reviews or notes.

**Known limit:** with no authentication, all users of one deployment share one workspace. Notes carry timestamps but no author.

## 2. Frontend architecture

| Path | Responsibility |
|---|---|
| `src/api/workspace.js` | `fetch` wrapper for `/api/workspace`, throws `Error(detail)` on non-2xx |
| `src/composables/useToasts.js` + `components/shell/ToastHost.vue` | Transient messages (`info`/`error`), optional action (Undo), auto-dismiss after 5s, `aria-live="polite"` |
| `src/composables/useWatchlist.js` | Watched tickers; `load`, `isWatched`, `toggle` (optimistic, rolls back + error toast) |
| `src/composables/useFlagReviews.js` | All reviews; `load`, `reviewFor(ticker, flagId)`, `setReview` (optimistic) |
| `src/composables/useNotes.js` | Notes per ticker; `load(ticker)`, `add`, `update`, `remove` (undo re-creates) |
| `src/composables/useScreens.js` | Saved screens; `load`, `save`, `remove` |
| `src/utils/csv.js` | `toCsv(columns, rows)` (RFC 4180 quoting), `downloadCsv(name, text)` |
| `src/utils/portfolio.js` | `portfolioRow(ticker, profile, reviews)` → metrics plus `unresolved` count |
| `src/utils/screen.js` | `applyScreen(profiles, criteria)`, `sectorsOf(profiles)` |
| `src/utils/compare.js` | `compareRows(profiles)` with worst-value index per metric; `parseCompareHash`, `formatCompareHash` |
| `src/composables/useShortcuts.js` | `createShortcutMatcher(bindings)` (pure) + global listener + `onShortcut(action, fn)` subscription |
| `components/portfolio/WatchlistView.vue`, `ScreenerView.vue`, `CompareView.vue` | Portfolio views |
| `components/overview/FlagNoteEditor.vue`, `NotesPanel.vue` | Triage UI |
| `components/shell/ShortcutHelp.vue` | Help overlay |

**Unresolved flag:** a red flag with severity watch or critical whose review status is missing, `open`, or `escalated`.

## 3. UI

**Navigation:**
- Tabs read `Overview · Financials · Trends & peers · Scenarios · Calls & Q&A · Filings │ Watchlist · Screener · Compare`. A divider separates the company tabs from the portfolio tabs.
- The CompanyStrip is hidden on the portfolio tabs.

**Watchlist:**
- The ☆/★ toggle is in the CompanyStrip only. Stars in switcher rows were dropped as a nested-button accessibility problem; YAGNI.
- Table columns: Ticker · Company · FFI · Critical · Watch · M-Score · Drift · Unresolved. Default sort is FFI descending.
- Row click opens the company Overview. Header actions: Export CSV.
- Removing a company from the watchlist shows a toast with Undo.

**Flag triage (Overview, Red flags panel):**
- Adds a Status `<select>` column and a Note button with a popover editor (Save/Cancel, Ctrl+Enter saves).
- Header toggle: "Hide dismissed". When shown, dismissed rows are dimmed.
- Controls stop click propagation so they don't open the flag's modal.

**Notes panel (Overview):**
- Composer with Ctrl+Enter, list of notes newest first with dates, inline edit, and delete with Undo.
- Layout: Peers spans 2 columns and Notes takes 1 at xl.

**Strip:** shows an "N unresolved" chip when N > 0.

**Memo:** the preview adds section "3. Analyst review" (reviews table + notes); the Markdown export gets the same section from the backend.

**Screener:**
- Filters panel (FFI min/max, M-Score above, drift ≥, sector select, kind, critical-only) plus a Results panel with a count, CSV export, and "Save screen" with an inline name field.
- A saved-screens list loads a screen into the filters or deletes it.

**Compare:**
- Up to 4 ticker chips plus an "Add company" select (current company and watchlist first).
- Metrics table: FFI, M-Score, drift, call-vs-10-Q decoupling, footnote flags, auditor, period. The worst numeric value in each row is shown in `text-critical`.
- Red flags per company are listed below.
- The URL hash `#compare=NVDA,SMCI` is kept in sync and opens Compare on load.

**Shortcuts:**

| Keys | Action |
|---|---|
| `g o` / `g w` / `g s` / `g c` / `g f` | Switch to Overview / Watchlist / Screener / Compare / Filings |
| `/` | Open the company switcher |
| `j` / `k` | Move the selected red flag |
| `r` | Mark the selected flag reviewed |
| `?` | Show the help overlay |
| `Esc` | Close the overlay |

Shortcuts are ignored while typing in an input, textarea, select, or contenteditable element, and when Ctrl, Meta, or Alt is held. `⌘K` is unchanged.

## 4. Errors & testing

- Workspace reads failing → the panel's error state with Retry. Research panels are unaffected.
- Writes are optimistic; on failure they roll back and show an error toast.
- Backend: pytest for the store (temp file + reopen persistence), API (status codes, validation 422s, 404s), the memo renderer, and memo download including the review section. An autouse conftest fixture points the workspace store at `:memory:` so tests never write into `uploads/`.
- Frontend: Vitest for csv, portfolio, screen, compare, the shortcut matcher, composables with mocked `fetch` (rollback paths), and components (watchlist table, flag status change, notes add/delete/undo, compare worst highlight). Plus headless browser checks with the backend running locally.

## 5. Delivery

Each PR is CI-gated, then squash-merged.

1. `feat/workspace-api`: backend store, routes, memo section, tests.
2. `feat/watchlist`: API client, toasts, `useWatchlist`, `useFlagReviews` (read), CSV util, portfolio util, strip star, nav sections, WatchlistView.
3. `feat/flag-triage-notes`: status/note in Red flags, NotesPanel, unresolved chip, memo preview section.
4. `feat/screener`: screen util, `useScreens`, ScreenerView.
5. `feat/compare`: compare util, CompareView, hash sync.
6. `feat/shortcuts`: matcher, listener, help overlay, j/k/r flag navigation, peers CSV.
