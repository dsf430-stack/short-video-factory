"""Render assistant-prepared, reviewed jobs using official Sweety + existing 068.
No model API or model API key is used by this entry point.
"""
import argparse, hashlib, json, re, shutil, subprocess, sys
from pathlib import Path
REPO=Path(__file__).resolve().parents[1]
PIN='5206ec0d17f9b353e400b64b9c51ad69e721e02a'
def digest(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,v):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def run(*a): subprocess.run([str(x) for x in a],check=True)
def normalize(t): return ''.join(c for c in t if c.isalnum())
def parse_srt(path):
    def seconds(value):
        hours, minutes, tail = value.replace(',', '.').split(':')
        return int(hours) * 3600 + int(minutes) * 60 + float(tail)
    result = []
    for block in re.split(r'\n\s*\n', Path(path).read_text().strip()):
        lines = block.splitlines()
        left, right = lines[1].split(' --> ')
        result.append({'start': seconds(left), 'end': seconds(right), 'text': ''.join(lines[2:])})
    return result


def align_scenes(scenes, events):
    """Map real Edge sentence boundaries; never interpolate character timing."""
    result, offset = [], 0
    for index, scene in enumerate(scenes):
        selected, found = [], ''
        expected = normalize(scene['text'])
        while offset < len(events) and len(found) < len(expected):
            event = events[offset]
            selected.append(event)
            found += normalize(event['text'])
            offset += 1
        if found != expected or not selected:
            raise ValueError('Edge sentence boundaries do not match storyboard scene ' + str(index))
        start = selected[0]['start']
        if result and start < result[-1]['end']:
            if result[-1]['end'] - start > .02:
                raise ValueError('Measured sentence boundaries overlap')
            start = result[-1]['end']
        end = selected[-1]['end']
        cues = [{'text': event['text'], 'start': max(0, event['start'] - start),
                 'end': event['end'] - start} for event in selected]
        spoken = ''.join(cue['text'] for cue in cues)
        if scene['text'].startswith(spoken) and not scene['text'][len(spoken):].strip():
            cues[-1]['text'] += scene['text'][len(spoken):]
        elif spoken != scene['text']:
            # Provider may trim/insert whitespace around separately spoken English.
            # Alphanumeric content was already matched exactly above. Preserve
            # script typography without changing any measured event boundaries.
            cursor = 0
            for cue in cues:
                count = len(normalize(cue['text']))
                begin = cursor
                while count:
                    if scene['text'][cursor].isalnum(): count -= 1
                    cursor += 1
                while cursor < len(scene['text']) and not scene['text'][cursor].isalnum(): cursor += 1
                cue['text'] = scene['text'][begin:cursor]
            if cursor != len(scene['text']): raise ValueError('Subtitle typography mapping incomplete')
        result.append({'id': f's{index}', 'text': scene['text'], 'start': start, 'end': end,
                       'caption_cues': cues})
    if offset != len(events):
        raise ValueError('Unmapped Edge sentence events')
    return result



def main(args):
 from PIL import Image
 from preparation import resolve_bundle, choose_candidate
 bundle=resolve_bundle(REPO/'handdraw/prepared',args.topic,args.seconds)
 root=Path(args.output).resolve();root.mkdir(parents=True,exist_ok=True)
 skill=Path(args.official).resolve()/'skills/sweety-handdraw-video'
 actual=subprocess.check_output(['git','-C',str(skill),'rev-parse','HEAD'],text=True).strip()
 if actual!=PIN: raise ValueError('Official source pin changed')
 sys.path.insert(0,str(skill/'scripts'))
 from clean_image import clean_image
 from video_verifier import build_fingerprint, file_hash
 command=skill/'scripts/handdraw_video.py'
 fingerprint=hashlib.sha256((str(args.seconds)+digest(Path(__file__))+digest(REPO/'handdraw/preparation.py')+json.dumps(json.loads((REPO/'smart_voice/voices.json').read_text())['voices']['068'],sort_keys=True) + ''.join(str(p.relative_to(bundle))+digest(p) for p in sorted(bundle.rglob('*')) if p.is_file())).encode()).hexdigest()
 receipt=root/'prepared-receipt.json'
 film=root/'outputs/film.mp4'
 cached=False
 if receipt.exists() and film.exists() and json.loads(receipt.read_text()).get('bundle_sha256')==fingerprint:
  try:
   record=json.loads((root/'work/render-record.json').read_text())
   cached=record['video_sha256']==file_hash(film) and record['build_fingerprint']==build_fingerprint(root)
  except (ValueError,FileNotFoundError,KeyError): pass
 if not cached:
  for directory in ['style','design','inputs']:
   shutil.copytree(bundle/directory,root/directory,dirs_exist_ok=True)
  shutil.copyfile(bundle/'design.json',root/'design.json')
  story=json.loads((bundle/'story.json').read_text()); scenes=story['scenes']
  candidates=story.get('script_candidates',[[s['text'] for s in scenes]])
  measured={}; attempts=[]; selected=None
  for _ in range(min(12,len(candidates))):
   candidate=choose_candidate(candidates,measured,args.seconds-1-.5)
   if candidate is None: break
   if len(candidates[candidate])!=len(scenes):raise ValueError('Script candidate scene count mismatch')
   text=''.join(candidates[candidate]);text_hash=hashlib.sha256(text.encode()).hexdigest()
   narration=root/f'inputs/voice-{text_hash[:16]}.txt';narration.write_text(text)
   mp3=narration.with_suffix('.mp3')
   if not mp3.exists():run(sys.executable,REPO/'smart_voice/generate_voice.py','--voice-id','068','--text-file',narration,'--output',mp3)
   meta=json.loads(mp3.with_suffix('.json').read_text())
   expected=json.loads((REPO/'smart_voice/voices.json').read_text())['voices']['068']
   if meta['text_sha256']!=text_hash or meta['voice_id']!='068' or meta['sha256']!=digest(mp3) or any(meta['preset'][k]!=expected[k] for k in ('voice','rate','pitch','volume')):raise ValueError('Voice cache mismatch')
   master=root/'inputs/master.wav';run('ffmpeg','-y','-v','error','-i',mp3,'-ar',48000,'-ac',1,'-c:a','pcm_s16le',master)
   import wave
   with wave.open(str(master)) as wav: duration=wav.getnframes()/wav.getframerate()
   hold=args.seconds-1-duration;measured[candidate]=duration
   attempts.append({'candidate':candidate,'seconds':duration,'hold':hold,'text':text})
   save(root/'voice-measurement.json',{'attempts':attempts,'target_film_seconds':args.seconds,'voice':meta['preset']})
   print('MEASURED_NARRATION_SECONDS',duration,'REQUIRED_END_HOLD',hold,flush=True)
   if .2<=hold<=.8:
    selected=candidate;break
  if selected is None:raise ValueError('SCRIPT_FIT_REQUIRED: measured editorial candidates exhausted; see voice-measurement.json. Voice was not stretched or truncated.')
  for scene,spoken in zip(scenes,candidates[selected]):scene['text']=spoken
  # Requirements cite stable core facts present in every editorial candidate.
  beats=align_scenes(scenes,parse_srt(mp3.with_suffix('.srt')))
  save(root/'inputs/alignment.json',{'version':1,'source_sha256':digest(master),'script_sha256':text_hash,'beats':beats})
  if args.voice_only:
   print('VOICE_FIT_READY',json.dumps({'seconds':duration,'hold':hold,'candidate':selected}),flush=True)
   return
  art=json.loads((root/'design/art-direction.json').read_text());drawing=json.loads((root/'design/drawing-review.json').read_text())
  for entry in art['images']:
   image=(root/'design'/entry['source']).resolve()
   pixels=lambda:hashlib.sha256(Image.open(image).convert('RGBA').tobytes()).hexdigest()
   if entry['sha256']!=digest(image) or entry['pixel_sha256']!=pixels():raise ValueError('Reviewed source image changed')
   clean_image(image,root/'privacy'/f'{image.stem}.json')
   if pixels()!=entry['pixel_sha256']:raise ValueError('Privacy cleanup altered reviewed pixels')
   original_sha=entry['sha256']
   entry['sha256']=digest(image)
   for review in drawing['illustrations']:
    if review['source_sha256']==original_sha or review['plan_id']==image.stem:review['source_sha256']=digest(image)
  save(root/'design/art-direction.json',art);save(root/'design/drawing-review.json',drawing)
  font='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
  pages=[]
  for s in scenes:
   pages.append({'beats':[{'id':s['id'],'text':s['text'],'actions':[
    {'type':'text','text':s['label'],'x':s.get('label_x',120),'y':s.get('label_y',250),'size':s.get('label_size',90),'weight':1,'z':40},
    {'type':'illustration','drawing_plan_id':s['id'],'source':s.get('source','inputs/'+s['id']+'.png'),**({'crop':s['crop']} if s.get('crop') else {}),'x':s.get('image_x',120),'y':s.get('image_y',480),'width':s.get('image_width',840),'height':s.get('image_height',840),'weight':5,'parts':s['parts'],**({'outline_mask':s['outline_mask']} if s.get('outline_mask') else {})}]}]})
  for page, scene in zip(pages,scenes):
   page['beats'][0]['actions'].extend({'type':'text','weight':.3,'z':50,**item} for item in scene.get('annotations',[]))
  manifest={'version':1,'title':story['title'],'design_file':'design.json','canvas':{'width':1080,'height':1920,'fps':30},'paper':story.get('paper','#FFFFFF'),'font':{'path':font,'index':3},'cover':{'source':'inputs/cover.png','seconds':1},'hand':{'preset':'pen-only','scale':.25,'pen_text':''},'narration':{'source':'inputs/master.wav','alignment':'inputs/alignment.json'},'audio':{'end_hold_seconds':hold},'ending':{'caption_hold_seconds':min(.2,hold)},'captions':{'font':{'path':font,'index':3},'font_size':46,'bottom_margin':210,'max_width_ratio':.9,'max_lines':2,'color':'#FFFFFF','stroke_color':'#151515','stroke_width':3,'background':None},'art_direction':{'record':'design/art-direction.json'},'drawing_plan':'design/drawing-plan.json','drawing_review':'design/drawing-review.json','pages':pages}
  save(root/'job.json',manifest);(root/'script.txt').write_text(text)
  if story.get('caption_font_size'):
   manifest['captions']['font_size']=story['caption_font_size']
   manifest['captions']['stroke_width']=2
   save(root/'job.json',manifest)
  for stage in ['doctor','build']:run(sys.executable,command,stage,root)
  run(sys.executable,command,'verify',root,'--assets-only')
  run(sys.executable,command,'render',root,'--preview','--start',1,'--duration',story.get('preview_seconds',7))
  if args.preview_only:
   print('PREVIEW_READY',root/'work/review/preview.mp4',flush=True)
   return
  run(sys.executable,command,'render',root)
  save(receipt,{'bundle_sha256':fingerprint,'official_commit':PIN})
 run(sys.executable,command,'verify',root)
 if json.loads((bundle/'story.json').read_text()).get('natural_duration'):
  args.seconds=json.loads((root/'work/timeline.json').read_text())['duration']
 probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(film)]))
 v=next(s for s in probe['streams'] if s['codec_type']=='video')
 if (v['width'],v['height'],v['avg_frame_rate'])!=(1080,1920,'30/1') or abs(float(v['duration'])-args.seconds)>.05:raise ValueError('Requested format or duration failed')
 report={'status':'ENGINEERING_PASS','topic':args.topic,'seconds':float(v['duration']),'official_commit':PIN,'voice':'068','sha256':digest(film),'human_listening':'UNCERTAIN','model_api_required':False}
 review_path=REPO/'handdraw/final-reviews'/f"{digest(film)}.json"
 if review_path.exists():
  shutil.copyfile(review_path,root/'review.json');run(sys.executable,command,'finalize',root);report['status']='SUCCESS'
 save(root/'acceptance.json',report)
 print('VERIFIED_FILM',str(film),json.dumps(report),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--topic',required=True);p.add_argument('--seconds',type=int,default=30);p.add_argument('--official',required=True);p.add_argument('--output',required=True);p.add_argument('--preview-only',action='store_true');p.add_argument('--voice-only',action='store_true');main(p.parse_args())
