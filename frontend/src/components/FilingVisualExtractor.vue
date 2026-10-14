<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import {
  BarChart3,
  PieChart,
  Layers,
  AlertTriangle,
  ShieldAlert,
  ArrowRight,
  TrendingUp,
  Globe,
  Loader2,
  CheckCircle2,
  Info
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

const isLoading = ref(false)
const visualData = ref(null)
const activeExhibitId = ref(null)
const hoveredStep = ref(null)

const fetchVisuals = async () => {
  isLoading.value = true
  try {
    const res = await fetch(`/api/forensics/visuals/${props.ticker}`)
    if (res.ok) {
      visualData.value = await res.json()
      if (visualData.value.exhibits?.length > 0) {
        activeExhibitId.value = visualData.value.exhibits[0].id
      }
    }
  } catch (err) {
    console.error('Failed to load visual exhibits:', err)
  } finally {
    isLoading.value = false
  }
}

watch(() => props.ticker, () => {
  fetchVisuals()
})

onMounted(() => {
  fetchVisuals()
})

const currentExhibit = computed(() => {
  if (!visualData.value?.exhibits) return null
  return visualData.value.exhibits.find(e => e.id === activeExhibitId.value) || visualData.value.exhibits[0]
})

const maxStepValue = computed(() => {
  if (!currentExhibit.value?.steps) return 1
  return Math.max(...currentExhibit.value.steps.map(s => s.value), 1)
})

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
      <div class="flex items-center gap-2.5">
        <div class="p-2 rounded-xl bg-sky-500/10 text-sky-400 border border-sky-500/20">
          <BarChart3 class="w-4 h-4" />
        </div>
        <div>
          <h2 class="text-base font-bold text-white tracking-tight flex items-center gap-2">
            SEC Visual Exhibit & Reconciliation Studio
            <span class="text-[10px] font-mono px-2 py-0.5 rounded-full bg-sky-500/10 text-sky-300 border border-sky-500/20">
              ASC 606 & Non-GAAP
            </span>
          </h2>
          <p class="text-xs text-slate-400">
            Interactive GAAP-to-Non-GAAP reconciliation waterfall bridges, sovereign geographic billing exposure, and segment margins
          </p>
        </div>
      </div>

      <!-- Exhibit Switcher Tabs -->
      <div v-if="visualData?.exhibits" class="flex flex-wrap gap-1.5 p-1 rounded-xl bg-slate-950/60 border border-white/5">
        <button
          v-for="exhibit in visualData.exhibits"
          :key="exhibit.id"
          @click="activeExhibitId = exhibit.id"
          class="apple-press px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer flex items-center gap-1.5"
          :class="activeExhibitId === exhibit.id 
            ? 'bg-sky-500/20 text-sky-300 border border-sky-500/30 shadow-xs' 
            : 'text-slate-400 hover:text-slate-200'"
        >
          <Layers v-if="exhibit.exhibit_type === 'waterfall_bridge'" class="w-3 h-3 text-sky-400" />
          <Globe v-else-if="exhibit.exhibit_type === 'geographic_exposure'" class="w-3 h-3 text-emerald-400" />
          <BarChart3 v-else class="w-3 h-3 text-purple-400" />
          <span>{{ exhibit.title }}</span>
        </button>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="isLoading" class="p-16 flex flex-col items-center justify-center space-y-3">
      <Loader2 class="w-8 h-8 animate-spin text-sky-500" />
      <span class="text-xs text-slate-400 font-mono">Extracting structural visual exhibits and reconciliation bridges...</span>
    </div>

    <!-- Active Exhibit Display -->
    <div v-else-if="currentExhibit" class="space-y-6">
      
      <!-- Exhibit Meta Bar -->
      <div class="flex flex-wrap items-center justify-between gap-3 text-xs bg-slate-950/40 p-3 rounded-xl border border-white/5">
        <div class="flex items-center gap-3">
          <span class="text-slate-400 font-mono">Source: <strong class="text-slate-200">{{ currentExhibit.filing_source }}</strong></span>
          <span>·</span>
          <span class="text-slate-400 font-mono">Period: <strong class="text-slate-200">{{ currentExhibit.fiscal_period }}</strong></span>
        </div>

        <div v-if="currentExhibit.non_gaap_divergence_pct" class="flex items-center gap-2">
          <span class="text-[11px] font-mono text-slate-400">Non-GAAP Divergence:</span>
          <span class="px-2 py-0.5 rounded-md text-[11px] font-mono font-bold bg-amber-500/10 text-amber-300 border border-amber-500/20">
            +{{ currentExhibit.non_gaap_divergence_pct }}%
          </span>
        </div>
      </div>

      <!-- VIEW 1: Waterfall Bridge Renderer -->
      <div v-if="currentExhibit.exhibit_type === 'waterfall_bridge' || currentExhibit.exhibit_type === 'segment_waterfall'" class="space-y-4">
        
        <!-- Interactive Waterfall Bar Graphic -->
        <div class="p-6 rounded-2xl bg-slate-950/80 border border-white/5 space-y-4">
          <div class="h-56 w-full flex items-end justify-between gap-3 pt-6 pb-2 px-4 relative">
            
            <div
              v-for="step in currentExhibit.steps"
              :key="step.label"
              @mouseenter="hoveredStep = step"
              @mouseleave="hoveredStep = null"
              class="flex-1 flex flex-col items-center justify-end h-full gap-2 group cursor-pointer"
            >
              <!-- Step Value Label -->
              <span class="text-[11px] font-mono font-bold transition-transform group-hover:scale-105"
                :class="step.is_total 
                  ? 'text-white' 
                  : step.step_type === 'positive' 
                    ? 'text-sky-400' 
                    : 'text-rose-400'"
              >
                {{ step.step_type === 'positive' && !step.is_total ? '+' : '' }}{{ formatUSD(step.value) }}
              </span>

              <!-- Column Bar -->
              <div 
                class="w-full rounded-t-lg transition-all"
                :class="step.is_total
                  ? 'bg-gradient-to-t from-slate-700 to-slate-500 group-hover:from-slate-600 group-hover:to-slate-400'
                  : step.step_type === 'positive'
                    ? 'bg-gradient-to-t from-sky-600/70 to-sky-400 group-hover:from-sky-500 group-hover:to-sky-300'
                    : 'bg-gradient-to-t from-rose-600/70 to-rose-400 group-hover:from-rose-500 group-hover:to-rose-300'"
                :style="{ height: `${Math.max(12, (step.value / maxStepValue) * 85)}%` }"
              ></div>

              <!-- Step Bottom Label -->
              <span class="text-[10px] text-slate-400 font-medium text-center line-clamp-2 h-7 leading-tight">
                {{ step.label }}
              </span>
            </div>

          </div>

          <!-- Step Detail Hover Commentary -->
          <div 
            v-if="hoveredStep" 
            class="p-3 rounded-xl bg-slate-900 border border-white/10 text-xs flex items-center justify-between gap-3 text-slate-200"
          >
            <div class="flex items-center gap-2">
              <Info class="w-4 h-4 text-sky-400 shrink-0" />
              <span><strong>{{ hoveredStep.label }}:</strong> {{ hoveredStep.commentary }}</span>
            </div>
            <span class="font-mono font-bold text-sky-300 shrink-0">{{ formatUSD(hoveredStep.value) }}</span>
          </div>
        </div>

        <!-- Audit Warning Callout -->
        <div 
          v-if="currentExhibit.audit_warning" 
          class="p-4 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-300 text-xs flex items-start gap-3"
        >
          <AlertTriangle class="w-4 h-4 shrink-0 text-amber-400 mt-0.5" />
          <div class="space-y-1">
            <span class="font-bold">PCAOB & SEC Non-GAAP Audit Finding:</span>
            <p class="leading-relaxed">{{ currentExhibit.audit_warning }}</p>
          </div>
        </div>

      </div>

      <!-- VIEW 2: Geographic Exposure Renderer -->
      <div v-else-if="currentExhibit.exhibit_type === 'geographic_exposure'" class="space-y-4">
        
        <div class="p-6 rounded-2xl bg-slate-950/80 border border-white/5 space-y-5">
          <div class="space-y-3">
            <div 
              v-for="slice_ in currentExhibit.pie_slices" 
              :key="slice_.region"
              class="space-y-1.5"
            >
              <div class="flex items-center justify-between text-xs">
                <div class="flex items-center gap-2">
                  <span class="font-semibold text-white">{{ slice_.region }}</span>
                  <span 
                    v-if="slice_.risk_level.includes('SANCTION') || slice_.risk_level.includes('CONCENTRATION')"
                    class="text-[9px] font-mono px-1.5 py-0.5 rounded bg-rose-500/10 text-rose-300 border border-rose-500/20 font-bold"
                  >
                    {{ slice_.risk_level }}
                  </span>
                  <span 
                    v-else-if="slice_.risk_level.includes('REGULATORY') || slice_.risk_level.includes('COMPETITIVE')"
                    class="text-[9px] font-mono px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-300 border border-amber-500/20 font-bold"
                  >
                    {{ slice_.risk_level }}
                  </span>
                </div>

                <div class="flex items-center gap-3 font-mono">
                  <span class="text-slate-400">{{ formatUSD(slice_.revenue_m) }}</span>
                  <span class="font-bold text-emerald-400 w-12 text-right">{{ slice_.percentage }}%</span>
                </div>
              </div>

              <!-- Horizontal Progress Bar -->
              <div class="h-2 w-full rounded-full bg-slate-800 overflow-hidden">
                <div 
                  class="h-full rounded-full transition-all duration-500"
                  :class="slice_.risk_level.includes('SANCTION') 
                    ? 'bg-rose-500' 
                    : slice_.risk_level.includes('REGULATORY') || slice_.risk_level.includes('CONCENTRATION') 
                      ? 'bg-amber-500' 
                      : 'bg-emerald-500'"
                  :style="{ width: `${slice_.percentage}%` }"
                ></div>
              </div>
            </div>
          </div>
        </div>

        <!-- Audit Warning Callout for Geographic Exposure -->
        <div 
          v-if="currentExhibit.audit_warning" 
          class="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-start gap-3"
        >
          <ShieldAlert class="w-4 h-4 shrink-0 text-rose-400 mt-0.5" />
          <div class="space-y-1">
            <span class="font-bold">Sovereign Regulatory Exposure Finding:</span>
            <p class="leading-relaxed">{{ currentExhibit.audit_warning }}</p>
          </div>
        </div>

      </div>

      <!-- Executive Visual Audit Synthesis -->
      <div class="p-4 rounded-xl bg-slate-900/60 border border-white/5 text-xs text-slate-300 leading-relaxed">
        <strong class="text-white block mb-1">Visual Audit Takeaway:</strong>
        {{ visualData.executive_summary }}
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
