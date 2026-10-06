"""Write an H3 bake job from a genre table or a reference cut sheet.

Seconds, cuts, and subtitles stay on the template. This module does not
render an mp4 and does not post. Spoken lines that are still the placeholder
stay missing. They are not filled in here.
"""

from __future__ import annotations

import argparse
import json
import shlex
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

import affi_reference as ref

_RUNNER = Path(__file__).resolve().parents[2] / "h3-runner"
if (_RUNNER / "h3_runner").is_dir():
    sys.path.insert(0, str(_RUNNER))

try:
    from h3_runner.official import (
        MAX_DURATION_S,
        MIN_DURATION_S,
        diffusers_accepts,
        frames_for_seconds,
    )
except ImportError:
    # The reference Colab downloads this folder without h3-runner.
    # These match h3_runner/official.py: fps 24, 17*n+5, aligned duration in [5, 15].
    MIN_DURATION_S = 5.0
    MAX_DURATION_S = 15.0

    def frames_for_seconds(duration_s: float) -> int:
        return int(round(float(duration_s) * 24))

    def _align_num_frames(num_frames: int) -> int:
        frames = int(num_frames)
        while frames % 17 != 5:
            frames += 1
        return frames

    def diffusers_accepts(num_frames: int) -> bool:
        aligned = _align_num_frames(num_frames) / 24
        return MIN_DURATION_S <= aligned <= MAX_DURATION_S


SCHEMA = "affi-bake-job/v1"
PLACEHOLDER_LINE = "台詞は入力"
PLACEHOLDER_THEME = "テーマは入力"

# Same map as affi_genre_templates.REFERENCE_HANDLES.
# Kept here so the reference Colab does not have to download the genre module.
GENRE_HANDLES = {
    "美容スキンケア": "the.care.logic",
    "ドッグフード": "nuts0629",
    "見守りカメラ": "junjun_ranran",
    "婚活": "yako.shiawasekon",
}

# Colab のドロップダウンに出す文。ハンドルだけではどれか分からない。
ACCOUNT_CHOICES = (
    ("美容スキンケア（the.care.logic）", "the.care.logic"),
    ("ドッグフード（nuts0629）", "nuts0629"),
    ("見守りカメラ（junjun_ranran）", "junjun_ranran"),
    ("婚活（yako.shiawasekon）", "yako.shiawasekon"),
)
DOG_PATTERNS = (
    ("インタビュー（既定）", "interview"),
    ("咀嚼", "asmr"),
    ("ダンス", "dance"),
    ("会話", "talk"),
)
_MODE_JA = {mode: label.split("（")[0] for label, mode in DOG_PATTERNS}
_ALL_LOOKS = ("キャラ", "動物", "動物2", "人物", "人物2", "場所", "口調")


def resolve_account(label: str, dog_pattern: str = "インタビュー（既定）") -> tuple[str, str | None]:
    """Map the Colab menu to one handle. Dog-food patterns apply only to nuts0629."""
    handles = {text: handle for text, handle in ACCOUNT_CHOICES}
    handles.update({handle: handle for _text, handle in ACCOUNT_CHOICES})
    handle = handles.get(label)
    if handle is None:
        raise KeyError(f"アカウントが無い: {label}")
    if handle != "nuts0629":
        return handle, None
    modes = {text: mode for text, mode in DOG_PATTERNS}
    mode = modes.get(dog_pattern)
    if mode is None:
        raise KeyError(f"ドッグフードの型が無い: {dog_pattern}")
    return handle, mode


def describe_account(handle: str, mode: str | None = None) -> str:
    """One account, in Japanese, before any other sheet."""
    item = ref.template_for(handle)
    view = _mode_view(item, mode)
    beats = _expand_beats(view["timeline"], int(view["repeat"]))
    cut_sum = round(sum(float(beat["end_s"]) - float(beat["start_s"]) for beat in beats), 3)
    used = ref.used_look_names(handle)
    unused = [name for name in _ALL_LOOKS if name not in used]
    pattern = _MODE_JA.get(view["mode"] or "", "切り替えはない")
    lines = [
        "再現するのはこの1件です。",
        f"ジャンル: {item['genre']}",
        f"アカウント: {handle}",
        f"型: {pattern}",
        f"秒: {_num(float(view['duration_s']))}",
        f"画面: {view['canvas']}",
        f"使う見た目: {'、'.join(used)}",
        f"使わない見た目: {'、'.join(unused)}",
    ]
    if abs(cut_sum - float(view["duration_s"])) > 0.051:
        lines.append(
            f"カットの合計は {_num(cut_sum)} 秒。型は {_num(float(view['duration_s']))} 秒。足りない秒は足さない。"
        )
    if handle != "nuts0629":
        lines.append("型の切り替えはドッグフードだけ。このアカウントでは使わない。")
    return "\n".join(lines)


def _accepts(duration_s: float) -> bool:
    return bool(diffusers_accepts(frames_for_seconds(duration_s)))


def _num(value: float) -> str:
    return f"{float(value):.3f}".rstrip("0").rstrip(".")


def _needs_line(speech: str) -> bool:
    return str(speech or "").strip() not in {"", "なし", "無し"}


def _aspect(canvas: str) -> tuple[str, int, int]:
    raw = str(canvas).lower().replace("×", "x")
    width_s, height_s = raw.split("x")
    width, height = int(width_s), int(height_s)
    if height >= width:
        return "9:16", 1080, 1920
    return "16:9", 1920, 1080


def _mode_view(item: Mapping[str, Any], mode: str | None) -> dict[str, Any]:
    modes = item.get("modes") or {}
    if not modes:
        return {
            "mode": None,
            "timeline": list(item["timeline"]),
            "duration_s": float(item["duration_s"]),
            "canvas": str(item["canvas"]),
            "subtitle": item.get("subtitle"),
            "repeat": 1,
            "cuts": item.get("cuts"),
            "audio": item.get("audio"),
        }
    key = mode or item.get("default_mode")
    if not key or key not in modes:
        raise KeyError(f"mode が無い: {key}")
    block = modes[key]
    return {
        "mode": key,
        "timeline": list(block["timeline"]),
        "duration_s": float(block["duration_s"]),
        "canvas": str(block.get("canvas") or item.get("canvas")),
        "subtitle": block.get("subtitle"),
        "repeat": int(block.get("repeat") or 1),
        "cuts": block.get("cuts"),
        "audio": block.get("audio"),
    }


def _expand_beats(timeline: Sequence[Mapping[str, Any]], repeat: int) -> list[dict[str, Any]]:
    beats = [dict(beat) for beat in timeline if not beat.get("optional")]
    if repeat < 1:
        raise ValueError(f"repeat が 0 以下: {repeat}")
    if repeat == 1 or not beats:
        return beats
    span = float(beats[-1]["end_s"]) - float(beats[0]["start_s"])
    if span <= 0:
        raise ValueError("繰り返すカットの長さが 0")
    expanded: list[dict[str, Any]] = []
    for cycle in range(repeat):
        offset = cycle * span
        for beat in beats:
            row = dict(beat)
            row["start_s"] = float(beat["start_s"]) + offset
            row["end_s"] = float(beat["end_s"]) + offset
            row["id"] = f"{beat['id']}-{cycle + 1}"
            expanded.append(row)
    return expanded


def split_trim(total: float) -> list[float]:
    """Cut lengths that sum to ``total`` and that H3 can generate.

    A piece shorter than 5 seconds stays that long in the edit. The generator
    request is raised to 5 seconds and trimmed back. A piece H3 cannot take
    as one request is split into equal pieces inside 5–15 seconds.
    """
    total_ms = int(round(float(total) * 1000))
    if total_ms <= 0:
        raise ValueError(f"カットの長さが 0 以下: {total}")
    seconds = total_ms / 1000
    if seconds < MIN_DURATION_S or (seconds <= MAX_DURATION_S and _accepts(seconds)):
        return [seconds]
    count = 2
    while count <= 24:
        if seconds / count < MIN_DURATION_S - 1e-9:
            break
        each = total_ms // count
        parts_ms = [each] * count
        parts_ms[-1] += total_ms - each * count
        parts = [ms / 1000 for ms in parts_ms]
        if all(MIN_DURATION_S <= part <= MAX_DURATION_S and _accepts(part) for part in parts):
            return parts
        count += 1
    raise ValueError(f"H3 の 5〜15 秒に分けられない: {seconds}秒")


def _request_seconds(trim_s: float) -> float:
    if trim_s < MIN_DURATION_S:
        return float(MIN_DURATION_S)
    return float(trim_s)


def _one_take(cuts: Any, duration_s: float, beat_sum: float) -> bool:
    if cuts not in (0, "0"):
        return False
    if abs(beat_sum - duration_s) > 0.051:
        return False
    return MIN_DURATION_S <= duration_s <= MAX_DURATION_S and _accepts(duration_s)


def _subtitle_text(style: str, line: str, needs_line: bool) -> str:
    if style == "字幕なし":
        return "字幕なし"
    if needs_line and line and line != PLACEHOLDER_LINE:
        return line
    return style


def _prompt(beats: Sequence[Mapping[str, Any]], theme: str, lines: Sequence[str], locked: str) -> str:
    parts = [ref._imagine(beat, theme, line, locked) for beat, line in zip(beats, lines)]
    return "\n".join(parts)


def bake_reference(
    handle: str,
    *,
    mode: str | None = None,
    theme: str = PLACEHOLDER_THEME,
    lines: Sequence[str] | None = None,
    look: Mapping[str, Any] | None = None,
    image: str | None = None,
) -> dict[str, Any]:
    """One job. The template's timeline is the cut list. H3 only packs generation."""
    item = ref.template_for(handle)
    theme_text = (theme or "").strip() or PLACEHOLDER_THEME
    ref.reject_likeness(theme_text)
    for line in lines or []:
        ref.reject_likeness(line)
    view = _mode_view(item, mode)
    locked = ref.look_block(handle, look)
    beats = _expand_beats(view["timeline"], int(view["repeat"]))
    spoken = [str(line).strip() for line in (lines or [])]
    style = ref._subtitle_line(item, view["subtitle"])
    cuts: list[dict[str, Any]] = []
    for index, beat in enumerate(beats):
        line = spoken[index] if index < len(spoken) and spoken[index] else PLACEHOLDER_LINE
        needs = _needs_line(str(beat.get("speech") or ""))
        start_s = float(beat["start_s"])
        end_s = float(beat["end_s"])
        cuts.append(
            {
                "id": str(beat["id"]),
                "start_s": start_s,
                "end_s": end_s,
                "duration_s": round(end_s - start_s, 3),
                "picture": beat.get("picture"),
                "camera": beat.get("camera"),
                "speech": beat.get("speech"),
                "line": line,
                "needs_line": needs,
                "subtitle": _subtitle_text(style, line, needs),
            }
        )
    duration_s = float(view["duration_s"])
    cut_sum = round(sum(cut["duration_s"] for cut in cuts), 3)
    blocked: list[str] = []
    if abs(cut_sum - duration_s) > 0.051:
        blocked.append(
            f"カットの合計 { _num(cut_sum) } 秒と型の { _num(duration_s) } 秒が違う。足りない秒は足さない。"
        )
    aspect, delivery_w, delivery_h = _aspect(view["canvas"])
    clips: list[dict[str, Any]] = []
    if not any(reason.startswith("カットの合計") for reason in blocked):
        if _one_take(view["cuts"], duration_s, cut_sum):
            groups = [(cuts, duration_s)]
        else:
            groups = [([cut], float(cut["duration_s"])) for cut in cuts]
        serial = 1
        for group, group_duration in groups:
            cursor = float(group[0]["start_s"])
            prompt = _prompt(group, theme_text, [cut["line"] for cut in group], locked["line"])
            cut_ids = [cut["id"] for cut in group]
            for trim_s in split_trim(group_duration):
                request_s = _request_seconds(trim_s)
                if not _accepts(request_s):
                    raise ValueError(f"H3 が受け取れない秒数: {request_s}")
                clip_id = f"{serial:02d}-" + "-".join(cut_ids)
                end_s = round(cursor + trim_s, 3)
                clips.append(
                    {
                        "id": clip_id,
                        "cut_ids": cut_ids,
                        "trim_s": trim_s,
                        "request_s": request_s,
                        "prompt_name": f"{clip_id}.txt",
                        "prompt": prompt,
                        "start_s": round(cursor, 3),
                        "end_s": end_s,
                    }
                )
                cursor = end_s
                serial += 1
    if theme_text == PLACEHOLDER_THEME:
        blocked.append("テーマは入力のまま")
    for cut in cuts:
        if cut["needs_line"] and cut["line"] == PLACEHOLDER_LINE:
            blocked.append(f"{cut['id']} の台詞は入力のまま")
    image_text = (image or "").strip()
    if not image_text or not Path(image_text).is_file():
        blocked.append("静止画が無い。FL2VA は最初のコマに画像が要る")
    trim_sum = round(sum(clip["trim_s"] for clip in clips), 3)
    if clips and abs(trim_sum - duration_s) > 0.051:
        raise ValueError(f"書き出し {trim_sum} 秒が型の {duration_s} 秒と違う")
    return {
        "schema": SCHEMA,
        "source": "reference",
        "handle": handle,
        "genre": item["genre"],
        "mode": view["mode"],
        "theme": theme_text,
        "duration_s": duration_s,
        "canvas": view["canvas"],
        "aspect": aspect,
        "delivery_width": delivery_w,
        "delivery_height": delivery_h,
        "look": {"ja": locked["ja"], "en": locked["en"], "ref_image": locked["ref_image"]},
        "cuts": cuts,
        "clips": clips,
        "join": {
            "delivery": "delivery.mp4",
            "width": delivery_w,
            "height": delivery_h,
            "parts": [{"file": f"clips/{clip['id']}.mp4", "trim_s": clip["trim_s"]} for clip in clips],
        },
        "audio": view["audio"],
        "image": image_text,
        "status": "blocked" if blocked else "ready",
        "blocked": blocked,
        "generates_video": False,
        "posts": False,
        "seconds_from": "reference-template",
        "commands": [],
    }


def bake_genre(genre: str, **kwargs: Any) -> dict[str, Any]:
    handle = GENRE_HANDLES.get(genre)
    if handle is None:
        raise KeyError(f"ジャンルが無い: {genre}")
    job = bake_reference(handle, **kwargs)
    job["source"] = "genre"
    if job["genre"] != genre:
        job["blocked"].append("参照アカウントのジャンル名と表のジャンル名が違う")
        job["status"] = "blocked"
    return job


def annotate_table(
    job: dict[str, Any],
    *,
    duration_band: str | None,
    opening_type: str | None,
    main_subject: str | None,
    face_shown: str | None,
    basis: str | None,
    account_confidence: str | None,
    homage: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Attach the genre table. Do not change seconds, cuts, or subtitles."""
    table: dict[str, Any] = {
        "duration_band": duration_band,
        "opening_type": opening_type,
        "main_subject": main_subject,
        "face_shown": face_shown,
        "basis": basis,
        "account_confidence": account_confidence,
    }
    if homage:
        table["first_3_seconds"] = homage.get("first_3_seconds")
        table["borrow"] = list(homage.get("borrow") or [])
        table["do_not_copy"] = list(homage.get("do_not_copy") or [])
    job["source"] = "genre"
    job["genre_table"] = table
    job["seconds_from"] = "reference-template"
    return job


def _command(job_dir: Path, clip: Mapping[str, Any], image: str, aspect: str) -> str:
    args = [
        "python3",
        "h3-runner/run_h3.py",
        "--task",
        "fl2va",
        "--prompt-file",
        str(job_dir / "prompts" / str(clip["prompt_name"])),
        "--duration",
        _num(float(clip["request_s"])),
        "--aspect",
        aspect,
        "--seed",
        "0",
        "--out",
        str(job_dir / "clips" / f"{clip['id']}.mp4"),
    ]
    if image:
        args.extend(["--image", image])
    return " ".join(shlex.quote(part) for part in args)


def write_job(job: dict[str, Any], folder: str | Path) -> Path:
    """Write job.json, prompts, and the H3 commands. Do not run them."""
    job_dir = Path(folder)
    prompt_dir = job_dir / "prompts"
    prompt_dir.mkdir(parents=True, exist_ok=True)
    for clip in job["clips"]:
        (prompt_dir / str(clip["prompt_name"])).write_text(str(clip["prompt"]), encoding="utf-8")
    commands = [
        "# mp4 は焼かない。投稿しない。ready のとき、Research のルートで次を実行する。",
        f"# status={job['status']}",
    ]
    if job["blocked"]:
        commands.extend(f"# {reason}" for reason in job["blocked"])
    commands.extend(_command(job_dir, clip, str(job.get("image") or ""), str(job["aspect"])) for clip in job["clips"])
    job["commands"] = commands
    path = job_dir / "job.json"
    path.write_text(json.dumps(job, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (job_dir / "commands.txt").write_text("\n".join(commands) + "\n", encoding="utf-8")
    subtitles = [
        {"id": cut["id"], "start_s": cut["start_s"], "end_s": cut["end_s"], "text": cut["subtitle"]}
        for cut in job["cuts"]
    ]
    (job_dir / "subtitles.json").write_text(
        json.dumps(subtitles, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="型から H3 の焼くジョブを書く。mp4 は焼かない。投稿しない。")
    parser.add_argument("cmd", choices=["reference", "genre"])
    parser.add_argument("--handle", default="")
    parser.add_argument("--genre", default="")
    parser.add_argument("--mode", default="")
    parser.add_argument("--theme", default=PLACEHOLDER_THEME)
    parser.add_argument("--lines", default="")
    parser.add_argument("--image", default="")
    parser.add_argument("--look", default="")
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    look = ref.load_look(Path(args.look)) if args.look else None
    lines = args.lines.splitlines()
    mode = args.mode or None
    image = args.image or None
    if args.cmd == "reference":
        if not args.handle:
            raise SystemExit("reference には --handle が要る")
        job = bake_reference(args.handle, mode=mode, theme=args.theme, lines=lines, look=look, image=image)
    else:
        if not args.genre:
            raise SystemExit("genre には --genre が要る")
        job = bake_genre(args.genre, mode=mode, theme=args.theme, lines=lines, look=look, image=image)
    path = write_job(job, Path(args.out))
    print(job["status"])
    for reason in job["blocked"]:
        print(reason)
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
