"""Inspect the actual encoded MP4: decode, probe, loudness, black frames, contact sheet."""
from pathlib import Path
import json,subprocess,hashlib
from PIL import Image, ImageDraw
p=Path(__file__).resolve().parent;f=p/'008-rain-v1.mp4'
def run(a):return subprocess.run(a,capture_output=True,text=True,check=True)
probe=json.loads(run(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(f)]).stdout)
v=next(x for x in probe['streams'] if x['codec_type']=='video');a=next(x for x in probe['streams'] if x['codec_type']=='audio')
assert (v['width'],v['height'],v['r_frame_rate'])==(1080,1920,'30/1')
assert abs(float(probe['format']['duration'])-30)<.05
run(['ffmpeg','-v','error','-i',str(f),'-f','null','-'])
r=run(['ffmpeg','-hide_banner','-i',str(f),'-af','loudnorm=I=-14:TP=-1:LRA=7:print_format=json','-f','null','-']);vol=json.loads(r.stderr[r.stderr.rfind('{'):])
r=run(['ffmpeg','-hide_banner','-i',str(f),'-vf','blackdetect=d=0.15:pix_th=0.10:pic_th=0.98','-an','-f','null','-']);black=[l for l in r.stderr.splitlines() if 'black_start:' in l]
canvas=Image.new('RGB',(1890,520),'#151822');draw=ImageDraw.Draw(canvas)
for i,t in enumerate([1.5,6,11,16,19.5,23,28]):
 out=p/f'encoded-{t}.png';run(['ffmpeg','-v','error','-y','-ss',str(t),'-i',str(f),'-frames:v','1',str(out)])
 im=Image.open(out).convert('RGB').resize((270,480));canvas.paste(im,(270*i,30));draw.text((270*i+10,8),f'{t}s',fill='white')
canvas.save(p/'encoded-contact-sheet.png')
summary={'technical':'PASS','full_decode':'PASS','width':v['width'],'height':v['height'],'fps':v['r_frame_rate'],'duration':probe['format']['duration'],'audio_codec':a['codec_name'],'audio_duration':a.get('duration'),'loudness':vol,'black_segments':black,'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'subjective_listening':'UNCERTAIN: not listened','full_speed_viewing':'UNCERTAIN: not watched','user_acceptance':'PENDING'}
(p/'final-qa.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2));print(json.dumps(summary,ensure_ascii=False))
