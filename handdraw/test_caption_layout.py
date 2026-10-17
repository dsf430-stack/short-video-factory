import unittest
from caption_layout import choose_caption_width, wrap_lines, caption_bottom_margin


class CaptionLayoutTests(unittest.TestCase):
    def test_observed_question_mark_orphan_and_other_sentence_endings(self):
        texts = ['白天抬頭看到月亮，難道它忘記下班了嗎？',
                 '但不是每天都明顯，觀察時別直視太陽。',
                 '有時太陽和月亮，會一起出現在地平線上方。',
                 '我們看見月亮，是因為它把照到表面的太陽光，反射進我們眼裡。']
        measure = lambda text: len(text) * 52
        self.assertEqual(wrap_lines(texts[0], measure, 952)[-1], '？')
        ratio = choose_caption_width(texts, measure)
        for text in texts:
            rows = wrap_lines(text, measure, int(1080 * ratio) - 20)
            self.assertEqual(''.join(rows), text)
            self.assertLessEqual(len(rows), 2)
            self.assertTrue(all(row[0] not in '，。？' for row in rows))

    def test_overlong_subtitles_fail_before_rendering_instead_of_losing_text(self):
        with self.assertRaisesRegex(ValueError, 'CAPTION_LAYOUT_REQUIRED'):
            choose_caption_width(['長' * 80], lambda text: len(text) * 52)

    def test_two_line_caption_clears_final_scene_annotation(self):
        bottom, height = 1588.2, 122
        margin = caption_bottom_margin(bottom, height)
        self.assertGreaterEqual(1920 - margin - height - bottom, 48)
        self.assertGreaterEqual(margin, 120)
        self.assertEqual(caption_bottom_margin(1300, height), 210)
        with self.assertRaisesRegex(ValueError, 'CAPTION_LAYOUT_REQUIRED'):
            caption_bottom_margin(1780, height)
