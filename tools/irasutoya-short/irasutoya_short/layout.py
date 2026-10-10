"""参考スクショがあれば、テロップの高さとキャラの左右を寄せる。"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image


def analyze_screenshots(paths: list[str | Path]) -> dict:
    """5〜10枚の静止画から、文字がありそうな帯と人物の左右を読む。"""
    if not paths:
        return default_layout()
    telop_ys: list[float] = []
    sides: list[float] = []
    for path in paths[:10]:
        with Image.open(path) as im:
            rgb = np.array(im.convert("RGB"))
        h, w = rgb.shape[:2]
        gray = rgb.mean(axis=2)
        # 横方向のコントラストが高い行をテロップ帯とみなす
        dx = np.abs(np.diff(gray.astype(np.float32), axis=1)).mean(axis=1)
        bottom = dx[int(h * 0.55) :]
        if bottom.size:
            rel = (int(h * 0.55) + int(np.argmax(bottom))) / h
            telop_ys.append(rel)
        mid = gray[int(h * 0.25) : int(h * 0.75)]
        # 白っぽくない画素の重心
        ink = mid < 210
        if ink.any():
            cols = ink.sum(axis=0)
            xs = np.arange(w)
            center = float((cols * xs).sum() / max(cols.sum(), 1)) / w
            sides.append(center)
    layout = default_layout()
    if telop_ys:
        layout["telop_y_ratio"] = float(np.median(telop_ys))
    if sides:
        layout["character_x_ratio"] = float(np.median(sides))
    layout["screenshot_count"] = len(paths[:10])
    return layout


def default_layout() -> dict:
    return {
        "telop_y_ratio": 0.84,
        "character_x_ratio": 0.5,
        "screenshot_count": 0,
    }
