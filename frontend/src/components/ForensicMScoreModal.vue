<script setup>
import { ref, reactive, watch } from 'vue'
import { 
  Calculator, 
  FileSearch, 
  AlertTriangle, 
  ShieldAlert, 
  CheckCircle2, 
  X, 
  Loader2, 
  HelpCircle,
  TrendingDown,
  TrendingUp,
  Sparkles
} from 'lucide-vue-next'
import { formatEnum } from '../utils/ffi.js'

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false
  },
  initialTab: {
    type: String,
    default: 'mscore'
  }
})

const emit = defineEmits(['close'])

const activeTab = ref('mscore') // 'mscore' | 'footnotes'

watch(() => props.isOpen, (open) => {
  if (open) activeTab.value = props.initialTab
}, { immediate: true })

// --- Beneish M-Score State ---
const beneishForm = reactive({
  sales_t: 1000.0,
  sales_t_prev: 950.0,
  cogs_t: 600.0,
  cogs_t_prev: 575.0,
  receivables_t: 100.0,
  receivables_t_prev: 105.0,
  current_assets_t: 400.0,
  current_assets_t_prev: 380.0,
  ppe_t: 500.0,
  ppe_t_prev: 480.0,
  total_assets_t: 1200.0,
  total_assets_t_prev: 1150.0,
  depreciation_t: 50.0,
  depreciation_t_prev: 48.0,
  sga_t: 150.0,
  sga_t_prev: 145.0,
  long_term_debt_t: 200.0,
  long_term_debt_t_prev: 220.0,
  net_income_t: 120.0,
  operating_cash_flow_t: 160.0,
})

const isCalculating = ref(false)
const mScoreResult = ref(null)
const mScoreError = ref('')

const presets = {
  clean: {
    label: 'Clean Quality (Normal)',
    data: {
      sales_t: 1000.0,
      sales_t_prev: 950.0,
      cogs_t: 600.0,
      cogs_t_prev: 575.0,
      receivables_t: 100.0,
      receivables_t_prev: 105.0,
      current_assets_t: 400.0,
      current_assets_t_prev: 380.0,
      ppe_t: 500.0,
      ppe_t_prev: 480.0,
      total_assets_t: 1200.0,
      total_assets_t_prev: 1150.0,
      depreciation_t: 50.0,
      depreciation_t_prev: 48.0,
      sga_t: 150.0,
      sga_t_prev: 145.0,
      long_term_debt_t: 200.0,
      long_term_debt_t_prev: 220.0,
      net_income_t: 120.0,
      operating_cash_flow_t: 160.0,
    }
  },
  manipulator: {
    label: 'Aggressive / Manipulator Profile',
    data: {
      sales_t: 2500.0,
      sales_t_prev: 1500.0,
      cogs_t: 1800.0,
      cogs_t_prev: 900.0,
      receivables_t: 850.0,
      receivables_t_prev: 200.0,
      current_assets_t: 1200.0,
      current_assets_t_prev: 600.0,
      ppe_t: 600.0,
      ppe_t_prev: 500.0,
      total_assets_t: 3200.0,
      total_assets_t_prev: 1600.0,
      depreciation_t: 20.0,
      depreciation_t_prev: 40.0,
      sga_t: 300.0,
      sga_t_prev: 180.0,
      long_term_debt_t: 1400.0,
      long_term_debt_t_prev: 400.0,
      net_income_t: 350.0,
      operating_cash_flow_t: -120.0,
    }
  }
}

const applyPreset = (key) => {
  Object.assign(beneishForm, presets[key].data)
  calculateMScore()
}

const calculateMScore = async () => {
  isCalculating.value = true
  mScoreError.value = ''
  try {
    const res = await fetch('/api/forensics/mscore', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(beneishForm)
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      throw new Error(err.detail || `Server returned ${res.status}`)
    }
    mScoreResult.value = await res.json()
  } catch (err) {
    mScoreError.value = err.message
  } finally {
    isCalculating.value = false
  }
}

// --- Footnote Scanner State ---
const footnoteText = ref('')
const isScanningFootnotes = ref(false)
const footnoteResult = ref(null)
const footnoteError = ref('')

const footnoteSamples = {
  svb: `Note 7. Held-to-Maturity Securities & Capital Disclosures
The Company holds substantial residential mortgage-backed securities classified as held-to-maturity. 
Due to rapid interest rate increases, the gross unrealized losses on held-to-maturity investment securities reached $1.9 billion. 
Fair value was significantly less than amortized cost, resulting in severe accumulated other comprehensive loss of $2.1 billion.
Furthermore, a single customer sector accounted for approximately 35% of total deposit funding.`,
  controls: `Item 9A. Controls and Procedures
Management assessed the effectiveness of internal control over financial reporting as of fiscal year-end.
Based on that evaluation, management concluded that internal controls were not effective due to a material weakness in internal control over financial reporting.
Separately, Note 16 discloses that the Company entered into related-party loans to executive officers amounting to $14 million. 
Additionally, the independent registered public accounting firm was dismissed following disagreements with auditors.`
}

const loadFootnoteSample = (key) => {
  footnoteText.value = footnoteSamples[key]
  scanFootnotes()
}

const scanFootnotes = async () => {
  if (!footnoteText.value.trim() || isScanningFootnotes.value) return
  isScanningFootnotes.value = true
  footnoteError.value = ''
  try {
    const res = await fetch('/api/forensics/footnotes/scan', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: footnoteText.value })
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      throw new Error(err.detail || `Server returned ${res.status}`)
    }
    footnoteResult.value = await res.json()
  } catch (err) {
    footnoteError.value = err.message
  } finally {
    isScanningFootnotes.value = false
  }
}

const indexDescriptions = {
  DSRI: { name: 'Days Sales in Receivables Index', warning: '> 1.20 suggests channel stuffing or aggressive revenue recognition' },
  GMI: { name: 'Gross Margin Index', warning: '> 1.20 signals deteriorating margins, increasing manipulation incentive' },
  AQI: { name: 'Asset Quality Index', warning: '> 1.25 indicates capitalization of operating expenses into deferred assets' },
  SGI: { name: 'Sales Growth Index', warning: 'High growth increases pressure to sustain momentum artificially' },
  DEPI: { name: 'Depreciation Index', warning: '> 1.20 indicates slower depreciation rate, artificially boosting profit' },
  SGAI: { name: 'SG&A Expenses Index', warning: '> 1.0 signals decreasing administrative sales efficiency' },
  LVGI: { name: 'Leverage Index', warning: '> 1.25 highlights increasing debt leverage and risk profile' },
  TATA: { name: 'Total Accruals to Total Assets', warning: '> 0.05 highlights positive accounting profit without real cash flow' }
}
</script>

<template>
  <div v-if="isOpen" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fade-in">
    <div class="bg-slate-900 border border-slate-700 rounded-2xl w-full max-w-5xl max-h-[92vh] flex flex-col shadow-2xl overflow-hidden">
      
      <!-- Modal Header -->
      <div class="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-900/90">
        <div class="flex items-center gap-3">
          <div class="p-2 rounded-xl bg-purple-500/10 text-purple-400 border border-purple-500/20">
            <Calculator class="w-5 h-5" />
          </div>
          <div>
            <h3 class="text-base font-semibold text-slate-100 flex items-center gap-2">
              Forensic Accounting & Beneish M-Score
              <span class="text-[10px] font-mono px-2 py-0.5 rounded-full bg-purple-500/10 text-purple-400 border border-purple-500/20">
                8-Variable Model
              </span>
            </h3>
            <p class="text-xs text-slate-400">
              Quantify earnings manipulation probability & scan buried footnote hazards
            </p>
          </div>
        </div>
        <button 
          @click="emit('close')"
          class="text-slate-400 hover:text-slate-200 p-1.5 rounded-lg hover:bg-slate-800 transition-colors cursor-pointer"
        >
          <X class="w-5 h-5" />
        </button>
      </div>

      <!-- Navigation Tabs -->
      <div class="px-6 pt-3 border-b border-slate-800 bg-slate-950/40 flex items-center gap-4">
        <button
          @click="activeTab = 'mscore'"
          class="pb-3 text-xs font-medium border-b-2 transition-colors cursor-pointer flex items-center gap-2"
          :class="activeTab === 'mscore' ? 'border-purple-400 text-purple-400' : 'border-transparent text-slate-400 hover:text-slate-200'"
        >
          <Calculator class="w-4 h-4" />
          <span>Beneish M-Score Calculator</span>
        </button>

        <button
          @click="activeTab = 'footnotes'"
          class="pb-3 text-xs font-medium border-b-2 transition-colors cursor-pointer flex items-center gap-2"
          :class="activeTab === 'footnotes' ? 'border-amber-400 text-amber-400' : 'border-transparent text-slate-400 hover:text-slate-200'"
        >
          <FileSearch class="w-4 h-4" />
          <span>Footnote Hazard Scanner</span>
          <span class="text-[10px] px-1.5 py-0.2 rounded bg-amber-500/20 text-amber-300 font-mono">5 Red Flags</span>
        </button>
      </div>

      <!-- Tab 1: Beneish M-Score -->
      <div v-if="activeTab === 'mscore'" class="flex-1 overflow-y-auto p-6 space-y-6">
        <!-- Preset Controls -->
        <div class="flex flex-wrap items-center justify-between gap-4 p-4 rounded-xl bg-slate-800/40 border border-slate-800">
          <div class="flex items-center gap-2">
            <span class="text-xs text-slate-400">Load Scenario Preset:</span>
            <button
              @click="applyPreset('clean')"
              class="px-3 py-1.5 rounded-lg bg-emerald-950/40 border border-emerald-800/60 hover:bg-emerald-900/40 text-emerald-300 text-xs font-medium transition-colors cursor-pointer"
            >
              Clean Profile (Normal)
            </button>
            <button
              @click="applyPreset('manipulator')"
              class="px-3 py-1.5 rounded-lg bg-rose-950/40 border border-rose-800/60 hover:bg-rose-900/40 text-rose-300 text-xs font-medium transition-colors cursor-pointer"
            >
              Aggressive Accruals (High Risk)
            </button>
          </div>

          <button
            @click="calculateMScore"
            :disabled="isCalculating"
            class="px-5 py-2 rounded-lg bg-purple-600 hover:bg-purple-500 disabled:opacity-50 text-white text-xs font-semibold flex items-center gap-2 transition-colors cursor-pointer"
          >
            <Loader2 v-if="isCalculating" class="w-3.5 h-3.5 animate-spin" />
            <Calculator v-else class="w-3.5 h-3.5" />
            <span>{{ isCalculating ? 'Calculating...' : 'Run M-Score Analysis' }}</span>
          </button>
        </div>

        <div v-if="mScoreError" class="p-3 bg-rose-950/30 border border-rose-800/60 rounded-lg text-rose-300 text-xs flex items-center gap-2">
          <AlertTriangle class="w-4 h-4 shrink-0" />
          <span>{{ mScoreError }}</span>
        </div>

        <!-- M-Score Result Dashboard Banner -->
        <div v-if="mScoreResult" class="space-y-4">
          <div 
            class="p-5 rounded-2xl border flex flex-wrap items-center justify-between gap-6"
            :class="mScoreResult.is_manipulator_probable 
              ? 'bg-rose-950/20 border-rose-800/60' 
              : 'bg-emerald-950/20 border-emerald-800/60'"
          >
            <div class="space-y-1">
              <div class="text-xs font-medium text-slate-400">Beneish M-Score (Threshold: -1.78)</div>
              <div class="flex items-baseline gap-3">
                <span 
                  class="text-4xl font-extrabold tabular-nums"
                  :class="mScoreResult.is_manipulator_probable ? 'text-rose-400' : 'text-emerald-400'"
                >
                  {{ mScoreResult.m_score }}
                </span>
                <span 
                  class="px-2.5 py-0.5 rounded-md text-xs font-medium border"
                  :class="mScoreResult.is_manipulator_probable 
                    ? 'bg-rose-500/10 text-rose-300 border-rose-500/30' 
                    : 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30'"
                >
                  {{ formatEnum(mScoreResult.risk_level) }}
                </span>
              </div>
              <p class="text-xs text-slate-300 pt-1 max-w-xl leading-relaxed">
                {{ mScoreResult.interpretation }}
              </p>
            </div>

            <div class="text-right space-y-1 bg-slate-900/60 p-3.5 rounded-xl border border-slate-800">
              <div class="text-[11px] text-slate-400">Manipulation probability</div>
              <div 
                class="text-xl font-bold tabular-nums"
                :class="mScoreResult.is_manipulator_probable ? 'text-rose-400' : 'text-emerald-400'"
              >
                {{ mScoreResult.is_manipulator_probable ? 'High (>75%)' : 'Low (<5%)' }}
              </div>
              <div class="text-[10px] text-slate-500">Benchmark: M > -1.78 flags restatements</div>
            </div>
          </div>

          <!-- Flagged Red Flags Alert Box -->
          <div v-if="mScoreResult.flagged_indices?.length > 0" class="p-4 rounded-xl bg-rose-950/30 border border-rose-800/50 space-y-2">
            <div class="text-xs font-semibold text-rose-400 flex items-center gap-1.5">
              <ShieldAlert class="w-4 h-4 shrink-0" />
              <span>Flagged accounting anomalies ({{ mScoreResult.flagged_indices.length }})</span>
            </div>
            <ul class="space-y-1.5 pl-5 list-disc text-xs text-rose-200">
              <li v-for="(flag, idx) in mScoreResult.flagged_indices" :key="idx" class="leading-relaxed">
                {{ flag }}
              </li>
            </ul>
          </div>

          <!-- 8 Indices Breakdown Cards -->
          <div class="space-y-2">
            <h4 class="text-xs font-semibold text-slate-300">
              8 Beneish forensic indices
            </h4>
            <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
              <div 
                v-for="(val, code) in mScoreResult.indices" 
                :key="code"
                class="p-3 rounded-xl bg-slate-800/50 border border-slate-700/60 space-y-1.5"
              >
                <div class="flex items-center justify-between">
                  <span class="text-xs font-bold text-slate-200 font-mono">{{ code }}</span>
                  <span class="text-xs font-bold tabular-nums text-purple-400">{{ val }}</span>
                </div>
                <div class="text-[10px] text-slate-400 font-medium leading-tight">
                  {{ indexDescriptions[code]?.name }}
                </div>
                <div class="text-[9px] text-slate-500 leading-tight pt-0.5">
                  {{ indexDescriptions[code]?.warning }}
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Inputs Grid -->
        <div class="space-y-3 pt-2">
          <div class="text-xs font-semibold text-slate-300 flex items-center gap-2">
            <span>Input financial statements ($ in millions)</span>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <!-- Period t (Current) -->
            <div class="p-4 rounded-xl bg-slate-800/30 border border-slate-800 space-y-3">
              <div class="text-xs font-semibold text-purple-400 border-b border-slate-800 pb-1.5">
                Current Period (Year t)
              </div>
              <div class="grid grid-cols-2 gap-2.5 text-xs">
                <div>
                  <label class="block text-[11px] text-slate-400 mb-1">Revenues ($)</label>
                  <input v-model.number="beneishForm.sales_t" type="number" step="any" class="w-full bg-slate-800 border border-slate-700 rounded px-2.5 py-1 text-slate-200 font-mono" />
                </div>
                <div>
                  <label class="block text-[11px] text-slate-400 mb-1">COGS ($)</label>
                  <input v-model.number="beneishForm.cogs_t" type="number" step="any" class="w-full bg-slate-800 border border-slate-700 rounded px-2.5 py-1 text-slate-200 font-mono" />
                </div>
                <div>
                  <label class="block text-[11px] text-slate-400 mb-1">Accounts Receivable ($)</label>
                  <input v-model.number="beneishForm.receivables_t" type="number" step="any" class="w-full bg-slate-800 border border-slate-700 rounded px-2.5 py-1 text-slate-200 font-mono" />
                </div>
                <div>
                  <label class="block text-[11px] text-slate-400 mb-1">Current Assets ($)</label>
                  <input v-model.number="beneishForm.current_assets_t" type="number" step="any" class="w-full bg-slate-800 border border-slate-700 rounded px-2.5 py-1 text-slate-200 font-mono" />
                </div>
                <div>
                  <label class="block text-[11px] text-slate-400 mb-1">Net PP&E ($)</label>
                  <input v-model.number="beneishForm.ppe_t" type="number" step="any" class="w-full bg-slate-800 border border-slate-700 rounded px-2.5 py-1 text-slate-200 font-mono" />
                </div>
                <div>
                  <label class="block text-[11px] text-slate-400 mb-1">Total Assets ($)</label>
                  <input v-model.number="beneishForm.total_assets_t" type="number" step="any" class="w-full bg-slate-800 border border-slate-700 rounded px-2.5 py-1 text-slate-200 font-mono" />
                </div>
                <div>
                  <label class="block text-[11px] text-slate-400 mb-1">Depreciation Expense ($)</label>
                  <input v-model.number="beneishForm.depreciation_t" type="number" step="any" class="w-full bg-slate-800 border border-slate-700 rounded px-2.5 py-1 text-slate-200 font-mono" />
                </div>
                <div>
                  <label class="block text-[11px] text-slate-400 mb-1">SG&A Expense ($)</label>
                  <input v-model.number="beneishForm.sga_t" type="number" step="any" class="w-full bg-slate-800 border border-slate-700 rounded px-2.5 py-1 text-slate-200 font-mono" />
                </div>
                <div>
                  <label class="block text-[11px] text-slate-400 mb-1">Long-term Debt ($)</label>
                  <input v-model.number="beneishForm.long_term_debt_t" type="number" step="any" class="w-full bg-slate-800 border border-slate-700 rounded px-2.5 py-1 text-slate-200 font-mono" />
                </div>
                <div>
                  <label class="block text-[11px] text-slate-400 mb-1">Net Income ($)</label>
                  <input v-model.number="beneishForm.net_income_t" type="number" step="any" class="w-full bg-slate-800 border border-slate-700 rounded px-2.5 py-1 text-slate-200 font-mono" />
                </div>
                <div class="col-span-2">
                  <label class="block text-[11px] text-slate-400 mb-1">Operating Cash Flow ($)</label>
                  <input v-model.number="beneishForm.operating_cash_flow_t" type="number" step="any" class="w-full bg-slate-800 border border-slate-700 rounded px-2.5 py-1 text-slate-200 font-mono" />
                </div>
              </div>
            </div>

            <!-- Period t-1 (Prior) -->
            <div class="p-4 rounded-xl bg-slate-800/30 border border-slate-800 space-y-3">
              <div class="text-xs font-semibold text-slate-400 border-b border-slate-800 pb-1.5">
                Prior Period (Year t-1)
              </div>
              <div class="grid grid-cols-2 gap-2.5 text-xs">
                <div>
                  <label class="block text-[11px] text-slate-400 mb-1">Prior Revenues ($)</label>
                  <input v-model.number="beneishForm.sales_t_prev" type="number" step="any" class="w-full bg-slate-800 border border-slate-700 rounded px-2.5 py-1 text-slate-200 font-mono" />
                </div>
                <div>
                  <label class="block text-[11px] text-slate-400 mb-1">Prior COGS ($)</label>
                  <input v-model.number="beneishForm.cogs_t_prev" type="number" step="any" class="w-full bg-slate-800 border border-slate-700 rounded px-2.5 py-1 text-slate-200 font-mono" />
                </div>
                <div>
                  <label class="block text-[11px] text-slate-400 mb-1">Prior Receivables ($)</label>
                  <input v-model.number="beneishForm.receivables_t_prev" type="number" step="any" class="w-full bg-slate-800 border border-slate-700 rounded px-2.5 py-1 text-slate-200 font-mono" />
                </div>
                <div>
                  <label class="block text-[11px] text-slate-400 mb-1">Prior Current Assets ($)</label>
                  <input v-model.number="beneishForm.current_assets_t_prev" type="number" step="any" class="w-full bg-slate-800 border border-slate-700 rounded px-2.5 py-1 text-slate-200 font-mono" />
                </div>
                <div>
                  <label class="block text-[11px] text-slate-400 mb-1">Prior Net PP&E ($)</label>
                  <input v-model.number="beneishForm.ppe_t_prev" type="number" step="any" class="w-full bg-slate-800 border border-slate-700 rounded px-2.5 py-1 text-slate-200 font-mono" />
                </div>
                <div>
                  <label class="block text-[11px] text-slate-400 mb-1">Prior Total Assets ($)</label>
                  <input v-model.number="beneishForm.total_assets_t_prev" type="number" step="any" class="w-full bg-slate-800 border border-slate-700 rounded px-2.5 py-1 text-slate-200 font-mono" />
                </div>
                <div>
                  <label class="block text-[11px] text-slate-400 mb-1">Prior Depreciation ($)</label>
                  <input v-model.number="beneishForm.depreciation_t_prev" type="number" step="any" class="w-full bg-slate-800 border border-slate-700 rounded px-2.5 py-1 text-slate-200 font-mono" />
                </div>
                <div>
                  <label class="block text-[11px] text-slate-400 mb-1">Prior SG&A Expense ($)</label>
                  <input v-model.number="beneishForm.sga_t_prev" type="number" step="any" class="w-full bg-slate-800 border border-slate-700 rounded px-2.5 py-1 text-slate-200 font-mono" />
                </div>
                <div class="col-span-2">
                  <label class="block text-[11px] text-slate-400 mb-1">Prior Long-term Debt ($)</label>
                  <input v-model.number="beneishForm.long_term_debt_t_prev" type="number" step="any" class="w-full bg-slate-800 border border-slate-700 rounded px-2.5 py-1 text-slate-200 font-mono" />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Tab 2: Footnote Hazards Scanner -->
      <div v-if="activeTab === 'footnotes'" class="flex-1 overflow-y-auto p-6 space-y-6">
        <div class="space-y-3">
          <div class="flex flex-wrap items-center justify-between gap-3">
            <span class="text-xs text-slate-400">Load Test Disclosures:</span>
            <div class="flex items-center gap-2">
              <button
                @click="loadFootnoteSample('svb')"
                class="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs transition-colors cursor-pointer"
              >
                SVB Held-to-Maturity Losses
              </button>
              <button
                @click="loadFootnoteSample('controls')"
                class="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs transition-colors cursor-pointer"
              >
                Auditor Material Weakness & Insider Loans
              </button>
            </div>
          </div>

          <textarea
            v-model="footnoteText"
            rows="5"
            placeholder="Paste raw 10-K / 10-Q footnote disclosures, auditor reports, or commitment notes here..."
            class="w-full bg-slate-800/80 border border-slate-700 rounded-xl p-3 text-xs text-slate-200 font-mono leading-relaxed focus:outline-none focus:border-amber-500"
          ></textarea>

          <div class="flex items-center justify-between">
            <span class="text-[11px] text-slate-500">
              Scans for Related-Party, Customer Concentration (>10%), HTM Losses, Goodwill Impairment, and SOX 404 Weakness
            </span>
            <button
              @click="scanFootnotes"
              :disabled="isScanningFootnotes || !footnoteText.trim()"
              class="px-5 py-2 rounded-lg bg-amber-500 hover:bg-amber-400 disabled:opacity-50 text-slate-950 text-xs font-semibold flex items-center gap-2 transition-colors cursor-pointer"
            >
              <Loader2 v-if="isScanningFootnotes" class="w-3.5 h-3.5 animate-spin" />
              <FileSearch v-else class="w-3.5 h-3.5" />
              <span>{{ isScanningFootnotes ? 'Scanning...' : 'Scan Footnotes' }}</span>
            </button>
          </div>
        </div>

        <div v-if="footnoteError" class="p-3 bg-rose-950/30 border border-rose-800/60 rounded-lg text-rose-300 text-xs flex items-center gap-2">
          <AlertTriangle class="w-4 h-4 shrink-0" />
          <span>{{ footnoteError }}</span>
        </div>

        <!-- Footnote Scan Results -->
        <div v-if="footnoteResult" class="space-y-4">
          <!-- Summary Banner -->
          <div class="p-4 rounded-xl bg-slate-800/60 border border-slate-700 flex items-center justify-between">
            <div class="space-y-0.5">
              <div class="text-xs font-semibold text-slate-200">Scan Results Summary</div>
              <p class="text-xs text-slate-400">{{ footnoteResult.summary }}</p>
            </div>
            <div class="flex items-center gap-3">
              <div class="text-center px-3 py-1 rounded bg-rose-950/40 border border-rose-800 text-rose-300 text-xs font-mono font-bold">
                {{ footnoteResult.high_risk_count }} High Risk
              </div>
              <div class="text-center px-3 py-1 rounded bg-amber-950/40 border border-amber-800 text-amber-300 text-xs font-mono font-bold">
                {{ footnoteResult.medium_risk_count }} Moderate
              </div>
            </div>
          </div>

          <!-- Finding Cards -->
          <div v-if="footnoteResult.findings?.length > 0" class="space-y-3">
            <div 
              v-for="(f, idx) in footnoteResult.findings" 
              :key="idx"
              class="p-4 rounded-xl border space-y-2.5"
              :class="f.severity === 'HIGH' ? 'bg-rose-950/20 border-rose-800/50' : 'bg-amber-950/20 border-amber-800/50'"
            >
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-2">
                  <span 
                    class="px-2 py-0.5 rounded text-[10px] font-medium"
                    :class="f.severity === 'HIGH' ? 'bg-rose-500/20 text-rose-300' : 'bg-amber-500/20 text-amber-300'"
                  >
                    {{ formatEnum(f.severity) }}
                  </span>
                  <span class="text-xs font-bold text-slate-200">{{ f.title }}</span>
                </div>
                <span class="text-[10px] text-slate-500 font-mono">Matched: "{{ f.matched_phrase }}"</span>
              </div>

              <div class="p-2.5 rounded-lg bg-slate-900/80 border border-slate-800 text-xs text-slate-300 font-mono leading-relaxed">
                {{ f.excerpt }}
              </div>

              <p class="text-xs text-slate-400 leading-relaxed italic">
                {{ f.explanation }}
              </p>
            </div>
          </div>

          <div v-else class="text-center py-8 text-slate-500 space-y-2">
            <CheckCircle2 class="w-8 h-8 mx-auto text-emerald-400 opacity-80" />
            <p class="text-xs">No buried footnote hazards detected in the scanned text.</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
