import { useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { request } from '@/lib/api'
import { useApp } from '@/lib/store'

export default function OfferApplication({ opportunity }) {
  const { signedIn } = useApp()
  const [draft, setDraft] = useState(null), [busy, setBusy] = useState(false)
  const [error, setError] = useState(''), [result, setResult] = useState(null)
  const [consent, setConsent] = useState(false), [notes, setNotes] = useState('')
  const [category, setCategory] = useState('entry_fee')
  const event = useRef(crypto.randomUUID())
  if (opportunity.source !== 'verified' || opportunity.status !== 'open') return <p>This listing is for exploration. Applications become available when the organizer and opening are verified.</p>
  if (!signedIn) return <Link className="vm-primary" to="/veeramangai/login">Sign in to prepare your application</Link>
  async function prepare() {
    setBusy(true); setError('')
    try {
      const response = await request('/api/veeramangai/offers/draft', { method: 'POST', body: { opportunity_id: opportunity.id, consent_to_prepare: true } })
      if (!response.claimable || !response.draft) throw new Error(response.reason || 'This opportunity is unavailable.')
      setDraft(response.draft)
    } catch (e) { setError(e.message) } finally { setBusy(false) }
  }
  async function submit(e) {
    e.preventDefault()
    if (!consent || busy || result) return
    setBusy(true); setError('')
    try { setResult(await request('/api/veeramangai/offers/claim', { method: 'POST', body: { event_id: event.current, opportunity_id: opportunity.id, category, consent_to_share: true, notes } })) }
    catch (e) { setError(e.message) } finally { setBusy(false) }
  }
  return <section aria-label="Prepare and review application">
    {!draft && <><p>Avvai can fill a request from your saved profile. You review it before sharing with the participating coordinator.</p><button className="vm-primary" disabled={busy} onClick={prepare}>{busy ? 'Preparing…' : 'Prepare from my profile'}</button></>}
    {draft && !result && <form onSubmit={submit} className="vm-form"><h3>Review your request</h3><p>Name: {draft.display_name}</p><p>District: {draft.district_id || 'Not provided'} · Sport: {draft.sport_id || 'Not provided'}</p><Link to="/veeramangai/profile">Edit profile details</Link><label>Support needed<select value={category} disabled={busy} onChange={e => setCategory(e.target.value)}><option value="entry_fee">Entry fee</option><option value="equipment">Equipment</option><option value="travel">Travel</option></select></label><label>Optional note<textarea maxLength={500} disabled={busy} value={notes} onChange={e => setNotes(e.target.value)} /></label><label><input type="checkbox" checked={consent} disabled={busy} onChange={e => setConsent(e.target.checked)} /> Share these profile details and my note with the participating coordinator.</label><p>This creates a support request in Avvai. The coordinator must arrange any application with the organizer.</p><button className="vm-primary" disabled={busy || !consent}>{busy ? 'Submitting…' : 'Confirm and submit request'}</button></form>}
    {error && <p role="alert">{error}</p>}
    {result && <p role="status">Your request was submitted. <Link to="/veeramangai/requests">Track its status</Link></p>}
  </section>
}
