import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Mail, MessageCircle, UserRound, Bus, ArrowUpRight, LogOut } from 'lucide-react'
import { useApp } from '@/lib/store'
import { useT } from '@/lib/i18n'
import ExperienceControls from '@/components/ExperienceControls'
import { AthleteNav } from './AthleteSpace'
import './Veeramangai.css'
import './AthleteSpace.css'

export default function Connections() {
  const { signedIn, signOut, health } = useApp()
  const t = useT()
  const [error, setError] = useState(''), [busy, setBusy] = useState(false)
  const cards = [
    [UserRound, t('Your account', 'உங்கள் கணக்கு'), signedIn ? t('Signed in', 'உள்நுழைந்துள்ளீர்கள்') : t('Guest mode', 'விருந்தினர் பயன்முறை'), t('Save your profile and follow your requests with your own account.', 'உங்கள் சுயவிவரத்தைச் சேமித்து கோரிக்கைகளைப் பின்தொடருங்கள்.'), signedIn ? 'profile' : 'login', signedIn ? t('Edit profile', 'சுயவிவரத்தை மாற்றுக') : t('Log in or create account', 'உள்நுழைக அல்லது பதிவு செய்க')],
    [Mail, t('Email updates', 'மின்னஞ்சல் தகவல்கள்'), t('Opt-in required', 'உங்கள் ஒப்புதல் தேவை'), t('Choose email updates in your profile. Delivery also requires an enabled notification workflow; a saved preference is not proof of delivery.', 'சுயவிவரத்தில் மின்னஞ்சல் தகவல்களைத் தேர்வு செய்யலாம். அனுப்பும் சேவையும் செயல்பாட்டில் இருக்க வேண்டும்.'), 'profile', t('Manage email preferences', 'மின்னஞ்சல் விருப்பங்கள்')],
    [MessageCircle, t('SMS & keypad phones', 'SMS மற்றும் சாதாரண கைபேசி'), health?.services?.sms_provider ? `${health.services.sms_provider} · ${t('configured, delivery unverified', 'அமைக்கப்பட்டது; அனுப்புதல் சரிபார்க்கப்படவில்லை')}` : t('Connection not verified', 'இணைப்பு சரிபார்க்கப்படவில்லை'), t('Try the SMS-style journey flow. The simulator is not a real delivered text. Real messages need a working gateway and recipient consent.', 'SMS பயண உதவியை முயற்சிக்கவும். மாதிரி திரையில் வரும் பதில் உண்மையில் அனுப்பப்பட்ட குறுஞ்செய்தி அல்ல.'), '/demo', t('Open SMS demo', 'SMS மாதிரி திறக்க')],
    [Bus, t('Journey tools', 'பயண உதவிகள்'), t('Routes, circle & check-ins', 'வழிகள் மற்றும் பயணத் தகவல்கள்'), t('Plan a bus or metro trip, manage trusted contacts and check your journey. Sample places and test tickets stay labelled.', 'பேருந்து அல்லது மெட்ரோ பயணத்தைத் திட்டமிடுங்கள். மாதிரி இடங்களும் சோதனைச் சீட்டுகளும் குறிக்கப்பட்டுள்ளன.'), '/booking', t('Plan a trip', 'பயணம் திட்டமிடுக')],
  ]
  return <div className="vm-app avvai-home"><header className="avvai-top"><Link className="avvai-wordmark" to="/veeramangai">avvai<span>அவ்வை</span></Link><ExperienceControls /></header><main className="avvai-main"><p className="vm-eyebrow">{t('CONNECTED ON YOUR TERMS', 'உங்கள் விருப்பப்படி இணைந்திருங்கள்')}</p><h1>{t('A place for every update.', 'உங்கள் தகவல்களுக்கு ஓர் இடம்.')}</h1><p>{t('Manage how you sign in, stay informed and get around.', 'உங்கள் கணக்கு, தகவல்கள் மற்றும் பயணத்தை நிர்வகிக்கவும்.')}</p><div className="avvai-connection-grid">{cards.map(([Icon,title,status,description,path,label])=><section className="avvai-connection-card" key={title}><Icon size={26}/><span className="vm-badge">{status}</span><h2>{title}</h2><p>{description}</p><Link className="vm-text-link" to={path.startsWith('/') ? path : `/veeramangai/${path}`}>{label}<ArrowUpRight size={17}/></Link></section>)}</div><div className="avvai-shortcuts"><Link to="/demo">{t('Try CALL callback in the SMS flow', 'SMS வழியில் CALL வசதியை முயற்சிக்கவும்')} ↗</Link><Link to="/circle">{t('Trusted circle', 'நம்பிக்கையான தொடர்புகள்')} ↗</Link><Link to="/veeramangai/requests">{t('My requests', 'என் கோரிக்கைகள்')} ↗</Link><Link to="/veeramangai/directory?kind=documents">DigiLocker ↗</Link></div>{signedIn && <button className="vm-primary" disabled={busy} onClick={async()=>{setBusy(true);setError('');try{await signOut()}catch{setError(t('Could not sign out. Try again.', 'வெளியேற முடியவில்லை. மீண்டும் முயற்சிக்கவும்.'))}finally{setBusy(false)}}}><LogOut size={16}/>{t('Sign out', 'வெளியேறுக')}</button>}{error && <p role="alert">{error}</p>}</main><AthleteNav/></div>
}
