"""署名の検査と、未公開 47 本の割り当て。"""

from __future__ import annotations

import subprocess
import unittest
from pathlib import Path

import numpy as np

from irasutoya_short import sprites
from irasutoya_short.sfx import bgm_loop
from irasutoya_short.qa import caption_fit_problems, caption_hits_edge, caption_overlaps_face, dead_air, distinct_stills
from irasutoya_short.textutil import orphan_punctuation_lines, wrap_caption_lines
from irasutoya_short.render import render_telop
from irasutoya_short.style_draw import PALETTES, build_still, font_path, telop_placement
from irasutoya_short.stylevar import (
    MATRIX,
    assign_unpublished,
    check_signature,
    credit_lines,
    fit_scene_durations,
    gaps_ok,
    kane_published_history,
    load_jobs,
    parse_signature,
    published_signatures,
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
    def test_tight_cuts_do_not_pad_a_long_bucket(self) -> None:
        scenes = []
        for index in range(13):
            scenes.append({"role": "hook" if index == 0 else "body", "voice_seconds": 1.15, "text": "あ", "lead": 0.0})
        scenes.append({"role": "credit", "voice_seconds": 0.15, "text": "", "lead": 0.0})
        project = {"style_axes": {"M": "M5", "L": "L5"}, "scenes": scenes}
        status = fit_scene_durations(project)
        self.assertIn(status, ("ok", "retarget", "short"))
        self.assertTrue(gaps_ok(scenes))
        content = [scene for scene in scenes if scene["role"] != "credit"]
        slack = max(float(scene["duration"]) - float(scene["voice_seconds"]) for scene in content)
        self.assertLess(slack, 1.35)
        self.assertLess(float(scenes[-1]["duration"]), 1.35)
        self.assertLess(sum(float(scene["duration"]) for scene in scenes), 25)

    def test_paper_theater_is_not_a_five_second_hold(self) -> None:
        scenes = []
        for index in range(5):
            scenes.append({"role": "hook" if index == 0 else "body", "voice_seconds": 1.0, "text": "あ", "lead": 0.0})
        scenes.append({"role": "credit", "voice_seconds": 0.15, "text": "", "lead": 0.0})
        project = {"style_axes": {"M": "M6", "L": "L3"}, "scenes": scenes}
        fit_scene_durations(project)
        self.assertTrue(gaps_ok(scenes))
        slack = max(float(scene["duration"]) - float(scene["voice_seconds"]) for scene in scenes if scene["role"] != "credit")
        self.assertLess(slack, 1.35)
        self.assertLess(sum(float(scene["duration"]) for scene in scenes), 15)


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


class CaptionAndAirTests(unittest.TestCase):
    def test_caption_stays_off_a_face_and_inside_the_frame(self) -> None:
        axes = {"C": "C1", "P": "P1", "T": "T5", "F": "F1", "H": "H2", "M": "M2", "B": "B2", "L": "L1", "A": "A1"}
        placement = telop_placement(axes, {"role": "body"})
        face = (400, 700, 700, 1100)
        placement["faces"] = [face]
        telop = render_telop("手取りはその残りだった", "body", 1080, 1920, 1.0, 0.5, "body", None, placement)
        self.assertFalse(caption_overlaps_face(telop, [face]))
        self.assertFalse(caption_hits_edge(telop))
        wide = telop_placement(
            {"C": "C5", "P": "P2", "T": "T1", "F": "F5", "H": "H5", "M": "M3", "B": "B2", "L": "L2", "A": "A2"},
            {"role": "body"},
        )
        long = render_telop("源泉徴収票で先に見る欄は天引きの欄だけ見ろ", "body", 1080, 1920, 1.0, 0.5, "body", None, wide)
        self.assertFalse(caption_hits_edge(long, 48))
        self.assertEqual(caption_fit_problems(wide["text_box"], wide["container"], 1080, 1920), [])
        self.assertEqual(orphan_punctuation_lines(wide["wrapped"]), [])

    def test_caption_box_contains_the_glyphs(self) -> None:
        axes = {"C": "C1", "P": "P1", "T": "T1", "F": "F1", "H": "H3", "M": "M1", "B": "B1", "L": "L1", "A": "A2"}
        placement = telop_placement(axes, {"role": "hook"})
        render_telop("ウォーターサーバーあるあ\nる", "hook", 1080, 1920, 1.0, 0.5, "hook", None, placement)
        self.assertEqual(caption_fit_problems(placement["text_box"], placement["container"], 1080, 1920), [])
        self.assertNotIn("、", orphan_punctuation_lines(placement["wrapped"]))
        self.assertFalse(any(len(line.strip()) == 1 for line in placement["wrapped"].split("\n")))
        comma = wrap_caption_lines("第3位、途中でやめにくい", 6, len)
        self.assertEqual(orphan_punctuation_lines("\n".join(comma)), [])
        self.assertTrue(orphan_punctuation_lines("第3位\n、"))

    def test_three_chapters_change_the_picture(self) -> None:
        book = _GreenBook()
        axes = {"C": "C1", "P": "P1", "T": "T1", "F": "F1", "H": "H3", "M": "M1", "B": "B1", "L": "L1", "A": "A2"}
        stills = []
        for index in range(6):
            stills.append(
                build_still(
                    {"role": "body", "telop": "あ"},
                    book,
                    axes,
                    ["hero"],
                    index,
                    6,
                    set(),
                    width=180,
                    height=320,
                )
            )
        self.assertTrue(distinct_stills(stills, 3))

    def test_dead_air_flags_silence_and_a_held_frame(self) -> None:
        frozen = _clip("/tmp/qa-frozen.mp4", moving=False, tone=False, frames=72)
        moving = _clip("/tmp/qa-moving.mp4", moving=True, tone=True, frames=48)
        self.assertTrue(any(item.startswith("silence") for item in dead_air(frozen)))
        self.assertTrue(any(item.startswith("freeze") for item in dead_air(frozen)))
        self.assertEqual(dead_air(moving), [])


def _clip(path: str, *, moving: bool, tone: bool, frames: int) -> str:
    width, height = 160, 160
    base = np.zeros((height, width, 3), dtype=np.uint8)
    base[:, :] = (230, 220, 200)
    base[40:120, 50:110] = (30, 40, 90)
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{width}x{height}", "-r", "24",
        "-i", "pipe:0",
    ]
    if tone:
        cmd.extend(["-f", "lavfi", "-i", "sine=frequency=440:sample_rate=24000:duration=4"])
    else:
        cmd.extend(["-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono"])
    cmd.extend(["-t", f"{frames / 24:.3f}", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", path])
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    assert proc.stdin is not None
    for index in range(frames):
        frame = base
        if moving:
            shift = index // 2
            frame = np.zeros_like(base)
            frame[:, shift:] = base[:, : width - shift]
            frame[:, :shift] = base[:, :1]
        proc.stdin.write(frame.tobytes())
    proc.stdin.close()
    proc.wait(timeout=30)
    return path


class _GreenBook:
    def still(self, asset_id: str, height: int) -> np.ndarray:
        sprite = np.zeros((max(1, height), max(1, height // 2), 4), dtype=np.uint8)
        sprite[:, :, 1] = 180
        sprite[:, :, 3] = 255
        return sprite


if __name__ == "__main__":
    unittest.main()
