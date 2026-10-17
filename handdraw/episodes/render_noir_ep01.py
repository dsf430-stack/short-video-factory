#!/usr/bin/env python3
"""Generate a 60s black-and-white suspense storyboard MP4, without pretending to animate actors."""
import argparse, pathlib, subprocess, sys
from PIL import Image, ImageDraw, ImageFont

SCENES=[
("凌晨 3:17","凌晨三點十七分，便利商店來了一位奇怪的客人。",6),
("門鈴響了","自動門開了。她站在門口，沒有腳步聲。",7),
("你看得到我嗎？","她問店員，你看得到我嗎？",9),
("她就在眼前","店員回答，妳不是就在我面前？",9),
("監視器","女子沒有回答，只指向頭頂的監視器。",9),
("空無一人","螢幕裡，櫃台前竟然沒有任何人。",11),
("不要回頭","就在這時，螢幕跳出四個字，不要回頭。",9)]
assert sum(s[2] for s in SCENES)==60

def run(args): subprocess.run(args,check=True)
def font(size):
    for p in ['/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc','/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc']:
        if pathlib.Path(p).exists(): return ImageFont.truetype(p,size)
    raise RuntimeError('Install fonts-noto-cjk')

def frame(i,title,path):
    im=Image.new('RGB',(1080,1920),'white');d=ImageDraw.Draw(im)
    # Hand-drawn-style monochrome storyboard line art: actual actor motion is NOT claimed.
    d.rectangle((65,270,1015,1490),outline='black',width=9)
    d.line((65,600,1015,600),fill='black',width=7)
    d.rectangle((145,790,930,1150),outline='black',width=8)
    d.rectangle((175,820,370,1090),outline='black',width=5)
    if i in (1,2,3,4):
        d.ellipse((675,640,795,760),outline='black',width=9)
        d.line((735,760,735,1020),fill='black',width=11)
        d.line((735,810,650,930),fill='black',width=9)
        d.line((735,810,830,920),fill='black',width=9)
    if i in (4,5,6):
        d.rectangle((380,340,720,570),outline='black',width=12)
        d.text((410,420),'03:17',font=font(60),fill='black')
    d.text((100,90),f'EP01   {i+1:02d}/07',font=font(58),fill='black')
    d.text((110,1540),title,font=font(88),fill='black')
    d.text((110,1690),'凌晨 3:17',font=font(58),fill='black')
    im.save(path)

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',default='noir-ep01.mp4');p.add_argument('--work',default='noir-work');a=p.parse_args()
    w=pathlib.Path(a.work);w.mkdir(parents=True,exist_ok=True)
    segments=[]
    for i,(title,spoken,duration) in enumerate(SCENES):
        img=w/f'scene{i}.png';vid=w/f'scene{i}.mp4';frame(i,title,img)
        run(['ffmpeg','-y','-loglevel','error','-loop','1','-framerate','30','-i',str(img),'-t',str(duration),'-vf','format=yuv420p','-r','30','-c:v','libx264','-preset','ultrafast',str(vid)])
        segments.append(vid)
    concat=w/'concat.txt';concat.write_text(''.join("file '"+str(f.resolve())+"'\n" for f in segments))
    # No synthetic fake narration: use existing voice 068 if available; otherwise fail clearly.
    text=w/'narration.txt';text.write_text(''.join(s[1] for s in SCENES))
    audio=w/'voice.mp3'
    run([sys.executable,'smart_voice/generate_voice.py','--voice-id','068','--text-file',str(text),'--output',str(audio)])
    run(['ffmpeg','-y','-loglevel','error','-f','concat','-safe','0','-i',str(concat),'-i',str(audio),'-filter_complex','[1:a]apad[a]','-map','0:v','-map','[a]','-t','60','-c:v','copy','-c:a','aac','-b:a','160k',a.output])
    result=subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','default=noprint_wrappers=1:nokey=1',a.output],text=True)
    if abs(float(result)-60)>.2:raise RuntimeError('duration mismatch '+result)
    print('RENDERED',a.output)
if __name__=='__main__':main()
