import { useT } from '@/lib/i18n'

/** Bottom-sheet confirmation. Used before paying or messaging anyone (never for SOS). */
export default function Confirm({ open, title, body, confirmLabel, cancelLabel, onConfirm, onCancel, onClose, busy, tone = 'teal', children }) {
  const t = useT()
  if (!open) return null
  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-ink/50" role="dialog" aria-modal="true" aria-labelledby="confirm-title">
      <div className="w-full max-w-[430px] rounded-t-[28px] bg-white px-4 pt-2.5 pb-6 text-ink">
        <span className="mx-auto mb-3 block h-[5px] w-10 rounded-full bg-[#D6C8E2]" />
        <div className="flex items-start justify-between gap-3">
          <h2 id="confirm-title" className="text-lg font-extrabold">{title}</h2>
          {onClose && (
            <button type="button" onClick={onClose} aria-label={t('Close', 'மூடு')} className="-mt-1 flex size-10 shrink-0 items-center justify-center rounded-full bg-cream text-lg">✕</button>
          )}
        </div>
        {body && <div className="mt-1 text-sm leading-relaxed text-ink-2">{body}</div>}
        {children}
        {onConfirm && <div className="mt-4 grid grid-cols-2 gap-2.5">
          <button type="button" onClick={onCancel} className="h-[54px] rounded-2xl border-2 border-line bg-white text-[15px] font-extrabold">
            {cancelLabel || t('No', 'வேண்டாம்')}
          </button>
          <button
            type="button"
            onClick={onConfirm}
            disabled={busy}
            className={`h-[54px] rounded-2xl text-[15px] font-extrabold text-white disabled:opacity-60 ${tone === 'pink' ? 'bg-pink' : 'bg-teal'}`}
          >
            {busy ? t('Please wait…', 'காத்திருங்கள்…') : confirmLabel || t('Yes', 'ஆம்')}
          </button>
        </div>}
      </div>
    </div>
  )
}
