<script setup>
import { ref, watch, onMounted, computed, onUnmounted } from 'vue'
import {
  Gavel,
  X,
  ShieldAlert,
  AlertTriangle,
  FileCheck,
  FileText,
  Scale,
  Sparkles,
  Loader2,
  CheckCircle2,
  ChevronRight,
  BookOpen
} from 'lucide-vue-next'

const props = defineProps({
  show: {
    type: Boolean,
    default: false
  },
  ticker: {
    type: String,
    default: 'NVDA'
  },
  companyName: {
    type: String,
    default: 'NVIDIA Corporation'
  }
})

const emit = defineEmits(['close'])

const isLoading = ref(false)
const auditData = ref(null)
const selectedInquiryId = ref(null)

const runCrossExamination = async () => {
  isLoading.value = true
  try {
    const res = await fetch('/api/forensics/auditor/cross-examine', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ticker: props.ticker })
    })
    if (res.ok) {
      auditData.value = await res.json()
      if (auditData.value.inquiries?.length > 0) {
        selectedInquiryId.value = auditData.value.inquiries[0].id
      }
    }
  } catch (err) {
    console.error('Failed to run auditor cross-examination:', err)
  } finally {
    isLoading.value = false
  }
}

watch(() => props.show, (val) => {
  if (val) {
    runCrossExamination()
  }
})

const currentInquiry = computed(() => {
  if (!auditData.value?.inquiries) return null
  return auditData.value.inquiries.find(i => i.id === selectedInquiryId.value) || auditData.value.inquiries[0]
})

// Close on Escape
const onKeydown = (e) => {
  if (e.key === 'Escape' && props.show) {
    emit('close')
  }
}

onMounted(() => {
  window.addEventListener('keydown', onKeydown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', onKeydown)
})
</script>

<template>
  <div 
    v-if="show" 
    class="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 bg-slate-950/80 backdrop-blur-md"
    @click.self="emit('close')"
  >
    <div class="apple-modal w-full max-w-4xl max-h-[90vh] rounded-3xl bg-slate-900 border border-white/10 shadow-2xl flex flex-col overflow-hidden">
      
      <!-- Modal Header -->
      <div class="p-6 border-b border-white/10 flex items-center justify-between bg-slate-950/60">
        <div class="flex items-center gap-3">
          <div class="p-2.5 rounded-2xl bg-rose-500/10 text-rose-400 border border-rose-500/20">
            <Scale class="w-5 h-5" />
          </div>
          <div>
            <div class="flex items-center gap-2">
              <h2 class="text-base font-bold text-white tracking-tight">
                Adversarial SEC Enforcement & Big 4 Cross-Examination Studio
              </h2>
              <span class="text-[10px] font-mono px-2 py-0.5 rounded-full bg-rose-500/10 text-rose-300 border border-rose-500/20 font-bold">
                PCAOB Forensic Mode
              </span>
            </div>
            <p class="text-xs text-slate-400">
              Aggressive legal-evidentiary interrogation challenging {{ companyName }} ({{ ticker }}) accounting disclosures
            </p>
          </div>
        </div>

        <button 
          @click="emit('close')"
          class="apple-press p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 transition-colors cursor-pointer"
        >
          <X class="w-5 h-5" />
        </button>
      </div>

      <!-- Loading State -->
      <div v-if="isLoading" class="p-20 flex flex-col items-center justify-center space-y-4">
        <Loader2 class="w-8 h-8 animate-spin text-rose-500" />
        <span class="text-xs text-slate-400 font-mono">
          Formulating adversarial interrogation questions from SEC 10-K footnotes and ASC standards...
        </span>
      </div>

      <!-- Body -->
      <div v-else-if="auditData" class="flex-1 overflow-y-auto p-6 space-y-6">
        
        <!-- Summary & Firm Info -->
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-3 p-4 rounded-2xl bg-slate-950/60 border border-white/5 text-xs">
          <div>
            <span class="text-slate-500 block text-[11px]">Audit Committee / Enforcement Agency</span>
            <span class="font-semibold text-white">{{ auditData.audit_firm }}</span>
          </div>
          <div>
            <span class="text-slate-500 block text-[11px]">Regulatory Defense Posture</span>
            <span class="font-semibold text-amber-300">{{ auditData.overall_posture }}</span>
          </div>
          <div>
            <span class="text-slate-500 block text-[11px]">Enforcement Scrutiny Index</span>
            <div class="flex items-center gap-2 mt-0.5">
              <span class="text-base font-bold font-mono text-rose-400">{{ auditData.risk_index }} / 100</span>
              <span class="text-[10px] font-mono px-1.5 py-0.5 rounded bg-rose-500/10 text-rose-300 border border-rose-500/20">
                Elevated
              </span>
            </div>
          </div>
        </div>

        <!-- Inquiries Layout -->
        <div class="grid grid-cols-1 md:grid-cols-12 gap-6">
          
          <!-- Inquiries List (4 cols) -->
          <div class="md:col-span-5 space-y-2">
            <span class="text-xs text-slate-400 font-medium block mb-2">
              Cross-examination inquiries ({{ auditData.inquiries.length }})
            </span>

            <button
              v-for="inquiry in auditData.inquiries"
              :key="inquiry.id"
              @click="selectedInquiryId = inquiry.id"
              class="apple-press w-full text-left p-3.5 rounded-xl border transition-all cursor-pointer flex flex-col space-y-1.5"
              :class="selectedInquiryId === inquiry.id
                ? 'bg-rose-500/10 border-rose-500/40 text-white shadow-xs'
                : 'bg-slate-950/40 border-white/5 hover:border-white/10 text-slate-300'"
            >
              <div class="flex items-center justify-between">
                <span class="text-[10px] font-mono px-1.5 py-0.5 rounded font-medium"
                  :class="inquiry.severity === 'SUBPOENA_VULNERABILITY' || inquiry.severity === 'CRITICAL_DEFICIENCY'
                    ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                    : 'bg-amber-500/20 text-amber-300 border border-amber-500/30'"
                >
                  {{ inquiry.severity }}
                </span>
                <ChevronRight class="w-3.5 h-3.5 text-slate-500" />
              </div>
              <h4 class="text-xs font-semibold leading-tight line-clamp-1">{{ inquiry.topic }}</h4>
              <span class="text-[10px] font-mono text-slate-400">{{ inquiry.statutory_rule_citation }}</span>
            </button>
          </div>

          <!-- Active Inquiry Detail (7 cols) -->
          <div v-if="currentInquiry" class="md:col-span-7 space-y-5 p-5 rounded-2xl bg-slate-950/80 border border-white/5">
            
            <!-- Citation & Topic Title -->
            <div class="space-y-1.5 border-b border-white/5 pb-3">
              <div class="flex items-center gap-2">
                <span class="text-[10px] font-mono px-2 py-0.5 rounded-md bg-slate-800 text-slate-300 border border-white/10">
                  {{ currentInquiry.statutory_rule_citation }}
                </span>
                <span class="text-xs font-mono font-medium text-rose-400">
                  Posture: {{ currentInquiry.management_defense_posture }}
                </span>
              </div>
              <h3 class="text-sm font-semibold text-white">{{ currentInquiry.topic }}</h3>
            </div>

            <!-- Interrogation Prompt (The Question) -->
            <div class="space-y-2">
              <span class="text-xs text-slate-400 font-medium flex items-center gap-1.5">
                <Gavel class="w-3.5 h-3.5 text-rose-400" />
                Prosecutorial inquiry:
              </span>
              <blockquote class="text-xs text-rose-100 italic bg-rose-950/20 p-4 rounded-xl border-l-2 border-rose-500/60 leading-relaxed font-serif">
                "{{ currentInquiry.interrogation_prompt }}"
              </blockquote>
            </div>

            <!-- Evidentiary Documents Required -->
            <div class="space-y-2">
              <span class="text-xs text-slate-400 font-medium flex items-center gap-1.5">
                <FileCheck class="w-3.5 h-3.5 text-sky-400" />
                Required audit workpapers and subpoena evidence:
              </span>
              <ul class="space-y-1.5 text-xs text-slate-300">
                <li 
                  v-for="(doc, idx) in currentInquiry.required_evidentiary_documents" 
                  :key="idx"
                  class="flex items-start gap-2 bg-slate-900/60 p-2 rounded-lg border border-white/5"
                >
                  <FileText class="w-3.5 h-3.5 text-sky-400 shrink-0 mt-0.5" />
                  <span>{{ doc }}</span>
                </li>
              </ul>
            </div>

            <!-- Recommended Counsel Rebuttal -->
            <div class="space-y-1.5 p-3.5 rounded-xl bg-emerald-950/20 border border-emerald-500/20 text-xs">
              <span class="font-bold text-emerald-300 flex items-center gap-1.5">
                <Sparkles class="w-3.5 h-3.5" />
                Recommended Legal Defense Rebuttal Strategy:
              </span>
              <p class="text-slate-300 leading-relaxed">
                {{ currentInquiry.recommended_counsel_rebuttal }}
              </p>
            </div>

          </div>

        </div>

        <!-- Overall Summary -->
        <div class="p-4 rounded-xl bg-slate-950/60 border border-white/5 text-xs text-slate-300 leading-relaxed space-y-1">
          <strong class="text-white block">Audit Committee Synthesis:</strong>
          <p>{{ auditData.enforcement_risk_summary }}</p>
        </div>

      </div>

      <!-- Modal Footer -->
      <div class="p-4 border-t border-white/10 bg-slate-950/80 flex items-center justify-between text-xs">
        <span class="text-slate-500 font-mono">Simulated for institutional risk & audit committee evaluation</span>
        <button
          @click="emit('close')"
          class="apple-press px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-white font-semibold cursor-pointer"
        >
          Close Cross-Examination
        </button>
      </div>

    </div>
  </div>
</template>

<style scoped>
.apple-modal {
  backdrop-filter: blur(28px) saturate(190%);
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
