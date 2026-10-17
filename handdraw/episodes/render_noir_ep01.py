#!/usr/bin/env python3
"""EP01 continuity re-edit: continuous measured 068 master, causal cuts, original noir pictures."""
import argparse, pathlib, subprocess, json, re, hashlib, wave
import numpy as np
from PIL import Image
ROOT=pathlib.Path(__file__).resolve().parent/'noir-ep01'
REV=ROOT/'reedit-v2'
OFFSET=.45
FPS=30

def run(args): subprocess.run([str(x) for x in args],check=True)
def sha(p): return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def probe(p): return json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(p)],text=True))
def cues(p):
 def sec(x):
  h,m,s=x.replace(',','.').split(':');return 3600*int(h)+60*int(m)+float(s)
 return [dict(start=sec(a),end=sec(b),text=t.replace('\n','')) for _,a,b,t in re.findall(r'(\d+)\n(.*?) --> (.*?)\n(.*?)(?=\n\n|$)',p.read_text(),re.S)]
def stamp(t):
 cs=round(t*100);h,cs=divmod(cs,360000);m,cs=divmod(cs,6000);s,cs=divmod(cs,100);return f'{h}:{m:02}:{s:02}.{cs:02}'
def wrap(text):
 # Keep real sentence times; only arrange glyphs, never interpolate cue times.
 pieces=[]
 while len(text)>17:
  cut=17
  while cut>1 and text[cut] in '，。！？、：；？」』':cut-=1
  pieces.append(text[:cut]);text=text[cut:]
 pieces.append(text)
 if len(pieces)>1 and len(pieces[-1])<4:
  n=4-len(pieces[-1]);pieces[-1]=pieces[-2][-n:]+pieces[-1];pieces[-2]=pieces[-2][:-n]
 return r'\N'.join(pieces)
def captions(path,events):
 header='''[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2
ScaledBorderAndShadow: yes
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Noto Sans CJK TC,52,&H00FFFFFF,&H00FFFFFF,&H00101010,&H80000000,0,0,0,0,100,100,0,0,1,3,1,2,72,72,145,1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
'''
 path.write_text(header+''.join(f"Dialogue: 0,{stamp(c['start'])},{stamp(c['end'])},Default,,0,0,0,,{wrap(c['text'])}\n" for c in events))
def soundscape(path,knock_start,breath_start):
 sr=48000;n=sr*60;rng=np.random.default_rng(317);t=np.arange(n)/sr
 white=rng.standard_normal(n);rain=(white-np.roll(white,1))*.003
 rain*=.85+.15*np.sin(2*np.pi*.19*t)
 drone=sum(np.sin(2*np.pi*f*t+.2*np.sin(2*np.pi*.13*t)) for f in (55,65.4064,82.4069,110))*.002
 knocks=np.zeros(n);knock_times=[knock_start+j*.28 for j in range(3)]
 for start in knock_times:
  q=np.arange(round(sr*.3))/sr;k=(np.sin(2*np.pi*145*q)*.06+rng.standard_normal(len(q))*.018)*np.exp(-q*28)
  begin=round(start*sr);knocks[begin:begin+len(q)]+=k
 # Short original noise envelope is Foley, not a replaced voice or downloaded recording.
 q=np.arange(round(sr*.75))/sr;breath=rng.standard_normal(len(q));breath=np.convolve(breath,np.ones(20)/20,mode='same')*.10*np.sin(np.pi*q/.75)**2
 begin=round(breath_start*sr);knocks[begin:begin+len(q)]+=breath
 fade=np.minimum(t/1.2,1)*np.minimum((60-t)/.6,1);bed=(rain+drone+knocks)*fade
 with wave.open(str(path),'wb') as w:w.setparams((1,2,sr,0,'NONE','not compressed'));w.writeframes(np.int16(np.clip(bed,-1,1)*32767).tobytes())
 return dict(provenance='Original procedural rain, three knocks, A-minor drone and breath Foley, seed 317; no external generation service',knocks_seconds=knock_times,breath_seconds=breath_start,auto_ducking='unavailable; fixed low bed',rms_dbfs=float(20*np.log10(np.sqrt(np.mean(bed**2)))))
def main():
 p=argparse.ArgumentParser();p.add_argument('--output',default='noir-ep01.mp4');p.add_argument('--work',default='noir-work');p.add_argument('--preview',action='store_true');a=p.parse_args();w=pathlib.Path(a.work);w.mkdir(parents=True,exist_ok=True)
 W,H=(270,480) if a.preview else (1080,1920);assets=REV/'assets'
 for image,record in [(ROOT/'assets/sheet.png',ROOT/'design/art-direction.json'),(assets/'continuity.png',REV/'design/art-direction.json')]:
  art=json.loads(record.read_text())['images'][0];assert art['status']=='pass' and art['sha256']==sha(image),'Unreviewed or changed image'
 meta=json.loads((assets/'narration.json').read_text());script=(REV/'narration.txt').read_text().strip();assert meta['voice_id']=='068' and meta['sha256']==sha(assets/'narration.mp3') and meta['text_sha256']==hashlib.sha256(script.encode()).hexdigest()
 assert meta['preset']==json.loads((ROOT.parents[2]/'smart_voice/voices.json').read_text())['voices']['068']
 assert 55<=meta['duration']<=58
 events=cues(assets/'narration.srt');normalize=lambda s:''.join(c for c in s if c.isalnum());assert normalize(''.join(c['text'] for c in events))==normalize(script)
 for c in events:c['start']+=OFFSET;c['end']+=OFFSET
 assert all(b['start']>=a0['end'] and b['start']-a0['end']<.5 for a0,b in zip(events,events[1:]));assert events[-1]['end']<58
 cuts=lambda i:round(events[i-1]['start']*FPS)
 # The gesture and discovery may not appear before their corresponding spoken sentence.
 # source sheet, quadrant, cue start, editorial purpose, pan target x/y (0..1)
 specs=[('old',0,0,'Rainy exterior establishes time and place',.5,.45),
 ('old',2,cuts(2),'Clerk alone at work',.5,.5),
 ('new',0,cuts(3),'Knuckles at glass when knocks are narrated',.65,.4),
 ('new',0,cuts(4),'Dry-haired woman outside in rain',.85,.35),
 ('new',1,cuts(7),'Woman now inside, arms down',.5,.5),
 ('new',1,cuts(8),'Clerk waits, neutral two-shot',.5,.5),
 ('new',2,cuts(9),'Woman asks; no raised arm',.5,.40),
 ('old',2,cuts(10),'Clerk replies, puzzled',.5,.4),
 ('new',2,cuts(11),'Woman does not smile',.5,.4),
 ('old',1,cuts(12),'Only now show pointing at CCTV',.55,.32),
 ('old',1,cuts(13),'Follow indicated direction toward camera',.15,.05),
 ('old',3,cuts(14),'First reveal empty CCTV customer area',.5,.45),
 ('new',1,cuts(15),'Return to woman still in place, arms down',.7,.4),
 ('new',3,cuts(16),'Gaze shifts past clerk shoulder',.6,.35),
 ('old',3,cuts(17),'CCTV warning appears during warning sentence',.5,.45),
 ('old',2,cuts(18),'Clerk freezes; breath behind him',.5,.35)]
 assert [s[2] for s in specs]==sorted(set(s[2] for s in specs));assert next(s[2] for s in specs if s[3].startswith('Only now'))==cuts(12)
 shots=[];parts=[]
 for label,sheet in [('old',ROOT/'assets/sheet.png'),('new',assets/'continuity.png')]:
  im=Image.open(sheet);iw,ih=im.size;boxes=[(0,0,iw//2,ih//2),(iw//2,0,iw,ih//2),(0,ih//2,iw//2,ih),(iw//2,ih//2,iw,ih)]
  for i,box in enumerate(boxes):im.crop(box).save(w/f'{label}{i}.png')
 for i,(label,quad,start,purpose,px,py) in enumerate(specs):
  end=specs[i+1][2] if i+1<len(specs) else 1800;frames=end-start
  # Repeated neutral insert keeps the same zoom trajectory across its cue boundary.
  continuing=i==5;z0=1.035+(specs[5][2]-specs[4][2])*.00007 if continuing else 1.035
  z=f'{z0}+on*0.00007';x=f'(iw-iw/zoom)*{px}';y=f'(ih-ih/zoom)*{py}'
  vf=f"scale={W*2}:{H*2},zoompan=z='{z}':x='{x}':y='{y}':d={frames}:s={W}x{H}:fps=30,setsar=1,format=yuv420p"
  if i==0:vf+=',fade=t=in:st=0:d=0.18'
  out=w/f'scene{i:02}.mp4';run(['ffmpeg','-y','-v','error','-i',w/f'{label}{quad}.png','-vf',vf,'-frames:v',frames,'-an','-c:v','libx264','-preset','fast','-crf','20','-threads','2',out]);parts.append(out)
  shots.append(dict(index=i,start_frame=start,end_frame=end,start=start/30,end=end/30,source=label,quadrant=quad,purpose=purpose,transition='direct causal cut; continuous narration, rain and drone',zoom=z,pan=[px,py]));print('SHOT',i,purpose,flush=True)
 concat=w/'concat.txt';concat.write_text(''.join("file '"+str(f.resolve())+"'\n" for f in parts));joined=w/'camera.mp4';run(['ffmpeg','-y','-v','error','-f','concat','-safe','0','-i',concat,'-c','copy',joined])
 font='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc';assert pathlib.Path(font).exists()
 ass=w/'captions.ass';captions(ass,events)
 sound=soundscape(w/'soundscape.wav',events[2]['end']-1.0,events[-1]['end']+.20)
 title=w/'title.txt';title.write_text('凌晨 3:17');warning=w/'warning.txt';warning.write_text('不要回頭');ending=w/'ending.txt';ending.write_text('第一集｜不存在的客人\n待續')
 # Narrative screen warning is separate from the one subtitle layer; no chapter titles spoil later beats.
 ratio=W/1080;warning_on=events[16]['end']-1.25;warning_off=specs[-1][2]/30
 vf=f"subtitles={ass},drawtext=fontfile={font}:textfile={title}:fontsize={round(72*ratio)}:fontcolor=white:shadowcolor=black:shadowx=2:shadowy=2:x={round(65*ratio)}:y={round(110*ratio)}:enable='lt(t,2.8)',drawtext=fontfile={font}:textfile={warning}:fontsize={round(94*ratio)}:fontcolor=white:box=1:boxcolor=black@0.88:boxborderw={round(20*ratio)}:x=(w-tw)/2:y={round(1000*ratio)}:enable='between(t,{warning_on},{warning_off-.001})',drawtext=fontfile={font}:textfile={ending}:fontsize={round(52*ratio)}:fontcolor=white:shadowcolor=black:shadowx=2:shadowy=2:x=(w-tw)/2:y={round(1470*ratio)}:enable='gte(t,58.3)',fade=t=out:st=59.75:d=0.25"
 temp=pathlib.Path(a.output).with_suffix('.tmp.mp4')
 run(['ffmpeg','-y','-v','error','-i',joined,'-i',assets/'narration.mp3','-i',w/'soundscape.wav','-filter_complex',f'[1:a]adelay={round(OFFSET*1000)}:all=1,apad[n];[n][2:a]amix=inputs=2:normalize=0,alimiter=limit=0.95:level=false:latency=true[a]','-map','0:v:0','-map','[a]','-vf',vf,'-t','60','-c:v','libx264','-preset','fast','-crf','20','-threads','2','-c:a','aac','-b:a','192k','-ar','48000','-movflags','+faststart',temp]);temp.replace(a.output)
 info=probe(a.output);v=next(x for x in info['streams'] if x['codec_type']=='video');au=next(x for x in info['streams'] if x['codec_type']=='audio');assert (v['width'],v['height'],v['avg_frame_rate'],int(v['nb_frames']))==(W,H,'30/1',1800);assert abs(float(info['format']['duration'])-60)<.05 and v['codec_name']=='h264' and au['codec_name']=='aac';assert not any(s['codec_type']=='subtitle' for s in info['streams']);run(['ffmpeg','-v','error','-i',a.output,'-f','null','-'])
 def pcm(p):return np.frombuffer(subprocess.check_output(['ffmpeg','-v','error','-i',str(p),'-vn','-ac','1','-ar','16000','-f','f32le','-']),np.float32)
 original=np.pad(pcm(assets/'narration.mp3'),(round(OFFSET*16000),0));mixed=pcm(a.output);n=min(len(original),len(mixed));mask=np.zeros(n,bool)
 for c in events:mask[round(c['start']*16000):round(c['end']*16000)]=True
 correlation=float(np.corrcoef(original[:n][mask],mixed[:n][mask])[0,1]);assert correlation>.97
 report=dict(revision='continuity-v2',format=info['format'],video=v,audio=au,full_decode='PASS',voice_id='068',voice_duration=meta['duration'],voice_offset=OFFSET,voice_sha256=meta['sha256'],voice_preset=meta['preset'],subtitle_cues=events,subtitle_timing='One complete measured master with unchanged provider sentence times plus 450ms offset',narration_correlation=correlation,camera_motion=shots,soundscape=sound,warning_on=warning_on,main_narration_max_gap=max(b['start']-c['end'] for c,b in zip(events,events[1:])),actor_animation=False,subjective_listening='UNCERTAIN',visual_review='PENDING',sha256=sha(a.output))
 (w/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));(w/'narration.txt').write_text(script);(w/'episode.srt').write_text((assets/'narration.srt').read_text());print('RENDERED',a.output,'CORRELATION',correlation,flush=True)
if __name__=='__main__':main()
