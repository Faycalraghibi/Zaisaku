<script setup>
import { AlertTriangle } from 'lucide-vue-next'

defineProps({
  title: { type: String, required: true },
  state: { type: String, default: 'ready' }, // ready | loading | empty | error
  emptyText: { type: String, default: 'Nothing to show yet.' },
  errorText: { type: String, default: 'Could not load this panel.' }
})

const emit = defineEmits(['retry'])
</script>

<template>
  <section class="flex flex-col min-h-0 rounded-md border border-line bg-panel">
    <header class="flex items-center justify-between gap-2 h-8 px-3 border-b border-line shrink-0">
      <h2 class="text-[11px] font-semibold uppercase tracking-[0.04em] text-muted truncate">{{ title }}</h2>
      <div v-if="$slots.actions" class="flex items-center gap-1 shrink-0">
        <slot name="actions" />
      </div>
    </header>

    <div class="flex-1 min-h-0 overflow-auto">
      <div v-if="state === 'loading'" class="p-3 space-y-2" aria-busy="true" data-state="loading">
        <div v-for="n in 3" :key="n" class="h-4 rounded-sm bg-raised animate-pulse" />
      </div>

      <div v-else-if="state === 'empty'" class="p-3 flex flex-wrap items-center gap-2 text-xs text-muted" data-state="empty">
        <span>{{ emptyText }}</span>
        <slot name="empty-action" />
      </div>

      <div v-else-if="state === 'error'" role="alert" class="p-3 flex items-center justify-between gap-3 text-xs" data-state="error">
        <span class="flex items-center gap-2 text-fg">
          <AlertTriangle class="w-3.5 h-3.5 text-watch shrink-0" />
          {{ errorText }}
        </span>
        <button type="button" class="btn" @click="emit('retry')">Retry</button>
      </div>

      <slot v-else />
    </div>
  </section>
</template>
