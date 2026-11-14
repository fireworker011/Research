"""声と、その約15%の自作BGMを1本のwavにする。

BGMは正弦波の自作。フリー素材は置かない。切り抜きも合成もしない。
"""

from __future__ import annotations

import math
import os
import struct
import wave
from pathlib import Path

RATE = 48000
VOICE_AMP = 8000
BGM_RATIO = 0.15
FONT_CANDIDATES = (
    "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
    "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
    "C:/Windows/Fonts/YuGothM.ttc",
    "C:/Windows/Fonts/meiryo.ttc",
    "C:/Windows/Fonts/msgothic.ttc",
)


def filter_path(path: str) -> str:
    """ffmpeg のフィルタはコロンで区切る。Windows の C: を逃す。"""
    return path.replace("\\", "/").replace(":", r"\:")


def font_path() -> str:
    chosen = os.environ.get("VIDEO_FONT", "").strip()
    if chosen:
        return chosen
    for candidate in FONT_CANDIDATES:
        if Path(candidate).is_file():
            return candidate
    raise SystemExit("日本語と数字が入った字体が無い。VIDEO_FONT に ttc のパスを置く")


def write_wav(
    path: Path,
    seconds: float,
    voice_spans: list[tuple[float, float]],
    bgm: bool,
) -> None:
    count = int(round(seconds * RATE))
    # 2音の実効値が、声の実効値の15%になる振幅。
    partial = 0.6
    bed_amp = VOICE_AMP * BGM_RATIO / math.sqrt(1 + partial * partial)
    frames = bytearray()
    for index in range(count):
        second = index / RATE
        voice = 0.0
        if any(start <= second < end for start, end in voice_spans):
            voice = math.sin(2 * math.pi * 220 * second) * VOICE_AMP
        bed = 0.0
        if bgm:
            bed = math.sin(2 * math.pi * 110 * second) * bed_amp
            bed += math.sin(2 * math.pi * 164.81 * second) * (bed_amp * 0.6)
        sample = int(voice + bed)
        if sample > 32767:
            sample = 32767
        elif sample < -32767:
            sample = -32767
        frames += struct.pack("<h", sample)
    with wave.open(str(path), "w") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(RATE)
        handle.writeframes(frames)
