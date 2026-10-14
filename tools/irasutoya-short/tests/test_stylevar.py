"""署名の検査と、未公開 47 本の割り当て。"""

from __future__ import annotations

import unittest
from pathlib import Path

import numpy as np

from irasutoya_short import sprites
from irasutoya_short.sfx import bgm_loop
from irasutoya_short.style_draw import PALETTES, build_still, font_path
from irasutoya_short.stylevar import (
    MATRIX,
    assign_unpublished,
    check_signature,
    credit_lines,
    fit_scene_durations,
    kane_published_history,
    length_ok,
    load_jobs,
    parse_signature,
    published_signatures,
    rhythm_ok,
    shared_axes,
)

ROOT = Path(__file__).resolve().parents[3]
STYLE_MD = ROOT / "affiliate-shorts" / "STYLE-VARIATION.md"


class SignatureRuleTests(unittest.TestCase):
    def test_matrix_labels_are_in_the_markdown(self) -> None:
        text = STYLE_MD.read_text(encoding="utf-8")
        for line, axes in MATRIX.items():
            self.assertIn({"kane": "金メモ", "pet": "ペット", "konkatsu": "婚活", "beauty": "美容", "bousai": "防災"}[line], text)
            for codes in axes.values():
                for label in codes.values():
                    self.assertIn(label, text)

    def test_published_are_parsed_and_not_clones_across_lines(self) -> None:
        published = published_signatures()
        self.assertEqual(len(published), 5)
        self.assertEqual(published[0].text(), "kane:C1-P2-T2-F1-H3-M1-B4-L2-A4")
        self.assertLessEqual(shared_axes(published[3], published[0]), 2)
        self.assertLessEqual(shared_axes(published[4], published[0]), 2)

    def test_exact_match_and_prev_and_last5(self) -> None:
        history = kane_published_history()
        clone = parse_signature("kane:C1-P2-T2-F1-H3-M1-B4-L2-A4")
        blocked = check_signature(clone, history)
        self.assertFalse(blocked["ok"])
        self.assertIn("exact", blocked["errors"])
        near = parse_signature("kane:C2-P1-T1-F2-H2-M2-B2-L1-A1")
        near_prev = check_signature(near, [clone])
        self.assertLessEqual(near_prev["shared_prev"], 2)
        crowded = parse_signature("kane:C1-P2-T2-F1-H2-M3-B2-L3-A2")
        self.assertGreater(shared_axes(crowded, clone), 3)
        self.assertFalse(check_signature(crowded, [clone])["ok"])

    def test_last5_allows_three_and_rejects_four(self) -> None:
        older = parse_signature("kane:C3-P3-T3-F3-H3-M3-B3-L3-A3")
        share3 = parse_signature("kane:C3-P3-T3-F4-H4-M4-B4-L4-A4")
        self.assertEqual(shared_axes(share3, older), 3)
        history = [older, older, older, older, parse_signature("kane:C6-P6-T6-F6-H6-M6-B6-L5-A6")]
        # 直前とは C6 側で共有 0。直近5本の最大は 3。公開済みとは別に見る。
        report = check_signature(share3, history, published=[])
        self.assertNotIn("last5", report["errors"])
        self.assertNotIn("prev", report["errors"])
        share4 = parse_signature("kane:C3-P3-T3-F3-H4-M4-B4-L4-A4")
        report4 = check_signature(share4, history, published=[])
        self.assertIn("last5", report4["errors"])

    def test_unpublished_sequence_passes(self) -> None:
        jobs = load_jobs(ROOT)
        signatures = assign_unpublished(jobs)
        self.assertEqual(len(signatures), 47)
        history = kane_published_history()
        published = published_signatures()
        seen = set()
        for job, signature in zip(jobs, signatures):
            report = check_signature(signature, history, published)
            self.assertTrue(report["ok"], f"#{job['video_id']} {signature.text()} {report['errors']}")
            self.assertNotIn(signature.text(), seen)
            seen.add(signature.text())
            history.append(signature)
        self.assertGreaterEqual(len({item.C for item in signatures}), 4)
        self.assertGreaterEqual(len({item.P for item in signatures}), 4)
        self.assertGreaterEqual(len({item.L for item in signatures}), 3)


class DurationFitTests(unittest.TestCase):
    def test_fast_cuts_land_in_l2(self) -> None:
        scenes = []
        for index in range(13):
            scenes.append({"role": "hook" if index == 0 else "body", "voice_seconds": 1.15, "text": "あ", "lead": 0.0})
        scenes.append({"role": "credit", "voice_seconds": 0.15, "text": "", "lead": 0.0})
        project = {"style_axes": {"M": "M1", "L": "L2"}, "scenes": scenes}
        self.assertEqual(fit_scene_durations(project), "ok")
        total = sum(float(scene["duration"]) for scene in scenes)
        self.assertTrue(length_ok(total, "L2"))
        self.assertTrue(rhythm_ok(scenes, "M1"))

    def test_paper_theater_lands_in_l3(self) -> None:
        scenes = []
        for index in range(5):
            scenes.append({"role": "hook" if index == 0 else "body", "voice_seconds": 1.0, "text": "あ", "lead": 0.0})
        scenes.append({"role": "credit", "voice_seconds": 0.15, "text": "", "lead": 0.0})
        project = {"style_axes": {"M": "M6", "L": "L3"}, "scenes": scenes}
        self.assertEqual(fit_scene_durations(project), "ok")
        total = sum(float(scene["duration"]) for scene in scenes)
        self.assertTrue(length_ok(total, "L3"))
        self.assertTrue(rhythm_ok(scenes, "M6"))


class PictureVariationTests(unittest.TestCase):
    def test_palettes_and_layouts_differ(self) -> None:
        book = _GreenBook()
        used: set[str] = set()
        office = build_still(
            {"role": "hook", "telop": "あ"},
            book,
            {"C": "C1", "P": "P2", "T": "T2", "F": "F1", "H": "H3", "M": "M1", "B": "B4", "L": "L2", "A": "A2"},
            ["hero"],
            0,
            4,
            used,
            width=180,
            height=320,
        )
        grid = build_still(
            {"role": "body", "telop": "い"},
            book,
            {"C": "C6", "P": "P6", "T": "T1", "F": "F6", "H": "H1", "M": "M6", "B": "B1", "L": "L5", "A": "A6"},
            ["hero"],
            0,
            4,
            used,
            width=180,
            height=320,
        )
        self.assertFalse(np.array_equal(office, grid))
        self.assertIn("hero", used)
        self.assertEqual(PALETTES["P2"]["wall"], (244, 236, 220))

    def test_fonts_draw_japanese(self) -> None:
        from PIL import Image, ImageDraw

        from irasutoya_short.style_draw import load_font

        for code in ("F1", "F2", "F3", "F4", "F5", "F6"):
            path = font_path(code)
            self.assertTrue(Path(path).is_file(), path)
            font = load_font(path, 48)
            image = Image.new("RGB", (200, 80), (255, 255, 255))
            ImageDraw.Draw(image).text((4, 4), "金", font=font, fill=(0, 0, 0))
            self.assertGreater(int(np.asarray(image).min()), -1)
            self.assertLess(int(np.asarray(image).min()), 250)

    def test_mouth_levels_stay_identical(self) -> None:
        rgba = np.zeros((32, 32, 4), dtype=np.uint8)
        rgba[:, :, 3] = 255
        levels, _anchor = sprites.mouth_levels(rgba)
        self.assertGreater(len(levels), 1)
        for frame in levels[1:]:
            self.assertTrue(np.array_equal(frame, levels[0]))

    def test_bgm_kinds_are_not_the_same_buffer(self) -> None:
        beds = [bgm_loop(2.0, kind) for kind in ("B2", "B3", "B4", "B5", "B6")]
        self.assertTrue(np.allclose(bgm_loop(1.0, "B1"), 0))
        for index, bed in enumerate(beds):
            for other in beds[index + 1 :]:
                self.assertFalse(np.allclose(bed, other))

    def test_credit_adds_irasutoya_and_keeps_speakers(self) -> None:
        project = {
            "scenes": [
                {"role": "hook", "text": "あ", "credit": "VOICEVOX:四国めたん"},
                {"role": "body", "text": "い", "credit": "VOICEVOX:白上虎太郎"},
                {"role": "body", "text": "う", "credit": "VOICEVOX:四国めたん"},
                {"role": "credit", "text": "", "telop": "古い"},
            ]
        }
        lines = credit_lines(project)
        self.assertEqual(lines[0], "VOICEVOX:四国めたん")
        self.assertEqual(lines[1], "VOICEVOX:白上虎太郎")
        self.assertEqual(lines[-1], "イラスト：いらすとや")


class _GreenBook:
    def still(self, asset_id: str, height: int) -> np.ndarray:
        sprite = np.zeros((max(1, height), max(1, height // 2), 4), dtype=np.uint8)
        sprite[:, :, 1] = 180
        sprite[:, :, 3] = 255
        return sprite


if __name__ == "__main__":
    unittest.main()
