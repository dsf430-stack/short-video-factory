"""Prepare inputs for the unchanged official Sweety VoxCPM2 adapter."""
import argparse
import json
import re
from pathlib import Path


def prepare(text, name, model, output):
    text = text.strip()
    if not text or len(text) > 10000:
        raise ValueError('Narration must contain 1-10000 characters')
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,64}', name):
        raise ValueError('Filename must be 1-64 ASCII letters, digits, _ or -')
    root = Path(output).resolve()
    root.mkdir(parents=True, exist_ok=True)
    job = {'version': 1, 'title': 'R01 儒雅青年配音',
           'voxcpm': {'voice': 'scholarly-young-man', 'mode': 'combined',
                      'model_path': str(Path(model).resolve()), 'cfg_value': 2.0,
                      'timesteps': 10, 'seed': 2026},
           'narration': {'source': f'{name}.wav', 'alignment': f'{name}.alignment.json'},
           'pages': [{'beats': [{'id': 'narration', 'text': text}]}]}
    (root / 'job.json').write_text(json.dumps(job, ensure_ascii=False, indent=2), encoding='utf-8')
    (root / 'script.txt').write_text(text, encoding='utf-8')
    return job


if __name__ == '__main__':
    import os
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    prepare(os.environ['R01_NARRATION'], os.environ['R01_FILENAME'],
            os.environ['R01_MODEL'], args.output)
