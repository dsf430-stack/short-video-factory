"""Re-render existing approved jobs and exercise retry without generating new media."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
CASES = {
    'short-natural': 'job-a0e3dc64c9e15415b154',
    'style13-target': 'job-d158225f04c9fad3ceaa',
    'long-silent-style17': 'job-ff73bc84af8d413fc3d5',
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', required=True, choices=CASES)
    parser.add_argument('--official', required=True)
    args = parser.parse_args()
    identity = CASES[args.case]
    bundle = ROOT/'prepared'/identity
    request = json.loads((bundle/'request.json').read_text())
    output = ROOT/'output'/'regression'/args.case
    command = [sys.executable, str(ROOT/'produce.py'), '--job-id', identity,
               '--topic', request['topic'], '--style', request['style'],
               '--official', args.official, '--output', str(output)]
    if request.get('seconds') is not None:
        command.extend(['--seconds', str(request['seconds'])])
    subprocess.run(command, check=True, timeout=3300)
    first = json.loads((output/'acceptance.json').read_text())
    if args.case == 'short-natural':
        # Simulate interrupted final acceptance, without altering the actual MP4.
        (output/'prepared-receipt.json').unlink()
        subprocess.run(command, check=True, timeout=3300)
        state = json.loads((output/'pipeline-state.json').read_text())
        assert state['stages']['render']['reused'], 'Retry unnecessarily re-rendered the film'
        assert first['sha256'] == json.loads((output/'acceptance.json').read_text())['sha256']
    print('REGRESSION_PASS', args.case, first['seconds'], first['sha256'], flush=True)


if __name__ == '__main__':
    main()
