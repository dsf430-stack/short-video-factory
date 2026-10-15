#!/usr/bin/env python3
"""Render time-driven pages using all three upstream page contracts, over HTTP."""
import argparse, functools, http.server, json, math, pathlib, subprocess, tempfile, threading
from playwright.sync_api import sync_playwright

def probe(p):
 return json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(p)],text=True))
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('page'); ap.add_argument('out'); ap.add_argument('--root'); ap.add_argument('--duration',type=float,required=True); ap.add_argument('--fps',type=int,default=30); ap.add_argument('--size',default='1080x1920'); ap.add_argument('--audio'); ap.add_argument('--still',type=float)
 a=ap.parse_args(); page=pathlib.Path(a.page).resolve(); out=pathlib.Path(a.out).resolve(); root=pathlib.Path(a.root).resolve() if a.root else page.parent
 if not page.is_file() or out.exists(): raise ValueError('Missing page or output already exists')
 rel=page.relative_to(root); w,h=map(int,a.size.split('x'))
 if a.duration<=0 or a.fps<=0 or min(w,h)<=0 or w%2 or h%2: raise ValueError('Invalid duration, fps or even output dimensions')
 audio=pathlib.Path(a.audio).resolve() if a.audio else None
 if audio:
  info=probe(audio)
  if not any(s['codec_type']=='audio' for s in info['streams']): raise ValueError('Audio input has no audio stream')
  if float(info['format']['duration'])+1/a.fps<a.duration: raise ValueError('Audio shorter than requested film; refusing silent tail or truncated film')
 out.parent.mkdir(parents=True,exist_ok=True); errors=[]
 handler=functools.partial(http.server.SimpleHTTPRequestHandler,directory=str(root)); server=http.server.ThreadingHTTPServer(('127.0.0.1',0),handler); threading.Thread(target=server.serve_forever,daemon=True).start()
 try:
  with tempfile.TemporaryDirectory(prefix='motion-hub-') as tmp, sync_playwright() as p:
   browser=p.chromium.launch(headless=True,args=['--enable-unsafe-swiftshader']); pg=browser.new_page(viewport={'width':w,'height':h},device_scale_factor=1)
   pg.on('pageerror',lambda e:errors.append(str(e)))
   pg.on('console',lambda m:errors.append(m.text) if m.type=='error' else None)
   pg.on('response',lambda r:errors.append(f'HTTP {r.status}: {r.url}') if r.status>=400 else None)
   from urllib.parse import quote
   pg.goto(f'http://127.0.0.1:{server.server_port}/{quote(rel.as_posix())}')
   pg.wait_for_function("(typeof window.render==='function'||typeof window.seek==='function'||typeof window.renderFrame==='function') && window.ready!==false && window.READY!==false && window.__ready!==false",timeout=60000)
   pg.evaluate('document.fonts.ready'); draw="async t=>{if(window.prepare) await window.prepare(t); const f=window.render||window.seek||window.renderFrame; await f(t)}"
   # A frame must be identical after seeking elsewhere: catch stateful animation bugs.
   t=min(a.duration/2,1); pg.evaluate(draw,t); first=pg.screenshot(); pg.evaluate(draw,0); pg.evaluate(draw,t)
   if first!=pg.screenshot(): raise ValueError('FAILED: nondeterministic page')
   if a.still is not None:
    pg.evaluate(draw,a.still)
    if errors: raise ValueError('\n'.join(errors))
    pg.screenshot(path=str(out)); return
   video=pathlib.Path(tmp)/'video.mp4'; frames=round(a.duration*a.fps)
   if frames<1: raise ValueError('Film must contain at least one frame')
   cmd=['ffmpeg','-v','error','-y','-f','image2pipe','-framerate',str(a.fps),'-i','-','-c:v','libx264','-pix_fmt','yuv420p','-crf','18','-movflags','+faststart',str(video)]
   ff=subprocess.Popen(cmd,stdin=subprocess.PIPE)
   try:
    for i in range(frames):
     pg.evaluate(draw,i/a.fps); ff.stdin.write(pg.screenshot(type='png'))
    ff.stdin.close()
    if ff.wait()!=0: raise ValueError('ffmpeg failed')
   finally:
    if ff.poll() is None: ff.kill(); ff.wait()
   if errors: raise ValueError('\n'.join(errors))
   final=pathlib.Path(tmp)/'final.mp4'
   if audio: subprocess.run(['ffmpeg','-v','error','-y','-i',str(video),'-i',str(audio),'-map','0:v:0','-map','1:a:0','-t',str(frames/a.fps),'-c:v','copy','-c:a','aac','-movflags','+faststart',str(final)],check=True)
   else: final=video
   data=probe(final); v=next(s for s in data['streams'] if s['codec_type']=='video')
   if v['width']!=w or v['height']!=h or abs(float(data['format']['duration'])-frames/a.fps)>1/a.fps+0.01: raise ValueError('Output size or duration mismatch')
   if audio and not any(s['codec_type']=='audio' for s in data['streams']): raise ValueError('Missing audio stream')
   subprocess.run(['ffmpeg','-v','error','-i',str(final),'-f','null','-'],check=True)
   import shutil
   shutil.copyfile(final,out)
   out.with_suffix('.verification.json').write_text(json.dumps({'status':'SUCCESS','deterministic':True,'frames':frames,'audio':str(audio) if audio else None,'probe':data,'visual_quality':'UNCERTAIN: requires frame review and film_gate'},ensure_ascii=False,indent=2))
   print('SUCCESS: '+str(out)); browser.close()
 finally: server.shutdown(); server.server_close()
if __name__=='__main__': main()
