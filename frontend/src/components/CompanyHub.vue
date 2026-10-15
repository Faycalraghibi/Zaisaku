<script setup>
import { ref, computed, onMounted } from 'vue'
import {
  FileText,
  Globe,
  UploadCloud,
  Loader2,
  ExternalLink,
  Trash2,
  Sparkles,
  X,
  Terminal,
  BookOpen,
  Cpu,
  Scale
} from 'lucide-vue-next'

import FilingDiffModal from './FilingDiffModal.vue'
import ForensicMScoreModal from './ForensicMScoreModal.vue'
import { useCompany } from '../composables/useCompany.js'
import TopBar from './shell/TopBar.vue'
import CompanyStrip from './shell/CompanyStrip.vue'
import OverviewDashboard from './overview/OverviewDashboard.vue'
import WatchlistView from './portfolio/WatchlistView.vue'
import { useWatchlist } from '../composables/useWatchlist.js'
import { useFlagReviews } from '../composables/useFlagReviews.js'
import { unresolvedCount } from '../utils/portfolio.js'
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
import AnomalyRadarModal from './AnomalyRadarModal.vue'

const emit = defineEmits(['open-chat', 'document-count-change', 'open-palette'])

// --- Active Navigation Tab ---
const currentTab = ref('overview')
const PORTFOLIO_TABS = ['watchlist', 'screener', 'compare']
const isPortfolioView = computed(() => PORTFOLIO_TABS.includes(currentTab.value))

const navigationTabs = computed(() => [
  { id: 'overview', label: 'Overview', section: 'company' },
  { id: 'financials', label: 'Financials', section: 'company' },
  { id: 'benchmarks', label: 'Trends & peers', section: 'company' },
  { id: 'scenarios', label: 'Scenarios', section: 'company' },
  { id: 'interrogation', label: 'Calls & Q&A', section: 'company' },
  { id: 'filings', label: 'Filings', section: 'company', count: documents.value.length || null },
  { id: 'watchlist', label: 'Watchlist', section: 'portfolio', count: watchlist.tickers.value.length || null }
])

// --- Modal Visibility States ---
const showDiffModal = ref(false)
const showMScoreModal = ref(false)
const mScoreInitialTab = ref('mscore')
const openMScoreModal = (tab) => {
  mScoreInitialTab.value = tab
  showMScoreModal.value = true
}
const showRadarModal = ref(false)
const showScorecardModal = ref(false)
const showSecModal = ref(false)
const showDeleteModal = ref(false)
const showFilingViewerModal = ref(false)
const showInvestigationRunner = ref(false)
const showSandboxModal = ref(false)
const showInstitutionalReportModal = ref(false)
const showAuditorModal = ref(false)
const showAnomalyModal = ref(false)
const selectedDocForViewer = ref(null)

const openFilingViewer = (doc = null) => {
  selectedDocForViewer.value = doc
  showFilingViewerModal.value = true
}

const { currentCompany, selectCompany } = useCompany()
const watchlist = useWatchlist()
const flagReviews = useFlagReviews()
const unresolvedForCurrent = computed(() =>
  unresolvedCount(currentCompany.value, flagReviews.reviewsFor(currentCompany.value.ticker))
)

// --- Documents (Filings tab) State ---
const documents = ref([])
const isLoadingDocs = ref(false)
const isUploading = ref(false)
const docErrorMsg = ref('')

const docsLoadError = ref(false)

const fetchDocuments = async () => {
  isLoadingDocs.value = true
  docErrorMsg.value = ''
  docsLoadError.value = false
  try {
    const res = await fetch('/api/documents')
    if (!res.ok) throw new Error(`Documents request failed (${res.status})`)
    const data = await res.json()
    documents.value = data.documents || []
    emit('document-count-change', documents.value.length)
  } catch (err) {
    docsLoadError.value = true
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

const switchWorkspace = (tabId) => {
  currentTab.value = tabId
}

const documentsState = computed(() => (isLoadingDocs.value ? 'loading' : docsLoadError.value ? 'error' : 'ready'))

const handleFlagAction = (action) => {
  if (action === 'diff') showDiffModal.value = true
  else if (action === 'radar') showRadarModal.value = true
  else if (action === 'footnotes') openMScoreModal('footnotes')
  else if (action === 'mscore') openMScoreModal('mscore')
}

const handleMemo = (id) => {
  if (id === 'preview') showInstitutionalReportModal.value = true
  else if (id === 'export') exportDueDiligenceMemo()
}

const handleTool = (id) => {
  if (id === 'run-audit') showInvestigationRunner.value = true
  else if (id === 'auditor-qa') showAuditorModal.value = true
  else if (id === 'scorecard') showScorecardModal.value = true
  else if (id === 'sandbox') showSandboxModal.value = true
}

const triggerAction = (actionId) => {
  if (actionId === 'sec-import') showSecModal.value = true
  else if (actionId === 'beneish-mscore') openMScoreModal('mscore')
  else if (actionId === 'auditor-studio') showAuditorModal.value = true
  else if (actionId === 'stress-tester') currentTab.value = 'scenarios'
  else if (actionId === 'export-memo') showInstitutionalReportModal.value = true
  else if (actionId === 'investigation-runner') showInvestigationRunner.value = true
  else if (actionId === 'filing-diff') showDiffModal.value = true
  else if (actionId === 'contradiction-radar') showRadarModal.value = true
  else if (actionId === 'footnote-scan') openMScoreModal('footnotes')
  else if (actionId === 'rag-sandbox') showSandboxModal.value = true
}

defineExpose({
  switchWorkspace,
  triggerAction,
  selectCompany,
  currentCompany
})

onMounted(async () => {
  watchlist.load()
  flagReviews.load()
  await fetchDocuments()
})
</script>

<template>
  <div class="flex-1 flex flex-col h-screen overflow-hidden bg-bg text-fg">
    
    <TopBar
      v-model:current-tab="currentTab"
      :tabs="navigationTabs"
      @open-palette="emit('open-palette')"
      @memo="handleMemo"
      @open-chat="emit('open-chat')"
    />
    <CompanyStrip
      v-if="!isPortfolioView"
      :company="currentCompany"
      :watched="watchlist.isWatched(currentCompany.ticker)"
      :unresolved="unresolvedForCurrent"
      @show-flags="currentTab = 'overview'"
      @toggle-watch="watchlist.toggle(currentCompany.ticker)"
      @tool="handleTool"
    />

    <!-- Workspace body. Legacy tabs stay in a dark island until their redesign phase. -->
    <main class="flex-1 overflow-y-auto custom-scrollbar">
        <Transition name="fade-view" mode="out-in">
          <OverviewDashboard
            v-if="currentTab === 'overview'"
            key="overview"
            :company="currentCompany"
            :documents="documents"
            :documents-state="documentsState"
            @open-scorecard="showScorecardModal = true"
            @open-anomaly="showAnomalyModal = true"
            @flag-action="handleFlagAction"
            @open-mscore="openMScoreModal('mscore')"
            @open-diff="showDiffModal = true"
            @go-tab="switchWorkspace"
            @open-sec="showSecModal = true"
            @open-filing="openFilingViewer"
            @retry-documents="fetchDocuments"
          />
          <WatchlistView v-else-if="currentTab === 'watchlist'" key="watchlist" @open-company="currentTab = 'overview'" />

          
          <!-- ========================================== -->
          <!-- VIEW 2: FINANCIALS & VISUAL EXHIBITS       -->
          <!-- ========================================== -->
          <div v-else-if="currentTab === 'financials'" key="financials" data-theme="dark" class="min-h-full bg-bg text-fg p-6 *:mx-auto *:max-w-7xl space-y-6">
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
          <div v-else-if="currentTab === 'benchmarks'" key="benchmarks" data-theme="dark" class="min-h-full bg-bg text-fg p-6 *:mx-auto *:max-w-7xl space-y-6">
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
          <div v-else-if="currentTab === 'scenarios'" key="scenarios" data-theme="dark" class="min-h-full bg-bg text-fg p-6 *:mx-auto *:max-w-7xl space-y-6">
            <ScenarioStressTester 
              :ticker="currentCompany.ticker" 
              :company-name="currentCompany.name" 
            />
          </div>

          <!-- ========================================== -->
          <!-- VIEW 5: AUDIO & ADVERSARIAL INQUIRIES      -->
          <!-- ========================================== -->
          <div v-else-if="currentTab === 'interrogation'" key="interrogation" data-theme="dark" class="min-h-full bg-bg text-fg p-6 *:mx-auto *:max-w-7xl space-y-6">
            <!-- Earnings Call Audio Simulator -->
            <AudioCallSimulator 
              :ticker="currentCompany.ticker" 
              :company-name="currentCompany.name" 
            />

            <!-- Forensic Inquiry Trigger Cards -->
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
              
              <!-- Trigger 1: Auditor Q&A -->
              <div class="apple-card rounded-2xl p-5 flex flex-col justify-between space-y-3">
                <div class="space-y-2">
                  <div class="p-2 rounded-xl bg-rose-500/10 text-rose-400 border border-rose-500/20 w-fit">
                    <Scale class="w-5 h-5" />
                  </div>
                  <h3 class="text-sm font-bold text-white">Auditor Q&amp;A</h3>
                  <p class="text-xs text-slate-300 leading-relaxed">
                    Prosecutorial interrogation simulating Big 4 / PCAOB and SEC Enforcement inquiries on revenue recognition cut-off and undisclosed liabilities.
                  </p>
                </div>
                <button
                  @click="showAuditorModal = true"
                  class="apple-press py-2 px-3.5 rounded-xl bg-rose-600 hover:bg-rose-500 text-white text-xs font-medium flex items-center justify-center cursor-pointer shadow-xs"
                >
                  Launch cross-examination
                </button>
              </div>

              <!-- Trigger 2: Audit run -->
              <div class="apple-card rounded-2xl p-5 flex flex-col justify-between space-y-3">
                <div class="space-y-2">
                  <div class="p-2 rounded-xl bg-purple-500/10 text-purple-400 border border-purple-500/20 w-fit">
                    <Terminal class="w-5 h-5" />
                  </div>
                  <h3 class="text-sm font-semibold text-white">Audit run</h3>
                  <p class="text-xs text-slate-300 leading-relaxed">
                    Dispatches synchronized specialized subagents across filings, transcripts, and footnotes with real-time SSE execution telemetry.
                  </p>
                </div>
                <button
                  @click="showInvestigationRunner = true"
                  class="apple-press py-2 px-3.5 rounded-xl bg-purple-600 hover:bg-purple-500 text-white text-xs font-medium flex items-center justify-center cursor-pointer shadow-xs"
                >
                  Run audit
                </button>
              </div>

              <!-- Trigger 3: AI Prompt & RAG Laboratory Sandbox -->
              <div class="apple-card rounded-2xl p-5 flex flex-col justify-between space-y-3">
                <div class="space-y-2">
                  <div class="p-2 rounded-xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 w-fit">
                    <Cpu class="w-5 h-5" />
                  </div>
                  <h3 class="text-sm font-semibold text-white">AI benchmark and RAG laboratory</h3>
                  <p class="text-xs text-slate-300 leading-relaxed">
                    Evaluate LLM reasoning latencies, hallucination rates, and cross-encoder reranking precision across institutional queries.
                  </p>
                </div>
                <button
                  @click="showSandboxModal = true"
                  class="apple-press py-2 px-3.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium flex items-center justify-center cursor-pointer shadow-xs"
                >
                  Open benchmark lab
                </button>
              </div>

            </div>
          </div>

          <!-- ========================================== -->
          <!-- VIEW 6: EVIDENCE ROOM (Filings & Documents)-->
          <!-- ========================================== -->
          <div v-else-if="currentTab === 'filings'" key="filings" data-theme="dark" class="min-h-full bg-bg text-fg p-6 *:mx-auto *:max-w-7xl space-y-4">
            
            <div class="flex flex-wrap items-center justify-between gap-4">
              <div>
                <h2 class="text-base font-bold text-white tracking-tight flex items-center gap-2">
                  Filings
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
                  <thead class="bg-[#161b22] text-slate-400 text-xs font-medium border-b border-white/10">
                    <tr>
                      <th class="py-3 px-4 font-medium">Document and source</th>
                      <th class="py-3 px-4 font-medium">Identifier</th>
                      <th class="py-3 px-4 font-medium">Status</th>
                      <th class="py-3 px-4 font-medium text-right">Actions</th>
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
                        <span class="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                          <span class="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
                          Indexed and vectorized
                        </span>
                      </td>
                      <td class="py-3.5 px-4 text-right">
                        <div class="flex items-center justify-end gap-2">
                          <button
                            @click="openFilingViewer(doc)"
                            class="apple-press px-2.5 py-1 rounded-lg bg-sky-500/10 hover:bg-sky-500/20 text-sky-400 border border-sky-500/20 text-xs font-medium flex items-center gap-1 cursor-pointer transition-colors"
                            title="Open interactive SEC document viewer"
                          >
                            <BookOpen class="w-3 h-3" />
                            <span>Viewer</span>
                          </button>

                          <button
                            @click="askAiAboutDoc(doc)"
                            class="apple-press px-2.5 py-1 rounded-lg bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/20 text-xs font-medium flex items-center gap-1 cursor-pointer transition-colors"
                            title="Ask Zaisaku about this document"
                          >
                            <Sparkles class="w-3 h-3" />
                            <span>Query filing</span>
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
      :initial-tab="mScoreInitialTab" 
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
    <AnomalyRadarModal
      :is-open="showAnomalyModal"
      :initial-ticker="currentCompany.ticker"
      @close="showAnomalyModal = false"
      @select-ticker="selectCompany"
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
.apple-press {
  transition: transform 0.15s cubic-bezier(0.32, 0.72, 0, 1), background-color 0.15s ease;
}

.fade-view-enter-active,
.fade-view-leave-active {
  transition: opacity 0.15s ease;
}

.fade-view-enter-from,
.fade-view-leave-to {
  opacity: 0;
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
  .fade-view-enter-active,
  .fade-view-leave-active {
    transition: none !important;
    transform: none !important;
  }
}
</style>
