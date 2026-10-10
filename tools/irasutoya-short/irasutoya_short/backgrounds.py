"""背景はいらすとやを使わず、コードで描く。"""

from __future__ import annotations

import math

import numpy as np
from PIL import Image, ImageDraw

from irasutoya_short.constants import HEIGHT, WIDTH


def render_bg(name: str, width: int = WIDTH, height: int = HEIGHT) -> np.ndarray:
    if name == "office":
        return _office(width, height, night=False)
    if name == "office_night":
        return _office(width, height, night=True)
    if name == "chat":
        return _chat(width, height)
    if name == "lines":
        base = _office(width, height, night=False)
        return _blend(base, concentration(width, height), 0.55)
    if name == "credit":
        img = Image.new("RGB", (width, height), (18, 22, 32))
        return np.array(img)
    raise ValueError(f"未知の背景: {name}")


def concentration(width: int = WIDTH, height: int = HEIGHT) -> np.ndarray:
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    cx, cy = width // 2, int(height * 0.42)
    for i in range(48):
        ang = (math.tau * i) / 48
        x2 = cx + math.cos(ang) * width
        y2 = cy + math.sin(ang) * height
        draw.line((cx, cy, x2, y2), fill=(255, 255, 255, 150), width=8 if i % 2 == 0 else 3)
    # 中心を空けてキャラの顔が読めるようにする
    mask = Image.new("L", (width, height), 255)
    mdraw = ImageDraw.Draw(mask)
    mdraw.ellipse((cx - 220, cy - 260, cx + 220, cy + 220), fill=0)
    img.putalpha(mask)
    return np.array(img)


def _blend(rgb: np.ndarray, overlay: np.ndarray, strength: float) -> np.ndarray:
    alpha = overlay[:, :, 3:4].astype(np.float32) / 255.0 * strength
    base = rgb.astype(np.float32)
    src = overlay[:, :, :3].astype(np.float32)
    out = src * alpha + base * (1 - alpha)
    return out.astype(np.uint8)


def _office(width: int, height: int, night: bool) -> np.ndarray:
    wall = (32, 40, 64) if night else (244, 236, 220)
    floor = (48, 42, 38) if night else (196, 164, 112)
    img = Image.new("RGB", (width, height), wall)
    draw = ImageDraw.Draw(img)
    floor_y = int(height * 0.72)
    draw.rectangle((0, floor_y, width, height), fill=floor)
    draw.rectangle((0, floor_y, width, floor_y + 18), fill=(90, 70, 48) if not night else (20, 20, 28))
    # 窓
    win = (40, 90, 420, int(height * 0.48))
    draw.rounded_rectangle(win, radius=12, fill=(18, 28, 48) if night else (198, 228, 255), outline=(80, 80, 90), width=8)
    if night:
        rng = np.random.default_rng(3)
        for _ in range(18):
            x = int(rng.integers(60, 390))
            y = int(rng.integers(110, int(height * 0.42)))
            draw.rectangle((x, y, x + 18, y + 12), fill=(255, 214, 90))
    else:
        draw.rectangle((70, 120, 200, 280), fill=(255, 255, 255))
        draw.rectangle((230, 150, 380, 300), fill=(170, 190, 210))
    # 蛍光灯
    light = (255, 244, 210) if not night else (90, 110, 150)
    draw.rounded_rectangle((width - 280, 40, width - 80, 70), radius=8, fill=light)
    # 机
    desk_y = int(height * 0.78)
    draw.rectangle((80, desk_y, width - 80, desk_y + 36), fill=(150, 110, 70) if not night else (70, 54, 40))
    # 時計（素材にしない）
    cx, cy, r = width - 160, 180, 54
    draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(255, 255, 255), outline=(40, 40, 40), width=6)
    draw.line((cx, cy, cx, cy - 30), fill=(20, 20, 20), width=4)
    draw.line((cx, cy, cx + 22, cy + 8), fill=(180, 40, 40), width=4)
    return np.array(img)


def _chat(width: int, height: int) -> np.ndarray:
    img = Image.new("RGB", (width, height), (230, 236, 242))
    draw = ImageDraw.Draw(img)
    phone = (int(width * 0.18), int(height * 0.08), int(width * 0.82), int(height * 0.62))
    draw.rounded_rectangle(phone, radius=36, fill=(250, 252, 255), outline=(40, 50, 60), width=8)
    draw.rectangle((phone[0] + 24, phone[1] + 70, phone[2] - 24, phone[1] + 130), fill=(220, 40, 40))
    # 全体送信の赤い帯は文字を後でテロップ側に任せる。帯だけ。
    bubble_w = phone[2] - phone[0] - 80
    y = phone[1] + 170
    for color in ((220, 245, 220), (255, 255, 255), (220, 245, 220)):
        draw.rounded_rectangle((phone[0] + 40, y, phone[0] + 40 + bubble_w, y + 90), radius=16, fill=color, outline=(180, 190, 180))
        y += 110
    # 請求書の紙
    paper = (int(width * 0.3), int(height * 0.66), int(width * 0.7), int(height * 0.9))
    draw.rounded_rectangle(paper, radius=8, fill=(255, 255, 255), outline=(30, 30, 30), width=4)
    for i in range(6):
        yy = paper[1] + 40 + i * 36
        draw.line((paper[0] + 30, yy, paper[2] - 30, yy), fill=(180, 180, 180), width=4)
    draw.ellipse((paper[2] - 150, paper[1] + 30, paper[2] - 40, paper[1] + 140), outline=(200, 30, 30), width=8)
    return np.array(img)
