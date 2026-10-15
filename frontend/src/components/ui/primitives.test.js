import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import Panel from './Panel.vue'
import DataTable from './DataTable.vue'
import SeverityDot from './SeverityDot.vue'
import ThresholdScale from './ThresholdScale.vue'
import MenuButton from './MenuButton.vue'

describe('Panel', () => {
  it('renders slot content when ready', () => {
    const w = mount(Panel, { props: { title: 'Peers' }, slots: { default: '<p class="body">ok</p>' } })
    expect(w.find('h2').text()).toBe('Peers')
    expect(w.find('.body').exists()).toBe(true)
  })
  it('shows skeleton when loading', () => {
    const w = mount(Panel, { props: { title: 'x', state: 'loading' }, slots: { default: '<p class="body">ok</p>' } })
    expect(w.find('[data-state="loading"]').exists()).toBe(true)
    expect(w.find('.body').exists()).toBe(false)
  })
  it('shows empty text', () => {
    const w = mount(Panel, { props: { title: 'x', state: 'empty', emptyText: 'No filings' } })
    expect(w.find('[data-state="empty"]').text()).toContain('No filings')
  })
  it('emits retry from the error state', async () => {
    const w = mount(Panel, { props: { title: 'x', state: 'error', errorText: 'Boom' } })
    expect(w.find('[role="alert"]').text()).toContain('Boom')
    await w.find('button').trigger('click')
    expect(w.emitted('retry')).toHaveLength(1)
  })
})

describe('DataTable', () => {
  const columns = [
    { key: 'ticker', label: 'Ticker', sortable: true },
    { key: 'ffi', label: 'FFI', align: 'right', sortable: true, format: (v) => v.toFixed(1) }
  ]
  const rows = [
    { ticker: 'NVDA', ffi: 18 },
    { ticker: 'AMD', ffi: 34 },
    { ticker: 'SMCI', ffi: 84 }
  ]
  const tickers = (w) => w.findAll('tbody tr').map((tr) => tr.attributes('data-row'))

  it('formats cells', () => {
    const w = mount(DataTable, { props: { columns, rows, rowKey: 'ticker' } })
    expect(w.find('tbody tr td:last-child').text()).toBe('18.0')
  })
  it('sorts on header click and toggles direction', async () => {
    const w = mount(DataTable, { props: { columns, rows, rowKey: 'ticker' } })
    await w.findAll('thead button')[1].trigger('click')
    expect(tickers(w)).toEqual(['NVDA', 'AMD', 'SMCI'])
    await w.findAll('thead button')[1].trigger('click')
    expect(tickers(w)).toEqual(['SMCI', 'AMD', 'NVDA'])
    expect(w.findAll('th')[1].attributes('aria-sort')).toBe('descending')
  })
  it('emits row-click only when clickable', async () => {
    const plain = mount(DataTable, { props: { columns, rows, rowKey: 'ticker' } })
    await plain.find('tbody tr').trigger('click')
    expect(plain.emitted('row-click')).toBeUndefined()

    const w = mount(DataTable, { props: { columns, rows, rowKey: 'ticker', clickable: true } })
    await w.find('tbody tr').trigger('click')
    expect(w.emitted('row-click')[0][0]).toEqual(rows[0])
  })
  it('highlights the matching row', () => {
    const w = mount(DataTable, { props: { columns, rows, rowKey: 'ticker', highlight: 'AMD' } })
    expect(w.find('[data-row="AMD"]').classes()).toContain('bg-accent-soft')
  })
})

describe('SeverityDot', () => {
  it('labels severity for assistive tech', () => {
    const w = mount(SeverityDot, { props: { level: 'critical', withLabel: true } })
    expect(w.find('[role="img"]').attributes('aria-label')).toBe('Severity: Critical')
    expect(w.text()).toContain('Critical')
  })
})

describe('ThresholdScale', () => {
  it('positions the marker and exposes meter values', () => {
    const w = mount(ThresholdScale, { props: { value: -2, min: -4, max: 0, label: 'M-Score', thresholds: [{ at: -1.78, label: '-1.78' }] } })
    expect(w.find('[data-marker]').attributes('style')).toContain('left: 50%')
    expect(w.find('[role="meter"]').attributes('aria-valuenow')).toBe('-2')
  })
  it('omits the marker without a value', () => {
    const w = mount(ThresholdScale, { props: { value: null, min: -4, max: 0, label: 'M-Score' } })
    expect(w.find('[data-marker]').exists()).toBe(false)
  })
})

describe('MenuButton', () => {
  it('opens, selects, and closes', async () => {
    const w = mount(MenuButton, { props: { label: 'Memo', items: [{ id: 'preview', label: 'Preview memo' }] } })
    expect(w.find('[role="menu"]').exists()).toBe(false)
    await w.find('button').trigger('click')
    await w.find('[role="menuitem"]').trigger('click')
    expect(w.emitted('select')[0]).toEqual(['preview'])
    expect(w.find('[role="menu"]').exists()).toBe(false)
  })
})
