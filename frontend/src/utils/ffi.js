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
