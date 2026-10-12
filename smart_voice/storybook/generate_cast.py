"""Generate only new male dialogue, reuse validated original 068 narrator ranges."""
import argparse,asyncio,hashlib,json,re,subprocess,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import generate_voice as voice
import edge_tts

def run(args):
    p=subprocess.run(args,capture_output=True,text=True)
    if p.returncode:raise RuntimeError(p.stderr)
    return p.stdout

def duration(path):return float(run(['ffprobe','-v','error','-show_entries','format=duration','-of','default=nw=1:nk=1',str(path)]))
def stamp(t):
    n=round(t*1000);h,n=divmod(n,3600000);m,n=divmod(n,60000);s,n=divmod(n,1000)
    return f'{h:02}:{m:02}:{s:02},{n:03}'

async def main(a):
    spec=json.loads(Path(a.script).read_text());out=Path(a.output).resolve();out.mkdir(parents=True,exist_ok=True)
    source=Path(a.narrator).resolve()
    if hashlib.sha256(source.read_bytes()).hexdigest()!=spec['narrator_sha256']:raise RuntimeError('Original narrator fingerprint mismatch')
    inventory={v['ShortName'] for v in await edge_tts.list_voices()}
    for code in ['068','ZH_Yunxi','ZH_Yunjian']:
        if voice.VOICES[code]['voice'] not in inventory:raise RuntimeError('Missing requested voice: '+code)
    print('Verified voice inventory: 068, ZH_Yunxi, ZH_Yunjian')
    clock=0;wav_files=[];events=[];srt=[]
    for i,item in enumerate(spec['segments'],1):
        wav=out/f'segment_{i:02}.wav'
        role=item['role'];code=spec['roles'][role]
        if role=='旁白':
            start,end=item['source_range'];length=end-start
            run(['ffmpeg','-y','-v','error','-ss',str(start),'-i',str(source),'-t',str(length),'-af',f'afade=t=in:d=0.004,afade=t=out:st={max(0,length-.004)}:d=0.004','-ar','44100','-ac','1','-c:a','pcm_s16le',str(wav)])
            provenance='original verified 068 narrator excerpt'
        else:
            mp3=out/f'segment_{i:02}.mp3'
            await voice.synthesize(item['text'],str(mp3),code)
            run(['ffmpeg','-y','-v','error','-i',str(mp3),'-ar','44100','-ac','1','-c:a','pcm_s16le',str(wav)])
            provenance='new male dialogue synthesized using verified migrated endpoint'
        d=duration(wav)
        if d<=0:raise RuntimeError('Empty audio segment')
        run(['ffmpeg','-v','error','-xerror','-i',str(wav),'-f','null','-'])
        events.append({'index':i,'role':role,'voice_code':code,'voice':voice.VOICES[code]['voice'],'text':item['text'],'start':clock,'end':clock+d,'duration':d,'scene':item['scene'],'source':provenance})
        srt.append(f'{i}\n{stamp(clock)} --> {stamp(clock+d)}\n{item["text"]}\n')
        clock+=d;wav_files.append(wav)
        print(f'SUCCESS segment {i} {role} {d:.3f}s',flush=True)
    listing=out/'cast.concat.txt';listing.write_text(''.join(f"file '{p}'\n" for p in wav_files))
    joined=out/'cast_narration.mp3'
    run(['ffmpeg','-y','-v','error','-f','concat','-safe','0','-i',str(listing),'-af','loudnorm=I=-13:TP=-1:LRA=7','-ar','44100','-ac','1','-c:a','libmp3lame','-b:a','192k',str(joined)])
    run(['ffmpeg','-v','error','-xerror','-i',str(joined),'-f','null','-'])
    (out/'cast_subtitles.srt').write_text('\n'.join(srt),encoding='utf-8')
    stats=subprocess.run(['ffmpeg','-hide_banner','-i',str(joined),'-af','loudnorm=I=-13:TP=-1:LRA=7:print_format=json','-f','null','-'],capture_output=True,text=True,check=True)
    levels=json.loads(stats.stderr[stats.stderr.rfind('{'):])
    if float(levels['input_i'])<-24 or float(levels['input_tp'])>=0:raise RuntimeError('Cast loudness failed')
    metadata={'status':'SUCCESS','preset':{'narrator':voice.VOICES['068']['voice'],'田忌':voice.VOICES['ZH_Yunjian']['voice'],'孫臏':voice.VOICES['ZH_Yunxi']['voice'],'rate':'+20%','pitch':'+5Hz'},'duration':duration(joined),'sha256':hashlib.sha256(joined.read_bytes()).hexdigest(),'narrator_source_sha256':spec['narrator_sha256'],'segments':events,'full_decode':'PASS','loudness':levels,'subjective_listening':'UNCERTAIN'}
    (out/'cast_narration.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2));print('SUCCESS cast narration',metadata['duration'])

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--script',required=True);p.add_argument('--narrator',required=True);p.add_argument('--output',required=True);a=p.parse_args()
    try:asyncio.run(main(a))
    except Exception as e:
        out=Path(a.output);out.mkdir(parents=True,exist_ok=True);(out/'cast.error.log').write_text(repr(e));raise
