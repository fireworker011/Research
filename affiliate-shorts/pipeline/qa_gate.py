"""尺、解像度、音声、字幕、名札、口の重ね絵を見て、落ちたら出力を止める。"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import numpy as np

from irasutoya_short.constants import HEIGHT, WIDTH
from irasutoya_short.sprites import _face_box, draw_mouth, mouth_anchor, skin_color

MIN_DURATION = 20.0
MAX_DURATION = 30.0
MEAN_VOLUME_FLOOR_DB = -45.0

_MEAN_VOLUME = re.compile(r"mean_volume:\s*(-?\d+(?:\.\d+)?)\s*dB")


def caption_overlay_has_box(overlay: np.ndarray) -> bool:
    """字幕レイヤに、文字の縁ではない塗りつぶしの帯があるか。

    文字は枠の中が空く。帯は枠のほとんどを塗る。
    """
    alpha = overlay[:, :, 3]
    opaque = alpha > 200
    ys, xs = np.where(opaque)
    if len(xs) == 0:
        return False
    x0, x1 = int(xs.min()), int(xs.max())
    y0, y1 = int(ys.min()), int(ys.max())
    box_w = x1 - x0 + 1
    box_h = y1 - y0 + 1
    if box_w < int(WIDTH * 0.35) or box_h < 36:
        return False
    filled = int(opaque[y0 : y1 + 1, x0 : x1 + 1].sum()) / float(box_w * box_h)
    return filled > 0.72


def diff_centroid(before: np.ndarray, after: np.ndarray) -> tuple[int, int] | None:
    delta = np.abs(before[:, :, :3].astype(np.int16) - after[:, :, :3].astype(np.int16)).sum(axis=2)
    ys, xs = np.where(delta > 40)
    if len(xs) == 0:
        return None
    return int(round(float(xs.mean()))), int(round(float(ys.mean())))


def judge_mouth(rgba: np.ndarray, *, overlay: bool, center: tuple[int, int] | None) -> list[str]:
    """重ね絵を使うときは、目・鼻・口の並びの口に乗っていること。使わないときは位置が無いこと。"""
    errors: list[str] = []
    anchor = mouth_anchor(rgba)
    box = _face_box(rgba)
    if not overlay:
        if center is not None:
            errors.append("口の重ね絵は無しなのに、重ね位置がある")
        return errors
    if anchor is None or box is None:
        errors.append("口の位置が取れないので、重ね絵は出せない")
        return errors
    face_h = max(1, int(box["bot"] - box["top"]))
    eye_line = int(box["top"] + face_h * 0.38)
    if not (eye_line < anchor.y < int(box["bot"]) + 6):
        errors.append("基準の口が、目のラインより上か顔の外にある")
    if center is None:
        errors.append("口の重ね絵を使うのに、置いた位置が無い")
        return errors
    limit = max(10, int(anchor.width * 0.55))
    if abs(center[0] - anchor.x) > limit or abs(center[1] - anchor.y) > limit:
        errors.append("口の重ね絵が、キャラの口からずれている")
    if center[1] <= eye_line:
        errors.append("口の重ね絵が目の位置にある")
    return errors


def mouth_self_test(rgba: np.ndarray) -> dict:
    """正しい口は通し、目の位置と『無しなのに位置がある』は止める。"""
    anchor = mouth_anchor(rgba)
    box = _face_box(rgba)
    if anchor is None or box is None:
        raise RuntimeError("口の自己テストに使う絵から、口の位置が取れません。")
    face_h = max(1, int(box["bot"] - box["top"]))
    on_mouth = judge_mouth(rgba, overlay=True, center=(anchor.x, anchor.y))
    on_eyes = judge_mouth(
        rgba,
        overlay=True,
        center=(anchor.x, max(0, anchor.y - int(face_h * 0.45))),
    )
    absent = judge_mouth(rgba, overlay=False, center=None)
    leaked = judge_mouth(rgba, overlay=False, center=(anchor.x, anchor.y))
    skin = skin_color(rgba, anchor.x, anchor.y, anchor.width)
    drawn = draw_mouth(rgba, anchor, 0.65, skin)
    centroid = diff_centroid(rgba, drawn)
    drawn_errors = judge_mouth(rgba, overlay=True, center=centroid)
    checks = {
        "on_mouth": on_mouth,
        "on_eyes": on_eyes,
        "absent": absent,
        "leaked": leaked,
        "drawn": drawn_errors,
        "anchor": {"x": anchor.x, "y": anchor.y, "width": anchor.width},
    }
    if on_mouth or absent or not on_eyes or not leaked or drawn_errors or centroid is None:
        raise RuntimeError(f"口の自己テストが落ちました: {json.dumps(checks, ensure_ascii=False)}")
    return checks


def pure_self_test() -> None:
    box = np.zeros((HEIGHT, WIDTH, 4), dtype=np.uint8)
    box[1400:1600, 180:900, 3] = 210
    box[1400:1600, 180:900, :3] = (20, 20, 20)
    if not caption_overlay_has_box(box):
        raise RuntimeError("字幕の帯を見落としています。")
    stroke = np.zeros((HEIGHT, WIDTH, 4), dtype=np.uint8)
    stroke[1500:1520, 400:700, 3] = 255
    if caption_overlay_has_box(stroke):
        raise RuntimeError("文字の縁を帯と見なしています。")


def probe_media(path: Path) -> dict:
    if not path.is_file():
        return {"exists": False, "duration": None, "width": None, "height": None, "has_audio": False, "mean_volume_db": None}
    proc = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration:stream=codec_type,width,height",
            "-of", "json", str(path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    payload = json.loads(proc.stdout or "{}")
    duration = None
    if payload.get("format", {}).get("duration") is not None:
        duration = float(payload["format"]["duration"])
    width = height = None
    has_audio = False
    for stream in payload.get("streams") or []:
        if stream.get("codec_type") == "video" and width is None:
            width = stream.get("width")
            height = stream.get("height")
        if stream.get("codec_type") == "audio":
            has_audio = True
    volume = subprocess.run(
        ["ffmpeg", "-hide_banner", "-i", str(path), "-af", "volumedetect", "-f", "null", "-"],
        check=False,
        capture_output=True,
        text=True,
    )
    match = _MEAN_VOLUME.search(volume.stderr or "")
    mean_volume = float(match.group(1)) if match else None
    return {
        "exists": True,
        "duration": duration,
        "width": width,
        "height": height,
        "has_audio": has_audio,
        "mean_volume_db": mean_volume,
    }


def _check(checks: list[dict], name: str, ok: bool, detail: str) -> None:
    checks.append({"name": name, "pass": bool(ok), "detail": detail})


def evaluate(plan: dict, media_path: Path | None) -> dict:
    checks: list[dict] = []
    media = probe_media(media_path) if media_path is not None else {
        "exists": False, "duration": None, "width": None, "height": None,
        "has_audio": False, "mean_volume_db": None,
    }
    duration = media["duration"] if media["exists"] else plan.get("duration_sec")
    duration_ok = duration is not None and MIN_DURATION <= float(duration) <= MAX_DURATION
    shown = "無し" if duration is None else f"{float(duration):.2f}秒"
    _check(checks, "duration", duration_ok, f"{shown}（20秒以上30秒以下）")

    width = media["width"] if media["exists"] else WIDTH
    height = media["height"] if media["exists"] else HEIGHT
    resolution_ok = media["exists"] and width == WIDTH and height == HEIGHT
    _check(checks, "resolution", resolution_ok, f"{width}x{height}")

    volume = media["mean_volume_db"]
    audio_ok = bool(media["has_audio"]) and volume is not None and volume > MEAN_VOLUME_FLOOR_DB
    volume_text = "無し" if volume is None else f"{volume:.1f} dB"
    _check(checks, "audio", audio_ok, f"音声 {'あり' if media['has_audio'] else 'なし'}、平均 {volume_text}")

    overflows = [item for item in plan.get("captions") or [] if item.get("overflow")]
    _check(checks, "caption_overflow", not overflows, "はみ出し無し" if not overflows else "はみ出し: " + "、".join(item["role"] for item in overflows))

    boxes = [item for item in plan.get("captions") or [] if item.get("has_box")]
    _check(checks, "text_boxes", not boxes, "字幕の帯は無し" if not boxes else "帯がある行があります")

    tags = list(plan.get("tags") or [])
    _check(checks, "name_tags", not tags, "名札とタグは無し" if not tags else "、".join(tags))

    mouth_overlay = bool(plan.get("mouth_overlay"))
    scenes = list(plan.get("mouths") or [])
    present = [item for item in scenes if item.get("overlay_used")]
    position_errors = [err for item in scenes for err in item.get("errors") or []]
    if mouth_overlay:
        mouth_ok = not position_errors and all(item.get("checked") for item in scenes)
        detail = "重ね絵は口の位置" if mouth_ok else "、".join(position_errors) or "口の確認が足りない"
        _check(checks, "mouth_position", mouth_ok, detail)
    else:
        absent_ok = not present and not position_errors
        _check(checks, "mouth_overlay_absent", absent_ok, "口の重ね絵は無い" if absent_ok else "口の重ね絵が残っている")

    passed = all(item["pass"] for item in checks) and bool(media["exists"] or plan.get("blocked_before_encode"))
    if plan.get("blocked_before_encode"):
        passed = False
    return {
        "pass": passed,
        "checks": checks,
        "duration_sec": None if duration is None else round(float(duration), 2),
        "width": width,
        "height": height,
        "mouth_overlay": mouth_overlay,
        "media": media,
    }


def write_report(path: Path, script: dict, report: dict) -> None:
    lines = [
        "# QA",
        "",
        f"結果: {'pass' if report['pass'] else 'fail'}",
        "",
        f"タイトル: {script.get('title', '')}",
        "",
        "投稿はしない。",
        "",
        "| 項目 | 結果 | 内容 |",
        "| --- | --- | --- |",
    ]
    for item in report["checks"]:
        mark = "pass" if item["pass"] else "fail"
        lines.append(f"| {item['name']} | {mark} | {item['detail']} |")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")
