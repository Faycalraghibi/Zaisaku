import { describe, it, expect, vi } from 'vitest'
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

describe('selectCompany with a search entry', () => {
  it('keeps the curated profile for covered tickers', async () => {
    const { companyProfiles } = await import('../data/companyProfiles.js')
    const { currentCompany, selectCompany } = useCompany()
    selectCompany('SMCI', { ticker: 'SMCI', name: 'Super Micro Computer', ffi_score: 84 })
    expect(currentCompany.value).toStrictEqual(companyProfiles.SMCI)
  })
})

describe('runSearch', () => {
  it('never shows results from a previous query', async () => {
    vi.useFakeTimers()
    const pending = []
    vi.stubGlobal('fetch', vi.fn(() => new Promise((resolve) => pending.push(resolve))))
    const { searchResults, runSearch } = useCompany()
    const reply = (i, results) => pending[i]({ ok: true, json: async () => ({ results }) })

    runSearch('smci')
    await vi.advanceTimersByTimeAsync(200)
    reply(0, [{ ticker: 'SMCI' }])
    await vi.advanceTimersByTimeAsync(0)
    expect(searchResults.value.map((r) => r.ticker)).toEqual(['SMCI'])

    runSearch('googl')
    expect(searchResults.value).toEqual([])

    await vi.advanceTimersByTimeAsync(200)
    runSearch('goog')
    await vi.advanceTimersByTimeAsync(200)
    reply(2, [{ ticker: 'GOOGL' }])
    reply(1, [{ ticker: 'STALE' }])
    await vi.advanceTimersByTimeAsync(0)
    expect(searchResults.value.map((r) => r.ticker)).toEqual(['GOOGL'])
    vi.useRealTimers()
  })
})
