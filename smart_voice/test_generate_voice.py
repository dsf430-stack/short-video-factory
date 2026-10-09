import asyncio
import importlib.util
import tempfile
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location('voice', Path(__file__).with_name('generate_voice.py'))
voice = importlib.util.module_from_spec(spec)
spec.loader.exec_module(voice)


class NarrationTests(unittest.TestCase):
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


if __name__ == '__main__':
    unittest.main()
