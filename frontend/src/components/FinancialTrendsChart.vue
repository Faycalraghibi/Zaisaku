<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import {
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  ShieldAlert,
  Sparkles,
  Info,
  Calendar,
  Layers,
  Loader2,
  X
} from 'lucide-vue-next'

const props = defineProps({
  ticker: {
    type: String,
    default: 'NVDA'
  }
})

const emit = defineEmits(['open-chat'])

const activeMetricView = ref('accrual') // 'accrual' | 'dso' | 'mscore'
const isLoading = ref(true)
const trendsData = ref(null)
const errorMsg = ref('')
const activeAnomaly = ref(null)
const hoveredIndex = ref(null)

const fetchTrends = async (symbol) => {
  isLoading.value = true
  errorMsg.value = ''
  activeAnomaly.value = null
  try {
    const res = await fetch(`/api/forensics/trends/${encodeURIComponent(symbol)}`)
    if (!res.ok) throw new Error('Failed to load financial trend history')
    trendsData.value = await res.json()
  } catch (err) {
    errorMsg.value = err.message
  } finally {
    isLoading.value = false
  }
}

watch(() => props.ticker, (newTicker) => {
  if (newTicker) fetchTrends(newTicker)
})

onMounted(() => {
  fetchTrends(props.ticker)
})

// --- SVG Coordinate Calculations ---
const chartWidth = 720
const chartHeight = 260
const padding = { top: 30, right: 40, bottom: 40, left: 60 }
const innerWidth = chartWidth - padding.left - padding.right
const innerHeight = chartHeight - padding.top - padding.bottom

const history = computed(() => trendsData.value?.history || [])
const anomalies = computed(() => trendsData.value?.anomalies || [])

const getX = (index) => {
  if (history.value.length <= 1) return padding.left
  return padding.left + (index / (history.value.length - 1)) * innerWidth
}

// Compute Y range for View 1: Accrual Gap (Net Income vs OCF)
const accrualRange = computed(() => {
  if (!history.value.length) return { min: 0, max: 100 }
  const vals = history.value.flatMap(h => [h.operating_cash_flow, h.net_income])
  const minVal = Math.min(0, ...vals)
  const maxVal = Math.max(...vals) * 1.15 || 100
  return { min: minVal, max: maxVal }
})

const getYAccrual = (val) => {
  const { min, max } = accrualRange.value
  const norm = (val - min) / (max - min || 1)
  return padding.top + (1 - norm) * innerHeight
}

// Compute Y range for View 2: DSO
const dsoRange = computed(() => {
  if (!history.value.length) return { min: 0, max: 120 }
  const dsos = history.value.map(h => h.dso)
  const maxVal = Math.max(100, ...dsos) * 1.2
  return { min: 0, max: maxVal }
})

const getYDso = (val) => {
  const { min, max } = dsoRange.value
  const norm = (val - min) / (max - min || 1)
  return padding.top + (1 - norm) * innerHeight
}

// Compute Y range for View 3: Beneish M-Score (-3.5 to -0.5)
const mscoreRange = { min: -3.6, max: -0.8 }
const getYMScore = (val) => {
  const { min, max } = mscoreRange
  const clamped = Math.max(min, Math.min(max, val))
  const norm = (clamped - min) / (max - min)
  return padding.top + (1 - norm) * innerHeight
}

// Path generator
const generatePath = (pts) => {
  if (!pts.length) return ''
  return pts.reduce((acc, pt, idx) => {
    return idx === 0 ? `M ${pt.x} ${pt.y}` : `${acc} L ${pt.x} ${pt.y}`
  }, '')
}

const ocfPath = computed(() => {
  const pts = history.value.map((h, i) => ({ x: getX(i), y: getYAccrual(h.operating_cash_flow) }))
  return generatePath(pts)
})

const netIncomePath = computed(() => {
  const pts = history.value.map((h, i) => ({ x: getX(i), y: getYAccrual(h.net_income) }))
  return generatePath(pts)
})

const dsoPath = computed(() => {
  const pts = history.value.map((h, i) => ({ x: getX(i), y: getYDso(h.dso) }))
  return generatePath(pts)
})

const mscorePath = computed(() => {
  const pts = history.value.map((h, i) => ({ x: getX(i), y: getYMScore(h.beneish_mscore) }))
  return generatePath(pts)
})

const mscoreThresholdY = computed(() => getYMScore(-1.78))

const selectAnomaly = (anomaly) => {
  activeAnomaly.value = anomaly
}

const askAiAboutAnomaly = (anomaly) => {
  const q = `Explain the financial forensic risk behind ${props.ticker}'s ${anomaly.year} ${anomaly.title}: ${anomaly.description}`
  emit('open-chat', q)
}
</script>

<template>
  <div class="apple-card rounded-3xl p-6 sm:p-7 space-y-6">
    
    <!-- Header with Toggle Controls -->
    <div class="flex flex-wrap items-center justify-between gap-4 border-b border-white/5 pb-5">
      <div>
        <div class="flex items-center gap-2">
          <span class="text-sm font-bold text-white tracking-tight flex items-center gap-2">
            Multi-Year Forensic Accrual & Financial Trajectory
            <span class="text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              5-Year Horizon
            </span>
          </span>
        </div>
        <p class="text-xs text-slate-400 mt-0.5">
          Detecting earnings manipulation, working capital divergence, and cash collection anomalies
        </p>
      </div>

      <!-- Segmented View Toggle -->
      <div class="flex items-center bg-slate-900/90 p-1 rounded-xl border border-white/10 text-xs">
        <button
          @click="activeMetricView = 'accrual'"
          class="apple-press px-3 py-1.5 rounded-lg font-medium transition-all cursor-pointer"
          :class="activeMetricView === 'accrual' ? 'bg-emerald-500 text-slate-950 font-semibold shadow-xs' : 'text-slate-400 hover:text-white'"
        >
          Accrual Divergence (OCF vs NI)
        </button>
        <button
          @click="activeMetricView = 'dso'"
          class="apple-press px-3 py-1.5 rounded-lg font-medium transition-all cursor-pointer"
          :class="activeMetricView === 'dso' ? 'bg-emerald-500 text-slate-950 font-semibold shadow-xs' : 'text-slate-400 hover:text-white'"
        >
          Receivables DSO Trend
        </button>
        <button
          @click="activeMetricView = 'mscore'"
          class="apple-press px-3 py-1.5 rounded-lg font-medium transition-all cursor-pointer"
          :class="activeMetricView === 'mscore' ? 'bg-emerald-500 text-slate-950 font-semibold shadow-xs' : 'text-slate-400 hover:text-white'"
        >
          Beneish M-Score Trajectory
        </button>
      </div>
    </div>

    <!-- Chart Body -->
    <div v-if="isLoading" class="h-64 flex items-center justify-center">
      <Loader2 class="w-6 h-6 animate-spin text-emerald-400" />
    </div>

    <div v-else-if="errorMsg" class="p-4 rounded-xl bg-white/[0.03] border border-white/10 flex items-center justify-between gap-4">
      <div class="flex items-center gap-2.5 text-xs text-slate-300">
        <AlertTriangle class="w-4 h-4 text-amber-400 shrink-0" />
        <span>{{ errorMsg }}. The analysis service may be offline.</span>
      </div>
      <button
        @click="fetchTrends(ticker)"
        class="apple-press shrink-0 text-xs font-medium px-3 py-1.5 rounded-lg border border-white/10 bg-slate-800/80 hover:bg-slate-700 text-slate-200 cursor-pointer"
      >
        Retry
      </button>
    </div>

    <div v-else class="space-y-4">
      
      <!-- Interactive SVG Chart Area -->
      <div class="relative w-full overflow-x-auto">
        <svg 
          :viewBox="`0 0 ${chartWidth} ${chartHeight}`" 
          class="w-full h-64 select-none overflow-visible"
        >
          <!-- Horizontal Grid Lines -->
          <line 
            v-for="i in 4" 
            :key="i"
            :x1="padding.left" 
            :x2="chartWidth - padding.right" 
            :y1="padding.top + (i * (innerHeight / 4))" 
            :y2="padding.top + (i * (innerHeight / 4))" 
            stroke="rgba(255,255,255,0.06)" 
            stroke-dasharray="3 3"
          />

          <!-- VIEW 1: Accrual Divergence (OCF vs Net Income) -->
          <g v-if="activeMetricView === 'accrual'">
            <!-- OCF Curve -->
            <path 
              :d="ocfPath" 
              fill="none" 
              stroke="#10b981" 
              stroke-width="3" 
              stroke-linecap="round"
              stroke-linejoin="round"
            />
            <!-- Net Income Curve -->
            <path 
              :d="netIncomePath" 
              fill="none" 
              stroke="#38bdf8" 
              stroke-width="2.5" 
              stroke-dasharray="5 3"
              stroke-linecap="round"
              stroke-linejoin="round"
            />

            <!-- Data Points -->
            <g v-for="(h, i) in history" :key="'accrual-pt-' + i">
              <!-- OCF Circle -->
              <circle 
                :cx="getX(i)" 
                :cy="getYAccrual(h.operating_cash_flow)" 
                r="4.5" 
                fill="#10b981" 
                stroke="#090d16" 
                stroke-width="2"
                class="transition-all hover:r-6 cursor-pointer"
                @mouseenter="hoveredIndex = i"
                @mouseleave="hoveredIndex = null"
              />
              <!-- NI Circle -->
              <circle 
                :cx="getX(i)" 
                :cy="getYAccrual(h.net_income)" 
                r="4" 
                fill="#38bdf8" 
                stroke="#090d16" 
                stroke-width="2"
                class="transition-all hover:r-6 cursor-pointer"
                @mouseenter="hoveredIndex = i"
                @mouseleave="hoveredIndex = null"
              />
            </g>
          </g>

          <!-- VIEW 2: DSO Trend -->
          <g v-if="activeMetricView === 'dso'">
            <path 
              :d="dsoPath" 
              fill="none" 
              stroke="#f59e0b" 
              stroke-width="3" 
              stroke-linecap="round"
              stroke-linejoin="round"
            />
            <g v-for="(h, i) in history" :key="'dso-pt-' + i">
              <circle 
                :cx="getX(i)" 
                :cy="getYDso(h.dso)" 
                r="5" 
                fill="#f59e0b" 
                stroke="#090d16" 
                stroke-width="2"
                class="transition-all hover:r-7 cursor-pointer"
                @mouseenter="hoveredIndex = i"
                @mouseleave="hoveredIndex = null"
              />
              <text 
                :x="getX(i)" 
                :y="getYDso(h.dso) - 10" 
                fill="#fcd34d" 
                font-size="10" 
                text-anchor="middle"
                font-family="monospace"
              >
                {{ h.dso }}d
              </text>
            </g>
          </g>

          <!-- VIEW 3: Beneish M-Score Trajectory vs -1.78 Threshold -->
          <g v-if="activeMetricView === 'mscore'">
            <!-- Manipulator Redline Threshold (-1.78) -->
            <line 
              :x1="padding.left" 
              :x2="chartWidth - padding.right" 
              :y1="mscoreThresholdY" 
              :y2="mscoreThresholdY" 
              stroke="#f43f5e" 
              stroke-width="1.5" 
              stroke-dasharray="4 4"
            />
            <text 
              :x="chartWidth - padding.right" 
              :y="mscoreThresholdY - 6" 
              fill="#f43f5e" 
              font-size="10" 
              text-anchor="end"
              font-weight="bold"
              font-family="monospace"
            >
              Fraud Threshold: -1.78
            </text>

            <!-- M-Score Line -->
            <path 
              :d="mscorePath" 
              fill="none" 
              stroke="#c084fc" 
              stroke-width="3" 
              stroke-linecap="round"
              stroke-linejoin="round"
            />
            <g v-for="(h, i) in history" :key="'mscore-pt-' + i">
              <circle 
                :cx="getX(i)" 
                :cy="getYMScore(h.beneish_mscore)" 
                r="5" 
                :fill="h.beneish_mscore > -1.78 ? '#f43f5e' : '#c084fc'" 
                stroke="#090d16" 
                stroke-width="2"
                class="transition-all hover:r-7 cursor-pointer"
                @mouseenter="hoveredIndex = i"
                @mouseleave="hoveredIndex = null"
              />
              <text 
                :x="getX(i)" 
                :y="getYMScore(h.beneish_mscore) - 10" 
                fill="#e9d5ff" 
                font-size="10" 
                text-anchor="middle"
                font-family="monospace"
              >
                {{ h.beneish_mscore }}
              </text>
            </g>
          </g>

          <!-- X-Axis Fiscal Year Labels -->
          <g v-for="(h, i) in history" :key="'year-' + i">
            <text 
              :x="getX(i)" 
              :y="chartHeight - 12" 
              fill="#94a3b8" 
              font-size="11" 
              text-anchor="middle" 
              font-weight="500"
            >
              FY{{ h.year }}
            </text>
          </g>

          <!-- Clickable AI Anomaly Pins -->
          <g v-for="a in anomalies" :key="a.id">
            <g 
              v-if="history.findIndex(h => h.year === a.year) !== -1"
              :transform="`translate(${getX(history.findIndex(h => h.year === a.year))}, ${padding.top + 10})`"
              @click="selectAnomaly(a)"
              class="cursor-pointer group"
            >
              <circle r="10" fill="#f43f5e" fill-opacity="0.2" class="animate-ping" />
              <circle r="7" fill="#f43f5e" stroke="#ffffff" stroke-width="1.5" />
              <text y="3" text-anchor="middle" fill="#ffffff" font-size="8" font-weight="bold">!</text>
            </g>
          </g>
        </svg>

        <!-- Hover Tooltip -->
        <div 
          v-if="hoveredIndex !== null && history[hoveredIndex]"
          class="absolute top-2 left-1/2 -translate-x-1/2 apple-glass px-4 py-2 rounded-xl border border-white/15 text-xs text-slate-200 pointer-events-none shadow-xl flex items-center gap-4"
        >
          <span class="font-bold text-white">FY{{ history[hoveredIndex].year }}</span>
          <span class="text-emerald-400">OCF: ${{ (history[hoveredIndex].operating_cash_flow).toLocaleString() }}M</span>
          <span class="text-sky-400">Net Income: ${{ (history[hoveredIndex].net_income).toLocaleString() }}M</span>
          <span class="text-amber-400">DSO: {{ history[hoveredIndex].dso }}d</span>
          <span class="text-purple-300">M-Score: {{ history[hoveredIndex].beneish_mscore }}</span>
        </div>
      </div>

      <!-- Legend & Insights Sub-bar -->
      <div class="flex flex-wrap items-center justify-between gap-4 pt-2 border-t border-white/5 text-xs">
        <div class="flex items-center gap-4">
          <div v-if="activeMetricView === 'accrual'" class="flex items-center gap-3">
            <span class="flex items-center gap-1.5 text-slate-300">
              <span class="w-3 h-1 bg-emerald-500 rounded-full inline-block"></span>
              Operating Cash Flow
            </span>
            <span class="flex items-center gap-1.5 text-slate-300">
              <span class="w-3 h-0.5 border-t border-dashed border-sky-400 inline-block"></span>
              Net Income
            </span>
          </div>

          <div v-if="activeMetricView === 'dso'" class="flex items-center gap-1.5 text-slate-300">
            <span class="w-3 h-1 bg-amber-500 rounded-full inline-block"></span>
            Days Sales Outstanding (Receivables conversion speed)
          </div>

          <div v-if="activeMetricView === 'mscore'" class="flex items-center gap-3">
            <span class="flex items-center gap-1.5 text-slate-300">
              <span class="w-3 h-1 bg-purple-400 rounded-full inline-block"></span>
              Beneish M-Score
            </span>
            <span class="flex items-center gap-1.5 text-rose-400 font-medium">
              <span class="w-3 h-0.5 border-t border-dashed border-rose-500 inline-block"></span>
              Manipulation Redline (-1.78)
            </span>
          </div>
        </div>

        <div v-if="anomalies.length > 0" class="flex items-center gap-1.5 text-rose-400 font-medium">
          <span class="w-2 h-2 rounded-full bg-rose-500 animate-pulse"></span>
          <span>{{ anomalies.length }} AI Anomaly Marker{{ anomalies.length !== 1 ? 's' : '' }} Flagged (Click Pin to Inspect)</span>
        </div>
        <div v-else class="text-emerald-400 text-[11px] font-medium flex items-center gap-1">
          <Sparkles class="w-3 h-3" />
          <span>Zero manipulation anomalies detected across 5-year timeline</span>
        </div>
      </div>

      <!-- Anomaly Drawer / Popover Card -->
      <div 
        v-if="activeAnomaly" 
        class="p-4 rounded-2xl bg-slate-900/90 border border-rose-500/30 shadow-xl space-y-3 animate-in fade-in slide-in-from-top-2 duration-200"
      >
        <div class="flex items-start justify-between">
          <div class="flex items-center gap-2">
            <div class="p-1.5 rounded-lg bg-rose-500/20 text-rose-400">
              <AlertTriangle class="w-4 h-4" />
            </div>
            <div>
              <h4 class="text-xs font-semibold text-white flex items-center gap-2">
                {{ activeAnomaly.title }}
                <span class="text-xs font-mono px-2 py-0.5 rounded-md bg-rose-500/20 text-rose-300 border border-rose-500/30">
                  FY{{ activeAnomaly.year }} / {{ activeAnomaly.severity.toLowerCase() }} risk
                </span>
              </h4>
            </div>
          </div>
          <button @click="activeAnomaly = null" class="text-slate-400 hover:text-white p-1">
            <X class="w-3.5 h-3.5" />
          </button>
        </div>

        <p class="text-xs text-slate-300 leading-relaxed">
          {{ activeAnomaly.description }}
        </p>

        <div class="flex flex-wrap items-center justify-between gap-3 pt-1 border-t border-white/5">
          <span class="text-xs text-amber-300/90">
            <strong>Recommended audit procedure:</strong> {{ activeAnomaly.suggested_audit_action }}
          </span>
          <button
            @click="askAiAboutAnomaly(activeAnomaly)"
            class="apple-press text-xs font-medium px-3 py-1.5 rounded-xl bg-rose-600 hover:bg-rose-500 text-white flex items-center gap-1.5 cursor-pointer shadow-xs"
          >
            <Sparkles class="w-3 h-3" />
            <span>Investigate anomaly</span>
          </button>
        </div>
      </div>

    </div>

  </div>
</template>
