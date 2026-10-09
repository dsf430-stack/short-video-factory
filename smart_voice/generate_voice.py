"""Numbered Edge-TTS narration; verified TLS, <=300-character chunks, MP3/SRT QA."""
import argparse
import asyncio
import hashlib
import json
import re
import shutil
import ssl
import subprocess
import tempfile
from pathlib import Path

import certifi
import edge_tts
import edge_tts.communicate

ROOT = Path(__file__).resolve().parent
VOICES = json.loads((ROOT / 'voices.json').read_text(encoding='utf-8'))['voices']


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
        for index, chunk in enumerate(chunks):
            raw = temp / f'{index}.mp3'
            chunk_events = []
            stream = edge_tts.Communicate(
                chunk, preset['voice'], rate=preset['rate'], pitch=preset['pitch'],
                volume=preset['volume'], boundary='SentenceBoundary',
                connect_timeout=15, receive_timeout=30,
            )
            with raw.open('wb') as handle:
                async for item in stream.stream():
                    if item['type'] == 'audio':
                        handle.write(item['data'])
                    elif item['type'] == 'SentenceBoundary':
                        chunk_events.append((item['offset'] / 1e7, item['duration'] / 1e7, item['text']))
            run(['ffmpeg', '-v', 'error', '-i', str(raw), '-f', 'null', '-'])
            duration = float(run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                                  '-of', 'default=nw=1:nk=1', str(raw)]).stdout)
            normalize = lambda value: ''.join(c.casefold() for c in value if c.isalnum())
            if not chunk_events or normalize(''.join(e[2] for e in chunk_events)) != normalize(chunk):
                raise RuntimeError('Sentence boundaries do not cover the submitted text')
            if any(start < 0 or length <= 0 or start + length > duration + 0.15
                   for start, length, _ in chunk_events):
                raise RuntimeError('Invalid sentence timing')
            events.extend((offset + start, min(offset + start + length, offset + duration), sentence)
                          for start, length, sentence in chunk_events)
            offset += duration
        concat = temp / 'concat.txt'
        concat.write_text(''.join(f"file '{index}.mp3'\n" for index in range(len(chunks))))
        final = temp / 'final.mp3'
        run(['ffmpeg', '-y', '-v', 'error', '-f', 'concat', '-safe', '0', '-i', str(concat),
             '-af', 'loudnorm=I=-11:TP=-1:LRA=7', '-ar', '44100', '-ac', '1',
             '-c:a', 'libmp3lame', '-b:a', '192k', str(final)])
        measured = run(['ffmpeg', '-hide_banner', '-i', str(final), '-af',
                        'loudnorm=I=-11:TP=-1:LRA=7:print_format=json', '-f', 'null', '-'])
        stats = json.loads(measured.stderr[measured.stderr.rfind('{'):])
        if float(stats['input_i']) <= -25 or float(stats['input_tp']) >= 0:
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
            'subjective_listening': 'UNCERTAIN', 'sha256': hashlib.sha256(final.read_bytes()).hexdigest(),
        }, ensure_ascii=False, indent=2), encoding='utf-8')
        # Publish only after synthesis and QA; MP3 acts as completion marker.
        srt.replace(out.with_suffix('.srt'))
        metadata.replace(out.with_suffix('.json'))
        final.replace(out)


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
    text = args.text if args.text is not None else Path(args.text_file).read_text(encoding='utf-8-sig')
    language = args.language
    if language == 'auto':
        language = 'zh' if re.search(r'[\u3400-\u9fff]', text) else 'en'
    voice_id = select_voice(args.topic, language) if args.voice_id == 'auto' else args.voice_id
    try:
        asyncio.run(synthesize(text, args.output, voice_id))
    except Exception as error:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.with_suffix('.error.log').write_text(f'FAILED: {type(error).__name__}: {error}\n', encoding='utf-8')
        print(f'FAILED: {error}')
        return 1
    print(f'SUCCESS voice_id={voice_id} output={args.output}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
