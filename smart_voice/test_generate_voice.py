import asyncio
import importlib.util
import json
import subprocess
import tempfile
import unittest
import ssl
from unittest.mock import AsyncMock, patch
import aiohttp
from pathlib import Path

spec = importlib.util.spec_from_file_location('voice', Path(__file__).with_name('generate_voice.py'))
voice = importlib.util.module_from_spec(spec)
spec.loader.exec_module(voice)


class NarrationTests(unittest.TestCase):
    def test_cached_audio_publishes_with_trailing_ffmpeg_log(self):
        # Real audio + real ffmpeg, with network forbidden: exercise synthesis,
        # level validation, subtitles, metadata and atomic publication together.
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            raw = root / 'source.mp3'
            subprocess.run(['ffmpeg', '-y', '-v', 'error', '-f', 'lavfi',
                            '-i', 'sine=frequency=440:duration=2', str(raw)], check=True)
            actual_run = voice.run
            suffixes = ('', '\n[out#0/null @ 0x123] audio:188KiB\n')
            for index, suffix in enumerate(suffixes):
                def logged_run(args):
                    result = actual_run(args)
                    if any('print_format=json' in str(arg) for arg in args):
                        result.stderr += suffix
                    return result
                output = root / f'case-{index}.mp3'
                with patch.object(voice, 'get_chunk', AsyncMock(return_value=(
                        raw, [(0.0, 1.5, '你好。')], 2.0, True))), \
                        patch.object(voice, 'run', side_effect=logged_run), \
                        patch.object(voice.edge_tts, 'Communicate', side_effect=AssertionError('network forbidden')):
                    asyncio.run(voice.synthesize('你好。', str(output), '068'))
                metadata = json.loads(output.with_suffix('.json').read_text())
                self.assertEqual(metadata['status'], 'SUCCESS')
                self.assertEqual(metadata['cache_hits'], 1)
                self.assertIn('你好。', output.with_suffix('.srt').read_text())
                self.assertGreater(output.stat().st_size, 0)
                self.assertEqual(metadata['preset'], voice.VOICES['068'])

    def test_bad_loudness_reports_do_not_publish_audio(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            raw = root / 'source.mp3'
            subprocess.run(['ffmpeg', '-y', '-v', 'error', '-f', 'lavfi',
                            '-i', 'sine=frequency=440:duration=2', str(raw)], check=True)
            actual_run = voice.run
            reports = ('{"input_i": "-11",', '{}',
                       '{"input_i":"-inf","input_tp":"-1"}',
                       '{"input_i":"-30","input_tp":"-1"}',
                       '{"input_i":"-11","input_tp":"0"}')
            for index, report in enumerate(reports):
                def invalid_report(args):
                    result = actual_run(args)
                    if any('print_format=json' in str(arg) for arg in args):
                        result.stderr = report + '\nFFmpeg summary\n'
                    return result
                output = root / f'bad-{index}.mp3'
                with self.subTest(report=report), \
                        patch.object(voice, 'get_chunk', AsyncMock(return_value=(
                            raw, [(0.0, 1.5, '你好。')], 2.0, True))), \
                        patch.object(voice, 'run', side_effect=invalid_report):
                    with self.assertRaises((json.JSONDecodeError, KeyError, RuntimeError)):
                        asyncio.run(voice.synthesize('你好。', str(output), '068'))
                    for suffix in ('.mp3', '.srt', '.json'):
                        self.assertFalse(output.with_suffix(suffix).exists())

    def test_task_rate_reaches_synthesis_without_mutating_068(self):
        original = dict(voice.VOICES['068'])
        probe = AsyncMock(side_effect=RuntimeError('offline synthesis probe'))
        with tempfile.TemporaryDirectory() as directory, patch.object(voice, 'get_chunk', probe):
            with self.assertRaisesRegex(RuntimeError, 'offline synthesis probe'):
                asyncio.run(voice.synthesize('你好。', str(Path(directory) / 'test.mp3'), '068', rate='-27%'))
        self.assertEqual(probe.call_args.args[1]['rate'], '-27%')
        self.assertEqual(probe.call_args.args[1]['voice'], original['voice'])
        self.assertEqual(probe.call_args.args[1]['pitch'], original['pitch'])
        self.assertEqual(voice.VOICES['068'], original)

    def test_invalid_task_rate_rejected_before_network(self):
        with self.assertRaisesRegex(ValueError, 'signed integer'):
            asyncio.run(voice.synthesize('你好。', '/tmp/unused-rate-test.mp3', '068', rate='-27.5%'))

    def test_chunks_preserve_every_character_and_limit(self):
        text = ('這是一段中文旁白。' * 45) + '最後一句不能遺失。'
        chunks = voice.split_text(text)
        self.assertGreater(len(chunks), 1)
        self.assertEqual(''.join(chunks), text)
        self.assertTrue(all(0 < len(c) <= 300 for c in chunks))

    def test_auto_chinese_keeps_068(self):
        self.assertEqual(voice.select_voice('science', 'zh-TW'), '068')

    def test_reject_english_voice_for_chinese_before_output(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory) / 'test.mp3'
            with self.assertRaisesRegex(ValueError, 'English-only'):
                asyncio.run(voice.synthesize('你好', str(out), 'F01'))
            self.assertFalse(out.exists())

    def test_protect_existing_audio(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory) / 'test.mp3'
            out.write_bytes(b'previous artifact')
            with self.assertRaises(FileExistsError):
                asyncio.run(voice.synthesize('你好', str(out), '068'))
            self.assertEqual(out.read_bytes(), b'previous artifact')

    def test_only_transient_failures_retry(self):
        self.assertTrue(voice.retryable(TimeoutError('timeout')))
        self.assertTrue(voice.retryable(ConnectionResetError('reset')))
        self.assertFalse(voice.retryable(ssl.SSLError('certificate')))
        for code in (401, 403, 404):
            self.assertFalse(voice.retryable(aiohttp.ClientResponseError(None, (), status=code)))
        for code in (429, 503):
            self.assertTrue(voice.retryable(aiohttp.ClientResponseError(None, (), status=code)))

    def test_cache_identity_contains_text_and_voice_settings(self):
        preset = voice.VOICES['068']
        key = voice.chunk_key('你好。', preset)
        self.assertNotEqual(key, voice.chunk_key('再見。', preset))
        self.assertNotEqual(key, voice.chunk_key('你好。', dict(preset, rate='+0%')))

    def test_protect_existing_subtitles(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory) / 'test.mp3'
            out.with_suffix('.srt').write_text('existing subtitles')
            with self.assertRaises(FileExistsError):
                asyncio.run(voice.synthesize('你好', str(out), '068'))
            self.assertFalse(out.exists())
            self.assertEqual(out.with_suffix('.srt').read_text(), 'existing subtitles')


if __name__ == '__main__':
    unittest.main()

