// Illustrated place thumbnails (from design/screens_html/Explore.html). Photos come later (V1 gap).
export function PlaceThumb({ type, size = 48 }) {
  const s = size
  const art = {
    shg_kiosk: <><rect width="54" height="54" fill="#2B2340" /><rect x="8" y="22" width="38" height="26" fill="#FFB52E" /><path d="M4 22 L27 8 L50 22Z" fill="#FF4F8B" /><rect x="20" y="30" width="14" height="18" fill="#2B2340" /><circle cx="14" cy="28" r="2" fill="#FFF3B0" /><circle cx="40" cy="28" r="2" fill="#FFF3B0" /></>,
    pharmacy: <><rect width="54" height="54" fill="#DFF5EF" /><rect x="12" y="13" width="30" height="30" rx="4" fill="#FFFFFF" stroke="#0FA596" strokeWidth="3" /><path d="M27 19v18M18 28h18" stroke="#FF4F8B" strokeWidth="4" strokeLinecap="round" /></>,
    bus_shelter: <><rect width="54" height="54" fill="#E6EEFF" /><rect x="7" y="22" width="40" height="18" rx="5" fill="#1F5BDA" /><rect x="11" y="25" width="32" height="7" rx="2" fill="#BFD3FF" /><circle cx="16" cy="42" r="3" fill="#24132F" /><circle cx="38" cy="42" r="3" fill="#24132F" /></>,
    tea_shop: <><rect width="54" height="54" fill="#FFF1D6" /><path d="M14 24h22v11a9 9 0 0 1-9 9h-4a9 9 0 0 1-9-9z" fill="#FFFFFF" stroke="#C26A00" strokeWidth="2.5" /><path d="M36 27h4a3 3 0 0 1 0 7h-4" stroke="#C26A00" strokeWidth="2.5" fill="none" /><path d="M20 13q2 3 0 6M27 11q2 3 0 6" stroke="#C26A00" strokeWidth="2" fill="none" strokeLinecap="round" /></>,
    police_booth: <><rect width="54" height="54" fill="#E6EEFF" /><path d="M27 9l14 6v9c0 8-6 14-14 16-8-2-14-8-14-16v-9z" fill="#1F4FB8" /><path d="M21 26l4 4 8-9" stroke="#FFFFFF" strokeWidth="3" fill="none" strokeLinecap="round" /></>,
    hospital: <><rect width="54" height="54" fill="#FFE6EF" /><rect x="12" y="14" width="30" height="28" rx="3" fill="#FFFFFF" stroke="#E3263F" strokeWidth="2.5" /><path d="M27 20v16M19 28h16" stroke="#E3263F" strokeWidth="4" strokeLinecap="round" /></>,
    atm: <><rect width="54" height="54" fill="#E2F7F3" /><rect x="12" y="12" width="30" height="32" rx="4" fill="#0B7F74" /><rect x="16" y="16" width="22" height="10" rx="2" fill="#BFF0E6" /><rect x="18" y="32" width="18" height="4" rx="2" fill="#FFFFFF" /></>,
    bakery: <><rect width="54" height="54" fill="#FFF4E0" /><path d="M12 34c0-10 7-16 15-16s15 6 15 16z" fill="#E8960F" /><path d="M19 26l3 6M27 23v8M35 26l-3 6" stroke="#FFF3C4" strokeWidth="2.5" strokeLinecap="round" /><rect x="10" y="34" width="34" height="5" rx="2.5" fill="#C26A00" /></>,
    grocery: <><rect width="54" height="54" fill="#F3E8FA" /><path d="M13 20h28l-3 18H16z" fill="#5B1F96" /><circle cx="21" cy="17" r="4" fill="#FF4F8B" /><circle cx="30" cy="16" r="4" fill="#FFB52E" /></>,
    petrol_bunk: <><rect width="54" height="54" fill="#FFF1D6" /><rect x="15" y="14" width="18" height="28" rx="3" fill="#E3263F" /><rect x="18" y="18" width="12" height="8" rx="1.5" fill="#FFFFFF" /><path d="M33 22h4v14a3 3 0 0 0 6 0V24" stroke="#24132F" strokeWidth="2.5" fill="none" /></>,
  }
  return (
    <svg width={s} height={s} viewBox="0 0 54 54" aria-hidden="true">{art[type] || art.grocery}</svg>
  )
}

/** Night hero illustration for the Place screen, labelled with the place name. */
export function PlaceHero({ name }) {
  return (
    <svg viewBox="0 0 390 300" role="img" aria-label={`Illustration of ${name} at night`} className="block w-full">
      <defs><linearGradient id="nsky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#2B1C44" /><stop offset="1" stopColor="#6B2F6E" /></linearGradient></defs>
      <rect width="390" height="300" fill="url(#nsky)" />
      <circle cx="330" cy="60" r="22" fill="#FFF3C4" /><circle cx="340" cy="54" r="20" fill="#3A2550" />
      <g fill="#22182F"><rect x="0" y="120" width="70" height="180" /><rect x="300" y="110" width="90" height="190" /></g>
      <rect x="0" y="250" width="390" height="50" fill="#2A2232" />
      <rect x="95" y="130" width="200" height="120" rx="6" fill="#FFB52E" />
      <path d="M80 132 L195 86 L310 132Z" fill="#FF4F8B" />
      <path d="M80 132 h230 v14 h-230z" fill="#DB3570" />
      <path d="M90 146 q9 10 18 0 q9 10 18 0 q9 10 18 0 q9 10 18 0 q9 10 18 0 q9 10 18 0 q9 10 18 0 q9 10 18 0 q9 10 18 0 q9 10 18 0 q9 10 18 0 q9 10 18 0z" fill="#FFFFFF" opacity=".9" />
      <rect x="120" y="176" width="70" height="74" rx="4" fill="#5B1F96" /><rect x="210" y="170" width="64" height="40" rx="4" fill="#FFF3C4" />
      <circle cx="150" cy="200" r="11" fill="#DBA077" /><rect x="138" y="212" width="24" height="38" rx="8" fill="#FF4F8B" />
      <text x="195" y="124" textAnchor="middle" fontFamily="Noto Sans,sans-serif" fontWeight="800" fontSize="14" fill="#FFFFFF">{name.toUpperCase().slice(0, 26)}</text>
      <g fill="#FFF3B0"><circle cx="100" cy="160" r="4" /><circle cx="290" cy="160" r="4" /></g>
    </svg>
  )
}
