from pathlib import Path
import json
import tempfile
from flipbook_renderer import FlipbookRenderer, read_srt

root = Path(__file__).resolve().parent
manifest = json.loads((root/'job.json').read_text())
assert ''.join(c['text'] for c in read_srt(root/'inputs/preview.srt')) == (root/'inputs/narration.txt').read_text().strip()
renderer = FlipbookRenderer(root)
assert 10 <= renderer.duration <= 15
assert len(renderer.pages) == 2
assert all(len(p['photos']) >= 3 for p in manifest['pages'])
assert len({p['sha256'] for p in manifest['photos'].values()}) == 6
for variant in ['single_page', 'too_few_photos', 'duplicate_photograph', 'extra_unrendered_pages']:
    changed = json.loads(json.dumps(manifest))
    if variant == 'single_page':
        changed['pages'] = changed['pages'][:1]
    elif variant == 'too_few_photos':
        changed['pages'][0]['photos'] = [1, 2]
    elif variant == 'duplicate_photograph':
        changed['pages'][0]['photos'] = [1, 1, 2]
    else:
        changed['pages'].append(changed['pages'][0])
    with tempfile.TemporaryDirectory(prefix='taiwan-flipbook-test-') as tmp:
        job = Path(tmp)
        (job/'inputs').symlink_to(root/'inputs', target_is_directory=True)
        (job/'job.json').write_text(json.dumps(changed))
        try:
            FlipbookRenderer(job)
        except ValueError:
            print('PASS rejection:', variant)
        else:
            raise AssertionError('Invalid configuration accepted: ' + variant)
print('SUCCESS: true inputs, timestamps, photo count, uniqueness and invalid configuration gates')
