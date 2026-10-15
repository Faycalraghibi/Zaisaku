<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import {
  Search,
  LayoutDashboard,
  BarChart3,
  TrendingUp,
  Activity,
  Scale,
  FileText,
  FileSearch,
  ShieldAlert,
  Download,
  Bot,
  AlertTriangle,
  Flame,
  CheckCircle2,
  Building2,
  Sparkles,
  Sliders,
  FolderOpen,
  Layers,
  Loader2
} from 'lucide-vue-next'

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false
  },
  currentTicker: {
    type: String,
    default: 'NVDA'
  }
})

const emit = defineEmits([
  'close',
  'select-workspace',
  'select-action',
  'select-ticker',
  'open-chat'
])

const searchQuery = ref('')
const selectedIndex = ref(0)
const searchInputRef = ref(null)

const workspaces = [
  { id: 'overview', label: 'Executive Dossier', desc: 'FFI Fragility Scorecard, Beneish M-Score & Anomaly Radar', icon: LayoutDashboard },
  { id: 'financials', label: 'Financials & Exhibits', desc: 'Multi-statement GAAP extracts and visual waterfall bridges', icon: BarChart3 },
  { id: 'benchmarks', label: 'Multi-Year & Peers', desc: '5-year forensic time-series and sector comparative matrix', icon: TrendingUp },
  { id: 'scenarios', label: 'Scenario Stress Lab', desc: 'AI macro shock engine and Monte Carlo simulation', icon: Activity },
  { id: 'interrogation', label: 'Audio & Inquiries', desc: 'Synchronized earnings call audio and auditor cross-examination', icon: Scale },
  { id: 'filings', label: 'Evidence Room', desc: 'Full-text SEC filing search, chunk inspection & doc ingestion', icon: FileText }
]

const institutionalActions = [
  { id: 'sec-import', label: 'Ingest SEC EDGAR Filing', desc: 'Ingest live Form 10-K / 10-Q from SEC EDGAR', icon: FileSearch },
  { id: 'beneish-mscore', label: 'Run 8-Factor Beneish M-Score', desc: 'Calculate manipulation index and accrual risk', icon: ShieldAlert },
  { id: 'auditor-studio', label: 'Launch Auditor Cross-Examiner', desc: 'Hostile SEC Enforcement & Big 4 audit simulator', icon: Scale },
  { id: 'stress-tester', label: 'Execute Macro Shock Stress Test', desc: 'Simulate stagflation or rate spikes with Monte Carlo', icon: Activity },
  { id: 'export-memo', label: 'Generate Due Diligence Memorandum', desc: 'Print-ready institutional audit report', icon: Download },
  { id: 'investigation-runner', label: 'Autonomous Forensic Agent', desc: 'Run 4-stage forensic agent investigation', icon: Bot },
  { id: 'filing-diff', label: 'Analyze Filing Language Drift', desc: 'Item 1A & Item 7 diff comparison', icon: FileText },
  { id: 'contradiction-radar', label: 'Earnings Call Tone Radar', desc: 'Detect guidance vs 10-Q contradictions', icon: AlertTriangle },
  { id: 'footnote-scan', label: 'Scan Footnote Accounting Hazards', desc: 'Detect off-balance sheet and related-party risks', icon: Flame },
  { id: 'rag-sandbox', label: 'AI Prompt & RAG Laboratory', desc: 'Benchmark temperature, chunks, and LLM providers', icon: Sliders }
]

const macroIndices = [
  { ticker: 'SPY', name: 'S&P 500 Large-Cap Core Benchmark', score: 'FFI 22', tier: 'CORE BENCHMARK', color: 'blue' },
  { ticker: 'QQQ', name: 'Invesco QQQ Nasdaq-100 Growth', score: 'FFI 25', tier: 'TECH BENCHMARK', color: 'blue' },
  { ticker: 'DIA', name: 'SPDR Dow Jones Industrial Average', score: 'FFI 19', tier: 'BLUE CHIP', color: 'blue' },
  { ticker: 'IWM', name: 'iShares Russell 2000 Small-Cap', score: 'FFI 44', tier: 'SMALL CAP', color: 'amber' },
  { ticker: 'SMH', name: 'VanEck Semiconductor Sector ETF', score: 'FFI 31', tier: 'SEMI BENCHMARK', color: 'purple' },
  { ticker: 'XLK', name: 'Technology Select Sector SPDR', score: 'FFI 22', tier: 'TECH SECTOR', color: 'blue' },
  { ticker: 'XLF', name: 'Financial Select Sector SPDR', score: 'FFI 27', tier: 'FINANCIALS', color: 'blue' }
]

const watchlistTickers = [
  { ticker: 'NVDA', name: 'NVIDIA Corporation', score: 'FFI 18', tier: 'LOW RISK', color: 'emerald' },
  { ticker: 'AAPL', name: 'Apple Inc.', score: 'FFI 14', tier: 'LOW RISK', color: 'emerald' },
  { ticker: 'MSFT', name: 'Microsoft Corporation', score: 'FFI 22', tier: 'LOW RISK', color: 'emerald' },
  { ticker: 'TSLA', name: 'Tesla, Inc.', score: 'FFI 42', tier: 'MODERATE', color: 'amber' },
  { ticker: 'AMZN', name: 'Amazon.com, Inc.', score: 'FFI 28', tier: 'LOW RISK', color: 'emerald' },
  { ticker: 'SMCI', name: 'Super Micro Computer, Inc.', score: 'FFI 84', tier: 'CRITICAL ALERT', color: 'rose' }
]

// Filtered categories
const filteredWorkspaces = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  if (!q) return workspaces
  return workspaces.filter(w => w.label.toLowerCase().includes(q) || w.desc.toLowerCase().includes(q))
})

const filteredIndices = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  if (!q) return macroIndices
  return macroIndices.filter(i => i.ticker.toLowerCase().includes(q) || i.name.toLowerCase().includes(q) || i.tier.toLowerCase().includes(q))
})

const filteredTickers = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  if (!q) return watchlistTickers
  return watchlistTickers.filter(t => t.ticker.toLowerCase().includes(q) || t.name.toLowerCase().includes(q))
})

const filteredActions = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  if (!q) return institutionalActions
  return institutionalActions.filter(a => a.label.toLowerCase().includes(q) || a.desc.toLowerCase().includes(q))
})

// Dynamic SEC EDGAR & Universal Ticker Search
const remoteResults = ref([])
const isSearchingRemote = ref(false)
let searchDebounceTimer = null

const performRemoteSearch = (query) => {
  if (searchDebounceTimer) clearTimeout(searchDebounceTimer)
  const q = query.trim()
  if (!q || q.length < 2) {
    remoteResults.value = []
    isSearchingRemote.value = false
    return
  }
  isSearchingRemote.value = true
  searchDebounceTimer = setTimeout(async () => {
    try {
      const res = await fetch(`/api/forensics/tickers/search?q=${encodeURIComponent(q)}&limit=6`)
      if (res.ok) {
        const data = await res.json()
        const existingSymbols = new Set([
          ...macroIndices.map(m => m.ticker),
          ...watchlistTickers.map(w => w.ticker)
        ])
        remoteResults.value = (data.results || []).filter(r => !existingSymbols.has(r.ticker))
      }
    } catch (e) {
      console.error('Remote directory search failed:', e)
    } finally {
      isSearchingRemote.value = false
    }
  }, 180)
}

watch(searchQuery, (newVal) => {
  performRemoteSearch(newVal)
})

// Unified flat list for arrow key navigation
const flattenedItems = computed(() => {
  const items = []
  
  // Ask AI option when search query is present
  if (searchQuery.value.trim().length > 1) {
    items.push({
      type: 'ai-prompt',
      id: 'ai-prompt',
      label: `Ask AI Co-Analyst: "${searchQuery.value.trim()}"`,
      desc: 'Query vector database and indexed financial filings with frontier LLM',
      icon: Sparkles
    })
  }

  filteredWorkspaces.value.forEach(w => {
    items.push({ type: 'workspace', ...w })
  })

  filteredIndices.value.forEach(i => {
    items.push({
      type: 'ticker',
      ticker: i.ticker,
      name: i.name,
      score: i.score,
      tier: i.tier,
      color: i.color,
      label: `${i.ticker} • ${i.name}`,
      desc: `${i.score} (${i.tier})`
    })
  })

  filteredTickers.value.forEach(t => {
    items.push({ type: 'ticker', ...t, label: `${t.ticker} • ${t.name}`, desc: `${t.score} (${t.tier})` })
  })

  remoteResults.value.forEach(r => {
    const tier = r.risk_tier.replace('_', ' ')
    items.push({
      type: 'ticker',
      ticker: r.ticker,
      name: r.name,
      score: `FFI ${Math.round(r.ffi_score)}`,
      tier: tier,
      color: r.risk_tier === 'CRITICAL_ALERT' ? 'rose' : (r.risk_tier === 'ELEVATED_WATCH' ? 'amber' : 'emerald'),
      label: `${r.ticker} • ${r.name}`,
      desc: `${r.sector} (${r.exchange})`
    })
  })

  filteredActions.value.forEach(a => {
    items.push({ type: 'action', ...a })
  })

  return items
})

watch(() => props.isOpen, (open) => {
  if (open) {
    searchQuery.value = ''
    selectedIndex.value = 0
    nextTick(() => {
      searchInputRef.value?.focus()
    })
  }
})

const scrollContainerRef = ref(null)

const scrollToActiveItem = () => {
  nextTick(() => {
    const activeEl = scrollContainerRef.value?.querySelector('[data-active="true"]')
    if (activeEl) {
      activeEl.scrollIntoView({ block: 'nearest', behavior: 'smooth' })
    }
  })
}

watch(selectedIndex, () => {
  scrollToActiveItem()
})

const executeItem = (item) => {
  if (!item) return

  if (item.type === 'ai-prompt') {
    emit('open-chat', searchQuery.value.trim())
    emit('close')
  } else if (item.type === 'workspace') {
    emit('select-workspace', item.id)
    emit('close')
  } else if (item.type === 'action') {
    emit('select-action', item.id)
    emit('close')
  } else if (item.type === 'ticker') {
    emit('select-ticker', item.ticker)
    emit('close')
  }
}

const handleKeyDown = (e) => {
  if (!props.isOpen) return

  if (e.key === 'Escape') {
    e.preventDefault()
    emit('close')
  } else if (e.key === 'ArrowDown') {
    e.preventDefault()
    if (flattenedItems.value.length > 0) {
      selectedIndex.value = (selectedIndex.value + 1) % flattenedItems.value.length
    }
  } else if (e.key === 'ArrowUp') {
    e.preventDefault()
    if (flattenedItems.value.length > 0) {
      selectedIndex.value = (selectedIndex.value - 1 + flattenedItems.value.length) % flattenedItems.value.length
    }
  } else if (e.key === 'Enter') {
    e.preventDefault()
    if (flattenedItems.value[selectedIndex.value]) {
      executeItem(flattenedItems.value[selectedIndex.value])
    }
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
      class="fixed inset-0 z-50 flex items-start justify-center pt-20 px-4 bg-black/70 backdrop-blur-xl animate-fadeIn"
      @click.self="emit('close')"
    >
      <div 
        class="apple-spotlight-modal w-full max-w-2xl rounded-2xl shadow-2xl overflow-hidden flex flex-col border border-white/10"
        @click.stop
      >
        <!-- Apple Spotlight Search Header -->
        <div class="relative flex items-center px-4 py-3.5 border-b border-white/10 bg-slate-900/90">
          <Search class="w-5 h-5 text-slate-400 mr-3 shrink-0" />
          <input
            ref="searchInputRef"
            v-model="searchQuery"
            type="text"
            placeholder="Search commands, filings, metrics, or jump to workspace..."
            class="w-full bg-transparent text-sm sm:text-base text-white placeholder-slate-400 focus:outline-none"
          />
          <div class="flex items-center gap-1.5 shrink-0 ml-2">
            <kbd class="px-1.5 py-0.5 text-[10px] font-mono text-slate-400 bg-slate-800 rounded border border-white/10">ESC</kbd>
          </div>
        </div>

        <!-- Scrollable Command Results Area -->
        <div ref="scrollContainerRef" class="max-h-[60vh] overflow-y-auto p-2 space-y-4 custom-scrollbar bg-slate-950/80">
          
          <!-- AI Co-Analyst Quick Query Option (if query exists) -->
          <div v-if="searchQuery.trim().length > 1" class="space-y-1">
            <div class="px-2 pt-1 pb-1 text-xs font-semibold text-slate-400">
              AI Co-Analyst direct inquiry
            </div>
            <div
              @click="executeItem(flattenedItems[0])"
              @mouseenter="selectedIndex = 0"
              class="flex items-center justify-between p-2.5 rounded-xl cursor-pointer transition-all duration-150"
              :class="selectedIndex === 0 ? 'bg-indigo-600/25 border border-indigo-500/40 text-white' : 'text-slate-300 hover:bg-white/5 border border-transparent'"
              :data-active="selectedIndex === 0"
            >
              <div class="flex items-center gap-3">
                <div class="p-2 rounded-lg bg-indigo-500/20 text-indigo-400 border border-indigo-500/30">
                  <Sparkles class="w-4 h-4" />
                </div>
                <div>
                  <div class="text-sm font-medium text-white flex items-center gap-2">
                    Ask AI Co-Analyst: <span class="text-indigo-300 font-semibold italic">"{{ searchQuery.trim() }}"</span>
                  </div>
                  <div class="text-xs text-slate-400">Query vector index and financial filings with citations</div>
                </div>
              </div>
              <kbd v-if="selectedIndex === 0" class="px-1.5 py-0.5 font-mono text-[10px] bg-white/10 rounded border border-white/15 text-slate-300">↵</kbd>
            </div>
          </div>

          <!-- Workspaces & Views -->
          <div v-if="filteredWorkspaces.length > 0" class="space-y-1">
            <div class="px-2 pt-1 pb-1 text-xs font-semibold text-slate-400 flex items-center gap-1.5">
              <FolderOpen class="w-3.5 h-3.5" />
              <span>Workspace views</span>
            </div>
            <div
              v-for="item in filteredWorkspaces"
              :key="item.id"
              @click="executeItem({ type: 'workspace', ...item })"
              @mouseenter="selectedIndex = flattenedItems.findIndex(i => i.type === 'workspace' && i.id === item.id)"
              class="flex items-center justify-between p-2.5 rounded-xl cursor-pointer transition-all duration-150"
              :class="selectedIndex === flattenedItems.findIndex(i => i.type === 'workspace' && i.id === item.id) ? 'bg-blue-600/20 border border-blue-500/40 text-white' : 'text-slate-300 hover:bg-white/5 border border-transparent'"
              :data-active="selectedIndex === flattenedItems.findIndex(i => i.type === 'workspace' && i.id === item.id)"
            >
              <div class="flex items-center gap-3">
                <div class="p-2 rounded-lg bg-slate-800 text-slate-300 border border-white/5">
                  <component :is="item.icon" class="w-4 h-4" />
                </div>
                <div>
                  <div class="text-sm font-medium text-white">{{ item.label }}</div>
                  <div class="text-xs text-slate-400">{{ item.desc }}</div>
                </div>
              </div>
              <span class="text-xs font-medium text-slate-500">View</span>
            </div>
          </div>

          <!-- Macro Market Indices & Benchmarks -->
          <div v-if="filteredIndices.length > 0" class="space-y-1">
            <div class="px-2 pt-1 pb-1 text-xs font-semibold text-slate-400 flex items-center gap-1.5">
              <Layers class="w-3.5 h-3.5 text-blue-400" />
              <span>Macro market indices and sector ETFs</span>
            </div>
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-1.5">
              <div
                v-for="item in filteredIndices"
                :key="item.ticker"
                @click="executeItem({ type: 'ticker', ...item })"
                @mouseenter="selectedIndex = flattenedItems.findIndex(i => i.type === 'ticker' && i.ticker === item.ticker)"
                class="flex items-center justify-between p-2 rounded-xl cursor-pointer transition-all duration-150"
                :class="selectedIndex === flattenedItems.findIndex(i => i.type === 'ticker' && i.ticker === item.ticker) ? 'bg-blue-600/20 border border-blue-500/30 text-white' : 'text-slate-300 bg-slate-900/40 hover:bg-white/5 border border-white/5'"
                :data-active="selectedIndex === flattenedItems.findIndex(i => i.type === 'ticker' && i.ticker === item.ticker)"
              >
                <div class="flex items-center gap-2.5">
                  <span class="font-mono font-bold text-xs px-2 py-0.5 rounded bg-blue-500/20 text-blue-300 border border-blue-500/30">
                    {{ item.ticker }}
                  </span>
                  <div class="truncate text-xs font-medium text-slate-200">
                    {{ item.name }}
                  </div>
                </div>
                <div class="shrink-0 flex items-center gap-1.5">
                  <span class="text-[10px] tabular-nums font-semibold px-1.5 py-0.5 rounded border bg-blue-500/10 text-blue-300 border-blue-500/20">
                    {{ item.score }}
                  </span>
                </div>
              </div>
            </div>
          </div>

          <!-- Watchlist Tickers -->
          <div v-if="filteredTickers.length > 0" class="space-y-1">
            <div class="px-2 pt-1 pb-1 text-xs font-semibold text-slate-400 flex items-center gap-1.5">
              <Building2 class="w-3.5 h-3.5" />
              <span>Watchlist tickers</span>
            </div>
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-1.5">
              <div
                v-for="item in filteredTickers"
                :key="item.ticker"
                @click="executeItem({ type: 'ticker', ...item })"
                @mouseenter="selectedIndex = flattenedItems.findIndex(i => i.type === 'ticker' && i.ticker === item.ticker)"
                class="flex items-center justify-between p-2 rounded-xl cursor-pointer transition-all duration-150"
                :class="selectedIndex === flattenedItems.findIndex(i => i.type === 'ticker' && i.ticker === item.ticker) ? 'bg-white/10 border border-white/20 text-white' : 'text-slate-300 bg-slate-900/40 hover:bg-white/5 border border-white/5'"
                :data-active="selectedIndex === flattenedItems.findIndex(i => i.type === 'ticker' && i.ticker === item.ticker)"
              >
                <div class="flex items-center gap-2.5">
                  <span class="font-mono font-bold text-xs px-2 py-1 rounded bg-slate-800 text-slate-200 border border-white/10">
                    {{ item.ticker }}
                  </span>
                  <div class="truncate text-xs font-medium text-slate-200">
                    {{ item.name }}
                  </div>
                </div>
                <div class="shrink-0 flex items-center gap-1.5">
                  <span 
                    class="text-[10px] tabular-nums font-semibold px-1.5 py-0.5 rounded border"
                    :class="item.color === 'rose' ? 'bg-rose-500/10 text-rose-400 border-rose-500/20' : item.color === 'amber' ? 'bg-amber-500/10 text-amber-400 border-amber-500/20' : 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'"
                  >
                    {{ item.score }}
                  </span>
                </div>
              </div>
            </div>
          </div>

          <!-- Dynamic SEC EDGAR Directory Search Results -->
          <div v-if="remoteResults.length > 0 || isSearchingRemote" class="space-y-1">
            <div class="px-2 pt-1 pb-1 text-xs font-semibold text-slate-400 flex items-center justify-between">
              <div class="flex items-center gap-1.5">
                <Search class="w-3.5 h-3.5 text-emerald-400" />
                <span>SEC EDGAR universe autocomplete</span>
              </div>
              <div v-if="isSearchingRemote" class="flex items-center gap-1 text-[10px] text-emerald-400 font-mono">
                <Loader2 class="w-3 h-3 animate-spin" />
                <span>Searching SEC...</span>
              </div>
            </div>
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-1.5">
              <div
                v-for="item in remoteResults"
                :key="item.ticker"
                @click="executeItem({ type: 'ticker', ticker: item.ticker })"
                @mouseenter="selectedIndex = flattenedItems.findIndex(i => i.type === 'ticker' && i.ticker === item.ticker)"
                class="flex items-center justify-between p-2 rounded-xl cursor-pointer transition-all duration-150"
                :class="selectedIndex === flattenedItems.findIndex(i => i.type === 'ticker' && i.ticker === item.ticker) ? 'bg-emerald-500/20 border border-emerald-500/30 text-white' : 'text-slate-300 bg-slate-900/40 hover:bg-white/5 border border-white/5'"
                :data-active="selectedIndex === flattenedItems.findIndex(i => i.type === 'ticker' && i.ticker === item.ticker)"
              >
                <div class="flex items-center gap-2.5 min-w-0">
                  <span class="font-mono font-bold text-xs px-2 py-0.5 rounded bg-emerald-500/15 text-emerald-300 border border-emerald-500/20 shrink-0">
                    {{ item.ticker }}
                  </span>
                  <div class="truncate text-xs font-medium text-slate-200">
                    <div class="truncate">{{ item.name }}</div>
                    <div class="text-[10px] text-slate-500 truncate">{{ item.sector }}</div>
                  </div>
                </div>
                <div class="shrink-0 flex items-center gap-1.5 ml-2">
                  <span class="text-[10px] font-mono px-1.5 py-0.5 rounded bg-white/5 text-slate-400 border border-white/10">
                    CIK {{ item.cik }}
                  </span>
                </div>
              </div>
            </div>
          </div>

          <!-- Institutional Actions -->
          <div v-if="filteredActions.length > 0" class="space-y-1">
            <div class="px-2 pt-1 pb-1 text-xs font-semibold text-slate-400 flex items-center gap-1.5">
              <Activity class="w-3.5 h-3.5" />
              <span>Institutional forensic actions</span>
            </div>
            <div
              v-for="item in filteredActions"
              :key="item.id"
              @click="executeItem({ type: 'action', ...item })"
              @mouseenter="selectedIndex = flattenedItems.findIndex(i => i.type === 'action' && i.id === item.id)"
              class="flex items-center justify-between p-2.5 rounded-xl cursor-pointer transition-all duration-150"
              :class="selectedIndex === flattenedItems.findIndex(i => i.type === 'action' && i.id === item.id) ? 'bg-emerald-600/20 border border-emerald-500/40 text-white' : 'text-slate-300 hover:bg-white/5 border border-transparent'"
              :data-active="selectedIndex === flattenedItems.findIndex(i => i.type === 'action' && i.id === item.id)"
            >
              <div class="flex items-center gap-3">
                <div class="p-2 rounded-lg bg-slate-800 text-slate-300 border border-white/5">
                  <component :is="item.icon" class="w-4 h-4" />
                </div>
                <div>
                  <div class="text-sm font-medium text-white">{{ item.label }}</div>
                  <div class="text-xs text-slate-400">{{ item.desc }}</div>
                </div>
              </div>
              <kbd v-if="selectedIndex === flattenedItems.findIndex(i => i.type === 'action' && i.id === item.id)" class="px-1.5 py-0.5 font-mono text-[10px] bg-white/10 rounded border border-white/15 text-slate-300">↵</kbd>
            </div>
          </div>

          <!-- Empty State -->
          <div v-if="flattenedItems.length === 0" class="py-12 text-center text-slate-400">
            <Search class="w-8 h-8 mx-auto mb-2 text-slate-500 opacity-60" />
            <p class="text-sm font-medium">No matching commands or filings found</p>
            <p class="text-xs text-slate-500 mt-1">Try searching for "Beneish", "10-K", "Stress", "NVDA", or "Audio"</p>
          </div>

        </div>

        <!-- Apple Spotlight Footer Bar -->
        <div class="px-4 py-2.5 border-t border-white/10 bg-slate-900/90 text-[11px] text-slate-400 flex items-center justify-between">
          <div class="flex items-center gap-3">
            <span class="flex items-center gap-1">
              <kbd class="px-1.5 py-0.5 font-mono text-[10px] bg-slate-800 rounded border border-white/10">↑</kbd>
              <kbd class="px-1.5 py-0.5 font-mono text-[10px] bg-slate-800 rounded border border-white/10">↓</kbd>
              Navigate
            </span>
            <span class="flex items-center gap-1">
              <kbd class="px-1.5 py-0.5 font-mono text-[10px] bg-slate-800 rounded border border-white/10">↵</kbd>
              Execute
            </span>
          </div>
          <div class="flex items-center gap-1.5 font-mono text-slate-400">
            <span class="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
            <span>ZAISAKU SPOTLIGHT</span>
          </div>
        </div>

      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.apple-spotlight-modal {
  background: rgba(13, 19, 31, 0.88);
  backdrop-filter: blur(32px) saturate(200%);
}

.custom-scrollbar::-webkit-scrollbar {
  width: 5px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.02);
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.12);
  border-radius: 9999px;
}
</style>
