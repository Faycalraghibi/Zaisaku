import { describe, it, expect } from 'vitest'
import { scalePosition } from './scale.js'

describe('scalePosition', () => {
  it('maps value linearly to 0..100', () => {
    expect(scalePosition(-2, -4, 0)).toBe(50)
    expect(scalePosition(-4, -4, 0)).toBe(0)
    expect(scalePosition(0, -4, 0)).toBe(100)
  })
  it('clamps out-of-range values', () => {
    expect(scalePosition(-9, -4, 0)).toBe(0)
    expect(scalePosition(3, -4, 0)).toBe(100)
  })
  it('returns null for missing values or a zero-width range', () => {
    expect(scalePosition(null, -4, 0)).toBeNull()
    expect(scalePosition(1, 2, 2)).toBeNull()
  })
})
