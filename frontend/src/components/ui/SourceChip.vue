<script setup>
defineProps({
  label: { type: String, required: true }
})
const emit = defineEmits(['open'])
</script>

<template>
  <button
    type="button"
    class="inline-flex items-center h-5 px-1.5 rounded-sm border border-line font-mono text-[10px] text-muted hover:text-fg hover:border-accent whitespace-nowrap cursor-pointer"
    :title="`Open source: ${label}`"
    @click.stop="emit('open')"
  >
    {{ label }}
  </button>
</template>
