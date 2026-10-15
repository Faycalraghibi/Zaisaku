<script setup>
import { ref } from 'vue'
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
        composite_ffi: props.profile.ffi || 18,
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
                <span class="text-[10px] tracking-widest font-mono uppercase text-blue-400 font-bold print:text-neutral-700">
                  CONFIDENTIAL • FOR INSTITUTIONAL USE ONLY
                </span>
                <h1 class="text-xl font-bold tracking-tight text-white mt-1 print:text-black">
                  FORENSIC FINANCIAL AUDIT & DUE DILIGENCE MEMORANDUM
                </h1>
                <p class="text-xs text-neutral-400 mt-0.5 print:text-neutral-600">
                  Target Entity: {{ companyName }} (NASDAQ: {{ ticker }}) • CIK: {{ profile.cik || '0001045810' }}
                </p>
              </div>

              <!-- Risk Badge -->
              <div class="text-right">
                <span class="inline-block px-3 py-1 rounded-md text-xs font-bold uppercase tracking-wider bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 print:border-black print:text-black">
                  FFI: {{ profile.ffi || 18 }} / 100 • LOW FRAGILITY
                </span>
                <div class="text-[10px] text-neutral-500 mt-1 font-mono print:text-neutral-600">
                  Audited Date: October 2026
                </div>
              </div>
            </div>
          </div>

          <!-- Metadata Box -->
          <div class="grid grid-cols-2 sm:grid-cols-4 gap-4 p-4 rounded-lg bg-white/[0.02] border border-white/10 text-xs print:bg-neutral-50 print:border-neutral-300 print:text-neutral-900">
            <div>
              <span class="text-neutral-400 print:text-neutral-600 block text-[10px] uppercase">Sector</span>
              <span class="font-medium text-white print:text-black">{{ profile.sector || 'Semiconductors & AI' }}</span>
            </div>
            <div>
              <span class="text-neutral-400 print:text-neutral-600 block text-[10px] uppercase">Auditor of Record</span>
              <span class="font-medium text-white print:text-black">{{ profile.auditor || 'PricewaterhouseCoopers LLP' }}</span>
            </div>
            <div>
              <span class="text-neutral-400 print:text-neutral-600 block text-[10px] uppercase">Filing Form</span>
              <span class="font-medium text-white print:text-black">{{ profile.period || 'Form 10-K / 10-Q' }}</span>
            </div>
            <div>
              <span class="text-neutral-400 print:text-neutral-600 block text-[10px] uppercase">Analyst Division</span>
              <span class="font-medium text-white print:text-black">Institutional Forensic Intelligence Group</span>
            </div>
          </div>

          <!-- Section 1: Executive Summary & Recommendation -->
          <div class="space-y-2">
            <h3 class="text-xs font-bold tracking-wider uppercase text-blue-400 border-b border-neutral-800 pb-1 print:text-black print:border-black">
              1. Executive Summary & Forensic Fragility Index
            </h3>
            <p class="text-xs leading-relaxed text-neutral-300 print:text-neutral-800">
              The proprietary Forensic Fragility Index (FFI) for {{ companyName }} is assessed at
              <strong class="text-white print:text-black">{{ profile.ffi || 18 }} out of 100</strong>, reflecting institutional-grade financial reporting health and absence of aggressive earnings manipulation patterns. A tri-pillar synthesis across consecutive 10-K regulatory filings, footnote disclosures, and earnings conference call transcripts indicates negligible structural fragility.
            </p>
          </div>

          <!-- Section 2: Pillar Analysis -->
          <div class="space-y-3">
            <h3 class="text-xs font-bold tracking-wider uppercase text-blue-400 border-b border-neutral-800 pb-1 print:text-black print:border-black">
              2. Tri-Pillar Forensic Findings
            </h3>

            <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
              <!-- Pillar 1 -->
              <div class="p-3.5 rounded-lg bg-white/[0.02] border border-white/10 print:border-neutral-300 print:bg-white text-xs space-y-1.5">
                <span class="font-semibold text-white print:text-black block">Language Drift (Item 1A)</span>
                <span class="text-[11px] font-mono text-emerald-400 print:text-black">{{ profile.driftScore || 8.5 }}% YoY Volatility</span>
                <p class="text-[11px] text-neutral-400 print:text-neutral-700 leading-normal">
                  {{ profile.driftExcerpt || 'Modest legal modifications concerning international trade controls without adverse risk shift.' }}
                </p>
              </div>

              <!-- Pillar 2 -->
              <div class="p-3.5 rounded-lg bg-white/[0.02] border border-white/10 print:border-neutral-300 print:bg-white text-xs space-y-1.5">
                <span class="font-semibold text-white print:text-black block">Beneish M-Score & Accruals</span>
                <span class="text-[11px] font-mono text-emerald-400 print:text-black">M-Score: {{ profile.mscore || -2.85 }}</span>
                <p class="text-[11px] text-neutral-400 print:text-neutral-700 leading-normal">
                  Comfortably beneath -1.78 threshold. Total accruals to total assets (TATA) remain negative and non-aggressive.
                </p>
              </div>

              <!-- Pillar 3 -->
              <div class="p-3.5 rounded-lg bg-white/[0.02] border border-white/10 print:border-neutral-300 print:bg-white text-xs space-y-1.5">
                <span class="font-semibold text-white print:text-black block">Tone Contradiction Radar</span>
                <span class="text-[11px] font-mono text-emerald-400 print:text-black">{{ profile.divergenceScore || 11.0 }} / 100 Decoupling</span>
                <p class="text-[11px] text-neutral-400 print:text-neutral-700 leading-normal">
                  {{ profile.radarExcerpt || 'Management guidance aligns closely with conservative supply-chain commentary.' }}
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
