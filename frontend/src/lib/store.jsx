import { createContext, useCallback, useContext, useEffect, useState } from 'react'

import { api } from '@/lib/api'
import { supabase } from '@/lib/supabase'

/** App-wide state: Supabase session, her profile (masked phone only), active trip id. */
const Ctx = createContext(null)

export function AppProvider({ children }) {
  const [profile, setProfile] = useState(null)
  const [me, setMe] = useState(null)
  const [session, setSession] = useState(null)
  const [tripId, setTripIdState] = useState(() => sessionStorage.getItem('sp_trip'))
  const [demo, setDemo] = useState(null)

  const refresh = useCallback(() => {
    api.profile().then(setProfile).catch(() => setProfile(null))
    api.me().then(setMe).catch(() => setMe(null))
  }, [])

  useEffect(() => {
    api.health().then(setDemo).catch(() => setDemo(null))
    if (!supabase) { refresh(); return undefined }
    supabase.auth.getSession().then(({ data }) => { setSession(data.session); refresh() })
    const { data: sub } = supabase.auth.onAuthStateChange((event, s) => {
      setSession(s)
      if (event === 'SIGNED_IN' || event === 'SIGNED_OUT' || event === 'USER_UPDATED') refresh()
    })
    return () => sub.subscription.unsubscribe()
  }, [refresh])

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

  const signOut = async () => {
    if (supabase) await supabase.auth.signOut()
    setTripId(null)
    refresh()
  }

  return (
    <Ctx.Provider value={{ profile, me, session, signedIn: Boolean(session), refresh, signOut, tripId, setTripId, health: demo }}>
      {children}
    </Ctx.Provider>
  )
}

export const useApp = () => useContext(Ctx)
