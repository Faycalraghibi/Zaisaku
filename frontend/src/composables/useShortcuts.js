export const SHORTCUTS = [
  { keys: 'g o', action: 'go-overview', label: 'Go to Overview' },
  { keys: 'g w', action: 'go-watchlist', label: 'Go to Watchlist' },
  { keys: 'g s', action: 'go-screener', label: 'Go to Screener' },
  { keys: 'g c', action: 'go-compare', label: 'Go to Compare' },
  { keys: 'g f', action: 'go-filings', label: 'Go to Filings' },
  { keys: '/', action: 'open-switcher', label: 'Switch company' },
  { keys: 'j', action: 'flag-next', label: 'Next red flag' },
  { keys: 'k', action: 'flag-prev', label: 'Previous red flag' },
  { keys: 'r', action: 'flag-reviewed', label: 'Mark selected flag reviewed' },
  { keys: '?', action: 'help', label: 'Show keyboard shortcuts' }
]

export function createShortcutMatcher (bindings, { timeout = 1000, now = () => Date.now() } = {}) {
  const sequences = bindings.map((b) => ({ keys: b.keys.split(' '), action: b.action }))
  let buffer = []
  let last = 0

  const exactMatch = (keys) => sequences.find((s) => s.keys.length === keys.length && s.keys.every((k, i) => k === keys[i]))
  const isPrefix = (keys) => sequences.some((s) => s.keys.length > keys.length && keys.every((k, i) => s.keys[i] === k))

  return (key) => {
    const t = now()
    if (t - last > timeout) buffer = []
    last = t

    const candidate = [...buffer, key]
    const exact = exactMatch(candidate)
    if (exact) {
      buffer = []
      return exact.action
    }
    if (isPrefix(candidate)) {
      buffer = candidate
      return null
    }
    // Not part of the pending sequence: start over from this key alone.
    buffer = []
    const single = exactMatch([key])
    if (single) return single.action
    if (isPrefix([key])) buffer = [key]
    return null
  }
}

const isTyping = (el) => {
  if (!el || !el.tagName) return false
  return ['INPUT', 'TEXTAREA', 'SELECT'].includes(el.tagName) || el.isContentEditable
}

const handlers = new Map()

export function onShortcut (action, fn) {
  if (!handlers.has(action)) handlers.set(action, new Set())
  handlers.get(action).add(fn)
  return () => handlers.get(action)?.delete(fn)
}

export function dispatchShortcut (action) {
  const set = handlers.get(action)
  if (!set || !set.size) return false
  set.forEach((fn) => fn())
  return true
}

export function installShortcuts (target = window) {
  const match = createShortcutMatcher(SHORTCUTS)
  const onKeydown = (e) => {
    if (e.ctrlKey || e.metaKey || e.altKey || e.key === 'Shift' || isTyping(e.target)) return
    const action = match(e.key)
    if (action && dispatchShortcut(action)) e.preventDefault()
  }
  target.addEventListener('keydown', onKeydown)
  return () => target.removeEventListener('keydown', onKeydown)
}
