import { ref } from 'vue'
import { companyProfiles, profileFromSearchEntry, fallbackProfile } from '../data/companyProfiles.js'

const RECENT_MAX = 6
const SEARCH_DEBOUNCE_MS = 180

export const pushRecent = (list, ticker, max = RECENT_MAX) =>
  [ticker, ...list.filter((t) => t !== ticker)].slice(0, max)

const currentCompany = ref(companyProfiles.NVDA)
const recent = ref(['NVDA'])
const searchResults = ref([])
const isSearching = ref(false)
const searchError = ref('')
let searchTimer = null
let searchSeq = 0

const selectCompany = (ticker, entry = null) => {
  const t = (ticker || '').toUpperCase().trim()
  if (!t) return
  // Curated profiles always win; a search row only describes companies outside coverage.
  currentCompany.value = companyProfiles[t] ?? (entry ? profileFromSearchEntry(t, entry) : fallbackProfile(t))
  recent.value = pushRecent(recent.value, t)
}

const runSearch = (query) => {
  const q = (query || '').trim()
  if (searchTimer) clearTimeout(searchTimer)
  // Results always belong to the latest query: clear now, and drop replies to superseded queries.
  const seq = ++searchSeq
  searchError.value = ''
  searchResults.value = []
  if (!q) {
    isSearching.value = false
    return
  }
  isSearching.value = true
  searchTimer = setTimeout(async () => {
    try {
      const res = await fetch(`/api/forensics/tickers/search?q=${encodeURIComponent(q)}&limit=8`)
      if (!res.ok) throw new Error('Search unavailable')
      const data = await res.json()
      if (seq === searchSeq) searchResults.value = data.results || []
    } catch {
      if (seq === searchSeq) searchError.value = 'Search unavailable. Showing local matches only.'
    } finally {
      if (seq === searchSeq) isSearching.value = false
    }
  }, SEARCH_DEBOUNCE_MS)
}

export function useCompany () {
  return { currentCompany, recent, searchResults, isSearching, searchError, selectCompany, runSearch }
}
