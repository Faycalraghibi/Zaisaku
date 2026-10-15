<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { ChevronDown } from 'lucide-vue-next'

defineProps({
  label: { type: String, required: true },
  items: { type: Array, default: () => [] }, // [{ id, label }]
  align: { type: String, default: 'right' }
})

const emit = defineEmits(['select'])

const open = ref(false)
const root = ref(null)

const onDocumentPointer = (e) => {
  if (root.value && !root.value.contains(e.target)) open.value = false
}

onMounted(() => document.addEventListener('mousedown', onDocumentPointer))
onUnmounted(() => document.removeEventListener('mousedown', onDocumentPointer))

const choose = (item) => {
  open.value = false
  emit('select', item.id)
}
</script>

<template>
  <div ref="root" class="relative" @keydown.esc="open = false">
    <button type="button" class="btn" aria-haspopup="menu" :aria-expanded="open" @click="open = !open">
      <slot name="icon" />
      <span>{{ label }}</span>
      <ChevronDown class="w-3 h-3 text-faint" />
    </button>
    <div
      v-if="open"
      role="menu"
      class="absolute top-full mt-1 z-40 min-w-44 rounded-md border border-line bg-panel shadow-lg py-1"
      :class="align === 'right' ? 'right-0' : 'left-0'"
    >
      <button
        v-for="item in items"
        :key="item.id"
        type="button"
        role="menuitem"
        class="w-full text-left px-3 h-7 text-xs text-fg hover:bg-raised cursor-pointer"
        @click="choose(item)"
      >
        {{ item.label }}
      </button>
    </div>
  </div>
</template>
