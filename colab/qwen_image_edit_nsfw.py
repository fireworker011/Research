"""Qwen Image Edit NSFW. Mk1227 Space runtime on Colab (A100)."""
from __future__ import annotations

import base64
import gc
import io
import json
import re
import sys
from pathlib import Path
from typing import Any

# Mk1227/Qwen-Image-Edit-NSFW .env.example. Compiled app.so is not copied;
# weights, scheduler, FP8, rewrite, auto size, and no extra LoRAs match.
PIPE_ID = "Qwen/Qwen-Image-Edit-2511"
AIO_REPO_ID = "Phr00t/Qwen-Image-Edit-Rapid-AIO"
AIO_FILENAME = "v23/Qwen-Rapid-AIO-NSFW-v23.safetensors"
AIO_REPO_TYPE = "model"
TRANSFORMER_ID = "prithivMLmods/Qwen-Image-Edit-Rapid-AIO-V23"
LORA_REPO = "wiikoo/Qwen-lora-nsfw"

STEPS = 4
TRUE_CFG = 1.0
GUIDANCE = 1.0
DEFAULT_WIDTH = 576
DEFAULT_HEIGHT = 1024
CANVAS_AUTO = "auto（入力）"
CANVAS_FIXED = "576x1024"
CANVAS_OPTIONS = (CANVAS_AUTO, CANVAS_FIXED)
SPACE_GPU_MIN_VRAM_GIB = 20.0
SPACE_GPU_RESIDENT_GIB = 35.0
L4_MIN_VRAM_GIB = SPACE_GPU_MIN_VRAM_GIB
VRAM_OFFLOAD_GIB = 8.0
ENABLE_FP8_QUANT = True
ENABLE_TENSOR_OFFLOADING = True
# Space .env is true. Proven Mk1227 /infer that keeps faces uses False.
DEFAULT_REWRITE_PROMPT = False
REWRITE_MODEL = "Qwen/Qwen2.5-VL-72B-Instruct"
REWRITE_PROVIDER = "nebius"
REWRITE_ASSISTANT_PROMPT = (
    "you are a helpful assistant, you should provide useful answers to users."
)
REWRITE_USER_TEMPLATE = "{system_prompt}\n\nUser Input: {user_prompt}\n\nRewritten Prompt:"
SCHED_SHIFT = 1.0
SCHED_NUM_TRAIN_TIMESTEPS = 1000
SCHED_BASE_IMAGE_SEQ_LEN = 256
SCHED_MAX_IMAGE_SEQ_LEN = 8192
SCHED_TIME_SHIFT_TYPE = "exponential"
SCHED_USE_DYNAMIC_SHIFTING = True
SCHED_BASE_SHIFT = 1.0986122886681098
SCHED_MAX_SHIFT = 1.0986122886681098
# Space .env は torchao==0.11.0。今の git+diffusers は FqnToConfig が要り 0.11 では
# `from diffusers import QwenImageEditPlusPipeline` が落ちる。Colab は 0.16+。
TORCHAO_COLAB_SPEC = "torchao>=0.16.0"
TORCHAO_COLAB_MIN = (0, 16)
DIFFUSERS_COLAB_SPEC = "git+https://github.com/huggingface/diffusers.git"
# Weights stay on the Colab VM HuggingFace cache. Drive only holds JPGs.
DRIVE_FREE_GIB = 2
WEIGHTS_CACHE_GIB = 70
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
SYSTEM_PROMPT = """
# Edit Instruction Rewriter
You are a professional edit instruction rewriter. Your task is to generate a precise, concise, and visually achievable professional-level edit instruction based on the user-provided instruction and the image to be edited.

Please strictly follow the rewriting rules below:

## 1. General Principles
- Keep the rewritten prompt **concise and comprehensive**. Avoid overly long sentences and unnecessary descriptive language.
- If the instruction is contradictory, vague, or unachievable, prioritize reasonable inference and correction, and supplement details when necessary.
- Keep the main part of the original instruction unchanged, only enhancing its clarity, rationality, and visual feasibility.
- All added objects or modifications must align with the logic and style of the scene in the input images.
- If multiple sub-images are to be generated, describe the content of each sub-image individually.

## 2. Task-Type Handling Rules

### 1. Add, Delete, Replace Tasks
- If the instruction is clear (already includes task type, target entity, position, quantity, attributes), preserve the original intent and only refine the grammar.
- If the description is vague, supplement with minimal but sufficient details (category, color, size, orientation, position, etc.).
- Remove meaningless instructions: e.g., "Add 0 objects" should be ignored or flagged as invalid.
- For replacement tasks, specify "Replace Y with X" and briefly describe the key visual features of X.

### 2. Text Editing Tasks
- All text content must be enclosed in English double quotes. Keep the original language of the text, and keep the capitalization.
- Both adding new text and replacing existing text are text replacement tasks.
- Specify text position, color, and layout only if user has required.

### 3. Human Editing Tasks
- Make the smallest changes to the given user's prompt.
- If changes to background, action, expression, camera shot, or ambient lighting are required, please list each modification individually.
- Edits to makeup or facial features / expression must be subtle, not exaggerated, and must preserve the subject's identity consistency.
- Never rewrite as "generate a new image" or describe a new person. Keep the same face, hair, and person as the input.

### 4. Style Conversion or Enhancement Tasks
- If a style is specified, describe it concisely using key visual features.
- For style reference, analyze the original image and extract key characteristics, integrating them into the instruction.
- Colorization tasks (including old photo restoration) must use the fixed template: "Restore and colorize the old photo."

### 5. Material Replacement
- Clearly specify the object and the material.

### 6. Logo/Pattern Editing
- Material replacement should preserve the original shape and structure as much as possible.

### 7. Multi-Image Tasks
- Rewritten prompts must clearly point out which image's element is being modified.

## 3. Rationale and Logic Check
- Resolve contradictory instructions.
- Supplement missing critical information.

# Output Format Example
```json
{
 "Rewritten": "..."
}
```
""".strip()

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
UNCENSOR_TRIGGER = "nsfw, penis, vagina, nipples"
UNCENSOR_ANAL_TRIGGER = "nsfw, penis, anus, anal, nipples"
UNCENSOR_SCAT_TRIGGER = "nsfw, penis, anus, feces, nipples"
LORA_TRIGGERS = {
    "remove_clothing": "remove her clothing",
    "CockQwen_v3": "Erect Penis",
    "qwen_uncensor": UNCENSOR_TRIGGER,
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
FACE_KEEP = (
    "Keep the exact same face, hair, and person as the input image. "
    "Keep the exact same art medium. Do not swap to a different person. Adult 21+."
)
REF_FACE = (
    "Picture 2 is the face lock of the same person. Copy face, hair, and art medium from Picture 2. "
    "Edit Picture 1. Do not copy Picture 2's crop or clothes unless asked."
)
FUTA_LOCK = (
    "Same person, same face. Fully nude. Futanari: a fully erect 20cm human penis with pale shaft and pink glans "
    "standing in front of the crotch, hairless female pussy visible at the base of the shaft, "
    "no testicles, no scrotum, no balls. Female breasts. Not a man. Do not redraw the face."
)
T2I_REWRITE_RE = re.compile(
    r"\b(?:generate a new image|generate an image(?: of)?|create a new image|"
    r"create an image of|text-to-image|from scratch)\b",
    re.I,
)
DEFAULT_EDIT_PROMPT = (
    f"{KEEP_LOCK} Remove only the clothes. Do not tie the hair. {FUTA_LOCK}"
)
DEFAULT_NEGATIVE = ""
STYLE_PRESET_DEFAULT = "入力のまま"
STYLE_LABELS = ("アニメ絵", "リアル", "3D", "漫画")
STYLE_PRESETS = {
    STYLE_PRESET_DEFAULT: (
        "Keep the exact same art medium as the input image: same line work, coloring, "
        "shading, and texture. This is an edit of that picture, not a restyle."
    ),
    "アニメ絵": (
        "Stay 2D Japanese anime. Do not convert to photoreal, 3D CGI, or live action."
    ),
    "リアル": "Stay photorealistic live-action. Do not convert to anime, manga, or 3D CGI.",
    "3D": "Stay 3D CGI. Do not convert to 2D anime, manga, or a real photograph.",
    "漫画": (
        "Stay 2D manga / comic with the same ink and screentones. "
        "Do not convert to photoreal or 3D CGI."
    ),
}
STYLE_NEGATIVES = {
    "アニメ絵": "photorealistic, photograph, 3d render, real skin pores, live action",
    "リアル": "anime, manga, cartoon, 3d render, illustration, lineart, cel shading",
    "3D": "2d anime, manga, photograph, live action, flat cel, lineart screentone",
    "漫画": "photorealistic, 3d render, live action, painterly, photograph, cgi",
}
ANAL_HOLE_LOCK = (
    "ANAL HOLE LOCK: The erect 20cm is in the ANUS. The wet pink anal ring stretches "
    "around the shaft. The sphincter grips it. This is anal sex. Never vaginal. "
    "Never the front hole."
)
ANAL_ANATOMY = (
    "ANAL ANATOMY: The anus is the rear hole toward the tailbone (coccyx). "
    "Enter that rear hole only. The front hole toward the belly stays closed and unused."
)
ANAL_JOIN = (
    "ANAL JOIN: Two adult futanari women, not a man. Female breasts, erect 20cm each, "
    "no testicles. The partner's 20cm glans and shaft are inside the receiver's stretched "
    "anal ring only. Show penis-in-anus: the sphincter gripping the shaft. "
    "The receiver's own 20cm hangs free in front, empty of any penis. "
    "Unused pussy stays shut and is not the joining point. No clothes. Adult 21+."
)
ANAL_DETAIL = f"{ANAL_HOLE_LOCK} {ANAL_ANATOMY} {ANAL_JOIN}"
ANAL_CLOSE = "JOIN CLOSE: The penis entering in this image is in the anus."
ANAL_REAR_LOCK = (
    "REAR ANAL LOCK: From behind, all fours, or standing doggy: camera on the buttocks. "
    "The UPPER hole toward the tailbone is the anus — the 20cm is in THAT hole only. "
    "The LOWER front hole toward the belly stays closed. "
    "Joining point is penis-in-anus, the upper hole. Not a front-crotch crop."
)
ANAL_FRONT_LOCK = (
    "FRONT ANAL LOCK: Facing camera, on her back, lap, or sitting down: hips tilted so "
    "the rear hole is reachable. The LOWER hole toward the buttocks is the anus — the 20cm "
    "is in THAT hole only. The UPPER front hole toward the belly stays closed. "
    "Joining point is penis-in-anus below the closed front hole. Not a vaginal crop."
)
_ANAL_CUE_RE = re.compile(r"アナル|肛門|\banal\b|\banus\b", re.I)
_SCAT_CUE_RE = re.compile(
    r"脱糞|うんこ|糞|\bscat\b|\bfeces\b|\bdefecat|\bstool\b|\bturd\b",
    re.I,
)
_URINE_CUE_RE = re.compile(
    r"放尿|おしっこ|小便|飲尿|\burine\b|\bpee\b|\bpiss\b",
    re.I,
)
STYLE_PIN_LABELS = frozenset({"ウェットシャワー", "セルフタッチ"})
ANAL_REAR_PRESETS = frozenset({"アナルバック", "アナル立ちバック"})
ANAL_FRONT_PRESETS = frozenset({"アナル正常位", "アナル騎乗位", "アナル座位", "肛門リフト"})
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
SCAT_HOLE_LOCK = (
    "SCAT HOLE LOCK: Feces leaves the ANUS only — the rear hole between the buttocks, "
    "toward the tailbone. The log is still attached to the stretched anal opening. "
    "Nothing comes out of the front hole, the urethra, or the penis. Not from off-screen."
)
SCAT_ACT = (
    "SCAT ACT: She is defecating from the anus now. Camera on the buttocks. "
    "A thick formed opaque brown human turd is being pushed out of the dilated anus. "
    "Sausage-shaped, two fingers thick, ring-segmented. Soft-solid like clay: it hangs, "
    "sags, breaks, and piles. It does not bounce. It does not stretch like slime. "
    "This is the act of passing stool now, not a body already coated from before."
)
FECES_LOOK = (
    "FECES LOOK: A real thick human turd. Opaque dull-matte medium-dark brown like wet "
    "garden soil or used coffee grounds — the color of adult human stool. Cylindrical, "
    "sausage-thick (about two fingers wide), with visible ring-segments. The tapered tip "
    "comes out of the dilated anus first; the rest of the log stays connected to the anal "
    "opening and hangs by gravity. Soft-solid like clay or putty: it sags, folds, and piles "
    "on itself. Surface slightly moist, interior dense. Smears as lumpy paste, not a sheet. "
    "Not chocolate syrup. Not caramel. Not ice cream. Not translucent amber gel. "
    "Not bouncing jelly. Not rubbery slime. Not stretchy gel strands. Not a glossy blob. "
    "Not a cartoon swirl. Not a uniform slime sheet. Not watery diarrhea. "
    "Keep the identical face and the input art medium. Adult futanari: 20cm penis, unused "
    "front hole shut, no testicles. Not a man. Adult 21+."
)
SCAT_DETAIL = f"{SCAT_HOLE_LOCK} {SCAT_ACT} {FECES_LOOK}"

# ayooo123 / Mk1227 のクイックプロンプトと同じ12個。行為の竿はフタナリに差し替える。
SEX_PRESET_DEFAULT = "服抜きフタナリ（既定）"
SEX_PRESETS = {
    "服を脱ぐ": (
        "Remove all clothing from the person. Keep the exact same camera angle, framing, crop, pose, "
        "and IDENTICAL FACE as the input image — same facial features, same expression, same person, "
        "zero changes to face."
    ),
    "ウェットシャワー": (
        "Medium shot, front-facing camera. THE SAME WOMAN from the input image with the IDENTICAL FACE — "
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
        "POV close-up from the man's perspective looking down. THE SAME WOMAN from this image with the "
        "IDENTICAL FACE — same facial features, same eyes, nose, mouth, absolutely unchanged, fully nude "
        "with bare breasts exposed, performing oral sex on a large thick erect penis. Her face fills most "
        "of the frame, lips wrapped around the shaft. One hand grips the base. She keeps eye contact with "
        "the camera. The penis enters from the bottom of the frame — only the shaft visible. Same "
        "environment and lighting as the input image. Face must remain exactly as in the input image."
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
        "POV — he lies on his back below, THE SAME WOMAN from the image with the IDENTICAL FACE — same "
        "facial features, unchanged, same expression — straddles him facing the camera with a satisfied "
        "look, hands on her own hips. She is topless with bare breasts exposed, lower body fully nude, "
        "sitting on his erect penis inserted into her from below. The man's bare chest is visible at the "
        "bottom edge; his head, face and arms are completely out of view. Same environment as the input "
        "image. Face must remain exactly as in the source image."
    ),
    "乳房プレイ": (
        "THE SAME WOMAN from this image with the IDENTICAL FACE — absolutely unchanged facial features, "
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
        "Same environment and lighting as the input image. "
        "THE SAME WOMAN with the IDENTICAL FACE — absolutely unchanged facial features, same person, same "
        "expression — is held up in the air with her legs raised wide in an M shape, her body facing the "
        "camera, completely nude. An adult futanari holds her up from behind. Camera shows the joining: "
        "the partner's erect 20cm enters from below into the ANUS, the LOWER hole toward the buttocks, "
        "not the upper front hole. Anal ring around the shaft. Bare breasts visible. Partner mostly "
        "out of view behind her. Face shows intense pleasure. Not vaginal. Face must remain exactly as "
        "in the input image."
    ),
    "アナルバック": (
        "Rear three-quarter view, slightly low, camera on the buttocks and the joining. THE SAME PERSON "
        "from the input image with the IDENTICAL FACE — same facial features, same eyes, nose, mouth, "
        "absolutely unchanged — looks back over her shoulder so her face is fully visible. She is on all "
        "fours in doggy position, completely nude, back arched, knees apart. An adult futanari partner "
        "kneels behind her; partner's face out of frame. The partner's erect 20cm is thrusting into the "
        "receiver's ANUS — the UPPER rear hole toward the tailbone. The anal ring stretches around the "
        "shaft. The receiver's own 20cm hangs in front. Same environment. Not a man. Not vaginal."
    ),
    "アナル立ちバック": (
        "Full-body three-quarter rear view, camera on the buttocks. THE SAME PERSON from the input image "
        "with the IDENTICAL FACE — same facial features, unchanged — is standing, bent forward at the waist "
        "in standing doggy, hands braced on a wall or bed, looking back so her face is visible. Completely "
        "nude. An adult futanari partner stands behind her, face out of frame, hips flush against her ass. "
        "The partner's erect 20cm is buried in the receiver's ANUS — the UPPER rear hole gripping the shaft. "
        "The receiver's own erect 20cm hangs between her thighs. Same environment. Not a man. Not vaginal."
    ),
    "アナル正常位": (
        "Three-quarter view from above and in front, medium shot. THE SAME PERSON from the input image with "
        "the IDENTICAL FACE — same facial features, unchanged — lies on her back in anal missionary, hips "
        "tilted up, legs folded toward her chest or spread in an M, looking at the camera. Completely nude. "
        "The partner's erect 20cm is inserted in the LOWER hole toward the buttocks — the ANUS. Anal ring "
        "around the shaft. Her own erect 20cm lies on her belly. Partner between her legs, face out of "
        "frame. Same environment. Not a man. Not vaginal."
    ),
    "アナル騎乗位": (
        "Eye-level medium shot, front. THE SAME PERSON from the input image with the IDENTICAL FACE — same "
        "facial features, unchanged — is anal riding: sitting down onto the partner's 20cm with her ANUS, "
        "facing the camera, completely nude, straddling an adult futanari partner who lies on her back below. "
        "Partner's face out of frame. The buttocks sit down on the shaft; the penis is in the anus from below. "
        "The receiver's own erect 20cm stands in front. Hands on her own thighs. Same environment. Not a man. "
        "Not vaginal."
    ),
    "アナル座位": (
        "Eye-level medium shot. THE SAME PERSON from the input image with the IDENTICAL FACE — same facial "
        "features, unchanged — sits in an adult futanari partner's lap in seated anal sex, more upright than "
        "anal riding, feet down or hooked, completely nude. Partner sits on a chair or the edge of the bed, "
        "face out of frame. The partner's erect 20cm is in the receiver's ANUS — the LOWER hole toward the "
        "buttocks takes the full shaft. The receiver's own erect 20cm is visible in front. Same environment. "
        "Not a man. Not vaginal."
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
        "Rear three-quarter from behind and slightly below. Camera on the buttocks. THE SAME PERSON from "
        "the input with the IDENTICAL FACE — same facial features, unchanged, looking back so her face is "
        "readable. She squats fully nude, knees apart. Between the buttocks the ANUS is dilated. A thick "
        "formed opaque brown human turd, sausage-shaped and two fingers thick, is being pushed out of that "
        "anus now, still attached to the stretched anal opening, hanging and sagging like clay. Her 20cm "
        "futanari penis hangs in front, unused. No testicles. Not a man. Not from the front hole."
    ),
    "脱糞（後背）": (
        "Rear three-quarter view, slightly low, camera on the buttocks. THE SAME PERSON from the input with "
        "the IDENTICAL FACE — same facial features, unchanged — looks back over her shoulder so her face is "
        "readable. She is on all fours, fully nude. Her 20cm futanari penis hangs between her thighs. The "
        "UPPER hole toward the tailbone is the anus: a thick formed opaque brown human turd is leaving that "
        "anus now, still attached to the opening, hanging and sagging like clay, two fingers thick, "
        "ring-segmented. The LOWER front hole stays closed with nothing coming out. No testicles. Not a man."
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


def require_space_gpu_or_exit(vram_gib: float, name: str = "") -> None:
    """T4 is too small. A100/H100 hold the Space stack. L4 offloads."""
    label = (name or "").strip() or "GPU"
    if vram_gib < SPACE_GPU_MIN_VRAM_GIB:
        raise SystemExit(
            f"{label} の VRAM が {vram_gib:.1f} GiB。"
            "A100（40GB または 80GB）か H100 を選んで①からやり直してください。T4 は不可。"
        )


def require_l4_or_exit(vram_gib: float, name: str = "") -> None:
    """Back-compat name. Same gate as require_space_gpu_or_exit."""
    require_space_gpu_or_exit(vram_gib, name)


def space_device_mode(vram_gib: float) -> str:
    if float(vram_gib) >= SPACE_GPU_RESIDENT_GIB:
        return "cuda"
    return "model_cpu_offload"


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
    """Drop cached torchao after a pip reinstall. peft caches availability."""
    for name in list(sys.modules):
        if name == "torchao" or name.startswith("torchao."):
            del sys.modules[name]
    peft_utils = sys.modules.get("peft.import_utils")
    fn = getattr(peft_utils, "is_torchao_available", None)
    cache_clear = getattr(fn, "cache_clear", None)
    if callable(cache_clear):
        cache_clear()


def drop_stale_diffusers_modules() -> None:
    """②を同じランタイムで再実行したとき、失敗した import の残骸を捨てる。"""
    for name in list(sys.modules):
        if name == "diffusers" or name.startswith("diffusers."):
            del sys.modules[name]


def require_torchao_for_git_diffusers(version: str | None = None) -> str:
    """git+diffusers imports FqnToConfig. torchao 0.11 cannot."""
    try:
        import torchao

        ver = version or str(getattr(torchao, "__version__", "0"))
        from torchao.quantization import FqnToConfig  # noqa: F401
    except Exception as e:
        raise SystemExit(
            f"torchao が git+diffusers と食い違う（{e}）。"
            f"{TORCHAO_COLAB_SPEC} を入れて②をやり直す。まだならランタイム再起動→①②。"
        ) from e
    major, minor = pillow_major_minor(ver)
    if (major, minor) < TORCHAO_COLAB_MIN:
        raise SystemExit(
            f"torchao {ver} は git+diffusers に足りない（FqnToConfig）。"
            f"{TORCHAO_COLAB_SPEC} を入れて②をやり直す。まだならランタイム再起動→①②。"
        )
    return ver


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


def auto_canvas_size(
    image: Any,
    *,
    min_size: int = 256,
    max_size: int = 2048,
    multiple: int = 32,
) -> tuple[int, int]:
    """Space DEFAULT_HEIGHT/WIDTH=auto. Keep aspect, snap to 32, clamp 256–2048."""
    rgb = image.convert("RGB") if hasattr(image, "convert") else image
    w, h = rgb.size
    scale = 1.0
    longest = max(w, h)
    shortest = min(w, h)
    if longest > max_size:
        scale = max_size / float(longest)
    if shortest * scale < min_size:
        scale = min_size / float(shortest)
    w = int(round(w * scale))
    h = int(round(h * scale))
    w = min(max(w, min_size), max_size)
    h = min(max(h, min_size), max_size)
    return snapped_size(w, h, multiple)


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
        "Mk1227 Space と同じ載せ方: 2511 + Phr00t AIO NSFW v23 単一ファイル + FP8 + scheduler。",
        "Drive に置くのは input/ と output/ の JPG だけ。",
        f"Drive の空きは {DRIVE_FREE_GIB}GB あれば足りる。H3 の参照土台 21GB は不要。",
        f"重みは Colab ディスク（HuggingFace キャッシュ 約{WEIGHTS_CACHE_GIB}GB）。Drive には載せない。",
        "GPU は A100 / H100。L4 は offload。T4 は不可。",
        "スマホは Drive input。アップロード（ファイル選択）は PC だけ。",
    ]


def canvas_form_options() -> list[str]:
    return list(CANVAS_OPTIONS)


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


def face_lock_image(image: Any) -> Any:
    """Picture 2 for Edit Plus. Portrait → upper crop. Close-up → same frame."""
    rgb = image.convert("RGB") if hasattr(image, "convert") else image
    w, h = rgb.size
    if h >= int(w * 1.25):
        crop_h = max(64, int(h * 0.40))
        crop_w = max(64, int(w * 0.78))
        left = max(0, (w - crop_w) // 2)
        top = int(h * 0.03)
        rgb = rgb.crop((left, top, min(w, left + crop_w), min(h, top + crop_h)))
    return snapped_rgb(rgb)


def lock_identity_prompt(
    prompt: str,
    *,
    has_ref: bool = False,
    style: str = "",
    pin_ends: bool = False,
) -> str:
    """Rewrite/VL often drops the face. Re-lead with FACE_KEEP. Strip t2i phrasing."""
    out = T2I_REWRITE_RE.sub(" ", prompt or "")
    out = re.sub(r" +", " ", out).strip()
    if not out.lower().startswith(FACE_KEEP.lower()):
        out = f"{FACE_KEEP} {out}".strip()
    if has_ref and REF_FACE.lower() not in out.lower():
        out = f"{out} {REF_FACE}".strip()
    return apply_style(out, style, pin_ends=pin_ends)


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


_PHOTO_STYLE_PULL = (
    (re.compile(r"Amateur phone-camera snapshot,?\s*", re.I), ""),
    (re.compile(r"natural indoor lighting,?\s*", re.I), ""),
    (re.compile(r"\bthe original photo\b", re.I), "the input image"),
    (re.compile(r"\binput photo\b", re.I), "input image"),
    (re.compile(r"\bthis photo\b", re.I), "this image"),
    (re.compile(r"\bfrom the photo\b", re.I), "from the image"),
    (re.compile(r"\bthe photo\b", re.I), "the image"),
)


def strip_photo_style_pull(text: str) -> str:
    """Sex presets from the Space say photo. That restyles anime/3D inputs."""
    out = text or ""
    for cre, repl in _PHOTO_STYLE_PULL:
        out = cre.sub(repl, out)
    return re.sub(r" {2,}", " ", out).strip()


def apply_style(prompt: str, style: str = "", *, pin_ends: bool = False) -> str:
    label = (style or "").strip() or STYLE_PRESET_DEFAULT
    lock = STYLE_PRESETS.get(label)
    if not lock:
        raise SystemExit(f"unknown style: {label}")
    out = prompt or ""
    out = out.replace("Realistic nude body, natural skin.", "")
    if label != "リアル":
        out = strip_photo_style_pull(out)
    if pin_ends and out.lower().startswith(FACE_KEEP.lower()):
        rest = out[len(FACE_KEEP) :].lstrip()
        if not rest.lower().startswith(lock.lower()):
            out = f"{FACE_KEEP} {lock} {rest}".strip()
    if lock.lower() not in out.lower():
        out = f"{out} {lock}".strip()
    elif pin_ends and not out.lower().endswith(lock.lower()):
        out = f"{out} {lock}".strip()
    return out.strip()


def is_sex_act_preset(label: str) -> bool:
    return (label or "").strip() in SEX_ACT_PRESETS


def is_anal_preset(label: str) -> bool:
    return (label or "").strip() in ANAL_PRESETS


def wants_anal_lock(text: str = "", preset: str = "") -> bool:
    if is_anal_preset(preset):
        return True
    return bool(_ANAL_CUE_RE.search(text or ""))


def is_excrete_preset(label: str) -> bool:
    return (label or "").strip() in EXCRETE_PRESETS


def is_urine_preset(label: str) -> bool:
    return (label or "").strip() in URINE_PRESETS


def is_scat_preset(label: str) -> bool:
    return (label or "").strip() in SCAT_PRESETS


def wants_scat_lock(text: str = "", preset: str = "") -> bool:
    if is_scat_preset(preset):
        return True
    return bool(_SCAT_CUE_RE.search(text or ""))


def wants_urine_lock(text: str = "", preset: str = "") -> bool:
    if is_urine_preset(preset):
        return True
    return bool(_URINE_CUE_RE.search(text or ""))


def pins_style_lock(preset: str = "", extra: str = "") -> bool:
    """Sex/excrete/pose-change restyle to photoreal unless the medium is pinned both ends."""
    label = (preset or "").strip()
    return (
        is_sex_act_preset(label)
        or is_excrete_preset(label)
        or wants_anal_lock(extra, label)
        or wants_scat_lock(extra, label)
        or wants_urine_lock(extra, label)
        or label in STYLE_PIN_LABELS
    )


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
    anal = wants_anal_lock(extra, label)
    scat = wants_scat_lock(extra, label)
    urine = wants_urine_lock(extra, label)
    if label and label != SEX_PRESET_DEFAULT:
        base = SEX_PRESETS.get(label)
        if not base:
            raise SystemExit(f"unknown quick prompt: {label}")
        if is_excrete_preset(label):
            if is_scat_preset(label):
                parts.append(SCAT_HOLE_LOCK)
                parts.append(base)
                parts.append(SCAT_ACT)
                parts.append(FECES_LOOK)
            else:
                parts.append(base)
                if URINE_DETAIL not in parts:
                    parts.append(URINE_DETAIL)
        elif is_sex_act_preset(label):
            pose = apply_futa_partner(base) if futa else base
            if is_anal_preset(label):
                parts.append(ANAL_HOLE_LOCK)
                if label in ANAL_REAR_PRESETS:
                    parts.append(ANAL_REAR_LOCK)
                elif label in ANAL_FRONT_PRESETS:
                    parts.append(ANAL_FRONT_LOCK)
                parts.append(pose)
                if futa:
                    parts.append(ANAL_ANATOMY)
                    parts.append(ANAL_JOIN)
                parts.append(ANAL_CLOSE)
            else:
                parts.append(pose)
        else:
            parts.append(base)
            blob = base.lower()
            outfit = label in OUTFIT_PRESETS
            if not outfit:
                if undress and label == "服を脱ぐ":
                    pass
                elif undress and "remove all clothing" not in blob and "completely nude" not in blob:
                    parts.append("Remove only the clothes. Do not tie the hair.")
                if futa and "20cm" not in " ".join(parts).lower() and not anal:
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
        if scat:
            if SCAT_HOLE_LOCK not in parts:
                parts.insert(0, SCAT_HOLE_LOCK)
            if SCAT_ACT not in parts:
                parts.append(SCAT_ACT)
            if FECES_LOOK not in parts:
                parts.append(FECES_LOOK)
        elif anal:
            if ANAL_HOLE_LOCK not in parts:
                parts.insert(0, ANAL_HOLE_LOCK)
            if futa and ANAL_JOIN not in parts:
                parts.append(ANAL_ANATOMY)
                parts.append(ANAL_JOIN)
            if ANAL_CLOSE not in parts:
                parts.append(ANAL_CLOSE)
        elif urine:
            if URINE_DETAIL not in parts:
                parts.append(URINE_DETAIL)
        if undress and "remove only the clothes" not in blob and not anal and not scat and not urine:
            parts.append("Remove only the clothes. Do not tie the hair.")
        if futa and "20cm" not in " ".join(parts).lower() and not anal and not scat and not urine:
            parts.append(FUTA_LOCK)
    pose_ok = (
        bool(extra)
        or is_sex_act_preset(label)
        or is_excrete_preset(label)
        or label in STYLE_PIN_LABELS
    )
    # Rapid-AIO's VL template already says "generate a new image". A wall of
    # IDENTITY/I2I/SCOPE meta makes it obey the text and drop the source face.
    # Lead with a short keep-face line. Proven Space /infer also keeps rewrite off.
    if not " ".join(parts).lower().startswith(FACE_KEEP.lower()):
        parts.insert(0, FACE_KEEP)
    if anal and ANAL_HOLE_LOCK in parts:
        parts = [p for p in parts if p != ANAL_HOLE_LOCK]
        parts.insert(1, ANAL_HOLE_LOCK)
    if scat and SCAT_HOLE_LOCK in parts:
        parts = [p for p in parts if p != SCAT_HOLE_LOCK]
        parts.insert(1, SCAT_HOLE_LOCK)
    if not pose_ok and "change clothing only" not in " ".join(parts).lower():
        parts.append("Change clothing only. Keep the exact same pose, camera, crop, lighting, and background.")
    if has_ref:
        parts.append(REF_FACE)
    joined = " ".join(parts)
    for trig in extra_triggers or []:
        t = (trig or "").strip()
        if t and t.lower() not in joined.lower():
            parts.append(t)
            joined = " ".join(parts)
    return apply_style(joined, style, pin_ends=pins_style_lock(label, extra))


def lora_trigger(name: str, preset: str = "", extra: str = "") -> str:
    if name == "qwen_uncensor":
        if wants_anal_lock(extra, preset):
            return UNCENSOR_ANAL_TRIGGER
        if wants_scat_lock(extra, preset):
            return UNCENSOR_SCAT_TRIGGER
    return LORA_TRIGGERS[name]


def lora_stack(
    undress: bool,
    futa: bool,
    preset: str = "",
    extra: str = "",
) -> list[tuple[str, float, str]]:
    rows: list[tuple[str, float, str]] = []
    label = (preset or "").strip()

    def add(name: str) -> None:
        rows.append((name, LORA_WEIGHTS[name], lora_trigger(name, label, extra)))

    if label in OUTFIT_PRESETS:
        return rows
    if is_excrete_preset(label):
        add("qwen_uncensor")
        if futa:
            add("CockQwen_v3")
        return rows
    if is_sex_act_preset(label):
        add("qwen_uncensor")
        if not wants_anal_lock(extra, label):
            add("Qwen4Play_v2")
        if futa:
            add("CockQwen_v3")
        return rows
    if undress:
        add("remove_clothing")
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


def classify_aio_key(key: str) -> tuple[str, str] | None:
    """Map ComfyUI / diffusers AIO keys. WaifuLuna/QwenEditHot load path."""
    if key.startswith("model.diffusion_model."):
        return "transformer", key[len("model.diffusion_model.") :]
    if key.startswith("diffusion_model."):
        return "transformer", key[len("diffusion_model.") :]
    if key.startswith("transformer."):
        return "transformer", key[len("transformer.") :]
    if key.startswith("first_stage_model."):
        return "vae", key[len("first_stage_model.") :]
    if key.startswith("vae."):
        return "vae", key[len("vae.") :]
    if "conditioner.embedders.0." in key:
        return "text_encoder", key.split("conditioner.embedders.0.", 1)[1]
    if key.startswith("text_encoder."):
        return "text_encoder", key[len("text_encoder.") :]
    idx = key.find("text_encoder.")
    if idx >= 0:
        return "text_encoder", key[idx + len("text_encoder.") :]
    return None


def split_aio_state_dict(state_dict: dict[str, Any]) -> dict[str, dict[str, Any]]:
    buckets: dict[str, dict[str, Any]] = {
        "transformer": {},
        "vae": {},
        "text_encoder": {},
    }
    for key, value in state_dict.items():
        hit = classify_aio_key(key)
        if hit is None:
            continue
        bucket, new_key = hit
        buckets[bucket][new_key] = value
    return buckets


def inject_aio_state(pipe: Any, state_dict: dict[str, Any]) -> dict[str, Any]:
    buckets = split_aio_state_dict(state_dict)
    first = next(iter(state_dict), "")
    stats: dict[str, Any] = {
        "first_key": first,
        "transformer": len(buckets["transformer"]),
        "vae": len(buckets["vae"]),
        "text_encoder": len(buckets["text_encoder"]),
        "transformer_missing": 0,
        "vae_missing": 0,
        "text_encoder_missing": 0,
    }
    for name in ("transformer", "vae", "text_encoder"):
        weights = buckets[name]
        module = getattr(pipe, name, None)
        if not weights or module is None or not hasattr(module, "load_state_dict"):
            continue
        msg = module.load_state_dict(weights, strict=False)
        missing = getattr(msg, "missing_keys", None) or []
        stats[f"{name}_missing"] = len(missing)
    return stats


def load_aio_checkpoint(pipe: Any, path: str | Path) -> dict[str, Any]:
    from safetensors.torch import load_file

    state = load_file(str(path))
    try:
        return inject_aio_state(pipe, state)
    finally:
        del state
        gc.collect()


def space_scheduler_config(base: dict[str, Any] | None = None) -> dict[str, Any]:
    cfg = dict(base or {})
    cfg.update(
        {
            "shift": SCHED_SHIFT,
            "num_train_timesteps": SCHED_NUM_TRAIN_TIMESTEPS,
            "base_image_seq_len": SCHED_BASE_IMAGE_SEQ_LEN,
            "max_image_seq_len": SCHED_MAX_IMAGE_SEQ_LEN,
            "time_shift_type": SCHED_TIME_SHIFT_TYPE,
            "use_dynamic_shifting": SCHED_USE_DYNAMIC_SHIFTING,
            "base_shift": SCHED_BASE_SHIFT,
            "max_shift": SCHED_MAX_SHIFT,
        }
    )
    return cfg


def apply_space_scheduler(pipe: Any, scheduler_cls: Any = None) -> Any:
    cls = scheduler_cls
    if cls is None:
        from diffusers import FlowMatchEulerDiscreteScheduler

        cls = FlowMatchEulerDiscreteScheduler
    current = getattr(pipe, "scheduler", None)
    base = dict(getattr(current, "config", {}) or {})
    pipe.scheduler = cls.from_config(space_scheduler_config(base))
    return pipe.scheduler


def quantize_transformer_fp8(transformer: Any) -> str:
    """Mk1227 ENABLE_FP8_QUANT. torchao float8 weight-only."""
    if transformer is None:
        return "skip (no transformer)"
    try:
        from torchao.quantization import quantize_
    except Exception as e:
        return f"skip ({e})"
    attempts: list[tuple[str, Any]] = []
    try:
        from torchao.quantization import Float8WeightOnlyConfig

        attempts.append(("Float8WeightOnlyConfig", Float8WeightOnlyConfig()))
    except Exception:
        pass
    try:
        from torchao.quantization import float8_weight_only

        attempts.append(("float8_weight_only", float8_weight_only()))
    except Exception:
        pass
    try:
        from torchao.quantization import Float8DynamicActivationFloat8WeightConfig

        attempts.append(
            (
                "Float8DynamicActivationFloat8WeightConfig",
                Float8DynamicActivationFloat8WeightConfig(),
            )
        )
    except Exception:
        pass
    errors: list[str] = []
    for name, cfg in attempts:
        try:
            quantize_(transformer, cfg)
            return name
        except Exception as e:
            errors.append(f"{name}: {e}")
    blob = "; ".join(errors)[:240] if errors else "no torchao float8 config"
    return f"skip ({blob})"


def parse_rewritten_prompt(raw: str) -> str:
    text = (raw or "").strip()
    if not text:
        return ""
    cleaned = text.replace("```json", "").replace("```", "").strip()
    try:
        data = json.loads(cleaned)
    except Exception:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start >= 0 and end > start:
            try:
                data = json.loads(cleaned[start : end + 1])
            except Exception:
                return text.replace("\n", " ").strip()
        else:
            return text.replace("\n", " ").strip()
    if isinstance(data, dict):
        out = data.get("Rewritten") or data.get("rewritten") or ""
        if isinstance(out, str) and out.strip():
            return out.strip().replace("\n", " ")
    return text.replace("\n", " ").strip()


def rewrite_edit_prompt(
    prompt: str,
    image: Any = None,
    *,
    token: str = "",
    enabled: bool = True,
    client_factory: Any = None,
) -> str:
    """Space DEFAULT_REWRITE_PROMPT via Qwen2.5-VL-72B. Missing token = typed prompt."""
    text = (prompt or "").strip()
    if not enabled:
        return text
    if not token:
        print("rewrite skip: no HF_TOKEN")
        return text
    if image is None:
        print("rewrite skip: no image")
        return text
    try:
        if client_factory is not None:
            client = client_factory(token)
        else:
            from huggingface_hub import InferenceClient

            client = InferenceClient(provider=REWRITE_PROVIDER, token=token)
        buf = io.BytesIO()
        rgb = image.convert("RGB") if hasattr(image, "convert") else image
        rgb.save(buf, format="PNG")
        b64 = base64.b64encode(buf.getvalue()).decode("ascii")
        user = REWRITE_USER_TEMPLATE.format(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=text,
        )
        resp = client.chat.completions.create(
            model=REWRITE_MODEL,
            messages=[
                {"role": "system", "content": REWRITE_ASSISTANT_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{b64}"},
                        },
                        {"type": "text", "text": user},
                    ],
                },
            ],
        )
        raw = resp.choices[0].message.content
        if isinstance(raw, list):
            raw = " ".join(
                str(part.get("text", part) if isinstance(part, dict) else part)
                for part in raw
            )
        out = parse_rewritten_prompt(str(raw or ""))
        return out or text
    except Exception as e:
        print("rewrite skip", str(e)[:200])
        return text


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


EDIT_VAE_AREA = 1024 * 1024


def clamp_edit_vae_area(
    pipe: Any = None,
    width: int = DEFAULT_WIDTH,
    height: int = DEFAULT_HEIGHT,
) -> int:
    """Keep official 1024² VAE encode. Canvas shrink drops face latents."""
    del width, height
    area = EDIT_VAE_AREA
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
    sequential: bool = False,
    torch_module: Any = None,
) -> str:
    """Space ENABLE_TENSOR_OFFLOADING = model_cpu_offload. Sequential is OOM fallback."""
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


def place_edit_pipe(
    pipe: Any,
    vram_gib: float,
    torch_module: Any = None,
) -> str:
    """A100 40/80: GPU resident. Under 35GiB: tensor offload like ZeroGPU."""
    mode = space_device_mode(vram_gib)
    if mode == "cuda":
        try:
            pipe.to("cuda")
            setattr(pipe, "_qwen_edit_offload", "cuda")
            return "cuda"
        except Exception as e:
            print("cuda place fail → model_cpu_offload", str(e)[:180])
    return force_edit_offload(pipe, sequential=False, torch_module=torch_module)


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
        current = getattr(pipe, "_qwen_edit_offload", None)
        if current == "sequential_cpu_offload":
            raise
        if current == "cuda":
            print("VRAM OOM → model_cpu_offload でもう一度")
            free_cuda(torch_module)
            force_edit_offload(pipe, sequential=False, torch_module=torch_module)
            return _call(images)
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
    height: int | None = DEFAULT_HEIGHT,
    width: int | None = DEFAULT_WIDTH,
    size_auto: bool = False,
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
        "guidance_scale": float(guidance),
    }
    if not size_auto:
        if height is not None:
            out["height"] = int(height)
        if width is not None:
            out["width"] = int(width)
    if (negative or "").strip() and float(true_cfg) > 1.0:
        out["negative_prompt"] = negative
    return out


def save_jpeg(image: Any, dest: str | Path, quality: int = 92) -> Path:
    path = Path(dest)
    path.parent.mkdir(parents=True, exist_ok=True)
    image.convert("RGB").save(path, "JPEG", quality=quality)
    return path
