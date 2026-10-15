import { buildRedFlags } from '../components/overview/overviewModel.js'

const UNRESOLVED_STATUSES = new Set(['open', 'escalated'])

// A flag needs attention when it is watch/critical and nobody has closed it out.
export const isUnresolved = (flag, review) =>
  flag.severity !== 'good' && (!review || UNRESOLVED_STATUSES.has(review.status))

export function unresolvedCount (profile, reviews = []) {
  const byFlag = new Map(reviews.map((r) => [r.flag_id, r]))
  return buildRedFlags(profile).filter((f) => isUnresolved(f, byFlag.get(f.id))).length
}

export function portfolioRow (ticker, profile, reviews = []) {
  if (!profile) {
    return {
      ticker, name: 'Not in coverage', covered: false,
      ffi: null, critical: null, watch: null, mscore: null, drift: null, unresolved: null
    }
  }
  const flags = buildRedFlags(profile)
  return {
    ticker,
    name: profile.name,
    covered: true,
    ffi: profile.ffi,
    critical: flags.filter((f) => f.severity === 'critical').length,
    watch: flags.filter((f) => f.severity === 'watch').length,
    mscore: profile.mscore ?? null,
    drift: profile.driftScore ?? null,
    unresolved: unresolvedCount(profile, reviews)
  }
}
