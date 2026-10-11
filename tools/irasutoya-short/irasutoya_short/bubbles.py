"""地の文は端の四角枠、会話はしっぽ付きの吹き出し。"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from irasutoya_short.constants import FONT_CANDIDATES


def _font(size: int) -> ImageFont.FreeTypeFont:
    for path in FONT_CANDIDATES:
        if Path(path).is_file():
            return ImageFont.truetype(path, size=size)
    return ImageFont.load_default()


def _text_size(font: ImageFont.ImageFont, text: str) -> tuple[int, int]:
    dummy = Image.new("RGB", (8, 8))
    draw = ImageDraw.Draw(dummy)
    box = draw.multiline_textbbox((0, 0), text, font=font, spacing=6)
    return box[2] - box[0], box[3] - box[1]


def character_x_ratio(kind: str, side: str) -> float:
    """枠は顔の反対側、会話の吹き出しは話者の頭の上。"""
    if kind == "caption":
        return 0.32 if side == "right" else 0.68
    return 0.60 if side == "right" else 0.40


def render_bubble(text: str, kind: str, side: str, width: int, height: int, scale: float) -> np.ndarray:
    if side not in ("left", "right"):
        raise ValueError(f"吹き出しの位置が不明です: {side}")
    raw = text.replace("\r", "").strip()
    if kind == "caption":
        return _caption_box(raw, side, width, height, scale)
    if kind == "speech":
        return _speech_bubble(raw, side, width, height, scale)
    raise ValueError(f"未知の吹き出し: {kind}")


def _caption_box(text: str, side: str, width: int, height: int, scale: float) -> np.ndarray:
    """縦書きの白枠。しっぽは付けない。顔に被さらない端へ置く。"""
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    if not text:
        return np.array(img)
    columns = [ln for ln in text.split("\n") if ln] or [text]
    size = max(28, int(52 * scale))
    while True:
        font = _font(size)
        gap = max(4, int(size * 0.22))
        line_h = size + max(2, int(size * 0.14))
        longest = max(len(col) for col in columns)
        box_w = 36 * 2 + len(columns) * size + max(0, len(columns) - 1) * gap
        box_h = 28 * 2 + longest * line_h
        if size <= 28 or (box_w <= int(width * 0.34) and box_h <= int(height * 0.78)):
            break
        size -= 2
    margin = int(width * 0.03)
    top = int(height * 0.10)
    left = width - margin - box_w if side == "right" else margin
    top = max(12, min(height - box_h - 12, top))
    left = max(8, min(width - box_w - 8, left))
    draw = ImageDraw.Draw(img)
    draw.rectangle((left, top, left + box_w, top + box_h), fill=(255, 255, 255, 245), outline=(12, 12, 12, 255), width=6)
    for ci, col in enumerate(columns):
        x = left + 36 + (len(columns) - 1 - ci) * (size + gap)
        for ri, ch in enumerate(col):
            y = top + 28 + ri * line_h
            draw.text((x, y), ch, font=font, fill=(18, 18, 18, 255))
    return np.array(img)


def _speech_bubble(text: str, side: str, width: int, height: int, scale: float) -> np.ndarray:
    """会話用。角丸に、話者の方へ向くしっぽを付ける。"""
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    if not text:
        return np.array(img)
    size = max(28, int(46 * scale))
    font = _font(size)
    while size > 28:
        font = _font(size)
        tw, th = _text_size(font, text)
        if tw <= int(width * 0.42) and th <= int(height * 0.28):
            break
        size -= 2
    tw, th = _text_size(font, text)
    pad_x, pad_y = 28, 18
    box_w = tw + pad_x * 2
    box_h = th + pad_y * 2
    tail = 52
    anchor_x = int(width * character_x_ratio("speech", side))
    left = anchor_x - box_w // 2
    left = max(8, min(width - box_w - 8, left))
    tip_y = int(height * 0.44)
    top = max(12, tip_y - tail - box_h)
    draw = ImageDraw.Draw(img)
    cx = left + box_w // 2
    base_l, base_r = cx - 22, cx + 22
    tip = (cx, min(height - 8, top + box_h + tail))
    draw.polygon([(base_l, top + box_h - 1), (base_r, top + box_h - 1), tip], fill=(255, 255, 255, 245))
    draw.line([(base_l, top + box_h), tip, (base_r, top + box_h)], fill=(12, 12, 12, 255), width=5)
    draw.rounded_rectangle(
        (left, top, left + box_w, top + box_h),
        radius=18,
        fill=(255, 255, 255, 245),
        outline=(12, 12, 12, 255),
        width=5,
    )
    draw.line((base_l + 6, top + box_h - 1, base_r - 6, top + box_h - 1), fill=(255, 255, 255, 245), width=8)
    draw.multiline_text((left + pad_x, top + pad_y - 2), text, font=font, fill=(18, 18, 18, 255), spacing=6, align="center")
    return np.array(img)
