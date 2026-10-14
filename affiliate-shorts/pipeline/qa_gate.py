"""尺、解像度、音声、字幕、名札、口の重ね絵を見て、落ちたら出力を止める。"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import numpy as np

from irasutoya_short.constants import HEIGHT, WIDTH
from irasutoya_short.sprites import _face_box, draw_mouth, mouth_anchor, skin_color

from styles import judge, load_style_log

MIN_DURATION = 20.0
MAX_DURATION = 30.0
MEAN_VOLUME_FLOOR_DB = -45.0
IRASUTOYA_POINT_LIMIT = 20
MAX_SUBJECT_HEIGHT = 0.80
MAX_SUBJECT_WIDTH = 0.90
MAX_SUBJECT_AREA = 0.65

_MEAN_VOLUME = re.compile(r"mean_volume:\s*(-?\d+(?:\.\d+)?)\s*dB")
COLLAB_RE = re.compile(r"いらすとや|irasutoya", re.IGNORECASE)


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


def tally_images(uses: list[dict], thumbnail: dict | None) -> dict:
    """同じ出典URLは1点。色違いは同じ点。表情が違う別URLは別点。サムネイルもこの中。"""
    seen: dict[str, str] = {}
    log: list[dict] = []
    for use in uses:
        url = str(use.get("source_url") or "").strip()
        asset_id = str(use.get("id") or "")
        emotion = str(use.get("emotion") or "")
        recolor = bool(use.get("recolor"))
        row = {"id": asset_id, "emotion": emotion, "source_url": url, "thumbnail": False}
        if not url:
            row["points"] = 0
            row["reason"] = "出典URLが無い"
            row["error"] = True
            log.append(row)
            continue
        if url in seen:
            row["points"] = 0
            row["reason"] = "同じ絵の色違い。点数に足さない" if recolor else "同じ絵の再利用。点数に足さない"
            log.append(row)
            continue
        seen[url] = asset_id
        row["points"] = 1
        row["reason"] = "別の絵。表情が違えば別点"
        log.append(row)
    if not uses and thumbnail is None:
        note = "いらすとやの絵は無い。サムネイルの追加も無い。"
    elif thumbnail is None:
        note = "サムネイル専用の絵は無い。動画に出した絵をサムネイルにするので、点数は増えない。"
    else:
        url = str(thumbnail.get("source_url") or "").strip()
        asset_id = str(thumbnail.get("id") or thumbnail.get("character") or "thumbnail")
        emotion = str(thumbnail.get("emotion") or "")
        row = {"id": asset_id, "emotion": emotion, "source_url": url, "thumbnail": True}
        if not url:
            row["points"] = 0
            row["reason"] = "サムネイルの出典URLが無い"
            row["error"] = True
            note = "サムネイルの出典URLが無い。"
        elif url in seen:
            row["points"] = 0
            row["reason"] = "サムネイルは動画と同じ絵。点数に足さない"
            note = "サムネイルは動画と同じ絵。点数は増えない。"
        else:
            seen[url] = asset_id
            row["points"] = 1
            row["reason"] = "サムネイルだけの絵"
            note = "サムネイルだけの絵を1点に数えた。"
        log.append(row)
    errors = [row for row in log if row.get("error")]
    count = len(seen)
    return {
        "count": count,
        "limit": IRASUTOYA_POINT_LIMIT,
        "ok": count <= IRASUTOYA_POINT_LIMIT and not errors,
        "log": log,
        "thumbnail_note": note,
    }


def collaboration_hits(branding: dict) -> list[str]:
    """チャンネル名やタイトルが、いらすとやとの協力を示す書き方になっていないか。"""
    hits: list[str] = []
    for key in ("name", "genre", "title", "theme"):
        if COLLAB_RE.search(str(branding.get(key) or "")):
            hits.append(key)
    for tag in branding.get("tags") or []:
        if COLLAB_RE.search(str(tag)):
            hits.append(f"tag:{tag}")
    for text in branding.get("texts") or []:
        if COLLAB_RE.search(str(text)):
            hits.append("本文")
            break
    return hits


def subject_errors(subject: dict) -> list[str]:
    """イラストは部屋と字幕の一部。画面そのものにはしない。"""
    errors: list[str] = []
    if subject.get("background") != "generated":
        errors.append("背景がイラストそのものになっている")
    if float(subject.get("max_height_ratio") or 0) > MAX_SUBJECT_HEIGHT:
        errors.append("イラストが縦いっぱいに近い")
    if float(subject.get("max_width_ratio") or 0) > MAX_SUBJECT_WIDTH:
        errors.append("イラストが横いっぱいに近い")
    if float(subject.get("max_area_ratio") or 0) > MAX_SUBJECT_AREA:
        errors.append("イラストが画面の大部分を占めている")
    if int(subject.get("caption_count") or 0) < 1:
        errors.append("字幕が無く、イラストが内容そのものになっている")
    return errors


def image_gate_self_test() -> None:
    over = tally_images(
        [{"id": f"n{i}", "emotion": "x", "source_url": f"https://example.invalid/{i}.png"} for i in range(21)],
        None,
    )
    if over["count"] != 21 or over["ok"]:
        raise RuntimeError(f"21点を止めていません: {over['count']}")
    mixed = tally_images(
        [
            {"id": "a", "emotion": "trouble", "source_url": "https://example.invalid/a.png"},
            {"id": "a", "emotion": "trouble", "source_url": "https://example.invalid/a.png", "recolor": True},
            {"id": "b", "emotion": "angry", "source_url": "https://example.invalid/b.png"},
        ],
        {"id": "a", "emotion": "trouble", "source_url": "https://example.invalid/a.png"},
    )
    if mixed["count"] != 2 or sum(row["points"] for row in mixed["log"]) != 2:
        raise RuntimeError(f"再利用と色違いの数え方が違います: {mixed}")
    thumb = tally_images(
        [{"id": "a", "emotion": "trouble", "source_url": "https://example.invalid/a.png"}],
        {"id": "c", "emotion": "smile", "source_url": "https://example.invalid/c.png"},
    )
    if thumb["count"] != 2:
        raise RuntimeError(f"サムネイルだけの絵を数えていません: {thumb}")
    if collaboration_hits({"name": "30秒そなえ帳", "genre": "防災グッズ・備え", "title": "一日の水", "theme": "備蓄", "tags": ["防災"], "texts": ["三日分"]}):
        raise RuntimeError("普通の名前を、協力を示すと見なしています。")
    if not collaboration_hits({"name": "いらすとや公式", "title": "", "texts": []}):
        raise RuntimeError("協力を示す名前を通しています。")
    if not collaboration_hits({"name": "", "title": "いらすとやコラボ", "texts": []}):
        raise RuntimeError("協力を示すタイトルを通しています。")
    if subject_errors({"background": "generated", "max_height_ratio": 0.60, "max_width_ratio": 0.45, "max_area_ratio": 0.27, "caption_count": 4}):
        raise RuntimeError("部屋の中の人物を、主体すぎると見なしています。")
    if not subject_errors({"background": "illustration", "max_height_ratio": 0.60, "max_width_ratio": 0.45, "max_area_ratio": 0.27, "caption_count": 4}):
        raise RuntimeError("イラストだけの背景を通しています。")
    if not subject_errors({"background": "generated", "max_height_ratio": 0.95, "max_width_ratio": 0.45, "max_area_ratio": 0.27, "caption_count": 4}):
        raise RuntimeError("画面いっぱいのイラストを通しています。")


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


def _style_verdict(plan: dict, duration: float | None) -> dict:
    style = plan.get("style")
    empty = {
        "ok": False,
        "thumb_ok": False,
        "fit_failed": True,
        "detail": "見た目の記録が無い",
        "thumb_detail": "サムネの記録が無い",
        "signature": "",
        "thumb_signature": "",
        "shared_with_prev": None,
        "shared_max_last5": None,
        "bgm": "",
    }
    if not isinstance(style, dict) or "axes" not in style:
        return empty
    verdict = judge(
        dict(style["axes"]),
        load_style_log(),
        str(plan.get("video_id") or ""),
        line=str(style.get("line") or ""),
        length_options=list(style.get("length_options") or []),
        measured_seconds=None if duration is None else float(duration),
    )
    reasons = list(verdict["reasons"])
    if style.get("fit_failed"):
        reasons.append("選んだ長さに尺を合わせられなかった")
    thumb_reasons = [item for item in reasons if item.startswith("サムネ")]
    other = [item for item in reasons if item not in thumb_reasons]
    prev = verdict["shared_with_prev"]
    last = verdict["shared_max_last5"]
    detail = f"{verdict['signature']}。直前との共有 {('-' if prev is None else prev)}。直近5本の最大 {('-' if last is None else last)}"
    if other:
        detail += "。" + "。".join(other)
    thumb_detail = verdict["thumb_signature"]
    if thumb_reasons:
        thumb_detail += "。" + "。".join(thumb_reasons)
    else:
        thumb_detail += "。構図・配色・文字位置は直前と2つ以上違う"
    return {
        "ok": not other,
        "thumb_ok": not thumb_reasons,
        "fit_failed": bool(style.get("fit_failed")),
        "detail": detail,
        "thumb_detail": thumb_detail,
        "signature": verdict["signature"],
        "thumb_signature": verdict["thumb_signature"],
        "shared_with_prev": prev,
        "shared_max_last5": last,
        "bgm": str(style.get("bgm") or ""),
    }


def _credit_ok(plan: dict) -> tuple[bool, str]:
    caption = str(plan.get("credit_caption") or "")
    missing = [voice for voice in plan.get("voice_credits") or [] if str(voice) not in caption]
    if "イラスト：いらすとや" not in caption:
        missing.append("イラスト：いらすとや")
    if missing:
        return False, "クレジットに無い: " + "、".join(str(item) for item in missing)
    return True, "使った声と、イラスト：いらすとや"


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

    if "images" not in plan:
        tally = {"count": None, "limit": IRASUTOYA_POINT_LIMIT, "ok": False, "log": [], "thumbnail_note": "点数の記録が無い。"}
        _check(checks, "irasutoya_count", False, "点数の記録が無い")
    else:
        tally = tally_images(list(plan.get("images") or []), plan.get("thumbnail"))
        if tally["ok"]:
            detail = f"{tally['count']}点（上限{tally['limit']}）。{tally['thumbnail_note']}"
        else:
            detail = f"{tally['count']}点（上限{tally['limit']}）。上限を超えたので止めた。{tally['thumbnail_note']}"
        _check(checks, "irasutoya_count", bool(tally["ok"]), detail)

    if "subject" not in plan:
        _check(checks, "irasutoya_subject", False, "主体の記録が無い")
    else:
        subject_problems = subject_errors(plan["subject"])
        _check(
            checks,
            "irasutoya_subject",
            not subject_problems,
            "イラストは画面の一部" if not subject_problems else "、".join(subject_problems),
        )

    if "branding" not in plan:
        _check(checks, "irasutoya_name", False, "名前の記録が無い")
    else:
        hits = collaboration_hits(plan["branding"])
        _check(checks, "irasutoya_name", not hits, "協力を示す名前は無い" if not hits else "協力を示す書き方: " + "、".join(hits))

    style_verdict = _style_verdict(plan, duration)
    _check(
        checks,
        "style_signature",
        bool(style_verdict["ok"]) and not style_verdict.get("fit_failed"),
        style_verdict["detail"],
    )
    _check(checks, "style_thumb", bool(style_verdict["thumb_ok"]), style_verdict["thumb_detail"])
    credit_ok, credit_detail = _credit_ok(plan)
    _check(checks, "credit_line", credit_ok, credit_detail)

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
        "image_tally": tally,
        "style": style_verdict,
    }


def write_report(path: Path, script: dict, report: dict) -> None:
    lines = [
        "# QA",
        "",
        f"結果: {'pass' if report['pass'] else 'fail'}",
        "",
        f"タイトル: {script.get('title', '')}",
        "",
        f"チャンネル設定: {script.get('channel', '')}",
        f"チャンネル名: {_channel_label(script)}",
        f"ジャンル: {script.get('genre') or '未定'}",
        f"見た目: {(report.get('style') or {}).get('signature') or '無し'}",
        f"サムネ: {(report.get('style') or {}).get('thumb_signature') or '無し'}",
        "",
        "投稿はしない。",
        "",
        "| 項目 | 結果 | 内容 |",
        "| --- | --- | --- |",
    ]
    for item in report["checks"]:
        mark = "pass" if item["pass"] else "fail"
        lines.append(f"| {item['name']} | {mark} | {item['detail']} |")
    tally = report.get("image_tally") or {}
    log = list(tally.get("log") or [])
    lines.extend(["", "## いらすとやの点数", ""])
    if tally.get("count") is None:
        lines.append("記録が無い。")
    else:
        lines.append(f"{tally['count']}点（上限{tally.get('limit', IRASUTOYA_POINT_LIMIT)}）")
        lines.append("")
        lines.append(str(tally.get("thumbnail_note") or ""))
        lines.append("")
        lines.append("| 素材 | 表情 | 点数 | 理由 | 出典 |")
        lines.append("| --- | --- | --- | --- | --- |")
        for row in log:
            lines.append(
                f"| {row.get('id', '')} | {row.get('emotion', '')} | {row.get('points', '')} | {row.get('reason', '')} | {row.get('source_url', '')} |"
            )
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def _channel_label(script: dict) -> str:
    name = str(script.get("channel_name") or "").strip()
    if not name:
        return "未定"
    if script.get("name_status") == "working":
        return f"{name}（仮称）"
    return name
