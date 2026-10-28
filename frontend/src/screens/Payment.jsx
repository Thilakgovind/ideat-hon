import { useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { toast } from 'sonner'

import { img } from '@/assets'
import Confirm from '@/components/Confirm'
import { BackButton, ErrorState, Icon, Loading, SampleLabel, SectionLabel } from '@/components/kit'
import { api } from '@/lib/api'
import { clock, useAsync } from '@/lib/hooks'
import { useT } from '@/lib/i18n'
import { cn } from '@/lib/utils'

const UPI = [
  ['gpay', 'GPay', 'G', 'bg-[#E8F0FE] text-metro'],
  ['phonepe', 'PhonePe', 'P', 'bg-[#F1E6FD] text-plum'],
  ['paytm', 'Paytm', '₱', 'bg-[#E3F5FD] text-[#0A78B8]'],
  ['upi', 'UPI ID', '@', 'bg-[#FFF1DE] text-[#C26A00]'],
]

function loadRazorpay() {
  if (window.Razorpay) return Promise.resolve(true)
  return new Promise((resolve) => {
    const s = document.createElement('script')
    s.src = 'https://checkout.razorpay.com/v1/checkout.js'
    s.onload = () => resolve(true)
    s.onerror = () => resolve(false)
    document.body.appendChild(s)
  })
}

export default function Payment() {
  const t = useT()
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const ref = { from: params.get('from'), to: params.get('to'), time: params.get('time'), option_id: params.get('option') }
  const [method, setMethod] = useState('gpay')
  const [asking, setAsking] = useState(false)
  const [busy, setBusy] = useState(false)
  // Unconfirmed order request = price summary only; nothing is created or charged.
  const quote = useAsync(() => api.payOrder(ref), [ref.from, ref.to, ref.time, ref.option_id])
  const s = quote.data?.summary
  const methodName = [...UPI, ['card', t('card', 'கார்டு')], ['travelcard', t('travel card', 'பயண அட்டை')]].find((m) => m[0] === method)?.[1]

  async function pay() {
    setBusy(true)
    try {
      const order = await api.payOrder({ ...ref, confirmed: true })
      if (order.ticket) return navigate(`/ticket/${order.ticket.ticket_id}`, { replace: true })
      if (order.mode === 'test' && (await loadRazorpay())) {
        const rzp = new window.Razorpay({
          key: order.checkout_key_id,
          order_id: order.order_id,
          amount: order.amount_paise,
          currency: 'INR',
          name: 'SafePath (test mode)',
          description: s.lines.map((l) => l.label).join(' + '),
          prefill: { method: ['card', 'travelcard'].includes(method) ? 'card' : 'upi' },
          theme: { color: '#5B1F96' },
          handler: async (r) => {
            const v = await api.payVerify({ order_id: r.razorpay_order_id, payment_id: r.razorpay_payment_id, signature: r.razorpay_signature })
            navigate(`/ticket/${v.ticket.ticket_id}`, { replace: true })
          },
          modal: { ondismiss: () => setBusy(false) },
        })
        rzp.open()
        return
      }
      // Demo mode: mock payment, clearly labelled on the ticket.
      const v = await api.payVerify({ order_id: order.order_id, payment_id: `pay_mock_${Date.now()}`, signature: 'mock' })
      toast(t('Demo payment: no money was taken', 'டெமோ: பணம் எடுக்கப்படவில்லை'))
      navigate(`/ticket/${v.ticket.ticket_id}`, { replace: true })
    } catch (e) {
      toast.error(e.message)
      setBusy(false)
    } finally {
      setAsking(false)
    }
  }

  return (
    <div className="flex min-h-dvh flex-col bg-cream">
      <div className="flex items-center gap-3 px-4 pt-[18px] pb-1.5">
        <BackButton />
        <h1 className="text-xl font-extrabold">{t('Pay for your trip', 'பயணத்துக்கு செலுத்துங்கள்')}</h1>
      </div>

      <div className="flex flex-1 flex-col gap-3.5 px-4 pt-1.5">
        {quote.loading ? <Loading rows={2} />
          : quote.error ? <ErrorState error={quote.error} onRetry={quote.reload} />
          : quote.data?.free ? (
            <ErrorState error={{ message: t('No payment needed. Free for women on ordinary (white-board) buses.', 'கட்டணம் தேவையில்லை. சாதாரண (வெள்ளை பலகை) பஸ்ஸில் பெண்களுக்கு இலவசம்.') }} />
          ) : s && (
            <>
              <div className="relative flex items-center gap-2 overflow-hidden rounded-3xl bg-[linear-gradient(140deg,#5B1F96,#8A2FC2)] p-[18px] text-white">
                <div className="flex flex-1 flex-col gap-2.5">
                  <span className="text-xs font-bold tracking-[0.1em] opacity-80">{t(`YOUR TRIP · TODAY ${clock(ref.time)}`, `உங்கள் பயணம் · இன்று ${clock(ref.time)}`)}</span>
                  <div className="flex flex-col gap-0.5">
                    <span className="text-[17px] font-extrabold">{s.from}</span>
                    <span className="text-[13px] opacity-80">{t(`to ${s.to}`, `${s.to} வரை`)}</span>
                  </div>
                  <div className="flex flex-col gap-1.5 text-sm">
                    {s.lines.map((l, i) => (
                      <div key={i} className="flex justify-between gap-2">
                        <span>{l.mode === 'bus' ? `${t('Bus', 'பஸ்')} ${l.label}` : `${l.label} · ${l.from} → ${l.to}`}</span>
                        <span className={cn('font-bold', l.fare_inr === 0 && 'font-extrabold text-[#9DF5DC]')}>{l.fare_inr === 0 ? t('Free on ordinary buses', 'சாதாரண பஸ்ஸில் இலவசம்') : `₹${l.fare_inr}`}</span>
                      </div>
                    ))}
                  </div>
                </div>
                <img src={img.featPay} alt="AVAL holding a coin" className="-mr-2.5 h-[126px] w-24 shrink-0 object-contain" />
              </div>

              <div className="flex items-baseline justify-between px-1">
                <span className="text-[15px] text-mute">{t('Total to pay', 'செலுத்த வேண்டியது')}</span>
                <span className="tabular text-[32px] font-extrabold">₹{s.amount_inr}</span>
              </div>

              <div className="flex flex-col gap-2.5">
                <SectionLabel>{t('Pay with UPI', 'UPI மூலம் செலுத்துங்கள்')}</SectionLabel>
                <div className="grid grid-cols-4 gap-2.5">
                  {UPI.map(([id, name, letter, cls]) => (
                    <button key={id} type="button" aria-pressed={method === id} onClick={() => setMethod(id)}
                      className={cn('flex h-[84px] flex-col items-center justify-center gap-1.5 rounded-[18px] bg-white text-xs font-bold text-ink',
                        method === id ? 'border-[2.5px] border-plum' : 'border-[1.5px] border-line')}>
                      <span className={cn('flex size-9 items-center justify-center rounded-xl font-black', cls)}>{letter}</span>{name}
                    </button>
                  ))}
                </div>
              </div>

              <div className="flex flex-col gap-2">
                <SectionLabel>{t('Other ways', 'மற்ற வழிகள்')}</SectionLabel>
                {[['card', t('Debit / credit card', 'டெபிட் / கிரெடிட் கார்டு'), <Icon.card key="c" stroke="#5B1F96" width={2} />],
                  ['travelcard', t('Metro travel card', 'மெட்ரோ பயண அட்டை'), <Icon.ticket key="t" stroke="#5B1F96" width={2} />]].map(([id, label, ico]) => (
                  <button key={id} type="button" aria-pressed={method === id} onClick={() => setMethod(id)}
                    className={cn('flex h-14 items-center gap-3 rounded-2xl bg-white px-4 text-[15px] font-semibold text-ink',
                      method === id ? 'border-[2.5px] border-plum' : 'border-[1.5px] border-line')}>
                    {ico}{label}
                  </button>
                ))}
              </div>
            </>
          )}
      </div>

      <div className="flex flex-col items-center gap-2.5 px-4 pt-3 pb-[22px]">
        <button type="button" disabled={!s || busy} onClick={() => setAsking(true)}
          className="sp-btn-primary min-h-[58px] w-full text-lg">
          {s ? t(`Pay ₹${s.amount_inr} with ${methodName}`, `₹${s.amount_inr} ${methodName} மூலம் செலுத்து`) : t('Pay', 'செலுத்து')}
        </button>
        <span className="flex items-center gap-1.5 text-xs text-mute">
          <Icon.lock stroke="#0FA596" size={14} width={2.4} />
          {t('Secured by Razorpay · test mode · the free bus leg costs nothing', 'Razorpay · சோதனை முறை · இலவச பஸ் பகுதிக்கு கட்டணம் இல்லை')}
        </span>
        <SampleLabel />
      </div>

      <Confirm open={asking} busy={busy} tone="pink" onCancel={() => setAsking(false)} onConfirm={pay}
        title={quote.data?.preview || ''}
        body={t('Razorpay TEST mode: no real money is taken in this V1 demo.', 'Razorpay சோதனை முறை: உண்மையான பணம் எடுக்கப்படாது.')}
        confirmLabel={t(`Yes, pay ₹${s?.amount_inr ?? ''}`, `ஆம், ₹${s?.amount_inr ?? ''} செலுத்து`)} />
    </div>
  )
}
