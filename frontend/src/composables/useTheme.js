import { ref, computed, watch } from 'vue'

const STORAGE_KEY = 'zaisaku-theme'
const MODES = ['system', 'light', 'dark']

export const resolveTheme = (mode, prefersDark) =>
  mode === 'system' ? (prefersDark ? 'dark' : 'light') : mode

const readMode = (storage) => {
  try {
    const value = storage?.getItem(STORAGE_KEY)
    return MODES.includes(value) ? value : 'system'
  } catch {
    return 'system'
  }
}

const writeMode = (storage, value) => {
  try {
    storage?.setItem(STORAGE_KEY, value)
  } catch {
    // Storage blocked (private mode, policy): theme still applies for this session.
  }
}

export function createTheme ({ storage, mediaQuery, root }) {
  const mode = ref(readMode(storage))
  const prefersDark = ref(Boolean(mediaQuery?.matches))
  const resolved = computed(() => resolveTheme(mode.value, prefersDark.value))

  mediaQuery?.addEventListener?.('change', (e) => { prefersDark.value = e.matches })
  watch(resolved, (value) => { root.dataset.theme = value }, { immediate: true, flush: 'sync' })

  const setMode = (value) => {
    if (!MODES.includes(value)) return
    mode.value = value
    writeMode(storage, value)
  }
  const cycle = () => setMode(MODES[(MODES.indexOf(mode.value) + 1) % MODES.length])

  return { mode, resolved, setMode, cycle }
}

let instance = null

const safeLocalStorage = () => {
  try {
    return window.localStorage
  } catch {
    return null
  }
}

export function useTheme () {
  if (!instance) {
    instance = createTheme({
      storage: safeLocalStorage(),
      mediaQuery: window.matchMedia?.('(prefers-color-scheme: dark)'),
      root: document.documentElement
    })
  }
  return instance
}
