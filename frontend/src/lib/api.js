// Thin client for the SafePath FastAPI backend (proxied by Vite in dev).
const BASE = import.meta.env.VITE_API_BASE || ''

export class ApiError extends Error {
  constructor(message, status) {
    super(message)
    this.status = status
  }
}

async function request(path, { method = 'GET', body, form } = {}) {
  let res
  try {
    res = await fetch(BASE + path, {
      method,
      headers: body ? { 'Content-Type': 'application/json' } : undefined,
      body: body ? JSON.stringify(body) : form,
    })
  } catch {
    throw new ApiError('Cannot reach SafePath server. Is the backend running?', 0)
  }
  const data = await res.json().catch(() => ({}))
  if (!res.ok) throw new ApiError(data.detail || `Request failed (${res.status})`, res.status)
  return data
}

const qs = (params) =>
  new URLSearchParams(Object.entries(params).filter(([, v]) => v !== undefined && v !== null && v !== '')).toString()

export const api = {
  health: () => request('/health'),
  profile: () => request('/api/profile'),
  chat: (text, lang) => request('/api/aval/chat', { method: 'POST', body: { text, lang } }),
  voice: (blob, lang, hint) => {
    const form = new FormData()
    if (blob) form.append('audio', blob, 'speech.webm')
    form.append('lang', lang)
    if (hint) form.append('hint', hint)
    return request('/api/aval/voice', { method: 'POST', form })
  },
  routes: (p) => request(`/api/routes?${qs(p)}`),
  safeRoute: (p) => request(`/api/safe-route?${qs(p)}`),
  places: (p = {}) => request(`/api/places?${qs(p)}`),
  place: (id) => request(`/api/places/${encodeURIComponent(id)}`),
  tripStart: (b) => request('/api/trip/start', { method: 'POST', body: b }),
  trip: (id) => request(`/api/trip/${encodeURIComponent(id)}`),
  checkin: (b) => request('/api/trip/checkin', { method: 'POST', body: b }),
  reached: (trip_id) => request('/api/trip/reached', { method: 'POST', body: { trip_id } }),
  sos: (b = {}) => request('/api/sos', { method: 'POST', body: b }),
  circle: () => request('/api/circle'),
  circleAction: (b) => request('/api/circle', { method: 'POST', body: b }),
  payOrder: (b) => request('/api/pay/order', { method: 'POST', body: b }),
  payVerify: (b) => request('/api/pay/verify', { method: 'POST', body: b }),
  tickets: () => request('/api/tickets'),
  demoChat: (text, lang) => request('/api/demo/chat', { method: 'POST', body: { text, lang } }),
  outbox: () => request('/api/demo/outbox'),
  ticket: (id) => request(`/api/tickets/${encodeURIComponent(id)}`),
}
