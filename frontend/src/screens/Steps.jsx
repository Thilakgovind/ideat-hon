import { useSearchParams } from 'react-router-dom'

import { transitLegs } from '@/components/Cards'
import { BackButton, EmptyState, ErrorState, Icon, Loading, Pill, RouteBadge } from '@/components/kit'
import { useStartTrip } from '@/components/StartTrip'
import { api } from '@/lib/api'
import { clock, useAsync } from '@/lib/hooks'
import { useT } from '@/lib/i18n'

const COLOR = { walk: '#5B1F96', bus: '#FF4F8B', metro: '#1F5BDA', train: '#2F7A55', auto: '#FFC21C' }
// Illustrated route shape on the light map; each leg takes a share of it by minutes.
const SHAPE = [[110, 380], [120, 330], [110, 150], [250, 130], [268, 92]]

function split(legs) {
  const segs = SHAPE.slice(1).map((p, i) => [SHAPE[i], p, Math.hypot(p[0] - SHAPE[i][0], p[1] - SHAPE[i][1])])
  const total = segs.reduce((s, x) => s + x[2], 0)
  const mins = legs.reduce((s, l) => s + l.minutes, 0) || 1
  const at = (d) => {
    for (const [a, b, len] of segs) {
      if (d <= len) return [a[0] + ((b[0] - a[0]) * d) / len, a[1] + ((b[1] - a[1]) * d) / len]
      d -= len
    }
    return SHAPE[SHAPE.length - 1]
  }
  let d = 0
  return legs.map((l) => {
    const from = d
    d += (l.minutes / mins) * total
    const pts = [at(from)]
    let acc = 0
    for (const [, b, len] of segs) { acc += len; if (acc > from && acc < d) pts.push(b) }
    pts.push(at(d))
    return { leg: l, pts }
  })
}

export default function Steps() {
  const t = useT()
  const [params] = useSearchParams()
  const [startTrip, tripSheet] = useStartTrip()
  const ref = { from: params.get('from'), to: params.get('to'), time: params.get('time'), option: params.get('option') }
  const plan = useAsync(() => api.routes({ from: ref.from, to: ref.to, time: ref.time }), [ref.from, ref.to, ref.time])
  const place = useAsync(() => (params.get('place') ? api.place(params.get('place')) : Promise.resolve(null)), [params.get('place')])
  const opt = plan.data?.options?.find((o) => o.id === ref.option)
  const legs = opt?.legs || []
  const parts = opt ? split(legs) : []
  const dest = place.data?.name || plan.data?.to

  const stepText = (l, i) => {
    const nextT = legs[i + 1]
    if (l.mode === 'walk') {
      return i === legs.length - 1
        ? [t(`Walk to ${dest}`, `${dest} வரை நடக்கவும்`), `${l.minutes} min${place.data?.night_safety?.tags?.length ? ` · ${place.data.night_safety.tags.slice(0, 2).join(', ').toLowerCase()}` : ''}`]
        : [t(`Walk to ${nextT?.from || 'the stop'}`, `${nextT?.from || 'நிறுத்தம்'} வரை நடக்கவும்`), `${l.minutes} min${opt.switch_info && nextT?.mode === 'metro' ? ` · ${opt.switch_info.lit ? t('lit walkway', 'வெளிச்சம்') : ''}` : ''}`]
    }
    if (l.mode === 'auto') return [t('Auto, door to door', 'ஆட்டோ'), t(`~₹${l.fare_inr} · estimate`, `~₹${l.fare_inr}`)]
    const stops = l.stops ? l.stops.length - 1 : l.stations ? l.stations.length - 1 : null
    const name = l.mode === 'bus' ? `${t('Bus', 'பஸ்')} ${l.label}` : l.label
    return [`${name} · ${l.is_free ? 'FREE' : `₹${l.fare_inr}`}`,
      [t(`Arrives ${clock(l.start)}`, `${clock(l.start)} வருகை`), stops ? t(`${stops} stops`, `${stops} நிறுத்தங்கள்`) : null,
        l.mode === 'bus' ? t('sit near the driver', 'ஓட்டுநர் அருகே அமருங்கள்') : l.women_coach ? t(`women: ${l.women_coach.toLowerCase()}`, 'பெண்கள் பெட்டி') : null,
        t(`get off at ${l.to}`, `${l.to}-ல் இறங்கவும்`)].filter(Boolean).join(' · ')]
  }

  return (
    <div className="relative flex min-h-dvh flex-col bg-[#EDF0F4]">
      <svg viewBox="0 0 390 420" aria-hidden="true" className="block w-full">
        <rect width="390" height="420" fill="#EDF0F4" />
        <path d="M-20 250 C80 230 140 290 220 270 C300 250 330 210 410 220 L410 256 C330 248 300 290 220 310 C140 330 80 270 -20 290Z" fill="#9CCBF2" />
        <rect x="240" y="60" width="110" height="70" rx="14" fill="#CDEBC9" />
        <g stroke="#FFFFFF" strokeWidth="14" strokeLinecap="round" fill="none"><path d="M-10 150 L400 120" /><path d="M90 -10 L130 430" /><path d="M290 -10 L260 430" /><path d="M-10 380 L400 360" /></g>
        {parts.map(({ leg, pts }, i) => (
          <path key={i} d={`M${pts.map((p) => p.join(' ')).join(' L')}`} stroke={COLOR[leg.mode]} strokeWidth={leg.mode === 'walk' ? 5 : 7}
            strokeDasharray={leg.mode === 'walk' ? '1 8' : undefined} strokeLinecap="round" strokeLinejoin="round" fill="none" />
        ))}
        {parts.slice(1).map(({ pts }, i) => <circle key={i} cx={pts[0][0]} cy={pts[0][1]} r="7" fill="#FFFFFF" stroke="#FF4F8B" strokeWidth="3" />)}
        <circle cx="110" cy="380" r="9" fill="#5B1F96" stroke="#FFFFFF" strokeWidth="3" />
        <rect x="250" y="52" width="46" height="46" rx="14" fill="#FFB52E" stroke="#FFFFFF" strokeWidth="3" />
        <path d="M257 76 L273 64 L289 76Z" fill="#FF4F8B" /><rect x="261" y="76" width="24" height="14" fill="#FFFFFF" /><rect x="269" y="80" width="8" height="10" fill="#5B1F96" />
      </svg>
      <div className="absolute top-4 left-4"><BackButton className="shadow-[0_4px_12px_rgba(36,19,47,0.12)]" /></div>

      <div className="relative -mt-14 flex flex-1 flex-col gap-3 rounded-t-[28px] bg-white px-4 pt-2.5 pb-5 shadow-[0_-6px_20px_rgba(36,19,47,0.08)]">
        <span className="h-[5px] w-10 self-center rounded-full bg-[#E0D6EA]" />
        {plan.loading ? <Loading rows={3} /> : plan.error ? <ErrorState error={plan.error} onRetry={plan.reload} />
          : !opt ? <EmptyState title={t('This option is no longer running', 'இந்த வழி இப்போது இல்லை')} hint={t('Go back and pick another', 'திரும்பி வேறொன்றைத் தேர்ந்தெடுங்கள்')} />
          : (
            <>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-xl font-extrabold">{opt.total_min} min</span>
                  {transitLegs(opt).map((l, i) => <RouteBadge key={i} label={l.label} mode={l.mode} size="sm" />)}
                  {opt.badges?.includes('SAFEST') && <Pill className="bg-safe-bg text-teal-dark">SAFEST</Pill>}
                </div>
                <span className="text-[15px] font-extrabold">{opt.fare_is_estimate ? '~' : ''}₹{opt.fare_inr}</span>
              </div>
              <span className="text-[15px] font-extrabold">{t('Steps', 'படிகள்')}</span>
              <ol className="flex flex-col">
                {legs.map((l, i) => {
                  const [title, sub] = stepText(l, i)
                  const last = i === legs.length - 1
                  return (
                    <li key={i} className="flex gap-3">
                      <div className="flex w-5 flex-col items-center">
                        <span className={`size-3.5 ${last ? 'rounded' : 'rounded-full'}`} style={{ background: last ? '#0FA596' : COLOR[l.mode] }} />
                        {!last && <span className="w-[3px] flex-1" style={l.mode === 'walk' ? { background: 'repeating-linear-gradient(#C9B8D6 0 4px, transparent 4px 8px)' } : { background: COLOR[l.mode], width: 4 }} />}
                      </div>
                      <div className={`flex flex-1 justify-between gap-2 ${last ? '' : 'pb-3.5'}`}>
                        <div className="flex flex-col"><span className="text-sm font-extrabold">{title}</span><span className="text-xs text-mute">{sub}</span></div>
                        <span className="text-xs font-bold">{clock(l.start)}</span>
                      </div>
                    </li>
                  )
                })}
              </ol>
              <button type="button" onClick={() => startTrip({ from: plan.data.from, to: plan.data.to, time: plan.data.time, option_id: opt.id })}
                className="mt-auto flex h-14 items-center justify-center gap-2 rounded-2xl bg-mint text-[17px] font-extrabold text-night-2">
                <Icon.nav stroke="#14111B" size={20} width={2.4} />{t('Start navigation', 'வழிகாட்டல் தொடங்கு')}
              </button>
              <span className="text-center text-[11px] text-mute">{t('Opens the green-line live view · circle gets your ETA if you say yes · sample data', 'நேரலை பார்வை · ஒப்புதலுடன் வட்டத்துக்கு நேரம் · மாதிரி தரவு')}</span>
            </>
          )}
      </div>
      {tripSheet}
    </div>
  )
}
