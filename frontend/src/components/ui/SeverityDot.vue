<script setup>
import { computed } from 'vue'

const props = defineProps({
  level: { type: String, required: true }, // good | watch | critical
  withLabel: { type: Boolean, default: false }
})

const LABELS = { good: 'Low', watch: 'Watch', critical: 'Critical' }
const COLORS = { good: 'bg-good', watch: 'bg-watch', critical: 'bg-critical' }

const label = computed(() => LABELS[props.level] ?? 'Unknown')
</script>

<template>
  <span class="inline-flex items-center gap-1.5">
    <span
      role="img"
      :aria-label="`Severity: ${label}`"
      class="inline-block w-2 h-2 rounded-full shrink-0"
      :class="COLORS[level] ?? 'bg-faint'"
    />
    <span v-if="withLabel" class="text-xs text-muted">{{ label }}</span>
  </span>
</template>
