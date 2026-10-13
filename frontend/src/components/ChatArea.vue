<script setup>
import { ref, nextTick, computed } from 'vue'
import { Send, Bot, User, Loader2, Sparkles, Table as TableIcon } from 'lucide-vue-next'
import SourceBadge from './SourceBadge.vue'

const props = defineProps({
  documentCount: {
    type: Number,
    default: 0
  }
})

const messages = ref([
  {
    role: 'assistant',
    text: 'Hello! I am Zaisaku, your financial AI assistant. Upload some documents on the left and ask me questions about them.',
    sources: [],
    confidence: null,
    model: null
  }
])

const query = ref('')
const isQuerying = ref(false)
const currentStage = ref('')
const chatContainer = ref(null)

const scrollToBottom = async () => {
  await nextTick()
  if (chatContainer.value) {
    chatContainer.value.scrollTop = chatContainer.value.scrollHeight
  }
}

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
  <div class="flex flex-col flex-1 h-full bg-slate-950">
    <div class="h-16 border-b border-slate-800 flex items-center justify-between px-6 shrink-0 bg-slate-900/50 backdrop-blur-md">
      <h1 class="text-lg font-medium text-slate-100 flex items-center gap-2">
        <Sparkles class="w-5 h-5 text-emerald-500" />
        Chat with Documents
      </h1>
      <div class="text-xs text-slate-400 bg-slate-800 px-3 py-1.5 rounded-full font-mono flex items-center gap-2">
        <div class="w-2 h-2 rounded-full" :class="documentCount > 0 ? 'bg-emerald-500' : 'bg-amber-500'"></div>
        {{ documentCount }} Doc{{ documentCount !== 1 ? 's' : '' }} Indexed
      </div>
    </div>

    <div ref="chatContainer" class="flex-1 overflow-y-auto p-4 sm:p-6 space-y-6 scroll-smooth">
      <div 
        v-for="(msg, idx) in messages" 
        :key="idx"
        class="flex gap-4 max-w-4xl mx-auto"
        :class="msg.role === 'user' ? 'flex-row-reverse' : ''"
      >
        <div 
          class="w-8 h-8 rounded-full flex items-center justify-center shrink-0 mt-1"
          :class="msg.role === 'user' ? 'bg-blue-600' : 'bg-emerald-600'"
        >
          <User v-if="msg.role === 'user'" class="w-4 h-4 text-white" />
          <Bot v-else class="w-4 h-4 text-white" />
        </div>

        <div 
          class="flex flex-col gap-2 max-w-[80%]"
          :class="msg.role === 'user' ? 'items-end' : 'items-start'"
        >
          <div 
            class="px-5 py-3.5 rounded-2xl shadow-sm text-sm"
            :class="[
              msg.role === 'user' 
                ? 'bg-blue-600 text-white rounded-tr-sm' 
                : 'bg-slate-800 text-slate-200 rounded-tl-sm border border-slate-700 leading-relaxed whitespace-pre-wrap',
              msg.isError ? 'bg-red-900/50 border-red-500 text-red-200' : ''
            ]"
          >
            {{ msg.text }}
            <span v-if="msg.isStreaming" class="inline-block w-1.5 h-3.5 ml-1 bg-emerald-400 animate-pulse align-middle"></span>
          </div>

          <div v-if="msg.role === 'assistant' && (msg.sources?.length > 0 || msg.model || hasTable(msg.text))" class="flex flex-wrap items-center gap-x-4 gap-y-2 mt-1 px-1">
            <div v-if="msg.confidence !== null" class="flex items-center gap-1.5 text-xs font-medium bg-slate-800/80 px-2 py-1 rounded border border-slate-700/50">
              <span class="text-slate-400">Confidence:</span>
              <span :class="confidenceColor(msg.confidence)">{{ (msg.confidence * 100).toFixed(1) }}%</span>
            </div>
            
            <div v-if="msg.model" class="flex items-center gap-1.5 text-xs font-mono bg-slate-800/80 px-2 py-1 rounded border border-slate-700/50 text-slate-400">
               {{ msg.model }} <span class="text-slate-600">|</span> <span class="text-blue-400">{{ msg.env }}</span>
            </div>

            <button
              v-if="hasTable(msg.text)"
              @click="exportTableToCsv(msg.text)"
              class="flex items-center gap-1.5 text-xs font-medium bg-emerald-950/40 text-emerald-400 hover:bg-emerald-900/60 px-2.5 py-1 rounded border border-emerald-800/60 transition-colors cursor-pointer"
              title="Export tables in this response to CSV"
            >
              <TableIcon class="w-3.5 h-3.5" />
              <span>Export CSV</span>
            </button>

            <div v-if="msg.sources?.length > 0" class="flex flex-wrap gap-2 items-center w-full mt-1.5">
              <span class="text-xs text-slate-500">Sources:</span>
              <SourceBadge v-for="source in msg.sources" :key="source" :source="source" />
            </div>
          </div>
        </div>
      </div>

      <div v-if="isQuerying && !messages.some(m => m.isStreaming)" class="flex gap-4 max-w-4xl mx-auto">
        <div class="w-8 h-8 rounded-full bg-emerald-600 flex items-center justify-center shrink-0">
          <Bot class="w-4 h-4 text-white" />
        </div>
        <div class="px-5 py-4 rounded-2xl bg-slate-800 text-slate-200 rounded-tl-sm border border-slate-700 flex items-center gap-3">
          <div class="flex gap-1">
            <div class="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-bounce [animation-delay:-0.3s]"></div>
            <div class="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-bounce [animation-delay:-0.15s]"></div>
            <div class="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-bounce"></div>
          </div>
          <span class="text-sm text-slate-400 font-medium">{{ currentStage || 'Analyzing documents...' }}</span>
        </div>
      </div>
    </div>

    <div class="p-4 bg-slate-900 border-t border-slate-800 shrink-0">
      <div class="max-w-4xl mx-auto relative">
        <textarea
          v-model="query"
          @keydown.enter.prevent="sendQuery"
          placeholder="Ask a question about the documents..."
          class="w-full bg-slate-800 border-2 border-slate-700 rounded-xl pl-4 pr-16 py-3.5 text-slate-200 text-sm placeholder:text-slate-500 focus:outline-none focus:border-emerald-500/50 focus:ring-1 focus:ring-emerald-500/50 resize-none overflow-hidden hover:border-slate-600 transition-colors"
          rows="1"
          :disabled="isQuerying || documentCount === 0"
          title="Type your question and press Enter"
        ></textarea>
        
        <button 
          @click="sendQuery"
          :disabled="!query.trim() || isQuerying || documentCount === 0"
          class="absolute right-2 top-2 p-2 bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-700 disabled:text-slate-500 text-white rounded-lg transition-colors group"
        >
          <Loader2 v-if="isQuerying" class="w-4 h-4 animate-spin" />
          <Send v-else class="w-4 h-4 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform" />
        </button>
      </div>
      <div class="text-center mt-2 text-[10px] text-slate-500">
        Press <kbd class="px-1 py-0.5 bg-slate-800 rounded border border-slate-700 font-mono text-slate-400">Enter</kbd> to send
      </div>
    </div>
  </div>
</template>
