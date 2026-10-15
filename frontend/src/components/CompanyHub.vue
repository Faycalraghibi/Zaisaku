<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import {
  ShieldAlert,
  GitCompare,
  Calculator,
  Radio,
  FileText,
  Globe,
  UploadCloud,
  Loader2,
  ExternalLink,
  Trash2,
  Sparkles,
  Download,
  Search,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  TrendingDown,
  TrendingUp,
  Sliders,
  Layers,
  FileCheck,
  Building2,
  Calendar,
  X,
  Terminal,
  Play,
  BookOpen,
  Cpu,
  Scale,
  BarChart3,
  Activity,
  ChevronRight,
  Clock,
  Printer
} from 'lucide-vue-next'

import FilingDiffModal from './FilingDiffModal.vue'
import ForensicMScoreModal from './ForensicMScoreModal.vue'
import ContradictionRadarModal from './ContradictionRadarModal.vue'
import ForensicScorecardModal from './ForensicScorecardModal.vue'
import FinancialTrendsChart from './FinancialTrendsChart.vue'
import FilingViewerModal from './FilingViewerModal.vue'
import ForensicInvestigationRunner from './ForensicInvestigationRunner.vue'
import PeerComparisonMatrix from './PeerComparisonMatrix.vue'
import FinancialTableExtractor from './FinancialTableExtractor.vue'
import AudioCallSimulator from './AudioCallSimulator.vue'
import ForensicSandboxModal from './ForensicSandboxModal.vue'
import InstitutionalReportModal from './InstitutionalReportModal.vue'
import ScenarioStressTester from './ScenarioStressTester.vue'
import FilingVisualExtractor from './FilingVisualExtractor.vue'
import AuditorCrossExaminerModal from './AuditorCrossExaminerModal.vue'

const emit = defineEmits(['open-chat', 'document-count-change'])

// --- Active Navigation Tab ---
const currentTab = ref('overview')
const navigationTabs = [
  { id: 'overview', label: 'Executive Dossier', icon: ShieldAlert },
  { id: 'financials', label: 'Financials & Exhibits', icon: BarChart3 },
  { id: 'benchmarks', label: 'Multi-Year & Peers', icon: TrendingUp },
  { id: 'scenarios', label: 'Scenario Stress Lab', icon: Activity, badge: '1k Runs' },
  { id: 'interrogation', label: 'Audio & Inquiries', icon: Scale },
  { id: 'filings', label: 'Evidence Room', icon: FileText }
]

// --- Modal Visibility States ---
const showDiffModal = ref(false)
const showMScoreModal = ref(false)
const showRadarModal = ref(false)
const showScorecardModal = ref(false)
const showSecModal = ref(false)
const showDeleteModal = ref(false)
const showFilingViewerModal = ref(false)
const showInvestigationRunner = ref(false)
const showSandboxModal = ref(false)
const showInstitutionalReportModal = ref(false)
const showAuditorModal = ref(false)
const selectedDocForViewer = ref(null)

const openFilingViewer = (doc = null) => {
  selectedDocForViewer.value = doc
  showFilingViewerModal.value = true
}

// --- Active Company State & Presets ---
const searchInput = ref('NVDA')
const isSearching = ref(false)

const companyProfiles = {
  NVDA: {
    ticker: 'NVDA',
    name: 'NVIDIA Corporation',
    exchange: 'NASDAQ',
    cik: '0001045810',
    sector: 'Semiconductors & AI Hardware',
    period: 'FY2024 / Q3 FY2025 Form 10-K & 10-Q',
    auditor: 'PricewaterhouseCoopers LLP',
    ffi: 18,
    riskTier: 'LOW_RISK',
    driftScore: 8.5,
    driftLabel: 'Low YoY Drift (8.5%)',
    driftAdded: 4,
    driftRemoved: 2,
    driftExcerpt: 'Export administration regulations and restrictions on high-performance accelerators to select jurisdictions.',
    mscore: -2.85,
    mscoreLabel: 'Safe Non-Manipulator (-2.85)',
    mscoreProb: '< 1%',
    tataAccrual: -0.045,
    divergenceScore: 11.0,
    radarLabel: 'Harmonized Guidance (11.0 / 100)',
    radarExcerpt: 'Strong data center demand across all cloud hyperscalers aligned with conservative supply-chain commentary.',
    footnotesClean: true,
    footnoteCount: 1,
    footnoteExcerpt: 'Customer A accounts for approximately 13% of total revenue. Clean SOX 404 internal controls opinion.'
  },
  AAPL: {
    ticker: 'AAPL',
    name: 'Apple Inc.',
    exchange: 'NASDAQ',
    cik: '0000320193',
    sector: 'Consumer Electronics & Software',
    period: 'FY2024 Form 10-K & Q1 FY2025 Form 10-Q',
    auditor: 'Ernst & Young LLP',
    ffi: 14,
    riskTier: 'LOW_RISK',
    driftScore: 6.2,
    driftLabel: 'Minimal Language Drift (6.2%)',
    driftAdded: 2,
    driftRemoved: 1,
    driftExcerpt: 'Compliance modifications regarding European Digital Markets Act (DMA) app distribution.',
    mscore: -2.92,
    mscoreLabel: 'High Quality Accruals (-2.92)',
    mscoreProb: '< 1%',
    tataAccrual: -0.062,
    divergenceScore: 8.5,
    radarLabel: 'Disciplined Tone Alignment (8.5 / 100)',
    radarExcerpt: 'Services gross margins commentary mirrors 10-K revenue recognition schedule.',
    footnotesClean: true,
    footnoteCount: 0,
    footnoteExcerpt: 'Zero material weaknesses in ICFR. No concentrated customers exceeding 10%.'
  },
  MSFT: {
    ticker: 'MSFT',
    name: 'Microsoft Corporation',
    exchange: 'NASDAQ',
    cik: '0000789019',
    sector: 'Cloud & Enterprise Infrastructure',
    period: 'FY2024 Form 10-K & Q2 FY2025 Form 10-Q',
    auditor: 'Deloitte & Touche LLP',
    ffi: 16,
    riskTier: 'LOW_RISK',
    driftScore: 7.8,
    driftLabel: 'Predictable Updates (7.8%)',
    driftAdded: 3,
    driftRemoved: 1,
    driftExcerpt: 'Azure cloud capacity scaling commitments and capital expenditure projections.',
    mscore: -2.78,
    mscoreLabel: 'Clean Balance Sheet (-2.78)',
    mscoreProb: '< 1%',
    tataAccrual: -0.051,
    divergenceScore: 10.2,
    radarLabel: 'Synchronized Tone (10.2 / 100)',
    radarExcerpt: 'Azure AI ARR growth narrative corresponds with reported commercial remaining performance obligations (RPO).',
    footnotesClean: true,
    footnoteCount: 0,
    footnoteExcerpt: 'Diversified customer base. Unqualified audit on internal control over financial reporting.'
  },
  TSLA: {
    ticker: 'TSLA',
    name: 'Tesla Inc.',
    exchange: 'NASDAQ',
    cik: '0001318605',
    sector: 'Automotive & Energy Storage',
    period: 'FY2024 Form 10-K & Q3 FY2025 Form 10-Q',
    auditor: 'PricewaterhouseCoopers LLP',
    ffi: 46,
    riskTier: 'WATCHLIST',
    driftScore: 24.1,
    driftLabel: 'Elevated Margin Shift (24.1%)',
    driftAdded: 7,
    driftRemoved: 4,
    driftExcerpt: 'Regulatory credit revenue variability and autonomous vehicle regulatory approval disclosures.',
    mscore: -2.10,
    mscoreLabel: 'Moderate Accrual Fluctuation (-2.10)',
    mscoreProb: '3.8%',
    tataAccrual: 0.012,
    divergenceScore: 38.5,
    radarLabel: 'Divergent Executive Tone (38.5 / 100)',
    radarExcerpt: 'Optimistic spoken call timelines on robotaxi commercialization contrast with MD&A risk caveats.',
    footnotesClean: false,
    footnoteCount: 2,
    footnoteExcerpt: 'Warranty reserve adjustments and concentration of automotive regulatory credits.'
  },
  AMZN: {
    ticker: 'AMZN',
    name: 'Amazon.com Inc.',
    exchange: 'NASDAQ',
    cik: '0001018724',
    sector: 'E-Commerce & Cloud Services',
    period: 'FY2024 Form 10-K & Q3 FY2025 Form 10-Q',
    auditor: 'Ernst & Young LLP',
    ffi: 22,
    riskTier: 'LOW_RISK',
    driftScore: 9.4,
    driftLabel: 'Stable Disclosures (9.4%)',
    driftAdded: 4,
    driftRemoved: 2,
    driftExcerpt: 'AWS power infrastructure requirements and retail regional fulfillment efficiency.',
    mscore: -2.65,
    mscoreLabel: 'Healthy Cash Conversion (-2.65)',
    mscoreProb: '< 1%',
    tataAccrual: -0.038,
    divergenceScore: 14.5,
    radarLabel: 'Consistent Guidance (14.5 / 100)',
    radarExcerpt: 'International store segment operational leverage corresponds with reported cash flow.',
    footnotesClean: true,
    footnoteCount: 1,
    footnoteExcerpt: 'Lease accounting commitments for fulfillment centers and sovereign tax examination reserves.'
  }
}

const currentCompany = ref(companyProfiles.NVDA)

const selectCompany = (ticker) => {
  const t = ticker.toUpperCase().trim()
  if (companyProfiles[t]) {
    currentCompany.value = companyProfiles[t]
  } else {
    currentCompany.value = {
      ticker: t,
      name: `${t} Corporation`,
      exchange: 'NYSE/NASDAQ',
      cik: '0000000000',
      sector: 'Diversified Enterprise',
      period: 'Form 10-K Annual Filing',
      auditor: 'Big 4 Independent Audit Committee',
      ffi: 20,
      riskTier: 'LOW_RISK',
      driftScore: 10.0,
      driftLabel: 'Standard Drift (10.0%)',
      driftAdded: 3,
      driftRemoved: 2,
      driftExcerpt: 'Standard forward-looking statements and operational risk factors.',
      mscore: -2.50,
      mscoreLabel: 'Standard Accruals (-2.50)',
      mscoreProb: '< 2%',
      tataAccrual: -0.040,
      divergenceScore: 12.0,
      radarLabel: 'Aligned Guidance (12.0 / 100)',
      radarExcerpt: 'Guidance and disclosures align with trailing financial reporting.',
      footnotesClean: true,
      footnoteCount: 0,
      footnoteExcerpt: 'Standard disclosure footnotes. Unqualified audit opinion.'
    }
  }
  searchInput.value = t
}

// --- FFI Color Styling ---
const ffiColor = (score) => {
  if (score < 25) {
    return {
      text: 'text-emerald-400',
      bg: 'bg-emerald-500/10',
      border: 'border-emerald-500/20',
      label: 'Low Fragility'
    }
  } else if (score < 50) {
    return {
      text: 'text-amber-400',
      bg: 'bg-amber-500/10',
      border: 'border-amber-500/20',
      label: 'Watchlist Fragility'
    }
  } else {
    return {
      text: 'text-rose-400',
      bg: 'bg-rose-500/10',
      border: 'border-rose-500/20',
      label: 'Critical Alert'
    }
  }
}

// --- Documents Evidence Room State ---
const documents = ref([])
const isLoadingDocs = ref(false)
const isUploading = ref(false)
const docErrorMsg = ref('')

const fetchDocuments = async () => {
  isLoadingDocs.value = true
  docErrorMsg.value = ''
  try {
    const res = await fetch('/api/documents')
    if (res.ok) {
      const data = await res.json()
      documents.value = data.documents || []
      emit('document-count-change', documents.value.length)
    }
  } catch (err) {
    console.error('Failed to fetch documents:', err)
  } finally {
    isLoadingDocs.value = false
  }
}

const handleFileUpload = async (e) => {
  const file = e.target.files?.[0]
  if (!file) return

  isUploading.value = true
  docErrorMsg.value = ''
  const formData = new FormData()
  formData.append('file', file)

  try {
    const res = await fetch('/api/documents/upload', {
      method: 'POST',
      body: formData
    })
    if (!res.ok) {
      const errData = await res.json()
      throw new Error(errData.detail || 'Upload failed')
    }
    await fetchDocuments()
  } catch (err) {
    docErrorMsg.value = err.message
  } finally {
    isUploading.value = false
    e.target.value = ''
  }
}

// Delete Document Handling
const docToDelete = ref(null)
const isDeleting = ref(false)

const confirmDeleteDocument = (doc) => {
  docToDelete.value = doc
  showDeleteModal.value = true
}

const cancelDelete = () => {
  docToDelete.value = null
  showDeleteModal.value = false
}

const executeDelete = async () => {
  if (!docToDelete.value) return
  isDeleting.value = true
  try {
    const res = await fetch(`/api/documents/${docToDelete.value.doc_id}`, {
      method: 'DELETE'
    })
    if (res.ok) {
      await fetchDocuments()
      cancelDelete()
    }
  } catch (err) {
    console.error('Failed to delete document:', err)
  } finally {
    isDeleting.value = false
  }
}

// --- SEC EDGAR Ingestion State ---
const secTicker = ref('NVDA')
const secForm = ref('10-K')
const isImportingSec = ref(false)
const secErrorMsg = ref('')

const handleSecImport = async () => {
  if (!secTicker.value.trim()) return
  isImportingSec.value = true
  secErrorMsg.value = ''
  try {
    const res = await fetch('/api/ingest/sec', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        ticker: secTicker.value.trim().toUpperCase(),
        form: secForm.value,
        count: 2
      })
    })
    if (!res.ok) {
      const errData = await res.json()
      throw new Error(errData.detail || 'SEC ingestion failed')
    }
    showSecModal.value = false
    selectCompany(secTicker.value)
    await fetchDocuments()
  } catch (err) {
    secErrorMsg.value = err.message
  } finally {
    isImportingSec.value = false
  }
}

// --- Memo Export Handling ---
const isExportingMemo = ref(false)
const exportDueDiligenceMemo = async () => {
  isExportingMemo.value = true
  try {
    const res = await fetch('/api/forensics/report/download', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        ticker: currentCompany.value.ticker,
        company_name: currentCompany.value.name
      })
    })
    if (!res.ok) throw new Error('Failed to export memorandum')
    const blob = await res.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `Institutional_Due_Diligence_Memo_${currentCompany.value.ticker}.md`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  } catch (err) {
    console.error('Memo export failed:', err)
  } finally {
    isExportingMemo.value = false
  }
}

const askAiAboutDoc = (doc) => {
  emit('open-chat', `Conduct an in-depth forensic financial audit on the filing '${doc.source}'. Analyze language drift, footnotes, and potential accounting risks.`)
}

onMounted(async () => {
  await fetchDocuments()
})
</script>

<template>
  <div class="flex-1 flex flex-col h-screen overflow-hidden bg-[#080b12] text-slate-100 font-sans">
    
    <!-- Top Persistent Apple Frosted Glass Header -->
    <header class="apple-glass sticky top-0 z-30 px-6 py-3 flex flex-wrap items-center justify-between gap-4 border-b border-white/8 shrink-0">
      
      <!-- Brand & Platform Scope -->
      <div class="flex items-center gap-3">
        <div class="w-8 h-8 rounded-xl bg-gradient-to-br from-emerald-400/20 to-teal-600/30 border border-emerald-400/30 flex items-center justify-center text-emerald-400 font-bold font-mono shadow-xs text-sm">
          Z
        </div>
        <div>
          <div class="flex items-center gap-2">
            <span class="text-sm font-bold tracking-tight text-white">ZAISAKU</span>
            <span class="text-[10px] font-mono font-semibold px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-300 border border-emerald-500/20">
              Enterprise v2.4
            </span>
          </div>
          <p class="text-[11px] text-slate-400">Institutional Forensic Due Diligence & Intelligence Suite</p>
        </div>
      </div>

      <!-- Quick Ticker Switcher -->
      <div class="flex items-center gap-1.5 p-1 rounded-xl bg-slate-900/80 border border-white/10">
        <button
          v-for="ticker in ['NVDA', 'AAPL', 'MSFT', 'TSLA', 'AMZN']"
          :key="ticker"
          @click="selectCompany(ticker)"
          class="apple-press px-2.5 py-1 rounded-lg text-xs font-semibold transition-all cursor-pointer"
          :class="currentCompany.ticker === ticker 
            ? 'bg-emerald-500 text-slate-950 font-bold shadow-xs' 
            : 'text-slate-400 hover:text-white hover:bg-slate-800/60'"
        >
          {{ ticker }}
        </button>

        <div class="relative hidden sm:flex items-center border-l border-white/10 pl-2">
          <Search class="w-3.5 h-3.5 text-slate-500 absolute left-4" />
          <input
            v-model="searchInput"
            @keydown.enter="selectCompany(searchInput)"
            placeholder="Search symbol..."
            class="w-28 pl-7 pr-2 py-1 text-xs bg-slate-800/80 rounded-lg text-white placeholder:text-slate-500 focus:outline-none focus:w-36 transition-all border border-transparent focus:border-emerald-500/40"
          />
        </div>
      </div>

      <!-- Global Actions Tray -->
      <div class="flex items-center gap-2">
        <button
          @click="showInstitutionalReportModal = true"
          class="apple-press text-xs font-medium px-3 py-1.5 rounded-xl border border-white/10 bg-slate-800/90 hover:bg-slate-700/80 text-slate-200 flex items-center gap-1.5 transition-all cursor-pointer shadow-xs"
          title="Print-Ready Institutional Due Diligence Memorandum"
        >
          <FileText class="w-3.5 h-3.5 text-slate-400" />
          <span class="hidden md:inline">Memo Preview</span>
        </button>

        <button
          @click="exportDueDiligenceMemo"
          :disabled="isExportingMemo"
          class="apple-press text-xs font-medium px-3 py-1.5 rounded-xl border border-white/10 bg-slate-800/90 hover:bg-slate-700/80 text-slate-200 flex items-center gap-1.5 transition-all cursor-pointer shadow-xs"
          title="Export Markdown Memorandum"
        >
          <Loader2 v-if="isExportingMemo" class="w-3.5 h-3.5 animate-spin text-emerald-400" />
          <Download v-else class="w-3.5 h-3.5 text-slate-400" />
          <span>Export</span>
        </button>

        <button
          @click="emit('open-chat')"
          class="apple-press text-xs font-semibold px-3.5 py-1.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 flex items-center gap-1.5 transition-all cursor-pointer shadow-xs"
          title="Toggle AI Co-Analyst Drawer (Ctrl + K)"
        >
          <Sparkles class="w-3.5 h-3.5 fill-current" />
          <span>Co-Analyst</span>
          <kbd class="text-[9px] font-mono bg-slate-950/20 px-1 py-0.5 rounded border border-black/20 ml-1 hidden sm:inline">Ctrl+K</kbd>
        </button>
      </div>

    </header>

    <!-- Sub-Header: Apple Segmented Workspace Navigation Menu -->
    <div class="px-6 py-2.5 bg-slate-950/70 border-b border-white/8 shrink-0 flex items-center justify-between overflow-x-auto scrollbar-none">
      <div class="flex items-center gap-1 p-1 rounded-xl bg-slate-900/90 border border-white/10">
        <button
          v-for="tab in navigationTabs"
          :key="tab.id"
          @click="currentTab = tab.id"
          class="apple-press px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all cursor-pointer flex items-center gap-2 whitespace-nowrap"
          :class="currentTab === tab.id 
            ? 'bg-white/10 text-white font-semibold shadow-xs border border-white/10' 
            : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/40'"
        >
          <component :is="tab.icon" class="w-3.5 h-3.5" :class="currentTab === tab.id ? 'text-emerald-400' : 'text-slate-500'" />
          <span>{{ tab.label }}</span>
          <span 
            v-if="tab.badge" 
            class="text-[9px] font-mono px-1.5 py-0.2 rounded-full bg-rose-500/10 text-rose-300 border border-rose-500/20 font-bold"
          >
            {{ tab.badge }}
          </span>
          <span 
            v-else-if="tab.id === 'filings' && documents.length > 0" 
            class="text-[9px] font-mono px-1.5 py-0.2 rounded-full bg-slate-800 text-slate-400"
          >
            {{ documents.length }}
          </span>
        </button>
      </div>

      <!-- Target Company Fast Info Badge -->
      <div class="hidden lg:flex items-center gap-3 text-xs text-slate-400 font-mono">
        <span>Target: <strong class="text-white">{{ currentCompany.name }}</strong> ({{ currentCompany.ticker }})</span>
        <span>·</span>
        <span>Auditor: <strong class="text-slate-300">{{ currentCompany.auditor }}</strong></span>
      </div>
    </div>

    <!-- Main Workspace Body with Apple Spring Slide View Transition -->
    <main class="flex-1 overflow-y-auto p-6 custom-scrollbar">
      <div class="max-w-7xl mx-auto">
        <Transition name="apple-view" mode="out-in">
          
          <!-- ========================================== -->
          <!-- VIEW 1: EXECUTIVE DOSSIER (Overview)       -->
          <!-- ========================================== -->
          <div v-if="currentTab === 'overview'" key="overview" class="space-y-6">
            
            <!-- Hero Profile & FFI Card -->
            <section class="apple-card rounded-3xl p-6 sm:p-8 flex flex-col lg:flex-row items-start lg:items-center justify-between gap-8 relative overflow-hidden">
              <div class="space-y-4 max-w-2xl">
                <div class="flex flex-wrap items-center gap-2.5">
                  <span class="px-2.5 py-1 rounded-full text-xs font-mono font-bold bg-white/10 text-white border border-white/15">
                    {{ currentCompany.exchange }}: {{ currentCompany.ticker }}
                  </span>
                  <span class="text-xs text-slate-400 flex items-center gap-1">
                    <Building2 class="w-3.5 h-3.5 text-slate-500" />
                    {{ currentCompany.sector }}
                  </span>
                  <span class="text-xs text-slate-600">·</span>
                  <span class="text-xs text-slate-400 font-mono">CIK {{ currentCompany.cik }}</span>
                </div>

                <h1 class="text-3xl sm:text-4xl font-extrabold tracking-tight text-white">
                  {{ currentCompany.name }}
                </h1>

                <div class="flex flex-wrap items-center gap-y-2 gap-x-4 text-xs text-slate-400">
                  <span class="flex items-center gap-1.5">
                    <Calendar class="w-3.5 h-3.5 text-slate-500" />
                    {{ currentCompany.period }}
                  </span>
                  <span>·</span>
                  <span class="flex items-center gap-1.5">
                    <FileCheck class="w-3.5 h-3.5 text-emerald-400" />
                    Auditor of Record: {{ currentCompany.auditor }}
                  </span>
                </div>

                <p class="text-xs sm:text-sm text-slate-300 leading-relaxed max-w-xl">
                  Automated triangulation across SEC EDGAR regulatory language shifts, forensic accrual accounting indicators (Beneish M-Score), and earnings call tone decoupling to detect hidden liabilities.
                </p>
              </div>

              <!-- FFI Fragility Gauge Card -->
              <div class="w-full lg:w-auto shrink-0">
                <div class="bg-slate-900/90 border border-white/10 rounded-2xl p-5 sm:p-6 flex flex-col items-center gap-4 text-center shadow-xl min-w-[280px]">
                  <span class="text-[11px] font-semibold tracking-wider text-slate-400 uppercase">
                    Forensic Fragility Index (FFI)
                  </span>

                  <div class="relative flex items-center justify-center">
                    <div 
                      class="w-28 h-28 rounded-full border-4 flex flex-col items-center justify-center transition-all shadow-inner"
                      :class="[ffiColor(currentCompany.ffi).border, ffiColor(currentCompany.ffi).bg]"
                    >
                      <span class="text-3xl font-extrabold tracking-tight text-white font-mono">
                        {{ currentCompany.ffi }}
                      </span>
                      <span class="text-[10px] text-slate-400 uppercase font-semibold">
                        / 100
                      </span>
                    </div>
                  </div>

                  <div class="space-y-1">
                    <span 
                      class="px-3 py-1 rounded-full text-xs font-semibold inline-block border"
                      :class="[ffiColor(currentCompany.ffi).border, ffiColor(currentCompany.ffi).bg, ffiColor(currentCompany.ffi).text]"
                    >
                      {{ ffiColor(currentCompany.ffi).label }}
                    </span>
                    <p class="text-[11px] text-slate-400">
                      Drift 30% · M-Score 40% · Contradictions 30%
                    </p>
                  </div>

                  <div class="w-full space-y-2 pt-2 border-t border-white/5">
                    <button
                      @click="showInvestigationRunner = true"
                      class="apple-press w-full py-2 px-3 rounded-xl bg-purple-600/90 hover:bg-purple-500 text-xs font-semibold text-white flex items-center justify-center gap-1.5 transition-all cursor-pointer shadow-xs"
                    >
                      <Terminal class="w-3.5 h-3.5" />
                      <span>Autonomous Multi-Agent Audit</span>
                    </button>

                    <button
                      @click="showAuditorModal = true"
                      class="apple-press w-full py-2 px-3 rounded-xl bg-rose-950/40 hover:bg-rose-900/60 border border-rose-500/30 text-xs font-semibold text-rose-300 hover:text-white flex items-center justify-center gap-1.5 transition-all cursor-pointer shadow-xs"
                    >
                      <Scale class="w-3.5 h-3.5 text-rose-400" />
                      <span>Adversarial Cross-Examination</span>
                    </button>

                    <button
                      @click="showScorecardModal = true"
                      class="apple-press w-full py-1.5 px-3 rounded-xl bg-slate-800 hover:bg-slate-700/80 border border-white/10 text-xs font-medium text-slate-300 hover:text-white flex items-center justify-center gap-1.5 transition-all cursor-pointer"
                    >
                      <Sliders class="w-3.5 h-3.5 text-emerald-400" />
                      <span>Inspect Audit Scorecard</span>
                    </button>
                  </div>
                </div>
              </div>
            </section>

            <!-- 4 Core Forensic Pillar Cards -->
            <section class="space-y-3">
              <div class="flex items-center justify-between">
                <div>
                  <h2 class="text-sm font-bold text-white tracking-tight uppercase">Forensic Intelligence Pillars</h2>
                  <p class="text-xs text-slate-400">Continuous institutional monitoring across four analytical audit vectors</p>
                </div>
                <span class="text-xs text-slate-500 font-mono">SEC EDGAR Continuous Ingestion</span>
              </div>

              <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                
                <!-- Card 1: Language Drift -->
                <div class="apple-card rounded-2xl p-5 flex flex-col justify-between space-y-3">
                  <div class="space-y-2">
                    <div class="flex items-center justify-between">
                      <div class="flex items-center gap-2">
                        <div class="p-1.5 rounded-lg bg-amber-500/10 text-amber-400 border border-amber-500/20">
                          <GitCompare class="w-3.5 h-3.5" />
                        </div>
                        <h3 class="text-xs font-bold text-white uppercase tracking-wider">Filing Language Drift</h3>
                      </div>
                      <span class="text-xs font-mono font-semibold px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-300 border border-amber-500/20">
                        {{ currentCompany.driftLabel }}
                      </span>
                    </div>

                    <div class="flex items-center gap-3 text-xs text-slate-400 font-mono">
                      <span class="text-emerald-400 font-medium">+{{ currentCompany.driftAdded }} Risks Added</span>
                      <span>·</span>
                      <span class="text-slate-400">-{{ currentCompany.driftRemoved }} Retired</span>
                    </div>

                    <blockquote class="text-xs text-slate-300 italic border-l-2 border-amber-500/40 pl-3 py-1 bg-slate-950/40 rounded-r-lg font-serif">
                      "{{ currentCompany.driftExcerpt }}"
                    </blockquote>
                  </div>

                  <div class="pt-2 flex items-center justify-between border-t border-white/5">
                    <span class="text-[11px] text-slate-500 font-mono">YoY Redline Semantic Matching</span>
                    <button
                      @click="showDiffModal = true"
                      class="apple-press text-xs font-semibold text-amber-400 hover:text-amber-300 flex items-center gap-1 cursor-pointer"
                    >
                      <span>Inspect Redline Diff</span>
                      <ArrowRight class="w-3 h-3" />
                    </button>
                  </div>
                </div>

                <!-- Card 2: Beneish M-Score -->
                <div class="apple-card rounded-2xl p-5 flex flex-col justify-between space-y-3">
                  <div class="space-y-2">
                    <div class="flex items-center justify-between">
                      <div class="flex items-center gap-2">
                        <div class="p-1.5 rounded-lg bg-purple-500/10 text-purple-400 border border-purple-500/20">
                          <Calculator class="w-3.5 h-3.5" />
                        </div>
                        <h3 class="text-xs font-bold text-white uppercase tracking-wider">Beneish M-Score Accruals</h3>
                      </div>
                      <span class="text-xs font-mono font-semibold px-2 py-0.5 rounded-full bg-purple-500/10 text-purple-300 border border-purple-500/20">
                        {{ currentCompany.mscoreLabel }}
                      </span>
                    </div>

                    <div class="flex items-center gap-3 text-xs text-slate-400 font-mono">
                      <span>Threshold: <strong class="text-slate-200">-1.78</strong></span>
                      <span>·</span>
                      <span>Prob: <strong class="text-emerald-400">{{ currentCompany.mscoreProb }}</strong></span>
                      <span>·</span>
                      <span>TATA: <strong class="text-slate-200">{{ currentCompany.tataAccrual }}</strong></span>
                    </div>

                    <p class="text-xs text-slate-300 leading-relaxed bg-slate-950/40 p-2.5 rounded-lg border border-white/5">
                      Total Accruals to Total Assets (TATA) and Asset Quality Index (AQI) indicate earnings are backed by operational cash collection.
                    </p>
                  </div>

                  <div class="pt-2 flex items-center justify-between border-t border-white/5">
                    <span class="text-[11px] text-slate-500 font-mono">8-Factor Probabilistic Model</span>
                    <button
                      @click="showMScoreModal = true"
                      class="apple-press text-xs font-semibold text-purple-400 hover:text-purple-300 flex items-center gap-1 cursor-pointer"
                    >
                      <span>Audit Accruals</span>
                      <ArrowRight class="w-3 h-3" />
                    </button>
                  </div>
                </div>

                <!-- Card 3: Tone Decoupling -->
                <div class="apple-card rounded-2xl p-5 flex flex-col justify-between space-y-3">
                  <div class="space-y-2">
                    <div class="flex items-center justify-between">
                      <div class="flex items-center gap-2">
                        <div class="p-1.5 rounded-lg bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                          <Radio class="w-3.5 h-3.5" />
                        </div>
                        <h3 class="text-xs font-bold text-white uppercase tracking-wider">Earnings Call vs 10-Q Radar</h3>
                      </div>
                      <span class="text-xs font-mono font-semibold px-2 py-0.5 rounded-full bg-cyan-500/10 text-cyan-300 border border-cyan-500/20">
                        {{ currentCompany.radarLabel }}
                      </span>
                    </div>

                    <p class="text-xs text-slate-300 leading-relaxed bg-slate-950/40 p-2.5 rounded-lg border border-white/5">
                      {{ currentCompany.radarExcerpt }}
                    </p>
                  </div>

                  <div class="pt-2 flex items-center justify-between border-t border-white/5">
                    <span class="text-[11px] text-slate-500 font-mono">Cross-Modal Decoupling</span>
                    <button
                      @click="showRadarModal = true"
                      class="apple-press text-xs font-semibold text-cyan-400 hover:text-cyan-300 flex items-center gap-1 cursor-pointer"
                    >
                      <span>Inspect Contradictions</span>
                      <ArrowRight class="w-3 h-3" />
                    </button>
                  </div>
                </div>

                <!-- Card 4: Footnote Hazards -->
                <div class="apple-card rounded-2xl p-5 flex flex-col justify-between space-y-3">
                  <div class="space-y-2">
                    <div class="flex items-center justify-between">
                      <div class="flex items-center gap-2">
                        <div class="p-1.5 rounded-lg bg-rose-500/10 text-rose-400 border border-rose-500/20">
                          <ShieldAlert class="w-3.5 h-3.5" />
                        </div>
                        <h3 class="text-xs font-bold text-white uppercase tracking-wider">Footnote Disclosure Scan</h3>
                      </div>
                      <span 
                        class="text-xs font-mono font-semibold px-2 py-0.5 rounded-full border"
                        :class="currentCompany.footnotesClean 
                          ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/20' 
                          : 'bg-rose-500/10 text-rose-300 border-rose-500/20'"
                      >
                        {{ currentCompany.footnotesClean ? 'Clean Disclosures' : `${currentCompany.footnoteCount} Hazards Flagged` }}
                      </span>
                    </div>

                    <p class="text-xs text-slate-300 leading-relaxed bg-slate-950/40 p-2.5 rounded-lg border border-white/5">
                      {{ currentCompany.footnoteExcerpt }}
                    </p>
                  </div>

                  <div class="pt-2 flex items-center justify-between border-t border-white/5">
                    <span class="text-[11px] text-slate-500 font-mono">Automated NLP Disclosure Audit</span>
                    <button
                      @click="showMScoreModal = true"
                      class="apple-press text-xs font-semibold text-rose-400 hover:text-rose-300 flex items-center gap-1 cursor-pointer"
                    >
                      <span>Scan Footnotes</span>
                      <ArrowRight class="w-3 h-3" />
                    </button>
                  </div>
                </div>

              </div>
            </section>

          </div>

          <!-- ========================================== -->
          <!-- VIEW 2: FINANCIALS & VISUAL EXHIBITS       -->
          <!-- ========================================== -->
          <div v-else-if="currentTab === 'financials'" key="financials" class="space-y-6">
            <FinancialTableExtractor 
              :ticker="currentCompany.ticker" 
              :company-name="currentCompany.name" 
            />
            <FilingVisualExtractor 
              :ticker="currentCompany.ticker" 
              :company-name="currentCompany.name" 
            />
          </div>

          <!-- ========================================== -->
          <!-- VIEW 3: MULTI-YEAR TRENDS & PEER BENCHMARK -->
          <!-- ========================================== -->
          <div v-else-if="currentTab === 'benchmarks'" key="benchmarks" class="space-y-6">
            <FinancialTrendsChart 
              :ticker="currentCompany.ticker" 
              @open-chat="emit('open-chat', $event)" 
            />
            <PeerComparisonMatrix 
              :ticker="currentCompany.ticker" 
              @select-ticker="selectCompany" 
            />
          </div>

          <!-- ========================================== -->
          <!-- VIEW 4: SCENARIO STRESS LAB (Monte Carlo)   -->
          <!-- ========================================== -->
          <div v-else-if="currentTab === 'scenarios'" key="scenarios" class="space-y-6">
            <ScenarioStressTester 
              :ticker="currentCompany.ticker" 
              :company-name="currentCompany.name" 
            />
          </div>

          <!-- ========================================== -->
          <!-- VIEW 5: AUDIO & ADVERSARIAL INQUIRIES      -->
          <!-- ========================================== -->
          <div v-else-if="currentTab === 'interrogation'" key="interrogation" class="space-y-6">
            <!-- Earnings Call Audio Simulator -->
            <AudioCallSimulator 
              :ticker="currentCompany.ticker" 
              :company-name="currentCompany.name" 
            />

            <!-- Forensic Inquiry Trigger Cards -->
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
              
              <!-- Trigger 1: Adversarial Cross-Examination Studio -->
              <div class="apple-card rounded-2xl p-5 flex flex-col justify-between space-y-3">
                <div class="space-y-2">
                  <div class="p-2 rounded-xl bg-rose-500/10 text-rose-400 border border-rose-500/20 w-fit">
                    <Scale class="w-5 h-5" />
                  </div>
                  <h3 class="text-sm font-bold text-white">Adversarial Cross-Examination</h3>
                  <p class="text-xs text-slate-300 leading-relaxed">
                    Prosecutorial interrogation simulating Big 4 / PCAOB and SEC Enforcement inquiries on revenue recognition cut-off and undisclosed liabilities.
                  </p>
                </div>
                <button
                  @click="showAuditorModal = true"
                  class="apple-press py-2 px-3.5 rounded-xl bg-rose-600 hover:bg-rose-500 text-white text-xs font-semibold flex items-center justify-center gap-1.5 cursor-pointer shadow-xs"
                >
                  <span>Launch Cross-Examination</span>
                  <ArrowRight class="w-3.5 h-3.5" />
                </button>
              </div>

              <!-- Trigger 2: Autonomous Multi-Agent Investigation Runner -->
              <div class="apple-card rounded-2xl p-5 flex flex-col justify-between space-y-3">
                <div class="space-y-2">
                  <div class="p-2 rounded-xl bg-purple-500/10 text-purple-400 border border-purple-500/20 w-fit">
                    <Terminal class="w-5 h-5" />
                  </div>
                  <h3 class="text-sm font-bold text-white">Autonomous 4-Stage Multi-Agent Audit</h3>
                  <p class="text-xs text-slate-300 leading-relaxed">
                    Dispatches synchronized specialized subagents across filings, transcripts, and footnotes with real-time SSE execution telemetry.
                  </p>
                </div>
                <button
                  @click="showInvestigationRunner = true"
                  class="apple-press py-2 px-3.5 rounded-xl bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold flex items-center justify-center gap-1.5 cursor-pointer shadow-xs"
                >
                  <span>Launch Agent Swarm</span>
                  <ArrowRight class="w-3.5 h-3.5" />
                </button>
              </div>

              <!-- Trigger 3: AI Prompt & RAG Laboratory Sandbox -->
              <div class="apple-card rounded-2xl p-5 flex flex-col justify-between space-y-3">
                <div class="space-y-2">
                  <div class="p-2 rounded-xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 w-fit">
                    <Cpu class="w-5 h-5" />
                  </div>
                  <h3 class="text-sm font-bold text-white">AI RAG & Prompt Benchmark Lab</h3>
                  <p class="text-xs text-slate-300 leading-relaxed">
                    Evaluate LLM reasoning latencies, hallucination rates, and cross-encoder reranking precision across institutional queries.
                  </p>
                </div>
                <button
                  @click="showSandboxModal = true"
                  class="apple-press py-2 px-3.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold flex items-center justify-center gap-1.5 cursor-pointer shadow-xs"
                >
                  <span>Open Benchmark Lab</span>
                  <ArrowRight class="w-3.5 h-3.5" />
                </button>
              </div>

            </div>
          </div>

          <!-- ========================================== -->
          <!-- VIEW 6: EVIDENCE ROOM (Filings & Documents)-->
          <!-- ========================================== -->
          <div v-else-if="currentTab === 'filings'" key="filings" class="space-y-4">
            
            <div class="flex flex-wrap items-center justify-between gap-4">
              <div>
                <h2 class="text-base font-bold text-white tracking-tight flex items-center gap-2">
                  Regulatory Filings & Audio Evidence Room
                  <span class="text-xs font-mono font-normal px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 border border-slate-700">
                    {{ documents.length }} Document{{ documents.length !== 1 ? 's' : '' }}
                  </span>
                </h2>
                <p class="text-xs text-slate-400">Indexed 10-K, 10-Q, 8-K filings and audio transcripts available for RAG inference</p>
              </div>

              <div class="flex items-center gap-2">
                <button
                  @click="showSecModal = true"
                  class="apple-press text-xs font-medium px-3.5 py-1.5 rounded-xl border border-slate-700 bg-slate-800 hover:bg-slate-700 text-slate-200 flex items-center gap-1.5 cursor-pointer"
                >
                  <Globe class="w-3.5 h-3.5 text-emerald-400" />
                  <span>Ingest SEC EDGAR</span>
                </button>

                <label 
                  class="apple-press text-xs font-medium px-3.5 py-1.5 rounded-xl border border-dashed border-slate-700 bg-slate-800/60 hover:bg-slate-800 text-slate-300 hover:text-white flex items-center gap-2 cursor-pointer transition-all"
                  :class="{ 'opacity-50 pointer-events-none': isUploading }"
                >
                  <Loader2 v-if="isUploading" class="w-3.5 h-3.5 animate-spin text-emerald-400" />
                  <UploadCloud v-else class="w-3.5 h-3.5 text-emerald-400" />
                  <span>Upload (PDF, HTML, TXT)</span>
                  <input type="file" class="hidden" accept=".pdf,.html,.txt" @change="handleFileUpload" :disabled="isUploading" />
                </label>
              </div>
            </div>

            <div v-if="docErrorMsg" class="p-3 rounded-xl bg-red-950/40 border border-red-800 text-red-300 text-xs">
              {{ docErrorMsg }}
            </div>

            <!-- Table of Filings -->
            <div class="apple-card rounded-2xl overflow-hidden">
              <div v-if="isLoadingDocs" class="p-12 flex justify-center items-center">
                <Loader2 class="w-6 h-6 animate-spin text-emerald-500" />
              </div>

              <div v-else-if="documents.length === 0" class="p-12 text-center space-y-3">
                <FileText class="w-8 h-8 text-slate-600 mx-auto" />
                <p class="text-sm text-slate-400 font-medium">No SEC filings or transcripts indexed yet.</p>
                <p class="text-xs text-slate-500 max-w-md mx-auto">
                  Use "Ingest SEC EDGAR" to import consecutive 10-Ks from SEC EDGAR, or upload a transcript PDF.
                </p>
              </div>

              <div v-else class="overflow-x-auto">
                <table class="w-full text-left text-xs text-slate-300">
                  <thead class="bg-slate-950/80 text-slate-400 uppercase tracking-wider text-[10px] border-b border-white/5 font-mono">
                    <tr>
                      <th class="py-3 px-4 font-semibold">Document Name / Source</th>
                      <th class="py-3 px-4 font-semibold">Identifier</th>
                      <th class="py-3 px-4 font-semibold">Status</th>
                      <th class="py-3 px-4 font-semibold text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody class="divide-y divide-white/5">
                    <tr 
                      v-for="doc in documents" 
                      :key="doc.doc_id"
                      class="hover:bg-slate-800/40 transition-colors group"
                    >
                      <td class="py-3.5 px-4 font-medium text-white flex items-center gap-2.5">
                        <FileText class="w-4 h-4 text-emerald-400 shrink-0" />
                        <span class="truncate max-w-md" :title="doc.source">{{ doc.source || 'Document' }}</span>
                      </td>
                      <td class="py-3.5 px-4 font-mono text-[11px] text-slate-500">
                        {{ doc.doc_id }}
                      </td>
                      <td class="py-3.5 px-4">
                        <span class="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-mono bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                          <span class="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
                          Indexed & Reranked
                        </span>
                      </td>
                      <td class="py-3.5 px-4 text-right">
                        <div class="flex items-center justify-end gap-2">
                          <button
                            @click="openFilingViewer(doc)"
                            class="apple-press px-2.5 py-1 rounded-lg bg-sky-500/10 hover:bg-sky-500/20 text-sky-400 border border-sky-500/20 text-xs font-medium flex items-center gap-1 cursor-pointer transition-colors"
                            title="Open interactive SEC document & AI annotation viewer"
                          >
                            <BookOpen class="w-3 h-3" />
                            <span>AI Studio</span>
                          </button>

                          <button
                            @click="askAiAboutDoc(doc)"
                            class="apple-press px-2.5 py-1 rounded-lg bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/20 text-xs font-medium flex items-center gap-1 cursor-pointer transition-colors"
                            title="Query AI Co-Analyst on this document"
                          >
                            <Sparkles class="w-3 h-3" />
                            <span>Ask AI</span>
                          </button>

                          <a
                            :href="`/api/documents/${doc.doc_id}/raw`"
                            target="_blank"
                            class="apple-press p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white border border-white/5 transition-colors cursor-pointer"
                            title="View Raw Document"
                          >
                            <ExternalLink class="w-3.5 h-3.5" />
                          </a>

                          <button
                            @click="confirmDeleteDocument(doc)"
                            class="apple-press p-1.5 rounded-lg bg-slate-800 hover:bg-rose-950/40 text-slate-400 hover:text-rose-400 border border-white/5 transition-colors cursor-pointer"
                            title="Delete Document"
                          >
                            <Trash2 class="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

          </div>

        </Transition>
      </div>
    </main>

    <!-- Modals & Drawers -->
    <FilingDiffModal 
      :is-open="showDiffModal" 
      :ticker="currentCompany.ticker" 
      @close="showDiffModal = false" 
      @open-chat="emit('open-chat', $event)" 
    />
    <ForensicMScoreModal 
      :is-open="showMScoreModal" 
      :ticker="currentCompany.ticker" 
      @close="showMScoreModal = false" 
      @open-chat="emit('open-chat', $event)" 
    />
    <ContradictionRadarModal 
      :is-open="showRadarModal" 
      :ticker="currentCompany.ticker" 
      @close="showRadarModal = false" 
      @open-chat="emit('open-chat', $event)" 
    />
    <ForensicScorecardModal 
      :is-open="showScorecardModal" 
      :ticker="currentCompany.ticker" 
      :company-name="currentCompany.name" 
      @close="showScorecardModal = false" 
      @open-chat="emit('open-chat', $event)" 
    />
    <FilingViewerModal 
      :is-open="showFilingViewerModal" 
      :document="selectedDocForViewer" 
      :ticker="currentCompany.ticker" 
      @close="showFilingViewerModal = false" 
      @open-chat="emit('open-chat', $event)" 
    />
    <ForensicInvestigationRunner 
      :is-open="showInvestigationRunner" 
      :ticker="currentCompany.ticker" 
      @close="showInvestigationRunner = false" 
      @open-chat="emit('open-chat', $event)" 
    />
    <ForensicSandboxModal 
      :is-open="showSandboxModal" 
      :ticker="currentCompany.ticker" 
      @close="showSandboxModal = false" 
    />
    <InstitutionalReportModal 
      :is-open="showInstitutionalReportModal" 
      :ticker="currentCompany.ticker" 
      :company-name="currentCompany.name" 
      :profile="currentCompany" 
      @close="showInstitutionalReportModal = false" 
    />
    <AuditorCrossExaminerModal
      :show="showAuditorModal"
      :ticker="currentCompany.ticker"
      :company-name="currentCompany.name"
      @close="showAuditorModal = false"
    />

    <!-- SEC EDGAR Ingestion Modal -->
    <Teleport to="body">
      <div 
        v-if="showSecModal" 
        class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-fadeIn"
        @keydown.esc="showSecModal = false"
      >
        <div class="apple-glass rounded-2xl max-w-md w-full p-6 shadow-2xl space-y-5 text-slate-200 border border-white/10">
          <div class="flex items-center justify-between border-b border-white/10 pb-4">
            <div class="flex items-center gap-2.5">
              <div class="p-2 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                <Globe class="w-5 h-5" />
              </div>
              <div>
                <h3 class="font-semibold text-white text-base">Ingest SEC EDGAR Filings</h3>
                <p class="text-xs text-slate-400">Directly ingest consecutive filings from the SEC EDGAR API</p>
              </div>
            </div>
            <button @click="showSecModal = false" class="text-slate-400 hover:text-white p-1 rounded-lg cursor-pointer">
              <X class="w-4 h-4" />
            </button>
          </div>

          <div class="space-y-4">
            <div>
              <label class="block text-xs font-medium text-slate-300 mb-1">Stock Ticker Symbol</label>
              <input
                v-model="secTicker"
                placeholder="e.g. NVDA, AAPL, MSFT"
                class="w-full bg-slate-800 border border-slate-700 rounded-xl px-3.5 py-2.5 text-sm text-white placeholder:text-slate-500 uppercase font-mono focus:outline-none focus:border-emerald-500"
              />
            </div>

            <div>
              <label class="block text-xs font-medium text-slate-300 mb-1">Form Type</label>
              <select
                v-model="secForm"
                class="w-full bg-slate-800 border border-slate-700 rounded-xl px-3 py-2.5 text-sm text-white focus:outline-none focus:border-emerald-500 cursor-pointer"
              >
                <option value="10-K">Form 10-K (Annual Comprehensive Report)</option>
                <option value="10-Q">Form 10-Q (Quarterly Report)</option>
              </select>
            </div>

            <div v-if="secErrorMsg" class="p-3 rounded-lg bg-rose-950/40 border border-rose-800 text-rose-300 text-xs">
              {{ secErrorMsg }}
            </div>
          </div>

          <div class="flex items-center justify-end gap-3 pt-2">
            <button
              @click="showSecModal = false"
              :disabled="isImportingSec"
              class="apple-press px-4 py-2 text-xs font-medium rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 cursor-pointer"
            >
              Cancel
            </button>
            <button
              @click="handleSecImport"
              :disabled="isImportingSec || !secTicker.trim()"
              class="apple-press px-4 py-2 text-xs font-semibold rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white flex items-center gap-2 cursor-pointer shadow-xs"
            >
              <Loader2 v-if="isImportingSec" class="w-3.5 h-3.5 animate-spin" />
              <span>Ingest & Index</span>
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Delete Confirmation Modal -->
    <Teleport to="body">
      <div 
        v-if="showDeleteModal" 
        class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-fadeIn"
        @keydown.esc="cancelDelete"
      >
        <div class="apple-glass rounded-2xl max-w-sm w-full p-6 shadow-2xl space-y-4 text-slate-200 border border-white/10">
          <div class="flex items-center gap-3">
            <div class="p-2.5 rounded-xl bg-rose-500/10 text-rose-400 border border-rose-500/20">
              <Trash2 class="w-5 h-5" />
            </div>
            <div>
              <h3 class="font-semibold text-white text-base">Delete Filing</h3>
              <p class="text-xs text-slate-400">Purge from indexed vector database</p>
            </div>
          </div>

          <p class="text-xs text-slate-300 leading-relaxed">
            Are you sure you want to remove <span class="font-semibold text-white break-all">"{{ docToDelete?.source }}"</span> from the evidence room?
          </p>

          <div class="flex items-center justify-end gap-2.5 pt-2">
            <button
              @click="cancelDelete"
              :disabled="isDeleting"
              class="apple-press px-3.5 py-2 text-xs font-medium rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 cursor-pointer"
            >
              Cancel
            </button>
            <button
              @click="executeDelete"
              :disabled="isDeleting"
              class="apple-press px-3.5 py-2 text-xs font-semibold rounded-xl bg-rose-600 hover:bg-rose-500 text-white flex items-center gap-2 cursor-pointer"
            >
              <Loader2 v-if="isDeleting" class="w-3.5 h-3.5 animate-spin" />
              <span>Delete</span>
            </button>
          </div>
        </div>
      </div>
    </Teleport>

  </div>
</template>

<style scoped>
.apple-glass {
  background: rgba(10, 14, 23, 0.82);
  backdrop-filter: blur(28px) saturate(190%);
}

.apple-card {
  background: rgba(15, 23, 42, 0.72);
  backdrop-filter: blur(24px) saturate(180%);
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.apple-press {
  transition: transform 0.18s cubic-bezier(0.32, 0.72, 0, 1), background-color 0.18s ease;
}

.apple-press:active {
  transform: scale(0.975);
}

/* Apple spring slide view transitions */
.apple-view-enter-active,
.apple-view-leave-active {
  transition: opacity 0.22s cubic-bezier(0.32, 0.72, 0, 1), transform 0.22s cubic-bezier(0.32, 0.72, 0, 1);
}

.apple-view-enter-from {
  opacity: 0;
  transform: translateY(6px) scale(0.995);
}

.apple-view-leave-to {
  opacity: 0;
  transform: translateY(-6px) scale(0.995);
}

.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.02);
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.12);
  border-radius: 9999px;
}

@media (prefers-reduced-motion: reduce) {
  .apple-press {
    transition: none !important;
    transform: none !important;
  }
  .apple-view-enter-active,
  .apple-view-leave-active {
    transition: none !important;
    transform: none !important;
  }
}
</style>
