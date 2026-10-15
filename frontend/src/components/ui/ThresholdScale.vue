<script setup>
import { computed } from 'vue'
import { scalePosition } from './scale.js'

const props = defineProps({
  value: { type: Number, default: null },
  min: { type: Number, required: true },
  max: { type: Number, required: true },
  thresholds: { type: Array, default: () => [] }, // [{ at, label }]
  label: { type: String, required: true }
})

const marker = computed(() => scalePosition(props.value, props.min, props.max))
const ticks = computed(() =>
  props.thresholds
    .map((t) => ({ ...t, pos: scalePosition(t.at, props.min, props.max) }))
    .filter((t) => t.pos !== null)
)
</script>

<template>
  <div
    role="meter"
    :aria-label="label"
    :aria-valuemin="min"
    :aria-valuemax="max"
    :aria-valuenow="value ?? undefined"
    class="pt-1 pb-4"
  >
    <div class="relative h-1.5 rounded-full bg-raised">
      <span
        v-for="t in ticks"
        :key="t.at"
        class="absolute top-1/2 -translate-y-1/2 w-px h-3 bg-faint"
        :style="{ left: `${t.pos}%` }"
      />
      <span
        v-if="marker !== null"
        data-marker
        class="absolute top-1/2 -translate-x-1/2 -translate-y-1/2 w-2.5 h-2.5 rounded-full bg-fg ring-2 ring-panel"
        :style="{ left: `${marker}%` }"
      />
      <span
        v-for="t in ticks"
        :key="`l-${t.at}`"
        class="absolute top-3 -translate-x-1/2 text-[10px] text-faint tabular-nums"
        :style="{ left: `${t.pos}%` }"
      >{{ t.label }}</span>
    </div>
  </div>
</template>
