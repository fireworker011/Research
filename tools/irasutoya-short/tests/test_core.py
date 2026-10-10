"""ネットワークも音声合成も使わない単体テスト。"""

from __future__ import annotations

import unittest

import numpy as np

from irasutoya_short.audio import mix_tracks
from irasutoya_short.lipsync import mouth_envelope
from irasutoya_short.qa import body_count, title_rejection
from irasutoya_short.revise import apply_note
from irasutoya_short.scriptgen import generate_script
from irasutoya_short.sfx import make_sfx
from irasutoya_short.sprites import mouth_anchor
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
        self.assertEqual(len(script["scenes"]), 6)
        roles = [s["role"] for s in script["scenes"]]
        self.assertEqual(roles, ["hook", "develop", "develop", "develop", "punch", "credit"])
        self.assertLessEqual(len(script["asset_ids"]), 10)
        hook = script["scenes"][0]
        self.assertEqual(hook["text"], "お前の方が早いだろ")
        self.assertEqual(hook["speaker"], "rival")
        card = script["scenes"][2]
        self.assertNotIn("お前の方が早いだろ", card["text"])
        punch = " ".join(s["text"] for s in script["scenes"] if s["role"] == "punch")
        self.assertIn("全体送信", punch)
        spoken = "\n".join(s["text"] for s in script["scenes"])
        self.assertNotIn("あなたなら", spoken)
        self.assertEqual(script["closing"], "あなたならどうする？")
        self.assertEqual(script["scenes"][-1]["role"], "credit")
        self.assertIn("VOICEVOX:四国めたん", script["scenes"][-1]["telop"])
        hints = [s["duration_hint"] for s in script["scenes"][:5]]
        self.assertEqual(hints, [2.37, 5.53, 0.97, 5.53, 11.05])

    def test_punchline_required(self) -> None:
        bad = dict(BRIEF)
        bad["punchline"] = ""
        with self.assertRaises(ValueError):
            generate_script(bad)

    def test_three_bullets_required(self) -> None:
        bad = dict(BRIEF)
        bad["bullets"] = BRIEF["bullets"][:2]
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


if __name__ == "__main__":
    unittest.main()
