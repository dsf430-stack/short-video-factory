import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch
import archive_drive as a


class ArchiveTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.film = self.root / 'film.mp4'
        self.film.write_bytes(b'unique-test-content')
        self.sha, self.md5 = a.hashes(self.film)
        self.report = {'status': 'ENGINEERING_PASS', 'sha256': self.sha,
                       'job_id': 'job-new-test', 'voice': '068', 'seconds': 15}
        self.remote = {'id': 'remote-file', 'size': str(self.film.stat().st_size),
                       'md5Checksum': self.md5, 'parents': [a.FOLDER_ID],
                       'appProperties': {'sha256': self.sha}, 'webViewLink': 'https://drive.google.com/file/d/remote-file/view'}
        self.service = MagicMock()
        self.service.files().get().execute.side_effect = [
            {'mimeType': 'application/vnd.google-apps.folder', 'capabilities': {'canAddChildren': True}}, self.remote]

    def test_saved_hash_is_reused_without_create(self):
        self.service.files().list().execute.return_value = {'files': [self.remote]}
        receipt = a.archive(self.service, self.film, self.report, self.sha, self.md5, MagicMock())
        self.assertEqual(receipt['status'], 'ALREADY_SAVED')
        self.service.files().create.assert_not_called()

    def test_upload_is_read_back_and_verified(self):
        self.service.files().list().execute.return_value = {'files': []}
        self.service.files().create().next_chunk.return_value = (None, {'id': 'remote-file'})
        receipt = a.archive(self.service, self.film, self.report, self.sha, self.md5, MagicMock())
        self.assertEqual(receipt['status'], 'SAVED')
        self.service.files().create().next_chunk.assert_called_once_with(num_retries=0)

    def test_uncertain_upload_is_not_repeated(self):
        self.service.files().list().execute.return_value = {'files': []}
        self.service.files().create().next_chunk.side_effect = TimeoutError('response lost')
        with self.assertRaises(TimeoutError):
            a.archive(self.service, self.film, self.report, self.sha, self.md5, MagicMock())
        self.service.files().create().next_chunk.assert_called_once()

    def test_bad_checksum_or_parent_is_rejected(self):
        for change in ({'md5Checksum': 'wrong'}, {'parents': ['other-folder']}, {'size': '0'}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                a.verify_remote({**self.remote, **change}, self.film, self.sha, self.md5)

    def test_duplicate_hash_is_not_uploaded_again(self):
        self.service.files().list().execute.return_value = {'files': [self.remote, self.remote]}
        with self.assertRaises(ValueError):
            a.archive(self.service, self.film, self.report, self.sha, self.md5, MagicMock())
        self.service.files().create.assert_not_called()

    def test_modified_film_fails_before_external_write(self):
        (self.root / 'acceptance.json').write_text(json.dumps(self.report))
        (self.root / 'transcript.srt').write_text('1\n00:00:01,000 --> 00:00:02,000\n測試\n')
        self.film.write_bytes(b'tampered')
        with self.assertRaisesRegex(ValueError, 'passing acceptance'):
            a.validated_film(self.root)


if __name__ == '__main__':
    unittest.main()
