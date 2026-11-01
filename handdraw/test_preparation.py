import json
import tempfile
import unittest
from pathlib import Path
from preparation import resolve_bundle, choose_candidate
class PreparationTests(unittest.TestCase):
 def test_new_topic_persists_request_without_faking_assets(self):
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder);(root/'catalog.json').write_text('{}')
   with self.assertRaisesRegex(ValueError,'PREPARATION_REQUIRED'):resolve_bundle(root,'新題材',30)
   requests=list(root.glob('*/request.json'));self.assertEqual(len(requests),1)
   self.assertEqual(json.loads(requests[0].read_text())['topic'],'新題材')
   self.assertEqual(json.loads(requests[0].read_text())['duration_mode'],'narration')
   self.assertEqual(json.loads((root/'catalog.json').read_text()),{})
 def test_catalog_cannot_escape(self):
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder);(root/'catalog.json').write_text('{"bad":"../escape"}')
   with self.assertRaisesRegex(ValueError,'escapes'):resolve_bundle(root,'bad',30)
 def test_candidate_selection_uses_measured_rate(self):
  self.assertEqual(choose_candidate([['甲'*10],['甲'*20],['甲'*30]],{1:10},15),2)
  self.assertIsNone(choose_candidate([['甲']],{0:10},15))

 def test_new_topic_does_not_inherit_previous_active_duration(self):
  from unittest.mock import patch
  from resolve_job import resolve
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder);(root/'prepared').mkdir()
   (root/'active-job.json').write_text(json.dumps({'job_id':'old-job','topic':'舊影片','seconds':220,'style':'17'}))
   with patch('resolve_job.resolve_bundle',return_value=root/'prepared'/'new-job') as mocked:
    result=resolve({'topic':'新影片'},root=root)
   self.assertEqual(result['topic'],'新影片')
   self.assertEqual(result['seconds'],30)
   mocked.assert_called_once_with(root/'prepared','新影片',30,None,None)
if __name__=='__main__':unittest.main()
