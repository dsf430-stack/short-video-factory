import json, subprocess, pathlib, hashlib, math
R=pathlib.Path("hf-results")
def run(args):
    p=subprocess.run(args,capture_output=True,text=True)
    (R/"verification.log").open("a").write(str(args)+"\n"+p.stdout+p.stderr+"\n")
    if p.returncode: raise RuntimeError(p.stderr)
    return p
def probe(p):
    return json.loads(run(["ffprobe","-v","error","-count_frames","-show_streams","-show_format","-of","json",str(p)]).stdout)
audio=probe(R/"narration.mp3")
duration=float(audio["format"]["duration"])
if duration>20: raise RuntimeError(f"Narration {duration}s exceeds 20s; revise script without truncation")
srt=(R/"narration.srt").read_text()
if "-->" not in srt: raise RuntimeError("Missing true speech timing subtitles")
run(["ffmpeg","-y","-i",str(R/"picture.mp4"),"-i",str(R/"narration.mp3"),"-vf","subtitles=hf-results/narration.srt:force_style='FontName=Noto Sans CJK TC,FontSize=18,MarginV=45'","-af","apad","-t","20","-c:v","libx264","-pix_fmt","yuv420p","-c:a","aac","-b:a","192k","-movflags","+faststart",str(R/"hyperframes-068-20s.mp4")])
p=R/"hyperframes-068-20s.mp4"
data=probe(p);(R/"ffprobe.json").write_text(json.dumps(data,indent=2))
v=next(x for x in data["streams"] if x["codec_type"]=="video")
a=next(x for x in data["streams"] if x["codec_type"]=="audio")
assert v["codec_name"]=="h264" and a["codec_name"]=="aac"
assert v["width"]*16==v["height"]*9
assert int(v["nb_read_frames"])==600
assert abs(float(data["format"]["duration"])-20)<0.1
run(["ffmpeg","-v","error","-i",str(p),"-f","null","-"])
m=run(["ffmpeg","-hide_banner","-i",str(p),"-af","loudnorm=print_format=json","-f","null","-"])
stats=json.loads(m.stderr[m.stderr.rfind("{"):])
assert math.isfinite(float(stats["input_i"])) and float(stats["input_i"])>-35
for sec in [1,6,11,16]:
    run(["ffmpeg","-y","-v","error","-ss",str(sec),"-i",str(p),"-frames:v","1",str(R/f"frame-{sec}.png")])
raw=subprocess.run(["ffmpeg","-v","error","-i",str(p),"-vf","fps=2,scale=64:114","-f","rawvideo","-pix_fmt","gray","-"],capture_output=True,check=True).stdout
frames=[raw[i:i+7296] for i in range(0,len(raw),7296)]
assert len(set(hashlib.sha256(x).hexdigest() for x in frames))>12,"Insufficient actual motion"
(R/"checkpoint.txt").write_text("SUCCESS: real 20s 9:16 H264/AAC MP4; 600 decoded frames; motion and non-silent audio verified.\nVoice source: existing corrected smart_voice/generate_voice.py; requested legacy generate_voices_by_chars.py absent from main.\nSubjective listening and visual review: UNCERTAIN pending artifact inspection.\n")
(R/"qa.json").write_text(json.dumps({"status":"SUCCESS","audio":stats,"sha256":hashlib.sha256(p.read_bytes()).hexdigest(),"voice_source":"smart_voice/generate_voice.py","motion_unique_frames":len(set(hashlib.sha256(x).hexdigest() for x in frames))},indent=2))
