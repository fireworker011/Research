"""ネットワークも音声合成も使わない単体テスト。"""

from __future__ import annotations

import unittest

import numpy as np

from irasutoya_short.audio import mix_tracks
from irasutoya_short.bubbles import render_bubble
from irasutoya_short.lipsync import mouth_envelope
from irasutoya_short.qa import body_count, title_rejection
from irasutoya_short.render import mouth_should_move
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

CAPTION_BRIEF = {
    "format": "caption",
    "hook": "会議の5分前なのに、メモはまだ下書きのままだ",
    "bullets": [
        "同じ文を3回書き直して、まだ一度も送っていない",
        "「もうちょっと整えてから送る」",
        "隣の席は殴り書きの1通で、先に返事をもらっていた",
        "何が違ったのか、その場では分からなかった",
    ],
    "punchline": "遅れた原因は、文章の粗さではなかった。「整えるほど、送れなくなっていた」",
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
        self.assertNotIn("bubble", script["scenes"][0])

    def test_caption_format_keeps_sukatto_path(self) -> None:
        script = generate_script(CAPTION_BRIEF)
        self.assertEqual(script["format"], "caption")
        self.assertGreaterEqual(len(script["scenes"]), 8)
        self.assertLessEqual(len(script["scenes"]), 12)
        roles = [s["role"] for s in script["scenes"]]
        self.assertLess(roles.index("hook"), roles.index("punch"))
        self.assertLess(roles.index("punch"), roles.index("close"))
        kinds = [s["bubble"]["kind"] for s in script["scenes"] if s["role"] != "credit"]
        self.assertIn("caption", kinds)
        self.assertIn("speech", kinds)
        speakers = {s["speaker"] for s in script["scenes"] if s.get("bubble", {}).get("kind") == "speech"}
        self.assertEqual(speakers, {"hero"})
        narr = [s for s in script["scenes"] if s.get("bubble", {}).get("kind") == "caption"]
        self.assertTrue(all(s["speaker"] == "narrator" for s in narr))
        sides = [s["bubble"]["side"] for s in script["scenes"] if "bubble" in s]
        self.assertEqual(sides[0], "right")
        self.assertEqual(sides[1], "left")
        self.assertNotIn("VOICEVOX:剣崎雌雄", script["credits"])
        self.assertIn("VOICEVOX:四国めたん", script["credits"])
        self.assertIn("VOICEVOX:白上虎太郎", script["credits"])
        self.assertLessEqual(len(script["asset_ids"]), 20)
        plain = generate_script(BRIEF)
        self.assertNotIn("format", plain)
        self.assertEqual(len(plain["scenes"]), 14)

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


class BubbleTests(unittest.TestCase):
    def test_caption_sits_on_the_edge_without_a_tail(self) -> None:
        right = render_bubble("会議の前なのに\nメモは下書き", "caption", "right", 1920, 1080, 1.0)
        self.assertEqual(int(right[:, :700, 3].max()), 0)
        self.assertGreater(int(right[:, 1400:, 3].max()), 200)
        left = render_bubble("会議の前なのに\nメモは下書き", "caption", "left", 1920, 1080, 1.0)
        self.assertEqual(int(left[:, 1200:, 3].max()), 0)
        self.assertGreater(int(left[:, :500, 3].max()), 200)

    def test_speech_has_a_narrow_tail(self) -> None:
        img = render_bubble("整えてから送る", "speech", "right", 1920, 1080, 1.0)
        alpha = img[:, :, 3]
        ys = np.where(alpha > 200)[0]
        self.assertGreater(len(ys), 0)
        top, bot = int(ys.min()), int(ys.max())
        mid = int((alpha[top + (bot - top) // 3] > 200).sum())
        tip = int((alpha[bot - 2] > 200).sum())
        self.assertGreater(mid, tip + 8)
        xs = np.where(alpha > 200)[1]
        tip_x = float(np.median(xs[ys > bot - 3]))
        body = xs[ys < bot - 36]
        center = (float(body.min()) + float(body.max())) / 2
        self.assertLess(abs(tip_x - center), 36)

    def test_narration_does_not_move_the_mouth(self) -> None:
        caption = {"speaker": "narrator", "bubble": {"kind": "caption", "side": "right"}}
        self.assertFalse(mouth_should_move(caption, "hero", 0))
        speech = {"speaker": "hero", "bubble": {"kind": "speech", "side": "left"}}
        self.assertTrue(mouth_should_move(speech, "hero", 0))
        self.assertFalse(mouth_should_move(speech, "rival", 1))
        sukatto = {"speaker": "narrator"}
        self.assertTrue(mouth_should_move(sukatto, "hero", 0))


class ReviseTests(unittest.TestCase):
    def test_colloquial(self) -> None:
        project = {"settings": {"speed": 1.2, "hook_speed": 1.4, "telop_scale": 1.0, "sfx_gain": 0.3, "bgm_gain": 0.05, "mouth_gain": 1.0}, "scenes": []}
        changes = apply_note(project, "テンポ悪いな。SEがうるさい")
        self.assertGreater(project["settings"]["speed"], 1.2)
        self.assertLess(project["settings"]["sfx_gain"], 0.3)
        self.assertTrue(any("テンポ" in c for c in changes))


if __name__ == "__main__":
    unittest.main()
