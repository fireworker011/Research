"""MiniMax H3 image-to-video with a free prompt (phone Colab).

Same FL2VA unet + turbo LoRA as the T2V phone notebook, but one still is wired
as first_frame (I2VA). Unlike h3_motion_graphics this is not locked to the
coconala ad copy: the prompt is free text. Canvas follows the still (auto) or
9:16 / 16:9 like T2V, plus the 8:9 canvas used by the I2VA homage.

Affiliate URLs never go in prompts. Prompts that describe minors are refused.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from h3_motion_graphics import (
    CANVAS_8_9,
    FORBIDDEN_IN_PROMPT,
    I2VA_HEADER,
    build_i2va_graph,
    fl2va_header,
    i2va_retry_plans,
    underage_prompt_errors,
)
from h3_t2v import CANVAS_16_9, CANVAS_9_16, is_16_9, is_9_16

REPO = "fireworker011/Research"
BRANCH = "cursor/minimax-h3-motion-identity-e959"
NOTEBOOK = "minimax_h3_i2v_free_phone.ipynb"
# Cell 2 probes these in order for colab/h3_i2v_free.py and then pulls every
# helper from the first branch that has it, so the helper set stays coherent.
HELPER_BRANCHES = (BRANCH, "cursor/h3-i2v-free-phone-22ce")
HELPER_FILES = (
    "colab/h3_r2v_core.py",
    "colab/h3_motion_graphics.py",
    "colab/h3_i2v_phone.py",
    "colab/h3_t2v.py",
    "colab/h3_civitai.py",
    "colab/h3_i2v_free.py",
)

DURATION_S = 10.0
ASPECT_AUTO = "auto"
ASPECT_CHOICES = (ASPECT_AUTO, "9:16", "16:9", "8:9")
CANVASES = {"9:16": CANVAS_9_16, "16:9": CANVAS_16_9, "8:9": CANVAS_8_9}

DEFAULT_I2V_PROMPT = (
    I2VA_HEADER + "\n\n"
    "Live-action cinematic photorealism, no anime, no illustration. "
    "Keep the exact same person, outfit, and setting as <Picture 1>. "
    "The camera holds, then adds slow 2.5D parallax. The subject blinks, "
    "the gaze shifts slightly, hair and fabric sway in a soft breeze. "
    "Identity, face, and colors stay locked. No on-screen text, no logos, no URL.\n\n"
    "overall_soundscape: Quiet room tone, soft fabric rustle.\n\n"
    "non_diegetic_music: Sparse warm piano, short hold at the end.\n"
)

DEFAULT_I2V_PROMPT_16_9 = (
    I2VA_HEADER + "\n\n"
    "Horizontal 16:9 live-action cinematic photorealism, no anime, no illustration. "
    "Keep the exact same person, outfit, and setting as <Picture 1>. "
    "Wide cinematic frame; the camera holds, then adds a slow push-in. "
    "The subject blinks, the gaze shifts slightly, hair and fabric sway. "
    "Identity, face, and colors stay locked. No on-screen text, no logos, no URL.\n\n"
    "overall_soundscape: Quiet room tone, soft fabric rustle.\n\n"
    "non_diegetic_music: Sparse warm piano, short hold at the end.\n"
)


def canvas_from_image_size(width: int, height: int) -> tuple[int, int]:
    """Pick the H3 canvas whose aspect is closest to the still (portrait → 9:16,
    landscape → 16:9, near-square → 8:9)."""
    w, h = int(width), int(height)
    if w <= 0 or h <= 0:
        return CANVAS_9_16
    ratio = w / h
    return min(CANVASES.values(), key=lambda c: abs(ratio - c[0] / c[1]))


def canvas_for_aspect(aspect: str | None, *, image_size: tuple[int, int] | None = None) -> tuple[int, int]:
    raw = (aspect or ASPECT_AUTO).strip().lower().replace("：", ":").replace("/", ":")
    if raw in ("", ASPECT_AUTO, "image", "画像", "same"):
        return canvas_from_image_size(*image_size) if image_size else CANVAS_9_16
    if raw in ("9:16", "portrait", "shorts"):
        return CANVAS_9_16
    if raw in ("16:9", "landscape", "wide"):
        return CANVAS_16_9
    if raw in ("8:9", "square", "squareish"):
        return CANVAS_8_9
    raise ValueError(f"I2V aspect must be auto, 9:16, 16:9 or 8:9, got {aspect!r}")


def i2v_canvas_ok(width: int, height: int) -> bool:
    w, h = int(width), int(height)
    return w >= 32 and h >= 32 and w % 32 == 0 and h % 32 == 0


def resolve_i2v_prompt(
    prompt: str | None,
    *,
    landscape: bool = False,
    with_last_frame: bool = False,
    duration_s: float = DURATION_S,
) -> str:
    """Free text wins. Empty → neutral default. The Picture 1 (and Picture 2)
    alignment header is prepended when the text does not reference it, so the
    still is always declared as the 0.00s frame."""
    text = (prompt or "").strip()
    if not text:
        text = DEFAULT_I2V_PROMPT_16_9 if landscape else DEFAULT_I2V_PROMPT
    if with_last_frame:
        if "Picture 2" not in text:
            if text.startswith(I2VA_HEADER):
                text = text[len(I2VA_HEADER):].lstrip()
            text = fl2va_header(duration_s) + "\n\n" + text
    elif "Picture 1" not in text:
        text = I2VA_HEADER + "\n\n" + text
    return text


def validate_i2v_prompt(prompt: str, *, with_last_frame: bool = False) -> list[str]:
    errs: list[str] = []
    p = (prompt or "").strip()
    if not p:
        return ["I2V prompt is empty"]
    low = p.lower()
    for bad in FORBIDDEN_IN_PROMPT:
        if bad.lower() in low:
            errs.append(f"forbidden string in prompt: {bad}")
    errs.extend(underage_prompt_errors(p))
    if "Picture 1" not in p:
        errs.append("Picture 1 reference missing (first frame lock)")
    if with_last_frame and "Picture 2" not in p:
        errs.append("Picture 2 reference missing (last frame lock)")
    return errs


def i2v_retry_plans(*, width: int, height: int) -> list[dict[str, Any]]:
    """Same-aspect smaller canvases after OOM. Never drops first_frame."""
    return i2va_retry_plans(width=width, height=height)


def build_i2v_graph(
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
) -> dict[str, Any]:
    """MiniMaxH3ImageToVideo with first_frame wired; last_frame optional."""
    return build_i2va_graph(
        first_image=first_image,
        last_image=last_image,
        prompt=prompt,
        unet=unet,
        lora_name=lora_name,
        lora_strength=lora_strength,
        width=width,
        height=height,
        duration_s=duration_s,
        seed=seed,
        steps=steps,
        filename_prefix=filename_prefix,
        has_lora_loader=has_lora_loader,
        has_audio_decode=has_audio_decode,
    )


def assert_i2v_graph(g: dict[str, Any], *, expect_last: bool) -> list[str]:
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
        errs.append("I2V without LAST_IMAGE must not wire last_frame")
    if any(n.get("class_type") == "MiniMaxH3ReferenceToVideo" for n in g.values()):
        errs.append("R2V node must not be in the I2V graph")
    if not any(n.get("class_type") == "LoadImage" for n in g.values()):
        errs.append("I2V must load the still")
    w, h = int(inn.get("width") or 0), int(inn.get("height") or 0)
    if not i2v_canvas_ok(w, h):
        errs.append("canvas must be multiples of 32")
    errs.extend(validate_i2v_prompt(str(inn.get("prompt") or ""), with_last_frame=expect_last))
    return errs


def aspect_label(width: int, height: int) -> str:
    w, h = int(width), int(height)
    if is_9_16(w, h):
        return "9:16"
    if is_16_9(w, h):
        return "16:9"
    if h > 0 and abs(w / h - 8 / 9) <= 0.03:
        return "8:9"
    return f"{w}x{h}"


def i2v_free_colab_url(*, repo: str = REPO, branch: str = BRANCH, path: str = NOTEBOOK) -> str:
    return f"https://colab.research.google.com/github/{repo}/blob/{branch}/{path}"


def helper_raw_url(rel: str, *, repo: str = REPO, branch: str = BRANCH) -> str:
    rel = str(rel).lstrip("/")
    return f"https://raw.githubusercontent.com/{repo}/{branch}/{rel}"


def helper_names() -> list[str]:
    return [Path(rel).name for rel in HELPER_FILES]
