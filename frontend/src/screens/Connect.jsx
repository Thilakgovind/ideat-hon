import { useState } from 'react'
import { toast } from 'sonner'

import { img } from '@/assets'
import Confirm from '@/components/Confirm'
import { AVATAR_COLORS, Avatar, BackButton, BottomNav, ErrorState, Icon, Loading, SampleLabel } from '@/components/kit'
import { api } from '@/lib/api'
import { useAsync } from '@/lib/hooks'
import { useT } from '@/lib/i18n'
import { useApp } from '@/lib/store'
import { cn } from '@/lib/utils'

export default function Connect() {
  const t = useT()
  const { tripId } = useApp()
  const res = useAsync(() => api.circle(), [])
  const trip = useAsync(() => (tripId ? api.trip(tripId).catch(() => null) : Promise.resolve(null)), [tripId])
  const [sheet, setSheet] = useState(null) // {kind:'add'} | {kind:'confirm', ...}
  const [form, setForm] = useState({ label: '', phone: '', relation: 'friend' })
  const [busy, setBusy] = useState(false)
  const contacts = res.data?.contacts || []
  const accepted = contacts.filter((c) => c.accepted)
  const tripActive = trip.data?.trip?.status === 'active'

  async function act(body, done) {
    setBusy(true)
    try {
      const r = await api.circleAction(body)
      if (r.needs_confirmation) {
        setSheet({ kind: 'confirm', body, preview: r.preview, to: r.to })
        return
      }
      done?.(r)
      setSheet(null)
      res.reload()
    } catch (e) {
      toast.error(e.message)
    } finally {
      setBusy(false)
    }
  }
  const delivered = (r) =>
    toast(r.delivery?.sent || r.invite?.status === 'sent' ? t('Sent', 'அனுப்பப்பட்டது') : t('Demo mode: message logged, not sent by SMS', 'டெமோ: SMS அனுப்பப்படவில்லை'))

  return (
    <div className="flex min-h-dvh flex-col bg-cream">
      <div className="flex flex-col rounded-b-[32px] bg-[linear-gradient(160deg,#0FA596,#0B7F74)] px-4 pt-[18px] text-white">
        <div className="flex items-center gap-3">
          <BackButton light />
          <h1 className="text-xl font-extrabold">{t('Your circle', 'உங்கள் வட்டம்')}</h1>
          <span className="ml-auto rounded-full bg-white/20 px-2.5 py-1.5 text-[13px] font-bold">{t(`${contacts.length} of ${res.data?.max ?? 5}`, `${contacts.length} / ${res.data?.max ?? 5}`)}</span>
        </div>
        <div className="flex items-end gap-1.5">
          <div className="flex flex-1 flex-col gap-1 pb-[22px]">
            <span className="text-[17px] leading-[1.3] font-extrabold">{t('Only people you trust. Only during trips.', 'நம்பிக்கையானவர்கள் மட்டும். பயணத்தின் போது மட்டும்.')}</span>
            <span className="font-tamil text-[13px] opacity-90">நம்பிக்கையானவர்கள் மட்டும்</span>
          </div>
          <img src={img.featConnect} alt="AVAL on the phone with her circle" className="h-[146px] w-28 object-contain" />
        </div>
      </div>

      <div className="flex flex-1 flex-col gap-2.5 px-4 pt-4 pb-4">
        {res.loading ? <Loading rows={3} /> : res.error ? <ErrorState error={res.error} onRetry={res.reload} /> : (
          <>
            {contacts.map((c, i) => {
              const [bg, fg] = AVATAR_COLORS[i % AVATAR_COLORS.length]
              const watching = c.accepted && tripActive
              return (
                <div key={c.id} className={cn('flex items-center gap-3 rounded-[20px] bg-white px-3.5 py-3', watching ? 'border-2 border-teal' : 'border-[1.5px] border-line')}>
                  <Avatar label={c.label} color={bg} text={fg} size={50} ring={watching ? '0 0 0 3px #FFFFFF, 0 0 0 5px #2EE6A8' : undefined} />
                  <div className="flex min-w-0 flex-1 flex-col">
                    <span className="text-base font-extrabold">{t(c.label, c.label_ta || c.label)}{c.relation && !['mother'].includes(c.relation) ? ` · ${c.relation}` : ''}</span>
                    <span className={cn('text-xs font-bold', !c.accepted ? 'text-[#B4540A]' : watching ? 'text-teal-dark' : 'font-normal text-mute')}>
                      {!c.accepted ? t('Invite pending', 'அழைப்பு நிலுவையில்') : watching ? t('Watching your trip now', 'உங்கள் பயணத்தைப் பார்க்கிறார்') : t('Not sharing · gets SOS alerts', 'பகிரவில்லை · SOS எச்சரிக்கை பெறுவார்')}
                    </span>
                    <span className="text-[11px] text-mute">{c.phone_masked}</span>
                  </div>
                  {c.accepted ? (
                    <>
                      <button type="button" aria-label={t(`Ask ${c.label} to call you`, `${c.label} அழைக்கச் சொல்`)} onClick={() => act({ action: 'message', contact_id: c.id, kind: 'call_me' }, delivered)}
                        className="flex size-11 items-center justify-center rounded-[14px] bg-safe-bg"><Icon.phone stroke="#0B7F74" size={20} /></button>
                      <button type="button" aria-label={t(`Remove ${c.label}`, `${c.label} நீக்கு`)} onClick={() => act({ action: 'remove', contact_id: c.id }, () => toast(t('Removed', 'நீக்கப்பட்டது')))}
                        className="flex size-11 items-center justify-center rounded-[14px] bg-lilac text-plum">✕</button>
                    </>
                  ) : (
                    <button type="button" onClick={() => act({ action: 'accept', contact_id: c.id }, () => toast(t('Marked accepted (demo)', 'ஏற்கப்பட்டது (டெமோ)')))}
                      className="h-10 rounded-xl border-[1.5px] border-line bg-cream px-3 text-[13px] font-bold text-ink">
                      {t('Accept (demo)', 'ஏற்கவும் (டெமோ)')}
                    </button>
                  )}
                </div>
              )
            })}
            {contacts.length < (res.data?.max ?? 5) && (
              <button type="button" onClick={() => setSheet({ kind: 'add' })}
                className="flex h-14 items-center justify-center gap-2 rounded-[18px] border-2 border-dashed border-[#C9B8D6] text-[15px] font-extrabold text-plum">
                <Icon.plus stroke="#5B1F96" size={20} />{t('Add someone you trust', 'நம்பிக்கையானவரைச் சேர்')}
              </button>
            )}
          </>
        )}

        <div className="flex flex-col gap-1.5 rounded-[18px] bg-lilac p-3.5">
          <span className="text-sm font-extrabold text-plum">{t('How sharing works', 'பகிர்வு எப்படி')}</span>
          <ul className="list-disc pl-4 text-[13px] leading-normal text-ink-2">
            <li>{t('They both have to accept', 'இருவரும் ஏற்க வேண்டும்')}</li>
            <li>{t('They see you only during a trip or SOS', 'பயணம் அல்லது SOS போது மட்டும் பார்ப்பார்கள்')}</li>
            <li>{t('If you miss a check-in, they see your last stop', 'செக்-இன் தவறினால் கடைசி நிறுத்தம் தெரியும்')}</li>
            <li>{t('Remove anyone, anytime', 'எப்போது வேண்டுமானாலும் நீக்கலாம்')}</li>
          </ul>
        </div>
        <span className="text-center text-[11px] text-mute">{t(`${accepted.length} accepted · phone numbers are never shown or logged`, `${accepted.length} ஏற்றனர் · எண்கள் காட்டப்படுவதில்லை`)}</span>
        <SampleLabel />
      </div>
      <BottomNav />

      <Confirm open={sheet?.kind === 'add'} onClose={() => setSheet(null)} title={t('Add someone you trust', 'நம்பிக்கையானவரைச் சேர்')}>
        <form className="mt-3 flex flex-col gap-2.5" onSubmit={(e) => { e.preventDefault(); act({ action: 'add', ...form, phone: form.phone ? `+91${form.phone.replace(/\D/g, '')}` : null }, delivered) }}>
          <input required placeholder={t('Name (eg. Amma)', 'பெயர் (உதா. அம்மா)')} value={form.label} onChange={(e) => setForm({ ...form, label: e.target.value })}
            className="h-12 rounded-xl border-2 border-line px-3 outline-none" />
          <div className="flex h-12 items-center gap-2 rounded-xl border-2 border-line px-3">
            <span className="font-bold">+91</span>
            <input inputMode="numeric" placeholder={t('Mobile number', 'கைபேசி எண்')} value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value.replace(/[^\d ]/g, '').slice(0, 11) })}
              className="min-w-0 flex-1 outline-none" />
          </div>
          <select value={form.relation} onChange={(e) => setForm({ ...form, relation: e.target.value })} className="h-12 rounded-xl border-2 border-line px-2">
            {['mother', 'sister', 'friend', 'colleague', 'neighbour'].map((r) => <option key={r} value={r}>{r}</option>)}
          </select>
          <button type="submit" className="sp-btn-primary">{t('Continue', 'தொடர்')}</button>
        </form>
      </Confirm>
      <Confirm open={sheet?.kind === 'confirm'} busy={busy} onCancel={() => setSheet(null)}
        onConfirm={() => act({ ...sheet.body, confirmed: true }, delivered)}
        title={t(`Send this to ${sheet?.to}?`, `${sheet?.to}-க்கு அனுப்பவா?`)} body={<span className="italic">“{sheet?.preview}”</span>}
        confirmLabel={t('Yes, send', 'ஆம், அனுப்பு')} />
    </div>
  )
}
