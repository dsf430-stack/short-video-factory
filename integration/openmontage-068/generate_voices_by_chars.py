"""068 voice: character-based chunks, resumable synthesis, MP3 and timed SRT.

python generate_voices_by_chars.py --text-file narration.txt --output narration.mp3
Requires: edge-tts, certifi, ffmpeg, ffprobe. Original renderer is unchanged.

Verification: character preservation, chunk size limits, timestamp formatting,
CLI and decoding an existing real MP3 passed. New network synthesis NOT RUN:
this workspace lacks edge-tts/certifi. Next: run in the existing TTS environment.
"""
import argparse
import asyncio
import hashlib
import importlib
import json
import math
import re
import shutil
import ssl
import subprocess
from pathlib import Path


def split_text(text, limit):
    if limit < 20:
        raise ValueError('chars-per-chunk must be at least 20')
    text = text.strip()
    if not text:
        raise ValueError('Narration is empty')
    chunks = []
    while len(text) > limit:
        window = text[:limit]
        stops = [m.end() for m in re.finditer(r'[。！？!?；;\n]|[.!](?=\s)', window)]
        soft = [m.end() for m in re.finditer(r'[，,：:\s]', window)]
        choices = [p for p in stops if p >= limit // 2]
        if not choices:
            choices = [p for p in soft if p >= limit // 2]
        cut = choices[-1] if choices else limit
        chunks.append(text[:cut])
        text = text[cut:]
    if text:
        chunks.append(text)
    return chunks


def run(cmd):
    return subprocess.check_output(cmd, stderr=subprocess.STDOUT).decode()


def duration(path):
    value = float(run(['ffprobe', '-v', 'error', '-show_entries',
                       'format=duration', '-of', 'default=nw=1:nk=1', str(path)]))
    if not math.isfinite(value) or value <= 0:
        raise RuntimeError('Invalid audio duration: ' + str(path))
    return value


def validate(path):
    value = duration(path)
    run(['ffmpeg', '-v', 'error', '-i', str(path), '-f', 'null', '-'])
    return value


def atomic_json(path, value):
    temp = path.with_suffix('.tmp.json')
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
    temp.replace(path)


def stamp(seconds):
    ms = round(seconds * 1000)
    hours, ms = divmod(ms, 3600000)
    minutes, ms = divmod(ms, 60000)
    seconds, ms = divmod(ms, 1000)
    return f'{hours:02}:{minutes:02}:{seconds:02},{ms:03}'


async def synthesize(text, mp3, timing, args):
    import certifi
    module = importlib.import_module('edge_tts.communicate')
    constants = importlib.import_module('edge_tts.constants')
    module.WSS_URL = ('wss://api.msedgeservices.com/tts/cognitiveservices/websocket/v1'
                      f'?Ocp-Apim-Subscription-Key={constants.TRUSTED_CLIENT_TOKEN}')
    context = ssl.create_default_context()
    context.load_verify_locations(certifi.where())
    module._SSL_CTX = context
    ca = Path('/usr/local/share/ca-certificates/nebula-dns.crt')
    if ca.exists():
        bundle = mp3.parent / 'edge-combined-certs.pem'
        bundle.write_bytes(Path(certifi.where()).read_bytes() + b'\n' + ca.read_bytes())
        module._SSL_CTX = ssl.create_default_context(cafile=str(bundle))
    temporary = mp3.with_suffix('.tmp.mp3')
    events = []
    stream = module.Communicate(text, args.voice, rate=args.rate, pitch=args.pitch,
                                boundary='SentenceBoundary')
    with temporary.open('wb') as out:
        async for item in stream.stream():
            if item['type'] == 'audio':
                out.write(item['data'])
            elif item['type'] == 'SentenceBoundary':
                events.append({'offset': item['offset'] / 1e7,
                               'duration': item['duration'] / 1e7,
                               'text': item['text']})
    measured = validate(temporary)
    normalize = lambda s: ''.join(c.casefold() for c in s if c.isalnum())
    if not events or normalize(''.join(e['text'] for e in events)) != normalize(text):
        raise RuntimeError('Sentence boundaries do not cover the submitted text')
    if any(e['offset'] < 0 or e['duration'] <= 0 or
           e['offset'] + e['duration'] > measured + 0.15 for e in events):
        raise RuntimeError('Sentence boundary outside measured audio')
    temporary.replace(mp3)
    atomic_json(timing, {'duration': measured, 'sentences': events})


async def main(args):
    for tool in ('ffmpeg', 'ffprobe'):
        if not shutil.which(tool):
            raise RuntimeError(tool + ' is required')
    text = Path(args.text_file).read_text(encoding='utf-8-sig').strip()
    chunks = split_text(text, args.chars_per_chunk)
    if ''.join(chunks) != text:
        raise RuntimeError('Chunking changed the narration')
    output = Path(args.output).resolve()
    if output.suffix.lower() != '.mp3':
        raise ValueError('output must end in .mp3')
    output.parent.mkdir(parents=True, exist_ok=True)
    config = {'text': text, 'voice': args.voice, 'rate': args.rate,
              'pitch': args.pitch, 'chars_per_chunk': args.chars_per_chunk,
              'schema': 1}
    digest = hashlib.sha256(json.dumps(config, ensure_ascii=False,
                                      sort_keys=True).encode()).hexdigest()
    cache = output.parent / (output.stem + '.voice_cache') / digest
    cache.mkdir(parents=True, exist_ok=True)
    checkpoint = cache / 'checkpoint.json'
    state = {'status': 'RUNNING', 'config': config, 'chunks': len(chunks), 'completed': 0}
    atomic_json(checkpoint, state)
    metadata = output.with_suffix('.json')
    if output.exists():
        if not metadata.exists() or json.loads(metadata.read_text(encoding='utf-8')).get('input_hash') != digest:
            raise RuntimeError('Existing output has different or missing metadata; choose another output name')
        validate(output)
        if output.with_suffix('.srt').exists():
            print('SUCCESS: reusing completed output', output)
            state.update(status='SUCCESS', completed=len(chunks))
            atomic_json(checkpoint, state)
            return
    try:
        captions = []
        elapsed = 0.0
        for index, chunk in enumerate(chunks):
            mp3 = cache / f'{index:04}.mp3'
            timing = cache / f'{index:04}.json'
            if not (mp3.exists() and timing.exists()):
                for attempt in range(3):
                    try:
                        await synthesize(chunk, mp3, timing, args)
                        break
                    except Exception as error:
                        state.update(status='FAILED', failed_chunk=index, error=str(error))
                        atomic_json(checkpoint, state)
                        if attempt == 2 or any(s in str(error).lower() for s in
                                               ('blocked by policy', '403', '401', 'captcha')):
                            raise
                        await asyncio.sleep(2 ** attempt)
            validate(mp3)
            data = json.loads(timing.read_text(encoding='utf-8'))
            normalize = lambda s: ''.join(c.casefold() for c in s if c.isalnum())
            if normalize(''.join(e['text'] for e in data['sentences'])) != normalize(chunk):
                raise RuntimeError('Cached timing text differs from submitted chunk')
            pcm = cache / f'{index:04}.wav'
            if not pcm.exists():
                temp = cache / f'{index:04}.tmp.wav'
                run(['ffmpeg', '-y', '-v', 'error', '-i', str(mp3), '-ar', '24000',
                     '-ac', '1', '-c:a', 'pcm_s16le', str(temp)])
                validate(temp)
                temp.replace(pcm)
            measured = duration(pcm)
            for e in data['sentences']:
                captions.append({'start': elapsed + e['offset'],
                                 'end': elapsed + min(e['offset'] + e['duration'], measured),
                                 'text': e['text']})
            elapsed += measured
            state.update(status='RUNNING', completed=index + 1, error=None)
            atomic_json(checkpoint, state)
            print(f'{index + 1}/{len(chunks)} completed', flush=True)
        concat = cache / 'concat.txt'
        concat.write_text(''.join(f"file '{i:04}.wav'\n" for i in range(len(chunks))), encoding='utf-8')
        temp = output.with_suffix('.tmp.mp3')
        run(['ffmpeg', '-y', '-v', 'error', '-f', 'concat', '-safe', '0', '-i',
             str(concat), '-c:a', 'libmp3lame', '-b:a', '192k', str(temp)])
        measured = validate(temp)
        if abs(measured - elapsed) > 0.25:
            raise RuntimeError('Merged audio duration does not match source segments')
        srt = output.with_suffix('.srt')
        srt_temp = output.with_suffix('.tmp.srt')
        srt_temp.write_text('\n\n'.join(
            f"{i + 1}\n{stamp(e['start'])} --> {stamp(e['end'])}\n{e['text']}"
            for i, e in enumerate(captions)) + '\n', encoding='utf-8')
        temp.replace(output)
        srt_temp.replace(srt)
        atomic_json(metadata, {'status': 'SUCCESS', 'input_hash': digest,
                               'voice': args.voice, 'rate': args.rate, 'pitch': args.pitch,
                               'characters': len(text), 'chunks': len(chunks),
                               'duration': measured, 'sentences': captions,
                               'sha256': hashlib.sha256(output.read_bytes()).hexdigest(),
                               'subjective_listening': 'UNCERTAIN'})
        state.update(status='SUCCESS', duration=measured)
        atomic_json(checkpoint, state)
        print('SUCCESS:', output)
    except Exception as error:
        state.update(status='FAILED', error=str(error))
        atomic_json(checkpoint, state)
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--text-file', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--chars-per-chunk', type=int, default=300)
    parser.add_argument('--voice', default='zh-TW-HsiaoChenNeural')
    parser.add_argument('--rate', default='+20%')
    parser.add_argument('--pitch', default='+5Hz')
    asyncio.run(main(parser.parse_args()))
