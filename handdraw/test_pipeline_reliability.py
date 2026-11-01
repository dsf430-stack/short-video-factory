import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from PIL import Image
from bundle_contract import reviewed_images, duration_mode, require_validation_receipt
from pipeline_state import Pipeline, run_command, content_fingerprint, sync_inputs, check_runtime
from produce import execute
from preparation import save_json
from resolve_job import resolve


class ReliabilityTests(unittest.TestCase):
    def image_bundle(self, root):
        (root/'inputs').mkdir()
        (root/'design').mkdir()
        image = root/'inputs/scene.png'
        Image.new('RGB', (8, 8), 'white').save(image)
        with Image.open(image) as picture:
            pixels = hashlib.sha256(picture.convert('RGBA').tobytes()).hexdigest()
        entry = {'source': '../inputs/scene.png', 'status': 'pass', 'evidence': 'test evidence',
                 'sha256': hashlib.sha256(image.read_bytes()).hexdigest(), 'pixel_sha256': pixels}
        save_json(root/'design/art-direction.json', {'images': [entry]})
        return entry

    def test_missing_pixel_hash_is_rejected_before_production(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            entry = self.image_bundle(root)
            self.assertEqual(reviewed_images(root), 1)
            del entry['pixel_sha256']
            save_json(root/'design/art-direction.json', {'images': [entry]})
            with self.assertRaisesRegex(ValueError, 'pixel_sha256 missing'):
                reviewed_images(root)
            self.assertNotIn('pixel_sha256', json.loads((root/'design/art-direction.json').read_text())['images'][0])

    def test_activation_requires_current_official_preflight_receipt(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            with self.assertRaisesRegex(ValueError, 'PREFLIGHT_REQUIRED'):
                require_validation_receipt(root)
            save_json(root/'asset-validation.json', {'status':'ASSETS_VALIDATED','bundle_sha256':'old'})
            with patch('bundle_contract.validation_identity',return_value='new'):
                with self.assertRaisesRegex(ValueError, 'PREFLIGHT_STALE'):
                    require_validation_receipt(root)
            with patch('bundle_contract.validation_identity',return_value='old'):
                require_validation_receipt(root)

    def test_replaced_pixels_and_unsafe_sources_are_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            entry = self.image_bundle(root)
            Image.new('RGB', (8, 8), 'black').save(root/'inputs/scene.png')
            with self.assertRaisesRegex(ValueError, 'sha256 missing or mismatched'):
                reviewed_images(root)
            entry['source'] = '../../outside.png'
            save_json(root/'design/art-direction.json', {'images': [entry]})
            with self.assertRaisesRegex(ValueError, 'unsafe reviewed image'):
                reviewed_images(root)

    def test_duration_modes_cover_short_long_and_conflicting_requests(self):
        for seconds in (15, 30, 220, 7200):
            self.assertEqual(duration_mode({'duration_mode': 'target'}, {}, seconds), 'target')
        self.assertEqual(duration_mode({}, {}, None), 'narration')
        self.assertEqual(duration_mode({'duration_mode': 'narration'}, {}, 30), 'narration')
        for story, request, seconds in [({'duration_mode': 'target'}, {}, None),
            ({'duration_mode': 'target'}, {'duration_mode': 'narration'}, 30)]:
            with self.assertRaisesRegex(ValueError, 'DURATION_MODE_MISMATCH'):
                duration_mode(story, request, seconds)

    def test_failure_retains_exact_stage_and_previous_attempt(self):
        with tempfile.TemporaryDirectory() as folder:
            pipeline = Pipeline(folder)
            pipeline.start('voice')
            pipeline.fail(RuntimeError('HTTP 429'))
            state = json.loads(pipeline.path.read_text())
            self.assertEqual(state['failed_stage'], 'voice')
            self.assertEqual(state['error']['message'], 'HTTP 429')
            retry = Pipeline(folder)
            self.assertEqual(retry.state['previous_attempt']['status'], 'FAILED')
            retry.start('voice'); retry.done(reused=True); retry.finish('VOICE_READY')
            self.assertTrue(retry.state['stages']['voice']['reused'])

    def test_zero_duration_is_not_silently_replaced_by_previous_duration(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            with self.assertRaisesRegex(ValueError, 'positive integer'):
                resolve({'topic': 'duration test', 'seconds': 0}, root)

    def test_command_timeout_is_bounded_and_nonzero_is_failure(self):
        with self.assertRaises(subprocess.TimeoutExpired):
            run_command(sys.executable, '-c', 'import time; time.sleep(20)', timeout=.05)
        with self.assertRaises(subprocess.CalledProcessError):
            run_command(sys.executable, '-c', 'raise SystemExit(7)', timeout=5)

    def test_missing_bun_is_detected_before_image_cleanup(self):
        with patch('shutil.which', side_effect=lambda command: None if command=='bun' else '/bin/'+command), patch('pathlib.Path.is_file', return_value=True):
            with self.assertRaisesRegex(ValueError, 'RUNTIME_REQUIRED: bun'):
                check_runtime()
            check_runtime(voice_only=True)

    def test_failed_verification_invalidates_receipts_but_keeps_voice(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for name in ('prepared-receipt.json', 'render-input.json', 'voice.mp3'):
                (root/name).write_text('existing')
            def failed(args, pipeline):
                pipeline.start('verification')
                raise ValueError('corrupted MP4')
            with patch('produce.main', side_effect=failed):
                with self.assertRaisesRegex(ValueError, 'corrupted MP4'):
                    execute(argparse.Namespace(output=folder))
            self.assertFalse((root/'render-input.json').exists())
            self.assertFalse((root/'prepared-receipt.json').exists())
            self.assertTrue((root/'voice.mp3').exists())

    def test_sync_replaces_authoritative_audio_and_removes_stale_assets(self):
        with tempfile.TemporaryDirectory() as folder:
            bundle, output = Path(folder)/'bundle', Path(folder)/'output'
            for root in (bundle, output):
                for directory in ('style', 'design', 'inputs'):
                    (root/directory).mkdir(parents=True)
            (output/'design/stale.json').write_text('old')
            (output/'inputs/stale.png').write_text('old')
            (output/'inputs/voice-other.mp3').write_text('keep')
            (output/'inputs/voice-same.mp3').write_text('old voice')
            (bundle/'inputs/voice-same.mp3').write_text('authorized new voice')
            sync_inputs(bundle, output)
            self.assertFalse((output/'design/stale.json').exists())
            self.assertFalse((output/'inputs/stale.png').exists())
            self.assertEqual((output/'inputs/voice-other.mp3').read_text(), 'keep')
            self.assertEqual((output/'inputs/voice-same.mp3').read_text(), 'authorized new voice')

    def test_administrative_state_does_not_invalidate_content_cache(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder); bundle=root/'bundle'; bundle.mkdir()
            (root/'handdraw').mkdir(); (root/'smart_voice').mkdir()
            (root/'handdraw/core.py').write_text('pass')
            for name in ('generate_voice.py', 'voices.json'):
                (root/'smart_voice'/name).write_text('{}')
            save_json(bundle/'request.json', {'state': 'PREPARATION_REQUIRED', 'style': '1'})
            first=content_fingerprint(bundle,root,None,False,{'python':'test'})
            save_json(bundle/'request.json', {'state': 'ASSETS_VALIDATED', 'style': '1'})
            save_json(bundle/'preparation-status.json', {'missing': []})
            self.assertEqual(first,content_fingerprint(bundle,root,None,False,{'python':'test'}))
            save_json(bundle/'request.json', {'state': 'ASSETS_VALIDATED', 'style': '17'})
            self.assertNotEqual(first,content_fingerprint(bundle,root,None,False,{'python':'test'}))

if __name__ == '__main__':
    unittest.main()
