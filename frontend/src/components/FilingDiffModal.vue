<script setup>
import { ref } from 'vue'
import { GitCompare, Loader2, X, AlertTriangle, ShieldAlert, ArrowRight, CheckCircle2, ChevronRight } from 'lucide-vue-next'

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['close'])

const ticker = ref('NVDA')
const form = ref('10-K')
const useLlm = ref(true)
const isLoading = ref(false)
const errorMsg = ref('')
const diffResult = ref(null)
const activeSection = ref('')

const popularTickers = ['NVDA', 'AAPL', 'MSFT', 'TSLA', 'META', 'AMZN']

const runDiff = async () => {
  if (!ticker.value.trim() || isLoading.value) return
  isLoading.value = true
  errorMsg.value = ''
  diffResult.value = null

  try {
    const res = await fetch('/api/forensics/diff', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        ticker: ticker.value.trim().toUpperCase(),
        form: form.value,
        use_llm: useLlm.value
      })
    })

    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      throw new Error(err.detail || `Server returned ${res.status}`)
    }

    const data = await res.json()
    diffResult.value = data
    const sectionKeys = Object.keys(data.sections || {})
    if (sectionKeys.length > 0) {
      activeSection.value = sectionKeys.includes('item_1a_risk_factors') ? 'item_1a_risk_factors' : sectionKeys[0]
    }
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

const formatSectionTitle = (key) => {
  if (key === 'item_1a_risk_factors') return 'Item 1A: Risk Factors'
  if (key === 'item_7_mda') return 'Item 7: MD&A'
  if (key === 'item_3_legal') return 'Item 3: Legal Proceedings'
  return key.replace(/_/g, ' ').toUpperCase()
}
</script>

<template>
  <div v-if="isOpen" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-fade-in">
    <div class="bg-slate-900 border border-slate-700 rounded-2xl w-full max-w-4xl max-h-[90vh] flex flex-col shadow-2xl overflow-hidden">
      <!-- Modal Header -->
      <div class="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-900/80">
        <div class="flex items-center gap-2.5">
          <div class="p-2 rounded-lg bg-amber-500/10 text-amber-400 border border-amber-500/20">
            <GitCompare class="w-5 h-5" />
          </div>
          <div>
            <h3 class="text-base font-semibold text-slate-100 flex items-center gap-2">
              Forensic Filing Diff & Language Drift
              <span class="text-[10px] font-mono px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20">
                Lazy Prices Alpha
              </span>
            </h3>
            <p class="text-xs text-slate-400">
              Detect stealth risk additions and removed disclosures between consecutive SEC filings
            </p>
          </div>
        </div>
        <button 
          @click="emit('close')"
          class="text-slate-400 hover:text-slate-200 p-1.5 rounded-lg hover:bg-slate-800 transition-colors"
        >
          <X class="w-5 h-5" />
        </button>
      </div>

      <!-- Controls Form -->
      <div class="p-6 border-b border-slate-800 bg-slate-950/40 space-y-4 shrink-0">
        <div class="flex flex-wrap items-center gap-4">
          <div class="flex-1 min-w-[180px]">
            <label class="block text-xs font-medium text-slate-400 mb-1">Ticker</label>
            <input 
              v-model="ticker" 
              type="text" 
              placeholder="e.g. NVDA" 
              class="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 uppercase font-mono tracking-wider focus:outline-none focus:border-amber-500"
              @keydown.enter="runDiff"
            />
          </div>

          <div class="w-36">
            <label class="block text-xs font-medium text-slate-400 mb-1">Filing Form</label>
            <select 
              v-model="form" 
              class="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-amber-500"
            >
              <option value="10-K">10-K (Annual)</option>
              <option value="10-Q">10-Q (Quarterly)</option>
            </select>
          </div>

          <div class="flex items-center gap-2 pt-5">
            <input 
              id="useLlm" 
              v-model="useLlm" 
              type="checkbox" 
              class="rounded bg-slate-800 border-slate-700 text-amber-500 focus:ring-0 cursor-pointer"
            />
            <label for="useLlm" class="text-xs text-slate-300 cursor-pointer select-none">
              AI Forensic Summary
            </label>
          </div>

          <div class="pt-5">
            <button 
              @click="runDiff"
              :disabled="isLoading || !ticker.trim()"
              class="px-5 py-2 rounded-lg bg-amber-500 hover:bg-amber-400 disabled:bg-slate-800 disabled:text-slate-600 text-slate-950 font-medium text-sm flex items-center gap-2 transition-colors cursor-pointer"
            >
              <Loader2 v-if="isLoading" class="w-4 h-4 animate-spin" />
              <GitCompare v-else class="w-4 h-4" />
              <span>{{ isLoading ? 'Analyzing Filings...' : 'Analyze Drift' }}</span>
            </button>
          </div>
        </div>

        <!-- Quick Ticker Pills -->
        <div class="flex items-center gap-2 text-xs text-slate-400">
          <span>Popular:</span>
          <button 
            v-for="t in popularTickers" 
            :key="t"
            @click="ticker = t"
            class="px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 font-mono transition-colors"
          >
            {{ t }}
          </button>
        </div>

        <div v-if="errorMsg" class="p-3 bg-rose-950/30 border border-rose-800/60 rounded-lg text-rose-300 text-xs flex items-center gap-2">
          <AlertTriangle class="w-4 h-4 shrink-0" />
          <span>{{ errorMsg }}</span>
        </div>
      </div>

      <!-- Results Body -->
      <div class="flex-1 overflow-y-auto p-6 space-y-6">
        <div v-if="!diffResult && !isLoading" class="text-center py-12 text-slate-500 space-y-2">
          <GitCompare class="w-10 h-10 mx-auto opacity-30" />
          <p class="text-sm">Enter a stock ticker above to compute silent language drift and risk modifications.</p>
        </div>

        <div v-if="isLoading" class="text-center py-16 space-y-3">
          <Loader2 class="w-8 h-8 text-amber-400 animate-spin mx-auto" />
          <p class="text-sm text-slate-300 font-medium">Fetching consecutive filings from SEC EDGAR & running semantic diff...</p>
          <p class="text-xs text-slate-500">Calculating paragraph-level additions, removals, and risk factors drift</p>
        </div>

        <div v-if="diffResult" class="space-y-6">
          <!-- Overview Banner -->
          <div class="p-4 rounded-xl bg-slate-800/60 border border-slate-700/80 flex flex-wrap items-center justify-between gap-4">
            <div>
              <div class="text-xs text-slate-400 font-mono flex items-center gap-1.5">
                <span>{{ diffResult.current_filing }}</span>
                <ArrowRight class="w-3.5 h-3.5 text-slate-500" />
                <span>{{ diffResult.prior_filing }}</span>
              </div>
              <h4 class="text-base font-semibold text-slate-100 mt-1 flex items-center gap-2">
                {{ diffResult.ticker }} {{ diffResult.form }} Comparison
              </h4>
            </div>

            <div class="flex items-center gap-3">
              <div class="text-right">
                <div class="text-xs text-slate-400">Language Drift</div>
                <div class="text-2xl font-bold font-mono text-slate-100">
                  {{ diffResult.overall_drift_score }}%
                </div>
              </div>
              <div 
                class="px-3 py-1.5 rounded-lg border text-xs font-semibold uppercase tracking-wider"
                :class="severityColor(diffResult.overall_severity)"
              >
                {{ diffResult.overall_severity }}
              </div>
            </div>
          </div>

          <!-- Forensic Executive Takeaway -->
          <div v-if="diffResult.forensic_summary" class="p-4 rounded-xl bg-amber-950/20 border border-amber-800/40 space-y-2">
            <div class="text-xs font-semibold text-amber-400 flex items-center gap-1.5">
              <ShieldAlert class="w-4 h-4" />
              Forensic Executive Takeaway
            </div>
            <p class="text-xs text-slate-300 leading-relaxed whitespace-pre-wrap">
              {{ diffResult.forensic_summary }}
            </p>
          </div>

          <!-- Section Tabs -->
          <div class="space-y-4">
            <div class="flex border-b border-slate-800 gap-2">
              <button
                v-for="(sec, key) in diffResult.sections"
                :key="key"
                @click="activeSection = key"
                class="pb-2 px-3 text-xs font-medium border-b-2 transition-colors cursor-pointer flex items-center gap-1.5"
                :class="activeSection === key ? 'border-amber-400 text-amber-400' : 'border-transparent text-slate-400 hover:text-slate-200'"
              >
                <span>{{ formatSectionTitle(key) }}</span>
                <span class="text-[10px] px-1.5 py-0.2 rounded font-mono" :class="severityColor(sec.severity)">
                  {{ sec.drift_score }}%
                </span>
              </button>
            </div>

            <!-- Active Section Details -->
            <div v-if="diffResult.sections[activeSection]" class="space-y-4">
              <div class="flex items-center justify-between text-xs text-slate-400">
                <div>Similarity: <span class="font-mono text-slate-200">{{ (diffResult.sections[activeSection].similarity_ratio * 100).toFixed(1) }}%</span></div>
                <div>Drift Severity: <span class="font-semibold uppercase" :class="severityColor(diffResult.sections[activeSection].severity)">{{ diffResult.sections[activeSection].severity }}</span></div>
              </div>

              <!-- Added Paragraphs (Stealth New Risks) -->
              <div v-if="diffResult.sections[activeSection].added_paragraphs?.length > 0" class="space-y-2">
                <div class="text-xs font-semibold text-emerald-400 flex items-center gap-1.5">
                  <span class="w-2 h-2 rounded-full bg-emerald-500"></span>
                  Newly Inserted Disclosures & Risks ({{ diffResult.sections[activeSection].added_paragraphs.length }})
                </div>
                <div class="space-y-2">
                  <div 
                    v-for="(para, idx) in diffResult.sections[activeSection].added_paragraphs" 
                    :key="idx"
                    class="p-3 bg-emerald-950/20 border border-emerald-800/40 rounded-lg text-xs text-emerald-200 leading-relaxed"
                  >
                    <span class="font-bold text-emerald-400 mr-1">+</span> {{ para }}
                  </div>
                </div>
              </div>

              <!-- Removed Paragraphs (Dropped Commitments / Risks) -->
              <div v-if="diffResult.sections[activeSection].removed_paragraphs?.length > 0" class="space-y-2">
                <div class="text-xs font-semibold text-rose-400 flex items-center gap-1.5">
                  <span class="w-2 h-2 rounded-full bg-rose-500"></span>
                  Silently Removed Disclosures ({{ diffResult.sections[activeSection].removed_paragraphs.length }})
                </div>
                <div class="space-y-2">
                  <div 
                    v-for="(para, idx) in diffResult.sections[activeSection].removed_paragraphs" 
                    :key="idx"
                    class="p-3 bg-rose-950/20 border border-rose-800/40 rounded-lg text-xs text-rose-200 leading-relaxed"
                  >
                    <span class="font-bold text-rose-400 mr-1">-</span> {{ para }}
                  </div>
                </div>
              </div>

              <!-- Modified Clauses -->
              <div v-if="diffResult.sections[activeSection].modified_paragraphs?.length > 0" class="space-y-2">
                <div class="text-xs font-semibold text-amber-400 flex items-center gap-1.5">
                  <span class="w-2 h-2 rounded-full bg-amber-500"></span>
                  Substantively Modified Clauses ({{ diffResult.sections[activeSection].modified_paragraphs.length }})
                </div>
                <div class="space-y-3">
                  <div 
                    v-for="(mod, idx) in diffResult.sections[activeSection].modified_paragraphs" 
                    :key="idx"
                    class="p-3 bg-slate-800/60 border border-slate-700 rounded-lg space-y-2 text-xs"
                  >
                    <div class="p-2 rounded bg-rose-950/20 text-rose-300 border border-rose-900/30">
                      <span class="font-semibold text-rose-400">Prior:</span> {{ mod.old }}
                    </div>
                    <div class="p-2 rounded bg-emerald-950/20 text-emerald-300 border border-emerald-900/30">
                      <span class="font-semibold text-emerald-400">Current:</span> {{ mod.new }}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
