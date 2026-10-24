import { useEffect, useRef, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { toast } from 'sonner'

import Aval from '@/components/Aval'
import { BackButton } from '@/components/kit'
import { typeLabel } from '@/components/Cards'
import { api } from '@/lib/api'
import { useAsync } from '@/lib/hooks'
import { useT } from '@/lib/i18n'

const HOLD_MS = 2000

function position() {
  return new Promise((resolve) => {
    if (!navigator.geolocation) return resolve(null)
    navigator.geolocation.getCurrentPosition(
      (p) => resolve({ lat: p.coords.latitude, lng: p.coords.longitude }),
      () => resolve(null),
      { timeout: 3000, maximumAge: 60000 },
    )
  })
}

export default function Sos() {
  const t = useT()
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const tripId = params.get('trip')
  const [holding, setHolding] = useState(0)
  const [result, setResult] = useState(null)
  const [sending, setSending] = useState(false)
  const timer = useRef(null)
  const circle = useAsync(() => api.circle(), [])
  const help = useAsync(async () => {
    const trip = tripId ? await api.trip(tripId).catch(() => null) : null
    return api.places({ type: 'police_booth,shg_kiosk,pharmacy,hospital', open_now: true, radius_m: 1500, near: trip?.trip?.to })
  }, [tripId])
  const names = (circle.data?.contacts || []).filter((c) => c.accepted).map((c) => c.label)

  useEffect(() => () => clearInterval(timer.current), [])

  function down() {
    if (result || sending) return
    const t0 = Date.now()
    clearInterval(timer.current)
    timer.current = setInterval(() => {
      const p = Math.min(1, (Date.now() - t0) / HOLD_MS)
      setHolding(p)
      if (p >= 1) {
        clearInterval(timer.current)
        fire()
      }
    }, 50)
  }
  function up() {
    clearInterval(timer.current)
    if (!sending && !result) setHolding(0)
  }

  // SOS needs no confirmation: alert circle, show helplines, share location until stopped.
  async function fire() {
    setSending(true)
    try {
      const loc = await position()
      const r = await api.sos({ trip_id: tripId || undefined, ...(loc || {}) })
      setResult(r)
    } catch (e) {
      toast.error(e.message)
      setHolding(0)
    } finally {
      setSending(false)
    }
  }

  async function safeNow() {
    if (result) await api.sos({ action: 'stop' }).catch(() => {})
    navigate('/home')
  }

  const d = result?.delivery
  const nearest = result?.nearest_help || (help.data?.places || []).slice(0, 2)

  return (
    <div className="flex min-h-dvh flex-col bg-[#FFF4F4]">
      <div className="flex items-center justify-between px-4 pt-[18px]">
        <BackButton icon="close" />
        <span className="rounded-full bg-[#FFE1E4] px-3 py-1.5 text-[13px] font-bold text-[#B3122A]">
          {result ? (result.sos.location ? t('SOS active · sharing location', 'SOS செயலில் · இருப்பிடம் பகிர்வு') : t('SOS active', 'SOS செயலில்')) : t('Silent mode on', 'அமைதி முறை')}
        </span>
      </div>

      <div className="relative z-10 flex flex-col items-center gap-1.5 px-5 pt-2 text-center">
        <h1 className="text-2xl font-extrabold">{result ? t('Help is on the way', 'உதவி வருகிறது') : t('Need help?', 'உதவி தேவையா?')}</h1>
        <span className="font-tamil text-[15px] text-mute">{result ? 'உதவி வருகிறது' : 'உதவி தேவையா?'}</span>
      </div>

      <div className="flex justify-center pt-[22px] pb-3">
        <button
          type="button"
          aria-label={t('Hold for 2 seconds to send SOS', 'SOS அனுப்ப 2 விநாடி அழுத்தவும்')}
          onPointerDown={down}
          onPointerUp={up}
          onPointerLeave={up}
          onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && !e.repeat && down()}
          onKeyUp={up}
          onContextMenu={(e) => e.preventDefault()}
          className="sos-hold relative flex size-[220px] touch-none flex-col items-center justify-center gap-1 rounded-full bg-[radial-gradient(circle_at_50%_40%,#FF4A5F,#D11A33)] text-white shadow-[0_0_0_18px_#FFE1E4,0_0_0_36px_#FFF0F1] select-none"
        >
          {(holding > 0 || result) && <svg className="absolute inset-0" viewBox="0 0 220 220" aria-hidden="true">
            <circle cx="110" cy="110" r="104" fill="none" stroke="#FFFFFF" strokeWidth="6" strokeOpacity=".9"
              strokeDasharray={`${653 * (result ? 1 : holding)} 653`} transform="rotate(-90 110 110)" strokeLinecap="round" />
          </svg>}
          <span className="text-5xl font-black tracking-[0.04em]">SOS</span>
          <span className="text-sm font-bold opacity-95">
            {sending ? t('Sending…', 'அனுப்புகிறது…') : result ? t('Sent', 'அனுப்பப்பட்டது') : holding > 0 ? t('Keep holding…', 'அழுத்திக்கொண்டே இருங்கள்…') : t('Hold 2 seconds', '2 விநாடி அழுத்தவும்')}
          </span>
        </button>
      </div>

      <div className="relative z-10 flex flex-1 flex-col gap-2.5 px-4 pt-[18px]">
        {result ? (
          <div role="status" className="flex flex-col gap-2 rounded-[18px] border-[1.5px] border-[#F5D3D8] bg-white p-3.5">
            <span className="text-[13px] font-extrabold tracking-[0.06em] text-mute">{t('WHAT AVAL DID', 'அவள் செய்தது')}</span>
            {(result.circle_delivery || []).map((c) => (
              <div key={c.contact_id} className="flex items-center gap-2 text-sm">
                <span className={`flex size-[22px] items-center justify-center rounded-full text-xs font-extrabold ${c.status === 'sent' ? 'bg-teal text-white' : 'bg-[#FFE1E4] text-[#B3122A]'}`}>{c.status === 'sent' ? '✓' : '!'}</span>
                {c.label}: {c.status === 'sent' ? t('SMS sent', 'SMS அனுப்பப்பட்டது') : c.status === 'mock_logged' ? t('demo — logged, not sent', 'டெமோ — அனுப்பப்படவில்லை') : t('could not send — call 181', 'அனுப்ப முடியவில்லை — 181 அழைக்கவும்')}
              </div>
            ))}
            <div className="flex items-center gap-2 text-sm">
              <span className="flex size-[22px] items-center justify-center rounded-full bg-teal text-xs font-extrabold text-white">✓</span>
              {result.sos.location ? t('Sharing your location until you stop it', 'நிறுத்தும் வரை இருப்பிடம் பகிரப்படும்') : t('Location not available — your last trip stop is shared', 'இருப்பிடம் கிடைக்கவில்லை')}
            </div>
            {d && !d.any_real_alert && (
              <span className="text-xs font-bold text-[#B3122A]">{t('No real SMS went out (demo mode). Call 181 or 100 now.', 'உண்மையான SMS அனுப்பப்படவில்லை. 181 அல்லது 100 அழைக்கவும்.')}</span>
            )}
          </div>
        ) : (
          <div className="flex flex-col gap-2 rounded-[18px] border-[1.5px] border-[#F5D3D8] bg-white p-3.5">
            <span className="text-[13px] font-extrabold tracking-[0.06em] text-mute">{t('WHEN YOU HOLD, AVAL WILL', 'அழுத்தினால், அவள்')}</span>
            {[t(`Alert ${names.length ? names.slice(0, -1).join(', ') + (names.length > 1 ? ' and ' : '') + names[names.length - 1] : 'your circle'} by SMS`, `${names.join(', ') || 'வட்டத்துக்கு'} SMS எச்சரிக்கை`),
              t('Share your live location until you stop it', 'நிறுத்தும் வரை இருப்பிடம் பகிர்வு'),
              t('Show the nearest open shop and police booth', 'அருகிலுள்ள திறந்த கடை, காவல் பூத் காட்டும்')].map((s, i) => (
              <div key={i} className="flex items-center gap-2 text-sm">
                <span className="flex size-[22px] shrink-0 items-center justify-center rounded-full bg-[#FFE1E4] text-xs font-extrabold text-[#B3122A]">{i + 1}</span>{s}
              </div>
            ))}
          </div>
        )}

        <div className="grid grid-cols-2 gap-2.5">
          {[['181', t('Women helpline', 'பெண்கள் உதவி எண்')], ['100', t('Police', 'காவல்')]].map(([n, label]) => (
            <a key={n} href={`tel:${n}`} className="flex flex-col gap-0.5 rounded-[18px] border-[1.5px] border-[#F5D3D8] bg-white p-3 text-ink no-underline">
              <span className="text-xs text-mute">{label}</span><span className="text-[28px] font-black text-[#B3122A]">{n}</span>
            </a>
          ))}
        </div>

        <div className="flex items-center gap-2.5 rounded-[18px] bg-safe-bg px-3 py-2.5">
          <Aval pose="face" state="alert" className="size-11 shrink-0" label="AVAL, serious" />
          <span className="flex-1 text-[13px] leading-[1.4] text-[#24524E]">
            {nearest.length ? `${t('Nearest help', 'அருகிலுள்ள உதவி')}: ${nearest.map((p) => `${p.name || typeLabel(p.type)} ${p.distance_m} m`).join(' · ')}` : t('Finding help nearby…', 'அருகில் உதவி தேடுகிறது…')}
          </span>
        </div>
      </div>

      <div className="px-4 pt-3 pb-[22px]">
        <button type="button" onClick={safeNow} className="h-[54px] w-full rounded-2xl border-2 border-teal bg-white text-base font-extrabold text-teal-dark">
          {t("I'm safe now", 'நான் பாதுகாப்பாக இருக்கிறேன்')}
        </button>
      </div>
    </div>
  )
}
