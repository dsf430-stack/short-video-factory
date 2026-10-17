"""Validate complete speech artifacts before reuse; repair only the requested voice."""
import hashlib
import json
import re
from pathlib import Path


def valid_subtitles(path, expected_text=None):
    try:
        content=Path(path).read_text().strip()
        if not content:
            return False
        spoken=[];previous=0.
        def seconds(stamp):
            h,m,s=stamp.replace(',','.').split(':')
            return int(h)*3600+int(m)*60+float(s)
        for block in re.split(r'\n\s*\n',content):
            lines=block.splitlines()
            start,end=(seconds(t) for t in lines[1].split(' --> '))
            if start<previous-.02 or end<=start or len(lines)<3:
                return False
            previous=end;spoken.append(''.join(lines[2:]))
        normalize=lambda t:''.join(c for c in t if c.isalnum())
        return expected_text is None or normalize(''.join(spoken))==normalize(expected_text)
    except (OSError,ValueError,IndexError,TypeError):
        return False


def valid_voice_cache(mp3, text_hash, expected, text=None):
    mp3 = Path(mp3)
    try:
        meta = json.loads(mp3.with_suffix('.json').read_text())
        return (valid_subtitles(mp3.with_suffix('.srt'),text) and
                meta['text_sha256'] == text_hash and meta['voice_id'] == '068' and
                meta['sha256'] == hashlib.sha256(mp3.read_bytes()).hexdigest() and
                all(meta['preset'][k] == expected[k] for k in ('voice', 'rate', 'pitch', 'volume')))
    except (OSError, ValueError, KeyError, TypeError):
        return False


def invalidate_voice_cache(mp3):
    for suffix in ('.mp3', '.json', '.srt'):
        Path(mp3).with_suffix(suffix).unlink(missing_ok=True)
