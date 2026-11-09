#!/usr/bin/env python3
"""金メモの試作。表は1枚に描く。BGMは自作で、音量は声の約15%。

画面にクレジットを焼く。猫の切り抜き合成はしない。尺は10.5秒。
PRと商品名は入れない。金メモの実額は出してよい（2026-11-10 確認）。
--amount で渡した円をそのまま焼く。未指定の 100、200、300 は見本で、公式の額ではない。
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
    canvas = Canvas((255, 255, 255))
    canvas.rect(80, 140, 920, 1640, (255, 236, 200))
    canvas.rect(140, 480, 800, 150, (255, 214, 120))
    canvas.rect(140, 680, 800, 150, (255, 214, 120))
    canvas.rect(140, 880, 800, 150, (255, 214, 120))
    return canvas


def render(out: Path, bgm: bool, amounts: tuple[str, str, str] | None = None) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="kanememo-") as folder:
        root = Path(folder)
        frame = root / "frame.ppm"
        paint_flat().save(frame)
        audio = root / "audio.wav"
        write_wav(audio, SECONDS, [(0.0, 1.4), (2.0, 8.4)], bgm)
        lines = {
            "head": "いくら納める？\n",
            "row1": f"区分A  {amounts[0] if amounts else '100'}\n",
            "row2": f"区分B  {amounts[1] if amounts else '200'}\n",
            "row3": f"区分C  {amounts[2] if amounts else '300'}\n",
            "conclusion": "結論: 表の3行。\n",
            "credit": "BGM: 自作\n",
        }
        for name, text in lines.items():
            (root / f"{name}.txt").write_text(text, encoding="utf-8")
        credit_enable = "gte(t\\,0)" if bgm else "lt(t\\,0)"
        font = filter_path(font_path())
        parts = [
            f"drawtext=fontfile={font}:textfile={root / 'head.txt'}:expansion=none:fontsize=72:fontcolor=0x5A3A2A:x=(w-text_w)/2:y=220",
            f"drawtext=fontfile={font}:textfile={root / 'row1.txt'}:expansion=none:fontsize=56:fontcolor=0x5A3A2A:x=180:y=520",
            f"drawtext=fontfile={font}:textfile={root / 'row2.txt'}:expansion=none:fontsize=56:fontcolor=0x5A3A2A:x=180:y=720",
            f"drawtext=fontfile={font}:textfile={root / 'row3.txt'}:expansion=none:fontsize=56:fontcolor=0x5A3A2A:x=180:y=920",
            f"drawtext=fontfile={font}:textfile={root / 'conclusion.txt'}:expansion=none:fontsize=52:fontcolor=0x5A3A2A:x=(w-text_w)/2:y=1160:enable='between(t\\,6\\,8.5)'",
            f"drawtext=fontfile={font}:textfile={root / 'credit.txt'}:expansion=none:fontsize=42:fontcolor=0x5A3A2A:x=(w-text_w)/2:y=1580:enable='{credit_enable}'",
        ]
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
                ",".join(parts),
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
    parser = argparse.ArgumentParser(description="金メモの表と自作BGM")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--no-bgm", action="store_true")
    parser.add_argument("--amount", action="append", help="表の円。3つ。金メモの実額をそのまま焼く")
    args = parser.parse_args()
    amounts = None
    if args.amount:
        if len(args.amount) != 3:
            parser.error("--amount は3つ")
        amounts = (args.amount[0], args.amount[1], args.amount[2])
    render(args.out, bgm=not args.no_bgm, amounts=amounts)


if __name__ == "__main__":
    main()
