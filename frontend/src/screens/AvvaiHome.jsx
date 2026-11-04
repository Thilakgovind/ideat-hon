import { useState } from 'react'
import { Link } from 'react-router-dom'
import { ArrowUpRight, Search, Trophy, Wallet, Bus, Heart, Users, FileCheck, Tag, UserRound, ClipboardList, Mic, MessageCircle } from 'lucide-react'
import { AthleteNav } from './AthleteSpace'
import RelayBuddy from '@/components/RelayBuddy'
import TrialKit from '@/components/TrialKit'
import { request } from '@/lib/api'
import { useT } from '@/lib/i18n'
import HeritagePaths from '@/components/HeritagePaths'
import AthleteHeader from '@/components/AthleteHeader'
import { playCue } from '@/lib/sound'
import './Veeramangai.css'
import './AthleteSpace.css'

const paths = [
  ['Opportunities', 'Trials, camps and your next starting line.', Trophy, 'opportunities', 'mint'],
  ['Funding & welfare', 'Explore entry fees and support requests.', Wallet, 'funding', 'sand'],
  ['Travel', 'Plan how you get there and back.', Bus, 'travel', 'sky'],
  ['Mental wellbeing', 'A private place to ask for support.', Heart, 'wellbeing?tab=mind', 'lilac'],
  ['Body & recovery', 'Discuss rest, periods and recovery with Avvai.', Heart, 'wellbeing?tab=body', 'rose'],
  ['Partner offers', 'Find verified sponsor and merchant offers.', Tag, 'directory?kind=partners', 'sand'],
  ['NSS community', 'Discover verified institution activities.', Users, 'directory?kind=nss', 'mint'],
  ['Documents', 'Open DigiLocker and prepare your documents.', FileCheck, 'directory?kind=documents', 'sky'],
  ['My requests', 'Follow your requests and responses.', ClipboardList, 'requests', 'lilac'],
  ['My profile', 'Keep your sport and district up to date.', UserRound, 'profile', 'rose'],
]

const tamilNames = ['வாய்ப்புகள்', 'நிதி உதவி', 'பயணம்', 'மனநலம்', 'உடலும் ஓய்வும்', 'சலுகைகள்', 'NSS சமூகம்', 'ஆவணங்கள்', 'என் கோரிக்கைகள்', 'என் சுயவிவரம்']
const groups = [
  ['All', 'அனைத்தும்', paths],
  ['Sport', 'விளையாட்டு', paths.slice(0, 3)],
  ['Wellbeing', 'நலம்', paths.slice(3, 5)],
  ['Community', 'சமூகம்', paths.slice(5, 8)],
  ['Account', 'கணக்கு', paths.slice(8)],
]

export default function AvvaiHome({ explore = false }) {
  const t = useT()
  const [query, setQuery] = useState('')
  const [group, setGroup] = useState(0)
  const visible = groups[group][2].filter(([name, description]) => {
    const index = paths.findIndex(p => p[0] === name)
    return [name, description, tamilNames[index]].join(' ').toLowerCase().includes(query.trim().toLowerCase())
  })
  function row(item) {
    const [name, , Icon, path, tint] = item
    return <Link key={path} className="field-row" to={'/veeramangai/' + path}>
      <span className={'field-icon ' + tint}><Icon size={20}/></span>
      <strong>{t(name, tamilNames[paths.indexOf(item)])}</strong><ArrowUpRight size={16}/>
    </Link>
  }
  return <div className="vm-app field-space">
    <AthleteHeader/>
    <main className={explore ? 'field-main' : 'field-main field-home-grid'}>
      {explore ? <><div className="explore-photo"><h1>{t('Explore support', 'உதவிகளைத் தேடுக')}</h1></div>
        <label className="field-search"><Search size={19}/><input type="search" aria-label={t('Search support','உதவி தேடுக')} placeholder={t('Search sport, travel, documents…','விளையாட்டு, பயணம், ஆவணங்கள்…')} value={query} onChange={e => setQuery(e.target.value)}/></label>
        <div className="field-filters">{groups.map(([en, ta], i) => <button key={en} aria-pressed={group === i} onClick={() => setGroup(i)}>{t(en,ta)}</button>)}</div>
        <div className="field-rows">{visible.map(row)}</div>{!visible.length && <p role="status">{t('No matches in this group.', 'இந்தப் பிரிவில் பொருத்தம் இல்லை.')} <button onClick={() => {setGroup(0); setQuery('')}}>{t('Clear filters','மீட்டமை')}</button></p>}
      </> : <>
        <section className="field-hero"><div className="field-track" aria-hidden="true"/><div className="field-hero-copy"><span>{t('AVVAI  /  ATHLETE SUPPORT','அவ்வை  /  விளையாட்டு உதவி')}</span><h1>{t('What’s on your mind?', 'என்ன பேசலாம்?')}</h1><div className="field-actions"><Link onClick={playCue} to="/veeramangai/voice"><Mic size={18}/>{t('Speak','பேசுக')}</Link><Link to="/veeramangai/agent"><MessageCircle size={17}/>{t('Type','எழுதுக')}</Link></div></div><RelayBuddy/></section>
        <section className="home-wellbeing"><h2>{t('Your wellbeing','உங்கள் நலம்')}</h2><div className="field-pair">
          <Link to="/veeramangai/wellbeing?tab=mind"><Heart size={26}/><strong>{t('Mind','மனம்')}</strong><small>{t('Mood & support','மனநிலை மற்றும் உதவி')}</small></Link>
          <Link to="/veeramangai/wellbeing?tab=body"><span className="field-cycle" aria-hidden="true"/><strong>{t('Body','உடல்')}</strong><small>{t('Periods & recovery','மாதவிடாய் மற்றும் ஓய்வு')}</small></Link>
        </div></section>
        <section className="home-sport"><div className="field-heading"><h2>{t('Your sport','உங்கள் விளையாட்டு')}</h2><Link to="/veeramangai/features">{t('Explore all','அனைத்தும்')} ↗</Link></div>
        <TrialKit/><div className="field-rows">{paths.slice(0,3).map(row)}</div></section>
      </>}
      <details className="field-history"><summary>{t('Four women behind Avvai','அவ்வையின் நான்கு முன்னோடிகள்')}</summary><HeritagePaths/></details>
      <footer className="field-footer"><Link to="/veeramangai/connections">{t('Account & messages','கணக்கு மற்றும் செய்திகள்')}</Link><Link to="/veeramangai/information?page=privacy">{t('Privacy','தனியுரிமை')}</Link><Link to="/veeramangai/information?page=terms">{t('Terms','விதிமுறைகள்')}</Link></footer>
    </main><AthleteNav/></div>
}

export function SupportDirectory() {
  const kind = new URLSearchParams(window.location.search).get('kind') || 'partners'
  const [query, setQuery] = useState(''), [result, setResult] = useState(null), [busy, setBusy] = useState(false), [error, setError] = useState('')
  const documents = kind === 'documents'
  const title = documents ? 'Your documents, together.' : kind === 'nss' ? 'Find your community.' : 'Support for your next step.'
  async function search(e) {
    e.preventDefault(); setBusy(true); setError(''); setResult(null)
    try { setResult(await request(documents ? '/api/veeramangai/digilocker/start' : `/api/veeramangai/${kind === 'nss' ? 'nss' : 'partners'}/match`, documents ? {} : { method: 'POST', body: { query, limit: 10 } })) }
    catch { setError('We couldn’t load this right now. Please try again.') } finally { setBusy(false) }
  }
  return <div className="vm-app avvai-home"><header className="avvai-top"><Link to="/veeramangai" className="avvai-wordmark">avvai</Link><Link to="/veeramangai">Back to your space</Link></header><main className="avvai-main avvai-directory"><p className="vm-eyebrow">{documents ? 'DOCUMENTS' : kind === 'nss' ? 'NSS COMMUNITY' : 'PARTNER OFFERS'}</p><h1>{title}</h1><p>{documents ? 'Continue to the official DigiLocker site. Automatic document access is awaiting partner approval.' : 'Search the connected catalogue. Verified results appear here when available.'}</p><form className="avvai-directory-search" onSubmit={search}>{!documents && <label className="avvai-search"><Search size={18} /><input aria-label="Search catalogue" maxLength={200} placeholder="Search by opportunity or support…" value={query} onChange={e => setQuery(e.target.value)} /></label>}<button className="vm-primary" disabled={busy}>{busy ? 'Checking…' : documents ? 'Check document connection' : 'Find matches'}<ArrowUpRight size={16} /></button></form>{error && <p role="alert">{error}</p>}{result && <section className="avvai-results" aria-live="polite">{documents ? <><h2>Continue with DigiLocker</h2><p>{result.message}</p><a className="vm-primary" href={result.provider_url} target="_blank" rel="noopener noreferrer">Open official DigiLocker <ArrowUpRight size={16} /></a></> : <><p>{result.notice}</p>{result.matches?.length ? result.matches.map(row => <article key={row.id}><h2>{row.partner_name || row.institution_name || row.name}</h2><p>{row.eligibility || row.activity_type}</p><span className="vm-badge">{row.verified ? 'Verified listing' : 'Sample listing'}</span></article>) : <><h2>No verified matches yet.</h2><p>You can still ask Avvai to help prepare a support request.</p><Link className="vm-primary" to="/veeramangai/agent">Talk to Avvai <ArrowUpRight size={16} /></Link></>}</>}</section>}</main><AthleteNav /></div>
}
