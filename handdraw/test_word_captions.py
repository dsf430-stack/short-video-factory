import unittest
from produce import align_scenes, normalize


class WordCaptionTests(unittest.TestCase):
    def test_groups_long_text_at_provider_word_boundaries(self):
        text = '皇太極重用漢人官員，建立制度並強調滿語騎射，這段完整長句不能因字幕限制而刪除。'
        words = [c for c in text if c.isalnum()]
        events = [{'text': c, 'start': i * .19, 'end': i * .19 + .15}
                  for i, c in enumerate(words)]
        result = align_scenes([{'id': 'test', 'text': text}], events, word_events=True)[0]
        cues = result['caption_cues']
        self.assertEqual(''.join(c['text'] for c in cues), text)
        self.assertTrue(all(len(normalize(c['text'])) <= 24 for c in cues))
        starts = {round(e['start'], 6) for e in events}
        ends = {round(e['end'], 6) for e in events}
        self.assertTrue(all(round(c['start'] + result['start'], 6) in starts for c in cues))
        self.assertTrue(all(round(c['end'] + result['start'], 6) in ends for c in cues))
