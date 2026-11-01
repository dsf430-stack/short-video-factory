"""Atomic stage evidence and bounded commands; checkpoints are not validation."""
import json
import hashlib
import importlib.metadata
import os
import signal
import subprocess
import time
from pathlib import Path
from preparation import save_json


def check_runtime(voice_only=False):
    import shutil
    commands = ('ffmpeg', 'ffprobe') if voice_only else ('ffmpeg', 'ffprobe', 'bun', 'exiftool')
    missing = [command for command in commands if not shutil.which(command)]
    font = Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
    if not voice_only and not font.is_file():
        missing.append(str(font))
    if missing:
        raise ValueError('RUNTIME_REQUIRED: ' + ', '.join(missing))


def runtime_fingerprint():
    versions = {'python': __import__('sys').version}
    for name in ('Pillow', 'numpy', 'scipy', 'requests', 'edge-tts', 'aiohttp'):
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = 'not-installed'
    versions['ffmpeg'] = subprocess.check_output(['ffmpeg', '-version'], timeout=30, text=True).splitlines()[0]
    return versions


def content_fingerprint(bundle, repo, seconds, voice_only, runtime):
    bundle, repo = Path(bundle), Path(repo)
    files = [*(p for p in sorted((repo/'handdraw').glob('*.py')) if not p.name.startswith('test_')),
             repo/'smart_voice/generate_voice.py', repo/'smart_voice/voices.json']
    inputs = []
    for path in sorted(bundle.rglob('*')):
        if not path.is_file() or path.name == 'preparation-status.json':
            continue
        if path.name == 'request.json':
            request = json.loads(path.read_text())
            request.pop('state', None)
            data = json.dumps(request, sort_keys=True).encode()
        else:
            data = path.read_bytes()
        inputs.append((str(path.relative_to(bundle)), hashlib.sha256(data).hexdigest()))
    identity = {'seconds': seconds, 'voice_only': voice_only, 'runtime': runtime,
                'inputs': inputs, 'code': [(str(p.relative_to(repo)), hashlib.sha256(p.read_bytes()).hexdigest()) for p in files]}
    return hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()


def sync_inputs(bundle, root):
    import shutil
    bundle, root = Path(bundle), Path(root)
    # Design/style are immutable source snapshots. Remove deleted old files.
    for directory in ('style', 'design'):
        destination = root / directory
        if destination.exists():
            shutil.rmtree(destination)
        shutil.copytree(bundle / directory, destination)
    destination = root / 'inputs'
    destination.mkdir(parents=True, exist_ok=True)
    for path in destination.iterdir():
        if path.is_file() and not path.name.startswith('voice-') and not (bundle/'inputs'/path.name).is_file():
            path.unlink()
    # Prepared audio is authoritative (including authorized silent windows).
    # Audio generated on a previous attempt survives if it is not in the bundle.
    shutil.copytree(bundle/'inputs', destination, dirs_exist_ok=True)


def run_command(*args, timeout=1800):
    # Terminate descendants (including ffmpeg) when a stage exceeds its limit.
    process = subprocess.Popen([str(arg) for arg in args], start_new_session=True)
    try:
        code = process.wait(timeout=timeout)
    except BaseException:
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
        raise
    if code:
        raise subprocess.CalledProcessError(code, process.args)


class Pipeline:
    def __init__(self, root):
        self.path = Path(root) / 'pipeline-state.json'
        self.current = None
        self.state = {'version': 1, 'status': 'RUNNING', 'stages': {}}
        if self.path.exists():
            try:
                previous = json.loads(self.path.read_text())
                self.state['previous_attempt'] = {
                    key: previous.get(key) for key in ('status', 'failed_stage', 'error')}
            except (OSError, ValueError):
                self.state['previous_attempt'] = {'status': 'INVALID_CHECKPOINT'}
        self.write()

    def write(self):
        self.state['updated_at'] = time.time()
        save_json(self.path, self.state)

    def start(self, stage):
        self.current = stage
        self.state['stages'][stage] = {'status': 'RUNNING', 'started_at': time.time()}
        self.write()
        print('STAGE_START', stage, flush=True)

    def done(self, reused=False):
        self.state['stages'][self.current].update(
            status='DONE', completed_at=time.time(), reused=reused)
        self.write()
        print('STAGE_DONE', self.current, 'reused=' + str(reused), flush=True)
        self.current = None

    def fail(self, error):
        self.state.update(status='FAILED', failed_stage=self.current,
                          error={'type': type(error).__name__, 'message': str(error)})
        if self.current:
            self.state['stages'][self.current]['status'] = 'FAILED'
        self.write()

    def finish(self, status):
        self.state['status'] = status
        self.write()
