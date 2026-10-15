import { describe, it, expect } from 'vitest'
import { applyScreen, sectorsOf, describeCriteria, EMPTY_CRITERIA } from './screen.js'
import { companyProfiles } from '../data/companyProfiles.js'

const all = Object.values(companyProfiles)
const tickers = (list) => list.map((p) => p.ticker).sort()

describe('applyScreen', () => {
  it('returns everything for empty criteria', () => {
    expect(applyScreen(all, EMPTY_CRITERIA)).toHaveLength(all.length)
  })
  it('filters by FFI range inclusively', () => {
    const out = applyScreen(all, { ffi_min: 60, ffi_max: 100 })
    expect(out.every((p) => p.ffi >= 60)).toBe(true)
    expect(tickers(out)).toContain('SMCI')
  })
  it('filters M-Score strictly above a threshold', () => {
    expect(applyScreen(all, { mscore_above: -1.78 }).every((p) => p.mscore > -1.78)).toBe(true)
  })
  it('separates companies and indices', () => {
    expect(applyScreen(all, { kind: 'index' }).every((p) => p.is_macro_index)).toBe(true)
    expect(applyScreen(all, { kind: 'company' }).some((p) => p.is_macro_index)).toBe(false)
  })
  it('keeps only companies with a critical red flag', () => {
    expect(tickers(applyScreen(all, { critical_only: true }))).toContain('SMCI')
    expect(tickers(applyScreen(all, { critical_only: true }))).not.toContain('NVDA')
  })
  it('treats blank form values as unset', () => {
    expect(applyScreen(all, { ffi_min: '', sector: '' })).toHaveLength(all.length)
  })
})

describe('sectorsOf / describeCriteria', () => {
  it('lists unique sorted sectors', () => {
    const s = sectorsOf(all)
    expect(s).toEqual([...new Set(s)].sort((a, b) => a.localeCompare(b)))
  })
  it('summarises active criteria', () => {
    expect(describeCriteria({ ffi_min: 50, mscore_above: -1.78, critical_only: true, kind: 'company' }))
      .toBe('FFI ≥ 50 · M-Score > -1.78 · Companies · Critical flag')
    expect(describeCriteria(EMPTY_CRITERIA)).toBe('All companies')
  })
})
