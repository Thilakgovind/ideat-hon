import { useEffect, useRef, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ArrowUpRight, ArrowLeft, Send, Mic, Square, Volume2, X, Menu } from 'lucide-react'
import { Avvai } from '@/components/Avvai'
import { useRecorder, speak } from '@/lib/voice'
import { addDraft } from '@/lib/veeramangai'
import { useApp } from '@/lib/store'
import { SupportRequestForm } from './SupportWorkspace'
import { AthleteNav } from './AthleteSpace'
import '@fontsource/anton/400.css'
import './Veeramangai.css'

const MODULES = [
  { id: 'opportunities', name: 'Opportunities', tamil: 'வாய்ப்புகள்', queen: 'Velu Nachiyar', title: 'YOUR NEXT\nSTARTING LINE.', description: 'Find a place for your talent.', action: 'Explore opportunities', color: '#e5f641' },
  { id: 'funding', name: 'Funding', tamil: 'நிதி உதவி', queen: 'Sembiyan Mahadevi', title: 'BACK YOUR\nNEXT MOVE.', description: 'Turn a need into a support request.', action: 'Request support', color: '#ff867b' },
  { id: 'travel', name: 'Travel', tamil: 'பயணம்', queen: 'Rani Mangammal', title: 'GO FURTHER.\nTOGETHER.', description: 'Choose the support for your journey.', action: 'Plan a journey', color: '#174e39' },
  { id: 'support', name: 'Private support', tamil: 'தனிப்பட்ட உதவி', queen: 'Kundavai', title: 'YOUR VOICE.\nYOUR TERMS.', description: 'Ask for support, on your own terms.', action: 'Make a private request', color: '#ceb3ee' },
]
function Artwork({ index, className = '' }) { return <div className={`vm-art ${className}`}><img src="/veeramangai/queens.png" alt={`Artistic interpretation inspired by ${MODULES[index].queen}`} style={{ left: `${-index * 100}%` }} /></div> }
function Header({ tamil, setTamil }) {
  const [open, setOpen] = useState(false)
  return <header className="vm-header"><Link className="vm-brand" to="/veeramangai">VEERAMANGAI<span>வீரமங்கை</span></Link><nav className={open ? 'is-open' : ''}><Link to="/veeramangai">Home</Link><Link to="/veeramangai/features">Explore</Link><Link to="/veeramangai/requests">My requests</Link><Link to="/veeramangai/profile">My space</Link></nav><div className="vm-header-actions"><button onClick={() => setTamil(!tamil)}>{tamil ? 'English' : 'தமிழ்'}</button><Link className="vm-pill" to="/veeramangai/agent">Meet Avvai <ArrowUpRight size={16} /></Link><button className="vm-menu" aria-label="Toggle navigation" onClick={() => setOpen(!open)}><Menu /></button></div></header>
}
function DraftForm({ module, selected }) {
  const { signedIn } = useApp()
  const [choice, setChoice] = useState(''), [saved, setSaved] = useState(false), [note, setNote] = useState('')
  const choices = module === 'funding' ? ['Entry fee', 'Equipment', 'Training resources'] : module === 'travel' ? ['A trusted travel group', 'Travel cost support', 'Journey guidance'] : ['A lighter session', 'A rest', 'A private conversation']
  if (signedIn) return <SupportRequestForm key={module} module={module} />
  return <form className="vm-form" onSubmit={e => { e.preventDefault(); if (choice && !saved) { addDraft(module, choice, note); setSaved(true) } }}>
    <p className="vm-eyebrow">{selected ? `FOR: ${selected.name}` : 'YOUR CHOICE'}</p><h2>What would help?</h2>
    <div className="vm-options">{choices.map(c => <button type="button" aria-pressed={choice === c} key={c} onClick={() => { setChoice(c); setSaved(false) }}>{c}</button>)}</div>
    <label>Optional note <span>Keep personal details private.</span><textarea value={note} maxLength={300} onChange={e => setNote(e.target.value)} placeholder="Only share what you choose to share." /></label>
    <button className="vm-primary" disabled={!choice} type="submit">Prepare my request <ArrowUpRight size={18} /></button>
    {saved && <div role="status" className="vm-notice"><strong>Your demo request is ready.</strong><p>{choice}{note ? ` — ${note}` : ''}</p><p>Nothing was sent. A participating coordinator must confirm real support.</p></div>}
    <p className="vm-small">Demo only · Not sent to a coach, sponsor or travel provider.</p>{saved && <Link className="vm-text-link" to="/veeramangai/requests">View in my requests <ArrowUpRight size={16} /></Link>}
  </form>
}
export default function Veeramangai() {
  const { module } = useParams()
  const [tamil, setTamil] = useState(false), [filter, setFilter] = useState('All'), [selected, setSelected] = useState(null)
  const [catalog, setCatalog] = useState(null), [catalogError, setCatalogError] = useState('')
  const [visibleCount, setVisibleCount] = useState(24)
  useEffect(() => {
    const controller = new AbortController()
    fetch('/api/veeramangai/catalog', { signal: controller.signal })
      .then(r => { if (!r.ok) throw new Error('Catalog unavailable'); return r.json() })
      .then(setCatalog)
      .catch(e => { if (e.name !== 'AbortError') setCatalogError('Could not load opportunities. Please check the backend and reload.') })
    return () => controller.abort()
  }, [])
  const index = MODULES.findIndex(m => m.id === module), m = MODULES[index]
  useEffect(() => { window.scrollTo(0, 0); setSelected(null) }, [module])
  return <div className="vm-app"><Header tamil={tamil} setTamil={setTamil} />
    {!m ? <><section className="vm-intro"><p className="vm-eyebrow">TAMIL NADU · WOMEN IN SPORT</p><h1>{tamil ? 'ஒவ்வொரு பெண்ணும்.\nதனித்துவமான வலிமை.' : 'EVERY WOMAN.\nHER OWN POWER.'}</h1><div className="vm-intro-bottom"><p>{tamil ? 'உங்கள் வாய்ப்பைக் கண்டறியுங்கள். உதவியைக் கேளுங்கள்.' : 'Find your opportunity. Ask for support.\nChoose your way forward.'}</p><Link className="vm-text-link" to="/veeramangai/agent">Not sure where to start? Ask Avvai <ArrowUpRight size={18} /></Link></div></section>
      <section className="vm-grid" aria-label="Your four paths">{MODULES.map((item, i) => <Link className={`vm-feature vm-feature-${i}`} key={item.id} to={`/veeramangai/${item.id}`} style={{ '--feature-color': item.color }}><Artwork index={i} /><div className="vm-feature-copy"><span className="vm-eyebrow">0{i + 1} / INSPIRED BY {item.queen.toUpperCase()}</span><h2>{tamil ? item.tamil : item.name}</h2><p>{item.description}</p><div className="vm-card-action">{item.action}<ArrowUpRight size={20} /></div></div></Link>)}</section>
      <section className="vm-avvai-banner"><Avvai action="wave" size={160} /><div><p className="vm-eyebrow">YOUR COMPANION / AVVAI</p><h2>A LITTLE GUIDANCE.<br />A STRONGER NEXT STEP.</h2><p>Explore the app with Avvai in English or Tamil.</p></div><Link className="vm-pill" to="/veeramangai/agent">Talk to Avvai <ArrowUpRight size={18} /></Link></section>
    </> : <><section className={`vm-module vm-feature-${index}`} style={{ '--feature-color': m.color }}><div className="vm-module-copy"><Link to="/veeramangai" className="vm-text-link"><ArrowLeft size={16} /> All paths</Link><p className="vm-eyebrow">{m.name.toUpperCase()} / INSPIRED BY {m.queen.toUpperCase()}</p><h1>{m.title}</h1><p>{m.description}</p><span className="vm-small">Historical artwork is an artistic interpretation.</span></div><Artwork index={index} /></section><section className="vm-workspace">
      {module === 'opportunities' ? <><div className="vm-section-head"><h2>Find your next opportunity</h2><span className="vm-badge">Sample listings</span></div><div className="vm-filters">{['All', ...(catalog?.sports || []).map(s => s.name)].map(s => <button key={s} aria-pressed={filter === s} onClick={() => { setFilter(s); setVisibleCount(24) }}>{s}</button>)}</div>{!catalog && !catalogError && <p role="status">Loading opportunities…</p>}{catalogError && <p role="alert">{catalogError}</p>}{catalog && !catalog.opportunities.length && <p>No opportunities listed yet.</p>}<div className="vm-list">{(catalog?.opportunities || []).filter(o => filter === 'All' || o.sport === filter).slice(0, visibleCount).map(o => <button key={o.id} className="vm-list-card" onClick={() => setSelected(o)}><span className="vm-eyebrow">{o.district} · {o.sport}</span><h3>{o.name}</h3><p>{o.eligibility}</p><span className="vm-text-link">See opportunity <ArrowUpRight size={18} /></span></button>)}</div>{(catalog?.opportunities || []).filter(o => filter === 'All' || o.sport === filter).length > visibleCount && <button className="vm-primary" onClick={() => setVisibleCount(n => n + 24)}>Show more opportunities</button>}</> : <DraftForm key={module} module={module} />}
      <aside className="vm-guide-card"><Avvai action="front" size={100} /><h3>Let’s work out the next step.</h3><p>Avvai can explain how this feature works. You choose what happens next.</p><Link to={`/veeramangai/agent?topic=${module}`} className="vm-text-link">Ask Avvai <ArrowUpRight size={18} /></Link></aside>
    </section></>}
    {selected && <div className="vm-modal-backdrop" onClick={() => setSelected(null)}><section role="dialog" aria-modal="true" aria-labelledby="vm-opportunity-title" className="vm-modal" onClick={e => e.stopPropagation()}><button aria-label="Close" className="vm-close" onClick={() => setSelected(null)}><X /></button><span className="vm-badge">Sample opportunity · not open for applications</span><h2 id="vm-opportunity-title">{selected.name}</h2><p>{selected.district} · {selected.eligibility}</p><h3>Prepare your checklist</h3><p>{selected.needs}</p><p>No date or organizer is verified. This demonstration does not submit an application.</p><Link className="vm-primary" to="/veeramangai/funding">I want to attend — explore support <ArrowUpRight size={18} /></Link></section></div>}
    <footer className="vm-footer"><strong>VEERAMANGAI</strong><p>Illustrated heritage. Your own future.</p><span>Sample opportunities and request demonstrations are clearly labelled.</span><Link to="/avvai-studio">Avvai movement studio</Link></footer><AthleteNav />
  </div>
}

export function AvvaiAgentPage() {
  const [tamil, setTamil] = useState(false), [input, setInput] = useState(''), [messages, setMessages] = useState([]), [busy, setBusy] = useState(false), [error, setError] = useState('')
  const { recording, start, stop } = useRecorder()
  const end = useRef(null)
  useEffect(() => { end.current?.scrollIntoView({ block: 'nearest' }) }, [messages, busy])
  async function send(text) {
    if (!text.trim() || busy) return
    setInput(''); setError(''); setBusy(true); setMessages(ms => [...ms, { role: 'user', text }])
    try {
      const r = await fetch('/api/veeramangai/assistant', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ text, lang: tamil ? 'ta' : 'en' }) })
      if (!r.ok) throw new Error('Avvai could not reach the server. Start or restart the backend to enable the new agent endpoint.')
      const data = await r.json()
      setMessages(ms => [...ms, { role: 'assistant', text: data.reply, href: data.href, provider: data.provider, model: data.model, sources: data.sources, levels: data.answer_levels }])
    } catch (e) { setError(e.message) } finally { setBusy(false) }
  }
  async function voiceMessage() {
    if (!recording) { setError(''); await start(); return }
    const { blob } = await stop()
    if (!blob) { setError('Microphone unavailable. You can type your question below.'); return }
    setBusy(true); setError('')
    try {
      const form = new FormData(); form.append('audio', blob, 'speech.webm'); form.append('lang', tamil ? 'ta' : 'en')
      const r = await fetch('/api/veeramangai/voice', { method: 'POST', body: form })
      if (!r.ok) throw new Error('Voice is unavailable. Check the backend, or type your question.')
      const data = await r.json(); setMessages(ms => [...ms, { role: 'user', text: data.transcript }, { role: 'assistant', text: data.reply, href: data.href, provider: data.provider, model: data.model, sources: data.sources, levels: data.answer_levels }]);
      await speak({ audioBase64: data.audio_base64, text: data.reply, lang: tamil ? 'ta' : 'en' })
    } catch (e) { setError(e.message) } finally { setBusy(false) }
  }
  return <div className="vm-app"><Header tamil={tamil} setTamil={setTamil} /><main className="vm-agent-layout"><aside className="vm-agent-intro"><Link className="vm-text-link" to="/veeramangai"><ArrowLeft size={16} /> Your four paths</Link><p className="vm-eyebrow">MEET YOUR COMPANION</p><h1>{tamil ? 'வணக்கம்.\nநான் அவ்வை.' : 'VANAKKAM.\nI’M AVVAI.'}</h1><Avvai action={recording ? 'wave' : busy ? 'front' : 'wave'} size={280} /><p>I can help you explore opportunities, prepare support requests and understand your choices.</p><Link to="/avvai-studio" className="vm-text-link">See Avvai move <ArrowUpRight size={16} /></Link></aside><section className="vm-chat"><div className="vm-chat-heading"><div><strong>Avvai</strong><span>English / தமிழ் · Your next step</span></div><span className="vm-badge">You’re in control</span></div><div className="vm-messages" aria-live="polite">{!messages.length && <div className="vm-welcome"><h2>What would help you today?</h2><p>Choose a starting point or type your question.</p><div className="vm-options">{['Find a trial', 'Help with entry fees', 'Plan travel', 'Ask my coach for rest'].map(q => <button key={q} onClick={() => send(q)}>{q}<ArrowUpRight size={16} /></button>)}</div><p className="vm-small">No application, payment or message to a coach is sent from this chat.</p></div>}{messages.map((m, i) => <div className={`vm-message vm-${m.role}`} key={i}><p>{m.text}</p>{m.levels && <div className="vm-small"><p>{m.levels.next}</p><p>{m.levels.privacy}</p></div>}{m.sources?.length > 0 && <div className="vm-small">{m.sources.map(url => <a key={url} href={url} target="_blank" rel="noopener noreferrer">Read supporting guidance ↗ </a>)}</div>}{m.provider && <small className="vm-small">{m.provider === 'ollama' ? `Local Qwen · ${m.model || 'Ollama'}` : m.provider === 'support_policy' ? 'Support guidance · no health history saved' : m.provider}</small>}{m.href && <Link to={m.href}>Open this feature <ArrowUpRight size={14} /></Link>}{m.role === 'assistant' && <button aria-label="Read answer aloud" onClick={() => speak({ text: m.text, lang: tamil ? 'ta' : 'en' })}><Volume2 size={16} /></button>}</div>)}{busy && <p className="vm-thinking">Avvai is finding your next step…</p>}<div ref={end} /></div>{error && <p role="alert" className="vm-chat-error">{error}</p>}<form className="vm-composer" onSubmit={e => { e.preventDefault(); send(input) }}><input aria-label="Message Avvai" placeholder={tamil ? 'அவ்வையிடம் கேளுங்கள்…' : 'Ask Avvai…'} maxLength={1500} value={input} onChange={e => setInput(e.target.value)} /><button type="button" disabled={busy} aria-label={recording ? 'Stop recording' : 'Record voice question'} onClick={voiceMessage}>{recording ? <Square size={20} /> : <Mic size={20} />}</button><button aria-label="Send message" disabled={busy || !input.trim()}><Send size={20} /></button></form>{recording && <p className="vm-small">Recording — tap stop when finished.</p>}</section></main><AthleteNav /></div>
}
