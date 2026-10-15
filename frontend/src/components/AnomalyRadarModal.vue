<script setup>
import { ref, watch, onMounted, onUnmounted } from 'vue'
import {
  ShieldAlert,
  AlertTriangle,
  CheckCircle2,
  X,
  Loader2,
  Building2,
  ExternalLink,
  Flame,
  FileText,
  Scale,
  RefreshCw,
  Search
} from 'lucide-vue-next'

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false
  },
  initialTicker: {
    type: String,
    default: 'NVDA'
  }
})

const emit = defineEmits(['close', 'select-ticker'])

const currentTicker = ref(props.initialTicker || 'NVDA')
const customInput = ref('')
const isLoading = ref(false)
const errorMsg = ref('')
const anomalyData = ref(null)

const presets = [
  { ticker: 'NVDA', label: 'NVIDIA (Clean Baseline)' },
  { ticker: 'AAPL', label: 'Apple (Institutional Gold)' },
  { ticker: 'MSFT', label: 'Microsoft (Enterprise Safe)' },
  { ticker: 'TSLA', label: 'Tesla (Elevated Inventory)' },
  { ticker: 'AMZN', label: 'Amazon (Useful Life Scan)' },
  { ticker: 'SMCI', label: 'Super Micro (Critical Governance Alert)' }
]

const fetchAnomalies = async (symbol) => {
  const tickerToFetch = (symbol || currentTicker.value || 'NVDA').trim().toUpperCase()
  currentTicker.value = tickerToFetch
  isLoading.value = true
  errorMsg.value = ''

  try {
    const res = await fetch(`/api/forensics/anomalies/${tickerToFetch}`)
    if (!res.ok) {
      throw new Error(`Failed to scan anomalies: ${res.statusText}`)
    }
    const data = await res.json()
    anomalyData.value = data
  } catch (err) {
    errorMsg.value = err.message || 'Error scanning disclosure anomalies'
  } finally {
    isLoading.value = false
  }
}

watch(() => props.isOpen, (open) => {
  if (open) {
    currentTicker.value = props.initialTicker || 'NVDA'
    fetchAnomalies(currentTicker.value)
  }
})

const handlePresetClick = (symbol) => {
  fetchAnomalies(symbol)
  emit('select-ticker', symbol)
}

const handleCustomSearch = () => {
  if (customInput.value.trim()) {
    fetchAnomalies(customInput.value.trim())
    emit('select-ticker', customInput.value.trim().toUpperCase())
    customInput.value = ''
  }
}

const handleKeyDown = (e) => {
  if (props.isOpen && e.key === 'Escape') {
    e.preventDefault()
    emit('close')
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleKeyDown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeyDown)
})
</script>

<template>
  <Teleport to="body">
    <div
      v-if="isOpen"
      class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-xl animate-fadeIn"
      @click.self="emit('close')"
    >
      <div
        class="apple-glass rounded-2xl max-w-4xl w-full max-h-[90vh] flex flex-col shadow-2xl border border-white/10 text-slate-100 overflow-hidden"
        @click.stop
      >
        <!-- Modal Header -->
        <div class="px-6 py-4 border-b border-white/10 flex items-center justify-between bg-slate-900/80">
          <div class="flex items-center gap-3">
            <div class="p-2.5 rounded-xl bg-rose-500/10 text-rose-400 border border-rose-500/20">
              <ShieldAlert class="w-5 h-5" />
            </div>
            <div>
              <div class="flex items-center gap-2">
                <h2 class="text-base font-semibold text-white">Filing Anomaly & Corporate Governance Radar</h2>
                <span class="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-white/10">
                  PCAOB & SEC Form 12b-25
                </span>
              </div>
              <p class="text-xs text-slate-400">
                Automated detection of executive turnover, auditor independence breaches, and inventory-sales decoupling
              </p>
            </div>
          </div>
          <button
            @click="emit('close')"
            class="text-slate-400 hover:text-white p-1 rounded-lg transition-colors cursor-pointer"
          >
            <X class="w-5 h-5" />
          </button>
        </div>

        <!-- Ticker Selector Ribbon -->
        <div class="px-6 py-2.5 border-b border-white/10 bg-slate-950/60 flex flex-wrap items-center justify-between gap-3 text-xs">
          <div class="flex items-center gap-1.5 overflow-x-auto custom-scrollbar py-0.5">
            <span class="text-slate-400 text-[11px] font-semibold mr-1 uppercase tracking-wider">Presets:</span>
            <button
              v-for="p in presets"
              :key="p.ticker"
              @click="handlePresetClick(p.ticker)"
              class="apple-press px-2.5 py-1 rounded-lg text-xs font-mono transition-all cursor-pointer shrink-0"
              :class="currentTicker === p.ticker ? 'bg-indigo-600 text-white font-bold shadow-xs' : 'bg-slate-800/80 hover:bg-slate-700 text-slate-300 border border-white/5'"
            >
              {{ p.ticker }}
            </button>
          </div>

          <!-- Custom Ticker Search -->
          <div class="flex items-center gap-2 w-full sm:w-auto">
            <div class="relative w-full sm:w-36">
              <input
                v-model="customInput"
                type="text"
                placeholder="Custom ticker..."
                @keyup.enter="handleCustomSearch"
                class="w-full bg-slate-900 border border-white/10 rounded-lg pl-7 pr-2 py-1 text-xs text-white placeholder-slate-400 focus:outline-none focus:border-indigo-500 font-mono"
              />
              <Search class="w-3.5 h-3.5 text-slate-400 absolute left-2 top-1.5" />
            </div>
            <button
              @click="handleCustomSearch"
              class="apple-press px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs rounded-lg border border-white/10 cursor-pointer"
            >
              Scan
            </button>
          </div>
        </div>

        <!-- Body Area -->
        <div class="flex-1 overflow-y-auto p-6 space-y-6 custom-scrollbar bg-slate-950/40">
          <!-- Loading State -->
          <div v-if="isLoading" class="py-16 flex flex-col items-center justify-center space-y-3">
            <Loader2 class="w-8 h-8 text-indigo-400 animate-spin" />
            <p class="text-xs text-slate-400 font-medium">Scanning SEC EDGAR disclosures, proxy statements, and Form 8-K filings...</p>
          </div>

          <!-- Error State -->
          <div v-else-if="errorMsg" class="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs">
            <div class="font-semibold mb-1 flex items-center gap-2">
              <AlertTriangle class="w-4 h-4 text-rose-400" />
              <span>Anomaly Scan Failed</span>
            </div>
            <p>{{ errorMsg }}</p>
          </div>

          <!-- Data Content -->
          <div v-else-if="anomalyData" class="space-y-6">
            <!-- Executive Anomaly Summary Card -->
            <div 
              class="p-5 rounded-2xl border transition-all"
              :class="anomalyData.overall_anomaly_tier === 'CRITICAL_ALERT' 
                ? 'bg-rose-950/30 border-rose-500/30' 
                : anomalyData.overall_anomaly_tier === 'ELEVATED_WATCH' 
                ? 'bg-amber-950/25 border-amber-500/30' 
                : 'bg-emerald-950/20 border-emerald-500/25'"
            >
              <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-white/10">
                <div class="flex items-center gap-3">
                  <div 
                    class="p-3 rounded-xl border"
                    :class="anomalyData.overall_anomaly_tier === 'CRITICAL_ALERT' 
                      ? 'bg-rose-500/20 text-rose-400 border-rose-500/40' 
                      : anomalyData.overall_anomaly_tier === 'ELEVATED_WATCH' 
                      ? 'bg-amber-500/20 text-amber-400 border-amber-500/40' 
                      : 'bg-emerald-500/20 text-emerald-400 border-emerald-500/40'"
                  >
                    <component 
                      :is="anomalyData.overall_anomaly_tier === 'CRITICAL_ALERT' ? Flame : anomalyData.overall_anomaly_tier === 'ELEVATED_WATCH' ? AlertTriangle : CheckCircle2" 
                      class="w-6 h-6" 
                    />
                  </div>
                  <div>
                    <div class="flex items-center gap-2">
                      <span class="text-lg font-bold text-white">{{ anomalyData.ticker }}</span>
                      <span class="text-xs text-slate-400">• {{ anomalyData.company_name }}</span>
                    </div>
                    <div class="flex items-center gap-2 mt-1">
                      <span 
                        class="text-[11px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wider border"
                        :class="anomalyData.overall_anomaly_tier === 'CRITICAL_ALERT' 
                          ? 'bg-rose-500/20 text-rose-400 border-rose-500/30' 
                          : anomalyData.overall_anomaly_tier === 'ELEVATED_WATCH' 
                          ? 'bg-amber-500/20 text-amber-400 border-amber-500/30' 
                          : 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30'"
                      >
                        {{ anomalyData.overall_anomaly_tier.replace('_', ' ') }}
                      </span>
                      <span class="text-xs text-slate-400 font-mono">
                        Score: {{ anomalyData.anomaly_score }} / 100
                      </span>
                    </div>
                  </div>
                </div>

                <!-- Anomaly Metric Badges -->
                <div class="flex items-center gap-3 text-xs">
                  <div class="px-3 py-2 rounded-xl bg-slate-900/60 border border-white/10 text-center">
                    <span class="block text-[10px] text-slate-400 uppercase tracking-wider">Critical</span>
                    <span class="text-base font-bold" :class="anomalyData.critical_count > 0 ? 'text-rose-400' : 'text-slate-300'">
                      {{ anomalyData.critical_count }}
                    </span>
                  </div>
                  <div class="px-3 py-2 rounded-xl bg-slate-900/60 border border-white/10 text-center">
                    <span class="block text-[10px] text-slate-400 uppercase tracking-wider">Elevated</span>
                    <span class="text-base font-bold" :class="anomalyData.elevated_count > 0 ? 'text-amber-400' : 'text-slate-300'">
                      {{ anomalyData.elevated_count }}
                    </span>
                  </div>
                  <div class="px-3 py-2 rounded-xl bg-slate-900/60 border border-white/10 text-center">
                    <span class="block text-[10px] text-slate-400 uppercase tracking-wider">Signals</span>
                    <span class="text-base font-bold text-slate-200">
                      {{ anomalyData.findings.length }}
                    </span>
                  </div>
                </div>
              </div>

              <!-- Institutional Summary Text -->
              <p class="text-xs text-slate-300 leading-relaxed pt-3">
                {{ anomalyData.institutional_summary }}
              </p>
            </div>

            <!-- Detected Disclosure Signals List -->
            <div class="space-y-3">
              <h3 class="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-2">
                <span>Evaluated Disclosure Signals & Red Flags</span>
                <span class="text-[10px] font-mono text-slate-400">({{ anomalyData.findings.length }} audited)</span>
              </h3>

              <div class="space-y-3">
                <div
                  v-for="finding in anomalyData.findings"
                  :key="finding.id"
                  class="p-4 rounded-xl bg-slate-900/70 border border-white/10 space-y-3"
                >
                  <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                    <div class="flex items-center gap-2.5">
                      <span 
                        class="text-[10px] font-mono font-bold px-2 py-0.5 rounded border"
                        :class="finding.severity === 'CRITICAL' 
                          ? 'bg-rose-500/20 text-rose-400 border-rose-500/30' 
                          : finding.severity === 'ELEVATED' 
                          ? 'bg-amber-500/20 text-amber-400 border-amber-500/30' 
                          : finding.severity === 'MONITOR' 
                          ? 'bg-blue-500/20 text-blue-400 border-blue-500/30' 
                          : 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30'"
                      >
                        {{ finding.severity }}
                      </span>
                      <h4 class="text-xs font-semibold text-white">{{ finding.title }}</h4>
                    </div>

                    <span class="text-[11px] font-mono text-slate-400 truncate">
                      {{ finding.citation }}
                    </span>
                  </div>

                  <!-- Metric Observation Grid -->
                  <div class="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs bg-black/30 p-2.5 rounded-lg border border-white/5 font-mono">
                    <div>
                      <span class="text-[10px] text-slate-500 block uppercase">Observed Signal</span>
                      <span class="font-medium text-slate-200">{{ finding.observed_value }}</span>
                    </div>
                    <div>
                      <span class="text-[10px] text-slate-500 block uppercase">Institutional Benchmark</span>
                      <span class="font-medium text-slate-400">{{ finding.institutional_threshold }}</span>
                    </div>
                  </div>

                  <!-- Explanation -->
                  <p class="text-xs text-slate-300 leading-relaxed">
                    {{ finding.explanation }}
                  </p>

                  <!-- Remediation / Recommendation -->
                  <div class="p-2.5 rounded-lg bg-indigo-950/30 border border-indigo-500/20 text-indigo-300 text-xs flex items-start gap-2">
                    <Scale class="w-4 h-4 text-indigo-400 shrink-0 mt-0.5" />
                    <div>
                      <span class="font-semibold text-indigo-200 block text-[11px] uppercase tracking-wider mb-0.5">Audit Procedure Recommendation</span>
                      <span>{{ finding.remediation_recommendation }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Footer -->
        <div class="px-6 py-3 border-t border-white/10 bg-slate-900/90 flex items-center justify-between text-xs text-slate-400">
          <div class="flex items-center gap-2">
            <span class="w-2 h-2 rounded-full bg-emerald-400"></span>
            <span>SEC Enforcement & PCAOB Rule 3526 Calibrated</span>
          </div>
          <button
            @click="fetchAnomalies(currentTicker)"
            class="apple-press px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 flex items-center gap-1.5 cursor-pointer border border-white/10"
          >
            <RefreshCw class="w-3.5 h-3.5" :class="{ 'animate-spin': isLoading }" />
            <span>Re-scan Ticker</span>
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.apple-glass {
  background: rgba(10, 14, 23, 0.88);
  backdrop-filter: blur(32px) saturate(190%);
}

.apple-press {
  transition: transform 0.16s cubic-bezier(0.32, 0.72, 0, 1), background-color 0.16s ease;
}

.apple-press:active {
  transform: scale(0.975);
}

.custom-scrollbar::-webkit-scrollbar {
  width: 5px;
  height: 5px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.02);
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.12);
  border-radius: 9999px;
}
</style>
