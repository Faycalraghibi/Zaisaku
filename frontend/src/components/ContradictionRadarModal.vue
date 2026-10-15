<script setup>
import { ref } from 'vue'
import {
  Radio,
  FileText,
  Mic,
  AlertTriangle,
  ShieldAlert,
  X,
  Loader2,
  CheckCircle2,
  Sparkles,
  TrendingDown,
  TrendingUp
} from 'lucide-vue-next'

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['close'])

const ticker = ref('NVDA')
const useLlm = ref(false)
const isLoading = ref(false)
const errorMsg = ref('')
const radarResult = ref(null)

const callText = ref('')
const filingText = ref('')

const presets = {
  demand: {
    label: 'Tech Co Demand Contradiction',
    ticker: 'TECH',
    call: `CEO Prepared Remarks:
We are thrilled with our record-breaking momentum this quarter. We are seeing unprecedented demand and record backlog growth across our accelerated computing architecture. Customer commitments have never been higher and visibility into our future pipeline is exceptionally strong.`,
    filing: `Item 7. Management's Discussion and Analysis
During the fiscal quarter ended July 31, the Company observed lengthening sales cycles, customer pushouts, and order cancellations across several key enterprise customers. As a result, order visibility has become increasingly constrained, which may adversely affect future bookings.`
  },
  margin: {
    label: 'Retail / Hardware Margin Squeeze',
    ticker: 'CONS',
    call: `CFO Prepared Remarks:
Our pricing power remains strong and intact despite general inflation. We continue to benefit from disciplined pricing strategies, which enable sustainable gross margin expansion across our premium product lines.`,
    filing: `Item 7. Management's Discussion and Analysis
Gross margins compressed by 280 basis points during the quarter. The decline was primarily driven by aggressive promotional discounting and customer pricing concessions necessitated by heightened competitive pressure and cost inflation.`
  },
  supply: {
    label: 'Hardware Foundry Bottlenecks',
    ticker: 'SEMI',
    call: `COO Prepared Remarks:
Our manufacturing execution was superb. Our supply chain bottlenecks are fully resolved and foundry allocations have normalized across all advanced fabrication nodes.`,
    filing: `Item 1A. Risk Factors
The Company continues to experience severe supply chain disruptions and critical component shortages from our sole-source suppliers. Any prolonged manufacturing bottleneck will materially harm our delivery schedules.`
  }
}

const applyPreset = (key) => {
  const p = presets[key]
  ticker.value = p.ticker
  callText.value = p.call
  filingText.value = p.filing
  scanContradictions()
}

const scanContradictions = async () => {
  if (!callText.value.trim() || !filingText.value.trim() || isLoading.value) return
  isLoading.value = true
  errorMsg.value = ''
  radarResult.value = null

  try {
    const res = await fetch('/api/forensics/contradictions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        ticker: ticker.value.trim().toUpperCase() || 'CUSTOM',
        call_text: callText.value,
        filing_text: filingText.value,
        use_llm: useLlm.value
      })
    })

    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      throw new Error(err.detail || `Server returned ${res.status}`)
    }

    radarResult.value = await res.json()
  } catch (err) {
    errorMsg.value = err.message
  } finally {
    isLoading.value = false
  }
}

const severityColor = (severity) => {
  switch (severity?.toUpperCase()) {
    case 'CRITICAL': return 'text-rose-400 bg-rose-950/40 border-rose-800'
    case 'HIGH': return 'text-amber-400 bg-amber-950/40 border-amber-800'
    case 'MODERATE': return 'text-yellow-400 bg-yellow-950/40 border-yellow-800'
    default: return 'text-emerald-400 bg-emerald-950/40 border-emerald-800'
  }
}
</script>

<template>
  <div v-if="isOpen" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fade-in">
    <div class="bg-slate-900 border border-slate-700 rounded-2xl w-full max-w-5xl max-h-[92vh] flex flex-col shadow-2xl overflow-hidden">
      
      <!-- Header -->
      <div class="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-900/90">
        <div class="flex items-center gap-3">
          <div class="p-2 rounded-xl bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
            <Radio class="w-5 h-5" />
          </div>
          <div>
            <h3 class="text-base font-semibold text-slate-100 flex items-center gap-2">
              Earnings Call vs. 10-Q Contradiction Radar
              <span class="text-[10px] font-mono px-2 py-0.5 rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                Spoken Pitch vs Written Reality
              </span>
            </h3>
            <p class="text-xs text-slate-400">
              Catch discrepancies where executives hype guidance while regulatory filings warn of headwinds
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

          <div class="flex items-center gap-4">
            <div class="flex items-center gap-2">
              <input 
                id="useLlmRadar" 
                v-model="useLlm" 
                type="checkbox" 
                class="rounded bg-slate-800 border-slate-700 text-cyan-500 focus:ring-0 cursor-pointer"
              />
              <label for="useLlmRadar" class="text-xs text-slate-300 cursor-pointer select-none">
                AI Deep Semantic Verification
              </label>
            </div>

            <button
              @click="scanContradictions"
              :disabled="isLoading || !callText.trim() || !filingText.trim()"
              class="px-5 py-2 rounded-lg bg-cyan-500 hover:bg-cyan-400 disabled:opacity-50 text-slate-950 text-xs font-semibold flex items-center gap-2 transition-colors cursor-pointer"
            >
              <Loader2 v-if="isLoading" class="w-3.5 h-3.5 animate-spin" />
              <Radio v-else class="w-3.5 h-3.5" />
              <span>{{ isLoading ? 'Analyzing Discrepancies...' : 'Scan Radar' }}</span>
            </button>
          </div>
        </div>

        <!-- Input Split Textareas -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div class="space-y-1.5">
            <div class="flex items-center justify-between text-xs">
              <span class="font-semibold text-cyan-400 flex items-center gap-1.5">
                <Mic class="w-3.5 h-3.5" />
                Spoken Earnings Call / Executive Pitch
              </span>
              <span class="text-[10px] text-slate-500">Prepared remarks / Q&A</span>
            </div>
            <textarea
              v-model="callText"
              rows="4"
              placeholder="Paste CEO/CFO statements from the earnings call transcript here..."
              class="w-full bg-slate-800/80 border border-slate-700 rounded-xl p-3 text-xs text-slate-200 font-mono leading-relaxed focus:outline-none focus:border-cyan-500"
            ></textarea>
          </div>

          <div class="space-y-1.5">
            <div class="flex items-center justify-between text-xs">
              <span class="font-semibold text-amber-400 flex items-center gap-1.5">
                <FileText class="w-3.5 h-3.5" />
                Written SEC 10-Q Filing Disclosures
              </span>
              <span class="text-[10px] text-slate-500">Item 7 MD&A / Item 1A Risk Factors</span>
            </div>
            <textarea
              v-model="filingText"
              rows="4"
              placeholder="Paste official 10-Q or 10-K disclosures, notes, or risk factors here..."
              class="w-full bg-slate-800/80 border border-slate-700 rounded-xl p-3 text-xs text-slate-200 font-mono leading-relaxed focus:outline-none focus:border-amber-500"
            ></textarea>
          </div>
        </div>

        <div v-if="errorMsg" class="p-3 bg-rose-950/30 border border-rose-800/60 rounded-lg text-rose-300 text-xs flex items-center gap-2">
          <AlertTriangle class="w-4 h-4 shrink-0" />
          <span>{{ errorMsg }}</span>
        </div>
      </div>

      <!-- Results Body -->
      <div class="flex-1 overflow-y-auto p-6 space-y-6">
        <div v-if="!radarResult && !isLoading" class="text-center py-12 text-slate-500 space-y-2">
          <Radio class="w-10 h-10 mx-auto opacity-30" />
          <p class="text-sm">Select a scenario preset above or paste custom texts to run Contradiction Radar.</p>
        </div>

        <div v-if="isLoading" class="text-center py-16 space-y-3">
          <Loader2 class="w-8 h-8 text-cyan-400 animate-spin mx-auto" />
          <p class="text-sm text-slate-300 font-medium">Measuring tone decoupling & parsing semantic contradictions...</p>
          <p class="text-xs text-slate-500">Cross-checking executive guidance claims against regulatory SEC filings</p>
        </div>

        <div v-if="radarResult" class="space-y-6">
          <!-- Overview Banner -->
          <div class="p-5 rounded-2xl bg-slate-800/60 border border-slate-700 flex flex-wrap items-center justify-between gap-6">
            <div class="space-y-1">
              <div class="text-xs text-slate-400">Tone Decoupling Metric</div>
              <div class="flex items-baseline gap-3">
                <span class="text-3xl font-extrabold tabular-nums text-cyan-400">
                  {{ radarResult.tone_divergence_score }}%
                </span>
                <span 
                  class="px-2.5 py-1 rounded-md text-xs font-medium border"
                  :class="severityColor(radarResult.divergence_severity)"
                >
                  {{ radarResult.divergence_severity.toLowerCase() }} decoupling
                </span>
              </div>
              <p class="text-xs text-slate-300 pt-1 max-w-xl leading-relaxed">
                {{ radarResult.executive_summary }}
              </p>
            </div>

            <!-- Sentiment Polarity Chips -->
            <div class="flex items-center gap-4 bg-slate-900/60 p-3.5 rounded-xl border border-slate-800">
              <div class="text-center">
                <div class="text-xs text-slate-400 flex items-center gap-1 justify-center">
                  <Mic class="w-3 h-3 text-cyan-400" /> Call tone
                </div>
                <div class="text-xs font-semibold text-cyan-300 mt-1 capitalize">
                  {{ radarResult.call_sentiment.toLowerCase() }}
                </div>
              </div>

              <div class="h-8 w-px bg-slate-800"></div>

              <div class="text-center">
                <div class="text-xs text-slate-400 flex items-center gap-1 justify-center">
                  <FileText class="w-3 h-3 text-amber-400" /> 10-Q tone
                </div>
                <div class="text-xs font-semibold text-amber-300 mt-1 capitalize">
                  {{ radarResult.filing_sentiment.toLowerCase() }}
                </div>
              </div>
            </div>
          </div>

          <!-- Contradictions Cards List -->
          <div v-if="radarResult.contradictions?.length > 0" class="space-y-4">
            <div class="text-xs font-semibold text-slate-300 flex items-center gap-2">
              <ShieldAlert class="w-4 h-4 text-rose-400" />
              <span>Flagged guidance and operational contradictions ({{ radarResult.contradictions.length }})</span>
            </div>

            <div 
              v-for="(c, idx) in radarResult.contradictions" 
              :key="idx"
              class="p-5 rounded-2xl border space-y-4 bg-slate-800/40 border-slate-700/80"
            >
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-2.5">
                  <span 
                    class="px-2 py-0.5 rounded text-xs font-medium border"
                    :class="severityColor(c.severity)"
                  >
                    {{ c.severity.toLowerCase() }}
                  </span>
                  <h4 class="text-sm font-semibold text-slate-100">{{ c.topic }}</h4>
                </div>
              </div>

              <!-- Side-by-side Evidence -->
              <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div class="p-3.5 rounded-xl bg-cyan-950/20 border border-cyan-800/40 space-y-1.5">
                  <div class="text-[11px] font-semibold text-cyan-400 flex items-center gap-1.5">
                    <Mic class="w-3.5 h-3.5" />
                    Spoken Management Pitch (Earnings Call)
                  </div>
                  <div class="text-xs text-cyan-200/90 font-mono leading-relaxed">
                    {{ c.call_statement }}
                  </div>
                </div>

                <div class="p-3.5 rounded-xl bg-amber-950/20 border border-amber-800/40 space-y-1.5">
                  <div class="text-[11px] font-semibold text-amber-400 flex items-center gap-1.5">
                    <FileText class="w-3.5 h-3.5" />
                    Regulatory SEC Filing (10-Q / 10-K)
                  </div>
                  <div class="text-xs text-amber-200/90 font-mono leading-relaxed">
                    {{ c.filing_statement }}
                  </div>
                </div>
              </div>

              <!-- Forensic Takeaway -->
              <div class="p-3 rounded-xl bg-slate-900/80 border border-slate-800 text-xs text-slate-300 leading-relaxed">
                <span class="font-semibold text-rose-400">Forensic Divergence Takeaway:</span>
                {{ c.divergence_analysis }}
              </div>
            </div>
          </div>

          <div v-else class="text-center py-10 text-slate-500 space-y-2">
            <CheckCircle2 class="w-9 h-9 mx-auto text-emerald-400 opacity-80" />
            <p class="text-xs">No direct guidance or operational contradictions detected between call and filing.</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
