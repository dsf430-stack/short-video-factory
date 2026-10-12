#!/usr/bin/env python3
"""Add timed character speech bubbles and a schematic strategy map to a 068 MP4."""
import argparse, hashlib, json, math, subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from book_media import run,duration
from render_cached_book import measure

W,H,FPS=1280,720,25
DIALOGUES=[
    (8.427,13.177,'田忌','我們快去邯鄲，幫趙國解圍！','right'),
    (13.177,16.490,'孫臏','先等等。','left'),
    (16.490,20.896,'孫臏','魏國的主力都在趙國，它自己的都城，守軍就少了。','left'),
    (20.896,24.896,'田忌','要救趙國，為什麼看著魏國？','right'),
    (24.896,30.719,'孫臏','如果我們進逼魏國的都城大梁，魏軍就得趕回去保護自己的家。','left'),
]
MAP_PHASES=[16.490,20.896,24.896,34.635,39.240,44.385]
CAST_MODE=False

def wrap(text,size=21):
    return '\n'.join(text[i:i+size] for i in range(0,len(text),size))

def arrow(d,a,b,color,progress=1,width=5,dashed=False):
    end=(a[0]+(b[0]-a[0])*progress,a[1]+(b[1]-a[1])*progress)
    if dashed:
        length=math.dist(a,end)
        for start in range(0,int(length),16):
            stop=min(start+9,length)
            if length>0:
                p=(a[0]+(end[0]-a[0])*start/length,a[1]+(end[1]-a[1])*start/length)
                q=(a[0]+(end[0]-a[0])*stop/length,a[1]+(end[1]-a[1])*stop/length)
                d.line([p,q],fill=color,width=width)
    else:d.line([a,end],fill=color,width=width)
    if progress>.08:
        angle=math.atan2(end[1]-a[1],end[0]-a[0]);s=12
        d.polygon([end,(end[0]-s*math.cos(angle-.48),end[1]-s*math.sin(angle-.48)),(end[0]-s*math.cos(angle+.48),end[1]-s*math.sin(angle+.48))],fill=color)

def strategy_map(image,t,fonts):
    title,body,small=fonts
    layer=Image.new('RGBA',(W,H),(0,0,0,0));d=ImageDraw.Draw(layer)
    x,y=748,294
    d.rounded_rectangle((x,y,x+492,y+294),radius=13,fill=(248,239,219,250),outline=(89,79,55,255),width=2)
    d.text((x+18,y+12),'圍魏救趙・策略示意',font=title,fill=(40,59,52,255))
    d.text((x+18,y+44),'位置僅示意，不按比例',font=small,fill=(111,104,86,255))
    zhao=(x+94,y+118);wei=(x+236,y+202);qi=(x+393,y+118)
    red=(166,67,52,255);teal=(35,112,122,255);gold=(170,124,39,255)
    # Topological diagram, not an inferred geographic or historical survey map.
    if t<MAP_PHASES[2]:
        arrow(d,wei,zhao,red,1,width=5)
        d.text((x+115,y+153),'魏軍主力在外',font=small,fill=red)
        caption='魏攻趙，魏都守備較少'
    elif t<MAP_PHASES[3]:
        arrow(d,wei,zhao,red,.8,width=3,dashed=True)
        progress=min(1,max(.08,(t-MAP_PHASES[2])/3.5))
        arrow(d,qi,wei,teal,progress,width=6)
        caption='齊軍進逼大梁，迫使魏軍回援'
    elif t<MAP_PHASES[4]:
        arrow(d,qi,wei,teal,1,width=4)
        progress=min(1,max(.08,(t-MAP_PHASES[3])/3))
        arrow(d,zhao,wei,red,progress,width=6)
        caption='魏軍撤離邯鄲，回救大梁'
    else:
        arrow(d,qi,wei,teal,1,width=4)
        arrow(d,zhao,wei,red,1,width=4)
        encounter=(x+155,y+158)
        d.ellipse((encounter[0]-13,encounter[1]-13,encounter[0]+13,encounter[1]+13),fill=(255,246,210,255),outline=gold,width=3)
        d.text((x+23,y+184),'桂陵迎擊',font=small,fill=gold)
        caption='齊軍在桂陵迎擊，趙國解圍'
    for point,label,color in [(zhao,'趙・邯鄲',red),(wei,'魏・大梁',red),(qi,'齊',teal)]:
        px,py=point
        d.rounded_rectangle((px-13,py-10,px+13,py+10),radius=3,fill=color)
        d.text((px-42,py-39),label,font=body,fill=(42,43,36,255))
    d.text((x+16,y+260),caption,font=small,fill=(38,58,50,255))
    return Image.alpha_composite(image,layer)

def dialogue(image,t,fonts):
    title,body,small=fonts
    for start,end,name,text,side in DIALOGUES:
        if start<=t<end:
            if side=='left':
                x,y,width=36,390,676
                tail=(535,315) if t>=MAP_PHASES[2] else (450,235)
            else:
                x,y,width=736,378,502
                tail=(600,240) if t<DIALOGUES[1][0] else (856,290)
            wrapped=wrap(text,25 if side=='left' else 18)
            height=57+len(wrapped.split('\n'))*31
            if y+height>590:raise ValueError('Dialogue would overlap subtitles')
            layer=Image.new('RGBA',(W,H),(0,0,0,0));d=ImageDraw.Draw(layer)
            d.polygon([(x+90,y+2),(x+128,y+2),tail],fill=(255,251,239,246))
            d.rounded_rectangle((x,y,x+width,y+height),radius=15,fill=(255,251,239,246),outline=(87,95,70,255),width=2)
            d.text((x+19,y+10),name,font=title,fill=(154,72,44,255) if name=='田忌' else (37,108,94,255))
            d.multiline_text((x+19,y+43),wrapped,font=body,fill=(38,44,40,255),spacing=4)
            return Image.alpha_composite(image,layer)
    return image

def main():
    global DIALOGUES,MAP_PHASES,CAST_MODE
    ap=argparse.ArgumentParser();ap.add_argument('source');ap.add_argument('--font',required=True);ap.add_argument('--output',required=True);ap.add_argument('--events');a=ap.parse_args()
    if a.events:
        events=json.loads(Path(a.events).read_text())['segments']
        if len(events)!=14:raise ValueError('Expected the verified fourteen-segment story')
        DIALOGUES=[(s['start'],s['end'],s['role'],s['text'],'left' if s['role']=='孫臏' else 'right') for s in events if s['role']!='旁白']
        MAP_PHASES=[events[5]['start'],events[5]['end'],events[7]['start'],events[9]['start'],events[10]['start'],events[10]['end']]
        CAST_MODE=True
    source=Path(a.source).resolve();out=Path(a.output).resolve();out.parent.mkdir(exist_ok=True,parents=True)
    font=Path(a.font).resolve()
    fonts=[ImageFont.truetype(str(font),24),ImageFont.truetype(str(font),23),ImageFont.truetype(str(font),19)]
    decoder_log=out.with_suffix('.decode.log');encoder_log=out.with_suffix('.encode.log')
    with decoder_log.open('wb') as dl,encoder_log.open('wb') as el:
        dec=subprocess.Popen(['ffmpeg','-v','error','-i',str(source),'-map','0:v:0','-f','rawvideo','-pix_fmt','rgb24','pipe:1'],stdout=subprocess.PIPE,stderr=dl)
        enc=subprocess.Popen(['ffmpeg','-y','-v','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','pipe:0','-i',str(source),'-map','0:v:0','-map','1:a:0','-c:v','libx264','-preset','fast','-crf','18','-threads','2','-pix_fmt','yuv420p','-c:a','copy','-disposition:a:0','default','-movflags','+faststart',str(out)],stdin=subprocess.PIPE,stderr=el)
        frames=0
        try:
            while True:
                raw=dec.stdout.read(W*H*3)
                if not raw:break
                if len(raw)!=W*H*3:raise RuntimeError('Truncated decoded frame')
                t=frames/FPS
                if DIALOGUES[0][0]<=t<MAP_PHASES[-1]:
                    im=Image.frombytes('RGB',(W,H),raw).convert('RGBA')
                    if (MAP_PHASES[0]<=t<MAP_PHASES[1]) or (MAP_PHASES[2]<=t<MAP_PHASES[-1]):im=strategy_map(im,t,fonts)
                    im=dialogue(im,t,fonts)
                    raw=im.convert('RGB').tobytes()
                enc.stdin.write(raw);frames+=1
            enc.stdin.close();dec.stdout.close();dc=dec.wait();ec=enc.wait()
        except BaseException:
            dec.terminate();enc.terminate();dec.wait();enc.wait();raise
    if dc or ec:raise RuntimeError(decoder_log.read_text()+encoder_log.read_text())
    run(['ffmpeg','-v','error','-xerror','-i',str(out),'-f','null','-'])
    levels=measure(out)
    if float(levels['input_i'])<-24 or float(levels['input_tp'])>=0:raise RuntimeError('Audio verification failed')
    # Compare compressed AAC payloads, preserving original narration/BGM/SFX exactly.
    def audiohash(path):
        p=subprocess.run(['ffmpeg','-v','error','-i',str(path),'-map','0:a:0','-c:a','copy','-f','adts','pipe:1'],capture_output=True,check=True)
        return hashlib.sha256(p.stdout).hexdigest()
    if audiohash(source)!=audiohash(out):raise RuntimeError('Original soundtrack changed')
    report={'technical_status':'SUCCESS','visual_qa':'PENDING','subjective_listening':'UNCERTAIN','duration':duration(out),'frames':frames,'dialogues':DIALOGUES,'map':'topological strategy diagram, explicitly not to scale; no precise battlefield geography claimed','audio':'verified three-voice cast soundtrack preserved; no lip sync' if CAST_MODE else 'original 068 AAC bitstream preserved, no new character voices or lip sync','full_decode':'PASS','loudness':levels,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'output_sha256':hashlib.sha256(out.read_bytes()).hexdigest()}
    out.with_suffix('.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False))

if __name__=='__main__':main()
