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
