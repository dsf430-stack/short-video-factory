#!/usr/bin/env python3
"""V2 editorial adapter; reuses verified 068 synthesis and v1/storybook media helpers."""
import sys, json, math, hashlib, asyncio, argparse, importlib.util, time, shutil, traceback
from pathlib import Path
import numpy as np
from PIL import Image,ImageOps,ImageDraw,ImageFilter
ROOT=Path(__file__).resolve().parent;REPO=ROOT.parents[1]
sys.path.insert(0,str(REPO/'smart_voice/storybook'))
from book_media import run,duration
from render_cached_book import captions,seconds,measure,write_wav,add
module=importlib.util.spec_from_file_location('krill_v1_helpers',REPO/'smart_voice/krill_realphotos_20261013/produce.py')
v1=importlib.util.module_from_spec(module);module.loader.exec_module(v1);v1.ROOT=ROOT
FPS,W,H,SR=25,1920,1080,44100
OUT=ROOT/'output';VOICE=ROOT/'voices';PHOTOS=ROOT/'photos';FONTS=ROOT/'fonts'
for p in [OUT,VOICE,PHOTOS,FONTS]:p.mkdir(exist_ok=True)
SPEC=json.loads((ROOT/'story.json').read_text(encoding='utf-8'))
ASSETS={a['id']:a for a in SPEC['assets']}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def font(n):return v1.font(n)
def wrap(text,n):return [text[i:i+n] for i in range(0,len(text),n)]

def voice_stage():
    sys.path.insert(0,str(REPO/'smart_voice'))
    import generate_voice as gen
    base=dict(gen.VOICES['068'])
    for i,b in enumerate(SPEC['blocks'],1):
        target=VOICE/f'{i:02}.mp3';preset={**base,**SPEC['presets'][b['kind']]}
        text=b['text'];expected=hashlib.sha256(text.encode()).hexdigest()
        (VOICE/f'{i:02}.txt').write_text(text,encoding='utf-8')
        if target.exists():
            meta=json.loads(target.with_suffix('.json').read_text())
            if meta['status']!='SUCCESS' or meta['preset']!=preset or meta['text_sha256']!=expected or meta['sha256']!=sha(target):raise RuntimeError('V2 voice cache mismatched')
            print(f'REUSE VERIFIED V2 scene {i}',flush=True);continue
        # The override is scoped to this process and clip. No voices.json or main edits.
        gen.VOICES['068']=preset
        try:asyncio.run(gen.synthesize(text,str(target),'068'))
        except Exception as error:
            target.with_suffix('.error.log').write_text(traceback.format_exc(),encoding='utf-8')
            journal=target.with_suffix('.progress.json')
            if journal.exists():
                record=json.loads(journal.read_text());record.update(status='FAILED',error_type=type(error).__name__);gen.atomic_json(journal,record)
            raise
        finally:gen.VOICES['068']=base
        print(f'V2 VOICE {i} SUCCESS rate={preset["rate"]} pitch={preset["pitch"]}',flush=True)
    total=sum(duration(VOICE/f'{i:02}.mp3') for i in range(1,len(SPEC['blocks'])+1))
    (OUT/'voice_summary.json').write_text(json.dumps({'status':'SUCCESS','spoken_seconds':total,'base_preset_unchanged':base,'clip_presets':SPEC['presets'],'scope':SPEC['scope']},ensure_ascii=False,indent=2))
    print(f'V2 SPEECH {total:.3f}s',flush=True)

def assets_stage():
    for a in SPEC['assets']:
        print('DOWNLOAD '+a['id'],flush=True)
        v1.download(a['url'],PHOTOS/a['file']);Image.open(PHOTOS/a['file']).verify();time.sleep(1)
    v1.download('https://raw.githubusercontent.com/notofonts/noto-cjk/main/Sans/OTF/TraditionalChinese/NotoSansCJKtc-Regular.otf',FONTS/'NotoSansCJKtc-Regular.otf')
    v1.download('https://raw.githubusercontent.com/notofonts/noto-cjk/main/Sans/LICENSE',FONTS/'font-license.txt')
    # Keep reusable assets on the runner/artifact for later revisions.
    for a in SPEC['assets']:a['sha256']=sha(PHOTOS/a['file'])
    if len({a['sha256'] for a in SPEC['assets']})!=len(SPEC['assets']):raise RuntimeError('Duplicate photo bytes')
    (OUT/'asset_manifest.json').write_text(json.dumps(SPEC,ensure_ascii=False,indent=2),encoding='utf-8')

def photo(asset):return Image.open(PHOTOS/ASSETS[asset]['file']).convert('RGB')

def layout(shot,index):
    ids=[shot[0]]+shot[3:];style=shot[2];im=Image.new('RGB',(W,H),(7,17,28))
    # Full-screen photographic compositions, alternating with split and triptych.
    if style=='portrait':
        src=photo(ids[0]);bg=ImageOps.fit(src,(W,H),method=Image.Resampling.LANCZOS).filter(ImageFilter.GaussianBlur(32));im.paste(bg)
        fg=ImageOps.contain(src,(1100,880),method=Image.Resampling.LANCZOS);im.paste(fg,((W-fg.width)//2,105))
    elif style=='split':
        for j,k in enumerate(ids[:2]):im.paste(ImageOps.fit(photo(k),(950,H),method=Image.Resampling.LANCZOS),(j*970,0))
    elif style=='trio':
        for j,k in enumerate(ids[:3]):im.paste(ImageOps.fit(photo(k),(630,H),method=Image.Resampling.LANCZOS),(j*645,0))
    else:
        src=photo(ids[0])
        if style=='detail':
            w,h=src.size;src=src.crop((int(w*.07),int(h*.07),int(w*.93),int(h*.93)))
        im=ImageOps.fit(src,(W,H),method=Image.Resampling.LANCZOS,centering=(.5,.45))
    bg=OUT/f'photo_{index:02}.png';im.save(bg)
    layer=Image.new('RGBA',(W,H),(0,0,0,0));d=ImageDraw.Draw(layer)
    # Light gradients reserve reading space without a fixed presentation panel.
    for y in range(300):d.line((0,y,W,y),fill=(4,15,22,int(170*(1-y/300))))
    for y in range(900,H):d.line((0,y,W,y),fill=(3,11,17,int(90+140*(y-900)/180)))
    d.rounded_rectangle((40,25,360,72),radius=8,fill=(5,28,42,215))
    d.text((58,31),'阿福的冷知識  /  KRILL',font=font(25),fill=(95,228,219,255))
    for j,line in enumerate(wrap(shot[1],14)):
        d.text((44,112+j*78),line,font=font(62),fill=(255,243,188,255),stroke_width=3,stroke_fill=(5,15,25,230))
    label='  /  '.join(ASSETS[k]['label'] for k in ids)
    # Source identifiers link to full credits. Keep factual context readable.
    for j,line in enumerate(wrap(label,54)):
        d.text((44,822+j*29),line,font=font(22),fill=(245,249,252,255),stroke_width=1,stroke_fill=(0,0,0,255))
    credits=' | '.join(f'#{list(ASSETS).index(k)+1:02} '+ASSETS[k]['author']+' · '+ASSETS[k]['license'] for k in ids)
    for j,line in enumerate(wrap(credits,128)):
        d.text((44,891+j*22),line,font=font(16),fill=(221,236,244,255),stroke_width=1,stroke_fill=(0,0,0,255))
    over=OUT/f'overlay_{index:02}.png';layer.save(over)
    return bg,over,ids

def soundtrack(seconds_total,shots):
    n=math.ceil(seconds_total*SR);music=np.zeros(n);fx=np.zeros(n);rng=np.random.default_rng(68101302)
    beat=60/112;notes=[50,57,62,65,64,62,57,55]
    for i,start in enumerate(np.arange(.2,seconds_total-.5,beat)):
        if i%4==0:
            t=np.arange(round(1.9*SR))/SR;hz=440*2**((notes[(i//4)%len(notes)]-69)/12)
            add(music,.019*(1-np.exp(-t*20))*np.exp(-t/0.7)*(np.sin(2*np.pi*hz*t)+.2*np.sin(2*np.pi*2*hz*t)),float(start))
        t=np.arange(round(.11*SR))/SR
        if i%2==0:add(music,.01*np.sin(2*np.pi*(80*t-90*t*t))*np.exp(-t*37),float(start))
        else:add(music,.0028*rng.normal(0,1,len(t))*np.exp(-t*90),float(start))
    cues=[]
    for shot in shots[1:]:
        when=shot['start'];t=np.arange(round(.13*SR))/SR
        sound=.012*np.sin(2*np.pi*(850*t+2600*t*t))*np.sin(np.pi*t/.13)**2
        add(fx,sound,when);cues.append({'time':when,'type':'original synthetic soft transition accent'})
    fade=np.minimum(np.arange(n)/(SR*.5),1)*np.minimum(np.arange(n)[::-1]/(SR*2),1)
    write_wav(OUT/'music.wav',music*fade);write_wav(OUT/'sfx.wav',fx)
    return cues

def render_stage():
    records=[]
    for i,b in enumerate(SPEC['blocks'],1):
        p=VOICE/f'{i:02}.mp3';m=json.loads(p.with_suffix('.json').read_text())
        if m['status']!='SUCCESS' or sha(p)!=m['sha256'] or m['text_sha256']!=hashlib.sha256(b['text'].encode()).hexdigest() or m['preset']['rate']!=SPEC['presets'][b['kind']]['rate']:raise RuntimeError('Voice contract failed')
        records.append((p,m,duration(p)))
    spoken=sum(x[2] for x in records);total=spoken+SPEC['lead_seconds']+SPEC['chapter_pause']*len(records)+SPEC['credit_seconds']
    if not 140<=total<=215:raise RuntimeError(f'Unexpected V2 length {total}')
    subtitles=[];shots=[];parts=[];cursor=SPEC['lead_seconds']
    for i,(b,(p,m,length)) in enumerate(zip(SPEC['blocks'],records)):
        end=cursor+length+SPEC['chapter_pause'];start=0 if i==0 else cursor
        for block in p.with_suffix('.srt').read_text().strip().split('\n\n'):
            lines=block.splitlines();a,z=map(seconds,lines[1].split(' --> '));subtitles.append((cursor+a,cursor+z,''.join(lines[2:])))
        n=max(3,math.ceil((end-start)/4.7));selected=list(b['shots'])
        while len(selected)<n:
            base=list(b['shots'][(len(selected)-3)%len(b['shots'])]);base[2]='detail' if base[2]=='full' else base[2];selected.append(base)
        boundaries=[round((start+(end-start)*j/n)*FPS) for j in range(n+1)]
        for j,shot in enumerate(selected):shots.append({'index':len(shots)+1,'start':boundaries[j]/FPS,'end':boundaries[j+1]/FPS,'frames':boundaries[j+1]-boundaries[j],'block':i+1,'spec':shot})
        part=OUT/f'speech_{i+1:02}.wav';lead=SPEC['lead_seconds'] if i==0 else 0
        gain=1.055 if b['kind'] in ('hook','reveal') else .98
        vf=(f'adelay={round(lead*1000)}:all=1,' if lead else '')+f'volume={gain},apad=whole_dur={length+lead+SPEC["chapter_pause"]}'
        run(['ffmpeg','-y','-v','error','-i',str(p),'-af',vf,'-t',str(length+lead+SPEC['chapter_pause']),'-ar',str(SR),'-ac','1',str(part)])
        parts.append(part);cursor=end
    normalize=lambda t:''.join(c for c in t if c.isalnum())
    if normalize(''.join(s[2] for s in subtitles))!=normalize(''.join(b['text'] for b in SPEC['blocks'])):raise RuntimeError('Measured captions omit text')
    srt=OUT/'krill_068_v2.srt';srt.write_text(''.join(f'{i}\n{v1.timestamp(a)} --> {v1.timestamp(z)}\n{text}\n\n' for i,(a,z,text) in enumerate(subtitles,1)),encoding='utf-8')
    count=captions(srt,OUT/'captions.ass',total)
    ass=(OUT/'captions.ass').read_text().replace('PlayResX: 1280','PlayResX: 1920').replace('PlayResY: 720','PlayResY: 1080').replace('TC,32,','TC,49,').replace('85,85,34','128,128,43')
    (OUT/'captions.ass').write_text(ass,encoding='utf-8')
    clips=[];used=set()
    for shot in shots:
        i=shot['index'];frames=shot['frames'];bg,overlay,ids=layout(shot['spec'],i);used.update(ids)
        target=OUT/f'shot_{i:02}.mp4';clips.append(target)
        maxzoom=.07 if shot['spec'][2]=='detail' else .045
        z=f'1+{maxzoom}*on/{max(1,frames-1)}' if i%2 else f'{1+maxzoom}-{maxzoom}*on/{max(1,frames-1)}'
        x='iw/2-iw/zoom/2' if i%3 else '(iw-iw/zoom)*0.55'
        vf=f"[0:v]scale=2880:1620,zoompan=z='{z}':x='{x}':y='ih/2-ih/zoom/2':d={frames}:s={W}x{H}:fps={FPS}[bg];[bg][1:v]overlay=0:0,format=yuv420p"
        run(['ffmpeg','-y','-v','error','-i',str(bg),'-i',str(overlay),'-filter_complex',vf,'-frames:v',str(frames),'-an','-c:v','libx264','-preset','fast','-crf','21','-threads','2',str(target)])
        print(f'V2 SHOT {i}/{len(shots)} SUCCESS',flush=True)
    if used!=set(ASSETS):raise RuntimeError(f'Unused photos: {set(ASSETS)-used}')
    im=Image.new('RGB',(W,H),(5,23,34));d=ImageDraw.Draw(im);d.text((55,55),'真實照片來源與授權',font=font(48),fill=(244,247,228))
    for i,a in enumerate(SPEC['assets']):
        x=55+(i%3)*625;y=173+(i//3)*117
        for j,line in enumerate(wrap(f'#{i+1:02} {a["author"]}',43)):d.text((x,y+j*26),line,font=font(20),fill=(205,230,237))
        d.text((x,y+65),a['license'],font=font(20),fill=(90,219,209))
    d.text((55,940),'CC BY 2.0 / 3.0：creativecommons.org/licenses/by/2.0/、by/3.0/',font=font(24),fill=(205,230,237))
    d.text((55,987),'修改：裁切、鏡頭運動、排版。完整連結與科學來源見隨附說明。',font=font(24),fill=(205,230,237))
    im.save(OUT/'credits.png');endframes=math.ceil(total*FPS)-shots[-1]['end']*FPS;clip=OUT/'credits.mp4';clips.append(clip)
    run(['ffmpeg','-y','-v','error','-loop','1','-i',str(OUT/'credits.png'),'-frames:v',str(round(endframes)),'-r',str(FPS),'-an','-c:v','libx264','-preset','fast','-crf','21','-threads','2','-pix_fmt','yuv420p',str(clip)])
    listing=OUT/'picture.concat.txt';listing.write_text(''.join(f"file '{p}'\n" for p in clips))
    run(['ffmpeg','-y','-v','error','-f','concat','-safe','0','-i',str(listing),'-c','copy',str(OUT/'picture.mp4')])
    listing=OUT/'speech.concat.txt';listing.write_text(''.join(f"file '{p}'\n" for p in parts))
    run(['ffmpeg','-y','-v','error','-f','concat','-safe','0','-i',str(listing),'-af',f'apad=whole_dur={total}','-t',str(total),'-c:a','libmp3lame','-b:a','192k',str(OUT/'krill_068_v2.mp3')])
    cues=soundtrack(total,shots)
    run(['ffmpeg','-y','-v','error','-i',str(OUT/'krill_068_v2.mp3'),'-i',str(OUT/'music.wav'),'-i',str(OUT/'sfx.wav'),'-filter_complex','[0:a][1:a][2:a]amix=inputs=3:duration=first:normalize=0,loudnorm=I=-13:TP=-1:LRA=7[a]','-map','[a]','-ar','48000','-ac','2',str(OUT/'mixed.wav')])
    result=OUT/'Krill_Real_Photos_068_v2.mp4'
    run(['ffmpeg','-y','-v','error','-i',str(OUT/'picture.mp4'),'-i',str(OUT/'mixed.wav'),'-vf',f"ass='{OUT/'captions.ass'}':fontsdir='{FONTS}'",'-map','0:v:0','-map','1:a:0','-c:v','libx264','-preset','fast','-crf','21','-threads','2','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-t',str(total),'-disposition:a:0','default','-movflags','+faststart',str(result)])
    run(['ffmpeg','-v','error','-xerror','-i',str(result),'-f','null','-']);level=measure(result)
    if float(level['input_i'])<-24 or float(level['input_tp'])>=0:raise RuntimeError('Final volume failed')
    probe=json.loads(run(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(result)]));video=next(s for s in probe['streams'] if s['codec_type']=='video');audio=next(s for s in probe['streams'] if s['codec_type']=='audio')
    if (video['width'],video['height'],video['codec_name'],audio['codec_name'])!=(W,H,'h264','aac') or abs(float(probe['format']['duration'])-total)>.15:raise RuntimeError('Output contract failed')
    for shot in shots:
        run(['ffmpeg','-y','-v','error','-ss',str((shot['start']+shot['end'])/2),'-i',str(result),'-frames:v','1',str(OUT/f'qa_{shot["index"]:02}.jpg')])
    qa={'technical_status':'SUCCESS','visual_qa':'PENDING','subjective_listening':'UNCERTAIN','id':SPEC['id'],'duration':probe['format']['duration'],'format':'1920x1080 25fps H.264/AAC stereo','full_decode':'PASS','caption_count':count,'caption_text_coverage':'PASS','distinct_photos':len(used),'shot_count':len(shots),'mean_shot_seconds':sum(s['end']-s['start'] for s in shots)/len(shots),'max_shot_seconds':max(s['end']-s['start'] for s in shots),'voice_id':'068','clip_presets':SPEC['presets'],'base_068_settings_unchanged':True,'spoken_seconds':spoken,'loudness':level,'sha256':sha(result),'timeline':shots,'audio_sources':'original procedural 112 BPM bed and soft transition accents','auto_ducking':False,'publication_status':'UNPUBLISHED'}
    (OUT/'QA_v2.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2),encoding='utf-8')
    desc=['# 磷蝦真實照片第二版','', '回應修改：增加不同照片、縮短鏡頭、短句與問答開場；068聲線不變，本片逐段語速+27%～+44%、音調+2～+14Hz；沒有改動全域068設定。','', '照片為真實攝影，動物沒有被動畫化。顯微照片、特寫、滿版、雙畫面與三畫面交替。','', '## 照片來源與授權','']
    for i,a in enumerate(SPEC['assets'],1):desc.extend([f'- #{i:02} {a["author"]} — {a["license"]}',f'  {a["page"]}',f'  授權：{a.get("license_url","https://commons.wikimedia.org/wiki/Template:PD-USGov-NOAA")}',f'  內容：{a["label"]}；修改：裁切、鏡頭運動、排版。'])
    desc.extend(['','## 科學來源','']+[f'- {s["url"]} — {s["supports"]}' for s in SPEC['sources']])
    desc.extend(['','## 口徑與驗證','美國Farallones磷蝦群與手指上的磷蝦只作一般磷蝦示意，未宣称是南極磷蝦。','海外座頭鯨照片標示拍攝口徑；有另外加入南極Fournier Bay鯨魚照片。','Agulhas為研究船，用作极地航行示意，未聲稱是磷蝦捕撈船。','冰景為歷史照片，非當前海冰資料。','供應鏈及市場門檻是解說推論，非量化原因排名。','配樂與轉場提示音為本次程序生成；低固定增益，不宣稱自動ducking。','技術驗證通過；主觀聲音喜好與手機試聽待確認。'])
    (OUT/'照片授權與影片說明_v2.md').write_text('\n'.join(desc),encoding='utf-8')
    (OUT/'narration_v2.txt').write_text('\n\n'.join(b['text'] for b in SPEC['blocks']),encoding='utf-8')
    print(json.dumps({k:qa[k] for k in ['technical_status','duration','distinct_photos','shot_count','max_shot_seconds','spoken_seconds','loudness']},ensure_ascii=False),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--stage',choices=['voice','assets','render'],required=True);args=p.parse_args()
    {'voice':voice_stage,'assets':assets_stage,'render':render_stage}[args.stage]()
