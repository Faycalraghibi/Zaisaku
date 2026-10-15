import { ref } from 'vue'
import { workspaceApi } from '../api/workspace.js'
import { useToasts } from './useToasts.js'

const tickers = ref([])
const state = ref('idle') // idle | loading | ready | error

const load = async () => {
  state.value = 'loading'
  try {
    const rows = await workspaceApi.listWatchlist()
    tickers.value = rows.map((r) => r.ticker)
    state.value = 'ready'
  } catch {
    state.value = 'error'
  }
}

const isWatched = (ticker) => tickers.value.includes(String(ticker).toUpperCase())

const toggle = async (ticker) => {
  const { push } = useToasts()
  const t = String(ticker).toUpperCase()
  const before = tickers.value
  const removing = before.includes(t)
  tickers.value = removing ? before.filter((x) => x !== t) : [...before, t]
  try {
    if (removing) {
      await workspaceApi.removeFromWatchlist(t)
      push(`${t} removed from watchlist`, { action: { label: 'Undo', run: () => toggle(t) } })
    } else {
      await workspaceApi.addToWatchlist(t)
      push(`${t} added to watchlist`)
    }
  } catch (err) {
    tickers.value = before
    push(`Could not update watchlist: ${err.message}`, { tone: 'error' })
  }
}

export function useWatchlist () {
  return { tickers, state, load, isWatched, toggle }
}
