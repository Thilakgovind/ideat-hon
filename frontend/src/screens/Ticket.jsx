import { QRCodeSVG } from 'qrcode.react'
import { Link, useParams } from 'react-router-dom'

import Aval from '@/components/Aval'
import { BackButton, BottomNav, EmptyState, ErrorState, Loading, RouteBadge, SampleLabel } from '@/components/kit'
import { useStartTrip } from '@/components/StartTrip'
import { api } from '@/lib/api'
import { clock, toMin, useAsync, useNowIST } from '@/lib/hooks'
import { useT } from '@/lib/i18n'

const hhmm = (iso) => new Date(iso).toLocaleTimeString('en-GB', { timeZone: 'Asia/Kolkata', hour: '2-digit', minute: '2-digit' })

export default function Ticket() {
  const t = useT()
  const { id } = useParams()
  const now = useNowIST()
  const [startTrip, tripSheet] = useStartTrip()
  const res = useAsync(() => api.ticket(id), [id])
  const tk = res.data?.ticket
  const paidLine = tk?.lines.find((l) => l.fare_inr > 0) || tk?.lines[0]
  const next = useAsync(
    () => (paidLine && paidLine.mode !== 'bus' ? api.routes({ from: paidLine.from, to: paidLine.to, mode: paidLine.mode }) : Promise.resolve(null)),
    [paidLine?.from, paidLine?.to, paidLine?.mode],
  )
  const nextAt = next.data?.options?.[0]?.next?.[0]
  const nextIn = nextAt != null ? toMin(nextAt) - now.minutes : null
  const coach = tk?.women_coach ? (/front/i.test(tk.women_coach) ? t('Front', 'முன்') : /middle/i.test(tk.women_coach) ? t('Middle', 'நடு') : tk.women_coach) : '—'

  return (
    <div className="flex min-h-dvh flex-col bg-[linear-gradient(180deg,#FF4F8B_0%,#FF7AA6_38%,#FFF7EC_38%)]">
      <div className="flex items-center justify-between px-4 pt-[18px]">
        <BackButton to="/home" icon="close" light />
        <span className="text-[15px] font-bold text-white">
          {tk ? t(`Paid ₹${tk.amount_inr} · ${clock(hhmm(tk.issued_at), true)}`, `₹${tk.amount_inr} செலுத்தப்பட்டது · ${clock(hhmm(tk.issued_at), true)}`) : ''}
        </span>
        <span className="w-11" />
      </div>

      <div className="flex items-center gap-1 px-5">
        <Aval pose="cheer" className="h-36 w-[110px]" label="AVAL cheering" />
        <div className="flex flex-col gap-1 text-white">
          <span className="text-[26px] leading-[1.1] font-extrabold">{t("You're all set!", 'எல்லாம் தயார்!')}</span>
          <span className="font-tamil text-[15px] opacity-95">டிக்கெட் தயார்</span>
        </div>
      </div>

      {res.loading ? <Loading rows={2} className="mx-[18px]" />
        : res.error ? <ErrorState error={res.error} onRetry={res.reload} className="mx-[18px]" />
        : tk && (
          <div className="mx-[18px] flex flex-col overflow-hidden rounded-[26px] bg-white shadow-[0_16px_40px_rgba(91,31,150,0.18)]">
            <div className="flex flex-col gap-3 px-[18px] pt-4 pb-3">
              <div className="flex items-center justify-between">
                <span className={`rounded-lg px-2.5 py-1 text-[13px] font-extrabold text-white ${paidLine.mode === 'metro' ? 'bg-metro' : paidLine.mode === 'train' ? 'bg-train' : 'bg-pink'}`}>
                  {paidLine.label.toUpperCase()} · {tk.payment_mode === 'test' ? t('test ticket', 'சோதனை டிக்கெட்') : t('sample ticket', 'மாதிரி டிக்கெட்')}
                </span>
                <span className="text-[13px] font-bold text-teal-dark">{t(`Valid till ${clock(tk.valid_until, true)}`, `${clock(tk.valid_until)} வரை`)}</span>
              </div>
              <div className="flex items-center gap-2.5">
                <div className="flex flex-1 flex-col"><span className="text-[11px] font-semibold text-mute">{t('FROM', 'இருந்து')}</span><span className="text-[17px] font-extrabold">{paidLine.from}</span></div>
                <svg width="28" height="20" viewBox="0 0 28 20" fill="none" stroke="#FF4F8B" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M2 10h22M18 4l6 6-6 6" /></svg>
                <div className="flex flex-1 flex-col items-end"><span className="text-[11px] font-semibold text-mute">{t('TO', 'வரை')}</span><span className="text-right text-[17px] font-extrabold">{paidLine.to}</span></div>
              </div>
            </div>
            <div className="relative mx-[18px] h-0 border-t-2 border-dashed border-line">
              <span className="absolute -top-[13px] -left-8 size-6 rounded-full bg-cream" />
              <span className="absolute -top-[13px] -right-8 size-6 rounded-full bg-cream" />
            </div>
            <div className="flex flex-col items-center gap-2.5 px-[18px] pt-3.5 pb-4">
              <div className="rounded-2xl border-2 border-[#FFE1EC] p-2.5">
                <QRCodeSVG value={tk.qr_data} size={180} fgColor="#24132F" level="M" title="Ticket QR code" />
              </div>
              <span className="text-[13px] font-bold tracking-[0.12em] text-mute">{tk.ticket_id}</span>
              <div className="grid w-full grid-cols-3 gap-2">
                {[[t('Platform', 'நடைமேடை'), tk.platform || '—'], [t("Women's coach", 'பெண்கள் பெட்டி'), coach],
                  [paidLine.mode === 'bus' ? t('Valid', 'செல்லும்') : t('Next train', 'அடுத்த ரயில்'), paidLine.mode === 'bus' ? '2 h' : nextIn != null && nextIn >= 0 ? `${nextIn} min` : '—']].map(([k, v]) => (
                  <div key={k} className="flex flex-col items-center rounded-xl bg-cream p-2"><span className="text-[11px] text-mute">{k}</span><span className="text-base font-extrabold">{v}</span></div>
                ))}
              </div>
              <span className="text-center text-[11px] font-bold text-[#B3122A]">{t(tk.label, 'சோதனை டிக்கெட் - பயணத்துக்கு செல்லாது')}</span>
            </div>
          </div>
        )}

      <div className="mt-auto grid grid-cols-2 gap-2.5 px-4 pt-3 pb-[22px]">
        <Link to="/circle" className="flex h-[54px] items-center justify-center rounded-2xl border-2 border-plum bg-white text-[15px] font-extrabold text-plum no-underline">
          {t('Share with Amma', 'அம்மாவுடன் பகிர்')}
        </Link>
        <button type="button" disabled={!tk?.option_id}
          onClick={() => startTrip({ from: tk.from, to: tk.to, time: tk.trip_time, option_id: tk.option_id })}
          className="h-[54px] rounded-2xl bg-teal text-[15px] font-extrabold text-white disabled:opacity-50">
          {t('Start trip', 'பயணம் தொடங்கு')}
        </button>
      </div>
      {tripSheet}
    </div>
  )
}

export function Tickets() {
  const t = useT()
  const res = useAsync(() => api.tickets(), [])
  return (
    <div className="flex min-h-dvh flex-col bg-cream">
      <div className="flex items-center gap-3 px-4 pt-[18px] pb-2.5">
        <BackButton to="/home" />
        <h1 className="text-xl font-extrabold">{t('Your tickets', 'உங்கள் டிக்கெட்டுகள்')}</h1>
      </div>
      <div className="flex flex-1 flex-col gap-2.5 px-4">
        {res.loading ? <Loading /> : res.error ? <ErrorState error={res.error} onRetry={res.reload} />
          : res.data.tickets.length === 0 ? (
            <EmptyState title={t('No tickets yet', 'டிக்கெட் இல்லை')} hint={t('Free buses need no ticket. Metro and train tickets show here.', 'இலவச பஸ்ஸுக்கு டிக்கெட் தேவையில்லை.')} />
          ) : res.data.tickets.map((tk) => (
            <Link key={tk.ticket_id} to={`/ticket/${tk.ticket_id}`} className="flex items-center justify-between rounded-[18px] border-[1.5px] border-line bg-white px-3.5 py-3 text-ink no-underline">
              <div className="flex flex-col gap-1">
                <div className="flex gap-1.5">{tk.lines.map((l, i) => <RouteBadge key={i} label={l.label} mode={l.mode} size="sm" />)}</div>
                <span className="text-sm font-bold">{tk.from} → {tk.to}</span>
                <span className="text-xs text-mute">{tk.ticket_id} · {t(`valid till ${clock(tk.valid_until)}`, `${clock(tk.valid_until)} வரை`)}</span>
              </div>
              <span className="text-lg font-extrabold">₹{tk.amount_inr}</span>
            </Link>
          ))}
        <SampleLabel />
      </div>
      <BottomNav />
    </div>
  )
}
