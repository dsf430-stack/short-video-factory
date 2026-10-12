"""Real 068 synthesis and persistent resume verification; no substitute audio."""
import asyncio
import hashlib
import json
import ssl
import tempfile
from pathlib import Path
from unittest.mock import patch

import certifi
import generate_voice as voice


async def main():
    out = voice.ROOT / 'stability-output'
    out.mkdir(exist_ok=True)
    short = '阿福，這是本次新生成的零六八配音測試。聲音沿用曉臻，語速加百分之二十，音調加五赫茲。'
    await voice.synthesize(short, str(out / '068-new-test.mp3'), '068')
    long = ('這是一段中斷續跑的實際配音測試。每段旁白都有自己的文字與設定校驗碼，'
            '通過檢查後才會保存，接續時不必重新生成已完成的段落。') * 5 + '最後這句必須完整朗讀，字幕也必須保留。'
    chunks = voice.split_text(long)
    assert len(chunks) >= 2
    cache = out / '.068-cache'
    cache.mkdir(exist_ok=True)
    context = ssl.create_default_context()
    context.load_verify_locations(certifi.where())
    voice.edge_tts.communicate._SSL_CTX = context
    # Complete only the first real chunk, then discard the temporary execution state.
    progress = {'status': 'RUNNING', 'attempts': []}
    with tempfile.TemporaryDirectory(dir=out) as directory:
        await voice.get_chunk(chunks[0], voice.VOICES['068'], cache, Path(directory),
                              progress, out / 'seed.progress.json')
    await voice.synthesize(long, str(out / '068-resumed-long.mp3'), '068')
    first = json.loads((out / '068-resumed-long.json').read_text())
    assert first['cache_hits'] >= 1, first
    # Assert that a second run genuinely needs no speech-service connection.
    with patch.object(voice.edge_tts, 'Communicate', side_effect=AssertionError('Unexpected network call')):
        await voice.synthesize(long, str(out / '068-cache-verified.mp3'), '068')
    cached = json.loads((out / '068-cache-verified.json').read_text())
    assert cached['cache_hits'] == cached['chunks']
    assert first['text_sha256'] == hashlib.sha256(long.encode()).hexdigest()
    assert first['sha256'] == cached['sha256']
    # Corrupted bytes must be rejected, even when filenames/settings still match.
    damaged = cache / f'{voice.chunk_key(chunks[-1], voice.VOICES["068"])}.mp3'
    damaged.write_bytes(b'corrupted-cache-for-integrity-test')
    await voice.synthesize(long, str(out / '068-cache-repaired.mp3'), '068')
    repaired_progress = json.loads((out / '068-cache-repaired.progress.json').read_text())
    assert repaired_progress['invalid_cache']
    final = json.loads((out / '068-cache-repaired.json').read_text())
    report = {'status': 'SUCCESS', 'new_audio': True, 'resume': 'PASS',
              'offline_cache_reuse': 'PASS', 'corrupt_cache_regeneration': 'PASS',
              'voice_id': '068', 'preset': voice.VOICES['068'],
              'long_text_chars': len(long), 'chunks': final['chunks'],
              'duration': final['duration'], 'full_decode': final['full_decode'],
              'subjective_listening': 'UNCERTAIN'}
    (out / 'verification.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print(json.dumps(report, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    asyncio.run(main())
