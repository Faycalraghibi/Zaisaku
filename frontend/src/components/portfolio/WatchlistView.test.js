import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'

describe('WatchlistView', () => {
  beforeEach(() => vi.resetModules())

  it('lists watched companies riskiest first and flags uncovered tickers', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => ({ ok: true, status: 200, json: async () => [] })))
    const { useWatchlist } = await import('../../composables/useWatchlist.js')
    const w = useWatchlist()
    w.tickers.value = ['NVDA', 'SMCI', 'ZZZZ']
    w.state.value = 'ready'
    const { default: WatchlistView } = await import('./WatchlistView.vue')
    const wrapper = mount(WatchlistView)
    await flushPromises()
    const order = wrapper.findAll('tbody tr').map((tr) => tr.attributes('data-row'))
    expect(order).toEqual(['SMCI', 'NVDA', 'ZZZZ'])
    expect(wrapper.find('[data-row="ZZZZ"]').text()).toContain('Not in coverage')
  })

  it('opens a company on row click', async () => {
    const { useWatchlist } = await import('../../composables/useWatchlist.js')
    const w = useWatchlist()
    w.tickers.value = ['SMCI']
    w.state.value = 'ready'
    const { default: WatchlistView } = await import('./WatchlistView.vue')
    const { useCompany } = await import('../../composables/useCompany.js')
    const wrapper = mount(WatchlistView)
    await wrapper.find('[data-row="SMCI"]').trigger('click')
    expect(useCompany().currentCompany.value.ticker).toBe('SMCI')
    expect(wrapper.emitted('open-company')).toHaveLength(1)
  })
})
