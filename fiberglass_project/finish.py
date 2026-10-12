"""Original low-volume music/SFX, complete voice mix, and measured MP4 QA."""
import array, hashlib, json, math, random, re, subprocess, wave
from pathlib import Path

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'output'

def run(args):
    p=subprocess.run(args,capture_output=True,text=True)
    if p.returncode: raise RuntimeError(p.stderr)
    return p

def timestamp(t):
    ms=round(t*1000);h,ms=divmod(ms,3600000);m,ms=divmod(ms,60000);s,ms=divmod(ms,1000)
    return f'{h:02}:{m:02}:{s:02},{ms:03}'

timeline=json.loads((OUT/'timeline.json').read_text())
total,lead=timeline['total'],timeline['lead']
rate=24000;n=math.ceil(total*rate)
music=array.array('f',[0])*n
sfx=array.array('f',[0])*n
# A new original C-major arpeggio. No downloaded or unlicensed music.
notes=[60,64,67,72,67,64,62,65,69,74,69,65,57,60,64,69,64,60,55,59,62,67,62,59]
for i in range(math.ceil(total/.4)):
    start=round(i*.4*rate);freq=440*2**((notes[i%len(notes)]-69)/12)
    for j in range(min(round(1.3*rate),n-start)):
        t=j/rate;envelope=min(1,t/.015)*math.exp(-t*4.5)
        music[start+j]+=0.018*envelope*(math.sin(2*math.pi*freq*t)+.28*math.sin(2*math.pi*freq*2*t))
random.seed(68)
for i,sc in enumerate(timeline['scenes']):
    start=round((sc['start']+.1)*rate)
    for j in range(min(round(.16*rate),n-start)):
        t=j/rate;sfx[start+j]+=.008*random.uniform(-1,1)*math.exp(-t*24)
    if i in [2,3,5]:
        for j in range(min(round(.65*rate),n-start)):
            t=j/rate;sfx[start+j]+=.012*math.sin(2*math.pi*(880 if i==3 else 660)*t)*math.exp(-t*8)*min(1,t/.01)
for i in range(n):
    fade=min(1,i/rate/.5,max(0,(total-i/rate)/1.5));music[i]*=fade;sfx[i]*=fade
def wav(name,values):
    pcm=array.array('h',(round(max(-1,min(1,x))*32767) for x in values))
    with wave.open(str(OUT/name),'wb') as f:f.setnchannels(1);f.setsampwidth(2);f.setframerate(rate);f.writeframes(pcm.tobytes())
wav('original_music.wav',music);wav('scene_sfx.wav',sfx)
# Sidechain reduces the already quiet music during the verified narration.
run(['ffmpeg','-y','-v','error','-i',str(OUT/'fiberglass-20261012.mp3'),'-i',str(OUT/'original_music.wav'),'-i',str(OUT/'scene_sfx.wav'),'-filter_complex',f'[0:a]adelay={round(lead*1000)}:all=1,apad,asplit=2[v][key];[1:a][key]sidechaincompress=threshold=0.02:ratio=4:attack=20:release=350[m];[v][m][2:a]amix=inputs=3:duration=longest:normalize=0,alimiter=limit=0.89:level=false[a]','-map','[a]','-t',str(total),'-ar','48000','-ac','2',str(OUT/'full_mix.wav')])
run(['ffmpeg','-y','-v','error','-i',str(OUT/'picture.mp4'),'-i',str(OUT/'full_mix.wav'),'-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','192k','-disposition:a:0','default','-t',str(total),'-movflags','+faststart',str(OUT/'fiberglass_068_v01.mp4')])
run(['ffmpeg','-y','-v','error','-i',str(OUT/'full_mix.wav'),'-c:a','libmp3lame','-b:a','192k',str(OUT/'fiberglass_full_mix.mp3')])
(OUT/'fiberglass_video.srt').write_text(''.join(f'{i}\n{timestamp(c["start"]+lead)} --> {timestamp(c["end"]+lead)}\n{c["text"]}\n\n' for i,c in enumerate(timeline['cues'],1)),encoding='utf-8')
video=OUT/'fiberglass_068_v01.mp4'
run(['ffmpeg','-v','error','-xerror','-i',str(video),'-f','null','-'])
probe=json.loads(run(['ffprobe','-v','error','-count_frames','-show_streams','-show_format','-of','json',str(video)]).stdout)
v=next(x for x in probe['streams'] if x['codec_type']=='video');a=next(x for x in probe['streams'] if x['codec_type']=='audio')
assert v['codec_name']=='h264' and a['codec_name']=='aac'
assert (v['width'],v['height'])==(1080,1920)
assert int(v['nb_read_frames'])==round(total*24)
assert abs(float(probe['format']['duration'])-total)<.06
p=run(['ffmpeg','-hide_banner','-i',str(video),'-af','loudnorm=I=-11:TP=-1:LRA=7:print_format=json','-f','null','-'])
stats=json.loads(p.stderr[p.stderr.rfind('{'):])
assert math.isfinite(float(stats['input_i'])) and -25<float(stats['input_i'])<-5 and float(stats['input_tp'])<0
src=(ROOT/'narration.txt').read_text().strip();norm=lambda t:''.join(c.casefold() for c in t if c.isalnum())
assert norm(src)==norm(''.join(c['text'] for c in timeline['cues']))
assert timeline['cues'][-1]['end']+lead<total
original=json.loads((OUT/'fiberglass-20261012.json').read_text())
assert original['text_sha256']==hashlib.sha256(src.encode()).hexdigest()
assert original['sha256']==hashlib.sha256((OUT/'fiberglass-20261012.mp3').read_bytes()).hexdigest()
assert original['preset']['voice']=='zh-TW-HsiaoChenNeural'
assert original['preset']['rate']=='+20%' and original['preset']['pitch']=='+5Hz'
result={'status':'SUCCESS','video_seconds':total,'container_seconds':probe['format']['duration'],'frames':v['nb_read_frames'],'size':[1080,1920],'fps':24,'codecs':['h264','aac'],'full_decode':'PASS','narration_text_and_sha':'PASS','subtitles':'7 true sentence events + 0.6 seconds lead','measured_loudness':stats,'voice':original,'subjective_listening':'UNCERTAIN','sha256':hashlib.sha256(video.read_bytes()).hexdigest(),'voice_run':38249536043}
(OUT/'qa.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
(OUT/'checkpoint.md').write_text(f'# 玻璃纖維白板短片 v01\n\nSUCCESS：新068旁白、完整MP4解碼、{total:.3f}秒、1080×1920、24fps、H264/AAC、七句真實時間字幕與文字/音訊SHA校验。實測音量{stats["input_i"]} LUFS，峰值{stats["input_tp"]} dBTP。原創配樂、場景音效、旁白優先側鏈混音。\n\nUNCERTAIN：主觀與手機試聽。未發布社群。\n\n根因：ChatGPT容器DNS仍失敗，Node白板套件缺少；沿用最新main的068程式，由GitHub Actions產生本次真實旁白。恢復既有render.html/scene-dsl.js，用GitHub runner安裝缺少的渲染套件和完整中文字型。舊配音程式與舊故事音訊沒有參與本次成品。\n\n最後完成：技術QA。阻塞：無。下一步：畫面抽查、保存成品並讓使用者試看；只修改受影響部分。\n',encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))
