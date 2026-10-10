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
    face_width: int = 0
    face_height: int = 0


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


def _single_mouths(parts: list[dict], face_w: int, center: float) -> list[dict]:
    """左右一対の黒点（目・手）は口にしない。"""
    paired: set[int] = set()
    for i, left in enumerate(parts):
        for j in range(i + 1, len(parts)):
            right = parts[j]
            same_row = abs(left["y"] - right["y"]) <= 14
            apart = abs(left["x"] - right["x"]) >= face_w * 0.12
            if same_row and apart:
                paired.add(i)
                paired.add(j)
    singles = []
    for index, part in enumerate(parts):
        if index in paired:
            continue
        if abs(part["x"] - center) > face_w * 0.14:
            continue
        singles.append(part)
    return singles


def _pair_rows(parts: list[dict], face_w: int) -> list[tuple[dict, dict]]:
    rows: list[tuple[dict, dict]] = []
    used: set[int] = set()
    for i, left in enumerate(parts):
        if i in used:
            continue
        for j in range(i + 1, len(parts)):
            if j in used:
                continue
            right = parts[j]
            same_row = abs(left["y"] - right["y"]) <= 14
            apart = abs(left["x"] - right["x"]) >= max(12, face_w * 0.12)
            if same_row and apart:
                rows.append((left, right))
                used.add(i)
                used.add(j)
                break
    rows.sort(key=lambda pair: pair[0]["y"] + pair[1]["y"])
    return rows


def _mouth_below_eyes(parts: list[dict], box: dict) -> MouthAnchor | None:
    """目の下、次の左右の点（手）より上に口を置く。"""
    face_w = max(1, box["right"] - box["left"])
    rows = _pair_rows(parts, face_w)
    if not rows:
        return None
    left, right = rows[0]
    eye_y = (left["y"] + right["y"]) / 2
    eye_x = (left["x"] + right["x"]) / 2
    eye_gap = abs(left["x"] - right["x"])
    below = eye_y + eye_gap * 0.75
    if len(rows) > 1:
        below = (rows[1][0]["y"] + rows[1][1]["y"]) / 2
    gap_y = max(8.0, below - eye_y)
    y = int(eye_y + min(gap_y * 0.38, max(6.0, gap_y - 16)))
    width = max(18, int(eye_gap * 0.58))
    face_h = max(1, box["bot"] - box["top"])
    return MouthAnchor(int(round(eye_x)), y, width, max(4, int(gap_y * 0.2)), face_w, face_h)


def _lower_face_anchor(skin: np.ndarray, box: dict) -> MouthAnchor:
    """口の線が無い顔。いちばん広い行から、細る手前の下顔に置く。"""
    left, right = box["left"], box["right"]
    top, bot = box["top"], box["bot"]
    widths = [int(skin[y, left : right + 1].sum()) for y in range(top, bot + 1)]
    peak_i = int(np.argmax(widths[: max(1, int(len(widths) * 0.85))]))
    peak = max(1, widths[peak_i])
    jaw = bot
    run = 0
    for index in range(peak_i + 4, len(widths)):
        if widths[index] < peak * 0.78:
            run += 1
            if run >= 3:
                jaw = top + index - 2
                break
        else:
            run = 0
    span = max(4, jaw - (top + peak_i))
    y = min(jaw - 4, top + peak_i + int(span * 0.62))
    y = max(top + 4, min(bot - 2, y))
    xs = np.where(skin[y, left : right + 1])[0]
    x = int(left + float(xs.mean())) if len(xs) else (left + right) // 2
    face_w = max(1, right - left)
    face_h = max(1, jaw - top)
    width = max(14, int(min(face_w, widths[peak_i]) * 0.16))
    return MouthAnchor(x, y, width, 4, face_w, face_h)


def mouth_anchor(rgba: np.ndarray) -> MouthAnchor | None:
    """顔の中央、鼻より下の口を返す。左右に並ぶ目や手は使わない。"""
    box = _face_box(rgba)
    if box is None:
        return None
    skin = _skin_mask(rgba)
    chin = _chin_y(skin, box)
    lum = rgba[:, :, :3].astype(np.float32).mean(axis=2)
    alpha = rgba[:, :, 3] > 40
    face_w = max(1, box["right"] - box["left"])
    face_h = max(1, box["bot"] - box["top"])
    center = (box["left"] + box["right"]) / 2
    parts = [part for part in _dark_parts(lum, alpha, box, chin + 12) if part["y"] <= chin + 8]
    singles = _single_mouths(parts, face_w, center)
    if singles:
        mouth = max(singles, key=lambda part: (part["bottom"], part["width"]))
        return MouthAnchor(mouth["x"], mouth["y"], mouth["width"], mouth["height"], face_w, face_h)
    below = _mouth_below_eyes(parts, box)
    if below is not None:
        return below
    return _lower_face_anchor(skin, box)


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


def _talk_width(anchor: MouthAnchor) -> float:
    """閉じた線が細い顔でも、頭の高さに収まる口にする。"""
    stroke = max(8.0, float(anchor.width))
    face_w = float(anchor.face_width or 0)
    face_h = float(anchor.face_height or 0)
    if face_w < 24:
        return stroke
    talk = max(stroke, face_w * 0.22)
    if face_h > 24:
        talk = min(talk, face_h * 0.24)
    return talk


def draw_mouth(rgba: np.ndarray, anchor: MouthAnchor, openness: float, skin: np.ndarray) -> np.ndarray:
    """元の口の線を肌で隠し、あごが下へ開く口を描く。"""
    out = rgba.copy()
    skin_px = (int(skin[0]), int(skin[1]), int(skin[2]), 255)
    mx, my = float(anchor.x), float(anchor.y)
    talk_w = _talk_width(anchor)
    open_amt = float(np.clip(openness, 0.0, 1.0))
    cover_rx = max(talk_w * 0.58, float(anchor.width) * 0.75)
    cover_ry = max(talk_w * 0.20, float(anchor.height) * 0.85, 4.0)
    _fill_ellipse(out, mx, my, cover_rx, cover_ry, skin_px)
    if open_amt < 0.10:
        _fill_ellipse(out, mx, my, talk_w * 0.42, max(1.8, talk_w * 0.045), (110, 52, 52, 255))
        return out
    rx = talk_w * (0.40 + 0.12 * open_amt)
    ry = talk_w * (0.08 + 0.26 * open_amt)
    # 上端は元の口の近くに置き、開きは下へ伸ばす。
    cy = my + ry * 0.55
    lip = (
        int(skin[0] * 0.72),
        int(min(255, skin[1] * 0.48)),
        int(min(255, skin[2] * 0.45)),
        255,
    )
    _fill_ellipse(out, mx, cy, rx * 1.14, ry * 1.22, lip)
    _fill_ellipse(out, mx, cy, rx, ry, (58, 14, 20, 255))
    if open_amt > 0.34:
        _fill_ellipse(out, mx, cy - ry * 0.48, rx * 0.62, max(1.6, ry * 0.24), (250, 248, 242, 255))
    if open_amt > 0.68:
        _fill_ellipse(out, mx, cy + ry * 0.28, rx * 0.48, max(1.6, ry * 0.22), (186, 78, 84, 255))
    return out


def mouth_levels(rgba: np.ndarray, levels: int = 12) -> tuple[list[np.ndarray], MouthAnchor | None]:
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
