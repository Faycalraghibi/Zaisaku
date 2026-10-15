import { ref } from 'vue'
import { workspaceApi } from '../api/workspace.js'
import { useToasts } from './useToasts.js'

const reviews = ref([])
const state = ref('idle')

const load = async () => {
  state.value = 'loading'
  try {
    reviews.value = await workspaceApi.listAllFlagReviews()
    state.value = 'ready'
  } catch {
    state.value = 'error'
  }
}

const reviewFor = (ticker, flagId) =>
  reviews.value.find((r) => r.ticker === ticker && r.flag_id === flagId) ?? null

const reviewsFor = (ticker) => reviews.value.filter((r) => r.ticker === ticker)

const upsertLocal = (list, row) => [
  ...list.filter((r) => !(r.ticker === row.ticker && r.flag_id === row.flag_id)),
  row
]

const setReview = async (ticker, flagId, status, note = '') => {
  const before = reviews.value
  reviews.value = upsertLocal(before, { ticker, flag_id: flagId, status, note, updated_at: new Date().toISOString() })
  try {
    const saved = await workspaceApi.setFlagReview(ticker, flagId, status, note)
    reviews.value = upsertLocal(reviews.value, saved)
    return true
  } catch (err) {
    reviews.value = before
    useToasts().push(`Could not save review: ${err.message}`, { tone: 'error' })
    return false
  }
}

export function useFlagReviews () {
  return { reviews, state, load, reviewFor, reviewsFor, setReview }
}
