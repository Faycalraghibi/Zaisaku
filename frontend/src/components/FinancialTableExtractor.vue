<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import {
  Table,
  Download,
  Sparkles,
  TrendingUp,
  TrendingDown,
  RefreshCw,
  CheckCircle2,
  FileSpreadsheet,
  AlertCircle
} from 'lucide-vue-next'

const props = defineProps({
  ticker: {
    type: String,
    default: 'NVDA'
  },
  companyName: {
    type: String,
    default: 'NVIDIA Corporation'
  }
})

const loading = ref(false)
const error = ref(null)
const data = ref(null)
const activeStatementIndex = ref(0)
const copiedCsv = ref(false)

const currentStatement = computed(() => {
  if (!data.value || !data.value.statements || data.value.statements.length === 0) {
    return null
  }
  return data.value.statements[activeStatementIndex.value] || data.value.statements[0]
})

const fetchTables = async () => {
  loading.value = true
  error.value = null
  try {
    const res = await fetch(`/api/forensics/tables/${encodeURIComponent(props.ticker)}`)
    if (!res.ok) {
      throw new Error(`Failed to load financial tables (${res.status})`)
    }
    const json = await res.json()
    data.value = json
    activeStatementIndex.value = 0
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

watch(() => props.ticker, () => {
  fetchTables()
})

onMounted(() => {
  fetchTables()
})

// --- RFC 4180 CSV Export ---
const exportToCsv = () => {
  if (!currentStatement.value) return

  const stmt = currentStatement.value
  const headers = ['Line Item', ...stmt.period_labels, 'YoY Change (%)', 'AI Forensic Insight']
  
  const escapeCsv = (str) => {
    if (str == null) return ''
    const s = String(str).replace(/"/g, '""')
    return `"${s}"`
  }

  const csvRows = [
    headers.map(escapeCsv).join(','),
    ...stmt.rows.map(row => {
      const vals = row.values.map(v => (v != null ? Number(v).toFixed(1) : ''))
      const yoy = row.yoy_change_pct != null ? `${row.yoy_change_pct}%` : 'N/A'
      const insight = row.ai_insight || ''
      return [
        escapeCsv(row.line_item),
        ...vals.map(escapeCsv),
        escapeCsv(yoy),
        escapeCsv(insight)
      ].join(',')
    })
  ]

  const blob = new Blob([csvRows.join('\r\n')], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${props.ticker}_${stmt.id}_statements.csv`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)

  copiedCsv.value = true
  setTimeout(() => {
    copiedCsv.value = false
  }, 2500)
}

const formatNumber = (val) => {
  if (val == null) return '—'
  return Number(val).toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 1 })
}
</script>

<template>
  <div class="financial-table-extractor bg-[#141416]/80 backdrop-blur-2xl border border-white/10 rounded-2xl p-6 shadow-2xl transition-all">
    <!-- Header -->
    <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-5 border-b border-white/10">
      <div class="flex items-center gap-3">
        <div class="w-10 h-10 rounded-xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400">
          <Table class="w-5 h-5" />
        </div>
        <div>
          <div class="flex items-center gap-2">
            <h3 class="text-lg font-semibold text-white tracking-tight">
              Structured Financial Statements & Segment Extraction
            </h3>
            <span class="inline-flex items-center gap-1 px-2 py-0.5 text-[11px] font-medium rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              <CheckCircle2 class="w-3 h-3" /> XBRL Verified
            </span>
          </div>
          <p class="text-xs text-neutral-400 mt-0.5">
            Automated multi-period statement extraction, variance audit, and segment disaggregation for {{ ticker }}
          </p>
        </div>
      </div>

      <!-- Action Buttons -->
      <div class="flex items-center gap-2">
        <button
          @click="fetchTables"
          :disabled="loading"
          class="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-neutral-300 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg transition-all active:scale-[0.98]"
        >
          <RefreshCw :class="['w-3.5 h-3.5', loading ? 'animate-spin' : '']" />
          <span>Refresh</span>
        </button>

        <button
          @click="exportToCsv"
          :disabled="!currentStatement || loading"
          class="inline-flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-medium text-white bg-blue-600 hover:bg-blue-500 border border-blue-400/30 rounded-lg shadow-sm transition-all active:scale-[0.98]"
        >
          <FileSpreadsheet class="w-3.5 h-3.5" />
          <span>{{ copiedCsv ? 'CSV Exported!' : 'Export CSV' }}</span>
        </button>
      </div>
    </div>

    <!-- Error State -->
    <div v-if="error" class="p-4 my-4 bg-rose-500/10 border border-rose-500/20 rounded-xl flex items-center gap-3 text-rose-300 text-xs">
      <AlertCircle class="w-4 h-4 shrink-0" />
      <span>{{ error }}</span>
    </div>

    <!-- Loading State -->
    <div v-if="loading && !data" class="py-16 flex flex-col items-center justify-center gap-3 text-neutral-400">
      <RefreshCw class="w-6 h-6 animate-spin text-blue-400" />
      <span class="text-xs">Extracting structured financial tables and calculating YoY variance...</span>
    </div>

    <!-- Main Content -->
    <div v-else-if="currentStatement" class="mt-5 space-y-5">
      <!-- Statement Tabs -->
      <div class="flex items-center gap-2 overflow-x-auto pb-1 border-b border-white/5">
        <button
          v-for="(stmt, idx) in data.statements"
          :key="stmt.id"
          @click="activeStatementIndex = idx"
          :class="[
            'px-3.5 py-2 text-xs font-medium rounded-xl transition-all whitespace-nowrap',
            activeStatementIndex === idx
              ? 'bg-white/15 text-white border border-white/20 shadow-inner'
              : 'text-neutral-400 hover:text-neutral-200 hover:bg-white/5'
          ]"
        >
          {{ stmt.title }}
        </button>
        <span class="ml-auto text-[11px] text-neutral-400 self-center hidden sm:inline-block">
          Currency: {{ currentStatement.currency }}
        </span>
      </div>

      <!-- Financial Statement Table -->
      <div class="overflow-x-auto rounded-xl border border-white/10 bg-black/20">
        <table class="w-full text-left border-collapse text-xs">
          <thead>
            <tr class="border-b border-white/10 bg-white/[0.04] text-neutral-300 uppercase tracking-wider text-[11px]">
              <th class="py-3 px-4 font-semibold">Line Item</th>
              <th
                v-for="period in currentStatement.period_labels"
                :key="period"
                class="py-3 px-3 text-right font-semibold"
              >
                {{ period }}
              </th>
              <th class="py-3 px-3 text-right font-semibold">YoY Change</th>
              <th class="py-3 px-4 font-semibold">AI Forensic Insight</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-white/5">
            <tr
              v-for="(row, rIdx) in currentStatement.rows"
              :key="rIdx"
              :class="[
                'transition-colors hover:bg-white/[0.02]',
                row.is_total ? 'bg-white/[0.03] font-semibold text-white' : 'text-neutral-300'
              ]"
            >
              <!-- Line Item -->
              <td class="py-2.5 px-4">
                <span
                  :class="[
                    row.is_indent ? 'pl-5 text-neutral-400' : '',
                    row.is_total ? 'text-white font-medium' : ''
                  ]"
                >
                  {{ row.line_item }}
                </span>
              </td>

              <!-- Period Values -->
              <td
                v-for="(val, vIdx) in row.values"
                :key="vIdx"
                class="py-2.5 px-3 text-right font-mono text-[12px]"
              >
                {{ formatNumber(val) }}
              </td>

              <!-- YoY Change % -->
              <td class="py-2.5 px-3 text-right font-mono text-[12px]">
                <div v-if="row.yoy_change_pct != null" class="inline-flex items-center justify-end gap-1">
                  <TrendingUp v-if="row.yoy_change_pct > 0" class="w-3 h-3 text-emerald-400 shrink-0" />
                  <TrendingDown v-else-if="row.yoy_change_pct < 0" class="w-3 h-3 text-rose-400 shrink-0" />
                  <span
                    :class="[
                      'font-medium',
                      row.yoy_change_pct > 0 ? 'text-emerald-400' : row.yoy_change_pct < 0 ? 'text-rose-400' : 'text-neutral-400'
                    ]"
                  >
                    {{ row.yoy_change_pct > 0 ? '+' : '' }}{{ row.yoy_change_pct }}%
                  </span>
                </div>
                <span v-else class="text-neutral-500">—</span>
              </td>

              <!-- AI Forensic Insight -->
              <td class="py-2.5 px-4 text-neutral-300">
                <div v-if="row.ai_insight" class="flex items-center gap-1.5 text-[11px] text-blue-300 bg-blue-500/10 border border-blue-500/20 px-2 py-1 rounded-md">
                  <Sparkles class="w-3 h-3 text-blue-400 shrink-0" />
                  <span>{{ row.ai_insight }}</span>
                </div>
                <span v-else class="text-neutral-600 text-[11px]">—</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Footnote summary -->
      <div class="flex flex-col sm:flex-row sm:items-center justify-between text-[11px] text-neutral-400 pt-2 px-1">
        <div>
          Extraction source: <span class="text-neutral-300">{{ data.extraction_method }}</span>
        </div>
        <div>
          Audit Model Confidence: <span class="text-emerald-400 font-medium">{{ Math.round(data.confidence_score * 100) }}%</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
@media (prefers-reduced-motion: reduce) {
  .financial-table-extractor,
  .financial-table-extractor * {
    transition: none !important;
    animation: none !important;
  }
}
</style>
