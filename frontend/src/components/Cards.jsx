import { Link } from 'react-router-dom'

import { Icon, Pill, RouteBadge } from '@/components/kit'
import { clock } from '@/lib/hooks'
import { useT } from '@/lib/i18n'

export const transitLegs = (opt) => (opt?.legs || []).filter((l) => l.mode !== 'walk')

const TYPE_LABEL = {
  shg_kiosk: 'SHG kiosk', pharmacy: 'pharmacy', tea_shop: 'tea shop', atm: 'ATM', bakery: 'bakery', grocery: 'grocery',
  petrol_bunk: 'petrol bunk', police_booth: 'police booth', hospital: 'hospital', bus_shelter: 'bus shelter',
}
export const typeLabel = (t) => TYPE_LABEL[t] || t

/** The only free wording we use: the scheme covers ordinary buses, not a specific bus. */
export function useFreeText() {
  const t = useT()
  return t('Free for women on ordinary (white-board) buses', 'சாதாரண (வெள்ளை பலகை) பஸ்ஸில் பெண்களுக்கு இலவசம்')
}

/** True when the ride comes from the real MTC timetable (ChennaiGTFS), not sample data. */
export const isReal = (x) => Boolean(x?.source) && x.source !== 'sample'

/** Data label for screens that mix real bus times with sample places. */
export function useDataNote() {
  const t = useT()
  return (real) => (real
    ? t('Bus times: real MTC timetable (ChennaiGTFS, scheduled, not live). Safe places: sample data.',
      'பஸ் நேரம்: உண்மையான MTC அட்டவணை (ChennaiGTFS). பாதுகாப்பான இடங்கள்: மாதிரி தரவு.')
    : undefined)
}

/** Route card inside AVAL's reply (Main screen). */
export function RouteCard({ card }) {
  const t = useT()
  const opt = card.option
  const legs = transitLegs(opt)
  const first = legs[0]
  const sw = opt.safe_wait
  const freeText = useFreeText()
  return (
    <div className="flex flex-col gap-2.5 rounded-[18px] border-2 border-lilac p-3">
      <div className="flex items-center justify-between">
        <div className="flex flex-wrap items-center gap-2">
          {legs.map((l, i) => (
            <span key={i} className="flex items-center gap-1.5">
              {i > 0 && <span className="text-mute">→</span>}
              <span className={`rounded-[10px] px-2.5 py-1 text-base font-extrabold text-white ${l.mode === 'bus' ? 'bg-pink-deep' : l.mode === 'metro' ? 'bg-metro' : l.mode === 'train' ? 'bg-train' : 'bg-[#FFC21C] !text-ink'}`}>{l.label}</span>
            </span>
          ))}
          {opt.is_free && <Pill className="bg-[#E6F4F2] text-xs font-bold text-[#0B5F59]">{freeText}</Pill>}
          {!opt.is_free && opt.fare_inr > 0 && <Pill className="bg-lilac text-xs text-plum">{opt.fare_is_estimate ? '~' : ''}₹{opt.fare_inr}</Pill>}
        </div>
        <span className="tabular text-[13px] text-mute">{opt.total_min} min</span>
      </div>
      {first && first.mode !== 'auto' ? (
        <div className="flex flex-col gap-1.5 text-sm">
          <div className="flex justify-between"><span className="text-mute">{t('Board at', 'ஏறும் இடம்')}</span><span className="font-semibold">{opt.board_at}</span></div>
          <div className="flex justify-between">
            <span className="text-mute">{first.mode === 'bus' ? t('Next bus', 'அடுத்த பஸ்') : t('Next train', 'அடுத்த ரயில்')}</span>
            <span className="tabular font-semibold">{opt.next.slice(0, 2).map((x) => clock(x)).join(' · then ')}</span>
          </div>
          {first.free_note && (
            <span className="text-xs text-mute">{t('Deluxe / AC buses on this route are paid.', 'டீலக்ஸ் / AC பஸ்ஸில் கட்டணம் உண்டு.')}</span>
          )}
          {isReal(opt) && <span className="text-[11px] text-mute">{t('Real MTC timetable · ChennaiGTFS', 'உண்மையான MTC அட்டவணை · ChennaiGTFS')}</span>}
        </div>
      ) : (
        <div className="text-sm text-mute">{t('Door to door · fare is an estimate', 'வீட்டு வாசல் வரை · கட்டணம் மதிப்பீடு')}</div>
      )}
      {sw && (
        <div className="flex items-center gap-2.5 rounded-xl bg-cream p-2.5">
          <Icon.shield stroke="#0E7C74" width={2} />
          <div className="flex flex-col gap-px">
            <span className="text-[13px] font-bold">{t(`Wait at ${sw.name}`, `${sw.name_ta || sw.name}-ல் காத்திருங்கள்`)}</span>
            <span className="text-xs text-mute">
              {[sw.distance_m && `${sw.distance_m} m`, sw.women_run && t('women-run', 'பெண்கள் நடத்துவது'), sw.open_now && t('open now', 'இப்போது திறந்துள்ளது'), sw.crowd_now === 'busy' && t('busy', 'கூட்டம்')].filter(Boolean).join(' · ')}
            </span>
          </div>
        </div>
      )}
    </div>
  )
}

/** Booking screen option card. */
export function OptionCard({ opt, selected, onSelect }) {
  const t = useT()
  const legs = transitLegs(opt)
  const walkStart = opt.legs[0]?.mode === 'walk' ? opt.legs[0].minutes : 0
  const walkEnd = opt.legs.length > 1 && opt.legs[opt.legs.length - 1].mode === 'walk' ? opt.legs[opt.legs.length - 1].minutes : 0
  const ride = legs.reduce((s, l) => s + l.minutes, 0)
  const freeText = useFreeText()
  return (
    <button
      type="button"
      onClick={onSelect}
      aria-pressed={selected}
      className={`flex w-full flex-col gap-2.5 rounded-[20px] bg-white p-3.5 text-left text-ink ${selected ? 'border-[2.5px] border-plum' : 'border-[1.5px] border-line'}`}
    >
      <div className="flex items-center justify-between">
        <div className="flex flex-wrap items-center gap-1.5">
          {legs.length === 0 && <RouteBadge label={t('Walk', 'நட')} mode="walk" />}
          {legs.map((l, i) => (
            <span key={i} className="flex items-center gap-1.5">
              {i > 0 && <span className="text-mute">→</span>}
              <RouteBadge label={l.label} mode={l.mode} className={selected && i === 0 ? 'text-sm' : ''} />
            </span>
          ))}
          {opt.is_free && legs.length > 0 && <Pill className="bg-safe-bg text-teal-dark">{freeText}</Pill>}
          {isReal(opt) && <Pill className="bg-[#EAF1FF] text-[11px] text-[#1F4FB0]">{t('Real MTC times', 'உண்மையான நேரம்')}</Pill>}
          {legs.length === 1 && legs[0].mode === 'auto' && <span className="text-xs text-ink-2">{t('Door to door', 'வீட்டு வாசல் வரை')}</span>}
          {(opt.badges || []).filter((b) => b !== 'CHEAPEST').map((b) => (
            <Pill key={b} className={b === 'SAFEST' ? 'bg-safe-bg text-teal-dark' : 'bg-[#FFF1D6] text-[#9A5B00]'}>{b}</Pill>
          ))}
        </div>
        <div className="flex shrink-0 flex-col items-end">
          <span className="text-lg font-extrabold">{opt.total_min} min</span>
          <span className="text-xs text-mute">
            {opt.kind === 'auto' ? `~₹${opt.fare_inr}` : selected || opt.switches === 0 ? `${t('reach', 'சேர்வது')} ${clock(opt.reach_by)}` : `₹${opt.fare_inr} · ${opt.switches} ${t('switch', 'மாற்றம்')}`}
          </span>
        </div>
      </div>
      {selected && legs.length > 0 && legs[0].mode !== 'auto' && (
        <div className="flex items-center gap-1.5 text-xs font-semibold text-ink-2">
          {walkStart > 0 && <span>{t('Walk', 'நட')} {walkStart} min</span>}
          <span className="h-[3px] flex-1 rounded-sm bg-pink" />
          <span>{legs.map((l) => `${l.mode === 'bus' ? t('Bus', 'பஸ்') : l.label} ${l.minutes} min`).join(' + ')}</span>
          {walkEnd > 0 && <><span className="h-[3px] flex-[0.3] rounded-sm bg-[#C9B8D6]" /><span>{walkEnd} min</span></>}
          {walkStart === 0 && walkEnd === 0 && <span className="text-mute">{ride} min</span>}
        </div>
      )}
      {opt.switch_info && (
        <span className="text-xs text-ink-2">
          {t(`Switch at ${opt.switch_info.at}`, `${opt.switch_info.at}-ல் மாற்றம்`)} · {opt.switch_info.lit ? t('lit walkway', 'வெளிச்சமான நடைபாதை') : t('dark walkway', 'இருண்ட பாதை')}, {opt.switch_info.walk_min} min
        </span>
      )}
      {selected && opt.safety_tags?.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {opt.safety_tags.map((tag, i) => (
            <span key={tag} className={`rounded-lg px-2 py-1 text-xs font-bold ${i === 0 && tag.startsWith('Safe wait') ? 'bg-safe-bg text-teal-dark' : 'bg-lilac text-plum'}`}>{tag}</span>
          ))}
        </div>
      )}
    </button>
  )
}

/** Small list of places for AVAL replies. */
export function PlacesList({ places, limit = 3 }) {
  const t = useT()
  return (
    <div className="flex flex-col gap-1.5">
      {places.slice(0, limit).map((p) => (
        <Link key={p.id} to={`/place/${p.id}`} className="flex items-center justify-between rounded-xl bg-cream px-3 py-2 text-ink no-underline">
          <div className="flex flex-col">
            <span className="text-[13px] font-bold">{t(p.name, p.name_ta || p.name)}</span>
            <span className="text-xs text-mute">{typeLabel(p.type)}{p.distance_m != null ? ` · ${p.distance_m} m` : ''}{p.women_run ? ` · ${t('women-run', 'பெண்கள் நடத்துவது')}` : ''}</span>
          </div>
          <Pill className={p.open_now ? 'bg-teal text-white' : 'bg-line text-mute'}>{p.open_now ? 'OPEN' : t('Closed', 'மூடப்பட்டது')}</Pill>
        </Link>
      ))}
    </div>
  )
}
