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
