<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import CompanyHub from './components/CompanyHub.vue'
import ChatArea from './components/ChatArea.vue'

const isChatOpen = ref(false)
const chatInitialPrompt = ref('')
const documentCount = ref(0)

const handleOpenChat = (prompt = '') => {
  chatInitialPrompt.value = prompt || ''
  isChatOpen.value = true
}

const handleGlobalKeyDown = (e) => {
  // Ctrl + K or Cmd + K toggles the Co-Analyst drawer
  if ((e.ctrlKey || e.metaKey) && (e.key === 'k' || e.key === 'K')) {
    e.preventDefault()
    isChatOpen.value = !isChatOpen.value
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleGlobalKeyDown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleGlobalKeyDown)
})
</script>

<template>
  <div class="flex h-screen w-full bg-[#090d16] overflow-hidden text-slate-100">
    <!-- Primary Landing View: Institutional Company Due Diligence Hub -->
    <CompanyHub 
      @open-chat="handleOpenChat" 
      @document-count-change="(count) => documentCount = count"
    />

    <!-- Apple-Style Slide-Over Co-Analyst Drawer (Ctrl + K) -->
    <ChatArea 
      :is-open="isChatOpen"
      :document-count="documentCount"
      :initial-prompt="chatInitialPrompt"
      @close="isChatOpen = false"
    />
  </div>
</template>
