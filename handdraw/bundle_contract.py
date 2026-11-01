"""Shared, read-only checks used by activation, preflight and production.

These checks verify evidence integrity; they never create visual-review passes.
"""
import hashlib
import json
from pathlib import Path

OFFICIAL_COMMIT = '5206ec0d17f9b353e400b64b9c51ad69e721e02a'


def validation_identity(bundle):
    from pipeline_state import content_fingerprint
    bundle = Path(bundle)
    request = json.loads((bundle/'request.json').read_text()) if (bundle/'request.json').exists() else {}
    return content_fingerprint(bundle, Path(__file__).resolve().parents[1], request.get('seconds'), False,
                               {'official_commit': OFFICIAL_COMMIT})


def require_validation_receipt(bundle):
    path = Path(bundle)/'asset-validation.json'
    if not path.exists():
        raise ValueError('PREFLIGHT_REQUIRED: run check_bundle.py with the pinned official engine before activation')
    receipt = json.loads(path.read_text())
    if receipt.get('status') != 'ASSETS_VALIDATED' or receipt.get('bundle_sha256') != validation_identity(bundle):
        raise ValueError('PREFLIGHT_STALE: bundle or validation code changed; rerun check_bundle.py')


def reviewed_images(bundle):
    from PIL import Image
    bundle = Path(bundle).resolve()
    record = json.loads((bundle / 'design/art-direction.json').read_text())
    errors = []
    images = record.get('images', [])
    if not images:
        errors.append('art-direction.images is empty')
    for index, entry in enumerate(images):
        label = entry.get('source', f'images[{index}]')
        path = (bundle / 'design' / label).resolve()
        if not path.is_relative_to(bundle) or not path.is_file():
            errors.append(f'{label}: missing or unsafe reviewed image')
            continue
        if entry.get('status') != 'pass' or not entry.get('evidence', '').strip():
            errors.append(f'{label}: missing visual review evidence')
        if entry.get('sha256') != hashlib.sha256(path.read_bytes()).hexdigest():
            errors.append(f'{label}: sha256 missing or mismatched')
        try:
            with Image.open(path) as image:
                pixels = hashlib.sha256(image.convert('RGBA').tobytes()).hexdigest()
            if entry.get('pixel_sha256') != pixels:
                errors.append(f'{label}: pixel_sha256 missing or mismatched')
        except (OSError, ValueError) as error:
            errors.append(f'{label}: unreadable image ({error})')
    if errors:
        raise ValueError('BUNDLE_REVIEW_INVALID:\n' + '\n'.join(errors))
    return len(images)


def duration_mode(story, request, seconds):
    """Resolve one duration policy; reject contradictions instead of guessing."""
    modes = {v for v in (story.get('duration_mode'), request.get('duration_mode')) if v}
    if modes - {'target', 'narration'} or len(modes) > 1:
        raise ValueError('DURATION_MODE_MISMATCH: story and request must agree')
    mode = next(iter(modes), 'narration' if seconds is None else 'target')
    # Legacy successful bundles have seconds=30/178 but explicitly choose
    # narration in story.json. Retain that editorial choice; never cut speech.
    if mode == 'target' and seconds is None:
        raise ValueError('DURATION_MODE_MISMATCH: target requires seconds')
    return mode
