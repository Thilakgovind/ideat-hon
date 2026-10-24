import { useState } from 'react'
import { Link } from 'react-router-dom'

import { travel } from '@/assets'
import { BackButton, EmptyState, ErrorState, Icon, Loading, SampleLabel } from '@/components/kit'
import { api } from '@/lib/api'
import { clock, toMin, useAsync, useNowIST } from '@/lib/hooks'
import { useT } from '@/lib/i18n'
import { cn } from '@/lib/utils'

const STATIONS = ['Nungambakkam', 'Chetpet', 'Egmore', 'Kodambakkam', 'Mambalam', 'Guindy']

export default function Train() {
  const t = useT()
  const now = useNowIST()
  const [from, setFrom] = useState('Nungambakkam')
  const [to, setTo] = useState('Chennai Beach')
  const res = useAsync(() => api.routes({ from, to, mode: 'train', sort: 'fastest' }), [from, to, Math.floor(now.minutes / 2)])
  const opt = res.data?.options?.find((o) => o.kind === 'train')
  const leg = opt?.legs.find((l) => l.mode === 'train')
  const ladies = new Set((leg?.ladies_coaches || []).flatMap((c) => c.coach_numbers))
  const ord = (n) => `${n}${n === 1 ? 'st' : n === 2 ? 'nd' : n === 3 ? 'rd' : 'th'}`

  return (
    <div className="flex min-h-dvh flex-col bg-[#FBF8EC]">
      <div className="relative">
        <img src={travel.train} alt="Animated local train with AVAL at the ladies coach door" className="block h-[210px] w-full object-cover" />
        <BackButton className="absolute top-4 left-4" />
      </div>
      <div className="relative -mt-[26px] flex flex-1 flex-col gap-3 rounded-t-[26px] bg-[#FBF8EC] px-4 pt-4">
        <div className="flex items-end justify-between">
          <div className="flex flex-col">
            <h1 className="text-[22px] font-extrabold">{t('Local train', 'புறநகர் ரயில்')}</h1>
            <span className="font-tamil text-sm text-[#6B6450]">புறநகர் ரயில்</span>
          </div>
          <span className="text-[13px] font-bold text-train">{t('Chennai Beach line', 'சென்னை கடற்கரை வழி')}</span>
        </div>
        <div className="flex items-center gap-2 text-[13px] font-bold">
          <select aria-label={t('From', 'இருந்து')} value={from} onChange={(e) => setFrom(e.target.value)} className="h-10 flex-1 rounded-xl border-[1.5px] border-[#EDE6CC] bg-white px-2">
            {STATIONS.map((s) => <option key={s}>{s}</option>)}
          </select>
          <button type="button" aria-label={t('Swap', 'மாற்று')} onClick={() => { setFrom(to === 'Chennai Beach' || to === 'Tambaram' ? 'Nungambakkam' : to); setTo(to === 'Chennai Beach' ? 'Tambaram' : 'Chennai Beach') }}
            className="flex size-10 items-center justify-center rounded-xl border-[1.5px] border-[#EDE6CC] bg-white"><Icon.swap stroke="#2F7A55" size={18} /></button>
          <span className="flex h-10 flex-1 items-center rounded-xl border-[1.5px] border-[#EDE6CC] bg-white px-2">{t(`to ${to}`, `${to} வரை`)}</span>
        </div>

        {res.loading ? <Loading rows={3} /> : res.error ? <ErrorState error={res.error} onRetry={res.reload} />
          : !leg ? <EmptyState title={t('No train right now', 'இப்போது ரயில் இல்லை')} hint={t('The last train in the sample timetable leaves at 11:55 pm', 'கடைசி ரயில் இரவு 11:55')} />
          : (
            <>
              <div className="flex flex-col gap-2.5 rounded-[20px] border-[1.5px] border-[#EDE6CC] bg-white p-3.5">
                <span className="text-[13px] font-bold">{t('Where to stand · ladies coach', 'எங்கே நிற்பது · பெண்கள் பெட்டி')}</span>
                <div className="flex items-center gap-1" aria-hidden="true">
                  <span className="h-[30px] w-[22px] rounded-[10px_4px_4px_10px] bg-train" />
                  {Array.from({ length: leg.total_coaches }).map((_, i) => (
                    <span key={i} className={cn('flex h-[30px] flex-1 items-center justify-center rounded text-[8px] font-extrabold', ladies.has(i + 1) ? 'bg-pink text-white' : 'bg-[#E9D98A]')}>
                      {ladies.has(i + 1) ? 'LADIES' : ''}
                    </span>
                  ))}
                </div>
                <span className="text-xs text-[#6B6450]">
                  {[...ladies].map(ord).join(t(' and ', ' மற்றும் '))} {t('coach from the front', 'பெட்டி (முன்பக்கத்திலிருந்து)')} · {leg.ladies_coaches.map((c) => c.note).join('; ')}
                </span>
              </div>

              <div className="flex flex-col gap-2">
                {leg.next_detail.map((n, i) => {
                  const mins = toMin(n.time) + n.delay_min - now.minutes
                  return (
                    <div key={n.time} className={cn('flex items-center gap-3 rounded-[18px] bg-white px-3.5 py-3', i === 0 ? 'border-2 border-train' : 'border-[1.5px] border-[#EDE6CC]')}>
                      <div className="flex w-[54px] flex-col items-center"><span className="text-[22px] leading-none font-extrabold">{Math.max(0, mins)}</span><span className="text-[11px] text-[#6B6450]">min</span></div>
                      <div className="flex flex-1 flex-col">
                        <span className="text-[15px] font-bold">{clock(n.time)} · {t(`to ${leg.to}`, `${leg.to} வரை`)}{n.ladies_special ? ` · ${t('Ladies special', 'பெண்கள் சிறப்பு')}` : ''}</span>
                        <span className={cn('text-xs', n.delay_min ? 'text-[#B4540A]' : 'text-[#6B6450]')}>
                          {t(`Platform ${leg.platform}`, `நடைமேடை ${leg.platform}`)} · {n.delay_min ? t(`${n.delay_min} min late`, `${n.delay_min} நிமிடம் தாமதம்`) : t('on time', 'சரியான நேரம்')}
                        </span>
                      </div>
                    </div>
                  )
                })}
              </div>

              <div className="flex items-center gap-2.5 rounded-2xl bg-ink px-3.5 py-3 text-white">
                <Icon.warn stroke="#FFB52E" className="shrink-0" />
                <span className="text-[13px] leading-[1.4]">
                  {t(`Last train tonight leaves at ${clock(leg.last_train, true)}. AVAL will remind you 45 min before.`, `இன்றிரவு கடைசி ரயில் ${clock(leg.last_train, true)}. 45 நிமிடம் முன் நினைவூட்டுவேன்.`)}
                </span>
              </div>
            </>
          )}
        <SampleLabel className="text-[#6B6450]" />
      </div>

      <div className="grid grid-cols-2 gap-2.5 px-4 pt-2.5 pb-[22px]">
        <Link to="/circle" className="flex h-[54px] items-center justify-center rounded-2xl border-2 border-train bg-white text-[15px] font-extrabold text-train no-underline">{t('Share my train', 'என் ரயிலைப் பகிர்')}</Link>
        {opt ? (
          <Link to={`/payment?from=${encodeURIComponent(res.data.from)}&to=${encodeURIComponent(res.data.to)}&time=${res.data.time}&option=${encodeURIComponent(opt.id)}`}
            className="flex h-[54px] items-center justify-center rounded-2xl bg-train text-[15px] font-extrabold text-white no-underline">{t(`Buy ticket · ₹${opt.fare_inr}`, `டிக்கெட் · ₹${opt.fare_inr}`)}</Link>
        ) : <span className="flex h-[54px] items-center justify-center rounded-2xl bg-train/40 text-[15px] font-extrabold text-white">{t('Buy ticket', 'டிக்கெட்')}</span>}
      </div>
    </div>
  )
}
