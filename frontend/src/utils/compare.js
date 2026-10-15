import { buildRedFlags } from '../components/overview/overviewModel.js'

export const MAX_COMPARE = 4

const criticalCount = (p) => buildRedFlags(p).filter((f) => f.severity === 'critical').length
const footnoteFlags = (p) => (p.footnotesClean === false ? (p.footnoteCount ?? 0) : 0)

// worse: 'high' marks the largest value as worst; null = descriptive row.
const METRICS = [
  { key: 'ffi', label: 'Forensic fragility index', get: (p) => p.ffi, worse: 'high' },
  { key: 'mscore', label: 'Beneish M-Score', get: (p) => p.mscore, worse: 'high', format: (v) => v.toFixed(2) },
  { key: 'drift', label: 'Language drift', get: (p) => p.driftScore, worse: 'high', format: (v) => `${v}%` },
  { key: 'decoupling', label: 'Call vs 10-Q decoupling', get: (p) => p.divergenceScore, worse: 'high' },
  { key: 'footnotes', label: 'Footnote flags', get: footnoteFlags, worse: 'high' },
  { key: 'critical', label: 'Critical red flags', get: criticalCount, worse: 'high' },
  { key: 'auditor', label: 'Auditor', get: (p) => p.auditor, worse: null },
  { key: 'period', label: 'Period', get: (p) => p.period, worse: null }
]

export function compareRows (profiles) {
  return METRICS.map((m) => {
    const raw = profiles.map((p) => m.get(p) ?? null)
    const values = raw.map((v) => (v === null ? '—' : m.format ? m.format(v) : String(v)))
    let worstIndex = null
    if (m.worse) {
      const nums = raw.map((v) => (typeof v === 'number' ? v : null))
      const valid = nums.filter((v) => v !== null)
      if (valid.length > 1 && Math.max(...valid) !== Math.min(...valid)) worstIndex = nums.indexOf(Math.max(...valid))
    }
    return { key: m.key, label: m.label, values, worstIndex, numeric: Boolean(m.worse) }
  })
}

export function parseCompareHash (hash) {
  const match = /^#compare=([A-Za-z0-9.,-]*)$/.exec(hash || '')
  if (!match) return null
  const tickers = match[1].split(',').map((t) => t.trim().toUpperCase()).filter(Boolean)
  return [...new Set(tickers)].slice(0, MAX_COMPARE)
}

export const formatCompareHash = (tickers) => `#compare=${tickers.join(',')}`
