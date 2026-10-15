<script setup>
import { computed } from 'vue'
import { Monitor, Sun, Moon } from 'lucide-vue-next'
import { useTheme } from '../../composables/useTheme.js'

const { mode, cycle } = useTheme()

const icon = computed(() => ({ system: Monitor, light: Sun, dark: Moon })[mode.value])
const label = computed(() => `Theme: ${mode.value}. Click to change.`)
</script>

<template>
  <button type="button" class="btn-icon" :title="label" :aria-label="label" @click="cycle">
    <component :is="icon" class="w-3.5 h-3.5" />
  </button>
</template>
