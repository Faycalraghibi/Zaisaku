<script setup>
import { ref, nextTick, computed, watch, onMounted, onUnmounted } from 'vue'
import { Send, Bot, User, Loader2, Sparkles, Table as TableIcon, X, CornerDownLeft, FileText, ShieldAlert } from 'lucide-vue-next'
import SourceBadge from './SourceBadge.vue'

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false
  },
  documentCount: {
    type: Number,
    default: 0
  },
  initialPrompt: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['close'])

const messages = ref([
  {
    role: 'assistant',
    text: 'Hello. I am your Institutional AI Co-Analyst. You can query indexed SEC filings, 10-Ks, 10-Qs, and earnings transcripts for forensic anomalies, accounting accruals, or linguistic drift.',
    sources: [],
    confidence: null,
    model: null
  }
])

const query = ref('')
const isQuerying = ref(false)
const currentStage = ref('')
const chatContainer = ref(null)
const inputRef = ref(null)

const quickPrompts = [
  { label: 'Summarize Item 1A Risk Factors', icon: ShieldAlert, prompt: 'Summarize the primary Item 1A Risk Factors in the latest filing and note any newly added systemic risks.' },
  { label: 'Analyze Beneish M-Score Drivers', icon: FileText, prompt: 'Analyze the balance sheet and accrual quality: are there any signs of revenue inflation or unusual receivables growth?' },
  { label: 'Check Call vs 10-Q Contradictions', icon: Sparkles, prompt: 'Compare management remarks in the earnings call against the cautious disclosures in Item 7 MD&A.' }
]

const handleQuickPrompt = (promptText) => {
  query.value = promptText
  sendQuery()
}

const scrollToBottom = async () => {
  await nextTick()
  if (chatContainer.value) {
    chatContainer.value.scrollTop = chatContainer.value.scrollHeight
  }
}

watch(() => props.isOpen, async (open) => {
  if (open) {
    await nextTick()
    inputRef.value?.focus()
    scrollToBottom()
  }
})

watch(() => props.initialPrompt, (newVal) => {
  if (newVal && newVal.trim()) {
    query.value = newVal.trim()
    sendQuery()
  }
})

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

const sendQuery = async () => {
  if (!query.value.trim() || isQuerying.value) return

  const userQuestion = query.value.trim()
  query.value = ''

  messages.value.push({
    role: 'user',
    text: userQuestion
  })
  
  scrollToBottom()
  
  isQuerying.value = true
  currentStage.value = 'Searching indexed documents...'

  let assistantMsg = null

  try {
    const res = await fetch('/api/query/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question: userQuestion }),
      signal: AbortSignal.timeout(90000)
    })

    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      throw new Error(err.detail || `Server returned ${res.status}`)
    }

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
          if (event === 'stage') {
            currentStage.value = payload.message || payload.stage
          } else if (event === 'sources') {
            if (assistantMsg) assistantMsg.sources = payload.sources
          } else if (event === 'token') {
            if (!assistantMsg) {
              assistantMsg = {
                role: 'assistant',
                text: '',
                sources: [],
                confidence: null,
                model: null,
                env: null,
                isStreaming: true
              }
              messages.value.push(assistantMsg)
            }
            assistantMsg.text += payload.token
            scrollToBottom()
          } else if (event === 'complete') {
            if (!assistantMsg) {
              assistantMsg = {
                role: 'assistant',
                text: payload.answer || '',
                sources: payload.sources || [],
                confidence: payload.confidence,
                model: payload.model,
                env: payload.env
              }
              messages.value.push(assistantMsg)
            } else {
              assistantMsg.confidence = payload.confidence
              assistantMsg.sources = payload.sources || assistantMsg.sources
              assistantMsg.model = payload.model
              assistantMsg.env = payload.env
              assistantMsg.isStreaming = false
            }
          } else if (event === 'error') {
            throw new Error(payload.detail || 'Streaming failed')
          }
        } catch (parseErr) {
          if (event === 'error') throw parseErr
        }
      }
    }
  } catch (err) {
    const isTimeout = err.name === 'TimeoutError' || err.name === 'AbortError'
    const errorText = isTimeout 
      ? 'Request timed out after 90 seconds. The model took too long to respond.' 
      : `Error: ${err.message}`
    if (assistantMsg) {
      assistantMsg.text += `\n\n[${errorText}]`
      assistantMsg.isError = true
      assistantMsg.isStreaming = false
    } else {
      messages.value.push({
        role: 'assistant',
        text: errorText,
        isError: true
      })
    }
  } finally {
    isQuerying.value = false
    currentStage.value = ''
    scrollToBottom()
  }
}

const confidenceColor = (score) => {
  if (score >= 0.8) return 'text-emerald-400'
  if (score >= 0.5) return 'text-yellow-400'
  return 'text-red-400'
}

const hasTable = (text) => {
  return Boolean(text && /\|.+\|\n\|[-:\s|]+\|/m.test(text))
}

const exportTableToCsv = (text) => {
  if (!text) return
  const lines = text.split('\n')
  const csvRows = []
  let inTable = false

  for (const line of lines) {
    const trimmed = line.trim()
    if (trimmed.startsWith('|') && trimmed.endsWith('|')) {
      if (/^\|[-:\s|]+\|$/.test(trimmed)) {
        inTable = true
        continue
      }
      inTable = true
      const cells = trimmed
        .slice(1, -1)
        .split('|')
        .map(cell => {
          let c = cell.trim()
          if (c.includes('"') || c.includes(',') || c.includes('\n')) {
            c = `"${c.replace(/"/g, '""')}"`
          }
          return c
        })
      csvRows.push(cells.join(','))
    } else if (inTable && csvRows.length > 0) {
      inTable = false
      csvRows.push('')
    }
  }

  const csvContent = csvRows.filter((r, idx, arr) => !(r === '' && arr[idx - 1] === '')).join('\n').trim()
  if (!csvContent) return

  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.setAttribute('href', url)
  link.setAttribute('download', `financial_table_${Date.now()}.csv`)
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}
</script>

<template>
  <Teleport to="body">
    <!-- Backdrop Scrim with Blur -->
    <div 
      v-if="isOpen" 
      class="fixed inset-0 z-40 bg-black/60 backdrop-blur-xs transition-opacity duration-300"
      @click="emit('close')"
    ></div>

    <!-- Apple-Style Slide-Over Drawer with Spring Transition -->
    <Transition name="spring-drawer">
      <div 
        v-if="isOpen" 
        class="fixed inset-y-0 right-0 z-50 w-full max-w-xl bg-slate-900/95 backdrop-blur-2xl border-l border-white/10 shadow-2xl flex flex-col text-slate-100"
        role="dialog"
        aria-modal="true"
        aria-labelledby="drawer-title"
      >
        <!-- Header -->
        <div class="h-16 px-6 border-b border-white/10 flex items-center justify-between shrink-0 bg-slate-900/60 backdrop-blur-md">
          <div class="flex items-center gap-3">
            <div class="w-8 h-8 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
              <Sparkles class="w-4 h-4" />
            </div>
            <div>
              <h2 id="drawer-title" class="text-sm font-semibold tracking-tight text-white flex items-center gap-2">
                AI Co-Analyst
                <span class="text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  Forensic RAG
                </span>
              </h2>
              <p class="text-[11px] text-slate-400">Auditing 10-Ks, 10-Qs & Transcripts</p>
            </div>
          </div>

          <div class="flex items-center gap-3">
            <div class="hidden sm:flex items-center gap-2 text-xs text-slate-400 bg-slate-800/80 px-2.5 py-1 rounded-full border border-slate-700/60 font-mono">
              <span class="w-1.5 h-1.5 rounded-full" :class="documentCount > 0 ? 'bg-emerald-400' : 'bg-amber-400'"></span>
              <span>{{ documentCount }} Doc{{ documentCount !== 1 ? 's' : '' }}</span>
            </div>

            <button 
              @click="emit('close')"
              class="apple-press p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors flex items-center gap-1.5 cursor-pointer"
              title="Close drawer (Escape)"
            >
              <kbd class="text-[10px] font-mono text-slate-400 bg-slate-800 px-1.5 py-0.5 rounded border border-slate-700 hidden sm:inline">ESC</kbd>
              <X class="w-4 h-4" />
            </button>
          </div>
        </div>

        <!-- Quick Question Suggestions Bar -->
        <div class="px-6 py-2.5 bg-slate-950/40 border-b border-white/5 flex items-center gap-2 overflow-x-auto scrollbar-none shrink-0">
          <span class="text-[11px] font-medium text-slate-400 shrink-0">Quick Queries:</span>
          <button
            v-for="(item, idx) in quickPrompts"
            :key="idx"
            @click="handleQuickPrompt(item.prompt)"
            :disabled="isQuerying"
            class="apple-press shrink-0 text-xs px-2.5 py-1 rounded-full bg-slate-800/80 hover:bg-slate-700/80 border border-slate-700/60 text-slate-300 hover:text-white transition-all cursor-pointer flex items-center gap-1.5"
          >
            <component :is="item.icon" class="w-3 h-3 text-emerald-400" />
            <span>{{ item.label }}</span>
          </button>
        </div>

        <!-- Chat Stream Messages Container -->
        <div ref="chatContainer" class="flex-1 overflow-y-auto p-5 sm:p-6 space-y-5 scroll-smooth">
          <div 
            v-for="(msg, idx) in messages" 
            :key="idx"
            class="flex gap-3 max-w-full"
            :class="msg.role === 'user' ? 'flex-row-reverse' : ''"
          >
            <div 
              class="w-7 h-7 rounded-lg flex items-center justify-center shrink-0 mt-0.5"
              :class="msg.role === 'user' ? 'bg-blue-600 text-white' : 'bg-emerald-600 text-white'"
            >
              <User v-if="msg.role === 'user'" class="w-3.5 h-3.5" />
              <Bot v-else class="w-3.5 h-3.5" />
            </div>

            <div 
              class="flex flex-col gap-1.5 max-w-[85%]"
              :class="msg.role === 'user' ? 'items-end' : 'items-start'"
            >
              <div 
                class="px-4 py-3 rounded-2xl text-xs sm:text-sm leading-relaxed"
                :class="[
                  msg.role === 'user' 
                    ? 'bg-blue-600 text-white rounded-tr-xs shadow-sm font-normal' 
                    : 'bg-slate-800/90 text-slate-200 rounded-tl-xs border border-white/10 shadow-sm whitespace-pre-wrap',
                  msg.isError ? 'bg-rose-950/60 border-rose-500/50 text-rose-200' : ''
                ]"
              >
                {{ msg.text }}
                <span v-if="msg.isStreaming" class="inline-block w-1.5 h-3.5 ml-1 bg-emerald-400 animate-pulse align-middle"></span>
              </div>

              <!-- Metadata & Actions for Assistant Response -->
              <div v-if="msg.role === 'assistant' && (msg.sources?.length > 0 || msg.model || hasTable(msg.text))" class="flex flex-wrap items-center gap-2 mt-1 px-1">
                <div v-if="msg.confidence !== null" class="flex items-center gap-1.5 text-[10px] font-medium bg-slate-800/80 px-2 py-0.5 rounded border border-slate-700/50">
                  <span class="text-slate-400">Confidence:</span>
                  <span :class="confidenceColor(msg.confidence)">{{ (msg.confidence * 100).toFixed(1) }}%</span>
                </div>
                
                <div v-if="msg.model" class="flex items-center gap-1 text-[10px] font-mono bg-slate-800/80 px-2 py-0.5 rounded border border-slate-700/50 text-slate-400">
                  {{ msg.model }} <span class="text-slate-600">|</span> <span class="text-blue-400">{{ msg.env }}</span>
                </div>

                <button
                  v-if="hasTable(msg.text)"
                  @click="exportTableToCsv(msg.text)"
                  class="apple-press flex items-center gap-1 text-[10px] font-medium bg-emerald-950/40 text-emerald-400 hover:bg-emerald-900/60 px-2 py-0.5 rounded border border-emerald-800/60 transition-colors cursor-pointer"
                  title="Export markdown tables to CSV"
                >
                  <TableIcon class="w-3 h-3" />
                  <span>Export CSV</span>
                </button>

                <div v-if="msg.sources?.length > 0" class="flex flex-wrap gap-1.5 items-center w-full mt-1">
                  <span class="text-[10px] text-slate-500 uppercase tracking-wider font-semibold">Citations:</span>
                  <SourceBadge v-for="source in msg.sources" :key="source" :source="source" />
                </div>
              </div>
            </div>
          </div>

          <!-- Loading Stage Indicator -->
          <div v-if="isQuerying && !messages.some(m => m.isStreaming)" class="flex gap-3 max-w-full">
            <div class="w-7 h-7 rounded-lg bg-emerald-600 flex items-center justify-center shrink-0">
              <Bot class="w-3.5 h-3.5 text-white" />
            </div>
            <div class="px-4 py-3 rounded-2xl bg-slate-800/90 text-slate-200 rounded-tl-xs border border-white/10 flex items-center gap-3">
              <div class="flex gap-1">
                <div class="w-1.5 h-1.5 bg-emerald-400 rounded-full animate-bounce [animation-delay:-0.3s]"></div>
                <div class="w-1.5 h-1.5 bg-emerald-400 rounded-full animate-bounce [animation-delay:-0.15s]"></div>
                <div class="w-1.5 h-1.5 bg-emerald-400 rounded-full animate-bounce"></div>
              </div>
              <span class="text-xs text-slate-400 font-medium">{{ currentStage || 'Searching indexed evidence...' }}</span>
            </div>
          </div>
        </div>

        <!-- Input Dock -->
        <div class="p-4 bg-slate-900/90 border-t border-white/10 shrink-0">
          <div class="relative flex items-center">
            <textarea
              ref="inputRef"
              v-model="query"
              @keydown.enter.prevent="sendQuery"
              placeholder="Ask about risk factors, accrual flags, revenue recognition..."
              class="w-full bg-slate-800/90 border border-slate-700/80 rounded-xl pl-4 pr-14 py-3 text-slate-100 text-xs sm:text-sm placeholder:text-slate-500 focus:outline-none focus:border-emerald-500/50 focus:ring-1 focus:ring-emerald-500/40 resize-none overflow-hidden transition-all"
              rows="2"
              :disabled="isQuerying || documentCount === 0"
            ></textarea>
            
            <button 
              @click="sendQuery"
              :disabled="!query.trim() || isQuerying || documentCount === 0"
              class="apple-press absolute right-2.5 bottom-2.5 p-2 bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-700/60 disabled:text-slate-500 text-white rounded-lg transition-all cursor-pointer shadow-xs"
              title="Send question"
            >
              <Loader2 v-if="isQuerying" class="w-4 h-4 animate-spin" />
              <Send v-else class="w-4 h-4" />
            </button>
          </div>

          <div class="flex items-center justify-between mt-2 px-1 text-[11px] text-slate-500">
            <span>Press <kbd class="px-1.5 py-0.5 bg-slate-800 rounded border border-slate-700/60 font-mono text-slate-400">Enter</kbd> to send</span>
            <span v-if="documentCount === 0" class="text-amber-400 font-medium">No documents indexed</span>
            <span v-else class="text-emerald-400/80">{{ documentCount }} document{{ documentCount !== 1 ? 's' : '' }} ready</span>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>
