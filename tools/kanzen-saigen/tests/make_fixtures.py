#!/usr/bin/env python3
"""ffmpeg の testsrc で、3カットの参考動画と 6 秒の生成カットを作る。

各カットはべた塗りに testsrc を 20% 重ねたもの。色が違うので
PySceneDetect の threshold 27 ではカット境界だけが分かれる。
生成カットの先頭 8 フレーム（0.25秒より長い頭）は別色で、finish が捨てる。
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FPS = 30
WIDTH = 1080
HEIGHT = 1920
# 0.25s * 30fps = 7.5。trim は 0.25秒以降の最初のフレーム（8）から使う。
HEAD_FRAMES = 8
GEN_FRAMES = 180
CUTS = (
    ("0xD02020", 60),
    ("0x20A040", 45),
    ("0x2040D0", 60),
)
HEAD_COLOR = "0xC000C0"


def run(cmd: list[str]) -> None:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        tail = (proc.stderr or "").strip().splitlines()
        raise SystemExit("ffmpeg failed\n" + "\n".join(tail[-20:]))


def probe_frames(path: Path) -> int:
    proc = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-count_frames",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=nb_read_frames",
            "-of",
            "json",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return int(json.loads(proc.stdout)["streams"][0]["nb_read_frames"])


def encode_body(path: Path, color: str, frames: int) -> None:
    duration = frames / FPS
    run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "lavfi",
            "-i",
            f"color=c={color}:s={WIDTH}x{HEIGHT}:r={FPS}:d={duration}",
            "-f",
            "lavfi",
            "-i",
            f"testsrc=size={WIDTH}x{HEIGHT}:rate={FPS}:duration={duration}",
            "-filter_complex",
            "[1:v]format=rgba,colorchannelmixer=aa=0.20[t];"
            "[0:v][t]overlay=format=auto,format=yuv420p",
            "-frames:v",
            str(frames),
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-preset",
            "veryfast",
            "-crf",
            "20",
            "-bf",
            "0",
            "-r",
            str(FPS),
            "-fps_mode",
            "cfr",
            "-an",
            str(path),
        ]
    )
    got = probe_frames(path)
    if got != frames:
        raise SystemExit(f"{path.name}: {got} frames, expected {frames}")


def encode_gen(path: Path, color: str) -> None:
    body_frames = GEN_FRAMES - HEAD_FRAMES
    run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "lavfi",
            "-i",
            f"color=c={HEAD_COLOR}:s={WIDTH}x{HEIGHT}:r={FPS}:d=2",
            "-f",
            "lavfi",
            "-i",
            f"color=c={color}:s={WIDTH}x{HEIGHT}:r={FPS}:d=8",
            "-f",
            "lavfi",
            "-i",
            f"testsrc=size={WIDTH}x{HEIGHT}:rate={FPS}:duration=8",
            "-filter_complex",
            "[2:v]format=rgba,colorchannelmixer=aa=0.20[t];"
            "[1:v][t]overlay=format=auto,format=yuv420p[body];"
            f"[0:v]format=yuv420p,trim=end_frame={HEAD_FRAMES},setpts=PTS-STARTPTS[head];"
            f"[body]trim=end_frame={body_frames},setpts=PTS-STARTPTS[b];"
            "[head][b]concat=n=2:v=1:a=0,format=yuv420p",
            "-frames:v",
            str(GEN_FRAMES),
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-preset",
            "veryfast",
            "-crf",
            "20",
            "-bf",
            "0",
            "-r",
            str(FPS),
            "-fps_mode",
            "cfr",
            "-an",
            str(path),
        ]
    )
    got = probe_frames(path)
    if got != GEN_FRAMES:
        raise SystemExit(f"{path.name}: {got} frames, expected {GEN_FRAMES}")


def concat_ref(segments: list[Path], dest: Path) -> None:
    listing = dest.with_suffix(".txt")
    listing.write_text(
        "".join(f"file '{segment.resolve()}'\n" for segment in segments),
        encoding="utf-8",
    )
    run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(listing),
            "-c",
            "copy",
            str(dest),
        ]
    )
    listing.unlink(missing_ok=True)
    expected = sum(frames for _color, frames in CUTS)
    got = probe_frames(dest)
    if got != expected:
        raise SystemExit(f"{dest.name}: {got} frames, expected {expected}")


def encode_audio(path: Path) -> None:
    run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=440:sample_rate=48000:duration=10",
            "-c:a",
            "pcm_s16le",
            str(path),
        ]
    )


def main() -> None:
    work = HERE / "work"
    work.mkdir(parents=True, exist_ok=True)
    gen_dir = HERE / "gen"
    gen_dir.mkdir(parents=True, exist_ok=True)
    segments: list[Path] = []
    for index, (color, frames) in enumerate(CUTS, start=1):
        segment = work / f"ref-{index:02d}.mp4"
        encode_body(segment, color, frames)
        segments.append(segment)
        encode_gen(gen_dir / f"gen{index:02d}.mp4", color)
    concat_ref(segments, HERE / "ref_3cut.mp4")
    for segment in segments:
        segment.unlink(missing_ok=True)
    encode_audio(HERE / "audio.wav")
    print(f"wrote {HERE / 'ref_3cut.mp4'} and {gen_dir}/gen01-03.mp4")


if __name__ == "__main__":
    sys.exit(main())
