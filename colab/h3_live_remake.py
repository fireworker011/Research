#!/usr/bin/env python3
"""Live-action remake plan from a measured source video.

The source video supplies timing, blocking, and camera only. Identity and costume
come only from the stills the human supplies. Each span is one Comfy Ref2VA
generation. This module measures the source and writes a plan. It does not
generate, it does not post, and it does not write story text.

Roles are ``S1``, ``S2`` and so on. Character names and looks stay out of this
module and out of the sheet skeleton.
"""

from __future__ import annotations

import json
import math
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

from h3_sfw import ANIME2REAL_STRENGTH, LORA_FILES

SCHEMA = "h3-live-remake/v1"
FPS = 24
# H3 frame grid is 17k+5. 124 frames (5.167s) is the first accepted length.
# 345 frames (14.375s) is the last one under the 15s check. 362 is refused.
FRAMES_PER_CHUNK = 17
FRAME_REMAINDER = 5
MIN_FRAMES = 124
MAX_FRAMES = 345
DEFAULT_MAX_SPAN_S = 8.0
SCENE_THRESHOLD = 0.35
# Flashes and impact frames trip scene detection. Cuts closer than this merge.
MIN_SHOT_S = 0.5
WIDE = (1344, 768)
TALL = (768, 1344)
RESOLUTION = "768P"
SLOT = "入力"
AUDIO_MODES = ("source", "generated")
ROLE_RE = re.compile(r"^S[1-9][0-9]?$")
PROP_RE = re.compile(r"^P[1-9][0-9]?$")
CJK_RE = re.compile(r"[\u3040-\u30ff\u4e00-\u9fff\uff66-\uff9f]")
DIALOGUE_RE = re.compile(r"<d>\[Japanese\] .*?</d>")
PICTURE_RE = re.compile(r"<Picture (\d+)>")
SUBJECT_RE = re.compile(r"<Subject (\d+)>")
VIDEO_RE = re.compile(r"<Video (\d+)>")
AUDIO_RE = re.compile(r"<Audio \d+>")
PTS_RE = re.compile(r"pts_time:([0-9.]+)")

LIVE_ACTION_LOCK = (
    "Photorealistic live-action footage of real people on a real set: real skin, real hair, "
    "real fabric, real light. Not anime, not cel-shaded, not illustrated, no outlines. "
    "Each picture locks only identity and costume. The prose does not describe appearance."
)
VIDEO_ROLE = (
    "It supplies timing, blocking, shot order, and camera only. Its drawn line, flat color, "
    "outlines, and painted speed lines are not kept."
)
DEFAULT_SOUND = "Physical sound follows the visible action. No added music."
GENERATE_MSG = "生成は人間。このプランはコマンドと文までで、Comfy の生成ボタンは押さない。"
WEIGHT_NOTE = (
    "anime2real の取得元はこのリポジトリに登録していない。"
    f"マイドライブの h3-weights/loras に {LORA_FILES['anime2real']} を置く。"
)


class RemakeError(Exception):
    """A sheet or a measurement that cannot become a plan."""


def frame_of(seconds: float) -> int:
    return int(round(float(seconds) * FPS))


def align_frames(frames: int) -> int:
    """Smallest accepted 17k+5 frame count at or above ``frames``."""
    count = max(int(frames), MIN_FRAMES)
    return count + (FRAME_REMAINDER - count % FRAMES_PER_CHUNK) % FRAMES_PER_CHUNK


def canvas_for(width: int, height: int) -> tuple[int, int]:
    return WIDE if int(width) >= int(height) else TALL


def _max_span_frames(max_span_s: float) -> int:
    frames = frame_of(max_span_s)
    if frames < MIN_FRAMES or frames > MAX_FRAMES:
        raise RemakeError(f"1本の長さは {MIN_FRAMES / FPS:.3f}〜{MAX_FRAMES / FPS:.3f} 秒")
    return frames


def merge_cuts(times: Sequence[float], duration_s: float, min_shot_s: float = MIN_SHOT_S) -> list[float]:
    """Drop cuts that leave a shot shorter than ``min_shot_s``."""
    kept: list[float] = []
    last = 0.0
    end = float(duration_s)
    for value in sorted(float(item) for item in times):
        if value - last < min_shot_s or end - value < min_shot_s:
            continue
        kept.append(round(value, 3))
        last = value
    return kept


def shot_frames(cuts: Sequence[float], duration_s: float) -> list[tuple[int, int]]:
    """Frame bounds per shot. Bounds come from the global clock, so spans add up exactly."""
    bounds = [0] + [frame_of(cut) for cut in cuts] + [frame_of(duration_s)]
    shots = []
    for start, end in zip(bounds, bounds[1:]):
        if end <= start:
            raise RemakeError("カットの秒が並んでいない")
        shots.append((start, end))
    return shots


def plan_spans(shots: Sequence[tuple[int, int]], max_span_s: float = DEFAULT_MAX_SPAN_S) -> list[dict[str, Any]]:
    """Pack whole shots into spans. A shot longer than one span is split evenly."""
    limit = _max_span_frames(max_span_s)
    spans: list[dict[str, Any]] = []
    open_span: dict[str, Any] | None = None
    for start, end in shots:
        length = end - start
        if length > limit:
            if open_span is not None:
                spans.append(open_span)
                open_span = None
            pieces = math.ceil(length / limit)
            edges = [start + round(length * index / pieces) for index in range(pieces + 1)]
            for left, right in zip(edges, edges[1:]):
                spans.append({"start_frame": left, "end_frame": right, "shots": 1, "split_inside_shot": True})
            continue
        if open_span is not None and end - open_span["start_frame"] <= limit:
            open_span["end_frame"] = end
            open_span["shots"] += 1
            continue
        if open_span is not None:
            spans.append(open_span)
        open_span = {"start_frame": start, "end_frame": end, "shots": 1, "split_inside_shot": False}
    if open_span is not None:
        spans.append(open_span)
    return spans


def probe_source(path: str | Path) -> dict[str, Any]:
    """Duration, size, fps, and audio from ffprobe."""
    text = subprocess.check_output(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration:stream=codec_type,width,height,r_frame_rate",
            "-of",
            "json",
            str(path),
        ],
        text=True,
    )
    data = json.loads(text)
    video = next((item for item in data.get("streams", []) if item.get("codec_type") == "video"), None)
    if video is None:
        raise RemakeError("元動画に映像が無い")
    num, _, den = str(video.get("r_frame_rate") or "0/1").partition("/")
    fps = float(num) / float(den or 1) if float(den or 1) else 0.0
    return {
        "path": str(path),
        "duration_s": round(float(data["format"]["duration"]), 3),
        "width": int(video["width"]),
        "height": int(video["height"]),
        "fps": round(fps, 3),
        "has_audio": any(item.get("codec_type") == "audio" for item in data.get("streams", [])),
    }


def scene_cuts(path: str | Path, threshold: float = SCENE_THRESHOLD) -> list[float]:
    """Raw scene-change seconds from ffmpeg. Merge them with ``merge_cuts`` before use."""
    proc = subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-i",
            str(path),
            "-filter:v",
            f"select='gte(scene,{threshold})',showinfo",
            "-fps_mode",
            "vfr",
            "-f",
            "null",
            "-",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return [round(float(match), 3) for match in PTS_RE.findall(proc.stderr) if float(match) > 0]


def skeleton_sheet(
    source: Mapping[str, Any],
    cuts: Sequence[float],
    *,
    cuts_from: str,
    max_span_s: float = DEFAULT_MAX_SPAN_S,
) -> dict[str, Any]:
    """Empty sheet. Roles, stills, and span text stay as 入力 until a human fills them."""
    shots = shot_frames(cuts, float(source["duration_s"]))
    spans = plan_spans(shots, max_span_s)
    return {
        "schema": SCHEMA,
        "source": dict(source),
        "cuts": list(cuts),
        "cuts_from": cuts_from,
        "max_span_s": float(max_span_s),
        "audio": "source" if source.get("has_audio") else "generated",
        "cast": {},
        "place_still": "",
        "props": {},
        "spans": [
            {
                "index": index,
                "start_s": round(span["start_frame"] / FPS, 3),
                "end_s": round(span["end_frame"] / FPS, 3),
                "shots": span["shots"],
                "split_inside_shot": span["split_inside_shot"],
                "cast": {},
                "place": False,
                "props": [],
                "description": SLOT,
                "soundscape": "",
                "music": "N/A",
            }
            for index, span in enumerate(spans, start=1)
        ],
    }


def _filled(value: Any) -> str:
    text = str(value or "").strip()
    return "" if text == SLOT else text


def _check_text(text: str, label: str) -> None:
    bare = DIALOGUE_RE.sub("", text)
    if CJK_RE.search(bare):
        raise RemakeError(f"{label} は英語。日本語は <d>[Japanese] …</d> の中だけ")


def _pictures(span: Mapping[str, Any], sheet: Mapping[str, Any], reasons: list[str]) -> list[dict[str, Any]]:
    index = int(span["index"])
    cast = sheet.get("cast") or {}
    props = sheet.get("props") or {}
    found: list[dict[str, Any]] = []
    roles = span.get("cast") or {}
    for role in sorted(roles, key=lambda item: int(str(item)[1:])):
        if not ROLE_RE.match(str(role)):
            raise RemakeError(f"役は S1、S2 の形: {role}")
        form = str(roles[role] or "default")
        stills = (cast.get(role) or {}).get("stills") or {}
        path = _filled(stills.get(form))
        if not path:
            reasons.append(f"範囲 {index} の {role}（{form}）に静止画が無い")
            continue
        found.append({"role": role, "form": form, "kind": "identity", "path": path})
    if span.get("place"):
        place = _filled(sheet.get("place_still"))
        if not place:
            reasons.append(f"範囲 {index} は場所の静止画を使うが、place_still が空")
        else:
            found.append({"role": "place", "form": "", "kind": "environment", "path": place})
    for prop in span.get("props") or []:
        if not PROP_RE.match(str(prop)):
            raise RemakeError(f"小道具は P1、P2 の形: {prop}")
        path = _filled((props.get(prop) or {}).get("still"))
        if not path:
            reasons.append(f"範囲 {index} の {prop} に静止画が無い")
            continue
        found.append({"role": prop, "form": "", "kind": "prop", "path": path})
    for number, item in enumerate(found, start=1):
        item["label"] = f"<Picture {number}>"
    return found


def _prompt(
    span: Mapping[str, Any],
    pictures: Sequence[Mapping[str, Any]],
    description: str,
    start_s: float,
    end_s: float,
) -> str:
    identity = [item for item in pictures if item["kind"] == "identity"]
    subject_of = {item["role"]: f"<Subject {number}>" for number, item in enumerate(identity, start=1)}
    definitions = []
    retention = []
    for item in pictures:
        if item["kind"] == "identity":
            definitions.append(
                f"{item['label']} is the only identity and costume reference for {subject_of[item['role']]}."
            )
            retention.append(f"{item['label']} (identity and costume): fully_preserved - face, hair, body, and costume.")
        elif item["kind"] == "environment":
            definitions.append(f"{item['label']} is the environment reference. It sets the location, set dressing, and light.")
            retention.append(f"{item['label']} (environment): fully_preserved - location and light.")
        else:
            definitions.append(f"{item['label']} is the reference for one prop.")
            retention.append(f"{item['label']} (prop): fully_preserved - shape, material, and color.")
    definitions.append(f"<Video 1> is the source span from {start_s:.3f} to {end_s:.3f} seconds. {VIDEO_ROLE}")
    retention.append(
        "<Video 1> (timing, blocking, and camera): partially_preserved - timing, positions, shot order, "
        "and camera are kept; the drawn rendering is not."
    )
    for item in identity:
        subject = subject_of[item["role"]]
        definitions.append(
            f"{subject} is the person whose identity and costume come only from {item['label']} "
            "and whose motion and position come from <Video 1>."
        )
        retention.append(
            f"{subject} (appears in [Shot 1]): attribute_transfer - the motion of <Video 1> is performed "
            f"by the live-action person in {item['label']}."
        )
    body = description if description.startswith("[Shot 1]") else f"[Shot 1] {description}"
    sound = _filled(span.get("soundscape")) or DEFAULT_SOUND
    music = _filled(span.get("music")) or "N/A"
    return "\n\n".join(
        [
            "subject_definitions:\n" + "\n".join(definitions),
            "summary:\n[reference generation] The target is a photorealistic live-action version of <Video 1>. "
            "Shot order, timing, and camera follow <Video 1>.",
            "retention_analysis:\n" + "\n".join(retention),
            f"detailed_description:\n{LIVE_ACTION_LOCK} {body}",
            f"overall_soundscape:\n{sound}",
            f"non_diegetic_music:\n{music}",
        ]
    ) + "\n"


def _check_labels(description: str, pictures: Sequence[Mapping[str, Any]], index: int, reasons: list[str]) -> None:
    subjects = sum(1 for item in pictures if item["kind"] == "identity")
    for number in PICTURE_RE.findall(description):
        if not 1 <= int(number) <= len(pictures):
            reasons.append(f"範囲 {index} の文に <Picture {number}> があるが、その静止画が無い")
    for number in SUBJECT_RE.findall(description):
        if not 1 <= int(number) <= subjects:
            reasons.append(f"範囲 {index} の文に <Subject {number}> があるが、その役が無い")
    for number in VIDEO_RE.findall(description):
        if number != "1":
            reasons.append(f"範囲 {index} の文に <Video {number}> がある。動画は <Video 1> だけ")
    if AUDIO_RE.search(description):
        reasons.append(f"範囲 {index} の文に <Audio> がある。音はつなぎで載せる")


def conform_argv(source: str, start_frame: int, end_frame: int, request_frames: int, size: tuple[int, int], out: str) -> list[str]:
    """One reference slice at 24fps on the H3 canvas, padded with its last frame to the request length."""
    width, height = size
    start = start_frame / FPS
    length = (end_frame - start_frame) / FPS
    pad = (request_frames - (end_frame - start_frame)) / FPS
    return [
        "ffmpeg",
        "-y",
        "-ss",
        f"{start:.3f}",
        "-i",
        source,
        "-t",
        f"{length:.3f}",
        "-vf",
        f"fps={FPS},scale={width}:{height}:force_original_aspect_ratio=increase,"
        f"crop={width}:{height},tpad=stop_mode=clone:stop_duration={pad:.3f}",
        "-frames:v",
        str(request_frames),
        "-an",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        out,
    ]


def join_argv(source: str, spans: Sequence[Mapping[str, Any]], audio: str, out: str = "remake.mp4") -> list[str]:
    """Trim each generated span to its measured frames and join them. Audio is the source or the clips."""
    if audio not in AUDIO_MODES:
        raise RemakeError(f"audio は {' か '.join(AUDIO_MODES)}")
    argv = ["ffmpeg", "-y"]
    for span in spans:
        argv.extend(["-i", str(span["output"])])
    parts = []
    labels = []
    for index, span in enumerate(spans):
        frames = int(span["frames"])
        parts.append(f"[{index}:v]trim=end_frame={frames},setpts=PTS-STARTPTS[v{index}]")
        labels.append(f"[v{index}]")
        if audio == "generated":
            parts.append(f"[{index}:a]atrim=end={frames / FPS:.6f},asetpts=PTS-STARTPTS[a{index}]")
            labels.append(f"[a{index}]")
    total = sum(int(span["frames"]) for span in spans)
    if audio == "generated":
        parts.append("".join(labels) + f"concat=n={len(spans)}:v=1:a=1[v][a]")
        argv.extend(["-filter_complex", ";".join(parts), "-map", "[v]", "-map", "[a]"])
    else:
        parts.append("".join(labels) + f"concat=n={len(spans)}:v=1:a=0[v]")
        argv.extend(["-t", f"{total / FPS:.6f}", "-i", source])
        argv.extend(["-filter_complex", ";".join(parts), "-map", "[v]", "-map", f"{len(spans)}:a:0"])
    argv.extend(["-r", str(FPS), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", out])
    return argv


def build_remake_plan(sheet: Mapping[str, Any], *, runtime: str = "comfy") -> dict[str, Any]:
    """Check the sheet and write one Ref2VA plan per span, plus the conform and join commands."""
    if runtime != "comfy":
        raise RemakeError("live_remake は Comfy だけ。複数の静止画と LoRA は公式 API では読めない")
    if sheet.get("schema") != SCHEMA:
        raise RemakeError(f"シートの schema が {SCHEMA} ではない")
    source = sheet.get("source") or {}
    for key in ("path", "duration_s", "width", "height", "fps"):
        if key not in source:
            raise RemakeError(f"source に {key} が無い")
    audio = str(sheet.get("audio") or "generated")
    if audio not in AUDIO_MODES:
        raise RemakeError(f"audio は {' か '.join(AUDIO_MODES)}")
    if audio == "source" and not source.get("has_audio"):
        raise RemakeError("元動画に音が無いので audio=source にできない")
    limit = _max_span_frames(float(sheet.get("max_span_s") or DEFAULT_MAX_SPAN_S))
    size = canvas_for(int(source["width"]), int(source["height"]))
    spans_in = list(sheet.get("spans") or [])
    if not spans_in:
        raise RemakeError("範囲が無い")
    reasons: list[str] = []
    planned: list[dict[str, Any]] = []
    expected = 0
    lora = {"key": "anime2real", "file": LORA_FILES["anime2real"], "strength": ANIME2REAL_STRENGTH}
    for span in spans_in:
        index = int(span["index"])
        start = frame_of(span["start_s"])
        end = frame_of(span["end_s"])
        if start != expected:
            raise RemakeError(f"範囲 {index} の始まりが前の範囲の終わりと合わない")
        if end - start > limit:
            raise RemakeError(f"範囲 {index} が {limit / FPS:.3f} 秒を超える")
        expected = end
        request = align_frames(end - start)
        pictures = _pictures(span, sheet, reasons)
        description = _filled(span.get("description"))
        if not description:
            reasons.append(f"範囲 {index} の文が無い。video-to-h3-prompt の出力から、その範囲の動きとカメラを貼る")
        else:
            _check_text(description, f"範囲 {index} の文")
            _check_labels(description, pictures, index, reasons)
        for key in ("soundscape", "music"):
            _check_text(_filled(span.get(key)), f"範囲 {index} の {key}")
        name = f"span-{index:02d}"
        prompt = _prompt(span, pictures, description, start / FPS, end / FPS) if description else ""
        planned.append(
            {
                "index": index,
                "start_s": round(start / FPS, 3),
                "end_s": round(end / FPS, 3),
                "frames": end - start,
                "request_frames": request,
                "request_s": round(request / FPS, 3),
                "split_inside_shot": bool(span.get("split_inside_shot")),
                "pictures": [{"label": item["label"], "role": item["role"], "form": item["form"], "path": item["path"]} for item in pictures],
                "reference_video": f"{name}-ref.mp4",
                "conform_argv": conform_argv(str(source["path"]), start, end, request, size, f"{name}-ref.mp4"),
                "output": f"{name}.mp4",
                "prompt": prompt,
                "loras": [lora],
            }
        )
    if expected != frame_of(source["duration_s"]):
        raise RemakeError("範囲の終わりが元動画の終わりと合わない")
    notes = [
        f"元は {source['width']}x{source['height']}、{source['fps']}fps、{source['duration_s']}秒。"
        f"出力は {size[0]}x{size[1]}、{FPS}fps。補間はしない。",
        "範囲ごとに Ref2VA を1本。参照の動画は最後のコマで要求の長さまで伸ばし、つなぎで測った長さに切る。",
        "静止画が顔と衣装、動画が秒と位置とカメラ。文は見た目を書かない。",
        WEIGHT_NOTE,
        GENERATE_MSG,
    ]
    if any(item["split_inside_shot"] for item in planned):
        notes.append("1つのショットの中で割った範囲がある。つなぎ目で動きが段になることがある。")
    if audio == "source":
        notes.append("音は元動画の音をそのまま載せる。")
    total = sum(item["frames"] for item in planned)
    return {
        "schema": "h3-studio/v1",
        "remake_schema": SCHEMA,
        "job": "live_remake",
        "task": "ref2va",
        "runtime": runtime,
        "high_mem": True,
        "turbo": False,
        "duration": round(total / FPS, 3),
        "fps": FPS,
        "width": size[0],
        "height": size[1],
        "resolution": RESOLUTION,
        "loras": [lora],
        "trigger": "",
        "sampler_id": "live_remake:anime2real",
        "look": "",
        "prompt": "",
        "inputs": {"video": str(source["path"])},
        "passes": [],
        "audio": audio,
        "spans": planned,
        "join_argv": join_argv(str(source["path"]), planned, audio),
        "status": "blocked" if reasons else "ready",
        "blocked": reasons,
        "notes": notes,
        "generate": False,
        "publish": False,
    }


def load_sheet(path: str | Path) -> dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise RemakeError("シートはオブジェクト")
    return data


def measure(video: str | Path, *, threshold: float = SCENE_THRESHOLD, min_shot_s: float = MIN_SHOT_S, max_span_s: float = DEFAULT_MAX_SPAN_S) -> dict[str, Any]:
    source = probe_source(video)
    raw = scene_cuts(video, threshold)
    cuts = merge_cuts(raw, source["duration_s"], min_shot_s)
    label = f"ffmpeg scene>{threshold:g}。{min_shot_s:g}秒より短いショットは前とまとめた。目で直してよい。"
    return skeleton_sheet(source, cuts, cuts_from=label, max_span_s=max_span_s)


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    usage = "usage: h3_live_remake.py measure <video> [out.json] | plan <sheet.json>"
    if len(args) < 2 or args[0] not in {"measure", "plan"}:
        print(usage, file=sys.stderr)
        return 2
    try:
        if args[0] == "measure":
            sheet = measure(args[1])
            text = json.dumps(sheet, ensure_ascii=False, indent=2) + "\n"
            if len(args) > 2:
                Path(args[2]).write_text(text, encoding="utf-8")
                print("WROTE", args[2])
            else:
                sys.stdout.write(text)
            print(f"範囲 {len(sheet['spans'])} 本。カット {len(sheet['cuts'])}。", file=sys.stderr)
            return 0
        plan = build_remake_plan(load_sheet(args[1]))
    except (RemakeError, subprocess.CalledProcessError, OSError, json.JSONDecodeError) as exc:
        print(f"REMAKE STOP: {exc}")
        return 1
    json.dump(plan, sys.stdout, ensure_ascii=False, indent=2)
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
