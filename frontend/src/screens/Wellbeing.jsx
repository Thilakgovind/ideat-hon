import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { useT } from '@/lib/i18n'
import { AthleteNav } from './AthleteSpace'
import { playMood, stopMood } from '@/lib/sound'
import ExperienceControls from '@/components/ExperienceControls'
import './Veeramangai.css'
import './AthleteSpace.css'

export default function Wellbeing() {
  const t = useT()
  const [params] = useSearchParams()
  const [tab, setTab] = useState(params.get('tab') === 'body' ? 'body' : 'mind')
  const [agentResult, setAgentResult] = useState(null)
  const [agentBusy, setAgentBusy] = useState(false)
  const [agentError, setAgentError] = useState('')
  const [check, setCheck] = useState(null)
  const [period, setPeriod] = useState(null)
  const [energy, setEnergy] = useState(null)
  const [saved, setSaved] = useState(false)
  useEffect(() => {
    window.addEventListener('avvai-mute', stopMood)
    return () => { stopMood(); window.removeEventListener('avvai-mute', stopMood) }
  }, [])
  async function askAvvai() {
    const message = tab === 'mind' ? (check === 'stressed' ? 'I feel anxious and need mental health support.' : check === 'low' ? 'I feel low and need mental health support.' : 'I would like private mental health support.') : (period === 'yes' && energy === 'rest' ? 'My period cramps affect practice. How can I ask for rest?' : energy === 'rest' ? 'I am exhausted after training. How can I ask for rest?' : 'How can I discuss recovery and a lighter session with my coach?')
    setAgentBusy(true); setAgentError(''); setAgentResult(null)
    try {
      const response = await fetch('/api/veeramangai/assistant', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text:message,lang:document.documentElement.lang==='ta'?'ta':'en'}),signal:AbortSignal.timeout(30000)})
      if (!response.ok) throw new Error('Avvai is unavailable right now.')
      setAgentResult(await response.json())
    } catch { setAgentError('Avvai could not answer. Try again or use the support request link.') }
    finally { setAgentBusy(false) }
  }
  function save() {
    if (!check && !period && !energy) return
    sessionStorage.setItem('avvai_wellbeing_check', JSON.stringify({ check, period, energy, at: new Date().toISOString() }))
    setSaved(true)
  }
  function clear() { stopMood(); sessionStorage.removeItem('avvai_wellbeing_check'); setCheck(null); setPeriod(null); setEnergy(null); setSaved(false) }
  return <div className="vm-app wellbeing" data-atmosphere={tab === 'mind' ? check : energy}><header className="avvai-top"><Link className="avvai-wordmark" to="/veeramangai">avvai</Link><ExperienceControls/></header><main className="wellbeing-main"><p className="vm-eyebrow">{t('YOUR WELLBEING', 'உங்கள் நலம்')}</p><h1>{t('How are you, really?', 'நீங்கள் எப்படி இருக்கிறீர்கள்?')}</h1><p>{t('A quiet space to notice what you need. You decide what to share.', 'உங்களுக்கு என்ன தேவை என்பதை அறிய அமைதியான இடம். பகிர்வது உங்கள் விருப்பம்.')}</p><div className="wellbeing-tabs" role="tablist"><button role="tab" aria-selected={tab==='mind'} onClick={()=>setTab('mind')}>{t('Mind', 'மனம்')}</button><button role="tab" aria-selected={tab==='body'} onClick={()=>setTab('body')}>{t('Body', 'உடல்')}</button></div>{tab==='mind' ? <section role="tabpanel"><h2>{t('Check in with yourself', 'உங்களைப் பற்றி அறிந்துகொள்ளுங்கள்')}</h2><p>{t('No score. No judgement.', 'மதிப்பெண் இல்லை. தீர்ப்பும் இல்லை.')}</p><div className="wellbeing-choices">{[['steady','Steady','சீராக'],['stressed','Stressed','மன அழுத்தம்'],['low','Low','சோர்வு'],['unsure','Not sure','தெரியவில்லை']].map(([v,en,ta])=><button key={v} aria-pressed={check===v} onClick={()=>{playMood(v);setCheck(v);setSaved(false)}}>{t(en,ta)}</button>)}</div><div className="wellbeing-action"><p>{t('Want to talk it through?', 'பேச விரும்புகிறீர்களா?')}</p><Link to="/veeramangai/agent?topic=mental-wellbeing">{t('Talk to Avvai', 'அவ்வையுடன் பேசுக')}</Link><Link to="/veeramangai/support">{t('Ask for private support', 'தனிப்பட்ட உதவி கேளுங்கள்')}</Link></div><p className="wellbeing-note">{t('Avvai offers general support, not crisis care. If you may hurt yourself or are in immediate danger, call 112. For mental health support in India, Tele-MANAS: 14416.', 'அவ்வை அவசர சிகிச்சை அளிக்காது. உடனடி ஆபத்தில் 112 அழைக்கவும். மனநல உதவி: டெலி-மானஸ் 14416.')}</p></section> : <section role="tabpanel"><h2>{t('Listen to your body', 'உங்கள் உடலைக் கவனியுங்கள்')}</h2><p>{t('A period or training week can feel different for everyone. Track symptoms, not predicted hormones.', 'மாதவிடாய் மற்றும் பயிற்சி அனுபவம் ஒவ்வொருவருக்கும் மாறுபடும். உணர்வுகளைக் கவனியுங்கள்; ஹார்மோன் அளவை ஊகிக்க வேண்டாம்.')}</p><h3>{t('Period today?', 'இன்று மாதவிடாயா?')}</h3><div className="wellbeing-choices">{[['yes','Yes','ஆம்'],['no','No','இல்லை'],['skip','Prefer not to say','பகிர விருப்பமில்லை']].map(([v,en,ta])=><button key={v} aria-pressed={period===v} onClick={()=>{setPeriod(v);setSaved(false)}}>{t(en,ta)}</button>)}</div><h3>{t('Energy this week', 'இந்த வார ஆற்றல்')}</h3><div className="wellbeing-choices">{[['rest','Need rest','ஓய்வு தேவை'],['light','Lighter training','குறைந்த பயிற்சி'],['okay','Feeling okay','நலமாக உள்ளேன்']].map(([v,en,ta])=><button key={v} aria-pressed={energy===v} onClick={()=>{playMood(v);setEnergy(v);setSaved(false)}}>{t(en,ta)}</button>)}</div><div className="wellbeing-action"><Link to="/veeramangai/agent?topic=recovery">{t('Ask about recovery', 'மீட்பு பற்றி கேளுங்கள்')}</Link><Link to="/veeramangai/support">{t('Request rest privately', 'தனிப்பட்ட ஓய்வு கோரிக்கை')}</Link></div><p className="wellbeing-note">{t('This check-in cannot measure hormone levels or prescribe training from cycle phase. Missing periods, severe pain or unusually heavy bleeding deserve a clinician’s assessment.', 'இந்தப் பதிவு ஹார்மோன் அளவை அளவிடாது. மாதவிடாய் தவறுதல், கடுமையான வலி அல்லது அதிக இரத்தப்போக்கு இருந்தால் மருத்துவரை அணுகுங்கள்.')}</p></section>}<div className="wellbeing-guidance"><button disabled={agentBusy} onClick={askAvvai}>{agentBusy ? t('Avvai is thinking…', 'அவ்வை சிந்திக்கிறார்…') : t('Ask Avvai for a next step', 'அடுத்த படிக்கு அவ்வையிடம் கேளுங்கள்')}</button>{agentResult && <div role="status"><h2>{t('Avvai suggests', 'அவ்வை பரிந்துரை')}</h2><p>{agentResult.reply}</p>{agentResult.href && <Link to={agentResult.href}>{t('Open support option', 'உதவியைத் திறக்கவும்')}</Link>}</div>}{agentError && <p role="alert">{agentError}</p>}<p>{t('Only a short question based on your selection is sent when you press this button. Your saved check-in stays on this device.', 'இந்தப் பொத்தானை அழுத்தும்போது மட்டுமே சிறிய கேள்வி அனுப்பப்படும். உங்கள் பதிவு இந்தச் சாதனத்திலேயே இருக்கும்.')}</p></div><div className="wellbeing-save"><button onClick={save} disabled={!check&&!period&&!energy}>{t('Save on this device', 'இந்தச் சாதனத்தில் சேமிக்கவும்')}</button><button onClick={clear}>{t('Clear check-in', 'பதிவை நீக்குக')}</button>{saved&&<p role="status">{t('Saved in this browser session only. It was not sent to Avvai, a coach or a doctor.', 'இந்த உலாவியில் மட்டும் சேமிக்கப்பட்டது. அவ்வை, பயிற்சியாளர் அல்லது மருத்துவருக்கு அனுப்பப்படவில்லை.')}</p>}</div></main><AthleteNav/></div>
}
