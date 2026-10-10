"""白背景を抜いて、口の位置に開き具合の違う口を描く。"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

MOUTH_Y_RATIO = 0.72


def load_rgba(path: str | Path) -> np.ndarray:
    with Image.open(path) as im:
        arr = np.array(im.convert("RGBA"))
    return _key_edge_white(arr)


def _key_edge_white(arr: np.ndarray) -> np.ndarray:
    alpha = arr[:, :, 3]
    if int(alpha[0, 0]) < 20 and int(alpha[0, -1]) < 20 and int(alpha[-1, 0]) < 20:
        return arr
    rgb = arr[:, :, :3]
    near = (rgb[:, :, 0] > 242) & (rgb[:, :, 1] > 242) & (rgb[:, :, 2] > 242)
    if not (near[0, 0] or near[0, -1] or near[-1, 0] or near[-1, -1]):
        return arr
    step = 2
    small = near[::step, ::step]
    bg = _flood_from_border(small)
    full = np.repeat(np.repeat(bg, step, axis=0), step, axis=1)
    full = full[: near.shape[0], : near.shape[1]]
    out = arr.copy()
    out[full, 3] = 0
    return out


def _flood_from_border(near: np.ndarray) -> np.ndarray:
    bg = np.zeros_like(near)
    bg[0, :] = near[0, :]
    bg[-1, :] = near[-1, :]
    bg[:, 0] = near[:, 0]
    bg[:, -1] = near[:, -1]
    for _ in range(max(near.shape)):
        prev = bg
        dil = bg.copy()
        dil[1:, :] |= bg[:-1, :]
        dil[:-1, :] |= bg[1:, :]
        dil[:, 1:] |= bg[:, :-1]
        dil[:, :-1] |= bg[:, 1:]
        bg = dil & near
        if np.array_equal(bg, prev):
            break
    return bg


def mouth_anchor(rgba: np.ndarray) -> tuple[int, int, int]:
    alpha = rgba[:, :, 3] > 20
    ys, xs = np.where(alpha)
    if len(xs) == 0:
        h, w = rgba.shape[:2]
        return w // 2, int(h * 0.35), w // 5
    top, bot = int(ys.min()), int(ys.max())
    left, right = int(xs.min()), int(xs.max())
    height = bot - top + 1
    widths = np.zeros(height, dtype=np.int32)
    for i, y in enumerate(range(top, bot + 1)):
        cols = np.where(alpha[y, left : right + 1])[0]
        if len(cols):
            widths[i] = int(cols.max() - cols.min() + 1)
    zone = widths[: max(3, int(len(widths) * 0.55))]
    peak_i = int(np.argmax(zone))
    neck_i = min(len(widths) - 1, peak_i + max(4, int(len(widths) * 0.2)))
    for i in range(peak_i + 1, len(widths)):
        if widths[i] < widths[peak_i] * 0.72:
            neck_i = i
            break
    head_h = max(8, neck_i)
    my = int(top + MOUTH_Y_RATIO * head_h)
    my = min(bot - 2, max(top + 2, my))
    cols = np.where(alpha[my])[0]
    mx = int((cols.min() + cols.max()) / 2) if len(cols) else (left + right) // 2
    head_w = max(16, int(widths[peak_i]))
    return mx, my, head_w


def skin_color(rgba: np.ndarray, mx: int, my: int, head_w: int) -> np.ndarray:
    r = max(4, head_w // 16)
    y0, y1 = max(0, my - r), min(rgba.shape[0], my + r)
    x0, x1 = max(0, mx - r * 2), min(rgba.shape[1], mx + r * 2)
    patch = rgba[y0:y1, x0:x1]
    rgb = patch[:, :, :3]
    alpha = patch[:, :, 3] > 200
    lum = rgb.mean(axis=2)
    ok = alpha & (lum > 150) & (lum < 242)
    if int(ok.sum()) < 8:
        return np.array([255, 214, 196], dtype=np.uint8)
    return np.median(rgb[ok], axis=0).astype(np.uint8)


def _fill_ellipse(img: np.ndarray, cx: float, cy: float, rx: float, ry: float, color: tuple[int, int, int, int]) -> None:
    if rx < 1 or ry < 1:
        return
    x0 = max(0, int(cx - rx - 1))
    x1 = min(img.shape[1], int(cx + rx + 2))
    y0 = max(0, int(cy - ry - 1))
    y1 = min(img.shape[0], int(cy + ry + 2))
    if x1 <= x0 or y1 <= y0:
        return
    yy, xx = np.ogrid[y0:y1, x0:x1]
    mask = ((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2 <= 1.0
    region = img[y0:y1, x0:x1]
    region[mask] = color


def draw_mouth(rgba: np.ndarray, mx: int, my: int, head_w: int, openness: float, skin: np.ndarray) -> np.ndarray:
    out = rgba.copy()
    skin_px = (int(skin[0]), int(skin[1]), int(skin[2]), 255)
    cover_rx = max(4, int(head_w * 0.075))
    cover_ry = max(3, int(head_w * 0.05))
    _fill_ellipse(out, mx, my, cover_rx, cover_ry, skin_px)
    open_amt = float(np.clip(openness, 0.0, 1.0))
    if open_amt < 0.08:
        _fill_ellipse(out, mx, my + 1, cover_rx * 0.72, max(1.2, head_w * 0.01), (90, 45, 45, 255))
        return out
    rx = head_w * (0.04 + 0.055 * open_amt)
    ry = head_w * (0.015 + 0.075 * open_amt)
    _fill_ellipse(out, mx, my + ry * 0.15, rx, ry, (50, 12, 18, 255))
    if open_amt > 0.38:
        _fill_ellipse(out, mx, my - ry * 0.15, rx * 0.72, max(1.5, ry * 0.32), (250, 248, 242, 255))
    return out


def mouth_levels(rgba: np.ndarray, levels: int = 7) -> tuple[list[np.ndarray], tuple[int, int, int]]:
    mx, my, head_w = mouth_anchor(rgba)
    skin = skin_color(rgba, mx, my, head_w)
    frames = [draw_mouth(rgba, mx, my, head_w, i / (levels - 1), skin) for i in range(levels)]
    return frames, (mx, my, head_w)


def scale_rgba(arr: np.ndarray, height: int) -> np.ndarray:
    h, w = arr.shape[:2]
    if h <= 0 or height <= 0:
        return arr
    nw = max(1, int(round(w * (height / h))))
    im = Image.fromarray(arr, "RGBA").resize((nw, height), Image.Resampling.LANCZOS)
    return np.array(im)


def mark_mouth(rgba: np.ndarray, mx: int, my: int) -> np.ndarray:
    out = rgba.copy()
    _fill_ellipse(out, mx, my, 8, 8, (255, 0, 0, 255))
    return out
