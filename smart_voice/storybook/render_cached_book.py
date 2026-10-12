#!/usr/bin/env python3
"""068 companion renderer: reuse measured MP3/SRT; animate pages and mix real stems."""
import argparse, hashlib, json, math, re, shutil, wave
from pathlib import Path
import numpy as np

from book_media import run, duration
ROOT = Path(__file__).resolve().parent
SR, FPS = 44100, 25

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def write_wav(path, data):
    if not np.isfinite(data).all() or np.max(np.abs(data)) >= 1:
        raise ValueError('Invalid generated audio')
    with wave.open(str(path), 'wb') as f:
        f.setnchannels(1); f.setsampwidth(2); f.setframerate(SR)
        f.writeframes((data * 32767).astype('<i2').tobytes())

def add(dst, sound, start):
    a = round(start * SR); b = min(len(dst), a + len(sound))
    if a < 0 or a >= len(dst):
        raise ValueError('Sound cue out of range')
    dst[a:b] += sound[:b-a]

def make_stems(out, seconds):
    n = math.ceil(seconds * SR)
    music = np.zeros(n); fx = np.zeros(n)
    rng = np.random.default_rng(681012)
    # Original pentatonic composition. Harmonic synthesis, not recordings of instruments.
    melody = [62, 69, 74, 76, 74, 69, 67, 64, 62, 67, 69, 74, 69, 67, 64, 62]
    for i, start in enumerate(np.arange(0.6, seconds - 1, 1.6)):
        midi = melody[i % len(melody)]
        f = 440 * 2 ** ((midi - 69) / 12)
        t = np.arange(round(3.2 * SR)) / SR
        env = (1 - np.exp(-t * 35)) * np.exp(-t / 1.1)
        note = sum((1 / h**1.7) * np.sin(2 * np.pi * f * h * t) for h in range(1, 6))
        add(music, 0.23 * env * note, float(start))
        if i % 4 == 0:
            tb = np.arange(round(5.5 * SR)) / SR
            fb = 146.8324 if (i // 4) % 2 == 0 else 130.8128
            bass = np.sin(2*np.pi*fb*tb) + .3*np.sin(2*np.pi*fb*2*tb)
            add(music, .085 * (1-np.exp(-tb*4)) * np.exp(-tb/2.5) * bass, float(start))
    music *= np.minimum(np.arange(n)/(.8*SR),1) * np.minimum(np.arange(n)[::-1]/(1.5*SR),1)
    music *= .45 / np.max(np.abs(music))
    cues = []
    # Gentle synthesized wind in the siege and outdoor march; explicitly synthetic foley.
    wind = rng.normal(0, 1, n)
    wind = np.convolve(wind, np.ones(180)/180, mode='same')
    clock = np.arange(n) / SR
    envelope = np.zeros(n)
    for start, end in [(0, 8.427), (30.719, 44.385)]:
        gate = np.clip((clock-start)/.7,0,1) * np.clip((end-clock)/.7,0,1)
        envelope += gate
    fx += .11 * wind * envelope
    cues.append({'type':'synthesized soft wind','intervals':[[0,8.427],[30.719,44.385]]})
    for start, end, spacing in [(5.9,8.1,.42),(30.9,34.4,.5),(35.0,39.0,.36)]:
        for j, when in enumerate(np.arange(start,end,spacing)):
            t = np.arange(round(.14*SR)) / SR
            thud = np.sin(2*np.pi*(95-160*t)*t) * np.exp(-t*40)
            noise = rng.normal(0,1,len(t)) * np.exp(-t*75)
            add(fx,.22*thud+.06*noise,float(when))
        cues.append({'type':'synthesized hoof/footstep pulses','start':start,'end':end})
    # Paper rustle as the strategist points to the parchment.
    t = np.arange(round(.6*SR)) / SR
    rustle = rng.normal(0,1,len(t))
    rustle = np.convolve(rustle,np.ones(6)/6,mode='same')
    add(fx,.07*rustle*np.sin(np.pi*t/.6)**2,13.35)
    cues.append({'type':'synthesized paper rustle','start':13.35,'end':13.95})
    for when in [46.5,48.7,51.2]:
        t = np.arange(round(.38*SR)) / SR
        chirp = np.sin(2*np.pi*(1800*t+900*t*t)) * np.sin(np.pi*t/.38)**2
        add(fx,.055*chirp,when)
    cues.append({'type':'synthesized gentle bird chirps','starts':[46.5,48.7,51.2]})
    if np.max(np.abs(fx)) >= .8:
        raise ValueError('Foley would clip')
    write_wav(out/'background_music.wav',music)
    write_wav(out/'environment_sfx.wav',fx)
    return cues

def seconds(t):
    h,m,s = t.replace(',','.').split(':')
    return int(h)*3600+int(m)*60+float(s)

def ass_time(t):
    cs = round(t*100); h,cs = divmod(cs,360000); m,cs = divmod(cs,6000); s,cs = divmod(cs,100)
    return f'{h}:{m:02}:{s:02}.{cs:02}'

def captions(srt, out, total):
    blocks = srt.read_text(encoding='utf-8-sig').strip().split('\n\n')
    events = []
    previous = 0
    for block in blocks:
        lines = block.splitlines()
        start,end = map(seconds,lines[1].split(' --> '))
        text = ''.join(lines[2:])
        if not 0<=start<end<=total+.15 or start<previous:
            raise ValueError('Invalid measured subtitles')
        previous=end
        # Typesetting only: preserve all text and measured cue times.
        wrapped = '\\N'.join(text[i:i+24] for i in range(0,len(text),24))
        events.append(f'Dialogue: 0,{ass_time(start)},{ass_time(end)},Caption,,0,0,0,,{wrapped}')
    head = '''[Script Info]
ScriptType: v4.00+
PlayResX: 1280
PlayResY: 720
WrapStyle: 2
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Caption,Noto Sans CJK TC,32,&H00FFFFFF,&H00FFFFFF,&H00201811,&H90000000,0,0,0,0,100,100,0,0,1,2,1,2,85,85,34,1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
'''
    out.write_text(head+'\n'.join(events)+'\n',encoding='utf-8')
    return len(events)

def measure(path):
    import subprocess
    p = subprocess.run(['ffmpeg','-hide_banner','-i',str(path),'-af','loudnorm=I=-13:TP=-1:LRA=7:print_format=json','-f','null','-'],capture_output=True,text=True)
    if p.returncode:
        raise RuntimeError(p.stderr)
    return json.loads(p.stderr[p.stderr.rfind('{'):])

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('manifest'); args=ap.parse_args()
    source = Path(args.manifest).resolve(); base=source.parent
    spec=json.loads(source.read_text(encoding='utf-8'))
    out=base/'output'; out.mkdir(exist_ok=True)
    voice=base/spec['narration']; meta=json.loads((base/spec['audio_metadata']).read_text())
    if sha(voice)!=meta['sha256'] or meta['status']!='SUCCESS':
        raise ValueError('Narration cache verification failed')
    total=duration(voice)
    scenes=spec['scenes']
    if scenes[0]['start']!=0 or any(a['end']!=b['start'] for a,b in zip(scenes,scenes[1:])):
        raise ValueError('Scene timeline gap or overlap')
    if abs(scenes[-1]['end']-total)>.1:
        raise ValueError('Timeline does not cover the measured narration')
    font=base/spec['font']; fontdir=font.parent
    if not font.is_file():
        raise FileNotFoundError(font)
    clips=[]
    bounds=[round(s['start']*FPS) for s in scenes]+[math.ceil(total*FPS)]
    for i,s in enumerate(scenes):
        img=base/s['image']; frames=bounds[i+1]-bounds[i]
        if not img.is_file() or frames<=0:
            raise ValueError('Missing page or empty scene')
        title=out/f'title_{i+1}.txt'; title.write_text(s['title'],encoding='utf-8')
        clip=out/f'page_{i+1:02}.mp4'; clips.append(clip)
        maxzoom=1.055
        zoom=f"1+0.055*on/{max(frames-1,1)}" if i%2==0 else f"{maxzoom}-0.055*on/{max(frames-1,1)}"
        vf=(f"scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,"
            f"zoompan=z='{zoom}':x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2':d={frames}:s=1280x720:fps={FPS},"
            f"drawbox=x=0:y=600:w=iw:h=120:color=0x191b1c@0.66:t=fill,"
            f"drawbox=x=30:y=28:w=440:h=48:color=0xf8ecd9@0.92:t=fill,"
            f"drawtext=fontfile='{font}':textfile='{title}':fontsize=26:fontcolor=0x263b36:x=48:y=38,format=yuv420p")
        run(['ffmpeg','-y','-v','error','-threads','1','-loop','1','-i',str(img),'-vf',vf,'-frames:v',str(frames),'-an','-c:v','libx264','-preset','fast','-crf','20','-threads','1',str(clip)])
    shutil.copy2(voice,out/'narration.mp3')
    listing=out/'pages.concat.txt'
    listing.write_text(''.join("file '"+str(p)+"'\n" for p in clips))
    run(['ffmpeg','-y','-v','error','-f','concat','-safe','0','-i',str(listing),'-c','copy',str(out/'picture_track.mp4')])
    if 'audio_assets' in spec:
        cues=spec['audio_assets']['events']
        for key,name in [('music','background_music.wav'),('sfx','environment_sfx.wav')]:
            asset=base/spec['audio_assets'][key]
            if not asset.is_file():raise FileNotFoundError(asset)
            run(['ffmpeg','-y','-v','error','-i',str(asset),'-t',str(total),'-ar',str(SR),'-ac','1','-c:a','pcm_s16le',str(out/name)])
    else:
        cues=make_stems(out,total)
    run(['ffmpeg','-y','-v','error','-i',str(voice),'-i',str(out/'background_music.wav'),'-i',str(out/'environment_sfx.wav'),'-filter_complex','[0:a]volume=1.0[v];[1:a]volume=0.10[m];[2:a]volume=0.10[s];[v][m][s]amix=inputs=3:duration=first:normalize=0,loudnorm=I=-13:TP=-1:LRA=7[a]','-map','[a]','-ar',str(SR),'-ac','2','-c:a','pcm_s16le',str(out/'mixed_audio.wav')])
    captions_count=captions(base/spec['subtitles'],out/'captions.ass',total)
    shutil.copy2(base/spec['subtitles'],out/'subtitles.srt')
    result=out/'Weiwei_Jiuzhao_068_v1.mp4'
    run(['ffmpeg','-y','-v','error','-threads','1','-i',str(out/'picture_track.mp4'),'-i',str(out/'mixed_audio.wav'),'-vf',f"ass='{out/'captions.ass'}':fontsdir='{fontdir}'",'-map','0:v:0','-map','1:a:0','-c:v','libx264','-preset','fast','-crf','20','-threads','1','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-t',str(total),'-disposition:a:0','default','-movflags','+faststart',str(result)])
    run(['ffmpeg','-v','error','-xerror','-i',str(result),'-f','null','-'])
    loudness=measure(result)
    if float(loudness['input_i']) < -24 or float(loudness['input_tp']) >= 0:
        raise ValueError('Final mix loudness failed')
    streams=json.loads(run(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(result)]))
    video=next(s for s in streams['streams'] if s['codec_type']=='video')
    audio=next(s for s in streams['streams'] if s['codec_type']=='audio')
    if video['codec_name']!='h264' or audio['codec_name']!='aac' or (video['width'],video['height'])!=(1280,720):
        raise ValueError('Final format contract failed')
    report={'technical_status':'SUCCESS','subjective_listening':'UNCERTAIN','visual_qa':'PENDING','file':result.name,'duration':streams['format']['duration'],'full_decode':'PASS','voice':meta['preset'],'narration_source_sha256':sha(voice),'output_sha256':sha(result),'captions_count':captions_count,'loudness':loudness,'auto_ducking':False,'music_gain':.10,'sfx_gain':.10,'music_source':'original procedural pentatonic composition generated by this script','sfx_source':'original synthesized wind, pulses, paper rustle and chirps','sfx_events':cues,'motion':'camera zoom only; illustrated characters are not independently animated','kb02':'BLOCKED: supplied KB file contains only 12; no claim of full KB compliance','sources':spec['sources']}
    (out/'QA.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))

if __name__=='__main__':
    main()
