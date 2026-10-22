// Original, deterministic character animation for the approved 2B treatment.
// No external model or runtime network access. All motion is evaluated by frame.
export function setupScene(root, data) {
  const stage=root.querySelector('#stage'), bg=root.querySelector('#backdrop'), label=root.querySelector('#label'), kicker=root.querySelector('#kicker');
  const virtual=root.querySelector('#virtual');if(virtual)virtual.style.transform='scale('+(root.clientWidth/540)+')';
  const clamp=(x,a=0,b=1)=>Math.max(a,Math.min(b,x));
  const ease=x=>1-Math.pow(1-clamp(x),3);
  const mix=(a,b,t)=>a+(b-a)*t;
  const defs=`<defs><linearGradient id="page" x2="0" y2="1"><stop stop-color="#fff5d5"/><stop offset="1" stop-color="#cda56a"/></linearGradient><linearGradient id="gold"><stop stop-color="#ffe6a5"/><stop offset="1" stop-color="#c18b43"/></linearGradient><radialGradient id="glow"><stop stop-color="#ffe898" stop-opacity=".9"/><stop offset="1" stop-color="#ffa93a" stop-opacity="0"/></radialGradient><filter id="shadow"><feDropShadow dx="0" dy="8" stdDeviation="7" flood-opacity=".35"/></filter></defs>`;
  function person(x,y,s,role='hero',phase=0,action='walk') {
    const hero=role==='hero', colors={hero:'#ffd84b',fuxi:'#368f86',nuwa:'#ed9387',shennong:'#b58148',suiren:'#926542'};
    const wave=Math.sin(phase), step=action==='walk'?wave*22:0, bob=action==='walk'?Math.abs(Math.sin(phase))*4:Math.sin(phase)*1.5;
    const right=action==='point'?[50,-104]:action==='draw'?[49+wave*12,-26]:action==='lift'?[48,-160]:action==='collect'?[53,-8]:action==='open'?[58,-82]:[29-step,-43];
    const left=action==='open'?[-58,-82]:[-29+step,-43];
    const robe=hero?`<path d="M-24-106L24-106L32-55L-32-55Z" fill="${colors[role]}"/><path d="M-25-55H25V-30H5V-45H-5V-30H-25Z" fill="#253238"/>`:`<path d="M-26-108L26-108L45-25Q0-10-45-25Z" fill="${colors[role]}"/><path d="M-24-102L0-76L24-102M0-76V-25" fill="none" stroke="#f3d7a3" stroke-width="5"/>`;
    let accessory='';
    if(hero) accessory='<path d="M-34-146Q-34-191 0-191Q34-191 34-146Z" fill="#e94a3d" stroke="#17232b" stroke-width="5"/><path d="M-36-152H36V-137H-36Z" fill="#f35a4b" stroke="#17232b" stroke-width="4"/>';
    else if(role==='shennong') accessory='<path d="M-45-148L0-178L45-148Z" fill="#d5b76f" stroke="#293335" stroke-width="5"/><path d="M-39-54Q-63-80-75-42L-67-5L-30-10Z" fill="#a66f3d" stroke="#293335" stroke-width="5"/><path d="M-53-48L-62-85M-52-55L-35-83" stroke="#508553" stroke-width="8"/>';
    else accessory='<path d="M-31-147Q-29-178 0-174Q30-179 31-146" fill="#25363b" stroke="#17232b" stroke-width="5"/><circle cx="0" cy="-177" r="10" fill="#25363b"/>';
    return `<g transform="translate(${x} ${y+bob}) scale(${s})" filter="url(#shadow)"><ellipse cy="8" rx="52" ry="10" fill="#081b25" opacity=".32"/><g stroke="#182a32" stroke-width="10" stroke-linecap="round" stroke-linejoin="round" fill="none"><path d="M-12-34L${-17-step} 0L${-27-step} 3M12-34L${17+step} 0L${29+step} 3"/><path d="M-21-97L-35-71L${left[0]} ${left[1]}M21-97L38-75L${right[0]} ${right[1]}"/></g><g stroke="#182a32" stroke-width="5" stroke-linejoin="round">${robe}<circle cy="-137" r="34" fill="#fff6de"/></g><g fill="#233039"><circle cx="-10" cy="-133" r="3.6"/><circle cx="10" cy="-133" r="3.6"/></g><path d="M-6-120Q0-116 6-120" stroke="#233039" fill="none" stroke-width="3" stroke-linecap="round"/>${accessory}</g>`;
  }
  function book(x,y,s,opening=1){return `<g transform="translate(${x} ${y}) scale(${s})" filter="url(#shadow)"><rect x="-180" y="-112" width="360" height="236" rx="12" fill="#503735" stroke="#daa85b" stroke-width="7"/><g transform="scale(${Math.max(.04,opening)} 1)"><path d="M0-92Q-95-126-166-97V98Q-85 76 0 108Q85 76 166 98V-97Q95-126 0-92Z" fill="url(#page)" stroke="#715640" stroke-width="4"/><path d="M0-92V108" stroke="#85633e" stroke-width="4"/><circle cx="-80" cy="0" r="35" fill="none" stroke="#b98a4c" stroke-width="5"/><path d="M-110 35L-60-35M-113-22L-50 23M55-38H128M55-15H128M55 8H128M55 31H105" fill="none" stroke="#b98a4c" stroke-width="4"/></g></g>`;}
  function trigram(cx,cy,s,reveal){let lines='';for(let j=0;j<8;j++){let a=j*Math.PI/4,xx=Math.cos(a)*55,yy=Math.sin(a)*55; for(let k=0;k<3;k++){const vis=clamp(reveal*24-j*3-k);lines+=`<path d="M-16 ${k*7}H16" transform="translate(${cx+xx*s} ${cy+yy*s}) rotate(${j*45}) scale(${s})" fill="none" stroke="#ffe0a1" stroke-width="3" stroke-dasharray="32" stroke-dashoffset="${32*(1-vis)}"/>`;}}return `<circle cx="${cx}" cy="${cy}" r="${80*s}" fill="#193b39" opacity=".85"/>${lines}<circle cx="${cx}" cy="${cy}" r="${21*s}" fill="#f5d697"/><path d="M${cx} ${cy-21*s}Q${cx+25*s} ${cy-8*s} ${cx} ${cy}Q${cx-25*s} ${cy+8*s} ${cx} ${cy+21*s}" fill="#183d3c"/>`;}
  function herb(x,y,s){return `<g transform="translate(${x} ${y}) scale(${s})"><path d="M0 8V-60" stroke="#335b37" stroke-width="6"/><path d="M0-30Q-45-64-32-17Q-12-7 0-20M0-45Q37-79 33-38Q17-22 0-29M0-8Q30-33 29-6Q13 8 0 0" fill="#6ba55a" stroke="#274734" stroke-width="3"/></g>`;}
  function scroll(x,y,s,variant,open){let portraits=variant?['fuxi','shennong','suiren']:['fuxi','nuwa','shennong'];return `<g transform="translate(${x} ${y}) scale(${s})"><g transform="scale(${open} 1)"><rect x="-116" y="-198" width="232" height="278" fill="url(#page)" stroke="#79553c" stroke-width="4"/>${portraits.map((r,i)=>person(-70+i*70,3,.46,r,i,'point')).join('')}<path d="M-82 34H82" stroke="#bc8d4e" stroke-width="3"/></g><path d="M${-116*open}-207V91M${116*open}-207V91" stroke="#8b5836" stroke-width="13" stroke-linecap="round"/></g>`;}
  function sparkles(t,count=20){return Array.from({length:count},(_,i)=>{let x=(i*71+Math.sin(t*.7+i)*22)%540,y=(i*113-t*(12+i%7)+6000)%960,r=1.2+(i%3);return `<circle cx="${x}" cy="${y}" r="${r}" fill="#ffe8ad" opacity="${.25+.3*Math.sin(t+i)**2}"/>`;}).join('');}
  return frame=>{
    const t=frame/30, ph=t*5, cuts=data.cuts||[0,10,20,30];
    // Actual narration anchors determine semantic scene changes; local actions unfold inside them.
    const a=cuts[1],b=cuts[2],u=t<a?t/a*10:t<b?10+(t-a)/(b-a)*10:20+(t-b)/(30-b)*10;
    let panel=0, content='',title='',top='傳說中的文明起源', zoom=1.03+Math.sin(t*.13)*.025, pan=Math.sin(t*.12)*3;
    if(u<2.5){const p=ease(u/2.2);content=book(270,430,1.03,p)+person(270-110*p,680,1.25,'hero',ph,'open');title='三皇是哪三個？';}
    else if(u<6.8){const q=u-2.5;content=person(100+q*9,705,1.05,'hero',ph,'walk');['fuxi','nuwa','shennong'].forEach((r,i)=>{const z=ease((q-i*.5)/.7);content+=`<g opacity="${z}" transform="translate(0 ${30*(1-z)})">${person(190+i*115,515+i*28,.85,r,ph+i,'point')}</g>`;});title='伏羲・女媧・神農';top='三皇的其中一種說法';}
    else if(u<12.7){const q=u-6.8;content=`<ellipse cx="285" cy="645" rx="165" ry="58" fill="#617874" stroke="#263e40" stroke-width="6"/>${trigram(280,625,1.15,ease(q/2.5))}`+person(175,615,1.4,'fuxi',ph,'draw')+person(425,760,.95,'hero',ph,'point');title='伏羲畫八卦';top='傳說';zoom=1.06;}
    else if(u<16.2){panel=1;const q=u-12.7,p=ease(q/2.7);content=`<circle cx="290" cy="285" r="${100+30*p}" fill="url(#glow)"/><path d="M280 110L252 175L295 214L266 282L302 325" fill="none" stroke="#ffe4a0" stroke-width="${7-5*p}" opacity="${1-p*.8}"/>`+person(275,570-140*p,1.35,'nuwa',ph,'lift')+`<path d="M${335} ${350-135*p}l16-12 16 8-5 22-21 4Z" fill="#9ce3d9" stroke="#fff0b0" stroke-width="3"/>`+person(95,735,.98,'hero',ph,'point');title='女媧補天';top='傳說';}
    else if(u<20){panel=0;const q=u-16.2;content=person(285,650,1.5,'shennong',ph,'collect')+herb(340,655,1)+herb(165,705,.8)+person(100+q*10,780,1,'hero',ph,'walk');title='神農嘗百草';top='文明起源的傳說';}
    else if(u<23.6){panel=2;const q=u-20;content=`<ellipse cx="274" cy="675" rx="140" ry="100" fill="url(#glow)"/>`+person(160,640,1.2,'suiren',ph,'draw')+person(405-q*12,760,1,'hero',ph,'walk')+Array.from({length:8},(_,i)=>`<circle cx="${267+Math.sin(ph+i)*18}" cy="${595-((q*45+i*16)%160)}" r="${2+i%3}" fill="#ffda78" opacity=".7"/>`).join('');title='也有版本列入燧人';top='不同文獻・不同組合';}
    else if(u<28.3){panel=2;const q=u-23.6;content=scroll(145,480,.93,false,ease(q/.6))+scroll(400,555,.93,true,ease((q-.35)/.6))+person(270,795,1.1,'hero',ph,'open');title='先看採用哪種說法';top='三皇沒有唯一固定名單';}
    else {panel=0;const p=ease((u-28.3)/1.4);content=book(270,435,mix(.92,1.1,p),1-p)+person(150,735,1.12,'hero',ph,'point');title='你聽過哪一版？';top='三皇是哪三個';}
    bg.style.backgroundPosition=`${panel*50}% center`;bg.style.transform=`scale(${zoom}) translateY(${pan}px)`;
    stage.innerHTML=`${defs}${sparkles(t)}${content}`;
    label.textContent=title;kicker.textContent=top;
    // Short light wipes mask deliberate location cuts without deforming characters.
    const nearest=[2.5,6.8,12.7,16.2,20,23.6,28.3].reduce((m,c)=>Math.min(m,Math.abs(u-c)),10);
    root.querySelector('#wipe').style.opacity=String(Math.max(0,1-nearest/.13)*.6);
  };
}

