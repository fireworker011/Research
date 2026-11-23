#!/usr/bin/env python3
"""split → finish → qc が PASS になることと、オプションの尺が崩れないことを確かめる。"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import cv2

import make_fixtures

ROOT = Path(__file__).resolve().parent.parent
TESTS = Path(__file__).resolve().parent
PY = sys.executable


def run_tool(script: str, *args: object, check: bool = True) -> subprocess.CompletedProcess[str]:
    cmd = [PY, str(ROOT / script), *(str(arg) for arg in args)]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if check and proc.returncode != 0:
        raise AssertionError(f"{script} failed\n{proc.stdout}\n{proc.stderr}")
    return proc


def probe(path: Path) -> dict:
    proc = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-count_frames",
            "-show_entries",
            "stream=codec_type,codec_name,width,height,pix_fmt,r_frame_rate,nb_read_frames",
            "-of",
            "json",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    streams = json.loads(proc.stdout)["streams"]
    video = next(stream for stream in streams if stream.get("codec_type") == "video")
    video["has_audio"] = any(stream.get("codec_type") == "audio" for stream in streams)
    video["frame_count"] = int(video["nb_read_frames"])
    return video


def frame_at(path: Path, index: int):
    cap = cv2.VideoCapture(str(path))
    frame = None
    seen = 0
    while seen <= index:
        ok, frame = cap.read()
        if not ok:
            frame = None
            break
        seen += 1
    cap.release()
    if frame is None:
        raise AssertionError(f"frame {index} missing in {path}")
    return frame


def means(frame):
    blue, green, red = frame.mean(axis=(0, 1))
    return float(blue), float(green), float(red)


class KanzenSaigenTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        make_fixtures.main()
        cls.tmp = tempfile.TemporaryDirectory()
        cls.td = Path(cls.tmp.name)
        cls.split = cls.td / "split"
        run_tool("split_ref.py", TESTS / "ref_3cut.mp4", cls.split)
        cls.timeline = cls.split / "timeline.json"
        cls.out = cls.td / "out.mp4"
        run_tool(
            "finish.py",
            cls.timeline,
            TESTS / "gen",
            cls.out,
            "--fps",
            "30",
            "--audio",
            TESTS / "audio.wav",
        )
        cls.qc = run_tool("qc.py", cls.timeline, cls.out, check=False)
        cls.qc_text = (cls.td / "QC.md").read_text(encoding="utf-8")
        cls.contact_png = cls.td / "main-contact.png"
        shutil.copyfile(cls.td / "contact.png", cls.contact_png)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.tmp.cleanup()

    def test_split_writes_timeline_and_pngs(self) -> None:
        data = json.loads(self.timeline.read_text(encoding="utf-8"))
        self.assertEqual(data["scene_threshold"], 27)
        self.assertEqual([cut["frame_count"] for cut in data["cuts"]], [60, 45, 60])
        self.assertAlmostEqual(data["duration_sec"], 5.5, places=3)
        self.assertAlmostEqual(data["cuts"][0]["start_sec"], 0.0, places=3)
        self.assertAlmostEqual(data["cuts"][-1]["end_sec"], 5.5, places=3)
        for cut in data["cuts"]:
            self.assertGreaterEqual(cut["peak_frame"], 0)
            self.assertLess(cut["peak_frame"], cut["frame_count"])
            self.assertAlmostEqual(cut["peak_sec"], cut["peak_frame"] / 30, places=3)
            for key in ("file", "start_png", "peak_png", "end_png"):
                path = self.split / cut[key]
                self.assertTrue(path.is_file(), path)
                self.assertGreater(path.stat().st_size, 500)
            image = cv2.imread(str(self.split / cut["start_png"]))
            self.assertIsNotNone(image)
            self.assertEqual(image.shape[0], 1920)
            self.assertEqual(image.shape[1], 1080)

    def test_finish_qc_pass(self) -> None:
        self.assertEqual(self.qc.returncode, 0, self.qc.stdout + self.qc.stderr)
        lines = [line for line in self.qc_text.splitlines() if line.strip()]
        self.assertEqual(lines[0], "PASS", self.qc_text)
        self.assertEqual(len(lines), 2, self.qc_text)
        info = probe(self.out)
        self.assertEqual(info["codec_name"], "h264")
        self.assertEqual(info["pix_fmt"], "yuv420p")
        self.assertEqual(info["width"], 1080)
        self.assertEqual(info["height"], 1920)
        self.assertEqual(info["r_frame_rate"], "30/1")
        self.assertEqual(info["frame_count"], 165)
        self.assertTrue(info["has_audio"])
        contact = cv2.imread(str(self.contact_png))
        self.assertIsNotNone(contact)
        self.assertEqual(contact.shape[0], 480)
        self.assertEqual(contact.shape[1], 270 * 3)

        red = means(frame_at(self.out, 0))
        green = means(frame_at(self.out, 70))
        blue = means(frame_at(self.out, 120))
        self.assertGreater(red[2], red[1] + 40)
        self.assertGreater(red[2], red[0] + 40)
        self.assertGreater(green[1], green[2] + 40)
        self.assertGreater(green[1], green[0] + 40)
        self.assertGreater(blue[0], blue[2] + 40)
        self.assertGreater(blue[0], blue[1] + 40)

    def test_peak_aligns_flash_to_timeline_peak(self) -> None:
        gen_dir = self.td / "peak-gen"
        gen_dir.mkdir()
        flash = gen_dir / "gen01.mp4"
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-f",
                "lavfi",
                "-i",
                "color=c=0x808080:s=320x568:r=30:d=6",
                "-vf",
                "drawbox=x=0:y=0:w=iw:h=ih:color=white:t=fill:enable='eq(n\\,90)',format=yuv420p",
                "-frames:v",
                "180",
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-bf",
                "0",
                "-r",
                "30",
                "-an",
                str(flash),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        timeline = {
            "fps": 30.0,
            "fps_rational": "30/1",
            "duration_sec": 2.0,
            "frame_count": 60,
            "cuts": [
                {
                    "index": 1,
                    "start_sec": 0.0,
                    "end_sec": 2.0,
                    "duration_sec": 2.0,
                    "start_frame": 0,
                    "end_frame": 60,
                    "frame_count": 60,
                    "peak_sec": 1.0,
                    "peak_frame": 30,
                }
            ],
        }
        timeline_path = self.td / "peak-timeline.json"
        timeline_path.write_text(json.dumps(timeline), encoding="utf-8")
        out = self.td / "peak.mp4"
        run_tool(
            "finish.py",
            timeline_path,
            gen_dir,
            out,
            "--fps",
            "30",
            "--peak-align",
        )
        cap = cv2.VideoCapture(str(out))
        values: list[float] = []
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            values.append(float(frame.mean()))
        cap.release()
        bright = max(range(len(values)), key=lambda i: values[i])
        self.assertLessEqual(abs(bright - 30), 2, values[max(0, bright - 2) : bright + 3])
        self.assertGreater(values[bright], 200)

    def test_effects_speed_and_24fps_still_pass_qc(self) -> None:
        cases = (
            ("effects.mp4", ["--grain", "--vignette", "--shake", "--fps", "30"]),
            ("speed.mp4", ["--speed", "2", "--fps", "30"]),
            ("fps24.mp4", ["--fps", "24"]),
        )
        for name, extra in cases:
            out = self.td / name
            with self.subTest(name=name):
                run_tool(
                    "finish.py",
                    self.timeline,
                    TESTS / "gen",
                    out,
                    *extra,
                    "--audio",
                    TESTS / "audio.wav",
                )
                qc = run_tool("qc.py", self.timeline, out, check=False)
                self.assertEqual(qc.returncode, 0, qc.stdout + qc.stderr)
                self.assertTrue((out.parent / "QC.md").read_text(encoding="utf-8").startswith("PASS"))

    def test_xfade_shortens_by_the_overlap(self) -> None:
        out = self.td / "xfade.mp4"
        run_tool(
            "finish.py",
            self.timeline,
            TESTS / "gen",
            out,
            "--fps",
            "30",
            "--xfade",
            "0.1",
        )
        info = probe(out)
        duration = info["frame_count"] / 30
        self.assertAlmostEqual(duration, 5.5 - 0.2, delta=0.05)
        self.assertEqual(info["width"], 1080)
        self.assertEqual(info["height"], 1920)
        self.assertEqual(info["pix_fmt"], "yuv420p")


if __name__ == "__main__":
    unittest.main()
