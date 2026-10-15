import { reactive } from 'vue'
import { workspaceApi } from '../api/workspace.js'
import { useToasts } from './useToasts.js'

// ticker -> { state: 'loading'|'ready'|'error', items: Note[] (newest first) }
const byTicker = reactive({})

const entry = (ticker) => {
  if (!byTicker[ticker]) byTicker[ticker] = { state: 'idle', items: [] }
  return byTicker[ticker]
}

const load = async (ticker) => {
  const e = entry(ticker)
  e.state = 'loading'
  try {
    e.items = await workspaceApi.listNotes(ticker)
    e.state = 'ready'
  } catch {
    e.state = 'error'
  }
}

const notesFor = (ticker) => byTicker[ticker]?.items ?? []
const stateFor = (ticker) => byTicker[ticker]?.state ?? 'idle'

const add = async (ticker, body) => {
  try {
    const note = await workspaceApi.addNote(ticker, body)
    const e = entry(ticker)
    e.items = [note, ...e.items]
    return true
  } catch (err) {
    useToasts().push(`Could not save note: ${err.message}`, { tone: 'error' })
    return false
  }
}

const update = async (ticker, id, body) => {
  const e = entry(ticker)
  const before = e.items
  e.items = before.map((n) => (n.id === id ? { ...n, body } : n))
  try {
    const saved = await workspaceApi.updateNote(ticker, id, body)
    e.items = e.items.map((n) => (n.id === id ? saved : n))
    return true
  } catch (err) {
    e.items = before
    useToasts().push(`Could not update note: ${err.message}`, { tone: 'error' })
    return false
  }
}

const remove = async (ticker, id) => {
  const e = entry(ticker)
  const before = e.items
  const removed = before.find((n) => n.id === id)
  e.items = before.filter((n) => n.id !== id)
  try {
    await workspaceApi.deleteNote(ticker, id)
    if (removed) {
      // Undo re-creates the note (new id and timestamp; same text).
      useToasts().push('Note deleted', { action: { label: 'Undo', run: () => add(ticker, removed.body) } })
    }
  } catch (err) {
    e.items = before
    useToasts().push(`Could not delete note: ${err.message}`, { tone: 'error' })
  }
}

export function useNotes () {
  return { load, notesFor, stateFor, add, update, remove }
}
