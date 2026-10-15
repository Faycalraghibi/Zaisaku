import { describe, it, expect } from 'vitest'
import { toCsv } from './csv.js'

describe('toCsv', () => {
  const columns = [
    { key: 'ticker', label: 'Ticker' },
    { key: 'name', label: 'Name, full' },
    { key: 'mscore', label: 'M-Score' },
    { label: 'Computed', value: (r) => r.ffi * 2 }
  ]

  it('writes a header and quoted rows with CRLF', () => {
    const csv = toCsv(columns, [{ ticker: 'NVDA', name: 'NVIDIA "Corp"', mscore: -2.85, ffi: 9 }])
    expect(csv).toBe('Ticker,"Name, full",M-Score,Computed\r\nNVDA,"NVIDIA ""Corp""",-2.85,18\r\n')
  })

  it('leaves blanks for null and undefined', () => {
    expect(toCsv([{ key: 'a', label: 'A' }], [{ a: null }, {}])).toBe('A\r\n\r\n\r\n')
  })

  it('neutralises spreadsheet formula injection in text but not negative numbers', () => {
    const csv = toCsv([{ key: 'v', label: 'V' }], [{ v: '=HYPERLINK("x")' }, { v: '@cmd' }, { v: '-2.85' }, { v: '-x' }])
    expect(csv.split('\r\n').slice(1, 5)).toEqual(['"\'=HYPERLINK(""x"")"', "'@cmd", '-2.85', "'-x"])
  })
})
