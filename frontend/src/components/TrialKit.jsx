import { useState } from 'react'
import { ChevronDown } from 'lucide-react'
import { useT } from '@/lib/i18n'

const items = [
  ['kit', 'Pack shoes and training kit', 'காலணி மற்றும் பயிற்சி உடையை எடுத்து வை'],
  ['water', 'Fill my water bottle', 'தண்ணீர் பாட்டிலை நிரப்பு'],
  ['entry', 'Check entry details and ID', 'பதிவு விவரங்களையும் அடையாள அட்டையையும் சரிபார்'],
  ['trip', 'Check my route and return time', 'பாதை மற்றும் திரும்பும் நேரத்தைச் சரிபார்'],
]
const storageKey = 'avvai_trial_kit_v1'
function loadKit() {
  try {
    const saved = JSON.parse(sessionStorage.getItem(storageKey))
    return Array.isArray(saved) ? items.filter(([id]) => saved.includes(id)).map(([id]) => id) : []
  } catch { return [] }
}

export default function TrialKit() {
  const t = useT()
  const [checked, setChecked] = useState(loadKit)
  function update(next) {
    setChecked(next)
    try { sessionStorage.setItem(storageKey, JSON.stringify(next)) } catch { /* Still usable in memory. */ }
  }
  const summary = t(`${checked.length} of 4 ready`, `4 இல் ${checked.length} தயார்`)
  return <details className="trial-kit">
    <summary>
      <img src="/avvai/kit-shoes.webp" width="128" height="112" alt="" loading="lazy"/>
      <span className="kit-summary"><strong>{t('My trial-day kit', 'போட்டிக்கான தயாரிப்பு')}</strong>
        <small>{summary}</small>
        <span className="kit-meter" aria-hidden="true">{items.map(([id]) => <i key={id} className={checked.includes(id) ? 'packed' : ''}/>)}</span>
      </span><ChevronDown size={18} aria-hidden="true"/>
    </summary>
    <div className="kit-items">{items.map(([id, en, ta]) => <label key={id}>
      <input type="checkbox" checked={checked.includes(id)} onChange={e => update(e.target.checked ? [...checked, id] : checked.filter(x => x !== id))}/><span>{t(en, ta)}</span>
    </label>)}</div>
    <div className="kit-end"><small>{t('Saved in this tab', 'இந்தத் தாவலில் சேமிக்கப்படும்')}</small>
      <button type="button" disabled={!checked.length} onClick={() => update([])}>{t('Reset list','மீட்டமை')}</button></div>
  </details>
}
