#!/usr/bin/env python3
"""Pack one MiniMax H3 concept-LoRA dataset for fal trainers.

One concept per zip. Captions bake the trigger. Composition comes from
the filename so the same act can fire in any pose.

This script never trains weights and never prints API keys.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import Any

TRAIN_DIR = Path(__file__).resolve().parent
CONCEPTS_PATH = TRAIN_DIR / "concepts.json"
SCHEMA = "h3-lora-studio-train/v1"
PACK_SCHEMA = "h3-lora-studio-train-pack/v1"
VIDEO_EXTS = (".mp4", ".mov", ".avi", ".mkv")
POSE_ORDER = (
    "standing",
    "doggy",
    "missionary",
    "cowgirl",
    "side",
    "pov",
    "kneeling",
    "sitting",
    "squat",
)
CAMERA_ORDER = ("front", "behind", "side", "above")
SHOT_ORDER = ("close", "medium")
ASPECT_ALIASES = {
    "9x16": "9:16",
    "16x9": "16:9",
    "8x9": "8:9",
    "9:16": "9:16",
    "16:9": "16:9",
    "8:9": "8:9",
}
SECRET_RE = re.compile(
    r"(api[_-]?key|secret|token|password|authorization|hf_token|xai)",
    re.I,
)
LIVE_SECRET_RE = re.compile(
    r"\b(sk-[A-Za-z0-9_-]{8,}|hf_[A-Za-z0-9]{8,}|xai-[A-Za-z0-9_-]{8,})\b"
)
MALE_RE = re.compile(r"\b(the man|male character|his penis|a man)\b", re.I)
MINOR_TERMS = (
    "loli",
    "lolita",
    "shota",
    "syota",
    "child",
    "children",
    "kid",
    "kids",
    "toddler",
    "infant",
    "minor",
    "underage",
    "teen",
    "teenage",
    "teenager",
    "小学生",
    "中学生",
    "pedo",
)


class PackError(Exception):
    """User-facing validation failure."""


def load_bundle(path: Path | None = None) -> dict[str, Any]:
    raw = json.loads((path or CONCEPTS_PATH).read_text(encoding="utf-8"))
    if raw.get("schema") != SCHEMA:
        raise PackError(f"concepts schema must be {SCHEMA}")
    return raw


def list_concepts(bundle: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    data = bundle or load_bundle()
    return list(data.get("concepts") or [])


def skipped_concepts(bundle: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    data = bundle or load_bundle()
    return list(data.get("skipped") or [])


def get_concept(concept_id: str, bundle: dict[str, Any] | None = None) -> dict[str, Any]:
    data = bundle or load_bundle()
    for row in list_concepts(data):
        if row.get("id") == concept_id:
            return row
    skipped = {row.get("id") for row in skipped_concepts(data)}
    if concept_id in skipped:
        raise PackError(
            f"{concept_id} is skipped: 膣セックスは AIO があるので作らない"
        )
    known = ", ".join(row["id"] for row in list_concepts(data))
    raise PackError(f"unknown concept {concept_id}. known: {known}")


def other_triggers(concept_id: str, bundle: dict[str, Any] | None = None) -> tuple[str, ...]:
    data = bundle or load_bundle()
    return tuple(
        str(row["trigger"])
        for row in list_concepts(data)
        if row.get("id") != concept_id and row.get("trigger")
    )


def defaults(bundle: dict[str, Any] | None = None) -> dict[str, Any]:
    data = bundle or load_bundle()
    return dict(data.get("defaults") or {})


def tokenize_stem(stem: str) -> list[str]:
    return [part.lower() for part in re.split(r"[-_.]+", stem) if part]


def parse_filename_tags(name: str) -> dict[str, str]:
    """Read pose / camera / shot / aspect from a clip filename."""
    stem = Path(name).stem
    tokens = tokenize_stem(stem)
    poses = set(POSE_ORDER)
    cameras = set(CAMERA_ORDER)
    shots = set(SHOT_ORDER)
    pose = ""
    camera = ""
    shot = ""
    aspect = ""
    leftover: list[str] = []
    for token in tokens:
        if token in ASPECT_ALIASES and not aspect:
            aspect = ASPECT_ALIASES[token]
            continue
        leftover.append(token)
    tokens = leftover
    leftover = []
    for token in tokens:
        if token in poses and not pose:
            pose = token
            continue
        leftover.append(token)
    tokens = leftover
    leftover = []
    for token in tokens:
        if token in cameras and not camera:
            camera = token
            continue
        leftover.append(token)
    tokens = leftover
    leftover = []
    for token in tokens:
        if token in shots and not shot:
            shot = token
            continue
        leftover.append(token)
    return {
        "pose": pose,
        "camera": camera,
        "shot": shot,
        "aspect": aspect,
        "unknown": " ".join(leftover),
    }


def render_caption(concept: dict[str, Any], tags: dict[str, str]) -> str:
    template = str(concept.get("caption") or "").strip()
    if not template:
        raise PackError(f"{concept.get('id')} has no caption template")
    values = {
        "trigger": str(concept.get("trigger") or "").strip(),
        "pose": tags.get("pose") or "unspecified",
        "camera": tags.get("camera") or "unspecified",
        "shot": tags.get("shot") or "unspecified",
        "aspect": tags.get("aspect") or "unspecified",
    }
    if not values["trigger"]:
        raise PackError(f"{concept.get('id')} has no trigger")
    text = template.format(**values)
    return " ".join(text.split())


def caption_starts_with_trigger(text: str, trigger: str) -> bool:
    return str(text or "").lstrip().startswith(trigger)


def camera_after_action(text: str) -> bool:
    lower = text.lower()
    cam = lower.rfind(" camera")
    if cam < 0:
        return False
    action_marks = (
        "already fully inside",
        "drinks the yellow",
        "coming out of the anus",
        "inside the anus",
        "streams from the urethral",
        "act of defecating",
    )
    return any(mark in lower[:cam] for mark in action_marks)


def find_minors(text: str) -> list[str]:
    raw = str(text or "")
    blob = re.sub(r"[-_.]+", " ", raw.lower())
    hits = []
    for term in MINOR_TERMS:
        if term.isascii():
            if re.search(rf"\b{re.escape(term)}\b", blob):
                hits.append(term)
        elif term in raw:
            hits.append(term)
    return hits


def find_other_trigger(text: str, foreign: tuple[str, ...]) -> str:
    blob = str(text or "")
    for token in foreign:
        if re.search(rf"\b{re.escape(token)}\b", blob):
            return token
    return ""


def find_secrets(text: str) -> bool:
    return bool(SECRET_RE.search(text) or LIVE_SECRET_RE.search(text))


def iter_videos(src: Path) -> list[Path]:
    clips = [
        path
        for path in src.iterdir()
        if path.is_file() and path.suffix.lower() in VIDEO_EXTS
    ]
    clips.sort(key=lambda path: path.name.lower())
    return clips


def probe_video(path: Path) -> dict[str, Any]:
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "stream=codec_type,r_frame_rate,avg_frame_rate,width,height",
        "-show_entries",
        "format=duration",
        "-of",
        "json",
        str(path),
    ]
    try:
        raw = subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True)
    except (OSError, subprocess.CalledProcessError) as exc:
        raise PackError(f"ffprobe failed for {path.name}: {exc}") from exc
    data = json.loads(raw or "{}")
    streams = list(data.get("streams") or [])
    video = next((row for row in streams if row.get("codec_type") == "video"), None)
    audio = next((row for row in streams if row.get("codec_type") == "audio"), None)
    if video is None:
        video = next((row for row in streams if row.get("width")), {})
    rate = str((video or {}).get("r_frame_rate") or (video or {}).get("avg_frame_rate") or "")
    fps = _parse_rate(rate)
    duration = float((data.get("format") or {}).get("duration") or 0.0)
    width = int((video or {}).get("width") or 0)
    height = int((video or {}).get("height") or 0)
    return {
        "fps": fps,
        "duration_s": duration,
        "width": width,
        "height": height,
        "has_audio": audio is not None,
        "rate": rate,
    }


def _parse_rate(rate: str) -> float:
    if not rate or rate == "0/0":
        return 0.0
    if "/" in rate:
        num, den = rate.split("/", 1)
        if float(den) == 0:
            return 0.0
        return float(num) / float(den)
    return float(rate)


def fps_is_24(fps: float) -> bool:
    return abs(float(fps) - 24.0) < 0.001


def recommend_fal(concept: dict[str, Any], n_clips: int, bundle: dict[str, Any] | None = None) -> dict[str, Any]:
    cfg = defaults(bundle)
    if n_clips >= 120:
        steps = 5000
        lr = 1e-4
    elif n_clips >= 80:
        steps = 3000
        lr = 2e-4
    else:
        steps = 2000
        lr = 2e-4
    return {
        "trainer": concept.get("trainer") or cfg.get("trainer") or "minimax/h3/i2v/trainer",
        "number_of_steps": steps,
        "learning_rate": lr,
        "rank": int(concept.get("rank") or cfg.get("rank") or 16),
        "resolution": "medium",
        "number_of_frames": 73,
        "frame_rate": 24,
        "auto_scale_input": True,
        "strict_dataset": True,
        "debug_dataset": True,
        "trigger_phrase": "",
        "trigger_strategy": "baked_in_captions",
        "note_ja": "trigger はキャプション先頭に焼いてある。fal の trigger_phrase は空のまま。両方に入れない。料金は fal のtrainerページを見る。",
    }


def coverage_report(
    rows: list[dict[str, Any]],
    concept: dict[str, Any],
    bundle: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], list[str]]:
    cfg = defaults(bundle)
    poses = list(concept.get("poses") or POSE_ORDER[:6])
    cameras = list(cfg.get("cameras") or CAMERA_ORDER)
    shots = list(cfg.get("shots") or SHOT_ORDER)
    aspects = list(cfg.get("aspects") or ["9:16", "16:9"])
    pose_max = float(cfg.get("pose_max_share") or 0.25)
    n = len(rows)
    pose_counts = {pose: 0 for pose in poses}
    camera_counts = {cam: 0 for cam in cameras}
    shot_counts = {shot: 0 for shot in shots}
    aspect_counts = {asp: 0 for asp in aspects}
    unknown = 0
    for row in rows:
        tags = row["tags"]
        if tags.get("pose") in pose_counts:
            pose_counts[tags["pose"]] += 1
        else:
            unknown += 1
        if tags.get("camera") in camera_counts:
            camera_counts[tags["camera"]] += 1
        if tags.get("shot") in shot_counts:
            shot_counts[tags["shot"]] += 1
        if tags.get("aspect") in aspect_counts:
            aspect_counts[tags["aspect"]] += 1
    warnings: list[str] = []
    if unknown:
        warnings.append(f"{unknown} clip(s) have no known pose in the filename")
    if n:
        for pose, count in pose_counts.items():
            share = count / n
            if share > pose_max + 1e-9:
                warnings.append(
                    f"pose {pose} is {share:.0%} of the set (cap {pose_max:.0%}). "
                    "this becomes a pose LoRA like ThumbInButt"
                )
    missing_poses = [pose for pose, count in pose_counts.items() if count == 0]
    if n >= 12 and missing_poses:
        warnings.append(f"missing poses: {', '.join(missing_poses)}")
    missing_cameras = [cam for cam, count in camera_counts.items() if count == 0]
    if n >= 16 and len(missing_cameras) >= 2:
        warnings.append(f"missing cameras: {', '.join(missing_cameras)}")
    missing_shots = [shot for shot, count in shot_counts.items() if count == 0]
    if n >= 12 and missing_shots:
        warnings.append(f"missing shots: {', '.join(missing_shots)}")
    missing_aspects = [asp for asp, count in aspect_counts.items() if count == 0]
    if n >= 16 and missing_aspects:
        warnings.append(f"missing aspects: {', '.join(missing_aspects)}")
    return {
        "n": n,
        "poses": pose_counts,
        "cameras": camera_counts,
        "shots": shot_counts,
        "aspects": aspect_counts,
        "unknown_pose": unknown,
        "pose_max_share": pose_max,
    }, warnings


def resolve_caption(
    concept: dict[str, Any],
    video: Path,
    tags: dict[str, str],
    rewrite: bool,
) -> str:
    side = video.with_suffix(".txt")
    generated = render_caption(concept, tags)
    if rewrite or not side.is_file():
        return generated
    existing = side.read_text(encoding="utf-8").strip()
    if not existing:
        return generated
    trigger = str(concept.get("trigger") or "")
    if caption_starts_with_trigger(existing, trigger) or trigger in existing.split():
        return " ".join(existing.split())
    return f"{trigger}, {existing}"


def validate_text(label: str, text: str, foreign: tuple[str, ...]) -> list[str]:
    errors: list[str] = []
    if find_secrets(text):
        errors.append(f"{label}: looks like a secret")
    minors = find_minors(text)
    if minors:
        errors.append(f"{label}: minor terms {', '.join(minors)}")
    other = find_other_trigger(text, foreign)
    if other:
        errors.append(f"{label}: other concept trigger {other}")
    return errors


def inspect_probe(
    video: Path,
    concept: dict[str, Any],
    bundle: dict[str, Any],
) -> tuple[dict[str, Any] | None, list[str], list[str]]:
    cfg = defaults(bundle)
    seconds = cfg.get("clip_seconds") or {}
    want_min = float(seconds.get("min") or 5)
    want_max = float(seconds.get("max") or 10)
    hard_max = float(seconds.get("hard_max") or 15)
    info = probe_video(video)
    warnings: list[str] = []
    errors: list[str] = []
    fps = float(info.get("fps") or 0)
    if not fps_is_24(fps):
        errors.append(f"{video.name}: fps {fps:.3f} (need exact 24.000)")
    dur = float(info.get("duration_s") or 0)
    if dur > 30:
        errors.append(f"{video.name}: {dur:.1f}s is over 30s")
    elif dur > hard_max:
        errors.append(f"{video.name}: {dur:.1f}s is over {hard_max:.0f}s")
    elif dur and dur < 3:
        errors.append(f"{video.name}: {dur:.1f}s is under 3s")
    elif dur and (dur < want_min or dur > want_max):
        warnings.append(
            f"{video.name}: {dur:.1f}s (aim {want_min:.0f}-{want_max:.0f}s)"
        )
    width = int(info.get("width") or 0)
    height = int(info.get("height") or 0)
    if width and height and (width % 32 or height % 32):
        warnings.append(f"{video.name}: {width}x{height} is not a multiple of 32")
    if not info.get("has_audio"):
        warnings.append(f"{video.name}: no audio track (H3 trains sound too)")
    return info, warnings, errors


def collect_rows(
    concept: dict[str, Any],
    src: Path,
    bundle: dict[str, Any],
    *,
    rewrite: bool,
    skip_probe: bool,
) -> tuple[list[dict[str, Any]], list[str], list[str]]:
    if not src.is_dir():
        raise PackError(f"src is not a folder: {src}")
    videos = iter_videos(src)
    if not videos:
        raise PackError(f"no video files in {src}")
    foreign = other_triggers(str(concept["id"]), bundle)
    rows: list[dict[str, Any]] = []
    warnings: list[str] = []
    errors: list[str] = []
    for video in videos:
        tags = parse_filename_tags(video.name)
        errors.extend(validate_text(video.name, video.name, foreign))
        caption = resolve_caption(concept, video, tags, rewrite=rewrite)
        errors.extend(validate_text(f"{video.name} caption", caption, foreign))
        if MALE_RE.search(caption):
            warnings.append(f"{video.name}: caption names a man")
        if not caption_starts_with_trigger(caption, str(concept["trigger"])):
            warnings.append(f"{video.name}: caption should start with {concept['trigger']}")
        if not camera_after_action(caption):
            warnings.append(f"{video.name}: put the act before the camera in the caption")
        probe = None
        if not skip_probe:
            probe, probe_warns, probe_errors = inspect_probe(video, concept, bundle)
            warnings.extend(probe_warns)
            errors.extend(probe_errors)
        rows.append(
            {
                "src": str(video),
                "name": video.name,
                "tags": tags,
                "caption": caption,
                "probe": probe,
            }
        )
    return rows, warnings, errors


def write_captions(rows: list[dict[str, Any]]) -> None:
    for row in rows:
        Path(row["src"]).with_suffix(".txt").write_text(
            row["caption"] + "\n", encoding="utf-8"
        )


def pack_zip(rows: list[dict[str, Any]], zip_path: Path) -> None:
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for index, row in enumerate(rows, start=1):
            src = Path(row["src"])
            stem = f"{index:02d}"
            zf.write(src, arcname=stem + src.suffix.lower())
            zf.writestr(stem + ".txt", row["caption"] + "\n")


def write_report(
    path: Path,
    concept: dict[str, Any],
    rows: list[dict[str, Any]],
    coverage: dict[str, Any],
    warnings: list[str],
    fal: dict[str, Any],
) -> None:
    payload = {
        "schema": PACK_SCHEMA,
        "concept": concept.get("id"),
        "title_ja": concept.get("title_ja"),
        "trigger": concept.get("trigger"),
        "filename": concept.get("filename"),
        "clips": [
            {
                "n": index,
                "src": row["name"],
                "zip": f"{index:02d}{Path(row['name']).suffix.lower()}",
                "tags": row["tags"],
                "caption": row["caption"],
            }
            for index, row in enumerate(rows, start=1)
        ],
        "coverage": coverage,
        "warnings": warnings,
        "fal": fal,
    }
    dumped = json.dumps(payload, ensure_ascii=False, indent=2)
    if find_secrets(dumped):
        raise PackError("report would contain a secret")
    path.write_text(dumped + "\n", encoding="utf-8")


def grid_cells(concept: dict[str, Any], bundle: dict[str, Any] | None = None) -> list[dict[str, str]]:
    cfg = defaults(bundle)
    cells: list[dict[str, str]] = []
    n = 0
    for pose in concept.get("poses") or []:
        for camera in cfg.get("cameras") or CAMERA_ORDER:
            for shot in cfg.get("shots") or SHOT_ORDER:
                for aspect in cfg.get("aspects") or ["9:16", "16:9"]:
                    n += 1
                    aspect_token = aspect.replace(":", "x")
                    name = f"{pose}_{camera}_{shot}_{aspect_token}_{n:02d}.mp4"
                    cells.append(
                        {
                            "pose": pose,
                            "camera": camera,
                            "shot": shot,
                            "aspect": aspect,
                            "filename": name,
                        }
                    )
    return cells


def format_grid(concept: dict[str, Any], bundle: dict[str, Any] | None = None) -> str:
    lines = [
        f"# {concept['id']}  {concept.get('title_ja', '')}",
        f"trigger {concept.get('trigger')}  (bake in captions, leave fal trigger_phrase empty)",
        "",
        "filename = pose_camera_shot_aspect_nn.mp4",
        "",
    ]
    for cell in grid_cells(concept, bundle):
        lines.append(
            f"{cell['pose']:<11} {cell['camera']:<7} {cell['shot']:<7} "
            f"{cell['aspect']:<5} {cell['filename']}"
        )
    return "\n".join(lines) + "\n"


def format_list(bundle: dict[str, Any] | None = None) -> str:
    data = bundle or load_bundle()
    lines = ["id                 trigger   title"]
    for row in list_concepts(data):
        lines.append(
            f"{row['id']:<18} {row['trigger']:<9} {row.get('title_ja', '')}"
        )
    for row in skipped_concepts(data):
        lines.append(
            f"{'(skip) ' + row['id']:<18} {'—':<9} {row.get('reason_ja', '')}"
        )
    return "\n".join(lines) + "\n"


def _pose_line(concept: dict[str, Any]) -> str:
    return " / ".join(str(p) for p in (concept.get("poses") or []))


def format_checklist(bundle: dict[str, Any] | None = None) -> str:
    """Naomiチ向け。準備と作業を分ける。concepts.json が正。"""
    data = bundle or load_bundle()
    cfg = defaults(data)
    seconds = cfg.get("clip_seconds") or {}
    targets = cfg.get("target_clips") or {}
    aim_min = int(targets.get("min") or 80)
    aim_max = int(targets.get("max") or 160)
    fal_min = int(targets.get("fal_min") or 10)
    pose_max = float(cfg.get("pose_max_share") or 0.25)
    trainer = str(cfg.get("trainer") or "minimax/h3/i2v/trainer")
    rank = int(cfg.get("rank") or 16)
    concepts = list_concepts(data)
    lines = [
        "# 学習キット — 準備すること / やること",
        "",
        "キットは **重みを作らない**。やることは素材の検品と fal 用 zip まで。",
        "学習は fal。③への接続は `.safetensors` が Drive に入ってから **別セッション**。",
        "今の③は竿＋穴＋文章で出す。このキットは効きを固める用。",
        "",
        "## 担当",
        "",
        "| 誰 | やること |",
        "|---|---|",
        "| ナオミチ | 権利のある素材、撮影／収集、フォルダ分け、fal の課金、できた重みを Drive に置く |",
        "| キット（このフォルダ） | グリッド、キャプション、zip、構図の偏り検品 |",
        "| fal | `debug_dataset` のあと本学習 |",
        "| 別セッション | カタログ接続。重みが無いあいだは③に足さない |",
        "",
        "## 作る3本（1フォルダ1本。混ぜない）",
        "",
        "| id | トリガー | 覚えること | 体位 | グリッド |",
        "|---|---|---|---|---|",
    ]
    for row in concepts:
        n = len(grid_cells(row, data))
        lines.append(
            f"| `{row['id']}` | `{row['trigger']}` | {row.get('title_ja', '')} | "
            f"{_pose_line(row)} | {n}セル |"
        )
    lines.extend(
        [
            "",
            "1セル1本で埋めると **96本／概念**。これが本線（目標 "
            f"{aim_min}〜{aim_max}）。fal の下限は {fal_min}本だが、それだと構図が固定される。",
            f"1体位は全体の **{pose_max:.0%}超禁止**（96本なら1体位24本まで。均等なら16本）。",
            "",
            "## 作らない",
            "",
        ]
    )
    for row in skipped_concepts(data):
        lines.append(f"- `{row['id']}` … {row.get('reason_ja', '')}")
    lines.extend(
        [
            "- 3行為を1 LoRA に混ぜる（立ってキスしただけで糞や尿が混ざる）",
            "- ThumbInButt の四つん這い素材を流用する（また構図が死ぬ）",
            "",
            "## 準備（撮る／集める前。これがないと始めない）",
            "",
            "1. **ffmpeg / ffprobe**（24.000fps に打ち直す。無いとパックが落ちる）",
            f"2. **fal アカウント**。trainer は `{trainer}`。Fal H3 Max には LoRA を差せない",
            "3. **作業フォルダを3つ**。zip も素材も Git に入れない",
            "",
            "```",
            "h3-train/",
            "  raw/anal-any-h3/",
            "  raw/urine-drink-h3/",
            "  raw/scat-act-h3/",
            "  packed/",
            "```",
            "",
            "4. **権利のある素材だけ**（自分で撮る／買う／利用許諾がある）。無断転載は使わない",
            "5. **出演は成人女性／ふたなり 22歳以上だけ**。男なし。未成年なし",
            "6. グリッドを出す（印刷してチェックする）",
            "",
            "```bash",
            "python3 h3-lora-studio/train/pack_dataset.py --print-checklist",
            "python3 h3-lora-studio/train/pack_dataset.py --concept anal-any-h3 --print-grid",
            "python3 h3-lora-studio/train/pack_dataset.py --write-kit",
            "```",
            "",
            "印刷用は `h3-lora-studio/train/grids/<id>.txt`。",
            "",
            "## 素材の仕様（1本ずつ）",
            "",
            f"- 長さ **{int(seconds.get('min') or 5)}〜{int(seconds.get('max') or 10)}秒**。"
            f"3秒未満と {int(seconds.get('hard_max') or 15)}秒超は落とす",
            "- **ちょうど 24.000 fps**。23.976 / 25 / 30 は打ち直す。スローは等速に戻す",
            "- 先頭と末尾は黒・フェードなし",
            "- **音は残す**（H3 は映像と音を同時に覚える）",
            "- 解像度は 32 の倍数。9:16 は 704×1280。16:9 は 1280×704",
            "- ファイル名（キャプションは手で書かなくてよい）",
            "",
            "```",
            "{pose}_{camera}_{shot}_{aspect}_{番号}.mp4",
            "standing_front_close_9x16_01.mp4",
            "```",
            "",
            "camera は `front` `behind` `side` `above`。shot は `close` `medium`。aspect は `9x16` `16x9`。",
            "",
            "打ち直し（9:16の例。音を消さない）:",
            "",
            "```bash",
            "ffmpeg -y -i IN.mp4 \\",
            '  -filter:v "fps=24,scale=704:1280:force_original_aspect_ratio=decrease,'
            'pad=704:1280:(ow-iw)/2:(oh-ih)/2,setsar=1" \\',
            "  -t 10 -c:v libx264 -pix_fmt yuv420p -c:a aac -ar 44100 \\",
            "  standing_front_close_9x16_01.mp4",
            "```",
            "",
            "16:9 は `scale=1280:704` と `pad=1280:704`。",
            "",
            "## 概念ごとの中身（撮るときこれだけ見る）",
            "",
        ]
    )
    for row in concepts:
        lines.append(f"### `{row['id']}`（`{row['trigger']}`）")
        lines.append("")
        lines.append(str(row.get("why_ja") or ""))
        lines.append("")
        lines.append("画面に必須:")
        for item in row.get("must_show") or []:
            lines.append(f"- {item}")
        lines.append("")
        lines.append("画面に出したら捨てる:")
        for item in row.get("never_show") or []:
            lines.append(f"- {item}")
        extra = row.get("not_this") or []
        if extra:
            lines.append("")
            lines.append("この LoRA の仕事ではない: " + " / ".join(str(x) for x in extra))
        lines.append("")
    lines.extend(
        [
            "アナルは **もう入っている**。未挿入から入れる練習はしない。手は腰。親指にしない。膣にしない。",
            "飲尿は **亀頭先の尿道口から黄色い水**。根元のマンコから出さない。透明・白・画面外から、にしない。相手が飲む。",
            "脱糞は **今出している動き**。最初から塗れている肥溜めとは別。",
            "",
            "## やること（1概念ずつ。3本並行で混ぜない）",
            "",
            "### A. 集める",
            "",
            "1. `grids/<id>.txt` を開く",
            "2. 1セル1本撮る／集める。ファイル名をグリッド通りにする",
            "3. 上の ffmpeg で 24.000fps にする",
            "4. 目視: 行為が見える。別行為が映っていない。男がいない",
            "",
            "### B. パック（キット）",
            "",
            "```bash",
            "python3 h3-lora-studio/train/pack_dataset.py --list",
            "python3 h3-lora-studio/train/pack_dataset.py \\",
            "  --concept anal-any-h3 \\",
            "  --src ~/h3-train/raw/anal-any-h3 \\",
            "  --out ~/h3-train/packed \\",
            "  --check-only --strict-coverage",
            "```",
            "",
            "警告が残るうちは zip を作らない。体位が偏っていたら撮り足す。",
            "通ったら `--check-only` を外して zip を出す。",
            "",
            "```bash",
            "python3 h3-lora-studio/train/pack_dataset.py \\",
            "  --concept anal-any-h3 \\",
            "  --src ~/h3-train/raw/anal-any-h3 \\",
            "  --out ~/h3-train/packed \\",
            "  --rewrite-captions --strict-coverage",
            "```",
            "",
            "出来物:",
            "",
            "- `packed/anal-any-h3.zip` … 中身は `01.mp4` + `01.txt` の連番（fal の形式）",
            "- `packed/anal-any-h3-pack-report.json` … 本数・体位の割合・fal の推奨値",
            "- 隣の `.txt` はキャプション。先頭にトリガーが焼いてある",
            "",
            "ffprobe が無い試し打ちだけ `--skip-probe`。10本未満の配線確認だけ `--allow-small`。本学習には使わない。",
            "",
            "### C. fal",
            "",
            f"1. trainer `{trainer}` を開く",
            "2. **先に** `debug_dataset: true`。クロップとキャプションを見る。おかしかったら本学習しない",
            f"3. rank **{rank}**",
            f"4. {aim_min}本前後は 3000 step / 2e-4。120本超は 5000 step / 1e-4（report の `fal` に書いてある）",
            "5. `trigger_phrase` は **空**。キャプションに焼いてある。両方に入れると従わなくなる",
            "6. `auto_scale_input: true`、`strict_dataset: true`、`number_of_frames: 73`、24fps",
            "7. 料金はその場で fal の trainer ページを見る（ここに数字を書かない）",
            "8. 終わったら CDN を当てにせず `.safetensors` をすぐ落とす",
            "",
            "`Lora_Trainer_XL.ipynb` は SDXL。H3 には使わない。musubi-tuner の still は顔向き。この3本は動画で覚える。",
            "",
            "### D. 重みが手元に来てから（今はやらない）",
            "",
            "1. Drive `minimax-h3-comfyui/models/loras/` に置く",
            "   - `anal-any-h3.safetensors`",
            "   - `urine-drink-h3.safetensors`",
            "   - `scat-act-h3.safetensors`",
            "2. 別セッションでカタログに行を足す（`source: local`。②は DL せず Drive の同名ファイルを使う）",
            "3. アナルの act を `anal-any-h3` にする（竿＋穴は残す。ThumbInButt は戻さない）",
            "4. 飲尿・脱糞は今の situation の act を差し替える。**新しい話だけ**",
            "5. 既存話のジュボ置き換えは戻さない。医院・終電の `No feces.` は外さない",
            "",
            "## この概念が終わったと言える条件",
            "",
            f"- その概念の zip がある。中は連番の mp4+txt。本数 {aim_min}以上",
            f"- report の体位シェアがどれも {pose_max:.0%}以下。欠け体位なし",
            "- キャプション先頭がトリガー。fal の `trigger_phrase` は空",
            "- debug_dataset でクロップが行為を映している",
            "- `.safetensors` をローカル／Drive に保存した（CDN だけにしない）",
            "- まだカタログに行が無い（無い重みを③に足していない）",
            "",
            "## やらないこと",
            "",
            "- 3行為を1 LoRA に混ぜる",
            "- 1体位ばかり集める",
            "- 重みが無い状態で③／カタログに足す",
            "- 既存ストーリーへ飲尿を戻す",
            "- 医院・終電の `No feces.` を外す",
            "- 男・未成年を素材に入れる",
            "- fal の trigger とキャプションの二重焼き",
            "- 数字を発明して「学習できた」ことにする",
            "- Threads の schedule を戻す",
            "",
        ]
    )
    return "\n".join(lines)


def write_kit(dest: Path | None = None, bundle: dict[str, Any] | None = None) -> list[Path]:
    data = bundle or load_bundle()
    root = dest or TRAIN_DIR
    root.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    checklist = root / "CHECKLIST.md"
    checklist.write_text(format_checklist(data), encoding="utf-8")
    written.append(checklist)
    grids = root / "grids"
    grids.mkdir(parents=True, exist_ok=True)
    for concept in list_concepts(data):
        path = grids / f"{concept['id']}.txt"
        path.write_text(format_grid(concept, data), encoding="utf-8")
        written.append(path)
    return written


def assert_ready(
    rows: list[dict[str, Any]],
    warnings: list[str],
    errors: list[str],
    bundle: dict[str, Any],
    *,
    allow_small: bool,
    strict_coverage: bool,
) -> None:
    cfg = defaults(bundle)
    targets = cfg.get("target_clips") or {}
    fal_min = int(targets.get("fal_min") or 10)
    aim_min = int(targets.get("min") or 80)
    n = len(rows)
    if errors:
        raise PackError("\n".join(errors))
    if n < fal_min and not allow_small:
        raise PackError(f"{n} clips (fal needs {fal_min}+; aim {aim_min}+)")
    if n < aim_min:
        warnings.append(f"{n} clips (aim {aim_min}-{targets.get('max', 160)})")
    if strict_coverage and warnings:
        raise PackError("coverage warnings:\n" + "\n".join(warnings))


def run_pack(args: argparse.Namespace) -> int:
    bundle = load_bundle()
    if args.list:
        sys.stdout.write(format_list(bundle))
        return 0
    if args.print_checklist:
        sys.stdout.write(format_checklist(bundle))
        return 0
    if args.write_kit is not None:
        dest = Path(args.write_kit) if args.write_kit else TRAIN_DIR
        written = write_kit(dest, bundle)
        sys.stdout.write("wrote\n" + "\n".join(str(path) for path in written) + "\n")
        if not args.concept:
            return 0
    if not args.concept:
        raise PackError("need --concept (or --list / --print-checklist / --write-kit)")
    concept = get_concept(args.concept, bundle)
    if args.print_grid or args.write_shot_list:
        text = format_grid(concept, bundle)
        if args.write_shot_list:
            dest = Path(args.write_shot_list)
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(text, encoding="utf-8")
        if args.print_grid or not args.src:
            sys.stdout.write(text)
            if not args.src:
                return 0
    if not args.src:
        raise PackError("need --src")
    src = Path(args.src)
    rows, warnings, errors = collect_rows(
        concept,
        src,
        bundle,
        rewrite=args.rewrite_captions,
        skip_probe=args.skip_probe,
    )
    coverage, cover_warns = coverage_report(rows, concept, bundle)
    warnings.extend(cover_warns)
    assert_ready(
        rows,
        warnings,
        errors,
        bundle,
        allow_small=args.allow_small,
        strict_coverage=args.strict_coverage,
    )
    if args.write_captions_only or not args.check_only:
        write_captions(rows)
    fal = recommend_fal(concept, len(rows), bundle)
    out_dir = Path(args.out) if args.out else src
    out_dir.mkdir(parents=True, exist_ok=True)
    report_path = out_dir / f"{concept['id']}-pack-report.json"
    write_report(report_path, concept, rows, coverage, warnings, fal)
    zip_path = out_dir / f"{concept['id']}.zip"
    if args.check_only or args.write_captions_only:
        sys.stdout.write(f"clips {len(rows)}\nreport {report_path}\n")
    else:
        pack_zip(rows, zip_path)
        sys.stdout.write(f"clips {len(rows)}\nzip {zip_path}\nreport {report_path}\n")
    if warnings:
        sys.stdout.write("warnings:\n" + "\n".join(f"- {item}" for item in warnings) + "\n")
    sys.stdout.write(
        f"next: fal debug_dataset on {fal['trainer']} "
        f"(rank {fal['rank']}, trigger_phrase empty)\n"
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Pack one H3 concept LoRA dataset (anal / urine-drink / scat-act)."
    )
    parser.add_argument("--concept", help="anal-any-h3 | urine-drink-h3 | scat-act-h3")
    parser.add_argument("--src", help="folder of clips")
    parser.add_argument("--out", help="folder for zip + report")
    parser.add_argument("--list", action="store_true", help="print concepts")
    parser.add_argument("--print-checklist", action="store_true", help="print prepare/do checklist")
    parser.add_argument(
        "--write-kit",
        nargs="?",
        const="",
        default=None,
        help="write CHECKLIST.md and grids/ (default: this folder)",
    )
    parser.add_argument("--print-grid", action="store_true", help="print composition grid")
    parser.add_argument("--write-shot-list", help="write the grid to this text file")
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--write-captions-only", action="store_true")
    parser.add_argument("--rewrite-captions", action="store_true")
    parser.add_argument("--skip-probe", action="store_true", help="skip ffprobe")
    parser.add_argument("--allow-small", action="store_true", help="allow under 10 clips")
    parser.add_argument("--strict-coverage", action="store_true", help="fail on coverage warnings")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return run_pack(args)
    except PackError as exc:
        sys.stderr.write(str(exc) + "\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
