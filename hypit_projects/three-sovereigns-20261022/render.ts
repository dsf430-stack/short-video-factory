import { sealVisualTrack } from "@hypit/composition";
import { htmlVisual } from "@hypit/html-program";
import type { FontStackRef } from "@hypit/media";
import type { Timeline } from "@hypit/timeline";
import type { SpatialFrame } from "@hypit/spatial";
import type { TemporalInstant, TemporalWindow } from "@hypit/temporal";
import { readFileSync } from "node:fs";
export type Message = { id:string; sender:string; text:string; side:"left"|"right"; at:TemporalInstant };
export type ChatOptions = { id:string; title:string; entranceFrames:number };
export function renderChat(timeline:Timeline,within:SpatialFrame,window:TemporalWindow,font:FontStackRef,messages:readonly Message[],options:ChatOptions){
 const scene=JSON.parse(readFileSync(new URL('../scene.json',import.meta.url),'utf8'));
 const program=htmlVisual({html:scene.html,css:scene.css,data:scene.data,setup:scene.setup});
 return sealVisualTrack({id:options.id,timelineId:timeline.id,visualIr:'hypit.visual-ir@1',presents:[{id:options.id,order:0,z:0,span:window.span,elements:[{id:'three-sovereigns',kind:'program',order:0,program,style:[{name:'position',value:'absolute'},{name:'left',value:`${within.xPx}px`},{name:'top',value:`${within.yPx}px`},{name:'width',value:`${within.widthPx}px`},{name:'height',value:`${within.heightPx}px`}]}]}]});
}

