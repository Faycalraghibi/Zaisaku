import { describe, it, expect } from 'vitest'
import { ffiSeverity, formatEnum } from './ffi.js'

describe('ffiSeverity', () => {
  it('maps FFI tiers to severity levels', () => {
    expect(ffiSeverity(10)).toBe('good')
    expect(ffiSeverity(30)).toBe('watch')
    expect(ffiSeverity(80)).toBe('critical')
  })
})

describe('formatEnum', () => {
  it('turns backend enums into readable lowercase text', () => {
    expect(formatEnum('HIGH_RISK')).toBe('high risk')
    expect(formatEnum(null)).toBe('')
  })
})

import { driftSeverity, decouplingSeverity, mscoreSeverity, footnoteSeverity, tierToSeverity } from './ffi.js'

describe('pillar severities', () => {
  it('grades drift at 15 / 30', () => {
    expect(driftSeverity(14.9)).toBe('good')
    expect(driftSeverity(15)).toBe('watch')
    expect(driftSeverity(30)).toBe('critical')
    expect(driftSeverity(null)).toBe('watch')
  })
  it('grades decoupling at 25 / 50', () => {
    expect(decouplingSeverity(24)).toBe('good')
    expect(decouplingSeverity(25)).toBe('watch')
    expect(decouplingSeverity(50)).toBe('critical')
  })
  it('grades M-Score against -2.22 / -1.78', () => {
    expect(mscoreSeverity(-2.85)).toBe('good')
    expect(mscoreSeverity(-2.0)).toBe('watch')
    expect(mscoreSeverity(-1.42)).toBe('critical')
  })
  it('grades footnote flags', () => {
    expect(footnoteSeverity(true, 0)).toBe('good')
    expect(footnoteSeverity(false, 3)).toBe('watch')
    expect(footnoteSeverity(false, 4)).toBe('critical')
  })
  it('maps backend risk tiers', () => {
    expect(tierToSeverity('CRITICAL_ALERT')).toBe('critical')
    expect(tierToSeverity('WATCHLIST')).toBe('watch')
    expect(tierToSeverity('LOW_RISK')).toBe('good')
  })
})
