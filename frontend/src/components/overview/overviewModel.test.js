import { describe, it, expect } from 'vitest'
import { buildRedFlags, riskBreakdown } from './overviewModel.js'

const nvda = {
  ticker: 'NVDA', driftScore: 8.5, driftExcerpt: 'Export controls.',
  mscore: -2.85, tataAccrual: -0.045, mscoreProb: '< 1%',
  divergenceScore: 11, radarExcerpt: 'Guidance aligned.',
  footnotesClean: true, footnoteCount: 0, footnoteExcerpt: 'Customer A 13%.'
}
const smci = {
  ticker: 'SMCI', driftScore: 42, driftExcerpt: 'Special Committee.',
  mscore: -1.42, tataAccrual: 0.124, mscoreProb: '76%',
  divergenceScore: 78.5, radarExcerpt: 'Guidance conflicts.',
  footnotesClean: false, footnoteCount: 4, footnoteExcerpt: 'Auditor resigned.'
}

describe('buildRedFlags', () => {
  it('maps each pillar to a row with source and action', () => {
    const rows = buildRedFlags(nvda)
    expect(rows.map((r) => r.id).sort()).toEqual(['accruals', 'contradictions', 'drift', 'footnotes'])
    const drift = rows.find((r) => r.id === 'drift')
    expect(drift).toMatchObject({ source: '10-K Item 1A', action: 'diff', severity: 'good', finding: 'Export controls.' })
    expect(rows.find((r) => r.id === 'footnotes').action).toBe('footnotes')
    expect(rows.find((r) => r.id === 'contradictions').source).toBe('Earnings call')
  })

  it('describes accruals against the threshold', () => {
    expect(buildRedFlags(smci).find((r) => r.id === 'accruals').finding)
      .toBe('M-Score -1.42 is above the -1.78 manipulation threshold (TATA 0.124).')
  })

  it('sorts critical first and keeps pillar order within a level', () => {
    const mixed = { ...nvda, driftScore: 42, footnotesClean: false, footnoteCount: 1 }
    expect(buildRedFlags(mixed).map((r) => r.severity)).toEqual(['critical', 'watch', 'good', 'good'])
    expect(buildRedFlags(mixed)[0].id).toBe('drift')
  })

  it('skips pillars without data', () => {
    const rows = buildRedFlags({ ticker: 'X', driftExcerpt: '', mscore: null })
    expect(rows).toEqual([])
  })
})

describe('riskBreakdown', () => {
  it('returns weighted components with formatted values and severities', () => {
    expect(riskBreakdown(smci)).toEqual([
      { id: 'drift', label: 'Language drift', weight: 30, value: '42%', severity: 'critical' },
      { id: 'mscore', label: 'Beneish M-Score', weight: 40, value: '-1.42', severity: 'critical' },
      { id: 'contradictions', label: 'Call vs 10-Q', weight: 30, value: '78.5', severity: 'critical' }
    ])
  })
  it('shows a dash for missing values', () => {
    expect(riskBreakdown({}).map((r) => r.value)).toEqual(['—', '—', '—'])
  })
})
