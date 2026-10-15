import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'

describe('ScreenerView', () => {
  beforeEach(() => {
    vi.resetModules()
    vi.stubGlobal('fetch', vi.fn(async () => ({ ok: true, status: 200, json: async () => [] })))
  })

  it('narrows results as filters change', async () => {
    const { default: ScreenerView } = await import('./ScreenerView.vue')
    const w = mount(ScreenerView)
    await flushPromises()
    const before = w.findAll('tbody tr').length
    await w.find('input[type="checkbox"]').setValue(true)
    const after = w.findAll('tbody tr').map((tr) => tr.attributes('data-row'))
    expect(after.length).toBeLessThan(before)
    expect(after).toContain('SMCI')
  })

  it('saves the current criteria under a name', async () => {
    const fetchMock = vi.fn(async (url, opts = {}) =>
      opts.method === 'POST'
        ? { ok: true, status: 201, json: async () => ({ id: 's1', ...JSON.parse(opts.body), created_at: 't' }) }
        : { ok: true, status: 200, json: async () => [] })
    vi.stubGlobal('fetch', fetchMock)
    const { default: ScreenerView } = await import('./ScreenerView.vue')
    const w = mount(ScreenerView)
    await flushPromises()
    await w.find('input[aria-label="Minimum FFI"]').setValue('50')
    await w.findAll('button').find((b) => b.text() === 'Save screen').trigger('click')
    await w.find('input[aria-label="Screen name"]').setValue('High risk')
    await w.find('input[aria-label="Screen name"]').element.form.dispatchEvent(new Event('submit'))
    await flushPromises()
    const post = fetchMock.mock.calls.find(([, o]) => o?.method === 'POST')
    expect(JSON.parse(post[1].body)).toMatchObject({ name: 'High risk', criteria: { ffi_min: 50, kind: 'all' } })
    expect(w.text()).toContain('High risk')
  })
})
