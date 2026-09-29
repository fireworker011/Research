"""MiniMax-H3 request fields and the frame/canvas arithmetic the official code uses.

Transcribed from code that was read, not from a guessed API.

Request JSON
  MiniMax-AI/MiniMax-H3 ``d21241f`` ``scripts/readme/reproducible-768p-*.sh``
  plus the image ``conditions`` entry in the SGLang cookbook the README points at
  (https://docs.sglang.io/cookbook/diffusion/MiniMax/MiniMax-H3):
  ``type`` / ``uri`` / ``role: reference``.

Canvas and frames
  huggingface/diffusers ``modular_pipelines/minimax_h3/modular_pipeline.py``
  (``resolve_canvas_size``, ``align_num_frames``, ``video_latent_num_frames``,
  ``min_duration=5``, ``max_duration=15``, fps 24, canvas multiple 32,
  short edge 768, max pixels ``768 * 1344``).

Duration check
  ``before_encoder.py`` rejects the aligned duration when it is outside
  ``[5, 15]``. The comment there says 346 frames would round up to 362,
  which is 15.083 seconds, and that does not pass.
"""

from __future__ import annotations

FPS = 24
MIN_DURATION_S = 5.0
MAX_DURATION_S = 15.0
CANVAS_MULTIPLE = 32
CANVAS_SHORT_EDGE = 768
CANVAS_MAX_PIXELS = 768 * 1344
MIN_ASPECT_RATIO = 1 / 4
MAX_ASPECT_RATIO = 4
FRAMES_PER_CHUNK = 17
LATENTS_PER_CHUNK = 5
MODEL_ID = "MiniMaxAI/MiniMax-H3"
# Checkpoint scheduler_config.json values. Diffusers loads these itself.
VIDEO_FLOW_SHIFT = 12.0
AUDIO_FLOW_SHIFT = 3.0
# diffusers InputParam template default for num_inference_steps.
DEFAULT_STEPS = 50

# README.ja.md lists 4–15 seconds. The diffusers pipeline that the same README
# names for local runs enforces 5–15 on the aligned frame count.
README_MIN_DURATION_S = 4.0
README_MAX_DURATION_S = 15.0


def parse_aspect(aspect: str) -> tuple[float, float]:
    raw = (aspect or "").strip().replace("：", ":")
    if ":" not in raw:
        raise ValueError(f"aspect must look like 9:16, got {aspect!r}")
    left, right = raw.split(":", 1)
    width = float(left)
    height = float(right)
    if width <= 0 or height <= 0:
        raise ValueError(f"aspect must be positive, got {aspect!r}")
    return width, height


def resolve_canvas_size(
    aspect_width: float,
    aspect_height: float,
    canvas_multiple: int = CANVAS_MULTIPLE,
    short_edge: int = CANVAS_SHORT_EDGE,
    max_pixels: int = CANVAS_MAX_PIXELS,
    min_aspect_ratio: float = MIN_ASPECT_RATIO,
    max_aspect_ratio: float = MAX_ASPECT_RATIO,
) -> tuple[int, int]:
    """Return ``(height, width)``. Same rounding as diffusers ``resolve_canvas_size``."""
    if aspect_width <= 0 or aspect_height <= 0:
        raise ValueError(f"The aspect ratio must be positive, got {aspect_width}:{aspect_height}.")
    ratio = aspect_width / aspect_height
    if not min_aspect_ratio <= ratio <= max_aspect_ratio:
        raise ValueError(
            f"MiniMax-H3 supports aspect ratios from 1:{1 / min_aspect_ratio:g} to "
            f"{max_aspect_ratio:g}:1, got {aspect_width}:{aspect_height} ({ratio:g})."
        )
    if ratio >= 1.0:
        width, height = short_edge * ratio, float(short_edge)
    else:
        width, height = float(short_edge), short_edge / ratio
    area = width * height
    if area > max_pixels:
        scale = (max_pixels / area) ** 0.5
        width, height = width * scale, height * scale
    multiple = canvas_multiple
    return (
        max(multiple, round(height / multiple) * multiple),
        max(multiple, round(width / multiple) * multiple),
    )


def align_num_frames(
    num_frames: int,
    frames_per_chunk: int = FRAMES_PER_CHUNK,
    latents_per_chunk: int = LATENTS_PER_CHUNK,
) -> int:
    """Snap up to the next ``17 * n + 5`` the video VAE can encode."""
    if num_frames < 1:
        raise ValueError(f"`num_frames` must be positive, got {num_frames}.")
    frames = int(num_frames)
    while frames % frames_per_chunk != latents_per_chunk:
        frames += 1
    return frames


def video_latent_num_frames(
    num_frames: int,
    frames_per_chunk: int = FRAMES_PER_CHUNK,
    latents_per_chunk: int = LATENTS_PER_CHUNK,
) -> int:
    if num_frames % frames_per_chunk != latents_per_chunk:
        raise ValueError(
            f"`num_frames` must be of the form {frames_per_chunk} * n + {latents_per_chunk}, got {num_frames}."
        )
    return (num_frames - latents_per_chunk) // frames_per_chunk * latents_per_chunk + 2


def frames_for_seconds(duration_s: float) -> int:
    """``round(seconds * 24)``, the same conversion diffusers documents for audio-derived length."""
    return int(round(float(duration_s) * FPS))


def aligned_duration_s(num_frames: int) -> float:
    return align_num_frames(num_frames) / FPS


def diffusers_accepts(num_frames: int) -> bool:
    """True when the aligned duration is inside the check in ``before_encoder.py``."""
    return MIN_DURATION_S <= aligned_duration_s(num_frames) <= MAX_DURATION_S


def largest_legal_frames(max_frames: int) -> int | None:
    """Largest ``17 * n + 5`` at or below ``max_frames`` that diffusers accepts."""
    frames = int(max_frames)
    while frames >= int(MIN_DURATION_S * FPS):
        if frames % FRAMES_PER_CHUNK == LATENTS_PER_CHUNK and diffusers_accepts(frames):
            return frames
        frames -= 1
    return None


def spatial_tokens(height: int, width: int) -> int:
    """Effective 32× spatial downsample: VAE 16× then patch 2×2."""
    if height % CANVAS_MULTIPLE or width % CANVAS_MULTIPLE:
        raise ValueError(f"canvas must be a multiple of {CANVAS_MULTIPLE}, got {width}x{height}")
    return (height // CANVAS_MULTIPLE) * (width // CANVAS_MULTIPLE)


def build_video_request(
    *,
    task: str,
    prompt: str,
    duration_s: float,
    aspect_ratio: str,
    short_edge: int,
    seed: int,
    steps: int = DEFAULT_STEPS,
    image_uri: str | None = None,
) -> dict:
    """Official ``/v1/videos`` body. Image Ref2VA uses one reference condition and no video."""
    if task not in ("t2va", "ref2va"):
        raise ValueError(f"task must be t2va or ref2va, got {task!r}")
    text = (prompt or "").strip()
    if not text:
        raise ValueError("prompt is empty")
    if task == "ref2va":
        if not image_uri:
            raise ValueError("ref2va needs one image uri")
        conditions = [{"type": "image", "uri": image_uri, "role": "reference"}]
    else:
        if image_uri:
            raise ValueError("t2va takes no reference image")
        conditions = []
    if not README_MIN_DURATION_S <= float(duration_s) <= README_MAX_DURATION_S:
        raise ValueError(
            f"duration_seconds must be {README_MIN_DURATION_S:g}–{README_MAX_DURATION_S:g}, got {duration_s}"
        )
    parse_aspect(aspect_ratio)
    return {
        "model": MODEL_ID,
        "task": task,
        "prompt": text,
        "conditions": conditions,
        "target": {
            "short_edge": int(short_edge),
            "aspect_ratio": aspect_ratio,
            "duration_seconds": float(duration_s),
        },
        "num_outputs_per_prompt": 1,
        "num_inference_steps": int(steps),
        "flow_shift": VIDEO_FLOW_SHIFT,
        "audio_flow_shift": AUDIO_FLOW_SHIFT,
        "seed": int(seed),
    }
