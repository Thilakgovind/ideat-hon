import { useState } from 'react'
import { Link } from 'react-router-dom'

import { travel } from '@/assets'
import { BackButton, EmptyState, ErrorState, Icon, Loading, SampleLabel } from '@/components/kit'
import { api } from '@/lib/api'
import { clock, toMin, useAsync, useNowIST } from '@/lib/hooks'
import { useT } from '@/lib/i18n'
import { useApp } from '@/lib/store'

export default function Metro() {
  const t = useT()
  const now = useNowIST()
  const { profile } = useApp()
  const [from, setFrom] = useState('Koyambedu')
  const to = profile?.home_area || 'Nungambakkam'
  const res = useAsync(() => api.routes({ from, to, mode: 'metro', sort: 'fastest' }), [from, to, Math.floor(now.minutes / 2)])
  const opt = res.data?.options?.find((o) => o.kind === 'metro')
  const leg = opt?.legs.find((l) => l.mode === 'metro')
  const inMin = leg ? Math.max(0, toMin(leg.next[0]) - now.minutes) : null
  const coach = leg && /front/i.test(leg.women_coach) ? t('front coach', 'முன் பெட்டி') : leg?.women_coach

  return (
    <div className="flex min-h-dvh flex-col bg-[#F4F7FF]">
      <div className="relative">
        <img src={travel.metro} alt="Animated metro train with AVAL waving" className="block h-[210px] w-full object-cover" />
        <BackButton className="absolute top-4 left-4" />
      </div>
      <div className="relative -mt-[26px] flex flex-1 flex-col gap-3 rounded-t-[26px] bg-[#F4F7FF] px-4 pt-4">
        <div className="flex items-end justify-between">
          <div className="flex flex-col">
            <h1 className="text-[22px] font-extrabold">{t('Metro', 'மெட்ரோ')}</h1>
            <span className="font-tamil text-sm text-[#5D6A88]">மெட்ரோ</span>
          </div>
          <select aria-label={t('From station', 'நிலையம்')} value={from} onChange={(e) => setFrom(e.target.value)}
            className="h-10 rounded-xl border-[1.5px] border-[#DCE4F7] bg-white px-2 text-[13px] font-bold">
            {['Koyambedu', 'Anna Nagar Tower', 'Kilpauk', 'Vadapalani', 'Kodambakkam'].map((s) => <option key={s}>{s}</option>)}
          </select>
        </div>

        {res.loading ? <Loading rows={3} /> : res.error ? <ErrorState error={res.error} onRetry={res.reload} />
          : !leg ? <EmptyState title={t(`No metro from ${from} to ${to} right now`, 'இப்போது மெட்ரோ இல்லை')} hint={t('Metro runs 5 am – 11 pm in the sample timetable', 'மெட்ரோ காலை 5 - இரவு 11')} />
          : (
            <>
              <div className="flex items-center justify-between rounded-[22px] bg-metro px-[18px] py-4 text-white">
                <div className="flex flex-col gap-1">
                  <span className="text-xs font-bold tracking-[0.1em] uppercase opacity-80">{t(`Next train from ${leg.from}`, `${leg.from} அடுத்த ரயில்`)}</span>
                  <span className="text-[15px] font-semibold">{t(`Towards ${leg.to}`, `${leg.to} நோக்கி`)}</span>
                  <div className="mt-1 flex flex-wrap gap-1.5">
                    <span className="rounded-lg bg-white/20 px-2 py-1 text-xs font-bold">{t(`Platform ${leg.platform}`, `நடைமேடை ${leg.platform}`)}</span>
                    <span className="rounded-lg bg-pink px-2 py-1 text-xs font-bold">{t(`Women: ${coach}`, `பெண்கள்: ${coach}`)}</span>
                  </div>
                </div>
                <div className="flex flex-col items-center">
                  <span className="tabular text-5xl leading-none font-extrabold">{inMin}</span>
                  <span className="text-[13px] opacity-85">min</span>
                </div>
              </div>

              <div className="flex flex-col rounded-[22px] border-[1.5px] border-[#DCE4F7] bg-white px-4 py-3.5">
                <div className="flex min-h-11 items-center gap-3">
                  <span className="size-4 rounded-full border-4 border-metro bg-white" />
                  <span className="flex-1 text-[15px] font-extrabold">{leg.from}</span><span className="text-xs text-[#5D6A88]">{clock(leg.start)}</span>
                </div>
                <div className="flex min-h-9 items-center gap-3">
                  <span className="flex w-4 justify-center"><span className="h-9 w-1 bg-metro" /></span>
                  <span className="text-[13px] text-[#5D6A88]">{t(`${leg.stations.length - 1} stops · ${leg.minutes} min`, `${leg.stations.length - 1} நிறுத்தங்கள் · ${leg.minutes} நிமிடம்`)}{leg.stations.length > 2 ? ` · ${t('via', 'வழி')} ${leg.stations.slice(1, -1).map((s) => s.name).join(', ')}` : ''}</span>
                </div>
                <div className="flex min-h-11 items-center gap-3">
                  <span className="size-4 rounded-full bg-pink" />
                  <span className="flex-1 text-[15px] font-extrabold">{leg.to}</span><span className="text-xs text-[#5D6A88]">{clock(leg.end)}</span>
                </div>
                <div className="mt-2 flex gap-2 rounded-xl bg-[#F4F7FF] px-2.5 py-2 text-xs text-[#2E3A59]">
                  <Icon.up stroke="#1F5BDA" size={16} className="shrink-0" />{t(`Use ${leg.best_exit}`, `${leg.best_exit} பயன்படுத்துங்கள்`)}
                </div>
              </div>

              <div className="grid grid-cols-3 gap-2">
                {[[t('Fare', 'கட்டணம்'), `₹${leg.fare_inr}`, ''], [t('Then', 'அடுத்து'), leg.next[1] ? clock(leg.next[1]) : '—', ''],
                  [t('Remind me', 'நினைவூட்டு'), t('2 stops before', '2 நிறுத்தம் முன்'), 'text-sm']].map(([k, v, cls]) => (
                  <div key={k} className="flex flex-col items-center rounded-2xl border-[1.5px] border-[#DCE4F7] bg-white p-2.5">
                    <span className="text-[11px] text-[#5D6A88]">{k}</span><span className={`text-lg font-extrabold ${cls}`}>{v}</span>
                  </div>
                ))}
              </div>
            </>
          )}
        <SampleLabel className="text-[#5D6A88]" />
      </div>

      {opt && (
        <div className="px-4 pt-2.5 pb-[22px]">
          <Link to={`/payment?from=${encodeURIComponent(res.data.from)}&to=${encodeURIComponent(res.data.to)}&time=${res.data.time}&option=${encodeURIComponent(opt.id)}`}
            className="flex h-14 items-center justify-center rounded-2xl bg-metro text-[17px] font-extrabold text-white no-underline">
            {t(`Book ticket · ₹${opt.fare_inr}`, `டிக்கெட் · ₹${opt.fare_inr}`)}
          </Link>
        </div>
      )}
    </div>
  )
}
