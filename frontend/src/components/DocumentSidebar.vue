<script setup>
import { ref, watch, onMounted } from 'vue'
import { UploadCloud, Trash2, File as FileIcon, Loader2, AlertCircle, ExternalLink } from 'lucide-vue-next'

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
    emit('document-change', documents.value.length)
  } catch (err) {
    errorMsg.value = err.message
  } finally {
    isLoadingDocs.value = false
  }
}

const showDeleteModal = ref(false)
const docToDelete = ref(null)
const isDeleting = ref(false)

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
  errorMsg.value = ''
  try {
    const res = await fetch(`/api/documents/${docToDelete.value.doc_id}`, { method: 'DELETE' })
    if (!res.ok) throw new Error('Failed to delete document')
    showDeleteModal.value = false
    docToDelete.value = null
    await fetchDocuments()
  } catch (err) {
    errorMsg.value = err.message
  } finally {
    isDeleting.value = false
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
          <div class="flex items-center gap-1 shrink-0">
            <a 
              :href="`/api/documents/${doc.doc_id}/raw`"
              target="_blank"
              class="p-1.5 text-slate-500 hover:text-emerald-400 hover:bg-slate-700 rounded opacity-0 group-hover:opacity-100 transition-all"
              title="View original document in new tab"
            >
              <ExternalLink class="w-4 h-4" />
            </a>
            <button 
              @click="confirmDelete(doc)"
              class="p-1.5 text-slate-500 hover:text-red-400 hover:bg-slate-700 rounded opacity-0 group-hover:opacity-100 transition-all"
              title="Delete document"
            >
              <Trash2 class="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Delete Confirmation Modal -->
    <Teleport to="body">
      <div 
        v-if="showDeleteModal" 
        class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-xs"
        @keydown.esc="cancelDelete"
        @click.self="cancelDelete"
      >
        <div class="bg-slate-900 border border-slate-700/80 rounded-2xl max-w-sm w-full p-6 shadow-2xl text-slate-200 space-y-4 animate-in fade-in zoom-in-95 duration-150">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-full bg-red-950/60 border border-red-500/30 flex items-center justify-center shrink-0">
              <Trash2 class="w-5 h-5 text-red-400" />
            </div>
            <div>
              <h3 class="font-semibold text-slate-100 text-base">Delete Document</h3>
              <p class="text-xs text-slate-400">This action cannot be undone.</p>
            </div>
          </div>

          <p class="text-sm text-slate-300 leading-relaxed">
            Are you sure you want to delete <span class="font-medium text-white break-all">"{{ docToDelete?.source }}"</span>?
          </p>

          <div class="flex items-center justify-end gap-3 pt-2">
            <button
              type="button"
              @click="cancelDelete"
              :disabled="isDeleting"
              class="px-4 py-2 text-xs font-medium rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition-colors disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              type="button"
              @click="executeDelete"
              :disabled="isDeleting"
              class="px-4 py-2 text-xs font-medium rounded-lg bg-red-600 hover:bg-red-500 text-white transition-colors flex items-center gap-2 disabled:opacity-50"
            >
              <Loader2 v-if="isDeleting" class="w-3.5 h-3.5 animate-spin" />
              <span>{{ isDeleting ? 'Deleting...' : 'Delete' }}</span>
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>
