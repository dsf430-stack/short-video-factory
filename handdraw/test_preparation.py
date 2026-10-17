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
   self.assertEqual(json.loads((root/'catalog.json').read_text()),{})
 def test_catalog_cannot_escape(self):
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder);(root/'catalog.json').write_text('{"bad":"../escape"}')
   with self.assertRaisesRegex(ValueError,'escapes'):resolve_bundle(root,'bad',30)
 def test_candidate_selection_uses_measured_rate(self):
  self.assertEqual(choose_candidate([['甲'*10],['甲'*20],['甲'*30]],{1:10},15),2)
  self.assertIsNone(choose_candidate([['甲']],{0:10},15))
if __name__=='__main__':unittest.main()
