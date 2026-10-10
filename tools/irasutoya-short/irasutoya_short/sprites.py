"""白背景を抜いて、口の位置に開き具合の違う口を描く。"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

def load_rgba(path: str | Path) -> np.ndarray:
    with Image.open(path) as im:
        arr = np.array(im.convert("RGBA"))
    return _crop_opaque(_key_edge_white(arr))


def _crop_opaque(arr: np.ndarray) -> np.ndarray:
    ys, xs = np.where(arr[:, :, 3] > 10)
    if len(xs) == 0:
        return arr
    pad = 2
    y0 = max(0, int(ys.min()) - pad)
    y1 = min(arr.shape[0], int(ys.max()) + pad + 1)
    x0 = max(0, int(xs.min()) - pad)
    x1 = min(arr.shape[1], int(xs.max()) + pad + 1)
    return arr[y0:y1, x0:x1]


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


def _row_median(alpha: np.ndarray, lum: np.ndarray, y: int, x0: int, x1: int) -> float:
    sl = alpha[y, x0:x1]
    if int(sl.sum()) < 3:
        return 255.0
    return float(np.median(lum[y, x0:x1][sl]))


def _span_width(alpha_row: np.ndarray, cx: int) -> int:
    if cx < 0 or cx >= len(alpha_row) or not alpha_row[cx]:
        xs = np.where(alpha_row)[0]
        if len(xs) == 0:
            return 40
        cx = int(xs[np.argmin(np.abs(xs - cx))])
    left = cx
    while left > 0 and alpha_row[left - 1]:
        left -= 1
    right = cx
    while right < len(alpha_row) - 1 and alpha_row[right + 1]:
        right += 1
    return max(16, right - left + 1)


def mouth_anchor(rgba: np.ndarray) -> tuple[int, int, int]:
    """肌の帯の直後にある暗い線を口にする。いらすとやは目が左右に分かれて中心は肌のまま。"""
    alpha = rgba[:, :, 3] > 40
    ys, xs = np.where(alpha)
    if len(xs) == 0:
        h, w = rgba.shape[:2]
        return w // 2, int(h * 0.35), max(16, w // 5)
    top, bot = int(ys.min()), int(ys.max())
    ycut = top + max(8, int((bot - top) * 0.32))
    cols = np.where(alpha[top:ycut].any(axis=0))[0]
    if len(cols) == 0:
        cols = xs
    left, right = int(cols.min()), int(cols.max())
    cx = (left + right) // 2
    lum = rgba[:, :, :3].astype(np.int16).mean(axis=2)
    x0, x1 = max(0, cx - 10), min(rgba.shape[1], cx + 10)
    meds = np.array([_row_median(alpha, lum, y, x0, x1) for y in range(top, bot + 1)], dtype=np.float32)
    hair_at = next((i for i, value in enumerate(meds) if value < 70), 0)
    skin = meds > 165
    skin_end = None
    index = hair_at
    while index < len(skin):
        if not skin[index]:
            index += 1
            continue
        end = index
        while end < len(skin) and skin[end]:
            end += 1
        if end - index >= 20:
            skin_end = top + end
            break
        index = end
    if skin_end is None:
        my = top + int((bot - top) * 0.28)
    else:
        window = meds[skin_end - top : skin_end - top + 20]
        my = skin_end + (int(np.argmin(window)) if len(window) else 0)
    my = int(np.clip(my, top + 2, bot - 2))
    face_y = max(top, my - 18)
    head_w = _span_width(alpha[face_y], cx)
    return cx, my, head_w


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
