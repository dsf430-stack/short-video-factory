#!/usr/bin/env python3
"""Real-photo case adapter for existing 068/storybook media helpers. Run on Actions."""
import sys, json, math, hashlib, shutil, subprocess, urllib.request, time, re
from pathlib import Path
import numpy as np
from PIL import Image, ImageOps, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]
sys.path.insert(0, str(REPO / 'smart_voice/storybook'))
from book_media import run, duration
from render_cached_book import captions, seconds, measure, write_wav, add
FPS, W, H, SR = 25, 1920, 1080, 44100

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def download(url, dest):
    if dest.exists(): return
    for attempt in range(3):
        try:
            request=urllib.request.Request(url, headers={'User-Agent':'AfuEducationalVideo/1.0 (licensed Wikimedia photos)'})
            with urllib.request.urlopen(request, timeout=90) as response:
                data=response.read()
            if len(data)<1000: raise RuntimeError('Incomplete asset')
            temp=dest.with_suffix('.tmp'); temp.write_bytes(data); temp.replace(dest)
            return
        except Exception:
            if attempt==2: raise
            time.sleep(2**attempt)

def font(size): return ImageFont.truetype(str(ROOT/'fonts/NotoSansCJKtc-Regular.otf'),size)

def fit_photo(path, size):
    image=Image.open(path).convert('RGB')
    return ImageOps.fit(image,size,method=Image.Resampling.LANCZOS,centering=(.5,.5))

def plate(scene, index, assets, dest):
    im=Image.new('RGB',(W,H),(8,24,35))
    # Confine animals to a photo window; keep labels and subtitles on their own bands.
    image=Image.open(ROOT/'photos'/assets[scene['photo']]['file']).convert('RGB')
    photo=ImageOps.contain(image,(1180,790),method=Image.Resampling.LANCZOS)
    im.paste(photo,(40+(1180-photo.width)//2,145+(790-photo.height)//2))
    d=ImageDraw.Draw(im)
    d.text((48,35),'阿福的冷知識  /  ANTARCTIC KRILL',font=font(24),fill=(101,216,216))
    d.rounded_rectangle((1260,153,1870,855),radius=24,fill=(14,42,57))
    d.text((1300,192),f'{index+1:02}  /  {scene["title"]}',font=font(28),fill=(112,221,222))
    y=294
    for line in scene['lines']:
        for part in [line[j:j+11] for j in range(0,len(line),11)]:
            d.text((1300,y),part,font=font(46),fill=(247,245,231)); y+=74
        y+=18
    d.line((1300,690,1815,690),fill=(78,123,139),width=2)
    label=scene['label']
    for j,part in enumerate([label[k:k+20] for k in range(0,len(label),20)]):
        d.text((1300,723+j*31),part,font=font(20),fill=(178,206,212))
    credit=assets[scene['photo']]['credit']
    d.text((48,907),credit,font=font(18),fill=(169,195,204))
    d.rectangle((0,949,W,H),fill=(5,15,23))
    im.save(dest)

def music(path,total):
    # New neutral documentary arrangement, using the existing renderer's PCM helpers.
    data=np.zeros(math.ceil(total*SR)); melody=[50,57,62,64,62,57,55,52]
    for i,start in enumerate(np.arange(.3,total-1,2.7)):
        t=np.arange(round(4.1*SR))/SR
        hz=440*2**((melody[i%len(melody)]-69)/12)
        note=(np.sin(2*np.pi*hz*t)+.22*np.sin(2*np.pi*hz*2*t))
        add(data,.035*(1-np.exp(-t*5))*np.exp(-t/1.8)*note,float(start))
    data*=np.minimum(np.arange(len(data))/(2*SR),1)*np.minimum(np.arange(len(data))[::-1]/(3*SR),1)
    write_wav(path,data)

def timestamp(t):
    ms=round(t*1000);h,ms=divmod(ms,3600000);m,ms=divmod(ms,60000);s,ms=divmod(ms,1000)
    return f'{h:02}:{m:02}:{s:02},{ms:03}'

def main():
    spec=json.loads((ROOT/'story.json').read_text())
    out=ROOT/'output';out.mkdir(exist_ok=True)
    voices=ROOT/'voices';voices.mkdir(exist_ok=True)
    photos=ROOT/'photos';photos.mkdir(exist_ok=True)
    fonts=ROOT/'fonts';fonts.mkdir(exist_ok=True)
    # New text is synthesized ONLY by the current repository generator on GitHub runner.
    for i,s in enumerate(spec['scenes']):
        text=voices/f'{i+1:02}.txt'; text.write_text(s['text'],encoding='utf-8')
        audio=text.with_suffix('.mp3');meta=text.with_suffix('.json')
        if audio.exists():
            record=json.loads(meta.read_text())
            if record['status']!='SUCCESS' or record['voice_id']!='068' or sha(audio)!=record['sha256']:
                raise RuntimeError('Voice reuse verification failed')
            if record['text_sha256']!=hashlib.sha256(s['text'].encode()).hexdigest():
                print(f'INVALIDATE revised script scene {i+1}; unaffected speech retained',flush=True)
                for suffix in ['.mp3','.json','.srt','.progress.json']:
                    text.with_suffix(suffix).unlink(missing_ok=True)
            else:
                print(f'REUSE VERIFIED scene {i+1} sha256={record["sha256"]}',flush=True)
        if not audio.exists():
            subprocess.run([sys.executable,str(REPO/'smart_voice/generate_voice.py'),'--voice-id','068','--text-file',str(text),'--output',str(audio)],check=True)
    lengths=[duration(voices/f'{i+1:02}.mp3') for i in range(len(spec['scenes']))]
    spoken=sum(lengths);total=spec['target_seconds'];intro=1.0;credits=7.0
    if spoken>total-intro-credits:
        raise RuntimeError(f'Narration {spoken:.3f}s exceeds target; revise only script, do not retime voice')
    gap=(total-intro-credits-spoken)/len(lengths)
    assets={a['id']:a for a in spec['assets']}
    for a in spec['assets']:
        download(a['url'],photos/a['file'])
        Image.open(photos/a['file']).verify()
        a['sha256']=sha(photos/a['file'])
    download('https://raw.githubusercontent.com/notofonts/noto-cjk/main/Sans/OTF/TraditionalChinese/NotoSansCJKtc-Regular.otf',fonts/'NotoSansCJKtc-Regular.otf')
    download('https://raw.githubusercontent.com/notofonts/noto-cjk/main/Sans/LICENSE',fonts/'font-license.txt')
    timeline=[];cursor=intro;subtitles=[];audio_commands=[]
    for i,(s,length) in enumerate(zip(spec['scenes'],lengths)):
        audio=voices/f'{i+1:02}.mp3'
        start=0 if i==0 else cursor
        end=cursor+length+gap
        timeline.append({'index':i+1,'start':start,'end':end,'speech_start':cursor,'speech_end':cursor+length,'photo':s['photo'],'title':s['title'],'source_sha256':sha(audio)})
        for block in audio.with_suffix('.srt').read_text().strip().split('\n\n'):
            lines=block.splitlines();a,b=map(seconds,lines[1].split(' --> '));text=''.join(lines[2:])
            subtitles.append((a+cursor,b+cursor,text))
        # Append silence only as shot transition after VERIFIED spoken audio, never as voice.
        part=out/f'speech_part_{i+1:02}.wav'
        padding=gap+(intro if i==0 else 0)
        vf=f'adelay={round(intro*1000)}:all=1,' if i==0 else ''
        run(['ffmpeg','-y','-v','error','-i',str(audio),'-af',vf+f'apad=whole_dur={length+padding}', '-t',str(length+padding),'-ar',str(SR),'-ac','1',str(part)])
        audio_commands.append(part);cursor=end
    # Spoken text must survive alignment without omissions or inventions.
    normalize=lambda t: ''.join(c for c in t if c.isalnum())
    if normalize(''.join(t[2] for t in subtitles))!=normalize(''.join(s['text'] for s in spec['scenes'])): raise RuntimeError('Caption text mismatch')
    srt=out/'krill_068.srt'
    srt.write_text(''.join(f'{i}\n{timestamp(a)} --> {timestamp(b)}\n{text}\n\n' for i,(a,b,text) in enumerate(subtitles,1)),encoding='utf-8')
    count=captions(srt,out/'captions.ass',total)
    ass=(out/'captions.ass').read_text().replace('PlayResX: 1280','PlayResX: 1920').replace('PlayResY: 720','PlayResY: 1080').replace('TC,32,','TC,45,').replace('85,85,34','128,128,45')
    (out/'captions.ass').write_text(ass,encoding='utf-8')
    clips=[];bounds=[round(t['start']*FPS) for t in timeline]+[round((total-credits)*FPS)]
    for i,s in enumerate(spec['scenes']):
        p=out/f'plate_{i+1:02}.png';plate(s,i,assets,p)
        frames=bounds[i+1]-bounds[i];clip=out/f'shot_{i+1:02}.mp4';clips.append(clip)
        # Pan/zoom within the photo window; graphic panel remains fixed and readable.
        vf=(f"split=2[base][img];[img]crop=1180:790:40:145,scale=2360:1580,zoompan=z='1+0.035*on/{max(1,frames-1)}':x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2':d={frames}:s=1180x790:fps={FPS}[move];[base]loop=loop={frames-1}:size=1:start=0,setpts=N/({FPS}*TB)[fixed];[fixed][move]overlay=40:145:shortest=1,fade=t=in:st=0:d=0.22,format=yuv420p")
        run(['ffmpeg','-y','-v','error','-threads','2','-i',str(p),'-filter_complex',vf,'-frames:v',str(frames),'-an','-c:v','libx264','-preset','fast','-crf','21','-threads','2',str(clip)])
        print(f'SHOT {i+1} SUCCESS',flush=True)
    # Credits are inside the delivered MP4; full clickable URLs are provided separately.
    im=Image.new('RGB',(W,H),(8,24,35));d=ImageDraw.Draw(im)
    d.text((90,70),'照片來源與授權',font=font(52),fill=(240,244,231))
    for i,a in enumerate(spec['assets']):
        d.text((90,190+i*100),a['id'].upper()+'  /  '+a['credit'],font=font(28),fill=(205,226,228))
    d.text((90,835),'CC BY 2.0: creativecommons.org/licenses/by/2.0/',font=font(28),fill=(117,218,218))
    d.text((90,900),'修改：裁切、排版、鏡頭運動。完整連結及科學來源見隨附說明。',font=font(28),fill=(205,226,228))
    im.save(out/'credits.png');clip=out/'credits.mp4';clips.append(clip)
    run(['ffmpeg','-y','-v','error','-loop','1','-i',str(out/'credits.png'),'-t',str(credits),'-r',str(FPS),'-an','-c:v','libx264','-preset','fast','-crf','21','-threads','2','-pix_fmt','yuv420p',str(clip)])
    listing=out/'picture.concat.txt';listing.write_text(''.join(f"file '{p}'\n" for p in clips))
    run(['ffmpeg','-y','-v','error','-f','concat','-safe','0','-i',str(listing),'-c','copy',str(out/'picture.mp4')])
    listing=out/'audio.concat.txt';listing.write_text(''.join(f"file '{p}'\n" for p in audio_commands))
    run(['ffmpeg','-y','-v','error','-f','concat','-safe','0','-i',str(listing),'-af',f'apad=pad_dur={credits}','-t',str(total),'-c:a','libmp3lame','-b:a','192k',str(out/'krill_068.mp3')])
    music(out/'music.wav',total)
    run(['ffmpeg','-y','-v','error','-i',str(out/'krill_068.mp3'),'-i',str(out/'music.wav'),'-filter_complex','[0:a][1:a]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-13:TP=-1:LRA=7[a]','-map','[a]','-ar','48000','-ac','2',str(out/'mixed.wav')])
    result=out/'Krill_Real_Photos_068.mp4'
    run(['ffmpeg','-y','-v','error','-i',str(out/'picture.mp4'),'-i',str(out/'mixed.wav'),'-vf',f"ass='{out/'captions.ass'}':fontsdir='{fonts}'",'-map','0:v:0','-map','1:a:0','-c:v','libx264','-preset','fast','-crf','21','-threads','2','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-t',str(total),'-disposition:a:0','default','-movflags','+faststart',str(result)])
    run(['ffmpeg','-v','error','-xerror','-i',str(result),'-f','null','-'])
    level=measure(result)
    if float(level['input_i'])<-24 or float(level['input_tp'])>=0: raise RuntimeError('Mix volume failed')
    probe=json.loads(run(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(result)]))
    video=next(s for s in probe['streams'] if s['codec_type']=='video');audio=next(s for s in probe['streams'] if s['codec_type']=='audio')
    if (video['width'],video['height'],video['codec_name'],audio['codec_name'])!=(W,H,'h264','aac') or abs(float(probe['format']['duration'])-total)>.1: raise RuntimeError('Format/duration failed')
    for i,t in enumerate(timeline):
        at=t['speech_start']+min(3,(t['speech_end']-t['speech_start'])/2)
        run(['ffmpeg','-y','-v','error','-ss',str(at),'-i',str(result),'-frames:v','1',str(out/f'qa_{i+1:02}.jpg')])
    qa={'technical_status':'SUCCESS','visual_qa':'PENDING','subjective_listening':'UNCERTAIN','id':spec['id'],'format':'1920x1080, 25fps, H.264/AAC stereo','duration':probe['format']['duration'],'full_decode':'PASS','spoken_seconds':spoken,'transition_seconds_per_scene':gap,'caption_count':count,'caption_text_coverage':'PASS','loudness':level,'voice_id':'068','preset':json.loads((voices/'01.json').read_text())['preset'],'motion':spec['motion'],'auto_ducking':False,'music_source':'Original procedural documentary bed; low fixed gain, not recorded instruments','sfx':'Omitted: no verified suitable asset','sha256':sha(result),'timeline':timeline,'publication_status':'UNPUBLISHED'}
    (out/'QA.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2))
    (out/'asset_manifest.json').write_text(json.dumps(spec,ensure_ascii=False,indent=2))
    desc=['# 磷蝦多到養活鯨魚，為什麼我們餐桌上很少見？','', '真實照片運鏡影片；照片中的動物沒有被動畫化。068 曉臻中文旁白，實測語音字幕。','', '## 照片來源與授權','']
    for a in spec['assets']:
        desc.extend([f"- {a['id']}: {a['author']} — {a['license']}",f"  {a['page']}",f"  授權：{a.get('license_url','https://commons.wikimedia.org/wiki/Template:PD-USGov-NOAA')}",'  修改：裁切、鏡頭運動、排版。'])
    desc.extend(['','## 科學來源','']+[f"- {s['url']} — {s['supports']}" for s in spec['sources']])
    desc.extend(['','## 說明','座頭鯨照片攝於美國 Stellwagen Bank，用作攝食示意；海冰照片攝於1999年，非即時海況。','距離及售價是供應鏈推論；三道門檻是敘事模型，並非研究量化排名。','沒有宣稱磷蝦不能吃、醫療功效、當前捕撈配額或當前總量。','背景音樂為本次程序生成；未加入無授權音效。','技術驗證成功；主觀及手機試聽待確認；未發布。'])
    (out/'照片授權與影片說明.md').write_text('\n'.join(desc),encoding='utf-8')
    (out/'narration.txt').write_text('\n\n'.join(s['text'] for s in spec['scenes']))
    print(json.dumps(qa,ensure_ascii=False),flush=True)

if __name__=='__main__':main()
