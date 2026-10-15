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
