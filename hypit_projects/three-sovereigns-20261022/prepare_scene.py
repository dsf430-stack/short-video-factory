import base64,json,re,sys
from pathlib import Path
from PIL import Image
from io import BytesIO
ROOT=Path(__file__).resolve().parent
im=Image.open(ROOT/'assets/background-atlas.png').convert('RGB')
buf=BytesIO();im.save(buf,format='JPEG',quality=88,optimize=True)
image='data:image/jpeg;base64,'+base64.b64encode(buf.getvalue()).decode()
source=(ROOT/'scene.js').read_text(encoding='utf-8').replace('export function setupScene','function setupScene',1)
cuts=[0,10,20,30]
if len(sys.argv)>1:
 srt=Path(sys.argv[1]).read_text(encoding='utf-8-sig')
 def sec(s):
  a,b,c=s.replace(',','.').split(':');return int(a)*3600+int(b)*60+float(c)
 rows=[]
 for block in re.split(r'\n\s*\n',srt.strip()):
  l=block.splitlines()
  if len(l)>=3 and ' --> ' in l[1]:rows.append((sec(l[1].split(' --> ')[0]),''.join(l[2:])))
 for anchor,i in [('傳說伏羲',1),('但也有版本',2)]:
  matches=[t for t,s in rows if anchor in s]
  if matches:cuts[i]=matches[0]+.1
 data={'cuts':cuts}
else:data={'cuts':cuts}
html='<div id="backdrop"></div><div class="shade"></div><svg id="stage" viewBox="0 0 540 960"></svg><div id="heading"><div id="kicker"></div><div id="label"></div></div><div id="wipe"></div>'
css=':scope{background:#101d27;overflow:hidden}#backdrop,.shade,#stage,#wipe{position:absolute;inset:0;width:100%;height:100%}#backdrop{background-image:url('+image+');background-size:300% 100%;background-repeat:no-repeat}.shade{background:linear-gradient(180deg,rgba(4,15,29,.6),transparent 29%,transparent 65%,rgba(4,15,29,.8));}#stage{overflow:hidden}#heading{position:absolute;top:8%;left:4%;width:92%;text-align:center;font-family:"Noto Sans CJK TC","Noto Sans CJK JP",sans-serif;color:#fff4d8;text-shadow:0 3px 10px #102332;}#kicker{font-size:26px;letter-spacing:5px;color:#efcf92;margin-bottom:10px}#label{font-size:46px;font-weight:900;letter-spacing:1px;line-height:1.4}#wipe{background:#ffebba;pointer-events:none;opacity:0}'
html='<div id="virtual">'+html+'</div>'
css='#virtual{position:absolute;width:540px;height:960px;transform-origin:top left;}'+css
scene={'html':html,'css':css,'data':data,'setup':source+'\nreturn setupScene(root,data);'}
(ROOT/'scene.json').write_text(json.dumps(scene,ensure_ascii=False),encoding='utf-8')
# Standalone preview uses precisely the same frame evaluator and artwork.
(ROOT/'preview.html').write_text('<!doctype html><meta charset="utf-8"><style>body{margin:0;background:#111}#root{position:relative;width:540px;height:960px;overflow:hidden}'+css.replace(':scope','#root')+'</style><div id="root">'+html+'</div><script>'+source+';const draw=setupScene(document.querySelector("#root"),'+json.dumps(data)+');window.draw=draw;draw(0);</script>',encoding='utf-8')
print(json.dumps({'cuts':cuts,'scene_bytes':(ROOT/'scene.json').stat().st_size}))

