import { useState } from 'react'
import { Link } from 'react-router-dom'
import { ArrowLeft, Mic, Square, Volume2 } from 'lucide-react'
import { Avvai } from '@/components/Avvai'
import { useLang, useT } from '@/lib/i18n'
import { useRecorder, speak } from '@/lib/voice'
import { AthleteNav } from './AthleteSpace'
import AthleteHeader from '@/components/AthleteHeader'
import './Veeramangai.css'
import './AthleteSpace.css'

export default function AvvaiVoice() {
  const t=useT(), {lang}=useLang()
  const {recording,start,stop}=useRecorder({requireAudio:true})
  const [busy,setBusy]=useState(false), [answer,setAnswer]=useState(null), [error,setError]=useState('')
  async function toggle(){
    if(busy) return
    if(!recording){
      setError('');setAnswer(null);setBusy(true)
      try {
        if(!await start()) setError(t('Microphone unavailable. Allow microphone access or use Text chat.', 'மைக்ரோஃபோனை அனுமதிக்கவும் அல்லது எழுத்து உரையாடலைத் தேர்ந்தெடுக்கவும்.'))
      } finally {setBusy(false)}
      return
    }
    const {blob}=await stop()
    if(!blob){setError(t('Microphone unavailable. Check browser permission and try again.','மைக்ரோஃபோன் அனுமதியைச் சரிபார்த்து மீண்டும் முயலுங்கள்.'));return}
    setBusy(true);setError('')
    try{
      const form=new FormData();form.append('audio',blob,'speech.webm');form.append('lang',lang)
      const response=await fetch('/api/veeramangai/voice',{method:'POST',body:form,signal:AbortSignal.timeout(60000)})
      if(!response.ok)throw new Error('Voice service unavailable')
      const result=await response.json();setAnswer(result)
      await speak({audioBase64:result.audio_base64,text:result.reply,lang})
    }catch{setError(t('Voice could not answer. Try again or type to Avvai.','குரல் பதில் கிடைக்கவில்லை. மீண்டும் முயலுங்கள் அல்லது எழுதுங்கள்.'))}finally{setBusy(false)}
  }
  return <div className="vm-app avvai-voice"><AthleteHeader/><main className="voice-main"><Link className="voice-back" to="/veeramangai/agent"><ArrowLeft size={18}/>{t('Text chat','எழுத்து உரையாடல்')}</Link><div className="voice-stage"><p className="vm-eyebrow">{t('SPEAK WITH AVVAI','அவ்வையுடன் பேசுங்கள்')}</p><h1>{recording?t('I’m listening','நான் கேட்கிறேன்'):busy?t('One moment…','ஒரு நிமிடம்…'):t('Tell me what’s on your mind.','உங்கள் மனதில் உள்ளதைச் சொல்லுங்கள்.')}</h1><div className={`voice-character ${recording?'is-listening':''} ${busy?'is-thinking':''}`}><span className="voice-ring"/><span className="voice-ring"/><Avvai action={recording?'dance':busy?'front':'wave'} size={190}/></div><button className="voice-record" onClick={toggle} disabled={busy} aria-label={recording?t('Stop recording','பதிவை நிறுத்துக'):t('Start recording','பதிவைத் தொடங்கு')}>{recording?<Square size={28}/>:<Mic size={32}/>}</button><p className="voice-hint">{recording?t('Tap to finish','முடிக்க அழுத்துங்கள்'):t('Tap to speak in Tamil, Tanglish or English','தமிழ், தங்கிலீஷ் அல்லது ஆங்கிலத்தில் பேசுங்கள்')}</p></div>{error&&<p className="voice-error" role="alert">{error}</p>}{answer&&<section className="voice-answer" aria-live="polite"><p className="vm-eyebrow">{t('I HEARD','நான் கேட்டது')}</p><p>{answer.transcript}</p><p className="vm-eyebrow">{t('AVVAI SAYS','அவ்வை சொல்வது')}</p><h2>{answer.reply}</h2><button onClick={()=>speak({audioBase64:answer.audio_base64,text:answer.reply,lang})}><Volume2 size={18}/>{t('Hear again','மீண்டும் கேட்க')}</button>{answer.href&&<Link to={answer.href}>{t('Open this support option','உதவியைத் திறக்கவும்')} →</Link>}</section>}</main><AthleteNav/></div>
}
