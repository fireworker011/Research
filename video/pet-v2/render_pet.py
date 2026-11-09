#!/usr/bin/env python3
"""ペットの試作。猫の切り抜きと、別背景への合成はしない。

平面描画（爪とぎのように、猫と部屋を1枚に塗る）か、
渡した1枚を枠いっぱいにそのまま使う。本編字幕は冒頭1秒のフックだけ。
PRは最後の2秒。尺は10.5秒。
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from video.common.flat_mix import filter_path, font_path, write_wav

WIDTH = 1080
HEIGHT = 1920
SECONDS = 10.5
FRAMES = 252
HOOK = "押さなくなった？"
PR = "広告 #PR"


class Canvas:
    def __init__(self, color: tuple[int, int, int]) -> None:
        self.buf = bytearray(bytes(color) * (WIDTH * HEIGHT))

    def rect(self, x: int, y: int, width: int, height: int, color: tuple[int, int, int]) -> None:
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(WIDTH, x + width)
        y1 = min(HEIGHT, y + height)
        pixel = bytes(color)
        for row in range(y0, y1):
            start = (row * WIDTH + x0) * 3
            end = (row * WIDTH + x1) * 3
            self.buf[start:end] = pixel * (x1 - x0)

    def save(self, path: Path) -> None:
        header = f"P6\n{WIDTH} {HEIGHT}\n255\n".encode("ascii")
        path.write_bytes(header + bytes(self.buf))


def paint_flat() -> Canvas:
    """猫と背景を同じ1枚に塗る。素材を切り抜いて載せない。"""
    wall = (142, 206, 224)
    canvas = Canvas(wall)
    canvas.rect(0, 980, WIDTH, HEIGHT - 980, (226, 168, 106))
    canvas.rect(760, 640, 150, 480, (168, 98, 58))
    canvas.rect(280, 1120, 440, 300, (240, 150, 60))
    canvas.rect(300, 960, 210, 200, (240, 150, 60))
    canvas.rect(320, 900, 70, 90, (240, 150, 60))
    canvas.rect(450, 900, 70, 90, (240, 150, 60))
    canvas.rect(180, 1320, 180, 70, (244, 162, 80))
    return canvas


def fit_still(source: Path, dest: Path) -> None:
    """1枚を枠のサイズへ伸ばすだけ。マスクも背景の差し替えもしない。"""
    subprocess.check_call(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(source),
            "-vf",
            f"scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=decrease,"
            f"pad={WIDTH}:{HEIGHT}:(ow-iw)/2:(oh-ih)/2:color=0x8ECEE0",
            "-frames:v",
            "1",
            str(dest),
        ]
    )


def render(out: Path, image: Path | None, bgm: bool) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="pet-v2-") as folder:
        root = Path(folder)
        frame = root / "frame.ppm"
        if image is None:
            paint_flat().save(frame)
        else:
            fitted = root / "still.ppm"
            fit_still(image, fitted)
            frame = fitted
        audio = root / "audio.wav"
        write_wav(audio, SECONDS, [(0.0, 1.2), (6.0, 8.4)], bgm)
        hook = root / "hook.txt"
        pr = root / "pr.txt"
        hook.write_text(HOOK + "\n", encoding="utf-8")
        pr.write_text(PR + "\n", encoding="utf-8")
        font = filter_path(font_path())
        video_filter = (
            f"drawtext=fontfile={font}:textfile={hook}:expansion=none:fontsize=72:"
            "fontcolor=0x5A3A2A:x=(w-text_w)/2:y=160:enable='lt(t\\,1)',"
            f"drawtext=fontfile={font}:textfile={pr}:expansion=none:fontsize=64:"
            "fontcolor=0x5A3A2A:x=(w-text_w)/2:y=(h-text_h)/2:enable='gte(t\\,8.5)'"
        )
        subprocess.check_call(
            [
                "ffmpeg",
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-loop",
                "1",
                "-framerate",
                "24",
                "-i",
                str(frame),
                "-i",
                str(audio),
                "-vf",
                video_filter,
                "-t",
                str(SECONDS),
                "-frames:v",
                str(FRAMES),
                "-r",
                "24",
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-c:a",
                "aac",
                "-b:a",
                "128k",
                "-movflags",
                "+faststart",
                str(out),
            ]
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="ペットの平面描画か、1枚をそのまま使う")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--image", type=Path, help="1枚の画像。切り抜かず、枠に合わせる")
    parser.add_argument("--no-bgm", action="store_true")
    args = parser.parse_args()
    render(args.out, args.image, bgm=not args.no_bgm)


if __name__ == "__main__":
    main()
