#!/usr/bin/env python3
"""Synthetic mosaic tests. No adult media."""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from mosaic_apply import (
    MosaicError,
    apply_mosaic,
    build_filter,
    expand_box,
    load_boxes,
    mosaic_cell_px,
    pixel_box,
)


ROOT = Path(__file__).resolve().parent


def _write_solid_mp4(path: Path, color: str = "red", seconds: int = 1) -> None:
    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "lavfi",
        "-i",
        f"color=c={color}:s=640x360:d={seconds}:r=10",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        str(path),
    ]
    subprocess.run(cmd, check=True, capture_output=True)


def _write_marked_mp4(path: Path) -> None:
    """testsrc has high-frequency detail that a large mosaic cell flattens."""
    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "lavfi",
        "-i",
        "testsrc=size=640x360:rate=10:duration=1",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        str(path),
    ]
    subprocess.run(cmd, check=True, capture_output=True)


def _frame_png(video: Path, png: Path) -> None:
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(video),
        "-vframes",
        "1",
        str(png),
    ]
    subprocess.run(cmd, check=True, capture_output=True)


def _pixel(png: Path, x: int, y: int) -> tuple[int, int, int]:
    cmd = [
        "ffmpeg",
        "-i",
        str(png),
        "-vf",
        f"crop=1:1:{x}:{y},format=rgb24",
        "-f",
        "rawvideo",
        "-",
    ]
    result = subprocess.run(cmd, check=True, capture_output=True)
    data = result.stdout
    return data[0], data[1], data[2]


class LoadBoxesTests(unittest.TestCase):
    def test_example_file(self) -> None:
        spec = load_boxes(ROOT / "boxes.example.json")
        self.assertEqual(len(spec["boxes"]), 1)
        self.assertGreater(spec["margin"], 0)

    def test_rejects_empty(self) -> None:
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as handle:
            handle.write('{"version":1,"boxes":[]}')
            path = Path(handle.name)
        with self.assertRaises(MosaicError):
            load_boxes(path)

    def test_rejects_outside_frame(self) -> None:
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as handle:
            json.dump({"version": 1, "boxes": [{"x": 0.9, "y": 0.9, "w": 0.3, "h": 0.3}]}, handle)
            path = Path(handle.name)
        with self.assertRaises(MosaicError):
            load_boxes(path)


class GeometryTests(unittest.TestCase):
    def test_expand_stays_in_unit_square(self) -> None:
        expanded = expand_box({"x": 0.0, "y": 0.0, "w": 0.2, "h": 0.2}, 0.5)
        self.assertGreaterEqual(expanded["x"], 0)
        self.assertGreaterEqual(expanded["y"], 0)
        self.assertLessEqual(expanded["x"] + expanded["w"], 1.0001)

    def test_cell_at_least_four(self) -> None:
        self.assertGreaterEqual(mosaic_cell_px(100, 100), 4)
        self.assertGreaterEqual(mosaic_cell_px(1920, 100), 4)

    def test_pixel_box_even(self) -> None:
        x, y, w, h = pixel_box({"x": 0.1, "y": 0.1, "w": 0.33, "h": 0.33}, 640, 360)
        self.assertEqual(w % 2, 0)
        self.assertEqual(h % 2, 0)
        self.assertGreaterEqual(x, 0)
        self.assertLessEqual(x + w, 640)

    def test_filter_labels(self) -> None:
        filt = build_filter([{"x": 0.2, "y": 0.2, "w": 0.3, "h": 0.3}], 640, 360, 8)
        self.assertIn("overlay=", filt)
        self.assertIn("[v0]", filt)


class ApplyTests(unittest.TestCase):
    def test_mosaic_changes_box_and_spares_outside(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            source = tmp_path / "src.mp4"
            boxes = tmp_path / "boxes.json"
            out = tmp_path / "out.mp4"
            sheet = tmp_path / "sheet.png"
            frame = tmp_path / "frame.png"
            _write_marked_mp4(source)
            boxes.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "margin": 0.0,
                        "cell_div": 20,
                        "boxes": [{"x": 0.35, "y": 0.45, "w": 0.30, "h": 0.40}],
                    }
                ),
                encoding="utf-8",
            )
            result = apply_mosaic(source, boxes, out, sheet)
            self.assertFalse(result["compliant"])
            self.assertTrue(out.exists())
            self.assertTrue(sheet.exists())
            src_frame = tmp_path / "src.png"
            _frame_png(source, src_frame)
            _frame_png(out, frame)
            outside_src = _pixel(src_frame, 80, 40)
            outside_out = _pixel(frame, 80, 40)
            self.assertEqual(outside_src, outside_out)
            box_src = _pixel(src_frame, 320, 234)
            box_out = _pixel(frame, 320, 234)
            self.assertNotEqual(box_src, box_out)

    def test_cli_refuses_missing_boxes(self) -> None:
        from mosaic_apply import main

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            source = tmp_path / "src.mp4"
            _write_solid_mp4(source)
            code = main(
                [
                    "--in",
                    str(source),
                    "--boxes",
                    str(tmp_path / "missing.json"),
                    "--out",
                    str(tmp_path / "out.mp4"),
                ]
            )
            self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
