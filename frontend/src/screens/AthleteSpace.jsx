import { useEffect, useState } from 'react'
import { Link, NavLink, useNavigate } from 'react-router-dom'
import { ArrowUpRight, Home, Compass, ClipboardList, Sparkles, UserRound } from 'lucide-react'
import { Avvai } from '@/components/Avvai'
import { useApp } from '@/lib/store'
import { supabase } from '@/lib/supabase'
import { request } from '@/lib/api'
import { readDemo, saveDemo } from '@/lib/veeramangai'
import '@fontsource/anton/400.css'
import './Veeramangai.css'
import './AthleteSpace.css'

export function AthleteNav() {
  return <nav className="athlete-nav" aria-label="Athlete navigation">{[
    ['/veeramangai', 'Home', Home], ['/veeramangai/features', 'Explore', Compass],
    ['/veeramangai/requests', 'Requests', ClipboardList], ['/veeramangai/agent', 'Avvai', Sparkles],
    ['/veeramangai/profile', 'Profile', UserRound],
  ].map(([path, title, Icon]) => <NavLink end key={path} to={path}><Icon size={20} /><span>{title}</span></NavLink>)}</nav>
}
export default function AthleteSpace({ view = 'home' }) {
  const { signedIn, me } = useApp()
  const [profile, setProfile] = useState(() => readDemo('profile', { name: '', sport: 'Athletics', district: 'Chennai' }))
  const [requests, setRequests] = useState(() => readDemo('requests', []))
  const [saved, setSaved] = useState(false)
  const [connectionError, setConnectionError] = useState('')
  useEffect(() => {
    let active = true
    const sync = async () => {
      if (!signedIn) { setProfile(readDemo('profile', { name: '', sport: 'Athletics', district: 'Chennai' })); setRequests(readDemo('requests', [])); return }
      try {
        const [workspace, catalog, savedRequests] = await Promise.all([
          request('/api/veeramangai/workspace'), request('/api/veeramangai/catalog'), request('/api/veeramangai/requests?limit=100')])
        if (!active) return
        const p = workspace.profile
        setProfile({ name: p?.display_name || '', sport: catalog.sports.find(s => s.id === p?.sport_id)?.name || 'Sport', district: catalog.districts.find(d => d.id === p?.district_id)?.name || '' })
        setRequests(savedRequests.items.map(r => ({ ...r, need: r.category.replaceAll('_', ' '), created: r.created_at })))
        setConnectionError('')
      } catch { if (active) { setRequests([]); setProfile({ name: '', sport: 'Sport', district: '' }); setConnectionError('Could not load your saved workspace. Refresh to try again.') } }
    }
    sync()
    window.addEventListener('vm-demo-update', sync)
    window.addEventListener('focus', sync)
    return () => { active = false; window.removeEventListener('vm-demo-update', sync); window.removeEventListener('focus', sync) }
  }, [signedIn])
  const name = profile.name || 'Athlete'
  const today = new Intl.DateTimeFormat('en-IN', { timeZone: 'Asia/Kolkata', weekday: 'long', day: 'numeric', month: 'long' }).format(new Date())
  return <div className="vm-app athlete-space"><header className="athlete-top"><Link to="/veeramangai" className="vm-brand">VEERAMANGAI<span>வீரமங்கை</span></Link><div><span className="vm-badge">{signedIn ? 'Signed in' : 'Demo workspace'}</span>{!signedIn && <Link to="/veeramangai/login">Log in <ArrowUpRight size={15} /></Link>}</div></header>
    <main className="athlete-main">{connectionError && <p role="alert">{connectionError}</p>}{signedIn && <section className="athlete-brief"><h2>Your saved workspace</h2><p>{profile.name || 'Complete your profile'} · {profile.sport} · {profile.district}</p><Link to="/veeramangai/requests">{requests.length} saved requests</Link>{requests.slice(0,3).map(r => <p key={r.id}>{r.need}: {r.status}</p>)}</section>}{view === 'home' ? <><section className="athlete-greeting"><div><p className="vm-eyebrow">{today.toUpperCase()}</p><h1>VANAKKAM, {name.toUpperCase()}.</h1><p>Your space. Your pace. Your next step.</p></div><Link to="/veeramangai/profile" className="athlete-avatar" aria-label="Edit your profile">{name[0].toUpperCase()}</Link></section>
      <section className="athlete-today"><div><p className="vm-eyebrow">TODAY, START WITH YOU</p><h2>HOW ARE YOU<br />SHOWING UP TODAY?</h2><p>A lighter session? A new opportunity? We’re here for your next step.</p><Link className="vm-pill" to="/veeramangai/support">Check in privately <ArrowUpRight size={17} /></Link></div><Avvai action="wave" size={220} /></section>
      <div className="athlete-dashboard"><section><div className="vm-section-head"><h2>Keep moving forward</h2><Link to="/veeramangai/features">Explore all <ArrowUpRight size={15} /></Link></div><div className="athlete-next-grid"><Link to="/veeramangai/opportunities"><p className="vm-eyebrow">FOR YOUR NEXT STEP</p><h3>Find a trial.<br />Make it yours.</h3><p>Explore {profile.sport.toLowerCase()} and other sports.</p><span>Sample opportunities <ArrowUpRight size={17} /></span></Link><Link to="/veeramangai/requests"><p className="vm-eyebrow">YOUR REQUESTS</p><h3>{requests.length ? `${requests.length} ${signedIn ? 'saved request' : 'draft'}${requests.length > 1 ? 's' : ''} to review.` : 'Room for\nsomething new.'}</h3><p>Funding, travel and private support in one place.</p><span>View your requests <ArrowUpRight size={17} /></span></Link></div></section>
      <aside className="athlete-brief"><p className="vm-eyebrow">YOUR DAILY BOARD</p><h3>What’s coming up?</h3><p>No verified live headlines or deadlines are connected yet.</p><Link to="/veeramangai/opportunities">Explore sample events <ArrowUpRight size={16} /></Link><hr /><h3>Approval updates</h3><p>{requests.length ? (signedIn ? `Latest request: ${requests[0].need} — ${requests[0].status}.` : 'Your drafts are ready to review. None have been submitted to a coordinator.') : 'No requests or approvals yet. Start whenever you’re ready.'}</p></aside></div>
      <section className="athlete-story"><div><p className="vm-eyebrow">HERITAGE THAT MOVES WITH YOU</p><h2>THEIR COURAGE.<br />YOUR OWN PATH.</h2><p>Four women’s stories inspire the ways we support your journey.</p><Link to="/veeramangai/features">Meet your four paths <ArrowUpRight size={17} /></Link></div><div className="athlete-story-art" role="img" aria-label="Original interpretations of four Tamil historical women" /></section>
    </> : view === 'requests' ? <><p className="vm-eyebrow">YOUR PERSONAL SPACE</p><h1>MY REQUESTS.</h1><p className="athlete-lead">See what you’ve prepared and what still needs a real response.</p>{!requests.length ? <section className="athlete-empty"><Avvai action="front" size={130} /><h2>No requests yet.</h2><p>Prepare a request for funding, travel or private coach support.</p><Link className="vm-pill" to="/veeramangai/features">Find the support you need <ArrowUpRight size={16} /></Link></section> : <div className="athlete-request-list">{requests.map(r => <article key={r.id}><span className="vm-badge">{r.status}</span><h2>{r.need}</h2><p>{r.kind} · {new Date(r.created).toLocaleDateString('en-IN')}</p>{r.note && <p>{r.note}</p>}<small>Stored in this browser session. No coordinator, sponsor or coach has received this.</small></article>)}</div>}</> : <><p className="vm-eyebrow">ABOUT YOU</p><h1>YOUR SPACE.</h1><form className="athlete-profile" onSubmit={e => { e.preventDefault(); saveDemo('profile', profile); setSaved(true) }}><label>What should we call you?<input value={profile.name} maxLength={50} onChange={e => setProfile({ ...profile, name: e.target.value })} autoComplete="given-name" /></label><label>Your sport<select value={profile.sport} onChange={e => setProfile({ ...profile, sport: e.target.value })}>{['Athletics', 'Football', 'Kabaddi', 'Badminton', 'Basketball', 'Other'].map(s => <option key={s}>{s}</option>)}</select></label><label>Your district<select value={profile.district} onChange={e => setProfile({ ...profile, district: e.target.value })}>{['Chennai', 'Madurai', 'Coimbatore', 'Sivaganga', 'Tiruchirappalli', 'Other'].map(s => <option key={s}>{s}</option>)}</select></label><p>These preferences stay in this browser session. Don’t enter private health details here.</p><button className="vm-primary">Save my preferences</button>{saved && <p role="status">Preferences saved for this session.</p>}</form></>}
    </main><AthleteNav /></div>
}

export function AthleteLogin() {
  const navigate = useNavigate()
  const { signedIn } = useApp()
  const [email, setEmail] = useState(''), [password, setPassword] = useState(''), [busy, setBusy] = useState(false), [error, setError] = useState(''), [signup, setSignup] = useState(false), [notice, setNotice] = useState('')
  useEffect(() => { if (signedIn) navigate('/veeramangai/profile', { replace: true }) }, [signedIn, navigate])
  async function submit(e) {
    e.preventDefault(); setError(''); setNotice('')
    if (!supabase) { setError('Account login is not configured. You can explore the demo.'); return }
    setBusy(true)
    try {
      const { data, error: authError } = signup ? await supabase.auth.signUp({ email, password }) : await supabase.auth.signInWithPassword({ email, password })
      if (authError) {
        const code = authError.code || ''
        setError(code === 'email_not_confirmed' ? 'Open the confirmation email first, then come back and log in.'
          : code.includes('rate') || authError.status === 429 ? 'Too many attempts. Please wait a minute before trying again.'
          : signup ? 'Could not create this account. Check the email and use a password with at least 8 characters.'
          : 'Email or password was not accepted. If this is your first visit, click “New here? Create an account” below. Your n8n or Supabase dashboard login does not create an app account.')
        return
      }
      setPassword('')
      if (data.session) navigate('/veeramangai/profile')
      else setNotice('Check your email to confirm your account, then sign in.')
    } catch { setError('Account service is unavailable. Please try later or explore the demo.') } finally { setBusy(false) }
  }
  return <div className="vm-app athlete-login"><section className="athlete-login-art"><Link to="/veeramangai" className="vm-brand">VEERAMANGAI</Link><h1>YOUR GAME.<br />YOUR WORLD.</h1><p>A space to grow, find support and take the next step.</p><Avvai action="wave" size={260} /></section><section className="athlete-login-form"><p className="vm-eyebrow">WELCOME TO YOUR SPACE</p><h2>{signup ? 'Join the journey.' : 'Good to have you here.'}</h2><form onSubmit={submit}><label>Email<input type="email" required autoComplete="email" value={email} onChange={e => setEmail(e.target.value)} /></label><label>Password<input type="password" required minLength={8} autoComplete={signup ? 'new-password' : 'current-password'} value={password} onChange={e => setPassword(e.target.value)} /></label>{error && <p role="alert">{error}</p>}{notice && <p role="status">{notice}</p>}<button className="vm-primary" disabled={busy}>{busy ? 'Please wait…' : signup ? 'Create account' : 'Log in'} <ArrowUpRight size={17} /></button></form><button className="athlete-switch" onClick={() => { setSignup(!signup); setError(''); setNotice('') }}>{signup ? 'Already registered? Log in' : 'New here? Create an account'}</button><Link to="/veeramangai">Explore in demo mode <ArrowUpRight size={16} /></Link><p>Your profile and submitted requests are saved to your Supabase account. Sample opportunities remain labelled.</p></section></div>
}
