import { useEffect, useRef, useState } from 'react'

import Aval from '@/components/Aval'
import { BackButton, Icon, SampleLabel } from '@/components/kit'
import { api } from '@/lib/api'
import { useAsync } from '@/lib/hooks'
import { useLang, useT } from '@/lib/i18n'
import { speak, useRecorder } from '@/lib/voice'

const QUICK = ['nungambakkam bus', 'START', 'REACHED', 'HELP', 'CALL', 'நுங்கம்பாக்கம் 8 மணி பொண்ணோட']

/** Judges' demo: a keypad phone that sends SMS-style text to AVAL (via n8n when configured). */
export default function Demo() {
  const t = useT()
  const { lang } = useLang()
  const [thread, setThread] = useState([])
  const [text, setText] = useState('')
  const [last, setLast] = useState(null)
  const [busy, setBusy] = useState(false)
  const [avalState, setAvalState] = useState('idle')
  const rec = useRecorder()
  const outbox = useAsync(() => api.outbox(), [thread.length])
  const health = useAsync(() => api.health(), [])
  const end = useRef(null)
  useEffect(() => end.current?.scrollIntoView({ block: 'end' }), [thread])

  async function send(msg) {
    if (!msg.trim() || busy) return
    setThread((th) => [...th, { me: true, text: msg }])
    setText('')
    setBusy(true)
    setAvalState('thinking')
    try {
      const r = await api.demoChat(msg, lang)
      setThread((th) => [...th, { me: false, text: r.sms_text }])
      setLast(r)
      setAvalState(r.aval_state === 'alert' ? 'alert' : 'talking')
      setTimeout(() => setAvalState((s) => (s === 'talking' ? 'idle' : s)), 2000)
    } catch (e) {
      setThread((th) => [...th, { me: false, text: `(${e.message})`, error: true }])
      setAvalState('idle')
    } finally {
      setBusy(false)
    }
  }

  async function callDown() {
    setAvalState('listening')
    await rec.start()
  }
  async function callUp() {
    if (!rec.recording) return
    const { blob } = await rec.stop()
    setAvalState('thinking')
    try {
      const r = await api.voice(blob, lang)
      setThread((th) => [...th, { me: true, text: `🎙 ${r.transcript}` }, { me: false, text: r.reply.text }])
      setLast({ ...r, via: `voice · STT ${r.stt_provider} · TTS ${r.tts_provider}` })
      setAvalState('talking')
      await speak({ audioBase64: r.audio_base64, format: r.audio_format, text: r.reply.text, lang: r.reply.lang })
      setAvalState('idle')
    } catch (e) {
      setThread((th) => [...th, { me: false, text: `(${e.message})`, error: true }])
      setAvalState('idle')
    }
  }

  const services = health.data?.services || {}
  return (
    <div className="flex min-h-dvh flex-col gap-4 bg-[#1A1424] px-4 pt-4 pb-8 text-white">
      <div className="flex items-center gap-3">
        <BackButton to="/home" className="bg-white/15 [&_svg]:stroke-white" />
        <div className="flex flex-col">
          <h1 className="text-xl font-extrabold">{t('Demo: keypad phone', 'டெமோ: கீபேட் போன்')}</h1>
          <span className="text-xs text-[#B9AFC8]">{t('SMS-style text to AVAL, the same path a basic phone uses', 'அடிப்படை போன் போலவே SMS')}</span>
        </div>
      </div>

      {/* keypad phone */}
      <div className="mx-auto w-[260px] rounded-[34px] border-4 border-[#3A3448] bg-[#2B2340] p-4 shadow-[0_20px_40px_rgba(0,0,0,0.4)]">
        <div className="mb-2 flex justify-between text-[10px] text-[#B9AFC8]"><span>SafePath SMS</span><span>📶 🔋</span></div>
        <div className="no-scrollbar h-[220px] overflow-y-auto rounded-xl bg-[#C9E7C1] p-2 font-mono text-[12px] leading-snug text-[#123018]" aria-live="polite">
          {thread.length === 0 && <p className="opacity-70">{t('Type below or tap a quick message.', 'கீழே தட்டச்சு செய்யவும்.')}</p>}
          {thread.map((m, i) => (
            <p key={i} className={`mb-1.5 whitespace-pre-wrap ${m.me ? 'text-right' : ''} ${m.error ? 'text-[#8B1D2C]' : ''}`}>
              <span className={`inline-block max-w-[92%] rounded-md px-1.5 py-1 ${m.me ? 'bg-[#A8D69D]' : 'bg-white/60'}`}>{m.text}</span>
            </p>
          ))}
          {busy && <p className="opacity-70">…</p>}
          <div ref={end} />
        </div>
        <form className="mt-3 flex gap-2" onSubmit={(e) => { e.preventDefault(); send(text) }}>
          <label htmlFor="sms" className="sr-only">SMS text</label>
          <input id="sms" value={text} onChange={(e) => setText(e.target.value)} maxLength={160} placeholder="SMS…"
            className="h-11 min-w-0 flex-1 rounded-lg bg-[#1A1424] px-2 font-mono text-sm text-white outline-none" />
          <button type="submit" disabled={busy} className="h-11 rounded-lg bg-mint px-3 text-sm font-extrabold text-night-2 disabled:opacity-50">{t('Send', 'அனுப்பு')}</button>
        </form>
        <div className="mt-3 grid grid-cols-3 gap-1.5">
          {QUICK.map((q) => (
            <button key={q} type="button" onClick={() => send(q)} disabled={busy}
              className="min-h-11 truncate rounded-lg bg-[#3A3448] px-1 text-[11px] font-bold text-white disabled:opacity-50">{q}</button>
          ))}
        </div>
      </div>

      {/* Call AVAL */}
      <div className="flex items-center gap-3 rounded-2xl bg-white/10 p-3">
        <Aval state={avalState} className="h-24 w-[74px] shrink-0" />
        <div className="flex flex-1 flex-col gap-1">
          <span className="text-sm font-extrabold">{t('Call AVAL', 'அவளை அழை')}</span>
          <span className="text-xs text-[#D8CFE4]">{t('Hold the button and speak (Tamil or English). Sarvam turns speech to text and AVAL answers out loud.', 'அழுத்திப் பேசுங்கள். அவள் பதில் சொல்வாள்.')}</span>
        </div>
        <button type="button" aria-label={t('Hold to talk to AVAL', 'பேச அழுத்தவும்')} onPointerDown={callDown} onPointerUp={callUp} onPointerLeave={callUp}
          onContextMenu={(e) => e.preventDefault()}
          className={`flex size-16 shrink-0 touch-none items-center justify-center rounded-full ${rec.recording ? 'scale-110 bg-teal' : 'bg-pink'}`}>
          <Icon.mic stroke="#FFFFFF" size={28} />
        </button>
      </div>

      {/* What AVAL did */}
      <div className="flex flex-col gap-2 rounded-2xl bg-lilac p-3.5 text-ink">
        <div className="flex items-center justify-between">
          <span className="text-[11px] font-bold tracking-[0.12em] text-plum-deep uppercase">{t('What AVAL did', 'அவள் செய்தது')}</span>
          {last?.via && <span className="rounded-full bg-white px-2 py-0.5 text-[11px] font-bold text-plum">via {last.via}</span>}
        </div>
        {!last && <span className="text-sm text-mute">{t('Send a message to see each agent step.', 'ஒரு செய்தி அனுப்புங்கள்.')}</span>}
        {(last?.agent_steps || last?.steps || []).map((s, i) => (
          <div key={i} className="flex items-center gap-2 text-[13px]">
            <span className={`flex size-[18px] shrink-0 items-center justify-center rounded-full text-[11px] font-extrabold ${s.status === 'done' ? 'bg-teal-ink text-white' : 'bg-[#F6A623] text-ink'}`}>{s.status === 'done' ? '✓' : '!'}</span>
            {s.text}
          </div>
        ))}
        {last?.intake && (
          <span className="text-[11px] text-mute">
            intent <b>{last.intake.intent}</b> · parsed by <b>{last.intake.source}</b>{last.fallback ? ' · fallback reply' : ''}
          </span>
        )}
      </div>

      {/* Outbox + services */}
      <div className="flex flex-col gap-1.5 rounded-2xl bg-white/10 p-3.5">
        <span className="text-[11px] font-bold tracking-[0.12em] text-[#D8CFE4] uppercase">
          {t('SMS outbox', 'SMS வெளிப்பெட்டி')} · {outbox.data?.provider || '…'}
        </span>
        {(outbox.data?.messages || []).slice(-5).reverse().map((m, i) => (
          <div key={i} className="flex justify-between gap-2 text-xs">
            <span className="truncate text-[#D8CFE4]">{m.to || '—'} · {m.purpose}</span>
            <span className={m.status === 'sent' ? 'text-mint' : m.status === 'mock_logged' ? 'text-marigold' : 'text-[#FF8C90]'}>
              {m.status === 'sent' ? 'sent' : m.status === 'mock_logged' ? 'demo (not sent)' : `not sent${m.reason ? ` (${m.reason})` : ''}`}
            </span>
          </div>
        ))}
        {outbox.data?.messages?.length === 0 && <span className="text-xs text-[#B9AFC8]">{t('Nothing sent yet', 'எதுவும் அனுப்பவில்லை')}</span>}
        <span className="mt-1 text-[11px] text-[#B9AFC8]">
          {['gemini', 'sarvam', 'sms_provider', 'razorpay'].map((k) => `${k}: ${String(services[k] ?? '…').split(' ')[0]}`).join(' · ')}
        </span>
      </div>
      <SampleLabel className="text-[#B9AFC8]" />
    </div>
  )
}
