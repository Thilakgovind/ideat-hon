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
