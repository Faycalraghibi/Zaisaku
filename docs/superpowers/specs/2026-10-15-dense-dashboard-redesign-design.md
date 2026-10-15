# Dense Dashboard Redesign — Phase 1 Design

**Date:** 2026-10-15
**Status:** Approved in brainstorming, pending written-spec review

## Problem

The current UI reads as generic AI output: glass blur, glow rings, a different accent colour per card, rounded-3xl hero cards, in-app marketing prose, and inflated feature names. Zaisaku ships to a client, so it has to look like a professional research tool.

## Reference products (patterns only — no logos, colours, or names copied)

| Product | Pattern borrowed |
|---|---|
| Koyfin | Grid of compact widget panels with header bars; light/dark themes; dense tables |
| Hudson Labs | Tables where each finding carries a source chip linking to the filing; single slim search |
| Transparently.AI | Score broken down into per-category components |
| Ideagen Audit Analytics (AQRM) | Red-flag list with drill-down into the detail behind each flag |

Hudson Labs sells an AI tool named "Co-Analyst". Zaisaku's assistant is renamed **Ask Zaisaku** to avoid the collision.

## Decisions

- Direction: **dense dashboard** (Koyfin-style widget panels).
- Scope: **phased**. Phase 1 = tokens, theme, primitives, shell, Overview. Later phases move the other 5 tabs and the modals onto the same primitives, one PR each.
- Theme: **dark + light**, defaulting to the OS setting.
- Copy: **plain names**.
- Approach: **CSS-variable tokens + an in-house widget kit**. No UI library dependency.

## 1. Visual system

**Tokens** (CSS variables in `frontend/src/style.css`, exposed to Tailwind v4 via `@theme inline`):

| Token | Dark | Light |
|---|---|---|
| `--bg` page | `#0f1115` | `#f6f7f9` |
| `--panel` | `#16181d` | `#ffffff` |
| `--raised` (hover, header) | `#1f2228` | `#f0f2f5` |
| `--border` hairline | `#2a2e36` | `#e2e5ea` |
| `--text` | `#e6e8eb` | `#14171c` |
| `--text-muted` | `#9aa1ac` | `#5d6470` |
| `--text-faint` | `#6b7280` | `#8a919c` |
| `--accent` (interactive only) | `#5b8def` | `#2f6fdb` |
| `--sev-good` | `#3fb68b` | `#1f8a62` |
| `--sev-watch` | `#e0a83a` | `#b57b10` |
| `--sev-critical` | `#e5534b` | `#c9372c` |

Rules:
- Severity colours are used only for severity, never for decoration.
- No `backdrop-filter`, gradients, glows, or coloured shadows.
- Radius: 6px panels, 4px chips/inputs.

**Type:** Inter, falling back to system-ui. Base 13px; table cells 12px; `tabular-nums` on every number. Panel titles are 11px, uppercase, `--text-muted`, with 0.04em tracking; this is the only place caps are used. Monospace is reserved for tickers and CIKs.

**Density:** 8px grid. Panel header 32px, table row 28px. Overview fits six panels in 1440×900 without scrolling.

**Motion:** opacity fades of 150ms or less. The global `button:active` scale and the spring view transitions are removed, and `prefers-reduced-motion` is respected.

## 2. Shell & architecture

```
┌ TopBar (40px) ─────────────────────────────────────────────────────────┐
│ Zaisaku  [NVDA ▾]  Overview Financials Trends&peers Scenarios Calls&Q&A Filings   ⌘K  Memo▾  ◐  Ask Zaisaku │
├ CompanyStrip (36px) ───────────────────────────────────────────────────┤
│ NVIDIA Corporation  NVDA · NASDAQ · CIK 0001045810 · Semiconductors · FY2024 · PwC   Risk 18 Low   Tools▾ │
├ Content ───────────────────────────────────────────────────────────────┤
```

- **CompanySwitcher.** A single dropdown with three groups: Recent (session), Indices (current category list), and SEC search results (existing `/api` search logic). It replaces the category dropdown, the ticker ribbon, and the separate search input.
- **Tab renames:**

  | Old | New |
  |---|---|
  | Executive Dossier | Overview |
  | Financials & Exhibits | Financials |
  | Multi-Year & Peers | Trends & peers |
  | Scenario Stress Lab | Scenarios |
  | Audio & Inquiries | Calls & Q&A |
  | Evidence Room | Filings |

  Tab IDs stay the same, so `CommandPaletteModal` workspace switching keeps working.
- **Removed:** the "Enterprise 2.4" badge, the "1k Runs" badge, the brand tagline, and the in-app marketing sentences.
- **Renames:**
  - "Co-Analyst" → "Ask Zaisaku" in `App.vue`, `ChatArea.vue`, `CommandPaletteModal.vue`, `CompanyHub.vue`, and `FilingViewerModal.vue`.
  - "Autonomous Multi-Agent Audit" / "Run autonomous audit" → "Run audit".
  - "Adversarial cross-examination" → "Auditor Q&A".
  - "Inspect audit scorecard" → "Scorecard".
- **Tools ▾ menu** in CompanyStrip: Run audit, Auditor Q&A, Scorecard, Prompt sandbox.

**Files:**

| Path | Responsibility |
|---|---|
| `src/data/companyProfiles.js` | Static profile fixtures moved out of `CompanyHub.vue` |
| `src/composables/useCompany.js` | `currentCompany`, `selectCompany(ticker, entry?)`, recent list, SEC search state |
| `src/composables/useTheme.js` | `theme` (`light`/`dark`/`system`), persistence, sets `data-theme` on `<html>` |
| `src/components/shell/TopBar.vue` | Brand, switcher slot, tabs, right-side actions |
| `src/components/shell/CompanySwitcher.vue` | Combobox described above |
| `src/components/shell/CompanyStrip.vue` | Identity line, risk chip, Tools menu |
| `src/components/shell/ThemeToggle.vue` | Cycles system → light → dark |
| `src/components/ui/Panel.vue` | Header bar (title, actions slot, optional expand) + body; `state` prop: `ready`/`loading`/`empty`/`error` |
| `src/components/ui/DataTable.vue` | `columns` (key, label, align, sortable, format), `rows`, row click emit, compact rows |
| `src/components/ui/SeverityDot.vue` | `good`/`watch`/`critical` dot with accessible label |
| `src/components/ui/SourceChip.vue` | Small monospace chip naming the source; emits click |
| `src/components/ui/StatValue.vue` | Big number + label + optional sub-line |
| `src/components/ui/ThresholdScale.vue` | Horizontal scale with value marker and threshold ticks |
| `src/components/overview/OverviewDashboard.vue` | Grid of the six panels |
| `src/components/overview/redFlags.js` | Pure `buildRedFlags(profile)` → sorted rows |
| `src/components/overview/riskBreakdown.js` | Pure `riskBreakdown(profile)` → component rows with weights and severity |

`CompanyHub.vue` stays the container. It keeps modal visibility state, modal mounts, and the other 5 tab bodies, and it renders `TopBar`, `CompanyStrip`, and `OverviewDashboard`. Target size is about 600 lines.

Severity thresholds are shared with `InstitutionalReportModal.vue` by moving them into `src/utils/ffi.js`:
- drift 15/30%
- decoupling 25/50
- M-Score −2.22/−1.78
- footnotes: any flag = watch, 4+ = critical

## 3. Overview dashboard

The grid has 3 columns at ≥1280px, 2 at ≥768px, and 1 below that.

| Panel | Span | Content | Header action |
|---|---|---|---|
| Risk score | 1 | `StatValue` FFI + tier; table of Drift (30%), M-Score (40%), Contradictions (30%) with raw value + `SeverityDot` | Expand → scorecard modal |
| Red flags | 2 | `DataTable`: severity · finding · `SourceChip`. Rows come from `buildRedFlags`: drift excerpt ("10-K Item 1A"), radar excerpt ("Earnings call"), footnote excerpt ("10-K notes"). Sorted critical → good. Row click opens the diff modal, the contradiction radar, or the M-Score modal on the footnote tab, respectively | Anomaly radar |
| M-Score | 1 | `ThresholdScale` (range −4…0, ticks −2.22, −1.78), probability, TATA | Calculator → M-Score modal |
| Language drift | 1 | Drift %, +added / −retired, quoted excerpt | Redline → diff modal |
| Peers | 1 | `DataTable` ticker · FFI · M-Score · tier from `/api/forensics/peers/{ticker}`, current company row highlighted | Expand → Trends & peers tab |
| Filings | 1 | Latest 6 documents from `/api/documents` (already loaded in hub): name · type · date | Ingest → SEC modal |

Macro indices (`is_macro_index`):
- The Risk score panel shows "Constituent-weighted dispersion" instead of the weight table.
- The Red flags panel title becomes "Signals".

**Removed:**
- The FFI gauge ring.
- The governance banner, whose text was hard-coded on `ticker === 'SMCI'`.
- The marketing paragraph.

No score-history chart is added, because no historical score data exists.

## 4. States, theming, testing, delivery

**Panel states:**
- `loading`: 3 skeleton rows.
- `empty`: one muted line + action.
- `error`: amber icon + message + Retry.

Panels fail independently.

**Theming:**
- `useTheme` reads and writes `localStorage['zaisaku-theme']` inside try/catch and falls back to `system`.
- `system` follows `matchMedia('(prefers-color-scheme: dark)')` live.
- **Known gap:** modals and the 5 un-migrated tabs keep their dark hard-coded classes until their phase. In light mode they render as dark surfaces. They stay readable but are not themed.

**Testing:**
- Add `vitest`, `@vue/test-utils`, and `jsdom` as dev dependencies.
- Add `"test": "vitest run"` to `package.json`.
- Add a `npm test` step to the `frontend-build` CI job before the build.
- Unit tests cover:
  - `buildRedFlags` (mapping, sorting, macro case)
  - `riskBreakdown`
  - severity thresholds in `utils/ffi.js`
  - `ThresholdScale` marker position (including clamping)
  - `useTheme` persistence and fallback when storage throws
  - `DataTable` sort and row-click emit
  - `Panel` state rendering
- Visual check in a headless browser at 1440×900, 1280×800, and 390×844 in both themes.

**Delivery** (each PR CI-gated, then squash-merged):
1. `feat/design-tokens-theme` — tokens, `useTheme`, `ThemeToggle`, Vitest + CI step, motion cleanup.
2. `feat/ui-primitives` — `components/ui/*` with tests.
3. `feat/app-shell` — data extraction, `useCompany`, TopBar, CompanySwitcher, CompanyStrip, renames, badge removal.
4. `feat/overview-dashboard` — `OverviewDashboard`, `redFlags.js`, `riskBreakdown.js`, shared thresholds, old Overview markup deleted.

## Out of scope (later phases)

- Restyling the Financials, Trends & peers, Scenarios, Calls & Q&A, and Filings tabs.
- Restyling all modals and the command palette.
- Replacing hard-coded demo profiles with backend data.
