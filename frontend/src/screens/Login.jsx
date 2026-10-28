import { useEffect, useRef, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { img } from '@/assets'
import { Icon, SectionLabel } from '@/components/kit'
import { api } from '@/lib/api'
import { useLang, useT } from '@/lib/i18n'
import { useApp } from '@/lib/store'
import { otpError, supabase, toE164 } from '@/lib/supabase'
import { cn } from '@/lib/utils'

const AREAS = ['Anna Nagar West', 'Nungambakkam', 'Kilpauk', 'Koyambedu', 'T. Nagar', 'Egmore']
const RESEND_SECONDS = 45

export default function Login() {
  const { lang, setLang } = useLang()
  const t = useT()
  const navigate = useNavigate()
  const { me, signedIn, refresh } = useApp()
  const [step, setStep] = useState('phone') // phone -> otp -> profile
  const [phone, setPhone] = useState('')
  const [otp, setOtp] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const [wait, setWait] = useState(0)
  const [name, setName] = useState('')
  const [home, setHome] = useState('')
  const [start, setStart] = useState('Anna Nagar West')
  const otpRef = useRef(null)
  const digits = phone.replace(/\D/g, '')

  // Already signed in: finish setup, or go straight home.
  useEffect(() => {
    if (!signedIn || !me) return
    if (me.needs_setup) setStep('profile')
    else if (step !== 'profile') navigate('/home', { replace: true })
  }, [signedIn, me, step, navigate])

  useEffect(() => {
    if (!wait) return undefined
    const id = setTimeout(() => setWait((w) => w - 1), 1000)
    return () => clearTimeout(id)
  }, [wait])

  useEffect(() => { if (step === 'otp') otpRef.current?.focus() }, [step])

  const sendCode = async () => {
    setError(null)
    if (!supabase) { setError(otpError('provider disabled', t)); return }
    setBusy(true)
    const { error: e } = await supabase.auth.signInWithOtp({ phone: toE164(digits) })
    setBusy(false)
    if (e) { setError(otpError(e, t)); return }
    setStep('otp')
    setWait(RESEND_SECONDS)
  }

  const verify = async () => {
    setError(null)
    setBusy(true)
    const { error: e } = await supabase.auth.verifyOtp({ phone: toE164(digits), token: otp, type: 'sms' })
    setBusy(false)
    if (e) { setError(otpError(e, t)); setOtp(''); return }
    refresh() // the effect above moves on to profile setup or home
  }

  const saveProfile = async () => {
    setBusy(true)
    try {
      await api.saveMe({ display_name: name.trim(), home_area: home || undefined, start_area: start, lang })
      refresh()
      navigate('/home', { replace: true })
    } catch (e) {
      setError({ code: 'save', text: e.message })
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="flex min-h-dvh flex-col bg-cream">
      <div className="sp-aurora relative flex h-[340px] flex-col items-center justify-end overflow-hidden rounded-b-[40px] pb-[18px]">
        <div className="absolute top-[22px] right-5 left-5 flex items-center justify-between">
          <div className="flex gap-1.5" aria-hidden="true">
            {['phone', 'otp', 'profile'].map((s) => (
              <span key={s} className={cn('h-1.5 rounded-[3px] transition-all', s === step ? 'w-[22px] bg-white' : 'w-1.5 bg-white/50')} />
            ))}
          </div>
          {step !== 'profile' && (
            <Link to="/home" className="rounded-full bg-white/15 px-3 py-2 text-sm font-semibold text-white no-underline backdrop-blur">
              {t('Try demo', 'டெமோ')}
            </Link>
          )}
        </div>
        <img src={img.poseWave} alt={t('AVAL waving hello', 'அவள் வணக்கம் சொல்கிறாள்')} className="sp-float h-56 w-[176px] object-contain" />
        <span className="text-[36px] leading-none font-extrabold tracking-[-0.01em] text-white">SafePath</span>
        <span className="mt-1 font-serif-ta text-lg font-extrabold text-[#FFE1EC]">சேஃப்பாத்</span>
      </div>

      <div className="flex flex-1 flex-col gap-[18px] px-[22px] pt-[22px] pb-[18px]">
        {step === 'phone' && (
          <>
            <div className="flex flex-col gap-1">
              <span className="text-[22px] leading-[1.25] font-extrabold">{t('Travel freely. AVAL has your back.', 'பயமின்றி பயணியுங்கள்.')}</span>
              <span className="font-tamil text-[15px] text-mute">பயமின்றி பயணியுங்கள். அவள் உங்களுடன்.</span>
            </div>

            <div className="flex flex-col gap-2">
              <SectionLabel>Language · மொழி</SectionLabel>
              <div className="grid grid-cols-2 gap-2.5">
                {[['ta', 'தமிழ்'], ['en', 'English']].map(([code, label]) => (
                  <button key={code} type="button" aria-pressed={lang === code} onClick={() => setLang(code)}
                    className={cn('sp-press h-[52px] rounded-2xl border-2 text-[17px] font-bold',
                      lang === code ? 'border-plum bg-plum text-white shadow-[0_8px_18px_rgba(91,31,150,0.28)]' : 'border-line bg-white text-ink',
                      code === 'ta' && 'font-tamil')}>
                    {label}
                  </button>
                ))}
              </div>
            </div>

            <form className="flex flex-col gap-[14px]" onSubmit={(e) => { e.preventDefault(); if (digits.length === 10 && !busy) sendCode() }}>
              <div className="flex flex-col gap-2">
                <label htmlFor="phone"><SectionLabel>{t('Your mobile number', 'உங்கள் கைபேசி எண்')}</SectionLabel></label>
                <div className="flex h-14 items-center gap-2.5 rounded-2xl border-2 border-line bg-white px-4 focus-within:border-plum focus-within:shadow-[0_0_0_4px_rgba(91,31,150,0.12)]">
                  <span className="text-base font-bold">+91</span>
                  <span className="h-6 w-px bg-line" />
                  <input id="phone" inputMode="numeric" autoComplete="tel-national" placeholder="98xxx xxxxx" value={phone}
                    onChange={(e) => setPhone(e.target.value.replace(/[^\d ]/g, '').slice(0, 11))}
                    className="min-w-0 flex-1 bg-transparent text-[17px] font-semibold tracking-[0.04em] text-ink outline-none" />
                </div>
                <span className="text-xs text-mute">{t('Used only to sign you in and to alert your circle. Never shown to anyone.', 'உள்நுழையவும் உங்கள் வட்டத்துக்குத் தெரிவிக்கவும் மட்டும்.')}</span>
              </div>
              <button type="submit" disabled={digits.length !== 10 || busy} className="sp-btn-primary">
                {busy ? t('Sending…', 'அனுப்புகிறது…') : t('Send code by SMS', 'SMS குறியீடு அனுப்பு')}
                {!busy && <Icon.arrow stroke="#FFFFFF" size={20} />}
              </button>
            </form>
          </>
        )}

        {step === 'otp' && (
          <form className="flex flex-col gap-3" onSubmit={(e) => { e.preventDefault(); if (otp.length === 6 && !busy) verify() }}>
            <span className="text-[22px] font-extrabold">{t('Enter the 6-digit code', '6 இலக்க குறியீடு')}</span>
            <span className="text-sm text-mute">{t(`Sent to +91 ••••• ${digits.slice(-5)}`, `+91 ••••• ${digits.slice(-5)} க்கு அனுப்பப்பட்டது`)}</span>
            <label htmlFor="otp" className="sr-only">{t('Code', 'குறியீடு')}</label>
            <div className="relative" onClick={() => otpRef.current?.focus()}>
              <input ref={otpRef} id="otp" inputMode="numeric" autoComplete="one-time-code" maxLength={6} value={otp}
                onChange={(e) => setOtp(e.target.value.replace(/\D/g, '').slice(0, 6))}
                className="absolute inset-0 opacity-0" />
              <div className="grid grid-cols-6 gap-2" aria-hidden="true">
                {Array.from({ length: 6 }, (_, i) => (
                  <span key={i} className={cn('flex h-14 items-center justify-center rounded-xl border-2 bg-white text-2xl font-extrabold transition',
                    i === otp.length ? 'border-plum shadow-[0_0_0_4px_rgba(91,31,150,0.12)]' : otp[i] ? 'border-pink-deep' : 'border-line')}>
                    {otp[i] || ''}
                  </span>
                ))}
              </div>
            </div>
            <button type="submit" disabled={otp.length !== 6 || busy} className="sp-btn-primary">
              {busy ? t('Checking…', 'சரிபார்க்கிறது…') : t('Verify and continue', 'சரிபார்த்து தொடர்')}
            </button>
            <div className="flex items-center justify-between text-sm">
              <button type="button" onClick={() => { setStep('phone'); setOtp(''); setError(null) }} className="min-h-12 font-semibold text-plum">
                {t('Change number', 'எண்ணை மாற்று')}
              </button>
              <button type="button" disabled={wait > 0 || busy} onClick={sendCode} className="min-h-12 font-semibold text-plum disabled:text-mute">
                {wait > 0 ? t(`Resend in ${wait}s`, `${wait} வி.`) : t('Resend code', 'மீண்டும் அனுப்பு')}
              </button>
            </div>
          </form>
        )}

        {step === 'profile' && (
          <form className="flex flex-col gap-4" onSubmit={(e) => { e.preventDefault(); if (name.trim() && !busy) saveProfile() }}>
            <div className="flex items-center gap-3">
              <span className="text-[22px] leading-tight font-extrabold">{t('What should AVAL call you?', 'அவள் உங்களை எப்படி அழைக்கலாம்?')}</span>
            </div>
            {me?.phone_masked && (
              <span className="flex items-center gap-2 rounded-xl bg-safe-bg px-3 py-2 text-sm font-semibold text-teal-dark">
                <Icon.shield stroke="#0B7F74" size={18} />{t(`Signed in as ${me.phone_masked}`, `${me.phone_masked} ஆக உள்நுழைந்தீர்கள்`)}
              </span>
            )}
            <label className="flex flex-col gap-2">
              <SectionLabel>{t('Your name (or a nickname)', 'உங்கள் பெயர்')}</SectionLabel>
              <input value={name} onChange={(e) => setName(e.target.value.slice(0, 40))} autoComplete="given-name" placeholder="Priya"
                className="h-14 rounded-2xl border-2 border-line bg-white px-4 text-[17px] font-semibold outline-none focus:border-plum" />
            </label>
            <AreaPicker label={t('Where do you usually start?', 'வழக்கமாக எங்கிருந்து?')} value={start} onChange={setStart} />
            <AreaPicker label={t('Home area (optional)', 'வீட்டுப் பகுதி')} value={home} onChange={setHome} optional />
            <span className="text-xs text-mute">{t('We save the area only, never your exact address.', 'பகுதி மட்டும், சரியான முகவரி இல்லை.')}</span>
            <button type="submit" disabled={!name.trim() || busy} className="sp-btn-primary">
              {busy ? t('Saving…', 'சேமிக்கிறது…') : t('Start travelling', 'பயணம் தொடங்கு')}
            </button>
          </form>
        )}

        {error && (
          <div role="alert" className="flex flex-col gap-2 rounded-2xl border border-pink/30 bg-[#FFF0F5] px-3.5 py-3 text-sm text-ink">
            <span>{error.text}</span>
            {error.code === 'phone_off' && (
              <Link to="/home" className="self-start font-bold text-plum">{t('Continue in demo mode →', 'டெமோவில் தொடர் →')}</Link>
            )}
          </div>
        )}

        <div className="mt-auto flex items-start gap-2.5 rounded-[14px] bg-lilac px-3.5 py-3">
          <Icon.shield stroke="#0FA596" size={20} className="mt-px shrink-0" />
          <span className="text-[13px] leading-[1.45] text-ink-2">
            {t('We never track you in the background. Location is shared only during a trip or SOS.',
              'பின்னணியில் உங்களைக் கண்காணிப்பதில்லை. பயணம் அல்லது SOS போது மட்டுமே இருப்பிடம் பகிரப்படும்.')}
          </span>
        </div>
      </div>
    </div>
  )
}

function AreaPicker({ label, value, onChange, optional }) {
  return (
    <div className="flex flex-col gap-2">
      <SectionLabel>{label}</SectionLabel>
      <div className="flex flex-wrap gap-2" role="radiogroup" aria-label={label}>
        {AREAS.map((a) => (
          <button key={a} type="button" role="radio" aria-checked={value === a}
            onClick={() => onChange(optional && value === a ? '' : a)}
            className={cn('sp-press min-h-11 rounded-full border-2 px-3.5 text-sm font-semibold',
              value === a ? 'border-plum bg-plum text-white' : 'border-line bg-white text-ink')}>
            {a}
          </button>
        ))}
      </div>
    </div>
  )
}
