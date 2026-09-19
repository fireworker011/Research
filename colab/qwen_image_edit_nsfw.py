"""Qwen Image Edit NSFW for Colab L4. Same 4-step Rapid-AIO stack as Mk1227."""
from __future__ import annotations

import gc
import re
import sys
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
VRAM_OFFLOAD_GIB = 8.0
# Weights stay on the Colab VM HuggingFace cache. Drive only holds JPGs.
DRIVE_FREE_GIB = 2
WEIGHTS_CACHE_GIB = 40
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}
PHOTOREAL_NAME_MARKS = ("photoreal", "realperson", "real-person", "実写")
INPUT_SOURCE_DEFAULT = "Drive input"
INPUT_SOURCE_OPTIONS = (INPUT_SOURCE_DEFAULT, "アップロード")
REF_SOURCE_DEFAULT = "なし（元画像の顔）"
REF_SOURCE_OPTIONS = (REF_SOURCE_DEFAULT, "Drive から", "アップロード")
UPLOAD_PHONE_HINT = (
    "スマホの Colab ではファイル選択が使えない。"
    "入力は Drive input。JPG は Drive の qwen-image-edit-nsfw/input に置く。"
    "1枚だけなら 入力ファイル名 にファイル名を入れる。"
)
# Colab ships Pillow 11.3 with a matching _imaging .so. Do not -U to 12:
# 12.0 is missing _Ink; 12.3 .py on an 11.3 .so raises ImportError.
PILLOW_COLAB_SPEC = "pillow==11.3.0"

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
# Rapid-AIO V23 is already NSFW. qwen_uncensor is ~2.4GB and does not fit L4 24GB.
LORA_SKIP_UNDER_VRAM_GIB = {
    "qwen_uncensor": 28.0,
}

KEEP_LOCK = (
    "Keep the exact same person, exact same face, exact same hair length and style, "
    "exact same pose, exact same background, exact same lighting. Change clothing only."
)
IDENTITY_LOCK = (
    "MANDATORY IDENTITY LOCK: the output person is the exact same character as the input. "
    "Identical face, identical facial features, identical eyes, nose and mouth, "
    "identical hair length, color and hairstyle. Do not beautify, do not restyle the hair, "
    "do not swap to a different person. Zero changes to the face. This lock is required."
)
CLOTHING_SCOPE = (
    "EDIT SCOPE: change clothing or nudity only. Keep the exact same pose, camera, crop, "
    "background and lighting."
)
ACT_SCOPE = (
    "EDIT SCOPE: you may change clothing, pose, camera, location/background, and the sex act. "
    "You must not change who the person is, their face, their hair, or the art medium of the input."
)
I2I_SINGLE = (
    "This is image-to-image of Picture 1, not text-to-image. "
    "Edit the uploaded source. Do not invent a new person from text alone."
)
I2I_REF = (
    "This is multi-image I2I. Picture 1 is the source to edit "
    "(clothing, pose, location, sex act). "
    "Picture 2 is the face and art-medium lock: identical face, identical hair, "
    "identical art medium as Picture 2. Keep Picture 2's person. "
    "Do not copy Picture 2's pose or clothes unless asked. Adult 21+."
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
STYLE_PRESET_DEFAULT = "入力のまま"
STYLE_LABELS = ("アニメ絵", "リアル", "3D", "漫画")
STYLE_PRESETS = {
    STYLE_PRESET_DEFAULT: (
        "CRITICAL STYLE LOCK: keep the exact same art medium as the input image. "
        "If the input is 2D anime, stay 2D anime. If it is a photoreal photo, stay photoreal. "
        "If it is 3D CGI, stay 3D CGI. If it is manga or comic, stay manga. "
        "Do not convert to a different medium."
    ),
    "アニメ絵": (
        "CRITICAL STYLE LOCK: the input is 2D Japanese anime. Stay 2D anime illustration "
        "with the same cel shading, lineart, and palette. Do not convert to photoreal, 3D CGI, "
        "or live action."
    ),
    "リアル": (
        "CRITICAL STYLE LOCK: the input is a photoreal photograph. Stay photorealistic live-action. "
        "Do not convert to anime, manga, or 3D CGI."
    ),
    "3D": (
        "CRITICAL STYLE LOCK: the input is 3D CGI. Stay 3D CGI / game-engine render with the same "
        "shader and lighting. Do not convert to 2D anime, manga, or a real photograph."
    ),
    "漫画": (
        "CRITICAL STYLE LOCK: the input is 2D manga / comic. Stay manga with the same ink, "
        "screentones, and color (monochrome or limited). Do not convert to photoreal or 3D CGI."
    ),
}
STYLE_NEGATIVES = {
    "アニメ絵": "photorealistic, photograph, 3d render, real skin pores, live action",
    "リアル": "anime, manga, cartoon, 3d render, illustration, lineart, cel shading",
    "3D": "2d anime, manga, photograph, live action, flat cel, lineart screentone",
    "漫画": "photorealistic, 3d render, live action, painterly, photograph, cgi",
}
ANAL_DETAIL = (
    "Both adults are futanari women, not a man, not a male body. "
    "Each has female breasts, a feminine body, a fully erect 20cm human penis "
    "with a pale veined shaft and a pink glans with a visible corona, "
    "a hairless female pussy with inner labia at the base of the shaft, "
    "and a pink anus. No testicles, no scrotum, no balls on anyone. "
    "Sharp clean close detail of the futanari penis, the pussy, the anus, and the anal sex: "
    "the partner's 20cm glans and shaft are inside the receiver's stretched wet anal ring; "
    "the sphincter grips the shaft; the perineum, the receiver's pussy, and the receiver's own erect 20cm penis "
    "are fully visible and unobstructed. No clothes. Adult 21+."
)
SPACE_SEX_PRESET_LABELS = (
    "服を脱ぐ",
    "ウェットシャワー",
    "レースランジェリー",
    "ビキニ",
    "濡れたTシャツ",
    "フェラチオの視点",
    "セルフタッチ",
    "宣教師",
    "カウガール",
    "乳房プレイ",
    "フェイシャル",
    "肛門リフト",
)
ANAL_POSE_LABELS = (
    "アナルバック",
    "アナル立ちバック",
    "アナル正常位",
    "アナル騎乗位",
    "アナル座位",
)
URINE_LABELS = (
    "放尿（立ち）",
    "放尿（しゃがみ）",
    "ご褒美小便",
)
SCAT_LABELS = (
    "脱糞（しゃがみ）",
    "脱糞（後背）",
)
URINE_DETAIL = (
    "URINE LOOK: Opaque yellow urine, not clear, not white, not semen. When the 20cm pees, "
    "the stream comes out of the urethral opening at the glans tip (the small hole at the tip "
    "of the 20cm), the same hole semen would pulse from, not from the pussy at the base, not "
    "from the anus, not from off-screen. Continuous physically realistic yellow arc, splash and "
    "puddle. Keep the identical face and the input art medium. Adult futanari: no testicles, "
    "hairless pussy at the base of the shaft. Not a man. Adult 21+."
)
SCAT_DETAIL = (
    "SCAT ACT: Real adult human feces leaving the anus in this image. A formed opaque brown "
    "stool log, sausage-shaped and lightly segmented, is pushed out of the anus now. "
    "Soft-solid like clay: it sags, breaks, and piles. It does not bounce. It does not stretch "
    "like slime. This is the act of defecating now, not a body already coated from before. "
    "It leaves through the anus, not the vagina, not from off-screen. "
    "FECES LOOK: Opaque dull-matte medium-dark brown human stool, not chocolate syrup, not "
    "jelly, not slime, not a cartoon swirl. Slightly moist, dense, heavy. Keep the identical "
    "face and the input art medium. Adult futanari: 20cm penis, hairless pussy at the base, "
    "no testicles. Not a man. Adult 21+."
)

# ayooo123 / Mk1227 のクイックプロンプトと同じ12個。行為の竿はフタナリに差し替える。
SEX_PRESET_DEFAULT = "服抜きフタナリ（既定）"
SEX_PRESETS = {
    "服を脱ぐ": (
        "Remove all clothing from the person. Keep the exact same camera angle, framing, crop, pose, "
        "and IDENTICAL FACE as the input image — same facial features, same expression, same person, "
        "zero changes to face."
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
    "アナルバック": (
        "Rear three-quarter view, slightly low, medium-full shot. THE SAME PERSON from the input photo "
        "with the IDENTICAL FACE — same facial features, same eyes, nose, mouth, absolutely unchanged — "
        "looks back over her shoulder so her face is fully visible. She is on all fours in doggy position, "
        "completely nude, back arched, knees apart. An adult futanari partner kneels behind her; partner's "
        "face out of frame. The partner's erect 20cm futanari penis is thrusting into the receiver's anus "
        "from behind. Show the hanging receiver cock between her thighs, the hairless pussy at the base of "
        "that shaft, and the stretched anus around the penetrating shaft in one clear frame. Same environment "
        "and lighting as the original photo. Not a man."
    ),
    "アナル立ちバック": (
        "Full-body three-quarter rear view. THE SAME PERSON from the input photo with the IDENTICAL FACE — "
        "same facial features, unchanged — is standing, bent forward at the waist in standing doggy, hands "
        "braced on a wall or bed, looking back so her face is visible. Completely nude. An adult futanari "
        "partner stands behind her, face out of frame, hips flush against her ass. The partner's erect 20cm "
        "futanari penis is buried in the receiver's anus. The receiver's own erect 20cm penis hangs between "
        "her thighs; hairless pussy at the base; anus gripping the shaft. Same environment. Not a man."
    ),
    "アナル正常位": (
        "Three-quarter view from above and in front, medium shot. THE SAME PERSON from the input photo with "
        "the IDENTICAL FACE — same facial features, unchanged — lies on her back in missionary, legs folded "
        "toward her chest or spread in an M, looking at the camera. Completely nude. This is anal missionary, "
        "not vaginal: the partner's erect 20cm futanari penis is inserted in her anus. Her own erect 20cm "
        "penis lies on her belly pointing toward her navel, hairless pussy visible at the base of her shaft, "
        "anus below the perineum taking the partner. Partner is between her legs, face out of frame. Same "
        "environment. Not a man."
    ),
    "アナル騎乗位": (
        "Eye-level medium shot, front. THE SAME PERSON from the input photo with the IDENTICAL FACE — same "
        "facial features, unchanged — sits in cowgirl, facing the camera, completely nude, straddling an "
        "adult futanari partner who lies on her back below. Partner's face out of frame; partner's female "
        "breasts may show at the bottom edge. The partner's erect 20cm futanari penis is in the receiver's "
        "anus from below, not in the pussy. The receiver's own erect 20cm penis stands in front of her crotch; "
        "hairless pussy at the base; anus sitting down on the shaft. Hands on her own thighs. Same environment. "
        "Not a man."
    ),
    "アナル座位": (
        "Eye-level medium shot. THE SAME PERSON from the input photo with the IDENTICAL FACE — same facial "
        "features, unchanged — sits in an adult futanari partner's lap in seated anal sex, more upright than "
        "cowgirl, feet down or hooked, completely nude. Partner sits on a chair or the edge of the bed, face "
        "out of frame. The partner's erect 20cm futanari penis is in the receiver's anus. The receiver's own "
        "erect 20cm penis is visible in front; hairless pussy at the base of her shaft; anus taking the full "
        "shaft in the lap. Same environment. Not a man."
    ),
    "放尿（立ち）": (
        "Full-body front or three-quarter view. THE SAME PERSON from the input with the IDENTICAL FACE — "
        "same facial features, unchanged. She stands fully nude, feet apart. Her 20cm futanari penis is "
        "visible; a thick opaque yellow urine stream shoots from the urethral opening at the glans tip "
        "and arcs into a puddle. Hairless pussy at the base of the shaft. No urine from the pussy or anus. "
        "No testicles. Face fully readable. Same environment art medium. Not a man."
    ),
    "放尿（しゃがみ）": (
        "Medium-full shot. THE SAME PERSON from the input with the IDENTICAL FACE — same facial features, "
        "unchanged. She squats fully nude, knees apart, heels down, looking toward the camera so her face "
        "is readable. Her 20cm futanari penis hangs or is held between her thighs; opaque yellow urine "
        "streams from the urethral opening at the glans tip into a puddle between her feet. Hairless pussy "
        "at the base. No urine from the pussy or anus. No testicles. Not a man."
    ),
    "ご褒美小便": (
        "Close-up of THE SAME PERSON from the input with the IDENTICAL FACE — same facial features, "
        "absolutely unchanged. She looks up, mouth slightly open, receiving. An adult futanari 20cm penis "
        "enters from the top or edge of the frame, partner's face out of frame. Opaque yellow urine streams "
        "from the urethral opening at the glans tip onto her face, hair, lips and tongue. Not white, not "
        "semen, not clear water. Wet yellow on skin. Hairless pussy at the base of that shaft, no testicles. "
        "Not a man."
    ),
    "脱糞（しゃがみ）": (
        "Medium-full three-quarter view. THE SAME PERSON from the input with the IDENTICAL FACE — same "
        "facial features, unchanged, face readable. She squats fully nude, knees apart. Her 20cm futanari "
        "penis and hairless pussy are visible in front. The anus is clearly shown: a formed opaque brown "
        "sausage-shaped human stool log is being pushed out of the anus now, sagging like clay. Not jelly, "
        "not slime, not from the vagina. No testicles. Not a man."
    ),
    "脱糞（後背）": (
        "Rear three-quarter view, slightly low. THE SAME PERSON from the input with the IDENTICAL FACE — "
        "same facial features, unchanged — looks back over her shoulder so her face is readable. She is on "
        "all fours, fully nude. Her 20cm futanari penis hangs between her thighs with hairless pussy at the "
        "base. The anus is the focus: a formed opaque brown sausage-shaped human stool log is leaving the "
        "anus now. Soft-solid clay, not jelly, not slime, not from the vagina. No testicles. Not a man."
    ),
}
SEX_ACT_PRESETS = frozenset(
    {
        "フェラチオの視点",
        "宣教師",
        "カウガール",
        "乳房プレイ",
        "フェイシャル",
        "肛門リフト",
        *ANAL_POSE_LABELS,
    }
)
ANAL_PRESETS = frozenset({"肛門リフト", *ANAL_POSE_LABELS})
URINE_PRESETS = frozenset(URINE_LABELS)
SCAT_PRESETS = frozenset(SCAT_LABELS)
EXCRETE_PRESETS = frozenset({*URINE_LABELS, *SCAT_LABELS})
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


def drop_stale_pil_modules() -> None:
    """Drop cached PIL/torchvision after a Pillow reinstall on Colab."""
    for name in list(sys.modules):
        if (
            name == "PIL"
            or name.startswith("PIL.")
            or name == "torchvision"
            or name.startswith("torchvision.")
        ):
            del sys.modules[name]


def drop_stale_torchao_modules() -> None:
    """Colab ships torchao 0.10. peft 0.19+ raises if it is present and < 0.16."""
    for name in list(sys.modules):
        if name == "torchao" or name.startswith("torchao."):
            del sys.modules[name]
    peft_utils = sys.modules.get("peft.import_utils")
    fn = getattr(peft_utils, "is_torchao_available", None)
    cache_clear = getattr(fn, "cache_clear", None)
    if callable(cache_clear):
        cache_clear()


def lora_files_for_gpu(vram_gib: float | None = None) -> dict[str, str]:
    """Drop adapters that cannot share L4 24GB with the Rapid-AIO transformer."""
    files = dict(LORA_FILES)
    if vram_gib is None:
        return files
    for name, need in LORA_SKIP_UNDER_VRAM_GIB.items():
        if float(vram_gib) < need:
            files.pop(name, None)
    return files


def lora_skip_summary(errors: list[str], *, has_token: bool = False) -> str:
    """② LoRA miss is often torchao, not NFAA."""
    blob = " ".join(errors).lower()
    if "torchao" in blob:
        return (
            "LoRA なし（Colab の torchao が古い。②で uninstall してからもう一度）。"
            "Rapid-AIO NSFW merge だけで進む"
        )
    if any(mark in blob for mark in ("401", "403", "gated", "restricted", "nfaa")):
        return "LoRA なし（Colab Secrets に HF_TOKEN。NFAA）。Rapid-AIO NSFW merge だけで進む"
    if not has_token:
        return "LoRA なし（Colab Secrets に HF_TOKEN。NFAA）。Rapid-AIO NSFW merge だけで進む"
    return "LoRA なし。Rapid-AIO NSFW merge だけで進む"


def pillow_major_minor(version: str) -> tuple[int, int]:
    bits = [p for p in (version or "0").split(".") if p.isdigit()]
    major = int(bits[0]) if bits else 0
    minor = int(bits[1]) if len(bits) > 1 else 0
    return major, minor


def require_pillow_colab(version: str | None = None) -> str:
    """Keep Colab's Pillow 11.3. 12.0 lacks _Ink; 12.x .py vs 11.3 .so dies."""
    ver = version
    if ver is None:
        try:
            import PIL
            from PIL import Image  # noqa: F401

            ver = str(getattr(PIL, "__version__", "0"))
        except Exception as e:
            raise SystemExit(
                f"Pillow が壊れています（{e}）。"
                f"{PILLOW_COLAB_SPEC} に戻すか、ランタイムを再起動して①②。"
            ) from e
    major, minor = pillow_major_minor(ver)
    if (major, minor) == (12, 0):
        raise SystemExit(
            f"Pillow {ver} は Colab で壊れます（_Ink）。"
            f"{PILLOW_COLAB_SPEC} に戻して②をやり直してください。"
        )
    if major >= 12:
        raise SystemExit(
            f"Pillow {ver} は Colab の _imaging（11.3）と食い違う。"
            f"{PILLOW_COLAB_SPEC} に戻して②をやり直す。まだならランタイム再起動→①②。"
        )
    return ver


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


def style_form_options() -> list[str]:
    return [STYLE_PRESET_DEFAULT, *STYLE_LABELS]


def input_source_form_options() -> list[str]:
    return list(INPUT_SOURCE_OPTIONS)


def ref_source_form_options() -> list[str]:
    return list(REF_SOURCE_OPTIONS)


def drive_space_lines() -> list[str]:
    return [
        "これは i2i（元画像を編集）。t2i ではない。",
        "Drive に置くのは input/ と output/ の JPG だけ。",
        f"Drive の空きは {DRIVE_FREE_GIB}GB あれば足りる。H3 の参照土台 21GB は不要。",
        f"重みは Colab ディスク（HuggingFace キャッシュ 約{WEIGHTS_CACHE_GIB}GB）。Drive には載せない。",
        "スマホは Drive input。アップロード（ファイル選択）は PC だけ。",
    ]


def is_photoreal_path(path: str | Path) -> bool:
    name = Path(path).name.lower()
    return any(mark in name for mark in PHOTOREAL_NAME_MARKS)


def refuse_photoreal(path: str | Path) -> None:
    if is_photoreal_path(path):
        raise SystemExit(f"実写の他人は入れるな: {Path(path).name}")


def list_input_images(
    folder: str | Path,
    *,
    skip_name: str = "",
) -> tuple[list[Path], list[Path]]:
    root = Path(folder)
    kept: list[Path] = []
    skipped: list[Path] = []
    skip = (skip_name or "").strip().lower()
    if not root.is_dir():
        return kept, skipped
    for path in sorted(root.iterdir()):
        if not path.is_file():
            continue
        if path.suffix.lower() not in IMAGE_SUFFIXES:
            continue
        if skip and path.name.lower() == skip:
            continue
        if is_photoreal_path(path):
            skipped.append(path)
            continue
        kept.append(path)
    return kept, skipped


def resolve_input_paths(
    folder: str | Path,
    *,
    want_name: str = "",
    skip_name: str = "",
) -> tuple[list[Path], list[Path]]:
    """Drive input. Optional one filename (stem ok). Phone path: no files.upload."""
    kept, skipped = list_input_images(folder, skip_name=skip_name)
    want = (want_name or "").strip()
    if not want:
        return kept, skipped
    refuse_photoreal(want)
    want_l = want.lower()
    hits = [p for p in kept if p.name.lower() == want_l or p.stem.lower() == want_l]
    if not hits:
        names = ", ".join(p.name for p in kept) or "なし"
        raise SystemExit(f"Drive input に無い: {want}。あるのは: {names}。{UPLOAD_PHONE_HINT}")
    return hits, skipped


def snapped_rgb(image: Any) -> Any:
    """Keep aspect. Snap to 32 so a face reference is not stretched to 9:16."""
    rgb = image.convert("RGB")
    w, h = snapped_size(*rgb.size)
    if rgb.size == (w, h):
        return rgb
    return rgb.resize((w, h))


def pipe_images(source: Any, ref: Any | None = None) -> list[Any]:
    images = [source]
    if ref is not None:
        images.append(ref)
    return images


def style_negative(style: str = "", base: str = DEFAULT_NEGATIVE) -> str:
    label = (style or "").strip() or STYLE_PRESET_DEFAULT
    extra = STYLE_NEGATIVES.get(label, "")
    if not extra:
        return base
    return f"{base}, {extra}"


def apply_style(prompt: str, style: str = "") -> str:
    label = (style or "").strip() or STYLE_PRESET_DEFAULT
    lock = STYLE_PRESETS.get(label)
    if not lock:
        raise SystemExit(f"unknown style: {label}")
    out = prompt or ""
    out = out.replace("Realistic nude body, natural skin.", "")
    if label in {"アニメ絵", "漫画", "3D"}:
        out = out.replace(
            "Amateur phone-camera snapshot, natural indoor lighting",
            "Indoor lighting",
        )
    return f"{lock} {out}".strip()


def is_sex_act_preset(label: str) -> bool:
    return (label or "").strip() in SEX_ACT_PRESETS


def is_anal_preset(label: str) -> bool:
    return (label or "").strip() in ANAL_PRESETS


def is_excrete_preset(label: str) -> bool:
    return (label or "").strip() in EXCRETE_PRESETS


def is_urine_preset(label: str) -> bool:
    return (label or "").strip() in URINE_PRESETS


def is_scat_preset(label: str) -> bool:
    return (label or "").strip() in SCAT_PRESETS


def has_leftover_man(text: str) -> bool:
    cleaned = re.sub(r"\bnot a man\b", " ", text or "", flags=re.I)
    cleaned = re.sub(r"\bnever a man\b", " ", cleaned, flags=re.I)
    return bool(_LEFTOVER_MAN.search(cleaned))


def apply_futa_partner(prompt: str) -> str:
    """Sex presets from the Space use a man. H3 keeps 女体フタナリ（玉なし・20cm）."""
    out = prompt
    for old, new in _FUTA_PARTNER_SWAPS:
        out = out.replace(old, new)
    if has_leftover_man(out):
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
    style: str = "",
    has_ref: bool = False,
) -> str:
    label = (preset or "").strip()
    extra = (user_prompt or "").strip()
    parts: list[str] = []
    if label and label != SEX_PRESET_DEFAULT:
        base = SEX_PRESETS.get(label)
        if not base:
            raise SystemExit(f"unknown quick prompt: {label}")
        if is_excrete_preset(label):
            parts.append(base)
            if is_urine_preset(label) and URINE_DETAIL not in parts:
                parts.append(URINE_DETAIL)
            if is_scat_preset(label) and SCAT_DETAIL not in parts:
                parts.append(SCAT_DETAIL)
        elif is_sex_act_preset(label):
            parts.append(apply_futa_partner(base) if futa else base)
            if futa and is_anal_preset(label) and ANAL_DETAIL not in parts:
                parts.append(ANAL_DETAIL)
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
    pose_ok = (
        bool(extra)
        or is_sex_act_preset(label)
        or is_excrete_preset(label)
        or label in {"ウェットシャワー", "セルフタッチ"}
    )
    scope = ACT_SCOPE if pose_ok else CLOTHING_SCOPE
    i2i = I2I_REF if has_ref else I2I_SINGLE
    locked = f"{IDENTITY_LOCK} {i2i} {scope} {joined}"
    return apply_style(locked, style)


def lora_stack(
    undress: bool,
    futa: bool,
    preset: str = "",
) -> list[tuple[str, float, str]]:
    rows: list[tuple[str, float, str]] = []
    label = (preset or "").strip()
    if label in OUTFIT_PRESETS:
        return rows
    if is_excrete_preset(label):
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


def tune_edit_vae(pipe: Any) -> None:
    """Qwen VAE has tiling. Older AutoencoderKL also has slicing. Do not crash ②."""
    vae = getattr(pipe, "vae", None)
    if vae is None:
        return
    if hasattr(vae, "enable_tiling"):
        try:
            vae.enable_tiling(tile_sample_min_width=256, tile_sample_min_height=256)
        except TypeError:
            vae.enable_tiling()
    if hasattr(vae, "enable_slicing"):
        vae.enable_slicing()


def disable_safety(pipe: Any) -> Any:
    """Mk1227-class: no safety checker, no NSFW filter."""
    if hasattr(pipe, "safety_checker"):
        pipe.safety_checker = None
    if hasattr(pipe, "requires_safety_checker"):
        pipe.requires_safety_checker = False
    return pipe


def vram_used_gib(torch_module: Any = None) -> float:
    if torch_module is None or not getattr(torch_module, "cuda", None):
        return 0.0
    try:
        if not torch_module.cuda.is_available():
            return 0.0
        free, total = torch_module.cuda.mem_get_info()
    except Exception:
        return 0.0
    return (total - free) / 1024 ** 3


def is_cuda_oom(err: BaseException) -> bool:
    if type(err).__name__ == "OutOfMemoryError":
        return True
    return "out of memory" in str(err).lower()


def free_cuda(torch_module: Any = None) -> None:
    gc.collect()
    if torch_module is None:
        return
    cuda = getattr(torch_module, "cuda", None)
    if cuda is None:
        return
    try:
        cuda.empty_cache()
    except Exception:
        pass
    ipc = getattr(cuda, "ipc_collect", None)
    if callable(ipc):
        try:
            ipc()
        except Exception:
            pass


def clamp_edit_vae_area(
    pipe: Any = None,
    width: int = DEFAULT_WIDTH,
    height: int = DEFAULT_HEIGHT,
) -> int:
    """Edit-plus still encodes VAE at 1024² unless this module constant is lowered."""
    area = max(32 * 32, int(width) * int(height))
    names = [
        "diffusers.pipelines.qwenimage.pipeline_qwenimage_edit_plus",
        "diffusers.pipelines.qwenimage.pipeline_qwenimage_edit",
    ]
    if pipe is not None:
        names.insert(0, type(pipe).__module__)
    patched = 0
    seen: set[str] = set()
    for name in names:
        if not name or name in seen:
            continue
        seen.add(name)
        mod = sys.modules.get(name)
        if mod is not None and hasattr(mod, "VAE_IMAGE_SIZE"):
            setattr(mod, "VAE_IMAGE_SIZE", area)
            patched += 1
    return area if patched else 0


def force_edit_offload(
    pipe: Any,
    *,
    sequential: bool = True,
    torch_module: Any = None,
) -> str:
    """L4 24GB cannot hold the ~20GB transformer. Sequential is the default."""
    for name in ("maybe_free_model_hooks", "remove_all_hooks", "reset_device_map"):
        fn = getattr(pipe, name, None)
        if callable(fn):
            try:
                fn()
            except Exception:
                pass
    try:
        pipe.to("cpu")
    except Exception:
        pass
    free_cuda(torch_module)
    if hasattr(pipe, "enable_attention_slicing"):
        try:
            pipe.enable_attention_slicing()
        except Exception:
            pass
    mode = "cpu"
    if sequential and hasattr(pipe, "enable_sequential_cpu_offload"):
        pipe.enable_sequential_cpu_offload()
        mode = "sequential_cpu_offload"
    elif hasattr(pipe, "enable_model_cpu_offload"):
        pipe.enable_model_cpu_offload()
        mode = "model_cpu_offload"
    try:
        setattr(pipe, "_qwen_edit_offload", mode)
    except Exception:
        pass
    return mode


def run_pipe_edit(
    pipe: Any,
    images: list[Any],
    kwargs: dict[str, Any],
    torch_module: Any = None,
) -> Any:
    def _call(imgs: list[Any]) -> Any:
        try:
            return pipe(image=imgs, **kwargs).images[0]
        except TypeError:
            first = imgs[0] if imgs else imgs
            return pipe(image=first, **kwargs).images[0]

    try:
        return _call(images)
    except Exception as e:
        if torch_module is None or not is_cuda_oom(e):
            raise
        if getattr(pipe, "_qwen_edit_offload", None) == "sequential_cpu_offload":
            raise
        print("VRAM OOM → sequential_cpu_offload でもう一度")
        free_cuda(torch_module)
        force_edit_offload(pipe, sequential=True, torch_module=torch_module)
        return _call(images)


def infer_kwargs(
    prompt: str,
    *,
    seed: int | None = None,
    steps: int = STEPS,
    true_cfg: float = TRUE_CFG,
    guidance: float = GUIDANCE,
    negative: str = DEFAULT_NEGATIVE,
    torch_module: Any = None,
    device: str = "cpu",
    height: int = DEFAULT_HEIGHT,
    width: int = DEFAULT_WIDTH,
) -> dict[str, Any]:
    gen = None
    if torch_module is not None and seed is not None:
        gen = torch_module.Generator(device=device).manual_seed(int(seed))
    out: dict[str, Any] = {
        "prompt": prompt,
        "num_inference_steps": int(steps),
        "true_cfg_scale": float(true_cfg),
        "num_images_per_prompt": 1,
        "generator": gen,
        "height": int(height),
        "width": int(width),
    }
    if float(true_cfg) > 1.0:
        out["negative_prompt"] = negative
    if float(guidance) > 1.0:
        out["guidance_scale"] = float(guidance)
    return out


def save_jpeg(image: Any, dest: str | Path, quality: int = 92) -> Path:
    path = Path(dest)
    path.parent.mkdir(parents=True, exist_ok=True)
    image.convert("RGB").save(path, "JPEG", quality=quality)
    return path
