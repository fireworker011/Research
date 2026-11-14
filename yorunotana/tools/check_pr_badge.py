"""右上PRの画素チェック。

--expect true: 最後の2秒（120フレーム）だけに PR があり、それより前は 0。
  さらに広告の読み上げ開始が 尺-2.0秒 以降。
--expect false: 全フレームで PR が 0。
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import render_frames


def probe_duration(video: str) -> float:
    raw = subprocess.check_output(
        [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "json", video,
        ]
    )
    return float(json.loads(raw)["format"]["duration"])


def ad_speech_span(video: str) -> dict[str, float]:
    """最後の読み上げ区間。BGMだけの区間は広告の開始に数えない。"""
    cmd = [
        "ffmpeg", "-v", "error", "-i", video,
        "-ac", "1", "-ar", "24000", "-f", "s16le", "-",
    ]
    raw = subprocess.check_output(cmd)
    samples = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    sr = 24000
    duration = probe_duration(video)
    hop = int(0.02 * sr)
    if hop <= 0 or len(samples) <= hop:
        raise SystemExit("広告音声の長さを測れません")
    rms = np.array(
        [
            float(np.sqrt(np.mean(samples[index : index + hop] ** 2)))
            for index in range(0, len(samples) - hop, hop)
        ],
        dtype=np.float64,
    )
    bed = float(np.quantile(rms, 0.4))
    thresh = max(bed * 1.8, bed + 0.025, 0.055)
    loud = rms > thresh
    runs: list[tuple[int, int]] = []
    index = 0
    while index < len(loud):
        if not loud[index]:
            index += 1
            continue
        end = index
        while end < len(loud) and loud[end]:
            end += 1
        runs.append((index, end))
        index = end
    # 語の途中の短い谷（0.5秒未満）は一つの読みにまとめる。文と文の間は分けたまま。
    merged: list[tuple[int, int]] = []
    for start, end in runs:
        if merged and (start - merged[-1][1]) * 0.02 <= 0.50:
            merged[-1] = (merged[-1][0], end)
        else:
            merged.append((start, end))
    spoken = [(start, end) for start, end in merged if (end - start) * 0.02 >= 0.35]
    if not spoken:
        raise SystemExit("広告の読み上げが見つかりません")
    start_i, end_i = spoken[-1]
    start_sec = start_i * 0.02
    end_sec = end_i * 0.02
    return {
        "duration_sec": round(duration, 4),
        "ad_speech_start_sec": round(start_sec, 4),
        "ad_speech_end_sec": round(end_sec, 4),
        "ad_speech_dur_sec": round(end_sec - start_sec, 4),
        "ad_gate_sec": round(duration - 2.0, 4),
    }


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
    tail_n = min(render_frames.PR_TAIL_FRAMES, int(frames.shape[0]))
    if tail_n:
        head = present[:-tail_n]
        tail = present[-tail_n:]
    else:
        head = present
        tail = present[:0]
    head_pr = int(head.sum()) if len(head) else 0
    tail_pr = int(tail.sum()) if len(tail) else 0
    if expect:
        passed = head_pr == 0 and tail_n > 0 and tail_pr == int(tail.shape[0])
    else:
        passed = int(present.sum()) == 0
    ad: dict[str, float] | None = None
    if expect:
        ad = ad_speech_span(args.video)
        ad_ok = (
            ad["ad_speech_start_sec"] + 1e-4 >= ad["duration_sec"] - 2.0
            and ad["ad_speech_dur_sec"] <= 1.90
        )
        passed = passed and ad_ok
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
        "tail_frames": tail_n,
        "frames_with_pr_before_tail": head_pr,
        "tail_frames_with_pr": tail_pr,
        "expect_present": expect,
        "pass": passed,
    }
    if ad is not None:
        result.update(ad)
        result["ad_speech_in_tail"] = bool(ad["ad_speech_start_sec"] + 1e-4 >= ad["duration_sec"] - 2.0)
    Path(args.report).parent.mkdir(parents=True, exist_ok=True)
    Path(args.report).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
