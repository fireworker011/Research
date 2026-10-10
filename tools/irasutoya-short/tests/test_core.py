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

    def test_two_bodies(self) -> None:
        one = np.zeros((80, 80), dtype=np.uint8)
        one[10:70, 30:50] = 255
        self.assertEqual(body_count(one), 1)
        two = np.zeros((80, 120), dtype=np.uint8)
        two[10:70, 5:30] = 255
        two[10:70, 90:115] = 255
        self.assertEqual(body_count(two), 2)


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
