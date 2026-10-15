<script setup>
import { ref, computed } from 'vue'
import { ChevronUp, ChevronDown } from 'lucide-vue-next'
import { sortRows } from './sortRows.js'

const props = defineProps({
  // [{ key, label, align: 'left'|'right', sortable, format: (value, row) => string, width }]
  columns: { type: Array, required: true },
  rows: { type: Array, default: () => [] },
  rowKey: { type: String, required: true },
  highlight: { type: [String, Number], default: null },
  clickable: { type: Boolean, default: false },
  initialSort: { type: Object, default: null } // { key, dir }
})

const emit = defineEmits(['row-click'])

const sortKey = ref(props.initialSort?.key ?? null)
const sortDir = ref(props.initialSort?.dir ?? 'asc')

const sorted = computed(() => sortRows(props.rows, sortKey.value, sortDir.value))

const toggleSort = (col) => {
  if (!col.sortable) return
  if (sortKey.value === col.key) {
    sortDir.value = sortDir.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortKey.value = col.key
    sortDir.value = 'asc'
  }
}

const ariaSort = (col) => {
  if (!col.sortable) return undefined
  if (sortKey.value !== col.key) return 'none'
  return sortDir.value === 'asc' ? 'ascending' : 'descending'
}

const display = (col, row) => (col.format ? col.format(row[col.key], row) : row[col.key])

const onRowClick = (row) => {
  if (props.clickable) emit('row-click', row)
}
</script>

<template>
  <table class="w-full text-xs border-collapse">
    <thead>
      <tr>
        <th
          v-for="col in columns"
          :key="col.key"
          scope="col"
          :aria-sort="ariaSort(col)"
          :style="col.width ? { width: col.width } : null"
          class="h-7 px-3 font-medium text-muted border-b border-line whitespace-nowrap"
          :class="col.align === 'right' ? 'text-right' : 'text-left'"
        >
          <button
            v-if="col.sortable"
            type="button"
            class="inline-flex items-center gap-0.5 hover:text-fg cursor-pointer"
            @click="toggleSort(col)"
          >
            {{ col.label }}
            <ChevronUp v-if="sortKey === col.key && sortDir === 'asc'" class="w-3 h-3" />
            <ChevronDown v-else-if="sortKey === col.key" class="w-3 h-3" />
          </button>
          <template v-else>{{ col.label }}</template>
        </th>
      </tr>
    </thead>
    <tbody>
      <tr
        v-for="row in sorted"
        :key="row[rowKey]"
        :data-row="row[rowKey]"
        class="border-b border-line last:border-b-0"
        :class="[
          clickable ? 'cursor-pointer hover:bg-raised' : '',
          highlight !== null && row[rowKey] === highlight ? 'bg-accent-soft' : ''
        ]"
        :tabindex="clickable ? 0 : undefined"
        @click="onRowClick(row)"
        @keydown.enter="onRowClick(row)"
      >
        <td
          v-for="col in columns"
          :key="col.key"
          class="h-7 px-3 py-1 text-fg align-middle"
          :class="col.align === 'right' ? 'text-right whitespace-nowrap tabular-nums' : 'text-left'"
        >
          <slot :name="`cell-${col.key}`" :row="row" :value="row[col.key]">{{ display(col, row) }}</slot>
        </td>
      </tr>
    </tbody>
  </table>
</template>
