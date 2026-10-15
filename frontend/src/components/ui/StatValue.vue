<script setup>
defineProps({
  value: { type: [String, Number], required: true },
  label: { type: String, required: true },
  sub: { type: String, default: '' }
})
</script>

<template>
  <div class="space-y-0.5">
    <div class="text-[28px] leading-none font-semibold tracking-tight text-fg tabular-nums">{{ value }}</div>
    <div class="text-xs text-muted">{{ label }}</div>
    <div v-if="sub" class="text-[11px] text-faint tabular-nums">{{ sub }}</div>
  </div>
</template>
