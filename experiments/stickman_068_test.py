#!/usr/bin/env python3
"""Self-contained 30-second stickman motion test; never modifies existing videos."""
import argparse
import json
import math
import subprocess
from pathlib import Path
import hashlib
import sys
from PIL import Image, ImageDraw

W,H,FPS,DURATION=540,960,15,30
VOICE="zh-TW-HsiaoChenNeural"
NARRATION=("為什麼努力卻總是原地踏步？因為一直重複舊方法。"
"把大目標拆成小行動，每天向前一步，慢慢就能跨過高牆。"
"改變不是突然成功，而是今天開始。你願意試試嗎？")

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

def synthesize(audio_path):
    """Use the existing, verified 068 engine. Do not replace its WebSocket or cache."""
    script=Path(__file__).resolve().parents[1]/"smart_voice"/"generate_voice.py"
    if not script.is_file():
        raise FileNotFoundError(f"Official 068 entry missing: {script}")
    narration=audio_path.parent/"narration.txt"
    narration.write_text(NARRATION,encoding="utf-8")
    run(sys.executable,str(script),"--voice-id","068","--text-file",str(narration),"--output",str(audio_path))
    for suffix in (".mp3",".srt",".json"):
        path=audio_path.with_suffix(suffix)
        if not path.is_file() or path.stat().st_size==0:
            raise RuntimeError(f"Missing official 068 artifact: {path}")
    record=json.loads(audio_path.with_suffix(".json").read_text(encoding="utf-8"))
    if record.get("status")!="SUCCESS" or record.get("voice_id")!="068":
        raise RuntimeError("Official 068 QA did not succeed")
    if hashlib.sha256(audio_path.read_bytes()).hexdigest()!=record.get("sha256"):
        raise RuntimeError("Official 068 SHA mismatch")
    if record.get("text_sha256")!=hashlib.sha256(NARRATION.strip().encode()).hexdigest():
        raise RuntimeError("Official 068 narration mismatch")
    return float(record["duration"])

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",default="stickman_output")
    args=parser.parse_args()
    out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
    audio=out/"narration_068.mp3"
    voice_duration=synthesize(audio)
    if voice_duration > DURATION + 0.1:
        raise RuntimeError(f"068 narration {voice_duration:.2f}s exceeds {DURATION}s: refusing to truncate speech")
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
    (out/"verification.json").write_text(json.dumps({"status":"SUCCESS","format":probe,"voice":VOICE,"rate":"+20%","pitch":"+5Hz","narration_seconds":voice_duration,"narration_sha256":hashlib.sha256(audio.read_bytes()).hexdigest(),"srt":"narration_068.srt","note":"official smart_voice 068 engine; procedural stickman animation, not Gemini-generated video"},ensure_ascii=False,indent=2),encoding="utf-8")
    print("SUCCESS",final)

if __name__=="__main__":
    main()
