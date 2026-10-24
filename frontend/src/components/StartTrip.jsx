import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { toast } from 'sonner'

import Confirm from '@/components/Confirm'
import { api } from '@/lib/api'
import { useT } from '@/lib/i18n'
import { useApp } from '@/lib/store'

/**
 * Start a trip with Journey Watch. Messaging the circle needs an explicit yes,
 * so this always asks first (guardrail: confirm before messaging).
 *   const [startTrip, sheet] = useStartTrip(); startTrip({from, to, time, option_id})
 */
export function useStartTrip() {
  const t = useT()
  const navigate = useNavigate()
  const { setTripId } = useApp()
  const [payload, setPayload] = useState(null)
  const [busy, setBusy] = useState(false)

  async function go(notify) {
    setBusy(true)
    try {
      const res = await api.tripStart({ ...payload, confirmed: notify, notify_circle: notify })
      setTripId(res.trip.trip_id)
      if (notify) {
        toast(res.delivery.sent
          ? t(`Sent to ${res.delivery.sent} people in your circle`, `உங்கள் வட்டத்தில் ${res.delivery.sent} பேருக்கு அனுப்பப்பட்டது`)
          : t('Demo mode: circle message logged, not sent by SMS', 'டெமோ: செய்தி பதிவு, SMS அனுப்பப்படவில்லை'))
      }
      navigate(`/trip/${res.trip.trip_id}`)
    } catch (e) {
      toast.error(e.message)
    } finally {
      setBusy(false)
      setPayload(null)
    }
  }

  const sheet = (
    <Confirm
      open={!!payload}
      busy={busy}
      title={t('Share this trip with your circle?', 'இந்தப் பயணத்தை உங்கள் வட்டத்துடன் பகிரவா?')}
      body={t('Your circle gets your route and ETA by SMS. Location is shared only until you reach.',
        'உங்கள் வட்டம் வழி, நேரத்தை SMS-ல் பெறும். சேரும் வரை மட்டும் இருப்பிடம் பகிரப்படும்.')}
      confirmLabel={t('Yes, start & share', 'ஆம், தொடங்கு')}
      cancelLabel={t("Start, don't share", 'பகிராமல் தொடங்கு')}
      onConfirm={() => go(true)}
      onCancel={() => go(false)}
      onClose={() => setPayload(null)}
    />
  )
  return [setPayload, sheet]
}
