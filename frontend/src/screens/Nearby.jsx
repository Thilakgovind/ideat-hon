import { useMemo, useState } from 'react'
import { toast } from 'sonner'

import Confirm from '@/components/Confirm'
import SafeMap from '@/components/SafeMap'
import { BackButton, ErrorState, Loading } from '@/components/kit'
import { useStartTrip } from '@/components/StartTrip'
import { api } from '@/lib/api'
import { clock, useAsync, useNowIST } from '@/lib/hooks'
import { useT } from '@/lib/i18n'
import { useApp } from '@/lib/store'
import { typeLabel } from '@/components/Cards'

// The night map is an illustration (V1 gap: real tiles later). Routes, pins, crowd and people come from the API.
const SAFE_PATH = [[120, 470], [120, 90], [360, 90]]
const QUIET_PATH = [[120, 470], [330, 470], [330, 230], [360, 90]]

function along(path, f) {
  const segs = path.slice(1).map((p, i) => [path[i], p, Math.hypot(p[0] - path[i][0], p[1] - path[i][1])])
  let d = f * segs.reduce((s, x) => s + x[2], 0)
  for (const [a, b, len] of segs) {
    if (d <= len) return [a[0] + ((b[0] - a[0]) * d) / len, a[1] + ((b[1] - a[1]) * d) / len]
    d -= len
  }
  return path[path.length - 1]
}
const pts = (p) => p.map((x) => x.join(' ')).join(' L')
const GLOW = { busy: [70, 'url(#crowd)'], moderate: [55, 'url(#crowd)'], quiet: [40, 'url(#crowdSoft)'], empty: [0, ''] }

export default function Nearby() {
  const t = useT()
  const now = useNowIST()
  const { profile } = useApp()
  const [startTrip, tripSheet] = useStartTrip()
  const [ask, setAsk] = useState(null)
  const [busy, setBusy] = useState(false)
  const home = profile?.home_area || 'Nungambakkam'
  const res = useAsync(() => api.safeRoute({ to: home }), [home, Math.floor(now.minutes / 5)])
  const walk = res.data?.walk
  const [safe, quiet] = walk?.paths || []
  const near = safe?.your_people?.[0]
  const atHome = walk?.at_destination?.[0]

  // Live MapLibre layers from the API: green safest path, dashed quiet path, open / closed shops,
  // anonymous crowd glow along each path, and your accepted circle (sample positions).
  const mapRoutes = useMemo(() => [
    quiet && { id: 'quiet', coords: quiet.polyline, color: '#8E86A0', width: 4, dashed: true },
    safe && { id: 'safe', coords: safe.polyline, color: '#2EE6A8', width: 5, glow: true },
  ].filter(Boolean), [safe, quiet])
  const mapGlows = useMemo(() => [safe, quiet].filter(Boolean).flatMap((p) => {
    const pts = []
    for (let i = 0; i < p.polyline.length - 1; i++) {
      const [a, b] = [p.polyline[i], p.polyline[i + 1]]
      for (const f of [0.15, 0.5, 0.85]) pts.push({ lat: a[0] + (b[0] - a[0]) * f, lng: a[1] + (b[1] - a[1]) * f, level: p.people_around })
    }
    return pts
  }), [safe, quiet])
  const mapPins = useMemo(() => {
    const chip = (text, color, fg = '#24132F') => {
      const el = document.createElement('div')
      el.style.cssText = `display:flex;align-items:center;gap:6px;background:rgba(18,15,25,.9);border:1.5px solid ${color};border-radius:999px;padding:3px 9px 3px 3px;color:#F4EEF8;font:700 11px Noto Sans,sans-serif;white-space:nowrap`
      el.innerHTML = `<span style="width:22px;height:22px;border-radius:11px;background:${color};color:${fg};display:flex;align-items:center;justify-content:center;font-weight:800">${text[0]}</span>${text}`
      return el
    }
    const pins = []
    if (safe?.polyline?.length) {
      const start = safe.polyline[0]
      pins.push({ id: 'you', lat: start[0], lng: start[1], color: '#FF4F8B', size: 20, label: 'You · bus stop' })
    }
    for (const s of safe?.open_shops || []) pins.push({ id: s.id, lat: s.lat, lng: s.lng, color: '#2EE6A8', label: `${s.name} (open)` })
    for (const s of [...(quiet?.closed_shops || []), ...(safe?.closed_shops || [])]) pins.push({ id: s.id, lat: s.lat, lng: s.lng, color: '#3A3448', size: 14, label: `${s.name} (closed)` })
    if (near?.lat) pins.push({ id: near.id, lat: near.lat, lng: near.lng, element: chip(`${near.label} · ${near.off_route_m} m`, '#FFB52E') })
    if (atHome?.lat) pins.push({ id: atHome.id, lat: atHome.lat, lng: atHome.lng, element: chip(`${atHome.label} · home`, '#FF4F8B', '#fff') })
    return pins
  }, [safe, quiet, near, atHome])

  async function sendAsk(confirmed) {
    setBusy(true)
    try {
      const r = await api.circleAction({ action: 'message', contact_id: near.id, kind: 'meet', where: `${safe.name} near ${res.data.to}`, confirmed })
      if (r.needs_confirmation) return setAsk(r)
      toast(r.delivery.sent ? t(`Sent to ${r.to}`, `${r.to}-க்கு அனுப்பப்பட்டது`) : t(`Demo mode: message to ${r.to} logged, not sent`, `டெமோ: ${r.to}-க்கு அனுப்பப்படவில்லை`))
      setAsk(null)
    } catch (e) {
      toast.error(e.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="relative min-h-dvh overflow-hidden bg-night text-[#F4EEF8]">
      <SafeMap theme="dark" className="absolute inset-x-0 top-0 h-[540px] w-full" routes={mapRoutes} pins={mapPins} glows={mapGlows}
        fallback={<>
      <svg viewBox="0 0 390 560" aria-hidden="true" className="absolute inset-x-0 top-0 w-full">
        <defs>
          <radialGradient id="crowd"><stop offset="0" stopColor="#FFB52E" stopOpacity=".55" /><stop offset="1" stopColor="#FFB52E" stopOpacity="0" /></radialGradient>
          <radialGradient id="crowdSoft"><stop offset="0" stopColor="#FFB52E" stopOpacity=".3" /><stop offset="1" stopColor="#FFB52E" stopOpacity="0" /></radialGradient>
        </defs>
        <rect width="390" height="560" fill="#120F19" />
        <g fill="#1A1624"><rect x="20" y="120" width="80" height="90" rx="6" /><rect x="150" y="150" width="70" height="60" rx="6" /><rect x="260" y="110" width="100" height="80" rx="6" /><rect x="230" y="260" width="60" height="110" rx="6" /><rect x="20" y="300" width="70" height="80" rx="6" /><rect x="310" y="300" width="60" height="70" rx="6" /></g>
        <g stroke="#221D2E" strokeWidth="18" strokeLinecap="round" fill="none">
          <path d="M120 470 L120 90" /><path d="M120 90 L360 90" /><path d="M120 470 L330 470" /><path d="M330 470 L330 230" /><path d="M200 470 L200 230" /><path d="M200 230 L330 230" /><path d="M330 230 L360 90" /><path d="M-10 250 L120 250" />
        </g>
        {safe && GLOW[safe.people_around][0] > 0 && [0.2, 0.55, 0.85].map((f) => {
          const [x, y] = along(SAFE_PATH, f)
          return <circle key={f} cx={x} cy={y} r={GLOW[safe.people_around][0]} fill={GLOW[safe.people_around][1]} />
        })}
        {quiet && GLOW[quiet.people_around][0] > 0 && <circle cx="330" cy="380" r={GLOW[quiet.people_around][0]} fill={GLOW[quiet.people_around][1]} />}
        <path d={`M${pts(QUIET_PATH)}`} stroke="#6E6680" strokeWidth="5" strokeDasharray="3 9" strokeLinecap="round" fill="none" />
        <path d={`M${pts(SAFE_PATH)}`} stroke="#2EE6A8" strokeWidth="14" strokeOpacity=".22" strokeLinecap="round" strokeLinejoin="round" fill="none" />
        <path d={`M${pts(SAFE_PATH)}`} stroke="#2EE6A8" strokeWidth="5" strokeLinecap="round" strokeLinejoin="round" fill="none" />
        {safe?.open_shops.map((s, i) => {
          const [x, y] = along(SAFE_PATH, (i + 1) / (safe.open_shops.length + 1))
          return <circle key={s.id} cx={x + (i % 2 ? -22 : 22)} cy={y} r="9" fill="#2EE6A8" stroke="#120F19" strokeWidth="3"><title>{s.name}</title></circle>
        })}
        {[...(quiet?.closed_shops || []), ...(safe?.closed_shops || [])].map((s, i) => {
          const [x, y] = along(QUIET_PATH, (i + 1) / 4)
          return <circle key={s.id} cx={x + 20} cy={y + 20} r="7" fill="#3A3448"><title>{s.name} (closed)</title></circle>
        })}
        <circle cx="120" cy="470" r="30" fill="#FF4F8B" opacity=".14" /><circle cx="120" cy="470" r="10" fill="#FF4F8B" stroke="#FFFFFF" strokeWidth="3" />
        <rect x="350" y="80" width="20" height="20" rx="6" fill="#FFFFFF" /><path d="M355 90 l4 4 l7 -8" stroke="#120F19" strokeWidth="2.5" fill="none" strokeLinecap="round" />
      </svg>

      <span className="absolute top-[486px] left-[92px] rounded-[10px] bg-white px-2 py-1 text-xs font-extrabold text-night">{t('You · bus stop', 'நீங்கள் · நிறுத்தம்')}</span>
      {near && (
        <div className="absolute top-[140px] left-[22px] flex items-center gap-1.5 rounded-full border-[1.5px] border-marigold bg-night/90 py-1 pr-2.5 pl-1">
          <span className="flex size-[26px] items-center justify-center rounded-full bg-marigold text-xs font-extrabold text-ink">{near.label[0]}</span>
          <span className="text-[11px] font-bold">{t(`${near.label} · ${near.off_route_m} m off route`, `${near.label} · ${near.off_route_m} மீ`)}</span>
        </div>
      )}
      {atHome && (
        <div className="absolute top-[120px] right-4 flex items-center gap-1.5 rounded-full border-[1.5px] border-pink bg-night/90 py-1 pr-2.5 pl-1">
          <span className="flex size-[26px] items-center justify-center rounded-full bg-pink text-xs font-extrabold text-white">{atHome.label[0]}</span>
          <span className="text-[11px] font-bold">{t(`${atHome.label} · at home`, `${atHome.label} · வீட்டில்`)}</span>
        </div>
      )}
      {quiet && (
        <span className="absolute top-[410px] right-4 rounded-lg bg-night/85 px-2 py-[3px] text-[11px] font-bold text-[#8E86A0]">
          {t(`${quiet.people_label} · ${quiet.shops_open ? `${quiet.shops_open} shops open` : 'shops closed'}`, `${quiet.people_label_ta} · கடைகள் மூடல்`)}
        </span>
      )}
      </>} />

      <div className="absolute top-4 right-4 left-4 flex items-center gap-2.5">
        <BackButton className="bg-[rgba(36,30,48,0.92)] [&_svg]:stroke-[#F4EEF8]" />
        <div className="flex flex-1 flex-col">
          <h1 className="text-[17px] font-extrabold">{t('Safe way home', 'பாதுகாப்பான வீட்டு வழி')}</h1>
          <span className="text-xs text-[#B9AFC8]">{clock(res.data?.time, true)} · {t('bus stop → home', 'நிறுத்தம் → வீடு')}</span>
        </div>
        <span className="flex h-8 items-center gap-1.5 rounded-full bg-[rgba(36,30,48,0.92)] px-2.5 text-xs font-bold"><span className="size-2 rounded-full bg-mint" />Live</span>
      </div>
      <div className="absolute top-[72px] left-4 flex gap-2.5 rounded-xl bg-night/85 px-2.5 py-1.5 text-[11px] font-semibold text-[#D8CFE4]">
        <span className="flex items-center gap-1"><span className="size-2.5 rounded-full bg-marigold opacity-80" />{t('People around', 'மக்கள்')}</span>
        <span className="flex items-center gap-1"><span className="size-2.5 rounded-full bg-mint" />{t('Open now', 'திறந்துள்ளது')}</span>
        <span className="flex items-center gap-1"><span className="size-2.5 rounded-full bg-[#3A3448]" />{t('Closed', 'மூடல்')}</span>
      </div>

      <div className="relative mt-[520px] flex flex-col gap-2.5 rounded-t-[28px] bg-[#F7F2FA] px-4 pt-2.5 pb-[22px] text-ink">
        <span className="h-[5px] w-10 self-center rounded-full bg-[#D6C8E2]" />
        {res.loading ? <Loading rows={2} /> : res.error ? <ErrorState error={res.error} onRetry={res.reload} />
          : !safe ? <ErrorState error={{ message: t('No walking paths for this stop yet', 'இந்த நிறுத்தத்துக்கு வழி இல்லை') }} />
          : (
            <>
              <div className="flex flex-col gap-2.5 rounded-[20px] border-[2.5px] border-teal bg-white px-3.5 py-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="h-1 w-3.5 rounded-sm bg-teal" />
                    <span className="text-base font-extrabold">{t(safe.name, safe.name_ta)}</span>
                    {safe.badge && <span className="rounded-full bg-safe-bg px-2 py-[3px] text-[11px] font-extrabold text-teal-dark">SAFEST</span>}
                  </div>
                  <span className="tabular text-sm font-extrabold">{safe.minutes} min · {safe.distance_m} m</span>
                </div>
                <div className="grid grid-cols-3 gap-2">
                  <div className="flex flex-col rounded-xl bg-[#FFF4E0] p-2"><span className="text-[11px] font-bold text-[#8A5300]">{t('People around', 'மக்கள்')}</span><span className="text-[15px] font-extrabold">{t(safe.people_label, safe.people_label_ta)}</span></div>
                  <div className="flex flex-col rounded-xl bg-safe-bg p-2"><span className="text-[11px] font-bold text-teal-dark">{t('Open at night', 'இரவில் திறந்தவை')}</span><span className="text-[15px] font-extrabold">{safe.shops_open} {t('shops', 'கடைகள்')}</span></div>
                  <div className="flex flex-col rounded-xl bg-[#FFE6EF] p-2"><span className="text-[11px] font-bold text-[#B32A5B]">{t('Your people', 'உங்கள் ஆட்கள்')}</span><span className="text-[15px] font-extrabold">{near ? t(`${near.label} near`, `${near.label} அருகில்`) : t('None near', 'யாரும் இல்லை')}</span></div>
                </div>
                <span className="text-xs text-ink-2">{safe.open_shops.map((s) => typeLabel(s.type)).join(' · ')}</span>
              </div>
              {quiet && (
                <div className="flex items-center justify-between rounded-[20px] border-[1.5px] border-line bg-white px-3.5 py-3">
                  <div className="flex flex-col gap-0.5">
                    <div className="flex items-center gap-2"><span className="h-1 w-3.5 rounded-sm bg-[#8E86A0]" /><span className="text-[15px] font-extrabold">{t(quiet.name, quiet.name_ta)}</span></div>
                    <span className="text-xs text-mute">
                      {t(quiet.people_label, quiet.people_label_ta)} · {quiet.shops_open} {t('shops open', 'கடைகள் திறந்துள்ளன')} · {quiet.your_people.length ? quiet.your_people.map((p) => p.label).join(', ') : t('no one you know', 'தெரிந்தவர் இல்லை')}
                    </span>
                  </div>
                  <span className="text-sm font-bold text-mute">{quiet.minutes} min</span>
                </div>
              )}
              <div className="grid grid-cols-2 gap-2.5">
                <button type="button" disabled={!near} onClick={() => sendAsk(false)}
                  className="h-[54px] rounded-2xl border-2 border-plum bg-white text-sm font-extrabold text-plum disabled:opacity-40">
                  {near ? t(`Ask ${near.label} to meet`, `${near.label}-ஐ சந்திக்கக் கேள்`) : t('No one nearby', 'யாரும் அருகில் இல்லை')}
                </button>
                <button type="button" onClick={() => startTrip({ from: res.data.to, to: res.data.to, time: res.data.time, option_id: `walk:${safe.id}` })}
                  className="h-[54px] rounded-2xl bg-teal text-[15px] font-extrabold text-white">
                  {t(`Walk ${safe.name.toLowerCase()}`, `${safe.name_ta} வழியாக நட`)}
                </button>
              </div>
            </>
          )}
        <span className="text-center text-[11px] text-mute">{t('Crowd shown as anonymous areas, never individuals · sample data', 'கூட்டம் அநாமதேய பகுதிகளாக மட்டும் · மாதிரி தரவு')}</span>
      </div>

      {tripSheet}
      <Confirm open={!!ask} busy={busy} onCancel={() => setAsk(null)} onConfirm={() => sendAsk(true)}
        title={t(`Send this to ${ask?.to}?`, `${ask?.to}-க்கு அனுப்பவா?`)} body={<span className="italic">“{ask?.preview}”</span>}
        confirmLabel={t('Yes, send', 'ஆம், அனுப்பு')} />
    </div>
  )
}
