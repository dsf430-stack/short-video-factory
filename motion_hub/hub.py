#!/usr/bin/env python3
"""Pinned source installation, real source catalog and production brief integration."""
import argparse, json, pathlib, subprocess, sys
ROOT=pathlib.Path(__file__).resolve().parent
CACHE=ROOT/'.sources'
def run(*args): subprocess.run(args,check=True)
def load(name): return json.loads((ROOT/name).read_text())
def bootstrap():
 CACHE.mkdir(exist_ok=True)
 for item in load('sources.lock.json'):
  dest=CACHE/item['id']
  if not dest.exists():
   run('git','init',str(dest)); run('git','-C',str(dest),'remote','add','origin',item['url'])
  current=subprocess.run(['git','-C',str(dest),'rev-parse','HEAD'],capture_output=True,text=True)
  if current.returncode==0 and current.stdout.strip()==item['commit']: continue
  if subprocess.check_output(['git','-C',str(dest),'status','--porcelain'],text=True).strip(): raise ValueError(f'Refuse to overwrite modified source: {dest}')
  run('git','-C',str(dest),'fetch','--depth','1','origin',item['commit'])
  run('git','-C',str(dest),'checkout','--detach',item['commit'])
 print('SUCCESS: all five source commits installed')
def validate():
 ids=set()
 for e in load('catalog.json'):
  if e['id'] in ids: raise ValueError('Duplicate id: '+e['id'])
  ids.add(e['id']); p=CACHE/e['provider']/e['path']
  if not p.is_file(): raise ValueError('Missing real source: '+str(p))
 print(f'SUCCESS: {len(ids)} source entries verified')
def brief(a):
 entry=next((e for e in load('catalog.json') if e['id']==a.style),None)
 if entry is None: raise ValueError('Unknown style. Run list to get an exact source id.')
 if a.duration<=0: raise ValueError('duration must be positive')
 d=pathlib.Path(a.out).resolve(); d.mkdir(parents=True,exist_ok=True)
 if (d/'brief.md').exists(): raise ValueError('Refuse to overwrite existing brief')
 source=CACHE/entry['provider']/entry['path']
 if not source.is_file(): raise ValueError('Run bootstrap before creating a brief')
 audio=pathlib.Path(a.audio).resolve() if a.audio else None
 if audio and not audio.is_file(): raise ValueError('Audio file does not exist')
 config={'topic':a.topic,'duration':a.duration,'size':a.size,'fps':a.fps,'style':entry,'audio':str(audio) if audio else None,'status':'BRIEF_READY','render_status':'NOT_STARTED'}
 (d/'job.json').write_text(json.dumps(config,ensure_ascii=False,indent=2)+'\n')
 refs=[CACHE/'xilo-opus-video/skills/xilo-opus-video/SKILL.md',CACHE/'lemo-opuscar/DIRECTOR.md',CACHE/'lemo-opuscar/TECHNIQUE.md',source,CACHE/'mg-styles-15/rubric.md',CACHE/'huashu-art-motion/references/09-视频动画语法.md']
 text=f'''# 動畫製作設定\n題材：{a.topic}\n片長：{a.duration} 秒；畫幅：{a.size}；fps：{a.fps}\n風格：{entry['name']}\n旁白：{audio or '尚未提供；不得以樣片聲音充當新旁白'}\n\n先讀以下真實來源，依題材編寫場景與時間線。Xilo 統籌、Lemo 導演、所選風格卡定外觀、MG 評分、花叔檢查鏡頭內運動。\n'''+''.join(f'- {p}\n' for p in refs)+'''\n每個畫面須由時間決定；每鏡頭須有可見動作，不能只換投影片。先製作代表靜幀及短片驗證，再渲染。已有使用者確認時直接接續，不重問。\n建立 index.html，公開 window.render(t)、window.seek(t) 或 window.renderFrame(t) 之一。載入素材時以 window.ready=false，完成後設 true。尺寸從視窗讀取；使用本地字體並確認中文字形。不得複製示例故事或未授權的作者角色、聲音。保留素材來源和授權。\n使用 motion_hub/render.py 合成現有旁白，生成技術驗證紀錄；成片另外執行花叔 film_gate.py，並人工觀看抽幀，技術通過不等於藝術品質通過。\n'''
 (d/'brief.md').write_text(text)
 print('SUCCESS: '+str(d/'brief.md'))
def main():
 ap=argparse.ArgumentParser(description=__doc__); sub=ap.add_subparsers(dest='command',required=True)
 sub.add_parser('bootstrap'); sub.add_parser('validate'); ls=sub.add_parser('list'); ls.add_argument('--provider')
 b=sub.add_parser('brief'); b.add_argument('--topic',required=True); b.add_argument('--style',required=True); b.add_argument('--duration',type=float,required=True); b.add_argument('--size',default='1080x1920'); b.add_argument('--fps',type=int,default=30); b.add_argument('--audio'); b.add_argument('--out',required=True)
 a=ap.parse_args()
 if a.command=='bootstrap': bootstrap()
 elif a.command=='validate': validate()
 elif a.command=='brief': brief(a)
 else:
  for e in load('catalog.json'):
   if not a.provider or e['provider']==a.provider: print(e['id']+'\t'+e['name'])
if __name__=='__main__':
 try: main()
 except (ValueError,subprocess.CalledProcessError) as e: sys.exit('FAILED: '+str(e))
