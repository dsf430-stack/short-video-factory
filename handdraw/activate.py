"""Select an already reviewed assistant-prepared job for the existing Actions pipeline."""
import argparse
import hashlib
import json
from pathlib import Path
from preparation import resolve_bundle, save_json, safe_bundle

ROOT = Path(__file__).resolve().parent

def activate(job_id, prepared=ROOT / 'prepared', destination=ROOT / 'active-job.json'):
    request = json.loads((safe_bundle(prepared, job_id) / 'request.json').read_text())
    bundle = resolve_bundle(prepared, request['topic'], request['seconds'], job_id, request['style'])
    selection = {'job_id': bundle.name, 'topic': request['topic'], 'seconds': request['seconds'],
                 'style': request['style'], 'bundle_sha256': hashlib.sha256(''.join(str(p.relative_to(bundle)) + hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(bundle.rglob('*')) if p.is_file() and p.name != 'preparation-status.json').encode()).hexdigest(), 'mode': 'chatgpt-prepared-no-extra-model-api'}
    save_json(destination, selection)
    return selection

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--job-id', required=True)
    args = p.parse_args()
    print(json.dumps(activate(args.job_id), ensure_ascii=False))
