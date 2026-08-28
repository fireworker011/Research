#!/usr/bin/env python3
"""Autumn note banners at 1280x670. Exact BANNER_10 strings. Do not git-add PNGs."""
from __future__ import annotations

import os
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1280, 670
FONT_PATH = "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc"
OUT_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../../output/sprint/banners")
)

BANNERS = [
    ("01", "秋の告知", "leaf"),
    ("02", "顔も声も出さない", "notebook"),
    ("03", "毎日1本出す", "pencil"),
    ("04", "短尺のまま", "hourglass"),
    ("05", "手順は別記事", "sticky"),
    ("06", "同じアカウント", "two_notebooks"),
    ("07", "未完成なら出さない", "can"),
    ("08", "続報", "envelope"),
    ("09", "準備中", "frame"),
    ("10", "公開は別判断", "handle"),
]


def wood_desk() -> Image.Image:
    img = Image.new("RGB", (W, H), (92, 58, 32))
    px = img.load()
    for y in range(H):
        for x in range(W):
            grain = ((x * 13 + y * 7) % 17) - 8
            stripe = 8 if (y // 18) % 2 == 0 else -6
            r = max(40, min(150, 98 + grain + stripe + (x // 80)))
            g = max(24, min(100, 62 + grain // 2 + stripe // 2))
            b = max(16, min(70, 34 + grain // 3))
            px[x, y] = (r, g, b)
    light = Image.new("L", (W, H), 0)
    ld = ImageDraw.Draw(light)
    ld.ellipse((-80, -120, 520, 420), fill=210)
    light = light.filter(ImageFilter.GaussianBlur(90))
    overlay = Image.new("RGB", (W, H), (255, 236, 200))
    return Image.composite(overlay, img, light)


def mug(draw: ImageDraw.ImageDraw, x: int, y: int) -> None:
    draw.ellipse((x, y + 70, x + 110, y + 120), fill=(214, 206, 196))
    draw.rounded_rectangle((x + 8, y, x + 102, y + 96), 8, fill=(232, 224, 212))
    draw.arc((x + 88, y + 18, x + 138, y + 72), 270, 90, fill=(210, 200, 188), width=10)
    draw.ellipse((x + 18, y + 8, x + 92, y + 28), fill=(246, 240, 230))
    draw.ellipse((x + 28, y + 14, x + 82, y + 26), fill=(120, 78, 48))


def notebook(draw: ImageDraw.ImageDraw, x: int, y: int, color=(48, 72, 92)) -> None:
    draw.rounded_rectangle((x + 6, y + 8, x + 186, y + 128), 4, fill=(28, 28, 28))
    draw.rounded_rectangle((x, y, x + 180, y + 120), 4, fill=color)
    draw.line((x + 18, y + 8, x + 18, y + 112), fill=(210, 186, 120), width=4)


def leaf(draw: ImageDraw.ImageDraw, x: int, y: int) -> None:
    draw.ellipse((x, y, x + 70, y + 36), fill=(176, 86, 32))
    draw.polygon([(x + 8, y + 18), (x + 70, y + 8), (x + 64, y + 28)], fill=(148, 62, 22))
    draw.line((x + 6, y + 18, x + 68, y + 18), fill=(92, 40, 16), width=2)


def pencil(draw: ImageDraw.ImageDraw, x: int, y: int) -> None:
    draw.rectangle((x, y, x + 160, y + 14), fill=(196, 148, 52))
    draw.polygon([(x + 160, y), (x + 188, y + 7), (x + 160, y + 14)], fill=(214, 186, 140))
    draw.polygon([(x + 176, y + 4), (x + 188, y + 7), (x + 176, y + 10)], fill=(40, 40, 40))
    draw.rectangle((x, y, x + 18, y + 14), fill=(180, 64, 52))


def hourglass(draw: ImageDraw.ImageDraw, x: int, y: int) -> None:
    draw.rectangle((x, y, x + 56, y + 10), fill=(72, 52, 36))
    draw.rectangle((x, y + 86, x + 56, y + 96), fill=(72, 52, 36))
    draw.polygon([(x + 8, y + 10), (x + 48, y + 10), (x + 28, y + 48)], fill=(210, 186, 140))
    draw.polygon([(x + 8, y + 86), (x + 48, y + 86), (x + 28, y + 48)], fill=(210, 186, 140))
    draw.ellipse((x + 16, y + 18, x + 40, y + 32), fill=(168, 120, 64))


def sticky(draw: ImageDraw.ImageDraw, x: int, y: int) -> None:
    draw.rectangle((x + 6, y + 6, x + 86, y + 86), fill=(180, 160, 80))
    draw.rectangle((x, y, x + 80, y + 80), fill=(244, 228, 140))


def can(draw: ImageDraw.ImageDraw, x: int, y: int) -> None:
    draw.rounded_rectangle((x, y + 18, x + 72, y + 110), 8, fill=(168, 168, 160))
    draw.ellipse((x, y, x + 72, y + 36), fill=(196, 196, 188))
    draw.ellipse((x + 10, y + 8, x + 62, y + 28), fill=(120, 120, 116))


def envelope(draw: ImageDraw.ImageDraw, x: int, y: int) -> None:
    draw.rectangle((x, y + 20, x + 150, y + 110), fill=(236, 228, 212))
    draw.polygon([(x, y + 20), (x + 75, y + 70), (x + 150, y + 20)], fill=(220, 210, 190))
    draw.line((x, y + 20, x + 75, y + 70), fill=(180, 168, 148), width=2)
    draw.line((x + 150, y + 20, x + 75, y + 70), fill=(180, 168, 148), width=2)


def frame(draw: ImageDraw.ImageDraw, x: int, y: int) -> None:
    draw.rectangle((x, y, x + 120, y + 90), outline=(72, 52, 36), width=10)
    draw.rectangle((x + 12, y + 12, x + 108, y + 78), fill=(232, 220, 196))


def handle(draw: ImageDraw.ImageDraw, x: int, y: int) -> None:
    draw.rectangle((x, y, x + 18, y + 140), fill=(86, 64, 44))
    draw.ellipse((x + 6, y + 48, x + 70, y + 92), outline=(168, 148, 92), width=10)
    draw.ellipse((x + 2, y + 58, x + 22, y + 82), fill=(140, 120, 72))


PROPS = {
    "leaf": lambda d: leaf(d, 40, 560),
    "notebook": lambda d: notebook(d, 70, 430),
    "pencil": lambda d: pencil(d, 80, 560),
    "hourglass": lambda d: hourglass(d, 80, 480),
    "sticky": lambda d: sticky(d, 70, 500),
    "two_notebooks": lambda d: (notebook(d, 50, 430), notebook(d, 160, 450, (48, 72, 92))),
    "can": lambda d: can(d, 80, 470),
    "envelope": lambda d: envelope(d, 50, 470),
    "frame": lambda d: frame(d, 70, 480),
    "handle": lambda d: handle(d, 70, 430),
}


def fit_font(text: str, max_w: int) -> ImageFont.FreeTypeFont:
    size = 96
    while size >= 36:
        font = ImageFont.truetype(FONT_PATH, size)
        if font.getlength(text) <= max_w:
            return font
        size -= 2
    return ImageFont.truetype(FONT_PATH, 36)


def render_one(idx: str, text: str, prop: str, dest: str) -> tuple[int, int]:
    img = wood_desk()
    draw = ImageDraw.Draw(img)
    mug(draw, 1040, 430)
    PROPS[prop](draw)
    font = fit_font(text, W - 160)
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (W - tw) // 2 - bbox[0]
    y = 210 - bbox[1]
    # shadow then cream text — no extra glyphs
    draw.text((x + 3, y + 3), text, font=font, fill=(40, 24, 12))
    draw.text((x, y), text, font=font, fill=(248, 240, 224))
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    img.save(dest, "PNG")
    with Image.open(dest) as check:
        return check.size


def main() -> None:
    os.makedirs(OUT_DIR, exist_ok=True)
    for idx, text, prop in BANNERS:
        path = os.path.join(OUT_DIR, f"banner_{idx}.png")
        w, h = render_one(idx, text, prop, path)
        print(f"{idx}\t{w}x{h}\t{text}\t{path}")
        if (w, h) != (W, H):
            raise SystemExit(f"size fail {idx}: {w}x{h}")


if __name__ == "__main__":
    main()
