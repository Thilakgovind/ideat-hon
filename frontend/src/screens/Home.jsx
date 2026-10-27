import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { img, travel } from '@/assets'
import { AVATAR_COLORS, Avatar, BottomNav, Icon, SosFab } from '@/components/kit'
import { api } from '@/lib/api'
import { useAsync, useNowIST, clock } from '@/lib/hooks'
import { greeting, useT } from '@/lib/i18n'
import { useApp } from '@/lib/store'

export default function Home() {
  const t = useT()
  const navigate = useNavigate()
  const { profile, tripId } = useApp()
  const now = useNowIST()
  const [q, setQ] = useState('')
  const start = profile?.start_area || 'Anna Nagar West'
  const home = profile?.home_area || 'Nungambakkam'
  const [en, ta] = greeting(now.hour)

  const bus = useAsync(() => api.routes({ from: start, free_only: true }), [start, Math.floor(now.minutes / 5)])
  const circle = useAsync(() => api.circle(), [])
  const accepted = (circle.data?.contacts || []).filter((c) => c.accepted)
  const towardsHome = (bus.data?.arrivals || []).filter((a) => a.towards === home)
  const next = towardsHome[0] || bus.data?.arrivals?.[0]
  const then = (bus.data?.arrivals || []).find((a) => a !== next && a.number === next?.number)

  return (
    <div className="relative flex min-h-dvh flex-col bg-cream">
      <div className="flex flex-1 flex-col gap-3 px-[18px] pt-[18px] pb-4">
        <div className="flex items-center justify-between">
          <div className="flex flex-col gap-0.5">
            <span className="text-sm text-mute">{en} · <span className="font-tamil">{ta}</span></span>
            <span className="text-[26px] font-extrabold">{profile?.display_name || '…'}</span>
          </div>
          <Link to="/aval" aria-label="Ask AVAL" className="flex size-[52px] items-center justify-center rounded-full bg-lilac shadow-[0_0_0_3px_#FFFFFF,0_0_0_5px_#FF4F8B]">
            <img src={img.avalFaceSmile} alt="" className="size-[46px]" />
          </Link>
        </div>

        {tripId && (
          <Link to={`/trip/${tripId}`} className="flex items-center gap-2 rounded-2xl bg-mint px-3.5 py-2.5 text-sm font-extrabold text-night-2 no-underline">
            <span className="size-2 rounded-full bg-night-2" /> {t('Trip in progress — open live view', 'பயணம் நடக்கிறது — நேரலை')}
          </Link>
        )}

        <form className="flex items-center gap-2.5" onSubmit={(e) => { e.preventDefault(); if (q.trim()) navigate(`/aval?q=${encodeURIComponent(q.trim())}`) }}>
          <label htmlFor="where" className="flex h-14 min-w-0 flex-1 items-center gap-2.5 rounded-[18px] border-2 border-line bg-white px-4">
            <Icon.search stroke="#6A5878" size={20} />
            <input id="where" value={q} onChange={(e) => setQ(e.target.value)} placeholder="Where to? · எங்கே?"
              className="min-w-0 flex-1 bg-transparent text-base text-ink outline-none" />
          </label>
          <Link to="/aval?mic=1" aria-label="Speak to AVAL" className="flex size-14 items-center justify-center rounded-[18px] bg-plum">
            <Icon.mic stroke="#FFFFFF" size={24} />
          </Link>
        </form>

        <div className="no-scrollbar flex gap-2 overflow-x-auto">
          {(profile?.saved_places || []).map((p) => (
            <Link key={p.id} to={`/booking?from=${encodeURIComponent(start)}&to=${encodeURIComponent(p.to)}`}
              className="flex h-10 shrink-0 items-center rounded-full border-[1.5px] border-line bg-white px-3.5 text-sm font-semibold text-ink no-underline">
              {t(p.label, p.label_ta)}
            </Link>
          ))}
        </div>

        <Link to="/bus" className="flex items-center gap-3 rounded-[18px] bg-ink px-3.5 py-3 text-white no-underline">
          <span className="live-dot size-2.5 shrink-0 rounded-full bg-mint" />
          <div className="flex flex-1 flex-col">
            {bus.loading ? <span className="text-[15px] font-bold">{t('Checking free buses…', 'இலவச பஸ் பார்க்கிறது…')}</span>
              : bus.error ? <span className="text-[15px] font-bold">{t('Bus times unavailable', 'பஸ் நேரம் இல்லை')}</span>
              : next ? <>
                <span className="text-[15px] font-bold">{t(`Free bus ${next.number} in ${next.in_min} min`, `இலவச பஸ் ${next.number} · ${next.in_min} நிமிடம்`)}</span>
                <span className="text-xs opacity-75">{start}{then ? ` · then ${clock(then.time)}` : ''}</span>
              </> : <>
                <span className="text-[15px] font-bold">{t('No free bus right now', 'இப்போது இலவச பஸ் இல்லை')}</span>
                <span className="text-xs opacity-75">{t('Buses have stopped for tonight · try auto', 'இன்றிரவு பஸ் இல்லை')}</span>
              </>}
          </div>
          {next && <span className="rounded-full bg-pink px-2 py-1 text-[11px] font-extrabold">FREE</span>}
        </Link>

        <div className="flex items-baseline justify-between">
          <span className="text-lg font-extrabold">{t('How do you want to go?', 'எப்படிப் போக வேண்டும்?')}</span>
          <Link to="/explore" className="text-[13px] font-bold text-plum no-underline">{t('Find a place ›', 'இடம் தேடு ›')}</Link>
        </div>
        <div className="grid grid-cols-2 gap-2.5">
          {[
            ['/bus', travel.bus, t('Bus', 'பஸ்'), t('Free', 'இலவசம்'), 'text-pink-text', 'Animated free bus'],
            ['/metro', travel.metro, t('Metro', 'மெட்ரோ'), t('from ₹10', '₹10 முதல்'), 'text-mute', 'Animated metro'],
            ['/train', travel.train, t('Train', 'ரயில்'), t('Ladies coach', 'பெண்கள் பெட்டி'), 'text-mute', 'Animated local train'],
            [`/booking?from=${encodeURIComponent(start)}&to=${encodeURIComponent(home)}&sort=fastest`, travel.auto, t('Auto', 'ஆட்டோ'), t('Last mile', 'கடைசி தூரம்'), 'text-mute', 'Animated auto'],
          ].map(([to, src, label, sub, subCls, alt]) => (
            <Link key={label} to={to} className="overflow-hidden rounded-[18px] border-[1.5px] border-line bg-white text-ink no-underline">
              <img src={src} alt={alt} className="block h-[70px] w-full object-cover" />
              <div className="flex items-center justify-between px-3 pt-2 pb-2.5">
                <span className="text-[15px] font-extrabold">{label}</span>
                <span className={`text-[11px] font-bold ${subCls}`}>{sub}</span>
              </div>
            </Link>
          ))}
        </div>

        <Link to="/nearby" className="flex items-center gap-3 rounded-[18px] bg-night px-3.5 py-3 text-[#F4EEF8] no-underline">
          <svg width="40" height="40" viewBox="0 0 40 40" aria-hidden="true" className="shrink-0"><rect width="40" height="40" rx="12" fill="#221D2E" /><circle cx="14" cy="14" r="8" fill="#FFB52E" opacity=".35" /><path d="M10 32 L10 10 L30 10" stroke="#2EE6A8" strokeWidth="3" fill="none" strokeLinecap="round" /><circle cx="13" cy="22" r="3" fill="#2EE6A8" /><circle cx="22" cy="13" r="3" fill="#2EE6A8" /></svg>
          <div className="flex flex-1 flex-col">
            <span className="text-[15px] font-extrabold">{t('Safe way home', 'பாதுகாப்பான வீட்டு வழி')}</span>
            <span className="text-xs text-[#B9AFC8]">{t('Busy roads · shops open at night · your people nearby', 'கூட்டமான சாலை · இரவில் திறந்த கடைகள் · உங்கள் ஆட்கள்')}</span>
          </div>
          <Icon.chevron stroke="#B9AFC8" />
        </Link>

        <Link to="/circle" className="flex items-center justify-between rounded-[18px] border-[1.5px] border-line bg-white px-3.5 py-2.5 text-ink no-underline">
          <div className="flex items-center gap-2.5">
            <div className="flex">
              {accepted.slice(0, 3).map((c, i) => (
                <Avatar key={c.id} label={c.label} color={AVATAR_COLORS[i][0]} text={AVATAR_COLORS[i][1]} className={`border-2 border-white text-sm ${i ? '-ml-2.5' : ''}`} />
              ))}
            </div>
            <div className="flex flex-col">
              <span className="text-sm font-bold">{t(`Your circle · ${accepted.length} people`, `உங்கள் வட்டம் · ${accepted.length} பேர்`)}</span>
              <span className="text-xs text-mute">{t('They see you only during trips', 'பயணத்தின் போது மட்டும் பார்ப்பார்கள்')}</span>
            </div>
          </div>
          <Icon.chevron stroke="#6A5878" />
        </Link>
        <Link to="/demo" className="text-center text-xs font-bold text-plum no-underline">{t('Demo page for judges ›', 'நடுவர்களுக்கான டெமோ ›')}</Link>
      </div>

      <SosFab className="bottom-24 !fixed right-[max(16px,calc(50vw-199px))]" />
      <BottomNav />
    </div>
  )
}
