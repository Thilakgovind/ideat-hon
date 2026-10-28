import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { toast } from 'sonner'

import { img } from '@/assets'
import Aval from '@/components/Aval'
import { ErrorState, Loading } from '@/components/kit'
import { Switch } from '@/components/ui/switch'
import { api } from '@/lib/api'
import { clock, useAsync, useNowIST } from '@/lib/hooks'
import { useT } from '@/lib/i18n'
import { useApp } from '@/lib/store'

export default function LiveTrip() {
  const t = useT()
  const { id } = useParams()
  const navigate = useNavigate()
  const now = useNowIST()
  const { setTripId } = useApp()
  const [tick, setTick] = useState(0)
  const [shareLoc, setShareLoc] = useState(false)
  const [done, setDone] = useState(null)
  const res = useAsync(() => api.trip(id), [id, tick])
  const trip = res.data?.trip
  const walk = useAsync(() => (trip?.kind === 'walk' ? api.safeRoute({ to: trip.to }) : Promise.resolve(null)), [trip?.kind, trip?.to])
  const path = walk.data?.walk?.paths?.find((p) => `walk:${p.id}` === trip?.option_id)

  useEffect(() => {
    const iv = setInterval(() => setTick((x) => x + 1), 15000)
    return () => clearInterval(iv)
  }, [])

  // Location only while the trip is active and only if she turns it on.
  useEffect(() => {
    if (!shareLoc || trip?.status !== 'active' || !navigator.geolocation) return
    const send = () => navigator.geolocation.getCurrentPosition(
      (p) => api.checkin({ trip_id: id, lat: p.coords.latitude, lng: p.coords.longitude }).catch(() => {}),
      () => { toast(t('Location permission denied', 'இருப்பிட அனுமதி மறுக்கப்பட்டது')); setShareLoc(false) },
      { timeout: 10000, maximumAge: 60000 },
    )
    send()
    const iv = setInterval(send, 120000)
    return () => clearInterval(iv)
  }, [shareLoc, trip?.status, id, t])

  if (res.loading && !trip) return <div className="min-h-dvh bg-[#1A1424] p-4"><Loading /></div>
  if (res.error) return <div className="min-h-dvh bg-[#1A1424] p-4"><ErrorState error={res.error} onRetry={res.reload} /></div>

  const start = new Date(trip.start).getTime()
  const eta = new Date(trip.eta).getTime()
  const progress = Math.min(1, Math.max(0, (Date.now() - start) / Math.max(1, eta - start)))
  const left = trip.distance_m ? Math.round((trip.distance_m * (1 - progress)) / 50) * 50 : null
  const nowHHMM = `${String(Math.floor(now.minutes / 60)).padStart(2, '0')}:${String(now.minutes % 60).padStart(2, '0')}`
  const leg = trip.legs.find((l) => l.start <= nowHHMM && nowHHMM < l.end && l.mode !== 'walk') || trip.legs.find((l) => l.mode !== 'walk') || trip.legs[0]
  const watchers = trip.watchers || []
  const near = path?.your_people?.[0]
  const overdue = trip.status === 'active' && Date.now() > eta

  async function reached() {
    try {
      const r = await api.reached(id)
      setTripId(null)
      setDone(r)
    } catch (e) {
      toast.error(e.message)
    }
  }
  async function imOkay() {
    await api.checkin({ trip_id: id, ok: true }).catch(() => {})
    toast(t('Check-in sent', 'செக்-இன் அனுப்பப்பட்டது'))
  }

  if (done) {
    const d = done.delivery
    return (
      <div className="flex min-h-dvh flex-col items-center justify-center gap-3 bg-cream px-6 text-center">
        <Aval pose="cheer" className="h-56 w-44" label="AVAL cheering" />
        <h1 className="text-[26px] font-extrabold">{t('You reached safely!', 'பாதுகாப்பாக சேர்ந்தீர்கள்!')}</h1>
        <p className="text-sm text-mute">
          {d.sent ? t(`Your circle was told (${d.sent}).`, `உங்கள் வட்டத்துக்கு தெரிவிக்கப்பட்டது (${d.sent}).`)
            : d.demo_logged ? t('Demo mode: "reached" message logged, not sent by SMS.', 'டெமோ: செய்தி அனுப்பப்படவில்லை.')
            : t('Journey Watch is off. Location sharing stopped.', 'பயண கண்காணிப்பு நிறுத்தப்பட்டது.')}
        </p>
        <button type="button" onClick={() => navigate('/home')} className="sp-btn-safe w-full">{t('Back to home', 'முகப்புக்கு')}</button>
      </div>
    )
  }

  return (
    <div className="relative min-h-dvh overflow-hidden bg-[#1A1424] text-white">
      <svg viewBox="0 0 390 844" preserveAspectRatio="xMidYMin slice" aria-hidden="true" className="absolute inset-0 h-full w-full">
        <defs>
          <linearGradient id="dusk" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#2B1C44" /><stop offset=".45" stopColor="#6B2F6E" /><stop offset=".62" stopColor="#E77B7B" /></linearGradient>
          <linearGradient id="lane" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#2EE6A8" stopOpacity="0" /><stop offset="1" stopColor="#2EE6A8" stopOpacity=".75" /></linearGradient>
        </defs>
        <rect width="390" height="844" fill="url(#dusk)" />
        <g fill="#22182F"><rect x="0" y="250" width="60" height="220" /><rect x="58" y="300" width="44" height="170" /><rect x="290" y="230" width="64" height="240" /><rect x="350" y="290" width="40" height="180" /><rect x="230" y="330" width="44" height="140" /><rect x="120" y="350" width="36" height="120" /></g>
        <g fill="#FFD27A" opacity=".7"><rect x="12" y="280" width="8" height="8" /><rect x="30" y="310" width="8" height="8" /><rect x="304" y="260" width="8" height="8" /><rect x="326" y="300" width="8" height="8" /><rect x="300" y="350" width="8" height="8" /><rect x="70" y="330" width="8" height="8" /></g>
        <path d="M150 470 L240 470 L420 844 L-30 844 Z" fill="#2A2232" />
        <path d="M190 470 L200 470 L230 844 L160 844 Z" fill="url(#lane)" />
        <g stroke="#FFFFFF" strokeOpacity=".6" strokeWidth="4" strokeDasharray="24 30"><path d="M168 470 L60 844" /><path d="M222 470 L330 844" /></g>
        <g fill="#2EE6A8"><path d="M195 560 l-16 18 l16 -6 l16 6 z" opacity=".55" /><path d="M195 620 l-24 26 l24 -9 l24 9 z" opacity=".75" /><path d="M195 700 l-34 38 l34 -13 l34 13 z" /></g>
      </svg>

      <div className="absolute top-4 right-4 left-4 flex flex-col gap-2.5">
        <div className="flex items-center justify-between">
          <h1 className="text-lg font-extrabold">{trip.status === 'active' ? t('On your trip', 'பயணத்தில்') : trip.status === 'alerted' ? t('Circle alerted', 'வட்டம் எச்சரிக்கப்பட்டது') : t('Trip', 'பயணம்')}</h1>
          <Link to="/home" className="flex h-9 items-center rounded-full bg-mint px-3.5 text-[13px] font-extrabold text-night-2 no-underline">{t('Minimise', 'சிறிதாக்கு')}</Link>
        </div>
        <div className="flex items-center gap-3 rounded-[20px] border border-white/10 bg-[rgba(26,20,36,0.82)] p-3.5">
          <span className={`flex size-12 shrink-0 items-center justify-center rounded-[14px] text-base font-extrabold ${leg.mode === 'metro' ? 'bg-metro' : leg.mode === 'train' ? 'bg-train' : 'bg-pink'}`}>
            {leg.mode === 'walk' ? t('Walk', 'நட') : leg.label}
          </span>
          <div className="flex min-w-0 flex-1 flex-col">
            <span className="text-xs opacity-75">
              {path ? `${t(path.name, path.name_ta)} · ${t(path.people_label.toLowerCase(), path.people_label_ta)}${path.well_lit ? t(' and lit', ', வெளிச்சம்') : ''}` : `${trip.from} → ${trip.to}`}
            </span>
            <span className="text-[17px] leading-tight font-extrabold">
              {trip.next_open_shop ? t(`Next open shop: ${trip.next_open_shop.name}`, `அடுத்த திறந்த கடை: ${trip.next_open_shop.name}`) : trip.summary}
            </span>
          </div>
          <img src={img.avalFaceSmile} alt="AVAL" className="size-11 rounded-full bg-lilac" />
        </div>
        {(watchers.length > 0 || near) && (
          <div className="flex items-center gap-2 self-start rounded-full bg-[rgba(26,20,36,0.82)] py-1.5 pr-3 pl-1.5">
            <span className="flex size-[26px] items-center justify-center rounded-full bg-pink text-xs font-extrabold">{(near || watchers[0]).label[0]}</span>
            <span className="text-xs font-bold">
              {[near && t(`${near.label} is ${near.off_route_m} m away`, `${near.label} ${near.off_route_m} மீ தொலைவில்`),
                trip.notified_circle && watchers[0] && t(`${watchers[0].label} watching`, `${watchers[0].label} பார்க்கிறார்`),
                !trip.notified_circle && t('Circle not told (you chose not to share)', 'வட்டத்துக்கு தெரிவிக்கவில்லை')].filter(Boolean).join(' · ')}
            </span>
          </div>
        )}
        {overdue && (
          <div role="alert" className="flex items-center justify-between gap-2 rounded-2xl bg-marigold px-3.5 py-2.5 text-ink">
            <span className="text-sm font-bold">{t('Past your ETA. Are you safe?', 'நேரம் கடந்தது. நலமா?')}</span>
            <button type="button" onClick={imOkay} className="h-10 rounded-xl bg-ink px-3 text-sm font-extrabold text-white">{t("I'm okay", 'நலம்')}</button>
          </div>
        )}
      </div>

      <div className="absolute top-[360px] right-2 flex flex-col items-center">
        <span className="mb-1 rounded-xl bg-white px-2.5 py-1.5 text-xs font-extrabold text-ink">{t('Straight on', 'நேராக செல்லுங்கள்')}</span>
        <Aval pose="guide" className="h-[108px] w-[82px]" label="AVAL pointing the way" />
      </div>

      <div className="absolute inset-x-0 bottom-0 flex flex-col gap-3 rounded-t-[28px] bg-[#F7F2FA] px-4 pt-2.5 pb-[22px] text-ink">
        <span className="h-[5px] w-10 self-center rounded-full bg-[#D6C8E2]" />
        <div className="grid grid-cols-3 text-center">
          <div className="flex flex-col"><span className="text-xs text-mute">{t('Distance left', 'மீதமுள்ள தூரம்')}</span><span className="tabular text-lg font-extrabold">{left == null ? '—' : left >= 1000 ? `${(left / 1000).toFixed(1)} km` : `${left} m`}</span></div>
          <div className="flex flex-col border-x border-line"><span className="text-xs text-mute">{t('Reach by', 'சேரும் நேரம்')}</span><span className="tabular text-lg font-extrabold">{clock(trip.eta_hhmm)}</span></div>
          <div className="flex flex-col"><span className="text-xs text-mute">{t('Check-in', 'செக்-இன்')}</span><span className="text-lg font-extrabold text-teal-dark">{trip.status === 'active' ? t('On', 'ஆன்') : t('Off', 'ஆஃப்')}</span></div>
        </div>
        <div className="h-2 overflow-hidden rounded bg-line" role="progressbar" aria-valuenow={Math.round(progress * 100)} aria-valuemin={0} aria-valuemax={100}>
          <div className="h-2 bg-[linear-gradient(90deg,#0FA596,#2EE6A8)]" style={{ width: `${Math.round(progress * 100)}%` }} />
        </div>
        <label className="flex items-center justify-between text-[13px] font-semibold">
          {t('Share my live location with my circle', 'என் இருப்பிடத்தை வட்டத்துடன் பகிர்')}
          <Switch checked={shareLoc} onCheckedChange={setShareLoc} disabled={trip.status !== 'active'} className="data-[state=checked]:bg-teal" />
        </label>
        <div className="grid grid-cols-[1fr_76px] gap-2.5">
          <button type="button" onClick={reached} disabled={trip.status === 'reached'} className="sp-btn-safe">
            {t("I've reached", 'சேர்ந்துவிட்டேன்')}
          </button>
          <Link to={`/sos?trip=${id}`} aria-label="SOS" className="flex h-14 items-center justify-center rounded-2xl bg-sos text-base font-black text-white no-underline">SOS</Link>
        </div>
      </div>
    </div>
  )
}
