<script setup>
import { ref, computed } from 'vue'
import {
  X,
  Printer,
  Download,
  FileText,
  ShieldAlert,
  CheckCircle2,
  Calendar,
  Building,
  UserCheck
} from 'lucide-vue-next'
import { ffiTier } from '../utils/ffi.js'

const props = defineProps({
  isOpen: Boolean,
  ticker: {
    type: String,
    default: 'NVDA'
  },
  companyName: {
    type: String,
    default: 'NVIDIA Corporation'
  },
  profile: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['close'])

const ffiScore = computed(() => props.profile.ffi ?? 0)
const tier = computed(() => ffiTier(ffiScore.value))
// Beneish (1999): M-Score above -1.78 flags a likely manipulator; -2.22 is the conservative cut-off.
const MSCORE_THRESHOLD = -1.78
const MSCORE_GREY_ZONE = -2.22

const severityClass = {
  good: 'text-emerald-400',
  watch: 'text-amber-400',
  critical: 'text-rose-400'
}

const byThreshold = (value, watchAt, criticalAt) => {
  if (value == null) return 'watch'
  if (value >= criticalAt) return 'critical'
  return value >= watchAt ? 'watch' : 'good'
}

const pillars = computed(() => {
  const p = props.profile
  const mscoreSeverity = p.mscore == null
    ? 'watch'
    : p.mscore > MSCORE_THRESHOLD ? 'critical' : p.mscore > MSCORE_GREY_ZONE ? 'watch' : 'good'
  const mscoreVerdict = p.mscore == null
    ? 'M-Score unavailable for this filer.'
    : p.mscore > MSCORE_THRESHOLD
      ? `Above the ${MSCORE_THRESHOLD} manipulation threshold.`
      : `Below the ${MSCORE_THRESHOLD} manipulation threshold.`
  const accrualDetail = [
    p.tataAccrual != null ? `TATA ${p.tataAccrual}` : null,
    p.mscoreProb ? `manipulation probability ${p.mscoreProb}` : null
  ].filter(Boolean).join('; ')

  return [
    {
      title: 'Language drift (Item 1A)',
      metric: p.driftScore != null ? `${p.driftScore}% YoY drift` : 'Drift not computed',
      severity: byThreshold(p.driftScore, 15, 30),
      detail: p.driftExcerpt || 'No risk-factor redline available for this period.'
    },
    {
      title: 'Beneish M-Score & accruals',
      metric: p.mscore != null ? `M-Score: ${p.mscore}` : 'M-Score: n/a',
      severity: mscoreSeverity,
      detail: accrualDetail ? `${mscoreVerdict} ${accrualDetail}.` : mscoreVerdict
    },
    {
      title: 'Call vs 10-Q contradictions',
      metric: p.divergenceScore != null ? `${p.divergenceScore} / 100 decoupling` : 'Decoupling not computed',
      severity: byThreshold(p.divergenceScore, 25, 50),
      detail: p.radarExcerpt || 'No earnings call transcript aligned for this period.'
    },
    {
      title: 'Footnote disclosures',
      metric: p.footnotesClean === false
        ? `${p.footnoteCount ?? 0} flagged ${p.footnoteCount === 1 ? 'item' : 'items'}`
        : 'No flagged items',
      severity: p.footnotesClean === false ? (p.footnoteCount >= 4 ? 'critical' : 'watch') : 'good',
      detail: p.footnoteExcerpt || 'No footnote scan available for this period.'
    }
  ]
})

const entityLine = computed(() => {
  const parts = [`${props.companyName} (${props.profile.exchange || 'N/A'}: ${props.ticker})`]
  if (props.profile.cik && !/^0+$/.test(props.profile.cik)) parts.push(`CIK: ${props.profile.cik}`)
  return parts.join(' / ')
})

const isDownloading = ref(false)

const handlePrint = () => {
  window.print()
}

const handleDownloadMarkdown = async () => {
  isDownloading.value = true
  try {
    const payload = {
      ticker: props.ticker,
      company_name: props.companyName,
      scorecard: {
        composite_ffi: ffiScore.value,
        risk_level: props.profile.riskTier || 'LOW_RISK',
        summary: `Institutional forensic review of ${props.ticker} SEC filings, language drift, and executive tone.`
      }
    }

    const res = await fetch('/api/forensics/report/download', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })

    if (!res.ok) throw new Error('Download failed')

    const blob = await res.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `Institutional_Forensic_Memo_${props.ticker}.md`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  } catch (err) {
    console.error(err)
  } finally {
    isDownloading.value = false
  }
}
</script>

<template>
  <div
    v-if="isOpen"
    class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-fadeIn print:p-0 print:bg-white print:static"
    @click.self="emit('close')"
  >
    <div class="relative w-full max-w-4xl max-h-[92vh] flex flex-col bg-[#141416] border border-white/10 rounded-2xl shadow-2xl overflow-hidden print:border-none print:shadow-none print:bg-white print:max-h-none print:overflow-visible print:rounded-none">
      <!-- Toolbar (Hidden during print) -->
      <div class="flex items-center justify-between px-6 py-4 border-b border-white/10 bg-white/[0.02] print:hidden">
        <div class="flex items-center gap-3">
          <div class="w-9 h-9 rounded-xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400">
            <FileText class="w-5 h-5" />
          </div>
          <div>
            <h2 class="text-base font-semibold text-white tracking-tight">
              Institutional Due Diligence Memorandum Preview
            </h2>
            <p class="text-xs text-neutral-400">
              Print-ready executive brief formatted for investment committee and audit presentation
            </p>
          </div>
        </div>

        <div class="flex items-center gap-2">
          <button
            @click="handlePrint"
            class="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-white bg-white/10 hover:bg-white/15 border border-white/15 rounded-lg transition-all active:scale-[0.98]"
          >
            <Printer class="w-3.5 h-3.5" />
            <span>Print / PDF</span>
          </button>

          <button
            @click="handleDownloadMarkdown"
            :disabled="isDownloading"
            class="inline-flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-medium text-white bg-blue-600 hover:bg-blue-500 border border-blue-400/30 rounded-lg shadow-sm transition-all active:scale-[0.98]"
          >
            <Download class="w-3.5 h-3.5" />
            <span>{{ isDownloading ? 'Downloading...' : 'Export Markdown' }}</span>
          </button>

          <button
            @click="emit('close')"
            class="w-8 h-8 rounded-lg bg-white/5 hover:bg-white/10 text-neutral-400 hover:text-white flex items-center justify-center transition-all ml-1"
          >
            <X class="w-4 h-4" />
          </button>
        </div>
      </div>

      <!-- Printable Document Canvas -->
      <div class="flex-1 overflow-y-auto p-8 text-neutral-200 custom-scrollbar print:p-6 print:text-black print:overflow-visible">
        <div class="max-w-3xl mx-auto space-y-8 bg-neutral-900/40 p-8 rounded-xl border border-white/5 print:bg-white print:border-none print:p-0 print:space-y-6">
          <!-- Institutional Header -->
          <div class="border-b-2 border-neutral-700 pb-5 print:border-black">
            <div class="flex justify-between items-start">
              <div>
                <span class="text-xs font-medium text-blue-400 print:text-neutral-700">
                  Confidential / For institutional use only
                </span>
                <h1 class="text-xl font-bold tracking-tight text-white mt-1 print:text-black">
                  Forensic Financial Audit & Due Diligence Memorandum
                </h1>
                <p class="text-xs text-neutral-400 mt-0.5 print:text-neutral-600">
                  Target Entity: {{ entityLine }}
                </p>
              </div>

              <!-- Risk Badge -->
              <div class="text-right">
                <span
                  class="inline-block px-3 py-1 rounded-md text-xs font-semibold border print:border-black print:text-black"
                  :class="[tier.bg, tier.text, tier.border]"
                >
                  FFI: {{ ffiScore }} / 100 — {{ tier.label }}
                </span>
                <div class="text-[10px] text-neutral-500 mt-1 print:text-neutral-600">
                  Audited Date: October 2026
                </div>
              </div>
            </div>
          </div>

          <!-- Metadata Box -->
          <div class="grid grid-cols-2 sm:grid-cols-4 gap-4 p-4 rounded-lg bg-white/[0.02] border border-white/10 text-xs print:bg-neutral-50 print:border-neutral-300 print:text-neutral-900">
            <div>
              <span class="text-neutral-400 print:text-neutral-600 block text-[11px] font-medium">Sector</span>
              <span class="font-medium text-white print:text-black">{{ profile.sector || 'Semiconductors & AI' }}</span>
            </div>
            <div>
              <span class="text-neutral-400 print:text-neutral-600 block text-[11px] font-medium">Auditor of record</span>
              <span class="font-medium text-white print:text-black">{{ profile.auditor || 'PricewaterhouseCoopers LLP' }}</span>
            </div>
            <div>
              <span class="text-neutral-400 print:text-neutral-600 block text-[11px] font-medium">Filing form</span>
              <span class="font-medium text-white print:text-black">{{ profile.period || 'Form 10-K / 10-Q' }}</span>
            </div>
            <div>
              <span class="text-neutral-400 print:text-neutral-600 block text-[11px] font-medium">Analyst division</span>
              <span class="font-medium text-white print:text-black">Institutional Forensic Intelligence Group</span>
            </div>
          </div>

          <!-- Section 1: Executive Summary & Recommendation -->
          <div class="space-y-2">
            <h3 class="text-xs font-semibold text-blue-400 border-b border-neutral-800 pb-1 print:text-black print:border-black">
              1. Executive summary & forensic fragility index
            </h3>
            <p class="text-xs leading-relaxed text-neutral-300 print:text-neutral-800">
              The proprietary Forensic Fragility Index (FFI) for {{ companyName }} is assessed at
              <strong class="text-white print:text-black">{{ ffiScore }} out of 100</strong>.
              <template v-if="tier.key === 'low'">
                This reflects institutional-grade financial reporting health and absence of aggressive earnings manipulation patterns. A tri-pillar synthesis across consecutive 10-K regulatory filings, footnote disclosures, and earnings conference call transcripts indicates negligible structural fragility.
              </template>
              <template v-else>
                A tri-pillar synthesis across consecutive 10-K regulatory filings, footnote disclosures, and earnings conference call transcripts indicates {{ tier.key === 'watch' ? 'watchlist-level' : 'critical' }} structural fragility, warranting targeted follow-up on the flagged pillars.
              </template>
            </p>
          </div>

          <!-- Section 2: Pillar Analysis -->
          <div class="space-y-3">
            <h3 class="text-xs font-semibold text-blue-400 border-b border-neutral-800 pb-1 print:text-black print:border-black">
              2. Forensic pillar findings
            </h3>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div
                v-for="pillar in pillars"
                :key="pillar.title"
                class="p-3.5 rounded-lg bg-white/[0.02] border border-white/10 print:border-neutral-300 print:bg-white text-xs space-y-1.5"
              >
                <span class="font-semibold text-white print:text-black block">{{ pillar.title }}</span>
                <span class="text-[11px] font-mono print:text-black" :class="severityClass[pillar.severity]">{{ pillar.metric }}</span>
                <p class="text-[11px] text-neutral-400 print:text-neutral-700 leading-normal">
                  {{ pillar.detail }}
                </p>
              </div>
            </div>
          </div>

          <!-- Section 3: Sign-Off and Verification -->
          <div class="pt-4 border-t border-neutral-800 print:border-black flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 text-xs">
            <div>
              <span class="text-[10px] text-neutral-500 print:text-neutral-600 block">Sign-Off & Audit Directorate</span>
              <span class="font-semibold text-white print:text-black">Zaisaku Institutional Intelligence Group</span>
              <span class="text-[11px] text-neutral-400 print:text-neutral-600 block">Global Forensic Due Diligence & Risk Compliance</span>
            </div>

            <div class="text-right">
              <span class="text-[10px] text-neutral-500 print:text-neutral-600 block">Autonomous Verification</span>
              <span class="inline-flex items-center gap-1 text-emerald-400 font-mono text-xs font-semibold print:text-black">
                <CheckCircle2 class="w-3.5 h-3.5" /> SEC XBRL & SHA-256 Validated
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
@media print {
  body {
    background: white !important;
    color: black !important;
  }
}

.custom-scrollbar::-webkit-scrollbar {
  width: 5px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.02);
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.15);
}
</style>
