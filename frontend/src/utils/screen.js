import { buildRedFlags } from '../components/overview/overviewModel.js'
import { isIndexTicker } from '../data/companyProfiles.js'

export const EMPTY_CRITERIA = Object.freeze({
  ffi_min: null, ffi_max: null, mscore_above: null, drift_min: null, sector: null, kind: 'all', critical_only: false
})

const toNumber = (v) => (v === null || v === undefined || v === '' || Number.isNaN(Number(v)) ? null : Number(v))

// Form inputs give strings; the API and filters want numbers or null.
export function normalizeCriteria (criteria = {}) {
  const c = { ...EMPTY_CRITERIA, ...criteria }
  return {
    ffi_min: toNumber(c.ffi_min),
    ffi_max: toNumber(c.ffi_max),
    mscore_above: toNumber(c.mscore_above),
    drift_min: toNumber(c.drift_min),
    sector: c.sector ? String(c.sector) : null,
    kind: ['company', 'index'].includes(c.kind) ? c.kind : 'all',
    critical_only: Boolean(c.critical_only)
  }
}

const isIndex = (p) => Boolean(p.is_macro_index) || isIndexTicker(p.ticker)

export function applyScreen (profiles, criteria) {
  const c = normalizeCriteria(criteria)
  return profiles.filter((p) => {
    if (c.kind === 'company' && isIndex(p)) return false
    if (c.kind === 'index' && !isIndex(p)) return false
    if (c.ffi_min !== null && !(p.ffi >= c.ffi_min)) return false
    if (c.ffi_max !== null && !(p.ffi <= c.ffi_max)) return false
    if (c.mscore_above !== null && !(p.mscore > c.mscore_above)) return false
    if (c.drift_min !== null && !(p.driftScore >= c.drift_min)) return false
    if (c.sector && p.sector !== c.sector) return false
    if (c.critical_only && !buildRedFlags(p).some((f) => f.severity === 'critical')) return false
    return true
  })
}

export const sectorsOf = (profiles) =>
  [...new Set(profiles.map((p) => p.sector).filter(Boolean))].sort((a, b) => a.localeCompare(b))

export function describeCriteria (criteria) {
  const c = normalizeCriteria(criteria)
  const parts = []
  if (c.ffi_min !== null) parts.push(`FFI ≥ ${c.ffi_min}`)
  if (c.ffi_max !== null) parts.push(`FFI ≤ ${c.ffi_max}`)
  if (c.mscore_above !== null) parts.push(`M-Score > ${c.mscore_above}`)
  if (c.drift_min !== null) parts.push(`Drift ≥ ${c.drift_min}%`)
  if (c.sector) parts.push(c.sector)
  if (c.kind === 'company') parts.push('Companies')
  if (c.kind === 'index') parts.push('Indices')
  if (c.critical_only) parts.push('Critical flag')
  return parts.length ? parts.join(' · ') : 'All companies'
}
