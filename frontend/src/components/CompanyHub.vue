<script setup>
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
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
  Printer,
  ChevronDown,
  Check
} from 'lucide-vue-next'

import FilingDiffModal from './FilingDiffModal.vue'
import ForensicMScoreModal from './ForensicMScoreModal.vue'
import { ffiTier } from '../utils/ffi.js'
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

// --- Active Company State & Presets ---
const searchInput = ref('NVDA')
const isSearching = ref(false)
const searchResults = ref([])
const showSearchDropdown = ref(false)
const activeSearchIndex = ref(0)
let searchDebounceTimer = null

// --- Sector & Index Category Navigation ---
const activeCategory = ref('All')
const showCategoryMenu = ref(false)

const sectorCategories = [
  'All',
  'Macro Indices',
  'S&P 500',
  'Nasdaq 100',
  'Semiconductors',
  'Financials',
  'High-Risk'
]

const categoryTickerMap = {
  'All': ['SPY', 'QQQ', 'NVDA', 'AAPL', 'MSFT', 'TSLA', 'AMZN', 'SMCI'],
  'Macro Indices': ['SPY', 'QQQ', 'DIA', 'IWM', 'SMH', 'XLK', 'XLF'],
  'S&P 500': ['SPY', 'AAPL', 'MSFT', 'NVDA', 'AMZN', 'GOOGL', 'META', 'BRK.B', 'JPM'],
  'Nasdaq 100': ['QQQ', 'NVDA', 'AAPL', 'MSFT', 'AMZN', 'AVGO', 'META', 'TSLA', 'COST'],
  'Semiconductors': ['SMH', 'NVDA', 'AVGO', 'AMD', 'INTC'],
  'Financials': ['XLF', 'JPM', 'BAC', 'GS', 'BRK.B', 'V'],
  'High-Risk': ['SMCI', 'COIN', 'RIVN', 'BA', 'TSLA']
}

const visibleCategoryTickers = computed(() => {
  return categoryTickerMap[activeCategory.value] || categoryTickerMap['All']
})

const isIndexTicker = (ticker) => {
  return ['SPY', 'QQQ', 'DIA', 'IWM', 'SMH', 'XLK', 'XLF'].includes((ticker || '').toUpperCase())
}

const companyProfiles = {
  // --- Macro Market Benchmark Indices & Sector ETFs ---
  SPY: {
    ticker: 'SPY',
    name: 'SPDR S&P 500 ETF Trust',
    exchange: 'NYSE Arca',
    cik: '0000884394',
    sector: 'Large-Cap US Equities Core Benchmark',
    period: 'FY2024 / Q3 FY2025 S&P 500 Benchmark Review',
    auditor: 'State Street Global Advisors Trust Custody',
    ffi: 22.5,
    riskTier: 'LOW_RISK',
    is_macro_index: true,
    constituents: ['MSFT', 'AAPL', 'NVDA', 'AMZN', 'GOOGL', 'META', 'BRK.B'],
    driftScore: 5.4,
    driftLabel: 'Minimal Rebalancing Drift (5.4%)',
    driftAdded: 2,
    driftRemoved: 1,
    driftExcerpt: 'Quarterly constituent rebalancing and market capitalization float-adjusted weight adjustments.',
    mscore: -3.10,
    mscoreLabel: 'Aggregate Robust Accounting (-3.10)',
    mscoreProb: '< 0.5%',
    tataAccrual: -0.055,
    divergenceScore: 9.2,
    radarLabel: 'Harmonized Macro Guidance (9.2 / 100)',
    radarExcerpt: 'Aggregated earnings commentary across 500 leading corporations reflects disciplined operational leverage.',
    footnotesClean: true,
    footnoteCount: 0,
    footnoteExcerpt: 'Index physical replication fidelity < 0.03% tracking variance.'
  },
  QQQ: {
    ticker: 'QQQ',
    name: 'Invesco QQQ Trust',
    exchange: 'NASDAQ',
    cik: '0001067839',
    sector: 'Nasdaq-100 Growth & Technology Benchmark',
    period: 'FY2024 / Q3 FY2025 Annual Reconstitution',
    auditor: 'The Bank of New York Mellon Custody',
    ffi: 24.8,
    riskTier: 'LOW_RISK',
    is_macro_index: true,
    constituents: ['NVDA', 'AAPL', 'MSFT', 'AMZN', 'AVGO', 'META', 'TSLA'],
    driftScore: 7.8,
    driftLabel: 'Tech Exposure Realignment (7.8%)',
    driftAdded: 3,
    driftRemoved: 2,
    driftExcerpt: 'Special rebalancing rules enacted to constrain mega-cap technology concentration caps.',
    mscore: -2.95,
    mscoreLabel: 'High Quality Large-Cap Cash Flows (-2.95)',
    mscoreProb: '< 0.8%',
    tataAccrual: -0.060,
    divergenceScore: 12.4,
    radarLabel: 'Synchronized AI Guidance (12.4 / 100)',
    radarExcerpt: 'Hyperscaler capital expenditure roadmaps correspond with high-margin enterprise cloud bookings.',
    footnotesClean: true,
    footnoteCount: 0,
    footnoteExcerpt: 'Zero synthetic derivative leverage. Unbroken tracking continuity.'
  },
  DIA: {
    ticker: 'DIA',
    name: 'SPDR Dow Jones Industrial Average ETF',
    exchange: 'NYSE Arca',
    cik: '0001064641',
    sector: 'Blue-Chip US Mega-Cap Benchmark',
    period: 'Annual Price-Weighted Review',
    auditor: 'State Street Bank and Trust Company',
    ffi: 19.4,
    riskTier: 'LOW_RISK',
    is_macro_index: true,
    constituents: ['UNH', 'GS', 'MSFT', 'HD', 'CAT', 'MCD', 'BA'],
    driftScore: 4.8,
    driftLabel: 'Disciplined Blue-Chip Drift (4.8%)',
    driftAdded: 1,
    driftRemoved: 1,
    driftExcerpt: 'Constituent price-weighting adjustments preserving cross-industry balance.',
    mscore: -3.05,
    mscoreLabel: 'Blue-Chip Balance Sheets (-3.05)',
    mscoreProb: '< 0.5%',
    tataAccrual: -0.052,
    divergenceScore: 8.8,
    radarLabel: 'High Guidance Predictability (8.8 / 100)',
    radarExcerpt: 'Mature dividend-paying industrial leaders maintain high-certainty forward margin visibility.',
    footnotesClean: true,
    footnoteCount: 0,
    footnoteExcerpt: 'Standard physical custody disclosures and clean audit compliance.'
  },
  IWM: {
    ticker: 'IWM',
    name: 'iShares Russell 2000 ETF',
    exchange: 'NYSE Arca',
    cik: '0001100663',
    sector: 'Small-Cap US Equities Benchmark',
    period: 'Annual Russell Reconstitution',
    auditor: 'BlackRock Fund Advisors Custody',
    ffi: 44.2,
    riskTier: 'WATCHLIST',
    is_macro_index: true,
    constituents: ['FTAI', 'VRT', 'SMCI', 'MEDP', 'ENSG', 'SAIA'],
    driftScore: 28.5,
    driftLabel: 'Small-Cap Liquidity & Credit Drift (28.5%)',
    driftAdded: 12,
    driftRemoved: 8,
    driftExcerpt: 'Refinancing sensitivity to elevated floating interest rates and regional banking credit conditions.',
    mscore: -1.98,
    mscoreLabel: 'Elevated Non-Cash Accruals (-1.98)',
    mscoreProb: '14.2%',
    tataAccrual: 0.038,
    divergenceScore: 34.0,
    radarLabel: 'Dispersed Earnings Guidance (34.0 / 100)',
    radarExcerpt: 'Executive projections demonstrate wide variance between profitable compounders and debt-leveraged filers.',
    footnotesClean: false,
    footnoteCount: 3,
    footnoteExcerpt: '40% of small-cap constituents report negative trailing net income. Heightened 2026 debt wall.'
  },
  SMH: {
    ticker: 'SMH',
    name: 'VanEck Semiconductor ETF',
    exchange: 'NASDAQ',
    cik: '0001524316',
    sector: 'Semiconductor Hardware Sector Benchmark',
    period: 'MVIS US Listed Semiconductor 25 Index Review',
    auditor: 'Van Eck Associates Corporation',
    ffi: 31.0,
    riskTier: 'WATCHLIST',
    is_macro_index: true,
    constituents: ['NVDA', 'TSM', 'AVGO', 'AMD', 'QCOM', 'ASML', 'TXN'],
    driftScore: 16.2,
    driftLabel: 'Geopolitical & Fab Capacity Drift (16.2%)',
    driftAdded: 6,
    driftRemoved: 3,
    driftExcerpt: 'Foundry allocation bottlenecks, advanced packaging constraints, and multilateral export control updates.',
    mscore: -2.60,
    mscoreLabel: 'Capital Discipline (-2.60)',
    mscoreProb: '< 2.5%',
    tataAccrual: -0.032,
    divergenceScore: 18.0,
    radarLabel: 'Cyclical Tone Alignment (18.0 / 100)',
    radarExcerpt: 'Silicon wafer fab utilization rates correlate with hyperscaler custom accelerator and GPU demand.',
    footnotesClean: true,
    footnoteCount: 1,
    footnoteExcerpt: 'Customer concentration risks in leading fabless designers; TSMC advanced node concentration.'
  },
  XLK: {
    ticker: 'XLK',
    name: 'Technology Select Sector SPDR Fund',
    exchange: 'NYSE Arca',
    cik: '0001064642',
    sector: 'Enterprise Tech & Cloud Benchmark',
    period: 'Technology Select Sector Index Reconstitution',
    auditor: 'State Street Bank and Trust Company',
    ffi: 21.8,
    riskTier: 'LOW_RISK',
    is_macro_index: true,
    constituents: ['MSFT', 'NVDA', 'AAPL', 'AVGO', 'CRM', 'AMD', 'ORCL'],
    driftScore: 6.8,
    driftLabel: 'Software & Silicon Rebalancing (6.8%)',
    driftAdded: 3,
    driftRemoved: 1,
    driftExcerpt: 'Quarterly capping mechanisms maintaining diversification between enterprise SaaS and hardware.',
    mscore: -2.88,
    mscoreLabel: 'Robust Free Cash Conversion (-2.88)',
    mscoreProb: '< 1%',
    tataAccrual: -0.058,
    divergenceScore: 11.2,
    radarLabel: 'Harmonized Enterprise Demand (11.2 / 100)',
    radarExcerpt: 'Enterprise recurring ARR metrics aligned with low cancellation rates and high retention rates.',
    footnotesClean: true,
    footnoteCount: 0,
    footnoteExcerpt: 'Clean index replication with tight tracking efficiency.'
  },
  XLF: {
    ticker: 'XLF',
    name: 'Financial Select Sector SPDR Fund',
    exchange: 'NYSE Arca',
    cik: '0001064643',
    sector: 'Money Center Banks & Financials Benchmark',
    period: 'Financial Select Sector Index Reconstitution',
    auditor: 'State Street Bank and Trust Company',
    ffi: 27.2,
    riskTier: 'LOW_RISK',
    is_macro_index: true,
    constituents: ['BRK.B', 'JPM', 'V', 'MA', 'BAC', 'WFC', 'GS'],
    driftScore: 11.5,
    driftLabel: 'Capital Adequacy & Net Interest Drift (11.5%)',
    driftAdded: 5,
    driftRemoved: 2,
    driftExcerpt: 'Basel III endgame capital requirements and commercial real estate portfolio stress reserves.',
    mscore: -2.70,
    mscoreLabel: 'Regulated Bank Solvency (-2.70)',
    mscoreProb: '< 1.5%',
    tataAccrual: -0.042,
    divergenceScore: 15.5,
    radarLabel: 'Credit Cycle Alignment (15.5 / 100)',
    radarExcerpt: 'Net interest income outlooks reflect deposit beta stabilization and solid loan underwriting.',
    footnotesClean: true,
    footnoteCount: 1,
    footnoteExcerpt: 'Unrealized losses in held-to-maturity (HTM) securities fully disclosed and stress-tested.'
  },

  // --- Curated Institutional Equities ---
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
  },
  SMCI: {
    ticker: 'SMCI',
    name: 'Super Micro Computer, Inc.',
    exchange: 'NASDAQ',
    cik: '0001375365',
    sector: 'Server Hardware & AI Datacenters',
    period: 'FY2024 Form 10-K (Delinquent) & Form 8-K',
    auditor: 'Ernst & Young LLP (Resigned Oct 2024)',
    ffi: 84,
    riskTier: 'CRITICAL_ALERT',
    driftScore: 42.0,
    driftLabel: 'Severe Governance Drift (42.0%)',
    driftAdded: 18,
    driftRemoved: 9,
    driftExcerpt: 'Special Committee investigation into internal financial controls and related party commercial relationships.',
    mscore: -1.42,
    mscoreLabel: 'Probable Manipulation (-1.42)',
    mscoreProb: '76%',
    tataAccrual: 0.124,
    divergenceScore: 78.5,
    radarLabel: 'Hostile Divergence (78.5 / 100)',
    radarExcerpt: 'Guidance and press releases conflict sharply with delinquent 10-K filing status and auditor resignation.',
    footnotesClean: false,
    footnoteCount: 4,
    footnoteExcerpt: 'PCAOB Rule 3526 resignation of certifying accountant. Form 12b-25 late filing notifications pending.'
  },
  GOOGL: {
    ticker: 'GOOGL',
    name: 'Alphabet Inc.',
    exchange: 'NASDAQ',
    cik: '0001652044',
    sector: 'Internet Services & Generative AI',
    period: 'FY2024 Form 10-K & Q3 Form 10-Q',
    auditor: 'Deloitte & Touche LLP',
    ffi: 16.5,
    riskTier: 'LOW_RISK',
    driftScore: 7.2,
    driftLabel: 'Predictable Disclosures (7.2%)',
    driftAdded: 3,
    driftRemoved: 1,
    driftExcerpt: 'Antitrust regulatory litigation updates and Google Cloud enterprise AI infrastructure capex.',
    mscore: -2.88,
    mscoreLabel: 'Clean Cash Flow Profile (-2.88)',
    mscoreProb: '< 1%',
    tataAccrual: -0.048,
    divergenceScore: 9.8,
    radarLabel: 'Disciplined Guidance (9.8 / 100)',
    radarExcerpt: 'Search monetization resilience and Cloud operating margin expansion correspond with MD&A disclosures.',
    footnotesClean: true,
    footnoteCount: 0,
    footnoteExcerpt: 'Diversified worldwide revenues. Clean internal controls audit report.'
  },
  META: {
    ticker: 'META',
    name: 'Meta Platforms, Inc.',
    exchange: 'NASDAQ',
    cik: '0001326801',
    sector: 'Social Technologies & AI Advertising',
    period: 'FY2024 Form 10-K & Q3 Form 10-Q',
    auditor: 'Ernst & Young LLP',
    ffi: 21.0,
    riskTier: 'LOW_RISK',
    driftScore: 9.0,
    driftLabel: 'Disciplined Growth (9.0%)',
    driftAdded: 4,
    driftRemoved: 2,
    driftExcerpt: 'Reality Labs operating losses and data center silicon compute infrastructure scaling commitments.',
    mscore: -2.75,
    mscoreLabel: 'High Cash Conversion (-2.75)',
    mscoreProb: '< 1.2%',
    tataAccrual: -0.044,
    divergenceScore: 13.5,
    radarLabel: 'Consistent Commentary (13.5 / 100)',
    radarExcerpt: 'Family of Apps ad pricing leverage aligns with reported free cash flow margin trajectory.',
    footnotesClean: true,
    footnoteCount: 1,
    footnoteExcerpt: 'Legal proceedings regarding global data protection and minor child safety frameworks.'
  },
  AVGO: {
    ticker: 'AVGO',
    name: 'Broadcom Inc.',
    exchange: 'NASDAQ',
    cik: '0001730168',
    sector: 'Semiconductors & Infrastructure Software',
    period: 'FY2024 Form 10-K & Q4 Form 10-Q',
    auditor: 'PricewaterhouseCoopers LLP',
    ffi: 24.5,
    riskTier: 'LOW_RISK',
    driftScore: 11.2,
    driftLabel: 'VMware Integration Drift (11.2%)',
    driftAdded: 5,
    driftRemoved: 2,
    driftExcerpt: 'VMware subscription transition model and custom AI ASIC foundry delivery commitments.',
    mscore: -2.62,
    mscoreLabel: 'High Cash Quality (-2.62)',
    mscoreProb: '< 2%',
    tataAccrual: -0.035,
    divergenceScore: 14.0,
    radarLabel: 'Predictable Integration (14.0 / 100)',
    radarExcerpt: 'AI networking switch bookings align with hyperscaler purchase order schedules.',
    footnotesClean: true,
    footnoteCount: 1,
    footnoteExcerpt: 'Customer concentration in top custom silicon hyperscaler accounts for ~15% of net revenue.'
  },
  AMD: {
    ticker: 'AMD',
    name: 'Advanced Micro Devices, Inc.',
    exchange: 'NASDAQ',
    cik: '0000002488',
    sector: 'Semiconductors & Datacenter Compute',
    period: 'FY2024 Form 10-K & Q3 Form 10-Q',
    auditor: 'Ernst & Young LLP',
    ffi: 27.0,
    riskTier: 'LOW_RISK',
    driftScore: 12.5,
    driftLabel: 'GPU Acceleration Ramp (12.5%)',
    driftAdded: 5,
    driftRemoved: 2,
    driftExcerpt: 'MI300 datacenter GPU revenue recognition schedules and client PC inventory normalization.',
    mscore: -2.52,
    mscoreLabel: 'Standard Accruals (-2.52)',
    mscoreProb: '< 2.5%',
    tataAccrual: -0.028,
    divergenceScore: 16.5,
    radarLabel: 'Prudent Margin Targets (16.5 / 100)',
    radarExcerpt: 'Executive GPU revenue guidance corresponds with reported supply commitments at TSMC.',
    footnotesClean: true,
    footnoteCount: 1,
    footnoteExcerpt: 'Supply agreement commitments with external semiconductor wafer fabrication foundries.'
  },
  JPM: {
    ticker: 'JPM',
    name: 'JPMorgan Chase & Co.',
    exchange: 'NYSE',
    cik: '0000019617',
    sector: 'Investment Banking & Asset Management',
    period: 'FY2024 Form 10-K & Q3 Form 10-Q',
    auditor: 'PricewaterhouseCoopers LLP',
    ffi: 19.0,
    riskTier: 'LOW_RISK',
    driftScore: 8.0,
    driftLabel: 'Fortress Balance Sheet Drift (8.0%)',
    driftAdded: 3,
    driftRemoved: 1,
    driftExcerpt: 'Basel III endgame regulatory capital rules and net interest income rate sensitivity modeling.',
    mscore: -2.95,
    mscoreLabel: 'Fortress Solvency Profile (-2.95)',
    mscoreProb: '< 1%',
    tataAccrual: -0.050,
    divergenceScore: 10.5,
    radarLabel: 'Disciplined Banking Outlook (10.5 / 100)',
    radarExcerpt: 'Credit card net charge-off guidance accurately reflects observed loan loss provisioning.',
    footnotesClean: true,
    footnoteCount: 0,
    footnoteExcerpt: 'Allowance for credit losses fully supported. Unqualified internal controls audit.'
  },
  BA: {
    ticker: 'BA',
    name: 'The Boeing Company',
    exchange: 'NYSE',
    cik: '0000012927',
    sector: 'Aerospace & Commercial Defense OEM',
    period: 'FY2024 Form 10-K & Q3 Form 10-Q',
    auditor: 'Deloitte & Touche LLP',
    ffi: 58.0,
    riskTier: 'WATCHLIST',
    driftScore: 31.0,
    driftLabel: 'Elevated Operational Drift (31.0%)',
    driftAdded: 11,
    driftRemoved: 5,
    driftExcerpt: 'FAA production rate caps, IAM union labor work stoppages, and fixed-price defense program cost overruns.',
    mscore: -1.82,
    mscoreLabel: 'Strained Contract Accounting (-1.82)',
    mscoreProb: '22.5%',
    tataAccrual: 0.058,
    divergenceScore: 48.0,
    radarLabel: 'Divergent Cash Flow Narrative (48.0 / 100)',
    radarExcerpt: 'Optimistic spoken delivery timeline targets diverge from negative operating cash burn in 10-Q disclosures.',
    footnotesClean: false,
    footnoteCount: 3,
    footnoteExcerpt: '737 MAX quality assurance FAA directives. Liquidity credit facility amendments and equity dilution.'
  },
  COIN: {
    ticker: 'COIN',
    name: 'Coinbase Global, Inc.',
    exchange: 'NASDAQ',
    cik: '0001679788',
    sector: 'Digital Asset Exchange & Custody Platform',
    period: 'FY2024 Form 10-K & Q3 Form 10-Q',
    auditor: 'Deloitte & Touche LLP',
    ffi: 62.0,
    riskTier: 'WATCHLIST',
    driftScore: 34.5,
    driftLabel: 'Regulatory Litigation Drift (34.5%)',
    driftAdded: 14,
    driftRemoved: 6,
    driftExcerpt: 'SEC civil litigation under federal securities laws and crypto asset trading volume cyclicality.',
    mscore: -2.05,
    mscoreLabel: 'Volatile Transaction Accruals (-2.05)',
    mscoreProb: '8.4%',
    tataAccrual: 0.025,
    divergenceScore: 52.0,
    radarLabel: 'Volatile Revenue Guidance (52.0 / 100)',
    radarExcerpt: 'Subscription & services revenue claims diverge from episodic retail trading fee compression.',
    footnotesClean: false,
    footnoteCount: 3,
    footnoteExcerpt: 'Custodial crypto asset safeguarding obligations under SEC SAB 121 accounting.'
  }
}

const currentCompany = ref(companyProfiles.NVDA)

const selectCompany = (ticker, entryData = null) => {
  const t = (ticker || '').toUpperCase().trim()
  if (!t) return

  if (entryData) {
    const isMacro = entryData.is_macro_index || isIndexTicker(t)
    currentCompany.value = {
      ticker: t,
      name: entryData.name || `${t} Corporation`,
      exchange: entryData.exchange || (isMacro ? 'NYSE Arca' : 'NYSE/NASDAQ'),
      cik: entryData.cik || '0000000000',
      sector: entryData.sector || (isMacro ? 'Macro Market Benchmark' : 'Diversified Enterprise'),
      period: isMacro ? 'Market Benchmark Index Review' : 'Form 10-K / 10-Q Disclosures',
      auditor: isMacro ? 'Institutional Benchmark Trustee' : 'Independent Registered Public Accounting Firm',
      ffi: Math.round(entryData.ffi_score || 22),
      riskTier: entryData.risk_tier || 'LOW_RISK',
      is_macro_index: isMacro,
      constituents: isMacro ? (companyProfiles[t]?.constituents || ['NVDA', 'AAPL', 'MSFT', 'AMZN', 'GOOGL']) : [],
      driftScore: 9.5,
      driftLabel: 'Standard Risk Drift (9.5%)',
      driftAdded: 3,
      driftRemoved: 1,
      driftExcerpt: 'Operational and strategic risk disclosures conforming with trailing SEC reporting periods.',
      mscore: -2.65,
      mscoreLabel: 'Normalized Accruals (-2.65)',
      mscoreProb: '< 1.5%',
      tataAccrual: -0.040,
      divergenceScore: 12.0,
      radarLabel: 'Aligned Guidance (12.0 / 100)',
      radarExcerpt: 'Management forward guidance corresponds with reported cash flow and balance sheet metrics.',
      footnotesClean: true,
      footnoteCount: 0,
      footnoteExcerpt: 'Standard disclosure footnotes. Unqualified audit opinion on internal controls.'
    }
  } else if (companyProfiles[t]) {
    currentCompany.value = companyProfiles[t]
  } else {
    const isMacro = isIndexTicker(t)
    currentCompany.value = {
      ticker: t,
      name: `${t} Corporation`,
      exchange: isMacro ? 'NYSE Arca' : 'NYSE/NASDAQ',
      cik: '0000000000',
      sector: isMacro ? 'Macro Market Benchmark' : 'Diversified Enterprise',
      period: 'Form 10-K Annual Filing',
      auditor: 'Big 4 Independent Audit Committee',
      ffi: isMacro ? 22 : 20,
      riskTier: 'LOW_RISK',
      is_macro_index: isMacro,
      constituents: isMacro ? ['NVDA', 'AAPL', 'MSFT', 'AMZN', 'GOOGL'] : [],
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

// --- Live Autocomplete Search Handler ---
const onSearchInput = () => {
  const q = searchInput.value.trim()
  if (searchDebounceTimer) clearTimeout(searchDebounceTimer)
  if (!q) {
    searchResults.value = []
    showSearchDropdown.value = false
    isSearching.value = false
    return
  }
  isSearching.value = true
  searchDebounceTimer = setTimeout(async () => {
    try {
      const res = await fetch(`/api/forensics/tickers/search?q=${encodeURIComponent(q)}&limit=8`)
      if (res.ok) {
        const data = await res.json()
        searchResults.value = data.results || []
        showSearchDropdown.value = searchResults.value.length > 0
        activeSearchIndex.value = 0
      }
    } catch (e) {
      console.error('Ticker search failed:', e)
    } finally {
      isSearching.value = false
    }
  }, 180)
}

const selectSearchResult = (item) => {
  selectCompany(item.ticker, item)
  showSearchDropdown.value = false
  searchInput.value = item.ticker
}

const handleSearchEnter = () => {
  if (showSearchDropdown.value && searchResults.value.length > 0) {
    selectSearchResult(searchResults.value[activeSearchIndex.value] || searchResults.value[0])
  } else if (searchInput.value.trim()) {
    selectCompany(searchInput.value.trim())
    showSearchDropdown.value = false
  }
}

const navigateSearch = (dir) => {
  if (!showSearchDropdown.value || searchResults.value.length === 0) return
  activeSearchIndex.value = (activeSearchIndex.value + dir + searchResults.value.length) % searchResults.value.length
}

const handleClickOutside = (e) => {
  const target = e.target
  if (!target.closest('.category-menu-container')) {
    showCategoryMenu.value = false
  }
  if (!target.closest('.search-autocomplete-container')) {
    showSearchDropdown.value = false
  }
}

onMounted(() => {
  window.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  window.removeEventListener('click', handleClickOutside)
})

// --- FFI Color Styling ---
const ffiColor = ffiTier

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

const switchWorkspace = (tabId) => {
  currentTab.value = tabId
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
  else if (actionId === 'footnote-scan') showScorecardModal.value = true
  else if (actionId === 'rag-sandbox') showSandboxModal.value = true
}

defineExpose({
  switchWorkspace,
  triggerAction,
  selectCompany,
  currentCompany
})

onMounted(async () => {
  await fetchDocuments()
})
</script>

<template>
  <div class="flex-1 flex flex-col h-screen overflow-hidden bg-[#0d1117] text-slate-100 font-sans">
    
    <!-- Top Persistent Apple Frosted Glass Header -->
    <header class="apple-glass sticky top-0 z-30 px-6 py-3 flex flex-wrap xl:flex-nowrap items-center justify-between gap-4 border-b border-white/8 shrink-0">
      
      <!-- Brand & Platform Scope -->
      <div class="flex items-center gap-3 shrink-0">
        <div class="w-8 h-8 rounded-xl bg-slate-800/90 border border-white/10 flex items-center justify-center text-slate-100 font-bold text-sm tracking-tight shadow-xs">
          Z
        </div>
        <div>
          <div class="flex items-center gap-2">
            <span class="text-sm font-semibold tracking-tight text-white">ZAISAKU</span>
            <span class="hidden 2xl:inline text-[11px] font-medium px-2 py-0.5 rounded-md bg-white/5 text-slate-300 border border-white/10 whitespace-nowrap">
              Enterprise 2.4
            </span>
          </div>
          <p class="hidden 2xl:block text-xs text-slate-400">Institutional financial forensics and due diligence</p>
        </div>
      </div>

      <!-- Quick Ticker Switcher & Multi-Index Ribbon -->
      <div class="flex items-center gap-2 min-w-0">
        <!-- Sector / Index Filter Dropdown -->
        <div class="relative category-menu-container">
          <button
            @click="showCategoryMenu = !showCategoryMenu"
            class="apple-press flex items-center gap-1.5 px-2.5 py-1.5 rounded-xl bg-slate-900/90 border border-white/10 hover:border-white/20 text-xs font-medium text-slate-300 cursor-pointer shadow-xs"
            title="Filter by Market Benchmark or Sector"
          >
            <Layers class="w-3.5 h-3.5 text-emerald-400" />
            <span class="font-semibold text-white whitespace-nowrap">{{ activeCategory }}</span>
            <ChevronDown class="w-3 h-3 text-slate-400 transition-transform duration-200" :class="showCategoryMenu ? 'rotate-180' : ''" />
          </button>

          <!-- Category Dropdown Menu -->
          <div
            v-if="showCategoryMenu"
            class="absolute top-full left-0 mt-1.5 w-48 rounded-xl bg-slate-900/95 backdrop-blur-2xl border border-white/15 p-1 shadow-2xl z-50 animate-fadeIn"
          >
            <button
              v-for="cat in sectorCategories"
              :key="cat"
              @click="activeCategory = cat; showCategoryMenu = false"
              class="apple-press w-full flex items-center justify-between px-3 py-1.5 rounded-lg text-xs font-medium transition-all cursor-pointer text-left"
              :class="activeCategory === cat ? 'bg-emerald-500/15 text-emerald-300 font-semibold' : 'text-slate-300 hover:bg-white/5'"
            >
              <span>{{ cat }}</span>
              <Check v-if="activeCategory === cat" class="w-3.5 h-3.5 text-emerald-400" />
            </button>
          </div>
        </div>

        <!-- Ticker Quick Buttons for Active Category -->
        <div class="flex items-center gap-1 p-1 rounded-xl bg-slate-900/80 border border-white/10 overflow-x-auto min-w-0 max-w-[280px] sm:max-w-[360px] md:max-w-[440px] scrollbar-none">
          <button
            v-for="ticker in visibleCategoryTickers"
            :key="ticker"
            @click="selectCompany(ticker)"
            class="apple-press px-2.5 py-1 rounded-lg text-xs font-semibold transition-all cursor-pointer font-mono shrink-0"
            :class="currentCompany.ticker === ticker 
              ? (ticker === 'SMCI' ? 'bg-rose-600 text-white font-semibold shadow-xs' : (isIndexTicker(ticker) ? 'bg-blue-600 text-white font-semibold shadow-xs' : 'bg-white text-slate-950 font-semibold shadow-xs'))
              : 'text-slate-400 hover:text-white hover:bg-slate-800/60'"
          >
            {{ ticker }}
          </button>
        </div>

        <!-- Universal Autocomplete Search Bar -->
        <div class="relative search-autocomplete-container hidden sm:block">
          <div class="relative flex items-center">
            <Search class="w-3.5 h-3.5 text-slate-500 absolute left-2.5 pointer-events-none" />
            <input
              v-model="searchInput"
              @input="onSearchInput"
              @focus="showSearchDropdown = searchResults.length > 0"
              @keydown.enter="handleSearchEnter"
              @keydown.escape="showSearchDropdown = false"
              @keydown.down.prevent="navigateSearch(1)"
              @keydown.up.prevent="navigateSearch(-1)"
              placeholder="Search 10k+ SEC filers & indices..."
              class="w-36 lg:w-48 xl:w-56 pl-7 pr-11 py-1.5 text-xs bg-slate-800/80 rounded-xl text-white placeholder:text-slate-500 focus:outline-none focus:w-48 lg:focus:w-60 transition-all border border-transparent focus:border-white/20"
            />
            <Loader2 v-if="isSearching" class="w-3 h-3 text-slate-300 animate-spin absolute right-2.5 pointer-events-none" />
            <button
              v-else
              type="button"
              @click="emit('open-palette')"
              class="absolute right-1.5 text-[10px] font-mono bg-slate-900 px-1.5 py-0.5 rounded border border-white/10 text-slate-400 hover:text-white cursor-pointer"
              title="Open command palette (⌘K)"
              aria-label="Open command palette"
            >⌘K</button>
          </div>

          <!-- Instant Search Dropdown -->
          <div
            v-if="showSearchDropdown && searchResults.length > 0"
            class="absolute top-full left-0 mt-1.5 w-80 xl:w-96 rounded-2xl bg-slate-900/98 backdrop-blur-2xl border border-white/15 p-2 shadow-2xl z-50 animate-fadeIn"
          >
            <div class="px-2.5 py-1 text-xs text-slate-400 flex items-center justify-between border-b border-white/5 pb-1 mb-1">
              <span>SEC EDGAR & index directory</span>
              <span class="text-[11px] text-slate-500">{{ searchResults.length }} matches</span>
            </div>
            <div class="max-h-64 overflow-y-auto space-y-1 custom-scrollbar">
              <div
                v-for="(item, idx) in searchResults"
                :key="item.ticker"
                @click="selectSearchResult(item)"
                class="apple-press flex items-center justify-between p-2 rounded-xl cursor-pointer transition-all"
                :class="activeSearchIndex === idx ? 'bg-white/10 border border-white/15 text-white' : 'hover:bg-white/5 text-slate-200 border border-transparent'"
              >
                <div class="flex items-center gap-2.5 min-w-0">
                  <span 
                    class="px-2 py-0.5 rounded font-mono text-xs font-bold shrink-0"
                    :class="item.is_macro_index ? 'bg-blue-500/20 text-blue-300 border border-blue-500/30' : (item.risk_tier === 'CRITICAL_ALERT' ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30' : 'bg-white/10 text-white')"
                  >
                    {{ item.ticker }}
                  </span>
                  <div class="truncate">
                    <div class="text-xs font-medium text-white truncate">{{ item.name }}</div>
                    <div class="text-[11px] text-slate-400 flex items-center gap-2 truncate">
                      <span>{{ item.exchange }}</span>
                      <span class="truncate text-slate-500">{{ item.sector }}</span>
                    </div>
                  </div>
                </div>
                <div class="text-right shrink-0 ml-2">
                  <span 
                    class="text-[11px] tabular-nums font-semibold px-2 py-0.5 rounded border"
                    :class="item.ffi_score > 60 ? 'bg-rose-500/10 text-rose-300 border-rose-500/20' : (item.ffi_score > 35 ? 'bg-amber-500/10 text-amber-300 border-amber-500/20' : 'bg-emerald-500/10 text-emerald-300 border-emerald-500/20')"
                  >
                    FFI {{ Math.round(item.ffi_score) }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Global Actions Tray -->
      <div class="flex items-center gap-2 shrink-0 whitespace-nowrap">
        <!-- Spotlight Command Palette Trigger (⌘K) -->
        <button
          @click="emit('open-palette')"
          class="sm:hidden apple-press text-xs font-medium px-3 py-1.5 rounded-xl border border-white/10 bg-slate-900/90 hover:bg-slate-800 text-slate-300 flex items-center gap-2 cursor-pointer shadow-xs"
          title="Open command palette (⌘K)"
          aria-label="Open command palette"
        >
          <Search class="w-3.5 h-3.5 text-slate-400" />
        </button>

        <!-- Anomaly Radar Trigger -->
        <button
          @click="showAnomalyModal = true"
          class="apple-press text-xs font-medium px-3 py-1.5 rounded-xl border border-rose-500/20 bg-rose-500/10 hover:bg-rose-500/20 text-rose-300 flex items-center gap-1.5 transition-all cursor-pointer shadow-xs"
          title="Filing Anomaly & Governance Radar"
          aria-label="Anomaly radar"
        >
          <ShieldAlert class="w-3.5 h-3.5 text-rose-400" />
          <span class="hidden md:inline">Anomaly radar</span>
        </button>

        <button
          @click="showInstitutionalReportModal = true"
          class="apple-press text-xs font-medium px-3 py-1.5 rounded-xl border border-white/10 bg-slate-800/90 hover:bg-slate-700/80 text-slate-200 flex items-center gap-1.5 transition-all cursor-pointer shadow-xs"
          title="Print-Ready Institutional Due Diligence Memorandum"
          aria-label="Due diligence memo"
        >
          <FileText class="w-3.5 h-3.5 text-slate-400" />
          <span class="hidden md:inline">Memo</span>
        </button>

        <button
          @click="exportDueDiligenceMemo"
          :disabled="isExportingMemo"
          class="apple-press text-xs font-medium px-3 py-1.5 rounded-xl border border-white/10 bg-slate-800/90 hover:bg-slate-700/80 text-slate-200 flex items-center gap-1.5 transition-all cursor-pointer shadow-xs"
          title="Export Markdown Memorandum"
          aria-label="Export memo"
        >
          <Loader2 v-if="isExportingMemo" class="w-3.5 h-3.5 animate-spin text-slate-300" />
          <Download v-else class="w-3.5 h-3.5 text-slate-400" />
          <span class="hidden sm:inline">Export</span>
        </button>

        <button
          @click="emit('open-chat')"
          class="apple-press text-xs font-semibold px-3.5 py-1.5 rounded-xl bg-white hover:bg-slate-100 text-slate-950 flex items-center gap-1.5 transition-all cursor-pointer shadow-xs"
          title="Open AI Co-Analyst Drawer"
        >
          <Sparkles class="w-3.5 h-3.5 fill-current" />
          <span>Co-Analyst</span>
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
          <component :is="tab.icon" class="w-3.5 h-3.5" :class="currentTab === tab.id ? 'text-white' : 'text-slate-500'" />
          <span>{{ tab.label }}</span>
          <span 
            v-if="tab.badge" 
            class="text-[10px] tabular-nums px-1.5 py-0.2 rounded-full bg-rose-500/10 text-rose-300 border border-rose-500/20 font-medium"
          >
            {{ tab.badge }}
          </span>
          <span 
            v-else-if="tab.id === 'filings' && documents.length > 0" 
            class="text-[10px] tabular-nums px-1.5 py-0.2 rounded-full bg-slate-800 text-slate-400"
          >
            {{ documents.length }}
          </span>
        </button>
      </div>

      <!-- Target Company Context Info -->
      <div class="hidden lg:flex items-center gap-2.5 text-xs text-slate-400">
        <span class="px-2.5 py-1 rounded-lg bg-white/5 border border-white/10 text-white font-medium">{{ currentCompany.name }} ({{ currentCompany.ticker }})</span>
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
            <section class="apple-card rounded-3xl p-6 sm:p-8 flex flex-col lg:flex-row items-start justify-between gap-8 relative overflow-hidden">
              <div class="space-y-4 max-w-2xl">
                <div class="flex flex-wrap items-center gap-x-4 gap-y-2">
                  <span 
                    class="px-2.5 py-1 rounded-full text-xs font-mono font-bold border"
                    :class="currentCompany.is_macro_index ? 'bg-blue-500/20 text-blue-300 border-blue-500/30' : 'bg-white/10 text-white border-white/15'"
                  >
                    {{ currentCompany.is_macro_index ? 'BENCHMARK' : currentCompany.exchange }}: {{ currentCompany.ticker }}
                  </span>
                  <span class="text-xs text-slate-400 flex items-center gap-1">
                    <component :is="currentCompany.is_macro_index ? Layers : Building2" class="w-3.5 h-3.5" :class="currentCompany.is_macro_index ? 'text-blue-400' : 'text-slate-500'" />
                    {{ currentCompany.sector }}
                  </span>
                  <span class="text-xs text-slate-400 font-mono">{{ currentCompany.is_macro_index ? `Exchange: ${currentCompany.exchange}` : `CIK ${currentCompany.cik}` }}</span>
                </div>

                <h1 class="text-3xl sm:text-4xl font-extrabold tracking-tight text-white">
                  {{ currentCompany.name }}
                </h1>

                <!-- Macro Index Top Holdings Ribbon (if macro benchmark index) -->
                <div v-if="currentCompany.is_macro_index && currentCompany.constituents?.length" class="flex flex-wrap items-center gap-1.5 pt-1">
                  <span class="text-xs text-slate-400 font-medium">Top Holdings:</span>
                  <button
                    v-for="c in currentCompany.constituents"
                    :key="c"
                    @click="selectCompany(c)"
                    class="apple-press text-[11px] font-mono font-semibold px-2 py-0.5 rounded-md bg-slate-800/80 hover:bg-slate-700 text-slate-300 hover:text-white border border-white/10 cursor-pointer transition-colors"
                    :title="`Analyze constituent ${c}`"
                  >
                    {{ c }}
                  </button>
                </div>

                <div v-else class="flex flex-wrap items-center gap-y-2 gap-x-4 text-xs text-slate-400">
                  <span class="flex items-center gap-1.5">
                    <Calendar class="w-3.5 h-3.5 text-slate-500" />
                    {{ currentCompany.period }}
                  </span>
                  <span class="flex items-center gap-1.5">
                    <FileCheck class="w-3.5 h-3.5 text-emerald-400" />
                    Auditor of Record: {{ currentCompany.auditor }}
                  </span>
                </div>

                <p class="text-xs sm:text-sm text-slate-300 leading-relaxed max-w-xl">
                  Automated triangulation across SEC EDGAR regulatory language shifts, forensic accrual accounting indicators (Beneish M-Score), and earnings call tone decoupling to detect hidden liabilities.
                </p>
                <div class="flex flex-wrap items-center gap-2 pt-2">
                  <button
                    @click="showInvestigationRunner = true"
                    class="apple-press py-2 px-3.5 rounded-xl bg-white hover:bg-slate-100 text-slate-950 text-xs font-semibold flex items-center gap-2 transition-all cursor-pointer shadow-xs"
                  >
                    <Terminal class="w-3.5 h-3.5 text-slate-900" />
                    <span>Run autonomous audit</span>
                  </button>

                  <button
                    @click="showAuditorModal = true"
                    class="apple-press py-2 px-3.5 rounded-xl bg-slate-800 hover:bg-slate-700/80 border border-white/10 text-xs font-medium text-slate-200 hover:text-white flex items-center gap-2 transition-all cursor-pointer shadow-xs"
                  >
                    <Scale class="w-3.5 h-3.5 text-slate-400" />
                    <span>Adversarial cross-examination</span>
                  </button>

                  <button
                    @click="showScorecardModal = true"
                    class="apple-press py-2 px-3.5 rounded-xl bg-transparent hover:bg-white/5 border border-white/10 text-xs font-medium text-slate-400 hover:text-slate-200 flex items-center gap-2 transition-all cursor-pointer"
                  >
                    <Sliders class="w-3.5 h-3.5 text-slate-500" />
                    <span>Inspect audit scorecard</span>
                  </button>
                </div>
              </div>

              <!-- FFI Fragility Gauge Card -->
              <div class="w-full lg:w-auto shrink-0">
                <div class="bg-slate-900/90 border border-white/10 rounded-2xl p-5 sm:p-6 flex flex-col items-center gap-4 text-center shadow-xl min-w-[260px]">
                  <span class="text-xs font-semibold text-slate-400">
                    {{ currentCompany.is_macro_index ? 'Macro Fragility Index' : 'Forensic Fragility Index (FFI)' }}
                  </span>

                  <div class="relative flex items-center justify-center">
                    <div 
                      class="w-28 h-28 rounded-full border-4 flex flex-col items-center justify-center transition-all shadow-inner"
                      :class="[ffiColor(currentCompany.ffi).border, ffiColor(currentCompany.ffi).bg]"
                    >
                      <span class="text-3xl font-extrabold tracking-tight text-white tabular-nums">
                        {{ currentCompany.ffi }}
                      </span>
                      <span class="text-[10px] text-slate-400 font-medium">
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
                    <p v-if="currentCompany.is_macro_index" class="text-[11px] text-slate-400 pt-1">
                      Constituent-weighted fragility dispersion
                    </p>
                    <div v-else class="flex items-center justify-center gap-1.5 pt-1">
                      <span class="text-[11px] px-2 py-0.5 rounded-md bg-white/5 border border-white/10 text-slate-300">Drift 30%</span>
                      <span class="text-[11px] px-2 py-0.5 rounded-md bg-white/5 border border-white/10 text-slate-300">M-Score 40%</span>
                      <span class="text-[11px] px-2 py-0.5 rounded-md bg-white/5 border border-white/10 text-slate-300">Contradictions 30%</span>
                    </div>
                  </div>

                </div>
              </div>
            </section>

            <!-- Corporate Governance & Filing Anomaly Alert Widget -->
            <section 
              class="apple-card rounded-2xl p-4 sm:p-5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border"
              :class="currentCompany.ticker === 'SMCI' ? 'bg-rose-950/20 border-rose-500/30' : 'bg-slate-900/60 border-white/10'"
            >
              <div class="flex items-center gap-3.5">
                <div 
                  class="p-2.5 rounded-xl border shrink-0"
                  :class="currentCompany.ticker === 'SMCI' ? 'bg-rose-500/20 text-rose-400 border-rose-500/30' : 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20'"
                >
                  <ShieldAlert class="w-5 h-5" />
                </div>
                <div class="space-y-0.5">
                  <div class="flex items-center gap-2">
                    <h3 class="text-xs font-semibold text-white">Governance & disclosure anomaly radar</h3>
                    <span 
                      class="text-[11px] font-medium px-2 py-0.5 rounded-md border"
                      :class="currentCompany.ticker === 'SMCI' ? 'bg-rose-500/20 text-rose-300 border-rose-500/30' : (currentCompany.is_macro_index ? 'bg-blue-500/20 text-blue-300 border-blue-500/30' : 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20')"
                    >
                      {{ currentCompany.ticker === 'SMCI' ? 'Critical disclosure anomalies' : (currentCompany.is_macro_index ? 'Benchmark composite dispersion' : 'Normalized governance') }}
                    </span>
                  </div>
                  <p class="text-xs text-slate-300">
                    {{ currentCompany.ticker === 'SMCI' 
                      ? 'Auditor resignation (PCAOB Rule 3526), delinquent 10-K Form 12b-25 alerts, and inventory-sales decoupling detected.' 
                      : (currentCompany.is_macro_index ? 'Aggregated macro benchmark index: continuous cross-asset monitoring of constituent language drift, accruals, and sector guidance dispersion.' : 'Zero Form 12b-25 late filing delinquency, non-audit fee ratio < 10%, and unbroken executive audit committee tenure.') }}
                  </p>
                </div>
              </div>

              <div class="flex items-center gap-2.5 shrink-0 w-full sm:w-auto justify-end">
                <button
                  @click="showAnomalyModal = true"
                  class="apple-press px-3.5 py-1.5 rounded-xl text-xs font-medium text-white flex items-center gap-1.5 cursor-pointer shadow-xs"
                  :class="currentCompany.ticker === 'SMCI' ? 'bg-rose-600 hover:bg-rose-500' : 'bg-slate-800 hover:bg-slate-700 border border-white/10'"
                >
                  <Search class="w-3.5 h-3.5 text-slate-300" />
                  <span>Audit signals</span>
                </button>
              </div>
            </section>

            <!-- 4 Core Forensic Pillar Cards -->
            <section class="space-y-3">
              <div class="flex items-center justify-between">
                <div>
                  <h2 class="text-sm font-semibold text-white tracking-tight">Forensic intelligence pillars</h2>
                  <p class="text-xs text-slate-400">Continuous institutional monitoring across four analytical audit vectors</p>
                </div>
                <span class="text-xs text-slate-400">Continuous SEC EDGAR ingestion</span>
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
                        <h3 class="text-xs font-semibold text-white">Filing language drift</h3>
                      </div>
                      <span class="text-xs tabular-nums font-medium px-2 py-0.5 rounded-md bg-amber-500/10 text-amber-300 border border-amber-500/20">
                        {{ currentCompany.driftLabel }}
                      </span>
                    </div>

                    <div class="flex items-center gap-2 text-xs text-slate-400">
                      <span class="text-emerald-400 font-medium">+{{ currentCompany.driftAdded }} risks added</span>
                      <span class="text-slate-600">/</span>
                      <span class="text-slate-400">-{{ currentCompany.driftRemoved }} retired</span>
                    </div>

                    <blockquote class="text-xs text-slate-300 italic border-l-2 border-amber-500/40 pl-3 py-1 bg-slate-950/40 rounded-r-lg font-serif">
                      "{{ currentCompany.driftExcerpt }}"
                    </blockquote>
                  </div>

                  <div class="pt-2 flex items-center justify-between border-t border-white/5">
                    <span class="text-[11px] text-slate-500">Year-over-year semantic redline</span>
                    <button
                      @click="showDiffModal = true"
                      class="apple-press text-xs font-medium text-amber-300 hover:text-amber-200 cursor-pointer"
                    >
                      Inspect redline diff
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
                        <h3 class="text-xs font-semibold text-white">Beneish M-Score accruals</h3>
                      </div>
                      <span class="text-xs tabular-nums font-medium px-2 py-0.5 rounded-md bg-purple-500/10 text-purple-300 border border-purple-500/20">
                        {{ currentCompany.mscoreLabel }}
                      </span>
                    </div>

                    <div class="flex items-center gap-3 text-xs text-slate-400 tabular-nums">
                      <span>Threshold: <strong class="text-slate-200">-1.78</strong></span>
                      <span class="text-slate-600">/</span>
                      <span>Probability: <strong class="text-emerald-400">{{ currentCompany.mscoreProb }}</strong></span>
                      <span class="text-slate-600">/</span>
                      <span>TATA: <strong class="text-slate-200">{{ currentCompany.tataAccrual }}</strong></span>
                    </div>

                    <p class="text-xs text-slate-300 leading-relaxed bg-slate-950/40 p-2.5 rounded-lg border border-white/5">
                      Total Accruals to Total Assets (TATA) and Asset Quality Index (AQI) indicate earnings are backed by operational cash collection.
                    </p>
                  </div>

                  <div class="pt-2 flex items-center justify-between border-t border-white/5">
                    <span class="text-[11px] text-slate-500">8-factor probabilistic model</span>
                    <button
                      @click="openMScoreModal('mscore')"
                      class="apple-press text-xs font-medium text-purple-300 hover:text-purple-200 cursor-pointer"
                    >
                      Audit accruals
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
                        <h3 class="text-xs font-semibold text-white">Guidance vs 10-Q tone radar</h3>
                      </div>
                      <span class="text-xs font-medium px-2 py-0.5 rounded-md bg-cyan-500/10 text-cyan-300 border border-cyan-500/20">
                        {{ currentCompany.radarLabel }}
                      </span>
                    </div>

                    <p class="text-xs text-slate-300 leading-relaxed bg-slate-950/40 p-2.5 rounded-lg border border-white/5">
                      {{ currentCompany.radarExcerpt }}
                    </p>
                  </div>

                  <div class="pt-2 flex items-center justify-between border-t border-white/5">
                    <span class="text-[11px] text-slate-500">Cross-modal tone decoupling</span>
                    <button
                      @click="showRadarModal = true"
                      class="apple-press text-xs font-medium text-cyan-300 hover:text-cyan-200 cursor-pointer"
                    >
                      Inspect guidance discrepancies
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
                        <h3 class="text-xs font-semibold text-white">Footnote disclosure scan</h3>
                      </div>
                      <span 
                        class="text-xs font-medium px-2 py-0.5 rounded-md border"
                        :class="currentCompany.footnotesClean 
                          ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/20' 
                          : 'bg-rose-500/10 text-rose-300 border-rose-500/20'"
                      >
                        {{ currentCompany.footnotesClean ? 'Clean disclosures' : `${currentCompany.footnoteCount} hazards flagged` }}
                      </span>
                    </div>

                    <p class="text-xs text-slate-300 leading-relaxed bg-slate-950/40 p-2.5 rounded-lg border border-white/5">
                      {{ currentCompany.footnoteExcerpt }}
                    </p>
                  </div>

                  <div class="pt-2 flex items-center justify-between border-t border-white/5">
                    <span class="text-[11px] text-slate-500">Automated NLP disclosure scan</span>
                    <button
                      @click="openMScoreModal('footnotes')"
                      class="apple-press text-xs font-medium text-rose-300 hover:text-rose-200 cursor-pointer"
                    >
                      Scan footnotes
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
                  class="apple-press py-2 px-3.5 rounded-xl bg-rose-600 hover:bg-rose-500 text-white text-xs font-medium flex items-center justify-center cursor-pointer shadow-xs"
                >
                  Launch cross-examination
                </button>
              </div>

              <!-- Trigger 2: Autonomous Multi-Agent Investigation Runner -->
              <div class="apple-card rounded-2xl p-5 flex flex-col justify-between space-y-3">
                <div class="space-y-2">
                  <div class="p-2 rounded-xl bg-purple-500/10 text-purple-400 border border-purple-500/20 w-fit">
                    <Terminal class="w-5 h-5" />
                  </div>
                  <h3 class="text-sm font-semibold text-white">Autonomous multi-agent investigation</h3>
                  <p class="text-xs text-slate-300 leading-relaxed">
                    Dispatches synchronized specialized subagents across filings, transcripts, and footnotes with real-time SSE execution telemetry.
                  </p>
                </div>
                <button
                  @click="showInvestigationRunner = true"
                  class="apple-press py-2 px-3.5 rounded-xl bg-purple-600 hover:bg-purple-500 text-white text-xs font-medium flex items-center justify-center cursor-pointer shadow-xs"
                >
                  Run autonomous audit
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
                            title="Query AI Co-Analyst on this document"
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

.apple-press:active {
  transform: scale(0.98);
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
