#!/usr/bin/env python3
"""068 picture-book page turns; reuse validated narration, captions and audio mix."""
import argparse, hashlib, json, math, subprocess
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageEnhance
import render_cached_book as cached

W,H,FPS=1280,720,25
TURN=.64

def coefficients(dest,source):
    rows=[]; values=[]
    for (x,y),(u,v) in zip(dest,source):
        rows.extend([[x,y,1,0,0,0,-u*x,-u*y],[0,0,0,x,y,1,-v*x,-v*y]])
        values.extend([u,v])
    return np.linalg.solve(np.array(rows,dtype=float),np.array(values,dtype=float))

def page_turn(old,new,progress):
    s=progress*progress*(3-2*progress)
    angle=s*math.pi/2
    edge=max(2,(W-1)*math.cos(angle)); inset=H*.065*math.sin(angle)
    corners=[(0,0),(edge,inset),(edge,H-1-inset),(0,H-1)]
    coeff=coefficients(corners,[(0,0),(W-1,0),(W-1,H-1),(0,H-1)])
    sheet=old.transform((W,H),Image.Transform.PERSPECTIVE,coeff,Image.Resampling.BICUBIC,fillcolor=(0,0,0,0))
    alpha=sheet.getchannel('A')
    shade=ImageEnhance.Brightness(sheet.convert('RGB')).enhance(1-.22*math.sin(angle)).convert('RGBA')
    shade.putalpha(alpha)
    canvas=new.copy()
    if .01<progress<.99:
        overlay=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(overlay)
        for k in range(22,0,-1):
            a=round(65*math.sin(angle)*(1-k/23))
            x=round(edge)+k
            d.line([(x,round(inset)),(x,round(H-inset))],fill=(25,20,15,a),width=2)
        canvas=Image.alpha_composite(canvas,overlay)
    return Image.alpha_composite(canvas,shade).convert('RGB')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('manifest');args=ap.parse_args()
    manifest=Path(args.manifest).resolve();base=manifest.parent
    spec=json.loads(manifest.read_text(encoding='utf-8'));out=base/'output'
    prior=json.loads((out/'QA.json').read_text(encoding='utf-8'))
    if prior['technical_status']!='SUCCESS':
        raise RuntimeError('The validated 068 mix must exist before page-turn rendering')
    voice=base/spec['narration'];total=cached.duration(voice)
    if cached.sha(voice)!=prior['narration_source_sha256']:
        raise RuntimeError('Narration changed; refuse to reuse mix')
    mix=out/'mixed_audio.wav'
    if abs(cached.duration(mix)-total)>.1:
        raise RuntimeError('Existing mix duration mismatch')
    font=base/spec['font'];header=ImageFont.truetype(str(font),26);small=ImageFont.truetype(str(font),21)
    cards=[]
    for i,scene in enumerate(spec['scenes']):
        with Image.open(base/scene['image']) as im:
            im.verify()
        with Image.open(base/scene['image']) as im:
            card=ImageOps.fit(im.convert('RGB'),(W,H),method=Image.Resampling.LANCZOS).convert('RGBA')
        draw=ImageDraw.Draw(card)
        draw.rounded_rectangle((30,28,470,76),radius=8,fill=(248,236,217,242))
        draw.text((48,35),scene['title'],font=header,fill=(38,59,54,255))
        draw.rounded_rectangle((1040,28,1250,70),radius=8,fill=(248,236,217,242))
        draw.text((1055,35),f'圍魏救趙  {i+1} / 6',font=small,fill=(38,59,54,255))
        cards.append(card)
    frames=math.ceil(total*FPS);video=out/'flipbook_picture_track.mp4'
    cmd=['ffmpeg','-y','-v','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','pipe:0','-an','-c:v','libx264','-preset','fast','-crf','20','-pix_fmt','yuv420p','-threads','2',str(video)]
    log=out/'flipbook_encode.log'
    with log.open('wb') as stderr:
        process=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=stderr)
        try:
            idx=0
            for frame in range(frames):
                t=frame/FPS
                while idx<len(cards)-1 and t>=spec['scenes'][idx]['end']:
                    idx+=1
                boundary=spec['scenes'][idx]['end']
                if idx<len(cards)-1 and boundary-TURN<=t<boundary:
                    image=page_turn(cards[idx],cards[idx+1],(t-boundary+TURN)/TURN)
                else:
                    image=cards[idx].convert('RGB')
                process.stdin.write(image.tobytes())
            process.stdin.close();code=process.wait()
        except BaseException:
            process.stdin.close();process.terminate();process.wait();raise
    if code:
        raise RuntimeError(log.read_text(errors='replace'))
    n=math.ceil(total*cached.SR);paper=np.zeros(n);rng=np.random.default_rng(681013)
    turns=[]
    for scene in spec['scenes'][:-1]:
        start=scene['end']-TURN;t=np.arange(round(TURN*cached.SR))/cached.SR
        noise=rng.normal(0,1,len(t));noise=np.convolve(noise,np.ones(7)/7,mode='same')
        cached.add(paper,.075*noise*np.sin(np.pi*t/TURN)**2,start)
        turns.append({'start':start,'end':scene['end'],'type':'projected page rotation with synthesized paper rustle'})
    cached.write_wav(out/'page_turn_sfx.wav',paper)
    mixed=out/'mixed_flipbook.wav'
    cached.run(['ffmpeg','-y','-v','error','-i',str(mix),'-i',str(out/'page_turn_sfx.wav'),'-filter_complex','[1:a]volume=0.12[p];[0:a][p]amix=inputs=2:duration=first:normalize=0[a]','-map','[a]','-ar','44100','-ac','2','-c:a','pcm_s16le',str(mixed)])
    result=out/'Weiwei_Jiuzhao_068_flipbook_v1.mp4'
    vf=f"drawbox=x=0:y=600:w=iw:h=120:color=0x191b1c@0.66:t=fill,ass='{out/'captions.ass'}':fontsdir='{font.parent}'"
    cached.run(['ffmpeg','-y','-v','error','-i',str(video),'-i',str(mixed),'-vf',vf,'-map','0:v:0','-map','1:a:0','-c:v','libx264','-preset','fast','-crf','20','-threads','2','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-t',str(total),'-disposition:a:0','default','-movflags','+faststart',str(result)])
    cached.run(['ffmpeg','-v','error','-xerror','-i',str(result),'-f','null','-'])
    loudness=cached.measure(result)
    if float(loudness['input_i']) < -24 or float(loudness['input_tp'])>=0:
        raise RuntimeError('Page-turn mix loudness failed')
    audiobook=out/'Weiwei_Jiuzhao_068_audiobook.mp3'
    cached.run(['ffmpeg','-y','-v','error','-i',str(mixed),'-c:a','libmp3lame','-b:a','192k',str(audiobook)])
    cached.run(['ffmpeg','-v','error','-xerror','-i',str(audiobook),'-f','null','-'])
    report=dict(prior)
    report.update(file=result.name,output_sha256=cached.sha(result),duration=cached.duration(result),motion='stationary illustrated pages with perspective page-turn transitions; no independent character motion',page_turns=turns,loudness=loudness,visual_qa='PENDING',audiobook_file=audiobook.name,audiobook_sha256=cached.sha(audiobook))
    (out/'QA_flipbook.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))

if __name__=='__main__':
    main()
