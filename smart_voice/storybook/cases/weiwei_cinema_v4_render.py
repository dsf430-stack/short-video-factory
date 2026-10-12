import sys,json,math,subprocess,hashlib
from pathlib import Path
sys.path.insert(0,str(Path('../voice_test/068_audiobook').resolve()))
from book_media import run
from render_cached_book import captions
import add_dialogue_map as overlay
root=Path('.').resolve(); old=root.parent/'voice_test/068_audiobook/weiwei_cast_v3'
spec=json.loads((old/'manifest.json').read_text()); events=json.loads((old/'narration.json').read_text())['segments']
font=old/'fonts/NotoSansCJKtc-Regular.otf'
clips=[]
bounds=[round(s['start']*25) for s in spec['scenes']]+[1203]
for i,s in enumerate(spec['scenes']):
    n=bounds[i+1]-bounds[i];clip=root/f'shot{i+1}.mp4';clips.append(clip)
    vf=f"scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,zoompan=z='1+0.07*on/{n}':x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2':d={n}:s=1280x720:fps=25,drawbox=x=0:y=606:w=iw:h=114:color=black@0.65:t=fill,format=yuv420p"
    run(['ffmpeg','-y','-v','error','-loop','1','-i',str(root/f'images/{i+1:02}.png'),'-vf',vf,'-frames:v',str(n),'-an','-c:v','libx264','-preset','fast','-crf','19','-threads','2',str(clip)])
listing=root/'concat.txt';listing.write_text(''.join(f"file '{p}'\n" for p in clips))
run(['ffmpeg','-y','-v','error','-f','concat','-safe','0','-i',str(listing),'-c','copy',str(root/'picture.mp4')])
srt=(old/'subtitles.srt').read_text();blocks=srt.strip().split('\n\n')
for i,b in enumerate(blocks):
    lines=b.splitlines()
    if events[i]['role']!='旁白':lines[2]=events[i]['role']+'：'+lines[2]
    blocks[i]='\n'.join(lines)
(root/'subtitles.srt').write_text('\n\n'.join(blocks)+'\n')
captions(root/'subtitles.srt',root/'captions.ass',48.12)
source=old/'output/Weiwei_Jiuzhao_Cast_Dialogue_Map_v3.mp4'
run(['ffmpeg','-y','-v','error','-i',str(root/'picture.mp4'),'-i',str(source),'-vf',f"ass='{root/'captions.ass'}':fontsdir='{font.parent}'",'-map','0:v:0','-map','1:a:0','-c:v','libx264','-preset','fast','-crf','19','-threads','2','-c:a','copy','-movflags','+faststart',str(root/'captioned.mp4')])
# Keep cinematic compositions clear; speaker names are already in captions.
overlay.dialogue=lambda image,t,fonts:image
sys.argv=['add_dialogue_map',str(root/'captioned.mp4'),'--font',str(font),'--output',str(root/'Weiwei_Jiuzhao_Cinematic_v4.mp4'),'--events',str(old/'narration.json')]
overlay.main()
