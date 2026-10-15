import { ref } from 'vue'
import { workspaceApi } from '../api/workspace.js'
import { useToasts } from './useToasts.js'

const screens = ref([])
const state = ref('idle')

const load = async () => {
  state.value = 'loading'
  try {
    screens.value = await workspaceApi.listScreens()
    state.value = 'ready'
  } catch {
    state.value = 'error'
  }
}

const save = async (name, criteria) => {
  const { push } = useToasts()
  try {
    const screen = await workspaceApi.createScreen(name, criteria)
    screens.value = [...screens.value, screen]
    push(`Saved screen “${screen.name}”`)
    return screen
  } catch (err) {
    push(`Could not save screen: ${err.message}`, { tone: 'error' })
    return null
  }
}

const remove = async (id) => {
  const { push } = useToasts()
  const before = screens.value
  const removed = before.find((s) => s.id === id)
  screens.value = before.filter((s) => s.id !== id)
  try {
    await workspaceApi.deleteScreen(id)
    if (removed) push(`Deleted “${removed.name}”`, { action: { label: 'Undo', run: () => save(removed.name, removed.criteria) } })
  } catch (err) {
    screens.value = before
    push(`Could not delete screen: ${err.message}`, { tone: 'error' })
  }
}

export function useScreens () {
  return { screens, state, load, save, remove }
}
