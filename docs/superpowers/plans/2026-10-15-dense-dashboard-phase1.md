# Dense Dashboard Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the glass/gradient "AI slop" shell and Overview with a Koyfin-style dense dashboard (tokens, dark+light theme, widget primitives, slim shell, six-panel Overview), per `docs/superpowers/specs/2026-10-15-dense-dashboard-redesign-design.md`.

**Architecture:** CSS-variable tokens exposed to Tailwind v4 via `@theme inline`; `data-theme` on `<html>` switches palettes. Small in-house primitives in `src/components/ui/`. `CompanyHub.vue` stays the container (modal state, legacy tabs) but delegates shell and Overview to new components. Pure logic lives in `.js` modules with Vitest tests. Un-migrated tabs render inside a `data-theme="dark"` island so they stay readable in light mode.

**Tech Stack:** Vue 3.5 `<script setup>`, Tailwind v4, Vite 8, lucide-vue-next, Vitest 5 + @vue/test-utils 2 + jsdom.

**Conventions:**
- Every `**File:** \`path\`` line is followed by the complete file content for that path, relative to `frontend/`.
- Line endings: the repo index is LF, so write files with LF.
- Ship loop for every PR:

```bash
git checkout main && git pull --ff-only && git checkout -b <branch>
cd frontend && npm test && npm run build
git push -u origin <branch> && gh pr create ... && gh pr checks --watch
gh pr merge --squash --delete-branch   # only when all checks pass
```

**Spec deviation (deliberate, YAGNI):** the CompanySwitcher groups are **Recent / Indices / Companies / Search results**. The sector-category filter is dropped; Indices = the old "Macro Indices" list, and Companies = every non-index ticker that has a profile. The old "All"/"High-Risk" lists referenced RIVN, which has no profile.

---

## PR 1 — `feat/design-tokens-theme` (branch already exists with the spec commit)

### Task 1.1: Test tooling

- [ ] `cd frontend && npm i -D vitest@^5 @vue/test-utils@^2 jsdom@^30`
- [ ] Add `"test": "vitest run"` to `package.json` scripts.
- [ ] Add `test: { environment: 'jsdom' }` to `vite.config.js`:

**File:** `vite.config.js`
```js
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    tailwindcss(),
  ],
  server: {
    // Proxy API requests to backend during dev
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      }
    }
  },
  test: {
    environment: 'jsdom'
  }
})
```

- [ ] CI: in `.github/workflows/ci.yml` `frontend-build` job, insert before "Build frontend":

```yaml
      - name: Run unit tests
        run: npm test
```

### Task 1.2: Theme store (TDD)

**File:** `src/composables/useTheme.test.js`
```js
import { describe, it, expect } from 'vitest'
import { createTheme, resolveTheme } from './useTheme.js'

const memoryStorage = (initial = {}) => {
  const data = { ...initial }
  return {
    getItem: (k) => (k in data ? data[k] : null),
    setItem: (k, v) => { data[k] = String(v) },
    data
  }
}

const throwingStorage = {
  getItem: () => { throw new Error('denied') },
  setItem: () => { throw new Error('denied') }
}

const fakeMedia = (matches) => {
  const listeners = []
  return {
    matches,
    addEventListener: (_, fn) => listeners.push(fn),
    fire: (m) => listeners.forEach((fn) => fn({ matches: m }))
  }
}

const fakeRoot = () => ({ dataset: {} })

describe('resolveTheme', () => {
  it('follows the OS in system mode', () => {
    expect(resolveTheme('system', true)).toBe('dark')
    expect(resolveTheme('system', false)).toBe('light')
  })
  it('honours explicit modes', () => {
    expect(resolveTheme('light', true)).toBe('light')
    expect(resolveTheme('dark', false)).toBe('dark')
  })
})

describe('createTheme', () => {
  it('defaults to system and applies the resolved theme to the root', () => {
    const root = fakeRoot()
    const theme = createTheme({ storage: memoryStorage(), mediaQuery: fakeMedia(true), root })
    expect(theme.mode.value).toBe('system')
    expect(root.dataset.theme).toBe('dark')
  })

  it('reads a stored mode', () => {
    const root = fakeRoot()
    createTheme({ storage: memoryStorage({ 'zaisaku-theme': 'light' }), mediaQuery: fakeMedia(true), root })
    expect(root.dataset.theme).toBe('light')
  })

  it('ignores an invalid stored value', () => {
    const theme = createTheme({ storage: memoryStorage({ 'zaisaku-theme': 'purple' }), mediaQuery: fakeMedia(false), root: fakeRoot() })
    expect(theme.mode.value).toBe('system')
  })

  it('persists and applies setMode', () => {
    const storage = memoryStorage()
    const root = fakeRoot()
    const theme = createTheme({ storage, mediaQuery: fakeMedia(false), root })
    theme.setMode('dark')
    expect(storage.data['zaisaku-theme']).toBe('dark')
    expect(root.dataset.theme).toBe('dark')
  })

  it('cycles system -> light -> dark -> system', () => {
    const theme = createTheme({ storage: memoryStorage(), mediaQuery: fakeMedia(false), root: fakeRoot() })
    theme.cycle(); expect(theme.mode.value).toBe('light')
    theme.cycle(); expect(theme.mode.value).toBe('dark')
    theme.cycle(); expect(theme.mode.value).toBe('system')
  })

  it('tracks OS changes while in system mode', () => {
    const media = fakeMedia(false)
    const root = fakeRoot()
    createTheme({ storage: memoryStorage(), mediaQuery: media, root })
    media.fire(true)
    expect(root.dataset.theme).toBe('dark')
  })

  it('survives storage that throws', () => {
    const root = fakeRoot()
    const theme = createTheme({ storage: throwingStorage, mediaQuery: fakeMedia(false), root })
    expect(() => theme.setMode('dark')).not.toThrow()
    expect(root.dataset.theme).toBe('dark')
  })
})
```

- [ ] Run `npm test` → FAIL (module missing).

**File:** `src/composables/useTheme.js`
```js
import { ref, computed, watch } from 'vue'

const STORAGE_KEY = 'zaisaku-theme'
const MODES = ['system', 'light', 'dark']

export const resolveTheme = (mode, prefersDark) =>
  mode === 'system' ? (prefersDark ? 'dark' : 'light') : mode

const readMode = (storage) => {
  try {
    const value = storage?.getItem(STORAGE_KEY)
    return MODES.includes(value) ? value : 'system'
  } catch {
    return 'system'
  }
}

const writeMode = (storage, value) => {
  try {
    storage?.setItem(STORAGE_KEY, value)
  } catch {
    // Storage blocked (private mode, policy): theme still applies for this session.
  }
}

export function createTheme ({ storage, mediaQuery, root }) {
  const mode = ref(readMode(storage))
  const prefersDark = ref(Boolean(mediaQuery?.matches))
  const resolved = computed(() => resolveTheme(mode.value, prefersDark.value))

  mediaQuery?.addEventListener?.('change', (e) => { prefersDark.value = e.matches })
  watch(resolved, (value) => { root.dataset.theme = value }, { immediate: true, flush: 'sync' })

  const setMode = (value) => {
    if (!MODES.includes(value)) return
    mode.value = value
    writeMode(storage, value)
  }
  const cycle = () => setMode(MODES[(MODES.indexOf(mode.value) + 1) % MODES.length])

  return { mode, resolved, setMode, cycle }
}

let instance = null

const safeLocalStorage = () => {
  try {
    return window.localStorage
  } catch {
    return null
  }
}

export function useTheme () {
  if (!instance) {
    instance = createTheme({
      storage: safeLocalStorage(),
      mediaQuery: window.matchMedia?.('(prefers-color-scheme: dark)'),
      root: document.documentElement
    })
  }
  return instance
}
```

- [ ] Run `npm test` → PASS.

### Task 1.3: ThemeToggle component

**File:** `src/components/shell/ThemeToggle.vue`
```vue
<script setup>
import { computed } from 'vue'
import { Monitor, Sun, Moon } from 'lucide-vue-next'
import { useTheme } from '../../composables/useTheme.js'

const { mode, cycle } = useTheme()

const icon = computed(() => ({ system: Monitor, light: Sun, dark: Moon })[mode.value])
const label = computed(() => `Theme: ${mode.value}. Click to change.`)
</script>

<template>
  <button type="button" class="btn-icon" :title="label" :aria-label="label" @click="cycle">
    <component :is="icon" class="w-3.5 h-3.5" />
  </button>
</template>
```

**File:** `src/components/shell/ThemeToggle.test.js`
```js
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import ThemeToggle from './ThemeToggle.vue'

describe('ThemeToggle', () => {
  it('cycles the theme mode and updates its label', async () => {
    const wrapper = mount(ThemeToggle)
    const before = wrapper.attributes('aria-label')
    await wrapper.trigger('click')
    expect(wrapper.attributes('aria-label')).not.toBe(before)
    expect(['light', 'dark']).toContain(document.documentElement.dataset.theme)
  })
})
```

### Task 1.4: Tokens, base styles, motion cleanup

Replace the top of `src/style.css` (everything above `/* Institutional Design Typography */`) with:

```css
@import "tailwindcss";

/* Design tokens: light by default, dark under [data-theme=dark]. */
:root {
  --bg: #f6f7f9;
  --panel: #ffffff;
  --raised: #f0f2f5;
  --border: #e2e5ea;
  --text: #14171c;
  --text-muted: #5d6470;
  --text-faint: #8a919c;
  --accent: #2f6fdb;
  --accent-soft: rgb(47 111 219 / 0.1);
  --sev-good: #1f8a62;
  --sev-watch: #b57b10;
  --sev-critical: #c9372c;
  color-scheme: light;
}

[data-theme="dark"] {
  --bg: #0f1115;
  --panel: #16181d;
  --raised: #1f2228;
  --border: #2a2e36;
  --text: #e6e8eb;
  --text-muted: #9aa1ac;
  --text-faint: #6b7280;
  --accent: #5b8def;
  --accent-soft: rgb(91 141 239 / 0.14);
  --sev-good: #3fb68b;
  --sev-watch: #e0a83a;
  --sev-critical: #e5534b;
  color-scheme: dark;
}

@theme inline {
  --color-bg: var(--bg);
  --color-panel: var(--panel);
  --color-raised: var(--raised);
  --color-line: var(--border);
  --color-fg: var(--text);
  --color-muted: var(--text-muted);
  --color-faint: var(--text-faint);
  --color-accent: var(--accent);
  --color-accent-soft: var(--accent-soft);
  --color-good: var(--sev-good);
  --color-watch: var(--sev-watch);
  --color-critical: var(--sev-critical);
  --font-sans: "Inter", ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
  --font-mono: ui-monospace, SFMono-Regular, "Cascadia Mono", Menlo, Consolas, monospace;
}

:root {
  font-family: var(--font-sans);
  line-height: 1.5;
  font-weight: 400;
  color: var(--text);
  background-color: var(--bg);
  font-synthesis: none;
  text-rendering: optimizeLegibility;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

body {
  margin: 0;
  display: flex;
  min-width: 320px;
  min-height: 100vh;
  /* Base text size lives on body, not :root, so rem-based Tailwind sizes stay at 16px rem. */
  font-size: 13px;
  background-color: var(--bg);
  overflow-x: hidden;
}

#app {
  width: 100%;
  display: flex;
  flex-direction: column;
}

@layer components {
  .btn {
    @apply inline-flex items-center gap-1.5 h-7 px-2.5 rounded text-xs font-medium text-fg bg-panel border border-line hover:bg-raised transition-colors cursor-pointer whitespace-nowrap disabled:opacity-50 disabled:cursor-not-allowed focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-accent;
  }
  .btn-primary {
    @apply inline-flex items-center gap-1.5 h-7 px-3 rounded text-xs font-semibold text-white bg-accent hover:opacity-90 transition-opacity cursor-pointer whitespace-nowrap focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-accent;
  }
  .btn-ghost {
    @apply inline-flex items-center gap-1.5 h-6 px-2 rounded text-xs font-medium text-muted hover:text-fg hover:bg-raised transition-colors cursor-pointer whitespace-nowrap focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-accent;
  }
  .btn-icon {
    @apply inline-flex items-center justify-center w-7 h-7 rounded text-muted hover:text-fg hover:bg-raised transition-colors cursor-pointer focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-accent;
  }
}
```

- [ ] Delete the `/* Apple Tactile Pointer-Down Feedback */` block (global `button:active` / `.apple-press:active` scale), and remove `.apple-press:active` and `.apple-card:hover` from the reduced-motion list.
- [ ] Delete `.apple-press:active { transform: scale(0.98); }` from `CompanyHub.vue` `<style scoped>`.
- [ ] Keep `.apple-glass`, `.apple-card`, and `.spring-drawer-*`. Legacy components still use them until their phase.

### Task 1.5: index.html — font + no-flash theme

**File:** `index.html`
```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet" />
    <script>
      // Apply the saved theme before first paint to avoid a light/dark flash.
      (function () {
        var mode = 'system'
        try { mode = localStorage.getItem('zaisaku-theme') || 'system' } catch (e) {}
        var dark = mode === 'dark' || (mode !== 'light' && window.matchMedia('(prefers-color-scheme: dark)').matches)
        document.documentElement.dataset.theme = dark ? 'dark' : 'light'
      })()
    </script>
    <title>Zaisaku</title>
  </head>
  <body>
    <div id="app"></div>
    <script type="module" src="/src/main.js"></script>
  </body>
</html>
```

- [ ] `npm test && npm run build` → pass. Browser: app still renders (legacy dark surfaces cover the page). Commit `feat(ui): design tokens, theme store, and test tooling`.

---

## PR 2 — `feat/ui-primitives`

### Task 2.1: Pure helpers (TDD)

**File:** `src/components/ui/sortRows.test.js`
```js
import { describe, it, expect } from 'vitest'
import { sortRows } from './sortRows.js'

const rows = [
  { t: 'B', v: 2 },
  { t: 'a', v: null },
  { t: 'C', v: 10 },
  { t: 'd', v: -1 }
]

describe('sortRows', () => {
  it('sorts numbers ascending with nulls last', () => {
    expect(sortRows(rows, 'v', 'asc').map((r) => r.v)).toEqual([-1, 2, 10, null])
  })
  it('sorts numbers descending with nulls still last', () => {
    expect(sortRows(rows, 'v', 'desc').map((r) => r.v)).toEqual([10, 2, -1, null])
  })
  it('sorts strings case-insensitively', () => {
    expect(sortRows(rows, 't', 'asc').map((r) => r.t)).toEqual(['a', 'B', 'C', 'd'])
  })
  it('returns a copy and leaves input untouched without a key', () => {
    const out = sortRows(rows, null, 'asc')
    expect(out).toEqual(rows)
    expect(out).not.toBe(rows)
  })
})
```

**File:** `src/components/ui/sortRows.js`
```js
const isBlank = (v) => v === null || v === undefined || v === ''

export function sortRows (rows, key, dir = 'asc') {
  const copy = [...rows]
  if (!key) return copy
  const sign = dir === 'desc' ? -1 : 1
  return copy.sort((a, b) => {
    const x = a[key]
    const y = b[key]
    if (isBlank(x) && isBlank(y)) return 0
    if (isBlank(x)) return 1
    if (isBlank(y)) return -1
    if (typeof x === 'number' && typeof y === 'number') return (x - y) * sign
    return String(x).localeCompare(String(y), undefined, { sensitivity: 'base', numeric: true }) * sign
  })
}
```

**File:** `src/components/ui/scale.test.js`
```js
import { describe, it, expect } from 'vitest'
import { scalePosition } from './scale.js'

describe('scalePosition', () => {
  it('maps value linearly to 0..100', () => {
    expect(scalePosition(-2, -4, 0)).toBe(50)
    expect(scalePosition(-4, -4, 0)).toBe(0)
    expect(scalePosition(0, -4, 0)).toBe(100)
  })
  it('clamps out-of-range values', () => {
    expect(scalePosition(-9, -4, 0)).toBe(0)
    expect(scalePosition(3, -4, 0)).toBe(100)
  })
  it('returns null for missing values or a zero-width range', () => {
    expect(scalePosition(null, -4, 0)).toBeNull()
    expect(scalePosition(1, 2, 2)).toBeNull()
  })
})
```

**File:** `src/components/ui/scale.js`
```js
export function scalePosition (value, min, max) {
  if (value === null || value === undefined || Number.isNaN(Number(value)) || max === min) return null
  const pct = ((Number(value) - min) / (max - min)) * 100
  return Math.min(100, Math.max(0, pct))
}
```

### Task 2.2: Components

**File:** `src/components/ui/Panel.vue`
```vue
<script setup>
import { AlertTriangle } from 'lucide-vue-next'

defineProps({
  title: { type: String, required: true },
  state: { type: String, default: 'ready' }, // ready | loading | empty | error
  emptyText: { type: String, default: 'Nothing to show yet.' },
  errorText: { type: String, default: 'Could not load this panel.' }
})

const emit = defineEmits(['retry'])
</script>

<template>
  <section class="flex flex-col min-h-0 rounded-md border border-line bg-panel">
    <header class="flex items-center justify-between gap-2 h-8 px-3 border-b border-line shrink-0">
      <h2 class="text-[11px] font-semibold uppercase tracking-[0.04em] text-muted truncate">{{ title }}</h2>
      <div v-if="$slots.actions" class="flex items-center gap-1 shrink-0">
        <slot name="actions" />
      </div>
    </header>

    <div class="flex-1 min-h-0 overflow-auto">
      <div v-if="state === 'loading'" class="p-3 space-y-2" aria-busy="true" data-state="loading">
        <div v-for="n in 3" :key="n" class="h-4 rounded-sm bg-raised animate-pulse" />
      </div>

      <div v-else-if="state === 'empty'" class="p-3 flex flex-wrap items-center gap-2 text-xs text-muted" data-state="empty">
        <span>{{ emptyText }}</span>
        <slot name="empty-action" />
      </div>

      <div v-else-if="state === 'error'" role="alert" class="p-3 flex items-center justify-between gap-3 text-xs" data-state="error">
        <span class="flex items-center gap-2 text-fg">
          <AlertTriangle class="w-3.5 h-3.5 text-watch shrink-0" />
          {{ errorText }}
        </span>
        <button type="button" class="btn" @click="emit('retry')">Retry</button>
      </div>

      <slot v-else />
    </div>
  </section>
</template>
```

**File:** `src/components/ui/DataTable.vue`
```vue
<script setup>
import { ref, computed } from 'vue'
import { ChevronUp, ChevronDown } from 'lucide-vue-next'
import { sortRows } from './sortRows.js'

const props = defineProps({
  // [{ key, label, align: 'left'|'right', sortable, format: (value, row) => string, width }]
  columns: { type: Array, required: true },
  rows: { type: Array, default: () => [] },
  rowKey: { type: String, required: true },
  highlight: { type: [String, Number], default: null },
  clickable: { type: Boolean, default: false },
  initialSort: { type: Object, default: null } // { key, dir }
})

const emit = defineEmits(['row-click'])

const sortKey = ref(props.initialSort?.key ?? null)
const sortDir = ref(props.initialSort?.dir ?? 'asc')

const sorted = computed(() => sortRows(props.rows, sortKey.value, sortDir.value))

const toggleSort = (col) => {
  if (!col.sortable) return
  if (sortKey.value === col.key) {
    sortDir.value = sortDir.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortKey.value = col.key
    sortDir.value = 'asc'
  }
}

const ariaSort = (col) => {
  if (!col.sortable) return undefined
  if (sortKey.value !== col.key) return 'none'
  return sortDir.value === 'asc' ? 'ascending' : 'descending'
}

const display = (col, row) => (col.format ? col.format(row[col.key], row) : row[col.key])

const onRowClick = (row) => {
  if (props.clickable) emit('row-click', row)
}
</script>

<template>
  <table class="w-full text-xs border-collapse">
    <thead>
      <tr>
        <th
          v-for="col in columns"
          :key="col.key"
          scope="col"
          :aria-sort="ariaSort(col)"
          :style="col.width ? { width: col.width } : null"
          class="h-7 px-3 font-medium text-muted border-b border-line whitespace-nowrap"
          :class="col.align === 'right' ? 'text-right' : 'text-left'"
        >
          <button
            v-if="col.sortable"
            type="button"
            class="inline-flex items-center gap-0.5 hover:text-fg cursor-pointer"
            @click="toggleSort(col)"
          >
            {{ col.label }}
            <ChevronUp v-if="sortKey === col.key && sortDir === 'asc'" class="w-3 h-3" />
            <ChevronDown v-else-if="sortKey === col.key" class="w-3 h-3" />
          </button>
          <template v-else>{{ col.label }}</template>
        </th>
      </tr>
    </thead>
    <tbody>
      <tr
        v-for="row in sorted"
        :key="row[rowKey]"
        :data-row="row[rowKey]"
        class="border-b border-line last:border-b-0"
        :class="[
          clickable ? 'cursor-pointer hover:bg-raised' : '',
          highlight !== null && row[rowKey] === highlight ? 'bg-accent-soft' : ''
        ]"
        :tabindex="clickable ? 0 : undefined"
        @click="onRowClick(row)"
        @keydown.enter="onRowClick(row)"
      >
        <td
          v-for="col in columns"
          :key="col.key"
          class="h-7 px-3 py-1 text-fg align-middle"
          :class="col.align === 'right' ? 'text-right whitespace-nowrap tabular-nums' : 'text-left'"
        >
          <slot :name="`cell-${col.key}`" :row="row" :value="row[col.key]">{{ display(col, row) }}</slot>
        </td>
      </tr>
    </tbody>
  </table>
</template>
```

**File:** `src/components/ui/SeverityDot.vue`
```vue
<script setup>
import { computed } from 'vue'

const props = defineProps({
  level: { type: String, required: true }, // good | watch | critical
  withLabel: { type: Boolean, default: false }
})

const LABELS = { good: 'Low', watch: 'Watch', critical: 'Critical' }
const COLORS = { good: 'bg-good', watch: 'bg-watch', critical: 'bg-critical' }

const label = computed(() => LABELS[props.level] ?? 'Unknown')
</script>

<template>
  <span class="inline-flex items-center gap-1.5">
    <span
      role="img"
      :aria-label="`Severity: ${label}`"
      class="inline-block w-2 h-2 rounded-full shrink-0"
      :class="COLORS[level] ?? 'bg-faint'"
    />
    <span v-if="withLabel" class="text-xs text-muted">{{ label }}</span>
  </span>
</template>
```

**File:** `src/components/ui/SourceChip.vue`
```vue
<script setup>
defineProps({
  label: { type: String, required: true }
})
const emit = defineEmits(['open'])
</script>

<template>
  <button
    type="button"
    class="inline-flex items-center h-5 px-1.5 rounded-sm border border-line font-mono text-[10px] text-muted hover:text-fg hover:border-accent whitespace-nowrap cursor-pointer"
    :title="`Open source: ${label}`"
    @click.stop="emit('open')"
  >
    {{ label }}
  </button>
</template>
```

**File:** `src/components/ui/StatValue.vue`
```vue
<script setup>
defineProps({
  value: { type: [String, Number], required: true },
  label: { type: String, required: true },
  sub: { type: String, default: '' }
})
</script>

<template>
  <div class="space-y-0.5">
    <div class="text-[28px] leading-none font-semibold tracking-tight text-fg">{{ value }}</div>
    <div class="text-xs text-muted">{{ label }}</div>
    <div v-if="sub" class="text-[11px] text-faint">{{ sub }}</div>
  </div>
</template>
```

**File:** `src/components/ui/ThresholdScale.vue`
```vue
<script setup>
import { computed } from 'vue'
import { scalePosition } from './scale.js'

const props = defineProps({
  value: { type: Number, default: null },
  min: { type: Number, required: true },
  max: { type: Number, required: true },
  thresholds: { type: Array, default: () => [] }, // [{ at, label }]
  label: { type: String, required: true }
})

const marker = computed(() => scalePosition(props.value, props.min, props.max))
const ticks = computed(() =>
  props.thresholds
    .map((t) => ({ ...t, pos: scalePosition(t.at, props.min, props.max) }))
    .filter((t) => t.pos !== null)
)
</script>

<template>
  <div
    role="meter"
    :aria-label="label"
    :aria-valuemin="min"
    :aria-valuemax="max"
    :aria-valuenow="value ?? undefined"
    class="pt-1 pb-4"
  >
    <div class="relative h-1.5 rounded-full bg-raised">
      <span
        v-for="t in ticks"
        :key="t.at"
        class="absolute top-1/2 -translate-y-1/2 w-px h-3 bg-faint"
        :style="{ left: `${t.pos}%` }"
      />
      <span
        v-if="marker !== null"
        data-marker
        class="absolute top-1/2 -translate-x-1/2 -translate-y-1/2 w-2.5 h-2.5 rounded-full bg-fg ring-2 ring-panel"
        :style="{ left: `${marker}%` }"
      />
      <span
        v-for="t in ticks"
        :key="`l-${t.at}`"
        class="absolute top-3 -translate-x-1/2 text-[10px] text-faint tabular-nums"
        :style="{ left: `${t.pos}%` }"
      >{{ t.label }}</span>
    </div>
  </div>
</template>
```

**File:** `src/components/ui/MenuButton.vue`
```vue
<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { ChevronDown } from 'lucide-vue-next'

defineProps({
  label: { type: String, required: true },
  items: { type: Array, default: () => [] }, // [{ id, label }]
  align: { type: String, default: 'right' }
})

const emit = defineEmits(['select'])

const open = ref(false)
const root = ref(null)

const onDocumentPointer = (e) => {
  if (root.value && !root.value.contains(e.target)) open.value = false
}

onMounted(() => document.addEventListener('mousedown', onDocumentPointer))
onUnmounted(() => document.removeEventListener('mousedown', onDocumentPointer))

const choose = (item) => {
  open.value = false
  emit('select', item.id)
}
</script>

<template>
  <div ref="root" class="relative" @keydown.esc="open = false">
    <button type="button" class="btn" aria-haspopup="menu" :aria-expanded="open" @click="open = !open">
      <slot name="icon" />
      <span>{{ label }}</span>
      <ChevronDown class="w-3 h-3 text-faint" />
    </button>
    <div
      v-if="open"
      role="menu"
      class="absolute top-full mt-1 z-40 min-w-44 rounded-md border border-line bg-panel shadow-lg py-1"
      :class="align === 'right' ? 'right-0' : 'left-0'"
    >
      <button
        v-for="item in items"
        :key="item.id"
        type="button"
        role="menuitem"
        class="w-full text-left px-3 h-7 text-xs text-fg hover:bg-raised cursor-pointer"
        @click="choose(item)"
      >
        {{ item.label }}
      </button>
    </div>
  </div>
</template>
```

### Task 2.3: Component tests

**File:** `src/components/ui/primitives.test.js`
```js
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import Panel from './Panel.vue'
import DataTable from './DataTable.vue'
import SeverityDot from './SeverityDot.vue'
import ThresholdScale from './ThresholdScale.vue'
import MenuButton from './MenuButton.vue'

describe('Panel', () => {
  it('renders slot content when ready', () => {
    const w = mount(Panel, { props: { title: 'Peers' }, slots: { default: '<p class="body">ok</p>' } })
    expect(w.find('h2').text()).toBe('Peers')
    expect(w.find('.body').exists()).toBe(true)
  })
  it('shows skeleton when loading', () => {
    const w = mount(Panel, { props: { title: 'x', state: 'loading' }, slots: { default: '<p class="body">ok</p>' } })
    expect(w.find('[data-state="loading"]').exists()).toBe(true)
    expect(w.find('.body').exists()).toBe(false)
  })
  it('shows empty text', () => {
    const w = mount(Panel, { props: { title: 'x', state: 'empty', emptyText: 'No filings' } })
    expect(w.find('[data-state="empty"]').text()).toContain('No filings')
  })
  it('emits retry from the error state', async () => {
    const w = mount(Panel, { props: { title: 'x', state: 'error', errorText: 'Boom' } })
    expect(w.find('[role="alert"]').text()).toContain('Boom')
    await w.find('button').trigger('click')
    expect(w.emitted('retry')).toHaveLength(1)
  })
})

describe('DataTable', () => {
  const columns = [
    { key: 'ticker', label: 'Ticker', sortable: true },
    { key: 'ffi', label: 'FFI', align: 'right', sortable: true, format: (v) => v.toFixed(1) }
  ]
  const rows = [
    { ticker: 'NVDA', ffi: 18 },
    { ticker: 'AMD', ffi: 34 },
    { ticker: 'SMCI', ffi: 84 }
  ]
  const tickers = (w) => w.findAll('tbody tr').map((tr) => tr.attributes('data-row'))

  it('formats cells', () => {
    const w = mount(DataTable, { props: { columns, rows, rowKey: 'ticker' } })
    expect(w.find('tbody tr td:last-child').text()).toBe('18.0')
  })
  it('sorts on header click and toggles direction', async () => {
    const w = mount(DataTable, { props: { columns, rows, rowKey: 'ticker' } })
    await w.findAll('thead button')[1].trigger('click')
    expect(tickers(w)).toEqual(['NVDA', 'AMD', 'SMCI'])
    await w.findAll('thead button')[1].trigger('click')
    expect(tickers(w)).toEqual(['SMCI', 'AMD', 'NVDA'])
    expect(w.findAll('th')[1].attributes('aria-sort')).toBe('descending')
  })
  it('emits row-click only when clickable', async () => {
    const plain = mount(DataTable, { props: { columns, rows, rowKey: 'ticker' } })
    await plain.find('tbody tr').trigger('click')
    expect(plain.emitted('row-click')).toBeUndefined()

    const w = mount(DataTable, { props: { columns, rows, rowKey: 'ticker', clickable: true } })
    await w.find('tbody tr').trigger('click')
    expect(w.emitted('row-click')[0][0]).toEqual(rows[0])
  })
  it('highlights the matching row', () => {
    const w = mount(DataTable, { props: { columns, rows, rowKey: 'ticker', highlight: 'AMD' } })
    expect(w.find('[data-row="AMD"]').classes()).toContain('bg-accent-soft')
  })
})

describe('SeverityDot', () => {
  it('labels severity for assistive tech', () => {
    const w = mount(SeverityDot, { props: { level: 'critical', withLabel: true } })
    expect(w.find('[role="img"]').attributes('aria-label')).toBe('Severity: Critical')
    expect(w.text()).toContain('Critical')
  })
})

describe('ThresholdScale', () => {
  it('positions the marker and exposes meter values', () => {
    const w = mount(ThresholdScale, { props: { value: -2, min: -4, max: 0, label: 'M-Score', thresholds: [{ at: -1.78, label: '-1.78' }] } })
    expect(w.find('[data-marker]').attributes('style')).toContain('left: 50%')
    expect(w.find('[role="meter"]').attributes('aria-valuenow')).toBe('-2')
  })
  it('omits the marker without a value', () => {
    const w = mount(ThresholdScale, { props: { value: null, min: -4, max: 0, label: 'M-Score' } })
    expect(w.find('[data-marker]').exists()).toBe(false)
  })
})

describe('MenuButton', () => {
  it('opens, selects, and closes', async () => {
    const w = mount(MenuButton, { props: { label: 'Memo', items: [{ id: 'preview', label: 'Preview memo' }] } })
    expect(w.find('[role="menu"]').exists()).toBe(false)
    await w.find('button').trigger('click')
    await w.find('[role="menuitem"]').trigger('click')
    expect(w.emitted('select')[0]).toEqual(['preview'])
    expect(w.find('[role="menu"]').exists()).toBe(false)
  })
})
```

- [ ] `npm test && npm run build` → pass. Commit `feat(ui): dashboard primitives with tests`.

---

## PR 3 — `feat/app-shell`

### Task 3.1: Extract profile data

- [ ] Create `src/data/companyProfiles.js` by moving, verbatim, from `CompanyHub.vue`:
  - `companyProfiles` (export const)
  - `categoryTickerMap['Macro Indices']` → `export const INDEX_TICKERS`
  - every non-index key of `companyProfiles` → `export const FEATURED_TICKERS`
  - `isIndexTicker` (export, implemented as `INDEX_TICKERS.includes(...)`)
  - the two synthetic-profile object literals inside `selectCompany` → `export function profileFromSearchEntry(ticker, entry)` and `export function fallbackProfile(ticker)`. Bodies are identical to the current branches.
- [ ] Delete from `CompanyHub.vue`: `sectorCategories`, `categoryTickerMap`, `visibleCategoryTickers`, `activeCategory`, `showCategoryMenu`, the search refs and handlers (`searchInput` … `navigateSearch`), `handleClickOutside` and its listeners, `companyProfiles`, `isIndexTicker`, `selectCompany`.

### Task 3.2: useCompany (TDD for pure parts)

**File:** `src/composables/useCompany.test.js`
```js
import { describe, it, expect } from 'vitest'
import { pushRecent, useCompany } from './useCompany.js'

describe('pushRecent', () => {
  it('adds to the front, dedupes, and caps length', () => {
    expect(pushRecent(['A', 'B'], 'C', 3)).toEqual(['C', 'A', 'B'])
    expect(pushRecent(['A', 'B', 'C'], 'B', 3)).toEqual(['B', 'A', 'C'])
    expect(pushRecent(['A', 'B', 'C'], 'D', 3)).toEqual(['D', 'A', 'B'])
  })
})

describe('useCompany.selectCompany', () => {
  it('selects a known profile and records it as recent', () => {
    const { currentCompany, recent, selectCompany } = useCompany()
    selectCompany('smci')
    expect(currentCompany.value.ticker).toBe('SMCI')
    expect(recent.value[0]).toBe('SMCI')
  })
  it('builds a fallback profile for unknown tickers', () => {
    const { currentCompany, selectCompany } = useCompany()
    selectCompany('ZZZZ')
    expect(currentCompany.value.ticker).toBe('ZZZZ')
    expect(currentCompany.value.name).toBe('ZZZZ Corporation')
  })
  it('ignores blank input', () => {
    const { currentCompany, selectCompany } = useCompany()
    const before = currentCompany.value
    selectCompany('  ')
    expect(currentCompany.value).toBe(before)
  })
})
```

**File:** `src/composables/useCompany.js`
```js
import { ref } from 'vue'
import { companyProfiles, profileFromSearchEntry, fallbackProfile } from '../data/companyProfiles.js'

const RECENT_MAX = 6
const SEARCH_DEBOUNCE_MS = 180

export const pushRecent = (list, ticker, max = RECENT_MAX) =>
  [ticker, ...list.filter((t) => t !== ticker)].slice(0, max)

const currentCompany = ref(companyProfiles.NVDA)
const recent = ref(['NVDA'])
const searchResults = ref([])
const isSearching = ref(false)
const searchError = ref('')
let searchTimer = null

const selectCompany = (ticker, entry = null) => {
  const t = (ticker || '').toUpperCase().trim()
  if (!t) return
  if (entry) currentCompany.value = profileFromSearchEntry(t, entry)
  else currentCompany.value = companyProfiles[t] ?? fallbackProfile(t)
  recent.value = pushRecent(recent.value, t)
}

const runSearch = (query) => {
  const q = (query || '').trim()
  if (searchTimer) clearTimeout(searchTimer)
  searchError.value = ''
  if (!q) {
    searchResults.value = []
    isSearching.value = false
    return
  }
  isSearching.value = true
  searchTimer = setTimeout(async () => {
    try {
      const res = await fetch(`/api/forensics/tickers/search?q=${encodeURIComponent(q)}&limit=8`)
      if (!res.ok) throw new Error('Search unavailable')
      const data = await res.json()
      searchResults.value = data.results || []
    } catch {
      searchResults.value = []
      searchError.value = 'Search unavailable. Showing local matches only.'
    } finally {
      isSearching.value = false
    }
  }, SEARCH_DEBOUNCE_MS)
}

export function useCompany () {
  return { currentCompany, recent, searchResults, isSearching, searchError, selectCompany, runSearch }
}
```

### Task 3.3: Severity helper for the strip (TDD)

Append to `src/utils/ffi.js`:

```js
const TIER_TO_SEVERITY = { low: 'good', watch: 'watch', critical: 'critical' }

export const ffiSeverity = (score) => TIER_TO_SEVERITY[ffiTier(score).key]
```

Add `src/utils/ffi.test.js` covering `ffiSeverity(10) === 'good'`, `(30) === 'watch'`, `(80) === 'critical'`, and `formatEnum('HIGH_RISK') === 'high risk'`, `formatEnum(null) === ''`.

### Task 3.4: Shell components

**File:** `src/components/shell/CompanySwitcher.vue`
```vue
<script setup>
import { ref, computed, nextTick, onMounted, onUnmounted } from 'vue'
import { ChevronDown, Search, Loader2 } from 'lucide-vue-next'
import { useCompany } from '../../composables/useCompany.js'
import { companyProfiles, INDEX_TICKERS, FEATURED_TICKERS } from '../../data/companyProfiles.js'

const { currentCompany, recent, searchResults, isSearching, searchError, selectCompany, runSearch } = useCompany()

const open = ref(false)
const query = ref('')
const active = ref(0)
const root = ref(null)
const input = ref(null)

const toItem = (ticker) => ({ ticker, name: companyProfiles[ticker]?.name ?? ticker, entry: null })

const localMatches = (q) => {
  const needle = q.toLowerCase()
  return Object.values(companyProfiles)
    .filter((p) => p.ticker.toLowerCase().includes(needle) || p.name.toLowerCase().includes(needle))
    .slice(0, 8)
    .map((p) => toItem(p.ticker))
}

const groups = computed(() => {
  const q = query.value.trim()
  if (q) {
    const remote = searchResults.value.map((r) => ({ ticker: r.ticker, name: r.name, entry: r }))
    return [{ label: 'Search results', items: remote.length ? remote : localMatches(q) }]
  }
  return [
    { label: 'Recent', items: recent.value.map(toItem) },
    { label: 'Indices', items: INDEX_TICKERS.map(toItem) },
    { label: 'Companies', items: FEATURED_TICKERS.map(toItem) }
  ].filter((g) => g.items.length)
})

const flat = computed(() => groups.value.flatMap((g) => g.items))
const indexOf = (item) => flat.value.indexOf(item)

const openMenu = async () => {
  open.value = true
  query.value = ''
  active.value = 0
  await nextTick()
  input.value?.focus()
}

const close = () => { open.value = false }

const choose = (item) => {
  selectCompany(item.ticker, item.entry)
  close()
}

const onInput = () => {
  active.value = 0
  runSearch(query.value)
}

const move = (dir) => {
  const n = flat.value.length
  if (n) active.value = (active.value + dir + n) % n
}

const onEnter = () => {
  const item = flat.value[active.value]
  if (item) choose(item)
  else if (query.value.trim()) { selectCompany(query.value); close() }
}

const onDocumentPointer = (e) => {
  if (root.value && !root.value.contains(e.target)) close()
}

onMounted(() => document.addEventListener('mousedown', onDocumentPointer))
onUnmounted(() => document.removeEventListener('mousedown', onDocumentPointer))
</script>

<template>
  <div ref="root" class="relative">
    <button
      type="button"
      class="btn max-w-56"
      aria-haspopup="listbox"
      :aria-expanded="open"
      :aria-label="`Switch company, current ${currentCompany.ticker} ${currentCompany.name}`"
      @click="open ? close() : openMenu()"
    >
      <span class="font-mono font-semibold">{{ currentCompany.ticker }}</span>
      <span class="hidden lg:inline truncate text-muted font-normal">{{ currentCompany.name }}</span>
      <ChevronDown class="w-3 h-3 text-faint shrink-0" />
    </button>

    <div
      v-if="open"
      class="absolute top-full left-0 mt-1 z-50 w-80 rounded-md border border-line bg-panel shadow-lg"
      @keydown.esc="close"
    >
      <div class="flex items-center gap-2 h-9 px-3 border-b border-line">
        <Search class="w-3.5 h-3.5 text-faint shrink-0" />
        <input
          ref="input"
          v-model="query"
          type="text"
          role="combobox"
          aria-label="Search companies and indices"
          :aria-expanded="open"
          placeholder="Ticker or company name"
          class="flex-1 bg-transparent text-xs text-fg placeholder:text-faint outline-none"
          @input="onInput"
          @keydown.down.prevent="move(1)"
          @keydown.up.prevent="move(-1)"
          @keydown.enter.prevent="onEnter"
        />
        <Loader2 v-if="isSearching" class="w-3.5 h-3.5 text-faint animate-spin" />
      </div>

      <p v-if="searchError && query" class="px-3 pt-2 text-[11px] text-watch">{{ searchError }}</p>

      <div role="listbox" class="max-h-80 overflow-y-auto py-1">
        <template v-for="group in groups" :key="group.label">
          <div class="px-3 pt-2 pb-1 text-[10px] font-semibold uppercase tracking-[0.04em] text-faint">{{ group.label }}</div>
          <button
            v-for="item in group.items"
            :key="`${group.label}-${item.ticker}`"
            type="button"
            role="option"
            :aria-selected="indexOf(item) === active"
            class="w-full flex items-center gap-3 px-3 h-7 text-left text-xs cursor-pointer"
            :class="indexOf(item) === active ? 'bg-raised text-fg' : 'text-fg hover:bg-raised'"
            @mouseenter="active = indexOf(item)"
            @click="choose(item)"
          >
            <span class="font-mono font-semibold w-12 shrink-0">{{ item.ticker }}</span>
            <span class="truncate text-muted">{{ item.name }}</span>
          </button>
        </template>
        <p v-if="!flat.length" class="px-3 py-2 text-xs text-muted">No matches. Press Enter to open “{{ query.trim().toUpperCase() }}”.</p>
      </div>
    </div>
  </div>
</template>
```

**File:** `src/components/shell/TopBar.vue`
```vue
<script setup>
import { Search, FileText, Sparkles } from 'lucide-vue-next'
import CompanySwitcher from './CompanySwitcher.vue'
import ThemeToggle from './ThemeToggle.vue'
import MenuButton from '../ui/MenuButton.vue'

defineProps({
  tabs: { type: Array, required: true }, // [{ id, label, count? }]
  currentTab: { type: String, required: true }
})

const emit = defineEmits(['update:currentTab', 'open-palette', 'memo', 'open-chat'])

const memoItems = [
  { id: 'preview', label: 'Preview memo' },
  { id: 'export', label: 'Export Markdown' }
]
</script>

<template>
  <header class="flex flex-wrap md:flex-nowrap items-center gap-x-3 gap-y-1 min-h-10 px-3 py-1 md:py-0 border-b border-line bg-panel shrink-0">
    <span class="text-sm font-semibold tracking-tight text-fg shrink-0">Zaisaku</span>
    <CompanySwitcher />

    <nav aria-label="Workspace" class="order-last md:order-none w-full md:w-auto md:flex-1 min-w-0 overflow-x-auto">
      <ul class="flex items-center gap-0.5 h-8 md:h-10">
        <li v-for="tab in tabs" :key="tab.id" class="h-full">
          <button
            type="button"
            class="h-full px-2.5 text-xs font-medium whitespace-nowrap border-b-2 cursor-pointer transition-colors"
            :class="currentTab === tab.id ? 'border-accent text-fg' : 'border-transparent text-muted hover:text-fg'"
            :aria-current="currentTab === tab.id ? 'page' : undefined"
            @click="emit('update:currentTab', tab.id)"
          >
            {{ tab.label }}
            <span v-if="tab.count" class="ml-1 text-faint tabular-nums">{{ tab.count }}</span>
          </button>
        </li>
      </ul>
    </nav>

    <div class="flex items-center gap-1 ml-auto shrink-0">
      <button type="button" class="btn-icon sm:hidden" aria-label="Open command palette" @click="emit('open-palette')">
        <Search class="w-3.5 h-3.5" />
      </button>
      <button type="button" class="btn hidden sm:inline-flex text-muted" title="Command palette" @click="emit('open-palette')">
        <Search class="w-3.5 h-3.5" />
        <kbd class="font-mono text-[10px]">⌘K</kbd>
      </button>
      <MenuButton label="Memo" :items="memoItems" @select="(id) => emit('memo', id)">
        <template #icon><FileText class="w-3.5 h-3.5 text-muted" /></template>
      </MenuButton>
      <ThemeToggle />
      <button type="button" class="btn-primary" @click="emit('open-chat')">
        <Sparkles class="w-3.5 h-3.5" />
        <span class="hidden sm:inline">Ask Zaisaku</span>
      </button>
    </div>
  </header>
</template>
```

**File:** `src/components/shell/CompanyStrip.vue`
```vue
<script setup>
import { computed } from 'vue'
import { Wrench } from 'lucide-vue-next'
import SeverityDot from '../ui/SeverityDot.vue'
import MenuButton from '../ui/MenuButton.vue'
import { ffiTier, ffiSeverity } from '../../utils/ffi.js'

const props = defineProps({
  company: { type: Object, required: true }
})

const emit = defineEmits(['tool'])

const toolItems = [
  { id: 'run-audit', label: 'Run audit' },
  { id: 'auditor-qa', label: 'Auditor Q&A' },
  { id: 'scorecard', label: 'Scorecard' },
  { id: 'sandbox', label: 'Prompt sandbox' }
]

const meta = computed(() => {
  const c = props.company
  return [
    c.exchange,
    c.cik && !/^0+$/.test(c.cik) ? `CIK ${c.cik}` : null,
    c.sector,
    c.period,
    c.auditor
  ].filter(Boolean)
})

const tier = computed(() => ffiTier(props.company.ffi))
const severity = computed(() => ffiSeverity(props.company.ffi))
</script>

<template>
  <div class="flex flex-wrap items-center gap-x-4 gap-y-1 min-h-9 px-3 py-1.5 border-b border-line bg-bg shrink-0">
    <div class="flex items-baseline gap-2 min-w-0">
      <h1 class="text-sm font-semibold text-fg truncate">{{ company.name }}</h1>
      <span class="font-mono text-xs text-muted">{{ company.ticker }}</span>
    </div>
    <ul class="flex flex-wrap items-center gap-x-3 gap-y-0.5 text-xs text-muted min-w-0">
      <li v-for="item in meta" :key="item" class="truncate max-w-64" :class="item.startsWith('CIK') ? 'font-mono' : ''">{{ item }}</li>
    </ul>
    <div class="flex items-center gap-2 ml-auto">
      <span class="inline-flex items-center gap-1.5 h-7 px-2.5 rounded border border-line bg-panel text-xs">
        <SeverityDot :level="severity" />
        <span class="text-muted">Risk</span>
        <span class="font-semibold text-fg tabular-nums">{{ company.ffi }}</span>
        <span class="text-muted">{{ tier.label }}</span>
      </span>
      <MenuButton label="Tools" :items="toolItems" @select="(id) => emit('tool', id)">
        <template #icon><Wrench class="w-3.5 h-3.5 text-muted" /></template>
      </MenuButton>
    </div>
  </div>
</template>
```

### Task 3.5: Wire CompanyHub, renames, legacy island

- [ ] Script: `import { useCompany } from '../composables/useCompany.js'`; `const { currentCompany, selectCompany } = useCompany()`. Import TopBar, CompanyStrip.
- [ ] `navigationTabs` becomes:

```js
const navigationTabs = computed(() => [
  { id: 'overview', label: 'Overview' },
  { id: 'financials', label: 'Financials' },
  { id: 'benchmarks', label: 'Trends & peers' },
  { id: 'scenarios', label: 'Scenarios' },
  { id: 'interrogation', label: 'Calls & Q&A' },
  { id: 'filings', label: 'Filings', count: documents.value.length || null }
])
```

- [ ] Add handlers:

```js
const handleMemo = (id) => {
  if (id === 'preview') showInstitutionalReportModal.value = true
  else if (id === 'export') exportDueDiligenceMemo()
}

const handleTool = (id) => {
  if (id === 'run-audit') showInvestigationRunner.value = true
  else if (id === 'auditor-qa') showAuditorModal.value = true
  else if (id === 'scorecard') showScorecardModal.value = true
  else if (id === 'sandbox') showSandboxModal.value = true
}
```

- [ ] `triggerAction`: `'footnote-scan'` → `openMScoreModal('footnotes')` (it currently opens the scorecard, which is the wrong target).
- [ ] Template: replace everything from `<!-- Top Persistent Apple Frosted Glass Header -->` through the end of the sub-header `</div>` (just before `<!-- Main Workspace Body`) with:

```html
    <TopBar
      v-model:current-tab="currentTab"
      :tabs="navigationTabs"
      @open-palette="emit('open-palette')"
      @memo="handleMemo"
      @open-chat="emit('open-chat')"
    />
    <CompanyStrip :company="currentCompany" @tool="handleTool" />
```

- [ ] Root element: `class="flex-1 flex flex-col h-screen overflow-hidden bg-bg text-fg"`.
- [ ] `<main>` becomes a legacy dark island: `<main data-theme="dark" class="flex-1 overflow-y-auto p-6 custom-scrollbar bg-bg text-fg">`. PR 4 lifts the Overview out of it.
- [ ] Delete the hero `<section>` (`<!-- Hero Profile & FFI Card -->`). The strip and Tools menu replace it. Keep the governance banner and pillars until PR 4.
- [ ] Transition: rename `apple-view` → `fade-view`; in scoped style replace the four `apple-view-*` rules with:

```css
.fade-view-enter-active,
.fade-view-leave-active {
  transition: opacity 0.15s ease;
}
.fade-view-enter-from,
.fade-view-leave-to {
  opacity: 0;
}
```

- [ ] Remove the now-unused lucide imports flagged by the build, and the `ffiColor`/`ffiTier` import if unused.
- [ ] `App.vue` root: `class="flex h-screen w-full overflow-hidden bg-bg text-fg"`.
- [ ] Rename user-visible "Co-Analyst" → "Ask Zaisaku" in `App.vue`, `ChatArea.vue`, `CommandPaletteModal.vue`, `CompanyHub.vue`, `FilingViewerModal.vue` (strings and comments only; check each hit with `grep -rn "Co-Analyst" src`). The palette's "Ask AI Co-Analyst:" row reads "Ask Zaisaku:".
- [ ] Palette workspace labels/descriptions: update to the new tab names (Overview, Financials, Trends & peers, Scenarios, Calls & Q&A, Filings).
- [ ] Remaining inflated strings in `CompanyHub.vue` legacy tabs: "Autonomous Multi-Agent Audit"/"Run autonomous audit" → "Run audit"; "Adversarial cross-examination" → "Auditor Q&A"; "Inspect audit scorecard" → "Scorecard".

- [ ] Verify: `npm test && npm run build`. Then a headless browser at 1440/1280/390 in light and dark (set `localStorage['zaisaku-theme']` via `page.addInitScript`):
  - the top bar is one row at ≥768;
  - the switcher opens, filters and selects;
  - the Memo menu opens the preview;
  - the Tools menu opens the scorecard;
  - legacy tabs stay dark in light mode.
- [ ] Commit `feat(ui): slim app shell with company switcher and plain naming`.

---

## PR 4 — `feat/overview-dashboard`

### Task 4.1: Shared severity thresholds (TDD)

Append to `src/utils/ffi.js`:

```js
// Beneish (1999): above -1.78 flags a likely manipulator; -2.22 is the conservative cut-off.
export const MSCORE_THRESHOLD = -1.78
export const MSCORE_GREY_ZONE = -2.22

const byThreshold = (value, watchAt, criticalAt) => {
  if (value === null || value === undefined) return 'watch'
  if (value >= criticalAt) return 'critical'
  return value >= watchAt ? 'watch' : 'good'
}

export const driftSeverity = (pct) => byThreshold(pct, 15, 30)
export const decouplingSeverity = (score) => byThreshold(score, 25, 50)

export const mscoreSeverity = (m) => {
  if (m === null || m === undefined) return 'watch'
  if (m > MSCORE_THRESHOLD) return 'critical'
  return m > MSCORE_GREY_ZONE ? 'watch' : 'good'
}

export const footnoteSeverity = (clean, count) => {
  if (clean !== false) return 'good'
  return (count ?? 0) >= 4 ? 'critical' : 'watch'
}

export const tierToSeverity = (tier) => {
  const t = String(tier || '').toUpperCase()
  if (t.startsWith('CRITICAL')) return 'critical'
  if (t === 'WATCHLIST') return 'watch'
  return 'good'
}

export const SEVERITY_RANK = { critical: 0, watch: 1, good: 2 }
```

Extend `src/utils/ffi.test.js`:
- drift 14.9 → good, 15 → watch, 30 → critical, null → watch
- decoupling 24 → good, 25 → watch, 50 → critical
- mscore −2.85 → good, −2.0 → watch, −1.42 → critical
- footnotes `(true, 0)` → good, `(false, 3)` → watch, `(false, 4)` → critical
- tiers `CRITICAL_ALERT` → critical, `WATCHLIST` → watch, `LOW_RISK` → good

- [ ] Refactor `InstitutionalReportModal.vue` `pillars` to use `driftSeverity`, `decouplingSeverity`, `mscoreSeverity`, `footnoteSeverity`, `MSCORE_THRESHOLD`, and delete its local `MSCORE_*`, `byThreshold` and inline M-Score severity. Behaviour is identical.

### Task 4.2: Overview logic (TDD)

**File:** `src/components/overview/overviewModel.test.js`
```js
import { describe, it, expect } from 'vitest'
import { buildRedFlags, riskBreakdown } from './overviewModel.js'

const nvda = {
  ticker: 'NVDA', driftScore: 8.5, driftExcerpt: 'Export controls.',
  mscore: -2.85, tataAccrual: -0.045, mscoreProb: '< 1%',
  divergenceScore: 11, radarExcerpt: 'Guidance aligned.',
  footnotesClean: true, footnoteCount: 0, footnoteExcerpt: 'Customer A 13%.'
}
const smci = {
  ticker: 'SMCI', driftScore: 42, driftExcerpt: 'Special Committee.',
  mscore: -1.42, tataAccrual: 0.124, mscoreProb: '76%',
  divergenceScore: 78.5, radarExcerpt: 'Guidance conflicts.',
  footnotesClean: false, footnoteCount: 4, footnoteExcerpt: 'Auditor resigned.'
}

describe('buildRedFlags', () => {
  it('maps each pillar to a row with source and action', () => {
    const rows = buildRedFlags(nvda)
    expect(rows.map((r) => r.id).sort()).toEqual(['accruals', 'contradictions', 'drift', 'footnotes'])
    const drift = rows.find((r) => r.id === 'drift')
    expect(drift).toMatchObject({ source: '10-K Item 1A', action: 'diff', severity: 'good', finding: 'Export controls.' })
    expect(rows.find((r) => r.id === 'footnotes').action).toBe('footnotes')
    expect(rows.find((r) => r.id === 'contradictions').source).toBe('Earnings call')
  })

  it('describes accruals against the threshold', () => {
    expect(buildRedFlags(smci).find((r) => r.id === 'accruals').finding)
      .toBe('M-Score -1.42 is above the -1.78 manipulation threshold (TATA 0.124).')
  })

  it('sorts critical first and keeps pillar order within a level', () => {
    const mixed = { ...nvda, driftScore: 42, footnotesClean: false, footnoteCount: 1 }
    expect(buildRedFlags(mixed).map((r) => r.severity)).toEqual(['critical', 'watch', 'good', 'good'])
    expect(buildRedFlags(mixed)[0].id).toBe('drift')
  })

  it('skips pillars without data', () => {
    const rows = buildRedFlags({ ticker: 'X', driftExcerpt: '', mscore: null })
    expect(rows).toEqual([])
  })
})

describe('riskBreakdown', () => {
  it('returns weighted components with formatted values and severities', () => {
    expect(riskBreakdown(smci)).toEqual([
      { id: 'drift', label: 'Language drift', weight: 30, value: '42%', severity: 'critical' },
      { id: 'mscore', label: 'Beneish M-Score', weight: 40, value: '-1.42', severity: 'critical' },
      { id: 'contradictions', label: 'Call vs 10-Q', weight: 30, value: '78.5', severity: 'critical' }
    ])
  })
  it('shows a dash for missing values', () => {
    expect(riskBreakdown({}).map((r) => r.value)).toEqual(['—', '—', '—'])
  })
})
```

**File:** `src/components/overview/overviewModel.js`
```js
import {
  MSCORE_THRESHOLD,
  SEVERITY_RANK,
  driftSeverity,
  decouplingSeverity,
  mscoreSeverity,
  footnoteSeverity
} from '../../utils/ffi.js'

const has = (v) => v !== null && v !== undefined && v !== ''

export function buildRedFlags (p) {
  const rows = []
  if (has(p.driftExcerpt)) {
    rows.push({ id: 'drift', severity: driftSeverity(p.driftScore), finding: p.driftExcerpt, source: '10-K Item 1A', action: 'diff' })
  }
  if (has(p.mscore)) {
    const side = p.mscore > MSCORE_THRESHOLD ? 'above' : 'below'
    const tata = has(p.tataAccrual) ? ` (TATA ${p.tataAccrual})` : ''
    rows.push({
      id: 'accruals',
      severity: mscoreSeverity(p.mscore),
      finding: `M-Score ${p.mscore} is ${side} the ${MSCORE_THRESHOLD} manipulation threshold${tata}.`,
      source: '10-K financials',
      action: 'mscore'
    })
  }
  if (has(p.radarExcerpt)) {
    rows.push({ id: 'contradictions', severity: decouplingSeverity(p.divergenceScore), finding: p.radarExcerpt, source: 'Earnings call', action: 'radar' })
  }
  if (has(p.footnoteExcerpt)) {
    rows.push({ id: 'footnotes', severity: footnoteSeverity(p.footnotesClean, p.footnoteCount), finding: p.footnoteExcerpt, source: '10-K notes', action: 'footnotes' })
  }
  // Array.prototype.sort is stable, so pillar order is kept within a severity level.
  return rows.sort((a, b) => SEVERITY_RANK[a.severity] - SEVERITY_RANK[b.severity])
}

const fmt = (v, suffix = '') => (has(v) ? `${v}${suffix}` : '—')

export function riskBreakdown (p) {
  return [
    { id: 'drift', label: 'Language drift', weight: 30, value: fmt(p.driftScore, '%'), severity: driftSeverity(p.driftScore) },
    { id: 'mscore', label: 'Beneish M-Score', weight: 40, value: fmt(p.mscore), severity: mscoreSeverity(p.mscore) },
    { id: 'contradictions', label: 'Call vs 10-Q', weight: 30, value: fmt(p.divergenceScore), severity: decouplingSeverity(p.divergenceScore) }
  ]
}
```

(Spec named two files `redFlags.js` and `riskBreakdown.js`. They are merged into one `overviewModel.js` because both are tiny and share imports.)

### Task 4.3: OverviewDashboard

**File:** `src/components/overview/OverviewDashboard.vue`
```vue
<script setup>
import { ref, computed, watch } from 'vue'
import Panel from '../ui/Panel.vue'
import DataTable from '../ui/DataTable.vue'
import SeverityDot from '../ui/SeverityDot.vue'
import SourceChip from '../ui/SourceChip.vue'
import StatValue from '../ui/StatValue.vue'
import ThresholdScale from '../ui/ThresholdScale.vue'
import { buildRedFlags, riskBreakdown } from './overviewModel.js'
import { ffiTier, ffiSeverity, formatEnum, tierToSeverity, mscoreSeverity, MSCORE_THRESHOLD, MSCORE_GREY_ZONE } from '../../utils/ffi.js'

const props = defineProps({
  company: { type: Object, required: true },
  documents: { type: Array, default: () => [] },
  documentsState: { type: String, default: 'ready' } // ready | loading | error
})

const emit = defineEmits(['open-scorecard', 'open-anomaly', 'flag-action', 'open-mscore', 'open-diff', 'go-tab', 'open-sec', 'open-filing', 'retry-documents'])

const tier = computed(() => ffiTier(props.company.ffi))
const flags = computed(() => buildRedFlags(props.company))
const breakdown = computed(() => riskBreakdown(props.company))
const mscoreLevel = computed(() => mscoreSeverity(props.company.mscore))

const flagColumns = [
  { key: 'severity', label: '', width: '28px' },
  { key: 'finding', label: 'Finding' },
  { key: 'source', label: 'Source', align: 'right', width: '120px' }
]

const breakdownColumns = [
  { key: 'label', label: 'Component' },
  { key: 'weight', label: 'Weight', align: 'right', format: (v) => `${v}%` },
  { key: 'value', label: 'Value', align: 'right' },
  { key: 'severity', label: '', align: 'right', width: '28px' }
]

// --- Peers ---
const peers = ref([])
const peersState = ref('loading')

const fetchPeers = async (ticker) => {
  peersState.value = 'loading'
  try {
    const res = await fetch(`/api/forensics/peers/${encodeURIComponent(ticker)}`)
    if (!res.ok) throw new Error('peers')
    const data = await res.json()
    peers.value = data.peers || []
    peersState.value = peers.value.length ? 'ready' : 'empty'
  } catch {
    peersState.value = 'error'
  }
}

watch(() => props.company.ticker, (t) => { if (t) fetchPeers(t) }, { immediate: true })

const peerColumns = [
  { key: 'ticker', label: 'Ticker', sortable: true },
  { key: 'name', label: 'Company', sortable: true },
  { key: 'market_cap', label: 'Mkt cap', align: 'right' },
  { key: 'ffi', label: 'FFI', align: 'right', sortable: true, format: (v) => v?.toFixed(1) },
  { key: 'drift_pct', label: 'Drift', align: 'right', sortable: true, format: (v) => `${v}%` },
  { key: 'beneish_mscore', label: 'M-Score', align: 'right', sortable: true, format: (v) => v?.toFixed(2) },
  { key: 'risk_tier', label: 'Tier', sortable: true },
  { key: 'key_vulnerability', label: 'Key vulnerability' }
]

// --- Filings ---
const recentDocs = computed(() => props.documents.slice(0, 6).map((d) => ({ ...d, short_id: String(d.doc_id).slice(0, 8) })))
const filingsState = computed(() => {
  if (props.documentsState !== 'ready') return props.documentsState
  return recentDocs.value.length ? 'ready' : 'empty'
})
const docColumns = [
  { key: 'source', label: 'Document' },
  { key: 'short_id', label: 'ID', align: 'right' }
]
</script>

<template>
  <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3 p-3">
    <!-- Risk score -->
    <Panel title="Risk score">
      <template #actions>
        <button type="button" class="btn-ghost" @click="emit('open-scorecard')">Scorecard</button>
      </template>
      <div class="p-3 flex items-start justify-between gap-4">
        <StatValue :value="company.ffi" :label="company.is_macro_index ? 'Macro fragility index' : 'Forensic fragility index'" sub="0 = clean · 100 = critical" />
        <span class="inline-flex items-center gap-1.5 text-xs text-muted">
          <SeverityDot :level="ffiSeverity(company.ffi)" />
          {{ tier.label }}
        </span>
      </div>
      <p v-if="company.is_macro_index" class="px-3 pb-3 text-xs text-muted">Constituent-weighted dispersion across index holdings.</p>
      <DataTable v-else :columns="breakdownColumns" :rows="breakdown" row-key="id">
        <template #cell-severity="{ row }"><SeverityDot :level="row.severity" /></template>
      </DataTable>
    </Panel>

    <!-- Red flags -->
    <Panel :title="company.is_macro_index ? 'Signals' : 'Red flags'" class="md:col-span-2" :state="flags.length ? 'ready' : 'empty'" empty-text="No findings for this period.">
      <template #actions>
        <button type="button" class="btn-ghost" @click="emit('open-anomaly')">Anomaly radar</button>
      </template>
      <DataTable :columns="flagColumns" :rows="flags" row-key="id" clickable @row-click="(row) => emit('flag-action', row.action)">
        <template #cell-severity="{ row }"><SeverityDot :level="row.severity" /></template>
        <template #cell-finding="{ row }"><span class="line-clamp-2">{{ row.finding }}</span></template>
        <template #cell-source="{ row }"><SourceChip :label="row.source" @open="emit('flag-action', row.action)" /></template>
      </DataTable>
    </Panel>

    <!-- M-Score -->
    <Panel title="Beneish M-Score" :state="company.mscore == null ? 'empty' : 'ready'" empty-text="M-Score not available for this filer.">
      <template #actions>
        <button type="button" class="btn-ghost" @click="emit('open-mscore')">Calculator</button>
      </template>
      <div class="p-3 space-y-3">
        <div class="flex items-start justify-between gap-4">
          <StatValue :value="company.mscore" label="Eight-variable score" :sub="`Probability ${company.mscoreProb ?? '—'} · TATA ${company.tataAccrual ?? '—'}`" />
          <SeverityDot :level="mscoreLevel" with-label />
        </div>
        <ThresholdScale
          :value="company.mscore"
          :min="-4"
          :max="0"
          label="Beneish M-Score position against thresholds"
          :thresholds="[{ at: MSCORE_GREY_ZONE, label: String(MSCORE_GREY_ZONE) }, { at: MSCORE_THRESHOLD, label: String(MSCORE_THRESHOLD) }]"
        />
      </div>
    </Panel>

    <!-- Language drift -->
    <Panel title="Language drift" :state="company.driftScore == null ? 'empty' : 'ready'" empty-text="No risk-factor redline for this period.">
      <template #actions>
        <button type="button" class="btn-ghost" @click="emit('open-diff')">Redline</button>
      </template>
      <div class="p-3 space-y-3">
        <StatValue :value="`${company.driftScore}%`" label="Year-over-year risk-factor drift" :sub="`+${company.driftAdded ?? 0} added · −${company.driftRemoved ?? 0} retired`" />
        <blockquote v-if="company.driftExcerpt" class="border-l-2 border-line pl-3 text-xs text-muted">{{ company.driftExcerpt }}</blockquote>
      </div>
    </Panel>

    <!-- Filings -->
    <Panel
      title="Filings"
      :state="filingsState"
      empty-text="No filings ingested."
      error-text="Could not load filings."
      @retry="emit('retry-documents')"
    >
      <template #actions>
        <button type="button" class="btn-ghost" @click="emit('open-sec')">Ingest</button>
      </template>
      <template #empty-action>
        <button type="button" class="btn" @click="emit('open-sec')">Ingest from EDGAR</button>
      </template>
      <DataTable :columns="docColumns" :rows="recentDocs" row-key="doc_id" clickable @row-click="(doc) => emit('open-filing', doc)">
        <template #cell-source="{ row }"><span class="truncate block max-w-56">{{ row.source || 'Document' }}</span></template>
        <template #cell-short_id="{ row }"><span class="font-mono text-faint">{{ row.short_id }}</span></template>
      </DataTable>
    </Panel>

    <!-- Peers -->
    <Panel
      title="Sector peers"
      class="md:col-span-2 xl:col-span-3"
      :state="peersState"
      empty-text="No peer set for this company."
      error-text="Could not load peer benchmark. The analysis service may be offline."
      @retry="fetchPeers(company.ticker)"
    >
      <template #actions>
        <button type="button" class="btn-ghost" @click="emit('go-tab', 'benchmarks')">Trends &amp; peers</button>
      </template>
      <DataTable :columns="peerColumns" :rows="peers" row-key="ticker" :highlight="company.ticker" :initial-sort="{ key: 'ffi', dir: 'desc' }">
        <template #cell-ticker="{ value }"><span class="font-mono font-semibold">{{ value }}</span></template>
        <template #cell-risk_tier="{ value }"><SeverityDot :level="tierToSeverity(value)" /> <span class="text-muted">{{ formatEnum(value) }}</span></template>
        <template #cell-key_vulnerability="{ value }"><span class="line-clamp-1 text-muted">{{ value }}</span></template>
      </DataTable>
    </Panel>
  </div>
</template>
```

**File:** `src/components/overview/OverviewDashboard.test.js`
```js
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import OverviewDashboard from './OverviewDashboard.vue'

const company = {
  ticker: 'NVDA', name: 'NVIDIA', ffi: 18, riskTier: 'LOW_RISK',
  driftScore: 8.5, driftAdded: 4, driftRemoved: 2, driftExcerpt: 'Export controls.',
  mscore: -2.85, mscoreProb: '< 1%', tataAccrual: -0.045,
  divergenceScore: 11, radarExcerpt: 'Aligned.',
  footnotesClean: true, footnoteCount: 0, footnoteExcerpt: 'Customer A.'
}

describe('OverviewDashboard', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn(async () => ({ ok: false, json: async () => ({}) })))
  })

  it('renders red flags and routes row clicks to flag-action', async () => {
    const w = mount(OverviewDashboard, { props: { company } })
    await flushPromises()
    const flagsPanel = w.findAll('section').find((sec) => sec.find('h2').text() === 'Red flags')
    const row = flagsPanel.find('[data-row="drift"]')
    expect(row.text()).toContain('Export controls.')
    await row.trigger('click')
    expect(w.emitted('flag-action')[0]).toEqual(['diff'])
  })

  it('shows the peers error state with retry when the API fails', async () => {
    const w = mount(OverviewDashboard, { props: { company } })
    await flushPromises()
    expect(w.text()).toContain('Could not load peer benchmark')
    expect(fetch).toHaveBeenCalledWith('/api/forensics/peers/NVDA')
  })

  it('shows the filings empty state with an ingest action', async () => {
    const w = mount(OverviewDashboard, { props: { company, documents: [] } })
    await flushPromises()
    expect(w.text()).toContain('No filings ingested.')
    await w.findAll('button').find((b) => b.text() === 'Ingest from EDGAR').trigger('click')
    expect(w.emitted('open-sec')).toHaveLength(1)
  })

  it('replaces the breakdown table for macro indices', async () => {
    const w = mount(OverviewDashboard, { props: { company: { ...company, is_macro_index: true } } })
    await flushPromises()
    expect(w.text()).toContain('Constituent-weighted dispersion')
    expect(w.text()).toContain('Signals')
  })
})
```

### Task 4.4: Wire into CompanyHub

- [ ] Add `const docsLoadError = ref(false)`. In `fetchDocuments`: set it `false` at the start, and `true` on `!res.ok` or in `catch`. Then:

```js
const documentsState = computed(() => (isLoadingDocs.value ? 'loading' : docsLoadError.value ? 'error' : 'ready'))

const handleFlagAction = (action) => {
  if (action === 'diff') showDiffModal.value = true
  else if (action === 'radar') showRadarModal.value = true
  else if (action === 'footnotes') openMScoreModal('footnotes')
  else if (action === 'mscore') openMScoreModal('mscore')
}
```

- [ ] Template: render the Overview *outside* the legacy island. Replace the `<main …>` block with:

```html
    <main class="flex-1 overflow-y-auto custom-scrollbar">
      <Transition name="fade-view" mode="out-in">
        <OverviewDashboard
          v-if="currentTab === 'overview'"
          key="overview"
          :company="currentCompany"
          :documents="documents"
          :documents-state="documentsState"
          @open-scorecard="showScorecardModal = true"
          @open-anomaly="showAnomalyModal = true"
          @flag-action="handleFlagAction"
          @open-mscore="openMScoreModal('mscore')"
          @open-diff="showDiffModal = true"
          @go-tab="switchWorkspace"
          @open-sec="showSecModal = true"
          @open-filing="openFilingViewer"
          @retry-documents="fetchDocuments"
        />
        <div v-else :key="currentTab" data-theme="dark" class="min-h-full bg-bg text-fg p-6">
          <div class="max-w-7xl mx-auto">
            <!-- existing VIEW 2..6 blocks, unchanged, with their v-if / v-else-if chain re-rooted so the first one uses v-if -->
          </div>
        </div>
      </Transition>
    </main>
```

  The existing VIEW 2–6 blocks move into that inner div as an inner `v-if`/`v-else-if` chain keyed by `currentTab`. Their markup is unchanged.

- [ ] Delete VIEW 1 entirely (governance banner + four pillar cards).
- [ ] Delete scoped `.apple-press`, `.apple-glass`, and `.apple-card` rules if the build shows no remaining usages in `CompanyHub.vue`. Legacy tabs may still use them, so delete only if `grep` finds 0 hits.
- [ ] Verify:
  - `npm test && npm run build`.
  - Headless browser at 1440×900 in light and dark: six panels, Risk/Red flags/M-Score/Drift/Filings above the fold, peers error card with Retry (backend down).
  - At 390×844: single column.
  - SMCI: red flags all critical, M-Score marker right of −1.78.
  - SPY: "Signals" + dispersion text.
  - Clicking the drift row opens the redline modal.
- [ ] Commit `feat(ui): dense overview dashboard`.

---

## Self-review

- Spec §1 tokens, type, density, motion → Tasks 1.4, 1.5. ✔
- Spec §2 shell, renames, files → Tasks 3.1–3.5. ✔ (switcher groups deviation noted at top)
- Spec §3 six panels, macro case, removed items → Tasks 4.2–4.4. ✔
- Spec §4 states, theme persistence, Vitest + CI, delivery → Tasks 1.1–1.3, 2.2, 4.3. ✔
- Names consistent: `ffiSeverity`, `tierToSeverity`, `buildRedFlags`, `riskBreakdown`, `scalePosition`, `sortRows`, `useCompany().selectCompany`, `handleFlagAction`, `documentsState`. ✔
