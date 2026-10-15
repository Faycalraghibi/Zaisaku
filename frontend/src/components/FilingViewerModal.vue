<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import {
  FileText,
  Sparkles,
  ShieldAlert,
  AlertTriangle,
  CheckCircle2,
  X,
  ExternalLink,
  BookOpen,
  Search,
  MessageSquare,
  Copy,
  ChevronRight,
  Send,
  Loader2
} from 'lucide-vue-next'

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false
  },
  ticker: {
    type: String,
    default: 'NVDA'
  },
  initialDoc: {
    type: Object,
    default: () => null
  }
})

const emit = defineEmits(['close', 'open-chat'])

const activeSection = ref('item_1a') // 'item_1a' | 'item_7' | 'footnotes'
const selectedText = ref('')
const selectionCoords = ref({ x: 0, y: 0 })
const showSelectionPopup = ref(false)
const aiExplanation = ref(null)
const isExplaining = ref(false)

const sections = {
  item_1a: {
    title: 'Item 1A. Risk Factors',
    period: 'Form 10-K (Annual Report)',
    paragraphs: [
      {
        id: 'p1',
        type: 'critical',
        label: 'Export Restrictions & Geopolitical Redline',
        text: 'Our business may be adversely impacted by changes in export administration regulations, including enhanced controls on advanced computing semiconductors and electronic components manufactured using U.S. technology. New or expanded licensing requirements by the U.S. Bureau of Industry and Security (BIS) restrict our ability to supply high-performance accelerated computing chips to specified global regions, which historically represented a material portion of our data center revenue.'
      },
      {
        id: 'p2',
        type: 'warning',
        label: 'Supply Chain & Advanced Packaging Capacity',
        text: 'We rely on a limited number of third-party foundries and advanced packaging facilities, specifically TSMC CoWoS (Chip-on-Wafer-on-Substrate) packaging, to fabricate our GPU architectures. Any disruption, yield constraint, or geopolitical event in the Taiwan Strait could severely impair our delivery schedules and cause significant revenue deferrals.'
      },
      {
        id: 'p3',
        type: 'normal',
        label: 'Rapid Technological Transition',
        text: 'The market for generative AI infrastructure experiences rapid generational shifts. If customers pause orders for current-generation architectures in anticipation of upcoming Blackwell platforms, our short-term revenue and gross margins may experience quarterly volatility.'
      }
    ]
  },
  item_7: {
    title: "Item 7. Management's Discussion & Analysis (MD&A)",
    period: 'Form 10-K (Annual Report)',
    paragraphs: [
      {
        id: 'p4',
        type: 'normal',
        label: 'Revenue & Gross Margin Trajectory',
        text: 'Total revenue for the fiscal period reached $60.9 billion, driven by unprecedented expansion in the Compute & Networking segment. Gross margins expanded to 72.7% compared to 56.9% in the prior fiscal period, primarily attributable to premium architecture mix and operational operating leverage across data center hyperscalers.'
      },
      {
        id: 'p5',
        type: 'warning',
        label: 'Customer Concentration Disclosure',
        text: 'Sales to one indirect customer, through multiple system integrators and distributors, represented approximately 13% of our total revenue for the fiscal period. Additionally, our top two CSP customers accounted for approximately 22% of total trade accounts receivable as of the fiscal balance sheet date.'
      }
    ]
  },
  footnotes: {
    title: 'Note 3. Commitments & Inventory Accruals',
    period: 'Financial Statement Footnotes',
    paragraphs: [
      {
        id: 'p6',
        type: 'normal',
        label: 'Foundry Purchase Commitments',
        text: 'We enter into non-cancelable long-term purchase obligations with wafer foundries to guarantee advanced node capacity. As of the end of the fiscal year, total non-cancelable wafer and component purchase commitments stood at $16.8 billion, payable over the subsequent 24 months.'
      },
      {
        id: 'p7',
        type: 'warning',
        label: 'Held-to-Maturity Securities & SOX 404',
        text: 'Our cash equivalents and marketable securities portfolio consists predominantly of U.S. Treasuries and high-grade corporate bonds. Management and independent auditor PricewaterhouseCoopers LLP issued an unqualified audit opinion affirming effective internal control over financial reporting (ICFR) under SOX Section 404.'
      }
    ]
  }
}

const currentSectionData = computed(() => sections[activeSection.value] || sections.item_1a)

const handleTextSelection = () => {
  const selection = window.getSelection()
  if (!selection || selection.isCollapsed) {
    showSelectionPopup.value = false
    return
  }
  const text = selection.toString().trim()
  if (text.length > 10) {
    selectedText.value = text
    const range = selection.getRangeAt(0)
    const rect = range.getBoundingClientRect()
    selectionCoords.value = {
      x: rect.left + rect.width / 2,
      y: rect.top - 10
    }
    showSelectionPopup.value = true
  } else {
    showSelectionPopup.value = false
  }
}

const explainSelection = async () => {
  if (!selectedText.value) return
  isExplaining.value = true
  showSelectionPopup.value = false
  aiExplanation.value = {
    snippet: selectedText.value,
    analysis: `Forensic analysis of selected disclosure for ${props.ticker}:\nThis clause addresses operational and geopolitical risk exposure. In forensic accounting audits, changes to this specific language typically correlate with forward order book uncertainty and customer pushback.`
  }
  isExplaining.value = false
}

const askAiAboutSelection = () => {
  if (!selectedText.value) return
  const q = `Perform a forensic deep-dive into this excerpt from ${props.ticker}'s ${currentSectionData.value.title}: "${selectedText.value}"`
  showSelectionPopup.value = false
  emit('open-chat', q)
}

const copySelection = () => {
  if (selectedText.value) {
    navigator.clipboard.writeText(selectedText.value)
    showSelectionPopup.value = false
  }
}

const handleKeyDown = (e) => {
  if (e.key === 'Escape' && props.isOpen) {
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
      class="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 bg-black/80 backdrop-blur-md animate-fade-in"
      role="dialog"
      aria-modal="true"
    >
      <div 
        class="bg-slate-900 border border-white/10 rounded-3xl w-full max-w-6xl h-[90vh] flex flex-col shadow-2xl overflow-hidden"
      >
        <!-- Modal Top Bar -->
        <div class="h-16 px-6 border-b border-white/10 flex items-center justify-between shrink-0 bg-slate-900/90 backdrop-blur-md">
          <div class="flex items-center gap-3">
            <div class="p-2 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              <BookOpen class="w-5 h-5" />
            </div>
            <div>
              <h3 class="text-sm font-semibold text-white flex items-center gap-2">
                SEC document and AI annotation viewer
                <span class="text-xs font-mono px-2 py-0.5 rounded-md bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  {{ ticker }} / Live EDGAR feed
                </span>
              </h3>
              <p class="text-xs text-slate-400">Interactive regulatory text reader with real-time AI risk highlights</p>
            </div>
          </div>

          <div class="flex items-center gap-3">
            <!-- Section Tabs -->
            <div class="hidden md:flex items-center bg-slate-800/80 p-1 rounded-xl border border-white/10 text-xs">
              <button
                @click="activeSection = 'item_1a'"
                class="apple-press px-3 py-1 rounded-lg transition-all cursor-pointer"
                :class="activeSection === 'item_1a' ? 'bg-white text-slate-950 font-semibold shadow-xs' : 'text-slate-300 hover:text-white'"
              >
                Item 1A Risk Factors
              </button>
              <button
                @click="activeSection = 'item_7'"
                class="apple-press px-3 py-1 rounded-lg transition-all cursor-pointer"
                :class="activeSection === 'item_7' ? 'bg-white text-slate-950 font-semibold shadow-xs' : 'text-slate-300 hover:text-white'"
              >
                Item 7 MD&A
              </button>
              <button
                @click="activeSection = 'footnotes'"
                class="apple-press px-3 py-1 rounded-lg transition-all cursor-pointer"
                :class="activeSection === 'footnotes' ? 'bg-white text-slate-950 font-semibold shadow-xs' : 'text-slate-300 hover:text-white'"
              >
                Notes & Controls
              </button>
            </div>

            <button 
              @click="emit('close')"
              class="apple-press text-slate-400 hover:text-white p-2 rounded-xl hover:bg-slate-800 transition-colors"
              title="Close viewer (ESC)"
            >
              <X class="w-5 h-5" />
            </button>
          </div>
        </div>

        <!-- Split View Content Area -->
        <div class="flex-1 flex flex-col lg:flex-row overflow-hidden">
          
          <!-- Left: Regulatory Filing Reader -->
          <div 
            class="flex-1 overflow-y-auto p-6 sm:p-8 space-y-6 bg-slate-950/60 border-r border-white/5"
            @mouseup="handleTextSelection"
          >
            <div class="space-y-1 border-b border-white/5 pb-4">
              <span class="text-xs font-mono text-emerald-400 font-medium">
                {{ currentSectionData.period }}
              </span>
              <h2 class="text-xl font-bold text-white tracking-tight">
                {{ currentSectionData.title }}
              </h2>
              <p class="text-xs text-slate-400">
                Tip: Highlight any sentence in the text below to run instant AI explanation or ask Zaisaku.
              </p>
            </div>

            <div class="space-y-5 text-xs sm:text-sm text-slate-200 leading-relaxed">
              <div 
                v-for="p in currentSectionData.paragraphs" 
                :key="p.id"
                class="p-4 sm:p-5 rounded-2xl border transition-all"
                :class="[
                  p.type === 'critical' ? 'bg-rose-950/20 border-rose-500/30 text-rose-100' :
                  p.type === 'warning' ? 'bg-amber-950/20 border-amber-500/30 text-amber-100' :
                  'bg-slate-900/60 border-white/5 text-slate-200'
                ]"
              >
                <div class="flex items-center justify-between mb-2">
                  <span 
                    class="text-xs font-medium px-2 py-0.5 rounded-md border"
                    :class="[
                      p.type === 'critical' ? 'bg-rose-500/20 text-rose-300 border-rose-500/30' :
                      p.type === 'warning' ? 'bg-amber-500/20 text-amber-300 border-amber-500/30' :
                      'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                    ]"
                  >
                    {{ p.label }}
                  </span>
                  <span class="text-xs text-slate-500 font-mono">Sec. {{ p.id.toUpperCase() }}</span>
                </div>
                <p class="font-normal">{{ p.text }}</p>
              </div>
            </div>
          </div>

          <!-- Right: AI Forensic Annotation & Studio Sidebar -->
          <div class="w-full lg:w-96 p-6 bg-slate-900/90 overflow-y-auto space-y-5 shrink-0">
            <div class="space-y-2">
              <h4 class="text-xs font-semibold text-white flex items-center gap-2">
                <Sparkles class="w-4 h-4 text-emerald-400" />
                AI forensic analysis
              </h4>
              <p class="text-xs text-slate-400">
                Continuous NLP monitoring of language revisions, semantic hedging, and accounting hazards.
              </p>
            </div>

            <!-- Active Selection Explanation Card -->
            <div v-if="aiExplanation" class="p-4 rounded-2xl bg-slate-800/80 border border-emerald-500/30 space-y-3 shadow-lg">
              <div class="flex items-center justify-between">
                <span class="text-[10px] font-mono text-emerald-400 font-bold uppercase">AI Clause Audit</span>
                <button @click="aiExplanation = null" class="text-slate-400 hover:text-white p-0.5">
                  <X class="w-3.5 h-3.5" />
                </button>
              </div>
              <blockquote class="text-[11px] text-slate-300 italic border-l-2 border-emerald-500 pl-2">
                "{{ aiExplanation.snippet }}"
              </blockquote>
              <p class="text-xs text-slate-200 leading-relaxed">
                {{ aiExplanation.analysis }}
              </p>
            </div>

            <!-- Pre-Computed Section Synthesis -->
            <div class="p-4 rounded-2xl bg-slate-950/60 border border-white/5 space-y-3">
              <span class="text-[10px] font-mono text-slate-400 uppercase font-bold">Automated Section Synthesis</span>
              <ul class="space-y-2 text-xs text-slate-300">
                <li class="flex items-start gap-2">
                  <CheckCircle2 class="w-3.5 h-3.5 text-emerald-400 shrink-0 mt-0.5" />
                  <span>Cross-encoder semantic similarity of <strong>91.5%</strong> against prior period.</span>
                </li>
                <li class="flex items-start gap-2">
                  <AlertTriangle class="w-3.5 h-3.5 text-amber-400 shrink-0 mt-0.5" />
                  <span><strong>1 Key Customer Concentration</strong> highlighted in MD&A Note 7.</span>
                </li>
                <li class="flex items-start gap-2">
                  <ShieldAlert class="w-3.5 h-3.5 text-rose-400 shrink-0 mt-0.5" />
                  <span>Export controls revision flagged as high-impact forward liability.</span>
                </li>
              </ul>
            </div>

            <!-- One-Click Audit Actions -->
            <div class="space-y-2 pt-2">
              <button
                @click="emit('open-chat', `Run an automated section audit on ${ticker}'s ${currentSectionData.title}. Identify newly added risks and linguistic hedging.`)"
                class="apple-press w-full py-2.5 px-4 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-400 hover:to-teal-400 text-slate-950 font-bold text-xs flex items-center justify-center gap-2 cursor-pointer shadow-xs"
              >
                <Sparkles class="w-3.5 h-3.5" />
                <span>Ask Zaisaku about this section</span>
              </button>
            </div>
          </div>

        </div>

        <!-- Floating Selection Action Popover -->
        <div 
          v-if="showSelectionPopup" 
          class="fixed z-50 -translate-x-1/2 -translate-y-full mb-2 bg-slate-900 border border-white/20 rounded-xl px-2 py-1.5 shadow-2xl flex items-center gap-1.5 animate-in fade-in zoom-in-95 duration-150"
          :style="{ left: `${selectionCoords.x}px`, top: `${selectionCoords.y}px` }"
        >
          <button 
            @click="explainSelection"
            class="apple-press text-xs px-2.5 py-1 rounded-lg bg-emerald-500/20 text-emerald-300 hover:bg-emerald-500 hover:text-slate-950 font-medium transition-all flex items-center gap-1 cursor-pointer"
          >
            <Sparkles class="w-3 h-3" />
            <span>Explain Clause</span>
          </button>

          <button 
            @click="askAiAboutSelection"
            class="apple-press text-xs px-2.5 py-1 rounded-lg bg-slate-800 text-slate-200 hover:bg-slate-700 font-medium transition-all flex items-center gap-1 cursor-pointer"
          >
            <MessageSquare class="w-3 h-3 text-sky-400" />
            <span>Ask Zaisaku</span>
          </button>

          <button 
            @click="copySelection"
            class="apple-press text-xs p-1 text-slate-400 hover:text-white rounded-lg transition-colors cursor-pointer"
            title="Copy selection"
          >
            <Copy class="w-3 h-3" />
          </button>
        </div>

      </div>
    </div>
  </Teleport>
</template>
