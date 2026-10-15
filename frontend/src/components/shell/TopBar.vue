<script setup>
import { Search, FileText, Sparkles } from 'lucide-vue-next'
import CompanySwitcher from './CompanySwitcher.vue'
import ThemeToggle from './ThemeToggle.vue'
import MenuButton from '../ui/MenuButton.vue'

defineProps({
  tabs: { type: Array, required: true }, // [{ id, label, count? }]
  currentTab: { type: String, required: true }
})

const emit = defineEmits(['update:currentTab', 'open-palette', 'memo', 'open-chat'])

const memoItems = [
  { id: 'preview', label: 'Preview memo' },
  { id: 'export', label: 'Export Markdown' }
]
</script>

<template>
  <header class="flex flex-wrap md:flex-nowrap items-center gap-x-3 gap-y-1 min-h-10 px-3 py-1 md:py-0 border-b border-line bg-panel shrink-0">
    <span class="text-sm font-semibold tracking-tight text-fg shrink-0">Zaisaku</span>
    <CompanySwitcher />

    <nav aria-label="Workspace" class="order-last md:order-none w-full md:w-auto md:flex-1 min-w-0 overflow-x-auto">
      <ul class="flex items-center gap-0.5 h-8 md:h-10">
        <template v-for="(tab, i) in tabs" :key="tab.id">
        <li v-if="i > 0 && tab.section !== tabs[i - 1].section" aria-hidden="true" class="w-px h-4 bg-line mx-1 self-center" />
        <li class="h-full">
          <button
            type="button"
            class="h-full px-2.5 text-xs font-medium whitespace-nowrap border-b-2 cursor-pointer transition-colors"
            :class="currentTab === tab.id ? 'border-accent text-fg' : 'border-transparent text-muted hover:text-fg'"
            :aria-current="currentTab === tab.id ? 'page' : undefined"
            @click="emit('update:currentTab', tab.id)"
          >
            {{ tab.label }}
            <span v-if="tab.count" class="ml-1 text-faint tabular-nums">{{ tab.count }}</span>
          </button>
        </li>
        </template>
      </ul>
    </nav>

    <div class="flex items-center gap-1 ml-auto shrink-0">
      <button type="button" class="btn-icon sm:hidden" aria-label="Open command palette" @click="emit('open-palette')">
        <Search class="w-3.5 h-3.5" />
      </button>
      <button type="button" class="btn hidden sm:inline-flex text-muted" title="Command palette" @click="emit('open-palette')">
        <Search class="w-3.5 h-3.5" />
        <kbd class="font-mono text-[10px]">⌘K</kbd>
      </button>
      <MenuButton label="Memo" :items="memoItems" @select="(id) => emit('memo', id)">
        <template #icon><FileText class="w-3.5 h-3.5 text-muted" /></template>
      </MenuButton>
      <ThemeToggle />
      <button type="button" class="btn-primary" @click="emit('open-chat')">
        <Sparkles class="w-3.5 h-3.5" />
        <span class="hidden sm:inline">Ask Zaisaku</span>
      </button>
    </div>
  </header>
</template>
