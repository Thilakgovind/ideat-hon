import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { readDemo } from '@/lib/veeramangai'
import { request } from '@/lib/api'
import { useApp } from '@/lib/store'
import { AthleteNav } from './AthleteSpace'
import SafeMap from '@/components/SafeMap'
import './Veeramangai.css'
import './AthleteSpace.css'

const labels = { entry_fee: 'Entry fee', equipment: 'Equipment', travel: 'Travel support', lighter_session: 'A lighter session', rest: 'Rest', private_conversation: 'A private conversation' }
const emptyProfile = { display_name: '', district_id: '', sport_id: '', language: 'ta', email_updates: false }
const errorText = e => typeof e.message === 'string' && !e.message.includes('[object') ? e.message : 'Please check your details and try again.'

export function SupportRequestForm({ module }) {
  const [category, setCategory] = useState(''), [consent, setConsent] = useState(false)
  const [busy, setBusy] = useState(false), [result, setResult] = useState(null), [error, setError] = useState('')
  const event = useRef(crypto.randomUUID())
  const choices = module === 'funding' ? ['entry_fee', 'equipment'] : module === 'travel' ? ['travel'] : ['lighter_session', 'rest', 'private_conversation']
  async function submit(e) {
    e.preventDefault(); setBusy(true); setError('')
    try {
      setResult(await request('/api/veeramangai/requests', { method: 'POST', body: { event_id: event.current, category, consent_to_share: true } }))
    } catch (e) { setError(errorText(e)) } finally { setBusy(false) }
  }
  return <><form className="vm-form" onSubmit={submit}><h2>Request support</h2><p>Your selected need is shared only with the assigned coordinator. You do not need to give a medical reason.</p>
    <div className="vm-options">{choices.map(c => <button key={c} type="button" disabled={busy || !!result} aria-pressed={category === c} onClick={() => { setCategory(c); event.current = crypto.randomUUID() }}>{labels[c]}</button>)}</div>
    <label><input type="checkbox" checked={consent} disabled={busy || !!result} onChange={e => setConsent(e.target.checked)} /> I agree to share this selected need with the participating coordinator.</label>
    <p>Support depends on a real coordinator's response. A request does not guarantee funding, a booking or a place in an event.</p>
    {error && <p role="alert">{error}</p>}{result && <p role="status">Request {result.duplicate ? 'already saved' : 'submitted'}. You can follow the response in My requests.</p>}
    <button className="vm-primary" disabled={busy || !category || !consent || !!result}>{busy ? 'Saving…' : result ? 'Submitted' : 'Submit my request'}</button>
    <Link className="vm-text-link" to="/veeramangai/requests">My requests</Link>
  </form>{module === 'travel' && <section className="vm-form"><h2>Plan your Chennai journey</h2><div style={{ height: 280, position: 'relative', overflow: 'hidden', borderRadius: 16 }}><SafeMap center={[13.0827, 80.2707]} zoom={11} className="h-full w-full" fallback={<p>Map unavailable. You can still explore route options.</p>} /></div><p>This city map does not identify verified sports venues or confirmed companions.</p><Link className="vm-primary" to="/booking">Explore bus and metro routes</Link><p>Any checkout in the travel demo uses Razorpay test mode. Demo tickets are not valid for travel.</p></section>}</>
}

export default function SupportWorkspace({ view = 'requests' }) {
  const { signedIn } = useApp()
  const drafts = readDemo('requests', [])
  const [profile, setProfile] = useState(emptyProfile), [catalog, setCatalog] = useState({ districts: [], sports: [] })
  const [workspace, setWorkspace] = useState(null), [items, setItems] = useState([]), [next, setNext] = useState(null)
  const [error, setError] = useState(''), [notice, setNotice] = useState(''), [busy, setBusy] = useState(false)
  const events = useRef({})
  const coordinator = view === 'coordinator'
  const endpoint = coordinator ? '/api/veeramangai/coordinator/requests' : '/api/veeramangai/requests'
  async function load(offset = 0) {
    const data = await request(`${endpoint}?offset=${offset}&limit=25`)
    setItems(old => offset ? [...old, ...data.items] : data.items); setNext(data.next_offset)
  }
  useEffect(() => {
    if (!signedIn) { setItems([]); setWorkspace(null); setProfile(emptyProfile); return }
    let active = true
    setError(''); setNotice('')
    Promise.all([request('/api/veeramangai/workspace'), request('/api/veeramangai/catalog')]).then(([w, c]) => {
      if (!active) return
      setWorkspace(w); setProfile(w.profile || emptyProfile); setCatalog(c)
    }).catch(e => { if (active) setError(errorText(e)) })
    if (view !== 'profile') request(`${endpoint}?limit=25`).then(data => { if (active) { setItems(data.items); setNext(data.next_offset) } }).catch(e => { if (active) setError(errorText(e)) })
    return () => { active = false }
  }, [signedIn, view, endpoint])
  async function save(e) {
    e.preventDefault(); setError(''); setNotice(''); setBusy(true)
    try {
      await request('/api/veeramangai/profile', { method: 'PUT', body: { display_name: profile.display_name, district_id: profile.district_id || null, sport_id: profile.sport_id || null, language: profile.language, email_updates: profile.email_updates } })
      setNotice('Profile saved to your account.')
    } catch (e) { setError(errorText(e)) } finally { setBusy(false) }
  }
  async function update(row, status) {
    setBusy(true); setError('')
    const key = `${row.id}:${row.status}:${status}`
    events.current[key] ||= crypto.randomUUID()
    try {
      await request(`/api/veeramangai/requests/${row.id}/status`, { method: 'POST', body: { event_id: events.current[key], expected_status: row.status, status } })
      await load(); setNotice('Response saved. Email updates are queued only for people who opted in.')
    } catch (e) { setError(errorText(e)) } finally { setBusy(false) }
  }
  return <div className="vm-app athlete-space"><header className="athlete-top"><Link className="vm-brand" to="/veeramangai">VEERAMANGAI</Link><Link to="/veeramangai/profile">My profile</Link></header><main className="athlete-main">
    <h1>{view === 'profile' ? 'YOUR PROFILE.' : coordinator ? 'COORDINATOR DESK.' : 'MY REQUESTS.'}</h1>
    {!signedIn ? <section className="avvai-guest-workspace"><h2>{view === 'profile' ? 'Make this space yours.' : 'Your drafts, ready to review.'}</h2><p>Create an account to save a profile and submit requests to a participating coordinator.</p><Link className="vm-primary" to="/veeramangai/login">Log in or create an account</Link><p><Link to="/veeramangai/features">Continue exploring</Link></p>{view === 'requests' && <><p>Guest drafts stay in this browser session. They have not been submitted and are not automatically transferred to your account.</p><div className="athlete-request-list">{drafts.map(d=><article key={d.id}><span className="vm-badge">Draft · not submitted</span><h2>{d.need}</h2><p>{d.note}</p><Link to={`/veeramangai/${d.kind}`}>Review this support option</Link></article>)}</div>{!drafts.length && <p>No drafts yet. Explore funding, travel or private support to prepare one.</p>}</>}</section> : <>
      {error && <p role="alert">{error}</p>}{notice && <p role="status">{notice}</p>}{!workspace && !error && <p role="status">Loading your saved workspace…</p>}
      {workspace && !workspace.coordinator_configured && <p>A participating coordinator has not been connected yet. You can save your profile; submissions will be available after setup.</p>}
      {workspace?.is_coordinator && <p><Link to="/veeramangai/coordinator">Open coordinator desk</Link></p>}
      {view === 'profile' ? <form className="athlete-profile" onSubmit={save}>
        <label>What should we call you?<input required maxLength={50} value={profile.display_name} onChange={e => setProfile({ ...profile, display_name: e.target.value })} /></label>
        <label>Your district<select value={profile.district_id || ''} onChange={e => setProfile({ ...profile, district_id: e.target.value })}><option value="">Choose later</option>{catalog.districts.map(d => <option key={d.id} value={d.id}>{d.name}</option>)}</select></label>
        <label>Your sport<select value={profile.sport_id || ''} onChange={e => setProfile({ ...profile, sport_id: e.target.value })}><option value="">Choose later</option>{catalog.sports.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}</select></label>
        <label>Language<select value={profile.language} onChange={e => setProfile({ ...profile, language: e.target.value })}><option value="ta">தமிழ்</option><option value="en">English</option></select></label>
        <label><input type="checkbox" checked={profile.email_updates} onChange={e => setProfile({ ...profile, email_updates: e.target.checked })} /> Email me when a request changes.</label><p>Email contains a generic sign-in reminder, never the request's private details. You can turn updates off here.</p>
        <button className="vm-primary" disabled={busy || !workspace}>{busy ? 'Saving…' : 'Save profile'}</button>
      </form> : <><p>{coordinator ? 'Review requests assigned to you. Confirm arrangements with the athlete before approving.' : 'Follow your requests and the coordinator’s responses here.'}</p><button className="vm-primary" disabled={busy} onClick={() => load().catch(e => setError(errorText(e)))}>Refresh</button>
        <div className="athlete-request-list">{items.map(row => <article key={row.id}><span className="vm-badge">{row.status}</span><h2>{labels[row.category]}</h2><p>{new Date(row.created_at).toLocaleDateString('en-IN')}</p><small>Reference: {row.id}</small>
          {coordinator && row.status === 'submitted' && <button disabled={busy} onClick={() => update(row, 'reviewing')}>Start review</button>}
          {coordinator && row.status === 'reviewing' && <button disabled={busy} onClick={() => update(row, 'approved')}>Confirm support</button>}
          {coordinator && ['submitted', 'reviewing'].includes(row.status) && <button disabled={busy} onClick={() => update(row, 'declined')}>Decline</button>}
          {!coordinator && ['submitted', 'reviewing'].includes(row.status) && <button disabled={busy} onClick={() => update(row, 'cancelled')}>Cancel request</button>}
        </article>)}</div>{!items.length && !error && <p>No saved requests yet.</p>}{next !== null && <button onClick={() => load(next).catch(e => setError(errorText(e)))}>Load more</button>}
        <Link className="vm-text-link" to="/veeramangai/features">Find support</Link>
      </>}
    </>}
  </main><AthleteNav /></div>
}
