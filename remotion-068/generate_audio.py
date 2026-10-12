import asyncio, pathlib, subprocess, sys
import edge_tts
root=pathlib.Path(__file__).resolve().parent
text=(root/'narration.txt').read_text(encoding='utf8').strip()
assert text and len(text)<=300, 'Narration must be 1-300 characters'
target=root/'public/audio/voice.mp3'
target.parent.mkdir(parents=True,exist_ok=True)
async def main():
    await edge_tts.Communicate(text,voice='zh-TW-HsiaoChenNeural',rate='+20%',pitch='+5Hz').save(str(target))
asyncio.run(main())
r=subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','default=noprint_wrappers=1:nokey=1',str(target)],capture_output=True,text=True,check=True)
duration=float(r.stdout.strip())
print('VOICE_DURATION_SECONDS',duration)
if not (5<=duration<=20): sys.exit('FAILED: narration does not fit the 20-second test')
