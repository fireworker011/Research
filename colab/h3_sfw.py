"""Non-adult H3 catalog.

Adult LoRA studios, the ward episode engine, and Civitai downloads are not
imported. One file name per LoRA. Generation stays outside this module.
"""

from __future__ import annotations

from typing import Any

# Speed: LightX2V FL2V turbo, 8 evaluations, strength 1.0.
SPEED_FILE = "minimax_h3_fl2v_turbo_8step_v1.0_768p_comfyui_bf16.safetensors"
SPEED_REPO = "lightx2v/Minimax-h3-Turbo"
SPEED_STRENGTH = 1.0
SPEED_STEPS = 9
SPEED_VIDEO_SHIFT = 6.0

# Action: Motion Continuity Repair V2. V1 is not registered.
ACTION_FILE = "Motion_Repair_V2.safetensors"
ACTION_REPO = "JOKER141/MiniMax-H3-General-Motion-Continuity-Repair"
ACTION_STRENGTH = 0.6

# Combat BASE V2. The Civitai save name is the same weights under another file name.
COMBAT_FILE = "H3_Combat_V2.safetensors"
COMBAT_REPO = "JOKER141/MiniMax-H3-Combat-Base-V2"
COMBAT_FIGHT_STRENGTH = 1.0
COMBAT_STACK_STRENGTH = 0.7
COMBAT_TRIGGER = "prfight2"
COMBAT_FINISH_TRIGGER = "prfight2, prfin1"

CHARSWAP_FILE = "h3_character_swap_pro4500_1000.safetensors"
CHARSWAP_STRENGTH = 1.0

ANIME2REAL_FILE = "Anime2Realsim__H3.safetensors"
ANIME2REAL_STRENGTH = 1.0

LORA_FILES = {
    "speed": SPEED_FILE,
    "action": ACTION_FILE,
    "combat": COMBAT_FILE,
    "charswap": CHARSWAP_FILE,
    "anime2real": ANIME2REAL_FILE,
}

# Names this tree does not download or register.
NOT_REGISTERED = (
    "combat_base_v2.safetensors",
    "Motion_Repair.safetensors",
    "Weapon",
    "GunFu",
    "Continuity",
)

# speed + action + combat may share one sampler. charswap and anime2real may not.
FAST_STACK = frozenset({"speed", "action", "combat"})

FAST_SECONDS = (6.0, 9.0)
JOIN_CLIP_SECONDS = frozenset({6.0, 9.0})
JOIN_MIN_S = 15.0
# A single H3 clip cannot be 15 seconds. 362 frames align to 15.083s and are refused.
ONE_SHOT_15_NOTE = (
    "1本で15秒は出せない。6秒は158フレーム（6.583秒）、9秒は226フレーム（9.417秒）になり、"
    "つなぎのときだけ指定秒で切って足す。"
)

I2VA_HEADER = (
    "For the target video, at 0.00 seconds into the target video, "
    "<Picture 1> (from [Shot 1]) is fully referenced."
)

# Buzz-pattern scripts already in the affi fixtures. This module does not rewrite them.
TEMPLATES = {
    "buy_before": {
        "pattern_id": "buy_before",
        "script": "minimaxh3/affi/fixtures/run02.md",
        "label": "悩み・不一致を先に出す",
    },
    "daily_food": {
        "pattern_id": "daily_same",
        "script": "minimaxh3/affi/fixtures/run01.md",
        "label": "日常・同じ子のふつうの場面（犬のごはん）",
    },
    "daily_camera": {
        "pattern_id": "daily_same",
        "script": "minimaxh3/affi/fixtures/run03.md",
        "label": "日常・同じ子のふつうの場面（見守り）",
    },
}


def fast_canvas(seconds: float) -> tuple[int, int, int]:
    """Width, height, and the VAE frame count for a fast FL2VA clip."""
    if seconds == 6.0:
        return 768, 1344, 158
    if seconds == 9.0:
        return 640, 1152, 226
    raise ValueError(f"fast clip is 6 or 9 seconds, got {seconds}")


def parse_join_parts(value: Any) -> tuple[float, ...]:
    """6-second and 9-second clips only. The sum must be at least 15 seconds."""
    if value is None or value == "":
        raw: list[Any] = [6.0, 9.0]
    elif isinstance(value, str):
        raw = [part.strip() for part in value.split(",") if part.strip()]
    elif isinstance(value, (list, tuple)):
        raw = list(value)
    else:
        raise ValueError("parts は 6 と 9 の並び")
    seconds: list[float] = []
    for item in raw:
        try:
            number = float(item)
        except (TypeError, ValueError) as exc:
            raise ValueError("parts は 6 と 9 の並び") from exc
        if number not in JOIN_CLIP_SECONDS:
            raise ValueError("つなぐ各本は 6 秒か 9 秒")
        seconds.append(number)
    if not seconds or sum(seconds) < JOIN_MIN_S:
        raise ValueError("つなぎは 15 秒以上")
    return tuple(seconds)


def join_ffmpeg(parts: tuple[float, ...], out_name: str = "joined.mp4") -> list[str]:
    """ffmpeg argv that trims each clip to its prompt seconds and concats at 1080x1920.

    Paths are placeholders. This function does not run ffmpeg.
    """
    inputs: list[str] = []
    filters: list[str] = []
    for index, seconds in enumerate(parts):
        inputs.extend(["-i", f"part-{index + 1}-{seconds:.0f}s.mp4"])
        filters.append(
            f"[{index}:v]trim=duration={seconds:.3f},setpts=PTS-STARTPTS,"
            f"scale=1080:1920:flags=lanczos,setsar=1[v{index}]"
        )
        filters.append(
            f"[{index}:a]atrim=duration={seconds:.3f},asetpts=PTS-STARTPTS[a{index}]"
        )
    paired = "".join(f"[v{index}][a{index}]" for index in range(len(parts)))
    filters.append(f"{paired}concat=n={len(parts)}:v=1:a=1[v][a]")
    return [
        "ffmpeg",
        "-y",
        *inputs,
        "-filter_complex",
        ";".join(filters),
        "-map",
        "[v]",
        "-map",
        "[a]",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-r",
        "24",
        "-c:a",
        "aac",
        out_name,
    ]
