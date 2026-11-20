import tempfile
import unittest
from pathlib import Path

from draft_qc_sheet import build_sheet, load_scenes, load_subs, main


SCENES = """| シーン | 開始 | 終了 | 画面 | セリフ | 元音声 |
|---|---|---|---|---|---|
| 1 | 00:00:00.000 | 00:00:02.000 | 猫が窓辺にいる | 夜になった | なし |
| 2 | 00:00:02.000 | 00:00:04.000 | 手元のコップ | もう一杯 | なし |
| 3 | 00:00:05.600 | 00:00:07.000 | 元の映像の海 | ここは静かに | あり |
"""

SRT = """1
00:00:00,000 --> 00:00:02,000
夜になった

2
00:00:02,000 --> 00:00:03,500
もう一杯

3
00:00:05,600 --> 00:00:07,000
波の音だけ
"""


class DraftQcSheetTest(unittest.TestCase):
    def test_gap_match_and_original_audio(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subs = root / "captions.srt"
            scenes = root / "scenes.md"
            subs.write_text(SRT, encoding="utf-8")
            scenes.write_text(SCENES, encoding="utf-8")
            cues = load_subs(subs)
            parsed = load_scenes(scenes)
            sheet = build_sheet(cues, parsed, subs.name, scenes.name)
        self.assertIn("元音声がある素材にナレーションを重ねない", sheet)
        self.assertIn("NG候補: 元音声ありの場面にセリフがある", sheet)
        self.assertIn("セリフと字幕が画面と合う", sheet)
        self.assertIn("体の欠けや崩れたシーンがない", sheet)
        self.assertIn("セリフ間は1.5秒以内", sheet)
        self.assertIn("最初から最後まで通して見る", sheet)
        self.assertIn("NG候補: 1.5秒を超える空きが1箇所", sheet)
        self.assertIn("00:00:03.500 → 00:00:05.600 の空き 2.100秒", sheet)
        self.assertIn("猫が窓辺にいる", sheet)
        self.assertIn("字幕とシーン表のセリフは一致。画面は要目視", sheet)
        self.assertIn("セリフ不一致", sheet)
        self.assertIn("画面に映っているもの", sheet)

    def test_exact_1_5_seconds_is_inside_the_limit(self) -> None:
        srt = """1
00:00:00,000 --> 00:00:01,000
あい

2
00:00:02,500 --> 00:00:03,000
うえ
"""
        scenes = """| 開始 | 終了 | 画面 | セリフ | 元音声 |
|---|---|---|---|---|
| 00:00:00.000 | 00:00:01.000 | 人 | あい | なし |
| 00:00:02.500 | 00:00:03.000 | 人 | うえ | なし |
"""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subs = root / "a.srt"
            scene_path = root / "s.md"
            subs.write_text(srt, encoding="utf-8")
            scene_path.write_text(scenes, encoding="utf-8")
            sheet = build_sheet(load_subs(subs), load_scenes(scene_path), "a.srt", "s.md")
        self.assertIn("下書きOK: 字幕のセリフ間は1.5秒以内", sheet)
        self.assertNotIn("NG候補: 1.5秒を超える", sheet)

    def test_cli_writes_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subs = root / "captions.vtt"
            scenes = root / "scenes.csv"
            out = root / "qc.md"
            subs.write_text(
                "WEBVTT\n\n00:00.000 --> 00:01.000\nこんにちは\n",
                encoding="utf-8",
            )
            scenes.write_text("start,end,visual,line,original_audio\n00:00.000,00:01.000,部屋,こんにちは,なし\n", encoding="utf-8")
            code = main(["--subs", str(subs), "--scenes", str(scenes), "--out", str(out)])
            self.assertEqual(code, 0)
            text = out.read_text(encoding="utf-8")
        self.assertIn("こんにちは", text)
        self.assertIn("部屋", text)
        self.assertIn("字幕とシーン表のセリフは一致", text)


if __name__ == "__main__":
    unittest.main()
