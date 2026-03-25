<script setup>
import { computed } from 'vue'
import { FileText, FileCode, FileImage } from 'lucide-vue-next'

const props = defineProps({
  source: {
    type: String,
    required: true
  }
})

const ext = computed(() => {
  const parts = props.source.split('.')
  return parts.length > 1 ? parts[parts.length - 1].toLowerCase() : ''
})

const icon = computed(() => {
  if (ext.value === 'pdf') return FileText
  if (ext.value === 'html') return FileCode
  return FileImage // txt/other
})

const colorClass = computed(() => {
  if (ext.value === 'pdf') return 'text-red-400 bg-red-400/10 border-red-400/20'
  if (ext.value === 'html') return 'text-orange-400 bg-orange-400/10 border-orange-400/20'
  return 'text-blue-400 bg-blue-400/10 border-blue-400/20' // txt
})
</script>

<template>
  <span 
    :class="[
      'inline-flex items-center gap-1.5 px-2 py-1 rounded-md text-xs font-medium border cursor-default transition-colors hover:bg-opacity-20',
      colorClass
    ]"
    :title="source"
  >
    <component :is="icon" class="w-3.5 h-3.5" />
    <span class="truncate max-w-[150px]">{{ source }}</span>
  </span>
</template>
