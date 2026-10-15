"""Original minimal electronic score; source narration is never regenerated."""
from pathlib import Path
import json, subprocess, wave
import numpy as np
p=Path(__file__).resolve().parent
sr=48000; dur=30; n=sr*dur
a=np.zeros(n,dtype=np.float64)
subs=json.loads((p/'subtitles.json').read_text())
def tone(start,length,freq,level):
 i=int(start*sr); count=min(int(length*sr),n-i)
 if count<=0:return
 t=np.arange(count)/sr
 # A tuned pluck with fast attack and an exponential release; no third-party samples.
 env=(1-np.exp(-t*300))*np.exp(-t*7/length)
 a[i:i+count]+=level*env*(np.sin(2*np.pi*freq*t)+.18*np.sin(2*np.pi*freq*2*t))
notes=[220,277.1826,329.6276,415.3047]
for j in range(60):
 at=j*.5
 if 8.25<at<8.55 or 17.75<at<18.1:continue
 tone(at,.46,notes[j%4],.023 if j%4 else .035)
 if j%4==0:tone(at,.75,55,.025)
for at in [3.927,8.542,14.458,18.062,21.448,25.635]:
 tone(at,.8,659.255,.045);tone(at+.04,.8,830.609,.025)
# Measured speech boundaries drive an 8dB score reduction, with short fades.
duck=np.ones(n)
for item in subs:
 i=max(0,int((item['start']-.08)*sr));j=min(n,int((item['end']+.15)*sr));duck[i:j]=10**(-8/20)
from scipy.ndimage import gaussian_filter1d
duck=gaussian_filter1d(duck,sigma=sr*.035)
a*=duck
a*=np.minimum(1,np.arange(n)/(sr*.05))*np.minimum(1,(n-np.arange(n))/(sr*.5))
with wave.open(str(p/'score.wav'),'wb') as w:
 w.setnchannels(1);w.setsampwidth(2);w.setframerate(sr);w.writeframes((np.clip(a,-1,1)*32767).astype('<i2').tobytes())
subprocess.run(['ffmpeg','-v','error','-y','-i',str(p/'narration.mp3'),'-i',str(p/'score.wav'),'-filter_complex','[0:a]adelay=1000,apad=whole_dur=30[v];[v][1:a]amix=inputs=2:duration=longest:normalize=0,loudnorm=I=-14:TP=-1:LRA=7[a]','-map','[a]','-t','30','-ar','48000','-c:a','pcm_s16le',str(p/'mix.wav')],check=True)
# Shift SRT by the exact same 1s delay applied to the voice.
def stamp(t):
 ms=round(t*1000);h,ms=divmod(ms,3600000);m,ms=divmod(ms,60000);s,ms=divmod(ms,1000);return f'{h:02}:{m:02}:{s:02},{ms:03}'
(p/'008-rain-v1.srt').write_text(''.join(f"{i}\n{stamp(s['start'])} --> {stamp(s['end'])}\n{s['text']}\n\n" for i,s in enumerate(subs,1)))
print('MIX_READY: voice delayed 1s, score ducked 8dB, complete 30s mix')
