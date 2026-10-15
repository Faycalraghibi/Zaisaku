import { ref } from 'vue'

const DEFAULT_TIMEOUT_MS = 5000

const toasts = ref([])
let seq = 0

const dismiss = (id) => {
  toasts.value = toasts.value.filter((t) => t.id !== id)
}

// action: { label, run } renders a button (e.g. Undo) inside the toast.
const push = (message, { tone = 'info', action = null, timeout = DEFAULT_TIMEOUT_MS } = {}) => {
  const id = ++seq
  toasts.value = [...toasts.value, { id, message, tone, action }]
  if (timeout) setTimeout(() => dismiss(id), timeout)
  return id
}

export function useToasts () {
  return { toasts, push, dismiss }
}
