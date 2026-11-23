#!/usr/bin/env python3
"""参考動画を PySceneDetect（threshold 27）でカットに分け、尺とピークを書き出す。

使い方:
    python3 split_ref.py ref.mp4 outdir
"""

from __future__ import annotations

import argparse
import json
import sys
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import ksutil
from scenedetect import SceneManager, open_video
from scenedetect.detectors import ContentDetector


def detect_ranges(path: Path) -> list[tuple[int, int]]:
    video = open_video(str(path))
    manager = SceneManager()
    manager.add_detector(ContentDetector(threshold=ksutil.SCENE_THRESHOLD))
    manager.detect_scenes(video, show_progress=False)
    scenes = manager.get_scene_list()
    if not scenes:
        count = ksutil.ffprobe(path)["frame_count"]
        return [(0, count)]
    return [(int(start.frame_num), int(end.frame_num)) for start, end in scenes]


def export_cut(ref: Path, start: int, end: int, dest: Path, fps: Fraction) -> None:
    count = end - start
    if count <= 0:
        ksutil.die(f"カット長が 0 です: {start}-{end}")
    rate = str(fps.numerator) if fps.denominator == 1 else f"{fps.numerator}/{fps.denominator}"
    vf = (
        f"trim=start_frame={start}:end_frame={end},"
        "setpts=PTS-STARTPTS,setsar=1,format=yuv420p"
    )
    ksutil.run(
        [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            "-i",
            str(ref),
            "-vf",
            vf,
            "-frames:v",
            str(count),
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-preset",
            "veryfast",
            "-crf",
            "18",
            "-bf",
            "0",
            "-r",
            rate,
            "-fps_mode",
            "cfr",
            "-an",
            str(dest),
        ]
    )
    written = ksutil.ffprobe(dest)["frame_count"]
    if written != count:
        ksutil.die(f"{dest.name} のフレーム数が {written} でした。期待は {count} です")


def seconds(frames: int, fps: Fraction) -> float:
    return float(Fraction(frames, 1) / fps)


def build(ref: Path, outdir: Path) -> dict:
    source = ksutil.ffprobe(ref)
    fps: Fraction = source["fps_fraction"]
    ranges = detect_ranges(ref)
    if not ranges:
        ksutil.die("カットを検出できませんでした")
    if ranges[0][0] != 0:
        ksutil.die(f"最初のカットがフレーム 0 から始まっていません: {ranges[0][0]}")
    for previous, nxt in zip(ranges, ranges[1:]):
        if previous[1] != nxt[0]:
            ksutil.die(f"カット境界が連続していません: {previous} -> {nxt}")
    if abs(ranges[-1][1] - source["frame_count"]) > 2:
        ksutil.die(
            "検出した末尾フレームが動画の長さと合いません: "
            f"{ranges[-1][1]} != {source['frame_count']}"
        )

    cuts = []
    for index, (start, end) in enumerate(ranges, start=1):
        name = f"cut{index:02d}"
        dest = outdir / f"{name}.mp4"
        export_cut(ref, start, end, dest, fps)
        scanned = ksutil.scan_motion(dest, float(fps), keep_images=True)
        peak_frame = int(scanned["peak_frame"])
        count = end - start
        if peak_frame >= count:
            peak_frame = count - 1
        start_png = f"{name}_start.png"
        peak_png = f"{name}_peak.png"
        end_png = f"{name}_end.png"
        ksutil.write_png(outdir / start_png, scanned["start"])
        ksutil.write_png(outdir / peak_png, scanned["peak"])
        ksutil.write_png(outdir / end_png, scanned["end"])
        cuts.append(
            {
                "index": index,
                "file": dest.name,
                "start_sec": seconds(start, fps),
                "end_sec": seconds(end, fps),
                "duration_sec": seconds(count, fps),
                "start_frame": start,
                "end_frame": end,
                "frame_count": count,
                "peak_frame": peak_frame,
                "peak_sec": seconds(peak_frame, fps),
                "start_png": start_png,
                "peak_png": peak_png,
                "end_png": end_png,
            }
        )
        print(
            f"{name}  {cuts[-1]['start_sec']:.3f}-{cuts[-1]['end_sec']:.3f}s"
            f"  {count}f  peak {peak_frame}"
        )

    total_frames = sum(cut["frame_count"] for cut in cuts)
    return {
        "source": str(ref),
        "fps": float(fps),
        "fps_rational": f"{fps.numerator}/{fps.denominator}",
        "width": source["width"],
        "height": source["height"],
        "duration_sec": seconds(total_frames, fps),
        "frame_count": total_frames,
        "scene_threshold": ksutil.SCENE_THRESHOLD,
        "cuts": cuts,
    }


def main(argv: list[str] | None = None) -> int:
    ksutil.require_tools()
    parser = argparse.ArgumentParser(
        description="参考動画をカットに分け、timeline.json と Start/Peak/End の PNG を書く。"
    )
    parser.add_argument("ref", type=Path, help="参考動画")
    parser.add_argument("outdir", type=Path, help="cutNN.mp4 と timeline.json の出力先")
    args = parser.parse_args(argv)
    if not args.ref.is_file():
        ksutil.die(f"参考動画がありません: {args.ref}")
    args.outdir.mkdir(parents=True, exist_ok=True)
    timeline = build(args.ref, args.outdir)
    dest = args.outdir / "timeline.json"
    dest.write_text(json.dumps(timeline, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{len(timeline['cuts'])} cuts -> {dest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
