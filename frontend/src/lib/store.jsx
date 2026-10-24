import { createContext, useContext, useEffect, useState } from 'react'

import { api } from '@/lib/api'

/** App-wide state: profile (no phone), active trip id. Persisted per tab only. */
const Ctx = createContext(null)

export function AppProvider({ children }) {
  const [profile, setProfile] = useState(null)
  const [tripId, setTripIdState] = useState(() => sessionStorage.getItem('sp_trip'))
  const [demo, setDemo] = useState(null)

  useEffect(() => {
    api.profile().then(setProfile).catch(() => setProfile(null))
    api.health().then(setDemo).catch(() => setDemo(null))
  }, [])

  // Forget a stored trip that the server no longer has (restart) or that has ended.
  useEffect(() => {
    if (!tripId) return
    api.trip(tripId)
      .then((r) => r.trip.status !== 'active' && setTripId(null))
      .catch((e) => e.status === 404 && setTripId(null))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tripId])

  const setTripId = (id) => {
    setTripIdState(id)
    if (id) sessionStorage.setItem('sp_trip', id)
    else sessionStorage.removeItem('sp_trip')
  }

  return <Ctx.Provider value={{ profile, tripId, setTripId, health: demo }}>{children}</Ctx.Provider>
}

export const useApp = () => useContext(Ctx)
