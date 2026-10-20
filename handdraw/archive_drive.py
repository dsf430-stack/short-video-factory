"""Archive an engineering-verified film; never publish or change Drive sharing."""
import argparse
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path

FOLDER_ID = '1MYEGF9AgF7nFpTgRZIU-79Vjs6qtDLB5'
SCOPE = 'https://www.googleapis.com/auth/drive.file'
FIELDS = 'id,name,size,md5Checksum,parents,webViewLink,appProperties'


def hashes(path):
    sha, md5 = hashlib.sha256(), hashlib.md5()
    with Path(path).open('rb') as source:
        for block in iter(lambda: source.read(1024 * 1024), b''):
            sha.update(block)
            md5.update(block)
    return sha.hexdigest(), md5.hexdigest()


def validated_film(root):
    root = Path(root)
    films = list(root.rglob('film.mp4'))
    if len(films) != 1:
        raise ValueError('Expected exactly one film.mp4 in the selected artifact')
    film = films[0]
    receipts = list(root.rglob('acceptance.json'))
    captions = list(root.rglob('transcript.srt'))
    if len(receipts) != 1 or len(captions) != 1 or not captions[0].read_text().strip():
        raise ValueError('Missing or ambiguous acceptance/captions')
    report = json.loads(receipts[0].read_text())
    sha, md5 = hashes(film)
    if report.get('status') not in ('ENGINEERING_PASS', 'SUCCESS') or report.get('sha256') != sha:
        raise ValueError('Film does not match a passing acceptance receipt')
    if report.get('voice') != '068' or not re.fullmatch(r'[A-Za-z0-9_.-]{1,96}', report.get('job_id', '')):
        raise ValueError('Missing 068 voice or valid job identity')
    probe = json.loads(subprocess.check_output([
        'ffprobe', '-v', 'error', '-show_streams', '-of', 'json', str(film)]))
    video = [s for s in probe['streams'] if s['codec_type'] == 'video']
    audio = [s for s in probe['streams'] if s['codec_type'] == 'audio']
    if (len(video) != 1 or len(audio) != 1
            or video[0]['codec_name'] != 'h264' or audio[0]['codec_name'] != 'aac'
            or (video[0]['width'], video[0]['height'], video[0]['avg_frame_rate']) != (1080, 1920, '30/1')
            or abs(float(video[0]['duration']) - float(report['seconds'])) > .05
            or any(s['codec_type'] == 'subtitle' for s in probe['streams'])):
        raise ValueError('MP4 format/receipt duration/subtitle-track check failed')
    subprocess.run(['ffmpeg', '-v', 'error', '-xerror', '-i', str(film), '-f', 'null', '-'], check=True)
    return film, report, sha, md5


def drive_client():
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    raw = os.environ.get('GDRIVE_AUTHORIZED_USER_JSON', '')
    if not raw:
        raise ValueError('DRIVE_AUTH_REQUIRED: configure GDRIVE_AUTHORIZED_USER_JSON in GitHub Secrets')
    data = json.loads(raw)
    # This utility never requests access to the whole Drive or accepts service-account keys.
    if data.get('type', 'authorized_user') != 'authorized_user' or set(data.get('scopes', [])) != {SCOPE}:
        raise ValueError('Use authorized-user OAuth with only drive.file scope; select the destination folder for that app')
    if not all(data.get(k) for k in ('client_id', 'client_secret', 'refresh_token')):
        raise ValueError('Incomplete authorized-user credential')
    credentials = Credentials.from_authorized_user_info(data, scopes=[SCOPE])
    return build('drive', 'v3', credentials=credentials, cache_discovery=False)


def check_destination(service):
    folder = service.files().get(fileId=FOLDER_ID, fields='id,mimeType,trashed,capabilities(canAddChildren)', supportsAllDrives=True).execute()
    if (folder.get('mimeType') != 'application/vnd.google-apps.folder' or folder.get('trashed')
            or not folder.get('capabilities', {}).get('canAddChildren')):
        raise ValueError('Destination folder is unavailable or not writable by this OAuth app')


def verify_remote(remote, film, sha, md5):
    if (remote.get('md5Checksum') != md5 or int(remote.get('size', -1)) != film.stat().st_size
            or FOLDER_ID not in remote.get('parents', [])
            or remote.get('appProperties', {}).get('sha256') != sha
            or not remote.get('webViewLink')):
        raise ValueError('DRIVE_VERIFY_FAILED: keep the artifact and inspect the existing file; do not blindly upload again')


def archive(service, film, report, sha, md5, media_factory):
    check_destination(service)
    query = f"trashed=false and '{FOLDER_ID}' in parents and appProperties has {{ key='sha256' and value='{sha}' }}"
    existing = service.files().list(q=query, fields=f'files({FIELDS}),nextPageToken', pageSize=100).execute()
    if existing.get('nextPageToken') or len(existing.get('files', [])) > 1:
        raise ValueError('Duplicate archive records; manual reconciliation required')
    if existing.get('files'):
        remote = existing['files'][0]
        state = 'ALREADY_SAVED'
    else:
        body = {'name': report['job_id'] + '.mp4', 'parents': [FOLDER_ID],
                'appProperties': {'sha256': sha, 'job_id': report['job_id'], 'qa': report['status']}}
        # A failed/uncertain create is NOT repeated. A later archive-only run searches by hash first.
        chunk_size = 8 * 1024 * 1024
        request = service.files().create(body=body, media_body=media_factory(str(film), mimetype='video/mp4', resumable=True, chunksize=chunk_size), fields=FIELDS)
        remote = None
        for _ in range((film.stat().st_size + chunk_size - 1) // chunk_size + 1):
            _, remote = request.next_chunk(num_retries=0)
            if remote is not None:
                break
        if remote is None:
            raise ValueError('UPLOAD_INCOMPLETE: chunk limit reached; inspect the destination before resuming')
        remote = service.files().get(fileId=remote['id'], fields=FIELDS, supportsAllDrives=True).execute()
        state = 'SAVED'
    verify_remote(remote, film, sha, md5)
    return {'status': state, 'file_id': remote['id'], 'url': remote['webViewLink'],
            'sha256': sha, 'folder_id': FOLDER_ID, 'job_id': report['job_id'],
            'engineering_status': report['status'], 'human_listening': report.get('human_listening', 'UNCERTAIN'),
            'source_run_id': os.environ.get('SOURCE_RUN_ID'), 'archive_run_id': os.environ.get('GITHUB_RUN_ID')}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--artifact', type=Path)
    parser.add_argument('--preflight', action='store_true')
    parser.add_argument('--receipt', type=Path, default=Path('drive-receipt.json'))
    args = parser.parse_args()
    service = drive_client()
    if args.preflight:
        check_destination(service)
        print('DRIVE_PREFLIGHT_PASS')
        return
    if not args.artifact:
        parser.error('--artifact is required for archiving')
    from googleapiclient.http import MediaFileUpload
    film, report, sha, md5 = validated_film(args.artifact)
    receipt = archive(service, film, report, sha, md5, MediaFileUpload)
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.receipt.with_suffix('.tmp')
    temporary.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n')
    temporary.replace(args.receipt)
    print(json.dumps(receipt, ensure_ascii=False))
    if os.environ.get('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'], 'a') as summary:
            summary.write(f"\nDrive: [{receipt['job_id']}]({receipt['url']}) — {receipt['status']}\n")


if __name__ == '__main__':
    # Do not echo OAuth refresh failures (which can contain credential request data).
    try:
        main()
    except Exception as error:
        print(f'ARCHIVE_FAILED ({type(error).__name__}). Credentials, destination access, or artifact checks failed; no automatic retry.', flush=True)
        raise SystemExit(1)
