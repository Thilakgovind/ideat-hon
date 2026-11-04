import { useState } from 'react'
import { Languages, Volume2, VolumeX } from 'lucide-react'
import { useLang } from '@/lib/i18n'

import { playCue } from '@/lib/sound'

export default function ExperienceControls() {
  const { lang, setLang } = useLang()
  const [sound, setSound] = useState(() => localStorage.getItem('avvai_sound') === 'on')
  return <div className="avvai-controls"><button type="button" onClick={() => setLang(lang === 'ta' ? 'en' : 'ta')} aria-label="Switch language"><Languages size={17} />{lang === 'ta' ? 'English' : 'தமிழ்'}</button><button type="button" aria-label="Interface sound" aria-pressed={sound} onClick={() => { localStorage.setItem('avvai_sound', sound ? 'off' : 'on'); setSound(!sound); if (!sound) playCue(); else window.dispatchEvent(new Event('avvai-mute')) }}>{sound ? <Volume2 size={17} /> : <VolumeX size={17} />}<span>{lang === 'ta' ? 'ஒலி' : 'Sound'}</span></button></div>
}
