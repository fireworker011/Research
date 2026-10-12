"""ネットワークも音声合成も使わない単体テスト。"""

from __future__ import annotations

import io
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np
from PIL import Image

from irasutoya_short.audio import mix_tracks, samples_for_frames, write_wav
from irasutoya_short.picture_first import fit_voice_to_lock, speed_factor
from irasutoya_short.constants import BLOCKED_STYLE_IDS, FPS, SAMPLE_RATE
from irasutoya_short.irasutoya import _download, cache_file, match_score, normalize_entries
from irasutoya_short.lipsync import mouth_envelope
from irasutoya_short.qa import body_count, multiple_faces, title_rejection
from irasutoya_short.render import _bar_radius, render_telop, shift_frame
from irasutoya_short.revise import apply_note
from irasutoya_short.scriptgen import generate_script
from irasutoya_short.sfx import make_sfx
from irasutoya_short.sprites import mouth_anchor
from irasutoya_short import tts
from irasutoya_short.templates import describe_templates, scene_speed, settings_for, telop_style, template_names
from irasutoya_short.textutil import wrap_telop


BRIEF = {
    "hook": "仕事押し付け君を請求書で撃退した話",
    "series_character": "仕事押し付け君",
    "bullets": [
        "金曜の17時、終わってない企画書が俺の机に置かれた",
        "そう言い残して定時で帰っていった「お前の方が早いだろ」",
        "誰もいないオフィスで終電まで3時間かかった",
        "月曜の朝、何事もなかった顔だった",
    ],
    "punchline": "作業ログと請求書を社内チャットに全体送信した。その場で送金して全員の前で頭を下げた",
    "closing": "あなたならどうする？",
}


class ScriptTests(unittest.TestCase):
    def test_shape(self) -> None:
        script = generate_script(BRIEF)
        self.assertGreaterEqual(len(script["scenes"]), 12)
        self.assertLessEqual(len(script["scenes"]), 14)
        roles = [s["role"] for s in script["scenes"]]
        self.assertLess(roles.index("hook"), roles.index("punch"))
        self.assertLess(roles.index("punch"), roles.index("close"))
        self.assertLessEqual(len(script["asset_ids"]), 10)
        hook = script["scenes"][0]
        self.assertIn("\n", hook["telop"])
        punch = " ".join(s["text"] for s in script["scenes"] if s["role"] == "punch")
        self.assertIn("全体送信", punch)
        close = script["scenes"][-2]
        self.assertIn("あなたなら", close["text"])
        self.assertEqual(script["scenes"][-1]["role"], "credit")
        self.assertIn("VOICEVOX:四国めたん", script["scenes"][-1]["telop"])

    def test_line_overrides_replace_canned_office_lines(self) -> None:
        brief = dict(BRIEF)
        brief["template"] = "sukatto"
        brief["lines"] = {
            "hero_refuse": "その契約は、今じゃない",
            "hero_aside": "まだ、数字を見てない",
            "boss_line": "その欄は、何だ",
        }
        script = generate_script(brief)
        blob = " ".join(scene["text"] for scene in script["scenes"])
        self.assertIn("その契約は、今じゃない", blob)
        self.assertIn("まだ、数字を見てない", blob)
        self.assertIn("その欄は、何だ", blob)
        self.assertNotIn("俺の仕事じゃねえだろ", blob)
        self.assertNotIn("どういうことだ", blob)

    def test_aruaru_list_voice_reads_each_item(self) -> None:
        brief = dict(BRIEF)
        brief["template"] = "aruaru"
        brief["item_voice"] = "list"
        brief["bullets"] = [
            "写真が、三年前のまま",
            "会う日に、残業が入る",
            "店を、相手に任せない",
            "既読のまま、終電で寝る",
            "趣味欄が、食べること",
            "翌朝、会社のチャットが先",
        ]
        script = generate_script(brief)
        items = [scene["text"] for scene in script["scenes"] if scene.get("tone") == "item"]
        self.assertIn("写真が、三年前のまま", items)
        self.assertIn("翌朝、会社のチャットが先", items)

    def test_punchline_required(self) -> None:
        bad = dict(BRIEF)
        bad["punchline"] = ""
        with self.assertRaises(ValueError):
            generate_script(bad)

    def test_wrap_breaks_on_particle(self) -> None:
        telop = wrap_telop("仕事押し付け君を請求書で撃退した話", 12, 2)
        self.assertIn("\n", telop)
        self.assertLessEqual(max(len(line) for line in telop.split("\n")), 12)


class QaTests(unittest.TestCase):
    def test_title_filters(self) -> None:
        self.assertIsNotNone(title_rejection("正月の鏡餅", "", ""))
        self.assertIsNotNone(title_rejection("話す二人", "男女", "男性"))
        self.assertIsNone(title_rejection("困るサラリーマン", "男性", "男性"))

    def test_multiple_faces_rejects_side_by_side(self) -> None:
        solo = np.zeros((200, 160, 4), dtype=np.uint8)
        yy, xx = np.ogrid[:200, :160]
        face = ((yy - 70) ** 2) / 40**2 + ((xx - 80) ** 2) / 36**2 <= 1
        solo[face, 0] = 230
        solo[face, 1] = 180
        solo[face, 2] = 150
        solo[face, 3] = 255
        self.assertFalse(multiple_faces(solo))
        pair = np.zeros((200, 320, 4), dtype=np.uint8)
        py, px = np.ogrid[:200, :320]
        for cx in (80, 240):
            blob = ((py - 70) ** 2) / 40**2 + ((px - cx) ** 2) / 36**2 <= 1
            pair[blob, 0] = 230
            pair[blob, 1] = 180
            pair[blob, 2] = 150
            pair[blob, 3] = 255
        self.assertTrue(multiple_faces(pair))
        self.assertIsNotNone(title_rejection("怒る上司の三段階", "", "男性"))

    def test_two_bodies(self) -> None:
        one = np.zeros((80, 80), dtype=np.uint8)
        one[10:70, 30:50] = 255
        self.assertEqual(body_count(one), 1)
        two = np.zeros((80, 120), dtype=np.uint8)
        two[10:70, 5:30] = 255
        two[10:70, 90:115] = 255
        self.assertEqual(body_count(two), 2)
        arm = np.zeros((100, 140), dtype=np.uint8)
        arm[8:90, 50:90] = 255
        arm[40:90, 8:30] = 255
        self.assertEqual(body_count(arm), 1)


class MouthTests(unittest.TestCase):
    def test_anchor_hits_mouth_not_collar(self) -> None:
        img = np.zeros((280, 180, 4), dtype=np.uint8)
        yy, xx = np.ogrid[:280, :180]
        head = ((yy - 90) ** 2) / 70**2 + ((xx - 90) ** 2) / 58**2 <= 1
        neck = (yy > 150) & (yy < 210) & (xx > 70) & (xx < 110)
        skin = head | neck
        img[skin, 0] = 230
        img[skin, 1] = 190
        img[skin, 2] = 160
        img[skin, 3] = 255
        img[70:82, 62:78] = (20, 20, 20, 255)
        img[70:82, 102:118] = (20, 20, 20, 255)
        img[108:114, 84:96] = (30, 20, 20, 255)
        img[132:140, 74:106] = (40, 20, 20, 255)
        img[188:206, 40:140] = (30, 30, 30, 255)
        anchor = mouth_anchor(img)
        self.assertIsNotNone(anchor)
        assert anchor is not None
        self.assertGreater(anchor.y, 125)
        self.assertLess(anchor.y, 148)
        self.assertGreater(anchor.x, 70)
        self.assertLess(anchor.x, 110)

    def test_anchor_prefers_mouth_over_chin_crease(self) -> None:
        img = np.zeros((280, 180, 4), dtype=np.uint8)
        yy, xx = np.ogrid[:280, :180]
        head = ((yy - 90) ** 2) / 70**2 + ((xx - 90) ** 2) / 58**2 <= 1
        neck = (yy > 150) & (yy < 210) & (xx > 70) & (xx < 110)
        skin = head | neck
        img[skin, 0] = 230
        img[skin, 1] = 190
        img[skin, 2] = 160
        img[skin, 3] = 255
        img[70:82, 62:78] = (20, 20, 20, 255)
        img[70:82, 102:118] = (20, 20, 20, 255)
        img[108:114, 84:96] = (30, 20, 20, 255)
        img[132:140, 74:106] = (40, 20, 20, 255)
        img[156:161, 78:108] = (20, 10, 10, 255)
        img[188:206, 40:140] = (30, 30, 30, 255)
        anchor = mouth_anchor(img)
        self.assertIsNotNone(anchor)
        assert anchor is not None
        self.assertGreater(anchor.y, 125)
        self.assertLess(anchor.y, 148)


class AudioTests(unittest.TestCase):
    def test_mouth_follows_loudness(self) -> None:
        sr = 24000
        samples = np.zeros(sr, dtype=np.float32)
        samples[2000:6000] = 0.6
        env = mouth_envelope(samples, nframes=24, sr=sr, fps=24)
        self.assertEqual(len(env), 24)
        self.assertGreater(float(env[4:8].max()), float(env[:2].max()))
        self.assertTrue(np.all(env >= 0))
        self.assertTrue(np.all(env <= 1))

    def test_sfx_sits_under_voice(self) -> None:
        voice = np.zeros(8000, dtype=np.float32)
        voice[1000:3000] = 0.4
        sfx = make_sfx("notify")
        assert sfx is not None
        mixed = mix_tracks(voice, sfx, 0.22, None, 0.0)
        self.assertGreater(float(np.max(np.abs(mixed[: len(sfx)]))), float(np.max(np.abs(voice[: len(sfx)]))))
        self.assertLess(float(np.max(np.abs(mixed))), 1.05)


class ReviseTests(unittest.TestCase):
    def test_colloquial(self) -> None:
        project = {"settings": {"speed": 1.2, "hook_speed": 1.4, "telop_scale": 1.0, "sfx_gain": 0.3, "bgm_gain": 0.05, "mouth_gain": 1.0}, "scenes": []}
        changes = apply_note(project, "テンポ悪いな。SEがうるさい")
        self.assertGreater(project["settings"]["speed"], 1.2)
        self.assertLess(project["settings"]["sfx_gain"], 0.3)
        self.assertTrue(any("テンポ" in c for c in changes))

    def test_tempo_scales_role_speed(self) -> None:
        project = {"settings": settings_for("ranking"), "scenes": []}
        before = project["settings"]["role_speed"]["punch"]
        apply_note(project, "テンポ悪いな")
        self.assertGreater(project["settings"]["role_speed"]["punch"], before)
        self.assertGreater(project["settings"]["hook_speed"], 1.55)


class TemplateTests(unittest.TestCase):
    def test_each_template(self) -> None:
        sfx_rows = []
        speed_rows = []
        looks = []
        for name in template_names():
            brief = dict(BRIEF)
            brief["template"] = name
            script = generate_script(brief)
            scenes = script["scenes"]
            self.assertEqual(script["template"], name)
            self.assertGreaterEqual(len(scenes), 12)
            self.assertLessEqual(len(scenes), 14)
            self.assertLessEqual(len(script["asset_ids"]), 20)
            self.assertLessEqual(len(script["asset_ids"]), 10)
            roles = [scene["role"] for scene in scenes]
            self.assertLess(roles.index("hook"), roles.index("punch"))
            self.assertLess(roles.index("punch"), roles.index("close"))
            self.assertEqual(scenes[-1]["role"], "credit")
            punch = " ".join(scene["text"] for scene in scenes if scene["role"] == "punch")
            self.assertIn("作業ログと請求書", punch)
            close = " ".join(scene["text"] for scene in scenes if scene["role"] == "close")
            self.assertIn("あなたなら", close)
            used: list[str] = []
            for scene in scenes:
                if scene["role"] == "credit":
                    continue
                self.assertNotIn(scene["style_id"], BLOCKED_STYLE_IDS)
                if scene["sfx"] == "none":
                    self.assertIsNone(make_sfx(scene["sfx"]))
                else:
                    self.assertIsNotNone(make_sfx(scene["sfx"]))
                credit = scene["credit"]
                self.assertTrue(credit.startswith("VOICEVOX:"))
                self.assertNotIn("青山", credit)
                if credit not in used:
                    used.append(credit)
            self.assertEqual(script["credits"], used)
            self.assertEqual(scenes[-1]["telop"], "\n".join(used))
            self.assertIn("VOICEVOX:四国めたん", scenes[-1]["telop"])
            self.assertIn("VOICEVOX:白上虎太郎", scenes[-1]["telop"])
            self.assertIn("VOICEVOX:玄野武宏", scenes[-1]["telop"])
            self.assertIn("VOICEVOX:剣崎雌雄", scenes[-1]["telop"])
            sfx_rows.append(tuple(scene["sfx"] for scene in scenes))
            speed_rows.append(tuple(sorted(settings_for(name)["role_speed"].items())))
            style = telop_style(name)
            looks.append(
                (
                    style["bar"],
                    style["stroke"],
                    style["size"],
                    style["slide"],
                    style["y_ratio"],
                    tuple(sorted(style["colors"].items())),
                )
            )
        self.assertEqual(len(set(sfx_rows)), len(template_names()))
        self.assertEqual(len(set(speed_rows)), len(template_names()))
        self.assertEqual(len(set(looks)), len(template_names()))

    def test_template_signatures(self) -> None:
        before = generate_script({**BRIEF, "template": "before_after"})
        tones = {scene.get("tone") for scene in before["scenes"]}
        self.assertIn("before", tones)
        self.assertIn("after", tones)
        aruaru = generate_script({**BRIEF, "template": "aruaru"})
        self.assertGreaterEqual(sum(1 for scene in aruaru["scenes"] if scene.get("tone") == "item"), 5)
        ranking = generate_script({**BRIEF, "template": "ranking"})
        blob = " ".join(scene["text"] for scene in ranking["scenes"])
        self.assertIn("第3位", blob)
        self.assertIn("第1位", blob)
        qa = generate_script({**BRIEF, "template": "qa"})
        self.assertIn("？", qa["scenes"][0]["text"])
        self.assertIn("答えは", " ".join(scene["text"] for scene in qa["scenes"] if scene["role"] == "punch"))

    def test_unknown_template(self) -> None:
        bad = dict(BRIEF)
        bad["template"] = "movie"
        with self.assertRaises(ValueError):
            generate_script(bad)

    def test_default_is_sukatto_pace(self) -> None:
        settings = settings_for("sukatto")
        self.assertEqual(settings["speed"], 1.28)
        self.assertEqual(settings["hook_speed"], 1.48)
        self.assertEqual(settings["sfx_gain"], 0.22)
        self.assertEqual(generate_script(BRIEF)["template"], "sukatto")
        labels = {row["id"]: row["label"] for row in describe_templates()}
        self.assertEqual(labels["before_after"], "ビフォーアフター")
        self.assertEqual(labels["aruaru"], "あるある列挙")
        self.assertEqual(labels["ranking"], "ランキング")
        self.assertEqual(labels["qa"], "問いかけ→答え")
        self.assertEqual(scene_speed(settings, {"role": "hook"}), 1.48)
        self.assertEqual(scene_speed(settings, {"role": "punch"}), 1.28)

    def test_telop_look_changes_pixels(self) -> None:
        left = render_telop("第1位", "punch", 480, 280, 1.0, 0.55, tone="punch", style=telop_style("sukatto"))
        right = render_telop("第1位", "punch", 480, 280, 1.0, 0.55, tone="rank", style=telop_style("ranking"))
        self.assertFalse(np.array_equal(left, right))
        self.assertEqual(_bar_radius("round", 80), 22)
        self.assertEqual(_bar_radius("square", 80), 4)
        self.assertEqual(_bar_radius("pill", 80), 40)
        with self.assertRaises(ValueError):
            _bar_radius("blob", 80)


class RuntimeTests(unittest.TestCase):
    def test_missing_voicevox_does_not_raise(self) -> None:
        if tts.Onnxruntime is None:
            self.assertFalse(tts.runtime_ready())
        else:
            self.assertIsInstance(tts.runtime_ready(), bool)


class ExportTests(unittest.TestCase):
    def test_audio_matches_frames(self) -> None:
        self.assertEqual(samples_for_frames(FPS), SAMPLE_RATE)
        self.assertEqual(samples_for_frames(6), SAMPLE_RATE // FPS * 6)

    def test_shift_does_not_wrap(self) -> None:
        frame = np.zeros((30, 40, 3), dtype=np.uint8)
        frame[:, :] = (10, 10, 10)
        frame[0, 0] = (255, 0, 0)
        frame[-1, -1] = (0, 0, 255)
        moved = shift_frame(frame, dx=4, dy=0)
        self.assertEqual(tuple(int(v) for v in moved[0, 4]), (255, 0, 0))
        self.assertEqual(tuple(int(v) for v in moved[-1, -1]), (10, 10, 10))
        self.assertFalse(np.array_equal(moved[0, 0], np.array([0, 0, 255], dtype=np.uint8)))


class AssetPickTests(unittest.TestCase):
    def test_match_score_needs_a_needle(self) -> None:
        self.assertGreater(match_score("困るサラリーマン", "男性", ["困", "サラリー"], "男性"), 0)
        self.assertEqual(match_score("空の写真", "青空", ["困"], "男性"), 0)
        self.assertLess(match_score("正月の鏡餅", "", ["困"], ""), 0)

    def test_entry_shapes(self) -> None:
        self.assertEqual(normalize_entries(None), [])
        self.assertEqual(len(normalize_entries({"title": "one"})), 1)
        self.assertEqual(len(normalize_entries([{"title": "a"}, {"title": "b"}])), 2)

    def test_cache_skips_network(self) -> None:
        root = Path(tempfile.mkdtemp())
        url = "https://example.invalid/sprite.png"
        buf = io.BytesIO()
        Image.new("RGBA", (16, 16), (1, 2, 3, 255)).save(buf, format="PNG")
        data = buf.getvalue()
        cached = cache_file(url, root)
        cached.parent.mkdir(parents=True, exist_ok=True)
        cached.write_bytes(data)
        dest = root / "out.png"
        _download(url, dest, cache_root=root)
        self.assertEqual(dest.read_bytes(), data)


class PictureFirstTests(unittest.TestCase):
    def test_speed_factor_stays_in_range(self) -> None:
        self.assertEqual(speed_factor(100, 100), 1.0)
        self.assertEqual(speed_factor(200, 100), 1.1)
        self.assertEqual(speed_factor(50, 100), 0.9)
        self.assertEqual(speed_factor(0, 100), 1.0)

    def test_voice_fit_does_not_recut_pictures(self) -> None:
        env = np.array([0.4, 0.9, 0.2, 0.0], dtype=np.float32)
        root = Path(tempfile.mkdtemp())
        wav = root / "scene_01.wav"
        voice = np.ones(48000, dtype=np.float32) * 0.2
        write_wav(wav, voice)
        scene = {
            "id": 1,
            "text": "試し",
            "style_id": 2,
            "role": "hook",
            "duration": 2.0,
            "voice_path": str(wav),
            "_voice": voice,
            "envelope": env.copy(),
        }
        locks = {1: {"duration": 2.0, "envelope": env.copy(), "voice_samples": 24000}}
        project = {
            "settings": {"speed": 1.0, "hook_speed": 1.0, "role_speed": {"hook": 1.0}},
            "scenes": [scene],
        }

        class _Speaker:
            def speak(self, text: str, style_id: int, speed: float) -> np.ndarray:
                return np.ones(int(48000 / speed), dtype=np.float32) * 0.2

        fit_voice_to_lock(project, _Speaker(), root, locks)
        self.assertEqual(scene["duration"], 2.0)
        self.assertEqual(scene["voice_rate_factor"], 1.1)
        self.assertTrue(np.array_equal(scene["envelope"], env))
        self.assertGreater(scene["voice_pause_sec"], 0)
        self.assertEqual(len(scene["_voice"]), samples_for_frames(int(round(2.0 * FPS))))


class BatchBriefTests(unittest.TestCase):
    def test_batch2_and_batch3_scripts(self) -> None:
        root = Path(__file__).resolve().parents[3] / "affiliate-shorts"
        folders = list((root / "batch2").glob("*/brief.json")) + list((root / "batch3").glob("*/brief.json"))
        self.assertGreaterEqual(len(folders), 22)
        for path in folders:
            brief = json.loads(path.read_text(encoding="utf-8"))
            script = generate_script(brief)
            self.assertGreaterEqual(len(script["scenes"]), 12)
            self.assertLessEqual(len(script["scenes"]), 14)
            self.assertTrue(script["credits"])


if __name__ == "__main__":
    unittest.main()
