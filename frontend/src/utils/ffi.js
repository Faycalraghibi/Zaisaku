// Shared Forensic Fragility Index helpers so every view labels scores identically.

export const formatEnum = (value) =>
  value ? String(value).replace(/_/g, ' ').toLowerCase() : ''

export const ffiTier = (score) => {
  if (score < 25) {
    return {
      key: 'low',
      text: 'text-emerald-400',
      bg: 'bg-emerald-500/10',
      border: 'border-emerald-500/20',
      label: 'Low fragility'
    }
  }
  if (score < 50) {
    return {
      key: 'watch',
      text: 'text-amber-400',
      bg: 'bg-amber-500/10',
      border: 'border-amber-500/20',
      label: 'Watchlist fragility'
    }
  }
  return {
    key: 'critical',
    text: 'text-rose-400',
    bg: 'bg-rose-500/10',
    border: 'border-rose-500/20',
    label: 'Critical alert'
  }
}

const TIER_TO_SEVERITY = { low: 'good', watch: 'watch', critical: 'critical' }

export const ffiSeverity = (score) => TIER_TO_SEVERITY[ffiTier(score).key]

// Beneish (1999): above -1.78 flags a likely manipulator; -2.22 is the conservative cut-off.
export const MSCORE_THRESHOLD = -1.78
export const MSCORE_GREY_ZONE = -2.22

const byThreshold = (value, watchAt, criticalAt) => {
  if (value === null || value === undefined) return 'watch'
  if (value >= criticalAt) return 'critical'
  return value >= watchAt ? 'watch' : 'good'
}

export const driftSeverity = (pct) => byThreshold(pct, 15, 30)
export const decouplingSeverity = (score) => byThreshold(score, 25, 50)

export const mscoreSeverity = (m) => {
  if (m === null || m === undefined) return 'watch'
  if (m > MSCORE_THRESHOLD) return 'critical'
  return m > MSCORE_GREY_ZONE ? 'watch' : 'good'
}

export const footnoteSeverity = (clean, count) => {
  if (clean !== false) return 'good'
  return (count ?? 0) >= 4 ? 'critical' : 'watch'
}

export const tierToSeverity = (tier) => {
  const t = String(tier || '').toUpperCase()
  if (t.startsWith('CRITICAL')) return 'critical'
  if (t === 'WATCHLIST') return 'watch'
  return 'good'
}

export const SEVERITY_RANK = { critical: 0, watch: 1, good: 2 }
