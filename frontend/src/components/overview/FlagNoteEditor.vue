<script setup>
import { ref, nextTick, onMounted, onUnmounted } from 'vue'
import { MessageSquare, MessageSquareText } from 'lucide-vue-next'

const props = defineProps({
  note: { type: String, default: '' },
  label: { type: String, required: true }
})

const emit = defineEmits(['save'])

const POPOVER_WIDTH = 288

const open = ref(false)
const draft = ref('')
const trigger = ref(null)
const popover = ref(null)
const area = ref(null)
const position = ref({ top: 0, left: 0 })

// Fixed positioning so the popover is not clipped by the panel's scroll container.
const place = () => {
  const rect = trigger.value.getBoundingClientRect()
  position.value = {
    top: rect.bottom + 4,
    left: Math.max(8, Math.min(window.innerWidth - POPOVER_WIDTH - 8, rect.right - POPOVER_WIDTH))
  }
}

const openEditor = async () => {
  draft.value = props.note
  place()
  open.value = true
  await nextTick()
  area.value?.focus()
}

const close = () => { open.value = false }

const save = () => {
  emit('save', draft.value.trim())
  close()
}

const onPointer = (e) => {
  if (!open.value) return
  if (popover.value?.contains(e.target) || trigger.value?.contains(e.target)) return
  close()
}

onMounted(() => {
  document.addEventListener('mousedown', onPointer)
  window.addEventListener('resize', close)
})
onUnmounted(() => {
  document.removeEventListener('mousedown', onPointer)
  window.removeEventListener('resize', close)
})
</script>

<template>
  <span class="inline-block" @click.stop @keydown.stop>
    <button
      ref="trigger"
      type="button"
      class="btn-icon w-6 h-6"
      :class="note ? 'text-accent' : ''"
      :aria-label="note ? `Edit note: ${label}` : `Add note: ${label}`"
      :aria-expanded="open"
      :title="note || 'Add note'"
      @click="open ? close() : openEditor()"
    >
      <component :is="note ? MessageSquareText : MessageSquare" class="w-3.5 h-3.5" />
    </button>
    <Teleport to="body">
      <div
        v-if="open"
        ref="popover"
        role="dialog"
        :aria-label="`Note: ${label}`"
        class="fixed z-[65] rounded-md border border-line bg-panel shadow-lg p-2 space-y-2"
        :style="{ top: `${position.top}px`, left: `${position.left}px`, width: `${POPOVER_WIDTH}px` }"
        @keydown.esc="close"
      >
        <textarea
          ref="area"
          v-model="draft"
          rows="4"
          maxlength="5000"
          class="w-full resize-y rounded border border-line bg-bg text-xs text-fg p-2 outline-none focus:border-accent placeholder:text-faint"
          placeholder="Evidence, follow-ups, why this status… (Ctrl+Enter to save)"
          @keydown.ctrl.enter.prevent="save"
          @keydown.meta.enter.prevent="save"
        />
        <div class="flex justify-end gap-1">
          <button type="button" class="btn-ghost" @click="close">Cancel</button>
          <button type="button" class="btn-primary" @click="save">Save</button>
        </div>
      </div>
    </Teleport>
  </span>
</template>
