import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import OverviewDashboard from './OverviewDashboard.vue'

const company = {
  ticker: 'NVDA', name: 'NVIDIA', ffi: 18, riskTier: 'LOW_RISK',
  driftScore: 8.5, driftAdded: 4, driftRemoved: 2, driftExcerpt: 'Export controls.',
  mscore: -2.85, mscoreProb: '< 1%', tataAccrual: -0.045,
  divergenceScore: 11, radarExcerpt: 'Aligned.',
  footnotesClean: true, footnoteCount: 0, footnoteExcerpt: 'Customer A.'
}

describe('OverviewDashboard', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn(async () => ({ ok: false, json: async () => ({}) })))
  })

  it('renders red flags and routes row clicks to flag-action', async () => {
    const w = mount(OverviewDashboard, { props: { company } })
    await flushPromises()
    const flagsPanel = w.findAll('section').find((sec) => sec.find('h2').text() === 'Red flags')
    const row = flagsPanel.find('[data-row="drift"]')
    expect(row.text()).toContain('Export controls.')
    await row.trigger('click')
    expect(w.emitted('flag-action')[0]).toEqual(['diff'])
  })

  it('shows the peers error state with retry when the API fails', async () => {
    const w = mount(OverviewDashboard, { props: { company } })
    await flushPromises()
    expect(w.text()).toContain('Could not load peer benchmark')
    expect(fetch).toHaveBeenCalledWith('/api/forensics/peers/NVDA')
  })

  it('shows the filings empty state with an ingest action', async () => {
    const w = mount(OverviewDashboard, { props: { company, documents: [] } })
    await flushPromises()
    expect(w.text()).toContain('No filings ingested.')
    await w.findAll('button').find((b) => b.text() === 'Ingest from EDGAR').trigger('click')
    expect(w.emitted('open-sec')).toHaveLength(1)
  })

  it('replaces the breakdown table for macro indices', async () => {
    const w = mount(OverviewDashboard, { props: { company: { ...company, is_macro_index: true } } })
    await flushPromises()
    expect(w.text()).toContain('Constituent-weighted dispersion')
    expect(w.text()).toContain('Signals')
  })

  it('saves a status change for a flag without opening its modal', async () => {
    const fetchMock = vi.fn(async (url, opts = {}) => {
      if (opts.method === 'PUT') return { ok: true, status: 200, json: async () => ({ ticker: 'NVDA', flag_id: 'drift', status: 'escalated', note: '', updated_at: 't' }) }
      return { ok: false, status: 500, json: async () => ({}) }
    })
    vi.stubGlobal('fetch', fetchMock)
    const w = mount(OverviewDashboard, { props: { company } })
    await flushPromises()
    const flagsPanel = w.findAll('section').find((sec) => sec.find('h2').text() === 'Red flags')
    await flagsPanel.find('[data-row="drift"] select').setValue('escalated')
    await flushPromises()
    expect(fetchMock).toHaveBeenCalledWith('/api/workspace/flags/NVDA/drift', expect.objectContaining({ method: 'PUT' }))
    expect(w.emitted('flag-action')).toBeUndefined()
  })
})
