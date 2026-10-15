import * as E from './engine.js';
const c=document.querySelector('canvas'),g=c.getContext('2d');
E.setAccent('#6DE4CB'); E.FONT.ui='Inter, TC'; E.FONT.disp='Inter, TC'; E.FONT.mono='Inter, TC';
const A=E.PAL.accent, C=E.clamp, L=E.lerp;
const timeline=[0,3.927,8.542,14.458,18.062,21.448,25.635,30];
const names=['一滴水，如何變成雨','蒸發','凝結','碰撞與合併','降雨','回到海洋','旅程，再次開始'];
const sub=await (await fetch('./subtitles.json')).json();
const dot=(ctx,x,y,r,col='#AAB2C1',a=1)=>{ctx.save();ctx.globalAlpha*=a;ctx.fillStyle=col;ctx.beginPath();ctx.arc(x,y,r,0,Math.PI*2);ctx.fill();ctx.restore()};
function txt(ctx,s,x,y,n=36,col='#E8EAF0',align='left',wt=500){ctx.font=`${wt} ${n}px Inter, TC`;ctx.fillStyle=col;ctx.textAlign=align;ctx.textBaseline='middle';ctx.fillText(s,x,y)}
function drop(ctx,x,y,r,accent=true,stretch=1){ctx.save();ctx.translate(x,y);ctx.scale(1,stretch);const p=new Path2D();p.moveTo(0,-r*1.38);p.bezierCurveTo(r*.18,-r*.75,r,-r*.12,r,r*.44);p.bezierCurveTo(r,r*1.47,-r,r*1.47,-r,r*.44);p.bezierCurveTo(-r,-r*.12,-r*.18,-r*.75,0,-r*1.38);E.litShape(ctx,p,{accent,glowR:accent?34:0,bbox:[-r,-r*1.38,r*2,r*2.88]});ctx.restore()}
function waves(ctx,t,y=1220){ctx.save();ctx.beginPath();ctx.rect(130,540,820,820);ctx.clip();for(let j=0;j<8;j++){ctx.beginPath();for(let x=100;x<=990;x+=6){const yy=y+j*18+Math.sin(x/85-t*1.5+j*.4)*14;if(x===100)ctx.moveTo(x,yy);else ctx.lineTo(x,yy)}ctx.strokeStyle=`rgba(175,189,208,${.75-j*.07})`;ctx.lineWidth=j===0?4:2;ctx.stroke()}ctx.restore()}
function label(ctx,s,y=1430){txt(ctx,s,540,y,30,'#8A90A0','center')}
function phase(ctx,k,t,u){
 const cam= k===0?L(1.35,1,E.eo(C(u/.8))): k===1?L(1,1.1,E.ss(u)): k===2?1.05: k===3?L(1,1.2,E.ss(u)):k===4?1.1:k===5?L(1.1,1,E.ss(u)):1;
 ctx.save();ctx.translate(540,930);ctx.scale(cam,cam);ctx.translate(-540,-930);
 if(k===0){
  drop(ctx,540,900,150,true,1+.035*Math.exp(-t*3)*Math.cos(t*12));
  ctx.strokeStyle='#3b4352';ctx.lineWidth=2;ctx.beginPath();ctx.arc(540,900,240,-Math.PI/2,-Math.PI/2+C(t/2.8)*Math.PI*2);ctx.stroke();
  txt(ctx,'H₂O',540,1190,40,'#8A90A0','center');label(ctx,'水循環觀測介面',1360);
 }
 if(k===1){
  waves(ctx,t);txt(ctx,'海洋',180,1330,28,'#8A90A0');
  for(let i=0;i<54;i++){
   const p=((t-timeline[1])*.22+i*.127)%1;
   const x0=190+(i%13)*56, x=x0+Math.sin(p*Math.PI)*100*(i%2?1:-1),y=L(1205,620,E.ss(p));
   const r=i===0?16:6+(i%4)*2;dot(ctx,x,y,r,i===0?A:'#CDD3DE',C(p*10)*C((1-p)*10));
  }
  ctx.strokeStyle='#858e9d';ctx.lineWidth=3;for(let i=0;i<4;i++){const x=310+i*150,y=690;ctx.beginPath();ctx.moveTo(x,y+80);ctx.lineTo(x,y);ctx.lineTo(x-12,y+17);ctx.moveTo(x,y);ctx.lineTo(x+12,y+17);ctx.stroke()}
  label(ctx,'加熱 → 液態水變成水氣');txt(ctx,'粒子為示意；水氣本身看不見',540,1490,23,'#5C6272','center');
 }
 if(k===2 || k===3){
  const local=t-timeline[2];
  for(let i=0;i<105;i++){
   const angle=i*2.399963,rad=Math.sqrt(i/105),tx=540+Math.cos(angle)*rad*300,ty=900+Math.sin(angle)*rad*170;
   const p=E.eo(C((local-i*.015)/3.1));
   const x=L(120+(i*137)%830,tx,p), y=L(1260+(i%9)*20,ty,p);
   const target= k===3?E.ss(C((t-timeline[3])/(timeline[4]-timeline[3]))):0;
   const xx=L(x,540,target*.95), yy=L(y,920,target*.95);
   dot(ctx,xx,yy,(8+i%6)*(1-target*.5),'#C6CCD6',.7);
  }
  const p=E.ss(C((local-.5)/3));
  ctx.strokeStyle='#5C6272';ctx.lineWidth=2;ctx.setLineDash([4,12]);ctx.beginPath();ctx.ellipse(540,900,360,240,0,0,Math.PI*2);ctx.stroke();ctx.setLineDash([]);
  if(k===2){dot(ctx,540,900,24,A);txt(ctx,'凝結核',540,1210,28,'#8A90A0','center');label(ctx,'水氣遇冷，凝結成小水滴')}
  else {const q=E.ss(u);drop(ctx,540,930,30+115*q,true);label(ctx,'小水滴合併，逐漸長大')}
 }
 if(k===4){
  const elapsed=t-timeline[4];
  for(let i=0;i<10;i++){const xx=220+i*71,yy=650+(i%3)*28;dot(ctx,xx,yy,75,'#A7AFBF',.7)}
  const p=C(elapsed/2.35),dy=L(730,1230,p*p);
  for(let i=0;i<18;i++){const pp=((elapsed*.5+i*.137)%1);drop(ctx,180+i%7*115,790+pp*440,7+i%3,false,1.4)}
  if(p<.96)drop(ctx,540,dy,110,true,1+.15*p);
  waves(ctx,t,1270);
  const r=C((p-.82)/.18)*210;ctx.strokeStyle=E.rgba(A,1-C((p-.82)/.18));ctx.lineWidth=4;ctx.beginPath();ctx.ellipse(540,1260,r,r*.23,0,0,Math.PI*2);ctx.stroke();
  label(ctx,'上升氣流托不住，便落成雨');
 }
 if(k===5){
  // A moving river path, returning the single accent node to the sea.
  const path=[];for(let j=0;j<=120;j++){let q=j/120;path.push([540+Math.sin(q*5.3)*230,L(610,1240,q)])}
  ctx.lineCap='round';ctx.strokeStyle='#303846';ctx.lineWidth=90;ctx.beginPath();path.forEach(([x,y],j)=>j?ctx.lineTo(x,y):ctx.moveTo(x,y));ctx.stroke();
  ctx.strokeStyle='#8A94A5';ctx.lineWidth=3;ctx.stroke();
  const p=C(u*1.13),at=Math.min(120,Math.floor(p*120));E.trail(ctx,path.slice(Math.max(0,at-20),at+1),{width:14,color:A});drop(ctx,...path[at],27,true);
  waves(ctx,t,1270);label(ctx,'河川將水送回海洋');
 }
 if(k===6){
  const pts=[[540,680],[800,1140],[280,1140]],labs=['蒸發','凝結','降雨'];
  for(let i=0;i<3;i++){
   const a=pts[i],b=pts[(i+1)%3];ctx.strokeStyle='#4E586A';ctx.lineWidth=3;ctx.beginPath();ctx.moveTo(...a);ctx.lineTo(...b);ctx.stroke();
   E.panel(ctx,a[0]-120,a[1]-80,240,160,{r:26,fill:'#1A1E28'});txt(ctx,labs[i],a[0],a[1],40,'#E8EAF0','center',600);
  }
  const p=((t-timeline[6])*.45)%3,i=Math.floor(p),q=p-i,a=pts[i],b=pts[(i+1)%3];dot(ctx,L(a[0],b[0],q),L(a[1],b[1],q),16,A);
  txt(ctx,'沒有終點的水循環',540,1430,33,'#8A90A0','center');
 }
 ctx.restore();
}
function render(t){
 g.setTransform(1,0,0,1,0,0);g.clearRect(0,0,1080,1920);E.bg(g,{cool:.35});E.grid(g,{module:48});
 const k=Math.min(6,timeline.findIndex((v,i)=>i<7&&t>=v&&t<timeline[i+1]));const kk=k<0?6:k,u=C((t-timeline[kk])/(timeline[kk+1]-timeline[kk]));
 txt(g,'WATER / CYCLE',84,115,25,'#8A90A0');txt(g,'水循環觀測',996,115,25,'#8A90A0','right');
 const title=names[kk];txt(g,title,540,286,kk===0?61:72,'#E8EAF0','center',650);
 // Expand the live UI surface at each new observation; no still images.
 const enter=E.back(C((t-timeline[kk])/.46),1.3),scale=.84+.16*enter;
 const [b,bg]=E.buf('observation',1080,1920);bg.clearRect(0,0,1080,1920);
 E.panel(bg,84,440,912,1120,{r:32,fill:'#12151C'});txt(bg,'OBSERVATION  /  '+['H₂O','EVAPORATION','CONDENSATION','COALESCENCE','RAINFALL','RETURN','CYCLE'][kk],132,494,22,'#8A90A0');
 phase(bg,kk,t,u);
 g.save();g.translate(540,1000);g.scale(scale,scale);g.translate(-540,-1000);
 E.lightReveal(g,b,0,0,1080,1920,C((t-timeline[kk]+.3)/1),{base:.42,glint:.14,soft:240});g.restore();
 for(let i=0;i<3;i++){const yy=1620,x=144+i*300;E.panel(g,x,yy,192,68,{r:20,cheap:true});txt(g,['蒸發','凝結','降雨'][i],x+96,yy+34,27,'#8A90A0','center');if((kk===1&&i===0)||((kk===2||kk===3)&&i===1)||(kk===4&&i===2))dot(g,x+22,yy+34,5,A)}
 E.vignette(g,.5);
 const line=sub.find(x=>t>=x.start&&t<x.end);if(line){
 const lines=[];let s=line.text;while(s.length>18){let br=18;for(let j=18;j>10;j--)if('，、。？'.includes(s[j-1])){br=j;break}lines.push(s.slice(0,br));s=s.slice(br)}if(s)lines.push(s);
 const h=lines.length*54+40,y=1820-h;E.panel(g,66,y,948,h,{r:30,fill:'#11151C'});dot(g,102,y+h/2,7,A);lines.forEach((s,i)=>txt(g,s,140,y+42+i*54,38));
 }
}
window.render=render;window.ready=false;await document.fonts.load('500 40px TC');await document.fonts.load('500 40px Inter');await document.fonts.ready;render(0);window.ready=true;
