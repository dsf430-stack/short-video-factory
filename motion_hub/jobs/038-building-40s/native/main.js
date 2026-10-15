// 038 高樓建造：Lemo tilt-shift 原生 Three.js 場景。
// 在 GitHub Runner 中將本目錄複製到固定 commit 的 styles/tilt-shift/demo/038-building/；
// 透過 ../post.js 使用官方 128-tap 移軸後製，而非 Canvas 假移軸。
import * as THREE from 'three';
import {makePost} from '../post.js';
const W=1080,H=1920,DUR=40;
const stage=document.getElementById('stage'),overlay=document.getElementById('ov'),ctx=overlay.getContext('2d');
const renderer=new THREE.WebGLRenderer({antialias:false,preserveDrawingBuffer:true,powerPreference:'high-performance'});
renderer.setSize(W,H);renderer.setPixelRatio(1);renderer.toneMapping=THREE.NeutralToneMapping;
renderer.shadowMap.enabled=true;renderer.shadowMap.type=THREE.PCFSoftShadowMap;stage.appendChild(renderer.domElement);
const scene=new THREE.Scene();scene.background=new THREE.Color('#b9d5e6');scene.fog=new THREE.Fog('#c8dbe8',250,820);
const camera=new THREE.PerspectiveCamera(29,W/H,1,1500);
const post=makePost(renderer,scene,camera,W,H,{ssaa:1,ao:false});
post.dof.band={y:.51,w:.055,amp:30,mix:.7,tilt:0,pow:1.2};post.dof.aper=5000;post.dof.maxCoc=30;
post.grade.uniforms.sat.value=1.55;post.grade.uniforms.contrast.value=.42;post.grade.uniforms.amt.value=.3;
const hemi=new THREE.HemisphereLight('#d7e7ff','#bda77d',1.45);scene.add(hemi);
const sun=new THREE.DirectionalLight('#fff0d7',3.2);sun.position.set(-110,200,130);sun.castShadow=true;sun.shadow.mapSize.set(2048,2048);Object.assign(sun.shadow.camera,{left:-180,right:180,top:180,bottom:-180,near:1,far:700});scene.add(sun);
const mat=(color,roughness=.8,metalness=0)=>new THREE.MeshStandardMaterial({color,roughness,metalness});
const concrete=mat('#d6d3c8'),steel=mat('#747b80',.52,.35),glass=mat('#3f9bbd',.14,.38),asphalt=mat('#4c555c'),soil=mat('#927a59'),grass=mat('#77a65d'),craneYellow=mat('#efb02a',.55,.2),white=mat('#f4ead9');
function block(w,h,d,m,x,y,z){const o=new THREE.Mesh(new THREE.BoxGeometry(w,h,d),m);o.position.set(x,y,z);o.castShadow=true;o.receiveShadow=true;scene.add(o);return o}
block(440,1,440,grass,0,-1,0);block(45,.5,440,asphalt,-116,-.4,0);block(440,.5,42,asphalt,0,-.4,130);
const lot=block(78,.5,72,soil,0,-.3,0);const basement=block(64,2,60,steel,0,-2,0);
const slabs=[],columns=[],windows=[],rails=[];
for(let f=0;f<22;f++){
 const slab=block(59,1.5,54,concrete,0,f*4.2+1.4,0);slabs.push(slab);
 const level=[];
 for(const x of [-26,0,26])for(const z of [-23,0,23])level.push(block(1.8,3.8,1.8,steel,x,f*4.2+3.5,z));
 columns.push(level);
 const glazing=[];
 for(let j=-4;j<=4;j++){glazing.push(block(4.6,3.6,.4,glass,j*5.8,f*4.2+3.5,27.3));glazing.push(block(.4,3.6,4.6,glass,30,f*4.2+3.5,j*5.8))}
 windows.push(glazing);
}
const roof=block(59,1,54,concrete,0,95,0);
for(let i=0;i<11;i++){const x=-170+i*32;block(16,12+(i%4)*7,18,mat(['#eadbc1','#d9b8a4','#b8d0c5'][i%3]),x,6+(i%4)*3.5,-115);block(16,.5,18,steel,x,12+(i%4)*7,-115)}
const craneTower=block(2,110,2,craneYellow,52,54,2);
const craneBoom=block(115,1.8,1.8,craneYellow,22,109,2);
const cable=block(.2,25,.2,steel,8,94,2);
const load=block(9,2,7,concrete,8,80,2);
const excavators=[];
for(let i=0;i<3;i++){const e=new THREE.Group();scene.add(e);const body=new THREE.Mesh(new THREE.BoxGeometry(9,3,6),craneYellow);body.position.y=2.8;e.add(body);const arm=new THREE.Mesh(new THREE.BoxGeometry(1.2,9,1.2),craneYellow);arm.position.set(3,6,0);arm.rotation.z=-.6;e.add(arm);const bucket=new THREE.Mesh(new THREE.BoxGeometry(3,2,3),steel);bucket.position.set(6,9,0);e.add(bucket);excavators.push(e)}
const trucks=[];
for(let i=0;i<6;i++){const g=new THREE.Group();const a=new THREE.Mesh(new THREE.BoxGeometry(10,3,5),mat(i%2?'#f2c142':'#eee9dc'));a.position.y=2.5;g.add(a);const b=new THREE.Mesh(new THREE.BoxGeometry(5,4,5),mat('#ddd9cf'));b.position.set(3,4,0);g.add(b);scene.add(g);trucks.push(g)}
const workers=[];
for(let i=0;i<20;i++){const o=block(.9,2,.9,mat(['#f1bf28','#eb734c','#e7eee4'][i%3]),0,1,0);workers.push(o)}
const clamp=(x,a=0,b=1)=>Math.min(b,Math.max(a,x));
function text(t){ctx.clearRect(0,0,W,H);const names=['整地與機具進場','開挖地基','地下結構與基礎','塔吊吊裝與樓層施工','玻璃帷幕逐層安裝','高樓完工'];let n=t<5?0:t<10?1:t<15?2:t<28?3:t<36?4:5;ctx.fillStyle='rgba(19,80,55,.94)';ctx.fillRect(50,1690,980,130);ctx.strokeStyle='#fff';ctx.lineWidth=4;ctx.strokeRect(60,1700,960,110);ctx.fillStyle='#fff';ctx.textAlign='center';ctx.font='bold 48px sans-serif';ctx.fillText(names[n],540,1774);ctx.textAlign='left';ctx.font='bold 30px monospace';ctx.fillStyle='#f6c24b';ctx.fillText(t>37?'×1 REAL TIME':'×40 TIME-LAPSE',62,110)}
function render(t){t=clamp(t,0,DUR);const fast=Math.floor(t*8)/8,build=clamp((fast-12)/19),clad=clamp((fast-27)/9);
lot.position.y=t<5?-.3:t<11?-2.8:-.3;basement.visible=t>=9;
for(let f=0;f<22;f++){const shown=build*22>f;slabs[f].visible=shown;for(const c of columns[f])c.visible=shown;for(const pane of windows[f])pane.visible=clad*22>f}
roof.visible=build>=1;craneTower.visible=craneBoom.visible=cable.visible=load.visible=t>=6&&t<37;
cable.position.x=load.position.x=15+Math.sin(fast*1.7)*22;load.position.y=74+Math.sin(fast*1.4)*8;cable.position.y=(109+load.position.y)/2;cable.scale.y=(109-load.position.y)/25;
for(let i=0;i<3;i++){const e=excavators[i];e.visible=t<12;e.position.set(-28+i*25+Math.sin(fast*.8+i)*5,0,12+i*9);e.rotation.y=.25*Math.sin(fast+i)}
for(let i=0;i<6;i++){const v=trucks[i];v.position.set(-116,0,((fast*22+i*70)%420)-210);v.visible=true}
for(let i=0;i<workers.length;i++){const w=workers[i];w.position.set(-40+(i*17)%85+Math.sin(fast*2+i)*3,1,42+(i*11)%29);w.visible=t<38}
const u=t/40;camera.position.set(155+u*25,190+u*50,220+u*32);camera.lookAt(0,37+u*12,0);camera.updateProjectionMatrix();sun.position.set(-110+u*75,200,130-u*30);
post.dof.focus=camera.position.distanceTo(new THREE.Vector3(0,40,0));post.dof.band.y=.49+Math.sin(u*Math.PI)*.04;
post.composer.render();text(t)}
window.render=render;window.seek=render;window.renderFrame=render;window.__ready=true;render(0);
