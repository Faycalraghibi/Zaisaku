import { describe, it, expect, vi, beforeEach } from 'vitest'

const jsonResponse = (status, body) => ({ ok: status < 400, status, json: async () => body })

describe('useWatchlist', () => {
  beforeEach(() => vi.resetModules())

  it('loads tickers', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => jsonResponse(200, [{ ticker: 'NVDA', added_at: 'x' }])))
    const { useWatchlist } = await import('./useWatchlist.js')
    const w = useWatchlist()
    await w.load()
    expect(w.tickers.value).toEqual(['NVDA'])
    expect(w.state.value).toBe('ready')
  })

  it('adds optimistically and rolls back with an error toast on failure', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => jsonResponse(500, { detail: 'disk full' })))
    const { useWatchlist } = await import('./useWatchlist.js')
    const { useToasts } = await import('./useToasts.js')
    const w = useWatchlist()
    const pending = w.toggle('smci')
    expect(w.tickers.value).toEqual(['SMCI'])
    await pending
    expect(w.tickers.value).toEqual([])
    expect(useToasts().toasts.value.at(-1)).toMatchObject({ tone: 'error' })
    expect(useToasts().toasts.value.at(-1).message).toContain('disk full')
  })

  it('offers undo after removal', async () => {
    const fetchMock = vi.fn(async (url, opts) => jsonResponse(opts?.method === 'DELETE' ? 204 : 200, opts?.method === 'DELETE' ? null : { ticker: 'NVDA', added_at: 'x' }))
    vi.stubGlobal('fetch', fetchMock)
    const { useWatchlist } = await import('./useWatchlist.js')
    const { useToasts } = await import('./useToasts.js')
    const w = useWatchlist()
    w.tickers.value = ['NVDA']
    await w.toggle('NVDA')
    expect(w.tickers.value).toEqual([])
    const toast = useToasts().toasts.value.at(-1)
    expect(toast.action.label).toBe('Undo')
    await toast.action.run()
    expect(w.tickers.value).toEqual(['NVDA'])
  })
})

describe('useFlagReviews', () => {
  beforeEach(() => vi.resetModules())

  it('sets a review optimistically and keeps the server row', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => jsonResponse(200, { ticker: 'SMCI', flag_id: 'drift', status: 'reviewed', note: 'ok', updated_at: 'srv' })))
    const { useFlagReviews } = await import('./useFlagReviews.js')
    const r = useFlagReviews()
    await r.setReview('SMCI', 'drift', 'reviewed', 'ok')
    expect(r.reviewFor('SMCI', 'drift')).toMatchObject({ status: 'reviewed', updated_at: 'srv' })
  })

  it('rolls back a failed review', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => jsonResponse(500, {})))
    const { useFlagReviews } = await import('./useFlagReviews.js')
    const r = useFlagReviews()
    await r.setReview('SMCI', 'drift', 'reviewed', '')
    expect(r.reviewFor('SMCI', 'drift')).toBeNull()
  })
})
