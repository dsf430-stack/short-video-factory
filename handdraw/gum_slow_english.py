"""Task-scoped 068 adapter: true slow English prosody, real boundary timestamps.
Reuses the established generator, cache, normalization, and verified TLS.
Each English teaching phrase is an intentionally separate utterance; Chinese
runs retain the existing +20% rate. No resampling or guessed word timings.
"""
import re,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'smart_voice'))
import generate_voice as engine
original_get=engine.get_chunk
original_split=engine.split_text
ENGLISH=re.compile(r'(Chewing gum\.|Aluminum foil\.)')
def split_teaching(text):
    result=[]
    for part in ENGLISH.split(text):
        if part.strip(): result.extend(original_split(part))
    return result
async def get_teaching(text,preset,*args,**kwargs):
    actual=dict(preset)
    if ENGLISH.fullmatch(text.strip()): actual['rate']='-25%'
    return await original_get(text,actual,*args,**kwargs)
engine.split_text=split_teaching
engine.get_chunk=get_teaching
engine.VOICES['068']=dict(engine.VOICES['068'],english_rate='-25%',english_phrases=['Chewing gum.','Aluminum foil.'],assembly='intentional teaching-phrase boundaries; original measured sentence events')
if __name__=='__main__':raise SystemExit(engine.main())
