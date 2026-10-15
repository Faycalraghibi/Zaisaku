# Review Fixes & UI/UX Polish Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the 10 code-review findings on `122c27c` (#33) and repair the UI/UX regressions visible in the running app, shipped as 5 small PRs that each pass CI and get squash-merged into `main`.

**Architecture:** Vue 3 + Tailwind v4 SPA in `frontend/`. All work is template/CSS/JS in `frontend/src`. One new shared helper module (`frontend/src/utils/ffi.js`) replaces the duplicated FFI tier logic so the hub and the memo cannot disagree again. No backend changes.

**Tech Stack:** Vue 3.5 (`<script setup>`), Tailwind CSS v4, Vite 8, lucide-vue-next. CI = `pytest` + `ruff` (backend) and `npm ci && npm run build` (frontend).

**Testing note:** The frontend has no unit-test runner and CI only builds it. Adding Vitest is out of scope (YAGNI for template fixes). Each task is verified by (1) `npm run build` passing and (2) a headless-browser check against `npx vite --port 5199` (served on `http://[::1]:5199/`; backend not required — API panels show their error state).

---

## Evidence: UI/UX problems seen in the running app (1440×900 and 390×844)

1. Header wraps to two rows at 1440px; action tray drops below brand.
2. Two search entry points side by side: the autocomplete input *and* a "Search or ⌘K" button whose label is truncated ("Search or").
3. Hero card: left column vertically centred against a tall FFI card → ~120px dead space above and below the company name.
4. Hero metadata uses literal `/` separator spans; on mobile they wrap onto their own line as orphans.
5. Sub-header repeats the company name *and* auditor already shown in the hero.
6. Pillar card action links use four different accent colours (amber, purple, cyan, rose) — "Scan footnotes" in rose reads as an alarm on a clean company.
7. Casing inconsistent after #33's "sentence case" pass: `Low Fragility`, `Critical Alert`, `Run M-Score Analysis`, `Load Scenario Preset:` remain Title Case.
8. Trends/Peers API failure renders a saturated red slab with no way to retry.
9. Browser tab title is `frontend`.

---

## File map

| File | Change |
|---|---|
| `frontend/src/utils/ffi.js` | **Create.** `ffiTier(score)` + `formatEnum(value)` shared helpers |
| `frontend/src/components/CompanyHub.vue` | FFI chips, footnote button, header, hero, sub-header, pillar links, scoped CSS removal |
| `frontend/src/components/ForensicMScoreModal.vue` | enum label, `initialTab` prop, casing |
| `frontend/src/components/PeerComparisonMatrix.vue` | enum label, error state |
| `frontend/src/components/FinancialTrendsChart.vue` | error state |
| `frontend/src/components/CommandPaletteModal.vue` | `↵` only on selected row |
| `frontend/src/components/InstitutionalReportModal.vue` | risk badge, exchange/CIK, summary sentence |
| `frontend/src/style.css` | drop `.tabular-nums`, `.caption-label` |
| `frontend/index.html` | title |

## PR breakdown (merge in order — all touch `CompanyHub.vue`, so each branches from fresh `main`)

| PR | Branch | Findings / issues |
|---|---|---|
| 1 | `fix/review-data-labels` | Review #1, #2, #3, #4, #7, #8 |
| 2 | `fix/memo-report-accuracy` | Review #5, #6 (+ hard-coded summary sentence) |
| 3 | `refactor/css-dedupe` | Review #9, #10 |
| 4 | `feat/ui-header-hero-layout` | UI issues 1–5 |
| 5 | `feat/ux-states-consistency` | UI issues 6–9 |

**Per-PR ship loop (same for every PR):**

```bash
git checkout main && git pull --ff-only
git checkout -b <branch>
# ...tasks...
cd frontend && npm run build          # must exit 0
git push -u origin <branch>
gh pr create --base main --title "<title>" --body "<body>"
gh pr checks --watch                  # wait for Backend Unit Tests + Frontend Build
gh pr merge --squash --delete-branch  # only if every check passed
```

If a check fails: read `gh run view --log-failed`, fix on the branch, push, re-watch. Never merge red.

---

## PR 1 — `fix/review-data-labels`

### Task 1.1: Shared enum/tier helper

**Files:** Create `frontend/src/utils/ffi.js`

- [ ] **Step 1: Create the module**

```js
// Shared Forensic Fragility Index helpers so every view labels scores identically.

export const formatEnum = (value) =>
  value ? String(value).replace(/_/g, ' ').toLowerCase() : ''

export const ffiTier = (score) => {
  if (score < 25) {
    return { key: 'low', text: 'text-emerald-400', bg: 'bg-emerald-500/10', border: 'border-emerald-500/20', label: 'Low fragility' }
  }
  if (score < 50) {
    return { key: 'watch', text: 'text-amber-400', bg: 'bg-amber-500/10', border: 'border-amber-500/20', label: 'Watchlist fragility' }
  }
  return { key: 'critical', text: 'text-rose-400', bg: 'bg-rose-500/10', border: 'border-rose-500/20', label: 'Critical alert' }
}
```

(Thresholds and colours must be copied from the existing `ffiColor` in `CompanyHub.vue:810-833` — read it first and mirror every branch exactly; only the labels change to sentence case.)

- [ ] **Step 2:** In `CompanyHub.vue` replace the body of `ffiColor` with an import: `import { ffiTier } from '../utils/ffi.js'` and `const ffiColor = ffiTier`.

### Task 1.2: Risk enum labels (review #1, #2)

**Files:** `ForensicMScoreModal.vue:304`, `PeerComparisonMatrix.vue:138`

- [ ] Import `formatEnum` from `../utils/ffi.js` in both files.
- [ ] `{{ mScoreResult.risk_level.toLowerCase() }}` → `{{ formatEnum(mScoreResult.risk_level) }}`
- [ ] `{{ p.risk_tier.toLowerCase() }}` → `{{ formatEnum(p.risk_tier) }}`
- [ ] Also `ForensicMScoreModal.vue:552` `f.severity.toLowerCase()` → `formatEnum(f.severity)` (same bug class).

### Task 1.3: FFI weight chips (review #3, #4)

**Files:** `CompanyHub.vue:1329-1333`

- [ ] Replace the chip row with:

```html
<p v-if="currentCompany.is_macro_index" class="text-[11px] text-slate-400 pt-1">
  Constituent-weighted fragility dispersion
</p>
<div v-else class="flex items-center justify-center gap-1.5 pt-1">
  <span class="text-[11px] px-2 py-0.5 rounded-md bg-white/5 border border-white/10 text-slate-300">Drift 30%</span>
  <span class="text-[11px] px-2 py-0.5 rounded-md bg-white/5 border border-white/10 text-slate-300">M-Score 40%</span>
  <span class="text-[11px] px-2 py-0.5 rounded-md bg-white/5 border border-white/10 text-slate-300">Contradictions 30%</span>
</div>
```

- [ ] Verify: select SPY in browser → chips absent, dispersion line present; select NVDA → three chips, third reads "Contradictions 30%".

### Task 1.4: "Scan footnotes" opens footnote tab (review #7)

**Files:** `ForensicMScoreModal.vue:17-26`, `CompanyHub.vue` (button ~1554, modal ~1819)

- [ ] Add prop `initialTab: { type: String, default: 'mscore' }` and `watch(() => props.isOpen, (open) => { if (open) activeTab.value = props.initialTab })`.
- [ ] In `CompanyHub.vue` add `const mScoreInitialTab = ref('mscore')`; "Audit accruals" → `@click="mScoreInitialTab = 'mscore'; showMScoreModal = true"`; "Scan footnotes" → `@click="mScoreInitialTab = 'footnotes'; showMScoreModal = true"`; pass `:initial-tab="mScoreInitialTab"`. The palette path (`actionId === 'beneish-mscore'`) sets `'mscore'`.
- [ ] Verify in browser: "Scan footnotes" opens with "Footnote Hazard Scanner" tab active.

### Task 1.5: `↵` hint only on selected row (review #8)

**Files:** `CommandPaletteModal.vue:337, 502`

- [ ] Wrap each row's `<kbd>↵</kbd>` in the same `selectedIndex === <rowIndex>` expression that row already uses for `:data-active` (AI row: `v-if="selectedIndex === 0"`; action row: `v-if="selectedIndex === flattenedItems.findIndex(i => i.type === 'action' && i.id === item.id)"`). Footer legend at line 524 stays.
- [ ] Commit: `fix(ui): correct risk labels, FFI weights, footnote action, and palette enter hint`

---

## PR 2 — `fix/memo-report-accuracy`

### Task 2.1: Memo header & badge driven by data (review #5, #6)

**Files:** `InstitutionalReportModal.vue:136-152, 184`

- [ ] Import `ffiTier` from `../utils/ffi.js`; add computeds:

```js
const ffiScore = computed(() => props.profile.ffi ?? 0)
const tier = computed(() => ffiTier(ffiScore.value))
const entityLine = computed(() => {
  const parts = [`${props.companyName} (${props.profile.exchange || 'N/A'}: ${props.ticker})`]
  if (!props.profile.is_macro_index && props.profile.cik) parts.push(`CIK: ${props.profile.cik}`)
  return parts.join(' / ')
})
```

- [ ] Header: `Target Entity: {{ entityLine }}`.
- [ ] Badge: `:class="[tier.bg, tier.text, tier.border]"` (keep `print:` classes), text `FFI: {{ ffiScore }} / 100 — {{ tier.label }}`.
- [ ] Replace every `profile.ffi || 18` (lines 46, 148, 184) with `ffiScore`.
- [ ] Line 184 summary: keep the opening clause, and swap the closing claim by tier: `low` → existing "negligible structural fragility" sentence; otherwise "indicates {{ tier.label.toLowerCase() }} warranting targeted follow-up on the flagged pillars."
- [ ] Verify: memo for SMCI shows rose badge + non-"low" text; SPY shows no CIK; NVDA unchanged.
- [ ] Commit: `fix(report): derive memo risk badge, exchange, and CIK from profile data`

---

## PR 3 — `refactor/css-dedupe`

### Task 3.1 (review #9, #10)

- [ ] Delete scoped `.apple-glass` and `.apple-card` blocks in `CompanyHub.vue` `<style scoped>` (~1993-2006); keep `.apple-press` and transition rules.
- [ ] Delete `.caption-label` and `.tabular-nums` rules from `style.css` (Tailwind v4 provides `tabular-nums`; build output must still contain `font-variant-numeric` — check `grep -c tabular-nums dist/assets/*.css` ≥ 1).
- [ ] Browser check: hub header and cards render; no visual collapse.
- [ ] Commit: `refactor(css): drop duplicated surface tokens and redundant utilities`

---

## PR 4 — `feat/ui-header-hero-layout`

### Task 4.1: Single-row header, one search entry

**Files:** `CompanyHub.vue:1018-1200`

- [ ] Header: `flex-wrap` → `flex-wrap xl:flex-nowrap`; tagline `<p>` gets `hidden 2xl:block`.
- [ ] Remove the standalone "Search or ⌘K" button at ≥sm. Put the hint inside the search input instead:

```html
<button
  type="button"
  @click="emit('open-palette')"
  class="absolute right-1.5 text-[10px] font-mono bg-slate-900 px-1.5 py-0.5 rounded border border-white/10 text-slate-400 hover:text-white cursor-pointer"
  title="Open command palette"
  aria-label="Open command palette"
>⌘K</button>
```

  (hidden while `isSearching` so it does not overlap the spinner; input `pr-7` → `pr-11`).
- [ ] Keep an icon-only palette button with `sm:hidden` and `aria-label` for mobile, where the input is hidden.
- [ ] Icon-only header buttons below `md` get `aria-label` equal to their `title`.
- [ ] Verify at 1440: header is one row; at 1280: no overflow; at 390: actions reachable.

### Task 4.2: Hero rebalance

**Files:** `CompanyHub.vue:1249-1365`

- [ ] Move the three action buttons ("Run autonomous audit", "Adversarial cross-examination", "Inspect audit scorecard") out of the gauge card into the left column under the description as `<div class="flex flex-wrap gap-2 pt-2">`, buttons `w-auto` (primary stays white).
- [ ] Section `lg:items-center` → `lg:items-start`; gauge card drops `min-w-[280px]` → `min-w-[240px]`.
- [ ] Replace the `<span>/</span>` separator spans (lines 1262, 1289) — delete them; parents already have `gap-x-*`, add `gap-x-4` where missing.
- [ ] Verify: dead space gone at 1440; no orphan separators at 390.

### Task 4.3: De-duplicate sub-header context

- [ ] Delete the `Auditor: …` span at `CompanyHub.vue:1234` (hero already shows it). Keep the company chip.
- [ ] Commit: `feat(ui): single-row header, unified search, and balanced hero layout`

---

## PR 5 — `feat/ux-states-consistency`

### Task 5.1: Retryable, calm error states

**Files:** `FinancialTrendsChart.vue:198`, `PeerComparisonMatrix.vue:95`

- [ ] Replace each error `<div>` with:

```html
<div v-else-if="errorMsg" class="p-4 rounded-xl bg-white/[0.03] border border-white/10 flex items-center justify-between gap-4">
  <div class="flex items-center gap-2.5 text-xs text-slate-300">
    <AlertTriangle class="w-4 h-4 text-amber-400 shrink-0" />
    <span>{{ errorMsg }}. The analysis service may be offline.</span>
  </div>
  <button @click="fetchTrends(ticker)" class="apple-press shrink-0 text-xs font-medium px-3 py-1.5 rounded-lg border border-white/10 bg-slate-800/80 hover:bg-slate-700 text-slate-200 cursor-pointer">Retry</button>
</div>
```

  (`fetchPeers(ticker)` in the peers file; import `AlertTriangle` from `lucide-vue-next` if not already imported; use `props.ticker` if `ticker` isn't destructured in template scope — template has prop access by name.)

### Task 5.2: Unified pillar action links

- [ ] `CompanyHub.vue` lines ~1449, 1488, 1519, 1555: replace `text-{amber|purple|cyan|rose}-300 hover:text-…-200` with `text-slate-200 hover:text-white underline-offset-4 hover:underline`. Status badges keep their semantic colours.

### Task 5.3: Sentence-case leftovers

- [ ] `ForensicMScoreModal.vue`: "Load Scenario Preset:" → "Load scenario preset:", "Run M-Score Analysis" → "Run M-Score analysis", "Clean Profile (Normal)" → "Clean profile (normal)", "Aggressive Accruals (High Risk)" → "Aggressive accruals (high risk)", tab "Footnote Hazard Scanner" → "Footnote hazard scanner", "Beneish M-Score Calculator" → "Beneish M-Score calculator". Proper nouns/acronyms keep caps.
- [ ] `index.html`: `<title>frontend</title>` → `<title>Zaisaku</title>`.
- [ ] Verify: Peers tab with backend down shows calm card + Retry; clicking Retry re-requests `/api/...` (network log shows second request).
- [ ] Commit: `feat(ux): retryable error states, unified pillar actions, consistent casing`

---

## Self-review

- Review findings 1–10 → PR1 (1,2,3,4,7,8), PR2 (5,6), PR3 (9,10). ✔
- UI issues 1–9 → PR4 (1–5), PR5 (6–9). ✔
- `ffiTier`/`formatEnum` defined in Task 1.1, used in 1.2, 2.1. ✔
- `initialTab` prop defined and consumed in Task 1.4. ✔
