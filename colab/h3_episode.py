"""One-click MiniMax H3 episode trailers (game-style homage, original story).

`episode.json` is the only input. Every beat is one 10-second H3 clip
(I2V from a clean still, last-frame chain, or T2V). Raw clips get a HUD,
title and end cards, and an audio crossfade stitch. Output lands in
`episodes/<slug>/final/`.

Isolation from the production Grokbot pipeline:
- own Drive root `minimax-h3-comfyui/episodes/<slug>/` (inbox/queued/output of
  the Coconala I2V bot are never touched; only `models/` is shared read-only)
- own prompt builder + validator (the Coconala ad validator is not used)
- Imagine 2.0 is never called (no XAI key, no hoodie-woman default prompt)
- no Automation; one explicit run renders every beat in one runtime, then stops
- HUD is composited after rendering, never burned into a first frame

Prompts are English; only speech inside 「」 is Japanese. Affiliate strings,
minors, brand IP, the referenced video's story elements, and audio meta
phrases that H3 reads aloud are rejected before any GPU time is spent.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from PIL import Image

from h3_hud import (
    HudError,
    card_clip,
    compose_beat,
    extract_last_frame,
    find_font,
    probe_duration,
    render_complete_layer,
    render_end_card,
    render_hud_layer,
    render_mission_layer,
    render_title_card,
    still_clip,
    stitch,
    synthetic_clip,
)
from h3_i2v_phone import BRANCH, REPO, TURBO_LORA_NAME, collect_output_videos, github_raw, newest_mp4, stage_image_into_input
from h3_i2v_runtime import COMFY_DIR_DEFAULT, PORT, comfy_free, ensure_comfy, post_prompt, start_comfy, wait_prompt
from h3_motion_graphics import (
    FORBIDDEN_IN_PROMPT,
    I2VA_HEADER,
    STUDIO_I2V_MINOR_RE,
    STUDIO_SAFETY_CLAUSE_RE,
    assert_i2va_graph,
    build_i2va_graph,
)
from h3_r2v_core import is_oom_error
from h3_t2v import assert_t2v_graph, build_t2v_graph

SCHEMA = "h3-episode/v1"
DRIVE_ROOT_DEFAULT = "/content/drive/MyDrive/minimax-h3-comfyui"
EPISODES_DIRNAME = "episodes"
REPO_EPISODES_DIR = "minimaxh3/episodes"
# H3 canvases are multiples of 32. 1280x720 is not valid; stills are scaled here.
CANVAS: dict[str, tuple[int, int]] = {"16:9": (1024, 576), "9:16": (576, 1024)}
OUTPUT_SIZE: dict[str, dict[int, tuple[int, int]]] = {
    "16:9": {720: (1280, 720), 1080: (1920, 1080)},
    "9:16": {720: (720, 1280), 1080: (1080, 1920)},
}
DURATION_LADDER = (10.0, 8.0, 6.0)
MAX_BEATS = 12
SOURCES = ("still", "chain", "t2v")
EPISODE_DIRS = ("stills", "input", "output", "raw", "hud", "hud/png", "final", "logs")
CARD_TITLE_S = 2.6
CARD_END_S = 3.2
ORIGINAL_LINE = "舞台・人物・物語はオリジナル"
# Files a fresh Colab runtime needs in /content. Fetched from GitHub, cached in Drive episodes/_lib/.
EPISODE_HELPERS = (
    "colab/h3_r2v_core.py",
    "colab/h3_motion_graphics.py",
    "colab/h3_t2v.py",
    "colab/h3_i2v_phone.py",
    "colab/h3_i2v_job.py",
    "colab/h3_i2v_runtime.py",
    "colab/h3_hud.py",
    "colab/h3_episode.py",
    "colab/h3_episode_colab_main.py",
)

LORA_FILES = {
    "turbo4": TURBO_LORA_NAME,
    "turbo8": "minimax_h3_fl2v_turbo_8step_v1.0_768p_comfyui_bf16.safetensors",
    "larry": "minimax_h3_turbo_v4_step600_ema_comfy.safetensors",
    "cinema": "Minimax_H3_cinematic_DY.safetensors",
}
# Larry and LightX2V turbo never stack (h3-lora-studio rule). cinema is optional everywhere.
PRESETS: dict[str, dict[str, Any]] = {
    "fast": {"stack": [("turbo4", 1.0, False)], "steps": 4, "trigger": ""},
    "preview": {"stack": [("turbo4", 1.0, False), ("cinema", 0.5, True)], "steps": 4, "trigger": "DY"},
    "daily": {"stack": [("larry", 1.0, False), ("cinema", 0.65, True)], "steps": 8, "trigger": "DY"},
}

SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{1,40}$")
BEAT_ID_RE = re.compile(r"^[0-9]{2}-[a-z0-9-]{1,32}$")
KANJI_RE = re.compile(r"[\u4e00-\u9fff]")
CJK_RE = re.compile(r"[\u3040-\u30ff\u4e00-\u9fff\uff66-\uff9f]")
QUOTE_RE = re.compile(r"「[^」]*」")
NEGATION_RE = re.compile(r"\b(?:no|never|without|not|nobody|none)\b[^.;\n]*", re.I)
IP_TOKENS_RE = re.compile(
    r"\b(street fighter|ryu|ken masters|hadouken|hadoken|shoryuken|gta|grand theft auto|rockstar|"
    r"pollo|seedance|yakuza|like a dragon|nintendo|playstation|xbox|capcom|sega|mario|zelda)\b",
    re.I,
)
META_AUDIO_TOKENS = ("lip-synced", "lip synced", "no other speech", "only say", "other_text", "not_spoken", "read aloud")
SCREEN_TOKENS_RE = re.compile(r"\b(hud|mini-?map|subtitles?|captions?|on-screen text|watermark|health bar|game ui)\b", re.I)
HARM_TOKENS_RE = re.compile(r"\b(blood|bloody|gore|gory|dismember\w*|corpses?|dead body|dead bodies)\b", re.I)
DEFAULT_MUSIC = "Low pulsing synth bass with a sparse taiko hit at the start; holds under the whole clip."
VIOLENCE_CLAUSE = (
    "Exaggerated video-game physics: adults tumble harmlessly like ragdolls, objects fly, "
    "comedic tone. Nobody is hurt, no blood, no injuries, no children anywhere in frame."
)


class EpisodeError(RuntimeError):
    pass


# ---------------------------------------------------------------- load / validate

def load_episode(path: Path | str) -> dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise EpisodeError("episode.json must be an object")
    return data


def canvas_for(ep: dict[str, Any]) -> tuple[int, int]:
    key = str(ep.get("canvas") or "16:9")
    if key not in CANVAS:
        raise EpisodeError(f"canvas must be one of {list(CANVAS)}")
    return CANVAS[key]


def output_size_for(ep: dict[str, Any]) -> tuple[int, int]:
    key = str(ep.get("canvas") or "16:9")
    height = int((ep.get("stitch") or {}).get("output_height") or 720)
    table = OUTPUT_SIZE.get(key) or OUTPUT_SIZE["16:9"]
    return table.get(height) or table[720]


def clip_seconds(ep: dict[str, Any]) -> float:
    return float(ep.get("clip_seconds") or 10.0)


def duration_ladder(ep: dict[str, Any]) -> list[float]:
    top = clip_seconds(ep)
    out = [top]
    for d in DURATION_LADDER:
        if d < top and d not in out:
            out.append(d)
    return out


def episode_assets(ep: dict[str, Any]) -> list[str]:
    """Relative paths the episode needs on disk (stills, cast refs, card images)."""
    rels: list[str] = []
    for beat in ep.get("beats") or []:
        if beat.get("still"):
            rels.append(str(beat["still"]))
    for c in (ep.get("cast") or {}).values():
        if isinstance(c, dict) and c.get("ref_still"):
            rels.append(str(c["ref_still"]))
    cards = ep.get("cards") or {}
    for key in ("title_image", "end_image"):
        if cards.get(key):
            rels.append(str(cards[key]))
    out: list[str] = []
    for r in rels:
        if r not in out:
            out.append(r)
    return out


def _speech_errors(beat: dict[str, Any], cast: dict[str, Any], where: str) -> list[str]:
    errs: list[str] = []
    speech = beat.get("speech") or []
    if not isinstance(speech, list):
        return [f"{where}: speech must be a list"]
    if speech and not beat.get("face_visible"):
        errs.append(f"{where}: speech only on beats with face_visible true (H3 lip-sync needs the mouth)")
    if len(speech) > 2:
        errs.append(f"{where}: at most 2 spoken lines per 10s beat")
    for i, item in enumerate(speech):
        if not isinstance(item, dict) or not item.get("who") or not item.get("line"):
            errs.append(f"{where}: speech[{i}] needs who + line")
            continue
        who = str(item["who"])
        line = str(item["line"]).strip()
        if who not in (beat.get("cast") or []):
            errs.append(f"{where}: speaker {who} is not in this beat's cast")
        if who not in cast:
            errs.append(f"{where}: speaker {who} is not in cast")
        if "「" in line or "」" in line:
            errs.append(f"{where}: speech[{i}] must not contain 「」 (added automatically)")
        if KANJI_RE.search(line):
            errs.append(f"{where}: speech[{i}] must be kana only (H3 misreads kanji): {line}")
        if len(line) > 26:
            errs.append(f"{where}: speech[{i}] too long for one breath (<= 26 chars)")
        if not CJK_RE.search(line):
            errs.append(f"{where}: speech[{i}] must be Japanese")
    return errs


def validate_episode(ep: dict[str, Any], *, root: Path | str | None = None) -> list[str]:
    errs: list[str] = []
    if ep.get("schema") != SCHEMA:
        errs.append(f"schema must be {SCHEMA}")
    slug = str(ep.get("slug") or "")
    if not SLUG_RE.match(slug):
        errs.append("slug must be lowercase kebab (2-41 chars)")
    if not str(ep.get("title") or "").strip():
        errs.append("title missing")
    if str(ep.get("canvas") or "16:9") not in CANVAS:
        errs.append(f"canvas must be one of {list(CANVAS)}")
    try:
        cs = clip_seconds(ep)
        if cs < 4 or cs > 10:
            errs.append("clip_seconds must be 4-10 (15s OOMs and shrinks the canvas)")
    except (TypeError, ValueError):
        errs.append("clip_seconds must be a number")
    render = ep.get("render") or {}
    preset = str(render.get("preset") or "fast")
    if preset not in PRESETS:
        errs.append(f"render.preset must be one of {list(PRESETS)}")
    fb = str(render.get("fallback_preset") or "fast")
    if fb not in PRESETS:
        errs.append(f"render.fallback_preset must be one of {list(PRESETS)}")
    if not str(ep.get("style") or "").strip():
        errs.append("style (English look lock) missing")
    world = ep.get("world") or {}
    if not str(world.get("lock") or "").strip():
        errs.append("world.lock (English environment lock) missing")
    for key, text in (("style", ep.get("style")), ("world.lock", world.get("lock"))):
        if text and CJK_RE.search(str(text)):
            errs.append(f"{key} must be English (Japanese only inside 「」 speech)")
    cast = ep.get("cast") or {}
    if not isinstance(cast, dict) or not cast:
        errs.append("cast must be a non-empty object")
        cast = {}
    for cid, c in cast.items():
        if not isinstance(c, dict):
            errs.append(f"cast.{cid} must be an object")
            continue
        if not str(c.get("lock") or "").strip():
            errs.append(f"cast.{cid}.lock (English identity lock) missing")
        elif CJK_RE.search(str(c["lock"])):
            errs.append(f"cast.{cid}.lock must be English")
        try:
            if int(c.get("age") or 0) < 20:
                errs.append(f"cast.{cid}.age must be an adult (>= 20)")
        except (TypeError, ValueError):
            errs.append(f"cast.{cid}.age must be an integer")
    beats = ep.get("beats") or []
    if not isinstance(beats, list) or not beats:
        errs.append("beats must be a non-empty list")
        beats = []
    if len(beats) > MAX_BEATS:
        errs.append(f"at most {MAX_BEATS} beats")
    seen: set[str] = set()
    for i, beat in enumerate(beats):
        where = f"beats[{i}]"
        if not isinstance(beat, dict):
            errs.append(f"{where} must be an object")
            continue
        bid = str(beat.get("id") or "")
        if not BEAT_ID_RE.match(bid):
            errs.append(f"{where}: id must look like 01-exit-noren")
        if bid in seen:
            errs.append(f"{where}: duplicate id {bid}")
        seen.add(bid)
        source = str(beat.get("source") or "still")
        if source not in SOURCES:
            errs.append(f"{where}: source must be one of {SOURCES}")
        if source == "chain" and i == 0:
            errs.append(f"{where}: first beat cannot chain (nothing before it)")
        still = str(beat.get("still") or "")
        if source == "still":
            if not still:
                errs.append(f"{where}: source still needs a still path")
            elif "-hud" in Path(still).stem or "hud" in Path(still).parts[:-1]:
                errs.append(f"{where}: HUD-burned stills cannot be first frames: {still}")
            elif root is not None and not (Path(root) / still).is_file():
                errs.append(f"{where}: still missing on disk: {still}")
        for cid in beat.get("cast") or []:
            if cid not in cast:
                errs.append(f"{where}: unknown cast id {cid}")
        for key in ("action", "camera"):
            text = str(beat.get(key) or "").strip()
            if not text:
                errs.append(f"{where}: {key} missing")
            elif CJK_RE.search(text):
                errs.append(f"{where}: {key} must be English")
        for key in ("sfx", "music", "place"):
            text = str(beat.get(key) or "")
            if text and CJK_RE.search(text):
                errs.append(f"{where}: {key} must be English")
        errs.extend(_speech_errors(beat, cast, where))
        hud = beat.get("hud") or {}
        mission = str(hud.get("mission") or "").strip()
        if not mission:
            errs.append(f"{where}: hud.mission missing")
        elif len(mission) > 24:
            errs.append(f"{where}: hud.mission too long (<= 24 chars)")
        if len(str(hud.get("hint") or "")) > 16:
            errs.append(f"{where}: hud.hint too long (<= 16 chars)")
        for key in ("health", "stamina"):
            try:
                v = float(hud.get(key, 1.0))
                if v < 0 or v > 1:
                    errs.append(f"{where}: hud.{key} must be 0-1")
            except (TypeError, ValueError):
                errs.append(f"{where}: hud.{key} must be a number")
        try:
            heat = int(hud.get("heat", 0) or 0)
            if heat < 0 or heat > 5:
                errs.append(f"{where}: hud.heat must be 0-5")
        except (TypeError, ValueError):
            errs.append(f"{where}: hud.heat must be an integer")
    cards = ep.get("cards") or {}
    if cards.get("end", True) and not str(cards.get("disclaimer") or "").strip():
        errs.append("cards.disclaimer required when the end card is on (fictional game notice)")
    stitch_cfg = ep.get("stitch") or {}
    if str(stitch_cfg.get("transition") or "xfade") not in ("xfade", "cut"):
        errs.append("stitch.transition must be xfade or cut")
    if int(stitch_cfg.get("output_height") or 720) not in (720, 1080):
        errs.append("stitch.output_height must be 720 or 1080")
    if root is not None:
        for rel in episode_assets(ep):
            if not (Path(root) / rel).is_file():
                errs.append(f"asset missing on disk: {rel}")
    return errs


# ---------------------------------------------------------------- prompts

def strip_negations(text: str) -> str:
    """Drop negated clauses so 'no blood' does not trip the positive blood check."""
    return NEGATION_RE.sub(" ", text)


def cjk_outside_quotes(text: str) -> bool:
    return bool(CJK_RE.search(QUOTE_RE.sub("", text)))


def forbidden_hits(text: str, *, never: list[str] | None = None) -> list[str]:
    low = text.lower()
    hits: list[str] = []
    for bad in FORBIDDEN_IN_PROMPT:
        if bad.lower() in low:
            hits.append(bad)
    for bad in META_AUDIO_TOKENS:
        if bad in low:
            hits.append(bad)
    for m in IP_TOKENS_RE.finditer(text):
        hits.append(m.group(0))
    positive = strip_negations(text)
    for m in SCREEN_TOKENS_RE.finditer(positive):
        hits.append(m.group(0))
    for m in HARM_TOKENS_RE.finditer(positive):
        hits.append(m.group(0))
    cleaned = STUDIO_SAFETY_CLAUSE_RE.sub(" ", text)
    for m in STUDIO_I2V_MINOR_RE.finditer(cleaned):
        hits.append(m.group(0))
    for bad in never or []:
        if bad and str(bad).lower() in low:
            hits.append(str(bad))
    out: list[str] = []
    for h in hits:
        if h.lower() not in [o.lower() for o in out]:
            out.append(h)
    return out


def _cast_block(ep: dict[str, Any], beat: dict[str, Any]) -> str:
    cast = ep.get("cast") or {}
    lines: list[str] = []
    for cid in beat.get("cast") or []:
        c = cast.get(cid) or {}
        name = str(c.get("name_en") or cid.title())
        lock = str(c.get("lock") or "").strip().rstrip(".")
        lines.append(f"{name}: {lock}. Adult, {int(c.get('age') or 0)}.")
    return "\n".join(lines)


def _speech_visual(ep: dict[str, Any], beat: dict[str, Any]) -> str:
    cast = ep.get("cast") or {}
    parts: list[str] = []
    for item in beat.get("speech") or []:
        name = str((cast.get(item["who"]) or {}).get("name_en") or str(item["who"]).title())
        parts.append(f"{name} speaks with clearly visible mouth movement: 「{item['line']}」.")
    return " ".join(parts)


def _speech_audio(ep: dict[str, Any], beat: dict[str, Any]) -> str:
    cast = ep.get("cast") or {}
    parts: list[str] = []
    for item in beat.get("speech") or []:
        c = cast.get(item["who"]) or {}
        voice = str(c.get("voice") or "natural adult voice")
        parts.append(f"「{item['line']}」 in a {voice}.")
    return " ".join(parts)


def build_beat_prompt(ep: dict[str, Any], beat: dict[str, Any], *, trigger: str = "") -> str:
    """Canonical H3 sections. English body, Japanese only inside 「」."""
    source = str(beat.get("source") or "still")
    canvas = str(ep.get("canvas") or "16:9")
    orientation = "Horizontal 16:9" if canvas == "16:9" else "Vertical 9:16"
    world = ep.get("world") or {}
    props = ep.get("props") or {}
    style = str(ep.get("style") or "").strip().rstrip(".")
    env = str(world.get("lock") or "").strip().rstrip(".")
    place = str(beat.get("place") or "").strip().rstrip(".")
    env_line = env + (f". {place}" if place else "")
    if world.get("no_text_on_signs", True):
        env_line += ". Signs, posters, and screens carry no readable letters"
    env_line += ". Adults only in frame."
    desc: list[str] = [f"[Shot 1] {orientation} {style}."]
    if source in ("still", "chain"):
        desc.append("<Picture 1> is the identity, costume, prop, and set lock; the clip starts exactly on it.")
    if source == "chain":
        desc.append("This shot continues the previous one without a cut.")
    desc.append(str(beat.get("camera") or "").strip().rstrip(".") + ".")
    desc.append(str(beat.get("action") or "").strip().rstrip(".") + ".")
    if props:
        desc.append("Props stay locked: " + "; ".join(f"{k} = {str(v).rstrip('.')}" for k, v in props.items()) + ".")
    if str(ep.get("violence") or "none") == "game" and beat.get("physics", False):
        desc.append(VIOLENCE_CLAUSE)
    vis = _speech_visual(ep, beat)
    if vis:
        desc.append(vis)
    desc.append("Identity, costume, and props stay locked for the whole clip.")
    sfx = str(beat.get("sfx") or "Natural ambience of the place").strip().rstrip(".")
    audio = _speech_audio(ep, beat)
    sound = sfx + "." + (f" {audio}" if audio else "")
    music = str(beat.get("music") or DEFAULT_MUSIC).strip()
    head = ""
    if source in ("still", "chain"):
        head = I2VA_HEADER + "\n\n"
    body = (
        f"subject_definitions:\n{_cast_block(ep, beat)}\n\n"
        f"environment:\n{env_line}\n\n"
        f"integrated_multimodal_description:\n{' '.join(desc)}\n\n"
        f"overall_soundscape:\n{sound}\n\n"
        f"non_diegetic_music:\n{music}\n"
    )
    prefix = f"{trigger.strip()}\n" if trigger.strip() else ""
    return prefix + head + body


def validate_beat_prompt(prompt: str, *, source: str, never: list[str] | None = None) -> list[str]:
    errs: list[str] = []
    p = prompt or ""
    if not p.strip():
        return ["prompt empty"]
    if source in ("still", "chain"):
        if I2VA_HEADER not in p:
            errs.append("I2VA 0.00s Picture 1 header missing")
        if "<Picture 1>" not in p:
            errs.append("Picture 1 tag missing")
    else:
        if "<Picture 1>" in p or I2VA_HEADER in p:
            errs.append("T2V beat must not reference Picture 1")
    for key in ("subject_definitions:", "environment:", "integrated_multimodal_description:", "overall_soundscape:", "non_diegetic_music:"):
        if key not in p:
            errs.append(f"missing {key}")
    if "[Shot 1]" not in p:
        errs.append("missing [Shot 1]")
    if cjk_outside_quotes(p):
        errs.append("Japanese outside 「」 (H3 reads it aloud)")
    hits = forbidden_hits(p, never=never)
    if hits:
        errs.append(f"forbidden in prompt: {hits}")
    return errs


def beat_prompts(ep: dict[str, Any], *, trigger: str = "") -> list[tuple[dict[str, Any], str, list[str]]]:
    never = [str(x) for x in ((ep.get("homage") or {}).get("never") or [])]
    out = []
    for beat in ep.get("beats") or []:
        prompt = build_beat_prompt(ep, beat, trigger=trigger)
        errs = validate_beat_prompt(prompt, source=str(beat.get("source") or "still"), never=never)
        out.append((beat, prompt, errs))
    return out


# ---------------------------------------------------------------- roots / staging

def episodes_root(main_root: Path | str | None = None) -> Path:
    env = os.environ.get("H3_EPISODES_ROOT")
    if env:
        return Path(env)
    return Path(main_root or os.environ.get("H3_DRIVE_ROOT") or DRIVE_ROOT_DEFAULT) / EPISODES_DIRNAME


def episode_root(slug: str, main_root: Path | str | None = None) -> Path:
    if not SLUG_RE.match(slug or ""):
        raise EpisodeError(f"bad slug {slug!r}")
    return episodes_root(main_root) / slug


def ensure_episode_tree(root: Path | str) -> Path:
    root = Path(root)
    for name in EPISODE_DIRS:
        (root / name).mkdir(parents=True, exist_ok=True)
    return root


def assert_not_production_root(root: Path | str, main_root: Path | str | None = None) -> None:
    """The episode tree must never be the Grokbot root (its inbox adopts bare jpgs as Coconala jobs)."""
    r = Path(root).resolve()
    main = Path(main_root or os.environ.get("H3_DRIVE_ROOT") or DRIVE_ROOT_DEFAULT).resolve()
    if r == main or r.parent == main and r.name in ("inbox", "queued", "running", "done", "failed", "input", "output", "models"):
        raise EpisodeError(f"episode root must live under {main / EPISODES_DIRNAME}, not {r}")


def stage_still(src: Path | str, dest: Path | str, canvas: tuple[int, int]) -> Path:
    """Scale (center-crop if the aspect differs) to the exact H3 canvas. JPEG, no HUD."""
    src = Path(src)
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    im = Image.open(src).convert("RGB")
    cw, ch = canvas
    target = cw / ch
    w, h = im.size
    if abs(w / h - target) > 0.01:
        if w / h > target:
            nw = int(round(h * target))
            x0 = (w - nw) // 2
            im = im.crop((x0, 0, x0 + nw, h))
        else:
            nh = int(round(w / target))
            y0 = (h - nh) // 2
            im = im.crop((0, y0, w, y0 + nh))
    im = im.resize((cw, ch), Image.LANCZOS)
    im.save(dest, "JPEG", quality=95, subsampling=0)
    return dest


def fetch_text(url: str, dest: Path, *, min_bytes: int = 100) -> bool:
    try:
        dest.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(url, dest)
        return dest.is_file() and dest.stat().st_size > min_bytes
    except Exception as e:  # network
        print("fetch fail", url, e)
        return False


def bootstrap_episode(slug: str, root: Path | str, *, branch: str | None = None, repo: str = REPO) -> list[str]:
    """First run on a fresh Drive: pull episode.json and its stills from GitHub. Never overwrites."""
    root = Path(root)
    ensure_episode_tree(root)
    br = branch or os.environ.get("H3_HELPER_BRANCH") or BRANCH
    fetched: list[str] = []
    ep_path = root / "episode.json"
    if not ep_path.is_file():
        if not fetch_text(github_raw(f"{REPO_EPISODES_DIR}/{slug}/episode.json", repo=repo, branch=br), ep_path):
            raise EpisodeError(f"episode.json missing in {root} and not on GitHub ({br})")
        fetched.append("episode.json")
    ep = load_episode(ep_path)
    for rel in episode_assets(ep):
        dest = root / rel
        if dest.is_file():
            continue
        if fetch_text(github_raw(f"{REPO_EPISODES_DIR}/{slug}/{rel}", repo=repo, branch=br), dest, min_bytes=1000):
            fetched.append(rel)
    return fetched


# ---------------------------------------------------------------- render plan

def resolve_preset(name: str, loras_dir: Path | str | None, *, fallback: str = "fast") -> dict[str, Any]:
    """Preset → concrete LoRA files that exist. Missing optional → dropped; missing required → fallback."""
    if name not in PRESETS:
        raise EpisodeError(f"unknown preset {name}")
    spec = PRESETS[name]
    stack: list[tuple[str, float]] = []
    notes: list[str] = []
    for key, strength, optional in spec["stack"]:
        fname = LORA_FILES[key]
        present = loras_dir is None or (Path(loras_dir) / fname).is_file()
        if present:
            stack.append((fname, float(strength)))
        elif optional:
            notes.append(f"optional LoRA missing, dropped: {fname}")
        else:
            notes.append(f"required LoRA missing: {fname} → preset {fallback}")
            if fallback == name:
                raise EpisodeError(f"preset {name} unusable and no fallback")
            out = resolve_preset(fallback, loras_dir, fallback=fallback)
            out["notes"] = notes + out.get("notes", [])
            return out
    names = [s[0].lower() for s in stack]
    if any("turbo_v4" in n for n in names) and any("fl2v_turbo" in n for n in names):
        raise EpisodeError("Larry and LightX2V turbo never stack")
    return {"name": name, "stack": stack, "steps": int(spec["steps"]), "trigger": str(spec["trigger"]), "notes": notes}


def chain_extra_loras(g: dict[str, Any], extra: list[tuple[str, float]]) -> dict[str, Any]:
    """Append LoraLoaderModelOnly nodes after node 2 and rewire scheduler/guider to the last one."""
    if not extra:
        return g
    if g.get("2", {}).get("class_type") != "LoraLoaderModelOnly":
        raise EpisodeError("graph has no LoRA loader to chain from (has_lora_loader False?)")
    prev = "2"
    for i, (name, strength) in enumerate(extra):
        nid = f"2{chr(ord('b') + i)}"
        g[nid] = {
            "class_type": "LoraLoaderModelOnly",
            "inputs": {"model": [prev, 0], "lora_name": name, "strength_model": float(strength)},
        }
        prev = nid
    g["23"]["inputs"]["model"] = [prev, 0]
    g["24"]["inputs"]["model"] = [prev, 0]
    return g


def build_episode_graph(
    *,
    source: str,
    first_image: str | None,
    prompt: str,
    unet: str,
    preset: dict[str, Any],
    width: int,
    height: int,
    duration_s: float,
    seed: int,
    filename_prefix: str,
    has_lora_loader: bool = True,
    has_audio_decode: bool = True,
) -> dict[str, Any]:
    stack = list(preset.get("stack") or [])
    lora_name, lora_strength = (stack[0] if stack else (None, 1.0))
    common = dict(
        prompt=prompt,
        unet=unet,
        lora_name=lora_name,
        lora_strength=float(lora_strength),
        width=int(width),
        height=int(height),
        duration_s=float(duration_s),
        seed=int(seed),
        steps=int(preset.get("steps") or 4),
        filename_prefix=filename_prefix,
        has_lora_loader=has_lora_loader,
        has_audio_decode=has_audio_decode,
    )
    if source == "t2v":
        g = build_t2v_graph(**common)
    else:
        if not first_image:
            raise EpisodeError("I2V beat needs a first image")
        g = build_i2va_graph(first_image=first_image, last_image=None, **common)
    if lora_name and has_lora_loader:
        chain_extra_loras(g, stack[1:])
    errs = assert_t2v_graph(g) if source == "t2v" else assert_i2va_graph(g, expect_last=False, homage=False)
    if errs:
        raise EpisodeError(f"graph invalid: {errs}")
    return g


def render_beat_comfy(
    *,
    source: str,
    first_image: str | None,
    prompt: str,
    comfy_dir: Path,
    canvas: tuple[int, int],
    durations: list[float],
    preset: dict[str, Any],
    seed: int,
    filename_prefix: str,
    port: int = PORT,
    object_info: dict[str, Any] | None = None,
    poster: Callable[..., Any] = post_prompt,
    waiter: Callable[..., Any] = wait_prompt,
) -> dict[str, Any]:
    """Keep the canvas; on OOM shorten the clip (10→8→6). Never drop the first frame."""
    obj = object_info or {}
    diff_dir = comfy_dir / "models/diffusion_models"
    diff = list(diff_dir.glob("*fl2va*")) if diff_dir.exists() else []
    unet = diff[0].name if diff else "minimax_h3_fl2va_pruned_int8_convrot.safetensors"
    out_root = comfy_dir / "output"
    before = newest_mp4(out_root)
    last_err: Any = None
    for dur in durations:
        g = build_episode_graph(
            source=source,
            first_image=first_image,
            prompt=prompt,
            unet=unet,
            preset=preset,
            width=canvas[0],
            height=canvas[1],
            duration_s=dur,
            seed=seed,
            filename_prefix=filename_prefix,
            has_lora_loader=("LoraLoaderModelOnly" in obj) if obj else True,
            has_audio_decode=("VAEDecodeAudio" in obj) if obj else True,
        )
        print("render", filename_prefix, f"{canvas[0]}x{canvas[1]}", f"{dur:.0f}s", "steps", preset.get("steps"), "loras", [s[0] for s in preset.get("stack") or []])
        res, err = poster(g, port)
        if err:
            last_err = err
            if is_oom_error(err):
                comfy_free(port)
                continue
            raise EpisodeError(err)
        if not (res and "prompt_id" in res):
            raise EpisodeError(str(res))
        ok, payload = waiter(res["prompt_id"], port)
        if ok:
            videos = collect_output_videos(payload, out_root)
            fresh = newest_mp4(out_root)
            if fresh and fresh not in videos and (before is None or fresh != before):
                videos.append(fresh)
            return {"videos": [str(v) for v in videos], "duration_s": dur, "canvas": f"{canvas[0]}x{canvas[1]}"}
        last_err = payload
        if is_oom_error(payload):
            comfy_free(port)
            continue
        raise EpisodeError(str(payload))
    raise EpisodeError(f"all durations OOM: {last_err}")


# ---------------------------------------------------------------- status

def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def load_status(root: Path) -> dict[str, Any]:
    p = root / "status.json"
    if p.is_file():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return {"beats": {}}


def save_status(root: Path, status: dict[str, Any]) -> None:
    status["updated"] = _now()
    (root / "status.json").write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


# ---------------------------------------------------------------- pipeline

def preflight(ep: dict[str, Any], root: Path | str, *, need_ffmpeg: bool = True) -> list[str]:
    """Everything that can fail before a GPU is touched."""
    errs = validate_episode(ep, root=root)
    try:
        find_font((ep.get("hud") or {}).get("font") or None)
    except HudError as e:
        errs.append(str(e))
    if need_ffmpeg and not shutil.which("ffmpeg"):
        errs.append("ffmpeg missing")
    preset_name = str((ep.get("render") or {}).get("preset") or "fast")
    trigger = PRESETS.get(preset_name, PRESETS["fast"])["trigger"]
    for beat, _prompt, perrs in beat_prompts(ep, trigger=trigger):
        for e in perrs:
            errs.append(f"{beat.get('id')}: {e}")
    return errs


def write_prompts(ep: dict[str, Any], dest_dir: Path | str, *, trigger: str = "") -> list[Path]:
    dest = Path(dest_dir)
    dest.mkdir(parents=True, exist_ok=True)
    out: list[Path] = []
    for beat, prompt, _errs in beat_prompts(ep, trigger=trigger):
        p = dest / f"{beat['id']}.txt"
        p.write_text(prompt, encoding="utf-8")
        out.append(p)
    return out


def hud_pngs(ep: dict[str, Any], beat: dict[str, Any], out_size: tuple[int, int], png_dir: Path) -> dict[str, Path | None]:
    hud_cfg = ep.get("hud") or {}
    hud = beat.get("hud") or {}
    theme_name = str(hud_cfg.get("theme") or "bandai")
    font = find_font(hud_cfg.get("font") or None)
    png_dir.mkdir(parents=True, exist_ok=True)
    bid = beat["id"]
    layer = render_hud_layer(out_size, hud, theme_name=theme_name, district=str(hud_cfg.get("district_label") or ""), icons=list(hud_cfg.get("icons") or []), font_path=font)
    p_hud = png_dir / f"{bid}-hud.png"
    layer.save(p_hud)
    mission = render_mission_layer(out_size, str(hud.get("mission") or ""), theme_name=theme_name, font_path=font)
    p_mis = png_dir / f"{bid}-mission.png"
    mission.save(p_mis)
    p_cmp: Path | None = None
    if hud.get("complete"):
        cmp_layer = render_complete_layer(out_size, str(hud_cfg.get("complete_text") or "ミッション完了"), theme_name=theme_name, font_path=font)
        p_cmp = png_dir / f"{bid}-complete.png"
        cmp_layer.save(p_cmp)
    return {"hud": p_hud, "mission": p_mis, "complete": p_cmp}


def _card_images(ep: dict[str, Any], root: Path, out_size: tuple[int, int], png_dir: Path) -> tuple[Path | None, Path | None]:
    cards = ep.get("cards") or {}
    hud_cfg = ep.get("hud") or {}
    font = find_font(hud_cfg.get("font") or None)
    title_png: Path | None = None
    end_png: Path | None = None
    beats = ep.get("beats") or []
    if cards.get("title", True):
        img = cards.get("title_image")
        if not img:
            for c in (ep.get("cast") or {}).values():
                if isinstance(c, dict) and c.get("ref_still"):
                    img = c["ref_still"]
                    break
        if not img and beats and beats[0].get("still"):
            img = beats[0]["still"]
        title_png = png_dir / "card-title.png"
        render_title_card(out_size, title=str(ep.get("title") or ""), subtitle=str(ep.get("subtitle") or ""), kicker=str(cards.get("kicker") or ORIGINAL_LINE), image=(root / img) if img else None, font_path=font).save(title_png)
    if cards.get("end", True):
        img = cards.get("end_image")
        if not img and beats and beats[-1].get("still"):
            img = beats[-1]["still"]
        lines = [str(x) for x in (cards.get("end_lines") or [])] or [str(cards.get("disclaimer") or ""), ORIGINAL_LINE]
        end_png = png_dir / "card-end.png"
        render_end_card(out_size, title=str(cards.get("end_title") or ep.get("title") or ""), lines=lines, image=(root / img) if img else None, font_path=font).save(end_png)
    return title_png, end_png


def finish_episode(ep: dict[str, Any], root: Path | str, *, raw_dir: Path | str | None = None, out_name: str | None = None) -> Path:
    """raw/<beat>.mp4 → hud/<beat>.mp4 → cards → final/<slug>-<stamp>.mp4 (+ latest.mp4)."""
    root = Path(root)
    ensure_episode_tree(root)
    raw = Path(raw_dir) if raw_dir else root / "raw"
    out_size = output_size_for(ep)
    png_dir = root / "hud" / "png"
    ordered: list[Path] = []
    for beat in ep.get("beats") or []:
        src = raw / f"{beat['id']}.mp4"
        if not src.is_file():
            raise EpisodeError(f"raw clip missing: {src}")
        pngs = hud_pngs(ep, beat, out_size, png_dir)
        dest = root / "hud" / f"{beat['id']}.mp4"
        compose_beat(src, dest, out_size=out_size, hud_png=pngs["hud"], mission_png=pngs["mission"], complete_png=pngs["complete"])
        ordered.append(dest)
    title_png, end_png = _card_images(ep, root, out_size, png_dir)
    clips: list[Path] = []
    if title_png:
        clips.append(card_clip(title_png, root / "hud" / "00-title.mp4", seconds=CARD_TITLE_S, out_size=out_size))
    clips.extend(ordered)
    if end_png:
        clips.append(card_clip(end_png, root / "hud" / "99-end.mp4", seconds=CARD_END_S, out_size=out_size))
    cfg = ep.get("stitch") or {}
    name = out_name or f"{ep['slug']}-{_now()}.mp4"
    final = root / "final" / name
    stitch(clips, final, out_size=out_size, transition=str(cfg.get("transition") or "xfade"), xfade_s=float(cfg.get("xfade_s", 0.35)), loudnorm=bool(cfg.get("loudnorm", True)))
    latest = root / "final" / "latest.mp4"
    shutil.copy2(final, latest)
    (root / "final" / "latest.txt").write_text(final.name + "\n", encoding="utf-8")
    return final


def _first_frame_for(beat: dict[str, Any], idx: int, ep: dict[str, Any], root: Path, canvas: tuple[int, int], comfy_input: Path | None) -> str | None:
    source = str(beat.get("source") or "still")
    if source == "t2v":
        return None
    staged = root / "input" / f"{beat['id']}.jpg"
    if source == "still":
        stage_still(root / str(beat["still"]), staged, canvas)
    else:
        prev = (ep.get("beats") or [])[idx - 1]
        prev_clip = root / "raw" / f"{prev['id']}.mp4"
        if not prev_clip.is_file():
            raise EpisodeError(f"chain source missing: {prev_clip}")
        tmp = root / "input" / f"{beat['id']}-last.jpg"
        extract_last_frame(prev_clip, tmp)
        stage_still(tmp, staged, canvas)
    if comfy_input is None:
        return staged.name
    return stage_image_into_input(staged, comfy_input)


def run_episode(
    ep: dict[str, Any],
    root: Path | str,
    *,
    models_root: Path | str | None = None,
    comfy_dir: Path | str | None = None,
    dry_run: bool = False,
    fresh: bool = False,
    preset_override: str | None = None,
    port: int = PORT,
    object_info: dict[str, Any] | None = None,
    poster: Callable[..., Any] = post_prompt,
    waiter: Callable[..., Any] = wait_prompt,
) -> Path:
    """The one click: preflight → every beat → HUD → cards → stitch. Resumes from raw/."""
    root = Path(root)
    ensure_episode_tree(root)
    errs = preflight(ep, root)
    if errs:
        raise EpisodeError("preflight failed:\n- " + "\n- ".join(errs))
    canvas = canvas_for(ep)
    render_cfg = ep.get("render") or {}
    preset_name = str(preset_override or render_cfg.get("preset") or "fast")
    fallback = str(render_cfg.get("fallback_preset") or "fast")
    seed = int(render_cfg.get("seed") or 42)
    status = load_status(root)
    status.update({"slug": ep.get("slug"), "canvas": f"{canvas[0]}x{canvas[1]}", "preset_requested": preset_name, "dry_run": bool(dry_run)})
    comfy = Path(comfy_dir or os.environ.get("H3_COMFY_DIR") or COMFY_DIR_DEFAULT)
    comfy_input: Path | None = None
    preset: dict[str, Any]
    if dry_run:
        preset = resolve_preset(preset_name, None, fallback=fallback)
    else:
        models = Path(models_root or os.environ.get("H3_MODELS_ROOT") or (Path(os.environ.get("H3_DRIVE_ROOT") or DRIVE_ROOT_DEFAULT) / "models"))
        ensure_comfy(comfy, root, models, need_r2v=False)
        start_comfy(comfy, port=port)
        preset = resolve_preset(preset_name, models / "loras", fallback=fallback)
        comfy_input = comfy / "input"
        if object_info is None:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/object_info", timeout=60) as r:
                object_info = json.loads(r.read().decode())
            if "MiniMaxH3ImageToVideo" not in (object_info or {}):
                raise EpisodeError("MiniMaxH3ImageToVideo missing in ComfyUI")
    for note in preset.get("notes") or []:
        print("preset:", note)
    status["preset"] = preset["name"]
    save_status(root, status)
    never = [str(x) for x in ((ep.get("homage") or {}).get("never") or [])]
    beats = ep.get("beats") or []
    for idx, beat in enumerate(beats):
        bid = beat["id"]
        raw_out = root / "raw" / f"{bid}.mp4"
        if raw_out.is_file() and not fresh:
            print("skip (exists)", raw_out.name)
            status["beats"].setdefault(bid, {})["state"] = "done"
            continue
        source = str(beat.get("source") or "still")
        prompt = build_beat_prompt(ep, beat, trigger=preset.get("trigger") or "")
        perrs = validate_beat_prompt(prompt, source=source, never=never)
        if perrs:
            raise EpisodeError(f"{bid}: {perrs}")
        (root / "logs" / f"{bid}.prompt.txt").write_text(prompt, encoding="utf-8")
        status["beats"][bid] = {"state": "running", "source": source, "started": _now()}
        save_status(root, status)
        try:
            if dry_run:
                first = _first_frame_for(beat, idx, ep, root, canvas, None)
                hue = (idx * 37) % 255
                synthetic_clip(raw_out.with_suffix(".part.mp4"), seconds=clip_seconds(ep), canvas=canvas, color=f"0x{hue:02x}{(120 + idx * 13) % 255:02x}{(200 - idx * 11) % 255:02x}", tone_hz=220 + idx * 40)
                result = {"videos": [str(raw_out.with_suffix(".part.mp4"))], "duration_s": clip_seconds(ep), "first": first}
            else:
                first = _first_frame_for(beat, idx, ep, root, canvas, comfy_input)
                result = render_beat_comfy(
                    source=source,
                    first_image=first,
                    prompt=prompt,
                    comfy_dir=comfy,
                    canvas=canvas,
                    durations=duration_ladder(ep),
                    preset=preset,
                    seed=seed + idx,
                    filename_prefix=f"video/h3_ep_{ep['slug']}_{bid}",
                    port=port,
                    object_info=object_info,
                    poster=poster,
                    waiter=waiter,
                )
            videos = [Path(v) for v in result.get("videos") or [] if Path(v).is_file()]
            if not videos:
                raise EpisodeError(f"{bid}: no mp4 produced")
            src = videos[-1]
            if src.resolve() != raw_out.resolve():
                shutil.copy2(src, raw_out)
                if src.name.endswith(".part.mp4"):
                    src.unlink(missing_ok=True)
            status["beats"][bid].update({"state": "done", "raw": str(raw_out), "duration_s": result.get("duration_s"), "finished": _now()})
        except Exception as e:
            status["beats"][bid].update({"state": "failed", "error": str(e)[:2000]})
            save_status(root, status)
            raise
        save_status(root, status)
    final = finish_episode(ep, root)
    status["final"] = str(final)
    save_status(root, status)
    print("FINAL", final)
    return final


def stills_trailer(ep: dict[str, Any], root: Path | str, *, seconds_per_beat: float = 2.5, out_name: str | None = None) -> Path:
    """No GPU: hold each clean still, add the same HUD/cards/stitch. A preview of the cut, not the motion."""
    root = Path(root)
    ensure_episode_tree(root)
    errs = validate_episode(ep, root=root)
    if errs:
        raise EpisodeError("episode invalid:\n- " + "\n- ".join(errs))
    canvas = canvas_for(ep)
    raw = root / "raw-stills"
    raw.mkdir(parents=True, exist_ok=True)
    prev_still: Path | None = None
    for beat in ep.get("beats") or []:
        still = beat.get("still")
        if still:
            prev_still = root / str(still)
        if prev_still is None:
            raise EpisodeError(f"{beat['id']}: stills preview needs a still on or before this beat")
        staged = root / "input" / f"{beat['id']}-preview.jpg"
        stage_still(prev_still, staged, canvas)
        still_clip(staged, raw / f"{beat['id']}.mp4", seconds=seconds_per_beat, canvas=canvas)
    return finish_episode(ep, root, raw_dir=raw, out_name=out_name or f"{ep['slug']}-stills-preview.mp4")


# ---------------------------------------------------------------- CLI

def _usage() -> str:
    return (
        "usage: h3_episode.py <check|prompts|dry-run|stills|finish> <episode.json|dir> [--out DIR] [--fresh] [--preset NAME]\n"
        "  check    validate + preflight, print prompts summary\n"
        "  prompts  write logs/<beat>.prompt.txt\n"
        "  dry-run  synthetic clips → HUD → stitch (no GPU)\n"
        "  stills   stills-only preview trailer (no GPU)\n"
        "  finish   HUD + cards + stitch over existing raw/*.mp4\n"
    )


def _resolve_paths(arg: str) -> tuple[Path, Path]:
    p = Path(arg)
    if p.is_dir():
        return p / "episode.json", p
    return p, p.parent


def main(argv: list[str] | None = None) -> int:
    args = list(argv if argv is not None else sys.argv[1:])
    if len(args) < 2:
        print(_usage())
        return 2
    cmd, target = args[0], args[1]
    opts = args[2:]
    out_dir = None
    fresh = "--fresh" in opts
    preset = None
    if "--out" in opts:
        out_dir = Path(opts[opts.index("--out") + 1])
    if "--preset" in opts:
        preset = opts[opts.index("--preset") + 1]
    ep_path, src_root = _resolve_paths(target)
    ep = load_episode(ep_path)
    work = out_dir or src_root
    if out_dir and out_dir.resolve() != src_root.resolve():
        ensure_episode_tree(out_dir)
        if not (out_dir / "episode.json").is_file():
            shutil.copy2(ep_path, out_dir / "episode.json")
        for rel in episode_assets(ep):
            dest = out_dir / rel
            if not dest.is_file() and (src_root / rel).is_file():
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_root / rel, dest)
    if cmd == "check":
        errs = preflight(ep, work)
        trig = PRESETS[str((ep.get("render") or {}).get("preset") or "fast")]["trigger"]
        for beat, prompt, _e in beat_prompts(ep, trigger=trig):
            print(f"{beat['id']:<22} {beat.get('source', 'still'):<5} {len(prompt):>5} chars  {((beat.get('hud') or {}).get('mission') or '')}")
        if errs:
            print("\n".join("ERR " + e for e in errs))
            return 1
        print("preflight ok:", ep.get("slug"), f"{len(ep.get('beats') or [])} beats", canvas_for(ep), "→", output_size_for(ep))
        return 0
    if cmd == "prompts":
        trig = PRESETS[str(preset or (ep.get("render") or {}).get("preset") or "fast")]["trigger"]
        for p in write_prompts(ep, Path(work) / "logs", trigger=trig):
            print(p)
        return 0
    if cmd == "dry-run":
        final = run_episode(ep, work, dry_run=True, fresh=fresh, preset_override=preset)
        print(final, f"{probe_duration(final):.2f}s")
        return 0
    if cmd == "stills":
        final = stills_trailer(ep, work)
        print(final, f"{probe_duration(final):.2f}s")
        return 0
    if cmd == "finish":
        final = finish_episode(ep, work)
        print(final, f"{probe_duration(final):.2f}s")
        return 0
    print(_usage())
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
