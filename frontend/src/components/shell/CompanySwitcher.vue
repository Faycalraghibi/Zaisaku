<script setup>
import { ref, computed, nextTick, onMounted, onUnmounted } from 'vue'
import { ChevronDown, Search, Loader2 } from 'lucide-vue-next'
import { useCompany } from '../../composables/useCompany.js'
import { onShortcut } from '../../composables/useShortcuts.js'
import { companyProfiles, INDEX_TICKERS, FEATURED_TICKERS } from '../../data/companyProfiles.js'

const { currentCompany, recent, searchResults, isSearching, searchError, selectCompany, runSearch } = useCompany()

const open = ref(false)
const query = ref('')
const active = ref(0)
const root = ref(null)
const input = ref(null)

const toItem = (ticker) => ({ ticker, name: companyProfiles[ticker]?.name ?? ticker, entry: null })

const localMatches = (q) => {
  const needle = q.toLowerCase()
  return Object.values(companyProfiles)
    .filter((p) => p.ticker.toLowerCase().includes(needle) || p.name.toLowerCase().includes(needle))
    .slice(0, 8)
    .map((p) => toItem(p.ticker))
}

const groups = computed(() => {
  const q = query.value.trim()
  if (q) {
    const remote = searchResults.value.map((r) => ({ ticker: r.ticker, name: r.name, entry: r }))
    return [{ label: 'Search results', items: remote.length ? remote : localMatches(q) }]
  }
  return [
    { label: 'Recent', items: recent.value.map(toItem) },
    { label: 'Indices', items: INDEX_TICKERS.map(toItem) },
    { label: 'Companies', items: FEATURED_TICKERS.map(toItem) }
  ].filter((g) => g.items.length)
})

const flat = computed(() => groups.value.flatMap((g) => g.items))
const indexOf = (item) => flat.value.indexOf(item)

const openMenu = async () => {
  open.value = true
  query.value = ''
  active.value = 0
  await nextTick()
  input.value?.focus()
}

const close = () => { open.value = false }

const choose = (item) => {
  selectCompany(item.ticker, item.entry)
  close()
}

const onInput = () => {
  active.value = 0
  runSearch(query.value)
}

const move = (dir) => {
  const n = flat.value.length
  if (n) active.value = (active.value + dir + n) % n
}

const onEnter = () => {
  const item = flat.value[active.value]
  if (item) choose(item)
  else if (query.value.trim()) { selectCompany(query.value); close() }
}

const onDocumentPointer = (e) => {
  if (root.value && !root.value.contains(e.target)) close()
}

let offShortcut = null
onMounted(() => {
  document.addEventListener('mousedown', onDocumentPointer)
  offShortcut = onShortcut('open-switcher', openMenu)
})
onUnmounted(() => {
  document.removeEventListener('mousedown', onDocumentPointer)
  offShortcut?.()
})
</script>

<template>
  <div ref="root" class="relative">
    <button
      type="button"
      class="btn max-w-56"
      aria-haspopup="listbox"
      :aria-expanded="open"
      :aria-label="`Switch company, current ${currentCompany.ticker} ${currentCompany.name}`"
      @click="open ? close() : openMenu()"
    >
      <span class="font-mono font-semibold">{{ currentCompany.ticker }}</span>
      <span class="hidden lg:inline truncate text-muted font-normal">{{ currentCompany.name }}</span>
      <ChevronDown class="w-3 h-3 text-faint shrink-0" />
    </button>

    <div
      v-if="open"
      class="absolute top-full left-0 mt-1 z-50 w-80 rounded-md border border-line bg-panel shadow-lg"
      @keydown.esc="close"
    >
      <div class="flex items-center gap-2 h-9 px-3 border-b border-line">
        <Search class="w-3.5 h-3.5 text-faint shrink-0" />
        <input
          ref="input"
          v-model="query"
          type="text"
          role="combobox"
          aria-label="Search companies and indices"
          :aria-expanded="open"
          placeholder="Ticker or company name"
          class="flex-1 bg-transparent text-xs text-fg placeholder:text-faint outline-none"
          @input="onInput"
          @keydown.down.prevent="move(1)"
          @keydown.up.prevent="move(-1)"
          @keydown.enter.prevent="onEnter"
        />
        <Loader2 v-if="isSearching" class="w-3.5 h-3.5 text-faint animate-spin" />
      </div>

      <p v-if="searchError && query" class="px-3 pt-2 text-[11px] text-watch">{{ searchError }}</p>

      <div role="listbox" class="max-h-80 overflow-y-auto py-1">
        <template v-for="group in groups" :key="group.label">
          <div class="px-3 pt-2 pb-1 text-[10px] font-semibold uppercase tracking-[0.04em] text-faint">{{ group.label }}</div>
          <button
            v-for="item in group.items"
            :key="`${group.label}-${item.ticker}`"
            type="button"
            role="option"
            :aria-selected="indexOf(item) === active"
            class="w-full flex items-center gap-3 px-3 h-7 text-left text-xs cursor-pointer"
            :class="indexOf(item) === active ? 'bg-raised text-fg' : 'text-fg hover:bg-raised'"
            @mouseenter="active = indexOf(item)"
            @click="choose(item)"
          >
            <span class="font-mono font-semibold w-12 shrink-0">{{ item.ticker }}</span>
            <span class="truncate text-muted">{{ item.name }}</span>
          </button>
        </template>
        <p v-if="!flat.length" class="px-3 py-2 text-xs text-muted">No matches. Press Enter to open “{{ query.trim().toUpperCase() }}”.</p>
      </div>
    </div>
  </div>
</template>
