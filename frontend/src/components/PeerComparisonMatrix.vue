<script setup>
import { ref, watch, onMounted } from 'vue'
import {
  Layers,
  TrendingDown,
  TrendingUp,
  AlertTriangle,
  ShieldAlert,
  CheckCircle2,
  Loader2,
  ExternalLink
} from 'lucide-vue-next'
import { formatEnum } from '../utils/ffi.js'

const props = defineProps({
  ticker: {
    type: String,
    default: 'NVDA'
  }
})

const emit = defineEmits(['select-ticker'])

const peerData = ref(null)
const isLoading = ref(true)
const errorMsg = ref('')

const fetchPeers = async (symbol) => {
  isLoading.value = true
  errorMsg.value = ''
  try {
    const res = await fetch(`/api/forensics/peers/${encodeURIComponent(symbol)}`)
    if (!res.ok) throw new Error('Failed to load sector peer benchmark')
    peerData.value = await res.json()
  } catch (err) {
    errorMsg.value = err.message
  } finally {
    isLoading.value = false
  }
}

watch(() => props.ticker, (newTicker) => {
  if (newTicker) fetchPeers(newTicker)
})

onMounted(() => {
  fetchPeers(props.ticker)
})

const riskTierBadge = (tier) => {
  switch (tier?.toUpperCase()) {
    case 'CRITICAL':
    case 'CRITICAL_ALERT':
      return 'bg-rose-500/20 text-rose-300 border-rose-500/30'
    case 'WATCHLIST':
      return 'bg-amber-500/20 text-amber-300 border-amber-500/30'
    default:
      return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
  }
}

const ffiColor = (score) => {
  if (score < 40) return 'text-emerald-400 font-bold'
  if (score < 70) return 'text-amber-400 font-bold'
  return 'text-rose-400 font-bold'
}
</script>

<template>
  <div class="apple-card rounded-3xl p-6 sm:p-7 space-y-6">
    <div class="flex flex-wrap items-center justify-between gap-4 border-b border-white/5 pb-4">
      <div>
        <h3 class="text-sm font-bold text-white tracking-tight flex items-center gap-2">
          Sector Peer Comparative Risk Matrix & Heatmap
          <span v-if="peerData" class="text-[10px] font-mono px-2 py-0.5 rounded-full bg-cyan-500/10 text-cyan-300 border border-cyan-500/20">
            {{ peerData.sector }}
          </span>
        </h3>
        <p class="text-xs text-slate-400 mt-0.5">
          Benchmarking Forensic Fragility (FFI), M-Score accruals, and disclosure vulnerabilities against direct competitors
        </p>
      </div>

      <div v-if="peerData" class="flex items-center gap-2 text-xs">
        <span class="text-slate-400">Sector Avg FFI:</span>
        <span class="font-mono font-bold text-slate-200 bg-slate-800 px-2 py-0.5 rounded-lg border border-white/10">
          {{ peerData.sector_average_ffi }} / 100
        </span>
      </div>
    </div>

    <div v-if="isLoading" class="h-44 flex items-center justify-center">
      <Loader2 class="w-6 h-6 animate-spin text-cyan-400" />
    </div>

    <div v-else-if="errorMsg" class="p-4 rounded-xl bg-white/[0.03] border border-white/10 flex items-center justify-between gap-4">
      <div class="flex items-center gap-2.5 text-xs text-slate-300">
        <AlertTriangle class="w-4 h-4 text-amber-400 shrink-0" />
        <span>{{ errorMsg }}. The analysis service may be offline.</span>
      </div>
      <button
        @click="fetchPeers(ticker)"
        class="apple-press shrink-0 text-xs font-medium px-3 py-1.5 rounded-lg border border-white/10 bg-slate-800/80 hover:bg-slate-700 text-slate-200 cursor-pointer"
      >
        Retry
      </button>
    </div>

    <div v-else-if="peerData" class="space-y-4">
      <!-- Heatmap Table -->
      <div class="overflow-x-auto rounded-2xl border border-white/5 bg-slate-950/60">
        <table class="w-full text-left text-xs text-slate-300">
          <thead class="bg-[#161b22] text-slate-400 text-xs font-medium border-b border-white/10">
            <tr>
              <th class="py-3 px-4 font-medium">Entity and ticker</th>
              <th class="py-3 px-3 font-medium">Market cap</th>
              <th class="py-3 px-3 font-medium">Fragility (FFI)</th>
              <th class="py-3 px-3 font-medium">Language drift</th>
              <th class="py-3 px-3 font-medium">Beneish M-Score</th>
              <th class="py-3 px-3 font-medium">Risk tier</th>
              <th class="py-3 px-4 font-medium">Key accounting vulnerability</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-white/5">
            <tr
              v-for="p in peerData.peers"
              :key="p.ticker"
              class="hover:bg-slate-800/40 transition-colors cursor-pointer group"
              :class="p.ticker === ticker.toUpperCase() ? 'bg-cyan-950/20 border-l-2 border-cyan-400' : ''"
              @click="emit('select-ticker', p.ticker)"
            >
              <td class="py-3 px-4 font-semibold text-white flex items-center gap-2">
                <span class="font-mono px-2 py-0.5 rounded bg-slate-800 border border-white/10 text-xs group-hover:border-cyan-400 transition-colors">
                  {{ p.ticker }}
                </span>
                <span class="truncate max-w-[140px] text-xs font-medium text-slate-300">{{ p.name }}</span>
              </td>
              <td class="py-3 px-3 font-mono tabular-nums text-slate-400">{{ p.market_cap }}</td>
              <td class="py-3 px-3 font-mono tabular-nums font-semibold" :class="ffiColor(p.ffi)">
                {{ p.ffi }}
              </td>
              <td class="py-3 px-3 font-mono tabular-nums text-slate-300">{{ p.drift_pct }}%</td>
              <td class="py-3 px-3 font-mono tabular-nums" :class="p.beneish_mscore > -1.78 ? 'text-rose-400 font-semibold' : 'text-emerald-400'">
                {{ p.beneish_mscore }}
              </td>
              <td class="py-3 px-3">
                <span class="px-2 py-0.5 rounded-md text-xs font-medium border" :class="riskTierBadge(p.risk_tier)">
                  {{ formatEnum(p.risk_tier) }}
                </span>
              </td>
              <td class="py-3 px-4 text-xs text-slate-400 max-w-sm truncate" :title="p.key_vulnerability">
                {{ p.key_vulnerability }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Sector Commentary Callout -->
      <div class="p-3.5 rounded-2xl bg-slate-900/60 border border-white/5 text-xs text-slate-300 flex items-start gap-3">
        <Layers class="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
        <p class="leading-relaxed">{{ peerData.sector_commentary }}</p>
      </div>
    </div>
  </div>
</template>
