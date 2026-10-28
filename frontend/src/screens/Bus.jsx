import { useState } from 'react'
import { Link } from 'react-router-dom'

import { img, travel } from '@/assets'
import { isReal, useDataNote } from '@/components/Cards'
import { BackButton, EmptyState, ErrorState, Icon, Loading, SampleLabel } from '@/components/kit'
import { api } from '@/lib/api'
import { clock, useAsync, useNowIST } from '@/lib/hooks'
import { useT } from '@/lib/i18n'
import { useApp } from '@/lib/store'
import { cn } from '@/lib/utils'

const STOPS = ['Anna Nagar West', 'Nungambakkam', 'Koyambedu', 'Kilpauk', 'T. Nagar', 'Teynampet']

export default function Bus() {
  const t = useT()
  const dataNote = useDataNote()
  const now = useNowIST()
  const { profile } = useApp()
  const [stop, setStop] = useState(null)
  const [freeOnly, setFreeOnly] = useState(true)
  const [picking, setPicking] = useState(false)
  const current = stop || profile?.start_area || 'Anna Nagar West'
  const saved = [profile?.start_area, profile?.home_area].filter(Boolean)

  const arr = useAsync(() => api.routes({ from: current, free_only: freeOnly }), [current, freeOnly, Math.floor(now.minutes / 2)])
  const wait = useAsync(() => api.places({ near: current, radius_m: 300, open_now: true }), [current])
  const rows = []
  for (const a of arr.data?.arrivals || []) {
    if (!rows.find((r) => r.number === a.number && r.towards === a.towards)) rows.push(a)
  }
  const safe = wait.data?.places?.[0]

  return (
    <div className="flex min-h-dvh flex-col bg-cream">
      <div className="relative">
        <img src={travel.bus} alt="Animated free bus with AVAL waving" className="block h-[220px] w-full object-cover" />
        <BackButton className="absolute top-4 left-4" />
      </div>

      <div className="relative -mt-[26px] flex flex-1 flex-col gap-3 rounded-t-[26px] bg-cream px-4 pt-3.5 pb-5">
        <div className="flex items-end justify-between">
          <div className="flex flex-col">
            <h1 className="text-[22px] font-extrabold">{t('Free bus tracker', 'இலவச பேருந்து')}</h1>
            <span className="font-tamil text-sm text-mute">இலவச பேருந்து</span>
          </div>
          <span className="flex items-center gap-1.5 text-xs font-bold text-teal-dark">
            <span className="size-2 rounded-full bg-mint" />{t('Timetable', 'அட்டவணை')}
          </span>
        </div>

        <button type="button" onClick={() => setPicking((v) => !v)} aria-expanded={picking}
          className="flex h-[52px] items-center gap-2.5 rounded-2xl border-[1.5px] border-line bg-white px-3.5 text-ink">
          <Icon.pin stroke="#FF4F8B" size={20} />
          <span className="flex-1 text-left text-[15px] font-bold">{t(`${current} stop`, `${current} நிறுத்தம்`)}</span>
          <span className="text-[13px] font-bold text-plum">{t('Change', 'மாற்று')}</span>
        </button>
        {picking && (
          <div className="flex flex-wrap gap-2">
            {STOPS.map((s) => (
              <button key={s} type="button" onClick={() => { setStop(s); setPicking(false) }}
                className={cn('h-10 rounded-full border-[1.5px] px-3.5 text-[13px] font-semibold', s === current ? 'border-plum bg-plum text-white' : 'border-line bg-white')}>
                {s}
              </button>
            ))}
          </div>
        )}

        <div className="flex gap-2">
          <button type="button" aria-pressed={freeOnly} onClick={() => setFreeOnly(true)}
            className={cn('h-9 rounded-full px-3.5 text-[13px]', freeOnly ? 'bg-pink font-extrabold text-white' : 'border-[1.5px] border-line bg-white font-semibold')}>
            {t('Ordinary buses', 'சாதாரண பஸ்')}
          </button>
          <button type="button" aria-pressed={!freeOnly} onClick={() => setFreeOnly(false)}
            className={cn('h-9 rounded-full px-3.5 text-[13px]', !freeOnly ? 'bg-pink font-extrabold text-white' : 'border-[1.5px] border-line bg-white font-semibold')}>
            {t('All buses', 'எல்லா பஸ்')}
          </button>
          {saved.filter((s) => s !== current).slice(0, 1).map((s) => (
            <button key={s} type="button" onClick={() => setStop(s)} className="h-9 rounded-full border-[1.5px] border-line bg-white px-3.5 text-[13px] font-semibold">
              {t('Saved stop', 'சேமித்தது')}: {s.split(' ')[0]}
            </button>
          ))}
        </div>

        {arr.loading ? <Loading rows={3} /> : arr.error ? <ErrorState error={arr.error} onRetry={arr.reload} />
          : rows.length === 0 ? <EmptyState title={t('No buses due right now', 'இப்போது பஸ் இல்லை')} hint={t('No more buses in the timetable now. Try an auto or call someone you trust.', 'அட்டவணையில் இப்போது பஸ் இல்லை. ஆட்டோ அல்லது நம்பிக்கையானவரை அழைக்கவும்.')} />
          : (
            <div className="flex flex-col gap-2">
              {rows.slice(0, 4).map((a, i) => {
                const later = (arr.data.arrivals || []).find((x) => x !== a && x.number === a.number && x.towards === a.towards)
                return (
                  <Link key={`${a.number}-${a.towards}`}
                    to={`/booking?from=${encodeURIComponent(current)}&to=${encodeURIComponent(a.towards)}&time=${a.time}`}
                    className={cn('flex items-center gap-3 rounded-[18px] bg-white px-3.5 py-3 text-ink no-underline', i === 0 ? 'border-2 border-pink' : 'border-[1.5px] border-line')}>
                    <span className={cn('flex h-11 w-[54px] items-center justify-center rounded-xl text-[17px] font-extrabold text-white', a.is_free ? 'bg-pink' : 'bg-plum')}>{a.number}</span>
                    <div className="flex flex-1 flex-col">
                      <span className="text-[15px] font-bold">{t(`to ${a.towards}`, `${a.towards} வரை`)}</span>
                      <span className="text-xs text-mute">{clock(a.time)}{later ? ` · ${t('then', 'பின்')} ${clock(later.time)}` : ''} · {a.is_free ? t('Free for women on ordinary (white-board) buses', 'சாதாரண (வெள்ளை பலகை) பஸ்ஸில் பெண்களுக்கு இலவசம்') : `₹${a.fare_inr}`}</span>
                    </div>
                    <div className="flex flex-col items-end">
                      <span className={cn('text-[22px] font-extrabold', i === 0 && 'text-pink-text')}>{a.in_min}</span>
                      <span className="-mt-1 text-[11px] text-mute">min</span>
                    </div>
                  </Link>
                )
              })}
            </div>
          )}

        {safe && (
          <div className="flex items-center gap-3 rounded-[18px] bg-safe-bg px-3 py-2.5">
            <img src={img.featShops} alt="" className="h-[62px] w-12 object-contain" />
            <div className="flex flex-1 flex-col">
              <span className="text-sm font-extrabold text-[#0B5F59]">{t(`Wait safely: ${safe.name}`, `பாதுகாப்பாக காத்திருங்கள்: ${safe.name_ta || safe.name}`)}</span>
              <span className="text-xs text-[#24524E]">
                {safe.distance_m} m{safe.women_run ? ` · ${t('women-run', 'பெண்கள் நடத்துவது')}` : ''} · {safe.open_24h ? t('open 24 h', '24 மணி நேரம்') : t(`open till ${clock(safe.close, true)}`, `${clock(safe.close, true)} வரை`)}
              </span>
            </div>
            <Link to={`/place/${safe.id}`} className="px-1 py-2.5 text-[13px] font-extrabold text-[#0B5F59] no-underline">{t('Details', 'விவரம்')}</Link>
          </div>
        )}
        <SampleLabel>{dataNote(rows.some(isReal))}</SampleLabel>
      </div>
    </div>
  )
}
