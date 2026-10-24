import { lazy, Suspense } from 'react'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'

import { Toaster } from '@/components/ui/sonner'
import { LangProvider } from '@/lib/i18n'
import { AppProvider } from '@/lib/store'

// One chunk per screen keeps the first load small on slow 3G.
const AvalChat = lazy(() => import('@/screens/AvalChat'))
const Booking = lazy(() => import('@/screens/Booking'))
const Bus = lazy(() => import('@/screens/Bus'))
const Connect = lazy(() => import('@/screens/Connect'))
const Explore = lazy(() => import('@/screens/Explore'))
const Home = lazy(() => import('@/screens/Home'))
const LiveTrip = lazy(() => import('@/screens/LiveTrip'))
const Login = lazy(() => import('@/screens/Login'))
const Metro = lazy(() => import('@/screens/Metro'))
const Nearby = lazy(() => import('@/screens/Nearby'))
const Payment = lazy(() => import('@/screens/Payment'))
const Place = lazy(() => import('@/screens/Place'))
const Reach = lazy(() => import('@/screens/Reach'))
const Sos = lazy(() => import('@/screens/Sos'))
const Steps = lazy(() => import('@/screens/Steps'))
const Ticket = lazy(() => import('@/screens/Ticket'))
const Tickets = lazy(() => import('@/screens/Ticket').then((m) => ({ default: m.Tickets })))
const Train = lazy(() => import('@/screens/Train'))

export default function App() {
  return (
    <LangProvider>
      <AppProvider>
        <BrowserRouter>
          {/* Phone-width column; full width on real phones */}
          <div className="mx-auto min-h-dvh w-full max-w-[430px] bg-cream shadow-[0_0_40px_rgba(36,19,47,0.12)]">
            <Suspense fallback={<div className="flex min-h-dvh items-center justify-center text-sm text-mute">SafePath…</div>}>
            <Routes>
              <Route path="/" element={<Login />} />
              <Route path="/home" element={<Home />} />
              <Route path="/aval" element={<AvalChat />} />
              <Route path="/booking" element={<Booking />} />
              <Route path="/payment" element={<Payment />} />
              <Route path="/ticket/:id" element={<Ticket />} />
              <Route path="/tickets" element={<Tickets />} />
              <Route path="/bus" element={<Bus />} />
              <Route path="/metro" element={<Metro />} />
              <Route path="/train" element={<Train />} />
              <Route path="/nearby" element={<Nearby />} />
              <Route path="/circle" element={<Connect />} />
              <Route path="/trip/:id" element={<LiveTrip />} />
              <Route path="/sos" element={<Sos />} />
              <Route path="/explore" element={<Explore />} />
              <Route path="/place/:id" element={<Place />} />
              <Route path="/reach/:id" element={<Reach />} />
              <Route path="/steps" element={<Steps />} />
              <Route path="*" element={<Navigate to="/home" replace />} />
            </Routes>
            </Suspense>
          </div>
          <Toaster position="top-center" theme="light" />
        </BrowserRouter>
      </AppProvider>
    </LangProvider>
  )
}
