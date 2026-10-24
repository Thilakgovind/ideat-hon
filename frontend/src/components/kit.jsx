import { Link, NavLink, useNavigate } from 'react-router-dom'

import { img } from '@/assets'
import { Skeleton } from '@/components/ui/skeleton'
import { useLang, useT } from '@/lib/i18n'
import { cn } from '@/lib/utils'

/* ---------- icons (paths copied from the design HTML) ---------- */
const I = ({ d, size = 22, stroke = 'currentColor', width = 2.2, children, className }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={stroke} strokeWidth={width}
    strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" className={className}>
    {d ? <path d={d} /> : children}
  </svg>
)
export const Icon = {
  back: (p) => <I d="M15 18l-6-6 6-6" {...p} />,
  close: (p) => <I d="M6 6l12 12M18 6L6 18" width={2.4} {...p} />,
  chevron: (p) => <I d="M9 6l6 6-6 6" size={18} {...p} />,
  arrow: (p) => <I d="M5 12h14M13 6l6 6-6 6" width={2.4} {...p} />,
  search: (p) => <I {...p}><circle cx="11" cy="11" r="7" /><path d="M20 20l-4-4" /></I>,
  mic: (p) => <I {...p}><rect x="9" y="3" width="6" height="11" rx="3" /><path d="M5 11a7 7 0 0 0 14 0M12 18v3" /></I>,
  shield: (p) => <I {...p}><path d="M12 3l8 3v6c0 4.5-3.4 8-8 9-4.6-1-8-4.5-8-9V6z" /><path d="M8.5 12l2.5 2.5 4.5-5" /></I>,
  pin: (p) => <I {...p}><path d="M12 21s-7-6.2-7-11a7 7 0 0 1 14 0c0 4.8-7 11-7 11z" /><circle cx="12" cy="10" r="2.5" /></I>,
  home: (p) => <I {...p}><path d="M3 11l9-7 9 7v9H3z" /><path d="M10 20v-6h4v6" /></I>,
  people: (p) => <I {...p}><circle cx="9" cy="8" r="3" /><circle cx="17" cy="9" r="2.5" /><path d="M3 20c0-3.3 2.7-6 6-6s6 2.7 6 6M15 15c3 0 6 2 6 5" /></I>,
  ticket: (p) => <I {...p}><rect x="3" y="5" width="18" height="14" rx="3" /><path d="M3 10h18M7 15h4" /></I>,
  swap: (p) => <I d="M7 4v16M3 8l4-4 4 4M17 20V4M13 16l4 4 4-4" {...p} />,
  phone: (p) => <I d="M5 4h4l2 5-2.5 1.5a11 11 0 0 0 5 5L15 13l5 2v4a2 2 0 0 1-2 2A16 16 0 0 1 3 6a2 2 0 0 1 2-2" {...p} />,
  message: (p) => <I d="M4 5h16v11H8l-4 4z" {...p} />,
  plus: (p) => <I d="M12 5v14M5 12h14" width={2.4} {...p} />,
  share: (p) => <I d="M12 3v12M7 8l5-5 5 5M5 14v6h14v-6" {...p} />,
  save: (p) => <I d="M6 3h12v18l-6-4-6 4z" {...p} />,
  nav: (p) => <I d="M3 11l18-8-8 18-2-8z" {...p} />,
  warn: (p) => <I d="M12 9v4M12 17h.01M10.3 3.9L2 18a2 2 0 0 0 1.7 3h16.6a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z" {...p} />,
  lock: (p) => <I {...p}><rect x="5" y="11" width="14" height="10" rx="2" /><path d="M8 11V8a4 4 0 0 1 8 0v3" /></I>,
  card: (p) => <I {...p}><rect x="3" y="5" width="18" height="14" rx="3" /><path d="M3 10h18" /></I>,
  up: (p) => <I d="M12 3v18M5 10l7-7 7 7" {...p} />,
}

/* ---------- layout ---------- */
export function Screen({ className, children, style }) {
  return (
    <div className={cn('relative flex min-h-dvh flex-col overflow-x-hidden bg-cream', className)} style={style}>
      {children}
    </div>
  )
}

export function BackButton({ to, className, light = false, icon = 'back', label }) {
  const navigate = useNavigate()
  const t = useT()
  const Ico = Icon[icon]
  return (
    <button
      type="button"
      aria-label={label || t(icon === 'close' ? 'Close' : 'Back', icon === 'close' ? 'மூடு' : 'பின்செல்')}
      onClick={() => (to ? navigate(to) : window.history.length > 1 ? navigate(-1) : navigate('/home'))}
      className={cn('flex size-11 shrink-0 items-center justify-center rounded-full bg-white', light && 'bg-white/25', className)}
    >
      <Ico stroke={light ? '#FFFFFF' : '#24132F'} size={icon === 'close' ? 20 : 22} />
    </button>
  )
}

export function LangToggle({ className, dark = false }) {
  const { lang, setLang } = useLang()
  const btn = (code, label) => (
    <button
      type="button"
      onClick={() => setLang(code)}
      aria-pressed={lang === code}
      className={cn(
        'h-9 rounded-full px-2.5 text-[13px] font-bold',
        lang === code ? 'bg-plum-deep text-white' : dark ? 'text-white' : 'text-ink',
        code === 'ta' && 'font-tamil',
      )}
    >
      {label}
    </button>
  )
  return (
    <div className={cn('flex gap-0.5 rounded-full p-1', dark ? 'bg-white/15' : 'bg-white', className)}>
      {btn('ta', 'தமிழ்')}
      {btn('en', 'EN')}
    </div>
  )
}

export function BottomNav({ className }) {
  const t = useT()
  const item = (to, label, ico, end) => (
    <NavLink
      to={to}
      end={end}
      className={({ isActive }) =>
        cn('flex min-h-12 flex-col items-center justify-center gap-0.5 text-[11px]',
          isActive ? 'font-extrabold text-plum' : 'font-semibold text-mute')
      }
    >
      {ico}
      {label}
    </NavLink>
  )
  return (
    <nav className={cn('sticky bottom-0 z-30 grid grid-cols-5 border-t border-line bg-white px-1 pt-2 pb-[18px]', className)} aria-label="Main">
      {item('/home', t('Home', 'முகப்பு'), <Icon.home />)}
      {item('/nearby', t('Route', 'வழி'), <Icon.pin width={2} />)}
      <NavLink to="/aval" className={({ isActive }) => cn('flex min-h-12 flex-col items-center justify-center gap-0.5 text-[11px] font-bold', isActive ? 'text-plum' : 'text-mute')}>
        <img src={img.avalFaceSmile} alt="" className="-mt-3.5 size-[34px] rounded-full bg-lilac shadow-[0_0_0_3px_#FFFFFF,0_0_0_5px_#5B1F96]" />
        AVAL
      </NavLink>
      {item('/circle', t('Circle', 'வட்டம்'), <Icon.people width={2} />)}
      {item('/tickets', t('Tickets', 'டிக்கெட்'), <Icon.ticket width={2} />)}
    </nav>
  )
}

export function SosFab({ className }) {
  return (
    <Link
      to="/sos"
      aria-label="SOS emergency"
      className={cn('absolute right-4 z-40 flex size-[60px] items-center justify-center rounded-full bg-sos text-[15px] font-black text-white no-underline shadow-[0_0_0_6px_rgba(227,38,63,0.18)]', className)}
    >
      SOS
    </Link>
  )
}

/* ---------- small pieces ---------- */
export function SampleLabel({ className, children }) {
  const t = useT()
  return <p className={cn('text-center text-[11px] text-mute', className)}>{children || t('Sample data for demo', 'மாதிரி தரவு')}</p>
}

export function RouteBadge({ label, mode = 'bus', className, size = 'md' }) {
  const color = { bus: 'bg-pink text-white', metro: 'bg-metro text-white', train: 'bg-train text-white', auto: 'bg-[#FFC21C] text-ink', walk: 'bg-lilac text-plum' }[mode]
  return (
    <span className={cn('rounded-lg font-extrabold', size === 'sm' ? 'px-[7px] py-0.5 text-xs' : 'px-2 py-[3px] text-[13px]', color, className)}>
      {label}
    </span>
  )
}

export function Pill({ children, className }) {
  return <span className={cn('rounded-full px-2 py-1 text-[11px] font-extrabold', className)}>{children}</span>
}

export function SectionLabel({ children, className }) {
  return <span className={cn('text-xs font-bold tracking-[0.1em] text-mute uppercase', className)}>{children}</span>
}

export function Loading({ rows = 3, className }) {
  return (
    <div className={cn('flex flex-col gap-2.5', className)} aria-busy="true" aria-label="Loading">
      {Array.from({ length: rows }).map((_, i) => (
        <Skeleton key={i} className="h-[72px] rounded-[18px] bg-lilac" />
      ))}
    </div>
  )
}

export function ErrorState({ error, onRetry, className }) {
  const t = useT()
  return (
    <div className={cn('flex flex-col items-center gap-2 rounded-[18px] border-[1.5px] border-[#F5D3D8] bg-white p-4 text-center', className)} role="alert">
      <Icon.warn stroke="#E3263F" />
      <span className="text-sm font-bold">{t("Couldn't load this", 'ஏற்ற முடியவில்லை')}</span>
      <span className="text-xs text-mute">{error?.message}</span>
      {onRetry && (
        <button type="button" onClick={onRetry} className="mt-1 h-10 rounded-xl border-[1.5px] border-line bg-cream px-4 text-sm font-bold">
          {t('Try again', 'மீண்டும் முயற்சி')}
        </button>
      )}
    </div>
  )
}

export function EmptyState({ title, hint, className }) {
  return (
    <div className={cn('flex flex-col items-center gap-1 rounded-[18px] border-[1.5px] border-dashed border-[#C9B8D6] p-5 text-center', className)}>
      <span className="text-sm font-bold">{title}</span>
      {hint && <span className="text-xs text-mute">{hint}</span>}
    </div>
  )
}

export function AvalTip({ children, pose = img.poseGuide, className }) {
  return (
    <div className={cn('flex items-end gap-1.5', className)}>
      <img src={pose} alt="AVAL pointing" className="h-[84px] w-16 object-contain" />
      <div className="mb-[18px] rounded-[16px_16px_16px_4px] bg-ink px-3 py-2.5 text-[13px] leading-[1.4] text-white">{children}</div>
    </div>
  )
}

export function Avatar({ label, color = '#FF4F8B', text = '#FFFFFF', size = 34, className, ring }) {
  return (
    <span
      className={cn('flex shrink-0 items-center justify-center rounded-full font-extrabold', className)}
      style={{ width: size, height: size, background: color, color: text, fontSize: size * 0.4, boxShadow: ring }}
    >
      {(label || '?').charAt(0).toUpperCase()}
    </span>
  )
}

export const AVATAR_COLORS = [
  ['#FF4F8B', '#FFFFFF'], ['#FFB52E', '#24132F'], ['#0FA596', '#FFFFFF'], ['#5B1F96', '#FFFFFF'], ['#1F5BDA', '#FFFFFF'],
]
