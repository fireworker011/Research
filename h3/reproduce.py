"""H3 prompt for reproducing one thrown video.

A local file is measured. Each span gets a Ref2VA prompt that binds that
measured span. Motion sentences are not invented. A bare link is refused
because the picture was not measured. This module does not queue Comfy and
does not post.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

from h3.live_remake import (
    FPS,
    LIGHTNING_FILE,
    LIGHTNING_STEPS,
    LIGHTNING_STRENGTH,
    MODEL_FILE,
    SCHEMA as REMAKE_SCHEMA,
    STEPS,
    RemakeError,
    _check_labels,
    _check_text,
    _filled,
    _pictures,
    align_frames,
    build_remake_plan,
    canvas_for,
    frame_of,
    load_sheet,
    measure,
)

SCHEMA = "h3-reproduce/v1"
VIDEO_EXT = {".mp4", ".mov", ".webm", ".mkv"}
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp"}
PLACE = "place"

# Filenames already registered on the studio and affi branches. This module
# does not load those branches. It only records whether reproduction uses them.
SPEED_FILE = "minimax_h3_fl2v_turbo_8step_v1.0_768p_comfyui_bf16.safetensors"
ACTION_FILE = "Motion_Repair_V2.safetensors"
COMBAT_FILE = "H3_Combat_V2.safetensors"
CHARSWAP_FILE = "h3_character_swap_pro4500_1000.safetensors"
ANIME2REAL_FILE = "Anime2Realsim__H3.safetensors"
CHAIN_FILE = "progressive_acceleration_slider_v1.0.safetensors"


class ReproduceError(Exception):
    """The thrown material cannot become one reproduction prompt."""


def lora_plan(*, lightning: bool) -> list[dict[str, Any]]:
    """Every known LoRA, with used true only for the one reproduction actually loads."""
    return [
        {
            "key": "none",
            "file": "",
            "strength": 0,
            "used": not lightning,
            "why": "完全再現は参照動画がタイミング、位置、カメラ、動きを持つ。LoRA は載せない。",
        },
        {
            "key": "lightning",
            "file": LIGHTNING_FILE,
            "strength": LIGHTNING_STRENGTH,
            "used": lightning,
            "why": (
                f"指定されたので steps {LIGHTNING_STEPS}、強さ {LIGHTNING_STRENGTH:g} で載せる。"
                if lightning
                else f"付けると steps が {STEPS} から {LIGHTNING_STEPS} になる。再現の必須ではない。"
            ),
        },
        {
            "key": "speed",
            "file": SPEED_FILE,
            "strength": 1.0,
            "used": False,
            "why": "FL2VA の Turbo。steps 9、video shift 6。Ref2VA の再現には載せない。",
        },
        {
            "key": "action",
            "file": ACTION_FILE,
            "strength": 0.6,
            "used": False,
            "why": "動き補修。参照動画がある再現には載せない。",
        },
        {
            "key": "combat",
            "file": COMBAT_FILE,
            "strength": 1.0,
            "used": False,
            "why": "格闘の別ジョブ。再現には載せない。",
        },
        {
            "key": "charswap",
            "file": CHARSWAP_FILE,
            "strength": 1.0,
            "used": False,
            "why": "全身差替の別ジョブ。人物静止画は公式 Ref2VA の参照として使い、この LoRA は載せない。",
        },
        {
            "key": "anime2real",
            "file": ANIME2REAL_FILE,
            "strength": 1.0,
            "used": False,
            "why": "実写寄せの別ジョブ。再現の絵を別の絵に寄せるので載せない。",
        },
        {
            "key": "chain",
            "file": CHAIN_FILE,
            "strength": 4.0,
            "used": False,
            "why": "百裂のオプトイン。再現には載せない。0未満は渡さない。",
        },
    ]


def _used_loras(lightning: bool) -> list[dict[str, Any]]:
    if not lightning:
        return []
    return [{"key": "lightning", "file": LIGHTNING_FILE, "strength": LIGHTNING_STRENGTH}]


def _base(video: str, *, lightning: bool, status: str, blocked: Sequence[str]) -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "job": "reproduce",
        "task": "ref2va",
        "runtime": "comfy",
        "status": status,
        "blocked": list(blocked),
        "video": video,
        "model_file": MODEL_FILE,
        "steps": LIGHTNING_STEPS if lightning else STEPS,
        "lightning": lightning,
        "loras": _used_loras(lightning),
        "lora_plan": lora_plan(lightning=lightning),
        "prompts": [],
        "generate": False,
        "publish": False,
        "queue": False,
    }


def _is_link(value: str) -> bool:
    text = value.strip()
    return "://" in text or text.startswith("www.")


def _lock_sentence(start_s: float, end_s: float, *, identity: bool) -> str:
    span = f"From {start_s:.3f} to {end_s:.3f} seconds the target follows <Video 1>."
    if identity:
        return (
            span
            + " Timing, positions, shot order, and camera come from <Video 1>."
            + " Identity and costume come only from the picture references."
        )
    return (
        span
        + " Rendering, timing, positions, shot order, and camera stay with <Video 1>."
        + " No shot, cut, or action is added."
    )


def _prompt_text(
    *,
    start_s: float,
    end_s: float,
    pictures: Sequence[Mapping[str, Any]],
    motion: str,
    sound: str,
    music: str,
) -> str:
    identity = [item for item in pictures if item["kind"] == "identity"]
    subject_of = {item["role"]: f"<Subject {number}>" for number, item in enumerate(identity, start=1)}
    definitions = [
        f"<Video 1> is the source span from {start_s:.3f} to {end_s:.3f} seconds."
    ]
    retention = []
    if identity:
        retention.append(
            "<Video 1> (timing, blocking, and camera): partially_preserved - "
            "timing, positions, shot order, and camera are kept."
        )
    else:
        definitions.append(
            "<Video 1> is also the picture reference. Rendering stays with <Video 1>."
        )
        retention.append(
            "<Video 1> (picture, timing, blocking, and camera): fully_preserved - "
            "rendering, timing, positions, shot order, and camera stay with <Video 1>."
        )
    for item in pictures:
        if item["kind"] == "identity":
            subject = subject_of[item["role"]]
            definitions.append(
                f"{item['label']} is the only identity and costume reference for {subject}."
            )
            definitions.append(
                f"{subject} takes identity and costume only from {item['label']} "
                "and takes motion and position from <Video 1>."
            )
            retention.append(
                f"{item['label']} (identity and costume): fully_preserved - face, hair, body, and costume."
            )
        elif item["kind"] == "environment":
            definitions.append(
                f"{item['label']} is the environment reference. It sets the location, set dressing, and light."
            )
            retention.append(f"{item['label']} (environment): fully_preserved - location and light.")
        else:
            definitions.append(f"{item['label']} is the reference for one prop.")
            retention.append(f"{item['label']} (prop): fully_preserved - shape, material, and color.")
    body = _lock_sentence(start_s, end_s, identity=bool(identity))
    if motion:
        body = f"{body} {motion}"
    return "\n\n".join(
        [
            "subject_definitions:\n" + "\n".join(definitions),
            "summary:\n[reference generation] Reproduce <Video 1> for this measured span. "
            "Do not add a shot, a cut, or an action that is not in <Video 1>.",
            "retention_analysis:\n" + "\n".join(retention),
            f"detailed_description:\n[Shot 1] {body}",
            f"overall_soundscape:\n{sound}",
            f"non_diegetic_music:\n{music}",
        ]
    ) + "\n"


def _sheet_from_video(
    video: Path,
    stills: Sequence[tuple[str, str]],
    motion: Sequence[str],
    *,
    soundscape: str,
    music: str,
) -> dict[str, Any]:
    sheet = measure(video)
    cast: dict[str, Any] = {}
    place = ""
    props: dict[str, Any] = {}
    span_cast: dict[str, str] = {}
    span_props: list[str] = []
    use_place = False
    for role, path in stills:
        if role == PLACE:
            if place:
                raise ReproduceError("place が二つある")
            place = path
            use_place = True
            continue
        if role.startswith("P"):
            if role in props:
                raise ReproduceError(f"{role} が二つある")
            props[role] = {"still": path}
            span_props.append(role)
            continue
        if role in cast:
            raise ReproduceError(f"{role} が二つある")
        cast[role] = {"stills": {"default": path}}
        span_cast[role] = "default"
    sheet["cast"] = cast
    sheet["place_still"] = place
    sheet["props"] = props
    if len(motion) > len(sheet["spans"]):
        raise ReproduceError("動きの文が範囲より多い")
    for index, span in enumerate(sheet["spans"]):
        span["cast"] = dict(span_cast)
        span["place"] = use_place
        span["props"] = list(span_props)
        span["description"] = motion[index] if index < len(motion) and motion[index].strip() else ""
        if soundscape:
            span["soundscape"] = soundscape
        if music:
            span["music"] = music
    return sheet


def _from_measured_sheet(sheet: Mapping[str, Any], *, lightning: bool, video: str) -> dict[str, Any]:
    source = sheet["source"]
    size = canvas_for(int(source["width"]), int(source["height"]))
    sound_default = (
        "The sound is the source audio of this span. No sound is added."
        if source.get("has_audio")
        else "No source audio is present. No sound is added."
    )
    music_default = "N/A"
    reasons: list[str] = []
    prompts = []
    for span in sheet["spans"]:
        pictures = _pictures(span, sheet, reasons)
        motion = _filled(span.get("description"))
        if motion:
            _check_text(motion, f"範囲 {span['index']} の文")
            _check_labels(motion, pictures, int(span["index"]), reasons)
        sound = _filled(span.get("soundscape")) or sound_default
        music = _filled(span.get("music")) or music_default
        _check_text(sound, f"範囲 {span['index']} の soundscape")
        _check_text(music, f"範囲 {span['index']} の music")
        start_s = float(span["start_s"])
        end_s = float(span["end_s"])
        frames = frame_of(end_s) - frame_of(start_s)
        text = ""
        if not reasons:
            text = _prompt_text(
                start_s=start_s,
                end_s=end_s,
                pictures=pictures,
                motion=motion,
                sound=sound,
                music=music,
            )
        prompts.append(
            {
                "index": span["index"],
                "start_s": start_s,
                "end_s": end_s,
                "frames": frames,
                "request_frames": align_frames(frames),
                "width": size[0],
                "height": size[1],
                "pictures": [
                    {"label": item["label"], "role": item["role"], "path": item["path"]}
                    for item in pictures
                ],
                "prompt": text,
            }
        )
    plan = _base(video, lightning=lightning, status="blocked" if reasons else "ready", blocked=reasons)
    plan["source"] = {
        "path": source.get("path"),
        "duration_s": source.get("duration_s"),
        "width": source.get("width"),
        "height": source.get("height"),
        "fps": source.get("fps"),
        "has_audio": source.get("has_audio"),
    }
    plan["canvas"] = {"width": size[0], "height": size[1], "fps": FPS}
    plan["cuts"] = list(sheet.get("cuts") or [])
    plan["prompts"] = prompts if not reasons else []
    plan["audio"] = "source" if source.get("has_audio") else "none"
    return plan


def build_reproduction(
    video: str,
    *,
    stills: Sequence[tuple[str, str]] = (),
    motion: Sequence[str] = (),
    lightning: bool = False,
    soundscape: str = "",
    music: str = "",
) -> dict[str, Any]:
    """One reproduction plan. Links and unread materials stay blocked."""
    if lightning not in (True, False):
        raise ReproduceError("lightning は true か false")
    text = str(video or "").strip()
    if not text:
        raise ReproduceError("動画が無い")
    if _is_link(text):
        plan = _base(
            text,
            lightning=lightning,
            status="blocked",
            blocked=["リンクだけでは映像を測れない。ファイルを置くと、尺とカットとプロンプトが出る。"],
        )
        return plan
    path = Path(text)
    if path.is_dir():
        return _from_directory(path, lightning=lightning)
    if not path.is_file():
        plan = _base(
            text,
            lightning=lightning,
            status="blocked",
            blocked=["ファイルが無い。測れる動画を1本置く。"],
        )
        return plan
    if path.suffix.lower() == ".json":
        if stills or motion or soundscape or music:
            raise ReproduceError("json と、別の静止画や動きの文は同時に渡さない")
        return _from_json(path, lightning=lightning)
    if path.suffix.lower() not in VIDEO_EXT:
        raise ReproduceError("動画は mp4、mov、webm、mkv。素材の役は json か --still で付ける")
    try:
        sheet = _sheet_from_video(path, stills, motion, soundscape=soundscape, music=music)
        return _from_measured_sheet(sheet, lightning=lightning, video=str(path))
    except RemakeError as exc:
        raise ReproduceError(str(exc)) from exc


def _from_directory(path: Path, *, lightning: bool) -> dict[str, Any]:
    videos = []
    images = []
    sheets = []
    for child in sorted(path.iterdir()):
        if not child.is_file():
            continue
        suffix = child.suffix.lower()
        if suffix in VIDEO_EXT:
            videos.append(child)
        elif suffix in IMAGE_EXT:
            images.append(child)
        elif suffix == ".json":
            sheets.append(child)
    if len(sheets) == 1 and not videos and not images:
        return _from_json(sheets[0], lightning=lightning)
    if len(videos) != 1:
        plan = _base(
            str(path),
            lightning=lightning,
            status="blocked",
            blocked=["動画は1本だけ置く。"],
        )
        return plan
    if images:
        names = "、".join(item.name for item in images)
        plan = _base(
            str(videos[0]),
            lightning=lightning,
            status="blocked",
            blocked=[f"静止画に役が無いのでプロンプトは出さない。S1 か place か P1 を付ける: {names}"],
        )
        return plan
    return build_reproduction(str(videos[0]), lightning=lightning)


def _from_json(path: Path, *, lightning: bool) -> dict[str, Any]:
    data = load_sheet(path)
    if data.get("schema") == REMAKE_SCHEMA:
        plan = build_remake_plan(data, lightning=lightning or bool(data.get("lightning")))
        plan["lora_plan"] = lora_plan(lightning=bool(plan.get("lightning")))
        plan["queue"] = False
        return plan
    if data.get("schema") != SCHEMA:
        raise ReproduceError(f"素材の schema が {SCHEMA} ではない")
    if lightning and data.get("lightning") is False:
        raise ReproduceError("lightning が衝突している")
    use_lightning = lightning or bool(data.get("lightning"))
    stills = []
    for item in data.get("stills") or []:
        if not isinstance(item, Mapping):
            raise ReproduceError("stills は role と path")
        role = str(item.get("role") or "").strip()
        still = str(item.get("path") or "").strip()
        if not role or not still:
            raise ReproduceError("stills は role と path")
        stills.append((role, still))
    motion_raw = data.get("motion") or []
    if isinstance(motion_raw, str):
        raise ReproduceError("motion は範囲ごとの配列")
    motion = [str(item) for item in motion_raw]
    video = str(data.get("video") or "").strip()
    return build_reproduction(
        video,
        stills=stills,
        motion=motion,
        lightning=use_lightning,
        soundscape=str(data.get("soundscape") or ""),
        music=str(data.get("music") or ""),
    )


def render_plan(plan: Mapping[str, Any]) -> str:
    """Japanese card plus the prompt text. The plan does not generate."""
    used = [item for item in plan.get("lora_plan") or [] if item.get("used")]
    used_line = "、".join(
        item["file"] or "なし" for item in used
    ) or "なし"
    lines = [
        "機能: 渡した動画の完全再現",
        f"状態: {plan.get('status')}",
        f"動画: {plan.get('video') or plan.get('inputs', {}).get('video', '')}",
        f"モデル: {plan.get('model_file') or plan.get('model', {}).get('file', '')} steps {plan.get('steps') or plan.get('model', {}).get('steps')}",
        f"載せる LoRA: {used_line}",
        "採否:",
    ]
    for item in plan.get("lora_plan") or []:
        if item.get("key") == "none":
            if item.get("used"):
                lines.append(f"- 載せる LoRA はない: {item.get('why')}")
            continue
        mark = "載せる" if item.get("used") else "載せない"
        lines.append(f"- {mark} {item.get('file')}: {item.get('why')}")
    for reason in plan.get("blocked") or []:
        lines.append(f"止まり: {reason}")
    prompts = plan.get("prompts")
    if prompts is None and plan.get("spans"):
        prompts = plan["spans"]
    for item in prompts or []:
        if not item.get("prompt"):
            continue
        lines.append(
            f"プロンプト {item.get('index')}: {float(item.get('start_s')):.3f}–{float(item.get('end_s')):.3f} 秒"
            f" 要求 {item.get('request_frames') or item.get('length')} フレーム"
        )
        lines.append(str(item["prompt"]).rstrip())
    lines.append("生成: しない")
    return "\n".join(lines) + "\n"


def _parse(argv: Sequence[str]) -> dict[str, Any]:
    video = ""
    stills: list[tuple[str, str]] = []
    motion: list[str] = []
    lightning = False
    index = 0
    args = list(argv)
    while index < len(args):
        item = args[index]
        if item == "--lightning":
            lightning = True
            index += 1
            continue
        if item == "--still":
            index += 1
            if index >= len(args) or "=" not in args[index]:
                raise ReproduceError("--still は S1=path の形")
            role, _, path = args[index].partition("=")
            stills.append((role.strip(), path.strip()))
            index += 1
            continue
        if item == "--motion":
            index += 1
            if index >= len(args):
                raise ReproduceError("--motion の文が無い")
            motion.append(args[index])
            index += 1
            continue
        if item.startswith("-"):
            raise ReproduceError("オプションが違う")
        if video:
            raise ReproduceError("動画は1本")
        video = item
        index += 1
    if not video:
        raise ReproduceError("動画ファイルか、素材の json を1つ渡す")
    return {"video": video, "stills": stills, "motion": motion, "lightning": lightning}


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if any(flag in args for flag in ("--generate", "--queue", "--publish")):
        print("REPRODUCE STOP: 生成と公開はこのコマンドでは走らない")
        return 1
    if not args or args[0] in {"-h", "--help"}:
        print(
            "usage: python -m h3.reproduce <video-or-materials.json> [--still S1=path] [--motion TEXT] [--lightning]",
            file=sys.stderr,
        )
        return 2
    try:
        parsed = _parse(args)
        plan = build_reproduction(
            parsed["video"],
            stills=parsed["stills"],
            motion=parsed["motion"],
            lightning=parsed["lightning"],
        )
    except (ReproduceError, RemakeError, OSError, json.JSONDecodeError) as exc:
        print(f"REPRODUCE STOP: {exc}")
        return 1
    if plan.get("generate") or plan.get("publish") or plan.get("queue"):
        print("REPRODUCE STOP: 計画が生成を要求している")
        return 1
    sys.stdout.write(render_plan(plan))
    return 0 if plan.get("status") != "blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main())
