import { describe, it, expect } from 'vitest'
import { compareRows, parseCompareHash, formatCompareHash, MAX_COMPARE } from './compare.js'
import { companyProfiles } from '../data/companyProfiles.js'

const { NVDA, SMCI } = companyProfiles

describe('compareRows', () => {
  it('marks the worst numeric value per row', () => {
    const rows = compareRows([NVDA, SMCI])
    const ffi = rows.find((r) => r.key === 'ffi')
    expect(ffi.values).toEqual([String(NVDA.ffi), String(SMCI.ffi)])
    expect(ffi.worstIndex).toBe(1)
    expect(rows.find((r) => r.key === 'mscore').worstIndex).toBe(1)
  })
  it('does not mark text rows or ties', () => {
    const rows = compareRows([NVDA, NVDA])
    expect(rows.find((r) => r.key === 'ffi').worstIndex).toBeNull()
    expect(rows.find((r) => r.key === 'auditor').worstIndex).toBeNull()
  })
  it('shows a dash for missing values', () => {
    const rows = compareRows([{ ...NVDA, mscore: null }, SMCI])
    expect(rows.find((r) => r.key === 'mscore').values[0]).toBe('—')
  })
})

describe('compare hash', () => {
  it('parses, normalises, dedupes and caps tickers', () => {
    expect(parseCompareHash('#compare=nvda,SMCI,nvda,amd,aapl,msft')).toEqual(['NVDA', 'SMCI', 'AMD', 'AAPL'].slice(0, MAX_COMPARE))
  })
  it('ignores other hashes', () => {
    expect(parseCompareHash('#other')).toBeNull()
    expect(parseCompareHash('')).toBeNull()
  })
  it('formats', () => {
    expect(formatCompareHash(['NVDA', 'SMCI'])).toBe('#compare=NVDA,SMCI')
  })
})
