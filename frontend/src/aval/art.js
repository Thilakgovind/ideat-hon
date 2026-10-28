/* AVAL art — copied verbatim from design/aval/code/{draw_v2,poses,features}.js and exported as an ES module. */
/* eslint-disable */
/* ---------- AVAL drawing (v2: layered, shaded) ---------- */
const C = {
  hair:'#1F1729', hairDeep:'#120C18', hairHi:'#43325A',
  skin:'#DBA077', skinSh:'#BC8160', skinHi:'#E4B28D',
  plum:'#5B1F96', plumSh:'#43157A', plumHi:'#7A36BD',
  pink:'#FF4F8B', pinkSh:'#DB3570',
  gold:'#FFB52E', goldSh:'#E8960F',
  teal:'#0FA596', tealSh:'#0B7F74',
  ink:'#2A2032', inkSh:'#1B1421', blush:'#FF8C90', lip:'#7A2E36', jas:'#FFFDF5', jasSh:'#E6DCC2'
};
function jasmine(points, r=4.6){
  return points.map(([x,y])=>`<g transform="translate(${x} ${y})">
    <circle r="${r}" fill="${C.jas}"/><path d="M${-r*.6} ${r*.3} a${r} ${r} 0 0 0 ${r*1.2} 0" fill="${C.jasSh}"/><circle r="${r*.32}" fill="#EFD98A"/></g>`).join('');
}
function braidChain(x0,y0,x1,y1,n){
  let s='';
  for(let i=0;i<n;i++){
    const t=i/(n-1), x=x0+(x1-x0)*t + (i%2?1.5:-1.5), y=y0+(y1-y0)*t, rx=10-t*3.5;
    s+=`<g><ellipse cx="${x}" cy="${y}" rx="${rx}" ry="8.5" fill="${C.hair}"/>
        <path d="M${x-rx*.8} ${y-2} q${rx*.8} -6 ${rx*1.6} 0" stroke="${C.hairHi}" stroke-width="2" fill="none" stroke-linecap="round"/>
        <path d="M${x-rx} ${y+3} q${rx} 6 ${rx*2} 0" stroke="${C.hairDeep}" stroke-width="2" fill="none"/></g>`;
  }
  return s + `<path d="M${x1-5} ${y1+5} q5 16 10 0z" fill="${C.hair}"/><rect x="${x1-5}" y="${y1+2}" width="10" height="5" rx="2.5" fill="${C.pink}"/>`;
}
function eyes(mood, dx=0){
  const L=78+dx, R=122+dx, Y=114;
  if(mood==='happy') return `<path d="M${L-8} ${Y+2} q8 -11 16 0 M${R-8} ${Y+2} q8 -11 16 0" stroke="#1B1720" stroke-width="5" fill="none" stroke-linecap="round"/>`;
  if(mood==='sleepy') return `<path d="M${L-7} ${Y+2} q7 5 14 0 M${R-7} ${Y+2} q7 5 14 0" stroke="#1B1720" stroke-width="4.5" fill="none" stroke-linecap="round"/>`;
  const up = mood==='thinking' ? -3 : 0, look = mood==='thinking' ? 3 : 0, ry = mood==='alert' ? 13 : 12;
  return `<g class="eyes">
    <rect x="${L-7+look}" y="${Y-ry+up}" width="14" height="${ry*2}" rx="7" fill="#1B1720" transform="rotate(-6 ${L} ${Y})"/>
    <rect x="${R-7+look}" y="${Y-ry+up}" width="14" height="${ry*2}" rx="7" fill="#1B1720" transform="rotate(6 ${R} ${Y})"/>
    <ellipse cx="${L+2+look}" cy="${Y-6+up}" rx="2.8" ry="3.6" fill="#fff"/><ellipse cx="${R+2+look}" cy="${Y-6+up}" rx="2.8" ry="3.6" fill="#fff"/>
    <circle cx="${L-2+look}" cy="${Y+6+up}" r="1.3" fill="#fff" opacity=".7"/><circle cx="${R-2+look}" cy="${Y+6+up}" r="1.3" fill="#fff" opacity=".7"/></g>`;
}
function brows(mood, dx=0){
  if(mood==='alert') return `<path d="M${66+dx} 94 l16 5 M${134+dx} 94 l-16 5" stroke="${C.hairDeep}" stroke-width="3.5" stroke-linecap="round"/>`;
  if(mood==='thinking') return `<path d="M${70+dx} 96 q8 -4 15 0 M${114+dx} 93 q8 -4 15 0" stroke="${C.hairDeep}" stroke-width="3" fill="none" stroke-linecap="round"/>`;
  return '';
}
function mouth(mood, dx=0){
  const x=100+dx;
  switch(mood){
    case 'talking': return `<ellipse class="mouth-talk" cx="${x}" cy="137" rx="6.5" ry="5.5" fill="${C.lip}"/>`;
    case 'alert': return `<path d="M${x-7} 139 h14" stroke="${C.lip}" stroke-width="3.2" stroke-linecap="round"/>`;
    case 'thinking': return `<path d="M${x-5} 139 q6 -3 11 1" stroke="${C.lip}" stroke-width="3" fill="none" stroke-linecap="round"/>`;
    case 'sleepy': return `<ellipse cx="${x}" cy="139" rx="3.5" ry="2.6" fill="${C.lip}"/>`;
    case 'happy': return `<path d="M${x-8} 134 q8 11 16 0z" fill="${C.lip}"/><path d="M${x-4} 138 q4 3 8 0" fill="${C.blush}"/>`;
    default: return `<path d="M${x-6} 135 q6 5 12 0" stroke="${C.lip}" stroke-width="3" fill="none" stroke-linecap="round"/>`;
  }
}
function jimikki(x,y){
  return `<g><circle cx="${x}" cy="${y}" r="3.2" fill="${C.gold}"/><path d="M${x-7} ${y+12} q7 -14 14 0z" fill="${C.gold}"/>
    <path d="M${x-7} ${y+12} q7 -6 14 0" fill="${C.goldSh}"/><circle cx="${x-5}" cy="${y+15}" r="1.4" fill="${C.gold}"/><circle cx="${x}" cy="${y+16}" r="1.4" fill="${C.gold}"/><circle cx="${x+5}" cy="${y+15}" r="1.4" fill="${C.gold}"/></g>`;
}
/* dx shifts the face for the 3/4 view */
function head(mood, dx=0){
  return `
  <!-- back hair -->
  <path d="M30 104 Q26 22 100 18 Q174 22 170 104 Q170 142 158 162 Q100 176 42 162 Q30 142 30 104Z" fill="${C.hair}"/>
  <path d="M40 112 Q40 150 52 166 L148 166 Q160 150 160 112 Q150 140 100 144 Q50 140 40 112Z" fill="${C.hairDeep}"/>
  ${jasmine([[160,44],[168,56],[173,70],[175,85],[174,100]],5.2)}
  <!-- face -->
  <path d="M${46+dx} 100 Q${46+dx} 164 ${100+dx} 166 Q${154+dx} 164 ${154+dx} 100 Q${154+dx} 58 ${100+dx} 56 Q${46+dx} 58 ${46+dx} 100Z" fill="${C.skin}"/>
  <path d="M${46+dx} 100 Q${48+dx} 120 ${54+dx} 128 Q${52+dx} 108 ${60+dx} 98Z M${154+dx} 100 Q${152+dx} 120 ${146+dx} 128 Q${148+dx} 108 ${140+dx} 98Z" fill="${C.skinSh}" opacity=".7"/>
  <clipPath id="fc${dx}"><path d="M${46+dx} 100 Q${46+dx} 164 ${100+dx} 166 Q${154+dx} 164 ${154+dx} 100 Q${154+dx} 58 ${100+dx} 56 Q${46+dx} 58 ${46+dx} 100Z"/></clipPath>
  <path d="M${36+dx} 108 Q${32+dx} 24 ${100+dx} 22 Q${168+dx} 24 ${164+dx} 108 Q${160+dx} 86 ${150+dx} 78 L${144+dx} 104 Q${138+dx} 82 ${128+dx} 74 L${120+dx} 100 Q${112+dx} 78 ${104+dx} 72 L${98+dx} 98 Q${88+dx} 76 ${76+dx} 74 L${68+dx} 102 Q${60+dx} 84 ${50+dx} 88 Q${40+dx} 96 ${36+dx} 108Z" transform="translate(0 6)" fill="${C.skinSh}" opacity=".5" clip-path="url(#fc${dx})"/>
  <circle cx="${100+dx}" cy="104" r="2.6" fill="${C.pink}"/>
  ${brows(mood,dx)}${eyes(mood,dx)}
  <ellipse cx="${63+dx}" cy="132" rx="10" ry="6" fill="${C.blush}" opacity=".75"/><ellipse cx="${137+dx}" cy="132" rx="10" ry="6" fill="${C.blush}" opacity=".75"/>
  ${mouth(mood,dx)}
  <!-- bangs: soft pointed strands -->
  <path d="M${36+dx} 108 Q${32+dx} 24 ${100+dx} 22 Q${168+dx} 24 ${164+dx} 108 Q${160+dx} 86 ${150+dx} 78 L${144+dx} 104 Q${138+dx} 82 ${128+dx} 74 L${120+dx} 100 Q${112+dx} 78 ${104+dx} 72 L${98+dx} 98 Q${88+dx} 76 ${76+dx} 74 L${68+dx} 102 Q${60+dx} 84 ${50+dx} 88 Q${40+dx} 96 ${36+dx} 108Z" fill="${C.hair}"/>
  <path d="M${62+dx} 38 Q${100+dx} 22 ${140+dx} 38" stroke="${C.hairHi}" stroke-width="6" fill="none" stroke-linecap="round" opacity=".8"/>
  <path d="M${76+dx} 74 Q${82+dx} 52 ${92+dx} 40 M${128+dx} 74 Q${120+dx} 52 ${110+dx} 40" stroke="${C.hairDeep}" stroke-width="2.5" fill="none" stroke-linecap="round"/>
  <!-- side locks -->
  <path d="M${38+dx} 96 Q${30+dx} 140 ${40+dx} 160 L${52+dx} 154 Q${44+dx} 128 ${50+dx} 100Z" fill="${C.hair}"/>
  <path d="M${162+dx} 96 Q${170+dx} 140 ${160+dx} 160 L${148+dx} 154 Q${156+dx} 128 ${150+dx} 100Z" fill="${C.hair}"/>
  ${jimikki(42+dx,158)}${jimikki(158+dx,158)}`;
}
function body(waveArm=false, leftArm=true){
  return `
  <ellipse cx="100" cy="292" rx="46" ry="7" fill="#24132F" opacity=".14"/>
  <!-- legs + flats -->
  <path d="M84 246 L84 278 Q84 284 92 284 L96 284 L98 246Z" fill="${C.ink}"/><path d="M102 246 L104 284 L108 284 Q116 284 116 278 L116 246Z" fill="${C.ink}"/>
  <path d="M84 250 L84 278 L89 278 L89 250Z" fill="${C.inkSh}"/>
  <path d="M78 286 Q78 278 90 278 L98 278 L98 290 L82 290 Q78 290 78 286Z" fill="${C.gold}"/><path d="M78 288 L98 288 L98 291 L82 291Z" fill="${C.goldSh}"/>
  <path d="M122 286 Q122 278 110 278 L102 278 L102 290 L118 290 Q122 290 122 286Z" fill="${C.gold}"/><path d="M102 288 L122 288 L118 291 L102 291Z" fill="${C.goldSh}"/>
  <!-- kurta -->
  <path d="M70 172 Q100 160 130 172 L144 248 Q100 258 56 248Z" fill="${C.plum}"/>
  <path d="M70 172 L62 230 L56 248 Q70 252 82 253 L84 176Z" fill="${C.plumSh}"/>
  <path d="M57 244 Q100 254 143 244 L144 250 Q100 260 56 250Z" fill="${C.gold}"/>
  <path d="M92 166 L100 178 L108 166" fill="none" stroke="${C.gold}" stroke-width="3" stroke-linejoin="round"/>
  <path d="M100 178 V214" stroke="${C.plumHi}" stroke-width="2"/><circle cx="100" cy="186" r="1.6" fill="${C.gold}"/><circle cx="100" cy="196" r="1.6" fill="${C.gold}"/>
  <!-- dupatta over both shoulders -->
  <path d="M70 172 Q78 168 84 176 L80 252 L70 250 Q72 210 70 172Z" fill="${C.pink}"/>
  <path d="M70 172 Q72 210 70 250 L74 250 Q76 210 74 174Z" fill="${C.pinkSh}"/>
  <path d="M130 172 Q122 168 116 176 L122 252 L132 250 Q130 210 130 172Z" fill="${C.pink}"/>
  <path d="M130 172 Q128 210 132 250 L128 251 Q125 210 126 174Z" fill="${C.pinkSh}"/>
  <!-- bag strap + bag -->
  <path d="M120 176 L80 236" stroke="${C.teal}" stroke-width="4" stroke-linecap="round"/>
  <rect x="68" y="228" width="24" height="20" rx="6" fill="${C.teal}"/><rect x="68" y="240" width="24" height="8" rx="4" fill="${C.tealSh}"/>
  ${leftArm?`  <!-- left arm with phone -->
  <path d="M68 178 Q56 204 62 226" stroke="${C.plum}" stroke-width="15" fill="none" stroke-linecap="round"/>
  <path d="M65 182 Q56 204 60 222" stroke="${C.plumSh}" stroke-width="5" fill="none" stroke-linecap="round"/>
  <rect x="52" y="214" width="14" height="24" rx="3.5" fill="${C.teal}" stroke="${C.ink}" stroke-width="2"/><rect x="55" y="218" width="8" height="12" rx="1.5" fill="#BFE6E1"/>
  <circle cx="64" cy="230" r="7.5" fill="${C.skin}"/><path d="M58 233 a7 7 0 0 0 12 0" fill="${C.skinSh}"/>
`:''}
  ${waveArm?'':rightArmDown()}
  <!-- neck -->
  <path d="M92 160 L92 172 Q100 178 108 172 L108 160Z" fill="${C.skinSh}"/>`;
}
function rightArmDown(){
  return `<g><path d="M132 178 Q144 204 138 226" stroke="${C.plum}" stroke-width="15" fill="none" stroke-linecap="round"/>
    <path d="M135 182 Q144 204 140 222" stroke="${C.plumSh}" stroke-width="5" fill="none" stroke-linecap="round"/>
    <circle cx="138" cy="230" r="7.5" fill="${C.skin}"/><path d="M132 233 a7 7 0 0 0 12 0" fill="${C.skinSh}"/></g>`;
}
function rightArm(bake){
  return `<g>
    <path d="M132 180 Q152 180 166 170" stroke="${C.plum}" stroke-width="15" fill="none" stroke-linecap="round"/>
    <g class="arm-r">
      <path d="M166 170 Q176 152 180 136" stroke="${C.plum}" stroke-width="14" fill="none" stroke-linecap="round"/>
      <path d="M169 166 Q177 152 180 140" stroke="${C.plumSh}" stroke-width="4" fill="none" stroke-linecap="round"/>
      <circle cx="181" cy="128" r="8" fill="${C.skin}"/><path d="M176 122 v-6 M181 121 v-8 M186 122 v-6" stroke="${C.skin}" stroke-width="3.6" stroke-linecap="round"/>
      <path d="M175 131 a7 7 0 0 0 12 0" fill="${C.skinSh}"/>
    </g></g>`;
}
function front(mood='smile', state='idle', bakeWave=false){
  const halo = state==='alert' ? `<circle class="halo" cx="100" cy="150" r="124" fill="${C.pink}" opacity=".16"/>` : '';
  const rings = state==='listening' ? `<circle class="ring" cx="100" cy="100" r="84" fill="none" stroke="${C.teal}" stroke-width="3"/><circle class="ring r2" cx="100" cy="100" r="84" fill="none" stroke="${C.teal}" stroke-width="3"/>` : '';
  const think = state==='thinking' ? `<g fill="${C.plum}" opacity=".85"><circle cx="166" cy="30" r="5"/><circle cx="180" cy="16" r="7"/><circle cx="198" cy="0" r="9"/></g>` : '';
  return `<svg viewBox="-20 -14 240 314" class="${state}" role="img" aria-label="AVAL, front view">
  ${halo}<g class="bob">${rings}${think}
    ${body(bakeWave||state==='wave')}
    <g class="braid">${braidChain(150,168,146,238,7)}${jasmine([[148,166],[156,172]],4)}</g>
    ${head(mood)}
    ${(bakeWave||state==='wave')?rightArm(bakeWave):''}
  </g></svg>`;
}
function threeQuarter(){
  return `<svg viewBox="-20 -14 240 314" role="img" aria-label="AVAL, three-quarter view"><g>
    ${body(false)}<g>${braidChain(152,168,150,236,7)}</g>${head('smile',8)}</g></svg>`;
}
function back(){
  return `<svg viewBox="-20 -14 240 314" role="img" aria-label="AVAL, back view"><g>
    <ellipse cx="100" cy="292" rx="46" ry="7" fill="#24132F" opacity=".14"/>
    <path d="M84 246 L84 284 L98 284 L98 246Z M102 246 L102 284 L116 284 L116 246Z" fill="${C.ink}"/>
    <path d="M78 286 Q78 278 90 278 L98 278 L98 290 L82 290Z M122 286 Q122 278 110 278 L102 278 L102 290 L118 290Z" fill="${C.gold}"/>
    <path d="M70 172 Q100 160 130 172 L144 248 Q100 258 56 248Z" fill="${C.plum}"/>
    <path d="M57 244 Q100 254 143 244 L144 250 Q100 260 56 250Z" fill="${C.gold}"/>
    <path d="M66 176 Q100 166 134 176 L140 206 Q100 196 60 206Z" fill="${C.pink}"/><path d="M60 200 Q100 190 140 200 L140 206 Q100 196 60 206Z" fill="${C.pinkSh}"/>
    <path d="M68 178 Q56 204 62 226 M132 178 Q144 204 138 226" stroke="${C.plum}" stroke-width="15" fill="none" stroke-linecap="round"/>
    <circle cx="62" cy="230" r="7.5" fill="${C.skin}"/><circle cx="138" cy="230" r="7.5" fill="${C.skin}"/>
    <path d="M30 104 Q26 22 100 18 Q174 22 170 104 Q170 142 158 162 Q100 176 42 162 Q30 142 30 104Z" fill="${C.hair}"/>
    <path d="M62 38 Q100 22 138 38" stroke="${C.hairHi}" stroke-width="6" fill="none" stroke-linecap="round" opacity=".8"/>
    <path d="M100 26 Q90 90 100 150 M100 26 Q110 90 100 150" stroke="${C.hairDeep}" stroke-width="2.5" fill="none"/>
    ${braidChain(100,150,100,236,8)}
    ${jasmine([[86,146],[94,140],[100,138],[106,140],[114,146],[92,154],[108,154]],4.6)}
    ${jimikki(30,150)}${jimikki(170,150)}
  </g></svg>`;
}
function faceOnly(mood){ return `<svg viewBox="18 8 164 176" role="img" aria-label="AVAL ${mood} face">${head(mood)}</svg>`; }

/* ---------- poses ---------- */
function sparkles(pts){
  return pts.map(([x,y,r])=>`<path d="M${x} ${y-r} Q${x} ${y} ${x+r} ${y} Q${x} ${y} ${x} ${y+r} Q${x} ${y} ${x-r} ${y} Q${x} ${y} ${x} ${y-r}Z" fill="${C.gold}"/>`).join('');
}
function hand(x,y){ return `<circle cx="${x}" cy="${y}" r="8" fill="${C.skin}"/><path d="M${x-6} ${y+3} a7 7 0 0 0 12 0" fill="${C.skinSh}"/>`; }
function armPath(d){ return `<path d="${d}" stroke="${C.plum}" stroke-width="15" fill="none" stroke-linecap="round"/>`; }
function wrapSvg(inner, label, cls=''){ return `<svg viewBox="-20 -14 240 314" class="${cls}" role="img" aria-label="AVAL, ${label}">${inner}</svg>`; }

function cheer(){
  return wrapSvg(`<g transform="rotate(-3 100 290)">
    ${body(true,false)}
    <g>${braidChain(150,168,152,238,7)}</g>
    ${head('happy')}
    ${armPath('M70 182 Q40 176 30 150')}${armPath('M30 150 Q24 132 22 118')}${hand(22,110)}
    ${armPath('M130 182 Q160 176 170 150')}${armPath('M170 150 Q176 132 178 118')}${hand(178,110)}
    ${sparkles([[4,96,9],[196,90,8],[14,64,5],[190,58,6],[100,-2,7]])}
  </g>`, 'cheering');
}
function guide(){
  return wrapSvg(`<g>
    ${body(true,true)}
    <g>${braidChain(150,168,146,238,7)}</g>
    ${head('smile')}
    ${armPath('M132 182 Q160 178 186 168')}
    <circle cx="192" cy="166" r="8" fill="${C.skin}"/><path d="M196 163 l14 -4" stroke="${C.skin}" stroke-width="5" stroke-linecap="round"/>
    <g transform="translate(170 206)"><rect x="-4" y="-16" width="40" height="26" rx="8" fill="${C.teal}"/><path d="M6 -3 h18 m-6 -6 l6 6 l-6 6" stroke="#fff" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round"/></g>
  </g>`, 'guiding the way');
}
function booking(){
  return wrapSvg(`<g>
    ${body(false,false)}
    <g>${braidChain(150,168,146,238,7)}</g>
    ${head('happy')}
    ${armPath('M70 182 Q50 192 42 206')}
    <g transform="rotate(-10 36 180)">
      <rect x="10" y="140" width="46" height="70" rx="8" fill="${C.ink}"/>
      <rect x="14" y="146" width="38" height="58" rx="4" fill="#fff"/>
      <rect x="18" y="150" width="30" height="8" rx="2" fill="${C.teal}"/>
      <g fill="${C.ink}">${[0,1,2,3,4].map(i=>[0,1,2,3,4].map(j=>((i*7+j*3)%4<2)?`<rect x="${20+j*5.4}" y="${164+i*5.4}" width="4.6" height="4.6"/>`:'').join('')).join('')}</g>
      <rect x="18" y="194" width="22" height="5" rx="2" fill="${C.pink}"/>
    </g>
    ${hand(40,208)}
    ${sparkles([[6,128,7],[64,124,5]])}
  </g>`, 'showing her phone ticket');
}
function sideRight(){ return wrapSvg(`<g>${body(false,true)}<g>${braidChain(48,168,52,236,7)}</g>${head('smile',12)}</g>`,'turned right'); }
function sideLeft(){ return wrapSvg(`<g transform="translate(200 0) scale(-1 1)">${body(false,true)}<g>${braidChain(48,168,52,236,7)}</g>${head('smile',12)}</g>`,'turned left'); }

/* ---------- travel scenes (640x360) ---------- */
function passenger(x,y,s,mood='happy',wave=false){
  return `<g transform="translate(${x} ${y}) scale(${s})">
    <path d="M58 176 Q100 160 142 176 L150 230 L50 230Z" fill="${C.plum}"/>
    <path d="M60 176 Q72 170 80 178 L78 230 L64 230Z" fill="${C.pink}"/><path d="M140 176 Q128 170 120 178 L122 230 L136 230Z" fill="${C.pink}"/>
    <path d="M92 166 L100 178 L108 166" fill="none" stroke="${C.gold}" stroke-width="3"/>
    ${braidChain(150,168,148,226,5)}
    ${head(mood)}
    ${wave?`${armPath('M132 190 Q160 186 170 160')}<g class="pw">${armPath('M170 160 Q176 146 178 132')}${hand(179,124)}</g>`:''}
  </g>`;
}
function wheel(x,y,r,hub){
  return `<g class="wheel"><circle cx="${x}" cy="${y}" r="${r}" fill="#1D1B22"/><circle cx="${x}" cy="${y}" r="${hub}" fill="#C9C6D1"/>
    <path d="M${x-hub} ${y} h${hub*2} M${x} ${y-hub} v${hub*2}" stroke="#6E6A78" stroke-width="3"/><circle cx="${x}" cy="${y}" r="3" fill="#1D1B22"/></g>`;
}
function city(y,color){
  let s=''; for(let k=0;k<2;k++) for(let i=0;i<8;i++){const x=k*640+i*80+10, h=40+((i*37)%5)*14;
    s+= i%3===1 ? `<circle cx="${x+30}" cy="${y-28}" r="22" fill="#9ED7A9"/><rect x="${x+27}" y="${y-10}" width="6" height="12" fill="#7A5A44"/>`
                : `<rect x="${x}" y="${y-h}" width="58" height="${h}" rx="4" fill="${color}"/>${[0,1].map(r=>`<rect x="${x+10}" y="${y-h+10+r*18}" width="12" height="9" fill="#fff" opacity=".6"/><rect x="${x+34}" y="${y-h+10+r*18}" width="12" height="9" fill="#fff" opacity=".6"/>`).join('')}`;}
  return `<g class="bg">${s}</g>`;
}
const ANIM = `<style>
.wheel{animation:spin .7s linear infinite;transform-box:fill-box;transform-origin:center}
@keyframes spin{to{transform:rotate(360deg)}}
.road{animation:dash .5s linear infinite}@keyframes dash{to{stroke-dashoffset:-52}}
.ride{animation:ride .45s ease-in-out infinite alternate}@keyframes ride{to{transform:translateY(-2.5px)}}
.bg{animation:pass 9s linear infinite}@keyframes pass{to{transform:translateX(-640px)}}
.sleepers{animation:pass2 .6s linear infinite}@keyframes pass2{to{transform:translateX(-30px)}}
.pw{animation:pwave .9s ease-in-out infinite;transform-box:fill-box;transform-origin:0% 100%}@keyframes pwave{50%{transform:rotate(-18deg)}}
.glow{animation:glow 1.6s ease-in-out infinite}@keyframes glow{50%{opacity:.35}}
@media (prefers-reduced-motion:reduce){*{animation:none!important}}
</style>`;
function sceneFrame(id, sky1, sky2, inner, label){
  return `<svg viewBox="0 0 640 360" role="img" aria-label="${label}"><defs><linearGradient id="sky${id}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="${sky1}"/><stop offset="1" stop-color="${sky2}"/></linearGradient></defs>
  <rect width="640" height="360" fill="url(#sky${id})"/>${ANIM}${inner}</svg>`;
}
function busScene(){
  return sceneFrame('b','#FFE7C2','#FFD1E0',`
  <circle cx="560" cy="70" r="34" fill="#FFC94A" opacity=".85"/>${city(300,"#F2C6D6")}
  <rect x="0" y="300" width="640" height="60" fill="#5C5566"/><path class="road" d="M0 330 h700" stroke="#FFFFFF" stroke-width="4" stroke-dasharray="30 22"/>
  <g class="ride">
    <path d="M70 110 Q70 84 98 84 L560 84 Q590 84 590 112 L590 290 L70 290Z" fill="#F7F7FA"/>
    <rect x="70" y="84" width="520" height="12" rx="6" fill="#E3E1EA"/>
    <rect x="96" y="104" width="470" height="92" rx="10" fill="#22202A"/>
    <clipPath id="busWin"><rect x="290" y="108" width="96" height="84" rx="6"/></clipPath>
    <rect x="290" y="108" width="96" height="84" rx="6" fill="#8FD6E0"/>
    <g clip-path="url(#busWin)">${passenger(282,100,0.5,'happy',true)}</g>
    ${[180,286,390,494].map(x=>`<rect x="${x}" y="104" width="6" height="92" fill="#F7F7FA"/>`).join('')}
    <rect x="186" y="108" width="100" height="84" rx="6" fill="#3A3746" opacity=".5"/>
    <rect x="96" y="104" width="78" height="170" rx="6" fill="#2C2A35"/><rect x="104" y="112" width="28" height="154" rx="4" fill="#8FD6E0" opacity=".55"/><rect x="140" y="112" width="28" height="154" rx="4" fill="#8FD6E0" opacity=".55"/>
    <rect x="70" y="204" width="520" height="34" fill="#35C6C9"/>
    <path d="M70 238 H590 V290 H70Z" fill="${C.plum}"/>
    <rect x="180" y="86" width="150" height="16" rx="3" fill="#1A1820"/><text x="255" y="99" text-anchor="middle" font-size="11" font-weight="800" fill="#FFB52E" font-family="Noto Sans,sans-serif">40H  NUNGAMBAKKAM</text>
    <rect x="400" y="212" width="132" height="22" rx="11" fill="${C.pink}"/><text x="466" y="227" text-anchor="middle" font-size="12" font-weight="800" fill="#fff" font-family="Noto Sans,sans-serif">FREE · இலவசம்</text>
    </g>${wheel(180,292,32,14)}${wheel(480,292,32,14)}<g>
    <rect x="574" y="230" width="16" height="12" rx="3" fill="#FFE27A"/>
  </g>`,'AVAL waving from an electric city bus');
}
function trainScene(){
  return sceneFrame('t','#D9F1FF','#FFF1D6',`
  <rect x="0" y="292" width="640" height="68" fill="#8C8577"/>
  ${city(290,'#CFE3EE')}<rect x="0" y="292" width="640" height="68" fill="#8C8577"/><g class="sleepers">${Array.from({length:24},(_,i)=>`<rect x="${i*30}" y="304" width="16" height="6" fill="#5A5348"/>`).join('')}</g>
  <path d="M0 300 h640 M0 314 h640" stroke="#C9C5BC" stroke-width="4"/>
  <g class="ride">
    <path d="M30 96 L600 96 L600 286 L30 286 Z" fill="#EBD776"/>
    <path d="M30 96 Q30 84 44 84 L600 84 L600 96 Z" fill="#D8C35E"/>
    <rect x="30" y="216" width="570" height="70" fill="#2F7A55"/><rect x="30" y="212" width="570" height="6" fill="#F3DF7A"/>
    ${[70,140,350,420,490].map(x=>`<rect x="${x}" y="118" width="48" height="56" rx="5" fill="#2B3A33"/>${[0,1,2,3].map(i=>`<path d="M${x} ${128+i*12} h48" stroke="#9FB0A6" stroke-width="2"/>`).join('')}`).join('')}
    <rect x="220" y="110" width="100" height="176" rx="6" fill="#1E2A25"/>
    <clipPath id="trainDoor"><rect x="224" y="114" width="92" height="172" rx="4"/></clipPath>
    <rect x="224" y="114" width="92" height="172" rx="4" fill="#BFE3D3"/>
    <rect x="268" y="114" width="4" height="172" fill="#C9C9C9"/>
    <g clip-path="url(#trainDoor)">${passenger(214,118,0.6,'smile')}<path d="M220 286 L320 286 L320 240 L220 240Z" fill="${C.plum}"/></g>
    <rect x="150" y="186" width="56" height="20" rx="4" fill="${C.pink}"/><text x="178" y="200" text-anchor="middle" font-size="10" font-weight="800" fill="#fff" font-family="Noto Sans,sans-serif">LADIES</text>
    <text x="178" y="226" text-anchor="middle" font-size="9" font-weight="700" fill="#fff" font-family="Noto Sans Tamil,sans-serif">மகளிர்</text>
    <path d="M600 96 L626 120 L626 270 L600 286Z" fill="#2F7A55"/><path d="M600 96 L626 120 L626 170 L600 160Z" fill="#2B3A33"/>
    <circle cx="616" cy="236" r="6" fill="#FFF3B0"/>
    ${[110,520].map(x=>`<rect x="${x-40}" y="284" width="80" height="12" rx="4" fill="#3B3B3B"/>`).join('')}
  </g>`,'AVAL at the door of a ladies coach on a suburban train');
}
function metroScene(){
  return sceneFrame('m','#EAF1FF','#F6EFFF',`
  <path d="M0 40 L640 40" stroke="#B9C3D8" stroke-width="10"/>${Array.from({length:9},(_,i)=>`<path d="M${i*80} 40 L${i*80+40} 0" stroke="#B9C3D8" stroke-width="6"/>`).join('')}
  ${city(100,'#D5DDF0')}<rect x="0" y="290" width="640" height="70" fill="#D8DCE6"/><rect x="0" y="290" width="640" height="10" fill="#FFD23F"/>
  <g class="ride">
    <path d="M40 100 L540 100 Q620 100 620 190 L620 280 L40 280Z" fill="#F4F7FD"/>
    <path d="M40 100 L540 100 Q600 100 612 150 L40 150Z" fill="#1F5BDA"/>
    <path d="M40 240 L620 240 L620 280 L40 280Z" fill="#1F5BDA"/>
    <path d="M560 112 Q604 120 612 170 L560 170Z" fill="#14244A"/>
    <rect x="60" y="156" width="430" height="78" rx="10" fill="#14244A"/>
    <clipPath id="metroWin"><rect x="250" y="160" width="110" height="70" rx="8"/></clipPath>
    <rect x="250" y="160" width="110" height="70" rx="8" fill="#A9C4FF"/>
    <g clip-path="url(#metroWin)">${passenger(258,152,0.42,'happy',true)}</g>
    ${[160,370].map(x=>`<rect x="${x}" y="156" width="6" height="78" fill="#F4F7FD"/>`).join('')}
    <rect class="glow" x="600" y="246" width="14" height="10" rx="3" fill="#FFF3B0"/>
    <text x="70" y="128" font-size="15" font-weight="800" fill="#fff" font-family="Noto Sans,sans-serif">METRO · மெட்ரோ</text>
  </g>`,'AVAL waving from a metro train window');
}
function autoScene(){
  return sceneFrame('a','#FFF0C7','#FFDCE4',`
  ${city(300,"#F7D9A8")}<rect x="0" y="300" width="640" height="60" fill="#5C5566"/><path class="road" d="M0 330 h700" stroke="#fff" stroke-width="4" stroke-dasharray="30 22"/>
  <g transform="translate(70 0)"><g class="ride">
    <path d="M150 96 Q160 70 220 70 L400 70 Q440 70 446 110 L452 200 L150 200Z" fill="#1E1C22"/>
    <clipPath id="autoSeat"><path d="M300 104 L436 104 L442 214 L300 214Z"/></clipPath>
    <path d="M300 104 L436 104 L442 214 L300 214Z" fill="#FFE7A8"/>
    <g clip-path="url(#autoSeat)">${passenger(300,96,0.64,'happy',true)}</g>
    <path d="M120 200 Q118 150 160 110 L196 110 L230 196 L300 196 L300 214 L452 214 L460 268 L110 268 Q100 236 120 200Z" fill="#FFC21C"/>
    <path d="M160 116 L194 116 L222 192 L136 192 Q140 146 160 116Z" fill="#9FD3E6" opacity=".85"/>
    <path d="M110 250 L460 250 L460 268 L110 268Z" fill="#E3A700"/>
    <rect x="96" y="220" width="18" height="14" rx="4" fill="#FFF3B0"/>
    </g>${wheel(150,280,26,10)}${wheel(400,280,26,10)}<g>
    <rect x="236" y="214" width="56" height="20" rx="4" fill="#1E1C22"/><text x="264" y="228" text-anchor="middle" font-size="10" font-weight="800" fill="#FFC21C" font-family="Noto Sans,sans-serif">AUTO</text>
  </g></g>`,'AVAL riding in an auto rickshaw');
}

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

export { front, head, faceOnly, back, threeQuarter, cheer, guide, booking, sideLeft, sideRight, busScene, trainScene, metroScene, autoScene, featShops, featConnect, featBus, featPay, featTrip, featSOS, combined };
