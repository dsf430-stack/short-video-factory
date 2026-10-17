"""Resolve explicit dispatch inputs or active-job.json into isolated Actions outputs."""
import hashlib
import json
import os
from pathlib import Path
from preparation import resolve_bundle, safe_bundle

ROOT = Path(__file__).resolve().parent


def resolve(inputs, root=ROOT):
    active = json.loads((root / 'active-job.json').read_text()) if (root / 'active-job.json').exists() else {}
    identity = inputs.get('job_id') or (active.get('job_id') if not inputs.get('topic') else None)
    request_path = safe_bundle(root / 'prepared', identity) / 'request.json' if identity else None
    request = json.loads(request_path.read_text()) if request_path and request_path.exists() else {}
    if identity and not request:
        legacy = safe_bundle(root / 'prepared', identity)
        story = json.loads((legacy / 'story.json').read_text())
        request = {'topic': story['topic']}
        resolved_path = legacy / 'style/resolved.json'
        if resolved_path.exists():
            request['style'] = json.loads(resolved_path.read_text()).get('catalog_id')
    topic = request.get('topic') or inputs.get('topic') or active.get('topic')
    if not topic:
        raise ValueError('Provide a topic or activate a prepared job')
    requested_seconds = inputs.get('seconds') or request.get('seconds') or active.get('seconds') or 30
    seconds = int(requested_seconds)
    if float(requested_seconds) != seconds:
        raise ValueError('Duration must be an integer number of seconds')
    style = str(inputs.get('style') or request.get('style') or '') or None
    bundle = resolve_bundle(root / 'prepared', topic, seconds, identity, style)
    key = hashlib.sha256(json.dumps({'bundle': bundle.name, 'seconds': seconds, 'style': style}, sort_keys=True).encode()).hexdigest()[:24]
    return {'topic': topic, 'seconds': seconds, 'style': style or '', 'job_id': bundle.name,
            'key': key, 'root': f'handdraw/output/{key}'}


if __name__ == '__main__':
    result = resolve(json.loads(os.environ.get('HANDDRAW_INPUTS', '{}')) or {})
    # A GITHUB_OUTPUT value must not inject another output field.
    for value in result.values():
        if '\n' in str(value) or '\r' in str(value):
            raise ValueError('Job fields must be single-line values')
    with open(os.environ['GITHUB_OUTPUT'], 'a') as stream:
        for key, value in result.items():
            stream.write(f'{key}={value}\n')
    print(json.dumps(result, ensure_ascii=False))
