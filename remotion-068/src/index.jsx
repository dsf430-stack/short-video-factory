import React from 'react';
import {registerRoot,Composition,AbsoluteFill,Sequence,Audio,staticFile,useCurrentFrame,interpolate,spring} from 'remotion';
const fps=30;
const slides=[
 {title:'為什麼存不到錢？',sub:'每天一杯飲料，花費悄悄累積',amount:'每天 60 元',kind:'cup'},
 {title:'一個月是多少？',sub:'60 × 30 = 1,800',amount:'1,800 元',kind:'calculator'},
 {title:'一年又是多少？',sub:'1,800 × 12 = 21,600',amount:'21,600 元',kind:'chart'},
 {title:'小改變，大不同',sub:'每週少買幾杯，開始存下第一筆錢',amount:'從今天開始',kind:'pig'}
];
function Sketch({kind,frame}){
 const p=interpolate(frame,[4,55],[0,1],{extrapolateLeft:'clamp',extrapolateRight:'clamp'});
 const common={fill:'none',stroke:'#182b3c',strokeWidth:9,strokeLinecap:'round',strokeLinejoin:'round',pathLength:100,strokeDasharray:100,strokeDashoffset:100*(1-p)};
 return <svg viewBox="0 0 700 600" style={{width:730,height:640}}>
 {kind==='cup'&&<><path {...common} d="M215 160 H480 L444 475 Q350 520 248 475 Z"/><path {...common} d="M250 310 Q350 260 452 310"/><path {...common} d="M320 130 L405 40"/></>}
 {kind==='calculator'&&<><rect x="195" y="70" width="310" height="460" rx="32" {...common}/><rect x="245" y="125" width="210" height="100" rx="10" {...common}/>{[0,1,2].map(i=>[0,1,2].map(j=><circle key={i+'-'+j} cx={278+j*72} cy={304+i*82} r="19" {...common}/>))}</>}
 {kind==='chart'&&<><path {...common} d="M125 500 H570 M135 500 V140"/><path {...common} d="M190 440 L300 350 L395 275 L530 105"/><path {...common} d="M495 110 L530 105 L535 165"/></>}
 {kind==='pig'&&<><path {...common} d="M170 300 Q150 180 310 170 Q500 135 535 280 Q580 360 520 420 L490 480 H430 L420 445 H305 L295 480 H235 L223 420 Q160 380 170 300 Z"/><circle cx="450" cy="280" r="10" fill="#182b3c"/><path {...common} d="M310 185 V140 H405 V185 M190 300 L135 280"/></>}
 </svg>
}
function Scene({index}){
 const frame=useCurrentFrame(),s=slides[index],appear=spring({frame,fps,config:{damping:16}});
 return <AbsoluteFill style={{backgroundColor:'#fffdf5',color:'#172c3b',fontFamily:'Noto Sans CJK TC, Noto Sans TC, sans-serif',alignItems:'center'}}>
  <div style={{position:'absolute',top:105,fontWeight:900,fontSize:68,textAlign:'center',width:'94%',transform:`translateY(${(1-appear)*45}px)`,opacity:appear}}>{s.title}</div>
  <div style={{position:'absolute',top:345}}><Sketch kind={s.kind} frame={frame}/></div>
  <div style={{position:'absolute',top:1080,fontSize:76,color:'#d95131',fontWeight:900,opacity:interpolate(frame,[25,60],[0,1],{extrapolateRight:'clamp'})}}>{s.amount}</div>
  <div style={{position:'absolute',top:1280,fontSize:40,width:'86%',textAlign:'center',lineHeight:1.6}}>{s.sub}</div>
  <div style={{position:'absolute',bottom:120,width:'85%',height:7,background:'#eee'}}><div style={{background:'#d95131',height:'100%',width:`${frame/150*100}%`}}/></div>
 </AbsoluteFill>
}
function Video(){return <AbsoluteFill style={{backgroundColor:'white'}}>{slides.map((_,i)=><Sequence key={i} from={i*150} durationInFrames={150}><Scene index={i}/></Sequence>)}<Audio src={staticFile('audio/voice.mp3')}/></AbsoluteFill>}
const Root=()=> <Composition id="Whiteboard068" component={Video} fps={30} durationInFrames={600} width={1080} height={1920}/>;
registerRoot(Root);
