"""Face-crop geometry for the 1.0x box and the 1.5x box."""

from __future__ import annotations

import math

from grokbuild.qa.records import FaceRead


def expand_box(
    box: tuple[float, float, float, float],
    scale: float,
    image_w: int,
    image_h: int,
) -> tuple[float, float, float, float] | None:
    if type(image_w) is not int or type(image_h) is not int:
        return None
    if image_w <= 0 or image_h <= 0:
        return None
    if isinstance(scale, bool) or not isinstance(scale, (int, float)):
        return None
    scale_f = float(scale)
    if not math.isfinite(scale_f) or scale_f <= 0:
        return None
    parsed = _finite_box(box)
    if parsed is None:
        return None
    x, y, w, h = parsed
    cx = x + (w / 2.0)
    cy = y + (h / 2.0)
    nw = w * scale_f
    nh = h * scale_f
    nx = cx - (nw / 2.0)
    ny = cy - (nh / 2.0)
    x1 = max(0.0, nx)
    y1 = max(0.0, ny)
    x2 = min(float(image_w), nx + nw)
    y2 = min(float(image_h), ny + nh)
    cw = x2 - x1
    ch = y2 - y1
    if cw <= 0.0 or ch <= 0.0:
        return None
    return (x1, y1, cw, ch)


def boxes_match(
    left: tuple[float, float, float, float] | None,
    right: tuple[float, float, float, float] | None,
    tol: float = 1e-6,
) -> bool:
    if left is None or right is None:
        return False
    if len(left) != 4 or len(right) != 4:
        return False
    return all(abs(float(a) - float(b)) <= tol for a, b in zip(left, right))


def build_face(
    box: tuple[float, float, float, float],
    age: float | None,
    scale: float,
    image_w: int,
    image_h: int,
    *,
    detected: bool = True,
) -> FaceRead:
    parsed = _finite_box(box)
    if parsed is None:
        stored = (0.0, 0.0, 0.0, 0.0)
        crop = (0.0, 0.0, 0.0, 0.0)
    else:
        stored = parsed
        expanded = expand_box(stored, scale, image_w, image_h)
        crop = expanded if expanded is not None else (0.0, 0.0, 0.0, 0.0)
    return FaceRead(box=stored, crop_box=crop, age_years=age, detected=detected)


def _finite_box(
    box: tuple[float, float, float, float],
) -> tuple[float, float, float, float] | None:
    if not isinstance(box, tuple) or len(box) != 4:
        return None
    values: list[float] = []
    for item in box:
        if isinstance(item, bool) or not isinstance(item, (int, float)):
            return None
        number = float(item)
        if not math.isfinite(number):
            return None
        values.append(number)
    x, y, w, h = values
    if w <= 0.0 or h <= 0.0:
        return None
    return (x, y, w, h)
