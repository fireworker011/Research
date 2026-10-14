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
    _paint_room(draw, axes, palette, index, n_scenes, width, height)
    _paint_props(draw, axes, palette, scene, index, n_scenes, width, height)
    if scene.get("role") != "credit" and not hide_people:
        _paint_people(image, book, axes, cast, scene, index, n_scenes, used, width, height)
    if scene.get("role") == "hook":
        _paint_hook(draw, axes, palette, scene, width, height)
    return np.asarray(image, dtype=np.uint8)


def _wash(draw: ImageDraw.ImageDraw, palette: dict, width: int, height: int) -> None:
    """壁にわずかなグラデーションを置き、カメラが動いたとき静止扱いにしない。"""
    wall = palette["wall"]
    shade = _lerp(wall, palette["floor"], 0.16)
    for y in range(0, height, 6):
        color = _lerp(wall, shade, y / max(1, height))
        draw.rectangle((0, y, width, y + 6), fill=color)


def _beat(index: int, n_scenes: int) -> int:
    """前半・中盤・後半で絵を変える。字幕だけが動く一本にしない。"""
    if n_scenes <= 1:
        return 0
    return min(2, index * 3 // n_scenes)


def _paper_reads(palette: dict) -> bool:
    wall = palette["wall"]
    paper = palette["paper"]
    return sum(abs(paper[channel] - wall[channel]) for channel in range(3)) >= 80


def _paper(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], palette: dict) -> None:
    if box[2] - box[0] < 36 or box[3] - box[1] < 36:
        return
    draw.rounded_rectangle(box, radius=8, fill=palette["paper"], outline=palette["ink"], width=2)


def _paint_room(draw: ImageDraw.ImageDraw, axes: dict, palette: dict, index: int, n_scenes: int, width: int, height: int) -> None:
    beat = _beat(index, n_scenes)
    if axes["A"] == "A5":
        for y in range(0, height, 6):
            color = _lerp(palette["sky"], palette["floor"], y / max(1, height))
            draw.rectangle((0, y, width, y + 6), fill=color)
        ground = int(height * (0.46 if beat == 1 else 0.92 if beat == 2 else 0.76))
        draw.rectangle((0, ground, width, height), fill=palette["floor"])
        return
    _wash(draw, palette, width, height)
    if axes["C"] == "C5" and _paper_reads(palette):
        split = int(height * (0.22 if beat == 2 else 0.46 if beat == 1 else 0.32))
        draw.rectangle((36, 36, width - 36, split), fill=palette["paper"])
        return
    floor_y = int(height * (0.46 if beat == 1 else 0.90 if beat == 2 else 0.72))
    draw.rectangle((0, floor_y, width, height), fill=palette["floor"])


def _paint_props(draw: ImageDraw.ImageDraw, axes: dict, palette: dict, scene: dict, index: int, n_scenes: int, width: int, height: int) -> None:
    if axes["A"] == "A5" or axes["C"] == "C5" or not _paper_reads(palette):
        return
    beat = _beat(index, n_scenes)
    mix = axes["A"]
    count = 2 if mix == "A2" else 1
    if beat == 2 and mix not in {"A2", "A6"}:
        return
    lane = caption_lane(axes, scene, width, height)
    fx0, fy0, fx1, fy1 = _free_box(lane, width, height)
    span_w = fx1 - fx0
    span_h = fy1 - fy0
    if span_w < 80 or span_h < 80:
        return
    card_h = max(48, int(span_h * 0.22))
    card_w = max(56, int(span_w * (0.36 if count == 2 else 0.46)))
    top = fy0 + 12
    if top + card_h > fy1 - 12:
        return
    gap = 28
    if count == 2 and card_w * 2 + gap > span_w - 24:
        count = 1
    if count == 1:
        left = fx1 - card_w - 16 if beat == 1 else fx0 + 16
        _paper(draw, (left, top, left + card_w, top + card_h), palette)
        return
    left = fx0 + max(12, (span_w - (card_w * 2 + gap)) // 2)
    _paper(draw, (left, top, left + card_w, top + card_h), palette)
    second = left + card_w + gap
    _paper(draw, (second, top, second + card_w, top + card_h), palette)


def _visible_cast(cast: list[str], index: int, n_scenes: int) -> list[str]:
    if not cast:
        return []
    beat = _beat(index, n_scenes)
    if len(cast) >= 2 and beat == 2:
        return [cast[index % len(cast)]]
    if beat == 1 and len(cast) >= 2:
        return list(reversed(cast))
    return list(cast)


def _placed_people(book, axes: dict, cast: list[str], scene: dict, index: int, n_scenes: int, width: int, height: int):
    if scene.get("role") == "credit" or book is None:
        return
    show = _visible_cast(cast, index, n_scenes)
    if not show:
        return
    lane = caption_lane(axes, scene, width, height)
    fx0, fy0, fx1, fy1 = _free_box(lane, width, height)
    fx0, fy0, fx1, fy1 = _pull_from_lane(fx0, fy0, fx1, fy1, lane)
    pad = 8
    fx0, fy0, fx1, fy1 = fx0 + pad, fy0 + pad, max(fx0 + pad + 1, fx1 - pad), max(fy0 + pad + 1, fy1 - pad)
    span_w = max(1, fx1 - fx0)
    span_h = max(1, fy1 - fy0)
    beat = _beat(index, n_scenes)
    count = len(show)
    for slot, asset_id in enumerate(show):
        sprite_h = _sprite_height(axes, span_h, beat, count)
        sprite = book.still(asset_id, sprite_h)
        if sprite.shape[0] > span_h or sprite.shape[1] > span_w:
            fitted = max(40, int(sprite_h * min(span_h / sprite.shape[0], span_w / sprite.shape[1])))
            sprite = book.still(asset_id, fitted)
        cx = _anchor_x(axes, beat, slot, count, fx0, span_w)
        x = int(cx - sprite.shape[1] / 2)
        y = int(fy1 - sprite.shape[0])
        x = max(fx0, min(x, fx1 - sprite.shape[1]))
        y = max(fy0, min(y, fy1 - sprite.shape[0]))
        yield asset_id, x, y, sprite


def _paint_people(image: Image.Image, book, axes: dict, cast: list[str], scene: dict, index: int, n_scenes: int, used: set[str], width: int, height: int) -> None:
    for asset_id, x, y, sprite in _placed_people(book, axes, cast, scene, index, n_scenes, width, height):
        sprite_im = Image.fromarray(sprite, "RGBA")
        image.paste(sprite_im, (x, y), sprite_im)
        used.add(asset_id)


def _sprite_rects(book, axes: dict, cast: list[str], scene: dict, index: int, n_scenes: int, width: int, height: int):
    return list(_placed_people(book, axes, cast, scene, index, n_scenes, width, height))


def face_rects(book, axes: dict, cast: list[str], scene: dict, index: int, n_scenes: int = 1, width: int = WIDTH, height: int = HEIGHT) -> list[tuple[int, int, int, int]]:
    rects: list[tuple[int, int, int, int]] = []
    for _asset_id, x, y, sprite in _sprite_rects(book, axes, cast, scene, index, n_scenes, width, height):
        box = head_box(sprite)
        if box is None:
            continue
        left, top, right, bot = box
        rects.append((x + left, y + top, x + right, y + bot))
    return rects


def body_rects(book, axes: dict, cast: list[str], scene: dict, index: int, n_scenes: int = 1, width: int = WIDTH, height: int = HEIGHT) -> list[tuple[int, int, int, int]]:
    rects: list[tuple[int, int, int, int]] = []
    for _asset_id, x, y, sprite in _sprite_rects(book, axes, cast, scene, index, n_scenes, width, height):
        alpha = sprite[:, :, 3] > 20
        ys, xs = np.where(alpha)
        if len(xs) == 0:
            continue
        rects.append((x + int(xs.min()), y + int(ys.min()), x + int(xs.max()) + 1, y + int(ys.max()) + 1))
    return rects


def _sprite_height(axes: dict, span_h: int, beat: int, count: int) -> int:
    scale = 0.88
    if axes.get("A") == "A3":
        scale = 0.46
    elif axes.get("A") == "A6":
        scale = 0.62
    elif axes.get("C") == "C3":
        scale = 0.52
    elif count >= 3:
        scale = 0.74
    if beat == 1:
        scale *= 0.58
    elif beat == 2:
        scale = min(0.98, scale * 1.15)
    return max(48, int(span_h * scale))


def _anchor_x(axes: dict, beat: int, slot: int, count: int, origin: int, span_w: int) -> int:
    layout = axes["C"]
    if count == 1:
        anchors = (0.22, 0.80, 0.50)
        if layout == "C4":
            anchors = (0.80, 0.22, 0.50)
        elif layout in {"C2", "C6"}:
            anchors = (0.24, 0.78, 0.50)
        return int(origin + span_w * anchors[beat])
    if beat == 1:
        gaps = (0.78, 0.48, 0.22)
    elif beat == 2:
        gaps = (0.50, 0.34, 0.66)
    elif layout == "C2":
        gaps = (0.24, 0.76, 0.50)
    elif layout == "C4":
        gaps = (0.62, 0.78, 0.90)
    else:
        gaps = (0.22, 0.50, 0.78)
    return int(origin + span_w * gaps[min(slot, 2)])


def _paint_hook(draw: ImageDraw.ImageDraw, axes: dict, palette: dict, scene: dict, width: int, height: int) -> None:
    if axes["H"] != "H1" or axes["T"] == "T1" or scene.get("role") != "hook":
        return
    lane = caption_lane(axes, scene, width, height)
    x = width - int(width * 0.16)
    y = 40
    if lane[0] <= x <= lane[2] and lane[1] <= y <= lane[3]:
        return
    font = load_font(font_path(axes["F"]), max(36, width // 18))
    draw.text((x, y), "？", font=font, fill=palette["ink"])


def caption_lane(axes: dict, scene: dict, width: int, height: int) -> tuple[int, int, int, int]:
    """字幕を置く帯。人物はこの外に立たせる。"""
    margin = 48
    place = telop_placement(axes, scene, width, height)
    mode = str(place["mode"])
    band = max(72, int(height * 0.22))
    if mode == "vertical":
        return (margin, margin, margin + int(width * 0.34), height - margin)
    if mode == "note":
        return (int(width * 0.40), int(height * 0.60), width - margin, height - margin)
    if mode in {"center", "bubble"}:
        top = int(height * 0.32)
        return (margin, top, width - margin, top + int(height * 0.30))
    if float(place["y_ratio"]) < 0.5:
        return (margin, margin, width - margin, margin + band)
    return (margin, height - margin - band, width - margin, height - margin)


def _pull_from_lane(
    fx0: int, fy0: int, fx1: int, fy1: int, lane: tuple[int, int, int, int], gap: int = 20,
) -> tuple[int, int, int, int]:
    lx0, ly0, lx1, ly1 = lane
    if fy1 <= ly0:
        fy1 = min(fy1, ly0 - gap)
    elif fy0 >= ly1:
        fy0 = max(fy0, ly1 + gap)
    if fx1 <= lx0:
        fx1 = min(fx1, lx0 - gap)
    elif fx0 >= lx1:
        fx0 = max(fx0, lx1 + gap)
    if fx1 - fx0 < 40 or fy1 - fy0 < 40:
        return fx0, fy0, max(fx0 + 40, fx1), max(fy0 + 40, fy1)
    return fx0, fy0, fx1, fy1


def _free_box(lane: tuple[int, int, int, int], width: int, height: int) -> tuple[int, int, int, int]:
    lx0, ly0, lx1, ly1 = lane
    choices = (
        (0, 0, width, ly0),
        (0, ly1, width, height),
        (0, 0, lx0, height),
        (lx1, 0, width, height),
    )
    best = max(choices, key=lambda box: max(0, box[2] - box[0]) * max(0, box[3] - box[1]))
    if best[2] - best[0] < 40 or best[3] - best[1] < 40:
        return (0, 0, width, height)
    return best


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
