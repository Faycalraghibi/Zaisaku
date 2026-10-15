const BASE = '/api/workspace'
const enc = encodeURIComponent

async function request (path, { method = 'GET', body } = {}) {
  const res = await fetch(`${BASE}${path}`, {
    method,
    headers: body === undefined ? undefined : { 'Content-Type': 'application/json' },
    body: body === undefined ? undefined : JSON.stringify(body)
  })
  if (!res.ok) {
    let detail = ''
    try {
      const data = await res.json()
      detail = typeof data.detail === 'string' ? data.detail : ''
    } catch {
      // Non-JSON error body; fall back to the status code.
    }
    throw new Error(detail || `Workspace request failed (${res.status})`)
  }
  return res.status === 204 ? null : res.json()
}

export const workspaceApi = {
  listWatchlist: () => request('/watchlist'),
  addToWatchlist: (ticker) => request(`/watchlist/${enc(ticker)}`, { method: 'PUT' }),
  removeFromWatchlist: (ticker) => request(`/watchlist/${enc(ticker)}`, { method: 'DELETE' }),
  listScreens: () => request('/screens'),
  createScreen: (name, criteria) => request('/screens', { method: 'POST', body: { name, criteria } }),
  deleteScreen: (id) => request(`/screens/${enc(id)}`, { method: 'DELETE' }),
  listAllFlagReviews: () => request('/flags'),
  setFlagReview: (ticker, flagId, status, note) =>
    request(`/flags/${enc(ticker)}/${enc(flagId)}`, { method: 'PUT', body: { status, note } }),
  listNotes: (ticker) => request(`/notes/${enc(ticker)}`),
  addNote: (ticker, body) => request(`/notes/${enc(ticker)}`, { method: 'POST', body: { body } }),
  updateNote: (ticker, id, body) => request(`/notes/${enc(ticker)}/${enc(id)}`, { method: 'PATCH', body: { body } }),
  deleteNote: (ticker, id) => request(`/notes/${enc(ticker)}/${enc(id)}`, { method: 'DELETE' })
}
