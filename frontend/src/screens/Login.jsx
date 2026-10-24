import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { img } from '@/assets'
import { Icon, SectionLabel } from '@/components/kit'
import { useLang, useT } from '@/lib/i18n'
import { cn } from '@/lib/utils'

export default function Login() {
  const { lang, setLang } = useLang()
  const t = useT()
  const navigate = useNavigate()
  const [phone, setPhone] = useState('')
  const [step, setStep] = useState('phone')
  const [otp, setOtp] = useState('')
  const digits = phone.replace(/\D/g, '')

  return (
    <div className="flex min-h-dvh flex-col bg-cream">
      <div className="relative flex h-[380px] flex-col items-center justify-end rounded-b-[40px] bg-[linear-gradient(160deg,#5B1F96_0%,#8A2FC2_55%,#FF4F8B_100%)] pb-[18px]">
        <div className="absolute top-[22px] right-5 left-5 flex items-center justify-between">
          <div className="flex gap-1.5">
            <span className="h-1.5 w-[22px] rounded-[3px] bg-white" />
            <span className="size-1.5 rounded-[3px] bg-white/50" />
            <span className="size-1.5 rounded-[3px] bg-white/50" />
          </div>
          <Link to="/home" className="px-1 py-2.5 text-sm font-semibold text-white no-underline">{t('Skip', 'தவிர்')}</Link>
        </div>
        <img src={img.poseWave} alt="AVAL waving hello" className="h-64 w-[196px] object-contain" />
        <span className="text-[38px] leading-none font-extrabold tracking-[-0.01em] text-white">SafePath</span>
        <span className="mt-1 font-serif-ta text-lg font-extrabold text-[#FFE1EC]">சேஃப்பாத்</span>
      </div>

      <div className="flex flex-1 flex-col gap-[18px] px-[22px] pt-[22px] pb-[18px]">
        <div className="flex flex-col gap-1">
          <span className="text-[22px] leading-[1.25] font-extrabold">Travel freely. AVAL has your back.</span>
          <span className="font-tamil text-[15px] text-mute">பயமின்றி பயணியுங்கள். அவள் உங்களுடன்.</span>
        </div>

        <div className="flex flex-col gap-2">
          <SectionLabel>Language · மொழி</SectionLabel>
          <div className="grid grid-cols-2 gap-2.5">
            {[['ta', 'தமிழ்'], ['en', 'English']].map(([code, label]) => (
              <button
                key={code}
                type="button"
                aria-pressed={lang === code}
                onClick={() => setLang(code)}
                className={cn('h-[52px] rounded-2xl border-2 text-[17px] font-bold',
                  lang === code ? 'border-plum bg-plum text-white' : 'border-line bg-white text-ink',
                  code === 'ta' && 'font-tamil')}
              >
                {label}
              </button>
            ))}
          </div>
        </div>

        {step === 'phone' ? (
          <form
            className="flex flex-col gap-[18px]"
            onSubmit={(e) => {
              e.preventDefault()
              if (digits.length === 10) setStep('otp')
            }}
          >
            <div className="flex flex-col gap-2">
              <label htmlFor="phone"><SectionLabel>{t('Mobile number', 'கைபேசி எண்')}</SectionLabel></label>
              <div className="flex h-14 items-center gap-2.5 rounded-2xl border-2 border-line bg-white px-4">
                <span className="text-base font-bold">+91</span>
                <span className="h-6 w-px bg-line" />
                <input
                  id="phone"
                  inputMode="numeric"
                  autoComplete="tel-national"
                  placeholder="98xxx xxxxx"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value.replace(/[^\d ]/g, '').slice(0, 11))}
                  className="min-w-0 flex-1 bg-transparent text-[17px] font-semibold tracking-[0.04em] text-ink outline-none"
                />
              </div>
            </div>
            <button
              type="submit"
              disabled={digits.length !== 10}
              className="flex h-14 items-center justify-center gap-2 rounded-2xl bg-pink text-[17px] font-extrabold text-white shadow-[0_8px_20px_rgba(255,79,139,0.3)] disabled:opacity-50"
            >
              {t('Send OTP', 'OTP அனுப்பு')}
              <Icon.arrow stroke="#FFFFFF" size={20} />
            </button>
          </form>
        ) : (
          <form
            className="flex flex-col gap-3"
            onSubmit={(e) => {
              e.preventDefault()
              if (otp.length === 4) navigate('/home')
            }}
          >
            <label htmlFor="otp" id="otp-label"><SectionLabel>{t('Enter OTP', 'OTP உள்ளிடவும்')}</SectionLabel></label>
            <input
              id="otp"
              aria-labelledby="otp-label"
              inputMode="numeric"
              autoComplete="one-time-code"
              maxLength={4}
              value={otp}
              onChange={(e) => setOtp(e.target.value.replace(/\D/g, '').slice(0, 4))}
              className="h-14 rounded-2xl border-2 border-line bg-white text-center text-2xl font-extrabold tracking-[0.6em] outline-none"
            />
            <span className="text-xs text-mute">
              {t('Demo mode: no OTP is sent. Enter any 4 digits.', 'டெமோ: OTP அனுப்பப்படவில்லை. ஏதேனும் 4 எண்கள்.')}
            </span>
            <button type="submit" disabled={otp.length !== 4} className="h-14 rounded-2xl bg-pink text-[17px] font-extrabold text-white disabled:opacity-50">
              {t('Continue', 'தொடர்')}
            </button>
          </form>
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
