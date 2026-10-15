<script setup>
import { ref, watch, onMounted, onUnmounted } from 'vue'
import {
  ShieldAlert,
  Loader2,
  CheckCircle2,
  AlertTriangle,
  FileText,
  Download,
  Sparkles,
  Terminal,
  X,
  Play,
  RotateCcw
} from 'lucide-vue-next'

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false
  },
  ticker: {
    type: String,
    default: 'NVDA'
  }
})

const emit = defineEmits(['close', 'open-chat'])

const isRunning = ref(false)
const currentStepIndex = ref(0)
const steps = ref([
  { id: 'parsing', name: 'SEC Ingestion & Chunking Agent', status: 'pending', message: 'Awaiting launch...', details: null },
  { id: 'accruals', name: 'Forensic Accrual & Beneish Agent', status: 'pending', message: 'Awaiting launch...', details: null },
  { id: 'contradictions', name: 'Contradiction Radar Agent', status: 'pending', message: 'Awaiting launch...', details: null },
  { id: 'synthesis', name: 'Due Diligence Synthesizer', status: 'pending', message: 'Awaiting launch...', details: null },
])

const logs = ref([])
const completedResult = ref(null)
const errorMsg = ref('')

const startInvestigation = async () => {
  isRunning.value = true
  errorMsg.value = ''
  completedResult.value = null
  logs.value = []
  currentStepIndex.value = 0

  steps.value.forEach(s => {
    s.status = 'pending'
    s.message = 'Queued...'
    s.details = null
  })

  logs.value.push(`[${new Date().toLocaleTimeString()}] Starting audit run for ${props.ticker}...`)

  try {
    const res = await fetch('/api/forensics/investigate/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ticker: props.ticker, form: '10-K' })
    })

    if (!res.ok) throw new Error(`Investigation runner returned status ${res.status}`)

    const reader = res.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const parts = buffer.split('\n\n')
      buffer = parts.pop() || ''

      for (const part of parts) {
        if (!part.trim()) continue
        let event = 'message'
        let dataStr = ''
        for (const line of part.split('\n')) {
          if (line.startsWith('event: ')) {
            event = line.slice(7).trim()
          } else if (line.startsWith('data: ')) {
            dataStr = line.slice(6).trim()
          }
        }
        if (!dataStr) continue
        try {
          const payload = JSON.parse(dataStr)
          if (event === 'step') {
            const idx = steps.value.findIndex(s => s.id === payload.stage)
            if (idx !== -1) {
              steps.value[idx].status = payload.status
              steps.value[idx].message = payload.message
              steps.value[idx].details = payload.details
              currentStepIndex.value = idx
            }
            logs.value.push(`[${new Date().toLocaleTimeString()}] [${payload.agent}] ${payload.message}`)
          } else if (event === 'complete') {
            completedResult.value = payload
            steps.value.forEach(s => s.status = 'completed')
            logs.value.push(`[${new Date().toLocaleTimeString()}] Investigation successfully completed. FFI Score: ${payload.composite_ffi}/100.`)
          }
        } catch (e) {
          console.error('Error parsing SSE payload', e)
        }
      }
    }
  } catch (err) {
    errorMsg.value = err.message
    logs.value.push(`[${new Date().toLocaleTimeString()}] ERROR: ${err.message}`)
  } finally {
    isRunning.value = false
  }
}

watch(() => props.isOpen, (open) => {
  if (open && !isRunning.value && !completedResult.value) {
    startInvestigation()
  }
})

const downloadDossier = () => {
  if (!completedResult.value?.memo_markdown) return
  const blob = new Blob([completedResult.value.memo_markdown], { type: 'text/markdown;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `investigation_dossier_${props.ticker.toLowerCase()}.md`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

const handleKeyDown = (e) => {
  if (e.key === 'Escape' && props.isOpen && !isRunning.value) {
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
      <div class="bg-slate-900 border border-white/10 rounded-3xl w-full max-w-4xl max-h-[90vh] flex flex-col shadow-2xl overflow-hidden">
        
        <!-- Header -->
        <div class="h-16 px-6 border-b border-white/10 flex items-center justify-between shrink-0 bg-slate-900/90 backdrop-blur-md">
          <div class="flex items-center gap-3">
            <div class="p-2 rounded-xl bg-purple-500/10 text-purple-400 border border-purple-500/20">
              <Terminal class="w-5 h-5" />
            </div>
            <div>
              <h3 class="text-sm font-bold text-white flex items-center gap-2">
                Audit run
                <span class="text-[10px] font-mono px-2 py-0.5 rounded-full bg-purple-500/10 text-purple-300 border border-purple-500/20">
                  SSE Live Pipeline
                </span>
              </h3>
              <p class="text-[11px] text-slate-400">Executing sequential autonomous audit sub-agents on {{ ticker }}</p>
            </div>
          </div>

          <div class="flex items-center gap-3">
            <button
              v-if="!isRunning"
              @click="startInvestigation"
              class="apple-press text-xs font-semibold px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-white/10 flex items-center gap-1.5 cursor-pointer"
            >
              <RotateCcw class="w-3.5 h-3.5 text-purple-400" />
              <span>Rerun Pipeline</span>
            </button>

            <button 
              @click="emit('close')"
              class="apple-press text-slate-400 hover:text-white p-2 rounded-xl hover:bg-slate-800 transition-colors"
            >
              <X class="w-5 h-5" />
            </button>
          </div>
        </div>

        <!-- Body -->
        <div class="flex-1 overflow-y-auto p-6 space-y-6">
          
          <!-- Agent Pipeline Nodes -->
          <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            <div 
              v-for="(s, idx) in steps" 
              :key="s.id"
              class="p-4 rounded-2xl border transition-all relative overflow-hidden"
              :class="[
                s.status === 'completed' ? 'bg-emerald-950/20 border-emerald-500/30 text-emerald-300' :
                s.status === 'running' ? 'bg-purple-950/30 border-purple-500/50 text-white shadow-lg shadow-purple-500/10' :
                'bg-slate-950/40 border-white/5 text-slate-400 opacity-60'
              ]"
            >
              <div class="flex items-center justify-between mb-2">
                <span class="text-[10px] font-mono font-bold uppercase">Stage 0{{ idx + 1 }}</span>
                <Loader2 v-if="s.status === 'running'" class="w-3.5 h-3.5 animate-spin text-purple-400" />
                <CheckCircle2 v-else-if="s.status === 'completed'" class="w-3.5 h-3.5 text-emerald-400" />
                <span v-else class="w-2 h-2 rounded-full bg-slate-700"></span>
              </div>
              <h4 class="text-xs font-semibold text-white truncate">{{ s.name }}</h4>
              <p class="text-[11px] text-slate-400 mt-1 line-clamp-2">{{ s.message }}</p>
            </div>
          </div>

          <!-- Completed Findings Card -->
          <div 
            v-if="completedResult"
            class="p-5 rounded-2xl bg-emerald-950/20 border border-emerald-500/30 space-y-3 animate-in fade-in zoom-in-95 duration-200"
          >
            <div class="flex flex-wrap items-center justify-between gap-3">
              <div class="flex items-center gap-2">
                <CheckCircle2 class="w-5 h-5 text-emerald-400" />
                <div>
                  <h4 class="text-xs font-bold text-white">Investigation Synthesis Complete</h4>
                  <p class="text-[11px] text-emerald-300">
                    Forensic Fragility Index: <strong>{{ completedResult.composite_ffi }} / 100</strong> ({{ completedResult.risk_tier }})
                  </p>
                </div>
              </div>

              <div class="flex items-center gap-2">
                <button
                  @click="downloadDossier"
                  class="apple-press text-xs font-semibold px-3.5 py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white flex items-center gap-1.5 cursor-pointer shadow-xs"
                >
                  <Download class="w-3.5 h-3.5" />
                  <span>Download Audit Dossier</span>
                </button>
              </div>
            </div>

            <p class="text-xs text-slate-200 leading-relaxed bg-slate-900/60 p-3 rounded-xl border border-white/5">
              {{ completedResult.summary }}
            </p>
          </div>

          <!-- Live Agent Terminal Logs -->
          <div class="space-y-2">
            <div class="flex items-center justify-between text-xs text-slate-400">
              <span class="text-xs font-medium text-slate-400">Real-time sub-agent execution telemetry</span>
              <span v-if="isRunning" class="flex items-center gap-1.5 text-purple-400 text-xs font-medium">
                <span class="w-2 h-2 rounded-full bg-purple-400 animate-pulse"></span>
                Inference stream active
              </span>
            </div>

            <div class="h-48 overflow-y-auto bg-black/70 rounded-2xl p-4 font-mono text-xs text-slate-300 space-y-1.5 border border-white/10">
              <div v-for="(log, i) in logs" :key="i" class="leading-relaxed">
                <span class="text-emerald-400">❯</span> {{ log }}
              </div>
              <div v-if="isRunning" class="text-slate-500 animate-pulse">
                <span>❯ Processing next agentic verification step...</span>
              </div>
            </div>
          </div>

        </div>

      </div>
    </div>
  </Teleport>
</template>
