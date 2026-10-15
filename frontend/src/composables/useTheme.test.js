import { describe, it, expect } from 'vitest'
import { createTheme, resolveTheme } from './useTheme.js'

const memoryStorage = (initial = {}) => {
  const data = { ...initial }
  return {
    getItem: (k) => (k in data ? data[k] : null),
    setItem: (k, v) => { data[k] = String(v) },
    data
  }
}

const throwingStorage = {
  getItem: () => { throw new Error('denied') },
  setItem: () => { throw new Error('denied') }
}

const fakeMedia = (matches) => {
  const listeners = []
  return {
    matches,
    addEventListener: (_, fn) => listeners.push(fn),
    fire: (m) => listeners.forEach((fn) => fn({ matches: m }))
  }
}

const fakeRoot = () => ({ dataset: {} })

describe('resolveTheme', () => {
  it('follows the OS in system mode', () => {
    expect(resolveTheme('system', true)).toBe('dark')
    expect(resolveTheme('system', false)).toBe('light')
  })
  it('honours explicit modes', () => {
    expect(resolveTheme('light', true)).toBe('light')
    expect(resolveTheme('dark', false)).toBe('dark')
  })
})

describe('createTheme', () => {
  it('defaults to system and applies the resolved theme to the root', () => {
    const root = fakeRoot()
    const theme = createTheme({ storage: memoryStorage(), mediaQuery: fakeMedia(true), root })
    expect(theme.mode.value).toBe('system')
    expect(root.dataset.theme).toBe('dark')
  })

  it('reads a stored mode', () => {
    const root = fakeRoot()
    createTheme({ storage: memoryStorage({ 'zaisaku-theme': 'light' }), mediaQuery: fakeMedia(true), root })
    expect(root.dataset.theme).toBe('light')
  })

  it('ignores an invalid stored value', () => {
    const theme = createTheme({ storage: memoryStorage({ 'zaisaku-theme': 'purple' }), mediaQuery: fakeMedia(false), root: fakeRoot() })
    expect(theme.mode.value).toBe('system')
  })

  it('persists and applies setMode', () => {
    const storage = memoryStorage()
    const root = fakeRoot()
    const theme = createTheme({ storage, mediaQuery: fakeMedia(false), root })
    theme.setMode('dark')
    expect(storage.data['zaisaku-theme']).toBe('dark')
    expect(root.dataset.theme).toBe('dark')
  })

  it('cycles system -> light -> dark -> system', () => {
    const theme = createTheme({ storage: memoryStorage(), mediaQuery: fakeMedia(false), root: fakeRoot() })
    theme.cycle(); expect(theme.mode.value).toBe('light')
    theme.cycle(); expect(theme.mode.value).toBe('dark')
    theme.cycle(); expect(theme.mode.value).toBe('system')
  })

  it('tracks OS changes while in system mode', () => {
    const media = fakeMedia(false)
    const root = fakeRoot()
    createTheme({ storage: memoryStorage(), mediaQuery: media, root })
    media.fire(true)
    expect(root.dataset.theme).toBe('dark')
  })

  it('survives storage that throws', () => {
    const root = fakeRoot()
    const theme = createTheme({ storage: throwingStorage, mediaQuery: fakeMedia(false), root })
    expect(() => theme.setMode('dark')).not.toThrow()
    expect(root.dataset.theme).toBe('dark')
  })
})
