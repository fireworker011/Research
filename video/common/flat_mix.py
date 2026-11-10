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
# 英数字と # が欠けている字体（DroidSansFallback など）は使わない。
REQUIRED_GLYPHS = "#0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
FONT_CANDIDATES = (
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
    "C:/Windows/Fonts/YuGothM.ttc",
    "C:/Windows/Fonts/meiryo.ttc",
    "C:/Windows/Fonts/msgothic.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
)


def filter_path(path: str) -> str:
    """ffmpeg のフィルタはコロンで区切る。Windows の C: を逃す。"""
    return path.replace("\\", "/").replace(":", r"\:")


def _sfnt_cmap(data: bytes, offset: int) -> set[int]:
    if offset + 12 > len(data):
        return set()
    num_tables = struct.unpack_from(">H", data, offset + 4)[0]
    rec = offset + 12
    cmap_off = None
    for index in range(num_tables):
        tag, _chk, table_off, _length = struct.unpack_from(">4sIII", data, rec + index * 16)
        if tag == b"cmap":
            cmap_off = table_off
            break
    if cmap_off is None:
        return set()
    if cmap_off + 4 > len(data):
        return set()
    num_records = struct.unpack_from(">H", data, cmap_off + 2)[0]
    chars: set[int] = set()
    for index in range(num_records):
        _plat, _enc, sub_off = struct.unpack_from(">HHI", data, cmap_off + 4 + index * 8)
        start = cmap_off + sub_off
        if start + 2 > len(data):
            continue
        fmt = struct.unpack_from(">H", data, start)[0]
        if fmt == 4:
            chars.update(_cmap_format4(data, start))
        elif fmt == 12:
            chars.update(_cmap_format12(data, start))
    return chars


def _cmap_format4(data: bytes, start: int) -> set[int]:
    if start + 14 > len(data):
        return set()
    seg_count = struct.unpack_from(">H", data, start + 6)[0] // 2
    end_off = start + 14
    start_off = end_off + 2 * seg_count + 2
    delta_off = start_off + 2 * seg_count
    range_off = delta_off + 2 * seg_count
    if range_off + 2 * seg_count > len(data):
        return set()
    chars: set[int] = set()
    for index in range(seg_count):
        end_code = struct.unpack_from(">H", data, end_off + 2 * index)[0]
        start_code = struct.unpack_from(">H", data, start_off + 2 * index)[0]
        id_delta = struct.unpack_from(">h", data, delta_off + 2 * index)[0]
        id_range = struct.unpack_from(">H", data, range_off + 2 * index)[0]
        for code in range(start_code, end_code + 1):
            if id_range == 0:
                glyph = (code + id_delta) & 0xFFFF
            else:
                loc = range_off + 2 * index + id_range + 2 * (code - start_code)
                if loc + 2 > len(data):
                    continue
                glyph_id = struct.unpack_from(">H", data, loc)[0]
                glyph = 0 if glyph_id == 0 else (glyph_id + id_delta) & 0xFFFF
            if glyph:
                chars.add(code)
    return chars


def _cmap_format12(data: bytes, start: int) -> set[int]:
    if start + 16 > len(data):
        return set()
    n_groups = struct.unpack_from(">I", data, start + 12)[0]
    chars: set[int] = set()
    for index in range(n_groups):
        loc = start + 16 + index * 12
        if loc + 12 > len(data):
            break
        first, last, glyph = struct.unpack_from(">III", data, loc)
        if glyph == 0 and first == last == 0:
            continue
        for code in range(first, last + 1):
            if glyph + (code - first) != 0:
                chars.add(code)
    return chars


def font_codepoints(path: str, face_index: int = 0) -> set[int]:
    """TTF/TTC/OTF の先頭面（または指定面）の cmap。"""
    data = Path(path).read_bytes()
    if len(data) < 16:
        return set()
    if data[:4] == b"ttcf":
        num = struct.unpack_from(">I", data, 8)[0]
        if face_index >= num:
            return set()
        offset = struct.unpack_from(">I", data, 12 + 4 * face_index)[0]
    else:
        offset = 0
    return _sfnt_cmap(data, offset)


def font_covers(path: str, text: str = REQUIRED_GLYPHS, face_index: int = 0) -> bool:
    if not Path(path).is_file():
        return False
    try:
        chars = font_codepoints(path, face_index)
    except (OSError, struct.error, ValueError):
        return False
    return all(ord(ch) in chars for ch in text)


def font_path() -> str:
    chosen = os.environ.get("VIDEO_FONT", "").strip()
    if chosen:
        if not Path(chosen).is_file():
            raise SystemExit(f"VIDEO_FONT の字体が無い: {chosen}")
        if not font_covers(chosen):
            raise SystemExit(f"VIDEO_FONT に #・英字・数字が欠けている: {chosen}")
        return chosen
    for candidate in FONT_CANDIDATES:
        if Path(candidate).is_file() and font_covers(candidate):
            return candidate
    raise SystemExit("日本語と英数字・# が入った字体が無い。VIDEO_FONT に Noto Sans CJK JP などのパスを置く")


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
