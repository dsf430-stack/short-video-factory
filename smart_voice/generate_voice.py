"""Numbered Edge-TTS narration; verified TLS, <=300-character chunks, MP3/SRT QA."""
import argparse
import aiohttp
import asyncio
import hashlib
import json
import math
import os
import re
import shutil
import ssl
import subprocess
import tempfile
import traceback
from pathlib import Path

import certifi
import edge_tts
import edge_tts.communicate
import edge_tts.constants

# Microsoft Read Aloud endpoint migration reported upstream in issue #490.
# Keep the stock client token, DRM, headers and TLS verification unchanged.
edge_tts.communicate.WSS_URL = (
    'wss://api.msedgeservices.com/tts/cognitiveservices/websocket/v1'
    f'?Ocp-Apim-Subscription-Key={edge_tts.constants.TRUSTED_CLIENT_TOKEN}'
)

ROOT = Path(__file__).resolve().parent
VOICES = json.loads((ROOT / 'voices.json').read_text(encoding='utf-8'))['voices']
SERVICE = 'api.msedgeservices.com'
CACHE_VERSION = 1


def retryable(error: Exception) -> bool:
    # Never retry a denied connection or a certificate error as a network blip.
    if isinstance(error, (ssl.SSLError, aiohttp.ClientSSLError)):
        return False
    if isinstance(error, aiohttp.ClientResponseError):
        return error.status in (408, 429, 500, 502, 503, 504)
    return isinstance(error, (asyncio.TimeoutError, ConnectionError,
                              aiohttp.ClientConnectionError, aiohttp.ClientPayloadError))


def atomic_json(path: Path, value: dict) -> None:
    with tempfile.NamedTemporaryFile('w', encoding='utf-8', dir=path.parent,
                                     delete=False, suffix='.tmp') as handle:
        pending = Path(handle.name)
        json.dump(value, handle, ensure_ascii=False, indent=2, allow_nan=False)
    pending.replace(path)


def chunk_key(text: str, preset: dict) -> str:
    config = {'text': text, 'preset': preset, 'service': SERVICE,
              'cache_version': CACHE_VERSION, 'edge_tts': edge_tts.__version__}
    return hashlib.sha256(json.dumps(config, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def inspect_chunk(raw: Path, events: list, text: str) -> float:
    run(['ffmpeg', '-v', 'error', '-i', str(raw), '-f', 'null', '-'])
    duration = float(run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                          '-of', 'default=nw=1:nk=1', str(raw)]).stdout)
    normalize = lambda value: ''.join(c.casefold() for c in value if c.isalnum())
    if not events or normalize(''.join(e[2] for e in events)) != normalize(text):
        raise RuntimeError('Sentence boundaries do not cover the submitted text')
    if not math.isfinite(duration) or duration <= 0 or any(
        not math.isfinite(start) or not math.isfinite(length) or start < 0 or length <= 0
        or start + length > duration + 0.15 for start, length, _ in events
    ):
        raise RuntimeError('Invalid sentence timing')
    if any(events[i][0] < events[i - 1][0] + events[i - 1][1] - 0.015
           for i in range(1, len(events))):
        raise RuntimeError('Overlapping sentence timing')
    return duration


async def get_chunk(text: str, preset: dict, cache: Path, temp: Path,
                    progress: dict, journal: Path) -> tuple[Path, list, float, bool]:
    key = chunk_key(text, preset)
    saved_audio, saved_meta = cache / f'{key}.mp3', cache / f'{key}.json'
    if saved_audio.exists() and saved_meta.exists():
        try:
            record = json.loads(saved_meta.read_text(encoding='utf-8'))
            if record['key'] != key or record['sha256'] != hashlib.sha256(saved_audio.read_bytes()).hexdigest():
                raise ValueError('Cached chunk hash mismatch')
            duration = inspect_chunk(saved_audio, record['events'], text)
            return saved_audio, record['events'], duration, True
        except (ValueError, KeyError, TypeError, RuntimeError) as error:
            progress.setdefault('invalid_cache', []).append({'key': key, 'error': str(error)})
            atomic_json(journal, progress)
            print(f'INVALID_CACHE key={key}; regenerating the same text', flush=True)
    raw = temp / f'{key}.mp3'
    for attempt in range(1, 4):
        events = []
        try:
            stream = edge_tts.Communicate(
                text, preset['voice'], rate=preset['rate'], pitch=preset['pitch'],
                volume=preset['volume'], boundary='SentenceBoundary',
                connect_timeout=15, receive_timeout=30,
            )
            async with asyncio.timeout(120):
                with raw.open('wb') as handle:
                    async for item in stream.stream():
                        if item['type'] == 'audio':
                            handle.write(item['data'])
                        elif item['type'] == 'SentenceBoundary':
                            events.append((item['offset'] / 1e7, item['duration'] / 1e7, item['text']))
            duration = inspect_chunk(raw, events, text)
            break
        except Exception as error:
            # Preserve exact cause while leaving successful earlier chunks intact.
            transient = retryable(error)
            progress.setdefault('attempts', []).append({'key': key, 'attempt': attempt,
                'type': type(error).__name__, 'status_code': getattr(error, 'status', None),
                'retryable': transient})
            atomic_json(journal, progress)
            if not transient or attempt == 3:
                raise
            delay = 2 ** attempt
            print(f'RETRY {attempt}/3 {type(error).__name__}; waiting {delay}s', flush=True)
            await asyncio.sleep(delay)
    raw.replace(saved_audio)
    atomic_json(saved_meta, {'key': key, 'sha256': hashlib.sha256(saved_audio.read_bytes()).hexdigest(),
                             'events': events, 'duration': duration, 'status': 'SUCCESS'})
    return saved_audio, events, duration, False


def select_voice(topic: str, language: str = 'en') -> str:
    if language.lower().startswith('zh'):
        return '068'
    t = topic.lower()
    if any(x in t for x in ('history', 'ancient', 'historical')):
        return 'M02'
    if any(x in t for x in ('science', 'space', 'physics', 'biology')):
        return 'M03'
    if any(x in t for x in ('emotional', 'heartwarming', 'sad')):
        return 'F03'
    if any(x in t for x in ('vocabulary', 'pronunciation', 'english lesson')):
        return 'F05'
    return 'F01'


def split_text(text: str) -> list[str]:
    # Keep every character; prefer sentence punctuation within the 300-char limit.
    chunks = []
    while text:
        end = min(300, len(text))
        if len(text) > 300:
            breaks = list(re.finditer(r'[。！？.!?\n]', text[:300]))
            if breaks:
                end = breaks[-1].end()
        chunks.append(text[:end])
        text = text[end:]
    return chunks


def run(args: list[str]) -> subprocess.CompletedProcess:
    result = subprocess.run(args, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(result.stderr)
    return result


def timestamp(seconds: float) -> str:
    ms = round(seconds * 1000)
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f'{h:02}:{m:02}:{s:02},{ms:03}'


async def synthesize(text: str, output: str, voice_id: str) -> None:
    text = text.strip()
    if not text:
        raise ValueError('Narration text is empty')
    if voice_id not in VOICES:
        raise ValueError(f'Unknown voice id: {voice_id}')
    preset = VOICES[voice_id]
    if re.search(r'[\u3400-\u9fff]', text) and not any(
        lang.startswith('zh') for lang in preset['languages']
    ):
        raise ValueError(f'{voice_id} is English-only; Chinese voices: 068, ZH_HsiaoYu, ZH_Xiaoxiao')
    for tool in ('ffmpeg', 'ffprobe'):
        if not shutil.which(tool):
            raise RuntimeError(f'{tool} is required')
    out = Path(output).resolve()
    if out.suffix.lower() != '.mp3':
        raise ValueError('Output must use .mp3')
    out.parent.mkdir(parents=True, exist_ok=True)
    for path in (out, out.with_suffix('.srt'), out.with_suffix('.json')):
        if path.exists():
            raise FileExistsError(f'Choose a new output filename: {path}')
    # Retain system trust (including managed runtime CA), then add certifi roots.
    context = ssl.create_default_context()
    context.load_verify_locations(certifi.where())
    edge_tts.communicate._SSL_CTX = context
    events = []
    offset = 0.0
    with tempfile.TemporaryDirectory(dir=out.parent, prefix='tts-') as directory:
        temp = Path(directory)
        chunks = split_text(text)
        cache = out.parent / '.068-cache'
        cache.mkdir(exist_ok=True)
        progress = {'status': 'RUNNING', 'text_sha256': hashlib.sha256(text.encode()).hexdigest(),
                    'voice_id': voice_id, 'chunks_total': len(chunks), 'completed': [], 'attempts': []}
        journal = out.with_suffix('.progress.json')
        atomic_json(journal, progress)
        for index, chunk in enumerate(chunks):
            raw, chunk_events, duration, cached = await get_chunk(chunk, preset, cache, temp, progress, journal)
            shutil.copyfile(raw, temp / f'{index}.mp3')
            events.extend((offset + start, min(offset + start + length, offset + duration), sentence)
                          for start, length, sentence in chunk_events)
            offset += duration
            progress['completed'].append({'index': index, 'key': chunk_key(chunk, preset),
                                          'cached': cached, 'duration': duration})
            atomic_json(journal, progress)
            print(f'CHUNK {index + 1}/{len(chunks)} SUCCESS cached={cached}', flush=True)
        concat = temp / 'concat.txt'
        concat.write_text(''.join(f"file '{index}.mp3'\n" for index in range(len(chunks))))
        final = temp / 'final.mp3'
        run(['ffmpeg', '-y', '-v', 'error', '-f', 'concat', '-safe', '0', '-i', str(concat),
             '-af', 'loudnorm=I=-11:TP=-1:LRA=7', '-ar', '44100', '-ac', '1',
             '-c:a', 'libmp3lame', '-b:a', '192k', str(final)])
        run(['ffmpeg', '-v', 'error', '-i', str(final), '-f', 'null', '-'])
        measured = run(['ffmpeg', '-hide_banner', '-i', str(final), '-af',
                        'loudnorm=I=-11:TP=-1:LRA=7:print_format=json', '-f', 'null', '-'])
        stats = json.loads(measured.stderr[measured.stderr.rfind('{'):])
        if (not math.isfinite(float(stats['input_i'])) or not math.isfinite(float(stats['input_tp']))
                or float(stats['input_i']) <= -25 or float(stats['input_tp']) >= 0):
            raise RuntimeError(f'Audio level check failed: {stats}')
        duration = float(run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                              '-of', 'default=nw=1:nk=1', str(final)]).stdout)
        if duration <= 0 or any(end > duration + 0.15 for _, end, _ in events):
            raise RuntimeError('Output duration or subtitle timing check failed')
        srt = temp / 'final.srt'
        srt.write_text(''.join(f'{i}\n{timestamp(start)} --> {timestamp(end)}\n{sentence}\n\n'
                               for i, (start, end, sentence) in enumerate(events, 1)), encoding='utf-8')
        metadata = temp / 'final.json'
        metadata.write_text(json.dumps({
            'status': 'SUCCESS', 'voice_id': voice_id, 'preset': preset,
            'text_sha256': hashlib.sha256(text.encode()).hexdigest(), 'chunks': len(chunks),
            'duration': duration, 'loudness': stats, 'full_decode': 'PASS',
            'service': SERVICE, 'cache_hits': sum(c['cached'] for c in progress['completed']),
            'attempts': progress['attempts'],
            'subjective_listening': 'UNCERTAIN', 'sha256': hashlib.sha256(final.read_bytes()).hexdigest(),
        }, ensure_ascii=False, indent=2), encoding='utf-8')
        # Publish only after synthesis and QA; MP3 acts as completion marker.
        published = []
        try:
            # Exclusive hard links refuse race-time overwrite of any existing artifact.
            for source, target in ((srt, out.with_suffix('.srt')),
                                   (metadata, out.with_suffix('.json')), (final, out)):
                os.link(source, target)
                published.append(target)
        except OSError:
            for target in published:
                target.unlink()
            raise
        progress['status'] = 'SUCCESS'
        atomic_json(journal, progress)
        out.with_suffix('.error.log').unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--text')
    source.add_argument('--text-file')
    parser.add_argument('--output', required=True)
    parser.add_argument('--voice-id', default='auto')
    parser.add_argument('--topic', default='')
    parser.add_argument('--language', default='auto')
    args = parser.parse_args()
    try:
        text = args.text if args.text is not None else Path(args.text_file).read_text(encoding='utf-8-sig')
        language = args.language
        if language == 'auto':
            language = 'zh' if re.search(r'[\u3400-\u9fff]', text) else 'en'
        voice_id = select_voice(args.topic, language) if args.voice_id == 'auto' else args.voice_id
        asyncio.run(synthesize(text, args.output, voice_id))
    except Exception as error:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        status = 'BLOCKED' if getattr(error, 'status', None) in (401, 403) else 'FAILED'
        output.with_suffix('.error.log').write_text(f'{status}: {traceback.format_exc()}', encoding='utf-8')
        journal = output.with_suffix('.progress.json')
        if journal.exists():
            progress = json.loads(journal.read_text(encoding='utf-8'))
            if progress.get('status') == 'RUNNING':
                progress.update(status=status, error_type=type(error).__name__,
                                status_code=getattr(error, 'status', None))
                atomic_json(journal, progress)
        print(f'{status}: {type(error).__name__}: {error}')
        return 1
    print(f'SUCCESS voice_id={voice_id} output={args.output}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

