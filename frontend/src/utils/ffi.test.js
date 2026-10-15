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
