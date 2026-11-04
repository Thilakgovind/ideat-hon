import { Link } from 'react-router-dom'
import { UserRound } from 'lucide-react'
import { useApp } from '@/lib/store'
import { useT } from '@/lib/i18n'
import ExperienceControls from './ExperienceControls'

export default function AthleteHeader() {
  const { signedIn } = useApp()
  const t = useT()
  return (
    <header className="field-header"><Link className="field-logo" to="/veeramangai">avvai<span>அவ்வை</span></Link><ExperienceControls/>
      <Link className="field-account" aria-label={signedIn ? t('Profile','சுயவிவரம்') : t('Log in','உள்நுழைக')} to={signedIn ? '/veeramangai/profile' : '/veeramangai/login'}><UserRound size={19}/></Link>
    </header>
  )
}
