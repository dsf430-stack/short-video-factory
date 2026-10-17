"""Resumable assistant-prepared jobs; no model API, topic allowlist or content template."""
import argparse
import hashlib
import json
import re
from pathlib import Path

REQUIRED = ('story.json', 'design.json', 'style/selection.json', 'style/resolved.json',
            'design/art-direction.json', 'design/drawing-plan.json',
            'design/drawing-plan.preflight.json', 'design/drawing-review.json', 'inputs/cover.png')


def save_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temporary.replace(path)


def job_identity(topic, seconds, style='4', script=''):
    if not topic.strip() or not isinstance(seconds, int) or not 3 <= seconds <= 3600:
        raise ValueError('A nonempty topic and integer duration from 3 to 3600 seconds are required')
    value = {'topic': topic, 'seconds': seconds, 'style': str(style),
             'script_sha256': hashlib.sha256(script.encode()).hexdigest()}
    return 'job-' + hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:20]


def safe_bundle(prepared, identity):
    prepared = Path(prepared).resolve()
    if not isinstance(identity, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,95}', identity):
        raise ValueError('Bundle path escapes prepared directory or has an invalid job id')
    bundle = (prepared / identity).resolve()
    if not bundle.is_relative_to(prepared) or bundle == prepared:
        raise ValueError('Bundle path escapes prepared directory')
    return bundle


def create_request(prepared, topic, seconds, style='4', script='', job_id=None):
    identity = job_id or job_identity(topic, seconds, style, script)
    bundle = safe_bundle(prepared, identity)
    bundle.mkdir(parents=True, exist_ok=True)
    for folder in ('inputs', 'design', 'style'):
        (bundle / folder).mkdir(exist_ok=True)
    request = {'topic': topic, 'seconds': seconds, 'style': str(style), 'job_id': identity,
               'voice_id': '068', 'mode': 'chatgpt-prepared-no-extra-model-api',
               'script_sha256': hashlib.sha256(script.encode()).hexdigest(),
               'state': 'PREPARATION_REQUIRED', 'required_files': list(REQUIRED)}
    existing = bundle / 'request.json'
    if existing.exists():
        current = json.loads(existing.read_text())
        for key in ('topic', 'seconds', 'style'):
            if current.get(key) != request[key]:
                raise ValueError('REQUEST_SETTINGS_MISMATCH: use a distinct job_id for a revised task')
        if script and current.get('script_sha256') != request['script_sha256']:
            raise ValueError('REQUEST_SCRIPT_MISMATCH: use a distinct job_id for a revised script')
    else:
        save_json(existing, request)
        if script:
            (bundle / 'source-script.txt').write_text(script, encoding='utf-8')
    return bundle


def validate_bundle(bundle, topic, voice_only=False):
    bundle = Path(bundle).resolve()
    required = ('story.json',) if voice_only else REQUIRED
    missing = [name for name in required if not (bundle / name).is_file()]
    if missing:
        save_json(bundle / 'preparation-status.json', {
            'state': 'PREPARATION_REQUIRED', 'missing': missing,
            'next_actor': 'ChatGPT assistant',
            'reason': 'Prepare and visually review this script in ChatGPT, then commit and dispatch. No extra model API key is required.'})
        raise ValueError(f'PREPARATION_REQUIRED: {bundle}; missing: {", ".join(missing)}')
    story = json.loads((bundle / 'story.json').read_text())
    if story.get('topic') != topic or not story.get('scenes'):
        raise ValueError('Prepared story topic mismatch or empty storyboard')
    ids = [scene['id'] for scene in story['scenes']]
    if len(set(ids)) != len(ids):
        raise ValueError('Storyboard scene ids must be unique')
    for scene in story['scenes']:
        if not scene.get('text', '').strip() or (not voice_only and not scene.get('parts')):
            raise ValueError('Every scene requires narration and reviewed semantic parts')
        if voice_only:
            continue
        for source in [scene.get('source', 'inputs/' + scene['id'] + '.png'), scene.get('outline_mask')]:
            if source:
                path = (bundle / source).resolve()
                if not path.is_relative_to(bundle) or not path.is_file():
                    raise ValueError('Missing or unsafe scene source: ' + source)
    # Do not let old missing-status files describe a now-prepared bundle.
    status = bundle / 'preparation-status.json'
    if not voice_only and status.exists():
        status.unlink()
    return story


def resolve_bundle(prepared, topic, seconds, job_id=None, style=None, voice_only=False):
    prepared = Path(prepared).resolve()
    if job_id:
        bundle = safe_bundle(prepared, job_id)
        if not bundle.is_dir():
            raise ValueError('Unknown job_id: ' + job_id)
    else:
        index = prepared / 'catalog.json'
        catalog = json.loads(index.read_text()) if index.exists() else {}
        # The index is only a shortcut. Exact requests resolve without registration.
        candidates = []
        if topic in catalog:
            candidates.append(safe_bundle(prepared, catalog[topic]))
        for request_path in sorted(prepared.glob('*/request.json')):
            request = json.loads(request_path.read_text())
            if request.get('topic') == topic and request.get('seconds') == seconds and (style is None or request.get('style') == str(style)):
                candidate = safe_bundle(prepared, request_path.parent.name)
                if candidate not in candidates:
                    candidates.append(candidate)
        matching = []
        for candidate in candidates:
            request_path = candidate / 'request.json'
            if request_path.exists():
                request = json.loads(request_path.read_text())
                if request.get('seconds') != seconds or (style is not None and request.get('style') != str(style)):
                    continue
            matching.append(candidate)
        if len(matching) > 1:
            raise ValueError('AMBIGUOUS_TOPIC: provide job_id; multiple scripts match this topic')
        bundle = matching[0] if matching else create_request(prepared, topic, seconds, style or '4')
    request_path = bundle / 'request.json'
    if request_path.exists():
        request = json.loads(request_path.read_text())
        if request.get('topic') != topic or request.get('seconds') != seconds or (style is not None and request.get('style') != str(style)):
            raise ValueError('REQUEST_SETTINGS_MISMATCH: topic, seconds or style differs from the selected job')
    validate_bundle(bundle, topic, voice_only)
    if style is not None:
        resolved = json.loads((bundle / 'style/resolved.json').read_text())
        if resolved.get('catalog_id') != str(style):
            raise ValueError('Requested style does not match the reviewed bundle')
    return bundle


def choose_candidate(candidates, measured, target, preferred=None):
    remaining = [i for i in range(len(candidates)) if i not in measured]
    if not remaining:
        return None
    length = lambda i: sum(c.isalnum() for text in candidates[i] for c in text)
    if not measured:
        if isinstance(preferred, int) and preferred in remaining:
            return preferred
        return remaining[len(remaining)//2]
    best = min(measured, key=lambda i: abs(measured[i]-target))
    rate = measured[best] / max(1, length(best))
    return min(remaining, key=lambda i: abs(length(i)*rate-target))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--topic', required=True)
    parser.add_argument('--seconds', type=int, default=30)
    parser.add_argument('--style', default='4')
    parser.add_argument('--script-file', type=Path)
    parser.add_argument('--job-id')
    parser.add_argument('--prepared', type=Path, default=Path(__file__).parent / 'prepared')
    args = parser.parse_args()
    bundle = create_request(args.prepared, args.topic, args.seconds, args.style,
                            args.script_file.read_text() if args.script_file else '', args.job_id)
    print(json.dumps({'job_id': bundle.name, 'bundle': str(bundle)}, ensure_ascii=False))
