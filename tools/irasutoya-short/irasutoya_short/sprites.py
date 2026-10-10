"""白背景を抜いて、口の位置に開き具合の違う口を描く。"""

from __future__ import annotations

from collections import deque
from pathlib import Path
from typing import NamedTuple

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


class MouthAnchor(NamedTuple):
    x: int
    y: int
    width: int
    height: int


def _skin_mask(rgba: np.ndarray) -> np.ndarray:
    alpha = rgba[:, :, 3] > 40
    red = rgba[:, :, 0].astype(np.int16)
    green = rgba[:, :, 1].astype(np.int16)
    blue = rgba[:, :, 2].astype(np.int16)
    lum = (red + green + blue) / 3
    peach = (red > 150) & (green > 90) & (blue > 60) & (red > blue + 15) & (lum < 245) & (lum > 120)
    return alpha & peach


def _blobs(mask: np.ndarray, step: int = 2, min_pts: int = 60) -> list[dict]:
    small = mask[::step, ::step]
    height, width = small.shape
    seen = np.zeros_like(small)
    found: list[dict] = []
    for y in range(height):
        for x in np.where(small[y] & ~seen[y])[0]:
            if seen[y, x]:
                continue
            queue: deque[tuple[int, int]] = deque([(y, int(x))])
            seen[y, x] = True
            count = 0
            top = bot = y
            left = right = int(x)
            while queue:
                cy, cx = queue.popleft()
                count += 1
                top, bot = min(top, cy), max(bot, cy)
                left, right = min(left, cx), max(right, cx)
                for ny, nx in ((cy - 1, cx), (cy + 1, cx), (cy, cx - 1), (cy, cx + 1)):
                    if 0 <= ny < height and 0 <= nx < width and small[ny, nx] and not seen[ny, nx]:
                        seen[ny, nx] = True
                        queue.append((ny, nx))
            if count < min_pts:
                continue
            found.append(
                {
                    "area": count,
                    "top": top * step,
                    "bot": bot * step,
                    "left": left * step,
                    "right": right * step,
                }
            )
    return found


def _face_box(rgba: np.ndarray) -> dict | None:
    skin = _skin_mask(rgba)
    alpha = rgba[:, :, 3] > 40
    ys, xs = np.where(alpha)
    if len(xs) == 0:
        return None
    fig_top, fig_bot = int(ys.min()), int(ys.max())
    fig_h = max(1, fig_bot - fig_top)
    candidates = []
    for blob in _blobs(skin):
        box_h = blob["bot"] - blob["top"]
        box_w = blob["right"] - blob["left"]
        if box_h < 50 or box_w < 40:
            continue
        if blob["top"] > fig_top + fig_h * 0.72:
            continue
        candidates.append(blob)
    if not candidates:
        return None
    highest = min(blob["top"] for blob in candidates)
    near = [blob for blob in candidates if blob["top"] <= highest + 40]
    return max(near, key=lambda blob: blob["area"])


def _chin_y(skin: np.ndarray, box: dict) -> int:
    """肌の幅が細る行。首・襟・手元はこの下に落ちる。"""
    left, right = box["left"], box["right"]
    top, bot = box["top"], box["bot"]
    widths = np.array([int(skin[y, left : right + 1].sum()) for y in range(top, bot + 1)], dtype=np.int32)
    if len(widths) < 12:
        return bot
    peak_i = int(np.argmax(widths[: max(1, int(len(widths) * 0.8))]))
    peak = int(widths[peak_i])
    run = 0
    for index in range(peak_i + 6, len(widths)):
        if widths[index] < peak * 0.42:
            run += 1
            if run >= 4:
                return top + index - 3
        else:
            run = 0
    return bot


def _dark_parts(lum: np.ndarray, alpha: np.ndarray, box: dict, y_limit: int) -> list[dict]:
    top, bot = box["top"], min(box["bot"], y_limit)
    left, right = box["left"], box["right"]
    face_w = max(1, right - left)
    face_h = max(1, box["bot"] - top)
    cx = (left + right) // 2
    band = max(8, int(face_w * 0.24))
    x0, x1 = max(0, cx - band), min(lum.shape[1], cx + band)
    y0 = top + int(face_h * 0.30)
    y1 = bot
    region = alpha[y0:y1, x0:x1] & (lum[y0:y1, x0:x1] < 125)
    if not region.any():
        return []
    height, width = region.shape
    seen = np.zeros_like(region)
    parts: list[dict] = []
    ys, xs = np.where(region)
    for y, x in zip(ys.tolist(), xs.tolist()):
        if seen[y, x]:
            continue
        queue: deque[tuple[int, int]] = deque([(y, x)])
        seen[y, x] = True
        pts_y = [y]
        pts_x = [x]
        while queue:
            cy, cx = queue.pop()
            for ny, nx in ((cy - 1, cx), (cy + 1, cx), (cy, cx - 1), (cy, cx + 1)):
                if 0 <= ny < height and 0 <= nx < width and region[ny, nx] and not seen[ny, nx]:
                    seen[ny, nx] = True
                    queue.append((ny, nx))
                    pts_y.append(ny)
                    pts_x.append(nx)
        if len(pts_y) < 8:
            continue
        py = np.asarray(pts_y)
        px = np.asarray(pts_x)
        part_w = int(px.max() - px.min() + 1)
        part_h = int(py.max() - py.min() + 1)
        if part_w < max(6, int(face_w * 0.05)) or part_w > int(face_w * 0.34):
            continue
        if part_h > int(face_h * 0.36):
            continue
        mid_x = x0 + float(px.mean())
        if abs(mid_x - ((left + right) / 2)) > face_w * 0.18:
            continue
        parts.append(
            {
                "x": int(round(mid_x)),
                "y": int(round(y0 + float(py.mean()))),
                "width": part_w,
                "height": max(2, part_h),
                "bottom": y0 + int(py.max()),
            }
        )
    return parts


def _dip_anchor(rgba: np.ndarray, box: dict, y_limit: int) -> MouthAnchor | None:
    """黒線がない口。中心の輝度が一段落ちて、また戻る行を口にする。"""
    lum = rgba[:, :, :3].astype(np.float32).mean(axis=2)
    alpha = rgba[:, :, 3] > 40
    left, right = box["left"], box["right"]
    top, bot = box["top"], min(box["bot"], y_limit)
    face_w = max(1, right - left)
    cx = (left + right) // 2
    half = max(6, int(face_w * 0.14))
    x0, x1 = max(0, cx - half), min(rgba.shape[1], cx + half)
    y_start = top + int((bot - top) * 0.22)
    meds: list[tuple[int, float]] = []
    for y in range(y_start, bot - 4):
        sl = lum[y, x0:x1]
        sa = alpha[y, x0:x1]
        if int(sa.sum()) < 8:
            continue
        meds.append((y, float(np.median(sl[sa]))))
    if len(meds) < 12:
        return None
    values = np.array([value for _, value in meds], dtype=np.float32)
    best_i = None
    best_depth = 8.0
    span = 6
    for index in range(span, len(values) - span):
        around = max(float(values[index - span : index].max()), float(values[index + 1 : index + span + 1].max()))
        depth = around - float(values[index])
        if depth > best_depth:
            best_depth = depth
            best_i = index
    if best_i is None:
        return None
    y = meds[best_i][0]
    width = max(12, int(face_w * 0.16))
    return MouthAnchor(cx, y, width, 4)


def mouth_anchor(rgba: np.ndarray) -> MouthAnchor | None:
    """顔の中で、鼻より下にある暗い口の線を返す。襟や顎の輪郭は幅が広すぎるので捨てる。"""
    box = _face_box(rgba)
    if box is None:
        return None
    chin = _chin_y(_skin_mask(rgba), box)
    lum = rgba[:, :, :3].astype(np.float32).mean(axis=2)
    alpha = rgba[:, :, 3] > 40
    parts = [part for part in _dark_parts(lum, alpha, box, chin + 12) if part["y"] <= chin + 8]
    if parts:
        mouth = max(parts, key=lambda part: (part["bottom"], part["width"]))
        return MouthAnchor(mouth["x"], mouth["y"], mouth["width"], mouth["height"])
    return _dip_anchor(rgba, box, chin)


def skin_color(rgba: np.ndarray, mx: int, my: int, mouth_w: int) -> np.ndarray:
    gap = max(4, mouth_w // 5)
    band = max(6, mouth_w // 6)
    y1 = max(0, my - gap)
    y0 = max(0, y1 - band)
    x0, x1 = max(0, mx - mouth_w // 2), min(rgba.shape[1], mx + mouth_w // 2)
    patch = rgba[y0:y1, x0:x1]
    if patch.size == 0:
        return np.array([255, 214, 196], dtype=np.uint8)
    rgb = patch[:, :, :3]
    alpha = patch[:, :, 3] > 200
    lum = rgb.mean(axis=2)
    ok = alpha & (lum > 140) & (lum < 242)
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


def draw_mouth(rgba: np.ndarray, anchor: MouthAnchor, openness: float, skin: np.ndarray) -> np.ndarray:
    out = rgba.copy()
    skin_px = (int(skin[0]), int(skin[1]), int(skin[2]), 255)
    mx, my = anchor.x, anchor.y
    cover_rx = max(4.0, anchor.width * 0.55)
    cover_ry = max(3.0, anchor.height * 0.55, anchor.width * 0.16)
    _fill_ellipse(out, mx, my, cover_rx, cover_ry, skin_px)
    open_amt = float(np.clip(openness, 0.0, 1.0))
    if open_amt < 0.08:
        _fill_ellipse(out, mx, my, cover_rx * 0.72, max(1.4, anchor.width * 0.035), (90, 45, 45, 255))
        return out
    rx = anchor.width * (0.42 + 0.08 * open_amt)
    ry = max(2.0, anchor.width * (0.05 + 0.32 * open_amt))
    ry = min(ry, max(cover_ry, anchor.width * 0.42))
    _fill_ellipse(out, mx, my, rx, ry, (50, 12, 18, 255))
    if open_amt > 0.38:
        _fill_ellipse(out, mx, my - ry * 0.22, rx * 0.62, max(1.5, ry * 0.28), (250, 248, 242, 255))
    return out


def mouth_levels(rgba: np.ndarray, levels: int = 7) -> tuple[list[np.ndarray], MouthAnchor | None]:
    anchor = mouth_anchor(rgba)
    if anchor is None:
        return [rgba.copy() for _ in range(levels)], None
    skin = skin_color(rgba, anchor.x, anchor.y, anchor.width)
    frames = [draw_mouth(rgba, anchor, i / (levels - 1), skin) for i in range(levels)]
    return frames, anchor


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
