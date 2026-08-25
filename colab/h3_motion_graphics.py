"""MiniMax H3 I2VA / FL2VA pack for a 10-shot motion-graphics homage.

This is NOT R2V. The original demo's motion is reconstructed from the instruction
sheets as timed shots. Picture 1 is the first frame at 0.00s.

Do not put affiliate URLs in prompts or git. On-screen CTA only; the clickable
link lives on the human's profile.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from h3_r2v_core import comfy_media_name, frames

# X @ponzponz15/2091744536716611856: 1280x1440 (8:9), 9.87s, 30fps, one still → video.
# Homage keeps 8:9. Default is VRAM-safer; native matches the posted file.
DURATION_S = 10.0
CANVAS_8_9 = (1024, 1152)
CANVAS_8_9_NATIVE = (1280, 1440)
DEFAULT_FIRST_IMAGE = "Image 1.jpg"

I2VA_HEADER = (
    "For the target video, at 0.00 seconds into the target video, "
    "<Picture 1> (from [Shot 1]) is fully referenced."
)

CHARACTER_LOCK = (
    "photorealistic young Japanese woman in her early 20s, long straight dark brown hair "
    "with soft bangs, gentle warm smile, fair translucent skin, natural makeup, wearing a "
    "white linen sleeveless camisole top with small buttons and matching long flowing "
    "drawstring skirt, barefoot, standing in a traditional Japanese tatami room with shoji "
    "doors and bonsai, soft natural sunlight, highly detailed realistic skin and fabric texture, "
    "pure photorealism"
)

COPY = {
    "main_a": "好きは、仕事になる。",
    "main_b": "未経験から、クリエイターへ。",
    "sub": "プロのスキルが、すぐ見つかる。",
    "learn": "動画・デザイン・AIを実践で学ぶ",
    "card_video": "動画編集",
    "card_video_sub": "ゼロから学べる",
    "card_design": "デザイン",
    "card_design_sub": "想いをカタチに",
    "card_ai": "AI活用",
    "card_ai_sub": "未来の武器になる",
    "timer": "たった1分で無料登録",
    "easy": "カンタン申込み！",
    "cta": "無料で始める",
    "cta_sub": "ココナラでスキルを探す",
    "pr": "広告",
}

FORBIDDEN_IN_PROMPT = (
    "px.a8.net",
    "a8mat=",
    "稼げる",
    "必ず稼",
    "月収",
    "年収",
)


def fl2va_header(duration_s: float = DURATION_S) -> str:
    end = f"{float(duration_s):.2f}"
    return (
        "How the reference pictures align with the target video — "
        "Picture 1 (from Shot 1) aligns with the 0.00-second mark of the target video; "
        f"Picture 2 (from Shot 10) aligns with the {end}-second mark of the target video."
    )


def build_i2va_prompt(*, duration_s: float = DURATION_S, with_last_frame: bool = False) -> str:
    """Official MiniMax H3 I2VA / FL2VA body. On-screen Japanese stays in quotes."""
    d = float(duration_s)
    header = fl2va_header(d) if with_last_frame else I2VA_HEADER
    c = COPY
    body = f"""integrated_multimodal_description: [Shot 1] Live-action, cinematic photorealism, no anime and no illustration. <Picture 1> is the exact first frame. The woman is {CHARACTER_LOCK}. The camera holds a static shot then adds 2.5D parallax with small amplitude at slow speed: hair sways, sunlight on shoji shifts, she blinks once. Identity, clothes, eye color, and room stay locked.
[Shot 2] At 00:01.000, the shot transitions with a soft diagonal wipe as motion-graphic type, not a subtitle, slides in: "{c['main_a']}" appears with outline registration then fill, followed by tracking on "{c['main_b']}". A tiny "{c['pr']}" mark sits in a corner. The previous wipe triggers the type.
[Shot 3] At 00:02.000, the camera cuts to a close-up of her right hand. Fingers move as if drawing; cyan trim-path lines extend from the fingertip and write "{c['main_b'][:3]}" as "未経験" in the air above the tatami. The line motion is caused by the hand.
[Shot 4] At 00:03.000, the shot pulls back with small amplitude at slow speed. Huge tracking type "{c['main_b']}" floats in front of her. Her smile stays the same face from <Picture 1>, with a slightly more hopeful catchlight. Hair continues to sway.
[Shot 5] At 00:04.500, the giant type triggers two clean pop-in cards of copy: "{c['learn']}" and "{c['sub']}". Text is a graphic object in 3D space, not burned-in captions.
[Shot 6] At 00:05.500, three portal cards open in a row, each caused by the previous pop: "{c['card_video']}" / "{c['card_video_sub']}"; "{c['card_design']}" / "{c['card_design_sub']}"; "{c['card_ai']}" / "{c['card_ai_sub']}". Icons look like real objects, not flat anime stickers.
[Shot 7] At 00:06.500, each card expands as a portal window into a photoreal skill-work scene (editing timeline, design canvas, AI interface) while the woman remains the same person from <Picture 1> in the room behind the cards.
[Shot 8] At 00:07.500, a badge scales up: "{c['timer']}" and "{c['easy']}". No income claims. The portal motion triggers the badge.
[Shot 9] At 00:08.500, the camera pulls out with medium amplitude at slow speed to the full advertisement layout. She looks toward the lens with the same gentle smile.
[Shot 10] At 00:09.200, a red CTA button reading "{c['cta']}" scales up and stays locked until {d:.2f} seconds. Secondary type "{c['cta_sub']}" sits under it. The "{c['pr']}" mark remains. Do not drop the CTA. Do not change her face, hair, or clothes.

overall_soundscape: Quiet tatami-room ambience, soft fabric rustle, a faint stylus tick when the trim-path line is drawn, light UI whooshes as cards open, a soft click when the CTA locks.

non_diegetic_music: Sparse warm piano at a moderate tempo with a low pulse that rises slightly into the final button hold, then holds a single resolving chord.
"""
    return header + "\n\n" + body.strip() + "\n"


def resolve_motion_prompt(
    prompt: str | None,
    *,
    duration_s: float = DURATION_S,
    with_last_frame: bool = False,
) -> str:
    """Use the pre-filled cell prompt, or rebuild if empty / last-frame lock is missing."""
    text = (prompt or "").strip()
    if not text:
        return build_i2va_prompt(duration_s=duration_s, with_last_frame=with_last_frame)
    if with_last_frame and "Picture 2" not in text:
        return build_i2va_prompt(duration_s=duration_s, with_last_frame=True)
    return text


def validate_motion_ad_prompt(prompt: str, *, with_last_frame: bool = False) -> list[str]:
    errs: list[str] = []
    p = prompt or ""
    low = p.lower()
    if with_last_frame:
        if "Picture 2" not in p or "aligns with the" not in p:
            errs.append("FL2VA header missing Picture 2 end alignment")
    else:
        if I2VA_HEADER not in p:
            errs.append("I2VA 0.00s Picture 1 header missing")
    if "integrated_multimodal_description:" not in p:
        errs.append("missing integrated_multimodal_description")
    if "overall_soundscape:" not in p:
        errs.append("missing overall_soundscape")
    if "non_diegetic_music:" not in p:
        errs.append("missing non_diegetic_music")
    for i in range(1, 11):
        if f"[Shot {i}]" not in p:
            errs.append(f"missing [Shot {i}]")
    for key in ("main_a", "main_b", "cta", "pr", "card_video", "cta_sub"):
        if COPY[key] not in p:
            errs.append(f"missing on-screen copy {key}")
    if "photoreal" not in low:
        errs.append("photoreal lock missing")
    if "<Picture 1>" not in p:
        errs.append("Picture 1 tag missing")
    for bad in FORBIDDEN_IN_PROMPT:
        if bad.lower() in low:
            errs.append(f"forbidden string in prompt: {bad}")
    return errs


def prefer_fl2v_lora(lora_paths: list[Path], use_lora: bool) -> str | None:
    if not use_lora or not lora_paths:
        return None
    names = [p.name for p in lora_paths if p.suffix.lower() == ".safetensors"]
    fl = [n for n in names if "fl2v" in n.lower() or "fl2va" in n.lower()]
    if fl:
        turbo = [n for n in fl if "turbo" in n.lower()]
        return sorted(turbo or fl, reverse=True)[0]
    return None


def build_i2va_graph(
    *,
    first_image: str,
    last_image: str | None,
    prompt: str,
    unet: str,
    lora_name: str | None,
    lora_strength: float,
    width: int,
    height: int,
    duration_s: float,
    seed: int,
    steps: int,
    filename_prefix: str,
    has_lora_loader: bool = True,
    has_audio_decode: bool = True,
    clip_name: str = "qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors",
    vvae: str = "minimax_h3_video_vae_fp16.safetensors",
    avae: str = "minimax_h3_audio_vae_fp32.safetensors",
) -> dict[str, Any]:
    """MiniMaxH3ImageToVideo: first frame required, last frame optional (CTA lock)."""
    if width % 32 or height % 32:
        raise ValueError(f"H3 width/height must be multiples of 32, got {width}x{height}")
    g: dict[str, Any] = {}
    length = frames(duration_s)
    g["100"] = {
        "class_type": "LoadImage",
        "inputs": {"image": comfy_media_name(first_image)},
    }
    g["1"] = {
        "class_type": "UNETLoader",
        "inputs": {"unet_name": unet, "weight_dtype": "default"},
    }
    model: list[Any] = ["1", 0]
    if lora_name and has_lora_loader:
        g["2"] = {
            "class_type": "LoraLoaderModelOnly",
            "inputs": {
                "model": ["1", 0],
                "lora_name": lora_name,
                "strength_model": float(lora_strength),
            },
        }
        model = ["2", 0]
    g["3"] = {
        "class_type": "CLIPLoader",
        "inputs": {"clip_name": clip_name, "type": "minimax", "device": "default"},
    }
    g["4"] = {"class_type": "VAELoader", "inputs": {"vae_name": vvae}}
    g["5"] = {"class_type": "VAELoader", "inputs": {"vae_name": avae}}
    i_inputs: dict[str, Any] = {
        "clip": ["3", 0],
        "vae": ["4", 0],
        "prompt": prompt,
        "width": int(width),
        "height": int(height),
        "length": length,
        "first_frame": ["100", 0],
    }
    if last_image:
        g["101"] = {
            "class_type": "LoadImage",
            "inputs": {"image": comfy_media_name(last_image)},
        }
        i_inputs["last_frame"] = ["101", 0]
    g["20"] = {"class_type": "MiniMaxH3ImageToVideo", "inputs": i_inputs}
    g["21"] = {"class_type": "RandomNoise", "inputs": {"noise_seed": int(seed)}}
    sampler = "euler" if lora_name else "res_multistep"
    scheduler = "simple" if lora_name else "beta"
    g["22"] = {"class_type": "KSamplerSelect", "inputs": {"sampler_name": sampler}}
    g["23"] = {
        "class_type": "BasicScheduler",
        "inputs": {
            "model": model,
            "scheduler": scheduler,
            "steps": int(steps) if lora_name else max(int(steps), 16),
            "denoise": 1.0,
        },
    }
    g["24"] = {
        "class_type": "BasicGuider",
        "inputs": {"model": model, "conditioning": ["20", 0]},
    }
    g["25"] = {
        "class_type": "SamplerCustomAdvanced",
        "inputs": {
            "noise": ["21", 0],
            "guider": ["24", 0],
            "sampler": ["22", 0],
            "sigmas": ["23", 0],
            "latent_image": ["20", 1],
        },
    }
    g["26"] = {"class_type": "VAEDecode", "inputs": {"samples": ["25", 0], "vae": ["4", 0]}}
    if has_audio_decode:
        g["27"] = {
            "class_type": "VAEDecodeAudio",
            "inputs": {"samples": ["25", 0], "vae": ["5", 0]},
        }
        g["28"] = {
            "class_type": "CreateVideo",
            "inputs": {"images": ["26", 0], "audio": ["27", 0], "fps": 24},
        }
    else:
        g["28"] = {"class_type": "CreateVideo", "inputs": {"images": ["26", 0], "fps": 24}}
    g["29"] = {
        "class_type": "SaveVideo",
        "inputs": {
            "video": ["28", 0],
            "filename_prefix": filename_prefix,
            "format": "auto",
            "codec": "auto",
        },
    }
    return g


def assert_i2va_graph(g: dict[str, Any], *, expect_last: bool) -> list[str]:
    errs: list[str] = []
    node = g.get("20") or {}
    if node.get("class_type") != "MiniMaxH3ImageToVideo":
        errs.append("node 20 must be MiniMaxH3ImageToVideo")
    inn = node.get("inputs") or {}
    if "first_frame" not in inn:
        errs.append("first_frame not wired")
    if expect_last and "last_frame" not in inn:
        errs.append("last_frame not wired")
    if not expect_last and "last_frame" in inn:
        errs.append("I2VA should not wire last_frame")
    if any(n.get("class_type") == "MiniMaxH3ReferenceToVideo" for n in g.values()):
        errs.append("R2V node must not be in the I2VA graph")
    prompt = inn.get("prompt") or ""
    errs.extend(validate_motion_ad_prompt(prompt, with_last_frame=expect_last))
    return errs
