<script setup>
import { ref, watch, nextTick } from 'vue'
import { X } from 'lucide-vue-next'
import { SHORTCUTS } from '../../composables/useShortcuts.js'

const props = defineProps({ open: { type: Boolean, default: false } })
const emit = defineEmits(['close'])

const closeButton = ref(null)
watch(() => props.open, async (isOpen) => {
  if (isOpen) {
    await nextTick()
    closeButton.value?.focus()
  }
})
</script>

<template>
  <div v-if="open" class="fixed inset-0 z-[60] flex items-center justify-center bg-[rgb(0_0_0/0.5)] p-4" @click.self="emit('close')" @keydown.esc="emit('close')">
    <div role="dialog" aria-modal="true" aria-labelledby="shortcut-help-title" class="w-full max-w-md rounded-md border border-line bg-panel text-fg shadow-xl">
      <header class="flex items-center justify-between h-10 px-4 border-b border-line">
        <h2 id="shortcut-help-title" class="text-sm font-semibold">Keyboard shortcuts</h2>
        <button ref="closeButton" type="button" class="btn-icon" aria-label="Close" @click="emit('close')"><X class="w-3.5 h-3.5" /></button>
      </header>
      <dl class="p-4 grid grid-cols-[auto_1fr] gap-x-6 gap-y-2 text-xs">
        <template v-for="s in SHORTCUTS" :key="s.action">
          <dt class="flex gap-1">
            <kbd v-for="k in s.keys.split(' ')" :key="k" class="min-w-6 h-6 px-1.5 inline-flex items-center justify-center rounded border border-line bg-raised font-mono text-[11px]">{{ k }}</kbd>
          </dt>
          <dd class="self-center text-muted">{{ s.label }}</dd>
        </template>
        <dt class="flex gap-1"><kbd class="h-6 px-1.5 inline-flex items-center rounded border border-line bg-raised font-mono text-[11px]">⌘K</kbd></dt>
        <dd class="self-center text-muted">Command palette</dd>
      </dl>
    </div>
  </div>
</template>
