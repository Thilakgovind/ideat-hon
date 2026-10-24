import { useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'

import { OptionCard, transitLegs } from '@/components/Cards'
import Confirm from '@/components/Confirm'
import { BackButton, EmptyState, ErrorState, Icon, Loading, SampleLabel, AvalTip } from '@/components/kit'
import { useStartTrip } from '@/components/StartTrip'
import { Switch } from '@/components/ui/switch'
import { api } from '@/lib/api'
import { clock, nowHHMM, useAsync } from '@/lib/hooks'
import { useT } from '@/lib/i18n'
import { useApp } from '@/lib/store'
import { cn } from '@/lib/utils'

export default function Booking() {
  const t = useT()
  const navigate = useNavigate()
  const { profile } = useApp()
  const [params, setParams] = useSearchParams()
  const from = params.get('from') || profile?.start_area || 'Anna Nagar West'
  const to = params.get('to') || profile?.home_area || 'Nungambakkam'
  const time = params.get('time') || ''
  const sort = params.get('sort') || 'safest'
  const child = params.get('child') === '1'
  const [picked, setPicked] = useState(params.get('option'))
  const [autoSheet, setAutoSheet] = useState(null)
  const [startTrip, tripSheet] = useStartTrip()

  const set = (patch) => {
    const next = new URLSearchParams(params)
    Object.entries(patch).forEach(([k, v]) => (v ? next.set(k, v) : next.delete(k)))
    setParams(next, { replace: true })
  }
  const plan = useAsync(() => api.routes({ from, to, time: time || undefined, sort, with_child: child }), [from, to, time, sort, child])
  const options = plan.data?.options || []
  const selected = options.find((o) => o.id === picked) || options[0]
  const legs = transitLegs(selected)
  const planTime = plan.data?.time

  function primary() {
    if (!selected) return
    const ref = { from: plan.data.from, to: plan.data.to, time: plan.data.time, option_id: selected.id }
    if (selected.kind === 'auto') return setAutoSheet(selected)
    if (selected.fare_inr > 0) {
      return navigate(`/payment?from=${encodeURIComponent(ref.from)}&to=${encodeURIComponent(ref.to)}&time=${ref.time}&option=${encodeURIComponent(ref.option_id)}`)
    }
    startTrip(ref)
  }

  const label = !selected ? '' : selected.kind === 'auto'
    ? t(`Book auto · ~₹${selected.fare_inr}`, `ஆட்டோ · ~₹${selected.fare_inr}`)
    : selected.fare_inr > 0 ? t(`Continue to pay · ₹${selected.fare_inr}`, `செலுத்த தொடர் · ₹${selected.fare_inr}`)
    : selected.kind === 'walk' ? t('Start walk', 'நடை தொடங்கு')
    : t(`Start free trip · ${legs.map((l) => l.label).join(' + ')}`, `இலவச பயணம் · ${legs.map((l) => l.label).join(' + ')}`)

  return (
    <div className="flex min-h-dvh flex-col bg-cream">
      <div className="flex items-center gap-3 px-4 pt-[18px] pb-2.5">
        <BackButton />
        <h1 className="text-xl font-extrabold">{t('Choose your ride', 'பயணத்தைத் தேர்ந்தெடுங்கள்')}</h1>
      </div>

      <div className="flex flex-1 flex-col gap-3 px-4 pb-4">
        <div className="flex items-center gap-3 rounded-[20px] border-[1.5px] border-line bg-white px-4 py-3.5">
          <div className="flex flex-col items-center gap-1">
            <span className="size-3 rounded-full border-[3px] border-teal" />
            <span className="h-[26px] w-0.5 bg-[repeating-linear-gradient(#C9B8D6_0_4px,transparent_4px_8px)]" />
            <span className="size-3 rounded-[3px] bg-pink" />
          </div>
          <div className="flex flex-1 flex-col gap-3.5">
            <div className="flex flex-col"><span className="text-[11px] font-semibold text-mute">{t('FROM', 'இருந்து')}</span><span className="text-base font-bold">{plan.data?.from || from}</span></div>
            <div className="flex flex-col"><span className="text-[11px] font-semibold text-mute">{t('TO', 'வரை')}</span><span className="text-base font-bold">{plan.data?.to || to}</span></div>
          </div>
          <button type="button" aria-label={t('Swap from and to', 'மாற்று')} onClick={() => { setPicked(null); set({ from: to, to: from, option: '' }) }}
            className="flex size-11 items-center justify-center rounded-[14px] border-[1.5px] border-line bg-cream">
            <Icon.swap stroke="#5B1F96" size={20} />
          </button>
        </div>

        <div className="flex items-center gap-2">
          <label className="relative flex h-9 items-center rounded-full bg-ink px-3.5 text-[13px] font-bold text-white">
            {time ? t(`Leave at · ${clock(time)}`, `புறப்பாடு · ${clock(time)}`) : t(`Leave now · ${clock(planTime || nowHHMM())}`, `இப்போது · ${clock(planTime || nowHHMM())}`)}
            <input type="time" aria-label={t('Leave time', 'புறப்படும் நேரம்')} value={time || planTime || ''} onChange={(e) => set({ time: e.target.value })}
              className="absolute inset-0 cursor-pointer opacity-0" />
          </label>
          <label className="flex h-9 items-center gap-1.5 rounded-full border-[1.5px] border-line bg-white px-3.5 text-[13px] font-semibold">
            <Switch checked={child} onCheckedChange={(v) => set({ child: v ? '1' : '' })} className="data-[state=checked]:bg-teal" aria-label={t('With child', 'குழந்தையுடன்')} />
            {t('With child', 'குழந்தையுடன்')}
          </label>
        </div>

        <div className="grid grid-cols-3 gap-1 rounded-[14px] bg-[#F0E6F6] p-1" role="tablist">
          {[['safest', t('Safest', 'பாதுகாப்பானது')], ['cheapest', t('Cheapest', 'மலிவானது')], ['fastest', t('Fastest', 'வேகமானது')]].map(([k, l]) => (
            <button key={k} type="button" role="tab" aria-selected={sort === k} onClick={() => { setPicked(null); set({ sort: k }) }}
              className={cn('h-10 rounded-[11px] text-sm', sort === k ? 'bg-white font-extrabold text-plum' : 'font-semibold text-mute')}>
              {l}
            </button>
          ))}
        </div>

        {plan.loading ? <Loading rows={3} />
          : plan.error ? <ErrorState error={plan.error} onRetry={plan.reload} />
          : plan.data?.error ? <EmptyState title={t("I couldn't find that place", 'அந்த இடம் கிடைக்கவில்லை')} hint={(plan.data.unmatched || []).join(', ')} />
          : options.length === 0 ? <EmptyState title={t('No ride in the sample timetable at this time', 'இந்த நேரத்தில் பயணம் இல்லை')} hint={t('Try another time', 'வேறு நேரம் முயற்சிக்கவும்')} />
          : (
            <div className="flex flex-col gap-3">
              {options.map((o) => <OptionCard key={o.id} opt={o} selected={o === selected} onSelect={() => setPicked(o.id)} />)}
              {plan.data.not_running_now?.length > 0 && (
                <span className="text-xs text-mute">{t(`Not running now: ${plan.data.not_running_now.join(', ')}`, `இப்போது ஓடவில்லை: ${plan.data.not_running_now.join(', ')}`)}</span>
              )}
            </div>
          )}

        {selected && (
          <AvalTip className="-mt-1">
            {tip(selected, plan.data, child, t)}
          </AvalTip>
        )}
        <SampleLabel />
      </div>

      <div className="sticky bottom-0 border-t border-line bg-cream px-4 pt-2.5 pb-[22px]">
        <button type="button" onClick={primary} disabled={!selected}
          className={cn('h-14 w-full rounded-2xl text-[17px] font-extrabold text-white disabled:opacity-50', selected?.fare_inr > 0 && selected?.kind !== 'auto' ? 'bg-pink' : 'bg-teal')}>
          {label || t('Choose a ride', 'தேர்ந்தெடுங்கள்')}
        </button>
      </div>

      {tripSheet}
      <Confirm open={!!autoSheet} title={t('Book an auto', 'ஆட்டோ பதிவு')} onClose={() => setAutoSheet(null)}
        body={t(`About ₹${autoSheet?.fare_inr} (estimate${autoSheet?.night_fare ? ', night fare' : ''}). Book in an app, then start Journey Watch so your circle can follow.`,
          `சுமார் ₹${autoSheet?.fare_inr}. செயலியில் பதிவு செய்து, பின் பயணத்தைத் தொடங்குங்கள்.`)}>
        <div className="mt-3 grid grid-cols-2 gap-2">
          {Object.entries(autoSheet?.booking_links || {}).map(([name, url]) => (
            <a key={name} href={url} target="_blank" rel="noreferrer" className="flex h-12 items-center justify-center rounded-xl border-[1.5px] border-line text-sm font-bold text-ink no-underline">{name}</a>
          ))}
        </div>
        <button type="button" onClick={() => { const o = autoSheet; setAutoSheet(null); startTrip({ from: plan.data.from, to: plan.data.to, time: plan.data.time, option_id: o.id }) }}
          className="mt-3 h-14 w-full rounded-2xl bg-teal text-base font-extrabold text-white">
          {t('Start Journey Watch', 'பயண கண்காணிப்பு தொடங்கு')}
        </button>
      </Confirm>
    </div>
  )
}

function tip(o, plan, child, t) {
  const legs = transitLegs(o)
  const name = legs.map((l) => l.label).join(' + ') || t('Walking', 'நடை')
  const when = clock(plan.time, true)
  const bits = []
  if ((o.badges || []).includes('SAFEST')) bits.push(t(`${name} is safest at ${when}.`, `${when}-க்கு ${name} பாதுகாப்பானது.`))
  else bits.push(t(`${name}: ${o.total_min} min.`, `${name}: ${o.total_min} நிமிடம்.`))
  if (o.is_free && legs.length) bits.push(t("It's free.", 'இது இலவசம்.'))
  if (o.safe_wait) bits.push(t(`Wait at ${o.safe_wait.name}.`, `${o.safe_wait.name_ta || o.safe_wait.name}-ல் காத்திருங்கள்.`))
  if (child && o.switches === 0) bits.push(t('No switches with your child.', 'குழந்தையுடன் மாற்றம் இல்லை.'))
  if (o.kind === 'auto' && o.night_fare) bits.push(t('Night fare applies.', 'இரவு கட்டணம்.'))
  return bits.join(' ')
}
