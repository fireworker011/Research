"""Qwen Image Edit NSFW for Colab L4. Same 4-step Rapid-AIO stack as Mk1227."""
from __future__ import annotations

from pathlib import Path
from typing import Any

# Phr00t Rapid-AIO NSFW v23, extracted for diffusers. 4 step / CFG 1. Same class as
# Mk1227/Qwen-Image-Edit-NSFW (ZeroGPU A10G ≈ Colab L4 24GB).
PIPE_ID = "Qwen/Qwen-Image-Edit-2511"
TRANSFORMER_ID = "prithivMLmods/Qwen-Image-Edit-Rapid-AIO-V23"
LORA_REPO = "wiikoo/Qwen-lora-nsfw"

STEPS = 4
TRUE_CFG = 1.0
GUIDANCE = 1.0
DEFAULT_WIDTH = 576
DEFAULT_HEIGHT = 1024
L4_MIN_VRAM_GIB = 20.0

# Optional extra adapters on top of the NSFW merge. Names match jt65 Fast2-nsfw.
LORA_FILES = {
    "remove_clothing": "loras/qwen_image_edit_remove-clothing_v1.0.safetensors",
    "CockQwen_v3": "loras/CockQwen-v3.safetensors",
    "qwen_uncensor": "loras/qwen_uncensor_000014928.safetensors",
}
LORA_WEIGHTS = {
    "remove_clothing": 0.7,
    "CockQwen_v3": 0.55,
    "qwen_uncensor": 0.4,
}
LORA_TRIGGERS = {
    "remove_clothing": "remove her clothing",
    "CockQwen_v3": "Erect Penis",
    "qwen_uncensor": "nsfw, penis, vagina, nipples",
}

KEEP_LOCK = (
    "Keep the exact same person, exact same face, exact same hair length and style, "
    "exact same pose, exact same background, exact same lighting. Change clothing only."
)
FUTA_LOCK = (
    "Fully nude. Futanari: a fully erect 20cm human penis with pale shaft and pink glans "
    "standing in front of the crotch, hairless female pussy visible at the base of the shaft, "
    "no testicles, no scrotum, no balls. Female breasts. Not a man."
)
DEFAULT_EDIT_PROMPT = (
    f"{KEEP_LOCK} Remove only the clothes. Do not tie the hair. {FUTA_LOCK}"
)
DEFAULT_NEGATIVE = (
    "clothes, dress, fabric, underwear, testicles, scrotum, balls, male body, "
    "blurry, extra limbs, worst quality, watermark"
)


def require_l4_or_exit(vram_gib: float, name: str = "") -> None:
    """Colab free T4 is too small. L4 / A10G 24GB is the Mk1227 class."""
    label = (name or "").strip() or "GPU"
    if vram_gib < L4_MIN_VRAM_GIB:
        raise SystemExit(
            f"{label} の VRAM が {vram_gib:.1f} GiB。L4（約24GB）を選んで①からやり直してください。"
        )


def snapped_size(width: int, height: int, multiple: int = 32) -> tuple[int, int]:
    w = max(multiple, int(width) // multiple * multiple)
    h = max(multiple, int(height) // multiple * multiple)
    return w, h


def resize_rgb(image: Any, width: int = DEFAULT_WIDTH, height: int = DEFAULT_HEIGHT):
    """Letterbox-free resize to edit canvas. Snap to 32 like the Space."""
    w, h = snapped_size(width, height)
    rgb = image.convert("RGB")
    if rgb.size == (w, h):
        return rgb
    return rgb.resize((w, h))


def compose_edit_prompt(
    user_prompt: str = "",
    *,
    undress: bool = True,
    futa: bool = True,
    extra_triggers: list[str] | None = None,
) -> str:
    parts: list[str] = []
    text = (user_prompt or "").strip()
    blob = (text or "").lower()
    if text:
        parts.append(text)
    else:
        parts.append(KEEP_LOCK)
        blob = KEEP_LOCK.lower()
    if undress and "remove only the clothes" not in blob:
        parts.append("Remove only the clothes. Do not tie the hair.")
    if futa and "20cm" not in blob:
        parts.append(FUTA_LOCK)
    for trig in extra_triggers or []:
        t = (trig or "").strip()
        if t and t.lower() not in " ".join(parts).lower():
            parts.append(t)
    return " ".join(parts)


def lora_stack(undress: bool, futa: bool) -> list[tuple[str, float, str]]:
    rows: list[tuple[str, float, str]] = []
    if undress:
        rows.append(
            (
                "remove_clothing",
                LORA_WEIGHTS["remove_clothing"],
                LORA_TRIGGERS["remove_clothing"],
            )
        )
        rows.append(
            (
                "qwen_uncensor",
                LORA_WEIGHTS["qwen_uncensor"],
                LORA_TRIGGERS["qwen_uncensor"],
            )
        )
    if futa:
        rows.append(
            (
                "CockQwen_v3",
                LORA_WEIGHTS["CockQwen_v3"],
                LORA_TRIGGERS["CockQwen_v3"],
            )
        )
    return rows


def disable_safety(pipe: Any) -> Any:
    """Mk1227-class: no safety checker, no NSFW filter."""
    if hasattr(pipe, "safety_checker"):
        pipe.safety_checker = None
    if hasattr(pipe, "requires_safety_checker"):
        pipe.requires_safety_checker = False
    return pipe


def infer_kwargs(
    prompt: str,
    *,
    seed: int | None = None,
    steps: int = STEPS,
    true_cfg: float = TRUE_CFG,
    guidance: float = GUIDANCE,
    negative: str = DEFAULT_NEGATIVE,
    torch_module: Any = None,
    device: str = "cuda",
) -> dict[str, Any]:
    gen = None
    if torch_module is not None and seed is not None:
        gen = torch_module.Generator(device=device).manual_seed(int(seed))
    neg = None if float(true_cfg) <= 1.0 else negative
    return {
        "prompt": prompt,
        "negative_prompt": neg if neg is not None else " ",
        "num_inference_steps": int(steps),
        "true_cfg_scale": float(true_cfg),
        "guidance_scale": float(guidance),
        "num_images_per_prompt": 1,
        "generator": gen,
    }


def save_jpeg(image: Any, dest: str | Path, quality: int = 92) -> Path:
    path = Path(dest)
    path.parent.mkdir(parents=True, exist_ok=True)
    image.convert("RGB").save(path, "JPEG", quality=quality)
    return path
