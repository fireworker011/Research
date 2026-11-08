"""1080x1920 / 60fps の手続き描画。AI画像は使わない。

使い方:
  python src/render_frames.py --job <json> --timing out/temp_audio/audio_timing.json --audio out/temp_audio/master_audio.wav --out out/<JobId>.mp4
  python src/render_frames.py --stills out/previews
"""

from __future__ import annotations

import argparse
import json
import math
import os
import random
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

WIDTH = 1080
HEIGHT = 1920
FPS = 60
ROOT = Path(__file__).resolve().parents[1]

YELLOW = (255, 238, 51, 255)
WHITE = (255, 255, 255, 255)
RED = (214, 36, 48, 255)
GRAY = (168, 174, 184, 255)

FONT_PATH: Path | None = None
FONT_INDEX = 0
FONT_NAME = ""
FONT_CACHE: dict[int, ImageFont.FreeTypeFont] = {}
_MEASURE = ImageDraw.Draw(Image.new("RGB", (8, 8)))


def log(message: str) -> None:
    print(message, file=sys.stderr)


def pr_badge_box() -> tuple[int, int, int, int]:
    width, height = 150, 80
    return (WIDTH - 44 - width, 40, width, height)


def font_candidates() -> list[Path]:
    windir = os.environ.get("WINDIR", r"C:\Windows")
    fonts = Path(windir) / "Fonts"
    ordered: list[Path] = []
    for name in ("YuGothB.ttc", "YuGothB.ttf", "yugothib.ttf", "BIZ-UDGothicB.ttc", "meiryob.ttc"):
        ordered.append(fonts / name)
    roots: list[Path] = [
        Path("/usr/share/fonts"),
        Path("/usr/local/share/fonts"),
        Path.home() / ".fonts",
        Path.home() / ".local" / "share" / "fonts",
    ]
    local = os.environ.get("LOCALAPPDATA")
    if local:
        roots.append(Path(local) / "Microsoft" / "Windows" / "Fonts")
    for root in roots:
        if root.exists():
            ordered.extend(sorted(root.rglob("NotoSansCJK-Bold.ttc")))
            ordered.extend(sorted(root.rglob("NotoSansCJKjp-Bold.otf")))
    for root in roots:
        if root.exists():
            ordered.extend(sorted(root.rglob("NotoSansCJK-Regular.ttc")))
    for name in ("YuGothM.ttc", "meiryo.ttc", "msgothic.ttc"):
        ordered.append(fonts / name)
    seen: set[str] = set()
    unique: list[Path] = []
    for path in ordered:
        key = str(path)
        if key in seen:
            continue
        seen.add(key)
        unique.append(path)
    return unique


def pick_face(path: Path) -> tuple[int, str] | None:
    fallback: tuple[int, str] | None = None
    for index in range(16):
        try:
            face = ImageFont.truetype(str(path), size=40, index=index)
        except OSError:
            break
        name = " ".join(face.getname())
        if "Mono" in name:
            continue
        if "CJK JP" in name:
            return index, name
        if fallback is None:
            fallback = (index, name)
    return fallback


def resolve_font() -> None:
    global FONT_PATH, FONT_INDEX, FONT_NAME
    if FONT_PATH is not None:
        return
    for path in font_candidates():
        if not path.exists():
            continue
        picked = pick_face(path)
        if picked is None:
            continue
        FONT_INDEX, FONT_NAME = picked
        FONT_PATH = path
        log(f"font {FONT_NAME} ({path})")
        return
    raise SystemExit("日本語フォントが見つかりません。Windowsの游ゴシック太字か、Noto Sans CJK を入れてください。")


def font_px(size: int) -> ImageFont.FreeTypeFont:
    resolve_font()
    size = int(size)
    cached = FONT_CACHE.get(size)
    if cached is None:
        cached = ImageFont.truetype(str(FONT_PATH), size=size, index=FONT_INDEX)
        FONT_CACHE[size] = cached
    return cached


def text_width(text: str, font: ImageFont.FreeTypeFont) -> float:
    return float(_MEASURE.textlength(text, font=font))


def line_height(font: ImageFont.FreeTypeFont) -> int:
    box = font.getbbox("あAg")
    return (box[3] - box[1]) + 12


def wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    breaks = set("。！？、 ")
    closers = set("、。！？）」』")
    lines: list[str] = []
    for paragraph in str(text).split("\n"):
        rest = paragraph
        if rest == "":
            lines.append("")
            continue
        while rest:
            if text_width(rest, font) <= max_width:
                lines.append(rest)
                break
            fit = 1
            for index in range(1, len(rest) + 1):
                if text_width(rest[:index], font) <= max_width:
                    fit = index
                else:
                    break
            cut = fit
            for index in range(fit, max(1, int(fit * 0.45)), -1):
                if rest[index - 1] in breaks:
                    cut = index
                    break
            if cut < len(rest) and rest[cut] in closers and text_width(rest[: cut + 1], font) <= max_width * 1.06:
                cut += 1
            lines.append(rest[:cut])
            rest = rest[cut:]
    return lines or [""]


def draw_lines(
    draw: ImageDraw.ImageDraw,
    x: float,
    y: float,
    text: str,
    font: ImageFont.FreeTypeFont,
    fill: tuple[int, int, int, int] | tuple[int, int, int],
    max_width: int,
    stroke: int = 0,
    align: str = "center",
) -> int:
    lines = wrap_text(text, font, max_width)
    step = line_height(font)
    anchor = "mt" if align == "center" else "lt"
    stroke_fill = (0, 0, 0, 255) if len(fill) == 4 else (0, 0, 0)
    for index, line in enumerate(lines):
        draw.text(
            (x, y + index * step),
            line,
            font=font,
            fill=fill,
            anchor=anchor,
            stroke_width=stroke,
            stroke_fill=stroke_fill if stroke else None,
        )
    return len(lines) * step


def vgradient(top: tuple[int, int, int], bottom: tuple[int, int, int]) -> Image.Image:
    ramp = np.linspace(0.0, 1.0, HEIGHT, dtype=np.float32)[:, None]
    arr = (1.0 - ramp) * np.array(top, dtype=np.float32) + ramp * np.array(bottom, dtype=np.float32)
    tiled = np.repeat(arr[:, None, :], WIDTH, axis=1)
    return Image.fromarray(np.clip(tiled, 0, 255).astype(np.uint8), "RGB")


def composite(base: Image.Image, overlay: Image.Image) -> Image.Image:
    canvas = base.convert("RGBA")
    canvas.alpha_composite(overlay)
    return canvas.convert("RGB")


def night_bg() -> Image.Image:
    return vgradient((9, 11, 18), (4, 5, 9))


def draw_pr_badge(draw: ImageDraw.ImageDraw) -> None:
    x, y, width, height = pr_badge_box()
    draw.rounded_rectangle([x, y, x + width, y + height], radius=18, fill=(0, 0, 0, 210))
    draw.text((x + width / 2, y + height / 2), "PR", font=font_px(48), fill=(255, 255, 255, 255), anchor="mm")


def pr_check_masks() -> tuple[np.ndarray, np.ndarray]:
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw_pr_badge(ImageDraw.Draw(overlay))
    base = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 255))
    base.alpha_composite(overlay)
    x, y, width, height = pr_badge_box()
    crop = np.asarray(base.convert("RGB").crop((x, y, x + width, y + height)))
    glyph = (crop[:, :, 0] >= 220) & (crop[:, :, 1] >= 220) & (crop[:, :, 2] >= 220)
    plate = np.zeros((height, width), dtype=bool)
    plate[12 : height - 12, 16 : width - 16] = True
    plate &= crop.mean(axis=2) < 50
    plate &= ~glyph
    return glyph, plate


def draw_hud(draw: ImageDraw.ImageDraw, day: object, clock: str, floor: str) -> None:
    draw.ellipse([48, 52, 84, 88], fill=RED)
    draw.text((100, 70), f"DAY {day}", font=font_px(42), fill=RED, anchor="lm")
    draw.text((48, 108), clock, font=font_px(76), fill=WHITE, anchor="lt")
    draw.text((48, 200), floor, font=font_px(36), fill=GRAY, anchor="lt")


def draw_top_card(draw: ImageDraw.ImageDraw, card: dict) -> None:
    badge = str(card.get("badge") or "")
    title = str(card.get("title") or "")
    badge_font = font_px(34)
    pad_x, pad_y = 28, 12
    badge_w = text_width(badge, badge_font) + pad_x * 2
    badge_h = 64
    x = (WIDTH - badge_w) / 2
    y = 292
    draw.rounded_rectangle([x, y, x + badge_w, y + badge_h], radius=16, fill=RED)
    draw.text((WIDTH / 2, y + badge_h / 2), badge, font=badge_font, fill=WHITE, anchor="mm")
    title_h = draw_lines(draw, WIDTH / 2, y + badge_h + 22, title, font_px(68), WHITE, 920)
    line_y = y + badge_h + 22 + title_h + 8
    draw.rectangle([(WIDTH - 680) / 2, line_y, (WIDTH + 680) / 2, line_y + 6], fill=RED)


def paint_overlay(day: object, clock: str, floor: str, pr: bool, top: dict | None, subtitle: str | None, color: str) -> Image.Image:
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    if subtitle:
        draw.rectangle([0, 1300, WIDTH, 1620], fill=(0, 0, 0, 120))
    draw_hud(draw, day, clock, floor)
    if top:
        draw_top_card(draw, top)
    if subtitle:
        fill = YELLOW if color == "yellow" else WHITE
        draw_lines(draw, WIDTH / 2, 1350, subtitle, font_px(62), fill, 960, stroke=8)
    if pr:
        draw_pr_badge(draw)
    return overlay


def clock_for(job: dict, segment: dict | None) -> str:
    if segment and segment.get("clock"):
        return str(segment["clock"])
    choice = job.get("choice_card") or {}
    if choice.get("clock"):
        return str(choice["clock"])
    segments = job.get("segments") or []
    if segments:
        return str(segments[-1].get("clock") or "")
    return ""


def draw_stickman(
    draw: ImageDraw.ImageDraw,
    ox: float,
    oy: float,
    pose: str,
    scale: float = 1.0,
    sw: int = 8,
    eye: str = "small",
    phone_on: bool | None = None,
    earphones: bool = False,
) -> dict[str, tuple[float, float]]:
    def point(x: float, y: float) -> tuple[float, float]:
        return (ox + x * scale, oy + y * scale)

    def line(a: tuple[float, float], b: tuple[float, float]) -> None:
        draw.line([point(*a), point(*b)], fill=(255, 255, 255), width=sw)

    def outline(center: tuple[float, float], radius: float) -> None:
        x, y = point(*center)
        r = radius * scale
        draw.ellipse([x - r, y - r, x + r, y + r], outline=(255, 255, 255), width=sw)

    def dot(center: tuple[float, float], radius: float, fill: tuple[int, int, int]) -> None:
        x, y = point(*center)
        r = radius * scale
        draw.ellipse([x - r, y - r, x + r, y + r], fill=fill)

    if pose == "kneel":
        head, radius, hand = (0.0, 0.0), 28.0, (48.0, 74.0)
        outline(head, radius)
        line((0, 28), (0, 92))
        line((0, 42), (-58, 98))
        line((0, 42), hand)
        line((0, 92), (-42, 132))
        line((-42, 132), (16, 138))
        line((0, 92), (38, 138))
    else:
        head, radius, hand = (0.0, 0.0), 26.0, (36.0, 78.0)
        outline(head, radius)
        line((0, 26), (0, 108))
        line((0, 48), (-40, 100))
        line((0, 48), hand if phone_on is not None else (40, 104))
        line((0, 108), (-30, 176))
        line((0, 108), (30, 176))
    if eye == "big":
        dot((-12, -2), 9, (255, 255, 255))
        dot((12, -2), 9, (255, 255, 255))
        dot((-12, -2), 4, (12, 12, 14))
        dot((12, -2), 4, (12, 12, 14))
    else:
        dot((-8, -2), 3.2, (20, 20, 24))
        dot((8, -2), 3.2, (20, 20, 24))
    phone_at = point(*hand)
    if phone_on is not None:
        hx, hy = phone_at
        draw.rounded_rectangle([hx - 8, hy - 8, hx + 34, hy + 62], radius=7, fill=(22, 22, 26))
        screen = (86, 168, 255) if phone_on else (10, 10, 14)
        draw.rounded_rectangle([hx - 3, hy - 1, hx + 29, hy + 55], radius=4, fill=screen)
        phone_at = (hx + 12, hy + 24)
    if earphones:
        x, y = point(*head)
        r = radius * scale
        draw.arc([x - r - 10, y - r - 12, x + r + 10, y + r * 0.2], 200, 340, fill=(255, 255, 255), width=max(3, sw - 2))
        dot((-radius - 2, 8), 6, (255, 255, 255))
        dot((radius + 2, 8), 6, (255, 255, 255))
    return {"phone": phone_at, "head": point(*head)}


def paint_door(params: dict, ctx: dict, segment: dict) -> Image.Image:
    del segment
    img = night_bg()
    draw = ImageDraw.Draw(img)
    draw.polygon([(160, 360), (920, 360), (980, 1180), (100, 1180)], fill=(16, 17, 24))
    draw.polygon([(100, 1180), (980, 1180), (1040, 1500), (40, 1500)], fill=(10, 10, 14))
    dx, dy = ctx.get("shift") or (0, 0)
    x, y, width, height = 330 + dx, 390 + dy, 420, 700
    draw.rectangle([x - 18, y - 18, x + width + 18, y + height + 24], fill=(42, 28, 18))
    draw.rectangle([x, y, x + width, y + height], fill=(112, 74, 42))
    draw.rectangle([x + 28, y + 28, x + width - 28, y + height / 2 - 16], outline=(62, 40, 22), width=8)
    draw.rectangle([x + 28, y + height / 2 + 10, x + width - 28, y + height - 28], outline=(62, 40, 22), width=8)
    draw.ellipse([x + width - 78, y + height / 2 - 16, x + width - 46, y + height / 2 + 16], fill=(214, 186, 110))
    gap_y = y + height + 8
    draw.rectangle([x + 12, gap_y, x + width - 12, gap_y + 16], fill=(6, 6, 8))
    light = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    light_draw = ImageDraw.Draw(light)
    cx = x + width / 2
    top_y = gap_y + 16
    bot_y = min(HEIGHT - 40, top_y + 210)
    light_draw.polygon(
        [(cx - 150, top_y), (cx + 150, top_y), (cx + 360, bot_y), (cx - 360, bot_y)],
        fill=(255, 206, 80, 90),
    )
    light_draw.polygon(
        [(cx - 70, top_y), (cx + 70, top_y), (cx + 160, bot_y - 16), (cx - 160, bot_y - 16)],
        fill=(255, 230, 150, 120),
    )
    img = composite(img, light)
    if params.get("shadow_visible", True):
        shade = ImageDraw.Draw(img)
        for side, spread in ((-80, 48), (80, 54)):
            shade.polygon(
                [
                    (cx + side - 16, top_y),
                    (cx + side + 16, top_y),
                    (cx + side + spread, bot_y - 8),
                    (cx + side + spread - 34, bot_y - 8),
                ],
                fill=(5, 5, 8),
            )
    return img


def paint_room(params: dict, ctx: dict, segment: dict) -> Image.Image:
    del ctx, segment
    img = night_bg()
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 1180, WIDTH, HEIGHT], fill=(8, 8, 12))
    draw.rectangle([70, 560, 520, 1080], fill=(12, 18, 40))
    draw.ellipse([360, 640, 450, 730], fill=(232, 230, 210))
    star = random.Random(7)
    for _ in range(36):
        sx = star.randint(86, 500)
        sy = star.randint(580, 1040)
        draw.ellipse([sx, sy, sx + 3, sy + 3], fill=(255, 255, 255))
    draw.rectangle([70, 560, 520, 1080], outline=(70, 78, 96), width=8)
    draw.rectangle([620, 380, 1000, 1120], fill=(42, 30, 20))
    book_rng = random.Random(11)
    colors = [(160, 48, 48), (48, 90, 150), (150, 120, 48), (48, 120, 80), (120, 60, 140), (180, 90, 40)]
    for shelf in range(6):
        top = 410 + shelf * 115
        draw.rectangle([640, top + 78, 980, top + 92], fill=(78, 56, 34))
        cursor = 656
        for book in range(8):
            span = book_rng.randint(30, 44)
            draw.rectangle([cursor, top, cursor + span - 6, top + 78], fill=colors[(shelf + book) % len(colors)])
            cursor += span
    glow = params.get("phone_glow", False)
    phones = params.get("earphones_on", False)
    anchors = draw_stickman(draw, 540, 860, "kneel", scale=2.15, sw=10, phone_on=bool(glow), earphones=bool(phones))
    if glow:
        hx, hy = anchors["phone"]
        layer = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
        layer_draw = ImageDraw.Draw(layer)
        layer_draw.polygon(
            [(hx - 20, hy), (hx + 50, hy + 10), (hx + 220, hy + 260), (hx - 140, hy + 280)],
            fill=(70, 140, 255, 110),
        )
        img = composite(img, layer)
    return img


def phone_box() -> tuple[int, int, int, int]:
    return (250, 340, 580, 900)


def screen_box(phone: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
    x, y, width, height = phone
    return (x + 18, y + 58, width - 36, height - 96)


def draw_phone_shell(draw: ImageDraw.ImageDraw, phone: tuple[int, int, int, int], screen_fill: tuple[int, int, int]) -> tuple[int, int, int, int]:
    x, y, width, height = phone
    draw.rounded_rectangle([x, y, x + width, y + height], radius=54, fill=(28, 28, 34))
    sx, sy, sw, sh = screen_box(phone)
    draw.rounded_rectangle([sx, sy, sx + sw, sy + sh], radius=28, fill=screen_fill)
    notch_w = 150
    draw.rounded_rectangle([x + width / 2 - notch_w / 2, y + 18, x + width / 2 + notch_w / 2, y + 46], radius=12, fill=(16, 16, 20))
    draw.rounded_rectangle([x + width / 2 - 70, y + height - 28, x + width / 2 + 70, y + height - 16], radius=6, fill=(180, 180, 186))
    return (sx, sy, sw, sh)


def paint_phone_tap(params: dict, ctx: dict, segment: dict) -> Image.Image:
    del segment
    img = night_bg()
    draw = ImageDraw.Draw(img)
    phone = phone_box()
    screen = draw_phone_shell(draw, phone, (8, 8, 12))
    sx, sy, sw, sh = screen
    cols, rows = 4, 5
    pad = 28
    cell_w = (sw - pad * 2) / cols
    cell_h = (sh - pad * 2) / rows
    palette = [
        (255, 96, 96), (255, 176, 48), (255, 214, 64), (72, 196, 120),
        (64, 156, 255), (176, 96, 255), (255, 112, 168), (64, 210, 200),
        (255, 140, 72), (120, 144, 255), (255, 96, 128), (88, 176, 255),
        (196, 160, 72), (120, 200, 96), (255, 80, 80), (255, 64, 144),
        (80, 120, 220), (220, 120, 60), (90, 200, 170), (180, 180, 80),
    ]
    progress = float(ctx.get("progress") or 0.0)
    sns_index = 15
    sns_center = (0.0, 0.0)
    for index in range(cols * rows):
        row, col = divmod(index, cols)
        cx = sx + pad + cell_w * col + cell_w / 2
        cy = sy + pad + cell_h * row + cell_h / 2
        side = min(cell_w, cell_h) * 0.62
        color = (255, 64, 144) if index == sns_index else palette[index]
        draw.rounded_rectangle([cx - side / 2, cy - side / 2, cx + side / 2, cy + side / 2], radius=16, fill=color)
        if index == sns_index:
            sns_center = (cx, cy)
            draw.rounded_rectangle([cx - 16, cy - 12, cx + 18, cy + 14], radius=8, outline=(255, 255, 255), width=4)
    locked = bool(params.get("locked"))
    action = params.get("action")
    if locked:
        cx, cy = sx + sw / 2, sy + sh / 2
        draw.rounded_rectangle([cx - 36, cy - 16, cx + 36, cy + 48], radius=8, outline=(230, 230, 230), width=8)
        draw.arc([cx - 28, cy - 52, cx + 28, cy + 8], 180, 0, fill=(230, 230, 230), width=8)
    elif action == "tap_sns_icon":
        x, y, width, height = phone
        start = (x + width + 30, y + height - 20)
        reach = progress
        end = (start[0] + (sns_center[0] - start[0]) * reach, start[1] + (sns_center[1] - start[1]) * reach)
        draw.line([start, end], fill=(255, 255, 255), width=16)
        draw.ellipse([end[0] - 18, end[1] - 18, end[0] + 18, end[1] + 18], fill=(255, 255, 255))
        if progress > 0.35:
            ripple = (progress - 0.35) / 0.65
            radius = 18 + ripple * 110
            draw.ellipse(
                [sns_center[0] - radius, sns_center[1] - radius, sns_center[0] + radius, sns_center[1] + radius],
                outline=(255, 255, 255),
                width=5,
            )
            inner = radius * 0.55
            draw.ellipse(
                [sns_center[0] - inner, sns_center[1] - inner, sns_center[0] + inner, sns_center[1] + inner],
                outline=(255, 210, 230),
                width=3,
            )
    return img


def paint_window_grid(params: dict, ctx: dict, segment: dict) -> Image.Image:
    img = night_bg()
    draw = ImageDraw.Draw(img)
    bx, by, bw, bh = 140, 400, 800, 860
    draw.rounded_rectangle([bx, by, bx + bw, by + bh], radius=10, fill=(20, 22, 30))
    cols = rows = 5
    gap = 16
    cell_w = (bw - gap * (cols + 1)) / cols
    cell_h = (bh - gap * (rows + 1)) / rows
    mode = params.get("mode") or "all_lit"
    off: set[int] = set()
    if mode == "all_dark":
        off = set(range(25))
    elif mode == "sequential_blackout":
        order = list(range(25))
        random.Random(int(segment.get("id") or 0) * 17 + 3).shuffle(order)
        count = int(round(float(ctx.get("progress") or 0.0) * 25))
        off = set(order[: max(0, min(25, count))])
    for index in range(25):
        row, col = divmod(index, cols)
        x = bx + gap + col * (cell_w + gap)
        y = by + gap + row * (cell_h + gap)
        lit = index not in off
        fill = (255, 196, 96) if lit else (8, 8, 12)
        draw.rounded_rectangle([x, y, x + cell_w, y + cell_h], radius=6, fill=fill)
        if lit and index % 3 == 0:
            cx, cy = x + cell_w / 2, y + cell_h / 2 + 8
            tone = (40, 36, 32)
            draw.line([(cx, cy - 16), (cx, cy + 8)], fill=tone, width=3)
            draw.ellipse([cx - 7, cy - 30, cx + 7, cy - 16], outline=tone, width=2)
            draw.line([(cx, cy - 6), (cx - 10, cy + 4)], fill=tone, width=3)
            draw.line([(cx, cy - 6), (cx + 12, cy + 2)], fill=tone, width=3)
            draw.rectangle([cx + 10, cy - 2, cx + 16, cy + 8], fill=(80, 140, 220))
    return img


def paint_peephole(params: dict, ctx: dict, segment: dict) -> Image.Image:
    del ctx, segment
    yy, xx = np.mgrid[0:HEIGHT, 0:WIDTH]
    dist = np.sqrt((xx - WIDTH / 2) ** 2 + (yy - 860) ** 2)
    ring = 0.55 + 0.45 * np.sin(dist / 26.0)
    falloff = np.clip(1.0 - dist / 520.0, 0.0, 1.0)
    red = np.clip(18 + 170 * falloff * ring, 0, 255).astype(np.uint8)
    arr = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
    arr[:, :, 0] = red
    arr[dist > 540] = (4, 0, 0)
    img = Image.fromarray(arr, "RGB")
    draw = ImageDraw.Draw(img)
    holding = params.get("holding_phone", True)
    draw_stickman(draw, WIDTH / 2, 760, "stand", scale=2.5, sw=12, eye="big", phone_on=True if holding else None)
    tag = params.get("speaker_tag")
    if tag:
        draw_lines(draw, WIDTH / 2, 1248, str(tag), font_px(40), YELLOW, 860, stroke=6)
    return img


def paint_phone_message(params: dict, ctx: dict, segment: dict) -> Image.Image:
    del ctx, segment
    img = night_bg()
    draw = ImageDraw.Draw(img)
    screen = draw_phone_shell(draw, phone_box(), (12, 14, 20))
    sx, sy, sw, sh = screen
    card = [sx + 28, sy + 80, sx + sw - 28, sy + 80 + 360]
    draw.rounded_rectangle(card, radius=28, fill=(48, 50, 58))
    draw.text((sx + sw / 2, sy + 130), f"差出人：{params.get('sender') or '不明'}", font=font_px(32), fill=(186, 188, 196), anchor="mt")
    y = sy + 200
    body_white = str(params.get("body_white") or "")
    body_red = str(params.get("body_red") or "")
    if body_white:
        y += draw_lines(draw, sx + sw / 2, y, body_white, font_px(40), WHITE, sw - 120)
    if body_red:
        draw_lines(draw, sx + sw / 2, y + 8, body_red, font_px(40), (255, 64, 72, 255), sw - 120)
    return img


def paint_app(params: dict, ctx: dict, segment: dict) -> Image.Image:
    del segment
    state = params.get("state") or "select_horror_book"
    img = night_bg()
    draw = ImageDraw.Draw(img)
    if state == "dark_waveform_only":
        screen = draw_phone_shell(draw, phone_box(), (5, 5, 5))
        sx, sy, sw, sh = screen
        phase = float(ctx.get("phase") or 0.0)
        pts = []
        count = 64
        for index in range(count):
            u = index / (count - 1)
            env = math.sin(u * math.pi)
            yy = sy + sh / 2 + math.sin(u * 18 + phase * math.tau * 2) * env * (sh * 0.16)
            pts.append((sx + 36 + u * (sw - 72), yy))
        draw.line(pts, fill=(255, 122, 24), width=4)
        return img
    screen = draw_phone_shell(draw, phone_box(), (14, 16, 22))
    sx, sy, sw, sh = screen
    draw.text((sx + 36, sy + 36), "Audible", font=font_px(40), fill=(255, 140, 40), anchor="lt")
    if state == "select_horror_book":
        rows = [("都市伝説", False), ("怪談", True), ("実話怪談", False)]
        for index, (label, selected) in enumerate(rows):
            top = sy + 140 + index * 120
            fill = (64, 36, 16) if selected else (28, 30, 36)
            draw.rounded_rectangle([sx + 28, top, sx + sw - 28, top + 96], radius=18, fill=fill)
            draw.text((sx + 56, top + 48), label, font=font_px(36), fill=WHITE, anchor="lm")
            if selected:
                draw.polygon([(sx + sw - 90, top + 36), (sx + sw - 90, top + 68), (sx + sw - 58, top + 52)], fill=(255, 160, 48))
        return img
    progress = float(ctx.get("progress") or 0.0)
    draw.ellipse([sx + sw / 2 - 70, sy + sh / 2 - 120, sx + sw / 2 + 70, sy + sh / 2 + 20], fill=(255, 140, 40))
    if progress < 0.5:
        draw.polygon(
            [(sx + sw / 2 - 16, sy + sh / 2 - 80), (sx + sw / 2 - 16, sy + sh / 2 - 20), (sx + sw / 2 + 28, sy + sh / 2 - 50)],
            fill=(20, 16, 12),
        )
    else:
        draw.rectangle([sx + sw / 2 - 22, sy + sh / 2 - 78, sx + sw / 2 - 6, sy + sh / 2 - 24], fill=(20, 16, 12))
        draw.rectangle([sx + sw / 2 + 6, sy + sh / 2 - 78, sx + sw / 2 + 22, sy + sh / 2 - 24], fill=(20, 16, 12))
    lock_y = sy + sh / 2 + 80
    draw.rounded_rectangle([sx + sw / 2 - 36, lock_y, sx + sw / 2 + 36, lock_y + 56], radius=8, outline=WHITE, width=6)
    if progress < 0.45:
        draw.arc([sx + sw / 2 - 24, lock_y - 36, sx + sw / 2 + 24, lock_y + 16], 200, 20, fill=WHITE, width=6)
    else:
        draw.arc([sx + sw / 2 - 24, lock_y - 28, sx + sw / 2 + 24, lock_y + 20], 180, 0, fill=WHITE, width=6)
    if progress > 0.2:
        dim = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
        ImageDraw.Draw(dim).rectangle([sx, sy, sx + sw, sy + sh], fill=(0, 0, 0, int(160 * progress)))
        img = composite(img, dim)
    return img


def paint_morning(params: dict, ctx: dict, segment: dict) -> Image.Image:
    del ctx, segment
    ramp = np.linspace(0.0, 1.0, HEIGHT, dtype=np.float32)[:, None]
    stops = np.array([[22, 32, 78], [224, 112, 72], [244, 196, 130], [28, 24, 30]], dtype=np.float32)
    bands = np.array([0.0, 0.42, 0.68, 1.0], dtype=np.float32)
    idx = np.searchsorted(bands, ramp[:, 0], side="right") - 1
    idx = np.clip(idx, 0, len(stops) - 2)
    span = (bands[idx + 1] - bands[idx])
    local = (ramp[:, 0] - bands[idx]) / np.maximum(span, 1e-6)
    color = stops[idx] * (1 - local)[:, None] + stops[idx + 1] * local[:, None]
    tiled = np.repeat(color[:, None, :], WIDTH, axis=1)
    img = Image.fromarray(np.clip(tiled, 0, 255).astype(np.uint8), "RGB")
    draw = ImageDraw.Draw(img)
    rng = random.Random(4)
    cursor = 0
    while cursor < WIDTH:
        block_w = rng.randint(80, 170)
        block_h = rng.randint(180, 520)
        draw.rectangle([cursor, 1180 - block_h, cursor + block_w - 8, 1240], fill=(18, 16, 26))
        cursor += block_w
    draw.rectangle([64, 300, 1016, 1220], outline=(236, 236, 236), width=16)
    draw.line([(540, 300), (540, 1220)], fill=(236, 236, 236), width=10)
    draw.line([(64, 760), (1016, 760)], fill=(236, 236, 236), width=10)
    draw.rectangle([0, 1188, WIDTH, HEIGHT], fill=(16, 14, 18))
    if params.get("stickman_standing", True):
        draw_stickman(draw, 540, 860, "stand", scale=2.15, sw=10, phone_on=None)
    return img


def button_palette(name: str) -> tuple[tuple[int, int, int], tuple[int, int, int]]:
    if name == "green":
        return (14, 58, 34), (52, 214, 116)
    if name == "red":
        return (62, 16, 22), (230, 56, 64)
    return (24, 24, 28), (230, 230, 230)


def draw_option(draw: ImageDraw.ImageDraw, box: list[float], text: str, color_name: str) -> None:
    fill, border = button_palette(color_name)
    draw.rounded_rectangle(box, radius=28, fill=fill, outline=border, width=8)
    draw_lines(draw, (box[0] + box[2]) / 2, (box[1] + box[3]) / 2 - 36, text, font_px(40), WHITE, box[2] - box[0] - 36)


def paint_choice(job: dict) -> Image.Image:
    card = job.get("choice_card") or {}
    img = vgradient((10, 12, 18), (6, 8, 12))
    draw = ImageDraw.Draw(img)
    draw_lines(draw, WIDTH / 2, 520, str(card.get("question") or ""), font_px(72), WHITE, 900)
    left = card.get("left_option") or {}
    right = card.get("right_option") or {}
    draw_option(draw, [64, 860, 508, 1080], str(left.get("text") or ""), str(left.get("color") or "green"))
    draw_option(draw, [572, 860, 1016, 1080], str(right.get("text") or ""), str(right.get("color") or "red"))
    draw.text((WIDTH / 2, 1220), str(card.get("subtext") or ""), font=font_px(36), fill=GRAY, anchor="mt")
    return img


def paint_day_end(job: dict) -> Image.Image:
    card = job.get("day_end_card") or {}
    img = vgradient((12, 10, 16), (28, 8, 12))
    draw = ImageDraw.Draw(img)
    draw.text((WIDTH / 2, 460), str(card.get("title") or ""), font=font_px(96), fill=WHITE, anchor="mt")
    draw.text((WIDTH / 2, 600), str(card.get("subtitle") or ""), font=font_px(64), fill=RED, anchor="mt")
    draw.text((WIDTH / 2, 760), str(card.get("status") or ""), font=font_px(48), fill=WHITE, anchor="mt")
    label = str(card.get("button_text") or "")
    width = min(860, text_width(label, font_px(40)) + 80)
    x = (WIDTH - width) / 2
    draw.rounded_rectangle([x, 980, x + width, 1100], radius=40, fill=RED)
    draw.text((WIDTH / 2, 1040), label, font=font_px(40), fill=WHITE, anchor="mm")
    return img


def paint_promo(job: dict, progress: float) -> Image.Image:
    promo = job.get("promo_outro") or {}
    img = vgradient((8, 10, 16), (18, 12, 10))
    draw = ImageDraw.Draw(img)
    y = 340
    y += draw_lines(draw, WIDTH / 2, y, str(promo.get("headline") or ""), font_px(58), WHITE, 920)
    steps = promo.get("steps") or []
    weights = [float(step.get("duration_sec") or 1) for step in steps] or [1.0]
    total = sum(weights) or 1.0
    acc = 0.0
    current = 0
    for index, weight in enumerate(weights):
        if progress <= (acc + weight) / total:
            current = index
            break
        acc += weight
        current = index
    y += 30
    for index, step in enumerate(steps):
        top = y
        border = (255, 140, 40, 255) if index == current else (70, 74, 84, 255)
        fill = (48, 28, 14, 255) if index == current else (22, 24, 30, 255)
        draw.rounded_rectangle([80, top, 1000, top + 150], radius=24, fill=fill, outline=border, width=6)
        draw.ellipse([110, top + 46, 170, top + 106], fill=border)
        draw.text((140, top + 76), str(step.get("step_num") or index + 1), font=font_px(32), fill=(20, 16, 12, 255), anchor="mm")
        draw_lines(draw, 196, top + 36, str(step.get("text") or ""), font_px(34), WHITE, 760, align="left")
        y = top + 174
    y += 10
    draw.text((WIDTH / 2, y), str(promo.get("app_name") or ""), font=font_px(40), fill=(255, 160, 48, 255), anchor="mt")
    y += 70
    y += draw_lines(draw, WIDTH / 2, y, str(promo.get("sub_copy") or ""), font_px(32), GRAY, 900)
    cta = str(promo.get("cta_button_text") or "")
    draw.rounded_rectangle([90, y + 24, 990, y + 140], radius=28, fill=(255, 122, 24, 255))
    draw_lines(draw, WIDTH / 2, y + 48, cta, font_px(34), (20, 16, 12, 255), 820)
    return img


SCENE_PAINTERS = {
    "door_view": paint_door,
    "room_stickman": paint_room,
    "phone_tap": paint_phone_tap,
    "window_grid": paint_window_grid,
    "peephole_stickman": paint_peephole,
    "phone_message": paint_phone_message,
    "app_demo_screen": paint_app,
    "morning_window": paint_morning,
}


def paint_scene(job: dict, item: dict, segment: dict | None, ctx: dict) -> Image.Image:
    kind = item["kind"]
    if kind == "segment":
        if segment is None:
            raise SystemExit("segment がありません")
        scene = segment.get("scene")
        painter = SCENE_PAINTERS.get(scene)
        if painter is None:
            known = ", ".join(sorted(SCENE_PAINTERS))
            raise SystemExit(f"未知のsceneです: {scene} (対応: {known})")
        return painter(segment.get("scene_params") or {}, ctx, segment)
    if kind == "choice_card":
        return paint_choice(job)
    if kind == "day_end_card":
        return paint_day_end(job)
    if kind == "promo_outro":
        return paint_promo(job, float(ctx.get("progress") or 0.0))
    raise SystemExit(f"未知のkindです: {kind}")


def render_frame(job: dict, item: dict, segment: dict | None, ctx: dict) -> Image.Image:
    scene = paint_scene(job, item, segment, ctx)
    subtitle = None
    top = None
    color = "white"
    if segment is not None:
        subtitle = segment.get("subtitle")
        top = segment.get("top_card")
        color = segment.get("text_color") or "white"
    overlay = paint_overlay(
        job.get("day"),
        clock_for(job, segment),
        str(job.get("floor_label") or ""),
        bool(job.get("pr_badge")),
        top if top else None,
        subtitle,
        color,
    )
    return composite(scene, overlay)


def resolve_segment(job: dict, item: dict) -> dict | None:
    if item.get("kind") != "segment":
        return None
    inline = item.get("segment")
    if isinstance(inline, dict):
        return inline
    wanted = item.get("segment_id")
    for segment in job.get("segments") or []:
        if segment.get("id") == wanted:
            return segment
    raise SystemExit(f"segment_id {wanted} がジョブにありません")


def animation_plan(job: dict, item: dict, segment: dict | None) -> tuple[list[dict], list[float] | None]:
    params = (segment or {}).get("scene_params") or {}
    scene = (segment or {}).get("scene")
    if scene == "door_view" and params.get("shake"):
        rng = random.Random(int(segment.get("id") or 0) * 97 + 3)
        contexts = []
        for index in range(6):
            contexts.append({"shift": (rng.randint(-6, 6), rng.randint(-6, 6)), "progress": 0.0, "phase": index / 6})
        return contexts, None
    if scene == "window_grid" and params.get("mode") == "sequential_blackout":
        count = 8
        return [{"shift": (0, 0), "progress": index / (count - 1), "phase": index / (count - 1)} for index in range(count)], None
    if scene == "phone_tap" and params.get("action") == "tap_sns_icon" and not params.get("locked"):
        count = 6
        return [{"shift": (0, 0), "progress": index / (count - 1), "phase": index / (count - 1)} for index in range(count)], None
    if scene == "app_demo_screen" and params.get("state") == "dark_waveform_only":
        count = 8
        return [{"shift": (0, 0), "progress": 1.0, "phase": index / count} for index in range(count)], None
    if scene == "app_demo_screen" and params.get("state") == "press_play_and_lock":
        count = 4
        return [{"shift": (0, 0), "progress": index / (count - 1), "phase": index / (count - 1)} for index in range(count)], None
    if item.get("kind") == "promo_outro":
        steps = (job.get("promo_outro") or {}).get("steps") or []
        if not steps:
            return [{"shift": (0, 0), "progress": 0.0, "phase": 0.0}], None
        weights = [float(step.get("duration_sec") or 1) for step in steps]
        total = sum(weights) or 1.0
        contexts = []
        acc = 0.0
        for weight in weights:
            mid = (acc + weight / 2.0) / total
            contexts.append({"shift": (0, 0), "progress": mid, "phase": mid})
            acc += weight
        return contexts, weights
    return [{"shift": (0, 0), "progress": 0.0, "phase": 0.0}], None


def split_frames(total: int, weights: list[float]) -> list[int]:
    safe = [max(0.0001, weight) for weight in weights]
    raw = [total * weight / sum(safe) for weight in safe]
    counts = [int(math.floor(value)) for value in raw]
    remain = total - sum(counts)
    order = sorted(range(len(raw)), key=lambda index: raw[index] - counts[index], reverse=True)
    for index in range(remain):
        counts[order[index % len(counts)]] += 1
    return counts


def run_ffmpeg(args: list[str]) -> None:
    result = subprocess.run(args, capture_output=True)
    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", "replace")[-2000:]
        raise SystemExit(f"ffmpegが失敗しました:\n{detail}")


def encode_still(image: Image.Image, frames: int, out_mp4: Path) -> None:
    png = out_mp4.with_suffix(".png")
    image.save(png, format="PNG")
    run_ffmpeg(
        [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-loop", "1", "-framerate", str(FPS), "-i", str(png),
            "-frames:v", str(frames),
            "-c:v", "libx264", "-preset", "ultrafast", "-bf", "0",
            "-crf", "16", "-pix_fmt", "yuv420p", "-an", str(out_mp4),
        ]
    )
    png.unlink(missing_ok=True)


def concat_videos(parts: list[Path], out_mp4: Path) -> None:
    listing = out_mp4.with_suffix(".ffconcat")
    lines = ["ffconcat version 1.0"]
    for part in parts:
        lines.append(f"file '{part.resolve().as_posix()}'")
    listing.write_text("\n".join(lines) + "\n", encoding="utf-8")
    run_ffmpeg(
        [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-f", "concat", "-safe", "0", "-i", str(listing),
            "-c", "copy", str(out_mp4),
        ]
    )
    listing.unlink(missing_ok=True)


def encode_holds(holds: list[tuple[Image.Image, int]], out_mp4: Path) -> None:
    if len(holds) == 1:
        encode_still(holds[0][0], holds[0][1], out_mp4)
        return
    parts: list[Path] = []
    for index, (image, frames) in enumerate(holds):
        if frames <= 0:
            continue
        part = out_mp4.with_name(f"{out_mp4.stem}_k{index}.mp4")
        encode_still(image, frames, part)
        parts.append(part)
    concat_videos(parts, out_mp4)
    for part in parts:
        part.unlink(missing_ok=True)


def frame_spans(items: list[dict]) -> list[tuple[int, int]]:
    spans = []
    cursor = 0
    for item in items:
        end = int(round(float(item["end_sec"]) * FPS))
        if end < cursor:
            end = cursor
        spans.append((cursor, end))
        cursor = end
    return spans


def load_json(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(f"ファイルがありません: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def render_video(job_path: Path, timing_path: Path, audio_path: Path, out_path: Path) -> None:
    if not audio_path.exists():
        raise SystemExit(f"音声ファイルがありません: {audio_path}")
    job = load_json(job_path)
    timing = load_json(timing_path)
    items = sorted(timing.get("items") or [], key=lambda item: float(item["start_sec"]))
    if not items:
        raise SystemExit("audio_timing.json に items がありません")
    spans = frame_spans(items)
    total_frames = spans[-1][1]
    if total_frames <= 0:
        raise SystemExit("動画のフレーム数が 0 です")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    work = out_path.parent / "_work" / str(job.get("job_id") or "job")
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)
    parts: list[Path] = []
    try:
        for index, (item, (start, end)) in enumerate(zip(items, spans)):
            count = end - start
            if count <= 0:
                continue
            segment = resolve_segment(job, item)
            contexts, weights = animation_plan(job, item, segment)
            if weights is None:
                weights = [1.0] * len(contexts)
            counts = split_frames(count, weights)
            holds: list[tuple[Image.Image, int]] = []
            for ctx, frames in zip(contexts, counts):
                if frames <= 0:
                    continue
                holds.append((render_frame(job, item, segment, ctx), frames))
            part = work / f"part_{index:03d}.mp4"
            encode_holds(holds, part)
            parts.append(part)
            log(f"{item.get('kind')} {item.get('scene') or ''} frames={count} holds={len(holds)}")
        silent = work / "video.mp4"
        concat_videos(parts, silent)
        duration = total_frames / FPS
        run_ffmpeg(
            [
                "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                "-i", str(silent), "-i", str(audio_path),
                "-map", "0:v:0", "-map", "1:a:0",
                "-c:v", "copy", "-c:a", "aac", "-b:a", "160k",
                "-af", f"apad=whole_dur={duration:.6f}",
                "-t", f"{duration:.6f}",
                "-movflags", "+faststart",
                str(out_path),
            ]
        )
    finally:
        shutil.rmtree(work, ignore_errors=True)
    log(f"wrote {out_path} frames={total_frames} duration={total_frames / FPS:.3f}s")


def demo_jobs() -> list[dict]:
    jobs = []
    for name in ("episode_day2.json", "episode_day3.json"):
        path = ROOT / "jobs" / name
        if path.exists():
            jobs.append(load_json(path))
    if not jobs:
        raise SystemExit("jobs/episode_day2.json と episode_day3.json がありません")
    return jobs


def find_segment(jobs: list[dict], scene: str, pred=None) -> tuple[dict, dict]:
    for job in jobs:
        for segment in job["segments"]:
            if segment.get("scene") == scene and (pred is None or pred(segment)):
                return job, segment
    raise SystemExit(f"プレビュー用の scene がありません: {scene}")


def write_contact_sheet(items: list[tuple[str, Image.Image]], dest: Path) -> None:
    cols = 3
    thumb_w = 420
    thumb_h = int(thumb_w * HEIGHT / WIDTH)
    label_h = 56
    pad = 18
    rows = math.ceil(len(items) / cols)
    sheet_w = cols * thumb_w + (cols + 1) * pad
    sheet_h = 84 + rows * (thumb_h + label_h) + (rows + 1) * pad
    sheet = Image.new("RGB", (sheet_w, sheet_h), (12, 12, 14))
    draw = ImageDraw.Draw(sheet)
    draw.text((pad, 24), "yorunotana scenes", font=font_px(36), fill=WHITE, anchor="lt")
    for index, (label, image) in enumerate(items):
        col = index % cols
        row = index // cols
        x = pad + col * (thumb_w + pad)
        y = 84 + row * (thumb_h + label_h + pad)
        thumb = image.resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        sheet.paste(thumb, (x, y))
        draw.text((x + thumb_w / 2, y + thumb_h + 8), label, font=font_px(24), fill=WHITE, anchor="mt")
    sheet.save(dest)


def export_stills(out_dir: Path) -> None:
    jobs = demo_jobs()
    out_dir.mkdir(parents=True, exist_ok=True)
    labeled: list[tuple[str, Image.Image]] = []

    def add(name: str, label: str, image: Image.Image) -> None:
        image.save(out_dir / f"{name}.png")
        labeled.append((label, image))

    def from_segment(name: str, label: str, job: dict, segment: dict, ctx: dict | None = None) -> None:
        item = {"kind": "segment", "segment_id": segment["id"], "segment": segment}
        add(name, label, render_frame(job, item, segment, ctx or {"shift": (0, 0), "progress": 0.0, "phase": 0.0}))

    job, seg = find_segment(jobs, "door_view", lambda item: item["scene_params"].get("shadow_visible") and not item["scene_params"].get("shake"))
    from_segment("door_view", "door_view", job, seg)

    job, seg = find_segment(jobs, "room_stickman", lambda item: item.get("top_card"))
    room = json.loads(json.dumps(seg))
    room["scene_params"] = {"phone_glow": True, "earphones_on": True}
    from_segment("room_stickman", "room_stickman", job, room)

    job, seg = find_segment(jobs, "phone_tap", lambda item: item["scene_params"].get("action") == "tap_sns_icon")
    from_segment("phone_tap", "phone_tap", job, seg, {"shift": (0, 0), "progress": 0.72, "phase": 0.72})

    job, seg = find_segment(jobs, "window_grid", lambda item: item["scene_params"].get("mode") == "sequential_blackout")
    from_segment("window_grid", "window_grid", job, seg, {"shift": (0, 0), "progress": 0.45, "phase": 0.45})

    job, seg = find_segment(jobs, "peephole_stickman", lambda item: item["scene_params"].get("speaker_tag"))
    from_segment("peephole_stickman", "peephole_stickman", job, seg)

    job, seg = find_segment(jobs, "phone_message", lambda item: item["scene_params"].get("body_white"))
    from_segment("phone_message", "phone_message", job, seg)

    job, seg = find_segment(jobs, "app_demo_screen", lambda item: item["scene_params"].get("state") == "dark_waveform_only")
    from_segment("app_demo_screen", "app_demo_screen", job, seg, {"shift": (0, 0), "progress": 1.0, "phase": 0.35})

    job, seg = find_segment(jobs, "morning_window")
    from_segment("morning_window", "morning_window", job, seg)

    day2 = next(job for job in jobs if job["day"] == 2)
    day3 = next(job for job in jobs if job["day"] == 3)
    static = {"shift": (0, 0), "progress": 0.25, "phase": 0.25}
    add("choice_card", "choice_card", render_frame(day2, {"kind": "choice_card", "segment_id": None}, None, static))
    add("day_end_card", "day_end_card", render_frame(day2, {"kind": "day_end_card", "segment_id": None}, None, static))
    add("promo_outro", "promo_outro", render_frame(day3, {"kind": "promo_outro", "segment_id": None}, None, {"shift": (0, 0), "progress": 0.25, "phase": 0.25}))

    hud = composite(night_bg(), paint_overlay(2, "9:16 PM", "14階", False, None, None, "white"))
    add("overlay_hud", "HUD", hud)
    badge = composite(night_bg(), paint_overlay(3, "4:30 AM", "14階", True, None, None, "white"))
    # isolate the badge: paint only PR on the night plate
    only = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw_pr_badge(ImageDraw.Draw(only))
    add("overlay_pr_badge", "PRバッジ", composite(night_bg(), only))
    card = composite(night_bg(), paint_overlay(2, "9:16 PM", "14階", False, {"badge": "ルール5", "title": "SNSを開くな"}, None, "yellow"))
    add("overlay_top_card", "top_card", card)
    sub = composite(night_bg(), paint_overlay(2, "6:05 AM", "14階", False, None, "ドアは開けなかった。", "yellow"))
    add("overlay_subtitle", "字幕", sub)
    del hud, badge
    sheet = out_dir / "contact_sheet.png"
    write_contact_sheet(labeled, sheet)
    glyph, plate = pr_check_masks()
    log(f"stills {len(labeled)} -> {out_dir} glyph={int(glyph.sum())} plate={int(plate.sum())}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="14階の2Dフレームを描く")
    parser.add_argument("--job")
    parser.add_argument("--timing")
    parser.add_argument("--audio")
    parser.add_argument("--out")
    parser.add_argument("--stills", help="シーンとオーバーレイのPNGを書き出すディレクトリ")
    args = parser.parse_args(argv)
    if args.stills:
        export_stills(Path(args.stills))
        if not args.job:
            return 0
    if not args.job:
        parser.error("--job か --stills が必要です")
    missing = [name for name in ("timing", "audio", "out") if not getattr(args, name)]
    if missing:
        parser.error("--" + " --".join(missing) + " が必要です")
    render_video(Path(args.job), Path(args.timing), Path(args.audio), Path(args.out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
