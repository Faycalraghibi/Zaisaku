// @vitest-environment node
import { describe, it, expect } from 'vitest'
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { companyProfiles } from './companyProfiles.js'

// The backend peer benchmark keeps its own fixture copy of some companies.
// A company must never show one score in the risk panel and another in the peers table.
const PEERS_PY = fileURLToPath(new URL('../../../backend/src/zaisaku/forensics/peers.py', import.meta.url))

const parsePeerMetrics = (source) =>
  [...source.matchAll(/PeerMetric\(\s*\n([\s\S]*?)\n\s*\)/g)].map(([, body]) => {
    const text = (key) => body.match(new RegExp(String.raw`\b${key}="([^"]*)"`))?.[1]
    const num = (key) => Number(body.match(new RegExp(String.raw`\b${key}=(-?[\d.]+)`))?.[1])
    return { ticker: text('ticker'), ffi: num('ffi'), drift: num('drift_pct'), mscore: num('beneish_mscore') }
  })

describe('backend peer fixtures', () => {
  const peers = parsePeerMetrics(readFileSync(PEERS_PY, 'utf8'))

  it('are parsed', () => {
    expect(peers.length).toBeGreaterThan(10)
    expect(peers.every((p) => p.ticker && Number.isFinite(p.ffi))).toBe(true)
  })

  it('match the frontend profiles for every shared ticker', () => {
    const mismatches = peers
      .filter((p) => companyProfiles[p.ticker])
      .filter((p) => {
        const f = companyProfiles[p.ticker]
        return f.ffi !== p.ffi || f.driftScore !== p.drift || f.mscore !== p.mscore
      })
      .map((p) => {
        const f = companyProfiles[p.ticker]
        return `${p.ticker}: backend ffi=${p.ffi} drift=${p.drift} m=${p.mscore} vs frontend ffi=${f.ffi} drift=${f.driftScore} m=${f.mscore}`
      })
    expect(mismatches).toEqual([])
  })
})
