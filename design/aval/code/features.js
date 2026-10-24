/* ---------- feature poses ---------- */
function label(x,y,text,fill,color='#fff',w){
  const ww = w || (text.length*7.4+18);
  return `<rect x="${x-ww/2}" y="${y-13}" width="${ww}" height="22" rx="11" fill="${fill}"/><text x="${x}" y="${y+3}" text-anchor="middle" font-size="12" font-weight="800" fill="${color}" font-family="Noto Sans,sans-serif">${text}</text>`;
}
function featShops(){
  return wrapSvg(`<g>
    ${body(true,false)}<g>${braidChain(150,168,146,238,7)}</g>${head('happy')}
    ${armPath('M70 182 Q58 204 56 226')}
    <path d="M38 222 h34 l-4 36 h-26z" fill="${C.pink}"/><path d="M46 222 q9 -14 18 0" stroke="${C.pinkSh}" stroke-width="3" fill="none"/>
    <path d="M42 236 h26" stroke="#fff" stroke-width="2" opacity=".6"/>${hand(55,226)}
    ${armPath('M132 182 Q160 178 168 150')}${armPath('M168 150 Q172 136 176 124')}${hand(177,118)}
    <g transform="translate(178 80)"><path d="M0 26 C-16 6 -14 -14 0 -14 C14 -14 16 6 0 26Z" fill="${C.teal}"/><circle cy="-2" r="6" fill="#fff"/></g>
    ${sparkles([[204,60,6],[150,52,4]])}
  </g>`,'finding safe shops nearby');
}
function featConnect(){
  return wrapSvg(`<g>
    ${body(true,true)}<g>${braidChain(150,168,146,238,7)}</g>${head('talking')}
    ${armPath('M132 182 Q156 172 158 150')}
    <rect x="150" y="112" width="16" height="30" rx="4" fill="${C.teal}" stroke="${C.ink}" stroke-width="2"/>${hand(158,146)}
    <g transform="translate(160 40)">
      <path d="M-34 -22 h68 a10 10 0 0 1 10 10 v26 a10 10 0 0 1 -10 10 h-50 l-12 10 v-10 h-6 a10 10 0 0 1 -10 -10 v-26 a10 10 0 0 1 10 -10z" fill="#fff" stroke="${C.plum}" stroke-width="2.5"/>
      <circle cx="-22" cy="2" r="9" fill="${C.pink}"/><circle cx="0" cy="2" r="9" fill="${C.gold}"/><circle cx="22" cy="2" r="9" fill="${C.teal}"/>
      <path d="M-26 -1 q4 5 8 0 M-4 -1 q4 5 8 0 M18 -1 q4 5 8 0" stroke="#fff" stroke-width="2" fill="none" stroke-linecap="round"/>
    </g>
  </g>`,'connecting with her trusted circle');
}
function featPay(){
  return wrapSvg(`<g>
    ${body(false,false)}<g>${braidChain(150,168,146,238,7)}</g>${head('happy')}
    ${armPath('M70 182 Q46 176 38 150')}
    <g transform="translate(30 116)"><circle r="24" fill="${C.gold}"/><circle r="18" fill="none" stroke="${C.goldSh}" stroke-width="3"/>
      <text y="9" text-anchor="middle" font-size="26" font-weight="800" fill="${C.ink}" font-family="Noto Sans,sans-serif">₹</text></g>
    ${hand(38,148)}
    <g transform="translate(176 120)"><circle r="16" fill="${C.teal}"/><path d="M-7 0 l5 5 l9 -10" stroke="#fff" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round"/></g>
    ${label(176,152,'PAID',C.teal)}
    ${sparkles([[8,86,6],[60,96,5]])}
  </g>`,'paying for a ticket');
}
function featBus(){
  return wrapSvg(`<g>
    <rect x="183" y="60" width="5" height="232" rx="2.5" fill="#8E8899"/>
    ${body(true,true)}<g>${braidChain(150,168,146,238,7)}</g>${head('smile')}
    ${armPath('M132 182 Q156 180 174 170')}<circle cx="178" cy="168" r="8" fill="${C.skin}"/>
    <rect x="152" y="14" width="64" height="58" rx="10" fill="${C.plum}"/>
    <text x="184" y="36" text-anchor="middle" font-size="14" font-weight="800" fill="#fff" font-family="Noto Sans,sans-serif">BUS 5D</text>
    <text x="184" y="56" text-anchor="middle" font-size="14" font-weight="800" fill="${C.gold}" font-family="Noto Sans,sans-serif">6 min</text>
    ${label(184,88,'FREE',C.pink)}
  </g>`,'checking if a free bus is coming');
}
function featTrip(){
  return wrapSvg(`<g>
    <path d="M-10 286 C40 250 150 300 210 240" stroke="${C.teal}" stroke-width="4" stroke-dasharray="2 10" stroke-linecap="round" fill="none"/>
    ${body(false,true)}<g>${braidChain(150,168,146,238,7)}</g>${head('smile')}
    <g transform="translate(176 92)"><path d="M0 -26 L22 -17 V0 C22 14 12 24 0 28 C-12 24 -22 14 -22 0 V-17Z" fill="${C.teal}"/>
      <path d="M-9 1 l6 6 l12 -13" stroke="#fff" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round"/></g>
    ${label(176,138,'WATCHING',C.plum)}
    <circle cx="206" cy="240" r="7" fill="${C.pink}"/><circle cx="206" cy="240" r="13" fill="none" stroke="${C.pink}" stroke-width="2" opacity=".5"/>
  </g>`,'on a live trip with Journey Watch');
}
function featSOS(){
  return wrapSvg(`<g>
    <circle cx="100" cy="160" r="108" fill="${C.pink}" opacity=".13"/>
    ${body(true,true)}<g>${braidChain(150,168,146,238,7)}</g>${head('alert')}
    ${armPath('M132 182 Q160 176 168 150')}${armPath('M168 150 Q172 136 174 124')}
    <g transform="translate(176 92)"><circle r="30" fill="#E3263F"/><circle r="30" fill="none" stroke="#fff" stroke-width="3" opacity=".6"/>
      <text y="7" text-anchor="middle" font-size="19" font-weight="900" fill="#fff" font-family="Noto Sans,sans-serif">SOS</text></g>
    ${hand(174,124)}
    ${label(176,140,'181 · 100','#fff','#E3263F',76)}
  </g>`,'pressing SOS');
}

/* ---------- combined poster 1200x720 ---------- */
function combined(){
  const items=[
    [featShops(),'Safe shops','பாதுகாப்பான கடைகள்'],[featConnect(),'Connect','இணைப்பு'],[featBus(),'Free bus now','இலவச பேருந்து'],
    [featPay(),'Pay & book','கட்டணம்'],[featTrip(),'Live trip','பயணக் காவல்'],[featSOS(),'SOS','அவசர உதவி']];
  const pos=[[50,130],[240,130],[145,420],[790,130],[980,130],[885,420]];
  return `<svg viewBox="0 0 1200 720" role="img" aria-label="AVAL and everything she helps with">
  <defs><linearGradient id="pg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#FFF1DC"/><stop offset="1" stop-color="#F6E3FF"/></linearGradient></defs>
  <rect width="1200" height="720" fill="url(#pg)"/>
  <circle cx="600" cy="400" r="250" fill="#FFFFFF" opacity=".55"/>
  <text x="600" y="66" text-anchor="middle" font-size="44" font-weight="800" fill="${C.plum}" font-family="Noto Sans,sans-serif">AVAL helps you travel freely</text>
  <text x="600" y="104" text-anchor="middle" font-size="24" font-weight="700" fill="${C.pink}" font-family="Noto Sans Tamil,sans-serif">அவள் உங்கள் பயணத் துணை</text>
  <svg x="440" y="150" width="320" height="420" viewBox="-20 -14 240 314">${front('happy','still',true).replace(/^<svg[^>]*>/,'').replace(/<\/svg>$/,'')}</svg>
  ${items.map(([svg,en,ta],i)=>{const [x,y]=pos[i]; return `<g>
     <rect x="${x}" y="${y}" width="170" height="270" rx="22" fill="#fff" stroke="#EADCF1" stroke-width="2"/>
     <svg x="${x+10}" y="${y+8}" width="150" height="196" viewBox="-20 -14 240 314">${svg.replace(/^<svg[^>]*>/,'').replace(/<\/svg>$/,'')}</svg>
     <text x="${x+85}" y="${y+230}" text-anchor="middle" font-size="18" font-weight="800" fill="${C.ink}" font-family="Noto Sans,sans-serif">${en}</text>
     <text x="${x+85}" y="${y+254}" text-anchor="middle" font-size="14" font-weight="700" fill="#6A5878" font-family="Noto Sans Tamil,sans-serif">${ta}</text></g>`;}).join('')}
  <g transform="translate(600 640)">${label(0,0,'SafePath · SDG 5 · Chennai',C.plum,'#fff',260)}</g>
  </svg>`;
}
