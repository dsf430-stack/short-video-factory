import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from preparation import create_request, job_identity, resolve_bundle, REQUIRED, save_json
from produce import align_scenes
from voice_cache import valid_voice_cache, invalidate_voice_cache, valid_subtitles
from resolve_job import resolve

class JobResolutionTests(unittest.TestCase):
 def ready(self, root, identity, script='新內容。', seconds=30):
  b=create_request(root,'同名題材',seconds,'4',script,identity)
  for name in REQUIRED:
   p=b/name;p.parent.mkdir(parents=True,exist_ok=True)
   if not p.exists():p.write_text('{}')
  save_json(b/'story.json',{'topic':'同名題材','scenes':[{'id':'opening','text':script,'source':'inputs/scene.png','parts':[{'id':'object'}]}]})
  save_json(b/'style/resolved.json',{'catalog_id':'4'})
  (b/'inputs/scene.png').write_bytes(b'fixture')
  return b
 def test_script_and_duration_get_distinct_requests(self):
  self.assertNotEqual(job_identity('題材',30,'4','甲'),job_identity('題材',30,'4','乙'))
  self.assertNotEqual(job_identity('題材',30),job_identity('題材',40))
 def test_unindexed_bundle_and_explicit_version(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);a=self.ready(root,'revision-a');self.ready(root,'revision-b','另一稿。')
   self.assertEqual(resolve_bundle(root,'同名題材',30,'revision-a','4'),a)
   with self.assertRaisesRegex(ValueError,'AMBIGUOUS_TOPIC'):resolve_bundle(root,'同名題材',30)
 def test_exact_settings_and_script_are_not_silently_changed(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);self.ready(root,'revision-a')
   with self.assertRaisesRegex(ValueError,'SETTINGS_MISMATCH'):resolve_bundle(root,'同名題材',40,'revision-a')
   with self.assertRaisesRegex(ValueError,'SCRIPT_MISMATCH'):create_request(root,'同名題材',30,'4','改稿','revision-a')
 def test_alignment_preserves_generic_scene_ids(self):
  b=align_scenes([{'id':'opening','text':'月亮。'}],[{'text':'月亮。','start':.05,'end':1.5}])
  self.assertEqual(b[0]['id'],'opening');self.assertEqual(b[0]['start'],.05)
 def test_incomplete_voice_cache_can_be_rebuilt_without_touching_other_voices(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'voice-a.mp3';p.write_bytes(b'audio');(Path(d)/'voice-b.mp3').write_bytes(b'keep')
   preset={'voice':'zh-TW-HsiaoChenNeural','rate':'+20%','pitch':'+5Hz','volume':'+0%'}
   save_json(p.with_suffix('.json'),{'voice_id':'068','text_sha256':'text','sha256':hashlib.sha256(b'audio').hexdigest(),'preset':preset})
   self.assertFalse(valid_voice_cache(p,'text',preset))
   p.with_suffix('.srt').write_text('1\n00:00:00,000 --> 00:00:01,000\n甲\n')
   self.assertTrue(valid_voice_cache(p,'text',preset))
   self.assertFalse(valid_voice_cache(p,'text',{**preset,'rate':'+0%'}))
   invalidate_voice_cache(p);self.assertTrue((Path(d)/'voice-b.mp3').exists())
 def test_wrong_or_invalid_subtitle_cache_is_not_reused(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'voice.srt';p.write_text('1\n00:00:00,000 --> 00:00:01,000\n舊稿。\n')
   self.assertFalse(valid_subtitles(p,'新稿。'))
   p.write_text('not an SRT');self.assertFalse(valid_subtitles(p))
 def test_active_job_carries_duration_and_isolated_output(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);b=self.ready(root/'prepared','ready-job',seconds=40)
   save_json(root/'active-job.json',{'job_id':b.name,'topic':'同名題材','seconds':40,'style':'4'})
   job=resolve({},root);self.assertEqual(job['seconds'],40)
   self.assertTrue(job['root'].startswith('handdraw/output/'))
   with self.assertRaisesRegex(ValueError,'escapes'):resolve({'job_id':'../other'},root)
 def test_speech_can_be_measured_before_images_but_full_render_cannot(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);b=create_request(root,'新腳本',30,job_id='new-script')
   save_json(b/'story.json',{'topic':'新腳本','scenes':[{'id':'intro','text':'先完成旁白。'}]})
   self.assertEqual(resolve_bundle(root,'新腳本',30,'new-script',voice_only=True),b)
   with self.assertRaisesRegex(ValueError,'PREPARATION_REQUIRED'):resolve_bundle(root,'新腳本',30,'new-script')
if __name__=='__main__':unittest.main()
