import { describe, it, expect, vi } from 'vitest'
import { createShortcutMatcher, installShortcuts, onShortcut, SHORTCUTS } from './useShortcuts.js'

const clock = () => {
  let t = 0
  return { now: () => t, advance: (ms) => { t += ms } }
}

describe('createShortcutMatcher', () => {
  it('matches single keys and two-key sequences', () => {
    const c = clock()
    const match = createShortcutMatcher(SHORTCUTS, { now: c.now })
    expect(match('j')).toBe('flag-next')
    expect(match('g')).toBeNull()
    expect(match('o')).toBe('go-overview')
  })
  it('drops a pending prefix after the timeout', () => {
    const c = clock()
    const match = createShortcutMatcher(SHORTCUTS, { now: c.now, timeout: 1000 })
    match('g')
    c.advance(1500)
    expect(match('o')).toBeNull()
  })
  it('recovers when a prefix is followed by an unrelated key', () => {
    const match = createShortcutMatcher(SHORTCUTS, { now: () => 0 })
    match('g')
    expect(match('j')).toBe('flag-next')
    expect(match('x')).toBeNull()
  })
})

describe('installShortcuts', () => {
  it('dispatches to subscribers, ignores typing and modifiers', () => {
    const target = document.createElement('div')
    document.body.appendChild(target)
    const uninstall = installShortcuts(target)
    const spy = vi.fn()
    const off = onShortcut('flag-next', spy)

    target.dispatchEvent(new KeyboardEvent('keydown', { key: 'j', bubbles: true }))
    expect(spy).toHaveBeenCalledTimes(1)

    const input = document.createElement('input')
    target.appendChild(input)
    input.dispatchEvent(new KeyboardEvent('keydown', { key: 'j', bubbles: true }))
    target.dispatchEvent(new KeyboardEvent('keydown', { key: 'j', ctrlKey: true, bubbles: true }))
    expect(spy).toHaveBeenCalledTimes(1)

    off()
    uninstall()
  })
})
