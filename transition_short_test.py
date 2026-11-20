"""変遷ショートの顔位置・字幕・結合。モデル生成はしない。"""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

import transition_short as ts


class LabelTest(unittest.TestCase):
    def test_jimin_2013_is_18(self):
        self.assertEqual(ts.age_label(2013, 1995), "2013 18yo")

    def test_prompt_locks_the_camera(self):
        self.assertIn("static locked-off camera", ts.POSITIVE)
        self.assertNotIn("camera tracking", ts.POSITIVE)
        self.assertIn("WanFirstLastFrameToVideo", ts.api_prompt("a.png", "b.png", "yearmorph/2013_2014", 1)["10"]["class_type"])

    def test_api_prompt_uses_both_photos_and_vertical_frame(self):
        prompt = ts.api_prompt("2013.png", "2014.png", "yearmorph/2013_2014", 7)
        flf = prompt["10"]["inputs"]
        self.assertEqual(flf["start_image"], ["6", 0])
        self.assertEqual(flf["end_image"], ["21", 0])
        self.assertEqual(flf["width"], 720)
        self.assertEqual(flf["height"], 1280)
        self.assertEqual(prompt["5"]["inputs"]["image"], "2013.png")
        self.assertEqual(prompt["20"]["inputs"]["image"], "2014.png")
        self.assertNotIn("narration", json.dumps(prompt))


class AlignMathTest(unittest.TestCase):
    def test_matrix_places_face_center_and_size(self):
        face = ts.Face(x=100, y=80, w=40, h=60, eye_y=100)
        # eye_to_chin = (80+60) - 100 = 40
        scale, tx, ty = ts.align_matrix(face)
        center_x = scale * face.center_x + tx
        center_y = scale * face.center_y + ty
        span = scale * face.eye_to_chin
        self.assertAlmostEqual(center_x, ts.FACE_CENTER_X_RATIO * ts.FRAME_W)
        self.assertAlmostEqual(center_y, ts.FACE_CENTER_Y_RATIO * ts.FRAME_H)
        self.assertAlmostEqual(span, ts.FACE_SIZE_RATIO * ts.FRAME_H)


class CaptionTest(unittest.TestCase):
    def test_filter_uses_yellow_and_the_year_label(self):
        text = ts.caption_filters("2013 18yo", "2014 19yo", 2.0)
        self.assertIn("2013 18yo", text)
        self.assertIn("2014 19yo", text)
        self.assertIn("0xE8CB28", text)
        self.assertIn("bordercolor=black", text)
        self.assertIn(f"h*{ts.CAPTION_CENTER_Y_RATIO}", text)

    def test_rendered_caption_sits_in_the_band(self):
        if shutil.which("ffmpeg") is None:
            self.skipTest("ffmpeg がありません")
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "cap.png"
            filt = ts._drawtext("2013 18yo", "1", ts.CAPTION_FONTSIZE, ts.CAPTION_STROKE)
            subprocess.run(
                [
                    "ffmpeg", "-y", "-f", "lavfi",
                    "-i", "color=c=black:s=720x1280:d=0.1:r=10",
                    "-vf", filt,
                    "-frames:v", "1", "-update", "1", str(out),
                ],
                check=True,
                capture_output=True,
            )
            cy = _yellow_centroid_y(out)
            self.assertGreaterEqual(cy, 0.62)
            self.assertLessEqual(cy, 0.65)


class AssembleTest(unittest.TestCase):
    def test_concat_uses_bgm_only_and_keeps_caption_band(self):
        if shutil.which("ffmpeg") is None:
            self.skipTest("ffmpeg がありません")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            aligned = root / "aligned"
            morphs = root / "morphs"
            aligned.mkdir()
            morphs.mkdir()
            photos = []
            for year, age in ((2013, 18), (2014, 19)):
                photos.append({
                    "year": year,
                    "age": age,
                    "label": f"{year} {age}yo",
                    "file": f"{year}.png",
                })
                # 実ファイルは結合では使わない。manifest の年だけ使う。
                (aligned / f"{year}.png").write_bytes(b"")
            (aligned / "manifest.json").write_text(json.dumps({
                "birth_year": 1995,
                "photos": photos,
            }), encoding="utf-8")
            for name in ("2013_2014",):
                _solid_clip(morphs / f"{name}.mp4", 0.4)
            bgm = root / "bgm.wav"
            subprocess.run(
                [
                    "ffmpeg", "-y", "-f", "lavfi",
                    "-i", "sine=frequency=440:duration=3",
                    str(bgm),
                ],
                check=True,
                capture_output=True,
            )
            out = root / "out.mp4"
            ts.assemble_short(morphs, aligned, out, bgm)
            probe = subprocess.run(
                [
                    "ffprobe", "-v", "error",
                    "-show_entries", "format=duration:stream=codec_type",
                    "-of", "json", str(out),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            info = json.loads(probe.stdout)
            kinds = [stream["codec_type"] for stream in info["streams"]]
            self.assertEqual(kinds.count("audio"), 1)
            self.assertAlmostEqual(float(info["format"]["duration"]), 0.4, delta=0.15)
            frame = root / "frame.png"
            subprocess.run(
                ["ffmpeg", "-y", "-i", str(out), "-frames:v", "1", str(frame)],
                check=True,
                capture_output=True,
            )
            cy = _yellow_centroid_y(frame)
            self.assertGreaterEqual(cy, 0.62)
            self.assertLessEqual(cy, 0.65)


class ReferenceFrameTest(unittest.TestCase):
    def test_reference_frame_locks_to_the_spec(self):
        video = Path(
            "/home/ubuntu/.cursor/projects/workspace/uploads/"
            "a1f67ccfa06b48d73c01044e6685b63682314a12985df34bf12fc125cc22823b_8088.mp4"
        )
        if not video.exists():
            self.skipTest("参考動画がこの環境にありません")
        import cv2

        model = Path("/tmp/models/yunet.onnx")
        if not model.exists():
            model = ts.ensure_yunet()
        cap = cv2.VideoCapture(str(video))
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(33 * cap.get(cv2.CAP_PROP_FPS)))
        ok, frame = cap.read()
        cap.release()
        self.assertTrue(ok)
        aligned = ts.align_image(frame, model)
        face = ts.detect_face(aligned, model)
        self.assertIsNotNone(face)
        center = face.center_y / ts.FRAME_H
        size = face.eye_to_chin / ts.FRAME_H
        self.assertAlmostEqual(center, 0.25, delta=0.03)
        self.assertAlmostEqual(size, 0.16, delta=0.03)


def _yellow_centroid_y(path: Path) -> float:
    import cv2
    import numpy as np

    image = cv2.imread(str(path))
    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB).astype(int)
    target = np.array(ts.CAPTION_COLOR_RGB)
    diff = abs(rgb - target)
    mask = (diff[:, :, 0] < 30) & (diff[:, :, 1] < 35) & (diff[:, :, 2] < 35) & (rgb[:, :, 0] > 180)
    ys = mask.nonzero()[0]
    if len(ys) < 20:
        raise AssertionError("黄色い字幕が見つかりません")
    return float(ys.mean()) / image.shape[0]


def _solid_clip(path: Path, seconds: float) -> None:
    subprocess.run(
        [
            "ffmpeg", "-y", "-f", "lavfi",
            "-i", f"color=c=0x222222:s=720x1280:d={seconds}:r=24",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", str(path),
        ],
        check=True,
        capture_output=True,
    )


if __name__ == "__main__":
    unittest.main()
