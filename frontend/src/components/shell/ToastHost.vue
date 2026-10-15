<script setup>
import { X } from 'lucide-vue-next'
import { useToasts } from '../../composables/useToasts.js'

const { toasts, dismiss } = useToasts()

const runAction = (toast) => {
  dismiss(toast.id)
  toast.action.run()
}
</script>

<template>
  <div class="fixed bottom-4 right-4 z-[70] flex flex-col gap-2 w-80 max-w-[calc(100vw-2rem)]" role="status" aria-live="polite">
    <div
      v-for="toast in toasts"
      :key="toast.id"
      class="flex items-center gap-2 pl-3 pr-1 py-1.5 rounded-md border bg-panel text-fg shadow-lg text-xs"
      :class="toast.tone === 'error' ? 'border-critical' : 'border-line'"
    >
      <span class="flex-1">{{ toast.message }}</span>
      <button v-if="toast.action" type="button" class="btn-ghost text-accent" @click="runAction(toast)">{{ toast.action.label }}</button>
      <button type="button" class="btn-icon w-6 h-6" aria-label="Dismiss notification" @click="dismiss(toast.id)">
        <X class="w-3 h-3" />
      </button>
    </div>
  </div>
</template>
