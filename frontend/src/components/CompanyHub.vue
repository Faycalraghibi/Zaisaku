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
  Code2,
  Terminal,
  Play,
  BookOpen,
  Cpu
} from 'lucide-vue-next'

import FilingDiffModal from './FilingDiffModal.vue'
import ForensicMScoreModal from './ForensicMScoreModal.vue'
import ContradictionRadarModal from './ContradictionRadarModal.vue'
import ForensicScorecardModal from './ForensicScorecardModal.vue'
import FinancialTrendsChart from './FinancialTrendsChart.vue'
import FilingViewerModal from './FilingViewerModal.vue'
import ForensicInvestigationRunner from './ForensicInvestigationRunner.vue'
import PeerComparisonMatrix from './PeerComparisonMatrix.vue'
import TechStackDrawer from './TechStackDrawer.vue'
import FinancialTableExtractor from './FinancialTableExtractor.vue'
import AudioCallSimulator from './AudioCallSimulator.vue'
import ForensicSandboxModal from './ForensicSandboxModal.vue'
import InstitutionalReportModal from './InstitutionalReportModal.vue'
import ScenarioStressTester from './ScenarioStressTester.vue'

const emit = defineEmits(['open-chat', 'document-count-change'])

// --- Modal Visibility States ---
const showDiffModal = ref(false)
const showMScoreModal = ref(false)
const showRadarModal = ref(false)
const showScorecardModal = ref(false)
const showSecModal = ref(false)
const showDeleteModal = ref(false)
const showFilingViewerModal = ref(false)
const showInvestigationRunner = ref(false)
const showTechStackDrawer = ref(false)
const showSandboxModal = ref(false)
const showInstitutionalReportModal = ref(false)
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
    mscoreProb: '< 1.5%',
    tataAccrual: -0.038,
    divergenceScore: 14.0,
    radarLabel: 'Consistent Disclosure (14.0 / 100)',
    radarExcerpt: 'Capex escalation matched by management discussion on cloud workload migration.',
    footnotesClean: true,
    footnoteCount: 0,
    footnoteExcerpt: 'Unqualified audit report. Well distributed vendor and customer matrix.'
  }
}

const currentCompany = ref(companyProfiles.NVDA)

const selectCompany = (symbol) => {
  const upper = symbol.toUpperCase().trim()
  searchInput.value = upper
  if (companyProfiles[upper]) {
    currentCompany.value = companyProfiles[upper]
  } else {
    // Generate a clean template for typed tickers
    currentCompany.value = {
      ticker: upper,
      name: `${upper} Corporation`,
      exchange: 'US SEC',
      cik: 'EDGAR Ingested',
      sector: 'Public Equity',
      period: 'Form 10-K & 10-Q Ingested Filings',
      auditor: 'Independent Registered Public Accounting Firm',
      ffi: 25,
      riskTier: 'LOW_RISK',
      driftScore: 12.0,
      driftLabel: 'Standard Language Drift (12.0%)',
      driftAdded: 3,
      driftRemoved: 1,
      driftExcerpt: 'Routine updates to forward-looking statements and competitive landscape disclosures.',
      mscore: -2.60,
      mscoreLabel: 'Acceptable Accrual Quality (-2.60)',
      mscoreProb: '< 2%',
      tataAccrual: -0.030,
      divergenceScore: 15.0,
      radarLabel: 'Standard Alignment (15.0 / 100)',
      radarExcerpt: 'Executive statements match primary financial disclosure trajectory.',
      footnotesClean: true,
      footnoteCount: 0,
      footnoteExcerpt: 'No critical SOX 404 material weaknesses detected in active document chunks.'
    }
  }
}

// --- Documents and Upload State ---
const documents = ref([])
const isLoadingDocs = ref(true)
const isUploading = ref(false)
const docErrorMsg = ref('')
const docToDelete = ref(null)
const isDeleting = ref(false)

const fetchDocuments = async () => {
  isLoadingDocs.value = true
  docErrorMsg.value = ''
  try {
    const res = await fetch('/api/documents')
    if (!res.ok) throw new Error('Failed to fetch documents')
    const data = await res.json()
    documents.value = data.documents || []
    emit('document-count-change', documents.value.length)
  } catch (err) {
    docErrorMsg.value = err.message
  } finally {
    isLoadingDocs.value = false
  }
}

const handleFileUpload = async (event) => {
  const file = event.target.files[0]
  if (!file) return

  const formData = new FormData()
  formData.append('file', file)

  isUploading.value = true
  docErrorMsg.value = ''

  try {
    const res = await fetch('/api/ingest', {
      method: 'POST',
      body: formData
    })
    
    if (!res.ok) {
      const errData = await res.json().catch(() => ({}))
      throw new Error(errData.detail || 'Upload failed')
    }
    
    event.target.value = ''
    await fetchDocuments()
  } catch (err) {
    docErrorMsg.value = err.message
  } finally {
    isUploading.value = false
  }
}

const confirmDelete = (doc) => {
  docToDelete.value = doc
  showDeleteModal.value = true
}

const cancelDelete = () => {
  if (isDeleting.value) return
  showDeleteModal.value = false
  docToDelete.value = null
}

const executeDelete = async () => {
  if (!docToDelete.value || isDeleting.value) return
  isDeleting.value = true
  try {
    const res = await fetch(`/api/documents/${docToDelete.value.doc_id}`, { method: 'DELETE' })
    if (!res.ok) throw new Error('Failed to delete document')
    showDeleteModal.value = false
    docToDelete.value = null
    await fetchDocuments()
  } catch (err) {
    docErrorMsg.value = err.message
  } finally {
    isDeleting.value = false
  }
}

// --- SEC EDGAR Ingest State ---
const secTicker = ref('NVDA')
const secForm = ref('10-K')
const isImportingSec = ref(false)
const secErrorMsg = ref('')

const handleSecImport = async () => {
  if (!secTicker.value.trim() || isImportingSec.value) return
  isImportingSec.value = true
  secErrorMsg.value = ''

  try {
    const res = await fetch('/api/sec/ingest', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        ticker: secTicker.value.trim().toUpperCase(),
        form: secForm.value
      })
    })

    if (!res.ok) {
      const errData = await res.json().catch(() => ({}))
      if (res.status === 504) {
        throw new Error('Server timed out (504). SEC filing is large; the task is processing in background.')
      }
      throw new Error(errData.detail || `SEC import failed with status ${res.status}`)
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

// --- Export Due Diligence Memo ---
const isExportingMemo = ref(false)

const exportDueDiligenceMemo = async () => {
  isExportingMemo.value = true
  try {
    const payload = {
      ticker: currentCompany.value.ticker,
      company_name: currentCompany.value.name,
      scorecard: {
        overall_ffi: currentCompany.value.ffi,
        risk_tier: currentCompany.value.riskTier,
        drift: {
          drift_score: currentCompany.value.driftScore,
          risk_level: currentCompany.value.riskTier === 'LOW_RISK' ? 'NORMAL' : 'ELEVATED'
        },
        mscore: {
          m_score: currentCompany.value.mscore,
          manipulation_probability: currentCompany.value.mscoreProb,
          risk_level: currentCompany.value.riskTier === 'LOW_RISK' ? 'SAFE' : 'WATCHLIST'
        },
        contradictions: {
          tone_divergence_score: currentCompany.value.divergenceScore,
          contradiction_count: currentCompany.value.riskTier === 'WATCHLIST' ? 1 : 0
        },
        key_findings: [
          currentCompany.value.driftExcerpt,
          `Beneish M-Score of ${currentCompany.value.mscore} reflects acceptable accrual quality.`,
          currentCompany.value.footnoteExcerpt
        ],
        generated_at: new Date().toISOString()
      }
    }

    const res = await fetch('/api/forensics/report/download', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })

    if (!res.ok) {
      throw new Error('Failed to generate institutional due diligence report')
    }

    const blob = await res.blob()
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `due_diligence_memo_${currentCompany.value.ticker.toLowerCase()}.md`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(url)
  } catch (err) {
    docErrorMsg.value = err.message
  } finally {
    isExportingMemo.value = false
  }
}

const askAiAboutDoc = (doc) => {
  const prompt = `Perform a forensic audit of "${doc.source || 'this filing'}". Highlight key accounting disclosures, unexpected language drift, or executive guidance risks.`
  emit('open-chat', prompt)
}

const ffiColor = (score) => {
  if (score < 40) return { bg: 'bg-emerald-500/10', border: 'border-emerald-500/30', text: 'text-emerald-400', label: 'Low Risk', fill: '#10b981' }
  if (score < 70) return { bg: 'bg-amber-500/10', border: 'border-amber-500/30', text: 'text-amber-400', label: 'Watchlist Anomaly', fill: '#f59e0b' }
  return { bg: 'bg-rose-500/10', border: 'border-rose-500/30', text: 'text-rose-400', label: 'Critical Fragility', fill: '#f43f5e' }
}

onMounted(() => {
  fetchDocuments()
})
</script>

<template>
  <div class="flex-1 flex flex-col h-full overflow-y-auto bg-[#090d16] text-slate-100 scroll-smooth">
    
    <!-- Top Navigation Chrome: Apple Translucent Glass -->
    <header class="apple-glass sticky top-0 z-30 px-6 py-3.5 flex flex-wrap items-center justify-between gap-4 border-b border-white/10 shrink-0">
      <div class="flex items-center gap-3">
        <div class="w-8 h-8 rounded-xl bg-gradient-to-br from-emerald-400/20 to-emerald-600/30 border border-emerald-400/30 flex items-center justify-center text-emerald-400 font-bold font-mono shadow-xs">
          Z
        </div>
        <div>
          <div class="flex items-center gap-2">
            <span class="text-sm font-semibold tracking-tight text-white">Zaisaku</span>
            <span class="text-[10px] uppercase font-mono px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              Forensic Hub
            </span>
          </div>
          <p class="text-[11px] text-slate-400">Institutional Equity & SEC Forensic Intelligence</p>
        </div>
      </div>

      <!-- Quick Ticker Selector & Search -->
      <div class="flex items-center gap-2 bg-slate-900/80 p-1 rounded-xl border border-white/10">
        <div class="flex items-center gap-1 px-1">
          <button
            v-for="ticker in ['NVDA', 'AAPL', 'MSFT', 'TSLA', 'AMZN']"
            :key="ticker"
            @click="selectCompany(ticker)"
            class="apple-press px-2.5 py-1 rounded-lg text-xs font-semibold transition-all cursor-pointer"
            :class="currentCompany.ticker === ticker ? 'bg-emerald-500 text-slate-950 shadow-xs' : 'text-slate-400 hover:text-white hover:bg-slate-800/60'"
          >
            {{ ticker }}
          </button>
        </div>

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

      <!-- Primary Actions -->
      <div class="flex items-center gap-2">
        <button
          @click="showInvestigationRunner = true"
          class="apple-press text-xs font-semibold px-3 py-1.5 rounded-xl border border-purple-500/30 bg-purple-950/30 hover:bg-purple-900/50 text-purple-300 flex items-center gap-1.5 transition-all cursor-pointer shadow-xs"
          title="Run Autonomous Multi-Agent Forensic Investigation"
        >
          <Terminal class="w-3.5 h-3.5 text-purple-400" />
          <span class="hidden lg:inline">Multi-Agent Audit</span>
        </button>

        <button
          @click="showTechStackDrawer = true"
          class="apple-press text-xs font-medium px-3 py-1.5 rounded-xl border border-cyan-500/30 bg-cyan-950/20 hover:bg-cyan-900/40 text-cyan-300 flex items-center gap-1.5 transition-all cursor-pointer shadow-xs"
          title="View Engineering Architecture Blueprint"
        >
          <Code2 class="w-3.5 h-3.5 text-cyan-400" />
          <span class="hidden lg:inline">Architecture</span>
        </button>

        <button
          @click="showSandboxModal = true"
          class="apple-press text-xs font-medium px-3 py-1.5 rounded-xl border border-indigo-500/30 bg-indigo-950/20 hover:bg-indigo-900/40 text-indigo-300 flex items-center gap-1.5 transition-all cursor-pointer shadow-xs"
          title="AI Prompt Engineering & Model Benchmark Sandbox"
        >
          <Cpu class="w-3.5 h-3.5 text-indigo-400" />
          <span class="hidden md:inline">AI Sandbox</span>
        </button>

        <button
          @click="showInstitutionalReportModal = true"
          class="apple-press text-xs font-medium px-3 py-1.5 rounded-xl border border-blue-500/30 bg-blue-950/20 hover:bg-blue-900/40 text-blue-300 flex items-center gap-1.5 transition-all cursor-pointer shadow-xs"
          title="Print-Ready Institutional Due Diligence Memorandum"
        >
          <FileText class="w-3.5 h-3.5 text-blue-400" />
          <span class="hidden md:inline">Memo Preview</span>
        </button>

        <button
          @click="showSecModal = true"
          class="apple-press text-xs font-medium px-3 py-1.5 rounded-xl border border-slate-700/80 bg-slate-800/80 hover:bg-slate-700/80 text-slate-200 flex items-center gap-1.5 transition-all cursor-pointer"
          title="Import consecutive filings from SEC EDGAR"
        >
          <Globe class="w-3.5 h-3.5 text-emerald-400" />
          <span class="hidden md:inline">Import SEC</span>
        </button>

        <button
          @click="exportDueDiligenceMemo"
          :disabled="isExportingMemo"
          class="apple-press text-xs font-medium px-3 py-1.5 rounded-xl border border-white/10 bg-slate-800 hover:bg-slate-700 text-slate-100 flex items-center gap-1.5 transition-all cursor-pointer shadow-xs"
          title="Generate Institutional Due Diligence Memo"
        >
          <Loader2 v-if="isExportingMemo" class="w-3.5 h-3.5 animate-spin text-emerald-400" />
          <Download v-else class="w-3.5 h-3.5 text-slate-300" />
          <span>Export Memo</span>
        </button>

        <button
          @click="emit('open-chat')"
          class="apple-press text-xs font-semibold px-3.5 py-1.5 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-400 hover:to-teal-400 text-slate-950 flex items-center gap-1.5 transition-all cursor-pointer shadow-xs"
          title="Open AI Co-Analyst Drawer (Ctrl + K)"
        >
          <Sparkles class="w-3.5 h-3.5" />
          <span>Co-Analyst</span>
          <kbd class="text-[9px] font-mono bg-slate-950/20 px-1 py-0.5 rounded border border-black/20 ml-1 hidden sm:inline">Ctrl+K</kbd>
        </button>
      </div>
    </header>

    <!-- Main Workspace Container -->
    <main class="max-w-7xl w-full mx-auto p-6 space-y-8">
      
      <!-- Hero Section: Target Profile & Forensic Fragility Scorecard -->
      <section class="apple-card rounded-3xl p-6 sm:p-8 flex flex-col lg:flex-row items-start lg:items-center justify-between gap-8 relative overflow-hidden">
        <!-- Ambient Specular Glow -->
        <div class="absolute -top-24 -left-24 w-80 h-80 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none"></div>

        <div class="space-y-4 max-w-2xl relative z-10">
          <div class="flex flex-wrap items-center gap-2.5">
            <span class="px-2.5 py-1 rounded-full text-xs font-mono font-bold bg-white/10 text-white border border-white/15">
              {{ currentCompany.exchange }}: {{ currentCompany.ticker }}
            </span>
            <span class="text-xs text-slate-400 flex items-center gap-1">
              <Building2 class="w-3.5 h-3.5" />
              {{ currentCompany.sector }}
            </span>
            <span class="text-xs text-slate-500">·</span>
            <span class="text-xs text-slate-400">CIK {{ currentCompany.cik }}</span>
          </div>

          <h1 class="text-3xl sm:text-4xl font-extrabold display-title text-white">
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
              Auditor: {{ currentCompany.auditor }}
            </span>
          </div>

          <p class="text-xs sm:text-sm text-slate-300 leading-relaxed max-w-xl">
            Real-time synthesis of SEC EDGAR language revisions, forensic accrual quality, and earnings call tone decoupling to detect hidden liabilities.
          </p>
        </div>

        <!-- FFI Composite Risk Gauge Hero Card -->
        <div class="w-full lg:w-auto shrink-0 relative z-10">
          <div class="bg-slate-900/90 border border-white/10 rounded-2xl p-5 sm:p-6 flex flex-col items-center gap-4 text-center shadow-xl min-w-[280px]">
            <span class="text-[11px] font-semibold tracking-wider text-slate-400 uppercase">
              Forensic Fragility Index (FFI)
            </span>

            <div class="relative flex items-center justify-center">
              <!-- Radial Meter Badge -->
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

            <button
              @click="showInvestigationRunner = true"
              class="apple-press w-full py-2 px-4 rounded-xl bg-purple-600 hover:bg-purple-500 text-xs font-semibold text-white flex items-center justify-center gap-2 transition-all cursor-pointer shadow-xs"
            >
              <Terminal class="w-3.5 h-3.5" />
              <span>Launch Multi-Agent Audit</span>
              <ArrowRight class="w-3.5 h-3.5" />
            </button>

            <button
              @click="showScorecardModal = true"
              class="apple-press w-full py-2 px-4 rounded-xl bg-slate-800 hover:bg-slate-700/80 border border-white/10 text-xs font-semibold text-slate-200 hover:text-white flex items-center justify-center gap-2 transition-all cursor-pointer"
            >
              <Sliders class="w-3.5 h-3.5 text-emerald-400" />
              <span>Inspect Full Audit Scorecard</span>
              <ArrowRight class="w-3.5 h-3.5 text-slate-400" />
            </button>
          </div>
        </div>
      </section>

      <!-- 4 Core Forensic Intelligence Cards -->
      <section class="space-y-4">
        <div class="flex items-center justify-between">
          <div>
            <h2 class="text-lg font-bold text-white tracking-tight">Forensic Intelligence Radar</h2>
            <p class="text-xs text-slate-400">Continuous institutional monitoring across four analytical pillars</p>
          </div>
          <span class="text-xs text-slate-400 font-mono">SEC Edgar v2.1</span>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
          
          <!-- Card 1: Filing Language Drift -->
          <div class="apple-card rounded-2xl p-6 flex flex-col justify-between space-y-4">
            <div class="space-y-2.5">
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-2">
                  <div class="p-2 rounded-xl bg-amber-500/10 text-amber-400 border border-amber-500/20">
                    <GitCompare class="w-4 h-4" />
                  </div>
                  <h3 class="text-sm font-semibold text-white">Filing Language Drift</h3>
                </div>
                <span class="text-xs font-mono font-semibold px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-300 border border-amber-500/20">
                  {{ currentCompany.driftLabel }}
                </span>
              </div>

              <div class="flex items-center gap-3 text-xs text-slate-400">
                <span class="text-emerald-400 font-medium">+{{ currentCompany.driftAdded }} Risks Added</span>
                <span>·</span>
                <span class="text-slate-400">-{{ currentCompany.driftRemoved }} Headwinds Retired</span>
              </div>

              <blockquote class="text-xs text-slate-300 italic border-l-2 border-amber-500/40 pl-3 py-1 bg-slate-900/40 rounded-r-lg">
                "{{ currentCompany.driftExcerpt }}"
              </blockquote>
            </div>

            <div class="pt-2 flex items-center justify-between border-t border-white/5">
              <span class="text-[11px] text-slate-500">YoY Redline Semantic Matching</span>
              <button
                @click="showDiffModal = true"
                class="apple-press text-xs font-medium text-amber-400 hover:text-amber-300 flex items-center gap-1 cursor-pointer"
              >
                <span>Inspect Redline Diff</span>
                <ArrowRight class="w-3.5 h-3.5" />
              </button>
            </div>
          </div>

          <!-- Card 2: Beneish M-Score & Accrual Quality -->
          <div class="apple-card rounded-2xl p-6 flex flex-col justify-between space-y-4">
            <div class="space-y-2.5">
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-2">
                  <div class="p-2 rounded-xl bg-purple-500/10 text-purple-400 border border-purple-500/20">
                    <Calculator class="w-4 h-4" />
                  </div>
                  <h3 class="text-sm font-semibold text-white">Beneish M-Score Accruals</h3>
                </div>
                <span class="text-xs font-mono font-semibold px-2 py-0.5 rounded-full bg-purple-500/10 text-purple-300 border border-purple-500/20">
                  {{ currentCompany.mscoreLabel }}
                </span>
              </div>

              <div class="flex items-center gap-3 text-xs text-slate-400">
                <span>Threshold: <strong class="text-slate-200">-1.78</strong></span>
                <span>·</span>
                <span>Prob: <strong class="text-emerald-400">{{ currentCompany.mscoreProb }}</strong></span>
                <span>·</span>
                <span>TATA: <strong class="text-slate-200">{{ currentCompany.tataAccrual }}</strong></span>
              </div>

              <p class="text-xs text-slate-300 leading-relaxed bg-slate-900/40 p-2.5 rounded-lg border border-white/5">
                Total Accruals to Total Assets (TATA) and Asset Quality Index (AQI) indicate earnings are backed by operational cash collection.
              </p>
            </div>

            <div class="pt-2 flex items-center justify-between border-t border-white/5">
              <span class="text-[11px] text-slate-500">8-Factor Probabilistic Model</span>
              <button
                @click="showMScoreModal = true"
                class="apple-press text-xs font-medium text-purple-400 hover:text-purple-300 flex items-center gap-1 cursor-pointer"
              >
                <span>Audit Financial Accruals</span>
                <ArrowRight class="w-3.5 h-3.5" />
              </button>
            </div>
          </div>

          <!-- Card 3: Earnings Call vs 10-Q Radar -->
          <div class="apple-card rounded-2xl p-6 flex flex-col justify-between space-y-4">
            <div class="space-y-2.5">
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-2">
                  <div class="p-2 rounded-xl bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                    <Radio class="w-4 h-4" />
                  </div>
                  <h3 class="text-sm font-semibold text-white">Tone Decoupling Radar</h3>
                </div>
                <span class="text-xs font-mono font-semibold px-2 py-0.5 rounded-full bg-cyan-500/10 text-cyan-300 border border-cyan-500/20">
                  {{ currentCompany.radarLabel }}
                </span>
              </div>

              <div class="flex items-center gap-3 text-xs text-slate-400">
                <span>Cross-Encoder Sentiment</span>
                <span>·</span>
                <span class="text-emerald-400 font-medium">No Deceptive Decoupling</span>
              </div>

              <blockquote class="text-xs text-slate-300 italic border-l-2 border-cyan-500/40 pl-3 py-1 bg-slate-900/40 rounded-r-lg">
                "{{ currentCompany.radarExcerpt }}"
              </blockquote>
            </div>

            <div class="pt-2 flex items-center justify-between border-t border-white/5">
              <span class="text-[11px] text-slate-500">Audio Prepared Remarks vs MD&A</span>
              <button
                @click="showRadarModal = true"
                class="apple-press text-xs font-medium text-cyan-400 hover:text-cyan-300 flex items-center gap-1 cursor-pointer"
              >
                <span>Launch Contradiction Radar</span>
                <ArrowRight class="w-3.5 h-3.5" />
              </button>
            </div>
          </div>

          <!-- Card 4: Footnote Accounting Hazards -->
          <div class="apple-card rounded-2xl p-6 flex flex-col justify-between space-y-4">
            <div class="space-y-2.5">
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-2">
                  <div class="p-2 rounded-xl bg-rose-500/10 text-rose-400 border border-rose-500/20">
                    <ShieldAlert class="w-4 h-4" />
                  </div>
                  <h3 class="text-sm font-semibold text-white">Footnote Hazards & SOX 404</h3>
                </div>
                <span 
                  class="text-xs font-mono font-semibold px-2 py-0.5 rounded-full border"
                  :class="currentCompany.footnotesClean ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : 'bg-amber-500/10 text-amber-400 border-amber-500/20'"
                >
                  {{ currentCompany.footnoteCount }} Disclosures Flagged
                </span>
              </div>

              <div class="flex items-center gap-3 text-xs text-slate-400">
                <span>SOX 404 ICFR: <strong class="text-emerald-400">Clean</strong></span>
                <span>·</span>
                <span>HTM Losses: <strong class="text-slate-200">$0</strong></span>
              </div>

              <p class="text-xs text-slate-300 leading-relaxed bg-slate-900/40 p-2.5 rounded-lg border border-white/5">
                {{ currentCompany.footnoteExcerpt }}
              </p>
            </div>

            <div class="pt-2 flex items-center justify-between border-t border-white/5">
              <span class="text-[11px] text-slate-500">Automated NLP Disclosure Audit</span>
              <button
                @click="showMScoreModal = true"
                class="apple-press text-xs font-medium text-rose-400 hover:text-rose-300 flex items-center gap-1 cursor-pointer"
              >
                <span>Scan Footnote Disclosures</span>
                <ArrowRight class="w-3.5 h-3.5" />
              </button>
            </div>
          </div>

        </div>
      </section>

      <!-- Multi-Year Accrual & Financial Trends -->
      <section>
        <FinancialTrendsChart 
          :ticker="currentCompany.ticker" 
          @open-chat="emit('open-chat', $event)" 
        />
      </section>

      <!-- Sector Peer Comparative Risk Matrix & Heatmap -->
      <section>
        <PeerComparisonMatrix 
          :ticker="currentCompany.ticker" 
          @select-ticker="selectCompany" 
        />
      </section>

      <!-- Structured Financial Statements & Segment Extraction Studio -->
      <section>
        <FinancialTableExtractor 
          :ticker="currentCompany.ticker" 
          :company-name="currentCompany.name" 
        />
      </section>

      <!-- Multimodal Earnings Call Audio & Synchronized Transcript Simulator -->
      <section>
        <AudioCallSimulator 
          :ticker="currentCompany.ticker" 
          :company-name="currentCompany.name" 
        />
      </section>

      <!-- AI Macro Scenario Stress-Tester & Monte Carlo Risk Engine -->
      <section>
        <ScenarioStressTester 
          :ticker="currentCompany.ticker" 
          :company-name="currentCompany.name" 
        />
      </section>

      <!-- Indexed SEC Filings & Evidence Room -->
      <section class="space-y-4">
        <div class="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h2 class="text-lg font-bold text-white tracking-tight flex items-center gap-2">
              Regulatory Filings & Audio Evidence Room
              <span class="text-xs font-mono font-normal px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 border border-slate-700">
                {{ documents.length }} Document{{ documents.length !== 1 ? 's' : '' }}
              </span>
            </h2>
            <p class="text-xs text-slate-400">Indexed 10-K, 10-Q, 8-K filings and earnings call transcripts available for RAG inference</p>
          </div>

          <!-- Quick File Upload Drag / Trigger -->
          <label 
            class="apple-press text-xs font-medium px-3.5 py-1.5 rounded-xl border border-dashed border-slate-700 bg-slate-800/60 hover:bg-slate-800 text-slate-300 hover:text-white flex items-center gap-2 cursor-pointer transition-all"
            :class="{ 'opacity-50 pointer-events-none': isUploading }"
          >
            <Loader2 v-if="isUploading" class="w-3.5 h-3.5 animate-spin text-emerald-400" />
            <UploadCloud v-else class="w-3.5 h-3.5 text-emerald-400" />
            <span>Upload Document (PDF, HTML, TXT)</span>
            <input type="file" class="hidden" accept=".pdf,.html,.txt" @change="handleFileUpload" :disabled="isUploading" />
          </label>
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
              Use "Import SEC Filing" to ingest consecutive 10-Ks from SEC EDGAR, or upload a transcript PDF.
            </p>
          </div>

          <div v-else class="overflow-x-auto">
            <table class="w-full text-left text-xs text-slate-300">
              <thead class="bg-slate-950/60 text-slate-400 uppercase tracking-wider text-[10px] border-b border-white/5">
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
                        class="apple-press p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
                        title="View Raw Document"
                      >
                        <ExternalLink class="w-3.5 h-3.5" />
                      </a>

                      <button
                        @click="confirmDelete(doc)"
                        class="apple-press p-1.5 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-slate-800 transition-colors cursor-pointer"
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
      </section>

    </main>

    <!-- Floating Action Pill: Ask AI Co-Analyst -->
    <div class="fixed bottom-6 right-6 z-30">
      <button
        @click="emit('open-chat')"
        class="apple-press px-4 py-3 rounded-full bg-slate-900/90 hover:bg-slate-800 text-white font-medium text-xs sm:text-sm shadow-2xl border border-white/15 backdrop-blur-xl flex items-center gap-2.5 group cursor-pointer"
      >
        <span class="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse"></span>
        <Sparkles class="w-4 h-4 text-emerald-400 group-hover:rotate-12 transition-transform" />
        <span>Ask AI Co-Analyst</span>
        <kbd class="text-[10px] font-mono bg-slate-800 text-slate-400 px-1.5 py-0.5 rounded border border-slate-700 hidden sm:inline">Ctrl + K</kbd>
      </button>
    </div>

    <!-- Modals -->
    <FilingDiffModal :is-open="showDiffModal" @close="showDiffModal = false" />
    <ForensicMScoreModal :is-open="showMScoreModal" @close="showMScoreModal = false" />
    <ContradictionRadarModal :is-open="showRadarModal" @close="showRadarModal = false" />
    <ForensicScorecardModal 
      :is-open="showScorecardModal" 
      @close="showScorecardModal = false"
      @open-diff="showScorecardModal = false; showDiffModal = true"
      @open-mscore="showScorecardModal = false; showMScoreModal = true"
      @open-radar="showScorecardModal = false; showRadarModal = true"
    />

    <!-- Advanced Modals -->
    <FilingViewerModal 
      :is-open="showFilingViewerModal" 
      :ticker="currentCompany.ticker" 
      :initial-doc="selectedDocForViewer" 
      @close="showFilingViewerModal = false" 
      @open-chat="emit('open-chat', $event)" 
    />
    <ForensicInvestigationRunner 
      :is-open="showInvestigationRunner" 
      :ticker="currentCompany.ticker" 
      @close="showInvestigationRunner = false" 
      @open-chat="emit('open-chat', $event)" 
    />
    <TechStackDrawer 
      :is-open="showTechStackDrawer" 
      @close="showTechStackDrawer = false" 
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

    <!-- SEC EDGAR Ingestion Modal -->
    <Teleport to="body">
      <div 
        v-if="showSecModal" 
        class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-xs"
        @keydown.esc="showSecModal = false"
      >
        <div class="apple-glass rounded-2xl max-w-md w-full p-6 shadow-2xl space-y-5 text-slate-200">
          <div class="flex items-center justify-between border-b border-white/10 pb-4">
            <div class="flex items-center gap-2.5">
              <div class="p-2 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                <Globe class="w-5 h-5" />
              </div>
              <div>
                <h3 class="font-semibold text-white text-base">Import SEC EDGAR Filing</h3>
                <p class="text-xs text-slate-400">Directly ingest from the SEC EDGAR API</p>
              </div>
            </div>
            <button @click="showSecModal = false" class="text-slate-400 hover:text-white p-1 rounded-lg">
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
                class="w-full bg-slate-800 border border-slate-700 rounded-xl px-3 py-2.5 text-sm text-white focus:outline-none focus:border-emerald-500"
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
              class="apple-press px-4 py-2 text-xs font-medium rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300"
            >
              Cancel
            </button>
            <button
              @click="handleSecImport"
              :disabled="isImportingSec || !secTicker.trim()"
              class="apple-press px-4 py-2 text-xs font-semibold rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white flex items-center gap-2"
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
        class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-xs"
        @keydown.esc="cancelDelete"
      >
        <div class="apple-glass rounded-2xl max-w-sm w-full p-6 shadow-2xl space-y-4 text-slate-200">
          <div class="flex items-center gap-3">
            <div class="p-2.5 rounded-xl bg-rose-500/10 text-rose-400 border border-rose-500/20">
              <Trash2 class="w-5 h-5" />
            </div>
            <div>
              <h3 class="font-semibold text-white text-base">Delete Document</h3>
              <p class="text-xs text-slate-400">Remove from vector embeddings</p>
            </div>
          </div>

          <p class="text-xs text-slate-300 leading-relaxed">
            Are you sure you want to delete <span class="font-semibold text-white break-all">"{{ docToDelete?.source }}"</span>?
          </p>

          <div class="flex items-center justify-end gap-2.5 pt-2">
            <button
              @click="cancelDelete"
              :disabled="isDeleting"
              class="apple-press px-3.5 py-2 text-xs font-medium rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300"
            >
              Cancel
            </button>
            <button
              @click="executeDelete"
              :disabled="isDeleting"
              class="apple-press px-3.5 py-2 text-xs font-semibold rounded-xl bg-rose-600 hover:bg-rose-500 text-white flex items-center gap-2"
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
