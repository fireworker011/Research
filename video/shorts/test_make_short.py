#!/usr/bin/env python3
"""make_short の台本読みと字幕の秒。映像は作らない。"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from video.shorts.make_short import (
    PROFILES,
    accent_spans,
    adult_marker,
    asset_rows,
    build_cues,
    judge_body,
    Scene,
    parse_script,
    pr_problem,
    render_srt,
    video_filter,
)


SCRIPT = ROOT / "video" / "shorts" / "scripts" / "2026-11-03-婚活-tanomeru-hito.md"


class MakeShortTests(unittest.TestCase):
    def test_adult_marker_ignores_the_word_adult_woman(self) -> None:
        self.assertIsNone(adult_marker("成人女性。顔は映さない。"))
        self.assertEqual(adult_marker("これはヌードです"), "ヌード")

    def test_script_has_four_lines_and_a_silent_tail(self) -> None:
        doc = parse_script(SCRIPT.read_text(encoding="utf-8"))
        self.assertEqual(len(doc.speeches), 4)
        self.assertEqual(doc.speeches[0].text, "友だちに写真頼むの、気まずくて。")
        self.assertTrue(doc.scenes[-1].pr_only)
        self.assertTrue(any(cap.text == "三脚とセルフタイマー" for cap in doc.captions))

    def test_body_over_8_5_seconds_fails_and_names_the_long_line(self) -> None:
        code, rows = judge_body([("長い一文です。", 6.0), ("次も長いです。", 6.0)], 0.2, 0.2)
        self.assertEqual(code, 1)
        self.assertTrue(any(row.startswith("DUR FAIL") and "超え" in row for row in rows))
        self.assertTrue(any(row.startswith("LINE FAIL") and "次も長いです。" in row for row in rows))

    def test_body_inside_8_5_seconds_passes_when_voice_is_at_least_60_percent(self) -> None:
        code, rows = judge_body([("長いめ。", 2.6), ("次も。", 2.6)], 0.2, 0.2)
        self.assertEqual(code, 0)
        self.assertTrue(any(row.startswith("RATIO PASS") for row in rows))
        self.assertTrue(all("FAIL" not in row for row in rows))

    def test_short_voice_fails_the_60_percent_line(self) -> None:
        code, rows = judge_body([("友だちに頼めない。", 1.211), ("撮ってもらった。", 0.845), ("三脚なし。", 0.862)], 0.2, 0.2)
        self.assertEqual(code, 1)
        self.assertTrue(any(row.startswith("RATIO FAIL") and "60%未満" in row for row in rows))
        self.assertTrue(any(row.startswith("DUR PASS") for row in rows))

    def test_accent_phrase_lengths_add_up(self) -> None:
        query = {
            "accent_phrases": [
                {
                    "moras": [
                        {"text": "シャ", "consonant_length": 0.1, "vowel_length": 0.2},
                        {"text": "シン", "consonant_length": 0.1, "vowel_length": 0.3},
                    ],
                    "pause_mora": {"vowel_length": 0.1},
                }
            ]
        }
        spans = accent_spans(query)
        self.assertEqual(len(spans), 1)
        self.assertEqual(spans[0][0], "シャシン")
        self.assertAlmostEqual(spans[0][2], 0.8, places=5)

    def test_missing_box_path_is_an_asset_fail(self) -> None:
        scenes = [Scene(0.0, 4.0, "公園", False)]
        rows = asset_rows(scenes, [{"path": "", "source": {"where": "自作", "id": ""}}])
        self.assertTrue(any(row.startswith("ASSET FAIL") for row in rows))

    def test_konkatsu_pr_is_only_the_last_two_seconds(self) -> None:
        doc = parse_script(SCRIPT.read_text(encoding="utf-8"))
        placed = [
            ("友だちに写真頼むの、気まずくて。", 0.25, 2.2),
            ("撮ってくれる人に頼んだ。", 2.6, 4.2),
            ("外の光で撮った。", 4.6, 6.0),
            ("三脚は、もう持ってこなくていい。", 6.4, 8.2),
        ]
        profile = PROFILES["konkatsu"]
        cues = build_cues(doc, placed, profile)
        self.assertIsNone(pr_problem(cues, profile))
        prs = [cue for cue in cues if cue.pr]
        self.assertEqual(len(prs), 1)
        self.assertEqual(prs[0].start, 8.5)
        self.assertEqual(prs[0].end, 10.5)
        self.assertNotIn("右上", render_srt(cues))
        early = [cue.text for cue in cues if cue.start < 8.5 and "PR" == cue.text]
        self.assertEqual(early, [])
        hook = [cue for cue in cues if cue.hook]
        self.assertEqual(len(hook), 1)
        self.assertEqual(hook[0].start, 0.0)
        self.assertLessEqual(hook[0].end, 1.0)

    def test_filter_does_not_change_speed_and_locks_30fps(self) -> None:
        profile = PROFILES["konkatsu"]
        graph = video_filter(
            [(Path("cut.ppm"), 10.5)],
            [],
            profile,
            "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
            Path("/tmp"),
            8.5,
        )
        self.assertNotIn("atempo", graph)
        self.assertIn("fps=30", graph)
        self.assertIn("gte(t\\,8.500)", graph)

    def test_pet_profile_matches_the_template_checker(self) -> None:
        pet = PROFILES["pet"]
        self.assertEqual(pet.fps, 24)
        self.assertEqual(pet.checker, "template")
        self.assertEqual(pet.captions, "hook")
        self.assertEqual(pet.pr, "tail")
        kane = PROFILES["kane"]
        self.assertTrue(kane.credit)
        self.assertEqual(kane.pr, "none")
        self.assertEqual(PROFILES["yorunotana"].silence_limit, 2.0)
        self.assertEqual(PROFILES["yorunotana"].duration_min, 60.0)


if __name__ == "__main__":
    unittest.main()
