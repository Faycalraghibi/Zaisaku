<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import CompanyHub from './components/CompanyHub.vue'
import ChatArea from './components/ChatArea.vue'
import CommandPaletteModal from './components/CommandPaletteModal.vue'

const isChatOpen = ref(false)
const isPaletteOpen = ref(false)
const chatInitialPrompt = ref('')
const documentCount = ref(0)
const companyHubRef = ref(null)

const handleOpenChat = (prompt = '') => {
  chatInitialPrompt.value = prompt || ''
  isChatOpen.value = true
}

const handleGlobalKeyDown = (e) => {
  // Ctrl + K or Cmd + K toggles the Spotlight Command Palette
  if ((e.ctrlKey || e.metaKey) && (e.key === 'k' || e.key === 'K')) {
    e.preventDefault()
    isPaletteOpen.value = !isPaletteOpen.value
  }
}

const handleSelectWorkspace = (workspaceId) => {
  companyHubRef.value?.switchWorkspace(workspaceId)
}

const handleSelectAction = (actionId) => {
  companyHubRef.value?.triggerAction(actionId)
}

const handleSelectTicker = (ticker) => {
  companyHubRef.value?.selectCompany(ticker)
}

onMounted(() => {
  window.addEventListener('keydown', handleGlobalKeyDown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleGlobalKeyDown)
})
</script>

<template>
  <div class="flex h-screen w-full overflow-hidden bg-bg text-fg">
    <!-- Primary Landing View: Institutional Company Due Diligence Hub -->
    <CompanyHub 
      ref="companyHubRef"
      @open-chat="handleOpenChat" 
      @open-palette="isPaletteOpen = true"
      @document-count-change="(count) => documentCount = count"
    />

    <!-- Apple Spotlight Style Command Palette (⌘K) -->
    <CommandPaletteModal
      :is-open="isPaletteOpen"
      :current-ticker="companyHubRef?.currentCompany?.ticker || 'NVDA'"
      @close="isPaletteOpen = false"
      @select-workspace="handleSelectWorkspace"
      @select-action="handleSelectAction"
      @select-ticker="handleSelectTicker"
      @open-chat="handleOpenChat"
    />

    <!-- Ask Zaisaku slide-over drawer -->
    <ChatArea 
      :is-open="isChatOpen"
      :document-count="documentCount"
      :initial-prompt="chatInitialPrompt"
      @close="isChatOpen = false"
    />
  </div>
</template>
