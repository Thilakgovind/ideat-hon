import { useMemo, useState } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { Link, useNavigate } from 'react-router-dom'

import { typeLabel } from '@/components/Cards'
import { BottomNav, ErrorState, Icon, Loading } from '@/components/kit'
import { PlaceThumb } from '@/components/PlaceArt'
import SafeMap from '@/components/SafeMap'
import { api } from '@/lib/api'
import { clock, nowHHMM, useAsync } from '@/lib/hooks'
import { useT } from '@/lib/i18n'
import { cn } from '@/lib/utils'

// Map frame: the demo corridor Anna Nagar -> Nungambakkam projected onto an illustrated light map.
const BOX = { n: 13.094, s: 13.054, w: 80.188, e: 80.252 }
const CENTER = { lat: 13.074, lng: 80.221 }
const project = (lat, lng) => [20 + ((lng - BOX.w) / (BOX.e - BOX.w)) * 340, 130 + ((BOX.n - lat) / (BOX.n - BOX.s)) * 400]
const AREAS = [['ANNA NAGAR', 13.0885, 80.2006], ['KILPAUK', 13.0829, 80.2417], ['KOYAMBEDU', 13.0694, 80.1948], ['NUNGAMBAKKAM', 13.0604, 80.2422]]

export default function Explore() {
  const t = useT()
  const navigate = useNavigate()
  const [chip, setChip] = useState('open_night')
  const [q, setQ] = useState('')
  const res = useAsync(() => api.places({ ...CENTER, radius_m: 5000, chip, open_now: chip === 'open_night' ? undefined : true }), [chip])
  const places = (res.data?.places || []).filter((p) => !q || p.name.toLowerCase().includes(q.toLowerCase()))

  // group pins that would overlap into "+N" clusters
  const pins = useMemo(() => {
    const out = []
    for (const p of places) {
      const [x, y] = project(p.lat, p.lng)
      const hit = out.find((c) => Math.hypot(c.x - x, c.y - y) < 46)
      if (hit) hit.more.push(p)
      else out.push({ x, y, p, more: [] })
    }
    return out
  }, [places])

  // Live map pins: the same picture thumbnails, one per place (MapLibre clusters by zoom on its own).
  const mapPins = useMemo(() => places.slice(0, 120).map((p) => {
    const el = document.createElement('button')
    el.type = 'button'
    el.setAttribute('aria-label', `${p.name}${p.open_now ? ', open now' : ''}`)
    el.style.cssText = 'position:relative;padding:0;border:3px solid #fff;border-radius:12px;box-shadow:0 4px 10px rgba(0,0,0,.18);background:#fff;cursor:pointer;line-height:0'
    el.innerHTML = `<span style="display:block;overflow:hidden;border-radius:9px">${renderToStaticMarkup(<PlaceThumb type={p.type} size={36} />)}</span>` +
      (p.open_now ? '<span style="position:absolute;top:-8px;right:-8px;background:#0FA596;color:#fff;font:800 8px Noto Sans,sans-serif;padding:1px 3px;border-radius:5px">OPEN</span>' : '')
    return { id: p.id, lat: p.lat, lng: p.lng, element: el, onClick: () => navigate(`/place/${p.id}`) }
  }), [places, navigate])
  const fit = useMemo(() => places.slice(0, 120).map((p) => [p.lat, p.lng]), [places])

  const chips = [
    ['open_night', t('Open at night', 'இரவில் திறந்தவை')], ['women_run', t('Women-run', 'பெண்கள் நடத்துவது')],
    ['pharmacy', t('Pharmacy', 'மருந்தகம்')], ['food', t('Tea & food', 'டீ & உணவு')], ['transit', t('Bus & metro', 'பஸ் & மெட்ரோ')],
    ['help', t('Police & help', 'காவல் & உதவி')],
  ]

  return (
    <div className="relative flex min-h-dvh flex-col bg-[#EDF0F4]">
      <div className="relative h-[560px] shrink-0 overflow-hidden">
        <SafeMap theme="light" className="absolute inset-0 h-full w-full" pins={mapPins} fit={fit.length > 1 ? fit : undefined}
          fallback={<>
        <svg viewBox="0 0 390 560" aria-hidden="true" className="absolute inset-0 h-full w-full">
          <rect width="390" height="560" fill="#EDF0F4" />
          <path d="M-20 400 C60 380 110 440 190 420 C270 400 300 350 410 370 L410 412 C300 392 280 440 190 464 C100 486 60 424 -20 444Z" fill="#9CCBF2" />
          <rect x="250" y="160" width="110" height="80" rx="14" fill="#CDEBC9" />
          <g stroke="#FFFFFF" strokeWidth="14" strokeLinecap="round" fill="none"><path d="M-10 260 L400 210" /><path d="M110 30 L150 560" /><path d="M290 30 L250 560" /></g>
          <g stroke="#FFFFFF" strokeWidth="7" fill="none"><path d="M-10 340 L400 310" /><path d="M200 30 L215 560" /></g>
          <g fontFamily="Noto Sans,sans-serif" fontWeight="700" fontSize="11" fill="#7A8396" letterSpacing=".08em">
            {AREAS.map(([n, lat, lng]) => { const [x, y] = project(lat, lng); return <text key={n} x={Math.min(x, 290)} y={y + 34}>{n}</text> })}
            <text x="150" y="440" fill="#4E8FCF" fontSize="10">Cooum river</text>
          </g>
        </svg>

        {res.loading ? null : pins.map(({ x, y, p, more }) => (
          <Link key={p.id} to={`/place/${p.id}`} className="absolute flex -translate-x-1/2 -translate-y-1/2 flex-col items-center gap-0.5 text-ink no-underline" style={{ left: `${(x / 390) * 100}%`, top: y }}>
            <div className="relative rounded-[14px] border-[3px] border-white shadow-[0_4px_10px_rgba(0,0,0,0.18)]">
              <div className="overflow-hidden rounded-[11px]"><PlaceThumb type={p.type} size={48} /></div>
              {p.open_now && <span className="absolute -top-2 -right-2 rounded-md bg-teal px-1 py-px text-[9px] font-extrabold text-white">OPEN</span>}
              {more.length > 0 && <span className="absolute -top-2 -left-2.5 rounded-md bg-ink px-1.5 py-px text-[9px] font-extrabold text-white">+{more.length}</span>}
            </div>
            <span className="max-w-[120px] truncate rounded-md bg-white px-1.5 py-0.5 text-[11px] font-extrabold">{p.name.replace(/ \(.*\)$/, '')}</span>
          </Link>
        ))}
          </>} />

        <div className="absolute top-4 right-4 left-4 flex gap-2.5">
          <label htmlFor="q" className="flex h-[50px] flex-1 items-center gap-2.5 rounded-2xl bg-white px-3.5 shadow-[0_4px_14px_rgba(36,19,47,0.1)]">
            <Icon.search stroke="#6A5878" size={20} />
            <input id="q" value={q} onChange={(e) => setQ(e.target.value)} placeholder={t('Search places in Chennai', 'சென்னையில் இடங்களைத் தேடு')} className="min-w-0 flex-1 bg-transparent text-[15px] text-ink outline-none" />
          </label>
          <Link to="/nearby" aria-label={t('Safe way home', 'வீட்டுக்கு வழி')} className="flex size-[50px] items-center justify-center rounded-2xl bg-white shadow-[0_4px_14px_rgba(36,19,47,0.1)]">
            <Icon.nav stroke="#1F5BDA" />
          </Link>
        </div>
        <div className="absolute top-[76px] left-4 flex items-center gap-1.5 rounded-full bg-ink px-3 py-1.5 text-xs font-bold text-white">
          <span className="size-2 rounded-full bg-mint" />{clock(res.data?.time || nowHHMM(), true)} · {chip === 'open_night' ? t('showing places open at night', 'இரவில் திறந்த இடங்கள்') : t('showing places open now', 'இப்போது திறந்த இடங்கள்')}
        </div>
      </div>

      <div className="relative -mt-6 flex flex-1 flex-col gap-3 rounded-t-[28px] bg-white px-4 pt-2.5 pb-4 shadow-[0_-6px_20px_rgba(36,19,47,0.08)]">
        <span className="h-[5px] w-10 self-center rounded-full bg-[#E0D6EA]" />
        <span className="text-lg font-extrabold">{t('What are you looking for?', 'என்ன தேடுகிறீர்கள்?')}</span>
        <div className="flex flex-wrap gap-2" role="radiogroup">
          {chips.map(([id, label]) => (
            <button key={id} type="button" role="radio" aria-checked={chip === id} onClick={() => setChip(id)}
              className={cn('h-10 rounded-xl px-3.5 text-[13px]', chip === id ? 'bg-ink font-bold text-white' : 'bg-[#F3EEF7] font-semibold')}>
              {label}
            </button>
          ))}
        </div>
        {res.loading ? <Loading rows={1} /> : res.error ? <ErrorState error={res.error} onRetry={res.reload} /> : (
          <>
            <div className="flex items-center gap-3 rounded-2xl bg-cream px-3 py-2.5 text-ink">
              <span className="rounded-lg bg-safe-bg px-2 py-1 text-[13px] font-extrabold text-teal-dark">{places.filter((p) => p.open_now).length} {t('open', 'திறந்தவை')}</span>
              <span className="flex-1 text-[13px] text-ink-2">
                {t(`${places.filter((p) => p.women_run).length} women-run · tap a pin to see reviews`, `${places.filter((p) => p.women_run).length} பெண்கள் நடத்துவது · விமர்சனங்களுக்கு தொடவும்`)}
              </span>
            </div>
            {places.length === 0 && <span className="text-center text-sm text-mute">{t('Nothing matches. Try another filter.', 'பொருத்தம் இல்லை.')}</span>}
            <div className="flex flex-col gap-1.5">
              {places.slice(0, 4).map((p) => (
                <Link key={p.id} to={`/place/${p.id}`} className="flex items-center gap-3 rounded-xl border-[1.5px] border-line px-3 py-2 text-ink no-underline">
                  <span className="overflow-hidden rounded-lg"><PlaceThumb type={p.type} size={36} /></span>
                  <div className="flex flex-1 flex-col"><span className="text-sm font-bold">{p.name}</span><span className="text-xs text-mute">{typeLabel(p.type)} · {p.address}</span></div>
                  {p.rating && <span className="text-sm font-extrabold">★ {p.rating}</span>}
                </Link>
              ))}
            </div>
          </>
        )}
        <span className="text-center text-[11px] text-mute">{t('Sample Chennai data for demo', 'மாதிரி சென்னை தரவு')}</span>
      </div>
      <BottomNav />
    </div>
  )
}
