export function readDemo(key, fallback) {
  try { return JSON.parse(sessionStorage.getItem(`vm_${key}`)) ?? fallback } catch { return fallback }
}
export function saveDemo(key, value) {
  sessionStorage.setItem(`vm_${key}`, JSON.stringify(value))
  window.dispatchEvent(new Event('vm-demo-update'))
}
export function addDraft(kind, need, note) {
  const drafts = readDemo('requests', [])
  saveDemo('requests', [{ id: crypto.randomUUID(), kind, need, note, status: 'Draft — not submitted', created: new Date().toISOString() }, ...drafts])
}
