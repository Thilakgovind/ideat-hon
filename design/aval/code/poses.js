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
    <rect x="180" y="86" width="150" height="16" rx="3" fill="#1A1820"/><text x="255" y="99" text-anchor="middle" font-size="11" font-weight="800" fill="#FFB52E" font-family="Noto Sans,sans-serif">21G  NUNGAMBAKKAM</text>
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
