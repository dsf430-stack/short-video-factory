import importlib.util,pathlib,tempfile,subprocess,sys,json
ROOT=pathlib.Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as td:
 d=pathlib.Path(td)
 for contract in ['render','seek','renderFrame']:
  text=(ROOT/'tests/smoke.html').read_text().replace("||'render'",f"||'{contract}'")
  page=d/(contract+'.html');page.write_text(text)
  subprocess.run([sys.executable,str(ROOT/'render.py'),str(page),str(d/(contract+'.mp4')),'--duration','2','--fps','12','--size','320x568','--audio',str(ROOT.parent/'smart_voice/samples/068.mp3')],check=True)
  assert json.loads((d/(contract+'.verification.json')).read_text())['status']=='SUCCESS'
 print('SUCCESS: all 3 page contracts render with real existing 068 audio')
