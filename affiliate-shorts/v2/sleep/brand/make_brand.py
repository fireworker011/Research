"""ねむりの棚のアイコンとバナー。実在の人物は描かない。"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parent

FONT = "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc"
INK = (244, 240, 230)
CREAM = (231, 225, 212)
GOLD = (228, 201, 138)


def font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT, size, index=0)


def gradient(width: int, height: int, left: tuple[int, int, int], right: tuple[int, int, int]) -> Image.Image:
    image = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(image)
    for x in range(width):
        t = x / (width - 1)
        color = tuple(int(left[i] + (right[i] - left[i]) * t) for i in range(3))
        draw.line([(x, 0), (x, height)], fill=color)
    return image


def paste_crescent(base: Image.Image, box: tuple[int, int, int, int], hole: tuple[int, int, int, int]) -> None:
    mask = Image.new("L", base.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse(box, fill=255)
    draw.ellipse(hole, fill=0)
    color = Image.new("RGB", base.size, CREAM)
    base.paste(color, (0, 0), mask)


def shelf(draw: ImageDraw.ImageDraw, x: int, y: int, scale: float) -> None:
    def s(value: int) -> int:
        return int(value * scale)

    draw.rounded_rectangle((x, y, x + s(460), y + s(18)), radius=s(6), fill=GOLD)
    draw.rounded_rectangle((x + s(24), y - s(78), x + s(150), y), radius=s(28), fill=(198, 214, 232))
    draw.rounded_rectangle((x + s(176), y - s(110), x + s(292), y), radius=s(12), fill=(143, 126, 168))
    draw.rounded_rectangle((x + s(196), y - s(86), x + s(272), y - s(18)), radius=s(8), fill=(186, 170, 206))
    draw.rounded_rectangle((x + s(318), y - s(64), x + s(430), y), radius=s(10), fill=(226, 196, 154))


def make_icon() -> Image.Image:
    image = gradient(800, 800, (28, 38, 72), (8, 10, 22))
    draw = ImageDraw.Draw(image)
    draw.ellipse((48, 48, 752, 752), outline=GOLD, width=4)
    paste_crescent(image, (250, 128, 530, 408), (318, 96, 620, 392))
    draw = ImageDraw.Draw(image)
    shelf(draw, 170, 500, 1)
    title = "ねむりの棚"
    face = font(72)
    box = draw.textbbox((0, 0), title, font=face)
    tw = box[2] - box[0]
    draw.text(((800 - tw) / 2, 560), title, font=face, fill=INK)
    sub = "睡眠と寝具"
    sub_face = font(32)
    box = draw.textbbox((0, 0), sub, font=sub_face)
    sw = box[2] - box[0]
    draw.text(((800 - sw) / 2, 650), sub, font=sub_face, fill=GOLD)
    return image


def make_banner() -> Image.Image:
    image = gradient(2560, 1440, (10, 14, 28), (62, 36, 28))
    draw = ImageDraw.Draw(image)
    paste_crescent(image, (80, 280, 560, 760), (210, 220, 720, 720))
    draw = ImageDraw.Draw(image)
    shelf(draw, 80, 1180, 1.15)
    draw.rounded_rectangle((2160, 430, 2460, 1020), radius=28, fill=(92, 58, 44))
    draw.rounded_rectangle((2208, 500, 2412, 760), radius=22, fill=(226, 196, 154))
    draw.rounded_rectangle((2208, 790, 2412, 960), radius=18, fill=(186, 170, 206))

    # YouTubeの全端末で残る中央 1546×423 の中に名前を置く。
    title = "ねむりの棚"
    face = font(112)
    draw.text((1280, 640), title, font=face, fill=INK, anchor="mm")
    draw.line((1040, 710, 1520, 710), fill=GOLD, width=3)
    handle = "@nemuri_tana"
    handle_face = font(46)
    draw.text((1280, 760), handle, font=handle_face, fill=GOLD, anchor="mm")
    line = "睡眠と寝具を、出典つきで"
    line_face = font(36)
    draw.text((1280, 830), line, font=line_face, fill=CREAM, anchor="mm")
    return image


if __name__ == "__main__":
    icon = make_icon()
    banner = make_banner()
    icon.save(OUT / "icon.png", "PNG")
    banner.save(OUT / "banner.png", "PNG")
    print(icon.size, banner.size)
