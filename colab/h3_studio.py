#!/usr/bin/env python3
"""H3 Studio lane for affi shorts.

The ward episode engine is not imported and not modified.
Jobs are exclusive. This module writes a plan and a prompt. It does not
call Comfy and it does not call the official Hailuo API.

Prompt sections follow ``.cursor/skills/h3-prompt-writing`` only
(``references/base-en.txt`` for T2VA / FL2VA, ``references/ref-en.txt`` for Ref2VA).
Hub's other eight skills are not used.
"""

from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, Mapping

from h3_sfw import (
    ACTION_STRENGTH,
    ANIME2REAL_STRENGTH,
    CHARSWAP_STRENGTH,
    COMBAT_FIGHT_STRENGTH,
    COMBAT_FINISH_TRIGGER,
    COMBAT_STACK_STRENGTH,
    COMBAT_TRIGGER,
    FAST_SECONDS,
    FAST_STACK,
    I2VA_HEADER,
    JOIN_MIN_S,
    LORA_FILES,
    ONE_SHOT_15_NOTE,
    SPEED_STEPS,
    SPEED_STRENGTH,
    SPEED_VIDEO_SHIFT,
    TEMPLATES,
    fast_canvas,
    join_ffmpeg,
    parse_join_parts,
)

SCHEMA = "h3-studio/v1"

JOBS = (
    "fast_motion",
    "combat_motion",
    "swap_character",
    "swap_face",
    "swap_outfit",
    "real",
    "orbit360",
    "two_pass",
    "text_scene",
    "join",
    "affi_template",
)
SWAP_JOBS = frozenset({"swap_character", "swap_face", "swap_outfit"})
VIDEO_SINK_JOBS = frozenset({"swap_character", "swap_face", "swap_outfit", "real"})
# Community LoRAs. The official Hailuo API cannot load them.
API_STOP_JOBS = frozenset(
    {
        "fast_motion",
        "combat_motion",
        "swap_character",
        "swap_face",
        "swap_outfit",
        "real",
        "two_pass",
    }
)
HIGH_MEM_JOBS = frozenset(
    {"fast_motion", "combat_motion", "swap_character", "swap_face", "swap_outfit", "real"}
)
TURBO_OFF_JOBS = frozenset({"combat_motion", "swap_character", "swap_face", "swap_outfit"})

# Re-exported so plans and tests share one registry. No second combat file.
COMBAT_STRENGTH = COMBAT_FIGHT_STRENGTH
# Same-sampler overlay is refused. The strength below is the refused overlay's number.
SWAP_OVERLAY_STRENGTH = 0.5
LUMIREAL = "LumiReal"

DEFAULT_SECONDS = 5.0
MIN_SECONDS = 4.0
MAX_SECONDS = 5.0
FPS = 24
# Affi stock 768P 9:16 canvas (docs/affi-stock/stock.md, the 6s part).
WIDTH = 768
HEIGHT = 1344
RESOLUTION = "768P"
# The seven text scenes are official Hailuo T2VA at 6s, 16:9, 768P.
# 16:9 uses the same two edges as the stock 9:16 frame, swapped.
TEXT_SCENE_SECONDS = 6.0
TEXT_SCENE_WIDTH = HEIGHT
TEXT_SCENE_HEIGHT = WIDTH
TEXT_SCENE_ASPECT = "16:9"

STUDIO_HELPERS = (
    "colab/h3_sfw.py",
    "colab/h3_studio.py",
    "colab/h3_studio_colab_main.py",
)

JOB_HELP = {
    "fast_motion": "FL2VA。スピード LoRA 1.0 は常に載る。アクション 0.6 とコンバット 0.7 は任意。格闘トリガーは付けない。",
    "combat_motion": "FL2VA + combat 1.0。Turbo 切。High-Mem。finish で決め。スピードやアクションとは積まない。",
    "swap_character": "キャラ差し替え。Ref2VA + charswap 1.0。Video=動き、Picture=全身。Hero シート必須。",
    "swap_face": "同じ charswap。Picture は顔と髪だけ。服は Video。",
    "swap_outfit": "同じ charswap。Picture は服だけ。顔は Video。",
    "real": "anime2real 1.0。swap と同じサンプラーには積まない。",
    "orbit360": "FL2VA。同じ絵を首尾。LoRA ファイル名は未確定なので積まない。",
    "two_pass": "A の mp4 を B の Video 1。LoRA はパスごとに分ける。",
    "text_scene": "シーン。T2VA。LoRA なし。場所は Hero の place。空欄は書かない。",
    "join": "6秒と9秒を切って足す。15秒以上。1本の15秒生成はしない。",
    "affi_template": "バズ型の既存台本を指す。台本は書き換えない。生成しない。",
}

LOOK_KEYS = ("hair", "color", "race", "age", "height", "weight", "clothes", "place")
LOOK_LABELS = (
    ("hair", "hair"),
    ("color", "color"),
    ("race", "race"),
    ("age", "age"),
    ("height", "height"),
    ("weight", "weight"),
    ("clothes", "clothes"),
    ("place", "place"),
)

REQUEST_KEYS = frozenset(
    {
        "job",
        "runtime",
        "high_mem",
        "action",
        "dialogue",
        "hero",
        "enemy",
        "hero_sheet",
        "video",
        "first_still",
        "last_still",
        "finish",
        "duration",
        "turbo",
        "passes",
        "lumireal",
        "with_action",
        "with_combat",
        "template",
        "parts",
    }
)
REFUSED_NOW = {
    "weapon": "Weapon / GunFu / Continuity は今足さない",
    "gunfu": "Weapon / GunFu / Continuity は今足さない",
    "continuity": "Weapon / GunFu / Continuity は今足さない",
    "orbit_file": "orbit はファイル名確定後",
}

API_MSG = "runtime=api では Combat / Swap / real を止める。公式 Hailuo API はこの LoRA を読めない。本体は Comfy High-Mem。"
HIGH_MEM_MSG = "Combat / Swap / real は Comfy High-Mem。High-Mem がオフなら止める。"
OVERLAY_MSG = (
    "swap と real は同じサンプラーに積まない。two_pass に分ける。"
    f"重ねるときの charswap は {SWAP_OVERLAY_STRENGTH:g}、プロンプトに {LUMIREAL}。"
)
GENERATE_MSG = "生成は人間。このエントリはプランとプロンプトまで書く。Comfy の生成ボタンは押さない。"

NO_TEXT = "No on-screen text, subtitles, captions, logos, brand marks, or watermarks appear at any point."
SOUND = "overall_soundscape: Quiet room tone continues under soft cloth movement and footsteps."
MUSIC = "non_diegetic_music: N/A"
LOCK_FULL = "Picture 1 locks the full body. The motion follows Video 1."
LOCK_FACE = "Picture 1 locks the face and hair only. The clothes follow Video 1."
LOCK_OUTFIT = "Picture 1 locks the clothes only. The face follows Video 1."

# Seven T2VA shots. Action is one English line. Japanese stays inside 「」.
# Sound is physical only. The engine adds the three official fields.
TEXT_SCENES = (
    (
        "hana-gate",
        "Behind a 68-year-old Japanese woman, Hana, gray bun, mint-green shop apron, brown cross-body strap. She walks away through a night station ticket gate under cool fluorescent tubes. A staffer stands far ahead, head down. Camera follows at shoulder height. She keeps walking through the gate.",
        "A low electrical hum from cool fluorescent tubes sits over night-station room tone. Footsteps continue across the ticket-gate floor, and the gate latch clicks once.",
    ),
    (
        "host-live",
        "A 28-year-old man in a gray hoodie and glasses leans toward a ring light and a laptop, mouth open, saying 「よし…金曜だけどライブ、いける…」. Hana mops softly in the background. Camera stays on his profile.",
        "A laptop fan and a small ring-light buzz sit under quiet room tone. A mop moves softly across the floor behind him.",
    ),
    (
        "hana-cart",
        "Behind Hana as she pushes a steel hot-food cart through a narrow door into a cold prep aisle of steel shelves. Yellow gloves on the handle. Camera follows at her back.",
        "Steel cart wheels roll through a narrow door onto the hard prep-aisle floor. The door shifts, and a shelf gives a light metal tick as the cart passes.",
    ),
    (
        "hana-shelf",
        "Hana bends over the cart between blue-lit steel shelves, kettle and sample bento boxes on the top shelf. Camera stays behind her as she reaches to the shelf.",
        "The cart frame creaks once. A kettle shifts on the top shelf, and a sample box taps the steel.",
    ),
    (
        "host-drop",
        "The same host under red ceiling light, both hands in his hair, mouth wide, shouting 「ライブが落ちたあああ！」. Camera holds on his face and shoulders.",
        "Room tone continues under a low electrical hum. Both hands drag through his hair.",
    ),
    (
        "hana-box",
        "Hana stands in the red-lit aisle, one yellow glove holding a clear sample bento box, the other a white teacup. She looks down at the box. Camera at her chest.",
        "Quiet aisle tone. The clear plastic box and the ceramic cup tap once in her gloves.",
    ),
    (
        "hana-exit",
        "Hana walks toward the camera through open station glass doors at night, mint apron, yellow gloves, small smile. She stops and raises the sample bento box, saying 「ふう…温め直しゃ直るだろ。」",
        "Night air and an open glass door stay in the station entrance. Footsteps come across the floor and stop.",
    ),
)

FL2VA_HEADER = (
    "How the reference pictures align with the target video — "
    "Picture 1 (from Shot 1) aligns with the 0.00-second mark of the target video; "
    "Picture 2 (from Shot 1) aligns with the {end}-second mark of the target video."
)

CJK_RE = re.compile(r"[\u3040-\u30ff\u4e00-\u9fff\uff66-\uff9f]")
QUOTE_RE = re.compile(r"「([^」]*)」")
DIALOGUE_BLOCK_RE = re.compile(r"<d>\[Japanese\] .*?</d>")
LATIN_RE = re.compile(r"[A-Za-z]")
NON_JP_SPEECH_RE = re.compile(r"[A-Za-z\u0400-\u04FF\uac00-\ud7af\u3131-\u318e]")
BLOCK_RE = re.compile(
    r"youtube|youtu\.be|ユーチューブ|\bmarvel\b|マーベル|公式\s*[CＣ]M|オルビス|\borbis\b|\bfurbo\b|ファーボ",
    re.IGNORECASE,
)
UNDERAGE_WORD_RE = re.compile(
    r"(?i)\b(?:child|children|teen|teens|minor|minors|loli|shota)\b|子供|子ども|小学生|中学生|高校生|未成年|少年|少女"
)


class StudioError(Exception):
    """The plan stops before any GPU work."""


@dataclass(frozen=True)
class Sheet:
    hair: str = ""
    color: str = ""
    race: str = ""
    age: str = ""
    height: str = ""
    weight: str = ""
    clothes: str = ""
    place: str = ""


@dataclass(frozen=True)
class StudioRequest:
    job: str
    runtime: str = "comfy"
    high_mem: bool = True
    action: str = ""
    dialogue: str = ""
    hero: Sheet = field(default_factory=Sheet)
    enemy: Sheet = field(default_factory=Sheet)
    hero_sheet: str = ""
    video: str = ""
    first_still: str = ""
    last_still: str = ""
    finish: bool = False
    duration: float = DEFAULT_SECONDS
    turbo: bool = False
    passes: tuple[StudioRequest, ...] = ()
    lumireal: bool = False
    with_action: bool = False
    with_combat: bool = False
    template: str = ""
    parts: tuple[float, ...] = ()


def request_from(raw: Mapping[str, Any]) -> StudioRequest:
    """Build one request. Unknown keys and refused lanes stop."""
    if not isinstance(raw, Mapping):
        raise StudioError("入力はオブジェクト")
    refused = [key for key in REFUSED_NOW if key in raw]
    if refused:
        raise StudioError(REFUSED_NOW[sorted(refused)[0]])
    unknown = sorted(set(raw) - REQUEST_KEYS)
    if unknown:
        raise StudioError(f"項目が違う: {unknown}")
    job = str(raw.get("job") or "").strip()
    if job not in JOBS:
        raise StudioError(f"ジョブが違う: {job}")
    if raw.get("passes") and job != "two_pass":
        raise StudioError("passes は two_pass だけ")
    passes_raw = raw.get("passes") or []
    if not isinstance(passes_raw, (list, tuple)):
        raise StudioError("passes は配列")
    passes = tuple(request_from(item) for item in passes_raw)
    hero_raw = raw.get("hero") or {}
    enemy_raw = raw.get("enemy") or {}
    if not isinstance(hero_raw, Mapping) or not isinstance(enemy_raw, Mapping):
        raise StudioError("Hero / Enemy はオブジェクト")
    return StudioRequest(
        job=job,
        runtime=_runtime(raw.get("runtime", "comfy")),
        high_mem=_as_bool(raw.get("high_mem", True), default=True),
        action=str(raw.get("action") or "").strip(),
        dialogue=str(raw.get("dialogue") or "").strip(),
        hero=_sheet(hero_raw),
        enemy=_sheet(enemy_raw),
        hero_sheet=str(raw.get("hero_sheet") or "").strip(),
        video=str(raw.get("video") or "").strip(),
        first_still=str(raw.get("first_still") or "").strip(),
        last_still=str(raw.get("last_still") or "").strip(),
        finish=_as_bool(raw.get("finish", False), default=False),
        duration=_duration_for(job, raw.get("duration", None if job in {"fast_motion", "join", "affi_template"} else DEFAULT_SECONDS)),
        turbo=_as_bool(raw.get("turbo", False), default=False),
        passes=passes,
        lumireal=_as_bool(raw.get("lumireal", False), default=False),
        with_action=_as_bool(raw.get("with_action", False), default=False),
        with_combat=_as_bool(raw.get("with_combat", False), default=False),
        template=str(raw.get("template") or "").strip(),
        parts=_parts_for(job, raw.get("parts")),
    )


def request_from_env(environ: Mapping[str, str] | None = None) -> StudioRequest:
    """Colab form environment. ``H3_STUDIO_JSON`` wins when it is set."""
    env = os.environ if environ is None else environ
    blob = str(env.get("H3_STUDIO_JSON") or "").strip()
    if blob:
        if blob.startswith("{"):
            data = json.loads(blob)
        else:
            data = json.loads(Path(blob).read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise StudioError("入力はオブジェクト")
        return request_from(data)
    job = str(env.get("H3_STUDIO_JOB") or "text_scene").strip()
    mapping: dict[str, Any] = {
        "job": job,
        "runtime": env.get("H3_STUDIO_RUNTIME") or "comfy",
        "high_mem": env.get("H3_STUDIO_HIGH_MEM", "1"),
        "action": env.get("H3_STUDIO_ACTION") or "",
        "dialogue": env.get("H3_STUDIO_DIALOGUE") or "",
        "hero": _sheet_env(env, "HERO"),
        "enemy": _sheet_env(env, "ENEMY"),
        "hero_sheet": env.get("H3_STUDIO_HERO_SHEET") or "",
        "video": env.get("H3_STUDIO_VIDEO") or "",
        "first_still": env.get("H3_STUDIO_FIRST") or "",
        "last_still": env.get("H3_STUDIO_LAST") or "",
        "finish": env.get("H3_STUDIO_FINISH", "0"),
        "duration": (
            env.get("H3_STUDIO_FAST_SECONDS") or "6"
            if job == "fast_motion"
            else env.get("H3_STUDIO_DURATION") or DEFAULT_SECONDS
        ),
        "turbo": env.get("H3_STUDIO_TURBO", "0"),
        "with_action": env.get("H3_STUDIO_WITH_ACTION", "0"),
        "with_combat": env.get("H3_STUDIO_WITH_COMBAT", "0"),
        "template": env.get("H3_STUDIO_TEMPLATE") or "",
    }
    if job == "join":
        mapping["parts"] = env.get("H3_STUDIO_PARTS") or ""
    if job == "two_pass":
        pass_a = str(env.get("H3_STUDIO_PASS_A") or "").strip()
        pass_b = str(env.get("H3_STUDIO_PASS_B") or "").strip()
        if not pass_a or not pass_b:
            raise StudioError("two_pass は A と B")
        shared = {key: value for key, value in mapping.items() if key != "job"}
        mapping["passes"] = [{**shared, "job": pass_a}, {**shared, "job": pass_b}]
    return request_from(mapping)


def build_plan(req: StudioRequest) -> dict[str, Any]:
    """One exclusive job. ``two_pass`` is two sequential plans, not one sampler."""
    _scan_request(req)
    _gate(req)
    if req.job == "two_pass":
        return _build_two_pass(req)
    if req.job == "combat_motion":
        return _build_combat(req)
    if req.job == "swap_character":
        return _build_swap(req, LOCK_FULL, "full body")
    if req.job == "swap_face":
        return _build_swap(req, LOCK_FACE, "face and hair")
    if req.job == "swap_outfit":
        return _build_swap(req, LOCK_OUTFIT, "clothes")
    if req.job == "real":
        return _build_real(req)
    if req.job == "orbit360":
        return _build_orbit(req)
    if req.job == "text_scene":
        return _build_text(req)
    if req.job == "fast_motion":
        return _build_fast(req)
    if req.job == "join":
        return _build_join(req)
    if req.job == "affi_template":
        return _build_template(req)
    raise StudioError(f"ジョブが違う: {req.job}")


def assert_loras_exclusive(keys: set[str]) -> None:
    """charswap and anime2real stay alone. Combat may sit with speed and action only."""
    if "charswap" in keys and "anime2real" in keys:
        raise StudioError(OVERLAY_MSG)
    if "charswap" in keys and keys - {"charswap"}:
        raise StudioError("charswap は同じサンプラーに他の LoRA を積まない")
    if "anime2real" in keys and keys - {"anime2real"}:
        raise StudioError("anime2real は同じサンプラーに他の LoRA を積まない")
    if "combat" in keys and not keys <= FAST_STACK:
        raise StudioError("Combat は speed と action 以外とは同じサンプラーに積まない")


def prompts_of(plan: Mapping[str, Any]) -> list[str]:
    """Prompt strings in pass order. ``two_pass`` has one prompt per pass."""
    if plan.get("job") == "two_pass":
        found: list[str] = []
        for child in plan.get("passes") or []:
            found.extend(prompts_of(child))
        return found
    text = str(plan.get("prompt") or "")
    return [text] if text else []


def _build_fast(req: StudioRequest) -> dict[str, Any]:
    if not req.first_still:
        raise StudioError("fast_motion は最初の絵が要る")
    if req.last_still:
        raise StudioError("fast_motion は最初の絵だけ。最後の絵は combat_motion")
    action, dialogue = _speech(req)
    look = _look_clause(req.hero, req.enemy)
    body = _sentences(
        NO_TEXT,
        look,
        "The shot begins in the composition of <Picture 1>.",
        action,
        dialogue,
        "The camera pushes in with small amplitude at slow speed.",
    )
    loras: list[dict[str, Any]] = [_lora("speed", SPEED_STRENGTH)]
    if req.with_combat:
        loras.append(_lora("combat", COMBAT_STACK_STRENGTH))
    if req.with_action:
        loras.append(_lora("action", ACTION_STRENGTH))
    notes = [
        f"steps {SPEED_STEPS}。video shift {SPEED_VIDEO_SHIFT:g}。スピード LoRA が Turbo。",
        "格闘の prfight2 は付けない。決めは combat_motion。",
    ]
    if req.with_action or req.with_combat:
        notes.append("アクションとコンバットはスピードの上に足す。charswap とは混ぜない。")
    built = _leaf(
        req,
        task="fl2va",
        prompt=_i2va_prompt(body=body),
        loras=tuple(loras),
        trigger="",
        turbo=True,
        notes=notes,
        inputs={
            "first_still": req.first_still,
            "last_still": "",
            "hero_sheet": req.hero_sheet,
            "video": "",
        },
    )
    width, height, frames = fast_canvas(req.duration)
    built["width"] = width
    built["height"] = height
    built["frames"] = frames
    built["steps"] = SPEED_STEPS
    built["video_shift"] = SPEED_VIDEO_SHIFT
    return built


def _build_join(req: StudioRequest) -> dict[str, Any]:
    parts = req.parts
    total = float(sum(parts))
    return {
        "schema": SCHEMA,
        "job": "join",
        "task": "join",
        "runtime": req.runtime,
        "high_mem": False,
        "turbo": False,
        "duration": total,
        "fps": FPS,
        "width": 1080,
        "height": 1920,
        "resolution": "1080P",
        "loras": [],
        "trigger": "",
        "sampler_id": "join:ffmpeg",
        "look": "",
        "prompt": "",
        "inputs": {},
        "passes": [{"seconds": seconds} for seconds in parts],
        "notes": [ONE_SHOT_15_NOTE, "ffmpeg はここでは実行しない。"],
        "generate": False,
        "ffmpeg": join_ffmpeg(parts),
    }


def _build_template(req: StudioRequest) -> dict[str, Any]:
    key = req.template or "buy_before"
    if key not in TEMPLATES:
        raise StudioError("テンプレが違う")
    item = TEMPLATES[key]
    return {
        "schema": SCHEMA,
        "job": "affi_template",
        "task": "affi",
        "runtime": req.runtime,
        "high_mem": False,
        "turbo": False,
        "duration": JOIN_MIN_S,
        "fps": FPS,
        "width": WIDTH,
        "height": HEIGHT,
        "resolution": RESOLUTION,
        "loras": [],
        "trigger": "",
        "sampler_id": "affi:template",
        "look": "",
        "prompt": "",
        "inputs": {},
        "passes": [],
        "notes": [
            str(item["label"]),
            "台本は fixtures の既存。ここでは書き換えない。",
            "採点は python -m minimaxh3.affi plan。生成と投稿はしない。",
        ],
        "generate": False,
        "template": key,
        "pattern_id": item["pattern_id"],
        "script": item["script"],
    }


def _build_combat(req: StudioRequest) -> dict[str, Any]:
    if not req.first_still or not req.last_still:
        raise StudioError("combat_motion は FL2VA。最初の絵と最後の絵が要る")
    action, dialogue = _speech(req)
    look = _look_clause(req.hero, req.enemy)
    trigger = COMBAT_FINISH_TRIGGER if req.finish else COMBAT_TRIGGER
    end = f"{req.duration:.2f}"
    body = _sentences(
        NO_TEXT,
        look,
        "The shot begins in the composition of Picture 1.",
        action,
        dialogue,
        (
            "The camera tracks the motion with small amplitude at fast speed and reaches "
            f"the composition of Picture 2 at the {end}-second mark."
        ),
    )
    prompt = _fl2va_prompt(trigger=trigger, end=end, body=body)
    notes: list[str] = []
    turbo = req.turbo
    if turbo:
        notes.append("Swap と Combat は Turbo を切る")
        turbo = False
    return _leaf(
        req,
        task="fl2va",
        prompt=prompt,
        loras=(_lora("combat", COMBAT_STRENGTH),),
        trigger=trigger,
        turbo=turbo,
        notes=notes,
        inputs={
            "first_still": req.first_still,
            "last_still": req.last_still,
            "hero_sheet": req.hero_sheet,
            "video": "",
        },
    )


def _build_swap(req: StudioRequest, lock: str, picture_role: str) -> dict[str, Any]:
    if not req.hero_sheet:
        raise StudioError("swap 時 Hero シート必須")
    if not req.video:
        raise StudioError("swap は Video が動き。Video が無い")
    action, dialogue = _speech(req)
    look = _look_clause(req.hero, req.enemy)
    if picture_role == "full body":
        subject = (
            "<Subject 1> is the person in <Picture 1>. The full body, face, hair, and clothes "
            "come from <Picture 1>. The motion comes from <Video 1>."
        )
        picture = "<Picture 1> is the full-body appearance sheet for <Subject 1>."
        video = "<Video 1> is the motion source. Appearance stays with <Picture 1>."
        retention = "\n".join(
            (
                "<Subject 1> (appears in [Shot 1]): fully_preserved - the full body comes from <Picture 1> and the motion comes from <Video 1>.",
                "<Picture 1> (full-body sheet): fully_preserved - face, hair, clothes, and body stay with <Picture 1>.",
                "<Video 1> (motion): fully_preserved - the motion follows <Video 1>.",
            )
        )
    elif picture_role == "face and hair":
        subject = (
            "<Subject 1> is the person whose face and hair come from <Picture 1> "
            "and whose clothes and motion come from <Video 1>."
        )
        picture = "<Picture 1> is the face and hair sheet. It does not replace the clothes."
        video = "<Video 1> is the motion source. The clothes stay with <Video 1>."
        retention = "\n".join(
            (
                "<Subject 1> (appears in [Shot 1]): partially_preserved - face and hair come from <Picture 1>; clothes and motion stay with <Video 1>.",
                "<Picture 1> (face and hair): fully_preserved - only the face and hair are taken from <Picture 1>.",
                "<Video 1> (motion and clothes): fully_preserved - motion and clothes follow <Video 1>.",
            )
        )
    elif picture_role == "clothes":
        subject = (
            "<Subject 1> is the person whose clothes come from <Picture 1> "
            "and whose face and motion come from <Video 1>."
        )
        picture = "<Picture 1> is the clothes sheet. It does not replace the face."
        video = "<Video 1> is the motion source. The face stays with <Video 1>."
        retention = "\n".join(
            (
                "<Subject 1> (appears in [Shot 1]): partially_preserved - clothes come from <Picture 1>; the face and motion stay with <Video 1>.",
                "<Picture 1> (clothes): fully_preserved - only the clothes are taken from <Picture 1>.",
                "<Video 1> (motion and face): fully_preserved - motion and the face follow <Video 1>.",
            )
        )
    else:
        raise StudioError(f"swap のロックが違う: {picture_role}")
    summary = (
        "[reference generation] "
        f"<Subject 1> keeps the roles above. {action}"
    )
    detail = _sentences(
        "[Shot 1] Live-action, vertical 9:16.",
        NO_TEXT,
        look,
        lock,
        action,
        dialogue,
        "The camera follows the motion of <Video 1> with small amplitude at slow speed.",
    )
    prompt = _ref_prompt(
        definitions="\n".join((subject, picture, video)),
        summary=summary,
        retention=retention,
        detail=detail,
        lumireal=False,
    )
    notes: list[str] = []
    turbo = req.turbo
    if turbo:
        notes.append("Swap と Combat は Turbo を切る")
        turbo = False
    return _leaf(
        req,
        task="ref2va",
        prompt=prompt,
        loras=(_lora("charswap", CHARSWAP_STRENGTH),),
        trigger="",
        turbo=turbo,
        notes=notes,
        inputs={
            "hero_sheet": req.hero_sheet,
            "video": req.video,
            "first_still": "",
            "last_still": "",
        },
    )


def _build_real(req: StudioRequest) -> dict[str, Any]:
    picture = _one_picture(req.hero_sheet, req.first_still, "real の絵は1枚")
    if not picture and not req.video:
        raise StudioError("real は絵か Video が要る")
    if req.video and not picture:
        raise StudioError("real の Ref2VA は Picture が要る")
    action, dialogue = _speech(req)
    look = _look_clause(req.hero, req.enemy)
    if req.video:
        prompt = _ref_prompt(
            definitions="\n".join(
                (
                    "<Subject 1> is the person in <Picture 1>.",
                    "<Picture 1> is the appearance frame for <Subject 1>.",
                    "<Video 1> is the motion source.",
                )
            ),
            summary=f"[reference generation] <Subject 1> keeps the appearance of <Picture 1> and the motion of <Video 1>. {action}",
            retention="\n".join(
                (
                    "<Subject 1> (appears in [Shot 1]): fully_preserved - appearance comes from <Picture 1> and motion comes from <Video 1>.",
                    "<Picture 1> (appearance): fully_preserved - the appearance frame stays <Picture 1>.",
                    "<Video 1> (motion): fully_preserved - the motion follows <Video 1>.",
                )
            ),
            detail=_sentences(
                "[Shot 1] Live-action, vertical 9:16.",
                NO_TEXT,
                look,
                "Picture 1 locks the full appearance. The motion follows Video 1.",
                action,
                dialogue,
                "The camera follows the motion of <Video 1> with small amplitude at slow speed.",
            ),
            lumireal=req.lumireal,
        )
        task = "ref2va"
        inputs = {"hero_sheet": picture, "video": req.video, "first_still": picture, "last_still": ""}
    else:
        end = f"{req.duration:.2f}"
        prompt = _fl2va_prompt(
            trigger=LUMIREAL if req.lumireal else "",
            end=end,
            body=_sentences(
                NO_TEXT,
                look,
                "Picture 1 and Picture 2 are the same appearance frame.",
                action,
                dialogue,
                "The camera holds a static shot inside that framing.",
            ),
        )
        task = "fl2va"
        inputs = {"hero_sheet": picture, "video": "", "first_still": picture, "last_still": picture}
    return _leaf(
        req,
        task=task,
        prompt=prompt,
        loras=(_lora("anime2real", ANIME2REAL_STRENGTH),),
        trigger="",
        turbo=req.turbo,
        notes=[],
        inputs=inputs,
    )


def _build_orbit(req: StudioRequest) -> dict[str, Any]:
    picture = _one_picture(req.first_still, req.hero_sheet, "orbit360 は同じ絵を首尾")
    if not picture:
        raise StudioError("orbit360 は同じ絵を首尾に置く。絵が無い")
    if req.last_still and req.last_still != picture:
        raise StudioError("orbit360 は同じ絵を首尾")
    action, dialogue = _speech(req)
    look = _look_clause(req.hero, req.enemy)
    end = f"{req.duration:.2f}"
    prompt = _fl2va_prompt(
        trigger="",
        end=end,
        body=_sentences(
            NO_TEXT,
            look,
            "Picture 1 and Picture 2 are the same picture.",
            action,
            dialogue,
            "The subject turns through one full orbit and returns to the opening pose and framing.",
            "The camera arcs around the subject with small amplitude at slow speed.",
        ),
    )
    return _leaf(
        req,
        task="fl2va",
        prompt=prompt,
        loras=(),
        trigger="",
        turbo=req.turbo,
        notes=["orbit の LoRA ファイル名は未確定。他のジョブの LoRA は積まない。"],
        inputs={"first_still": picture, "last_still": picture, "hero_sheet": req.hero_sheet, "video": ""},
    )


def _build_text(
    req: StudioRequest,
    *,
    framing: str = "vertical 9:16",
    sound: str | None = None,
    onscreen: bool = False,
) -> dict[str, Any]:
    action, dialogue = _speech(req, onscreen=onscreen)
    look = _look_clause(req.hero, req.enemy)
    camera = "" if "camera" in action.lower() else "The camera holds a static shot."
    body = _sentences(
        f"[Shot 1] Live-action, {framing}.",
        NO_TEXT,
        look,
        action,
        dialogue,
        camera,
    )
    sound_line = SOUND if sound is None else f"overall_soundscape: {sound}"
    prompt = "\n\n".join(
        (
            f"integrated_multimodal_description: {body}",
            sound_line,
            MUSIC,
        )
    ) + "\n"
    return _leaf(
        req,
        task="t2va",
        prompt=prompt,
        loras=(),
        trigger="",
        turbo=req.turbo,
        notes=["text_scene は LoRA なし。"],
        inputs={"hero_sheet": "", "video": "", "first_still": "", "last_still": ""},
    )


def build_text_scenes() -> dict[str, Any]:
    """Seven official Hailuo T2VA shots. No LoRA, no stills, no generate call."""
    clips = []
    for scene_id, action, sound in TEXT_SCENES:
        req = StudioRequest(
            job="text_scene",
            runtime="api",
            high_mem=False,
            action=action,
            duration=TEXT_SCENE_SECONDS,
            turbo=False,
        )
        _scan_request(req)
        _gate(req)
        clip = _build_text(req, framing=f"horizontal {TEXT_SCENE_ASPECT}", sound=sound, onscreen=True)
        clip["scene_id"] = scene_id
        clip["width"] = TEXT_SCENE_WIDTH
        clip["height"] = TEXT_SCENE_HEIGHT
        clip["aspect"] = TEXT_SCENE_ASPECT
        clip["shots"] = 1
        clip["output_mp4"] = f"{scene_id}.mp4"
        clip["notes"] = [
            "公式 Hailuo の T2VA。LoRA なし。Combat も charswap も切る。",
            "顔固定は後段の Ref2VA。この本には載せない。",
            "1本1ショット。",
        ]
        clips.append(clip)
    return {
        "schema": SCHEMA,
        "job": "text_scene",
        "batch": "text_scene_x7",
        "runtime": "api",
        "task": "t2va",
        "duration": TEXT_SCENE_SECONDS,
        "fps": FPS,
        "width": TEXT_SCENE_WIDTH,
        "height": TEXT_SCENE_HEIGHT,
        "aspect": TEXT_SCENE_ASPECT,
        "resolution": RESOLUTION,
        "loras": [],
        "turbo": False,
        "clips": clips,
        "poster": {"kind": "still", "video": False},
        "face_lock": "later_ref2va",
        "generate": False,
        "notes": [
            "7本とも公式 Hailuo の T2VA。Combat と charswap は切る。",
            "ポスターは静止画。このバッチの動画にはしない。",
            "顔固定は後段の Ref2VA。この7本には載せない。",
            GENERATE_MSG,
        ],
    }


def _build_two_pass(req: StudioRequest) -> dict[str, Any]:
    if len(req.passes) != 2:
        raise StudioError("two_pass は A と B の2本")
    left, right = req.passes
    if left.job == "two_pass" or right.job == "two_pass":
        raise StudioError("two_pass は入れ子にしない")
    if right.job not in VIDEO_SINK_JOBS:
        raise StudioError("two_pass の B は Video 1 を取るジョブ（swap か real）")
    plan_a = build_plan(replace(left, runtime=req.runtime, high_mem=req.high_mem))
    lumireal = left.job in SWAP_JOBS and right.job == "real"
    plan_b = build_plan(
        replace(
            right,
            runtime=req.runtime,
            high_mem=req.high_mem,
            video="{pass-a.mp4}",
            lumireal=lumireal,
        )
    )
    assert_loras_exclusive({item["key"] for item in plan_a["loras"]})
    assert_loras_exclusive({item["key"] for item in plan_b["loras"]})
    notes = ["B の Video 1 は A の mp4。同じサンプラーに両方の LoRA は積まない。"]
    if lumireal:
        notes.append(
            "swap のあと real に分ける。A の charswap は 1.0。B は anime2real 1.0。"
            f"同じサンプラーに重ねる場合の charswap {SWAP_OVERLAY_STRENGTH:g} は使わない。"
            f"B のプロンプトに {LUMIREAL} を書く。"
        )
    plan_a = {**plan_a, "pass_id": "A", "output_mp4": "pass-a.mp4"}
    plan_b = {**plan_b, "pass_id": "B"}
    return {
        "schema": SCHEMA,
        "job": "two_pass",
        "task": "two_pass",
        "runtime": req.runtime,
        "high_mem": req.high_mem,
        "turbo": False,
        "duration": req.duration,
        "fps": FPS,
        "width": WIDTH,
        "height": HEIGHT,
        "resolution": RESOLUTION,
        "loras": [],
        "trigger": "",
        "sampler_id": "two_pass:split",
        "look": "",
        "prompt": "",
        "inputs": {"video": "{pass-a.mp4}"},
        "passes": [plan_a, plan_b],
        "link": {"from": "pass-a.mp4", "to": "passes[1].inputs.video", "label": "Video 1"},
        "notes": notes,
        "generate": False,
    }


def _leaf(
    req: StudioRequest,
    *,
    task: str,
    prompt: str,
    loras: tuple[dict[str, Any], ...],
    trigger: str,
    turbo: bool,
    notes: list[str],
    inputs: dict[str, str],
) -> dict[str, Any]:
    keys = {item["key"] for item in loras}
    assert_loras_exclusive(keys)
    _assert_prompt(prompt)
    look = _look_clause(req.hero, req.enemy)
    sampler = f"{req.job}:" + ("+".join(item["key"] for item in loras) if loras else "none")
    return {
        "schema": SCHEMA,
        "job": req.job,
        "task": task,
        "runtime": req.runtime,
        "high_mem": req.high_mem,
        "turbo": turbo,
        "duration": req.duration,
        "fps": FPS,
        "width": WIDTH,
        "height": HEIGHT,
        "resolution": RESOLUTION,
        "loras": list(loras),
        "trigger": trigger,
        "sampler_id": sampler,
        "look": look,
        "prompt": prompt,
        "inputs": inputs,
        "passes": [],
        "notes": notes,
        "generate": False,
    }


def _i2va_prompt(*, body: str) -> str:
    chunks = [
        I2VA_HEADER,
        f"integrated_multimodal_description: [Shot 1] Live-action, vertical 9:16. {body}",
        SOUND,
        MUSIC,
    ]
    return "\n\n".join(chunks) + "\n"


def _fl2va_prompt(*, trigger: str, end: str, body: str) -> str:
    chunks = []
    if trigger:
        chunks.append(trigger)
    chunks.append(FL2VA_HEADER.format(end=end))
    chunks.append(f"integrated_multimodal_description: [Shot 1] Live-action, vertical 9:16. {body}")
    chunks.append(SOUND)
    chunks.append(MUSIC)
    return "\n\n".join(chunks) + "\n"


def _ref_prompt(*, definitions: str, summary: str, retention: str, detail: str, lumireal: bool) -> str:
    chunks = []
    if lumireal:
        chunks.append(LUMIREAL)
    chunks.extend(
        (
            "subject_definitions:\n" + definitions.strip(),
            "summary:\n" + summary.strip(),
            "retention_analysis:\n" + retention.strip(),
            "detailed_description: " + detail.strip(),
            SOUND,
            MUSIC,
        )
    )
    return "\n\n".join(chunks) + "\n"


def _lora(key: str, strength: float) -> dict[str, Any]:
    if key not in LORA_FILES:
        raise StudioError(f"LoRA が未登録: {key}")
    return {"key": key, "file": LORA_FILES[key], "strength": strength}


def _gate(req: StudioRequest) -> None:
    if req.runtime == "api" and req.job in API_STOP_JOBS:
        raise StudioError(API_MSG)
    if req.job in HIGH_MEM_JOBS and not req.high_mem:
        raise StudioError(HIGH_MEM_MSG)


def _scan_request(req: StudioRequest) -> None:
    blobs = [req.action, req.dialogue, req.hero_sheet, req.video, req.first_still, req.last_still, req.job]
    for sheet in (req.hero, req.enemy):
        for key in LOOK_KEYS:
            blobs.append(getattr(sheet, key))
    for blob in blobs:
        _scan_blocked(blob)
    for sheet in (req.hero, req.enemy):
        for key in LOOK_KEYS:
            if key != "age":
                _reject_cjk(getattr(sheet, key), "Look")
        _check_age(sheet.age)
    bare_action = _outside_quotes(req.action)
    if req.action.strip():
        if "\n" in req.action or "\r" in req.action or not LATIN_RE.search(bare_action):
            raise StudioError("action は英語1本")
        _reject_cjk(bare_action, "action")
    for child in req.passes:
        _scan_request(child)


def _speech(req: StudioRequest, *, onscreen: bool = False) -> tuple[str, str]:
    action, line = _take_dialogue(req.action, req.dialogue)
    _scan_blocked(action)
    _scan_blocked(line)
    if not line:
        return action, ""
    tag = f"<d>[Japanese] {line}</d>"
    if onscreen and "「" in req.action:
        return QUOTE_RE.sub(f"(S1): {tag}", req.action.strip(), count=1), ""
    if onscreen:
        return f"{action} (S1) says: {tag}", ""
    spoken = (
        "An adult voice (S1) says in an off-screen voiceover: "
        f"{tag} while the on-screen lips remain completely closed."
    )
    return action, spoken


def _take_dialogue(action: str, dialogue: str) -> tuple[str, str]:
    text = action.strip()
    if "\n" in text or "\r" in text:
        raise StudioError("action は英語1本")
    quotes = QUOTE_RE.findall(text)
    if len(quotes) > 1:
        raise StudioError("日本語は「」1つ")
    quoted = ""
    if quotes:
        quoted = quotes[0].strip()
        if not quoted:
            raise StudioError("「」が空")
        text = QUOTE_RE.sub(" ", text).strip()
        text = re.sub(r"\s{2,}", " ", text)
    field_line = dialogue.strip()
    if field_line.startswith("「") and field_line.endswith("」") and len(field_line) >= 2:
        field_line = field_line[1:-1].strip()
    if quoted and field_line:
        raise StudioError("日本語は1つ")
    line = field_line or quoted
    if line:
        if NON_JP_SPEECH_RE.search(line) or not CJK_RE.search(line):
            raise StudioError("「」の中は日本語だけ")
    if not LATIN_RE.search(text):
        raise StudioError("action は英語1本")
    _reject_cjk(text, "action")
    return text, line


def _look_clause(hero: Sheet, enemy: Sheet) -> str:
    chunks: list[str] = []
    for name, sheet in (("Hero", hero), ("Enemy", enemy)):
        bits: list[str] = []
        for key, label in LOOK_LABELS:
            value = getattr(sheet, key).strip()
            if not value:
                continue
            bits.append(f"{label} {value}")
        if bits:
            chunks.append(name + " " + ", ".join(bits))
    if not chunks:
        return ""
    return "Look: " + "; ".join(chunks) + "."


def _one_picture(primary: str, secondary: str, conflict: str) -> str:
    pics = [item for item in (primary.strip(), secondary.strip()) if item]
    if len(set(pics)) > 1:
        raise StudioError(conflict)
    return pics[0] if pics else ""


def _sentences(*parts: str) -> str:
    return " ".join(part.strip() for part in parts if part and part.strip())


def _outside_quotes(text: str) -> str:
    return QUOTE_RE.sub(" ", text)


def _reject_cjk(text: str, label: str) -> None:
    if text and CJK_RE.search(text):
        raise StudioError(f"{label} は英語。日本語は「」")


def _check_age(value: str) -> None:
    if not value:
        return
    if UNDERAGE_WORD_RE.search(value):
        raise StudioError("年齢が21未満の指定は止める")
    for match in re.finditer(r"\d+", value):
        number = int(match.group())
        after = value[match.end() : match.end() + 1]
        if after == "s" and number >= 20:
            continue
        if number < 21:
            raise StudioError("年齢が21未満の指定は止める")


def _scan_blocked(text: str) -> None:
    if text and BLOCK_RE.search(text):
        raise StudioError("公式CM・YouTube・Marvel・商品名は止める")


def _assert_prompt(prompt: str) -> None:
    stripped = DIALOGUE_BLOCK_RE.sub("", prompt)
    if CJK_RE.search(stripped):
        raise StudioError("日本語は <d> の中だけ")
    _scan_blocked(prompt)


def _sheet(raw: Mapping[str, Any]) -> Sheet:
    unknown = sorted(set(raw) - set(LOOK_KEYS))
    if unknown:
        raise StudioError(f"シートの項目が違う: {unknown}")
    values = {key: str(raw.get(key) or "").strip() for key in LOOK_KEYS}
    return Sheet(**values)


def _sheet_env(env: Mapping[str, str], prefix: str) -> dict[str, str]:
    return {key: str(env.get(f"H3_STUDIO_{prefix}_{key.upper()}") or "") for key in LOOK_KEYS}


def _runtime(value: Any) -> str:
    text = str(value or "comfy").strip().lower()
    if text not in {"comfy", "api"}:
        raise StudioError("runtime は comfy か api")
    return text


def _as_bool(value: Any, *, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, int) and value in (0, 1):
        return bool(value)
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "on"}:
        return True
    if text in {"0", "false", "no", "off", ""}:
        return False if text else default
    raise StudioError("真偽が読めない")


def _duration_for(job: str, value: Any) -> float:
    if job == "fast_motion":
        if value is None or value == "":
            return 6.0
        try:
            seconds = float(value)
        except (TypeError, ValueError) as exc:
            raise StudioError("fast_motion の尺は 6 か 9 秒") from exc
        if seconds not in FAST_SECONDS:
            raise StudioError("fast_motion の尺は 6 か 9 秒")
        return seconds
    if job in {"join", "affi_template"}:
        return JOIN_MIN_S
    if value is None:
        value = DEFAULT_SECONDS
    return _duration(value)


def _parts_for(job: str, value: Any) -> tuple[float, ...]:
    if job != "join":
        if value not in (None, "", [], ()):
            raise StudioError("parts は join だけ")
        return ()
    try:
        return parse_join_parts(value)
    except ValueError as exc:
        raise StudioError(str(exc)) from exc


def _duration(value: Any) -> float:
    if value is None or value == "":
        return DEFAULT_SECONDS
    try:
        seconds = float(value)
    except (TypeError, ValueError) as exc:
        raise StudioError("尺は 4–5 秒") from exc
    if seconds != seconds or seconds in (float("inf"), float("-inf")):
        raise StudioError("尺は 4–5 秒")
    if seconds < MIN_SECONDS or seconds > MAX_SECONDS:
        raise StudioError("尺は 4–5 秒")
    return seconds


def _lora_line(item: Mapping[str, Any]) -> str:
    return f"{item['key']} {item['file']} {item['strength']}"


def format_plan(plan: Mapping[str, Any]) -> str:
    """Short human-readable plan. The JSON file is the full plan."""
    lines = [
        f"job {plan.get('job')} task {plan.get('task')} runtime {plan.get('runtime')}",
        f"canvas {plan.get('width')}x{plan.get('height')} {plan.get('resolution')} {plan.get('fps')}fps {plan.get('duration')}s turbo={plan.get('turbo')}",
    ]
    loras = plan.get("loras") or []
    if loras:
        lines.append("loras " + "; ".join(_lora_line(item) for item in loras))
    if plan.get("trigger"):
        lines.append(f"trigger {plan['trigger']}")
    for note in plan.get("notes") or []:
        lines.append(f"note {note}")
    for prompt in prompts_of(plan):
        lines.append("---")
        lines.append(prompt.rstrip())
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] in {"-h", "--help"}:
        print("usage: h3_studio.py plan  < request.json", file=sys.stderr)
        print("       h3_studio.py scenes", file=sys.stderr)
        return 0 if args else 2
    if args[0] == "scenes":
        plan = build_text_scenes()
        if plan.get("generate"):
            print("STUDIO STOP:", GENERATE_MSG)
            return 1
        json.dump(plan, sys.stdout, ensure_ascii=False, indent=2)
        print()
        return 0
    if args[0] != "plan":
        print("usage: h3_studio.py plan  < request.json", file=sys.stderr)
        print("       h3_studio.py scenes", file=sys.stderr)
        return 2
    try:
        raw = json.loads(sys.stdin.read())
        plan = build_plan(request_from(raw))
    except (StudioError, json.JSONDecodeError) as exc:
        print(f"STUDIO STOP: {exc}")
        return 1
    json.dump(plan, sys.stdout, ensure_ascii=False, indent=2)
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
