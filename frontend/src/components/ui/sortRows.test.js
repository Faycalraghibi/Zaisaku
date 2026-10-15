import { describe, it, expect } from 'vitest'
import { sortRows } from './sortRows.js'

const rows = [
  { t: 'B', v: 2 },
  { t: 'a', v: null },
  { t: 'C', v: 10 },
  { t: 'd', v: -1 }
]

describe('sortRows', () => {
  it('sorts numbers ascending with nulls last', () => {
    expect(sortRows(rows, 'v', 'asc').map((r) => r.v)).toEqual([-1, 2, 10, null])
  })
  it('sorts numbers descending with nulls still last', () => {
    expect(sortRows(rows, 'v', 'desc').map((r) => r.v)).toEqual([10, 2, -1, null])
  })
  it('sorts strings case-insensitively', () => {
    expect(sortRows(rows, 't', 'asc').map((r) => r.t)).toEqual(['a', 'B', 'C', 'd'])
  })
  it('returns a copy and leaves input untouched without a key', () => {
    const out = sortRows(rows, null, 'asc')
    expect(out).toEqual(rows)
    expect(out).not.toBe(rows)
  })
})
