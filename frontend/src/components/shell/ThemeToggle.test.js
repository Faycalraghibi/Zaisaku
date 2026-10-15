import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import ThemeToggle from './ThemeToggle.vue'

describe('ThemeToggle', () => {
  it('cycles the theme mode and updates its label', async () => {
    const wrapper = mount(ThemeToggle)
    const before = wrapper.attributes('aria-label')
    await wrapper.trigger('click')
    expect(wrapper.attributes('aria-label')).not.toBe(before)
    expect(['light', 'dark']).toContain(document.documentElement.dataset.theme)
  })
})
