import { Link, useParams } from 'react-router-dom'
import { toast } from 'sonner'

import { typeLabel } from '@/components/Cards'
import { BackButton, ErrorState, Icon, Loading, SampleLabel } from '@/components/kit'
import { PlaceHero } from '@/components/PlaceArt'
import { api } from '@/lib/api'
import { clock, useAsync } from '@/lib/hooks'
import { useT } from '@/lib/i18n'

const ago = (d, t) => (d <= 1 ? t('yesterday', 'நேற்று') : d < 7 ? t(`${d} days ago`, `${d} நாள் முன்`) : d < 14 ? t('1 week ago', '1 வாரம் முன்') : t(`${Math.floor(d / 7)} weeks ago`, `${Math.floor(d / 7)} வாரம் முன்`))

export default function Place() {
  const t = useT()
  const { id } = useParams()
  const res = useAsync(() => api.place(id), [id])
  const p = res.data

  async function share() {
    const text = `${p.name} · ${p.address} · ${p.closes_label} (SafePath, sample data)`
    try {
      if (navigator.share) await navigator.share({ title: p.name, text })
      else { await navigator.clipboard.writeText(text); toast(t('Copied to share', 'நகலெடுக்கப்பட்டது')) }
    } catch { /* cancelled */ }
  }

  return (
    <div className="flex min-h-dvh flex-col bg-white">
      <div className="relative shrink-0">
        {p ? <PlaceHero name={p.name.replace(/ \(.*\)$/, '')} /> : <div className="h-[300px] bg-[#2B1C44]" />}
        <div className="absolute top-4 right-4 left-4 flex justify-between">
          <BackButton icon="close" className="bg-white/90" />
          <div className="flex gap-2">
            <button type="button" aria-label={t('Share', 'பகிர்')} onClick={share} disabled={!p} className="flex size-11 items-center justify-center rounded-full bg-white/90"><Icon.share stroke="#24132F" size={20} /></button>
            <button type="button" aria-label={t('Save', 'சேமி')} onClick={() => toast(t('Saved on this phone', 'சேமிக்கப்பட்டது'))} className="flex size-11 items-center justify-center rounded-full bg-white/90"><Icon.save stroke="#24132F" size={20} /></button>
          </div>
        </div>
        <span className="absolute right-4 bottom-9 rounded-lg bg-ink/75 px-2 py-1 text-[11px] font-bold text-white">{t('Illustration · photos later', 'விளக்கப்படம்')}</span>
      </div>

      <div className="relative -mt-6 flex flex-1 flex-col gap-3 rounded-t-3xl bg-white px-4 pt-[18px] pb-5">
        {res.loading ? <Loading rows={3} /> : res.error ? <ErrorState error={res.error} onRetry={res.reload} /> : (
          <>
            <div className="flex items-start justify-between gap-3">
              <div className="flex flex-col gap-0.5">
                <h1 className="text-[22px] font-extrabold">{t(p.name, p.name_ta || p.name)}</h1>
                <span className="text-[13px] text-mute">{p.category} · {p.address}</span>
              </div>
              {p.rating && (
                <div className="flex shrink-0 flex-col items-end"><span className="text-lg font-extrabold">★ {p.rating}</span><span className="text-[11px] text-mute">{p.reviews_count} {t('reviews', 'விமர்சனங்கள்')}</span></div>
              )}
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <span className={`rounded-lg px-2.5 py-1 text-xs font-extrabold text-white ${p.open_now ? 'bg-teal' : 'bg-mute'}`}>{p.open_now ? t('Open now', 'இப்போது திறந்துள்ளது') : t('Closed now', 'மூடப்பட்டுள்ளது')}</span>
              <span className="text-[13px] text-ink-2">{p.open_now || p.open_24h ? p.closes_label : t(`Opens ${clock(p.open, true)}`, `${clock(p.open, true)} திறக்கும்`)} · {t(`${p.distance_m} m from the Anna Nagar West stop`, `அண்ணா நகர் மேற்கு நிறுத்தத்திலிருந்து ${p.distance_m} மீ`)}</span>
            </div>

            <div className="flex flex-col gap-2 rounded-[18px] bg-lilac px-3.5 py-3">
              <div className="flex items-center justify-between">
                <span className="text-sm font-extrabold text-plum">{t('Safety at night', 'இரவில் பாதுகாப்பு')}</span>
                <span className={`text-[13px] font-extrabold ${p.night_safety.label === 'Low' ? 'text-sos' : 'text-teal-dark'}`}>{p.night_safety.label}</span>
              </div>
              <div className="flex flex-wrap gap-1.5 text-xs font-bold">
                {p.night_safety.tags.map((tag) => <span key={tag} className="rounded-lg bg-white px-2 py-1">{tag}</span>)}
                {p.night_safety.tags.length === 0 && <span className="text-mute">{t('No safety signals yet', 'தகவல் இல்லை')}</span>}
              </div>
            </div>

            <div className="grid grid-cols-3 gap-2">
              <Link to={`/reach/${p.id}`} className="flex h-12 items-center justify-center rounded-[14px] bg-plum text-sm font-extrabold text-white no-underline">{t('How to reach', 'எப்படிப் போவது')}</Link>
              <button type="button" disabled title={t('No phone listed in sample data', 'எண் இல்லை')} className="h-12 rounded-[14px] border-[1.5px] border-line bg-white text-sm font-bold text-ink disabled:opacity-50">{t('Call', 'அழை')}</button>
              <button type="button" onClick={share} className="h-12 rounded-[14px] border-[1.5px] border-line bg-white text-sm font-bold text-ink">{t('Share', 'பகிர்')}</button>
            </div>

            <div className="flex flex-col gap-2">
              <span className="text-[15px] font-extrabold">{t('What women say', 'பெண்கள் சொல்வது')}</span>
              {p.reviews.length === 0 && <span className="text-sm text-mute">{t(`No reviews yet for this ${typeLabel(p.type)}.`, 'இன்னும் விமர்சனங்கள் இல்லை.')}</span>}
              {p.reviews.map((r, i) => (
                <div key={i} className="flex flex-col gap-1 rounded-2xl bg-cream px-3 py-2.5">
                  <div className="flex justify-between"><span className="text-[13px] font-extrabold">{r.author} · ★ {r.rating}</span><span className="text-[11px] text-mute">{ago(r.days_ago, t)}</span></div>
                  <span lang={r.lang} className={`text-[13px] leading-[1.45] text-ink-2 ${r.lang === 'ta' ? 'font-tamil' : ''}`}>{r.text}</span>
                </div>
              ))}
            </div>
            <SampleLabel />
          </>
        )}
      </div>
    </div>
  )
}
