import { describe, it, expect } from 'vitest'
import { pushRecent, useCompany } from './useCompany.js'

describe('pushRecent', () => {
  it('adds to the front, dedupes, and caps length', () => {
    expect(pushRecent(['A', 'B'], 'C', 3)).toEqual(['C', 'A', 'B'])
    expect(pushRecent(['A', 'B', 'C'], 'B', 3)).toEqual(['B', 'A', 'C'])
    expect(pushRecent(['A', 'B', 'C'], 'D', 3)).toEqual(['D', 'A', 'B'])
  })
})

describe('useCompany.selectCompany', () => {
  it('selects a known profile and records it as recent', () => {
    const { currentCompany, recent, selectCompany } = useCompany()
    selectCompany('smci')
    expect(currentCompany.value.ticker).toBe('SMCI')
    expect(recent.value[0]).toBe('SMCI')
  })
  it('builds a fallback profile for unknown tickers', () => {
    const { currentCompany, selectCompany } = useCompany()
    selectCompany('ZZZZ')
    expect(currentCompany.value.ticker).toBe('ZZZZ')
    expect(currentCompany.value.name).toBe('ZZZZ Corporation')
  })
  it('ignores blank input', () => {
    const { currentCompany, selectCompany } = useCompany()
    const before = currentCompany.value
    selectCompany('  ')
    expect(currentCompany.value).toBe(before)
  })
})
