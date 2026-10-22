import hashlib,json,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
voice=Path(sys.argv[1]); silent=Path(sys.argv[2]); out=Path(sys.argv[3]);out.mkdir(parents=True,exist_ok=True)
def run(args):return subprocess.run(args,check=True,capture_output=True,text=True)
meta=json.loads(voice.with_suffix('.json').read_text())
assert meta['status']=='SUCCESS' and meta['voice_id']=='068'
assert meta['preset']['rate']=='+20%' and meta['preset']['pitch']=='+5Hz'
assert meta['duration']<=29.85, f"Natural narration needs shortening: {meta['duration']} seconds; do not truncate."
assert hashlib.sha256(voice.read_bytes()).hexdigest()==meta['sha256']
def sec(s):
 a,b,c=s.replace(',','.').split(':');return int(a)*3600+int(b)*60+float(c)
def ass_time(t):
 n=round(t*100);h,n=divmod(n,360000);m,n=divmod(n,6000);s,n=divmod(n,100);return f'{h}:{m:02}:{s:02}.{n:02}'
rows=[]
for b in re.split(r'\n\s*\n',voice.with_suffix('.srt').read_text(encoding='utf-8-sig').strip()):
 l=b.splitlines()
 if len(l)>=3 and ' --> ' in l[1]:
  a,z=l[1].split(' --> ');text=''.join(l[2:]);wrapped=[]
  while len(text)>17:
   k=17
   while k>1 and text[k] in '，。！？、：；」』）':k-=1
   wrapped.append(text[:k]);text=text[k:]
  wrapped.append(text)
  rows.append((sec(a)+.1,sec(z)+.1,'\\N'.join(wrapped)))
assert rows and rows[-1][1]<=30
ass='''[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2
[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
Style: Default,Noto Sans CJK TC,52,&H00FFFFFF,&H000000FF,&H0015212A,&H8015212A,-1,0,0,0,100,100,1,0,1,3,1,2,70,70,180,1
[Events]
Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
'''
ass+=''.join(f'Dialogue: 0,{ass_time(a)},{ass_time(b)},Default,,0,0,0,,{s}\n' for a,b,s in rows)
(out/'subtitles.ass').write_text(ass,encoding='utf-8')
final=out/'Three_Sovereigns_2B_068_30s.mp4'
# Entire narration is preserved; only silence is added to complete 30 seconds.
run(['ffmpeg','-y','-v','error','-i',str(silent),'-i',str(voice),'-filter_complex',f"[0:v]ass={out.as_posix()}/subtitles.ass,format=yuv420p[v];[1:a]adelay=100:all=1,apad[a]",'-map','[v]','-map','[a]','-t','30','-r','30','-c:v','libx264','-preset','medium','-crf','19','-c:a','aac','-b:a','192k','-movflags','+faststart',str(final)])
run(['ffmpeg','-v','error','-i',str(final),'-f','null','-'])
info=json.loads(run(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(final)]).stdout)
v=next(x for x in info['streams'] if x['codec_type']=='video');a=next(x for x in info['streams'] if x['codec_type']=='audio')
assert (v['width'],v['height'])==(1080,1920) and abs(float(info['format']['duration'])-30)<.08
record={'status':'ENGINEERING_PASS','duration':info['format']['duration'],'video':v,'audio':a,'voice_duration':meta['duration'],'voice_sha256':meta['sha256'],'sha256':hashlib.sha256(final.read_bytes()).hexdigest(),'subtitle_events':len(rows),'full_decode':'PASS','subjective_listening':'UNCERTAIN','visual_review':'PENDING','generation':'Original frame-driven character animation over built-in imagegen backgrounds; Hypit pinned local HTML renderer; no video model API.'}
(out/'verification.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
run(['ffmpeg','-v','error','-i',str(final),'-vf','fps=1/2,scale=270:480,tile=5x3','-frames:v','1',str(out/'review.jpg')])
print(json.dumps({k:record[k] for k in ['status','duration','voice_duration','sha256']}))

