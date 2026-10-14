"""署名の構図・配色・テロップ位置を1枚の静止画にする。口は描かない。"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from irasutoya_short.constants import FONT_CANDIDATES, HEIGHT, WIDTH

FONT_DIR = Path(__file__).resolve().parents[1] / "fonts"
FONT_FILES = {
    "F1": "ZenKakuGothicNew-Bold.ttf",
    "F2": "ZenMaruGothic-Bold.ttf",
    "F3": "ShipporiMincho-Bold.ttf",
    "F4": "YuseiMagic-Regular.ttf",
    "F5": "ZenKakuGothicNew-Regular.ttf",
    "F6": "MochiyPopOne-Regular.ttf",
}
FONT_BOLD = {
    "F5": "ZenKakuGothicNew-Bold.ttf",
}

PALETTES = {
    "P1": {
        "wall": (246, 248, 252),
        "floor": (28, 48, 86),
        "accent": (18, 42, 92),
        "trim": (210, 220, 234),
        "ink": (16, 24, 40),
        "paper": (255, 255, 255),
        "sky": (186, 206, 228),
    },
    "P2": {
        "wall": (244, 236, 220),
        "floor": (196, 164, 112),
        "accent": (176, 42, 42),
        "trim": (120, 84, 52),
        "ink": (42, 28, 24),
        "paper": (255, 252, 246),
        "sky": (198, 228, 255),
    },
    "P3": {
        "wall": (214, 240, 226),
        "floor": (24, 28, 26),
        "accent": (12, 14, 13),
        "trim": (70, 90, 78),
        "ink": (10, 16, 12),
        "paper": (246, 255, 250),
        "sky": (232, 255, 244),
    },
    "P4": {
        "wall": (255, 228, 120),
        "floor": (62, 64, 68),
        "accent": (42, 44, 48),
        "trim": (90, 92, 96),
        "ink": (28, 28, 30),
        "paper": (255, 248, 220),
        "sky": (255, 244, 190),
    },
    "P5": {
        "wall": (236, 228, 250),
        "floor": (250, 248, 252),
        "accent": (122, 86, 176),
        "trim": (176, 156, 206),
        "ink": (48, 32, 72),
        "paper": (255, 255, 255),
        "sky": (220, 210, 245),
    },
    "P6": {
        "wall": (16, 26, 58),
        "floor": (10, 14, 28),
        "accent": (212, 170, 78),
        "trim": (150, 120, 48),
        "ink": (236, 220, 170),
        "paper": (34, 44, 78),
        "sky": (36, 58, 110),
    },
}

_FONT_CACHE: dict[tuple[str, int], ImageFont.ImageFont] = {}


def font_path(code: str, *, bold: bool = False) -> str:
    name = FONT_BOLD.get(code, "") if bold else FONT_FILES[code]
    if not name:
        name = FONT_FILES[code]
    path = FONT_DIR / name
    if path.is_file():
        return str(path)
    for candidate in FONT_CANDIDATES:
        if Path(candidate).is_file():
            return candidate
    return ""


def load_font(path: str, size: int) -> ImageFont.ImageFont:
    key = (path, size)
    cached = _FONT_CACHE.get(key)
    if cached is not None:
        return cached
    if path and Path(path).is_file():
        font = ImageFont.truetype(path, size=size)
    else:
        font = ImageFont.load_default()
    _FONT_CACHE[key] = font
    return font


def _lerp(a: tuple[int, int, int], b: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def build_still(
    scene: dict,
    book,
    axes: dict,
    cast: list[str],
    index: int,
    n_scenes: int,
    used: set[str],
    *,
    hide_people: bool = False,
    width: int = WIDTH,
    height: int = HEIGHT,
) -> np.ndarray:
    palette = PALETTES[axes["P"]]
    image = Image.new("RGB", (width, height), palette["wall"])
    draw = ImageDraw.Draw(image)
    _paint_room(draw, axes, palette, index, width, height)
    _paint_props(draw, axes, palette, width, height)
    if scene.get("role") != "credit" and not hide_people:
        _paint_people(image, book, axes, cast, index, used, width, height)
    if scene.get("role") == "hook":
        _paint_hook(draw, axes, palette, width, height)
    return np.asarray(image, dtype=np.uint8)


def _paint_room(draw: ImageDraw.ImageDraw, axes: dict, palette: dict, index: int, width: int, height: int) -> None:
    layout = axes["C"]
    mix = axes["A"]
    if mix == "A5":
        for y in range(0, height, 6):
            color = _lerp(palette["sky"], palette["floor"], y / height)
            draw.rectangle((0, y, width, y + 6), fill=color)
        draw.ellipse((int(width * 0.55), int(height * 0.08), int(width * 0.92), int(height * 0.28)), fill=palette["trim"])
        return
    if layout == "C6":
        draw.rectangle((0, 0, width, height), fill=palette["accent"])
        panels = (
            (0, 0, width // 2, int(height * 0.42)),
            (width // 2, 0, width, int(height * 0.42)),
            (0, int(height * 0.42), width // 2, int(height * 0.78)),
            (width // 2, int(height * 0.42), width, int(height * 0.78)),
        )
        active = index % 4
        for panel_index, box in enumerate(panels):
            fill = palette["paper"] if panel_index == active else palette["wall"]
            draw.rectangle(box, fill=fill)
            draw.rectangle(box, outline=palette["ink"], width=10)
        return
    if layout == "C5":
        split = int(height * 0.40)
        draw.rectangle((0, 0, width, split), fill=palette["accent"])
        draw.rectangle((0, split, width, height), fill=palette["wall"])
        draw.rectangle((48, 48, width - 48, split - 36), outline=palette["paper"], width=8)
        return
    floor_y = int(height * 0.74)
    draw.rectangle((0, floor_y, width, height), fill=palette["floor"])
    draw.rectangle((0, floor_y, width, floor_y + 14), fill=palette["trim"])
    if layout != "C4":
        win = (48, 48, int(width * 0.46), int(height * 0.36))
        draw.rounded_rectangle(win, radius=12, fill=palette["sky"], outline=palette["ink"], width=8)
    draw.rectangle((70, int(height * 0.78), width - 70, int(height * 0.78) + 28), fill=palette["trim"])
    if layout == "C4":
        for row in range(6):
            top = int(height * 0.08) + row * int(height * 0.09)
            fill = palette["accent"] if row == index % 6 else palette["paper"]
            draw.rounded_rectangle((36, top, int(width * 0.42), top + int(height * 0.06)), radius=8, fill=fill)
    if layout == "C2":
        draw.rectangle((width // 2 - 6, int(height * 0.08), width // 2 + 6, int(height * 0.72)), fill=palette["accent"])


def _paint_props(draw: ImageDraw.ImageDraw, axes: dict, palette: dict, width: int, height: int) -> None:
    layout = axes["C"]
    mix = axes["A"]
    if mix == "A6" or layout == "C4":
        left, top = int(width * 0.08), int(height * 0.16)
        right, bottom = int(width * 0.48), int(height * 0.70)
        if layout == "C4":
            left, right = int(width * 0.50), int(width * 0.96)
        draw.rounded_rectangle((left, top, right, bottom), radius=8, fill=palette["paper"], outline=palette["ink"], width=6)
        for row in range(5):
            y = top + 36 + row * ((bottom - top - 60) // 5)
            draw.line((left + 24, y, right - 24, y), fill=palette["trim"], width=4)
        return
    if layout == "C3" or mix in {"A2", "A3"}:
        sheets = 4 if mix == "A2" else 2
        for sheet in range(sheets):
            ox, oy = sheet * 18, sheet * 14
            box = (
                int(width * 0.12) + ox,
                int(height * 0.08) + oy,
                int(width * 0.78) + ox,
                int(height * (0.58 if mix != "A3" else 0.66)) + oy,
            )
            draw.rounded_rectangle(box, radius=10, fill=palette["paper"], outline=palette["ink"], width=6)
            for line in range(7):
                y = box[1] + 40 + line * 36
                if y < box[3] - 24:
                    draw.line((box[0] + 28, y, box[2] - 28, y), fill=palette["trim"], width=4)
        return
    if mix == "A1":
        origin = (int(width * 0.08), int(height * 0.58))
        draw.rounded_rectangle((origin[0], origin[1], origin[0] + 180, origin[1] + 220), radius=8, fill=palette["paper"], outline=palette["ink"], width=5)
        draw.ellipse((origin[0] + 200, origin[1] + 40, origin[0] + 340, origin[1] + 180), fill=palette["accent"])
        draw.rectangle((origin[0] + 210, origin[1] + 190, origin[0] + 250, origin[1] + 280), fill=palette["trim"])


def _paint_people(image: Image.Image, book, axes: dict, cast: list[str], index: int, used: set[str], width: int, height: int) -> None:
    if not cast or book is None:
        return
    show = list(cast)
    if axes["A"] == "A6" and index % 2 == 1:
        return
    for slot, asset_id in enumerate(show):
        cx, foot, sprite_h = _slot(axes, slot, len(show), index, width, height)
        sprite = book.still(asset_id, sprite_h)
        sprite_im = Image.fromarray(sprite, "RGBA")
        x = int(cx - sprite_im.width / 2)
        y = int(foot - sprite_im.height)
        image.paste(sprite_im, (x, y), sprite_im)
        used.add(asset_id)


def _slot(axes: dict, slot: int, count: int, index: int, width: int, height: int) -> tuple[int, int, int]:
    layout = axes["C"]
    mix = axes["A"]
    tall = int(height * 0.56)
    mid = int(height * 0.46)
    small = int(height * 0.28)
    if mix == "A3":
        tall, mid, small = small, small, int(height * 0.22)
    if mix == "A6":
        tall = mid = small = int(height * 0.22)
    if layout == "C6":
        centers = ((0.25, 0.30), (0.75, 0.30), (0.25, 0.62), (0.75, 0.62))
        cx, cy = centers[(index + slot) % 4]
        return int(width * cx), int(height * cy) + small // 2, small
    if layout == "C5":
        xs = (0.28, 0.50, 0.72)
        return int(width * xs[min(slot, 2)]), int(height * 0.92), int(height * 0.34)
    if layout == "C4":
        xs = (0.62, 0.78, 0.90)
        return int(width * xs[min(slot, 2)]), int(height * 0.80), mid
    if layout == "C3":
        xs = (0.18, 0.38, 0.58)
        return int(width * xs[min(slot, 2)]), int(height * 0.94), small
    if layout == "C2":
        xs = (0.26, 0.74, 0.50)
        return int(width * xs[min(slot, 2)]), int(height * 0.80), mid if count > 1 else tall
    xs = (0.50, 0.32, 0.68)
    if count == 1:
        return int(width * 0.50), int(height * 0.80), tall
    return int(width * xs[min(slot, 2)]), int(height * 0.80), mid


def _paint_hook(draw: ImageDraw.ImageDraw, axes: dict, palette: dict, width: int, height: int) -> None:
    hook = axes["H"]
    if hook == "H1":
        box = (width - 160, 28, width - 28, 160)
        draw.ellipse(box, fill=palette["accent"])
        font = load_font(font_path(axes["F"]), 72)
        draw.text((width - 124, 48), "？", font=font, fill=palette["paper"])
        return
    if hook == "H3":
        draw.rectangle((20, 20, width - 20, height - 20), outline=palette["accent"], width=14)
        draw.rectangle((40, 40, width - 40, height - 40), outline=palette["ink"], width=4)
        return
    if hook == "H5":
        label = "あるある"
        font = load_font(font_path(axes["F"]), 42)
        pad = 18
        dummy = ImageDraw.Draw(Image.new("RGB", (8, 8)))
        box = dummy.textbbox((0, 0), label, font=font)
        tw, th = box[2] - box[0], box[3] - box[1]
        x, y = 36, 36 if axes["T"] != "T1" else int(height * 0.42)
        draw.rounded_rectangle((x, y, x + tw + pad * 2, y + th + pad), radius=12, fill=palette["accent"])
        draw.text((x + pad, y + 4), label, font=font, fill=palette["paper"])


def telop_placement(axes: dict, scene: dict, width: int = WIDTH, height: int = HEIGHT) -> dict:
    palette = PALETTES[axes["P"]]
    mode = {
        "T1": "band",
        "T2": "band",
        "T3": "vertical",
        "T4": "bubble",
        "T5": "center",
        "T6": "note",
    }[axes["T"]]
    hook = axes["H"]
    if scene.get("role") == "hook" and hook == "H4":
        mode = "bubble"
    y_ratio = {"T1": 0.14, "T2": 0.86, "T3": 0.18, "T4": 0.40, "T5": 0.48, "T6": 0.78}[axes["T"]]
    if mode == "bubble":
        y_ratio = 0.40
    if mode == "center":
        y_ratio = 0.48
    wall = palette["wall"]
    lum = 0.3 * wall[0] + 0.59 * wall[1] + 0.11 * wall[2]
    if lum < 140:
        fill = (255, 248, 230, 255)
        bar = (*palette["accent"], 230)
    else:
        fill = (20, 22, 28, 255)
        bar = (*palette["accent"], 235)
    size = 96 if scene.get("role") == "credit" else 112
    if mode == "center":
        size = 132
    if scene.get("role") == "hook" and hook == "H2":
        size = int(size * 1.28)
    emphasis = axes["F"] == "F5"
    return {
        "mode": mode,
        "y_ratio": y_ratio,
        "font": font_path(axes["F"]),
        "font_bold": font_path(axes["F"], bold=True) if emphasis else "",
        "size": size,
        "stroke": 3 if axes["F"] == "F5" else 7,
        "bar": "square" if axes["T"] == "T1" else "round",
        "fill": fill,
        "bar_fill": bar if mode != "note" else (*palette["paper"], 240),
        "emphasis": emphasis,
        "full_width": axes["T"] == "T1",
        "width": width,
        "height": height,
    }
