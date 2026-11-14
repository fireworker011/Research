"""pr_badge の動画で、右上PRが全フレームにあるかを画素で確認する。"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import render_frames


def main() -> int:
    parser = argparse.ArgumentParser(description="PRバッジの画素チェック")
    parser.add_argument("--video", required=True)
    parser.add_argument("--expect", choices=("true", "false"), required=True)
    parser.add_argument("--report", required=True)
    args = parser.parse_args()
    expect = args.expect == "true"
    x, y, width, height = render_frames.pr_badge_box()
    glyph, plate = render_frames.pr_check_masks()
    if int(glyph.sum()) < 20 or int(plate.sum()) < 20:
        raise SystemExit(f"PRマスクが不正です glyph={int(glyph.sum())} plate={int(plate.sum())}")
    cmd = [
        "ffmpeg", "-v", "error", "-i", args.video,
        "-vf", f"crop={width}:{height}:{x}:{y}",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-",
    ]
    raw = subprocess.check_output(cmd)
    frame_size = width * height * 3
    if len(raw) % frame_size != 0:
        raise SystemExit("切り出しサイズがフレーム境界に合いません")
    frames = np.frombuffer(raw, dtype=np.uint8).reshape((-1, height, width, 3))
    glyph_means = frames[:, glyph, :].mean(axis=(1, 2))
    plate_means = frames[:, plate, :].mean(axis=(1, 2))
    contrast = glyph_means - plate_means
    present = (glyph_means >= 150.0) & (contrast >= 60.0)
    # バッジあり/なしの静止画差分（圧縮前）も残す。
    with_badge = render_frames.composite(
        render_frames.night_bg(),
        render_frames.paint_overlay(3, "4:30 AM", "", True, None, None, "white"),
    )
    without = render_frames.composite(
        render_frames.night_bg(),
        render_frames.paint_overlay(3, "4:30 AM", "", False, None, None, "white"),
    )
    box = (x, y, x + width, y + height)
    diff = np.abs(
        np.asarray(with_badge.crop(box), dtype=np.int16) - np.asarray(without.crop(box), dtype=np.int16)
    ).mean()
    result = {
        "video": args.video,
        "frames": int(frames.shape[0]),
        "frames_with_pr": int(present.sum()),
        "frames_missing_pr": int((~present).sum()),
        "min_glyph_mean": round(float(glyph_means.min()), 2),
        "max_glyph_mean": round(float(glyph_means.max()), 2),
        "min_plate_mean": round(float(plate_means.min()), 2),
        "max_plate_mean": round(float(plate_means.max()), 2),
        "min_contrast": round(float(contrast.min()), 2),
        "still_mae_pr_vs_off": round(float(diff), 2),
        "expect_present": expect,
        "pass": bool(present.all()) if expect else bool((~present).all()),
    }
    Path(args.report).parent.mkdir(parents=True, exist_ok=True)
    Path(args.report).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
