"""Create resumable requests; catalog indexes ready bundles, never authorizes topics."""
import hashlib
import json
from pathlib import Path

REQUIRED = ('story.json', 'design.json', 'style/selection.json', 'style/resolved.json',
            'design/art-direction.json', 'design/drawing-plan.json',
            'design/drawing-plan.preflight.json', 'design/drawing-review.json', 'inputs/cover.png')

def resolve_bundle(prepared, topic, seconds):
    prepared = Path(prepared).resolve()
    catalog = json.loads((prepared / 'catalog.json').read_text())
    key = catalog.get(topic, 'topic-' + hashlib.sha256(topic.encode()).hexdigest()[:16])
    bundle = (prepared / key).resolve()
    if not bundle.is_relative_to(prepared) or bundle == prepared:
        raise ValueError('Bundle path escapes prepared directory')
    # Discover an assistant-prepared request even before its ready-index entry exists.
    if topic not in catalog:
        for candidate in sorted(prepared.glob('*/request.json')):
            request = json.loads(candidate.read_text())
            if request.get('topic') == topic:
                bundle = candidate.parent
                break
    bundle.mkdir(parents=True, exist_ok=True)
    for folder in ('inputs', 'design', 'style'):
        (bundle / folder).mkdir(exist_ok=True)
    request_path = bundle / 'request.json'
    if not request_path.exists():
        request_path.write_text(json.dumps({'topic': topic, 'seconds': seconds, 'style': '4',
            'voice_id': '068', 'state': 'PREPARATION_REQUIRED',
            'required_files': list(REQUIRED)}, ensure_ascii=False, indent=2) + '\n')
    missing = [name for name in REQUIRED if not (bundle / name).is_file()]
    if missing:
        (bundle / 'preparation-status.json').write_text(json.dumps({
            'state': 'PREPARATION_REQUIRED', 'missing': missing,
            'reason': 'No runtime content/image provider is configured. Assistant must prepare and visually review these assets; never substitute another topic.'}, ensure_ascii=False, indent=2) + '\n')
        raise ValueError(f'PREPARATION_REQUIRED: request created at {request_path}; missing: {", ".join(missing)}')
    story = json.loads((bundle / 'story.json').read_text())
    if story['topic'] != topic:
        raise ValueError('Prepared story topic mismatch')
    for scene in story['scenes']:
        source = (bundle / scene.get('source', 'inputs/' + scene['id'] + '.png')).resolve()
        if not source.is_relative_to(bundle) or not source.is_file():
            raise ValueError('Missing or unsafe scene source: ' + str(source))
    return bundle


def choose_candidate(candidates, measured, target):
    """Choose nearest unmeasured editorial variant, using observed speech rate."""
    remaining = [i for i in range(len(candidates)) if i not in measured]
    if not remaining:
        return None
    length = lambda i: sum(c.isalnum() for text in candidates[i] for c in text)
    if not measured:
        return remaining[len(remaining)//2]
    best = min(measured, key=lambda i: abs(measured[i]-target))
    rate = measured[best] / max(1, length(best))
    return min(remaining, key=lambda i: abs(length(i)*rate-target))
