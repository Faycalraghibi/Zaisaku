<script setup>
import { ref, watch, onMounted } from 'vue'
import { UploadCloud, Trash2, File as FileIcon, Loader2, AlertCircle } from 'lucide-vue-next'

const documents = ref([])
const isUploading = ref(false)
const isLoadingDocs = ref(true)
const errorMsg = ref('')

const emit = defineEmits(['document-change'])

const fetchDocuments = async () => {
  isLoadingDocs.value = true
  errorMsg.value = ''
  try {
    const res = await fetch('/api/documents')
    if (!res.ok) throw new Error('Failed to fetch documents')
    const data = await res.json()
    documents.value = data.documents || []
  } catch (err) {
    errorMsg.value = err.message
  } finally {
    isLoadingDocs.value = false
  }
}

const deleteDocument = async (docId) => {
  if (!confirm('Are you sure you want to delete this document?')) return
  
  try {
    const res = await fetch(`/api/documents/${docId}`, { method: 'DELETE' })
    if (!res.ok) throw new Error('Failed to delete document')
    await fetchDocuments()
    emit('document-change')
  } catch (err) {
    errorMsg.value = err.message
  }
}

const handleFileUpload = async (event) => {
  const file = event.target.files[0]
  if (!file) return

  const formData = new FormData()
  formData.append('file', file)

  isUploading.value = true
  errorMsg.value = ''

  try {
    const res = await fetch('/api/ingest', {
      method: 'POST',
      body: formData
    })
    
    if (!res.ok) {
      const errData = await res.json()
      throw new Error(errData.detail || 'Upload failed')
    }
    
    event.target.value = ''
    await fetchDocuments()
    emit('document-change')
  } catch (err) {
    errorMsg.value = err.message
  } finally {
    isUploading.value = false
  }
}

onMounted(() => {
  fetchDocuments()
})
</script>

<template>
  <div class="flex flex-col h-full bg-slate-900 border-r border-slate-800 w-72 shrink-0">
    <div class="p-4 border-b border-slate-800">
      <h2 class="text-lg font-semibold text-slate-100 flex items-center gap-2">
        <div class="w-6 h-6 rounded-full bg-emerald-500/20 flex items-center justify-center">
          <span class="text-emerald-400 text-xs font-bold font-mono">Z</span>
        </div>
        Zaisaku RAG
      </h2>
      <p class="text-xs text-slate-400 mt-1">Financial Knowledge Base</p>
    </div>

    <div class="p-4 border-b border-slate-800 space-y-4">
      <label 
        class="flex flex-col items-center justify-center w-full h-32 border-2 border-slate-700 border-dashed rounded-lg cursor-pointer bg-slate-800/50 hover:bg-slate-800 hover:border-emerald-500/50 transition-colors relative"
        :class="{ 'opacity-50 pointer-events-none': isUploading }"
      >
        <div class="flex flex-col items-center justify-center pt-5 pb-6">
          <Loader2 v-if="isUploading" class="w-8 h-8 text-emerald-500 mb-3 animate-spin" />
          <UploadCloud v-else class="w-8 h-8 text-slate-400 mb-3" />
          <p class="mb-2 text-sm text-slate-300">
            <span class="font-semibold">Click to upload</span>
          </p>
          <p class="text-xs text-slate-500">PDF, HTML, or TXT</p>
        </div>
        <input type="file" class="hidden" accept=".pdf,.html,.txt" @change="handleFileUpload" :disabled="isUploading" />
      </label>

      <div v-if="errorMsg" class="p-3 rounded bg-red-900/20 border border-red-900/50 text-red-400 text-xs flex gap-2 items-start">
        <AlertCircle class="w-4 h-4 shrink-0 mt-0.5" />
        <span class="flex-1">{{ errorMsg }}</span>
      </div>
    </div>

    <div class="flex-1 overflow-y-auto p-2 scrollbar-thin scrollbar-thumb-slate-700">
      <div class="px-2 py-2 text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">
        Indexed Documents ({{ documents.length }})
      </div>

      <div v-if="isLoadingDocs" class="flex justify-center p-4">
        <Loader2 class="w-5 h-5 animate-spin text-slate-500" />
      </div>
      
      <div v-else-if="documents.length === 0" class="text-center p-6 text-sm text-slate-500">
        No documents uploaded yet.
      </div>

      <div v-else class="space-y-1 mt-2">
        <div 
          v-for="doc in documents" 
          :key="doc.doc_id"
          class="flex items-center justify-between group p-2 rounded-md hover:bg-slate-800 transition-colors"
        >
          <div class="flex items-center gap-3 overflow-hidden">
            <FileIcon class="w-4 h-4 text-slate-400 shrink-0" />
            <div class="flex flex-col truncate">
              <span class="text-sm text-slate-200 truncate" :title="doc.source">{{ doc.source || 'Unknown file' }}</span>
              <span class="text-[10px] text-slate-500 font-mono">{{ doc.doc_id.split('-')[0] }}...</span>
            </div>
          </div>
          <button 
            @click="deleteDocument(doc.doc_id)"
            class="p-1.5 text-slate-500 hover:text-red-400 hover:bg-slate-700 rounded opacity-0 group-hover:opacity-100 transition-all shrink-0"
            title="Delete document"
          >
            <Trash2 class="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
