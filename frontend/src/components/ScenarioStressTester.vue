<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import {
  Sliders,
  TrendingDown,
  TrendingUp,
  AlertTriangle,
  ShieldAlert,
  ShieldCheck,
  RotateCcw,
  Play,
  Loader2,
  Activity,
  Layers,
  DollarSign,
  Clock,
  Sparkles,
  Info,
  HelpCircle,
  FileCheck
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

// --- State ---
const isLoadingPresets = ref(false)
const isSimulating = ref(false)
const presets = ref([])
const activePresetId = ref('taiwan_wafer_disruption')

const sliders = reactive({
  revenueShockPct: -18.5,
  grossMarginCompressionBps: -520,
  opexInflationPct: 9.5,
  dsoExpansionDays: 40,
  mcRuns: 1000
})

const simulationResult = ref(null)
const hoveredBin = ref(null)

// --- Load Presets ---
const fetchPresets = async () => {
  isLoadingPresets.value = true
  try {
    const res = await fetch('/api/forensics/stress/presets')
    if (res.ok) {
      presets.value = await res.json()
    }
  } catch (err) {
    console.error('Failed to load stress presets:', err)
  } finally {
    isLoadingPresets.value = false
  }
}

// --- Apply Preset ---
const applyPreset = (preset) => {
  activePresetId.value = preset.id
  sliders.revenueShockPct = preset.revenue_shock_pct
  sliders.grossMarginCompressionBps = preset.gross_margin_compression_bps
  sliders.opexInflationPct = preset.opex_inflation_pct
  sliders.dsoExpansionDays = preset.dso_expansion_days
  runSimulation()
}

// --- Run Simulation ---
const runSimulation = async () => {
  isSimulating.value = true
  try {
    const res = await fetch('/api/forensics/stress/simulate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        ticker: props.ticker,
        scenario_preset_id: activePresetId.value,
        revenue_shock_pct: Number(sliders.revenueShockPct),
        gross_margin_compression_bps: Number(sliders.grossMarginCompressionBps),
        opex_inflation_pct: Number(sliders.opexInflationPct),
        dso_expansion_days: Number(sliders.dsoExpansionDays),
        n_monte_carlo_runs: Number(sliders.mcRuns),
        random_seed: 42
      })
    })

    if (res.ok) {
      simulationResult.value = await res.json()
    }
  } catch (err) {
    console.error('Failed to run stress simulation:', err)
  } finally {
    isSimulating.value = false
  }
}

// --- Custom Slider Modification ---
const onCustomSliderChange = () => {
  activePresetId.value = 'custom'
  runSimulation()
}

// --- Reset to default preset ---
const resetToBaseline = () => {
  if (presets.value.length > 0) {
    applyPreset(presets.value[0])
  } else {
    sliders.revenueShockPct = -18.5
    sliders.grossMarginCompressionBps = -520
    sliders.opexInflationPct = 9.5
    sliders.dsoExpansionDays = 40
    runSimulation()
  }
}

// Watch ticker change
watch(() => props.ticker, () => {
  runSimulation()
})

onMounted(async () => {
  await fetchPresets()
  await runSimulation()
})

// --- Histogram Coordinates Calculation ---
const histogramMaxCount = computed(() => {
  if (!simulationResult.value?.monte_carlo?.histogram_bins) return 1
  return Math.max(...simulationResult.value.monte_carlo.histogram_bins.map(b => b.count), 1)
})

const var95LeftPct = computed(() => {
  if (!simulationResult.value?.monte_carlo) return '20%'
  const { min_fcf, max_fcf, var_95 } = simulationResult.value.monte_carlo
  const span = max_fcf - min_fcf
  if (span <= 0) return '20%'
  const pct = ((var_95 - min_fcf) / span) * 100
  return `${Math.max(4, Math.min(96, pct)).toFixed(1)}%`
})

const getBarHeightPct = (count) => {
  return ((count / histogramMaxCount.value) * 85).toFixed(1)
}

const formatUSD = (val) => {
  if (val === undefined || val === null) return '$0M'
  const abs = Math.abs(val)
  const sign = val < 0 ? '-' : ''
  return `${sign}$${abs.toLocaleString(undefined, { maximumFractionDigits: 0 })}M`
}
</script>

<template>
  <div class="apple-card rounded-2xl p-6 space-y-6">
    <!-- Header -->
    <div class="flex flex-wrap items-center justify-between gap-4 border-b border-white/5 pb-5">
      <div>
        <div class="flex items-center gap-2.5">
          <div class="p-2 rounded-xl bg-rose-500/10 text-rose-400 border border-rose-500/20">
            <Activity class="w-4 h-4" />
          </div>
          <div>
            <h2 class="text-base font-bold text-white tracking-tight flex items-center gap-2">
              Macro Scenario Stress-Tester & Monte Carlo Risk Engine
              <span class="text-[10px] font-mono px-2 py-0.5 rounded-full bg-rose-500/10 text-rose-300 border border-rose-500/20">
                1,000 Tail Runs
              </span>
            </h2>
            <p class="text-xs text-slate-400">
              Pro-forma liquidity drawdown, working capital deceleration, and Value-at-Risk (VaR) distribution
            </p>
          </div>
        </div>
      </div>

      <div class="flex items-center gap-2">
        <button
          @click="resetToBaseline"
          class="apple-press px-3 py-1.5 rounded-xl border border-white/10 bg-slate-800/80 hover:bg-slate-700 text-slate-300 text-xs font-medium flex items-center gap-1.5 transition-colors cursor-pointer"
          title="Reset to default scenario shock"
        >
          <RotateCcw class="w-3.5 h-3.5" />
          <span>Reset Preset</span>
        </button>

        <button
          @click="runSimulation"
          :disabled="isSimulating"
          class="apple-press px-3.5 py-1.5 rounded-xl bg-rose-600 hover:bg-rose-500 disabled:opacity-50 text-white text-xs font-semibold shadow-xs flex items-center gap-1.5 transition-all cursor-pointer"
        >
          <Loader2 v-if="isSimulating" class="w-3.5 h-3.5 animate-spin" />
          <Play v-else class="w-3.5 h-3.5 fill-current" />
          <span>{{ isSimulating ? 'Simulating...' : 'Simulate Shock' }}</span>
        </button>
      </div>
    </div>

    <!-- Scenario Preset Quick Selectors -->
    <div class="space-y-2">
      <div class="flex items-center justify-between">
        <span class="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
          <Layers class="w-3.5 h-3.5 text-rose-400" />
          Macro Shock Archetypes
        </span>
        <span class="text-[11px] text-slate-500 font-mono">Select preset to calibrate stress vectors</span>
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        <button
          v-for="preset in presets"
          :key="preset.id"
          @click="applyPreset(preset)"
          class="apple-press text-left p-3.5 rounded-xl border transition-all cursor-pointer flex flex-col justify-between space-y-2"
          :class="activePresetId === preset.id 
            ? 'bg-rose-500/10 border-rose-500/40 text-white shadow-xs' 
            : 'bg-slate-900/40 border-white/5 hover:border-white/15 text-slate-300'"
        >
          <div class="space-y-1">
            <div class="flex items-center justify-between">
              <span class="text-xs font-mono text-rose-400 font-medium">
                {{ preset.category }}
              </span>
              <span v-if="activePresetId === preset.id" class="w-2 h-2 rounded-full bg-rose-400 animate-pulse"></span>
            </div>
            <h4 class="text-xs font-bold leading-tight">{{ preset.name }}</h4>
            <p class="text-[11px] text-slate-400 line-clamp-2 leading-relaxed">
              {{ preset.description }}
            </p>
          </div>

          <div class="pt-2 border-t border-white/5 grid grid-cols-2 gap-2 text-[10px] font-mono">
            <div>
              <span class="text-slate-500 block">Top-Line</span>
              <span class="font-bold text-rose-400">{{ preset.revenue_shock_pct }}%</span>
            </div>
            <div>
              <span class="text-slate-500 block">Margin</span>
              <span class="font-bold text-amber-400">{{ preset.gross_margin_compression_bps }} bps</span>
            </div>
          </div>
        </button>
      </div>
    </div>

    <!-- Interactive Shock Parameter Sliders -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 p-4 rounded-xl bg-slate-950/60 border border-white/5">
      
      <!-- Slider 1: Top-Line Shock -->
      <div class="space-y-1.5">
        <div class="flex items-center justify-between text-xs">
          <span class="text-slate-400 font-medium">Revenue Shock</span>
          <span class="font-mono font-bold" :class="sliders.revenueShockPct < 0 ? 'text-rose-400' : 'text-emerald-400'">
            {{ sliders.revenueShockPct > 0 ? '+' : '' }}{{ sliders.revenueShockPct }}%
          </span>
        </div>
        <input 
          type="range" 
          min="-40" 
          max="10" 
          step="0.5"
          v-model.number="sliders.revenueShockPct" 
          @input="onCustomSliderChange"
          class="w-full accent-rose-500 h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer"
        />
        <div class="flex justify-between text-[10px] text-slate-500 font-mono">
          <span>-40%</span>
          <span>0%</span>
          <span>+10%</span>
        </div>
      </div>

      <!-- Slider 2: Margin Compression -->
      <div class="space-y-1.5">
        <div class="flex items-center justify-between text-xs">
          <span class="text-slate-400 font-medium">Gross Margin Cut</span>
          <span class="font-mono font-bold text-amber-400">
            {{ sliders.grossMarginCompressionBps }} bps
          </span>
        </div>
        <input 
          type="range" 
          min="-800" 
          max="0" 
          step="10"
          v-model.number="sliders.grossMarginCompressionBps" 
          @input="onCustomSliderChange"
          class="w-full accent-amber-500 h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer"
        />
        <div class="flex justify-between text-[10px] text-slate-500 font-mono">
          <span>-800 bps</span>
          <span>-400 bps</span>
          <span>0 bps</span>
        </div>
      </div>

      <!-- Slider 3: OpEx Inflation -->
      <div class="space-y-1.5">
        <div class="flex items-center justify-between text-xs">
          <span class="text-slate-400 font-medium">OpEx Cost Inflation</span>
          <span class="font-mono font-bold text-sky-400">
            +{{ sliders.opexInflationPct }}%
          </span>
        </div>
        <input 
          type="range" 
          min="0" 
          max="25" 
          step="0.5"
          v-model.number="sliders.opexInflationPct" 
          @input="onCustomSliderChange"
          class="w-full accent-sky-500 h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer"
        />
        <div class="flex justify-between text-[10px] text-slate-500 font-mono">
          <span>0%</span>
          <span>+12.5%</span>
          <span>+25%</span>
        </div>
      </div>

      <!-- Slider 4: DSO Expansion -->
      <div class="space-y-1.5">
        <div class="flex items-center justify-between text-xs">
          <span class="text-slate-400 font-medium">DSO Extension</span>
          <span class="font-mono font-bold text-purple-400">
            +{{ sliders.dsoExpansionDays }} days
          </span>
        </div>
        <input 
          type="range" 
          min="0" 
          max="75" 
          step="1"
          v-model.number="sliders.dsoExpansionDays" 
          @input="onCustomSliderChange"
          class="w-full accent-purple-500 h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer"
        />
        <div class="flex justify-between text-[10px] text-slate-500 font-mono">
          <span>0d</span>
          <span>+35d</span>
          <span>+75d</span>
        </div>
      </div>

    </div>

    <!-- Loading / Results View -->
    <div v-if="isSimulating && !simulationResult" class="p-16 flex flex-col items-center justify-center space-y-3">
      <Loader2 class="w-8 h-8 animate-spin text-rose-500" />
      <span class="text-xs text-slate-400 font-mono">Simulating pro-forma cash flows and 1,000 Monte Carlo runs...</span>
    </div>

    <div v-else-if="simulationResult" class="space-y-6">
      
      <!-- Key Pro-Forma Impact KPI Metric Cards -->
      <div class="grid grid-cols-2 md:grid-cols-4 gap-3.5">
        
        <!-- Shocked Revenue -->
        <div class="p-4 rounded-xl bg-slate-900/50 border border-white/5 space-y-1.5">
          <span class="text-[11px] text-slate-400 font-medium flex items-center justify-between">
            Shocked Revenue
            <TrendingDown v-if="simulationResult.pro_forma.revenue_delta < 0" class="w-3.5 h-3.5 text-rose-400" />
            <TrendingUp v-else class="w-3.5 h-3.5 text-emerald-400" />
          </span>
          <div class="text-lg font-bold text-white font-mono">
            {{ formatUSD(simulationResult.pro_forma.shocked_revenue) }}
          </div>
          <div class="text-[11px] font-mono" :class="simulationResult.pro_forma.revenue_delta < 0 ? 'text-rose-400' : 'text-emerald-400'">
            {{ simulationResult.pro_forma.revenue_delta < 0 ? '' : '+' }}{{ formatUSD(simulationResult.pro_forma.revenue_delta) }}
            ({{ simulationResult.pro_forma.revenue_delta_pct > 0 ? '+' : '' }}{{ simulationResult.pro_forma.revenue_delta_pct }}%)
          </div>
        </div>

        <!-- Shocked Gross Margin -->
        <div class="p-4 rounded-xl bg-slate-900/50 border border-white/5 space-y-1.5">
          <span class="text-[11px] text-slate-400 font-medium flex items-center justify-between">
            Shocked Margin
            <span class="text-[10px] font-mono text-slate-500">Base {{ (simulationResult.baseline.gross_margin * 100).toFixed(1) }}%</span>
          </span>
          <div class="text-lg font-bold text-amber-300 font-mono">
            {{ (simulationResult.pro_forma.shocked_gross_margin * 100).toFixed(1) }}%
          </div>
          <div class="text-[11px] font-mono text-amber-400">
            {{ simulationResult.pro_forma.gross_margin_delta_bps }} bps compression
          </div>
        </div>

        <!-- Working Capital Drag -->
        <div class="p-4 rounded-xl bg-slate-900/50 border border-white/5 space-y-1.5">
          <span class="text-[11px] text-slate-400 font-medium flex items-center justify-between">
            Working Capital Drag
            <Clock class="w-3.5 h-3.5 text-purple-400" />
          </span>
          <div class="text-lg font-bold text-purple-300 font-mono">
            {{ formatUSD(simulationResult.pro_forma.working_capital_drag) }}
          </div>
          <div class="text-[11px] font-mono text-slate-400">
            DSO expanded to {{ (simulationResult.baseline.dso + sliders.dsoExpansionDays).toFixed(0) }} days
          </div>
        </div>

        <!-- Pro-Forma Free Cash Flow -->
        <div class="p-4 rounded-xl bg-slate-900/50 border border-white/5 space-y-1.5">
          <span class="text-[11px] text-slate-400 font-medium flex items-center justify-between">
            Shocked FCF
            <span class="text-[10px] font-mono text-slate-500">Base {{ formatUSD(simulationResult.baseline.free_cash_flow) }}</span>
          </span>
          <div class="text-lg font-bold font-mono" :class="simulationResult.pro_forma.shocked_fcf < 0 ? 'text-rose-400' : 'text-emerald-300'">
            {{ formatUSD(simulationResult.pro_forma.shocked_fcf) }}
          </div>
          <div class="text-[11px] font-mono" :class="simulationResult.pro_forma.fcf_delta < 0 ? 'text-rose-400' : 'text-emerald-400'">
            {{ formatUSD(simulationResult.pro_forma.fcf_delta) }} delta ({{ (simulationResult.pro_forma.fcf_margin * 100).toFixed(1) }}% margin)
          </div>
        </div>

      </div>

      <!-- Monte Carlo Tail Risk Distribution & Histogram -->
      <div class="p-5 rounded-2xl bg-slate-950/80 border border-white/5 space-y-4">
        <div class="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h3 class="text-xs font-semibold text-white flex items-center gap-2">
              <span class="w-2 h-2 rounded-full bg-rose-500"></span>
              Monte Carlo tail risk distribution (1,000 iterations)
            </h3>
            <p class="text-[11px] text-slate-400">
              Parametric Gaussian distribution of pro-forma Free Cash Flow across correlated stochastic shocks
            </p>
          </div>

          <!-- VaR Metrics Badges -->
          <div class="flex items-center gap-2 text-xs font-mono">
            <span class="px-2.5 py-1 rounded-lg bg-slate-900 border border-white/10 text-slate-300">
              Mean: <strong class="text-white">{{ formatUSD(simulationResult.monte_carlo.mean_fcf) }}</strong>
            </span>
            <span class="px-2.5 py-1 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-300">
              VaR 95%: <strong class="text-rose-400">{{ formatUSD(simulationResult.monte_carlo.var_95) }}</strong>
            </span>
            <span class="px-2.5 py-1 rounded-lg bg-red-950/40 border border-red-800 text-red-300">
              CVaR 95%: <strong class="text-red-400">{{ formatUSD(simulationResult.monte_carlo.cvar_95) }}</strong>
            </span>
          </div>
        </div>

        <!-- Interactive Histogram Graphic -->
        <div class="space-y-2">
          <div class="h-44 w-full flex items-end gap-1.5 pt-6 pb-2 px-2 rounded-xl bg-slate-900/60 border border-white/5 relative">
            
            <!-- Hover Tooltip -->
            <div 
              v-if="hoveredBin" 
              class="absolute top-2 right-4 px-3 py-1 rounded-lg bg-slate-800 border border-white/10 text-[11px] font-mono text-slate-200 z-10 shadow-lg"
            >
              Range: {{ formatUSD(hoveredBin.bin_start) }} - {{ formatUSD(hoveredBin.bin_end) }} | Runs: {{ hoveredBin.count }}
            </div>

            <!-- Vertical VaR 95% Reference Line Indicator -->
            <div 
              class="absolute top-0 bottom-6 border-r border-dashed border-rose-500/80 pointer-events-none flex flex-col justify-between"
              :style="{ left: var95LeftPct }"
            >
              <span class="text-[9px] font-mono text-rose-400 -translate-x-1/2 bg-slate-950 px-1 rounded border border-rose-500/40">
                VaR 95% ({{ formatUSD(simulationResult.monte_carlo.var_95) }})
              </span>
            </div>

            <!-- Histogram Columns -->
            <div
              v-for="(bin, idx) in simulationResult.monte_carlo.histogram_bins"
              :key="idx"
              @mouseenter="hoveredBin = bin"
              @mouseleave="hoveredBin = null"
              class="flex-1 rounded-t-sm transition-all relative group cursor-pointer"
              :class="bin.bin_center < 0 
                ? 'bg-rose-600/70 hover:bg-rose-500' 
                : bin.bin_center < simulationResult.monte_carlo.var_95 
                  ? 'bg-amber-600/60 hover:bg-amber-500' 
                  : 'bg-emerald-600/60 hover:bg-emerald-500'"
              :style="{ height: `${getBarHeightPct(bin.count)}%` }"
            ></div>
          </div>

          <!-- X-Axis Labels -->
          <div class="flex justify-between text-[10px] font-mono text-slate-500 px-2">
            <span>Worst Case: {{ formatUSD(simulationResult.monte_carlo.min_fcf) }}</span>
            <span>Median FCF: {{ formatUSD(simulationResult.monte_carlo.median_fcf) }}</span>
            <span>Best Case: {{ formatUSD(simulationResult.monte_carlo.max_fcf) }}</span>
          </div>
        </div>

        <!-- Negative Cash Flow Probability Warning -->
        <div 
          v-if="simulationResult.monte_carlo.prob_negative_fcf > 0"
          class="p-3 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-300 text-xs flex items-center gap-2.5"
        >
          <AlertTriangle class="w-4 h-4 shrink-0 text-amber-400" />
          <span>
            <strong>Liquidity Warning:</strong> Simulated parameters yield a 
            <strong>{{ (simulationResult.monte_carlo.prob_negative_fcf * 100).toFixed(1) }}% probability</strong> 
            of quarterly operational cash burn (FCF &lt; $0).
          </span>
        </div>
      </div>

      <!-- 2D Sensitivity Grid (Revenue Shock vs Gross Margin Compression) -->
      <div class="space-y-3">
        <div class="flex items-center justify-between">
          <h3 class="text-xs font-semibold text-white flex items-center gap-2">
            <Sliders class="w-3.5 h-3.5 text-sky-400" />
            2D sensitivity matrix: pro-forma FCF vs margin compression
          </h3>
          <span class="text-xs text-slate-500 font-mono">Values in USD millions</span>
        </div>

        <div class="overflow-x-auto rounded-xl border border-white/5">
          <table class="w-full text-xs text-left">
            <thead class="bg-[#161b22] text-slate-400 text-xs font-medium border-b border-white/10">
              <tr>
                <th class="py-2.5 px-3 font-medium">Top-line shock \ Margin</th>
                <th class="py-2.5 px-3 text-right font-medium">0 bps</th>
                <th class="py-2.5 px-3 text-right font-medium">-200 bps</th>
                <th class="py-2.5 px-3 text-right font-medium">-400 bps</th>
                <th class="py-2.5 px-3 text-right font-medium">-600 bps</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-white/5 font-mono tabular-nums">
              <tr 
                v-for="row in simulationResult.sensitivity_matrix" 
                :key="row.revenue_shock_pct"
                class="hover:bg-slate-800/30 transition-colors"
              >
                <td class="py-2.5 px-3 font-semibold text-slate-300">
                  {{ row.revenue_shock_pct > 0 ? '+' : '' }}{{ row.revenue_shock_pct }}%
                </td>
                <td 
                  v-for="pt in row.points" 
                  :key="pt.margin_compression_bps"
                  class="py-2.5 px-3 text-right font-medium"
                  :class="pt.pro_forma_fcf < 0 
                    ? 'text-rose-400 bg-rose-950/20' 
                    : pt.pro_forma_fcf < simulationResult.baseline.free_cash_flow * 0.5 
                      ? 'text-amber-300 bg-amber-950/10' 
                      : 'text-emerald-400'"
                >
                  {{ formatUSD(pt.pro_forma_fcf) }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Institutional AI Forensic Commentary & Mitigation Playbook -->
      <div class="p-5 rounded-2xl bg-slate-900/60 border border-white/5 space-y-4">
        <div class="flex items-center justify-between border-b border-white/5 pb-3">
          <div class="flex items-center gap-2">
            <Sparkles class="w-4 h-4 text-emerald-400" />
            <h3 class="text-xs font-semibold text-white">
              Institutional credit rating and treasury playbook
            </h3>
          </div>

          <span 
            class="px-2 py-0.5 rounded-md text-xs font-medium border"
            :class="simulationResult.ai_commentary.capital_rating_impact === 'Severe Downgrade Risk'
              ? 'bg-rose-500/10 text-rose-300 border-rose-500/30'
              : simulationResult.ai_commentary.capital_rating_impact === 'Moderate Outlook Revision'
                ? 'bg-amber-500/10 text-amber-300 border-amber-500/30'
                : 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30'"
          >
            {{ simulationResult.ai_commentary.capital_rating_impact }}
          </span>
        </div>

        <p class="text-xs text-slate-300 leading-relaxed">
          {{ simulationResult.ai_commentary.executive_summary }}
        </p>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
          
          <!-- Vulnerabilities -->
          <div class="space-y-2 p-3.5 rounded-xl bg-slate-950/40 border border-white/5">
            <span class="text-xs font-semibold text-rose-400 flex items-center gap-1.5">
              <ShieldAlert class="w-3.5 h-3.5" />
              Identified Fragility Vectors
            </span>
            <ul class="space-y-1.5 text-[11px] text-slate-300">
              <li 
                v-for="(vuln, i) in simulationResult.ai_commentary.key_vulnerabilities" 
                :key="i"
                class="flex items-start gap-1.5"
              >
                <span class="text-rose-500 leading-none mt-1">▪</span>
                <span>{{ vuln }}</span>
              </li>
            </ul>
          </div>

          <!-- Hedging & Mitigations -->
          <div class="space-y-2 p-3.5 rounded-xl bg-slate-950/40 border border-white/5">
            <span class="text-xs font-semibold text-emerald-400 flex items-center gap-1.5">
              <ShieldCheck class="w-3.5 h-3.5" />
              Recommended Treasury & Supply-Chain Covenants
            </span>
            <ul class="space-y-1.5 text-[11px] text-slate-300">
              <li 
                v-for="(act, i) in simulationResult.ai_commentary.mitigation_actions" 
                :key="i"
                class="flex items-start gap-1.5"
              >
                <span class="text-emerald-500 leading-none mt-1">✓</span>
                <span>{{ act }}</span>
              </li>
            </ul>
          </div>

        </div>
      </div>

    </div>
  </div>
</template>

<style scoped>
.apple-card {
  background: rgba(15, 23, 42, 0.75);
  backdrop-filter: blur(24px) saturate(180%);
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.apple-press {
  transition: transform 0.18s cubic-bezier(0.32, 0.72, 0, 1), background-color 0.18s ease;
}

.apple-press:active {
  transform: scale(0.975);
}

@media (prefers-reduced-motion: reduce) {
  .apple-press {
    transition: none !important;
    transform: none !important;
  }
}
</style>
