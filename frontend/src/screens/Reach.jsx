import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import { transitLegs } from '@/components/Cards'
import { AvalTip, BackButton, EmptyState, ErrorState, Loading, Pill, RouteBadge, SampleLabel } from '@/components/kit'
import { api } from '@/lib/api'
import { clock, useAsync } from '@/lib/hooks'
import { useT } from '@/lib/i18n'
import { cn } from '@/lib/utils'

const FROMS = ['Koyambedu', 'Anna Nagar West', 'Kilpauk', 'Nungambakkam', 'T. Nagar']

export default function Reach() {
  const t = useT()
  const { id } = useParams()
  const place = useAsync(() => api.place(id), [id])
  const to = place.data?.near_stop_name
  const [from, setFrom] = useState(null)
  const start = from || (to === 'Koyambedu' ? 'Anna Nagar West' : 'Koyambedu')
  const [tab, setTab] = useState('transit')
  const plan = useAsync(() => (to ? api.routes({ from: start, to, sort: 'safest' }) : Promise.resolve(null)), [start, to])
  const opts = plan.data?.options || []
  const transit = opts.filter((o) => !['walk', 'auto'].includes(o.kind))
  const walk = opts.find((o) => o.kind === 'walk')
  const auto = opts.find((o) => o.kind === 'auto')
  const list = tab === 'transit' ? transit : tab === 'walk' ? (walk ? [walk] : []) : auto ? [auto] : []
  const safest = transit.find((o) => o.badges?.includes('SAFEST'))
  const fastest = transit.find((o) => o.badges?.includes('FASTEST'))
  const link = (o) => `/steps?from=${encodeURIComponent(plan.data.from)}&to=${encodeURIComponent(plan.data.to)}&time=${plan.data.time}&option=${encodeURIComponent(o.id)}&place=${id}`

  return (
    <div className="flex min-h-dvh flex-col bg-[#F6F3F9]">
      <div className="flex flex-col gap-3 rounded-b-3xl bg-white px-4 pt-[18px] pb-3.5 shadow-[0_4px_14px_rgba(36,19,47,0.06)]">
        <div className="flex items-center gap-3">
          <BackButton className="bg-[#F6F3F9]" />
          <div className="flex min-w-0 flex-col">
            <h1 className="text-[19px] font-extrabold">{t('How to reach', 'எப்படிப் போவது')}</h1>
            <span className="truncate text-xs text-mute">
              <select aria-label={t('From', 'இருந்து')} value={start} onChange={(e) => setFrom(e.target.value)} className="bg-transparent font-bold text-plum">
                {FROMS.filter((f) => f !== to).map((f) => <option key={f}>{f}</option>)}
              </select>{' '}→ {place.data?.name || '…'}{to ? `, ${to}` : ''}
            </span>
          </div>
        </div>
        <div className="flex gap-2" role="tablist">
          {[['transit', t('Transit', 'பொது போக்குவரத்து'), safest || transit[0]], ['walk', t('Walk', 'நடை'), walk], ['auto', t('Auto', 'ஆட்டோ'), auto]].map(([k, label, o]) => (
            <button key={k} type="button" role="tab" aria-selected={tab === k} onClick={() => setTab(k)} disabled={!o}
              className={cn('h-10 rounded-xl px-3.5 text-[13px] disabled:opacity-40', tab === k ? 'bg-plum font-extrabold text-white' : 'bg-[#F6F3F9] font-bold')}>
              {label}{o ? ` ${o.total_min} min` : ''}
            </button>
          ))}
        </div>
      </div>

      <div className="flex flex-1 flex-col gap-2.5 px-4 pt-3.5 pb-5">
        {place.loading || plan.loading ? <Loading rows={3} />
          : place.error || plan.error ? <ErrorState error={place.error || plan.error} onRetry={() => { place.reload(); plan.reload() }} />
          : list.length === 0 ? <EmptyState title={t('No option in the sample timetable right now', 'இப்போது வழி இல்லை')} hint={t('Try Auto, or another start point', 'ஆட்டோ அல்லது வேறு இடம்')} />
          : list.map((o, i) => {
            const legs = o.legs
            const bars = Math.max(1, Math.min(4, Math.round((o.safety_score || 50) / 25)))
            const card = (
              <div className={cn('flex flex-col gap-2 rounded-[18px] bg-white px-3.5 py-3 text-ink', i === 0 && tab === 'transit' ? 'border-[2.5px] border-teal' : 'border-[1.5px] border-[#E6DEEE]')}>
                <div className="flex gap-1.5">
                  {o.badges?.includes('SAFEST') && <Pill className="bg-safe-bg text-teal-dark">SAFEST</Pill>}
                  {o.badges?.includes('FASTEST') && <Pill className="bg-[#FFF1D6] text-[#9A5B00]">FASTEST</Pill>}
                  {o.is_free && transitLegs(o).length > 0 && <Pill className="bg-[#FFE6EF] text-[#B32A5B]">{t('Free for women on ordinary (white-board) buses', 'சாதாரண (வெள்ளை பலகை) பஸ்ஸில் பெண்களுக்கு இலவசம்')}</Pill>}
                </div>
                <div className="flex items-baseline justify-between">
                  <span className="text-lg font-extrabold">{o.total_min} min <span className="text-[13px] font-medium text-mute">{clock(legs[0].start)} – {clock(o.reach_by)}</span></span>
                  <span className="text-base font-extrabold">{o.fare_is_estimate ? '~' : ''}₹{o.fare_inr}</span>
                </div>
                <div className="flex flex-wrap items-center gap-1.5 text-xs font-bold text-ink-2">
                  {legs.map((l, j) => (
                    <span key={j} className="flex items-center gap-1.5">
                      {j > 0 && <span>›</span>}
                      {l.mode === 'walk' ? <span>{t('Walk', 'நட')} {l.minutes} min</span> : <><RouteBadge label={l.label} mode={l.mode} size="sm" /><span>{l.minutes} min</span></>}
                    </span>
                  ))}
                </div>
                <div className="flex items-center gap-2 text-xs text-ink-2">
                  <span className="flex gap-0.5" aria-label={`Safety ${bars} of 4`}>
                    {[0, 1, 2, 3].map((b) => <span key={b} className={cn('h-1.5 w-3.5 rounded-full', b < bars ? (bars >= 3 ? 'bg-teal' : 'bg-marigold') : 'bg-[#E6DEEE]')} />)}
                  </span>
                  {(o.safety_tags || []).join(' · ') || (o.switch_info ? `${t('1 change at', 'மாற்றம்')} ${o.switch_info.at}` : '')}
                </div>
              </div>
            )
            return o.kind === 'auto' ? <div key={o.id}>{card}</div> : <Link key={o.id} to={link(o)} className="no-underline">{card}</Link>
          })}

        {tab === 'transit' && safest && fastest && safest !== fastest && (
          <AvalTip>
            {t(`At ${clock(plan.data.time, true)}, ${transitLegs(safest).map((l) => l.label).join(' + ')} is safer than ${transitLegs(fastest).map((l) => l.label).join(' + ')}: ${(safest.safety_tags || []).slice(0, 2).join(', ').toLowerCase() || 'better stops'}.`,
              `${clock(plan.data.time, true)}-க்கு ${transitLegs(safest).map((l) => l.label).join(' + ')} பாதுகாப்பானது.`)}
          </AvalTip>
        )}
        <SampleLabel />
      </div>
    </div>
  )
}
