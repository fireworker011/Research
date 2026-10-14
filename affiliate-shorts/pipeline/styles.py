"""動画ごとの見た目。同じ型を次の動画へ丸ごと渡さない。"""

from __future__ import annotations

import csv
import math
import random
from pathlib import Path

import numpy as np

PIPELINE_DIR = Path(__file__).resolve().parent
FONT_DIR = PIPELINE_DIR / "fonts"
LOG_PATH = PIPELINE_DIR / "style-log.csv"
AXES = ("C", "P", "T", "F", "H", "M", "B", "L", "A")
THUMB_AXES = ("C", "P", "T", "F")
CPT = ("C", "P", "T")
PREV_SHARED_MAX = 2
LAST5_SHARED_MAX = 3
THUMB_CPT_SHARED_MAX = 1
GATE_MIN = 20.0
GATE_MAX = 30.0
FPS = 24

LOG_FIELDS = (
    "date",
    "line",
    "video_id",
    "status",
    "signature",
    "thumb_signature",
    "shared_axes_with_prev",
    "shared_axes_max_last5",
    "bgm_track",
    "length_sec",
    "irasutoya_count",
    "credit_ok",
    "notes",
)

_FONTS = {
    "kaku_bold": FONT_DIR / "ZenKakuGothicNew-Bold.ttf",
    "kaku_regular": FONT_DIR / "ZenKakuGothicNew-Regular.ttf",
    "maru": FONT_DIR / "ZenMaruGothic-Bold.ttf",
    "mincho": FONT_DIR / "ZenOldMincho-Bold.ttf",
    "hand": FONT_DIR / "YuseiMagic-Regular.ttf",
    "ud": FONT_DIR / "BIZUDPGothic-Bold.ttf",
    "pop": FONT_DIR / "RocknRollOne-Regular.ttf",
}

# 防災の軸。字幕の位置だけで、塗りつぶしの帯は作らない。
_BOUSAI = {
    "C": {
        "C1": {"character_x": 0.78, "character_h": 0.40, "motif": "diagram", "office": 0.25},
        "C2": {"character_x": 0.76, "character_h": 0.46, "motif": "checklist", "office": 0.2},
        "C3": {"character_x": 0.50, "character_h": 0.56, "motif": "room", "office": 0.82},
        "C4": {"character_x": 0.50, "character_h": 0.44, "motif": "qa", "office": 0.3},
        "C5": {"character_x": 0.72, "character_h": 0.44, "motif": "timeline", "office": 0.25},
        "C6": {"character_x": 0.50, "character_h": 0.40, "motif": "items", "office": 0.22},
    },
    "P": {
        "P1": {"wall": (248, 244, 236), "floor": (232, 122, 46), "accent": (214, 84, 18), "caption": (40, 36, 32, 255)},
        "P2": {"wall": (18, 42, 84), "floor": (24, 58, 110), "accent": (255, 206, 46), "caption": (255, 214, 64, 255)},
        "P3": {"wall": (92, 96, 102), "floor": (70, 72, 76), "accent": (196, 48, 42), "caption": (255, 236, 220, 255)},
        "P4": {"wall": (232, 242, 232), "floor": (46, 110, 78), "accent": (20, 90, 60), "caption": (18, 48, 36, 255)},
        "P5": {"wall": (16, 16, 18), "floor": (28, 28, 24), "accent": (240, 196, 32), "caption": (255, 214, 48, 255)},
        "P6": {"wall": (214, 236, 244), "floor": (24, 64, 112), "accent": (16, 52, 96), "caption": (14, 36, 72, 255)},
    },
    "T": {
        "T1": {"text_y": 0.16, "text_align": "center", "text_scale": 1.0},
        "T2": {"text_y": 0.84, "text_align": "center", "text_scale": 1.0},
        "T3": {"text_y": 0.40, "text_align": "left", "text_scale": 0.92},
        "T4": {"text_y": 0.58, "text_align": "center", "text_scale": 1.0},
        "T5": {"text_y": 0.46, "text_align": "center", "text_scale": 1.18},
        "T6": {"text_y": 0.78, "text_align": "right", "text_scale": 0.9},
    },
    "F": {
        "F1": {"body": "kaku_bold", "emphasis": "kaku_bold"},
        "F2": {"body": "maru", "emphasis": "maru"},
        "F3": {"body": "ud", "emphasis": "ud"},
        "F4": {"body": "mincho", "emphasis": "mincho"},
        "F5": {"body": "kaku_regular", "emphasis": "kaku_bold"},
        "F6": {"body": "hand", "emphasis": "hand"},
    },
}

_KANE = {
    "C": {
        "C1": {"character_x": 0.50, "character_h": 0.56, "motif": "room", "office": 0.8},
        "C2": {"character_x": 0.28, "character_h": 0.50, "motif": "qa", "office": 0.35},
        "C3": {"character_x": 0.50, "character_h": 0.36, "motif": "items", "office": 0.2},
        "C4": {"character_x": 0.74, "character_h": 0.46, "motif": "checklist", "office": 0.22},
        "C5": {"character_x": 0.50, "character_h": 0.44, "motif": "qa", "office": 0.28},
        "C6": {"character_x": 0.50, "character_h": 0.40, "motif": "panels", "office": 0.18},
    },
    "P": {
        "P1": {"wall": (244, 246, 248), "floor": (28, 48, 92), "accent": (20, 42, 86), "caption": (18, 32, 70, 255)},
        "P2": {"wall": (248, 236, 214), "floor": (168, 64, 52), "accent": (140, 36, 32), "caption": (72, 24, 20, 255)},
        "P3": {"wall": (214, 236, 226), "floor": (24, 28, 30), "accent": (16, 24, 22), "caption": (20, 24, 22, 255)},
        "P4": {"wall": (255, 214, 64), "floor": (64, 66, 70), "accent": (40, 40, 44), "caption": (32, 32, 34, 255)},
        "P5": {"wall": (236, 228, 246), "floor": (250, 248, 252), "accent": (98, 72, 150), "caption": (64, 42, 110, 255)},
        "P6": {"wall": (14, 22, 48), "floor": (20, 32, 64), "accent": (212, 170, 72), "caption": (236, 204, 110, 255)},
    },
    "T": {
        "T1": {"text_y": 0.14, "text_align": "center", "text_scale": 1.0},
        "T2": {"text_y": 0.86, "text_align": "center", "text_scale": 1.0},
        "T3": {"text_y": 0.20, "text_align": "vertical", "text_scale": 0.72},
        "T4": {"text_y": 0.60, "text_align": "center", "text_scale": 1.0},
        "T5": {"text_y": 0.42, "text_align": "center", "text_scale": 1.22},
        "T6": {"text_y": 0.80, "text_align": "right", "text_scale": 0.9},
    },
    "F": {
        "F1": {"body": "kaku_bold", "emphasis": "kaku_bold"},
        "F2": {"body": "maru", "emphasis": "maru"},
        "F3": {"body": "mincho", "emphasis": "mincho"},
        "F4": {"body": "hand", "emphasis": "hand"},
        "F5": {"body": "kaku_regular", "emphasis": "kaku_bold"},
        "F6": {"body": "pop", "emphasis": "pop"},
    },
}

_LINE_LOOK = {"bousai": _BOUSAI, "kane": _KANE}

_HOOK = {
    "H1": {"hook_scale": 1.2, "hook_effect": "", "alert": False, "early": 1.0},
    "H2": {"hook_scale": 1.12, "hook_effect": "", "alert": False, "early": 1.0},
    "H3": {"hook_scale": 1.0, "hook_effect": "", "alert": False, "early": 1.35},
    "H4": {"hook_scale": 1.0, "hook_effect": "", "alert": True, "early": 1.0},
    "H5": {"hook_scale": 1.05, "hook_effect": "shake", "alert": False, "early": 1.0},
    "H6": {"hook_scale": 1.0, "hook_effect": "", "alert": False, "early": 1.15},
}

_TEMPO = {
    "M1": {"early": 0.72, "late": 0.78, "punch": 1.0, "speech": 1.08, "hook_speech": 1.12},
    "M2": {"early": 1.0, "late": 1.0, "punch": 1.0, "speech": 1.0, "hook_speech": 1.0},
    "M3": {"early": 1.28, "late": 1.36, "punch": 1.05, "speech": 0.94, "hook_speech": 0.94},
    "M4": {"early": 0.7, "late": 1.32, "punch": 1.2, "speech": 1.0, "hook_speech": 1.14},
    "M5": {"early": 1.0, "late": 1.0, "punch": 1.55, "speech": 1.0, "hook_speech": 1.0},
    "M6": {"early": 1.18, "late": 1.22, "punch": 1.08, "speech": 0.96, "hook_speech": 0.96},
}

_ASSET = {
    "A1": {"h_mul": 0.75, "motif": 1.0},
    "A2": {"h_mul": 1.0, "motif": 0.75},
    "A3": {"h_mul": 0.7, "motif": 0.95},
    "A4": {"h_mul": 0.85, "motif": 0.8},
    "A5": {"h_mul": 0.58, "motif": 0.28},
    "A6": {"h_mul": 1.08, "motif": 0.22},
}

_L2_TARGETS = (22.0, 24.0, 26.0, 28.0)


def validate_style(raw: object) -> dict:
    if not isinstance(raw, dict):
        raise ValueError("style がありません。")
    line = raw.get("line")
    if line not in _LINE_LOOK:
        raise ValueError("style.line は bousai か kane です。")
    axes = raw.get("axes")
    if not isinstance(axes, dict):
        raise ValueError("style.axes がありません。")
    normalized = {"line": line, "axes": {}}
    for key in AXES:
        rows = axes.get(key)
        if not isinstance(rows, list) or len(rows) < 2:
            raise ValueError(f"style.axes.{key} は2つ以上の選択肢です。")
        cleaned = []
        seen = set()
        for row in rows:
            if not isinstance(row, dict):
                raise ValueError(f"style.axes.{key} の項目がオブジェクトではありません。")
            code = str(row.get("code") or "")
            label = str(row.get("label") or "")
            if not code.startswith(key) or code in seen or not label:
                raise ValueError(f"style.axes.{key} の code が違います: {code}")
            if code not in _choices_for(line, key):
                raise ValueError(f"{line} に {code} の描き方がありません。")
            item = {"code": code, "label": label}
            if key == "L":
                item["min"] = float(row["min"])
                item["max"] = float(row["max"])
                if item["min"] > item["max"]:
                    raise ValueError(f"{code} の長さの範囲が逆です。")
            cleaned.append(item)
            seen.add(code)
        normalized["axes"][key] = cleaned
    return normalized


def _choices_for(line: str, axis: str) -> set[str]:
    if axis == "H":
        return set(_HOOK)
    if axis == "M":
        return set(_TEMPO)
    if axis == "B":
        return {f"B{i}" for i in range(1, 7)}
    if axis == "L":
        return {f"L{i}" for i in range(1, 6)}
    if axis == "A":
        return set(_ASSET)
    return set(_LINE_LOOK[line][axis])


def format_signature(line: str, axes: dict[str, str]) -> str:
    return line + ":" + "-".join(axes[key] for key in AXES)


def format_thumb(axes: dict[str, str]) -> str:
    return "thumb:" + "-".join(axes[key] for key in THUMB_AXES)


def parse_signature(signature: str) -> tuple[str, dict[str, str]]:
    line, rest = signature.split(":", 1)
    parts = rest.split("-")
    if len(parts) != len(AXES):
        raise ValueError(f"署名の軸が9つではありません: {signature}")
    axes = {}
    for key, part in zip(AXES, parts):
        if not part.startswith(key):
            raise ValueError(f"署名の {key} が違います: {signature}")
        axes[key] = part
    return line, axes


def parse_thumb(signature: str) -> dict[str, str]:
    rest = signature.split(":", 1)[1]
    parts = rest.split("-")
    if len(parts) != len(THUMB_AXES):
        raise ValueError(f"サムネ署名が違います: {signature}")
    return {key: part for key, part in zip(THUMB_AXES, parts)}


def shared_axes(left: dict[str, str], right: dict[str, str], keys: tuple[str, ...] = AXES) -> list[str]:
    return [key for key in keys if left.get(key) and left.get(key) == right.get(key)]


def code_for_length(seconds: float, options: list[dict]) -> str | None:
    hits = []
    for item in options:
        if float(item["min"]) - 0.05 <= float(seconds) <= float(item["max"]) + 0.05:
            hits.append(item["code"])
    if len(hits) == 1:
        return hits[0]
    return None


def usable_lengths(options: list[dict]) -> list[dict]:
    """今の尺ゲート（20秒以上30秒以下）と重なる長さだけを選ぶ。"""
    picked = []
    for item in options:
        low = max(GATE_MIN, float(item["min"]))
        high = min(GATE_MAX, float(item["max"]))
        if low <= high:
            picked.append(item)
    return picked


def load_style_log(path: Path | None = None) -> list[dict]:
    target = path or LOG_PATH
    if not target.is_file():
        return []
    with target.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _history_for(history: list[dict], video_id: str) -> list[dict]:
    rows = []
    for row in history:
        if str(row.get("video_id") or "") == video_id:
            continue
        if not str(row.get("signature") or ""):
            continue
        rows.append(row)
    return rows


def judge(
    axes: dict[str, str],
    history: list[dict],
    video_id: str,
    *,
    line: str,
    length_options: list[dict],
    measured_seconds: float | None = None,
) -> dict:
    """直前とは共有2軸まで。直近5本と公開済みとは共有3軸まで。完全一致は不可。"""
    working = dict(axes)
    reasons: list[str] = []
    if measured_seconds is not None:
        measured = code_for_length(measured_seconds, length_options)
        if measured != axes.get("L"):
            shown = "範囲外" if measured is None else measured
            reasons.append(f"長さ {measured_seconds:.2f}秒は選んだ {axes.get('L')} ではなく {shown}")
        if measured:
            working["L"] = measured
    signature = format_signature(line, working)
    thumb = format_thumb(working)
    thumb_axes = {key: working[key] for key in THUMB_AXES}
    others = _history_for(history, video_id)
    previous = others[-1] if others else None
    last5 = others[-5:]
    published = [row for row in others if row.get("status") == "published" and row not in last5]
    compared = last5 + published
    shared_prev: int | None = None
    thumb_shared: list[str] = []
    if previous is not None:
        prev_axes = parse_signature(previous["signature"])[1]
        shared_prev = len(shared_axes(working, prev_axes))
        if shared_prev > PREV_SHARED_MAX:
            reasons.append(f"直前の動画と {shared_prev} 軸が同じ（最大 {PREV_SHARED_MAX}）")
        prev_thumb = parse_thumb(previous["thumb_signature"])
        thumb_shared = shared_axes(thumb_axes, prev_thumb, CPT)
        if len(thumb_shared) > THUMB_CPT_SHARED_MAX:
            reasons.append("サムネの構図・配色・文字位置が、直前と2つ以上同じ")
    max_last5 = 0
    exact = False
    for row in compared:
        other_line, other_axes = parse_signature(row["signature"])
        same = shared_axes(working, other_axes)
        max_last5 = max(max_last5, len(same))
        if row["signature"] == signature:
            exact = True
        if other_line == line and row["signature"] == signature:
            exact = True
    if exact:
        reasons.append("直近の署名と完全に同じ")
    if compared and max_last5 > LAST5_SHARED_MAX:
        reasons.append(f"直近5本と最大 {max_last5} 軸が同じ（最大 {LAST5_SHARED_MAX}）")
    return {
        "ok": not reasons,
        "reasons": reasons,
        "signature": signature,
        "thumb_signature": thumb,
        "shared_with_prev": shared_prev,
        "shared_max_last5": max_last5 if compared else None,
        "axes": working,
    }


def _length_target(code: str, item: dict, rng: random.Random) -> float:
    low = max(GATE_MIN, float(item["min"]))
    high = min(GATE_MAX, float(item["max"]))
    if code == "L1":
        return 20.0
    if high - low < 1:
        return low
    choices = [value for value in _L2_TARGETS if low <= value <= high]
    if not choices:
        return low
    return float(rng.choice(choices))


def _font_path(name: str) -> str:
    path = _FONTS[name]
    if not path.is_file():
        raise RuntimeError(f"書体ファイルがありません: {path.name}")
    return str(path)


def materialize(channel_style: dict, axes: dict[str, str], rng: random.Random, verdict: dict) -> dict:
    line = channel_style["line"]
    look = _LINE_LOOK[line]
    layout = dict(look["C"][axes["C"]])
    asset = _ASSET[axes["A"]]
    height = float(layout["character_h"]) * float(asset["h_mul"])
    layout["character_h"] = max(0.28, min(0.62, height))
    layout["motif_strength"] = float(asset["motif"])
    layout.update(look["T"][axes["T"]])
    hook = _HOOK[axes["H"]]
    tempo = dict(_TEMPO[axes["M"]])
    tempo["early"] = float(tempo["early"]) * float(hook["early"])
    fonts = look["F"][axes["F"]]
    length_item = next(item for item in channel_style["axes"]["L"] if item["code"] == axes["L"])
    target = _length_target(axes["L"], length_item, rng)
    palette = dict(look["P"][axes["P"]])
    palette["stroke"] = (0, 0, 0, 255)
    return {
        "line": line,
        "axes": dict(axes),
        "signature": verdict["signature"],
        "thumb_signature": verdict["thumb_signature"],
        "shared_with_prev": verdict["shared_with_prev"],
        "shared_max_last5": verdict["shared_max_last5"],
        "length_target": target,
        "length_target_frames": int(round(target * FPS)),
        "length_options": list(channel_style["axes"]["L"]),
        "fonts": {"body": _font_path(fonts["body"]), "emphasis": _font_path(fonts["emphasis"])},
        "palette": palette,
        "layout": layout,
        "hook": hook,
        "tempo": tempo,
        "bgm": axes["B"],
    }


def pick_style(channel_style: dict, history: list[dict], video_id: str, rng: random.Random | None = None) -> dict:
    source = rng or random.SystemRandom()
    line = channel_style["line"]
    options = {key: [item["code"] for item in channel_style["axes"][key]] for key in AXES}
    lengths = usable_lengths(channel_style["axes"]["L"])
    if not lengths:
        raise RuntimeError("尺ゲートと重なる長さの選択肢がありません。")
    options["L"] = [item["code"] for item in lengths]
    for _ in range(500):
        axes = {key: source.choice(options[key]) for key in AXES}
        if axes["L"] == "L1" and axes["M"] not in ("M1", "M2"):
            continue
        verdict = judge(axes, history, video_id, line=line, length_options=channel_style["axes"]["L"])
        if verdict["ok"]:
            return materialize(channel_style, axes, source, verdict)
    raise RuntimeError("直前と直近5本から十分に離れた見た目が選べませんでした。")


def fit_line_durations(durations: list[float], voices: list[float], target_frames: int, fps: int = FPS) -> list[float] | None:
    count = len(durations)
    if count == 0 or count != len(voices):
        return None
    floors = [max(1, math.ceil((float(voice) + 0.2) * fps)) for voice in voices]
    if sum(floors) > target_frames:
        return None
    current = [max(1, int(round(float(duration) * fps))) for duration in durations]
    total = sum(current)
    if total <= 0:
        return None
    frames = [max(floors[index], int(current[index] * target_frames / total)) for index in range(count)]
    diff = target_frames - sum(frames)
    guard = 0
    while diff != 0 and guard < 10000:
        guard += 1
        if diff > 0:
            index = max(range(count), key=lambda item: frames[item])
            frames[index] += 1
            diff -= 1
            continue
        candidates = [index for index in range(count) if frames[index] > floors[index]]
        if not candidates:
            return None
        index = max(candidates, key=lambda item: frames[item] - floors[item])
        frames[index] -= 1
        diff += 1
    if sum(frames) != target_frames:
        return None
    return [frame / fps for frame in frames]


def render_bed(code: str, seconds: float) -> np.ndarray:
    """その場で作るベッド。B ごとに形を変える。既存の音源は使わない。"""
    n = max(1, int(seconds * 24000))
    t = np.arange(n, dtype=np.float32) / 24000.0
    if code == "B1":
        return np.zeros(n, dtype=np.float32)
    if code == "B2":
        notes = (261.63, 329.63, 392.0, 523.25)
        out = np.zeros(n, dtype=np.float32)
        step = int(0.7 * 24000)
        for index, start in enumerate(range(0, n, step)):
            freq = notes[index % len(notes)]
            end = min(n, start + int(0.55 * 24000))
            lt = t[: end - start]
            out[start:end] += np.sin(2 * np.pi * freq * lt) * np.exp(-lt * 3.2) * 0.22
        return out
    if code == "B3":
        return (0.08 * np.sin(2 * np.pi * 110 * t) + 0.05 * np.sin(2 * np.pi * 164.8 * t)).astype(np.float32)
    if code == "B4":
        noise = np.random.default_rng(11).uniform(-1, 1, n).astype(np.float32)
        kernel = np.ones(400, dtype=np.float32) / 400
        return np.convolve(noise, kernel, mode="same").astype(np.float32) * 0.12
    if code == "B5":
        pulse = (np.sin(2 * np.pi * 2.2 * t) > 0).astype(np.float32)
        tone = np.sin(2 * np.pi * 440 * t) * 0.5 + np.sin(2 * np.pi * 554.37 * t) * 0.25
        return (tone * (0.35 + 0.65 * pulse) * 0.08).astype(np.float32)
    if code == "B6":
        notes = (196.0, 246.94, 293.66, 392.0)
        out = np.zeros(n, dtype=np.float32)
        step = int(0.38 * 24000)
        for index, start in enumerate(range(0, n, step)):
            freq = notes[index % len(notes)]
            end = min(n, start + int(0.3 * 24000))
            lt = np.arange(end - start, dtype=np.float32) / 24000.0
            out[start:end] += np.sin(2 * np.pi * freq * lt) * np.exp(-lt * 8) * 0.28
        return out
    raise ValueError(f"未知のBGMです: {code}")


def alert_blip() -> np.ndarray:
    """H4。警報そのものではなく、短い二音を小さく置く。"""
    n = int(0.35 * 24000)
    t = np.arange(n, dtype=np.float32) / 24000.0
    tone = np.sin(2 * np.pi * 660 * t) * (t < 0.12) + np.sin(2 * np.pi * 880 * t) * (t >= 0.16)
    return tone.astype(np.float32) * 0.12


def append_style_log(row: dict, path: Path | None = None) -> None:
    target = path or LOG_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    new_file = not target.is_file()
    with target.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=LOG_FIELDS, lineterminator="\n")
        if new_file:
            writer.writeheader()
        writer.writerow({key: row.get(key, "") for key in LOG_FIELDS})


def style_self_test() -> None:
    for path in _FONTS.values():
        if not path.is_file():
            raise RuntimeError(f"書体が足りません: {path.name}")
    seed_axes = parse_signature("kane:C1-P1-T2-F1-H1-M2-B1-L2-A1")[1]
    history = [{
        "video_id": "14",
        "status": "published",
        "signature": "kane:C1-P1-T2-F1-H1-M2-B1-L2-A1",
        "thumb_signature": "thumb:C1-P1-T1-F1",
    }]
    options = [
        {"code": "L1", "min": 15, "max": 20},
        {"code": "L2", "min": 21, "max": 30},
        {"code": "L3", "min": 31, "max": 40},
    ]
    same = judge(seed_axes, history, "new", line="kane", length_options=options)
    if same["ok"] or same["shared_with_prev"] != 9:
        raise RuntimeError(f"同じ署名を通しています: {same}")
    far = dict(seed_axes)
    far.update({"C": "C6", "P": "P6", "T": "T6", "F": "F6", "H": "H6", "M": "M6", "B": "B6", "A": "A6"})
    far_verdict = judge(far, history, "new", line="bousai", length_options=options)
    if not far_verdict["ok"]:
        raise RuntimeError(f"離れた署名を落としています: {far_verdict}")
    if far_verdict["shared_with_prev"] != 1:
        raise RuntimeError(f"共有軸の数が違います: {far_verdict}")
    close = dict(far)
    close["C"] = "C1"
    close["P"] = "P1"
    thumb_fail = judge(close, history, "new", line="bousai", length_options=options)
    if thumb_fail["ok"]:
        raise RuntimeError("サムネが直前と近すぎるのを通しています。")
    last = judge(far, history, "new", line="bousai", length_options=options, measured_seconds=22.0)
    if not last["ok"] or last["axes"]["L"] != "L2":
        raise RuntimeError(f"測った長さの判定が違います: {last}")
    missed = judge(far, history, "new", line="bousai", length_options=options, measured_seconds=20.0)
    if missed["ok"]:
        raise RuntimeError("選んだ長さと違う尺を通しています。")
    older = {
        "video_id": "old",
        "status": "review",
        "signature": "bousai:C6-P6-T6-F6-H6-M6-B6-L1-A6",
        "thumb_signature": "thumb:C6-P6-T6-F6",
    }
    recent = {
        "video_id": "prev",
        "status": "review",
        "signature": "kane:C2-P2-T3-F2-H2-M3-B3-L1-A2",
        "thumb_signature": "thumb:C2-P2-T3-F2",
    }
    crowded = dict(far)
    crowded["L"] = "L1"
    four = judge(crowded, [older, recent], "new", line="bousai", length_options=options)
    if four["ok"] or (four["shared_max_last5"] or 0) < 4:
        raise RuntimeError(f"直近5本との4軸を通しています: {four}")
    three = {"C": "C6", "P": "P6", "T": "T6", "F": "F2", "H": "H2", "M": "M1", "B": "B4", "L": "L2", "A": "A3"}
    three_ok = judge(three, [older, recent], "new", line="bousai", length_options=options)
    if not three_ok["ok"] or three_ok["shared_max_last5"] != 3:
        raise RuntimeError(f"直近5本との3軸を落としています: {three_ok}")
    fitted = fit_line_durations([2, 2, 2, 2], [1, 1, 1, 1], 480)
    if fitted is None or abs(sum(fitted) - 20.0) > 1e-6:
        raise RuntimeError(f"20秒へ揃えられません: {fitted}")
    if fit_line_durations([6, 6, 6, 6], [5.0, 5.0, 5.0, 5.0], 480) is not None:
        raise RuntimeError("声より短い尺を作っています。")
    beds = [render_bed(f"B{i}", 1.0) for i in range(1, 7)]
    if beds[0].any() or not beds[1].any():
        raise RuntimeError("BGMの有無が逆です。")
    if np.allclose(beds[1], beds[5]):
        raise RuntimeError("別のBGMが同じ波形です。")
