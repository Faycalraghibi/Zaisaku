<script setup>
import { computed } from 'vue'
import { Wrench, Star } from 'lucide-vue-next'
import SeverityDot from '../ui/SeverityDot.vue'
import MenuButton from '../ui/MenuButton.vue'
import { ffiTier, ffiSeverity } from '../../utils/ffi.js'

const props = defineProps({
  company: { type: Object, required: true },
  watched: { type: Boolean, default: false },
  unresolved: { type: Number, default: 0 }
})

const emit = defineEmits(['tool', 'toggle-watch', 'show-flags'])

const toolItems = [
  { id: 'run-audit', label: 'Run audit' },
  { id: 'auditor-qa', label: 'Auditor Q&A' },
  { id: 'scorecard', label: 'Scorecard' },
  { id: 'sandbox', label: 'Prompt sandbox' }
]

const meta = computed(() => {
  const c = props.company
  return [
    c.exchange,
    c.cik && !/^0+$/.test(c.cik) ? `CIK ${c.cik}` : null,
    c.sector,
    c.period,
    c.auditor
  ].filter(Boolean)
})

const tier = computed(() => ffiTier(props.company.ffi))
const severity = computed(() => ffiSeverity(props.company.ffi))
</script>

<template>
  <div class="flex flex-wrap items-center gap-x-4 gap-y-1 min-h-9 px-3 py-1.5 border-b border-line bg-bg shrink-0">
    <div class="flex items-baseline gap-2 min-w-0">
      <h1 class="text-sm font-semibold text-fg truncate">{{ company.name }}</h1>
      <span class="font-mono text-xs text-muted">{{ company.ticker }}</span>
    </div>
    <ul class="flex flex-wrap items-center gap-x-3 gap-y-0.5 text-xs text-muted min-w-0">
      <li v-for="item in meta" :key="item" class="truncate max-w-64" :class="item.startsWith('CIK') ? 'font-mono' : ''">{{ item }}</li>
    </ul>
    <div class="flex items-center gap-2 ml-auto">
      <button v-if="unresolved" type="button" class="btn text-watch" @click="emit('show-flags')">
        {{ unresolved }} unresolved {{ unresolved === 1 ? 'flag' : 'flags' }}
      </button>
      <button
        type="button"
        class="btn-icon"
        :aria-pressed="watched"
        :aria-label="watched ? `Remove ${company.ticker} from watchlist` : `Add ${company.ticker} to watchlist`"
        :title="watched ? 'On watchlist' : 'Add to watchlist'"
        @click="emit('toggle-watch')"
      >
        <Star class="w-3.5 h-3.5" :class="watched ? 'fill-current text-watch' : ''" />
      </button>
      <span class="inline-flex items-center gap-1.5 h-7 px-2.5 rounded border border-line bg-panel text-xs">
        <SeverityDot :level="severity" />
        <span class="text-muted">Risk</span>
        <span class="font-semibold text-fg tabular-nums">{{ company.ffi }}</span>
        <span class="text-muted">{{ tier.label }}</span>
      </span>
      <MenuButton label="Tools" :items="toolItems" @select="(id) => emit('tool', id)">
        <template #icon><Wrench class="w-3.5 h-3.5 text-muted" /></template>
      </MenuButton>
    </div>
  </div>
</template>
