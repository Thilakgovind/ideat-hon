import { useCallback, useEffect, useRef, useState } from 'react'

/** Load data from an async function; re-runs when deps change. */
export function useAsync(fn, deps = []) {
  const [state, setState] = useState({ data: null, error: null, loading: true })
  const fnRef = useRef(fn)
  fnRef.current = fn
  const run = useCallback(() => {
    let alive = true
    setState((s) => ({ ...s, loading: true, error: null }))
    fnRef.current()
      .then((data) => alive && setState({ data, error: null, loading: false }))
      .catch((error) => alive && setState({ data: null, error, loading: false }))
    return () => {
      alive = false
    }
  }, [])
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(run, deps)
  return { ...state, reload: run }
}

/** Minutes since midnight in India time, refreshed every 30 s. */
export function useNowIST() {
  const get = () => {
    const d = new Date(new Date().toLocaleString('en-US', { timeZone: 'Asia/Kolkata' }))
    return { hour: d.getHours(), minutes: d.getHours() * 60 + d.getMinutes(), date: d }
  }
  const [now, setNow] = useState(get)
  useEffect(() => {
    const id = setInterval(() => setNow(get()), 30000)
    return () => clearInterval(id)
  }, [])
  return now
}

export const toMin = (hhmm) => {
  if (!hhmm) return null
  const [h, m] = hhmm.split(':').map(Number)
  return h * 60 + m
}

/** 'HH:MM' (24h) -> '8:05' / '9:40 pm' style used in the designs. */
export function clock(hhmm, withSuffix = false) {
  if (!hhmm) return ''
  const [h, m] = hhmm.split(':').map(Number)
  const h12 = h % 12 || 12
  const base = `${h12}:${String(m).padStart(2, '0')}`
  return withSuffix ? `${base} ${h < 12 ? 'am' : 'pm'}` : base
}

export const nowHHMM = () => {
  const d = new Date(new Date().toLocaleString('en-US', { timeZone: 'Asia/Kolkata' }))
  return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}
