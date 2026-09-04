"""MiniMax H3 text-to-video. Same FL2VA unet as I2VA, no first frame.

Official Comfy template video_minimax_h3_t2v.json uses MiniMaxH3ImageToVideo
with first_frame / last_frame unwired. Default Shorts canvas is 9:16 576x1024
(multiples of 32). Landscape is 16:9 1024x576. Affiliate URLs never go in prompts.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from h3_motion_graphics import FORBIDDEN_IN_PROMPT, underage_prompt_errors
from h3_r2v_core import frames

DURATION_S = 5.0
GROKBOT_DURATION_S = 10.0
# Exact 9:16 and multiples of 32: 288x512, 576x1024, 864x1536.
CANVAS_9_16 = (576, 1024)
CANVAS_9_16_HIGH = (768, 1344)  # official short-edge 768 cap; slightly off 9:16
CANVAS_9_16_MIN = (288, 512)
CANVAS_9_16_LADDER = (CANVAS_9_16_HIGH, CANVAS_9_16, CANVAS_9_16_MIN)
# Exact 16:9 and multiples of 32. 1280x720 is not valid (720 % 32 != 0).
CANVAS_16_9 = (1024, 576)
CANVAS_16_9_HIGH = (1344, 768)  # 768 short-edge; slightly off 16:9
CANVAS_16_9_MIN = (512, 288)
CANVAS_16_9_LADDER = (CANVAS_16_9_HIGH, CANVAS_16_9, CANVAS_16_9_MIN)

DEFAULT_T2V_PROMPT = (
    "Vertical 9:16 live-action cinematic photorealism, no anime. "
    "A young Japanese woman in a dark navy zip-up hoodie sits at a desk with a laptop. "
    "Soft daylight, slight camera push-in. She looks toward the lens and blinks. "
    "A tiny on-screen mark reading \"広告\" sits in a corner. No URL. No income claims.\n\n"
    "overall_soundscape: Quiet room tone, faint keyboard tick.\n\n"
    "non_diegetic_music: Sparse warm piano, short hold at the end.\n"
)

DEFAULT_T2V_PROMPT_16_9 = (
    "Horizontal 16:9 live-action cinematic photorealism, no anime. "
    "A young Japanese woman in a dark navy zip-up hoodie sits at a desk with a laptop. "
    "Wide cinematic frame, soft daylight, slight camera push-in. "
    "She looks toward the lens and blinks. "
    "A tiny on-screen mark reading \"広告\" sits in a corner. No URL. No income claims.\n\n"
    "overall_soundscape: Quiet room tone, faint keyboard tick.\n\n"
    "non_diegetic_music: Sparse warm piano, short hold at the end.\n"
)


def is_9_16(width: int, height: int, *, tol: float = 0.03) -> bool:
    if height <= 0:
        return False
    return abs(width / height - 9 / 16) <= tol


def is_16_9(width: int, height: int, *, tol: float = 0.03) -> bool:
    if height <= 0:
        return False
    return abs(width / height - 16 / 9) <= tol


def canvas_for_aspect(aspect: str) -> tuple[int, int]:
    raw = (aspect or "9:16").strip().replace("：", ":")
    if raw in ("16:9", "16/9", "landscape", "wide"):
        return CANVAS_16_9
    if raw in ("9:16", "9/16", "portrait", "shorts"):
        return CANVAS_9_16
    raise ValueError(f"T2V aspect must be 9:16 or 16:9, got {aspect!r}")


def t2v_canvas_ok(width: int, height: int) -> bool:
    w, h = int(width), int(height)
    if w % 32 or h % 32 or w < 32 or h < 32:
        return False
    pair = (w, h)
    return is_9_16(w, h) or is_16_9(w, h) or pair in (CANVAS_9_16_HIGH, CANVAS_16_9_HIGH)


def t2v_retry_plans(*, width: int, height: int) -> list[dict[str, Any]]:
    w = max(32, int(width) // 32 * 32)
    h = max(32, int(height) // 32 * 32)
    plans = [{"width": w, "height": h, "label": f"{w}x{h}"}]
    area = w * h
    ladder = CANVAS_16_9_LADDER if (is_16_9(w, h) or (w, h) == CANVAS_16_9_HIGH) else CANVAS_9_16_LADDER
    for cw, ch in ladder:
        if cw * ch < area:
            plans.append({"width": int(cw), "height": int(ch), "label": f"{cw}x{ch}"})
    out: list[dict[str, Any]] = []
    seen: set[tuple[int, int]] = set()
    for p in plans:
        key = (p["width"], p["height"])
        if key in seen:
            continue
        seen.add(key)
        out.append(p)
    return out


def t2v_length_plans(duration_s: float) -> list[float]:
    """Grokbot asks for 10s; OOM may fall back to 5s. Aspect stays 9:16 or 16:9."""
    d = float(duration_s)
    out = [d]
    if d > 5:
        out.append(5.0)
    return out


def validate_t2v_prompt(prompt: str) -> list[str]:
    errs: list[str] = []
    p = (prompt or "").strip()
    if not p:
        errs.append("T2V prompt is empty")
        return errs
    low = p.lower()
    for bad in FORBIDDEN_IN_PROMPT:
        if bad.lower() in low:
            errs.append(f"forbidden string in prompt: {bad}")
    errs.extend(underage_prompt_errors(p))
    return errs


def resolve_t2v_prompt(prompt: str | None, *, landscape: bool = False) -> str:
    text = (prompt or "").strip()
    if text:
        return text
    return DEFAULT_T2V_PROMPT_16_9 if landscape else DEFAULT_T2V_PROMPT


def build_t2v_graph(
    *,
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
    """MiniMaxH3ImageToVideo with no first_frame = official T2V."""
    if width % 32 or height % 32:
        raise ValueError(f"H3 width/height must be multiples of 32, got {width}x{height}")
    g: dict[str, Any] = {}
    length = frames(duration_s)
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
    g["20"] = {
        "class_type": "MiniMaxH3ImageToVideo",
        "inputs": {
            "clip": ["3", 0],
            "vae": ["4", 0],
            "prompt": prompt,
            "width": int(width),
            "height": int(height),
            "length": length,
        },
    }
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


def assert_t2v_graph(g: dict[str, Any]) -> list[str]:
    errs: list[str] = []
    node = g.get("20") or {}
    if node.get("class_type") != "MiniMaxH3ImageToVideo":
        errs.append("node 20 must be MiniMaxH3ImageToVideo")
    inn = node.get("inputs") or {}
    if "first_frame" in inn:
        errs.append("T2V must not wire first_frame")
    if "last_frame" in inn:
        errs.append("T2V must not wire last_frame")
    if any(n.get("class_type") == "MiniMaxH3ReferenceToVideo" for n in g.values()):
        errs.append("R2V node must not be in the T2V graph")
    if any(n.get("class_type") == "LoadImage" for n in g.values()):
        errs.append("T2V must not load a still")
    w, h = int(inn.get("width") or 0), int(inn.get("height") or 0)
    if not t2v_canvas_ok(w, h):
        errs.append("canvas should stay 9:16 or 16:9 (or official 768-class)")
    errs.extend(validate_t2v_prompt(str(inn.get("prompt") or "")))
    return errs


def t2v_colab_url(*, repo: str = "fireworker011/Research", branch: str = "cursor/minimax-h3-motion-identity-e959") -> str:
    return (
        f"https://colab.research.google.com/github/{repo}/blob/{branch}/minimax_h3_t2v_phone.ipynb"
    )
