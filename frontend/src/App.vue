<script setup>
import { ref } from 'vue'
import DocumentSidebar from './components/DocumentSidebar.vue'
import ChatArea from './components/ChatArea.vue'

// We track the number of documents in App.vue so we can pass it to ChatArea
// to disable the chat input if there's no context available.
const documentCount = ref(0)
const sidebarRef = ref(null)

const handleDocumentChange = () => {
  if (sidebarRef.value && sidebarRef.value.documents) {
    documentCount.value = sidebarRef.value.documents.length
  }
}
</script>

<template>
  <main class="flex h-screen w-full bg-slate-950 overflow-hidden text-slate-200">
    <DocumentSidebar 
      ref="sidebarRef" 
      @document-change="handleDocumentChange" 
    />

    <ChatArea 
      :document-count="documentCount" 
    />
  </main>
</template>
