#!/usr/bin/env python3
"""つなぎ終わった動画を、尺・切れ目・黒フレーム・LUFS で判定する。

使い方:
    python3 qc.py timeline.json out.mp4

QC.md と contact.png を out.mp4 と同じフォルダに書く。
PASS なら終了コード 0、FAIL なら 1。
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

import ksutil


def evidence_line(
    out_dur: float,
    ref_dur: float,
    duration_ok: bool,
    cut_text: str,
    blacks: list[str],
    lufs: float | None,
    lufs_ok: bool,
) -> str:
    delta = abs(out_dur - ref_dur)
    if duration_ok:
        duration = f"全体尺 {out_dur:.3f}s（基準 {ref_dur:.3f}s、差 {delta:.3f}s）"
    else:
        duration = (
            f"全体尺 {out_dur:.3f}s（基準 {ref_dur:.3f}s、差 {delta:.3f}s、許容 ±0.200s）"
        )
    if blacks:
        black = f"黒フレームあり（{blacks[0]}s）"
    else:
        black = "黒フレームなし"
    if lufs is None:
        loud = "ラウドネスを測定できない"
    elif lufs_ok:
        loud = f"ラウドネス {lufs:.2f} LUFS"
    else:
        loud = f"ラウドネス {lufs:.2f} LUFS（許容 -15〜-13）"
    return "、".join((duration, cut_text, black, loud)) + "。"


def center_frames(timeline: dict, out_fps: float) -> list[int]:
    source_fps = ksutil.timeline_fps(timeline)
    mids: list[int] = []
    acc = 0
    for cut in timeline["cuts"]:
        count = ksutil.out_frames_for(cut, out_fps, source_fps)
        mids.append(acc + count // 2)
        acc += count
    return mids


def judge(timeline_path: Path, out_path: Path) -> int:
    if not out_path.is_file():
        ksutil.die(f"出力動画がありません: {out_path}")
    timeline = ksutil.load_timeline(timeline_path)
    info = ksutil.ffprobe(out_path)
    ref_dur = float(timeline["duration_sec"])
    out_dur = float(info["duration_sec"])
    duration_ok = abs(out_dur - ref_dur) <= ksutil.DURATION_TOL_SEC

    diffs = ksutil.frame_diffs(out_path)
    bounds = ksutil.expected_boundaries(timeline, float(info["fps"]))
    cut_ok, _delta, cut_text = ksutil.cut_alignment(diffs, bounds)

    blacks = ksutil.black_starts(out_path)
    black_ok = not blacks

    lufs = ksutil.measure_loudness(out_path) if ksutil.has_audio(out_path) else None
    lufs_ok = lufs is not None and -15.0 <= lufs <= -13.0
    passed = duration_ok and cut_ok and black_ok and lufs_ok

    report = out_path.parent / "QC.md"
    line = evidence_line(out_dur, ref_dur, duration_ok, cut_text, blacks, lufs, lufs_ok)
    report.write_text(("PASS\n" if passed else "FAIL\n") + line + "\n", encoding="utf-8")

    mids = center_frames(timeline, float(info["fps"]))
    found = ksutil.read_frames_at(out_path, mids)
    blank = np.zeros((info["height"], info["width"], 3), dtype=np.uint8)
    frames = [found.get(index, blank) for index in mids]
    ksutil.write_contact_sheet(out_path.parent / "contact.png", frames)

    sys.stdout.write(report.read_text(encoding="utf-8"))
    return 0 if passed else 1


def main(argv: list[str] | None = None) -> int:
    ksutil.require_tools()
    parser = argparse.ArgumentParser(
        description="尺・切れ目・黒フレーム・LUFS を判定し、QC.md と contact.png を書く。"
    )
    parser.add_argument("timeline", type=Path, help="split_ref.py の timeline.json")
    parser.add_argument("out", type=Path, help="finish.py の出力 mp4")
    args = parser.parse_args(argv)
    return judge(args.timeline, args.out)


if __name__ == "__main__":
    sys.exit(main())
