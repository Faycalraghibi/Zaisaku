export function scalePosition (value, min, max) {
  if (value === null || value === undefined || Number.isNaN(Number(value)) || max === min) return null
  const pct = ((Number(value) - min) / (max - min)) * 100
  return Math.min(100, Math.max(0, pct))
}
