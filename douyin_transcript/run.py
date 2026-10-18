"""Isolated adapter for pinned official douyin-transcript; no paid services."""
import argparse
import difflib
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def probe_duration(path):
    return float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', str(path)], text=True).strip())


def load_tool(path):
    spec = importlib.util.spec_from_file_location('official_douyin', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.ensure_dependencies(require_ffmpeg=True)
    return module


def get_info(dt, link, out):
    # Diagnose the observed missing videoInfoRes response, one User-Agent at a time.
    agents = [dt.HEADERS['User-Agent'],
              'Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36',
              'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36']
    results = []
    for i, agent in enumerate(agents):
        dt.HEADERS['User-Agent'] = agent
        try:
            info = dt.get_video_info(link)
            results.append({'user_agent_variant': i, 'status': 'PASS'})
            write_json(out / 'link-diagnostic.json', results)
            return info
        except Exception as exc:
            results.append({'user_agent_variant': i, 'status': 'FAIL', 'error': str(exc)})
            write_json(out / 'link-diagnostic.json', results)
    raise RuntimeError('Official Douyin parser failed with all 3 User-Agent variants; see link-diagnostic.json. No video downloaded.')


def export(dt, raw_srt, video, out, meta, reference=None):
    from opencc import OpenCC
    converter = OpenCC('s2twp.json')
    duration = probe_duration(video)
    segments = dt.parse_srt_segments(raw_srt.read_text(encoding='utf-8'))
    if not segments:
        raise ValueError('Empty ASR output')
    adjustments = []
    normalized = []
    previous = 0.0
    # Keep original timestamps/text untouched in transcript-raw.srt.
    # A decoder may round its last end beyond EOF; only intersect with actual media.
    for seg in segments:
        start, end = float(seg['start']), float(seg['end'])
        if start < previous - .001 or start < 0 or start >= duration or end <= start:
            raise ValueError(f'Invalid/overlapping ASR timestamp: {seg}')
        if end > duration:
            if end - duration > 2.0:
                raise ValueError('ASR overshoots media by more than 2 seconds; inspect raw output')
            adjustments.append({'index': seg['index'], 'raw_end': end, 'media_end': duration})
            end = int(duration * 1000) / 1000
        normalized.append({**seg, 'start': start, 'end': end, 'text': converter.convert(str(seg['text']))})
        previous = end
    srt = out / 'transcript.zh-TW.srt'
    md = out / 'transcript.zh-TW.md'
    txt = out / 'transcript.zh-TW.txt'
    srt.write_text(dt.generate_srt(normalized), encoding='utf-8')
    md.write_text(dt.generate_markdown({**meta, 'duration_seconds': duration, 'whisper_language': 'zh'}, normalized), encoding='utf-8')
    txt.write_text('\n'.join(s['text'] for s in normalized) + '\n', encoding='utf-8')
    write_json(out / 'segments.zh-TW.json', normalized)
    # Reparse the actual delivered SRT, not just the in-memory objects.
    delivered = dt.parse_srt_segments(srt.read_text(encoding='utf-8'))
    assert len(delivered) == len(normalized)
    assert all(0 <= s['start'] < s['end'] <= duration + .001 and s['text'].strip() for s in delivered)
    text = txt.read_text(encoding='utf-8').strip()
    assert text and re.search('[\u4e00-\u9fff]', text), 'No Chinese speech recognized'
    assert all(p.stat().st_size > 0 for p in (srt, md, txt))
    report = {'status': 'PASS', 'duration_seconds': duration, 'segments': len(delivered),
              'timestamp_adjustments': adjustments, 'text': text, 'human_review_required': True,
              'paid_api_used': False}
    if reference:
        # Verification only: reference is NEVER passed to recognizer or used to repair words.
        def clean(t):
            return re.sub(r'[^\u4e00-\u9fffA-Za-z0-9]', '', converter.convert(t))
        expected, actual = clean(reference.read_text(encoding='utf-8')), clean(text)
        # Explicit character edit distance, including insertions, deletions, substitutions.
        row = list(range(len(actual) + 1))
        for i, a in enumerate(expected, 1):
            nxt = [i]
            for j, b in enumerate(actual, 1):
                nxt.append(min(nxt[-1]+1, row[j]+1, row[j-1]+(a != b)))
            row = nxt
        cer = row[-1] / max(1, len(expected))
        report.update(character_error_rate=cer, reference_characters=len(expected),
                      differences=[{'operation': op, 'expected': expected[a:b], 'recognized': actual[c:d]}
                                   for op,a,b,c,d in difflib.SequenceMatcher(None,expected,actual).get_opcodes() if op != 'equal'])
        if cer > .15 or '石墨' not in text or '鉛筆' not in text:
            report['status'] = 'QUALITY_FAIL'
    report['files'] = {p.name: {'bytes': p.stat().st_size, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
                       for p in (raw_srt, srt, md, txt, out/'segments.zh-TW.json')}
    write_json(out / 'verification.json', report)
    # Existing factory accepts standard UTF-8 SRT through subtitleFile.
    write_json(out / 'factory-input.json', {'schema_version': 1, 'mode': 'transcription',
               'language': 'zh-TW', 'transcript_file': txt.name, 'subtitleFile': srt.name,
               'segments_file': 'segments.zh-TW.json', 'source_kind': meta['source_kind'],
               'asr_review_required': True, 'automatic_render': False})
    if report['status'] != 'PASS':
        raise ValueError(f'Quality check failed: CER={report["character_error_rate"]:.3f}; original recognition retained')
    return report


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--tool', default='.douyin-tool/scripts/douyin_transcript.py')
    p.add_argument('--whisper-bin', default='.whisper/build/bin/whisper-cli')
    p.add_argument('--model', required=True)
    p.add_argument('--mode', choices=['local-test', 'douyin'], default='local-test')
    p.add_argument('--link', default=os.environ.get('DOUYIN_LINK', ''))
    p.add_argument('--output', default='transcription-output')
    p.add_argument('--max-seconds', type=int, default=600)
    args = p.parse_args()
    out = Path(args.output).resolve()
    out.mkdir(parents=True, exist_ok=True)
    dt = load_tool(args.tool)
    summary = {'mode': args.mode, 'status': 'RUNNING', 'paid_api_used': False}
    write_json(out/'run.json', summary)
    try:
        reference = None
        if args.mode == 'local-test':
            source = Path('handdraw/prepared/job-637378837c79e0ffd659/inputs/voice-2395983e1d4d5ff9.mp3')
            reference = source.with_suffix('.txt')
            video = out / 'local-test.mp4'
            subprocess.run(['ffmpeg','-v','error','-y','-f','lavfi','-i','color=c=black:s=320x240:r=10','-i',str(source),'-shortest','-c:v','libx264','-c:a','aac',str(video)],check=True)
            meta = {'title': 'Existing Chinese narration test', 'source_kind': 'local-test'}
            # Probe live link independently; its failure never counts as a successful download.
            if args.link:
                try:
                    get_info(dt, args.link, out)
                    summary['douyin_probe'] = 'PASS_INFO_ONLY'
                except Exception as exc:
                    summary['douyin_probe'] = 'FAIL'
                    summary['douyin_error'] = str(exc)
        else:
            if not args.link.strip():
                raise ValueError('Douyin mode requires a share link')
            url = dt.extract_first_url(args.link)
            from urllib.parse import urlparse
            if not url or urlparse(url).hostname not in {'v.douyin.com','www.douyin.com','douyin.com','www.iesdouyin.com'}:
                raise ValueError('Input must contain a Douyin share URL')
            info = get_info(dt, args.link, out)
            write_json(out/'source.json', {k:info.get(k) for k in ('video_id','title','duration_seconds','source_url')})
            if float(info.get('duration_seconds',0)) > args.max_seconds:
                raise ValueError('Video exceeds configured duration limit')
            # Download with official implementation, no external parsing APIs/cookies.
            video = dt.DouyinProcessor().download_video(info, output_path=out/'source.mp4')
            meta = {**info, 'source_kind': 'douyin'}
        duration = probe_duration(video)
        if not 0 < duration <= args.max_seconds:
            raise ValueError('Invalid or over-limit video duration')
        # Lossless mono 16 kHz PCM input avoids an extra MP3 encoding generation.
        audio = out / 'audio.wav'
        subprocess.run(['ffmpeg','-v','error','-y','-i',str(video),'-vn','-ac','1','-ar','16000','-c:a','pcm_s16le',str(audio)], check=True)
        raw = out/'transcript-raw.srt'
        dt.DouyinProcessor().transcribe_audio_to_srt(audio,raw,str(Path(args.whisper_bin).resolve()),str(Path(args.model).resolve()),'zh')
        report = export(dt, raw, video, out, meta, reference)
        summary.update(status='PASS', segments=report['segments'], duration_seconds=duration)
    except Exception as exc:
        summary.update(status='FAIL', error=str(exc))
        raise
    finally:
        write_json(out/'run.json', summary)
        print(json.dumps(summary,ensure_ascii=False))


if __name__ == '__main__':
    main()
