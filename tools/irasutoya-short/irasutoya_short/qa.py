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
    "段階",
    "いろいろ",
    "パターン",
    "一覧",
    "駅員",
    "運転手",
    "車掌",
    "バス",
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


def multiple_faces(rgba: np.ndarray) -> bool:
    """同じ高さに、同じくらい大きい肌の塊が横並びなら、顔が複数ある。"""
    from irasutoya_short.sprites import _blobs, _skin_mask

    blobs = [
        blob
        for blob in _blobs(_skin_mask(rgba), step=2, min_pts=40)
        if blob["right"] - blob["left"] >= 36 and blob["bot"] - blob["top"] >= 36
    ]
    if len(blobs) < 2:
        return False
    blobs.sort(key=lambda blob: blob["area"], reverse=True)
    biggest = max(1, blobs[0]["area"])
    kept = [blob for blob in blobs if blob["area"] >= biggest * 0.5]
    for index, left in enumerate(kept):
        for right in kept[index + 1 :]:
            overlap_y = min(left["bot"], right["bot"]) - max(left["top"], right["top"])
            min_h = max(1, min(left["bot"] - left["top"], right["bot"] - right["top"]))
            overlap_x = min(left["right"], right["right"]) - max(left["left"], right["left"])
            if overlap_y / min_h > 0.45 and overlap_x <= 0:
                return True
    return False


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
        if multiple_faces(keyed):
            return "顔が横に複数ある"
        from irasutoya_short.sprites import mouth_anchor

        if mouth_anchor(keyed) is None:
            return "口の位置が取れない"
    ocr = _ocr_text(path)
    if ocr:
        for token in REJECT_TOKENS:
            if token in ocr:
                return f"絵の中の文字「{token}」"
        japanese = re.findall(r"[\u3040-\u30ff\u4e00-\u9fff]{2,}", ocr)
        if japanese:
            return f"文字が焼き込まれている: {japanese[0]}"
    return None


AIR_LIMIT = 1.5
SILENCE_NOISE = "-32dB"
FREEZE_NOISE = "-45dB"


def caption_overlaps_face(
    telop: np.ndarray,
    faces: list[tuple[int, int, int, int]],
    pad: int = 0,
) -> bool:
    if telop.ndim != 3 or telop.shape[2] < 4 or not faces:
        return False
    alpha = telop[:, :, 3] > 40
    height, width = alpha.shape
    for box in faces:
        x0 = max(0, int(box[0]) - pad)
        y0 = max(0, int(box[1]) - pad)
        x1 = min(width, int(box[2]) + pad)
        y1 = min(height, int(box[3]) + pad)
        if x1 <= x0 or y1 <= y0:
            continue
        if bool(alpha[y0:y1, x0:x1].any()):
            return True
    return False


def caption_hits_edge(telop: np.ndarray, margin: int = 8) -> bool:
    if telop.ndim != 3 or telop.shape[2] < 4 or margin <= 0:
        return False
    alpha = telop[:, :, 3] > 40
    if not bool(alpha.any()):
        return False
    height, width = alpha.shape
    return bool(
        alpha[:, :margin].any()
        or alpha[:, width - margin :].any()
        or alpha[:margin, :].any()
        or alpha[height - margin :, :].any()
    )


SAFE_MARGIN = 48


def ink_bbox(image: np.ndarray, alpha_min: int = 40) -> tuple[int, int, int, int] | None:
    if image.ndim != 3 or image.shape[2] < 4:
        return None
    ys, xs = np.where(image[:, :, 3] > alpha_min)
    if len(xs) == 0:
        return None
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def box_inside(inner: tuple[int, int, int, int], outer: tuple[int, int, int, int]) -> bool:
    return inner[0] >= outer[0] and inner[1] >= outer[1] and inner[2] <= outer[2] and inner[3] <= outer[3]


def safe_box(width: int, height: int, margin: int = SAFE_MARGIN) -> tuple[int, int, int, int]:
    return (margin, margin, width - margin, height - margin)


def caption_fit_problems(
    text_box: tuple[int, int, int, int] | None,
    container: tuple[int, int, int, int] | None,
    width: int,
    height: int,
) -> list[str]:
    """テロップの字が枠の中にあり、枠が画面の安全域に収まるかを返す。"""
    problems: list[str] = []
    if text_box is None or container is None:
        return ["caption missing"]
    if not box_inside(text_box, container):
        problems.append("caption outside its box")
    safe = safe_box(width, height)
    if not box_inside(container, safe) or not box_inside(text_box, safe):
        problems.append("caption outside the safe area")
    return problems


def distinct_stills(frames: list[np.ndarray], needed: int) -> bool:
    """見た目が needed 種類以上あるか。同じ絵の字幕違いでは足りない。"""
    if needed <= 1:
        return True
    kept: list[np.ndarray] = []
    for frame in frames:
        step_y = max(1, frame.shape[0] // 80)
        step_x = max(1, frame.shape[1] // 48)
        small = frame[::step_y, ::step_x].astype(np.int16)
        if all(float(np.mean(np.abs(small - prev))) >= 10.0 for prev in kept):
            kept.append(small)
    return len(kept) >= needed


def dead_air(path: str, limit: float = AIR_LIMIT) -> list[str]:
    """1.5秒を超える無音と、1.5秒を超える静止を返す。"""
    problems: list[str] = []
    problems.extend(_span_problems(path, "silence", f"silencedetect=n={SILENCE_NOISE}:d={limit}", limit))
    problems.extend(_span_problems(path, "freeze", f"freezedetect=n={FREEZE_NOISE}:d={limit}", limit))
    return problems


def _span_problems(path: str, kind: str, filter_arg: str, limit: float) -> list[str]:
    if shutil.which("ffmpeg") is None:
        raise RuntimeError("ffmpeg がありません")
    cmd = ["ffmpeg", "-hide_banner", "-i", str(path)]
    if kind == "silence":
        cmd.extend(["-af", filter_arg])
        start_key, duration_key = "silence_start", "silence_duration"
    else:
        cmd.extend(["-vf", filter_arg])
        start_key, duration_key = "freeze_start", "freeze_duration"
    cmd.extend(["-f", "null", "-"])
    proc = subprocess.run(cmd, capture_output=True, text=True)
    text = proc.stderr
    starts = [float(item) for item in re.findall(rf"{start_key}:\s*([0-9.]+)", text)]
    durations = [float(item) for item in re.findall(rf"{duration_key}:\s*([0-9.]+)", text)]
    if len(starts) > len(durations):
        match = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", text)
        if match:
            media = int(match.group(1)) * 3600 + int(match.group(2)) * 60 + float(match.group(3))
            durations.append(max(0.0, media - starts[len(durations)]))
    found: list[str] = []
    for seconds in durations:
        if seconds + 1e-3 >= limit:
            found.append(f"{kind} {seconds:.2f}s")
    return found
