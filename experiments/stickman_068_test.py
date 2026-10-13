#!/usr/bin/env python3
"""Self-contained 30-second stickman motion test; never modifies existing videos."""
import argparse
import asyncio
import json
import math
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw

W,H,FPS,DURATION=540,960,15,30
VOICE="zh-TW-HsiaoChenNeural"
NARRATION=("為什麼有些人總是原地踏步？其實不是你不夠努力，而是每天都在重複相同的方法。"
"想要突破，先把大目標拆成一個小動作。每天前進一點點，就能慢慢跨越眼前的高牆。"
"真正改變人生的，不是某一天突然成功，而是你今天願意踏出的那一步。你準備開始了嗎？")

def run(*args):
    subprocess.run(args,check=True)

def draw_frame(t):
    im=Image.new("RGB",(W,H),"white")
    d=ImageDraw.Draw(im)
    y=610
    d.line((35,y+180,W-35,y+180),fill=(25,25,25),width=7)
    phase=int(t//10)
    p=(t%10)/10
    x=105+330*p
    if phase==0:
        x=90+210*p
        for k in range(3):
            bx=310+60*k
            d.rectangle((bx,690-k*40,bx+33,786),outline=(30,30,30),width=5)
    elif phase==1:
        x=100+320*p
        d.rectangle((345,600,393,789),fill=(235,235,235),outline=(15,15,15),width=6)
        d.line((345,600,393,600),fill=(235,65,54),width=10)
        y-=round(90*math.sin(math.pi*p))
    else:
        x=90+355*p
        for k in range(4):
            yy=770-35*k
            d.line((70+95*k,yy,150+95*k,yy),fill=(30,30,30),width=7)
            if k<3: d.line((150+95*k,yy,150+95*k,yy-35),fill=(30,30,30),width=7)
    head_y=y-68+8*math.sin(t*8)
    limb_swing=22*math.sin(t*10)
    black=(18,18,18)
    d.ellipse((x-29,head_y-29,x+29,head_y+29),fill=black)
    d.line((x,head_y+29,x,y+52),fill=black,width=11)
    d.line((x,y-6,x-35-limb_swing,y+38),fill=black,width=9)
    d.line((x,y-6,x+35+limb_swing,y+35),fill=black,width=9)
    d.line((x,y+52,x-26+limb_swing,y+110),fill=black,width=10)
    d.line((x,y+52,x+27-limb_swing,y+110),fill=black,width=10)
    if phase==0:
        d.ellipse((355,260,445,350),outline=(255,181,25),width=9)
        for a in range(0,360,45):
            cx,cy=400,305
            u=math.radians(a)
            d.line((cx+60*math.cos(u),cy+60*math.sin(u),cx+76*math.cos(u),cy+76*math.sin(u)),fill=(255,181,25),width=6)
    elif phase==1:
        d.arc((60,205,470,500),205,335,fill=(30,145,200),width=12)
    else:
        d.ellipse((355,250,450,345),outline=(255,181,25),width=7)
        d.line((400,330,400,390),fill=(255,181,25),width=10)
    return im

async def synthesize(audio_path):
    import edge_tts
    tts=edge_tts.Communicate(NARRATION,VOICE,rate="+20%",pitch="+5Hz")
    await tts.save(str(audio_path))
    if not audio_path.exists() or audio_path.stat().st_size<1024:
        raise RuntimeError("068 synthesis did not produce a valid audio file")

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",default="stickman_output")
    args=parser.parse_args()
    out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
    audio=out/"narration_068.mp3"
    asyncio.run(synthesize(audio))
    frames=out/"frames";frames.mkdir(exist_ok=True)
    for n in range(FPS*DURATION):
        draw_frame(n/FPS).save(frames/f"frame_{n:04d}.png")
    silent=out/"silent.mp4"
    run("ffmpeg","-hide_banner","-loglevel","error","-y","-framerate",str(FPS),"-i",str(frames/"frame_%04d.png"),"-c:v","libx264","-preset","veryfast","-pix_fmt","yuv420p",str(silent))
    final=out/"stickman_30s_068.mp4"
    run("ffmpeg","-hide_banner","-loglevel","error","-y","-i",str(silent),"-i",str(audio),"-map","0:v:0","-map","1:a:0","-c:v","copy","-c:a","aac","-af","apad","-t",str(DURATION),"-movflags","+faststart",str(final))
    probe=json.loads(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration:stream=codec_type,codec_name","-of","json",str(final)],text=True))
    streams=probe["streams"]
    if not any(s["codec_type"]=="video" for s in streams) or not any(s["codec_type"]=="audio" for s in streams):
        raise RuntimeError("MP4 validation failed: missing audio or video")
    if not 29.9<=float(probe["format"]["duration"])<=30.1:
        raise RuntimeError("MP4 validation failed: duration is not 30 seconds")
    (out/"verification.json").write_text(json.dumps({"status":"SUCCESS","format":probe,"voice":VOICE,"rate":"+20%","pitch":"+5Hz","note":"procedural stickman animation, not Gemini-generated video"},ensure_ascii=False,indent=2),encoding="utf-8")
    print("SUCCESS",final)

if __name__=="__main__":
    main()
