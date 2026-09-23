"""One-click MiniMax H3 episode trailers (game-style homage, original story).

`episode.json` is the only input. Every beat is one 10-second H3 clip
(I2V from a clean still, last-frame chain, or T2V), or a `ui` beat (a frozen
frame with a pause menu, no GPU). A beat may show only a `trim` window of its
clip, and may `reuse` a take from a sibling episode's raw/. Raw clips get a
HUD (or subtitles only in cutscenes), title / mission-failed / end cards, and
an audio crossfade stitch. Output lands in `episodes/<slug>/final/`.

What the first render taught (measured against the reference video):
- every prop was injected into every prompt → the firewood truck appeared in
  the noren shot, the bicycle shot and inside the barbershop. Props are now
  per beat and every prompt carries a one-location continuous-take lock.
- 10s shots vs the reference's ~4s cuts → `trim`, and short `ui` freezes.
- the joke is "ordinary footage, crime-game HUD" → `tone: mundane` rejects
  set-piece words; endings are `cards.fail` (ミッション失敗), not Complete.

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

import copy
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

try:
    from google.colab import userdata as _COLAB_USERDATA
except ImportError:
    _COLAB_USERDATA = None

from PIL import Image

from h3_hud import (
    HudError,
    card_clip,
    compose_beat,
    expected_stitch_duration,
    extract_frame,
    find_font,
    probe_duration,
    probe_video_size,
    render_complete_layer,
    render_end_card,
    render_fail_card,
    render_hud_layer,
    render_menu_layer,
    render_mission_layer,
    render_subtitle_layer,
    render_title_card,
    still_clip,
    stitch,
    synthetic_clip,
)
from h3_i2v_phone import BRANCH, REPO, TURBO_LORA_NAME, collect_output_videos, github_raw, newest_mp4, stage_image_into_input
from h3_i2v_runtime import (
    COMFY_DIR_DEFAULT,
    PORT,
    STOCK_FL2VA_UNET,
    comfy_free,
    detect_vram_gb,
    ensure_comfy,
    is_erotic_unet_name,
    pick_stock_fl2va,
    post_prompt,
    start_comfy,
    wait_prompt,
)
from h3_motion_graphics import (
    FORBIDDEN_IN_PROMPT,
    I2VA_HEADER,
    STUDIO_I2V_MINOR_RE,
    STUDIO_SAFETY_CLAUSE_RE,
    assert_i2va_graph,
    build_i2va_graph,
)
from h3_r2v_core import is_oom_error
from h3_episode_packs import (
    CAMERA_PACKS,
    COMBAT_MODES,
    CONNECT_MODES,
    DEFAULT_CAMERA_PACK,
    DEFAULT_CONNECT,
    END_CONNECT_MODES,
    FIGHT_STORIES,
    GIN_MODES,
    GIN_OVERLAY_KEYS,
    HOSPITAL_ENCOUNTERS,
    INVITE_POSE_MODES,
    INVITE_POSE_OVERLAY_KEYS,
    PRESET_CANON,
    PRESET_ALIASES,
    STORY_MODES,
    STORY_OVERLAY_KEYS,
    TOILET_MODES,
    TOILET_OVERLAY_KEYS,
    TSUNO_MODES,
    TSUNO_OVERLAY_KEYS,
    canonical_camera,
    canonical_combat,
    canonical_connect,
    canonical_end_connect,
    canonical_gin,
    canonical_invite_pose,
    canonical_preset,
    canonical_story,
    REI_ATTACK_MODES,
    REI_ATTACK_OVERLAY_KEYS,
    REI_BEAST_MODES,
    REI_BEAST_OVERLAY_KEYS,
    REI_ESCAPE_OVERLAY_KEYS,
    REI_FILTH_BODY,
    REI_FILTH_HINT,
    REI_FILTH_SEAT,
    REI_KISS_MODES,
    REI_KISS_OVERLAY_KEYS,
    REI_MAST_MODES,
    REI_MAST_OVERLAY_KEYS,
    REI_MOTH_MODES,
    REI_MOTH_OVERLAY_KEYS,
    REI_ORAL_MODES,
    REI_ORAL_OVERLAY_KEYS,
    REI_POSE_MODES,
    REI_POSE_OVERLAY_KEYS,
    REI_TOILET_MODES,
    REI_TOILET_OVERLAY_KEYS,
    canonical_toilet,
    canonical_tsuno,
    canonical_rei_attack,
    canonical_rei_beast,
    canonical_rei_kiss,
    canonical_rei_mast,
    canonical_rei_moth,
    canonical_rei_oral,
    canonical_rei_pose,
    canonical_rei_toilet,
    describe_run,
    expand_presets,
    parse_appear,
    parse_scenes,
    scenes_to_choices,
)
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
# GPU length tries the beat's clip first, then these shorter fallbacks (OOM).
DURATION_LADDER = (10.0, 8.0, 6.0)
MAX_BEATS = 40
# ui = a frozen frame of the previous beat with a pause-menu drawn on it (no GPU, no prompt)
SOURCES = ("still", "chain", "t2v", "ui")
STILL_AS = ("first", "last", "both")
# Last-frame lock: Picture 2 is the end of the clip, not a 10.00s timestamp (OOM may shorten 10→8→6).
STILL_LAST_HEADER = (
    "How the reference pictures align with the target video — "
    "Picture 1 (from Shot 1) aligns with the 0.00-second mark of the target video; "
    "Picture 2 (from Shot 10) aligns with the last frame of the target video."
)
# mundane = the reference's comedy: the footage stays ordinary, only the HUD text is a crime game.
# action = the old default (game physics allowed). tone is opt-in so existing episodes keep validating.
TONES = ("mundane", "action")
EPISODE_DIRS = ("stills", "input", "output", "raw", "hud", "hud/png", "final", "logs")
CARD_TITLE_S = 2.6
CARD_END_S = 3.2
CARD_SECONDS = (1.5, 6.0)
FAIL_TEXT_DEFAULT = "ミッション失敗"
# A beat may show only a window of its GPU clip (the reference cuts every ~4s; H3 drifts after ~5s).
# Meeting beats that start at 0.00 and trim to 4–10s render that GPU length (not a discarded 10s tail).
MIN_TRIM_S = 1.5
UI_SECONDS = (1.5, 5.0)
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
    "colab/h3_episode_packs.py",
    "colab/h3_episode_colab_main.py",
)

LORA_FILES = {
    "turbo4": TURBO_LORA_NAME,
    "turbo8": "minimax_h3_fl2v_turbo_8step_v1.0_768p_comfyui_bf16.safetensors",
    "larry": "minimax_h3_turbo_v4_step600_ema_comfy.safetensors",
    "cinema": "Minimax_H3_cinematic_DY.safetensors",
    "combat": "H3_Combat_V2.safetensors",
    "mystic": "MysticXXX_MMH3-V4.safetensors",
    # Story-pack oral act (h3-lora-studio catalog blowjob-h3).
    "blowjob": "MM-H3_Blowjob_v3.safetensors",
    # H3 futanari growth (Mistermango23 v5.1). Trained words: penis growth.
    "futatf": "MiniMax-H3_Futa_Transformations_LoRA_V5.1.safetensors",
    # H3 seated masturbation / orgasmic contractions.
    "mast": "H3_masturbate_orgasm_v1.4.safetensors",
    # H3 facial. Strength 1.0; lower falls back to a paint-bucket shot. Trigger CUMSH0T.
    "cumshot": "epic_cumshots-MiniMaxH3-ALPHA-CUMSH0T.safetensors",
    # Experimental H3 kiss. Author: I2V is weak; keep strength at 0.5. No trigger word.
    "kiss": "cxy_kiss_lora_h3_v01_step1750.safetensors",
    # az420 Side Riding Cowgirl MiniMaxH3 2. Side-view riding insertion. Do not stack with AIO.
    "sideride": "cowgirl-side-2-mh3-e50-az420.safetensors",
    # H3 penis helper. Trigger PENISLORA. Creampie stacks use 0.45.
    "penis": "PLORA_H3_V2-step00006300.safetensors",
    # H3 pussy detail. No trigger. Creampie stacks use 0.4.
    "synth": "SynthPussy_H3_closeups_v1-step00008300.safetensors",
    # Final Thrust V1. Vaginal internal finish only. 0.55 stays photoreal; higher goes 3D.
    "thrust": "H3_FinalThrust.safetensors",
    # Oral creampie only. Trigger CUMOUF. Not for vaginal, anal, or facial beats.
    "cumouf": "CUMOUF_oral_creampie_H3_v1.safetensors",
}
LORA_URLS = {
    "combat": "https://huggingface.co/JOKER141/MiniMax-H3-Combat-Base-V2/resolve/main/H3_Combat_V2.safetensors",
    "mystic": "https://huggingface.co/lynaNSFW/mysticxxx_MM_H3/resolve/main/MysticXXX_MMH3-V4.safetensors",
    "blowjob": "https://civitai.com/api/download/models/3285598?fileId=3169863",
    "futatf": "https://civitai.com/api/download/models/3212000?fileId=3093723",
    "mast": "https://civitai.com/api/download/models/3311155?fileId=3196458",
    "cumshot": "https://civitai.com/api/download/models/3202064?fileId=3083352",
    "kiss": "https://civitai.com/api/download/models/3208556?fileId=3090649",
    "sideride": "https://civitai.com/api/download/models/3327446?fileId=3213328",
    "penis": "https://civitai.com/api/download/models/3277703?fileId=3161784",
    "synth": "https://civitai.com/api/download/models/3204862?fileId=3086301",
    "thrust": "https://civitai.com/api/download/models/3269564?fileId=3157295",
    "cumouf": "https://civitai.com/api/download/models/3223411?fileId=3105419",
}
# Studio oral act is 0.8 (catalog default 0.85). Combat/mystic stay 1.0.
# Kiss author recommends 0.5. Cumshot author says below 1.0 loses the ropes.
# Side-ride matches studio cowgirl strength. Trigger avoids the word cowgirl (H3 pose-name ban).
LORA_STRENGTHS = {
    "blowjob": 0.8,
    "kiss": 0.5,
    "sideride": 0.8,
    # User stack for an internal finish. Catalog defaults are higher and read as 3D.
    "penis": 0.45,
    "synth": 0.4,
    "thrust": 0.55,
    "cumouf": 0.5,
}
BLOWJOB_TRIGGER = "bl0w_j0b"
SIDERIDE_TRIGGER = "side view riding sex, straddling the hips, facing the partner"
COMBAT_ROUTE_KEY = "combat_on"
STORY_ROUTE_KEYS = tuple(STORY_OVERLAY_KEYS.values())
INVITE_POSE_ROUTE_KEYS = tuple(INVITE_POSE_OVERLAY_KEYS.values())
TOILET_ROUTE_KEYS = tuple(TOILET_OVERLAY_KEYS.values())
GIN_ROUTE_KEYS = tuple(GIN_OVERLAY_KEYS.values())
TSUNO_ROUTE_KEYS = tuple(TSUNO_OVERLAY_KEYS.values())
REI_ESCAPE_ROUTE_KEYS = tuple(REI_ESCAPE_OVERLAY_KEYS)
ROUTE_OVERLAY_KEYS = (
    STORY_ROUTE_KEYS
    + INVITE_POSE_ROUTE_KEYS
    + TOILET_ROUTE_KEYS
    + GIN_ROUTE_KEYS
    + TSUNO_ROUTE_KEYS
    + REI_ESCAPE_ROUTE_KEYS
)
OPTIONAL_ENCOUNTERS = frozenset({"gin", "tsuno", "toilet"})
# Colab shows four 登場 checkboxes; clearing all four leaves nothing to render.
APPEAR_NONE_MSG = "appear: at least one encounter must stay on / 登場を4人とも外すと作る場面が無い。1人は残せ"
CONNECT_LOCKS = frozenset({"t2v", "cut", "off"})
# Ward acts are authored connect:t2v. Chain/landing on this slug follows the dropdown instead.
DROPDOWN_WINS_T2V_LOCK = frozenset({"hospital-exit-adult"})
BEAT_CONNECT_END = "end"
# UNet lanes. Stock episodes never load Eros Max. Erotic episodes never silently fall back to stock.
LANES = ("stock", "erotic")
STOCK_ONLY_SLUGS = frozenset({"kasumi-late-desk", "bandai-district", "bandai-district-short"})
EROTIC_SLUG_SUFFIX = "-adult"
EROTIC_MODELS_SUBDIR = "erotic"
# Drive copy (Naomiichi): MyDrive/minimax-h3-comfyui/models/diffusion_models/
EROS_MAX_UNET = "10Eros_Max_h3_TURBO-hybrid_beta5_int8.safetensors"
EROS_MAX_ALIASES = (
    EROS_MAX_UNET,
    "10Eros_Max_H3_FL2VA-INT8-ConvRot.safetensors",
)
# Combat LoRA on TURBO-hybrid OOMs A100 40GB. Opt-in needs High-Memory (VRAM 80GB or Colab High-RAM).
HIGH_MEM_VRAM_GIB = 70.0
HIGH_MEM_RAM_GIB = 60.0
CHECKPOINTS: dict[str, dict[str, Any]] = {
    "stock": {
        "file": STOCK_FL2VA_UNET,
        "erotic": False,
        "url": "",
        "min_bytes": 1_000_000,
    },
    "eros-max": {
        "file": EROS_MAX_UNET,
        "aliases": EROS_MAX_ALIASES,
        "erotic": True,
        "url": (
            "https://huggingface.co/TenStrip/10Eros-Max/resolve/main/"
            f"{EROS_MAX_UNET}"
        ),
        # ~21GB int8. A 5GB truncated file must not count as ready.
        "min_bytes": 15_000_000_000,
        "expected_bytes": 21_000_000_000,
    },
}
# Larry and LightX2V turbo never stack (h3-lora-studio rule). Cinema is not a preset (heavy/slow).
# combat is never a preset; fight beats opt in with extra_loras: ["combat"] and never stack with turbo.
# User-facing names: speed / balance / quality. fast/preview/daily are aliases (see h3_episode_packs.py).
PRESETS: dict[str, dict[str, Any]] = expand_presets()
# Combat LoRA author samples at 20 / res_multistep+simple or euler+beta. Larry daily is euler+simple 8
# and muddies the hit. Fight beats bump to 12 euler+beta (16 cap). 20 OOMs with Larry+combat at 10s.
COMBAT_STEPS = 12
BEAT_STEPS_RANGE = (4, 16)
SAMPLERS = ("euler", "res_multistep")
SCHEDULERS = ("simple", "beta")
COMBAT_SAMPLER = "euler"
COMBAT_SCHEDULER = "beta"

SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{1,40}$")
BEAT_ID_RE = re.compile(r"^[0-9]{2}-[a-z0-9-]{1,32}$")
REUSE_RE = re.compile(r"^([a-z0-9][a-z0-9-]{1,40})/([0-9]{2}-[a-z0-9-]{1,32})$")
ADULT_AGE_MIN = 21
# "16y" / "16-year-old" in a lock. Do not match 21-year-old.
CAST_UNDERAGE_RE = re.compile(
    r"(?i)(?<!\d)(?:1[0-9]|[1-9])y\b|(?<!\d)(?:1[0-9]|[1-9])[\s_-]*years?"
)
KANJI_RE = re.compile(r"[\u4e00-\u9fff]")
KANA_RE = re.compile(r"[\u3040-\u30ff\uff66-\uff9f]")
CJK_RE = re.compile(r"[\u3040-\u30ff\u4e00-\u9fff\uff66-\uff9f]")
# H3 invents English / Hangul / Cyrillic when quotes are empty or mixed. Spoken audio is kana in 「」 only.
NON_JP_SPEECH_RE = re.compile(r"[A-Za-z\u0400-\u04FF\uac00-\ud7af\u3131-\u318e]")
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
# Words that make H3 stage a set piece. A mundane episode may not write them at all, not even negated:
# H3 materializes what is named ("no explosion" still draws smoke), so the fix is to leave them out.
ACTION_TOKENS_RE = re.compile(
    r"\b(explosions?|explod\w*|fireballs?|blasts?|erupt\w*|uppercuts?|punch\w*|kick\w*|fights?|fighting|brawls?|"
    r"ragdolls?|tumbl\w*|hurl\w*|crash\w*|gunshots?|weapons?|leaps?|leaping|jumps?|jumping|somersault\w*|"
    r"flips?|flying|chases?|chasing|speeding|double exposure)\b",
    re.I,
)
DEFAULT_MUSIC = "Low pulsing synth bass with a sparse taiko hit at the start; holds under the whole clip."
VIOLENCE_CLAUSE = (
    "Exaggerated video-game physics at real-time cutscene speed: adults sit down hard like ragdolls, "
    "objects slide, comedic tone. Nobody is hurt, no blood, no injuries, no children anywhere in frame."
)
# Named "slow motion" even negated still gets drawn. Physics beats stay at gameplay pace.
REALTIME_CLAUSE = (
    "Playback stays at real-time third-person game speed: the contact, the fold, and the sit-down "
    "finish inside this one shot at brisk walking-and-hit pace. Snappy. Motion starts at frame one."
)
GAMEPLAY_PACE_CLAUSE = (
    "Playback stays at real-time third-person game speed. Snappy. Motion starts at frame one. "
    "Do not invent a walk cycle. Feet stay planted unless the action names running or walking."
)
PLANTED_PACE_CLAUSE = (
    "Playback stays at real-time third-person game speed. Snappy. Motion starts at frame one. "
    "Only hips, hands, and mouths move. The feet do not take a step. The pair does not travel."
)
GAME_THIRD_PERSON_CLAUSE = (
    "Always a third-person gameplay camera: the adults stay fully visible in frame including feet."
)
PLANTED_CLAUSE = (
    "Feet planted on this same floor spot. Hip, hand, and mouth motion stay on this mark. "
    "Nobody walks, nobody runs, nobody moonwalks, nobody strides, nobody relocates, "
    "nobody slides down the corridor. A hip thrust is in place, not a step. "
    "Normal adult human height, nobody is giant. The background does not scroll. The camera holds."
)
# Nelson lifts Aya's feet. "Feet planted" and the word walk (even negated) make H3 invent a walk cycle.
NELSON_HOLD_RE = re.compile(
    r"feet stay in the air|heels sit beside|held up, both thighs|forearms already hold both thighs",
    re.I,
)
NELSON_PLANTED_CLAUSE = (
    "The pair stays on this same floor spot. The partner's feet stay on the same linoleum marks. "
    "Aya's feet stay in the air beside the partner's hips. Only hips and arms move. "
    "A hip thrust is in place. The camera holds. The background does not scroll. "
    "Normal adult human height, nobody is giant."
)
PLANTED_WALK_TAIL_RE = re.compile(
    r"\s*(?:Then\s+)?(?:Aya|She) STANDS and WALKS RIGHT[^.]*\."
    r"|\s*Then Aya WALKS RIGHT[^.]*\."
    r"|\s*Aya WALKS RIGHT along the corridor[^.]*\."
    r"|\s*The other adult FADES COMPLETELY OUT OF FRAME while Aya walks[^.]*\.",
    re.I,
)
GONE_FROM_FRAME_RE = re.compile(
    r"(?:Miki|Rei|Kana|Shino|Gin|Tsuno|The [^.]+?) (?:is|are) gone from frame one\.?\s*",
    re.I,
)
FADE_ONLY_AYA_RE = re.compile(r"Only Aya is in the corridor\.?\s*", re.I)
FADE_NOBODY_ELSE_RE = re.compile(r"Nobody else in frame\.?\s*", re.I)
RUN_CLAUSE = (
    "Runner shot only: she sprints left to right. The camera tracks horizontally on a straight line. "
    "Mouth closed, tongue fully inside the mouth, not an orgasm face."
)
SLOWMO_TOKENS_RE = re.compile(
    r"\b(slow[\s-]?mo(?:tion)?s?|slo-?mos?|bullet[\s-]?time|time[\s-]?dilation)\b",
    re.I,
)
# Positive phrasing on purpose (H3 obeys "add" better than "stop"). This is the per-shot location lock the
# first render lacked: the barbershop turned into a street with a truck within 1.5s.
CONTINUITY_CLAUSE = (
    "One continuous take: the whole clip stays inside this one location with the same people in frame "
    "from the first frame to the last, and nothing new enters the frame."
)
MUNDANE_CLAUSE = "Calm everyday pace, ordinary small movements, an unremarkable errand."


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


def beat_clip_seconds(ep: dict[str, Any], beat: dict[str, Any] | None = None) -> float:
    """GPU length for this beat.

    If the shown window starts at 0.00 and is already a legal 4–10s clip, render that
    length. Mid-clip trims still generate the episode clip so the window exists.
    """
    top = clip_seconds(ep)
    if not beat or str(beat.get("source") or "") == "ui":
        return top
    trim = beat.get("trim")
    if not isinstance(trim, dict):
        return top
    try:
        start = float(trim.get("start") or 0.0)
        seconds = float(trim.get("seconds") or 0.0)
    except (TypeError, ValueError):
        return top
    if start <= 0.0 and seconds >= 4.0:
        return min(seconds, top)
    return top


def duration_ladder(ep: dict[str, Any], beat: dict[str, Any] | None = None) -> list[float]:
    top = beat_clip_seconds(ep, beat)
    out = [top]
    for d in DURATION_LADDER:
        if d < top and d not in out:
            out.append(d)
    return out


def episode_tone(ep: dict[str, Any]) -> str:
    return str(ep.get("tone") or "action")


def episode_lane(ep: dict[str, Any]) -> str:
    raw = str((ep.get("render") or {}).get("lane") or "stock").strip().lower()
    return raw if raw in LANES else "stock"


def comfy_vram_for_lane(lane: str) -> str:
    """Erotic UNet uses Comfy default memory. `--normalvram` is not a current CLI flag."""
    return "default" if lane == "erotic" else "highvram"


def detect_ram_gb() -> float:
    try:
        return float(os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES")) / 1024 ** 3
    except (AttributeError, OSError, ValueError):
        return 0.0


def is_high_mem(*, vram_gb: float = 0.0, ram_gb: float = 0.0) -> bool:
    """Colab High-RAM (~80GB system) or an 80GB-class GPU."""
    return float(vram_gb) >= HIGH_MEM_VRAM_GIB or float(ram_gb) >= HIGH_MEM_RAM_GIB


def episode_combat(ep: dict[str, Any], override: str | None = None) -> str:
    """off / on. Empty keeps auto: stock UNet may load Combat, TURBO-hybrid does not."""
    raw = str(override if override not in (None, "") else (ep.get("render") or {}).get("combat") or "").strip()
    if not raw:
        return ""
    name = canonical_combat(raw)
    if name not in COMBAT_MODES:
        raise EpisodeError(f"render.combat must be one of {list(COMBAT_MODES)}")
    return name


def episode_story(ep: dict[str, Any], override: str | None = None) -> str:
    """accept / invite / evade / fight_win / fight_lose. Empty means the JSON body as-is."""
    raw = str(override if override not in (None, "") else (ep.get("render") or {}).get("story") or "").strip()
    if not raw:
        return ""
    name = canonical_story(raw)
    if name not in STORY_MODES:
        raise EpisodeError(f"render.story must be one of {list(STORY_MODES)}")
    return name


def episode_invite_pose(ep: dict[str, Any], override: str | None = None) -> str:
    """all_fours / m_open / ride. Empty keeps the recommended 四つん這い."""
    raw = str(override if override not in (None, "") else (ep.get("render") or {}).get("invite_pose") or "").strip()
    if not raw:
        return ""
    name = canonical_invite_pose(raw)
    if name not in INVITE_POSE_MODES:
        raise EpisodeError(f"render.invite_pose must be one of {list(INVITE_POSE_MODES)}")
    return name


def episode_toilet(ep: dict[str, Any], override: str | None = None) -> str:
    """off / pee / masturbate / tentacle. Empty keeps off."""
    raw = str(override if override not in (None, "") else (ep.get("render") or {}).get("toilet") or "").strip()
    if not raw:
        return ""
    name = canonical_toilet(raw)
    if name not in TOILET_MODES:
        raise EpisodeError(f"render.toilet must be one of {list(TOILET_MODES)}")
    return name


def episode_gin(ep: dict[str, Any], override: str | None = None) -> str:
    """off / taken / fuck / invite_doggy. Empty keeps off."""
    raw = str(override if override not in (None, "") else (ep.get("render") or {}).get("gin") or "").strip()
    if not raw:
        return ""
    name = canonical_gin(raw)
    if name not in GIN_MODES:
        raise EpisodeError(f"render.gin must be one of {list(GIN_MODES)}")
    return name


def episode_tsuno(ep: dict[str, Any], override: str | None = None) -> str:
    """off / accept_stand / invite_stand. Empty keeps off."""
    raw = str(override if override not in (None, "") else (ep.get("render") or {}).get("tsuno") or "").strip()
    if not raw:
        return ""
    name = canonical_tsuno(raw)
    if name not in TSUNO_MODES:
        raise EpisodeError(f"render.tsuno must be one of {list(TSUNO_MODES)}")
    return name


def _rei_choice(
    ep: dict[str, Any],
    *,
    field: str,
    override: str | None,
    canon: Callable[[str], str],
    modes: dict[str, dict[str, Any]],
) -> str:
    raw = str(override if override not in (None, "") else (ep.get("render") or {}).get(field) or "").strip()
    if not raw:
        return ""
    name = canon(raw)
    if name not in modes:
        raise EpisodeError(f"render.{field} must be one of {list(modes)}")
    return name


def episode_rei_mast(ep: dict[str, Any], override: str | None = None) -> str:
    return _rei_choice(ep, field="rei_mast", override=override, canon=canonical_rei_mast, modes=REI_MAST_MODES)


def episode_rei_toilet(ep: dict[str, Any], override: str | None = None) -> str:
    return _rei_choice(ep, field="rei_toilet", override=override, canon=canonical_rei_toilet, modes=REI_TOILET_MODES)


def episode_rei_beast(ep: dict[str, Any], override: str | None = None) -> str:
    return _rei_choice(ep, field="rei_beast", override=override, canon=canonical_rei_beast, modes=REI_BEAST_MODES)


def episode_rei_moth(ep: dict[str, Any], override: str | None = None) -> str:
    return _rei_choice(ep, field="rei_moth", override=override, canon=canonical_rei_moth, modes=REI_MOTH_MODES)


def episode_rei_attack(ep: dict[str, Any], override: str | None = None) -> str:
    return _rei_choice(ep, field="rei_attack", override=override, canon=canonical_rei_attack, modes=REI_ATTACK_MODES)


def episode_rei_kiss(ep: dict[str, Any], override: str | None = None) -> str:
    return _rei_choice(ep, field="rei_kiss", override=override, canon=canonical_rei_kiss, modes=REI_KISS_MODES)


def episode_rei_oral(ep: dict[str, Any], override: str | None = None) -> str:
    return _rei_choice(ep, field="rei_oral", override=override, canon=canonical_rei_oral, modes=REI_ORAL_MODES)


def episode_rei_pose(ep: dict[str, Any], override: str | None = None) -> str:
    return _rei_choice(ep, field="rei_pose", override=override, canon=canonical_rei_pose, modes=REI_POSE_MODES)


def episode_appear(ep: dict[str, Any], override: str | dict[str, Any] | None = None) -> dict[str, bool]:
    """Which hospital encounters to keep. Packs without encounter tags ignore this."""
    render = ep.get("render") or {}
    raw: str | dict[str, Any] | None
    if override not in (None, ""):
        raw = override
    elif "appear" in render:
        raw = render.get("appear")
    else:
        raw = None
    shown = parse_appear(raw)
    unknown = [name for name in shown if name not in HOSPITAL_ENCOUNTERS]
    if unknown:
        raise EpisodeError(f"render.appear unknown encounter {unknown}")
    return shown


def episode_scenes(
    ep: dict[str, Any],
    override: str | dict[str, Any] | None = None,
) -> dict[str, tuple[str | None, str | None]]:
    """Per-encounter (story, pose). Missing / inherit = (None, None). Fight stories ignore this."""
    render = ep.get("render") or {}
    if override not in (None, ""):
        raw = override
    elif "scenes" in render:
        raw = render.get("scenes")
    else:
        raw = None
    try:
        return parse_scenes(raw)
    except ValueError as e:
        raise EpisodeError(str(e)) from e


def resolve_encounter_stories(
    ep: dict[str, Any],
    *,
    story: str | None = None,
    scenes: str | dict[str, Any] | None = None,
) -> dict[str, str]:
    """Story per hospital encounter. Colab 5番 fight stories pin every scene."""
    global_story = episode_story(ep, story) or "accept"
    parsed = episode_scenes(ep, scenes)
    out: dict[str, str] = {}
    for name in HOSPITAL_ENCOUNTERS:
        local, _pose = parsed[name]
        if global_story in FIGHT_STORIES or local in FIGHT_STORIES:
            out[name] = global_story
        else:
            out[name] = local or global_story
    return out


def resolve_encounter_poses(
    ep: dict[str, Any],
    *,
    pose: str | None = None,
    scenes: str | dict[str, Any] | None = None,
) -> dict[str, str]:
    """Invite pose per hospital encounter. Local pose, else Colab 6番."""
    default_pose = episode_invite_pose(ep, pose) or "all_fours"
    parsed = episode_scenes(ep, scenes)
    out: dict[str, str] = {}
    for name in HOSPITAL_ENCOUNTERS:
        _story, local_pose = parsed[name]
        out[name] = local_pose or default_pose
    return out


def ending_story(ep: dict[str, Any]) -> str:
    """Complete/fail follows the last remaining hospital encounter, not skipped ones."""
    global_story = episode_story(ep) or "accept"
    if global_story in FIGHT_STORIES:
        return global_story
    last = ""
    for beat in ep.get("beats") or []:
        if isinstance(beat, dict) and beat.get("encounter") in HOSPITAL_ENCOUNTERS:
            last = str(beat.get("encounter") or "")
    if not last:
        return global_story
    return resolve_encounter_stories(ep).get(last, global_story)


def combat_lora_allowed(*, unet: str, combat: str, high_mem: bool) -> tuple[bool, str]:
    """Whether Combat V2 may stack. LightX2V turbo never. Hybrid needs High-Memory opt-in."""
    hybrid = is_turbo_hybrid_unet(unet)
    if combat == "off":
        return False, "combat LoRA skipped (off)"
    if combat == "on":
        if not high_mem:
            return False, "combat LoRA skipped (High-Memory only; this runtime is not)"
        return True, "combat LoRA on (High-Memory)"
    if hybrid:
        return False, "combat LoRA skipped (never with LightX2V turbo or TURBO-hybrid UNet)"
    return True, ""


def episode_voice(ep: dict[str, Any]) -> str:
    """Spoken audio lock. erotic lane defaults to japanese: H3 otherwise invents English."""
    raw = str((ep.get("render") or {}).get("voice") or "").strip().lower()
    if raw == "off":
        return ""
    if raw == "japanese" or episode_lane(ep) == "erotic":
        return "japanese"
    return ""


def episode_checkpoint(ep: dict[str, Any]) -> str:
    raw = str((ep.get("render") or {}).get("checkpoint") or "stock").strip().lower()
    return raw if raw in CHECKPOINTS else "stock"


def erotic_checkpoint_path(models_root: Path | str, spec: dict[str, Any]) -> Path:
    return Path(models_root) / EROTIC_MODELS_SUBDIR / str(spec["file"])


_WALK_SKIP_DIRS = frozenset(
    {
        "episodes",
        "inbox",
        "queued",
        "running",
        "done",
        "failed",
        "output",
        "input",
        "raw",
        "stills",
        "hud",
        "final",
        "logs",
        "loras",
        "vae",
        "text_encoders",
        "clip",
        "clip_vision",
        "__pycache__",
        "node_modules",
    }
)
_CACHE_WALK_DIRS = frozenset({"hub", "snapshots", "blobs", "refs", "fl2va", "models"})
_WEIGHT_SKIP_SUFFIXES = (".tmp", ".crdownload", ".aria2", ".json", ".txt", ".md", ".lock", ".jpg", ".png", ".mp4")


def _checkpoint_ready(path: Path, min_bytes: int) -> bool:
    try:
        return path.is_file() and path.stat().st_size >= min_bytes
    except OSError:
        return False


def is_erotic_weight_path(path: Path | str) -> bool:
    """True for Eros Max files, including HuggingFace hub paths that only bake the id into the folder."""
    p = Path(path)
    name = p.name
    if name.endswith(".part"):
        name = name[: -len(".part")]
    hay = p.as_posix().replace("\\", "/")
    if hay.endswith(".part"):
        hay = hay[: -len(".part")]
    return is_erotic_unet_name(name) or is_erotic_unet_name(hay)


def _erotic_search_plan(models_root: Path) -> list[tuple[Path, int, bool]]:
    """(folder, extra_depth, cache_filter). Unit tests pass a tmp root not named models, so Drive/HF are skipped."""
    plan: list[tuple[Path, int, bool]] = [
        (models_root / EROTIC_MODELS_SUBDIR, 1, False),
        (models_root / "diffusion_models", 1, False),
        (models_root / "checkpoints", 1, False),
        (models_root / "unet", 1, False),
        (models_root, 1, False),
    ]
    if models_root.name != "models":
        return plan
    drive = models_root.parent
    plan.extend(
        [
            (drive, 1, False),
            (drive / "cache" / "hf", 6, True),
            (drive / "cache" / "huggingface", 6, True),
            (drive / "cache" / "hf" / "hub", 6, True),
        ]
    )
    posix = models_root.as_posix().replace("\\", "/").lower()
    if "/drive/" in posix or posix.startswith("/content/drive/"):
        md = Path("/content/drive/MyDrive")
        plan.extend(
            [
                (md, 0, False),
                (md / "Downloads", 2, False),
                (md / "models", 2, False),
                (md / "ComfyUI" / "models", 3, False),
            ]
        )
        try:
            if md.is_dir():
                for path in md.iterdir():
                    if not path.is_dir() or path.is_symlink() or path.name.startswith("."):
                        continue
                    if is_erotic_unet_name(path.name) or "eros" in path.name.lower():
                        plan.append((path, 4, False))
        except OSError:
            pass
    comfy = Path(os.environ.get("H3_COMFY_DIR") or COMFY_DIR_DEFAULT)
    plan.extend(
        [
            (comfy / "models" / "diffusion_models", 1, False),
            (comfy / "models" / "diffusion_models.local_bak", 1, False),
            (comfy / "models", 2, False),
        ]
    )
    return plan


def _walk_weight_files(
    folder: Path,
    *,
    depth: int,
    cache_filter: bool = False,
    inside_eros: bool = False,
) -> list[Path]:
    out: list[Path] = []
    if depth < 0:
        return out
    try:
        if not folder.is_dir() or folder.is_symlink():
            return out
        entries = list(folder.iterdir())
    except OSError:
        return out
    for path in entries:
        name = path.name
        if name.startswith("."):
            continue
        try:
            if path.is_dir():
                if path.is_symlink() or depth <= 0:
                    continue
                low = name.lower()
                if low in _WALK_SKIP_DIRS:
                    continue
                eros_dir = is_erotic_unet_name(name) or "eros" in low
                if cache_filter and not inside_eros and low not in _CACHE_WALK_DIRS and not eros_dir:
                    continue
                out.extend(
                    _walk_weight_files(
                        path,
                        depth=depth - 1,
                        cache_filter=cache_filter,
                        inside_eros=inside_eros or eros_dir,
                    )
                )
            elif path.is_file():
                out.append(path)
        except OSError:
            continue
    return out


def _best_erotic_weight(paths: list[Path], want: str, spec: dict[str, Any]) -> Path:
    expected = int(spec.get("expected_bytes") or 0)
    uniq: list[Path] = []
    seen: set[Path] = set()
    for path in paths:
        try:
            key = path.resolve()
        except OSError:
            key = path
        if key in seen:
            continue
        seen.add(key)
        uniq.append(path)

    def rank(path: Path) -> tuple[int, int, int]:
        name = path.name[: -len(".part")] if path.name.endswith(".part") else path.name
        exact = 0 if name == want else 1
        try:
            size = path.stat().st_size
        except OSError:
            size = 0
        delta = abs(size - expected) if expected else 0
        return (exact, delta, -size)

    return sorted(uniq, key=rank)[0]


def is_turbo_hybrid_unet(name: str) -> bool:
    low = str(name or "").lower()
    return "turbo-hybrid" in low or "turbo_hybrid" in low


def locate_erotic_checkpoint(models_root: Path | str, spec: dict[str, Any] | None = None) -> Path | None:
    """Find a ready Eros Max on Drive / HF cache / Comfy. Incomplete copies under min_bytes are ignored."""
    spec = spec or CHECKPOINTS["eros-max"]
    min_bytes = int(spec.get("min_bytes") or 15_000_000_000)
    want = str(spec.get("file") or EROS_MAX_UNET)
    aliases = tuple(spec.get("aliases") or (want,))
    candidates: list[Path] = []
    explicit = (os.environ.get("H3_EROS_MAX") or "").strip()
    if explicit:
        extra = Path(explicit)
        if extra.is_file():
            candidates.append(extra)
        elif extra.is_dir():
            candidates.extend(_walk_weight_files(extra, depth=4, cache_filter=False))
    for folder, depth, cache_filter in _erotic_search_plan(Path(models_root)):
        for alias in aliases:
            exact = folder / alias
            if exact.is_file() or exact.is_symlink():
                candidates.append(exact)
            part = exact.with_name(exact.name + ".part")
            if part.is_file():
                candidates.append(part)
        candidates.extend(_walk_weight_files(folder, depth=depth, cache_filter=cache_filter))
    ready: list[Path] = []
    parts: list[Path] = []
    for path in candidates:
        name = path.name
        low = name.lower()
        if any(low.endswith(suf) for suf in _WEIGHT_SKIP_SUFFIXES):
            continue
        if not is_erotic_weight_path(path) and name != want and name != want + ".part" and name not in aliases and name not in {a + ".part" for a in aliases}:
            continue
        if not _checkpoint_ready(path, min_bytes):
            continue
        if name.endswith(".part"):
            parts.append(path)
        else:
            ready.append(path)
    if ready:
        return _best_erotic_weight(ready, want, spec)
    if parts:
        return _best_erotic_weight(parts, want, spec)
    return None


def _adopt_erotic_checkpoint(src: Path, dest: Path, min_bytes: int) -> Path:
    """Point models/erotic/<canonical> at a Drive copy. Never copy 22GB."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        src_r = src.resolve()
    except OSError:
        src_r = src
    if dest.exists() or dest.is_symlink():
        try:
            if dest.resolve() == src_r:
                return dest
        except OSError:
            pass
        dest_size = 0
        try:
            dest_size = dest.stat().st_size if dest.is_file() else 0
        except OSError:
            dest_size = 0
        if dest.is_file() and not dest.is_symlink() and dest_size >= min_bytes:
            return dest
        if dest.is_symlink() or dest.is_file():
            dest.unlink()
    canonical_part = dest.with_name(dest.name + ".part")
    try:
        same_part = src_r == canonical_part.resolve() if canonical_part.exists() else False
    except OSError:
        same_part = False
    if src.name == dest.name + ".part" and src.parent == dest.parent or same_part:
        src.replace(dest)
        return dest
    try:
        dest.symlink_to(src_r)
        return dest
    except OSError as e:
        print("eros symlink failed", dest, "->", src_r, e)
        return src


def _checkpoint_errors(ep: dict[str, Any]) -> list[str]:
    """Stock slugs cannot load Eros Max. *-adult slugs must declare the erotic lane."""
    errs: list[str] = []
    render = ep.get("render") or {}
    slug = str(ep.get("slug") or "")
    lane_raw = str(render.get("lane") or "stock").strip().lower()
    ckpt_raw = str(render.get("checkpoint") or "stock").strip().lower()
    if lane_raw not in LANES:
        errs.append(f"render.lane must be one of {list(LANES)}")
    if ckpt_raw not in CHECKPOINTS:
        errs.append(f"render.checkpoint must be one of {list(CHECKPOINTS)}")
        return errs
    spec = CHECKPOINTS[ckpt_raw]
    if spec["erotic"] and lane_raw != "erotic":
        errs.append("render.checkpoint eros-max is erotic-only; set render.lane erotic")
    if slug in STOCK_ONLY_SLUGS and lane_raw == "erotic":
        errs.append(f"{slug} is a stock episode; render.lane erotic is forbidden")
    if slug in STOCK_ONLY_SLUGS and spec["erotic"]:
        errs.append(f"{slug} is a stock episode; render.checkpoint eros-max is forbidden")
    if slug.endswith(EROTIC_SLUG_SUFFIX) and lane_raw != "erotic":
        errs.append(f"{slug} must set render.lane erotic (stock UNet is not implied by the slug)")
    if slug.endswith(EROTIC_SLUG_SUFFIX) and ckpt_raw != "eros-max":
        errs.append(f"{slug} must set render.checkpoint eros-max (no silent stock fallback)")
    return errs


def beat_source(beat: dict[str, Any]) -> str:
    return str(beat.get("source") or "still")


def is_ui_beat(beat: dict[str, Any]) -> bool:
    return beat_source(beat) == "ui"


def beat_still_as(beat: dict[str, Any]) -> str:
    """Where the authored still sits: opening frame (default), landing frame, or both."""
    raw = str(beat.get("still_as") or "first").strip() or "first"
    return raw


def uses_last_still(beat: dict[str, Any]) -> bool:
    return bool(beat.get("still")) and beat_still_as(beat) in ("last", "both")


def beat_renders(beat: dict[str, Any]) -> bool:
    """True when this beat can go to the GPU (a ui beat never does; a reuse beat only as fallback with a still)."""
    source = beat_source(beat)
    if source == "ui":
        return False
    if source == "still":
        return bool(beat.get("still"))
    return True


def episode_camera_pack(ep: dict[str, Any], override: str | None = None) -> str:
    """Pack name for this run. T2V episodes default to side2d so each clip can change camera."""
    raw = str(override if override not in (None, "") else (ep.get("render") or {}).get("camera_pack") or "").strip()
    if raw:
        return canonical_camera(raw)
    if any(isinstance(b, dict) and beat_source(b) == "t2v" for b in (ep.get("beats") or [])):
        return DEFAULT_CAMERA_PACK
    return ""


def episode_connect(ep: dict[str, Any], override: str | None = None) -> str:
    """t2v / chain / landing. Empty keeps authored source/still_as."""
    raw = str(override if override not in (None, "") else (ep.get("render") or {}).get("connect") or "").strip()
    if not raw:
        return ""
    return canonical_connect(raw)


def episode_end_connect(ep: dict[str, Any], override: str | None = None) -> str:
    """t2v / chain / follow. Empty keeps the recommended vanish cut."""
    raw = str(override if override not in (None, "") else (ep.get("render") or {}).get("end_connect") or "").strip()
    if not raw:
        return ""
    name = canonical_end_connect(raw)
    if name not in END_CONNECT_MODES:
        raise EpisodeError(f"render.end_connect must be one of {list(END_CONNECT_MODES)}")
    return name


def connect_rotates_camera(ep: dict[str, Any], override: str | None = None) -> bool:
    name = episode_connect(ep, override)
    if not name:
        return True
    spec = CONNECT_MODES.get(name) or {}
    return bool(spec.get("rotate_camera", True))


def _slide_trim_to_last(beat: dict[str, Any], clip_s: float) -> None:
    """Landing stills sit on the last generated frame; the shown window must include it."""
    trim = beat.get("trim")
    if not isinstance(trim, dict):
        seconds = min(5.0, float(clip_s))
        beat["trim"] = {"start": round(max(0.0, clip_s - seconds), 3), "seconds": seconds}
        return
    start = float(trim.get("start") or 0.0)
    seconds = float(trim.get("seconds") or 0.0) or float(clip_s)
    if start + seconds >= float(clip_s) - 0.05:
        return
    seconds = min(max(seconds, MIN_TRIM_S), float(clip_s))
    beat["trim"] = {"start": round(max(0.0, float(clip_s) - seconds), 3), "seconds": seconds}


def _connect_lock_holds(ep: dict[str, Any], beat: dict[str, Any], mode: str) -> bool:
    """Authored t2v/cut/off force T2V. Hospital chain/landing lets the dropdown win over t2v."""
    locked = str(beat.get("connect") or "").strip().lower()
    if locked not in CONNECT_LOCKS:
        return False
    if (
        locked == "t2v"
        and mode in ("chain", "landing")
        and str(ep.get("slug") or "") in DROPDOWN_WINS_T2V_LOCK
    ):
        return False
    return True


def apply_connect_mode(ep: dict[str, Any], override: str | None = None) -> dict[str, Any]:
    """Rewrite GPU beat source/still_as for a connect mode. UI and reuse beats stay put.

    t2v: every GPU beat is T2V including the first (prompt-correctable, cameras may change).
    chain: first GPU beat is T2V; later I2V from the previous clip's last frame.
    landing: first GPU still, later I2V onto the authored still as Picture 2.
    Hospital connect:t2v yields to chain and landing. cut/off stays T2V. A new person outside a -spot beat is still T2V. Spot beats stay I2V.
    """
    name = episode_connect(ep, override)
    if not name:
        return ep
    if name not in CONNECT_MODES:
        raise EpisodeError(f"render.connect must be one of {list(CONNECT_MODES)} (add a mode in h3_episode_packs.py)")
    out = copy.deepcopy(ep)
    render = dict(out.get("render") or {})
    render["connect"] = name
    out["render"] = render
    gpu_seen = 0
    for beat in out.get("beats") or []:
        if not isinstance(beat, dict) or is_ui_beat(beat):
            continue
        if beat.get("reuse"):
            gpu_seen += 1
            continue
        if _connect_lock_holds(out, beat, name):
            beat["source"] = "t2v"
            beat.pop("still_as", None)
            gpu_seen += 1
            continue
        if name == "t2v":
            beat["source"] = "t2v"
            beat.pop("still_as", None)
        elif name == "chain":
            if gpu_seen == 0:
                beat["source"] = "t2v"
                beat.pop("still_as", None)
            else:
                beat["source"] = "chain"
                beat.pop("still_as", None)
        else:  # landing
            if gpu_seen == 0:
                if beat.get("still"):
                    beat["source"] = "still"
                    beat["still_as"] = "first"
                else:
                    beat["source"] = "t2v"
                    beat.pop("still_as", None)
            elif beat.get("still"):
                beat["source"] = "still"
                beat["still_as"] = "last"
                _slide_trim_to_last(beat, beat_clip_seconds(out, beat))
            else:
                beat["source"] = "chain"
                beat.pop("still_as", None)
        gpu_seen += 1
    return out


def _has_combat_overlays(ep: dict[str, Any]) -> bool:
    return any(isinstance(b, dict) and isinstance(b.get(COMBAT_ROUTE_KEY), dict) for b in (ep.get("beats") or []))


def _has_story_overlays(ep: dict[str, Any]) -> bool:
    return any(
        isinstance(b, dict) and any(_is_overlay_payload(b.get(key)) for key in STORY_ROUTE_KEYS)
        for b in (ep.get("beats") or [])
    )


def _is_overlay_payload(value: Any) -> bool:
    if isinstance(value, dict):
        return True
    return isinstance(value, list) and any(isinstance(item, dict) for item in value)


def _expand_overlay(body: dict[str, Any], chosen: Any) -> list[dict[str, Any]]:
    """Dict overlay merges into one beat. List overlay replaces that beat with many."""
    if isinstance(chosen, list):
        out: list[dict[str, Any]] = []
        for item in chosen:
            if isinstance(item, dict):
                out.append(_merge_route_overlay(body, item))
        return out or [body]
    if isinstance(chosen, dict):
        return [_merge_route_overlay(body, chosen)]
    return [body]


def _honor_beat_connect(ep: dict[str, Any]) -> dict[str, Any]:
    """Authored t2v/cut/off stay T2V. Hospital chain/landing leaves t2v locks to the dropdown."""
    mode = episode_connect(ep)
    for beat in ep.get("beats") or []:
        if not isinstance(beat, dict) or is_ui_beat(beat):
            continue
        if _connect_lock_holds(ep, beat, mode):
            beat["source"] = "t2v"
            beat.pop("still_as", None)
    return ep


def is_end_connect_beat(beat: dict[str, Any]) -> bool:
    return str(beat.get("connect") or "").strip().lower() == BEAT_CONNECT_END


def _wire_runtime_connect(beat: dict[str, Any], *, chain: bool) -> None:
    if beat.get("reuse") or is_ui_beat(beat):
        return
    beat["source"] = "chain" if chain else "t2v"
    beat.pop("still_as", None)


def apply_end_connect(ep: dict[str, Any], *, end_connect: str | None = None) -> dict[str, Any]:
    """Wire scene-end walks (connect: end) from the runtime dropdown.

    t2v: vanish cut, next scene independent (recommended).
    chain: I2V the walk and the following non-ui beat from the previous last frame.
    follow: leave whatever 1番 already wired.
    """
    out = copy.deepcopy(ep)
    render = dict(out.get("render") or {})
    if end_connect not in (None, ""):
        render["end_connect"] = canonical_end_connect(end_connect) or end_connect
        out["render"] = render
    key = episode_end_connect(out) or "t2v"
    if key not in END_CONNECT_MODES:
        raise EpisodeError(f"render.end_connect must be one of {list(END_CONNECT_MODES)}")
    render = dict(out.get("render") or {})
    render["end_connect"] = key
    out["render"] = render
    if key == "follow":
        return out
    beats = list(out.get("beats") or [])
    chain = key == "chain"
    gpu_seen = 0
    follow_next = False
    wired: list[Any] = []
    for beat in beats:
        if not isinstance(beat, dict):
            wired.append(beat)
            continue
        item = dict(beat)
        if is_ui_beat(item):
            wired.append(item)
            continue
        if follow_next:
            if not item.get("reuse"):
                _wire_runtime_connect(item, chain=True)
            follow_next = False
            gpu_seen += 1
            wired.append(item)
            continue
        if is_end_connect_beat(item):
            _wire_runtime_connect(item, chain=bool(chain and gpu_seen))
            follow_next = bool(chain)
            gpu_seen += 1
            wired.append(item)
            continue
        gpu_seen += 1
        wired.append(item)
    out["beats"] = wired
    return out


def _cast_english_names(ep: dict[str, Any], ids: list[str]) -> str:
    cast = ep.get("cast") or {}
    names: list[str] = []
    for cid in ids:
        row = cast.get(cid) or {}
        names.append(str(row.get("name_en") or cid).strip() or cid)
    if not names:
        return "The previous partner"
    if len(names) == 1:
        return names[0] if names[0].lower().startswith("the ") else "The " + names[0]
    return ", ".join(names[:-1]) + " and " + names[-1]


def keep_chain_cast(ep: dict[str, Any]) -> dict[str, Any]:
    """I2V starts on the previous last frame. A missing body cannot be invented;
    an extra body cannot be deleted by saying 'only X in frame'.

    Grow (new person): T2V, so the newcomer is actually generated.
    A -spot encounter stays chain: the newcomer walks into the previous frame.
    Shrink (someone left): keep them in this beat's cast, fade them in the
    action, and KEEP the chain so 05→06 is a fade instead of a jump.
    Grow and shrink together: T2V, except a -spot, which stays chain
    and does not keep the previous extra person.
    """
    out = copy.deepcopy(ep)
    prev: set[str] = set()
    beats: list[Any] = []
    for beat in out.get("beats") or []:
        if not isinstance(beat, dict) or is_ui_beat(beat) or not beat_renders(beat):
            beats.append(beat)
            continue
        item = dict(beat)
        intended = [str(c) for c in (item.get("cast") or [])]
        intended_set = set(intended)
        dropped = prev - intended_set
        added = intended_set - prev
        if beat_source(item) == "chain" and not item.get("reuse"):
            spot = str(item.get("id") or "").endswith("-spot")
            if spot:
                item.pop("fade_cast", None)
            elif added:
                item["source"] = "t2v"
                item.pop("still_as", None)
                item.pop("fade_cast", None)
            elif dropped:
                fade_ids = sorted(dropped)
                item["fade_cast"] = fade_ids
                item["cast"] = list(dict.fromkeys(intended + fade_ids))
                action = str(item.get("action") or "").strip()
                fade = (
                    f"{_cast_english_names(out, fade_ids)} completely "
                    f"{'fades' if len(fade_ids) == 1 else 'fade'} out of frame in the first two seconds, "
                    "no walk-away, no residual limb, wing, tail, tooth, or horn. "
                )
                action = GONE_FROM_FRAME_RE.sub("", action)
                action = FADE_ONLY_AYA_RE.sub("", action)
                action = FADE_NOBODY_ELSE_RE.sub("", action)
                if "fade out of frame" not in action.lower():
                    item["action"] = (fade + action).strip()
                else:
                    item["action"] = action.strip()
        prev = intended_set
        beats.append(item)
    out["beats"] = beats
    return out


def _merge_route_overlay(beat: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    """Replace route fields. menu/hud deep-merge so the command window can retarget."""
    out = dict(beat)
    for key, value in overlay.items():
        if key in ("menu", "hud") and isinstance(value, dict) and isinstance(out.get(key), dict):
            merged = dict(out[key])
            merged.update(value)
            out[key] = merged
        else:
            out[key] = value
    return out


def _merge_combat_overlay(beat: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    return _merge_route_overlay(beat, overlay)


def apply_combat_route(ep: dict[str, Any], *, combat: str | None = None) -> dict[str, Any]:
    """One story per Combat switch. On = fight prompts. Off/empty = sex prompts, no fights.

    Beat JSON keeps the off-route as the body and optional combat_on overlays.
    This strips the overlay so GPU prompts never mix both plots.
    """
    out = copy.deepcopy(ep)
    render = dict(out.get("render") or {})
    if combat not in (None, ""):
        render["combat"] = canonical_combat(combat) or combat
        out["render"] = render
    on = episode_combat(out) == "on"
    beats: list[Any] = []
    for beat in out.get("beats") or []:
        if not isinstance(beat, dict):
            beats.append(beat)
            continue
        body = dict(beat)
        overlay = body.pop(COMBAT_ROUTE_KEY, None)
        if on and isinstance(overlay, dict):
            body = _merge_combat_overlay(body, overlay)
        beats.append(body)
    out["beats"] = beats
    return out


def _apply_story_ending(ep: dict[str, Any], spec: dict[str, Any]) -> dict[str, Any]:
    """Flip last-beat complete and cards.fail so Colab story choice can succeed or fail."""
    out = ep
    beats = [b for b in (out.get("beats") or []) if isinstance(b, dict)]
    if beats:
        last = dict(beats[-1])
        hud = dict(last.get("hud") or {})
        hud["complete"] = bool(spec.get("complete"))
        last["hud"] = hud
        beats[-1] = last
        all_beats = list(out.get("beats") or [])
        # Replace the last dict beat in the original list.
        for i in range(len(all_beats) - 1, -1, -1):
            if isinstance(all_beats[i], dict):
                all_beats[i] = last
                break
        out["beats"] = all_beats
    cards = dict(out.get("cards") or {})
    if spec.get("complete"):
        cards.pop("fail", None)
    else:
        fail = dict(cards.get("fail") or {})
        fail["text"] = str(fail.get("text") or "ミッション失敗")
        fail["reason"] = str(spec.get("fail_reason") or fail.get("reason") or "失敗")
        fail["seconds"] = float(fail.get("seconds") or 2.8)
        fail["image"] = str(fail.get("image") or "last-frame")
        cards["fail"] = fail
    out["cards"] = cards
    return out


def apply_story_route(
    ep: dict[str, Any],
    *,
    story: str | None = None,
    scenes: str | dict[str, Any] | None = None,
) -> dict[str, Any]:
    """One future per Colab 構成, or per hospital encounter when シーンごと is set.

    Body = ○受け入れる. on_* overlays hold the other four.
    Episodes without on_* keys are unchanged (霞東の 4 番はそのまま).
    Fight stories (5番) pin every scene and render.combat so Combat LoRA is allowed on 06/10.
    """
    out = copy.deepcopy(ep)
    if not _has_story_overlays(out):
        return out
    render = dict(out.get("render") or {})
    if story not in (None, ""):
        render["story"] = canonical_story(story) or story
        out["render"] = render
    if scenes not in (None, ""):
        render["scenes"] = scenes_to_choices(episode_scenes(out, scenes))
        out["render"] = render
    key = episode_story(out) or "accept"
    spec = STORY_MODES.get(key) or STORY_MODES["accept"]
    stories = resolve_encounter_stories(out)
    beats: list[Any] = []
    for beat in out.get("beats") or []:
        if not isinstance(beat, dict):
            beats.append(beat)
            continue
        enc = str(beat.get("encounter") or "")
        local = stories.get(enc, key) if enc in HOSPITAL_ENCOUNTERS else key
        overlay_field = STORY_OVERLAY_KEYS.get(local)
        chosen = beat.get(overlay_field) if overlay_field else None
        body = _pop_overlay_keys(beat, STORY_ROUTE_KEYS)
        body.pop(COMBAT_ROUTE_KEY, None)
        beats.extend(_expand_overlay(body, chosen))
    out["beats"] = beats
    render = dict(out.get("render") or {})
    render["story"] = key
    render["combat"] = spec.get("combat") or "off"
    out["render"] = render
    return out


def _pop_overlay_keys(beat: dict[str, Any], keys: tuple[str, ...]) -> dict[str, Any]:
    out = dict(beat)
    for key in keys:
        out.pop(key, None)
    return out


def apply_invite_pose(ep: dict[str, Any], *, pose: str | None = None) -> dict[str, Any]:
    """Merge invite_pose_* overlays when that encounter is □誘う. Other stories just drop the keys."""
    out = copy.deepcopy(ep)
    render = dict(out.get("render") or {})
    if pose not in (None, ""):
        render["invite_pose"] = canonical_invite_pose(pose) or pose
        out["render"] = render
    key = episode_invite_pose(out) or "all_fours"
    global_story = episode_story(out) or "accept"
    stories = resolve_encounter_stories(out)
    poses = resolve_encounter_poses(out)
    beats: list[Any] = []
    for beat in out.get("beats") or []:
        if not isinstance(beat, dict):
            beats.append(beat)
            continue
        enc = str(beat.get("encounter") or "")
        local_story = stories.get(enc, global_story) if enc in HOSPITAL_ENCOUNTERS else global_story
        local_pose = poses.get(enc, key) if enc in HOSPITAL_ENCOUNTERS else key
        field = INVITE_POSE_OVERLAY_KEYS.get(local_pose) if local_story == "invite" else None
        chosen = beat.get(field) if field else None
        body = _pop_overlay_keys(beat, INVITE_POSE_ROUTE_KEYS)
        beats.extend(_expand_overlay(body, chosen))
    out["beats"] = beats
    render = dict(out.get("render") or {})
    render["invite_pose"] = key
    out["render"] = render
    return out


def apply_toilet_route(ep: dict[str, Any], *, toilet: str | None = None) -> dict[str, Any]:
    """Replace the みき→れい walk with a toilet stall when Colab 7 is not 行かない."""
    out = copy.deepcopy(ep)
    render = dict(out.get("render") or {})
    if toilet not in (None, ""):
        render["toilet"] = canonical_toilet(toilet) or toilet
        out["render"] = render
    key = episode_toilet(out) or "off"
    field = TOILET_OVERLAY_KEYS.get(key)
    beats: list[Any] = []
    for beat in out.get("beats") or []:
        if not isinstance(beat, dict):
            beats.append(beat)
            continue
        body = _pop_overlay_keys(beat, TOILET_ROUTE_KEYS)
        chosen = beat.get(field) if field else None
        if _is_overlay_payload(chosen):
            expanded = _expand_overlay(body, chosen)
            for item in expanded:
                item["encounter"] = "toilet"
                item.pop("on_invite", None)
            beats.extend(expanded)
        else:
            beats.append(body)
    out["beats"] = beats
    render = dict(out.get("render") or {})
    render["toilet"] = key
    out["render"] = render
    return out


def apply_optional_events(
    ep: dict[str, Any],
    *,
    gin: str | None = None,
    tsuno: str | None = None,
) -> dict[str, Any]:
    """Insert Colab 8/9 ashen-infected beats. Off drops the marker beats."""
    out = copy.deepcopy(ep)
    render = dict(out.get("render") or {})
    if gin not in (None, ""):
        render["gin"] = canonical_gin(gin) or gin
        out["render"] = render
    if tsuno not in (None, ""):
        render["tsuno"] = canonical_tsuno(tsuno) or tsuno
        out["render"] = render
    gin_key = episode_gin(out) or "off"
    tsuno_key = episode_tsuno(out) or "off"
    gin_field = GIN_OVERLAY_KEYS.get(gin_key)
    tsuno_field = TSUNO_OVERLAY_KEYS.get(tsuno_key)
    beats: list[Any] = []
    for beat in out.get("beats") or []:
        if not isinstance(beat, dict):
            beats.append(beat)
            continue
        enc = str(beat.get("encounter") or "")
        if enc == "gin":
            chosen = beat.get(gin_field) if gin_field else None
            body = _pop_overlay_keys(beat, GIN_ROUTE_KEYS + TSUNO_ROUTE_KEYS)
            if not _is_overlay_payload(chosen):
                continue
            beats.extend(_expand_overlay(body, chosen))
            continue
        if enc == "tsuno":
            chosen = beat.get(tsuno_field) if tsuno_field else None
            body = _pop_overlay_keys(beat, GIN_ROUTE_KEYS + TSUNO_ROUTE_KEYS)
            if not _is_overlay_payload(chosen):
                continue
            beats.extend(_expand_overlay(body, chosen))
            continue
        beats.append(_pop_overlay_keys(beat, GIN_ROUTE_KEYS + TSUNO_ROUTE_KEYS))
    out["beats"] = beats
    render = dict(out.get("render") or {})
    render["gin"] = gin_key
    render["tsuno"] = tsuno_key
    out["render"] = render
    return out


# Invite lust finale. Only the last partner on an invite ending. Middle walks stay.
FINALE_LOOK: dict[str, str] = {
    "miki": (
        "Miki stays a slim adult with a short brown bob, vivid purple skin from face to the erect 22cm shaft, "
        "hollow empty dark eye sockets, open red lacerations and torn gashes across the face, neck, breasts, belly, back, "
        "arms, hands, thighs, knees, feet, hips, groin and the 22cm shaft, visible sweat beads on the intact purple skin "
        "between the open gashes, grimy dirty stains and wet peeling rotting patches on that skin, "
        "the 22cm shaft the same vivid purple as the hips not pale-tan flesh."
    ),
    "rei": (
        "Rei stays a slim feminine adult with long brown permed hair, vivid purple skin, vacant wide-open tired eyes, "
        "the LEFT half of her face and body stays readable as wet rotting raw red flesh on the left eye, left cheek, "
        "left breast, left arm and left hip, the right half stays vivid purple, thick extra-viscous dark-brown filthy "
        "sludge from hair to the erect 24cm shaft to her feet, open wounds across the torso, hips, groin and the 24cm shaft, "
        "the 24cm shaft the same vivid purple as the hips not pale-tan flesh."
    ),
    "kana": (
        "Kana stays a slim adult with long black hair, vivid purple skin, hollow empty dark eye sockets, visible fangs, "
        "dry scratch marks on the skin including the hips and the erect 20cm shaft, grimy dirty extra-viscous filthy slime "
        "covering her whole body including the 20cm shaft, wet peeling rotting patches on the shaft, "
        "the 20cm shaft the same vivid purple as the hips not pale-tan flesh."
    ),
    "shino": (
        "Shino stays an extremely tall elongated adult with long straight dark hair, very pale gray-white skin, "
        "vacant wide staring monster eyes, a long forked reptile tongue, long arms with hands past mid-thigh, "
        "grimy dirty stains from hair to the erect 30cm shaft to her feet, wet peeling rotting patches on the hips, "
        "groin and the 30cm shaft, the 30cm shaft the same pale gray-white as the hips not pale-tan flesh."
    ),
    "tsuno": (
        "Tsuno stays a slim feminine adult with long dark hair, ashen gray skin, a still-beautiful face whose LEFT half "
        "is cracked and decaying, one large single eye in the center of the face, two small dark horns at the hairline, "
        "each hand has exactly four long fingers, long decaying clawed feet, erect 24cm ashen-gray shaft with wet peeling "
        "rotting patches and grimy dirty stains on the hips, groin and the shaft, the shaft stays ashen gray not pale-tan flesh."
    ),
}
FINALE_NAME = {key: key[:1].upper() + key[1:] for key in FINALE_LOOK}
_FINALE_CLIMAX_OLD = (
    "Aya climaxes: wrecked pleasured orgasm face, body trembling with pleasure, drool dripping from the open mouth."
)
_FINALE_CLIMAX_NEW = (
    "Aya climaxes: wrecked pleasured orgasm face, eyes start to roll up until the whites show, "
    "tongue hanging out, thick saliva dripping, body trembling with pleasure."
)
_FINALE_FACE = (
    "Aya's tongue hangs out of her open mouth. Thick saliva drips from the tongue. "
    "Her face is ecstatic and lost in pleasure. "
)
_FINALE_PULL_RES = (
    re.compile(
        r" Then (?:Miki|Rei|Kana|Shino|Tsuno)'s hips PULL BACK so the shaft SLIDES OUT\. WHITE goo DRIPS DOWN\."
    ),
    re.compile(
        r" Then (?:Miki|Rei|Kana|Shino|Tsuno)'s hips draw back and the shaft leaves the anus\. The tip stays in the crack of the ass\."
    ),
    re.compile(
        r" They hold that join\. Then (?:Miki|Rei|Kana|Shino|Tsuno)'s hips draw back and the shaft leaves the (?:pussy|anus)\."
        r"(?: (?:Miki|Rei|Kana|Shino|Tsuno) lowers one of Aya's feet to the linoleum, then the other foot\."
        r" They remain standing still on this same linoleum mark\.)?"
    ),
)
_FINALE_LIMP = (
    " Aya ends flat on her back, fully limp, on this same linoleum spot. "
    "Her head rests on the linoleum. Her back rests on the linoleum. Her waist rests on the linoleum. "
    "Both knees lose their strength and fall outward. The inner thighs rest on the linoleum. "
    "The heels sit right beside the buttocks. The soles face each other. "
    "The legs stay open and spread on the linoleum. "
    "Her arms fall limp, one beside the head and one along her side. "
    "Her hands stay on the linoleum. Her legs rest on the linoleum with no hands on them. "
    "She stays still. Her chest rises with hard breaths."
)


def _finale_partner(beat: dict[str, Any]) -> str:
    for name in beat.get("cast") or []:
        key = str(name).strip().lower()
        if key in FINALE_LOOK:
            return key
    return ""


def _aya_was_filled(action: str) -> bool:
    low = action.lower()
    if "finishes inside gin" in low or "gin's pussy" in low:
        return False
    return any(
        phrase in low
        for phrase in (
            "finishes inside aya",
            "finishes inside the pussy",
            "finishes inside the anus",
            "fills the anus",
            "leaks around the base",
            "fills the pussy",
        )
    )


def _finale_pose(action: str) -> str:
    low = action.lower()
    if "held up" in low or ("forearms" in low and "anus" in low):
        return "nelson"
    if "sitting on" in low or "straddling" in low or "squat" in low:
        return "ride"
    if "palms on the wall" in low or "palms planted on the wall" in low:
        return "stand"
    if "all fours" in low or "palms and knees" in low:
        return "all_fours"
    return "m_open"


def _finale_anal(action: str) -> bool:
    low = action.lower()
    anal = "fills the anus" in low or "inside the anus" in low or "leaves the anus" in low
    vaginal = "fills the pussy" in low or "inside the pussy" in low or "leaks around the base" in low
    if anal and vaginal:
        return low.rfind("anus") > low.rfind("pussy")
    return anal


def _finale_drop_action(name: str, pose: str, anal: bool) -> str:
    who = FINALE_NAME[name]
    hole = "anus" if anal else "pussy"
    if pose == "all_fours":
        intro = (
            f"Already joined at the BASE on this same linoleum spot. Aya is on her palms and knees, the shaft inside the {hole}. "
            f"Her arms give out. Her chest DROPS onto the linoleum. She ROLLS onto her back. "
            f"The shaft SLIDES OUT as she rolls. {who} stays kneeling beside her."
        )
    elif pose == "ride":
        intro = (
            f"Aya is sitting on {who}'s hips on this same linoleum spot, shaft at the BASE inside the {hole}, torso leaned forward. "
            f"Her strength leaves the squat. She TIPS BACKWARD off the hips and FALLS onto her back on the linoleum beside {who}. "
            f"The shaft SLIDES OUT as she falls. {who} stays on her back."
        )
    elif pose == "stand":
        intro = (
            f"Aya stands with both palms on the wall on this same linoleum spot, hips pressed to {who}, the shaft at the BASE inside the {hole}. "
            f"Her knees buckle. She SLIDES down the wall and FALLS onto her back on the linoleum. "
            f"The shaft SLIDES OUT as she falls. {who} stoops beside her."
        )
    elif pose == "nelson":
        intro = (
            f"Aya is held up on this same linoleum spot, both thighs in {who}'s forearms, feet in the air, the shaft inside the {hole}. "
            f"Her body goes limp in {who}'s arms. {who} LOWERS Aya until her back meets the linoleum, then lets both thighs go. "
            f"The shaft SLIDES OUT as she is lowered. {who} stays beside her."
        )
    else:
        intro = (
            f"Already on her back on this same linoleum spot, knees pulled up, the shaft still at the BASE inside the {hole}. "
            f"Aya's strength leaves her. The knees FALL outward until the inner thighs meet the linoleum. "
            f"The heels slide down to sit beside the buttocks. The shaft SLIDES OUT as the hips go slack. "
            f"{who} stays kneeling beside her."
        )
    goo = f" Thick WHITE goo overflows from the {hole} and runs onto the linoleum."
    return (
        intro
        + _FINALE_LIMP
        + goo
        + " "
        + FINALE_LOOK[name]
        + " They do not cross the threshold. They stay in the building. "
        "Both stay fully nude. Brisk real-time. Consensual adult game beat"
    )


def _finale_kiss_action(name: str, pose: str, anal: bool) -> str:
    who = FINALE_NAME[name]
    hole = "anus" if anal else "pussy"
    if pose == "ride":
        approach = f"{who}'s torso COMES UP from the linoleum into a kneel beside Aya's head. "
    elif name == "shino":
        approach = "Shino is already stooping beside Aya's head so her head stays under the tubes. "
    else:
        approach = f"{who} is already beside Aya's head. "
    if name == "shino":
        tongue = (
            "Shino's long forked reptile tongue pushes into Aya's mouth and licks around the lips and the corners of the mouth. "
        )
    else:
        tongue = f"{who}'s tongue pushes into Aya's mouth and licks around the lips and the corners of the mouth. "
    return (
        "Aya is already flat on her back on this same linoleum spot, fully limp. "
        "Her head rests on the linoleum. Her back and her waist rest on the linoleum. "
        "Both knees are fallen outward. The inner thighs rest on the linoleum. "
        "The heels sit right beside the buttocks. The soles face each other. "
        "The legs stay open and spread on the linoleum. "
        "Her arms lie limp, one beside the head and one along her side. "
        "She stays still. Her chest rises with hard breaths. "
        f"Thick WHITE goo is on the {hole} and the linoleum. "
        + FINALE_LOOK[name]
        + " "
        + approach
        + f"{who}'s face LOWERS onto Aya's mouth. "
        "They stay joined in a deep wet french kiss, a tongue kiss. "
        + tongue
        + "Aya's tongue meets it, still hanging limp. "
        "They stay on this same linoleum spot. They do not cross the threshold. They stay in the building. "
        "Both stay fully nude. Last frame: mouths joined, the tongue still in Aya's mouth, Aya still flat and still. "
        "Brisk real-time. Consensual adult game beat"
    )


def _patch_finale_sex(beats: list[dict[str, Any]], peak_i: int) -> None:
    peak = beats[peak_i]
    action = str(peak.get("action") or "")
    if _FINALE_CLIMAX_OLD in action:
        action = action.replace(_FINALE_CLIMAX_OLD, _FINALE_CLIMAX_NEW, 1)
    for pattern in _FINALE_PULL_RES:
        action = pattern.sub("", action)
    partner = _finale_partner(peak)
    look = FINALE_LOOK.get(partner, "")
    if look and look not in action:
        action = action.replace("Both stay fully nude.", look + " Both stay fully nude.", 1)
    peak["action"] = action
    if peak_i <= 0:
        return
    hilt = beats[peak_i - 1]
    hilt_action = str(hilt.get("action") or "")
    low = hilt_action.lower()
    if "inside the mouth" in low or "tongue hangs out" in low or "last frame:" not in low:
        return
    if not any(phrase in low for phrase in ("shaft at the base inside", "shaft inside the pussy", "shaft inside the anus", "the shaft inside")):
        return
    hilt["action"] = hilt_action.replace("Last frame:", _FINALE_FACE + "Last frame:", 1)


def apply_invite_lust_finale(ep: dict[str, Any]) -> dict[str, Any]:
    """When an invite run ends, the last penetrator stays for the collapse and the kiss.

    Earlier invite scenes still walk on to the next adult. The partner's body, shaft,
    wounds and grime stay that person's, not the next name in the cast list.
    """
    if str(ep.get("slug") or "") != "hospital-exit-adult":
        return ep
    if ending_story(ep) != "invite":
        return ep
    beats = [b for b in (ep.get("beats") or []) if isinstance(b, dict)]
    if not beats:
        return ep
    last = beats[-1]
    last_id = str(last.get("id") or "")
    if last_id.endswith("-kiss") or not last_id.endswith("-walk"):
        return ep
    peak_i = -1
    for i in range(len(beats) - 2, -1, -1):
        bid = str(beats[i].get("id") or "")
        if bid.endswith("-peak"):
            peak_i = i
            break
        if bid.endswith("-walk"):
            break
    if peak_i < 0 or not _aya_was_filled(str(beats[peak_i].get("action") or "")):
        return ep
    partner = _finale_partner(beats[peak_i])
    if not partner:
        return ep
    action = str(beats[peak_i].get("action") or "")
    pose = _finale_pose(action)
    anal = _finale_anal(action) or pose == "nelson"
    _patch_finale_sex(beats, peak_i)
    base = last_id[: -len("-walk")]
    hud = dict(last.get("hud") or {})
    hud["complete"] = False
    shared = {
        "source": "t2v",
        "connect": "t2v",
        "camera_pack": "none",
        "loco": "planted",
        "still": "",
        "trim": {"start": 0, "seconds": 8.0},
        "cast": ["aya", partner],
        "trigger": "",
        "encounter": last.get("encounter") or beats[peak_i].get("encounter") or partner,
        "place": beats[peak_i].get("place") or last.get("place") or "",
        "music": last.get("music") or "Bass holds",
        "hud": hud,
    }
    drop = {
        **shared,
        "id": f"{base}-drop",
        "extra_loras": [],
        "camera": (
            "PROFILE side-on. Floor runs LEFT to RIGHT. Both adults full body including feet. "
            f"Aya falling onto her back, then flat and limp with her legs spread, {FINALE_NAME[partner]} beside her. The camera holds."
        ),
        "action": _finale_drop_action(partner, pose, anal),
        "voices": [{"who": "aya", "line": "はぁっ"}, {"who": partner, "line": "くっ"}],
        "sfx": "A body settling on linoleum, thick goo, HVAC",
    }
    kiss = {
        **shared,
        "id": f"{base}-kiss",
        "hud": dict(hud),
        "extra_loras": [["kiss", 0.5]],
        "camera": (
            "PROFILE side-on. Floor runs LEFT to RIGHT. Both adults full body including feet. "
            f"Aya flat on her back, limp, legs spread. {FINALE_NAME[partner]} beside her, tongue in Aya's mouth. The camera holds."
        ),
        "action": _finale_kiss_action(partner, pose, anal),
        "voices": [{"who": "aya", "line": "んっ"}, {"who": partner, "line": "んっ"}],
        "sfx": "A wet tongue kiss, HVAC",
    }
    ep["beats"] = beats[:-1] + [drop, kiss]
    return ep


def apply_appear_route(ep: dict[str, Any], *, appear: str | dict[str, Any] | None = None) -> dict[str, Any]:
    """Drop tagged encounters the Colab checkboxes turned off. Toilet beats stay if 7 is on."""
    out = copy.deepcopy(ep)
    shown = episode_appear(out, appear)
    tagged = any(isinstance(b, dict) and b.get("encounter") for b in (out.get("beats") or []))
    if not tagged:
        render = dict(out.get("render") or {})
        render["appear"] = shown
        out["render"] = render
        return out
    skipped = {name for name, on in shown.items() if not on}
    if tagged and not any(shown.get(name) for name in HOSPITAL_ENCOUNTERS):
        raise EpisodeError(APPEAR_NONE_MSG)
    beats: list[Any] = []
    for beat in out.get("beats") or []:
        if not isinstance(beat, dict):
            beats.append(beat)
            continue
        enc = str(beat.get("encounter") or "")
        if enc and enc not in OPTIONAL_ENCOUNTERS and enc in skipped:
            continue
        beats.append(beat)
    if not beats:
        raise EpisodeError(APPEAR_NONE_MSG)
    # Two ui beats in a row / ui first are invalid; drop a leading ui after a skip.
    cleaned: list[Any] = []
    for beat in beats:
        if not isinstance(beat, dict):
            cleaned.append(beat)
            continue
        if is_ui_beat(beat) and not cleaned:
            continue
        if is_ui_beat(beat) and cleaned and isinstance(cleaned[-1], dict) and is_ui_beat(cleaned[-1]):
            continue
        cleaned.append(beat)
    if not cleaned:
        raise EpisodeError("appear: at least one footage beat must stay")
    out["beats"] = cleaned
    render = dict(out.get("render") or {})
    render["appear"] = shown
    out["render"] = render
    out = apply_invite_lust_finale(out)
    spec = STORY_MODES.get(ending_story(out)) or STORY_MODES["accept"]
    return _apply_story_ending(out, spec)


def _has_rei_escape_overlays(ep: dict[str, Any]) -> bool:
    return any(
        isinstance(b, dict)
        and (
            str(b.get("rei_slot") or "").strip()
            or any(_is_overlay_payload(b.get(key)) for key in REI_ESCAPE_ROUTE_KEYS)
        )
        for b in (ep.get("beats") or [])
    )


def _inject_rei_filth(beat: dict[str, Any], filth: str | None) -> dict[str, Any]:
    if filth not in ("seat", "body"):
        return beat
    out = dict(beat)
    clause = REI_FILTH_BODY if filth == "body" else REI_FILTH_SEAT
    action = str(out.get("action") or "").strip()
    if clause not in action:
        out["action"] = (action + " " + clause).strip()
    hud = dict(out.get("hud") or {})
    hud["hint"] = REI_FILTH_HINT[filth]
    out["hud"] = hud
    return out


def apply_rei_escape_route(
    ep: dict[str, Any],
    *,
    mast: str | None = None,
    toilet: str | None = None,
    beast: str | None = None,
    moth: str | None = None,
    attack: str | None = None,
    kiss: str | None = None,
    oral: str | None = None,
    pose: str | None = None,
) -> dict[str, Any]:
    """Resolve futanari-rei-escape overlays. Episodes without rei_* keys are unchanged."""
    out = copy.deepcopy(ep)
    if not _has_rei_escape_overlays(out):
        return out
    render = dict(out.get("render") or {})
    if mast not in (None, ""):
        render["rei_mast"] = canonical_rei_mast(mast) or mast
    if toilet not in (None, ""):
        render["rei_toilet"] = canonical_rei_toilet(toilet) or toilet
    if beast not in (None, ""):
        render["rei_beast"] = canonical_rei_beast(beast) or beast
    if moth not in (None, ""):
        render["rei_moth"] = canonical_rei_moth(moth) or moth
    if attack not in (None, ""):
        render["rei_attack"] = canonical_rei_attack(attack) or attack
    if kiss not in (None, ""):
        render["rei_kiss"] = canonical_rei_kiss(kiss) or kiss
    if oral not in (None, ""):
        render["rei_oral"] = canonical_rei_oral(oral) or oral
    if pose not in (None, ""):
        render["rei_pose"] = canonical_rei_pose(pose) or pose
    out["render"] = render
    mast_key = episode_rei_mast(out) or "skip"
    toilet_key = episode_rei_toilet(out) or "ta"
    beast_key = episode_rei_beast(out) or "accept"
    moth_key = episode_rei_moth(out) or "tail"
    attack_key = episode_rei_attack(out) or "rei"
    kiss_key = episode_rei_kiss(out) or "off"
    oral_key = episode_rei_oral(out) or "skip"
    pose_key = episode_rei_pose(out) or "fours"
    if mast_key not in REI_MAST_MODES:
        raise EpisodeError(f"render.rei_mast must be one of {list(REI_MAST_MODES)}")
    if toilet_key not in REI_TOILET_MODES:
        raise EpisodeError(f"render.rei_toilet must be one of {list(REI_TOILET_MODES)}")
    if beast_key not in REI_BEAST_MODES:
        raise EpisodeError(f"render.rei_beast must be one of {list(REI_BEAST_MODES)}")
    if moth_key not in REI_MOTH_MODES:
        raise EpisodeError(f"render.rei_moth must be one of {list(REI_MOTH_MODES)}")
    if attack_key not in REI_ATTACK_MODES:
        raise EpisodeError(f"render.rei_attack must be one of {list(REI_ATTACK_MODES)}")
    if kiss_key not in REI_KISS_MODES:
        raise EpisodeError(f"render.rei_kiss must be one of {list(REI_KISS_MODES)}")
    if oral_key not in REI_ORAL_MODES:
        raise EpisodeError(f"render.rei_oral must be one of {list(REI_ORAL_MODES)}")
    if pose_key not in REI_POSE_MODES:
        raise EpisodeError(f"render.rei_pose must be one of {list(REI_POSE_MODES)}")
    attack_prefix = ""
    if attack_key == "her":
        attack_prefix = (
            "The succubus initiates: she pounces, torn wings wrap Rei, claws on Rei's hips. "
        )
    else:
        attack_prefix = (
            "Rei initiates: she grabs the succubus by the waist and presses her to the meat wall. "
        )
    filth: str | None = None
    beats: list[Any] = []
    for beat in out.get("beats") or []:
        if not isinstance(beat, dict):
            beats.append(beat)
            continue
        slot = str(beat.get("rei_slot") or "").strip()
        body = _pop_overlay_keys(beat, REI_ESCAPE_ROUTE_KEYS)
        body.pop("rei_slot", None)
        chosen: Any = None
        skip = False
        if slot == "mast":
            field = REI_MAST_OVERLAY_KEYS.get(mast_key)
            chosen = beat.get(field) if field else None
            skip = not _is_overlay_payload(chosen)
        elif slot == "toilet":
            field = REI_TOILET_OVERLAY_KEYS.get(toilet_key)
            chosen = beat.get(field) if field else None
            skip = not _is_overlay_payload(chosen)
        elif slot == "beast":
            field = REI_BEAST_OVERLAY_KEYS.get(beast_key)
            chosen = beat.get(field) if field else None
            skip = not _is_overlay_payload(chosen)
        elif slot == "moth":
            field = REI_MOTH_OVERLAY_KEYS.get(moth_key)
            chosen = beat.get(field) if field else None
            skip = not _is_overlay_payload(chosen)
        elif slot == "attack":
            field = REI_ATTACK_OVERLAY_KEYS.get(attack_key)
            chosen = beat.get(field) if field else None
            skip = not _is_overlay_payload(chosen)
        elif slot == "kiss":
            field = REI_KISS_OVERLAY_KEYS.get(kiss_key) if kiss_key != "off" else None
            chosen = beat.get(field) if field else None
            skip = not _is_overlay_payload(chosen)
        elif slot == "oral":
            field = REI_ORAL_OVERLAY_KEYS.get(oral_key)
            chosen = beat.get(field) if field else None
            skip = not _is_overlay_payload(chosen)
        elif slot == "pose":
            field = REI_POSE_OVERLAY_KEYS.get(pose_key)
            chosen = beat.get(field) if field else None
            skip = not _is_overlay_payload(chosen)
        if skip:
            continue
        expanded = _expand_overlay(body, chosen) if _is_overlay_payload(chosen) else [body]
        after_toilet = bool(filth)
        if slot == "toilet":
            filth = str((REI_TOILET_MODES.get(toilet_key) or {}).get("filth") or "")
        for item in expanded:
            row = dict(item)
            if after_toilet:
                row = _inject_rei_filth(row, filth)
            # Who-initiates is the S17 attack cut only. Kiss / oral / pose / S21
            # already describe their own blocking; prefixing "pounces" onto
            # fours-in (or "presses her to the meat wall" onto orgasm) contradicts
            # the overlay.
            if slot == "attack":
                action = str(row.get("action") or "")
                if attack_prefix and attack_prefix not in action:
                    row["action"] = attack_prefix + action
            beats.append(row)
    if not beats:
        raise EpisodeError("rei-escape: at least one footage beat must stay")
    out["beats"] = beats
    render = dict(out.get("render") or {})
    render["rei_mast"] = mast_key
    render["rei_toilet"] = toilet_key
    render["rei_beast"] = beast_key
    render["rei_moth"] = moth_key
    render["rei_attack"] = attack_key
    render["rei_kiss"] = kiss_key
    render["rei_oral"] = oral_key
    render["rei_pose"] = pose_key
    out["render"] = render
    cards = dict(out.get("cards") or {})
    cards.pop("fail", None)
    out["cards"] = cards
    last = None
    for i in range(len(beats) - 1, -1, -1):
        if isinstance(beats[i], dict):
            last = dict(beats[i])
            hud = dict(last.get("hud") or {})
            hud["complete"] = True
            last["hud"] = last.get("hud") and hud or hud
            last["hud"] = hud
            beats[i] = last
            out["beats"] = beats
            break
    return out


def resolve_episode_options(
    ep: dict[str, Any],
    *,
    story: str | None = None,
    pose: str | None = None,
    toilet: str | None = None,
    gin: str | None = None,
    tsuno: str | None = None,
    appear: str | dict[str, Any] | None = None,
    scenes: str | dict[str, Any] | None = None,
    rei_mast: str | None = None,
    rei_toilet: str | None = None,
    rei_beast: str | None = None,
    rei_moth: str | None = None,
    rei_attack: str | None = None,
    rei_kiss: str | None = None,
    rei_oral: str | None = None,
    rei_pose: str | None = None,
) -> dict[str, Any]:
    """Story + invite pose + toilet + optional events + appear + per-scene + rei-escape, without connect/combat Colab wiring."""
    out = apply_story_route(ep, story=story, scenes=scenes) if _has_story_overlays(ep) else copy.deepcopy(ep)
    out = apply_invite_pose(out, pose=pose)
    out = apply_toilet_route(out, toilet=toilet)
    out = apply_optional_events(out, gin=gin, tsuno=tsuno)
    out = apply_appear_route(out, appear=appear)
    return apply_rei_escape_route(
        out,
        mast=rei_mast,
        toilet=rei_toilet,
        beast=rei_beast,
        moth=rei_moth,
        attack=rei_attack,
        kiss=rei_kiss,
        oral=rei_oral,
        pose=rei_pose,
    )


HOSPITAL_WALK_IDS = frozenset({
    "01-cover",
    "04-peek",
    "04-toilet-in",
    "04-gin-lick",
    "04-tsuno-meet",
    "07-kana",
    "07-run",
    "10-shino",
    "11-door",
})
HOSPITAL_WALK_ID_RE = re.compile(r"(?:-walk|-out|-run|-slip)$")


def scrub_planted_action(action: str) -> str:
    """Sex/toilet holds must not also walk the corridor in the same take."""
    out = str(action or "")
    out = PLANTED_WALK_TAIL_RE.sub("", out)
    out = re.sub(r" at (?:brisk )?walking-and-hit pace", " at snappy real-time", out, flags=re.I)
    out = re.sub(r"Aya STEPS RIGHT FAST,?\s*", "Aya is already close. ", out)
    out = re.sub(
        r"Aya STEPS RIGHT toward (?P<who>[A-Za-z]+),?\s*",
        r"Aya is already close to \g<who>. ",
        out,
    )
    out = re.sub(
        r"(Miki|Rei|Kana|Shino|Gin|Tsuno) STEPS RIGHT(?: at snappy real-time)?,?\s*",
        r"\1 is already in place. ",
        out,
    )
    out = re.sub(
        r"Aya STEPS IN behind (?P<who>[A-Za-z]+)(?: and STOPS on this same linoleum spot)?",
        r"Aya is already behind \g<who> on this same linoleum spot",
        out,
    )
    if re.search(r"\bWALKS?\b|\bWALKING\b", out) and re.search(
        r"joined at the BASE|on all fours|STAYS SEATED|already seated|SQUATS|jupo|"
        r"feet stay in the air|heels sit beside|held up, both thighs",
        out,
        re.I,
    ):
        out = re.sub(r"\bWALKS?\b RIGHT", "stays", out)
        out = re.sub(r"\bWALKING\b", "holding still", out)
    if "same linoleum spot" not in out.lower() and "same floor spot" not in out.lower():
        out = out.rstrip(".") + ". They stay on this same floor spot. Feet do not travel."
    return re.sub(r" {2,}", " ", out).strip()


_SPOT_POSE = {
    "rei": "Rei WALKS IN from the RIGHT edge and STOPS ahead toward the RIGHT in an imposing waiting stance, facing Aya, full body including feet.",
    "kana": "Kana WALKS IN from the RIGHT edge and STOPS mid-corridor facing Aya, feet planted, full body including feet.",
    "shino": "Shino WALKS IN from the RIGHT edge and STOPS, stooping at the lit doorway at the RIGHT edge, full body including feet, the shaft at the front of the groin.",
    "gin": "Gin walks in from the LEFT edge, directly behind Aya toward the LEFT, matching Aya's stride, full body including feet. Aya is toward the RIGHT, facing RIGHT.",
    "tsuno": "Tsuno WALKS IN from the LEFT edge, directly behind Aya toward the LEFT, matching Aya's stride, full body including feet.",
}


def insert_presence_beats(ep: dict[str, Any]) -> dict[str, Any]:
    """Put a new person in frame before their first act so the act can be I2V.

    The spot itself is the one T2V draw. Rei, Kana, Shino, Gin, and Tsuno each get one.
    The opener stays the first clip. A beat that already ends in -spot is left alone.
    """
    if str(ep.get("slug") or "") != "hospital-exit-adult":
        return ep
    out = copy.deepcopy(ep)
    cast_rows = out.get("cast") or {}
    built: list[Any] = []
    prev: set[str] = set()
    seen_gpu = False
    for beat in out.get("beats") or []:
        if not isinstance(beat, dict) or is_ui_beat(beat) or not beat_renders(beat):
            built.append(beat)
            continue
        intended = [str(c) for c in (beat.get("cast") or [])]
        intended_set = set(intended)
        bid = str(beat.get("id") or "")
        added = [c for c in intended if c not in prev and c != "aya"]
        if seen_gpu and added and not bid.endswith("-spot"):
            names = []
            poses = []
            for cid in added:
                row = cast_rows.get(cid) or {}
                names.append(str(row.get("name_en") or cid).strip() or cid)
                poses.append(_SPOT_POSE.get(cid) or f"{names[-1]} WALKS IN from the frame edge and STOPS with Aya, full body including feet.")
            who = " and ".join(names)
            spot_id = f"{bid}-spot"
            if added == ["tsuno"]:
                action = (
                    "Aya WALKS toward the RIGHT side of the frame, facing RIGHT, fully nude, full body including feet, "
                    "grimy brown hospital dirt on her skin. Her walking stride gradually slows, then she STOPS, hesitant and afraid. "
                    "Tsuno ENTERS from the LEFT edge of the frame and WALKS directly behind Aya toward the LEFT, facing RIGHT, "
                    "matching Aya's stride, full body including feet. "
                    "From the viewer, that left side is directly behind Aya. "
                    "Aya stays toward the RIGHT and keeps facing RIGHT the whole take. Tsuno stays toward the LEFT. Aya does not turn yet. "
                    "The right edge of the frame stays a dark corridor continuing on. "
                    "Last frame: Aya toward the RIGHT, stopped, facing RIGHT. Tsuno toward the LEFT, directly behind her, both full body including feet. "
                    "This take ends on that stop. Motion starts at frame one. Brisk real-time."
                )
                camera = (
                    "PROFILE side-on. Floor runs LEFT to RIGHT. Both adults full body including feet. "
                    "Tsuno walks in from the LEFT edge, directly behind Aya toward the LEFT, matching her stride. "
                    "Aya toward the RIGHT, facing RIGHT, her stride slowing to a stop. "
                    "The right edge stays a dark corridor continuing on."
                )
            elif added == ["gin"]:
                action = (
                    "Aya WALKS toward the RIGHT side of the frame, facing RIGHT, fully nude, full body including feet, "
                    "grimy brown hospital dirt on her skin. Her walking stride gradually slows, then she STOPS, hesitant and afraid. "
                    "Gin ENTERS from the LEFT edge of the frame and WALKS directly behind Aya toward the LEFT, facing RIGHT, "
                    "matching Aya's stride, full body including feet. "
                    "From the viewer, that left side is directly behind Aya. "
                    "Aya stays toward the RIGHT and keeps facing RIGHT the whole take. Gin stays toward the LEFT. Aya does not turn yet. "
                    "The right edge of the frame stays a dark corridor continuing on. "
                    "Last frame: Aya toward the RIGHT, stopped, facing RIGHT. Gin toward the LEFT, directly behind her, both full body including feet. "
                    "Motion starts at frame one. Brisk real-time."
                )
                camera = (
                    "PROFILE side-on. Floor runs LEFT to RIGHT. Both adults full body including feet. "
                    "Gin walks in from the LEFT edge, directly behind Aya toward the LEFT, matching her stride. "
                    "Aya toward the RIGHT, facing RIGHT, her stride slowing to a stop. "
                    "The right edge stays a dark corridor continuing on."
                )
            else:
                action = (
                    "Aya is already in the corridor, fully nude, grimy brown hospital dirt on her skin. "
                    + " ".join(poses)
                    + " They share the frame, a short step apart. Aya takes one step closer and stops. "
                    f"Last frame: Aya and {who} both full body including feet, still a short step apart. "
                    "Motion starts at frame one. Brisk real-time."
                )
                camera = (
                    "PROFILE side-on. Floor runs LEFT to RIGHT. Both adults full body including feet. "
                    f"{who} walks into the frame with Aya."
                )
            built.append({
                "id": spot_id,
                "source": "chain",
                "connect": "chain",
                "trim": {"start": 0, "seconds": 6.0},
                "cast": list(intended),
                "encounter": beat.get("encounter") or "",
                "place": beat.get("place") or "",
                "camera": camera,
                "action": action,
                "voices": [{"who": "aya", "line": "ん"}],
                "sfx": "Quiet corridor, fluorescent buzz, one footstep, HVAC",
                "music": beat.get("music") or "Bass holds",
                "hud": dict(beat.get("hud") or {}),
                "loco": "walk",
                "extra_loras": [],
                "trigger": "",
            })
        built.append(beat)
        seen_gpu = True
        prev = intended_set
    out["beats"] = built
    return out


def apply_default_loco(ep: dict[str, Any]) -> dict[str, Any]:
    """Ward sex/toilet holds stay planted. Walk beats keep a walk cycle.

    The side2d pack otherwise injects 'Adults move LEFT or RIGHT' into every shot,
    so acts try to relocate down the corridor.
    """
    if str(ep.get("slug") or "") != "hospital-exit-adult":
        return ep
    for beat in ep.get("beats") or []:
        if not isinstance(beat, dict) or is_ui_beat(beat):
            continue
        bid = str(beat.get("id") or "")
        action = str(beat.get("action") or "")
        if re.search(r"STEPS SIDEWAYS|WALKS PAST|can pass", action, re.I):
            beat["loco"] = "walk"
            continue
        if not str(beat.get("loco") or "").strip():
            walk_words = bool(re.search(r"\bWALKS?\b|\bWALKING\b|\bRUNS?\b|\bSPRINT", action))
            planted_pose = bool(
                re.search(
                    r"joined at the BASE|already seated|STAYS SEATED|on all fours|palms planted|"
                    r"feet stay in the air|heels sit beside|held up, both thighs|woman facing the camera",
                    action,
                    re.I,
                )
            )
            if HOSPITAL_WALK_ID_RE.search(bid) or bid in HOSPITAL_WALK_IDS or (walk_words and not planted_pose):
                beat["loco"] = "run" if re.search(r"\bRUNS?\b|\bSPRINT", action) else "walk"
            else:
                beat["loco"] = "planted"
        if beat_loco(beat) == "planted":
            beat["action"] = scrub_planted_action(action)
    return ep


def prepare_episode(
    ep: dict[str, Any],
    *,
    connect_override: str | None = None,
    end_connect_override: str | None = None,
    camera_pack_override: str | None = None,
    preset_override: str | None = None,
    combat_override: str | None = None,
    story_override: str | None = None,
    invite_pose_override: str | None = None,
    toilet_override: str | None = None,
    gin_override: str | None = None,
    tsuno_override: str | None = None,
    appear_override: str | dict[str, Any] | None = None,
    scenes_override: str | dict[str, Any] | None = None,
    rei_mast_override: str | None = None,
    rei_toilet_override: str | None = None,
    rei_beast_override: str | None = None,
    rei_moth_override: str | None = None,
    rei_attack_override: str | None = None,
    rei_kiss_override: str | None = None,
    rei_oral_override: str | None = None,
    rei_pose_override: str | None = None,
) -> dict[str, Any]:
    """Apply Colab/CLI overrides, then wire beats for the chosen connect mode."""
    out = copy.deepcopy(ep)
    render = dict(out.get("render") or {})
    prefetch: list[str] = []
    _collect_extra_lora_keys(out, prefetch)
    if prefetch:
        render["lora_prefetch"] = prefetch
    if connect_override not in (None, ""):
        render["connect"] = canonical_connect(connect_override)
    if end_connect_override not in (None, ""):
        render["end_connect"] = canonical_end_connect(end_connect_override)
    if camera_pack_override not in (None, ""):
        render["camera_pack"] = canonical_camera(camera_pack_override)
    if preset_override not in (None, ""):
        lookup = canonical_preset(preset_override)
        render["preset"] = lookup if lookup in PRESETS else preset_override
    if story_override not in (None, ""):
        render["story"] = canonical_story(story_override) or story_override
    if combat_override not in (None, ""):
        render["combat"] = canonical_combat(combat_override) or combat_override
    if invite_pose_override not in (None, ""):
        render["invite_pose"] = canonical_invite_pose(invite_pose_override) or invite_pose_override
    if toilet_override not in (None, ""):
        render["toilet"] = canonical_toilet(toilet_override) or toilet_override
    if gin_override not in (None, ""):
        render["gin"] = canonical_gin(gin_override) or gin_override
    if tsuno_override not in (None, ""):
        render["tsuno"] = canonical_tsuno(tsuno_override) or tsuno_override
    if appear_override not in (None, ""):
        render["appear"] = parse_appear(appear_override)
    if scenes_override not in (None, ""):
        render["scenes"] = scenes_to_choices(episode_scenes(out, scenes_override))
    if rei_mast_override not in (None, ""):
        render["rei_mast"] = canonical_rei_mast(rei_mast_override) or rei_mast_override
    if rei_toilet_override not in (None, ""):
        render["rei_toilet"] = canonical_rei_toilet(rei_toilet_override) or rei_toilet_override
    if rei_beast_override not in (None, ""):
        render["rei_beast"] = canonical_rei_beast(rei_beast_override) or rei_beast_override
    if rei_moth_override not in (None, ""):
        render["rei_moth"] = canonical_rei_moth(rei_moth_override) or rei_moth_override
    if rei_attack_override not in (None, ""):
        render["rei_attack"] = canonical_rei_attack(rei_attack_override) or rei_attack_override
    if rei_kiss_override not in (None, ""):
        render["rei_kiss"] = canonical_rei_kiss(rei_kiss_override) or rei_kiss_override
    if rei_oral_override not in (None, ""):
        render["rei_oral"] = canonical_rei_oral(rei_oral_override) or rei_oral_override
    if rei_pose_override not in (None, ""):
        render["rei_pose"] = canonical_rei_pose(rei_pose_override) or rei_pose_override
    out["render"] = render
    if _has_story_overlays(out):
        out = apply_story_route(out, story=story_override, scenes=scenes_override)
    else:
        out = apply_combat_route(out)
    out = apply_invite_pose(out, pose=invite_pose_override)
    out = apply_toilet_route(out, toilet=toilet_override)
    out = apply_optional_events(out, gin=gin_override, tsuno=tsuno_override)
    out = apply_appear_route(out, appear=appear_override)
    out = apply_rei_escape_route(
        out,
        mast=rei_mast_override,
        toilet=rei_toilet_override,
        beast=rei_beast_override,
        moth=rei_moth_override,
        attack=rei_attack_override,
        kiss=rei_kiss_override,
        oral=rei_oral_override,
        pose=rei_pose_override,
    )
    out = apply_default_loco(out)
    out = insert_presence_beats(out)
    out = apply_connect_mode(out)
    out = _honor_beat_connect(out)
    out = apply_end_connect(out, end_connect=end_connect_override)
    return keep_chain_cast(out)


def gpu_index_map(ep: dict[str, Any]) -> dict[str, int]:
    """GPU beat order, skipping ui. Adjacent T2V shots rotate camera angles with this index."""
    out: dict[str, int] = {}
    i = 0
    for beat in ep.get("beats") or []:
        if isinstance(beat, dict) and beat_renders(beat):
            bid = str(beat.get("id") or "")
            if bid:
                out[bid] = i
                i += 1
    return out


def camera_angle(pack_name: str, gpu_index: int) -> str:
    pack = CAMERA_PACKS[canonical_camera(pack_name)]
    angles = pack["angles"]
    return str(angles[int(gpu_index) % len(angles)])


# Per-beat opt-out: keep beat.camera only. Hospital toilet must not inherit the corridor doorway.
AUTHORED_CAMERA_PACKS = frozenset({"", "none", "off", "authored", "beat"})


def resolve_beat_camera_pack(
    ep: dict[str, Any],
    beat: dict[str, Any] | None = None,
    override: str | None = None,
) -> str:
    """Episode/Colab pack, unless this beat opts out (toilet stall stays on the bowl)."""
    if isinstance(beat, dict) and "camera_pack" in beat:
        raw = str(beat.get("camera_pack") or "").strip().lower()
        if raw in AUTHORED_CAMERA_PACKS:
            return ""
        return canonical_camera(str(beat.get("camera_pack") or ""))
    if override not in (None, ""):
        return canonical_camera(override)
    return episode_camera_pack(ep)


def beat_loco(beat: dict[str, Any]) -> str:
    return str((beat or {}).get("loco") or "").strip().lower()


def _planted_camera_text(text: str) -> str:
    """Drop walk-track and doorway bait that spawns giant extra women during sex/toilet."""
    out = str(text or "")
    out = re.sub(r"Adults move LEFT or RIGHT\.?\s*", "", out)
    out = re.sub(
        r"The lit doorway sits at the RIGHT edge of the frame\.?\s*",
        "",
        out,
        flags=re.I,
    )
    out = re.sub(r"\bhorizontal track only\b", "camera holds", out, flags=re.I)
    out = re.sub(r"\btracks? left and right\b", "holds", out, flags=re.I)
    return re.sub(r"\s{2,}", " ", out).strip()


def camera_line(
    ep: dict[str, Any],
    beat: dict[str, Any],
    *,
    pack_name: str = "",
    gpu_index: int = 0,
    rotate: bool = True,
) -> str:
    """Pack lock + rotating angle (T2V) or a held camera (I2V chain/landing). Empty pack keeps beat.camera."""
    authored = str(beat.get("camera") or "").strip().rstrip(".")
    planted = beat_loco(beat) == "planted"
    if planted:
        authored = _planted_camera_text(authored).rstrip(".")
    if not pack_name:
        return authored
    key = canonical_camera(pack_name)
    if key not in CAMERA_PACKS:
        raise EpisodeError(f"unknown camera_pack {pack_name}")
    spec = CAMERA_PACKS[key]
    if planted and spec.get("planted_lock"):
        lock = str(spec["planted_lock"]).strip().rstrip(".")
    else:
        lock = str(spec["lock"]).strip().rstrip(".")
    parts = [lock + "."]
    if rotate and not planted:
        angle = camera_angle(key, gpu_index).strip().rstrip(".")
        parts.append("This shot: " + angle + ".")
    else:
        parts.append("The camera stays in this setup from the first frame to the last.")
    if authored:
        parts.append("Blocking: " + authored + ".")
    return " ".join(parts)


def beat_props(ep: dict[str, Any], beat: dict[str, Any]) -> list[str]:
    """Prop keys locked into this beat's prompt: the explicit list, else keys named in the beat text.

    Never every prop: the first render put the firewood truck into the barbershop and the noren shot
    because `props` was injected into all nine prompts.
    """
    props = ep.get("props") or {}
    if "props" in beat:
        return [str(k) for k in (beat.get("props") or []) if str(k) in props]
    text = " ".join(str(beat.get(k) or "") for k in ("action", "camera", "place")).lower()
    return [k for k in props if re.search(rf"\b{re.escape(str(k).lower())}s?\b", text)]


def beat_window(ep: dict[str, Any], beat: dict[str, Any]) -> tuple[float, float]:
    """(start, seconds) of the raw clip that reaches the final cut."""
    if is_ui_beat(beat):
        return 0.0, float(beat.get("seconds") or UI_SECONDS[0])
    trim = beat.get("trim") or {}
    start = float(trim.get("start") or 0.0)
    seconds = float(trim.get("seconds") or 0.0) or max(0.0, clip_seconds(ep) - start)
    return start, seconds


def card_seconds(ep: dict[str, Any]) -> dict[str, float]:
    cards = ep.get("cards") or {}
    fail = cards.get("fail") or {}
    return {
        "title": float(cards.get("title_seconds") or CARD_TITLE_S) if cards.get("title", True) else 0.0,
        "fail": float(fail.get("seconds") or 3.2) if fail else 0.0,
        "end": float(cards.get("end_seconds") or CARD_END_S) if cards.get("end", True) else 0.0,
    }


def expected_duration(ep: dict[str, Any]) -> float:
    """Planned final length (nominal clip length for untrimmed beats)."""
    cs = card_seconds(ep)
    durs: list[float] = []
    if cs["title"]:
        durs.append(cs["title"])
    durs.extend(beat_window(ep, b)[1] for b in ep.get("beats") or [])
    if cs["fail"]:
        durs.append(cs["fail"])
    if cs["end"]:
        durs.append(cs["end"])
    cfg = ep.get("stitch") or {}
    return expected_stitch_duration(durs, transition=str(cfg.get("transition") or "xfade"), xfade_s=float(cfg.get("xfade_s", 0.35)))


def subtitle_windows(speech: list[dict[str, Any]], seconds: float, *, lead: float = 0.3, gap: float = 0.15) -> list[tuple[float, float]]:
    """When each spoken line is on screen. Even split of the window unless `at`/`until` are authored."""
    n = len(speech)
    if not n or seconds <= 0:
        return []
    seg = max(0.5, (seconds - lead) / n)
    out: list[tuple[float, float]] = []
    for i, item in enumerate(speech):
        a = float(item.get("at", lead + i * seg))
        b = float(item.get("until", a + seg - gap))
        out.append((max(0.0, min(a, seconds)), max(0.0, min(b, seconds))))
    return out


def fail_image_rel(ep: dict[str, Any]) -> str:
    """Path of an authored fail-card image, or "" when it is the last frame / plain."""
    fail = (ep.get("cards") or {}).get("fail") or {}
    img = str(fail.get("image") or "last-frame")
    return "" if img in ("last-frame", "") else img


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
    if fail_image_rel(ep):
        rels.append(fail_image_rel(ep))
    out: list[str] = []
    for r in rels:
        if r not in out:
            out.append(r)
    return out


def _kana_voice_errors(line: str, where: str, field: str) -> list[str]:
    """Spoken audio is kana inside 「」. Latin/Hangul/Cyrillic in the quote becomes English (or other) TTS."""
    errs: list[str] = []
    if "「" in line or "」" in line:
        errs.append(f"{where}: {field} must not contain 「」 (added automatically)")
    if KANJI_RE.search(line):
        errs.append(f"{where}: {field} must be kana only (H3 misreads kanji): {line}")
    if NON_JP_SPEECH_RE.search(line):
        errs.append(f"{where}: {field} Japanese kana only (no English/other letters): {line}")
    if not KANA_RE.search(line):
        errs.append(f"{where}: {field} must be Japanese kana")
    if len(line) > 26:
        errs.append(f"{where}: {field} too long for one breath (<= 26 chars)")
    return errs


def beat_vocals(beat: dict[str, Any]) -> list[dict[str, Any]]:
    """Lip-sync speech plus pulled-back moans/breaths. Both become 「かな」 on the audio track."""
    out: list[dict[str, Any]] = []
    for key in ("speech", "voices"):
        raw = beat.get(key) or []
        if not isinstance(raw, list):
            continue
        for item in raw:
            if isinstance(item, dict):
                out.append(item)
    return out


def _speech_errors(beat: dict[str, Any], cast: dict[str, Any], where: str, *, window_s: float) -> list[str]:
    errs: list[str] = []
    speech = beat.get("speech") or []
    if not isinstance(speech, list):
        return [f"{where}: speech must be a list"]
    if speech and is_ui_beat(beat):
        errs.append(f"{where}: a ui beat is a frozen frame; it cannot speak")
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
        errs.extend(_kana_voice_errors(line, where, f"speech[{i}]"))
        text = str(item.get("text") or "")
        if text and (len(text) > 30 or not CJK_RE.search(text) or NON_JP_SPEECH_RE.search(text)):
            errs.append(f"{where}: speech[{i}].text is the subtitle: Japanese, <= 30 chars")
        try:
            at = float(item["at"]) if "at" in item else None
            until = float(item["until"]) if "until" in item else None
            if at is not None and (at < 0 or at >= window_s):
                errs.append(f"{where}: speech[{i}].at must be inside the beat window (0-{window_s:g}s)")
            if until is not None and (until <= (at or 0.0) or until > window_s + 0.01):
                errs.append(f"{where}: speech[{i}].until must be after at and inside the beat window")
        except (TypeError, ValueError):
            errs.append(f"{where}: speech[{i}].at/until must be seconds")
    return errs


def _voices_errors(beat: dict[str, Any], cast: dict[str, Any], where: str) -> list[str]:
    """Moans/breaths for pulled-back cameras. No face close-up. Still Japanese kana only."""
    raw = beat.get("voices", [])
    if raw in (None, []):
        return []
    if not isinstance(raw, list):
        return [f"{where}: voices must be a list"]
    errs: list[str] = []
    if is_ui_beat(beat):
        errs.append(f"{where}: a ui beat is a frozen frame; it cannot voice")
    if len(raw) > 4:
        errs.append(f"{where}: at most 4 voiced breaths per beat")
    for i, item in enumerate(raw):
        if not isinstance(item, dict) or not item.get("who") or not item.get("line"):
            errs.append(f"{where}: voices[{i}] needs who + line")
            continue
        who = str(item["who"])
        line = str(item["line"]).strip()
        if who not in (beat.get("cast") or []):
            errs.append(f"{where}: voicer {who} is not in this beat's cast")
        if who not in cast:
            errs.append(f"{where}: voicer {who} is not in cast")
        errs.extend(_kana_voice_errors(line, where, f"voices[{i}]"))
    return errs


def _ui_errors(beat: dict[str, Any], where: str) -> list[str]:
    errs: list[str] = []
    try:
        sec = float(beat.get("seconds") or 0.0)
        if sec < UI_SECONDS[0] or sec > UI_SECONDS[1]:
            errs.append(f"{where}: ui beat needs seconds {UI_SECONDS[0]:g}-{UI_SECONDS[1]:g}")
    except (TypeError, ValueError):
        errs.append(f"{where}: seconds must be a number")
    menu = beat.get("menu")
    if not isinstance(menu, dict):
        return errs + [f"{where}: ui beat needs menu {{title, items, selected}}"]
    if not str(menu.get("title") or "").strip():
        errs.append(f"{where}: menu.title missing")
    items = menu.get("items") or []
    if not isinstance(items, list) or not 2 <= len(items) <= 8:
        errs.append(f"{where}: menu.items must list 2-8 entries")
    elif any(not str(x).strip() or len(str(x)) > 12 for x in items):
        errs.append(f"{where}: menu.items entries are 1-12 chars")
    try:
        sel = int(menu.get("selected", 0) or 0)
        if items and not 0 <= sel < len(items):
            errs.append(f"{where}: menu.selected out of range")
    except (TypeError, ValueError):
        errs.append(f"{where}: menu.selected must be an index")
    for key in ("still", "trim", "reuse", "physics", "extra_loras", "trigger", "steps", "sampler", "scheduler", "still_as"):
        if beat.get(key):
            errs.append(f"{where}: ui beat cannot have {key}")
    return errs


def _render_plan_errors(beat: dict[str, Any], where: str) -> list[str]:
    """Per-beat steps/sampler (combat quality). UI beats are rejected in _ui_errors."""
    errs: list[str] = []
    if is_ui_beat(beat):
        return errs
    if beat.get("steps") is not None:
        try:
            s = int(beat["steps"])
            lo, hi = BEAT_STEPS_RANGE
            if s < lo or s > hi:
                errs.append(f"{where}: steps must be {lo}-{hi} (20 OOMs with Larry+combat)")
        except (TypeError, ValueError):
            errs.append(f"{where}: steps must be an integer")
    sampler = beat.get("sampler")
    if sampler and str(sampler) not in SAMPLERS:
        errs.append(f"{where}: sampler must be one of {SAMPLERS}")
    scheduler = beat.get("scheduler")
    if scheduler and str(scheduler) not in SCHEDULERS:
        errs.append(f"{where}: scheduler must be one of {SCHEDULERS}")
    if beat.get("still_as") is not None and str(beat.get("still_as")) not in STILL_AS:
        errs.append(f"{where}: still_as must be one of {STILL_AS}")
    if beat_still_as(beat) in ("last", "both") and not beat.get("still"):
        errs.append(f"{where}: still_as {beat_still_as(beat)} needs a still path")
    return errs


def _trim_errors(ep: dict[str, Any], beat: dict[str, Any], where: str) -> list[str]:
    trim = beat.get("trim")
    if trim is None:
        return []
    if not isinstance(trim, dict):
        return [f"{where}: trim must be {{start, seconds}}"]
    errs: list[str] = []
    try:
        start = float(trim.get("start") or 0.0)
        seconds = float(trim.get("seconds") or 0.0)
    except (TypeError, ValueError):
        return [f"{where}: trim.start/seconds must be numbers"]
    if start < 0:
        errs.append(f"{where}: trim.start must be >= 0")
    if seconds and seconds < MIN_TRIM_S:
        errs.append(f"{where}: trim.seconds must be >= {MIN_TRIM_S:g}s")
    gpu_s = beat_clip_seconds(ep, beat)
    if start + seconds > gpu_s + 0.01:
        errs.append(f"{where}: trim window ends after the {gpu_s:g}s clip")
    if beat_still_as(beat) == "last" and start + seconds < gpu_s - 0.05:
        errs.append(f"{where}: still_as last: trim must include the last frame (the still)")
    return errs


def _fail_card_errors(ep: dict[str, Any]) -> list[str]:
    cards = ep.get("cards") or {}
    fail = cards.get("fail")
    if not fail:
        return []
    if not isinstance(fail, dict):
        return ["cards.fail must be {text, reason, seconds, image}"]
    errs: list[str] = []
    if len(str(fail.get("text") or FAIL_TEXT_DEFAULT)) > 12:
        errs.append("cards.fail.text <= 12 chars")
    if len(str(fail.get("reason") or "")) > 30:
        errs.append("cards.fail.reason <= 30 chars (one deadpan line)")
    try:
        sec = float(fail.get("seconds") or 3.2)
        if sec < CARD_SECONDS[0] or sec > CARD_SECONDS[1]:
            errs.append(f"cards.fail.seconds must be {CARD_SECONDS[0]:g}-{CARD_SECONDS[1]:g}")
    except (TypeError, ValueError):
        errs.append("cards.fail.seconds must be a number")
    beats = [b for b in (ep.get("beats") or []) if isinstance(b, dict)]
    if beats and (beats[-1].get("hud") or {}).get("complete"):
        errs.append("cards.fail: the last beat cannot flash ミッション完了 right before ミッション失敗")
    return errs


def validate_episode(ep: dict[str, Any], *, root: Path | str | None = None) -> list[str]:
    if _has_rei_escape_overlays(ep):
        errs: list[str] = []

        def _check(label: str, **kwargs: Any) -> None:
            try:
                resolved = resolve_episode_options(ep, **kwargs)
            except EpisodeError as exc:
                errs.append(f"{label}: {exc}")
                return
            for err in validate_episode(resolved, root=root):
                errs.append(f"{label}: {err}")

        _check("rei-default")
        _check("rei-mast-stand", rei_mast="stand")
        _check("rei-mast-back", rei_mast="back")
        _check("rei-toilet-tb", rei_toilet="tb")
        _check("rei-toilet-tc", rei_toilet="tc")
        _check("rei-beast-invite", rei_beast="invite")
        _check("rei-beast-evade", rei_beast="evade")
        _check("rei-moth-mouth", rei_moth="mouth")
        _check("rei-attack-her", rei_attack="her")
        _check("rei-kiss-on", rei_kiss="on")
        _check("rei-oral-her", rei_oral="her")
        _check("rei-oral-rei", rei_oral="rei")
        _check("rei-pose-wall", rei_pose="wall")
        _check("rei-pose-straddle", rei_pose="straddle")
        _check("rei-pose-supine", rei_pose="supine")
        _check(
            "rei-full",
            rei_mast="stand",
            rei_toilet="tc",
            rei_beast="invite",
            rei_moth="mouth",
            rei_attack="her",
            rei_kiss="on",
            rei_oral="her",
            rei_pose="straddle",
        )
        return errs
    if _has_story_overlays(ep):
        errs: list[str] = []

        def _check(label: str, **kwargs: Any) -> None:
            try:
                resolved = resolve_episode_options(ep, **kwargs)
            except EpisodeError as exc:
                errs.append(f"{label}: {exc}")
                return
            for err in validate_episode(resolved, root=root):
                errs.append(f"{label}: {err}")

        for key in STORY_MODES:
            _check(f"story-{key}", story=key)
        for pose in INVITE_POSE_MODES:
            _check(f"invite-pose-{pose}", story="invite", pose=pose)
        for toilet in TOILET_MODES:
            if toilet == "off":
                continue
            _check(f"toilet-{toilet}", story="accept", toilet=toilet)
        try:
            resolve_episode_options(ep, appear="none")
            errs.append("appear-none: expected EpisodeError (at least one encounter must stay on)")
        except EpisodeError as exc:
            if "at least one encounter" not in str(exc):
                errs.append(f"appear-none: {exc}")
        try:
            resolve_episode_options(ep, story="accept", toilet="pee", appear="none")
            errs.append("appear-none-toilet: expected EpisodeError (at least one encounter must stay on)")
        except EpisodeError as exc:
            if "at least one encounter" not in str(exc):
                errs.append(f"appear-none-toilet: {exc}")
        for story in STORY_MODES:
            for enc in HOSPITAL_ENCOUNTERS:
                skip = {name: name != enc for name in HOSPITAL_ENCOUNTERS}
                _check(f"story-{story}/skip-{enc}", story=story, appear=skip)
                only = {name: name == enc for name in HOSPITAL_ENCOUNTERS}
                _check(f"story-{story}/only-{enc}", story=story, appear=only)
        _check("scenes-miki-evade", story="accept", scenes="miki=evade")
        _check("scenes-shino-invite", story="accept", scenes="shino=invite_all_fours")
        _check("scenes-mixed-ending", story="invite", scenes="shino=evade")
        _check("scenes-fight-ignore", story="fight_win", scenes="miki=evade,rei=accept,kana=invite,shino=evade")
        _check("gin-taken", story="accept", gin="taken")
        _check("gin-fuck", story="accept", gin="fuck")
        _check("gin-invite-doggy", story="invite", gin="invite_doggy")
        _check("tsuno-accept", story="accept", tsuno="accept_stand")
        _check("tsuno-invite", story="invite", tsuno="invite_stand")
        return errs
    if _has_combat_overlays(ep):
        errs: list[str] = []
        for label, mode in (("combat-off", "off"), ("combat-on", "on")):
            resolved = apply_combat_route(ep, combat=mode)
            for err in validate_episode(resolved, root=root):
                errs.append(f"{label}: {err}")
        return errs
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
    preset = canonical_preset(str(render.get("preset") or "fast"))
    if preset not in PRESETS:
        errs.append(f"render.preset must be one of {list(PRESET_CANON)} (aliases: fast/preview=speed, daily=balance)")
    fb = canonical_preset(str(render.get("fallback_preset") or "fast"))
    if fb not in PRESETS:
        errs.append(f"render.fallback_preset must be one of {list(PRESET_CANON)}")
    pack = str(render.get("camera_pack") or "").strip()
    if pack:
        pack_key = canonical_camera(pack)
        if pack_key not in CAMERA_PACKS:
            errs.append(f"render.camera_pack must be one of {list(CAMERA_PACKS)} (add a pack in h3_episode_packs.py)")
    connect = str(render.get("connect") or "").strip()
    if connect:
        connect_key = canonical_connect(connect)
        if connect_key not in CONNECT_MODES:
            errs.append(f"render.connect must be one of {list(CONNECT_MODES)} (add a mode in h3_episode_packs.py)")
    end_connect = str(render.get("end_connect") or "").strip()
    if end_connect:
        end_key = canonical_end_connect(end_connect)
        if end_key not in END_CONNECT_MODES:
            errs.append(f"render.end_connect must be one of {list(END_CONNECT_MODES)}")
    combat = str(render.get("combat") or "").strip()
    if combat:
        combat_key = canonical_combat(combat)
        if combat_key not in COMBAT_MODES:
            errs.append(f"render.combat must be one of {list(COMBAT_MODES)}")
    story = str(render.get("story") or "").strip()
    if story:
        story_key = canonical_story(story)
        if story_key not in STORY_MODES:
            errs.append(f"render.story must be one of {list(STORY_MODES)}")
    gin = str(render.get("gin") or "").strip()
    if gin:
        gin_key = canonical_gin(gin)
        if gin_key not in GIN_MODES:
            errs.append(f"render.gin must be one of {list(GIN_MODES)}")
    tsuno = str(render.get("tsuno") or "").strip()
    if tsuno:
        tsuno_key = canonical_tsuno(tsuno)
        if tsuno_key not in TSUNO_MODES:
            errs.append(f"render.tsuno must be one of {list(TSUNO_MODES)}")
    errs.extend(_checkpoint_errors(ep))
    tone = episode_tone(ep)
    if tone not in TONES:
        errs.append(f"tone must be one of {TONES}")
    if tone == "mundane" and str(ep.get("violence") or "none") != "none":
        errs.append("tone mundane needs violence none (the footage stays ordinary; only the HUD is a crime game)")
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
        else:
            lock = str(c.get("lock") or "")
            if STUDIO_I2V_MINOR_RE.search(lock) or CAST_UNDERAGE_RE.search(lock):
                errs.append(f"cast.{cid}.lock must describe an adult (no minor age tags)")
        try:
            if int(c.get("age") or 0) < ADULT_AGE_MIN:
                errs.append(f"cast.{cid}.age must be an adult (>= {ADULT_AGE_MIN})")
        except (TypeError, ValueError):
            errs.append(f"cast.{cid}.age must be an integer")
    beats = ep.get("beats") or []
    if not isinstance(beats, list) or not beats:
        errs.append("beats must be a non-empty list")
        beats = []
    if len(beats) > MAX_BEATS:
        errs.append(f"at most {MAX_BEATS} beats")
    props = ep.get("props") or {}
    slug_now = str(ep.get("slug") or "")
    seen: set[str] = set()
    face_beats = 0
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
        source = beat_source(beat)
        if source not in SOURCES:
            errs.append(f"{where}: source must be one of {SOURCES}")
        if source in ("chain", "ui") and i == 0:
            errs.append(f"{where}: first beat cannot be {source} (nothing before it)")
        if source == "t2v" and beat_still_as(beat) in ("last", "both"):
            errs.append(f"{where}: t2v cannot use still_as last/both (that locks Picture 2 and blocks prompt correction)")
        if beat_still_as(beat) == "last" and i == 0:
            errs.append(f"{where}: first beat cannot be still_as last (nothing to start from; use first or both)")
        if source == "ui" and i > 0 and isinstance(beats[i - 1], dict) and is_ui_beat(beats[i - 1]):
            errs.append(f"{where}: two ui beats in a row (the menu needs footage under it)")
        reuse = str(beat.get("reuse") or "")
        if reuse:
            m = REUSE_RE.match(reuse)
            if not m:
                errs.append(f"{where}: reuse must look like other-slug/01-beat-id")
            elif m.group(1) == slug_now and m.group(2) == bid:
                errs.append(f"{where}: reuse cannot point at itself")
            if source not in ("still", "t2v"):
                errs.append(f"{where}: reuse works with source still or t2v (chain and ui are built here)")
        still = str(beat.get("still") or "")
        if source == "still":
            if not still and not reuse:
                errs.append(f"{where}: source still needs a still path (or reuse)")
            elif still and ("-hud" in Path(still).stem or "hud" in Path(still).parts[:-1]):
                errs.append(f"{where}: HUD-burned stills cannot be first frames: {still}")
            elif still and root is not None and not (Path(root) / still).is_file():
                errs.append(f"{where}: still missing on disk: {still}")
        if source == "ui":
            errs.extend(_ui_errors(beat, where))
        errs.extend(_trim_errors(ep, beat, where))
        window_s = beat_window(ep, beat)[1]
        for cid in beat.get("cast") or []:
            if cid not in cast:
                errs.append(f"{where}: unknown cast id {cid}")
        beat_locks = beat.get("cast_lock")
        if beat_locks is not None:
            if not isinstance(beat_locks, dict):
                errs.append(f"{where}: cast_lock must be an object")
            else:
                shown = {str(cid) for cid in (beat.get("cast") or [])}
                for cid, lock in beat_locks.items():
                    if str(cid) not in shown:
                        errs.append(f"{where}: cast_lock.{cid} is not in this beat's cast")
                    text = str(lock or "")
                    if not text.strip():
                        errs.append(f"{where}: cast_lock.{cid} missing")
                    elif CJK_RE.search(text):
                        errs.append(f"{where}: cast_lock.{cid} must be English")
                    elif STUDIO_I2V_MINOR_RE.search(text) or CAST_UNDERAGE_RE.search(text):
                        errs.append(f"{where}: cast_lock.{cid} must describe an adult")
        if "props" in beat:
            if not isinstance(beat.get("props"), list):
                errs.append(f"{where}: props must be a list of keys from the episode props")
            else:
                for k in beat["props"]:
                    if str(k) not in props:
                        errs.append(f"{where}: unknown prop {k}")
        errs.extend(_extra_lora_errors(beat, where))
        errs.extend(_render_plan_errors(beat, where))
        for key in ("action", "camera"):
            text = str(beat.get(key) or "").strip()
            if not text and source != "ui":
                errs.append(f"{where}: {key} missing")
            elif CJK_RE.search(text):
                errs.append(f"{where}: {key} must be English")
            elif SLOWMO_TOKENS_RE.search(text):
                errs.append(f"{where}: {key} names slow motion (H3 draws it even when negated; leave the words out)")
        if "camera_pack" in beat:
            raw_pack = str(beat.get("camera_pack") or "").strip().lower()
            if raw_pack not in AUTHORED_CAMERA_PACKS:
                try:
                    canonical_camera(str(beat.get("camera_pack") or ""))
                except EpisodeError:
                    errs.append(
                        f"{where}: camera_pack must be one of {list(CAMERA_PACKS)} or none"
                    )
        for key in ("sfx", "music", "place", "environment"):
            text = str(beat.get(key) or "")
            if text and CJK_RE.search(text):
                errs.append(f"{where}: {key} must be English")
        if tone == "mundane":
            if beat.get("physics"):
                errs.append(f"{where}: tone mundane forbids physics")
            for key in ("action", "camera", "place"):
                m = ACTION_TOKENS_RE.search(str(beat.get(key) or ""))
                if m:
                    errs.append(f"{where}: tone mundane: do not write set-piece words, not even negated ({key}: {m.group(0)!r})")
        if beat.get("face_visible"):
            face_beats += 1
        errs.extend(_speech_errors(beat, cast, where, window_s=window_s))
        errs.extend(_voices_errors(beat, cast, where))
        if episode_voice(ep) == "japanese" and source != "ui":
            if not any(str(v.get("line") or "").strip() for v in beat_vocals(beat)):
                errs.append(
                    f"{where}: japanese voice needs speech or voices in kana "
                    "(H3 otherwise invents English or other languages)"
                )
        hud = beat.get("hud") or {}
        mission = str(hud.get("mission") or "").strip()
        if not mission:
            errs.append(f"{where}: hud.mission missing")
        elif len(mission) > 24:
            errs.append(f"{where}: hud.mission too long (<= 24 chars)")
        keyword = str(hud.get("mission_keyword") or "")
        if keyword and keyword not in mission:
            errs.append(f"{where}: hud.mission_keyword must be part of hud.mission")
        if len(str(hud.get("hint") or "")) > 16:
            errs.append(f"{where}: hud.hint too long (<= 16 chars)")
        if not isinstance(hud.get("visible", True), bool):
            errs.append(f"{where}: hud.visible must be true or false")
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
    if tone == "mundane" and face_beats > 2:
        errs.append("tone mundane: at most 2 face_visible beats (every new face shot is where the identity drifted)")
    cards = ep.get("cards") or {}
    if cards.get("end", True) and not str(cards.get("disclaimer") or "").strip():
        errs.append("cards.disclaimer required when the end card is on (fictional game notice)")
    for key in ("title_seconds", "end_seconds"):
        if cards.get(key) is not None:
            try:
                v = float(cards[key])
                if v < CARD_SECONDS[0] or v > CARD_SECONDS[1]:
                    errs.append(f"cards.{key} must be {CARD_SECONDS[0]:g}-{CARD_SECONDS[1]:g}")
            except (TypeError, ValueError):
                errs.append(f"cards.{key} must be a number")
    errs.extend(_fail_card_errors(ep))
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
    for m in SLOWMO_TOKENS_RE.finditer(text):
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


_LOOK_DROP_RE = re.compile(r"\b(?:no|never|not|without)\b", re.IGNORECASE)
_SHAFT_IN_LOOK_RE = re.compile(r"\b(?:shaft|penis|\d+\s*cm)\b", re.IGNORECASE)


def _positive_look(lock: str) -> str:
    """Keep the authored look. Drop negated clauses so H3 does not draw the named absence."""
    kept: list[str] = []
    for part in str(lock or "").split(","):
        piece = part.strip().rstrip(".")
        if not piece or _LOOK_DROP_RE.search(piece):
            continue
        kept.append(piece)
    return ", ".join(kept)


def _look_hold(ep: dict[str, Any], beat: dict[str, Any]) -> str:
    """Repeat the initial character look inside the action so dirt and a shaft do not wash off."""
    if str(ep.get("slug") or "") != "hospital-exit-adult":
        return ""
    cast = ep.get("cast") or {}
    locks = beat.get("cast_lock") if isinstance(beat.get("cast_lock"), dict) else {}
    lines: list[str] = []
    shaft_names: list[str] = []
    fade = {str(c) for c in (beat.get("fade_cast") or [])}
    for cid in beat.get("cast") or []:
        row = cast.get(cid) or {}
        name = str(row.get("name_en") or cid).strip() or str(cid)
        lock = str(locks.get(cid) or row.get("lock") or "")
        positive = _positive_look(lock)
        if positive:
            lines.append(f"{name}: {positive}.")
        if positive and str(cid) not in fade and _SHAFT_IN_LOOK_RE.search(positive):
            shaft_names.append(name)
    if not lines:
        return ""
    action = str(beat.get("action") or "").lower()
    shaft = ""
    if shaft_names and "shaft is gone" not in action:
        who = " and ".join(shaft_names)
        shaft = f" {who}'s shaft written in that look stays erect, the same length and the same color, on the groin."
    return (
        "Look that stays for this whole shot: "
        + " ".join(lines)
        + shaft
        + " Dirt, wounds, and slime in that look stay on the skin."
    )


def _cast_block(ep: dict[str, Any], beat: dict[str, Any]) -> str:
    cast = ep.get("cast") or {}
    beat_locks = beat.get("cast_lock") if isinstance(beat.get("cast_lock"), dict) else {}
    lines: list[str] = []
    for cid in beat.get("cast") or []:
        c = cast.get(cid) or {}
        name = str(c.get("name_en") or cid.title())
        lock = str(beat_locks.get(cid) or c.get("lock") or "").strip().rstrip(".")
        lines.append(f"{name}: {lock}. Adult, {int(c.get('age') or 0)}.")
    return "\n".join(lines)


def _speech_visual(ep: dict[str, Any], beat: dict[str, Any]) -> str:
    cast = ep.get("cast") or {}
    parts: list[str] = []
    speech_who = {str(item.get("who") or "") for item in (beat.get("speech") or []) if isinstance(item, dict)}
    for item in beat_vocals(beat):
        who = str(item.get("who") or "")
        line = str(item.get("line") or "").strip()
        if not who or not line:
            continue
        name = str((cast.get(who) or {}).get("name_en") or who.title())
        if who in speech_who:
            parts.append(f"{name} speaks with clearly visible mouth movement: 「{line}」.")
        else:
            parts.append(f"{name} voices 「{line}」.")
    return " ".join(parts)


def _speech_audio(ep: dict[str, Any], beat: dict[str, Any]) -> str:
    cast = ep.get("cast") or {}
    parts: list[str] = []
    for item in beat_vocals(beat):
        line = str(item.get("line") or "").strip()
        if not line:
            continue
        c = cast.get(item.get("who")) or {}
        voice = str(c.get("voice") or "natural adult voice")
        parts.append(f"「{line}」 in a {voice}.")
    return " ".join(parts)


ORAL_CAMERA_HOLD = (
    "The camera distance stays fixed for the whole take. "
    "Aya's face and the partner's face stay in frame the whole take. "
    "Both adults stay full body, both feet in frame."
)

RIDE_CAMERA_HOLD = (
    "The camera stays PROFILE side-on. "
    "The camera distance stays fixed for the whole take. "
    "Aya's face and the partner's face stay in frame the whole take. "
    "Both adults stay full body, both feet in frame. "
    "The hips lower in that side view."
)

PAIR_FRAME_HOLD = "Only two adults share this frame. Two faces."


def _hospital_prompt_holds(ep: dict[str, Any], beat: dict[str, Any]) -> list[str]:
    """Wide oral and side-on ride cameras, and a two-person lock on planted sex."""
    if str(ep.get("slug") or "") != "hospital-exit-adult":
        return []
    keys = {key for key, _strength in extra_lora_entries(beat)}
    holds: list[str] = []
    if "blowjob" in keys:
        holds.append(ORAL_CAMERA_HOLD)
    if "sideride" in keys:
        holds.append(RIDE_CAMERA_HOLD)
    cast = [str(c) for c in (beat.get("cast") or [])]
    sex = bool(keys & {"blowjob", "sideride", "thrust", "mystic", "futatf"}) or bool(
        NELSON_HOLD_RE.search(str(beat.get("action") or ""))
    )
    if beat_loco(beat) == "planted" and len(cast) == 2 and sex:
        holds.append(PAIR_FRAME_HOLD)
    return holds


def build_beat_prompt(
    ep: dict[str, Any],
    beat: dict[str, Any],
    *,
    trigger: str = "",
    camera_pack: str | None = None,
    gpu_index: int | None = None,
) -> str:
    """Canonical H3 sections. English body, Japanese only inside 「」."""
    source = beat_source(beat)
    canvas = str(ep.get("canvas") or "16:9")
    orientation = "Horizontal 16:9" if canvas == "16:9" else "Vertical 9:16"
    world = ep.get("world") or {}
    props = ep.get("props") or {}
    keys = beat_props(ep, beat)
    style = str(ep.get("style") or "").strip().rstrip(".")
    env = str(beat.get("environment") or world.get("lock") or "").strip().rstrip(".")
    place = str(beat.get("place") or "").strip().rstrip(".")
    env_line = env + (f". {place}" if place else "")
    if world.get("bare_set"):
        env_line += (
            ". Walls are only wet pulsating living flesh and viscera. "
            "Bare organic tissue, nothing man-made attached to the walls"
        )
    elif world.get("no_text_on_signs", True):
        env_line += ". Signs, posters, screens, and badges carry no readable letters"
    env_line += ". Adults only in frame."
    desc: list[str] = [f"[Shot 1] {orientation} {style}."]
    last_still = uses_last_still(beat)
    if last_still:
        desc.append("<Picture 1> is the opening identity lock; the clip starts exactly on it.")
        desc.append("<Picture 2> is the authored landing; the clip arrives on it at the last frame. Same faces, hair, and clothes. Arrival is at brisk walking-and-hit pace.")
        if beat_still_as(beat) == "last":
            desc.append("This shot continues the previous one without a cut until it lands on <Picture 2>.")
        elif beat_still_as(beat) == "both":
            desc.append("<Picture 1> and <Picture 2> are the same still; the clip holds this composition.")
    elif source in ("still", "chain"):
        if world.get("bare_set"):
            desc.append(
                "<Picture 1> is the identity lock; the clip starts exactly on it. "
                "Same person, same hair, fully nude bare skin. Expression and pose follow this shot's action, "
                "even if the opening frame shows a different face or a tongue out."
            )
        elif str(ep.get("slug") or "") == "hospital-exit-adult":
            desc.append(
                "<Picture 1> is the opening frame; the clip starts on it. "
                "Pose continues from it. Skin, dirt, wounds, hair, and shaft follow subject_definitions for the whole shot."
            )
        else:
            desc.append("<Picture 1> is the identity, costume, prop, and set lock; the clip starts exactly on it and the same person keeps this face, hair, and clothes until the end.")
    if source == "chain" and not last_still:
        desc.append("This shot continues the previous one without a cut.")
    desc.append(CONTINUITY_CLAUSE)
    loco = beat_loco(beat)
    if episode_tone(ep) == "mundane":
        desc.append(MUNDANE_CLAUSE)
    elif loco == "planted":
        desc.append(GAME_THIRD_PERSON_CLAUSE)
        desc.append(PLANTED_PACE_CLAUSE)
        action_txt = str(beat.get("action") or "")
        desc.append(NELSON_PLANTED_CLAUSE if NELSON_HOLD_RE.search(action_txt) else PLANTED_CLAUSE)
    else:
        desc.append(GAME_THIRD_PERSON_CLAUSE)
        desc.append(GAMEPLAY_PACE_CLAUSE)
        if loco == "run":
            desc.append(RUN_CLAUSE)
    pack = resolve_beat_camera_pack(ep, beat, camera_pack)
    idx = gpu_index if gpu_index is not None else gpu_index_map(ep).get(str(beat.get("id") or ""), 0)
    cam = camera_line(
        ep,
        beat,
        pack_name=pack,
        gpu_index=idx,
        rotate=connect_rotates_camera(ep),
    )
    if (
        cam
        and str(ep.get("slug") or "") == "hospital-exit-adult"
        and "sideride" in {key for key, _strength in extra_lora_entries(beat)}
    ):
        cam = re.sub(r"\s*from directly above\b", "", cam, flags=re.I)
    if cam:
        desc.append(cam if cam.endswith(".") else cam + ".")
    for hold_line in _hospital_prompt_holds(ep, beat):
        desc.append(hold_line)
    desc.append(str(beat.get("action") or "").strip().rstrip(".") + ".")
    hold = _look_hold(ep, beat)
    if hold:
        desc.append(hold)
    if keys:
        desc.append("Props in this shot stay locked: " + "; ".join(f"{k} = {str(props[k]).rstrip('.')}" for k in keys) + ".")
    if str(ep.get("violence") or "none") == "game" and beat.get("physics", False):
        desc.append(VIOLENCE_CLAUSE)
        desc.append(REALTIME_CLAUSE)
    vis = _speech_visual(ep, beat)
    if vis:
        desc.append(vis)
    if str(ep.get("slug") or "") == "hospital-exit-adult":
        desc.append("Identity and the subject_definitions look stay locked for the whole clip.")
    else:
        desc.append("Identity, costume, and props stay locked for the whole clip.")
    sfx = str(beat.get("sfx") or "Natural ambience of the place").strip().rstrip(".")
    audio = _speech_audio(ep, beat)
    sound = sfx + "." + (f" {audio}" if audio else "")
    music = str(beat.get("music") or DEFAULT_MUSIC).strip()
    head = ""
    if last_still:
        head = STILL_LAST_HEADER + "\n\n"
    elif source in ("still", "chain"):
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


def validate_beat_prompt(prompt: str, *, source: str, never: list[str] | None = None, still_as: str = "first") -> list[str]:
    errs: list[str] = []
    p = prompt or ""
    if not p.strip():
        return ["prompt empty"]
    last_still = still_as in ("last", "both")
    if last_still:
        if STILL_LAST_HEADER not in p:
            errs.append("last-frame Picture 2 header missing")
        if "<Picture 1>" not in p:
            errs.append("Picture 1 tag missing")
        if "<Picture 2>" not in p:
            errs.append("Picture 2 tag missing")
    elif source in ("still", "chain"):
        if I2VA_HEADER not in p:
            errs.append("I2VA 0.00s Picture 1 header missing")
        if "<Picture 1>" not in p:
            errs.append("Picture 1 tag missing")
    else:
        if "<Picture 1>" in p or I2VA_HEADER in p or STILL_LAST_HEADER in p:
            errs.append("T2V beat must not reference Picture 1")
    for key in ("subject_definitions:", "environment:", "integrated_multimodal_description:", "overall_soundscape:", "non_diegetic_music:"):
        if key not in p:
            errs.append(f"missing {key}")
    if "[Shot 1]" not in p:
        errs.append("missing [Shot 1]")
    if cjk_outside_quotes(p):
        errs.append("Japanese outside 「」 (H3 reads it aloud)")
    for m in QUOTE_RE.finditer(p):
        inner = m.group(0)[1:-1]
        if NON_JP_SPEECH_RE.search(inner) or not KANA_RE.search(inner):
            errs.append(f"quoted speech must be Japanese kana only: 「{inner}」")
    hits = forbidden_hits(p, never=never)
    if hits:
        errs.append(f"forbidden in prompt: {hits}")
    return errs


def extra_lora_entries(beat: dict[str, Any]) -> list[tuple[str, float]]:
    """Per-beat optional LoRAs stacked after the preset (combat on fight shots)."""
    raw = beat.get("extra_loras") or []
    if not isinstance(raw, list):
        return []
    out: list[tuple[str, float]] = []
    for item in raw:
        if isinstance(item, str):
            out.append((item, float(LORA_STRENGTHS.get(item, 1.0))))
            continue
        if isinstance(item, (list, tuple)) and item:
            key = str(item[0])
            try:
                strength = float(item[1]) if len(item) > 1 else float(LORA_STRENGTHS.get(key, 1.0))
            except (TypeError, ValueError):
                strength = float(LORA_STRENGTHS.get(key, 1.0))
            out.append((key, strength))
    return out


def merge_trigger(base: str, beat: dict[str, Any]) -> str:
    """Preset trigger (DY) then the beat trigger (prfight2, prfin1). Empty parts drop."""
    parts = [str(base or "").strip(), str(beat.get("trigger") or "").strip()]
    return "\n".join(p for p in parts if p)


def _extra_lora_errors(beat: dict[str, Any], where: str) -> list[str]:
    errs: list[str] = []
    if beat.get("trigger") and CJK_RE.search(str(beat.get("trigger") or "")):
        errs.append(f"{where}: trigger must be English / LoRA tokens")
    raw = beat.get("extra_loras")
    if raw is None:
        return errs
    if is_ui_beat(beat):
        return errs
    if not isinstance(raw, list):
        return errs + [f"{where}: extra_loras must be a list of keys or [key, strength]"]
    for i, item in enumerate(raw):
        key = ""
        if isinstance(item, str):
            key = item
        elif isinstance(item, (list, tuple)) and item:
            key = str(item[0])
            if len(item) > 1:
                try:
                    s = float(item[1])
                    if s < 0 or s > 2:
                        errs.append(f"{where}: extra_loras[{i}] strength must be 0-2")
                except (TypeError, ValueError):
                    errs.append(f"{where}: extra_loras[{i}] strength must be a number")
        else:
            errs.append(f"{where}: extra_loras[{i}] must be a key or [key, strength]")
            continue
        if key and key not in LORA_FILES:
            errs.append(f"{where}: unknown extra LoRA {key}")
    return errs


def apply_extra_loras(
    preset: dict[str, Any],
    beat: dict[str, Any],
    loras_dir: Path | str | None,
    unet: str = "",
    *,
    allow_combat: bool | None = None,
    skip_note: str = "",
) -> dict[str, Any]:
    """Copy a resolved preset and append beat.extra_loras. Combat never stacks with LightX2V turbo.

    When combat actually loads, the sample plan becomes euler+beta at 12 (Larry 8-step muddies the hit).
    Turbo fallback keeps the preset 4-step euler+simple and ignores beat.steps.
    TURBO-hybrid loads Combat only when High-Memory opt-in is on (A100 40GB otherwise OOM).
    """
    extra = extra_lora_entries(beat)
    out = dict(preset)
    if not extra:
        return _apply_beat_sampler(out, beat, combat_on=False)
    stack = list(preset.get("stack") or [])
    notes = list(preset.get("notes") or [])
    names = " ".join(str(s[0]).lower() for s in stack)
    turbo = "fl2v_turbo" in names
    if allow_combat is None:
        allow_combat, auto_note = combat_lora_allowed(unet=unet, combat="", high_mem=False)
        if auto_note and auto_note not in notes:
            notes.append(auto_note)
    elif skip_note and skip_note not in notes:
        notes.append(skip_note)
    combat_on = False
    combat_requested = any(key == "combat" for key, _s in extra)
    for key, strength in extra:
        fname = LORA_FILES.get(key)
        if not fname:
            notes.append(f"unknown extra LoRA dropped: {key}")
            continue
        if key == "cinema":
            notes.append("cinematic LoRA skipped (heavy; not a speed/quality preset)")
            continue
        if key == "combat" and turbo:
            notes.append("combat LoRA skipped (never with LightX2V turbo)")
            continue
        if key == "combat" and not allow_combat:
            note = skip_note or "combat LoRA skipped (never with LightX2V turbo or TURBO-hybrid UNet)"
            if note not in notes:
                notes.append(note)
            continue
        present = loras_dir is None or (Path(loras_dir) / fname).is_file()
        if not present:
            notes.append(f"optional extra LoRA missing, dropped: {fname}")
            continue
        stack.append((fname, float(strength)))
        if key == "combat":
            combat_on = True
    out["stack"] = stack
    out["notes"] = notes
    if combat_requested and not combat_on:
        return out
    return _apply_beat_sampler(out, beat, combat_on=combat_on)


def _apply_beat_sampler(preset: dict[str, Any], beat: dict[str, Any], *, combat_on: bool) -> dict[str, Any]:
    """Combat defaults to 12 euler+beta. Other beats only honor an authored steps/sampler."""
    out = dict(preset)
    notes = list(out.get("notes") or [])
    if combat_on:
        steps = beat.get("steps", COMBAT_STEPS)
        sampler = beat.get("sampler") or COMBAT_SAMPLER
        scheduler = beat.get("scheduler") or COMBAT_SCHEDULER
        out["steps"] = int(steps)
        out["sampler"] = str(sampler)
        out["scheduler"] = str(scheduler)
        notes.append(f"combat sampler {sampler}+{scheduler} {int(steps)} steps")
        out["notes"] = notes
        return out
    if beat.get("steps") is not None:
        out["steps"] = int(beat["steps"])
    if beat.get("sampler"):
        out["sampler"] = str(beat["sampler"])
    if beat.get("scheduler"):
        out["scheduler"] = str(beat["scheduler"])
    return out


def _collect_extra_lora_keys(node: Any, keys: list[str]) -> None:
    """Every extra LoRA in the raw tree, including overlays that the chosen route does not expand."""
    if isinstance(node, dict):
        if "extra_loras" in node:
            for key, _strength in extra_lora_entries(node):
                if key not in keys:
                    keys.append(key)
        for value in node.values():
            _collect_extra_lora_keys(value, keys)
    elif isinstance(node, list):
        for value in node:
            _collect_extra_lora_keys(value, keys)


def ensure_episode_loras(ep: dict[str, Any], loras_dir: Path | str) -> list[str]:
    """Fetch optional extra LoRAs into Drive models/loras. A file already over 1MB is left in place."""
    root = Path(loras_dir)
    notes: list[str] = []
    keys: list[str] = []
    for key in (ep.get("render") or {}).get("lora_prefetch") or []:
        name = str(key)
        if name not in keys:
            keys.append(name)
    _collect_extra_lora_keys(ep, keys)
    for key in keys:
        fname = LORA_FILES.get(key)
        url = LORA_URLS.get(key)
        if not fname or not url:
            continue
        dest = root / fname
        if dest.is_file() and dest.stat().st_size > 1_000_000:
            notes.append(f"skip existing {fname}")
            continue
        print("fetch LoRA", fname)
        if fetch_text(url, dest, min_bytes=1_000_000):
            notes.append(f"fetched {fname}")
        else:
            notes.append(f"fetch failed {fname}")
    return notes


def resolve_unet(
    ep: dict[str, Any],
    diff_dir: Path | str,
    *,
    models_root: Path | str | None = None,
) -> str:
    """Exact checkpoint for this episode. Erotic never falls back to stock; stock never picks Eros Max."""
    key = episode_checkpoint(ep)
    spec = CHECKPOINTS.get(key)
    if not spec:
        raise EpisodeError(f"unknown checkpoint {key}")
    if spec["erotic"] and episode_lane(ep) != "erotic":
        raise EpisodeError("erotic checkpoint blocked on a stock lane")
    if spec["erotic"]:
        min_bytes = int(spec.get("min_bytes") or 1_000_000)
        if models_root:
            found = locate_erotic_checkpoint(models_root, spec)
            if found is not None:
                return found.name
        exact = Path(diff_dir) / str(spec["file"])
        if exact.is_file() and is_erotic_unet_name(exact.name) and exact.stat().st_size >= min_bytes:
            return exact.name
        raise EpisodeError(f"erotic checkpoint missing: {spec['file']} (stock fallback is forbidden)")
    return pick_stock_fl2va(diff_dir)


def ensure_episode_checkpoint(ep: dict[str, Any], models_root: Path | str) -> list[str]:
    """Use a Drive copy of 10Eros_Max if one exists; otherwise fetch into models/erotic/.

    Never download it for a stock episode. Incomplete copies stay as `*.part`.
    """
    notes: list[str] = []
    key = episode_checkpoint(ep)
    spec = CHECKPOINTS[key]
    if not spec["erotic"]:
        return notes
    if episode_lane(ep) != "erotic":
        raise EpisodeError("refusing to fetch an erotic checkpoint for a stock episode")
    dest = erotic_checkpoint_path(models_root, spec)
    min_bytes = int(spec.get("min_bytes") or 1_000_000)
    expected = int(spec.get("expected_bytes") or 0)
    found = locate_erotic_checkpoint(models_root, spec)
    if found is not None:
        print("reuse Drive Eros Max", found, found.stat().st_size, "no HuggingFace fetch")
        notes.append(f"reused Drive copy {found}")
        return notes
    if _checkpoint_ready(dest, min_bytes):
        notes.append(f"checkpoint ready {spec['file']}")
        return notes
    url = str(spec.get("url") or "")
    if not url:
        raise EpisodeError(f"erotic checkpoint missing and no url: {spec['file']}")
    print("fetch checkpoint", spec["file"], "(resume ok, ~21GB, keep Run all if it stops)")
    if fetch_resumable(url, dest, min_bytes=min_bytes, expected_bytes=expected):
        notes.append(f"fetched {spec['file']}")
        return notes
    part = dest.with_name(dest.name + ".part")
    have = 0
    if dest.is_file():
        have = dest.stat().st_size
    elif part.is_file():
        have = part.stat().st_size
    need = expected or min_bytes
    raise EpisodeError(
        f"fetch incomplete {spec['file']}: {have} / {need} bytes kept on Drive. "
        "stock fallback is forbidden. Run all again (same A100); it continues the .part"
    )


def stage_erotic_unet(ep: dict[str, Any], models_root: Path | str) -> str:
    """Point Comfy at the erotic UNet. Drive FUSE cannot symlink (Errno 95); use the file in place."""
    spec = CHECKPOINTS[episode_checkpoint(ep)]
    if not spec["erotic"]:
        return resolve_unet(ep, Path(models_root) / "diffusion_models", models_root=models_root)
    min_bytes = int(spec.get("min_bytes") or 1_000_000)
    found = locate_erotic_checkpoint(models_root, spec)
    if found is None:
        raise EpisodeError(f"erotic checkpoint missing: {spec['file']} (stock fallback is forbidden)")
    dest = Path(models_root) / "diffusion_models" / found.name
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        found_r = found.resolve()
    except OSError:
        found_r = found
    if dest.exists():
        try:
            same = dest.resolve() == found_r
        except OSError:
            same = dest == found
        if same and _checkpoint_ready(dest, min_bytes):
            return found.name
        if _checkpoint_ready(dest, min_bytes) and is_erotic_unet_name(dest.name):
            return dest.name
        if dest.stat().st_size < min_bytes and is_erotic_unet_name(dest.name):
            dest.unlink()
        elif dest.exists() and not is_erotic_unet_name(dest.name):
            raise EpisodeError(f"refusing to replace {dest.name} with the erotic checkpoint")
    if dest.exists() or dest.is_symlink():
        return found.name
    try:
        dest.symlink_to(found_r)
    except OSError as e:
        if dest.parent.resolve() == found_r.parent.resolve() and is_erotic_unet_name(found_r.name):
            print("Drive cannot symlink; using", found_r.name)
            return found_r.name
        print("eros symlink skipped", dest, "->", found_r, e)
        return found.name
    return found.name


def beat_prompts(
    ep: dict[str, Any],
    *,
    trigger: str = "",
    camera_pack: str | None = None,
) -> list[tuple[dict[str, Any], str, list[str]]]:
    """Prompts for every beat that can reach the GPU (ui beats and still-less reuse beats have none)."""
    never = [str(x) for x in ((ep.get("homage") or {}).get("never") or [])]
    pack = camera_pack if camera_pack is not None else episode_camera_pack(ep)
    indexes = gpu_index_map(ep)
    out = []
    for beat in ep.get("beats") or []:
        if not beat_renders(beat):
            continue
        prompt = build_beat_prompt(
            ep,
            beat,
            trigger=merge_trigger(trigger, beat),
            camera_pack=pack,
            gpu_index=indexes.get(str(beat.get("id") or ""), 0),
        )
        errs = validate_beat_prompt(prompt, source=beat_source(beat), still_as=beat_still_as(beat), never=never)
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


def _civitai_token() -> str:
    env = str(os.environ.get("CIVITAI_API_TOKEN") or "").strip()
    if env:
        return env
    if _COLAB_USERDATA is None:
        return ""
    try:
        return str(_COLAB_USERDATA.get("CIVITAI_API_TOKEN") or "").strip()
    except Exception:
        return ""


def fetch_text(url: str, dest: Path, *, min_bytes: int = 100, token: str = "") -> bool:
    try:
        dest.parent.mkdir(parents=True, exist_ok=True)
        civitai = "civitai.com" in str(url).lower()
        tok = token or (_civitai_token() if civitai else "")
        if tok or civitai:
            headers = {"User-Agent": "h3-episode"}
            if tok:
                headers["Authorization"] = f"Bearer {tok}"
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=120) as resp, open(dest, "wb") as out:
                while True:
                    chunk = resp.read(1024 * 1024)
                    if not chunk:
                        break
                    out.write(chunk)
            return dest.is_file() and dest.stat().st_size > min_bytes
        urllib.request.urlretrieve(url, dest)
        return dest.is_file() and dest.stat().st_size > min_bytes
    except Exception as e:  # network
        print("fetch fail", url, e)
        return False


def _resume_download_once(url: str, part: Path) -> None:
    """One pass with wget/curl Range resume. Partial file is kept on failure."""
    part.parent.mkdir(parents=True, exist_ok=True)
    wget = shutil.which("wget")
    if wget:
        r = subprocess.run(
            [wget, "-c", "--tries=3", "--timeout=60", "-O", str(part), url],
            check=False,
        )
        if r.returncode == 0:
            return
        raise OSError(f"wget exit {r.returncode}")
    curl = shutil.which("curl")
    if curl:
        r = subprocess.run(
            ["curl", "-fL", "-C", "-", "--retry", "3", "-o", str(part), url],
            check=False,
        )
        if r.returncode == 0:
            return
        raise OSError(f"curl exit {r.returncode}")
    existing = part.stat().st_size if part.is_file() else 0
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "h3-episode", "Range": f"bytes={existing}-"},
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        status = int(getattr(resp, "status", 200) or 200)
        mode = "ab" if existing and status == 206 else "wb"
        with open(part, mode) as out:
            while True:
                chunk = resp.read(1024 * 1024)
                if not chunk:
                    break
                out.write(chunk)


def fetch_resumable(
    url: str,
    dest: Path,
    *,
    min_bytes: int,
    expected_bytes: int = 0,
    tries: int = 4,
) -> bool:
    """Download a large weight to Drive, resuming `*.part` across Colab reruns."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    part = dest.with_name(dest.name + ".part")
    need = int(expected_bytes or min_bytes)
    if dest.is_file() and dest.stat().st_size >= min_bytes:
        return True
    if dest.is_file() and dest.stat().st_size > 0:
        print("incomplete file, resume as .part", dest.name, dest.stat().st_size)
        dest.replace(part)
    delay = 4
    for i in range(max(1, int(tries))):
        have = part.stat().st_size if part.is_file() else 0
        print(f"fetch {dest.name} try {i + 1}/{tries} have {have} need {need}")
        try:
            _resume_download_once(url, part)
        except (OSError, urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
            print("fetch fail", dest.name, e)
        have = part.stat().st_size if part.is_file() else 0
        if have >= min_bytes and (not expected_bytes or have >= int(expected_bytes * 0.99)):
            part.replace(dest)
            print("fetched", dest.name, dest.stat().st_size)
            return True
        if i + 1 < tries:
            time.sleep(delay)
            delay = min(delay * 2, 32)
    return False


def _episode_beat_ids(path: Path) -> list[str]:
    if not path.is_file():
        return []
    try:
        return [str(b.get("id") or "") for b in (load_episode(path).get("beats") or [])]
    except Exception:
        return []


def bootstrap_episode(slug: str, root: Path | str, *, branch: str | None = None, repo: str = REPO) -> list[str]:
    """Pull episode.json from GitHub each run (Drive keeps the first packing otherwise). Stills never overwrite."""
    root = Path(root)
    ensure_episode_tree(root)
    br = branch or os.environ.get("H3_HELPER_BRANCH") or BRANCH
    fetched: list[str] = []
    ep_path = root / "episode.json"
    prev_ids = _episode_beat_ids(ep_path)
    staging = root / "logs" / "episode.json.fetch"
    if fetch_text(github_raw(f"{REPO_EPISODES_DIR}/{slug}/episode.json", repo=repo, branch=br), staging):
        new_ids = _episode_beat_ids(staging)
        shutil.copy2(staging, ep_path)
        fetched.append("episode.json")
        if prev_ids and new_ids != prev_ids:
            print(f"episode.json refreshed: {len(prev_ids)} beats → {len(new_ids)} beats")
    elif not ep_path.is_file():
        raise EpisodeError(f"episode.json missing in {root} and not on GitHub ({br})")
    else:
        print(f"episode.json fetch failed, keeping Drive copy ({len(prev_ids)} beats)")
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
    lookup = name if name in PRESETS else canonical_preset(name)
    if lookup not in PRESETS:
        raise EpisodeError(f"unknown preset {name}")
    spec = PRESETS[lookup]
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
            fb = fallback if fallback in PRESETS else canonical_preset(fallback)
            if fb == lookup or fb not in PRESETS:
                raise EpisodeError(f"preset {name} unusable and no fallback")
            out = resolve_preset(fb, loras_dir, fallback=fb)
            out["notes"] = notes + out.get("notes", [])
            return out
    names = [s[0].lower() for s in stack]
    if any("turbo_v4" in n for n in names) and any("fl2v_turbo" in n for n in names):
        raise EpisodeError("Larry and LightX2V turbo never stack")
    if any("cinematic" in n for n in names):
        raise EpisodeError("cinematic LoRA is not a speed/quality preset")
    out: dict[str, Any] = {
        "name": name,
        "canonical": canonical_preset(name),
        "stack": stack,
        "steps": int(spec["steps"]),
        "trigger": str(spec.get("trigger") or ""),
        "notes": notes,
    }
    if spec.get("sampler"):
        out["sampler"] = str(spec["sampler"])
    if spec.get("scheduler"):
        out["scheduler"] = str(spec["scheduler"])
    return out


def apply_unet_preset_rules(preset: dict[str, Any], unet: str) -> dict[str, Any]:
    """TURBO-hybrid already has turbo baked in. LoRA patches requantize INT8 and OOM A100 40GB."""
    if not is_turbo_hybrid_unet(unet):
        return preset
    skip_needles = ("fl2v_turbo", "turbo_v4")
    kept: list[tuple[str, float]] = []
    dropped: list[str] = []
    for fname, strength in preset.get("stack") or []:
        low = str(fname).lower()
        if any(needle in low for needle in skip_needles):
            dropped.append(str(fname))
            continue
        kept.append((fname, float(strength)))
    if not dropped:
        return preset
    out = dict(preset)
    out["stack"] = kept
    notes = list(preset.get("notes") or [])
    notes.append("LoRA skipped on TURBO-hybrid UNet (VRAM; turbo is baked in): " + ", ".join(dropped))
    out["notes"] = notes
    return out


def apply_sampler_plan(g: dict[str, Any], preset: dict[str, Any]) -> dict[str, Any]:
    """Patch KSampler after the I2VA/T2V builder. Daily Larry stays euler+simple 8 unless the preset says otherwise."""
    if "22" in g and preset.get("sampler"):
        g["22"]["inputs"]["sampler_name"] = str(preset["sampler"])
    if "23" in g:
        if preset.get("scheduler"):
            g["23"]["inputs"]["scheduler"] = str(preset["scheduler"])
        if preset.get("steps") is not None:
            g["23"]["inputs"]["steps"] = int(preset["steps"])
    return g


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
    last_image: str | None = None,
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
        g = build_i2va_graph(first_image=first_image, last_image=last_image, **common)
    if lora_name and has_lora_loader:
        chain_extra_loras(g, stack[1:])
    apply_sampler_plan(g, preset)
    errs = assert_t2v_graph(g) if source == "t2v" else assert_i2va_graph(g, expect_last=bool(last_image), homage=False)
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
    last_image: str | None = None,
    unet: str | None = None,
    port: int = PORT,
    object_info: dict[str, Any] | None = None,
    poster: Callable[..., Any] = post_prompt,
    waiter: Callable[..., Any] = wait_prompt,
) -> dict[str, Any]:
    """Keep the canvas. On OOM, unload VRAM and retry the same length once, then shorten (10→8→6).
    A successful beat does not unload. Never drop the first frame or last-frame still."""
    obj = object_info or {}
    unet = unet or pick_stock_fl2va(comfy_dir / "models/diffusion_models")
    out_root = comfy_dir / "output"
    before = newest_mp4(out_root)
    last_err: Any = None
    for dur in durations:
        for attempt in (1, 2):
            result = _render_beat_once(
                source=source,
                first_image=first_image,
                prompt=prompt,
                unet=unet,
                preset=preset,
                canvas=canvas,
                dur=dur,
                seed=seed,
                filename_prefix=filename_prefix,
                last_image=last_image,
                obj=obj,
                out_root=out_root,
                before=before,
                port=port,
                poster=poster,
                waiter=waiter,
            )
            if result.get("ok"):
                return result["payload"]
            last_err = result.get("error")
            if result.get("oom"):
                comfy_free(port)
                if attempt == 1:
                    print("free VRAM and retry", filename_prefix, f"{dur:.0f}s")
                    continue
                break
            raise EpisodeError(str(last_err))
    raise EpisodeError(f"all durations OOM: {last_err}")


def _render_beat_once(
    *,
    source: str,
    first_image: str | None,
    prompt: str,
    unet: str,
    preset: dict[str, Any],
    canvas: tuple[int, int],
    dur: float,
    seed: int,
    filename_prefix: str,
    last_image: str | None,
    obj: dict[str, Any],
    out_root: Path,
    before: Path | None,
    port: int,
    poster: Callable[..., Any],
    waiter: Callable[..., Any],
) -> dict[str, Any]:
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
        last_image=last_image,
    )
    print("render", filename_prefix, f"{canvas[0]}x{canvas[1]}", f"{dur:.0f}s", "steps", preset.get("steps"), "loras", [s[0] for s in preset.get("stack") or []])
    res, err = poster(g, port)
    if err:
        return {"ok": False, "oom": is_oom_error(err), "error": err}
    if not (res and "prompt_id" in res):
        return {"ok": False, "oom": False, "error": str(res)}
    ok, payload = waiter(res["prompt_id"], port)
    if ok:
        videos = collect_output_videos(payload, out_root)
        fresh = newest_mp4(out_root)
        if fresh and fresh not in videos and (before is None or fresh != before):
            videos.append(fresh)
        return {
            "ok": True,
            "payload": {"videos": [str(v) for v in videos], "duration_s": dur, "canvas": f"{canvas[0]}x{canvas[1]}"},
        }
    return {"ok": False, "oom": is_oom_error(payload), "error": payload}


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
    preset_name = canonical_preset(str((ep.get("render") or {}).get("preset") or "fast"))
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


def hud_pngs(ep: dict[str, Any], beat: dict[str, Any], out_size: tuple[int, int], png_dir: Path, *, window_s: float | None = None) -> dict[str, Any]:
    """All overlays of one beat as PNGs: hud, mission (keyword coloured), completion flash, menu, timed subtitles.

    `hud.visible: false` is the cutscene grammar of the reference: dialogue shots drop bars and mission line
    and keep only subtitles. The completion flash still fires so a cutscene can close a mission.
    """
    hud_cfg = ep.get("hud") or {}
    hud = beat.get("hud") or {}
    theme_name = str(hud_cfg.get("theme") or "bandai")
    font = find_font(hud_cfg.get("font") or None)
    png_dir.mkdir(parents=True, exist_ok=True)
    bid = beat["id"]
    visible = bool(hud.get("visible", True))
    out: dict[str, Any] = {"hud": None, "mission": None, "complete": None, "menu": None, "subtitles": []}
    if visible:
        layer = render_hud_layer(out_size, hud, theme_name=theme_name, district=str(hud_cfg.get("district_label") or ""), icons=list(hud_cfg.get("icons") or []), font_path=font)
        out["hud"] = png_dir / f"{bid}-hud.png"
        layer.save(out["hud"])
        mission = render_mission_layer(out_size, str(hud.get("mission") or ""), theme_name=theme_name, font_path=font, keyword=str(hud.get("mission_keyword") or ""))
        out["mission"] = png_dir / f"{bid}-mission.png"
        mission.save(out["mission"])
    if hud.get("complete"):
        cmp_layer = render_complete_layer(out_size, str(hud_cfg.get("complete_text") or "ミッション完了"), theme_name=theme_name, font_path=font)
        out["complete"] = png_dir / f"{bid}-complete.png"
        cmp_layer.save(out["complete"])
    if is_ui_beat(beat):
        menu = beat.get("menu") or {}
        layer = render_menu_layer(out_size, title=str(menu.get("title") or ""), items=[str(x) for x in menu.get("items") or []], selected=int(menu.get("selected", 0) or 0), theme_name=theme_name, font_path=font)
        out["menu"] = png_dir / f"{bid}-menu.png"
        layer.save(out["menu"])
    speech = beat.get("speech") or []
    if speech and hud_cfg.get("subtitles", True):
        seconds = float(window_s if window_s is not None else beat_window(ep, beat)[1])
        for i, (item, (a, b)) in enumerate(zip(speech, subtitle_windows(speech, seconds))):
            text = str(item.get("text") or item.get("line") or "")
            layer = render_subtitle_layer(out_size, text, theme_name=theme_name, font_path=font, above_mission=visible)
            p = png_dir / f"{bid}-sub{i}.png"
            layer.save(p)
            out["subtitles"].append((p, a, b))
    return out


def reuse_source(ep: dict[str, Any], beat: dict[str, Any], root: Path) -> Path | None:
    """raw/<beat>.mp4 of a sibling episode named by `reuse: "slug/beat-id"` (same Drive episodes/ folder)."""
    reuse = str(beat.get("reuse") or "")
    m = REUSE_RE.match(reuse)
    if not m:
        return None
    return Path(root).parent / m.group(1) / "raw" / f"{m.group(2)}.mp4"


def materialize_reuse(ep: dict[str, Any], root: Path | str, *, fresh: bool = False) -> dict[str, str]:
    """Copy reusable takes into raw/ so the rest of the pipeline sees plain raw clips. Returns beat id → source."""
    root = Path(root)
    copied: dict[str, str] = {}
    for beat in ep.get("beats") or []:
        src = reuse_source(ep, beat, root)
        if src is None:
            continue
        dest = root / "raw" / f"{beat['id']}.mp4"
        if dest.is_file() and not fresh:
            continue
        if not src.is_file():
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        copied[beat["id"]] = str(src)
    return copied


def previous_footage(ep: dict[str, Any], idx: int, root: Path, raw: Path, *, apply_trim: bool = True) -> tuple[Path, float]:
    """(raw clip, time inside it) of the nearest earlier non-ui beat's window end. Chain frames and menu freezes start here."""
    beats = ep.get("beats") or []
    for j in range(idx - 1, -1, -1):
        prev = beats[j]
        if is_ui_beat(prev):
            continue
        clip = raw / f"{prev['id']}.mp4"
        if not clip.is_file():
            raise EpisodeError(f"{beats[idx]['id']}: needs the previous clip first: {clip}")
        start, seconds = beat_window(ep, prev) if apply_trim else (0.0, probe_duration(clip))
        return clip, start + seconds - 0.12
    raise EpisodeError(f"{beats[idx]['id']}: no footage before this beat")


def materialize_ui_beat(ep: dict[str, Any], idx: int, root: Path, raw: Path, *, apply_trim: bool = True) -> Path:
    """A ui beat's raw clip: the previous beat frozen at its cut point, held for `seconds`. No GPU."""
    beat = (ep.get("beats") or [])[idx]
    clip, at = previous_footage(ep, idx, root, raw, apply_trim=apply_trim)
    frame = extract_frame(clip, root / "input" / f"{beat['id']}-freeze.jpg", at_s=at)
    size = probe_video_size(clip)
    if size == (0, 0):
        size = canvas_for(ep)
    return still_clip(frame, raw / f"{beat['id']}.mp4", seconds=float(beat.get("seconds") or UI_SECONDS[0]), canvas=size)


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


def _fail_card_image(ep: dict[str, Any], root: Path, raw: Path, out_size: tuple[int, int], png_dir: Path, *, apply_trim: bool) -> Path | None:
    """The ミッション失敗 freeze: last beat's cut point (default), an authored image, or plain dark."""
    cards = ep.get("cards") or {}
    fail = cards.get("fail")
    if not fail:
        return None
    hud_cfg = ep.get("hud") or {}
    font = find_font(hud_cfg.get("font") or None)
    beats = ep.get("beats") or []
    img: Path | None = None
    rel = fail_image_rel(ep)
    if rel:
        img = root / rel
    elif str(fail.get("image") or "last-frame") == "last-frame" and beats:
        clip, at = previous_footage(ep, len(beats), root, raw, apply_trim=apply_trim)
        img = extract_frame(clip, root / "input" / "fail-freeze.jpg", at_s=at)
    png = png_dir / "card-fail.png"
    render_fail_card(out_size, text=str(fail.get("text") or FAIL_TEXT_DEFAULT), reason=str(fail.get("reason") or ""), image=img, theme_name=str(hud_cfg.get("theme") or "bandai"), font_path=font).save(png)
    return png


def finish_episode(ep: dict[str, Any], root: Path | str, *, raw_dir: Path | str | None = None, out_name: str | None = None, apply_trim: bool = True) -> Path:
    """raw/<beat>.mp4 → hud/<beat>.mp4 → cards → final/<slug>-<stamp>.mp4 (+ latest.mp4).

    Reuse beats are copied in when missing, ui beats are frozen from the previous clip, trims are applied
    (`apply_trim=False` for stills previews whose held stills are shorter than any trim window).
    """
    root = Path(root)
    ensure_episode_tree(root)
    raw = Path(raw_dir) if raw_dir else root / "raw"
    if raw == root / "raw":
        materialize_reuse(ep, root)
    out_size = output_size_for(ep)
    png_dir = root / "hud" / "png"
    cs = card_seconds(ep)
    ordered: list[Path] = []
    for idx, beat in enumerate(ep.get("beats") or []):
        if is_ui_beat(beat):
            src = materialize_ui_beat(ep, idx, root, raw, apply_trim=apply_trim)
            start, seconds = 0.0, float(beat.get("seconds") or UI_SECONDS[0])
        else:
            src = raw / f"{beat['id']}.mp4"
            if not src.is_file():
                raise EpisodeError(f"raw clip missing: {src}")
            start, seconds = beat_window(ep, beat) if apply_trim else (0.0, probe_duration(src))
        pngs = hud_pngs(ep, beat, out_size, png_dir, window_s=seconds)
        dest = root / "hud" / f"{beat['id']}.mp4"
        compose_beat(
            src,
            dest,
            out_size=out_size,
            hud_png=pngs["hud"],
            mission_png=pngs["mission"],
            complete_png=pngs["complete"],
            trim_start=start if apply_trim else 0.0,
            trim_seconds=seconds if apply_trim else None,
            subtitles=pngs["subtitles"],
            menu_png=pngs["menu"],
        )
        ordered.append(dest)
    title_png, end_png = _card_images(ep, root, out_size, png_dir)
    fail_png = _fail_card_image(ep, root, raw, out_size, png_dir, apply_trim=apply_trim)
    clips: list[Path] = []
    if title_png:
        clips.append(card_clip(title_png, root / "hud" / "00-title.mp4", seconds=cs["title"], out_size=out_size))
    clips.extend(ordered)
    if fail_png:
        clips.append(card_clip(fail_png, root / "hud" / "98-fail.mp4", seconds=cs["fail"], out_size=out_size, fade_in_s=0.0))
    if end_png:
        clips.append(card_clip(end_png, root / "hud" / "99-end.mp4", seconds=cs["end"], out_size=out_size))
    cfg = ep.get("stitch") or {}
    name = out_name or f"{ep['slug']}-{_now()}.mp4"
    final = root / "final" / name
    stitch(clips, final, out_size=out_size, transition=str(cfg.get("transition") or "xfade"), xfade_s=float(cfg.get("xfade_s", 0.35)), loudnorm=bool(cfg.get("loudnorm", True)))
    latest = root / "final" / "latest.mp4"
    shutil.copy2(final, latest)
    (root / "final" / "latest.txt").write_text(final.name + "\n", encoding="utf-8")
    return final


def _stage_frame(src: Path, dest: Path, canvas: tuple[int, int], comfy_input: Path | None) -> str:
    stage_still(src, dest, canvas)
    if comfy_input is None:
        return dest.name
    return stage_image_into_input(dest, comfy_input)


def _first_frame_for(beat: dict[str, Any], idx: int, ep: dict[str, Any], root: Path, canvas: tuple[int, int], comfy_input: Path | None) -> str | None:
    source = beat_source(beat)
    if source == "t2v":
        return None
    staged = root / "input" / f"{beat['id']}.jpg"
    if beat_still_as(beat) == "last":
        prev_clip, at = previous_footage(ep, idx, root, root / "raw")
        tmp = root / "input" / f"{beat['id']}-from.jpg"
        extract_frame(prev_clip, tmp, at_s=at)
        return _stage_frame(tmp, staged, canvas, comfy_input)
    if source == "still" or beat_still_as(beat) == "both":
        if not beat.get("still"):
            raise EpisodeError(f"{beat['id']}: reuse source not on disk and no still to render from")
        return _stage_frame(root / str(beat["still"]), staged, canvas, comfy_input)
    prev_clip, at = previous_footage(ep, idx, root, root / "raw")
    tmp = root / "input" / f"{beat['id']}-last.jpg"
    extract_frame(prev_clip, tmp, at_s=at)
    return _stage_frame(tmp, staged, canvas, comfy_input)


def _last_frame_for(beat: dict[str, Any], root: Path, canvas: tuple[int, int], comfy_input: Path | None) -> str | None:
    if not uses_last_still(beat):
        return None
    staged = root / "input" / f"{beat['id']}-end.jpg"
    return _stage_frame(root / str(beat["still"]), staged, canvas, comfy_input)


def run_episode(
    ep: dict[str, Any],
    root: Path | str,
    *,
    models_root: Path | str | None = None,
    comfy_dir: Path | str | None = None,
    dry_run: bool = False,
    fresh: bool = False,
    preset_override: str | None = None,
    camera_pack_override: str | None = None,
    connect_override: str | None = None,
    end_connect_override: str | None = None,
    combat_override: str | None = None,
    story_override: str | None = None,
    invite_pose_override: str | None = None,
    toilet_override: str | None = None,
    gin_override: str | None = None,
    tsuno_override: str | None = None,
    appear_override: str | dict[str, Any] | None = None,
    scenes_override: str | dict[str, Any] | None = None,
    rei_mast_override: str | None = None,
    rei_toilet_override: str | None = None,
    rei_beast_override: str | None = None,
    rei_moth_override: str | None = None,
    rei_attack_override: str | None = None,
    rei_kiss_override: str | None = None,
    rei_oral_override: str | None = None,
    rei_pose_override: str | None = None,
    port: int = PORT,
    object_info: dict[str, Any] | None = None,
    poster: Callable[..., Any] = post_prompt,
    waiter: Callable[..., Any] = wait_prompt,
) -> Path:
    """The one click: preflight → every beat → HUD → cards → stitch. Resumes from raw/."""
    root = Path(root)
    ensure_episode_tree(root)
    ep = prepare_episode(
        ep,
        connect_override=connect_override,
        end_connect_override=end_connect_override,
        camera_pack_override=camera_pack_override,
        preset_override=preset_override,
        combat_override=combat_override,
        story_override=story_override,
        invite_pose_override=invite_pose_override,
        toilet_override=toilet_override,
        gin_override=gin_override,
        tsuno_override=tsuno_override,
        appear_override=appear_override,
        scenes_override=scenes_override,
        rei_mast_override=rei_mast_override,
        rei_toilet_override=rei_toilet_override,
        rei_beast_override=rei_beast_override,
        rei_moth_override=rei_moth_override,
        rei_attack_override=rei_attack_override,
        rei_kiss_override=rei_kiss_override,
        rei_oral_override=rei_oral_override,
        rei_pose_override=rei_pose_override,
    )
    print(
        describe_run(
            connect=episode_connect(ep),
            end_connect=episode_end_connect(ep),
            camera=episode_camera_pack(ep),
            preset=str((ep.get("render") or {}).get("preset") or ""),
            combat=episode_combat(ep),
            story=episode_story(ep),
            invite_pose=episode_invite_pose(ep),
            toilet=episode_toilet(ep),
            gin=episode_gin(ep),
            tsuno=episode_tsuno(ep),
            appear=episode_appear(ep),
            scenes=(ep.get("render") or {}).get("scenes"),
            episode=str(ep.get("slug") or ""),
            rei_mast=str((ep.get("render") or {}).get("rei_mast") or ""),
            rei_toilet=str((ep.get("render") or {}).get("rei_toilet") or ""),
            rei_beast=str((ep.get("render") or {}).get("rei_beast") or ""),
            rei_moth=str((ep.get("render") or {}).get("rei_moth") or ""),
            rei_attack=str((ep.get("render") or {}).get("rei_attack") or ""),
            rei_kiss=str((ep.get("render") or {}).get("rei_kiss") or ""),
            rei_oral=str((ep.get("render") or {}).get("rei_oral") or ""),
            rei_pose=str((ep.get("render") or {}).get("rei_pose") or ""),
        )
    )
    errs = preflight(ep, root)
    if errs:
        raise EpisodeError("preflight failed:\n- " + "\n- ".join(errs))
    canvas = canvas_for(ep)
    render_cfg = ep.get("render") or {}
    preset_name = str(preset_override or render_cfg.get("preset") or "fast")
    fallback = str(render_cfg.get("fallback_preset") or "fast")
    pack_name = episode_camera_pack(ep, camera_pack_override)
    if pack_name and pack_name not in CAMERA_PACKS:
        raise EpisodeError(f"unknown camera_pack {pack_name}")
    seed = int(render_cfg.get("seed") or 42)
    status = load_status(root)
    status.update({
        "slug": ep.get("slug"),
        "canvas": f"{canvas[0]}x{canvas[1]}",
        "preset_requested": preset_name,
        "camera_pack": pack_name,
        "connect": episode_connect(ep),
        "lane": episode_lane(ep),
        "checkpoint": episode_checkpoint(ep),
        "dry_run": bool(dry_run),
    })
    comfy = Path(comfy_dir or os.environ.get("H3_COMFY_DIR") or COMFY_DIR_DEFAULT)
    comfy_input: Path | None = None
    loras_dir: Path | None = None
    preset: dict[str, Any]
    unet_name = str(CHECKPOINTS.get(episode_checkpoint(ep), {}).get("file") or "")
    if dry_run:
        preset = resolve_preset(preset_name, None, fallback=fallback)
        if episode_checkpoint(ep) == "eros-max":
            preset = apply_unet_preset_rules(preset, unet_name)
    else:
        models = Path(models_root or os.environ.get("H3_MODELS_ROOT") or (Path(os.environ.get("H3_DRIVE_ROOT") or DRIVE_ROOT_DEFAULT) / "models"))
        ensure_comfy(comfy, root, models, need_r2v=False)
        vram = comfy_vram_for_lane(episode_lane(ep))
        start_comfy(comfy, port=port, vram=vram)
        print("comfy vram", vram)
        loras_dir = models / "loras"
        for note in ensure_episode_loras(ep, loras_dir):
            print("lora:", note)
        for note in ensure_episode_checkpoint(ep, models):
            print("checkpoint:", note)
        unet = stage_erotic_unet(ep, models)
        unet_name = unet
        print("unet", unet, "lane", episode_lane(ep), "checkpoint", episode_checkpoint(ep))
        preset = apply_unet_preset_rules(resolve_preset(preset_name, loras_dir, fallback=fallback), unet)
        comfy_input = comfy / "input"
        if object_info is None:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/object_info", timeout=60) as r:
                object_info = json.loads(r.read().decode())
            if "MiniMaxH3ImageToVideo" not in (object_info or {}):
                raise EpisodeError("MiniMaxH3ImageToVideo missing in ComfyUI")
    vram_gb = detect_vram_gb(dry_run=dry_run)
    ram_gb = 0.0 if dry_run else detect_ram_gb()
    high_mem = is_high_mem(vram_gb=vram_gb, ram_gb=ram_gb)
    allow_combat, combat_note = combat_lora_allowed(
        unet=unet_name,
        combat=episode_combat(ep),
        high_mem=high_mem,
    )
    status["combat"] = episode_combat(ep) or "auto"
    status["high_mem"] = high_mem
    if combat_note:
        print("combat:", combat_note)
    for note in preset.get("notes") or []:
        print("preset:", note)
    status["preset"] = preset["name"]
    status["preset_canonical"] = preset.get("canonical") or canonical_preset(preset_name)
    if not dry_run:
        status["unet"] = unet
    save_status(root, status)
    never = [str(x) for x in ((ep.get("homage") or {}).get("never") or [])]
    beats = ep.get("beats") or []
    gpu_indexes = gpu_index_map(ep)
    reused = materialize_reuse(ep, root, fresh=fresh)
    for bid, src in reused.items():
        print("reuse", bid, "←", src)
        status["beats"][bid] = {"state": "done", "source": "reuse", "reused": src, "finished": _now()}
    for idx, beat in enumerate(beats):
        bid = beat["id"]
        raw_out = root / "raw" / f"{bid}.mp4"
        if is_ui_beat(beat):
            status["beats"][bid] = {"state": "done", "source": "ui"}
            continue
        if bid in reused and raw_out.is_file():
            continue
        if raw_out.is_file() and not fresh:
            print("skip (exists)", raw_out.name)
            status["beats"].setdefault(bid, {})["state"] = "done"
            continue
        source = beat_source(beat)
        if beat.get("reuse"):
            print("reuse source missing, rendering instead:", bid, reuse_source(ep, beat, root))
        prompt = build_beat_prompt(
            ep,
            beat,
            trigger=merge_trigger(preset.get("trigger") or "", beat),
            camera_pack=pack_name,
            gpu_index=gpu_indexes.get(bid, 0),
        )
        perrs = validate_beat_prompt(prompt, source=source, still_as=beat_still_as(beat), never=never)
        if perrs:
            raise EpisodeError(f"{bid}: {perrs}")
        (root / "logs" / f"{bid}.prompt.txt").write_text(prompt, encoding="utf-8")
        status["beats"][bid] = {"state": "running", "source": source, "started": _now()}
        save_status(root, status)
        beat_preset = apply_extra_loras(
            preset,
            beat,
            loras_dir,
            unet=unet_name,
            allow_combat=allow_combat,
            skip_note=combat_note,
        )
        for note in beat_preset.get("notes") or []:
            if note not in (preset.get("notes") or []):
                print("preset:", note)
        try:
            if dry_run:
                first = _first_frame_for(beat, idx, ep, root, canvas, None)
                last = _last_frame_for(beat, root, canvas, None)
                hue = (idx * 37) % 255
                gpu_s = beat_clip_seconds(ep, beat)
                synthetic_clip(raw_out.with_suffix(".part.mp4"), seconds=gpu_s, canvas=canvas, color=f"0x{hue:02x}{(120 + idx * 13) % 255:02x}{(200 - idx * 11) % 255:02x}", tone_hz=220 + idx * 40)
                result = {"videos": [str(raw_out.with_suffix(".part.mp4"))], "duration_s": gpu_s, "first": first, "last": last}
            else:
                first = _first_frame_for(beat, idx, ep, root, canvas, comfy_input)
                last = _last_frame_for(beat, root, canvas, comfy_input)
                result = render_beat_comfy(
                    source=source,
                    first_image=first,
                    last_image=last,
                    prompt=prompt,
                    comfy_dir=comfy,
                    canvas=canvas,
                    durations=duration_ladder(ep, beat),
                    preset=beat_preset,
                    seed=seed + idx,
                    filename_prefix=f"video/h3_ep_{ep['slug']}_{bid}",
                    unet=unet_name,
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
        if is_ui_beat(beat):
            continue  # frozen from the previous held still by finish_episode
        still = beat.get("still")
        if still:
            prev_still = root / str(still)
        if prev_still is None:
            raise EpisodeError(f"{beat['id']}: stills preview needs a still on or before this beat")
        staged = root / "input" / f"{beat['id']}-preview.jpg"
        stage_still(prev_still, staged, canvas)
        still_clip(staged, raw / f"{beat['id']}.mp4", seconds=seconds_per_beat, canvas=canvas)
    return finish_episode(ep, root, raw_dir=raw, out_name=out_name or f"{ep['slug']}-stills-preview.mp4", apply_trim=False)


def plan_lines(ep: dict[str, Any], root: Path | str | None = None) -> list[str]:
    """One line per beat for `check`: source, window, props, HUD flags, reuse availability."""
    lines: list[str] = []
    for beat in ep.get("beats") or []:
        hud = beat.get("hud") or {}
        start, seconds = beat_window(ep, beat)
        src = beat_source(beat)
        note = ""
        if beat.get("reuse"):
            path = reuse_source(ep, beat, Path(root)) if root is not None else None
            state = "on disk" if path is not None and path.is_file() else ("missing → render" if beat_renders(beat) else "missing, no still")
            note = f" reuse {beat['reuse']} ({state})"
        flags = []
        if not hud.get("visible", True):
            flags.append("cutscene")
        if hud.get("complete"):
            flags.append("complete")
        if beat.get("speech"):
            flags.append(f"{len(beat['speech'])} lines")
        extras = extra_lora_entries(beat)
        if extras:
            flags.append("+".join(k for k, _s in extras))
        if src == "t2v":
            flags.append("t2v")
        pack = resolve_beat_camera_pack(ep, beat)
        if pack and src not in ("ui",):
            flags.append(f"{pack}#{gpu_index_map(ep).get(str(beat.get('id') or ''), 0)}")
        if beat.get("steps"):
            flags.append(f"{int(beat['steps'])}step")
        if beat.get("sampler") or beat.get("scheduler"):
            flags.append(f"{beat.get('sampler') or 'euler'}+{beat.get('scheduler') or 'simple'}")
        if uses_last_still(beat):
            flags.append(f"still={beat_still_as(beat)}")
        connect = episode_connect(ep)
        if connect:
            flags.append(connect)
        props = ",".join(beat_props(ep, beat)) if src != "ui" else "menu"
        lines.append(f"{beat['id']:<20} {src:<5} {start:>4.1f}s+{seconds:<4.1f} props[{props}] {' '.join(flags):<18} {hud.get('mission') or ''}{note}")
    return lines


# ---------------------------------------------------------------- CLI

def _usage() -> str:
    return (
        "usage: h3_episode.py <check|prompts|dry-run|stills|finish> <episode.json|dir> [--out DIR] [--fresh] [--preset NAME] [--camera PACK] [--connect MODE] [--combat off|on] [--story MODE] [--invite-pose MODE] [--toilet MODE] [--gin MODE] [--tsuno MODE] [--appear LIST] [--scenes LIST]\n"
        "  check    validate + preflight, print prompts summary\n"
        "  prompts  write logs/<beat>.prompt.txt\n"
        "  dry-run  synthetic clips → HUD → stitch (no GPU)\n"
        "  stills   stills-only preview trailer (no GPU)\n"
        "  finish   HUD + cards + stitch over existing raw/*.mp4\n"
        "  --preset speed|balance|quality（迷ったら balance）\n"
        "  --camera side2d|action3d（迷ったら side2d）\n"
        "  --connect t2v|chain|landing（迷ったら t2v=カット。chain=1本目T2V・2本目以降は前の最終フレームからI2V。landing=用意した最終フレームへ着く）\n"
        "  --combat off|on（迷ったら off。on はハイメモリ専用）\n"
        "  --story accept|invite|evade|fight_win|fight_lose（病棟の構成。迷ったら accept）\n"
        "  --invite-pose all_fours|m_open|ride（病棟の誘うポーズ。迷ったら all_fours）\n"
        "  --toilet off|pee|masturbate|tentacle（病棟の道中トイレ。迷ったら off）\n"
        "  --gin off|taken|fuck|invite_doggy（病棟の灰色オプション。迷ったら off）\n"
        "  --tsuno off|accept_stand|invite_stand（病棟の角オプション。迷ったら off）\n"
        "  --appear miki,rei,kana,shino（病棟の登場。外した名前はシーンごと飛ばす）\n"
        "  --scenes miki=evade,rei=invite_ride,...（病棟のシーンごと。inherit は 5番に従う。戦い構成は無視）\n"
        "  --rei-mast skip|stand|back（レイ脱出の合間おな。迷ったら skip）\n"
        "  --rei-toilet ta|tb|tc（レイ脱出の糞トイレ。迷ったら ta）\n"
        "  --rei-beast accept|invite|evade（レイ脱出の敵1。迷ったら accept）\n"
        "  --rei-moth tail|mouth（レイ脱出の蛾女。迷ったら tail）\n"
        "  --rei-attack rei|her（レイ脱出の襲う側。迷ったら rei）\n"
        "  --rei-kiss off|on（レイ脱出のキス。迷ったら off）\n"
        "  --rei-oral skip|her|rei（レイ脱出の口。迷ったら skip）\n"
        "  --rei-pose fours|wall|straddle|supine（レイ脱出の体位は動き。迷ったら fours）\n"
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
    camera = None
    connect = None
    combat = None
    story = None
    invite_pose = None
    toilet = None
    gin = None
    tsuno = None
    appear = None
    scenes = None
    rei_mast = None
    rei_toilet = None
    rei_beast = None
    rei_moth = None
    rei_attack = None
    rei_kiss = None
    rei_oral = None
    rei_pose = None
    if "--out" in opts:
        out_dir = Path(opts[opts.index("--out") + 1])
    if "--preset" in opts:
        preset = opts[opts.index("--preset") + 1]
    if "--camera" in opts:
        camera = opts[opts.index("--camera") + 1]
    if "--connect" in opts:
        connect = opts[opts.index("--connect") + 1]
    if "--combat" in opts:
        combat = opts[opts.index("--combat") + 1]
    if "--story" in opts:
        story = opts[opts.index("--story") + 1]
    if "--invite-pose" in opts:
        invite_pose = opts[opts.index("--invite-pose") + 1]
    if "--toilet" in opts:
        toilet = opts[opts.index("--toilet") + 1]
    if "--gin" in opts:
        gin = opts[opts.index("--gin") + 1]
    if "--tsuno" in opts:
        tsuno = opts[opts.index("--tsuno") + 1]
    if "--appear" in opts:
        appear = opts[opts.index("--appear") + 1]
    if "--scenes" in opts:
        scenes = opts[opts.index("--scenes") + 1]
    if "--rei-mast" in opts:
        rei_mast = opts[opts.index("--rei-mast") + 1]
    if "--rei-toilet" in opts:
        rei_toilet = opts[opts.index("--rei-toilet") + 1]
    if "--rei-beast" in opts:
        rei_beast = opts[opts.index("--rei-beast") + 1]
    if "--rei-moth" in opts:
        rei_moth = opts[opts.index("--rei-moth") + 1]
    if "--rei-attack" in opts:
        rei_attack = opts[opts.index("--rei-attack") + 1]
    if "--rei-kiss" in opts:
        rei_kiss = opts[opts.index("--rei-kiss") + 1]
    if "--rei-oral" in opts:
        rei_oral = opts[opts.index("--rei-oral") + 1]
    if "--rei-pose" in opts:
        rei_pose = opts[opts.index("--rei-pose") + 1]
    ep_path, src_root = _resolve_paths(target)
    ep = load_episode(ep_path)
    ep = prepare_episode(
        ep,
        connect_override=connect,
        camera_pack_override=camera,
        preset_override=preset,
        combat_override=combat,
        story_override=story,
        invite_pose_override=invite_pose,
        toilet_override=toilet,
        gin_override=gin,
        tsuno_override=tsuno,
        appear_override=appear,
        scenes_override=scenes,
        rei_mast_override=rei_mast,
        rei_toilet_override=rei_toilet,
        rei_beast_override=rei_beast,
        rei_moth_override=rei_moth,
        rei_attack_override=rei_attack,
        rei_kiss_override=rei_kiss,
        rei_oral_override=rei_oral,
        rei_pose_override=rei_pose,
    )
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
        print("\n".join(plan_lines(ep, work)))
        cs = card_seconds(ep)
        cards_note = " + ".join(f"{k} {v:g}s" for k, v in cs.items() if v)
        ckpt = episode_checkpoint(ep)
        print(
            f"lane {episode_lane(ep)} | checkpoint {ckpt} ({CHECKPOINTS[ckpt]['file']}) | "
            f"tone {episode_tone(ep)} | connect {episode_connect(ep) or '-'} | "
            f"camera {episode_camera_pack(ep, camera) or '-'} | "
            f"preset {preset or (ep.get('render') or {}).get('preset') or 'fast'} | "
            f"cards: {cards_note or 'none'} | expected ≈ {expected_duration(ep):.1f}s"
        )
        if errs:
            print("\n".join("ERR " + e for e in errs))
            return 1
        gpu = sum(1 for b in ep.get("beats") or [] if beat_renders(b) and not (b.get("reuse") and reuse_source(ep, b, Path(work)) and reuse_source(ep, b, Path(work)).is_file()))
        print("preflight ok:", ep.get("slug"), f"{len(ep.get('beats') or [])} beats", f"{gpu} to render", canvas_for(ep), "→", output_size_for(ep))
        return 0
    if cmd == "prompts":
        trig = PRESETS[canonical_preset(str(preset or (ep.get("render") or {}).get("preset") or "fast"))]["trigger"]
        for p in write_prompts(ep, Path(work) / "logs", trigger=trig):
            print(p)
        return 0
    if cmd == "dry-run":
        final = run_episode(
            ep,
            work,
            dry_run=True,
            fresh=fresh,
            preset_override=preset,
            camera_pack_override=camera,
            connect_override=connect,
        )
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
