import { describe, it, expect } from 'vitest'
import { portfolioRow, isUnresolved, unresolvedCount } from './portfolio.js'
import { companyProfiles } from '../data/companyProfiles.js'

const smci = companyProfiles.SMCI
const nvda = companyProfiles.NVDA

describe('isUnresolved', () => {
  it('ignores low-severity flags', () => {
    expect(isUnresolved({ severity: 'good' }, null)).toBe(false)
  })
  it('treats missing, open and escalated reviews as unresolved', () => {
    expect(isUnresolved({ severity: 'critical' }, null)).toBe(true)
    expect(isUnresolved({ severity: 'watch' }, { status: 'open' })).toBe(true)
    expect(isUnresolved({ severity: 'watch' }, { status: 'escalated' })).toBe(true)
    expect(isUnresolved({ severity: 'critical' }, { status: 'reviewed' })).toBe(false)
    expect(isUnresolved({ severity: 'critical' }, { status: 'dismissed' })).toBe(false)
  })
})

describe('portfolioRow', () => {
  it('summarises a covered company', () => {
    const row = portfolioRow('SMCI', smci, [])
    expect(row).toMatchObject({ ticker: 'SMCI', covered: true, ffi: smci.ffi, critical: 4, watch: 0, unresolved: 4 })
  })
  it('counts reviewed flags as resolved', () => {
    const reviews = [{ flag_id: 'drift', status: 'reviewed' }, { flag_id: 'footnotes', status: 'dismissed' }]
    expect(unresolvedCount(smci, reviews)).toBe(2)
  })
  it('reports zero unresolved for a clean company', () => {
    expect(portfolioRow('NVDA', nvda, []).unresolved).toBe(0)
  })
  it('marks tickers outside coverage without inventing metrics', () => {
    expect(portfolioRow('ZZZZ', undefined, [])).toEqual({
      ticker: 'ZZZZ', name: 'Not in coverage', covered: false,
      ffi: null, critical: null, watch: null, mscore: null, drift: null, unresolved: null
    })
  })
})
