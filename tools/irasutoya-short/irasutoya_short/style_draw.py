"""署名の構図・配色・テロップ位置を1枚の静止画にする。口は描かない。"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from irasutoya_short.constants import FONT_CANDIDATES, HEIGHT, WIDTH
from irasutoya_short.sprites import head_box

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


def _wash(draw: ImageDraw.ImageDraw, palette: dict, width: int, height: int) -> None:
    """壁にわずかなグラデーションを置き、カメラが動いたとき静止扱いにしない。"""
    wall = palette["wall"]
    shade = _lerp(wall, palette["floor"], 0.16)
    for y in range(0, height, 6):
        color = _lerp(wall, shade, y / max(1, height))
        draw.rectangle((0, y, width, y + 6), fill=color)


def _paper(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], palette: dict) -> None:
    draw.rounded_rectangle(box, radius=8, fill=palette["paper"], outline=palette["ink"], width=2)
    for line in range(6):
        y = box[1] + 28 + line * max(16, (box[3] - box[1] - 48) // 6)
        if y < box[3] - 16:
            draw.line((box[0] + 16, y, box[2] - 16, y), fill=palette["trim"], width=1)


def _paint_room(draw: ImageDraw.ImageDraw, axes: dict, palette: dict, index: int, width: int, height: int) -> None:
    layout = axes["C"]
    if axes["A"] == "A5":
        for y in range(0, height, 6):
            color = _lerp(palette["sky"], palette["floor"], y / max(1, height))
            draw.rectangle((0, y, width, y + 6), fill=color)
        return
    _wash(draw, palette, width, height)
    if layout == "C6":
        mid_x = width // 2
        y1 = int(height * 0.40)
        y2 = int(height * 0.74)
        ink = palette["ink"]
        draw.line((mid_x, 24, mid_x, y2), fill=ink, width=3)
        draw.line((24, y1, width - 24, y1), fill=ink, width=3)
        panels = (
            (24, 24, mid_x - 8, y1 - 8),
            (mid_x + 8, 24, width - 24, y1 - 8),
            (24, y1 + 8, mid_x - 8, y2 - 8),
            (mid_x + 8, y1 + 8, width - 24, y2 - 8),
        )
        active = panels[index % 4]
        draw.rectangle(active, fill=palette["paper"])
        return
    if layout == "C5":
        split = int(height * 0.42)
        draw.rectangle((0, 0, width, split), fill=palette["paper"])
        draw.line((36, split, width - 36, split), fill=palette["ink"], width=3)
        return
    floor_y = int(height * 0.74)
    draw.rectangle((0, floor_y, width, height), fill=palette["floor"])
    if layout == "C2":
        draw.line((width // 2, int(height * 0.08), width // 2, floor_y), fill=palette["ink"], width=3)
    if layout == "C4":
        font = load_font(font_path(axes["F"]), max(22, width // 16))
        left = int(width * 0.08)
        for row in range(5):
            y = int(height * 0.10) + row * int(height * 0.09)
            fill = palette["ink"] if row == index % 5 else palette["trim"]
            draw.text((left, y), str(row + 1), font=font, fill=fill)
            draw.line(
                (left + int(width * 0.08), y + int(height * 0.03), int(width * 0.42), y + int(height * 0.03)),
                fill=palette["trim"],
                width=1,
            )


def _paint_props(draw: ImageDraw.ImageDraw, axes: dict, palette: dict, width: int, height: int) -> None:
    layout = axes["C"]
    mix = axes["A"]
    if mix == "A6":
        left, top = int(width * 0.56), int(height * 0.16)
        right, bottom = int(width * 0.92), int(height * 0.48)
        for row in range(4):
            y = top + row * ((bottom - top) // 4)
            draw.line((left, y, right, y), fill=palette["trim"], width=1)
        for col in range(3):
            x = left + col * ((right - left) // 2)
            draw.line((x, top, x, bottom), fill=palette["trim"], width=1)
        return
    if layout == "C3" or mix in {"A1", "A2", "A3"}:
        sheets = 3 if mix == "A2" else 2 if mix == "A1" else 1
        for sheet in range(sheets):
            ox, oy = sheet * 14, sheet * 10
            box = (
                int(width * 0.10) + ox,
                int(height * 0.08) + oy,
                int(width * (0.62 if layout != "C4" else 0.46)) + ox,
                int(height * 0.46) + oy,
            )
            _paper(draw, box, palette)


def _visible_cast(axes: dict, cast: list[str], index: int) -> list[str]:
    if axes.get("A") == "A6" and index % 2 == 1:
        return []
    return list(cast)


def _placed_people(book, axes: dict, cast: list[str], index: int, width: int, height: int):
    show = _visible_cast(axes, cast, index)
    if not show or book is None:
        return
    for slot, asset_id in enumerate(show):
        cx, foot, sprite_h = _slot(axes, slot, len(show), index, width, height)
        sprite = book.still(asset_id, sprite_h)
        x = int(cx - sprite.shape[1] / 2)
        y = int(foot - sprite.shape[0])
        yield asset_id, x, y, sprite


def _paint_people(image: Image.Image, book, axes: dict, cast: list[str], index: int, used: set[str], width: int, height: int) -> None:
    for asset_id, x, y, sprite in _placed_people(book, axes, cast, index, width, height):
        sprite_im = Image.fromarray(sprite, "RGBA")
        image.paste(sprite_im, (x, y), sprite_im)
        used.add(asset_id)


def face_rects(book, axes: dict, cast: list[str], index: int, width: int = WIDTH, height: int = HEIGHT) -> list[tuple[int, int, int, int]]:
    rects: list[tuple[int, int, int, int]] = []
    for _asset_id, x, y, sprite in _placed_people(book, axes, cast, index, width, height):
        box = head_box(sprite)
        if box is None:
            continue
        left, top, right, bot = box
        rects.append((x + left, y + top, x + right, y + bot))
    return rects


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
    if axes["H"] != "H1" or axes["T"] == "T1":
        return
    font = load_font(font_path(axes["F"]), max(36, width // 18))
    draw.text((width - int(width * 0.16), 36), "？", font=font, fill=palette["ink"])


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
