<script setup>
import { ref, reactive, watch } from 'vue'
import {
  ShieldAlert,
  GitCompare,
  Calculator,
  Radio,
  AlertTriangle,
  CheckCircle2,
  X,
  Loader2,
  ArrowRight,
  TrendingDown,
  TrendingUp,
  Sliders,
  ExternalLink,
  Download
} from 'lucide-vue-next'

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['close', 'open-diff', 'open-mscore', 'open-radar'])

const form = reactive({
  ticker: 'AAPL',
  company_name: 'Apple Inc.',
  language_drift_score: 8.5,
  beneish_m_score: -2.85,
  footnote_hazards_count: 0,
  call_contradictions_score: 11.0,
  contradiction_count: 0,
})

const isLoading = ref(false)
const errorMsg = ref('')
const scorecardResult = ref(null)

watch(() => props.isOpen, (newVal) => {
  if (newVal && !scorecardResult.value) {
    calculateScorecard()
  }
})

const presets = {
  clean: {
    label: 'Clean Blue Chip (Normal)',
    ticker: 'AAPL',
    name: 'Apple Inc.',
    drift: 8.5,
    mscore: -2.85,
    footnotes: 0,
    divergence: 11.0,
    contradictions: 0
  },
  watchlist: {
    label: 'Watchlist Anomaly',
    ticker: 'WCH',
    name: 'Watchlist Tech Corp',
    drift: 28.5,
    mscore: -1.95,
    footnotes: 1,
    divergence: 32.0,
    contradictions: 1
  },
  critical: {
    label: 'Critical Fraud / Restatement Risk',
    ticker: 'FRAUD',
    name: 'Aggressive Capital Corp',
    drift: 72.0,
    mscore: -1.22,
    footnotes: 3,
    divergence: 65.0,
    contradictions: 3
  }
}

const applyPreset = (key) => {
  const p = presets[key]
  form.ticker = p.ticker
  form.company_name = p.name
  form.language_drift_score = p.drift
  form.beneish_m_score = p.mscore
  form.footnote_hazards_count = p.footnotes
  form.call_contradictions_score = p.divergence
  form.contradiction_count = p.contradictions
  calculateScorecard()
}

const calculateScorecard = async () => {
  isLoading.value = true
  errorMsg.value = ''
  try {
    const res = await fetch('/api/forensics/scorecard', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(form)
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      throw new Error(err.detail || `Server returned ${res.status}`)
    }
    scorecardResult.value = await res.json()
  } catch (err) {
    errorMsg.value = err.message
  } finally {
    isLoading.value = false
  }
}

const isExporting = ref(false)

const exportMemo = async () => {
  if (!scorecardResult.value) return
  isExporting.value = true
  try {
    const payload = {
      ticker: form.ticker,
      company_name: form.company_name,
      scorecard: scorecardResult.value,
    }
    const res = await fetch('/api/forensics/report/download', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })
    if (!res.ok) {
      throw new Error('Failed to generate report export')
    }
    const blob = await res.blob()
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `forensic_due_diligence_${(form.ticker || 'company').toLowerCase()}.md`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(url)
  } catch (err) {
    errorMsg.value = err.message
  } finally {
    isExporting.value = false
  }
}

const riskColor = (level) => {
  switch (level?.toUpperCase()) {
    case 'CRITICAL_ALERT': return 'text-rose-400 bg-rose-950/40 border-rose-800'
    case 'HIGH_RISK': return 'text-amber-400 bg-amber-950/40 border-amber-800'
    case 'WATCHLIST': return 'text-yellow-400 bg-yellow-950/40 border-yellow-800'
    default: return 'text-emerald-400 bg-emerald-950/40 border-emerald-800'
  }
}

const pillarStatusColor = (status) => {
  switch (status?.toUpperCase()) {
    case 'CRITICAL': return 'text-rose-400 bg-rose-500/20'
    case 'ELEVATED': return 'text-amber-400 bg-amber-500/20'
    default: return 'text-emerald-400 bg-emerald-500/20'
  }
}
</script>

<template>
  <div v-if="isOpen" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fade-in">
    <div class="bg-slate-900 border border-slate-700 rounded-2xl w-full max-w-5xl max-h-[92vh] flex flex-col shadow-2xl overflow-hidden">
      
      <!-- Header -->
      <div class="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-900/90">
        <div class="flex items-center gap-3">
          <div class="p-2 rounded-xl bg-rose-500/10 text-rose-400 border border-rose-500/20">
            <ShieldAlert class="w-5 h-5" />
          </div>
          <div>
            <h3 class="text-base font-semibold text-slate-100 flex items-center gap-2">
              Unified Forensic Risk Scorecard
              <span class="text-[10px] font-mono px-2 py-0.5 rounded-full bg-rose-500/10 text-rose-400 border border-rose-500/20">
                Composite FFI Engine
              </span>
            </h3>
            <p class="text-xs text-slate-400">
              Synthesizes Language Drift (30%), Beneish M-Score (40%), and Call Contradictions (30%) into an institutional audit
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

      <!-- Controls & Presets -->
      <div class="p-6 border-b border-slate-800 bg-slate-950/40 space-y-4 shrink-0">
        <div class="flex flex-wrap items-center justify-between gap-4">
          <div class="flex items-center gap-2">
            <span class="text-xs text-slate-400">Load Scenario Preset:</span>
            <button
              v-for="(p, key) in presets"
              :key="key"
              @click="applyPreset(key)"
              class="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs transition-colors cursor-pointer"
            >
              {{ p.label }}
            </button>
          </div>

          <div class="flex items-center gap-2">
            <button
              v-if="scorecardResult"
              @click="exportMemo"
              :disabled="isExporting || isLoading"
              class="px-3.5 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 disabled:opacity-50 text-slate-200 text-xs font-semibold flex items-center gap-1.5 transition-colors cursor-pointer"
            >
              <Loader2 v-if="isExporting" class="w-3.5 h-3.5 animate-spin text-rose-400" />
              <Download v-else class="w-3.5 h-3.5 text-rose-400" />
              <span>{{ isExporting ? 'Exporting...' : 'Export Due Diligence Memo' }}</span>
            </button>

            <button
              @click="calculateScorecard"
              :disabled="isLoading"
              class="px-5 py-2 rounded-lg bg-rose-600 hover:bg-rose-500 disabled:opacity-50 text-white text-xs font-semibold flex items-center gap-2 transition-colors cursor-pointer"
            >
              <Loader2 v-if="isLoading" class="w-3.5 h-3.5 animate-spin" />
              <Sliders v-else class="w-3.5 h-3.5" />
              <span>{{ isLoading ? 'Evaluating Audit...' : 'Recalculate Scorecard' }}</span>
            </button>
          </div>
        </div>

        <!-- Inputs Form Grid -->
        <div class="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
          <div>
            <label class="block text-[11px] text-slate-400 mb-1">Ticker / Company</label>
            <input v-model="form.ticker" type="text" class="w-full bg-slate-800 border border-slate-700 rounded px-2.5 py-1 text-slate-200 uppercase font-mono" />
          </div>

          <div>
            <label class="block text-[11px] text-slate-400 mb-1">Language Drift (%)</label>
            <input v-model.number="form.language_drift_score" type="number" step="any" class="w-full bg-slate-800 border border-slate-700 rounded px-2.5 py-1 text-slate-200 font-mono" />
          </div>

          <div>
            <label class="block text-[11px] text-slate-400 mb-1">Beneish M-Score</label>
            <input v-model.number="form.beneish_m_score" type="number" step="any" class="w-full bg-slate-800 border border-slate-700 rounded px-2.5 py-1 text-slate-200 font-mono" />
          </div>

          <div>
            <label class="block text-[11px] text-slate-400 mb-1">Footnote Hazards (Count)</label>
            <input v-model.number="form.footnote_hazards_count" type="number" min="0" class="w-full bg-slate-800 border border-slate-700 rounded px-2.5 py-1 text-slate-200 font-mono" />
          </div>

          <div>
            <label class="block text-[11px] text-slate-400 mb-1">Call Decoupling (%)</label>
            <input v-model.number="form.call_contradictions_score" type="number" step="any" class="w-full bg-slate-800 border border-slate-700 rounded px-2.5 py-1 text-slate-200 font-mono" />
          </div>

          <div>
            <label class="block text-[11px] text-slate-400 mb-1">Call Contradictions (Count)</label>
            <input v-model.number="form.contradiction_count" type="number" min="0" class="w-full bg-slate-800 border border-slate-700 rounded px-2.5 py-1 text-slate-200 font-mono" />
          </div>
        </div>

        <div v-if="errorMsg" class="p-3 bg-rose-950/30 border border-rose-800/60 rounded-lg text-rose-300 text-xs flex items-center gap-2">
          <AlertTriangle class="w-4 h-4 shrink-0" />
          <span>{{ errorMsg }}</span>
        </div>
      </div>

      <!-- Results Body -->
      <div class="flex-1 overflow-y-auto p-6 space-y-6">
        <div v-if="!scorecardResult && !isLoading" class="text-center py-12 text-slate-500 space-y-2">
          <ShieldAlert class="w-10 h-10 mx-auto opacity-30" />
          <p class="text-sm">Click 'Recalculate Scorecard' or select a preset to evaluate institutional forensic fragility.</p>
        </div>

        <div v-if="isLoading" class="text-center py-16 space-y-3">
          <Loader2 class="w-8 h-8 text-rose-400 animate-spin mx-auto" />
          <p class="text-sm text-slate-300 font-medium">Evaluating composite Forensic Fragility Index (FFI)...</p>
          <p class="text-xs text-slate-500">Cross-weighting filing modifications, accounting manipulation, and executive guidance traps</p>
        </div>

        <div v-if="scorecardResult" class="space-y-6">
          <!-- Overview Banner -->
          <div 
            class="p-5 rounded-2xl border flex flex-wrap items-center justify-between gap-6"
            :class="riskColor(scorecardResult.risk_level)"
          >
            <div class="space-y-1">
              <div class="text-xs font-medium text-slate-400">Forensic Fragility Index (0 to 100 FFI)</div>
              <div class="flex items-baseline gap-3">
                <span class="text-4xl font-extrabold font-mono text-slate-100">
                  {{ scorecardResult.composite_ffi }} <span class="text-lg font-normal text-slate-400">/ 100</span>
                </span>
                <span 
                  class="px-2.5 py-1 rounded-full text-xs font-semibold uppercase tracking-wider border"
                  :class="riskColor(scorecardResult.risk_level)"
                >
                  {{ scorecardResult.risk_level.replace(/_/g, ' ') }}
                </span>
              </div>
              <p class="text-xs text-slate-300 pt-1 max-w-xl leading-relaxed">
                {{ scorecardResult.summary }}
              </p>
            </div>

            <div class="text-right space-y-1 bg-slate-900/60 p-3.5 rounded-xl border border-slate-800">
              <div class="text-[11px] text-slate-400">Institutional Action</div>
              <div class="text-sm font-bold font-mono uppercase text-slate-100">
                {{ scorecardResult.recommendation.replace(/_/g, ' ') }}
              </div>
              <div class="text-[10px] text-slate-500">Threshold: FFI &ge; 45 warrants short/avoid</div>
            </div>
          </div>

          <!-- Red Flags Alert Box -->
          <div v-if="scorecardResult.red_flags?.length > 0" class="p-4 rounded-xl bg-rose-950/30 border border-rose-800/50 space-y-2">
            <div class="text-xs font-semibold text-rose-400 flex items-center gap-1.5">
              <ShieldAlert class="w-4 h-4 shrink-0" />
              <span>Critical Forensic Red Flags Flagged ({{ scorecardResult.red_flags.length }})</span>
            </div>
            <ul class="space-y-1 pl-5 list-disc text-xs text-rose-200">
              <li v-for="(flag, idx) in scorecardResult.red_flags" :key="idx" class="leading-relaxed">
                {{ flag }}
              </li>
            </ul>
          </div>

          <!-- 3 Pillars Grid -->
          <div class="space-y-3">
            <h4 class="text-xs font-semibold text-slate-300 uppercase tracking-wider">
              Forensic Intelligence Pillars
            </h4>

            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
              <!-- Pillar 1: Language Drift -->
              <div class="p-4 rounded-xl bg-slate-800/50 border border-slate-700/80 flex flex-col justify-between space-y-3">
                <div class="space-y-2">
                  <div class="flex items-center justify-between">
                    <div class="flex items-center gap-2">
                      <GitCompare class="w-4 h-4 text-amber-400" />
                      <span class="text-xs font-bold text-slate-200">Filing Language Drift</span>
                    </div>
                    <span 
                      class="px-2 py-0.5 rounded text-[10px] font-semibold font-mono"
                      :class="pillarStatusColor(scorecardResult.pillars.language_drift?.status)"
                    >
                      {{ scorecardResult.pillars.language_drift?.raw_score }}%
                    </span>
                  </div>
                  <div class="text-[11px] text-slate-400">Weight: 30% | Lazy Prices Alpha</div>
                  <ul class="text-xs text-slate-300 space-y-1 pl-4 list-disc">
                    <li v-for="(f, idx) in scorecardResult.pillars.language_drift?.key_findings" :key="idx">
                      {{ f }}
                    </li>
                  </ul>
                </div>

                <button
                  @click="emit('open-diff')"
                  class="w-full py-1.5 px-3 rounded-lg bg-amber-950/30 border border-amber-800/50 hover:bg-amber-900/40 text-amber-300 text-xs font-medium flex items-center justify-center gap-1.5 transition-colors cursor-pointer"
                >
                  <span>Open Diff Engine</span>
                  <ArrowRight class="w-3.5 h-3.5" />
                </button>
              </div>

              <!-- Pillar 2: Forensic Accounting -->
              <div class="p-4 rounded-xl bg-slate-800/50 border border-slate-700/80 flex flex-col justify-between space-y-3">
                <div class="space-y-2">
                  <div class="flex items-center justify-between">
                    <div class="flex items-center gap-2">
                      <Calculator class="w-4 h-4 text-purple-400" />
                      <span class="text-xs font-bold text-slate-200">Accounting & Footnotes</span>
                    </div>
                    <span 
                      class="px-2 py-0.5 rounded text-[10px] font-semibold font-mono"
                      :class="pillarStatusColor(scorecardResult.pillars.forensic_accounting?.status)"
                    >
                      {{ scorecardResult.pillars.forensic_accounting?.raw_score }} / 100
                    </span>
                  </div>
                  <div class="text-[11px] text-slate-400">Weight: 40% | Beneish Model + Footnotes</div>
                  <ul class="text-xs text-slate-300 space-y-1 pl-4 list-disc">
                    <li v-for="(f, idx) in scorecardResult.pillars.forensic_accounting?.key_findings" :key="idx">
                      {{ f }}
                    </li>
                  </ul>
                </div>

                <button
                  @click="emit('open-mscore')"
                  class="w-full py-1.5 px-3 rounded-lg bg-purple-950/30 border border-purple-800/50 hover:bg-purple-900/40 text-purple-300 text-xs font-medium flex items-center justify-center gap-1.5 transition-colors cursor-pointer"
                >
                  <span>Open M-Score Calculator</span>
                  <ArrowRight class="w-3.5 h-3.5" />
                </button>
              </div>

              <!-- Pillar 3: Call Contradictions -->
              <div class="p-4 rounded-xl bg-slate-800/50 border border-slate-700/80 flex flex-col justify-between space-y-3">
                <div class="space-y-2">
                  <div class="flex items-center justify-between">
                    <div class="flex items-center gap-2">
                      <Radio class="w-4 h-4 text-cyan-400" />
                      <span class="text-xs font-bold text-slate-200">Call vs 10-Q Radar</span>
                    </div>
                    <span 
                      class="px-2 py-0.5 rounded text-[10px] font-semibold font-mono"
                      :class="pillarStatusColor(scorecardResult.pillars.call_contradictions?.status)"
                    >
                      {{ scorecardResult.pillars.call_contradictions?.raw_score }} / 100
                    </span>
                  </div>
                  <div class="text-[11px] text-slate-400">Weight: 30% | Tone Decoupling Metric</div>
                  <ul class="text-xs text-slate-300 space-y-1 pl-4 list-disc">
                    <li v-for="(f, idx) in scorecardResult.pillars.call_contradictions?.key_findings" :key="idx">
                      {{ f }}
                    </li>
                  </ul>
                </div>

                <button
                  @click="emit('open-radar')"
                  class="w-full py-1.5 px-3 rounded-lg bg-cyan-950/30 border border-cyan-800/50 hover:bg-cyan-900/40 text-cyan-300 text-xs font-medium flex items-center justify-center gap-1.5 transition-colors cursor-pointer"
                >
                  <span>Open Contradiction Radar</span>
                  <ArrowRight class="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
