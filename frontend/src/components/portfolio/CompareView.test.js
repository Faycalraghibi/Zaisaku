import { describe, it, expect, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import CompareView from './CompareView.vue'

describe('CompareView', () => {
  beforeEach(() => window.history.replaceState(null, '', '/#compare=NVDA,SMCI'))

  it('reads tickers from the hash and highlights the worst value', () => {
    const w = mount(CompareView)
    expect(w.findAll('thead th').map((th) => th.text())).toEqual(['Metric', 'NVDA', 'SMCI'])
    const ffiRow = w.find('[data-row="ffi"]')
    expect(ffiRow.findAll('[data-worst]')).toHaveLength(1)
    expect(ffiRow.find('[data-worst]').text()).toBe(String(84))
  })

  it('keeps the hash in sync when removing a company', async () => {
    const w = mount(CompareView)
    await w.find('button[aria-label="Remove SMCI from comparison"]').trigger('click')
    expect(window.location.hash).toBe('#compare=NVDA')
    expect(w.text()).toContain('Add at least two companies to compare.')
  })
})
