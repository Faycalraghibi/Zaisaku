import {
  MSCORE_THRESHOLD,
  SEVERITY_RANK,
  driftSeverity,
  decouplingSeverity,
  mscoreSeverity,
  footnoteSeverity
} from '../../utils/ffi.js'

const has = (v) => v !== null && v !== undefined && v !== ''

export function buildRedFlags (p) {
  const rows = []
  if (has(p.driftExcerpt)) {
    rows.push({ id: 'drift', severity: driftSeverity(p.driftScore), finding: p.driftExcerpt, source: '10-K Item 1A', action: 'diff' })
  }
  if (has(p.mscore)) {
    const side = p.mscore > MSCORE_THRESHOLD ? 'above' : 'below'
    const tata = has(p.tataAccrual) ? ` (TATA ${p.tataAccrual})` : ''
    rows.push({
      id: 'accruals',
      severity: mscoreSeverity(p.mscore),
      finding: `M-Score ${p.mscore} is ${side} the ${MSCORE_THRESHOLD} manipulation threshold${tata}.`,
      source: '10-K financials',
      action: 'mscore'
    })
  }
  if (has(p.radarExcerpt)) {
    rows.push({ id: 'contradictions', severity: decouplingSeverity(p.divergenceScore), finding: p.radarExcerpt, source: 'Earnings call', action: 'radar' })
  }
  if (has(p.footnoteExcerpt)) {
    rows.push({ id: 'footnotes', severity: footnoteSeverity(p.footnotesClean, p.footnoteCount), finding: p.footnoteExcerpt, source: '10-K notes', action: 'footnotes' })
  }
  // Array.prototype.sort is stable, so pillar order is kept within a severity level.
  return rows.sort((a, b) => SEVERITY_RANK[a.severity] - SEVERITY_RANK[b.severity])
}

const fmt = (v, suffix = '') => (has(v) ? `${v}${suffix}` : '—')

export function riskBreakdown (p) {
  return [
    { id: 'drift', label: 'Language drift', weight: 30, value: fmt(p.driftScore, '%'), severity: driftSeverity(p.driftScore) },
    { id: 'mscore', label: 'Beneish M-Score', weight: 40, value: fmt(p.mscore), severity: mscoreSeverity(p.mscore) },
    { id: 'contradictions', label: 'Call vs 10-Q', weight: 30, value: fmt(p.divergenceScore), severity: decouplingSeverity(p.divergenceScore) }
  ]
}
