"""Qwen Image Edit NSFW for Colab L4. Same 4-step Rapid-AIO stack as Mk1227."""
from __future__ import annotations

import re
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
    "Qwen4Play_v2": "loras/Qwen4Play_v2.safetensors",
}
LORA_WEIGHTS = {
    "remove_clothing": 0.7,
    "CockQwen_v3": 0.55,
    "qwen_uncensor": 0.4,
    "Qwen4Play_v2": 0.6,
}
LORA_TRIGGERS = {
    "remove_clothing": "remove her clothing",
    "CockQwen_v3": "Erect Penis",
    "qwen_uncensor": "nsfw, penis, vagina, nipples",
    "Qwen4Play_v2": "bl0wj0b, c0wg1rl, m15510n4ry, penis",
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

# ayooo123 / Mk1227 のクイックプロンプトと同じ12個。行為の竿はフタナリに差し替える。
SEX_PRESET_DEFAULT = "服抜きフタナリ（既定）"
SEX_PRESETS = {
    "服を脱ぐ": (
        "Remove all clothing from the person. Keep the exact same camera angle, framing, crop, pose, "
        "and IDENTICAL FACE as the input image — same facial features, same expression, same person, "
        "zero changes to face. Realistic nude body, natural skin."
    ),
    "ウェットシャワー": (
        "Medium shot, front-facing camera. THE SAME WOMAN from the input photo with the IDENTICAL FACE — "
        "same facial features, same eyes, nose, mouth, expression, absolutely unchanged. She stands in a "
        "tiled shower, completely nude — all clothing removed, fully naked. Her wet skin glistens with water "
        "running down her body and water mist in the air. She looks at the camera. Change only the setting "
        "to the shower, keep her face exactly the same."
    ),
    "レースランジェリー": (
        "THE SAME WOMAN with the IDENTICAL FACE — zero changes to facial features, same person, same "
        "expression. Change only her outfit to a black lace lingerie set — bra and panties, keeping her "
        "exact pose and body. Same environment and lighting. Face must be exactly as in the source image."
    ),
    "ビキニ": (
        "THE SAME WOMAN with the IDENTICAL FACE — absolutely no changes to facial features, same person, "
        "same expression. Change only her outfit to a small string bikini, keeping her exact pose and body. "
        "Same environment and lighting. Preserve the exact same face from the input image."
    ),
    "濡れたTシャツ": (
        "THE SAME WOMAN with the IDENTICAL FACE — unchanged facial features, same person, same expression. "
        "Change only her outfit to a wet white t-shirt clinging to her body with no bra underneath, "
        "semi-transparent, keeping her exact pose and body. Same environment and lighting. Face identical "
        "to source."
    ),
    "フェラチオの視点": (
        "POV close-up from the man's perspective looking down. THE SAME WOMAN from this photo with the "
        "IDENTICAL FACE — same facial features, same eyes, nose, mouth, absolutely unchanged, fully nude "
        "with bare breasts exposed, performing oral sex on a large thick erect penis. Her face fills most "
        "of the frame, lips wrapped around the shaft. One hand grips the base. She keeps eye contact with "
        "the camera. The penis enters from the bottom of the frame — only the shaft visible. Same "
        "environment and lighting as the original photo. Face must remain exactly as in the input image."
    ),
    "セルフタッチ": (
        "Front view eye-level shot, medium shot. THE SAME WOMAN with the IDENTICAL FACE — same facial "
        "features, same expression, zero changes. She is half-reclining and leaning back against a sofa, "
        "completely nude — all clothing removed, fully naked, bare breasts visible, legs spread wide open. "
        "Her face turned toward the camera with a calm relaxed expression. Her right hand rests between her "
        "thighs with fingers touching her own vulva, her left hand on her left breast. Change only the "
        "setting to the indoor sofa. Preserve the exact same face from the source image."
    ),
    "宣教師": (
        "POV from directly above, top-down view. The camera points straight down at THE SAME WOMAN with the "
        "IDENTICAL FACE — absolutely unchanged facial features, same person, same expression. She lies flat "
        "on her back, fully nude — all clothing removed. Her bare breasts and pussy are visible from above. "
        "She looks up into the camera with her mouth slightly open. A man's erect penis is inserted into her "
        "vagina, only the base visible at the bottom of the frame; do NOT show the man's face or upper body. "
        "Same environment and lighting. Face must be identical to the input image."
    ),
    "カウガール": (
        "First-person male POV looking up from below, eye-level, medium shot. Cowgirl sex from the man's "
        "POV — he lies on his back below, THE SAME WOMAN from the photo with the IDENTICAL FACE — same "
        "facial features, unchanged, same expression — straddles him facing the camera with a satisfied "
        "look, hands on her own hips. She is topless with bare breasts exposed, lower body fully nude, "
        "sitting on his erect penis inserted into her from below. The man's bare chest is visible at the "
        "bottom edge; his head, face and arms are completely out of view. Same environment as the original "
        "photo. Face must remain exactly as in the source image."
    ),
    "乳房プレイ": (
        "THE SAME WOMAN from this photo with the IDENTICAL FACE — absolutely unchanged facial features, "
        "same person, same expression — fully nude with bare breasts exposed, sitting on a bed in a bedroom. "
        "A man is suckling her right nipple. She has her eyes closed in pleasure. Preserve the exact same "
        "face from the input image."
    ),
    "フェイシャル": (
        "POV, top-down, close-up. THE SAME WOMAN with the IDENTICAL FACE — same facial features, zero "
        "changes — lies on her back on a bed, head resting on the bed, hair spread out, looking at the "
        "camera, both hands raised with her left hand gripping her own hair. A man holds his thick erect "
        "penis with a red swollen glans rising up from the bottom of the frame, the glans pressed against "
        "her chin. Face must be exactly as in the source image."
    ),
    "肛門リフト": (
        "Amateur phone-camera snapshot, natural indoor lighting, same environment as the original photo. "
        "THE SAME WOMAN with the IDENTICAL FACE — absolutely unchanged facial features, same person, same "
        "expression — is held up in the air with her legs raised wide in an M shape, her body facing the "
        "camera, completely nude — all clothing removed, bare breasts and pussy visible. A muscular man "
        "holds her up from behind, his large erect penis penetrating her anus from below; the man is mostly "
        "out of view behind her. Her face shows intense pleasure. Face must remain exactly as in the input "
        "image."
    ),
}
SEX_ACT_PRESETS = frozenset(
    {"フェラチオの視点", "宣教師", "カウガール", "乳房プレイ", "フェイシャル", "肛門リフト"}
)
OUTFIT_PRESETS = frozenset({"レースランジェリー", "ビキニ", "濡れたTシャツ"})
_LEFTOVER_MAN = re.compile(r"\b(?:male pov|man's|men|man)\b", re.I)
_FUTA_PARTNER_SWAPS = (
    ("do NOT show the man's face or upper body", "do NOT show the partner's face or upper body"),
    ("from the man's perspective looking down", "from a futanari POV looking down"),
    ("performing oral sex on a large thick erect penis", "performing oral sex on a large thick erect 20cm futanari penis (no testicles, pussy at the base)"),
    ("First-person male POV looking up from below", "First-person futanari POV looking up from below"),
    ("Cowgirl sex from the man's POV — he lies on his back below", "Cowgirl sex from a futanari POV — she lies on her back below"),
    ("A man's erect penis is inserted", "A futanari erect 20cm human penis (no testicles, pussy at the base) is inserted"),
    ("A man holds his thick erect penis", "A futanari holds her thick erect 20cm penis (no testicles, pussy at the base)"),
    ("A muscular man holds her up from behind, his large erect penis penetrating her anus", "An adult futanari woman holds her up from behind, her large erect 20cm penis (no testicles, pussy at the base) penetrating her anus"),
    ("the man is mostly out of view behind her", "the futanari is mostly out of view behind her"),
    ("A man is suckling her right nipple", "An adult futanari woman is suckling her right nipple"),
    ("The man's bare chest is visible at the bottom edge; his head, face and arms are completely out of view", "The futanari's bare breasts and chest are visible at the bottom edge; her head, face and arms are completely out of view"),
    ("sitting on his erect penis inserted into her from below", "sitting on her erect 20cm futanari penis (no testicles, pussy at the base) inserted from below"),
    ("straddles him facing the camera", "straddles her facing the camera"),
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


def sex_preset_labels() -> list[str]:
    return list(SEX_PRESETS)


def sex_preset_form_options() -> list[str]:
    return [SEX_PRESET_DEFAULT, *sex_preset_labels()]


def is_sex_act_preset(label: str) -> bool:
    return (label or "").strip() in SEX_ACT_PRESETS


def apply_futa_partner(prompt: str) -> str:
    """Sex presets from the Space use a man. H3 keeps 女体フタナリ（玉なし・20cm）."""
    out = prompt
    for old, new in _FUTA_PARTNER_SWAPS:
        out = out.replace(old, new)
    if _LEFTOVER_MAN.search(out):
        out += (
            " Not a man. The penis is a futanari erect 20cm human penis, no testicles, "
            "hairless pussy at the base of the shaft."
        )
    return out


def compose_edit_prompt(
    user_prompt: str = "",
    *,
    undress: bool = True,
    futa: bool = True,
    extra_triggers: list[str] | None = None,
    preset: str = "",
) -> str:
    label = (preset or "").strip()
    extra = (user_prompt or "").strip()
    parts: list[str] = []
    if label and label != SEX_PRESET_DEFAULT:
        base = SEX_PRESETS.get(label)
        if not base:
            raise SystemExit(f"unknown quick prompt: {label}")
        if is_sex_act_preset(label):
            parts.append(apply_futa_partner(base) if futa else base)
        else:
            parts.append(base)
            blob = base.lower()
            outfit = label in OUTFIT_PRESETS
            if not outfit:
                if undress and label == "服を脱ぐ":
                    pass
                elif undress and "remove all clothing" not in blob and "completely nude" not in blob:
                    parts.append("Remove only the clothes. Do not tie the hair.")
                if futa and "20cm" not in " ".join(parts).lower():
                    parts.append(FUTA_LOCK)
        if extra:
            parts.append(extra)
    else:
        blob = extra.lower()
        if extra:
            parts.append(extra)
        else:
            parts.append(KEEP_LOCK)
            blob = KEEP_LOCK.lower()
        if undress and "remove only the clothes" not in blob:
            parts.append("Remove only the clothes. Do not tie the hair.")
        if futa and "20cm" not in " ".join(parts).lower():
            parts.append(FUTA_LOCK)
    joined = " ".join(parts)
    for trig in extra_triggers or []:
        t = (trig or "").strip()
        if t and t.lower() not in joined.lower():
            parts.append(t)
            joined = " ".join(parts)
    return joined


def lora_stack(
    undress: bool,
    futa: bool,
    preset: str = "",
) -> list[tuple[str, float, str]]:
    rows: list[tuple[str, float, str]] = []
    label = (preset or "").strip()
    if label in OUTFIT_PRESETS:
        return rows
    if is_sex_act_preset(label):
        rows.append(
            (
                "qwen_uncensor",
                LORA_WEIGHTS["qwen_uncensor"],
                LORA_TRIGGERS["qwen_uncensor"],
            )
        )
        rows.append(
            (
                "Qwen4Play_v2",
                LORA_WEIGHTS["Qwen4Play_v2"],
                LORA_TRIGGERS["Qwen4Play_v2"],
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
