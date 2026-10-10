"""ダウンロードしたいらすとやを見て、文字入り・季節違い・2人組を弾く。"""

from __future__ import annotations

import re
import shutil
import subprocess
from collections import deque

import numpy as np
from PIL import Image

from irasutoya_short.sprites import load_rgba

# 記事が挙げている事故: 文字が焼き込まれた絵、正月飾り、2人組。
REJECT_TOKENS = (
    "二人",
    "２人",
    "2人",
    "カップル",
    "親子",
    "家族",
    "集合",
    "グループ",
    "友達",
    "会話",
    "会議",
    "打ち合わせ",
    "正月",
    "年賀",
    "鏡餅",
    "門松",
    "クリスマス",
    "ハロウィン",
    "バレンタイン",
    "ひな祭",
    "こどもの日",
    "七夕",
    "水着",
    "桜",
    "紅葉",
    "雪だるま",
    "吹き出し",
    "セリフ",
    "せりふ",
    "文字入り",
    "メッセージ",
    "年賀状",
    "タイトル",
    "過労死",
    "死亡",
    "白衣",
)


def title_rejection(title: str, alt: str, gender: str) -> str | None:
    blob = f"{title} {alt}"
    for token in REJECT_TOKENS:
        if token in blob:
            return f"タイトルに「{token}」"
    if "男性" in blob and "女性" in blob:
        return "男女が同じ絵"
    if gender == "男性" and "女性" in alt and "男性" not in alt:
        return "女性の絵"
    if gender == "女性" and "男性" in alt and "女性" not in alt:
        return "男性の絵"
    return None


def _boxes(mask: np.ndarray) -> list[tuple[int, int, int, int, int]]:
    """連結成分の (x0, y0, x1, y1, area)。"""
    h, w = mask.shape
    seen = np.zeros_like(mask, dtype=bool)
    boxes: list[tuple[int, int, int, int, int]] = []
    for y in range(h):
        for x in range(w):
            if not mask[y, x] or seen[y, x]:
                continue
            q: deque[tuple[int, int]] = deque([(y, x)])
            seen[y, x] = True
            x0 = x1 = x
            y0 = y1 = y
            area = 0
            while q:
                cy, cx = q.popleft()
                area += 1
                x0, x1 = min(x0, cx), max(x1, cx)
                y0, y1 = min(y0, cy), max(y1, cy)
                for ny, nx in ((cy - 1, cx), (cy + 1, cx), (cy, cx - 1), (cy, cx + 1)):
                    if ny < 0 or nx < 0 or ny >= h or nx >= w:
                        continue
                    if seen[ny, nx] or not mask[ny, nx]:
                        continue
                    seen[ny, nx] = True
                    q.append((ny, nx))
            boxes.append((x0, y0, x1, y1, area))
    return boxes


def _side_by_side(a: tuple[int, int, int, int, int], b: tuple[int, int, int, int, int]) -> bool:
    ay0, ay1 = a[1], a[3]
    by0, by1 = b[1], b[3]
    y_overlap = max(0, min(ay1, by1) - max(ay0, by0))
    min_h = max(1, min(ay1 - ay0, by1 - by0))
    ax0, ax1 = a[0], a[2]
    bx0, bx1 = b[0], b[2]
    x_overlap = max(0, min(ax1, bx1) - max(ax0, bx0))
    min_w = max(1, min(ax1 - ax0, bx1 - bx0))
    return y_overlap / min_h > 0.5 and x_overlap / min_w < 0.15


def body_count(alpha: np.ndarray) -> int:
    """頭の高さが揃って左右に並んでいるときだけ2人とする。

    白シャツが透過して腕だけ分かれる絵は、腕のてっぺんが頭より低いので数えない。
    """
    if alpha.size == 0:
        return 0
    opaque = alpha > 20
    if int(opaque.sum()) < 30:
        return 0
    step = max(1, int(max(alpha.shape) // 160))
    small = opaque[::step, ::step]
    total = int(small.sum())
    boxes = [b for b in _boxes(small) if b[4] > total * 0.18]
    if len(boxes) >= 2:
        figure_top = min(b[1] for b in boxes)
        figure_bot = max(b[3] for b in boxes)
        head_line = figure_top + max(2, int((figure_bot - figure_top) * 0.12))
        heads = [b for b in boxes if b[1] <= head_line]
        for i, a in enumerate(heads):
            for b in heads[i + 1 :]:
                if _side_by_side(a, b):
                    return 2
    return 1 if opaque.any() else 0


def _ocr_text(path: str) -> str:
    if shutil.which("tesseract") is None:
        return ""
    try:
        out = subprocess.run(
            ["tesseract", path, "stdout", "-l", "jpn+eng", "--psm", "6", "tsv"],
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""
    words: list[str] = []
    for line in out.stdout.splitlines()[1:]:
        cols = line.split("\t")
        if len(cols) < 12:
            continue
        try:
            conf = float(cols[10])
        except ValueError:
            continue
        word = cols[11].strip()
        if conf >= 55 and len(word) >= 2 and any(ch.isalnum() or "\u3040" <= ch <= "\u9fff" for ch in word):
            words.append(word)
    return " ".join(words)


def inspect_image(path: str, title: str, alt: str, gender: str, kind: str) -> str | None:
    """不採用理由を返す。採用なら None。"""
    reason = title_rejection(title, alt, gender)
    if reason:
        return reason
    with Image.open(path) as im:
        rgba = np.array(im.convert("RGBA"))
    if rgba.shape[0] < 40 or rgba.shape[1] < 40:
        return "画像が小さすぎる"
    if kind == "person":
        keyed = load_rgba(path)
        if body_count(keyed[:, :, 3]) >= 2:
            return "2人以上に見える"
    ocr = _ocr_text(path)
    if ocr:
        for token in REJECT_TOKENS:
            if token in ocr:
                return f"絵の中の文字「{token}」"
        japanese = re.findall(r"[\u3040-\u30ff\u4e00-\u9fff]{2,}", ocr)
        if japanese:
            return f"文字が焼き込まれている: {japanese[0]}"
    return None
