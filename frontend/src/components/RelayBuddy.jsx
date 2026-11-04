import { useEffect, useState } from 'react'
import { Avvai } from './Avvai'
import { useT } from '@/lib/i18n'
import { playCue } from '@/lib/sound'

export default function RelayBuddy() {
  const t = useT()
  const [turn, setTurn] = useState('ready')
  useEffect(() => {
    if (turn !== 'running' && turn !== 'dancing') return
    const next = turn === 'running' ? 'holding' : 'ready'
    const timer = setTimeout(() => setTurn(next), turn === 'running' ? 900 : 1250)
    return () => clearTimeout(timer)
  }, [turn])
  const holding = turn === 'holding'
  const moving = turn === 'running' || turn === 'dancing'
  const label = holding ? t('Take baton', 'திரும்பப் பெறு') : t('Pass baton', 'கோலைக் கொடு')
  return <div className={'relay-buddy relay-' + turn}>
    <span className="relay-runner"><Avvai action={turn === 'running' ? 'run' : turn === 'dancing' ? 'dance' : holding ? 'front' : 'wave'} size={106}/></span>
    <span className="relay-baton" aria-hidden="true"/>
    <button type="button" disabled={moving} onClick={() => { playCue(); setTurn(holding ? 'dancing' : 'running') }}>
      {turn === 'running' ? t('Catching…','பிடிக்கிறார்…') : turn === 'dancing' ? t('Your turn!','உங்கள் முறை!') : label}
    </button>
    <span className="sr-only" role="status">{holding ? t('Avvai caught the baton.', 'அவ்வை கோலைப் பிடித்தார்.') : ''}</span>
  </div>
}
