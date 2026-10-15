<script setup>
import { ref, computed, watch } from 'vue'
import Panel from '../ui/Panel.vue'
import { useNotes } from '../../composables/useNotes.js'

const props = defineProps({
  ticker: { type: String, required: true }
})

const { load, notesFor, stateFor, add, update, remove } = useNotes()

watch(() => props.ticker, (t) => load(t), { immediate: true })

const notes = computed(() => notesFor(props.ticker))
const panelState = computed(() => {
  const s = stateFor(props.ticker)
  return s === 'loading' || s === 'idle' ? 'loading' : s === 'error' ? 'error' : 'ready'
})

const draft = ref('')
const editingId = ref(null)
const editDraft = ref('')

const submit = async () => {
  const body = draft.value.trim()
  if (!body) return
  if (await add(props.ticker, body)) draft.value = ''
}

const startEdit = (note) => {
  editingId.value = note.id
  editDraft.value = note.body
}

const saveEdit = async (note) => {
  const body = editDraft.value.trim()
  if (!body) return
  if (await update(props.ticker, note.id, body)) editingId.value = null
}

const formatDate = (iso) =>
  new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
</script>

<template>
  <Panel title="Notes" :state="panelState" error-text="Could not load notes." @retry="load(ticker)">
    <div class="p-3 space-y-3">
      <form class="space-y-2" @submit.prevent="submit">
        <textarea
          v-model="draft"
          rows="2"
          maxlength="5000"
          :aria-label="`New note for ${ticker}`"
          :placeholder="`Add a note on ${ticker}… (Ctrl+Enter to save)`"
          class="w-full resize-y rounded border border-line bg-bg text-xs text-fg p-2 outline-none focus:border-accent placeholder:text-faint"
          @keydown.ctrl.enter.prevent="submit"
          @keydown.meta.enter.prevent="submit"
        />
        <div class="flex justify-end">
          <button type="submit" class="btn-primary" :disabled="!draft.trim()">Add note</button>
        </div>
      </form>

      <p v-if="!notes.length" class="text-xs text-muted">No notes yet.</p>
      <ul v-else class="space-y-2">
        <li v-for="note in notes" :key="note.id" class="border-t border-line pt-2 space-y-1" :data-note="note.id">
          <div class="flex items-center justify-between gap-2 text-[11px] text-faint">
            <time :datetime="note.created_at">{{ formatDate(note.created_at) }}</time>
            <span v-if="editingId !== note.id" class="flex gap-0.5">
              <button type="button" class="btn-ghost h-5" @click="startEdit(note)">Edit</button>
              <button type="button" class="btn-ghost h-5" @click="remove(ticker, note.id)">Delete</button>
            </span>
          </div>
          <template v-if="editingId === note.id">
            <textarea
              v-model="editDraft"
              rows="3"
              maxlength="5000"
              aria-label="Edit note"
              class="w-full resize-y rounded border border-line bg-bg text-xs text-fg p-2 outline-none focus:border-accent"
              @keydown.ctrl.enter.prevent="saveEdit(note)"
              @keydown.meta.enter.prevent="saveEdit(note)"
              @keydown.esc="editingId = null"
            />
            <div class="flex justify-end gap-1">
              <button type="button" class="btn-ghost" @click="editingId = null">Cancel</button>
              <button type="button" class="btn-primary" :disabled="!editDraft.trim()" @click="saveEdit(note)">Save</button>
            </div>
          </template>
          <p v-else class="text-xs text-fg whitespace-pre-wrap break-words">{{ note.body }}</p>
        </li>
      </ul>
    </div>
  </Panel>
</template>
