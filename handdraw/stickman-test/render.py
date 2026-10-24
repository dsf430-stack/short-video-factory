"""Silent test adapter: unchanged official draw-v2 assets; no narration pipeline."""
import argparse, hashlib, json, subprocess, sys
from pathlib import Path
from PIL import Image

PIN = '3ae9b78d22af907afe70c1af4b8dc677f883bae1'
p = argparse.ArgumentParser()
p.add_argument('--official', required=True)
p.add_argument('--output', default='handdraw/stickman-test/output')
a = p.parse_args()
engine = Path(a.official).resolve()
actual = subprocess.check_output(['git','-C',str(engine),'rev-parse','HEAD'],text=True).strip()
if actual != PIN:
    raise ValueError('Official commit mismatch: '+actual)
sys.path.insert(0,str(engine/'skills/sweety-handdraw-video/scripts'))
from stroke_assets import configure_assets, build_illustration
import illustration_layers
out = Path(a.output).resolve(); out.mkdir(parents=True,exist_ok=True)
source = Path(__file__).with_name('source.png')
# Source is a code-native stick figure; regions match the authored geometry.
parts=[
 {'id':'head','polygon':[[.35,.08],[.65,.08],[.65,.253],[.35,.253]]},
 {'id':'torso','polygon':[[.47,.25],[.53,.25],[.53,.60],[.47,.60]]},
 {'id':'left_arm','polygon':[[.23,.31],[.50,.31],[.50,.48],[.23,.48]]},
 {'id':'right_arm','polygon':[[.5,.12],[.81,.12],[.81,.35],[.5,.35]]},
 {'id':'left_leg','polygon':[[.28,.58],[.51,.58],[.51,.87],[.28,.87]]},
 {'id':'right_leg','polygon':[[.49,.58],[.72,.58],[.72,.87],[.49,.87]]}]
configure_assets(out/'assets','',fps=30)
print('OFFICIAL_COMMIT',actual,flush=True)
print('SOURCE_SHA256',hashlib.sha256(source.read_bytes()).hexdigest(),flush=True)
print('SOURCE: newly authored code-native stick figure',flush=True)
meta=build_illustration('stickman',source,960,1560,parts=parts,seconds=14,drawing={'mode':'draw'})
summary={k:meta[k] for k in ['engine','width','height','seconds','drawability','time_compression','parts']}
(out/'engine-report.json').write_text(json.dumps(summary,indent=2))
print(json.dumps(summary,indent=2),flush=True)
if meta['drawability']['minimum_seconds']>14 or meta['time_compression']>1.001:
    raise ValueError('DRAWING_WINDOW_TOO_SHORT: stick figure requires minimum '+str(meta['drawability']['minimum_seconds'])+' seconds; 15-second film allows 14 seconds drawing and 1 second final hold. Refusing accelerated or omitted strokes.')
layers=illustration_layers.load(out/'assets','stickman')
film=out/'stickman-15s.mp4'
cmd=['ffmpeg','-y','-v','error','-f','rawvideo','-pix_fmt','rgb24','-s','1080x1920','-r','30','-i','-','-an','-c:v','libx264','-pix_fmt','yuv420p','-preset','fast','-crf','18',str(film)]
proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
for i in range(450):
    frame=Image.new('RGB',(1080,1920),'white')
    progress=min(1,max(0,(i/30-.1)/13.9))
    drawn=Image.fromarray(illustration_layers.compose(layers,progress))
    frame.paste(drawn,((1080-drawn.width)//2,(1920-drawn.height)//2),drawn)
    proc.stdin.write(frame.tobytes())
proc.stdin.close()
if proc.wait(): raise RuntimeError('FFmpeg encode failed')
subprocess.run(['ffmpeg','-v','error','-i',str(film),'-f','null','-'],check=True)
probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(film)]))
v=probe['streams'][0]
assert len(probe['streams'])==1 and v['codec_name']=='h264' and (v['width'],v['height'])==(1080,1920)
assert abs(float(probe['format']['duration'])-15)<.01
print('ENCODE_AND_DECODE_PASS; visual motion review still required',flush=True)
