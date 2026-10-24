import { useEffect, useRef, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'

import { img } from '@/assets'
import Aval from '@/components/Aval'
import { PlacesList, RouteCard } from '@/components/Cards'
import { useStartTrip } from '@/components/StartTrip'
import { BackButton, BottomNav, Icon, LangToggle, SampleLabel } from '@/components/kit'
import { api } from '@/lib/api'
import { clock } from '@/lib/hooks'
import { useLang, useT } from '@/lib/i18n'
import { useApp } from '@/lib/store'
import { speak, useRecorder } from '@/lib/voice'

const KEY = 'sp_chat'

export default function AvalChat() {
  const t = useT()
  const { lang } = useLang()
  const navigate = useNavigate()
  const { profile } = useApp()
  const [params, setParams] = useSearchParams()
  const [messages, setMessages] = useState(() => JSON.parse(sessionStorage.getItem(KEY) || '[]'))
  const [text, setText] = useState('')
  const [state, setState] = useState('wave')
  const [startTrip, tripSheet] = useStartTrip()
  const rec = useRecorder()
  const endRef = useRef(null)
  const name = profile?.display_name || ''

  useEffect(() => { sessionStorage.setItem(KEY, JSON.stringify(messages.slice(-20))) }, [messages])
  useEffect(() => { endRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' }) }, [messages, state])
  useEffect(() => {
    const id = setTimeout(() => setState((s) => (s === 'wave' ? 'idle' : s)), 2600)
    return () => clearTimeout(id)
  }, [])
  const handledQ = useRef(false)
  useEffect(() => {
    const q = params.get('q')
    if (q && !handledQ.current) {
      handledQ.current = true
      setParams({}, { replace: true })
      send(q)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  async function send(q, voiceMeta) {
    if (!q?.trim()) return
    setMessages((m) => [...m, { role: 'user', text: q, voice: voiceMeta }])
    setText('')
    setState('thinking')
    try {
      const res = await api.chat(q, lang)
      setMessages((m) => [...m, { role: 'aval', res }])
      setState(res.aval_state === 'alert' ? 'alert' : 'talking')
      setTimeout(() => setState((s) => (s === 'talking' ? 'idle' : s)), 2500)
    } catch (e) {
      setMessages((m) => [...m, { role: 'error', text: e.message }])
      setState('idle')
    }
  }

  async function onMicDown() {
    setState('listening')
    await rec.start()
  }

  async function onMicUp() {
    if (!rec.recording) return
    const { blob, seconds } = await rec.stop()
    setState('thinking')
    try {
      const res = await api.voice(blob, lang)
      setMessages((m) => [
        ...m,
        { role: 'user', text: res.transcript, voice: { seconds, provider: res.stt_provider, lang: res.intake?.lang } },
        { role: 'aval', res },
      ])
      setState('talking')
      await speak({ audioBase64: res.audio_base64, format: res.audio_format, text: res.reply.text, lang: res.reply.lang })
      setState(res.aval_state === 'alert' ? 'alert' : 'idle')
    } catch (e) {
      setMessages((m) => [...m, { role: 'error', text: e.message }])
      setState('idle')
    }
  }

  async function runAction(action) {
    const p = action.payload || {}
    if (action.id === 'choose_option') {
      navigate(`/booking?from=${encodeURIComponent(p.from)}&to=${encodeURIComponent(p.to)}&time=${p.time}&option=${encodeURIComponent(p.option_id)}`)
    } else if (action.id === 'start_trip') {
      startTrip(p)
    } else if (action.id === 'pay') {
      navigate(`/payment?from=${encodeURIComponent(p.from)}&to=${encodeURIComponent(p.to)}&time=${p.time}&option=${encodeURIComponent(p.option_id)}`)
    } else if (action.id === 'walk') {
      navigate('/nearby')
    } else if (action.id === 'ask_to_meet') {
      navigate('/circle')
    }
  }

  const quickAsks = [
    [t('Free bus now?', 'இலவச பஸ் இப்போ?'), () => send(t('Free bus now?', 'இலவச பஸ் இப்போ?'))],
    [t('Safe shops near me', 'அருகில் பாதுகாப்பான கடைகள்'), () => send('shops open now near me')],
    [t('Call Amma', 'அம்மாவை அழை'), () => navigate('/circle')],
    [t('Safe way home', 'வீட்டுக்கு வழி'), () => send('safe way home')],
  ]

  return (
    <div className="flex min-h-dvh flex-col bg-cream">
      <div className="flex items-center justify-between px-4 pt-[18px] pb-2.5">
        <BackButton to="/home" />
        <div className="flex items-baseline gap-2">
          <span className="text-[22px] font-extrabold tracking-[0.04em] text-plum-deep">AVAL</span>
          <span className="font-serif-ta text-lg font-extrabold text-pink-deep">அவள்</span>
        </div>
        <LangToggle />
      </div>

      <div className="flex h-[168px] items-end gap-1 px-4">
        <Aval state={state} className="h-[165px] w-32 shrink-0" />
        <div className="mb-10 flex flex-col gap-1 rounded-[22px_22px_22px_6px] bg-white px-4 py-3.5 shadow-[0_2px_0_#EADCF1]">
          {state === 'listening' ? (
            <span className="text-[17px] leading-[1.3] font-bold">{t("I'm listening…", 'கேட்கிறேன்…')}</span>
          ) : state === 'thinking' ? (
            <span className="text-[17px] leading-[1.3] font-bold">{t('Checking buses, places and your circle…', 'பஸ், இடங்கள், வட்டம் பார்க்கிறேன்…')}</span>
          ) : (
            <>
              <span className="text-[17px] leading-[1.3] font-bold">Hi {name}! Where are you going today?</span>
              <span className="font-tamil text-sm leading-normal text-mute">வணக்கம்! இன்று எங்கே போகிறீர்கள்?</span>
            </>
          )}
        </div>
      </div>

      <div className="flex flex-1 flex-col gap-3 px-4 pt-1 pb-3" aria-live="polite">
        {messages.length === 0 && (
          <SampleLabel>{t('Try: "Nungambakkam, 8am, with my daughter"', 'உதா: "நுங்கம்பாக்கம், 8 மணி, பொண்ணோட"')}</SampleLabel>
        )}
        {messages.map((m, i) =>
          m.role === 'user' ? (
            <div key={i} className="flex max-w-[78%] flex-col gap-1 self-end rounded-[20px_20px_6px_20px] bg-plum-deep px-4 py-3 text-white">
              <span className="text-[15px] leading-[1.4] font-semibold">{m.text}</span>
              {m.voice && (
                <span className="flex items-center gap-1 text-xs opacity-80">
                  <Icon.mic stroke="#FFFFFF" size={12} width={2.4} />
                  {m.voice.lang === 'ta' ? t('Spoken in Tamil', 'தமிழில் பேசியது') : t('Spoken', 'பேசியது')} · 0:{String(m.voice.seconds).padStart(2, '0')}
                  {m.voice.provider === 'mock' && ` · ${t('demo voice', 'டெமோ குரல்')}`}
                </span>
              )}
            </div>
          ) : m.role === 'error' ? (
            <div key={i} role="alert" className="rounded-2xl border-[1.5px] border-[#F5D3D8] bg-white px-3.5 py-2.5 text-sm text-sos">{m.text}</div>
          ) : (
            <AvalReply key={i} res={m.res} onAction={runAction} />
          ),
        )}
        {state === 'thinking' && (
          <div className="flex items-center gap-2 pl-[42px] text-sm text-mute">
            <span className="dots inline-flex gap-1"><span className="size-2 rounded-full bg-plum" /><span className="size-2 rounded-full bg-plum" /><span className="size-2 rounded-full bg-plum" /></span>
            {t('AVAL is working', 'அவள் வேலை செய்கிறாள்')}
          </div>
        )}
        <div ref={endRef} />
      </div>

      <div className="sticky bottom-0 z-30 bg-cream pt-2">
      <div className="no-scrollbar flex gap-2 overflow-x-auto px-4 pb-2.5">
        {quickAsks.map(([label, fn]) => (
          <button key={label} type="button" onClick={fn} className="h-10 shrink-0 rounded-full border-[1.5px] border-line bg-white px-3.5 text-[13px] font-semibold text-ink">
            {label}
          </button>
        ))}
      </div>

      <form className="flex items-center gap-2.5 px-4 pb-3.5" onSubmit={(e) => { e.preventDefault(); send(text) }}>
        <label htmlFor="ask" className="sr-only">Ask AVAL</label>
        <input id="ask" value={text} onChange={(e) => setText(e.target.value)} placeholder={t('Type or hold the mic…', 'தட்டச்சு செய்யவும் அல்லது மைக்கை அழுத்தவும்…')}
          className="h-[52px] min-w-0 flex-1 rounded-[26px] border-2 border-line bg-white px-[18px] text-[15px] text-ink outline-none" />
        <button
          type="button"
          aria-label={t('Hold to speak in Tamil', 'தமிழில் பேச அழுத்தவும்')}
          onPointerDown={onMicDown}
          onPointerUp={onMicUp}
          onPointerLeave={onMicUp}
          onContextMenu={(e) => e.preventDefault()}
          className={`flex size-16 shrink-0 touch-none items-center justify-center rounded-full bg-pink-deep shadow-[0_0_0_6px_#FBD9E5] ${rec.recording ? 'scale-110 bg-teal shadow-[0_0_0_10px_rgba(15,165,150,0.25)]' : ''}`}
        >
          <Icon.mic stroke="#FFFFFF" size={28} />
        </button>
      </form>

      <BottomNav className="static" />
      </div>

      {tripSheet}
    </div>
  )
}

function AvalReply({ res, onAction }) {
  const t = useT()
  const card = res.card || {}
  return (
    <>
      <div className="flex items-start gap-2">
        <img src={img.avalFaceV2} alt="" className="size-[34px] shrink-0 rounded-full bg-lilac" />
        <div className="flex min-w-0 flex-1 flex-col gap-3 rounded-[6px_22px_22px_22px] bg-white p-3.5 shadow-[0_2px_0_#EADCF1]">
          <span className={`text-[15px] leading-[1.45] ${res.reply.lang === 'ta' ? 'font-tamil' : ''}`}>{res.reply.text}</span>
          {card.type === 'route' && <RouteCard card={card} />}
          {card.type === 'places' && <PlacesList places={card.places} />}
          {card.type === 'place' && <PlacesList places={[card.place]} limit={1} />}
          {card.type === 'arrivals' && (
            <div className="flex flex-col gap-1.5">
              {card.arrivals.slice(0, 3).map((a, i) => (
                <div key={i} className="flex items-center justify-between rounded-xl bg-cream px-3 py-2 text-sm">
                  <span><b className="rounded-md bg-pink px-1.5 text-white">{a.number}</b> {t('to', '→')} {a.towards}</span>
                  <span className="tabular font-bold">{a.in_min} min</span>
                </div>
              ))}
            </div>
          )}
          {card.type === 'safe_route' && card.paths?.[0] && (
            <div className="rounded-xl bg-night p-3 text-sm text-[#F4EEF8]">
              <b>{card.paths[0].name}</b> · {card.paths[0].people_label} · {card.paths[0].shops_open} {t('shops open', 'கடைகள் திறந்துள்ளன')}
            </div>
          )}
          {card.type === 'sos' && (
            <div className="grid grid-cols-2 gap-2">
              {card.helplines.map((h) => (
                <a key={h.number} href={`tel:${h.number}`} className="rounded-xl border-[1.5px] border-[#F5D3D8] p-2 text-center text-ink no-underline">
                  <span className="block text-xs text-mute">{h.name}</span><span className="text-2xl font-black text-[#B3122A]">{h.number}</span>
                </a>
              ))}
            </div>
          )}
          {res.actions?.length > 0 && (
            <div className="flex gap-2">
              {res.actions.filter((a) => a.id !== 'cancel').map((a, i) => (
                <button key={a.id + i} type="button" onClick={() => onAction(a)}
                  className={`h-12 flex-1 rounded-[14px] text-[15px] font-bold ${i === 0 ? 'bg-teal-ink text-white' : 'border-2 border-plum-deep bg-white text-plum-deep'}`}>
                  {t(a.label, a.label_ta)}
                </button>
              ))}
            </div>
          )}
          {card.type === 'route' && card.option?.reach_by && (
            <span className="text-[11px] text-mute">{t(`Reach by ${clock(card.option.reach_by)} · sample timetable`, `${clock(card.option.reach_by)}-க்குள் · மாதிரி நேர அட்டவணை`)}</span>
          )}
        </div>
      </div>
      {res.steps?.length > 0 && (
        <div className="ml-[42px] flex flex-col gap-2 rounded-2xl bg-lilac px-3.5 py-3">
          <span className="text-[11px] font-bold tracking-[0.12em] text-plum-deep uppercase">{t('What AVAL did', 'அவள் செய்தது')}</span>
          <div className="flex flex-col gap-1.5 text-[13px]">
            {res.steps.map((s, i) => (
              <div key={i} className="flex items-center gap-2">
                <span className={`flex size-[18px] shrink-0 items-center justify-center rounded-full text-[11px] font-extrabold ${s.status === 'done' ? 'bg-teal-ink text-white' : 'bg-[#F6A623] text-ink'}`}>
                  {s.status === 'done' ? '✓' : '!'}
                </span>
                {s.text}
              </div>
            ))}
          </div>
        </div>
      )}
    </>
  )
}
