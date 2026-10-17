#!/usr/bin/env python3
"""EP01 image narrative: original noir specification, cached 068, camera motion and hard captions."""
import argparse, pathlib, subprocess, sys, json, re, hashlib, wave
import numpy as np
from PIL import Image

SCENES=[
("凌晨 3:17","凌晨三點十七分，便利商店來了一位奇怪的客人。",6),
("門鈴響了","自動門開了。她站在門口，沒有腳步聲。",7),
("你看得到我嗎？","她問店員，你看得到我嗎？",9),
("她就在眼前","店員回答，妳不是就在我面前？",9),
("監視器","女子沒有回答，只指向頭頂的監視器。",9),
("空無一人","螢幕裡，櫃台前竟然沒有任何人。",11),
("不要回頭","就在這時，螢幕跳出四個字，不要回頭。",9)]
assert sum(s[2] for s in SCENES)==60


ROOT=pathlib.Path(__file__).resolve().parent/'noir-ep01'
def run(args): subprocess.run([str(x) for x in args],check=True)
def sha(p): return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def probe(p): return json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(p)],text=True))
def cues(p):
 def sec(x):
  h,m,s=x.replace(',','.').split(':');return 3600*int(h)+60*int(m)+float(s)
 return [dict(start=sec(a),end=sec(b),text=t.replace('\n','')) for _,a,b,t in re.findall(r'(\d+)\n(.*?) --> (.*?)\n(.*?)(?=\n\n|$)',p.read_text(),re.S)]
def soundscape(path):
 # Original procedural Foley and minor-key drone, no downloaded music or external generation service.
 sr=48000;n=sr*60;rng=np.random.default_rng(317);t=np.arange(n)/sr
 white=rng.standard_normal(n);rain=(white-np.roll(white,1))*.003
 rain*=.85+.15*np.sin(2*np.pi*.19*t)
 drone=sum(np.sin(2*np.pi*f*t+.2*np.sin(2*np.pi*.13*t)) for f in (55,65.4064,82.4069,110))*.002
 knocks=np.zeros(n)
 for start in (6.1,6.48,6.88,51.1,51.48,51.88):
  q=np.arange(int(sr*.3))/sr;k=(np.sin(2*np.pi*145*q)*.06+rng.standard_normal(len(q))*.018)*np.exp(-q*28)
  begin=round(start*sr);knocks[begin:begin+len(q)]+=k
 fade=np.minimum(t/1.5,1)*np.minimum((60-t)/1.5,1)
 pcm=np.int16(np.clip((rain+drone+knocks)*fade,-1,1)*32767)
 with wave.open(str(path),'wb') as w:w.setparams((1,2,sr,0,'NONE','not compressed'));w.writeframes(pcm.tobytes())
 return dict(provenance='Original deterministic procedural synthesis with numpy, seed 317; no third-party recording',rain='continuous filtered noise',music='A minor drone: A1 C2 E2 A2',knocks_seconds=[6.1,6.48,6.88,51.1,51.48,51.88],auto_ducking='unavailable; low fixed background gain')
def main():
 p=argparse.ArgumentParser();p.add_argument('--output',default='noir-ep01.mp4');p.add_argument('--work',default='noir-work');a=p.parse_args();w=pathlib.Path(a.work);w.mkdir(parents=True,exist_ok=True)
 assets=ROOT/'assets';art=json.loads((ROOT/'design/art-direction.json').read_text());assert art['images'][0]['status']=='pass' and art['images'][0]['sha256']==sha(assets/'sheet.png')
 source=json.loads((assets/'source-verification.json').read_text());assert all(s['voice_id']=='068' for s in source['scenes'])
 font=next((x for x in ['/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc','/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc'] if pathlib.Path(x).exists()),None)
 if not font: raise RuntimeError('fonts-noto-cjk required')
 im=Image.open(assets/'sheet.png');iw,ih=im.size;boxes=[(0,0,iw//2,ih//2),(iw//2,0,iw,ih//2),(0,ih//2,iw//2,ih),(iw//2,ih//2,iw,ih)]
 for i,box in enumerate(boxes): im.crop(box).save(w/f'picture{i}.png')
 # Every frame moves; all figures remain fixed illustrations. Same encounter used for three deliberate reframings.
 pictures=[0,1,1,2,1,3,3];segments=[];offset=0;motion=[]
 for i,(title,spoken,duration) in enumerate(SCENES):
  frames=duration*30
  z=f'1.02+0.10*on/{frames-1}' if i not in (2,4) else '1.13'
  x='iw/2-iw/zoom/2';y='ih/2-ih/zoom/2'
  if i==2:x=f'(iw-iw/zoom)*(0.2+0.8*on/{frames-1})'
  if i==4:y=f'(ih-ih/zoom)*(1-on/{frames-1})'
  titlefile=w/f'title{i}.txt';titlefile.write_text(title)
  vf=f"scale=2160:3840,zoompan=z='{z}':x='{x}':y='{y}':d={frames}:s=1080x1920:fps=30,fade=t=in:st=0:d=0.25,fade=t=out:st={duration-.25}:d=0.25,drawbox=x=0:y=0:w=iw:h=250:color=black@0.4:t=fill,drawtext=fontfile={font}:textfile={titlefile}:fontsize=52:fontcolor=white:x=70:y=130,format=yuv420p"
  if i==0:vf+=f",drawtext=fontfile={font}:text='03\\:17':fontsize=100:fontcolor=white:x=70:y=240"
  if i==6:
   warning=w/'warning.txt';warning.write_text('不要回頭')
   vf+=f",drawtext=fontfile={font}:textfile={warning}:fontsize=100:fontcolor=white:box=1:boxcolor=black@0.88:boxborderw=24:x=(w-tw)/2:y=1000:enable='gte(t,2.5)'"
  out=w/f'scene{i}.mp4';run(['ffmpeg','-y','-loglevel','error','-i',w/f'picture{pictures[i]}.png','-vf',vf,'-frames:v',frames,'-an','-c:v','libx264','-preset','fast','-crf','20','-threads','2',out]);segments.append(out);motion.append(dict(scene=i+1,start=offset,duration=duration,picture=pictures[i],zoom=z,x=x,y=y,transition='0.25s dip to black'));offset+=duration
 concat=w/'concat.txt';concat.write_text(''.join("file '"+str(f.resolve())+"'\n" for f in segments))
 joined=w/'camera.mp4';run(['ffmpeg','-y','-loglevel','error','-f','concat','-safe','0','-i',concat,'-c','copy',joined])
 bg=w/'soundscape.wav';sound=soundscape(bg)
 subtitle=assets/'episode.srt';events=cues(subtitle);assert all(0<=c['start']<c['end']<=60 for c in events);assert all(b['start']>=a['end'] for a,b in zip(events,events[1:]))
 vf=f"subtitles={subtitle}:force_style='FontName=Noto Sans CJK TC,FontSize=8,MarginV=18,Outline=1,Alignment=2'"
 temporary=pathlib.Path(a.output).with_suffix('.tmp.mp4')
 run(['ffmpeg','-y','-loglevel','error','-i',joined,'-i',assets/'narration.m4a','-i',bg,'-filter_complex','[1:a][2:a]amix=inputs=2:normalize=0,alimiter=limit=0.95:level=false[a]','-map','0:v:0','-map','[a]','-vf',vf,'-t','60','-c:v','libx264','-preset','fast','-crf','20','-threads','2','-c:a','aac','-b:a','192k','-ar','48000','-movflags','+faststart',temporary]);temporary.replace(a.output)
 info=probe(a.output);v=next(x for x in info['streams'] if x['codec_type']=='video');au=next(x for x in info['streams'] if x['codec_type']=='audio')
 assert abs(float(info['format']['duration'])-60)<.05 and (v['width'],v['height'],v['avg_frame_rate'])==(1080,1920,'30/1') and int(v['nb_frames'])==1800
 assert v['codec_name']=='h264' and au['codec_name']=='aac' and not any(x['codec_type']=='subtitle' for x in info['streams'])
 run(['ffmpeg','-v','error','-i',a.output,'-f','null','-'])
 # Compare mixed narration with the locked original during real spoken cue windows.
 def pcm(p):return np.frombuffer(subprocess.check_output(['ffmpeg','-v','error','-i',str(p),'-vn','-ac','1','-ar','16000','-f','f32le','-']),dtype=np.float32)
 original=pcm(assets/'narration.m4a');mixed=pcm(a.output);mask=np.zeros(min(len(original),len(mixed)),bool)
 for c in events:mask[int(c['start']*16000):int(c['end']*16000)]=True
 correlation=float(np.corrcoef(original[:len(mask)][mask],mixed[:len(mask)][mask])[0,1]);assert correlation>.97
 report=dict(format=info['format'],video=v,audio=au,full_decode='PASS',visual_type='image_narrative_camera_motion',actor_animation=False,voice_id='068',voice_source_sha256=sha(assets/'narration.m4a'),voice_source_run=39038889615,subtitle_cues=events,subtitle_timing='Unchanged real provider cues aligned to unchanged source audio timeline',narration_correlation=correlation,camera_motion=motion,soundscape=sound,subjective_listening='UNCERTAIN',visual_review='PENDING',sha256=sha(a.output))
 (w/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));(w/'episode.srt').write_text(subtitle.read_text());(w/'narration.txt').write_text(''.join(s[1] for s in SCENES));print('RENDERED',a.output,flush=True)
if __name__=='__main__':main()
