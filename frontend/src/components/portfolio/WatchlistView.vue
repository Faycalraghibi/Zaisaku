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
