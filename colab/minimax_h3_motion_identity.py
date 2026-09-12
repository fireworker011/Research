"""MiniMax H3: copy motion from a reference video, identity from stills.

The Hailuo / MiniMax-H3 API treats a single image with no `role` as
`first_frame`, which silently switches the request to image-to-video (i2va).
i2va animates that still and cannot take motion from a reference clip. Mixing
`first_frame` with `reference_*` is also rejected.

This module always builds reference-to-video (r2va) payloads:

- images → role=reference_image  (appearance / identity)
- videos → role=reference_video  (motion / camera / timing only)
"""

from __future__ import annotations

import json
import math
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

MODEL = "MiniMax-H3"
DEFAULT_BASE_URL = "https://api.minimax.io"
ALLOWED_IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif"}
ALLOWED_VIDEO_EXT = {".mp4", ".mov"}
MIN_DURATION = 4
MAX_DURATION = 15
MIN_REF_VIDEO_SEC = 2.0
MAX_REF_VIDEO_SEC = 15.0
MIN_DIM = 256
MAX_DIM = 5760
MIN_ASPECT = 0.4
MAX_ASPECT = 2.5
MAX_IMAGE_BYTES = 30 * 1024 * 1024
MAX_VIDEO_BYTES = 50 * 1024 * 1024
I2VA_ROLES = frozenset({"first_frame", "last_frame"})
R2VA_IMAGE_ROLE = "reference_image"
R2VA_VIDEO_ROLE = "reference_video"
R2VA_AUDIO_ROLE = "reference_audio"

# Phrases the model must see so Video 1 does not overwrite Image 1 identity.
IDENTITY_MARKERS = (
    "appearance follows reference image",
    "ignore the person",
    "motion in reference video",
)


class PayloadError(ValueError):
    """Raised when a request would not run as motion+identity r2va."""


def choose_duration_from_video(video_seconds: float) -> int:
    """Map a reference-clip length onto H3's integer output duration (4–15s)."""
    if not math.isfinite(video_seconds) or video_seconds <= 0:
        raise PayloadError(f"invalid video duration: {video_seconds!r}")
    return max(MIN_DURATION, min(MAX_DURATION, int(round(video_seconds))))


def clamp_duration(seconds: int) -> int:
    if seconds < MIN_DURATION or seconds > MAX_DURATION:
        raise PayloadError(f"duration must be an integer in {MIN_DURATION}-{MAX_DURATION}, got {seconds}")
    return seconds


def build_motion_identity_prompt(
    n_images: int,
    extra_scene: str = "",
    n_videos: int = 1,
    *,
    keep_background_from_video: bool = False,
) -> str:
    """Build an English r2va prompt that splits identity and motion.

    MiniMax numbers references by type and order: Image 1, Image 2, Video 1.
    The official guide requires assigning each asset a job in natural language.
    """
    if n_images < 1:
        raise PayloadError("at least one identity image is required")
    if n_videos < 1:
        raise PayloadError("at least one motion video is required")
    if n_images > 9:
        raise PayloadError("MiniMax H3 accepts at most 9 reference images")
    if n_videos > 3:
        raise PayloadError("MiniMax H3 accepts at most 3 reference videos")

    image_labels = ", ".join(f"reference image {i}" for i in range(1, n_images + 1))
    picture_tags = ", ".join(f"<Picture {i}>" for i in range(1, n_images + 1))
    video_labels = ", ".join(f"reference video {i}" for i in range(1, n_videos + 1))
    video_tags = ", ".join(f"<Video {i}>" for i in range(1, n_videos + 1))

    bg_line = (
        f"Keep the environment, camera path, and staging of {video_labels}."
        if keep_background_from_video
        else (
            f"Use {video_labels} only for body motion, pose sequence, timing, and camera movement. "
            "Do not copy the original location unless the scene description below asks for it."
        )
    )

    extra = (extra_scene or "").strip()
    scene_block = extra if extra else "Keep the action readable; do not invent a different choreography."

    return f"""subject_definitions:
<Subject 1> is the person whose face, body, hairstyle, skin, and clothing come ONLY from {picture_tags} ({image_labels}).
<Subject 2> is the motion, pose sequence, timing, and camera movement taken from {video_tags} ({video_labels}). The person, face, body, clothing, and identity visible in {video_labels} must be discarded.

summary:
[reference generation] The target video shows <Subject 1> performing the exact motion of {video_tags}. Appearance is fully taken from {picture_tags}. Appearance from {video_tags} is not used.

retention_analysis:
<Subject 1> (appears throughout): fully_preserved - identity, face, body, hair, and clothing from {picture_tags} are retained.
{video_tags} (motion, camera, timing): attribute_transfer - only motion, camera path, and timing are transferred onto <Subject 1>. The original person in {video_labels} is not preserved.

The character's appearance follows {image_labels}. The character performs the exact motion in {video_labels}. Ignore the person, face, body, and clothing in {video_labels}; copy only movement, timing, and camera. {bg_line}

Scene: {scene_block}
""".strip()


def build_r2va_content(
    prompt: str,
    image_urls: Sequence[str],
    video_urls: Sequence[str],
    audio_urls: Sequence[str] | None = None,
) -> list[dict[str, Any]]:
    """Assemble a MiniMax H3 content[] array locked to r2va roles."""
    prompt = (prompt or "").strip()
    if not prompt:
        raise PayloadError("text prompt is required")
    if not image_urls:
        raise PayloadError("at least one reference_image URL is required")
    if not video_urls:
        raise PayloadError("at least one reference_video URL is required")
    if len(image_urls) > 9:
        raise PayloadError("at most 9 reference images")
    if len(video_urls) > 3:
        raise PayloadError("at most 3 reference videos")
    audio_urls = list(audio_urls or [])
    if len(audio_urls) > 3:
        raise PayloadError("at most 3 reference audios")
    if len(image_urls) + len(video_urls) + len(audio_urls) > 12:
        raise PayloadError("mixed reference files must total at most 12")

    content: list[dict[str, Any]] = [{"type": "text", "text": prompt}]
    for url in image_urls:
        content.append(
            {
                "type": "image_url",
                "image_url": {"url": _require_url(url, "image")},
                "role": R2VA_IMAGE_ROLE,
            }
        )
    for url in video_urls:
        content.append(
            {
                "type": "video_url",
                "video_url": {"url": _require_url(url, "video")},
                "role": R2VA_VIDEO_ROLE,
            }
        )
    for url in audio_urls:
        content.append(
            {
                "type": "audio_url",
                "audio_url": {"url": _require_url(url, "audio")},
                "role": R2VA_AUDIO_ROLE,
            }
        )
    assert_r2va_motion_identity(content)
    return content


def _require_url(url: str, kind: str) -> str:
    url = (url or "").strip()
    if not url:
        raise PayloadError(f"empty {kind} url")
    return url


def content_roles(content: Sequence[Mapping[str, Any]]) -> list[str | None]:
    return [item.get("role") for item in content if item.get("type") != "text"]


def assert_r2va_motion_identity(content: Sequence[Mapping[str, Any]]) -> None:
    """Fail fast if the payload would run as i2va or drop the identity/motion split."""
    if not content:
        raise PayloadError("empty content")

    texts = [item.get("text", "") for item in content if item.get("type") == "text"]
    if not any(str(t).strip() for t in texts):
        raise PayloadError("content must include a non-empty text item")

    image_roles = [
        item.get("role")
        for item in content
        if item.get("type") == "image_url"
    ]
    video_roles = [
        item.get("role")
        for item in content
        if item.get("type") == "video_url"
    ]
    all_roles = [item.get("role") for item in content if item.get("type") != "text"]

    if not image_roles:
        raise PayloadError("r2va motion+identity requires at least one image_url")
    if not video_roles:
        raise PayloadError("r2va motion+identity requires at least one video_url")

    if any(role in I2VA_ROLES for role in all_roles):
        raise PayloadError(
            "image-to-video and reference-to-video are mutually exclusive; "
            "do not send first_frame/last_frame with reference_image/reference_video"
        )

    if any(role is None or role == "" for role in image_roles):
        raise PayloadError(
            "image role is missing; MiniMax defaults a single image to first_frame (i2va), "
            "which cannot transfer motion from a reference video"
        )
    if any(role != R2VA_IMAGE_ROLE for role in image_roles):
        raise PayloadError(f"every image must use role={R2VA_IMAGE_ROLE}, got {image_roles}")
    if any(role != R2VA_VIDEO_ROLE for role in video_roles):
        raise PayloadError(f"every video must use role={R2VA_VIDEO_ROLE}, got {video_roles}")

    prompt = "\n".join(str(t) for t in texts).lower()
    if not any(marker in prompt for marker in IDENTITY_MARKERS):
        raise PayloadError(
            "prompt must assign jobs: appearance from reference image N, "
            "motion from reference video N, and ignore the person in the video"
        )


def build_generation_payload(
    content: Sequence[Mapping[str, Any]],
    *,
    duration: int,
    resolution: str = "768P",
    ratio: str = "adaptive",
    model: str = MODEL,
) -> dict[str, Any]:
    clamp_duration(duration)
    if resolution not in {"768P", "2K"}:
        raise PayloadError(f"resolution must be 768P or 2K, got {resolution}")
    assert_r2va_motion_identity(content)
    payload: dict[str, Any] = {
        "model": model,
        "content": list(content),
        "duration": duration,
        "resolution": resolution,
        "ratio": ratio,
    }
    return payload


def ensure_identity_lock_in_prompt(prompt: str, n_images: int) -> str:
    """If H3-Context-IR dropped the identity/motion split, prepend a hard lock."""
    prompt = (prompt or "").strip()
    if not prompt:
        raise PayloadError("IR prompt is empty")
    lowered = prompt.lower()
    if any(marker in lowered for marker in IDENTITY_MARKERS):
        return prompt
    lock = build_motion_identity_prompt(n_images)
    return f"{lock}\n\n{prompt}"


def ffprobe_json(path: str | Path) -> dict[str, Any]:
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-print_format",
        "json",
        "-show_format",
        "-show_streams",
        str(path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise PayloadError(f"ffprobe failed for {path}: {result.stderr.strip() or result.stdout.strip()}")
    return json.loads(result.stdout)


def video_stats(path: str | Path) -> dict[str, Any]:
    info = ffprobe_json(path)
    video_stream = next((s for s in info.get("streams", []) if s.get("codec_type") == "video"), None)
    if video_stream is None:
        raise PayloadError(f"no video stream in {path}")
    duration = float(info.get("format", {}).get("duration") or video_stream.get("duration") or 0)
    width = int(video_stream.get("width") or 0)
    height = int(video_stream.get("height") or 0)
    fps = _parse_fps(video_stream.get("avg_frame_rate") or video_stream.get("r_frame_rate"))
    codec = str(video_stream.get("codec_name") or "")
    size = int(info.get("format", {}).get("size") or Path(path).stat().st_size)
    return {
        "duration": duration,
        "width": width,
        "height": height,
        "fps": fps,
        "codec": codec,
        "size": size,
        "aspect": (width / height) if width and height else 0.0,
    }


def image_stats(path: str | Path) -> dict[str, Any]:
    from PIL import Image

    with Image.open(path) as im:
        width, height = im.size
    size = Path(path).stat().st_size
    return {
        "width": width,
        "height": height,
        "size": size,
        "aspect": (width / height) if width and height else 0.0,
    }


def _parse_fps(value: str | None) -> float:
    if not value or value == "0/0":
        return 0.0
    if "/" in value:
        num, den = value.split("/", 1)
        den_f = float(den)
        return float(num) / den_f if den_f else 0.0
    return float(value)


def needs_video_transcode(stats: Mapping[str, Any]) -> list[str]:
    reasons: list[str] = []
    duration = float(stats.get("duration") or 0)
    if duration < MIN_REF_VIDEO_SEC:
        reasons.append(f"duration {duration:.2f}s < {MIN_REF_VIDEO_SEC}s")
    if duration > MAX_REF_VIDEO_SEC:
        reasons.append(f"duration {duration:.2f}s > {MAX_REF_VIDEO_SEC}s")
    fps = float(stats.get("fps") or 0)
    if fps and (fps < 23.976 - 0.05 or fps > 60 + 0.05):
        reasons.append(f"fps {fps:.3f} outside 23.976-60")
    codec = str(stats.get("codec") or "")
    if codec and codec not in {"h264", "hevc", "h265"}:
        reasons.append(f"codec {codec} is not h264/hevc")
    width = int(stats.get("width") or 0)
    height = int(stats.get("height") or 0)
    if width < MIN_DIM or height < MIN_DIM or width > MAX_DIM or height > MAX_DIM:
        reasons.append(f"resolution {width}x{height} outside {MIN_DIM}-{MAX_DIM}")
    aspect = float(stats.get("aspect") or 0)
    if aspect and (aspect < MIN_ASPECT or aspect > MAX_ASPECT):
        reasons.append(f"aspect {aspect:.3f} outside {MIN_ASPECT}-{MAX_ASPECT}")
    size = int(stats.get("size") or 0)
    if size > MAX_VIDEO_BYTES:
        reasons.append(f"file {size} bytes > 50MB")
    return reasons


def prepare_motion_video(
    src: str | Path,
    dest: str | Path,
    *,
    ffmpeg_bin: str = "ffmpeg",
    strip_audio: bool = True,
) -> dict[str, Any]:
    """Normalize a motion clip to MiniMax H3 reference-video limits.

    Audio is stripped by default so the original performer's voice cannot
    leak identity into the output.
    """
    src = Path(src)
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    stats = video_stats(src)
    reasons = needs_video_transcode(stats)
    if strip_audio:
        reasons.append("strip audio (identity leak guard)")

    duration = float(stats["duration"])
    target_dur = min(MAX_REF_VIDEO_SEC, max(duration, MIN_REF_VIDEO_SEC))
    # If the clip is shorter than 2s, loop it until it clears the floor.
    loop_input: list[str] = []
    if duration < MIN_REF_VIDEO_SEC:
        loops = int(math.ceil(MIN_REF_VIDEO_SEC / max(duration, 0.01)))
        loop_input = ["-stream_loop", str(max(loops, 1))]

    vf = _fit_video_filter(int(stats["width"]), int(stats["height"]))
    cmd = [
        ffmpeg_bin,
        "-y",
        *loop_input,
        "-i",
        str(src),
        "-t",
        f"{target_dur:.3f}",
        "-vf",
        vf,
        "-r",
        "24",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        "-an" if strip_audio else "-c:a",
        *( [] if strip_audio else ["aac", "-b:a", "128k"] ),
        str(dest),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise PayloadError(f"ffmpeg failed: {result.stderr[-2000:]}")
    out_stats = video_stats(dest)
    out_stats["transcode_reasons"] = reasons
    out_stats["path"] = str(dest)
    if out_stats["duration"] < MIN_REF_VIDEO_SEC - 0.05:
        raise PayloadError(
            f"prepared video is still too short ({out_stats['duration']:.2f}s); "
            "use a 2-15s motion clip"
        )
    return out_stats


def _even(n: int) -> int:
    return n if n % 2 == 0 else n + 1


def target_video_canvas(width: int, height: int) -> tuple[int, int]:
    """Compute an even WxH that satisfies H3 min/max and aspect limits."""
    if width < 1 or height < 1:
        raise PayloadError(f"invalid video size {width}x{height}")
    w, h = float(width), float(height)
    # Cap the long edge.
    long_edge = max(w, h)
    if long_edge > MAX_DIM:
        scale = MAX_DIM / long_edge
        w, h = w * scale, h * scale
    # Lift the short edge.
    short_edge = min(w, h)
    if short_edge < MIN_DIM:
        scale = MIN_DIM / short_edge
        w, h = w * scale, h * scale
        if max(w, h) > MAX_DIM:
            # After lifting, cap again and accept letterboxing later.
            scale = MAX_DIM / max(w, h)
            w, h = w * scale, h * scale
    aspect = w / h
    if aspect < MIN_ASPECT:
        w = h * MIN_ASPECT
    elif aspect > MAX_ASPECT:
        h = w / MAX_ASPECT
    tw, th = _even(int(round(w))), _even(int(round(h)))
    tw = min(max(tw, MIN_DIM), MAX_DIM)
    th = min(max(th, MIN_DIM), MAX_DIM)
    tw, th = _even(tw), _even(th)
    if tw / th < MIN_ASPECT:
        tw = _even(int(math.ceil(th * MIN_ASPECT)))
    if tw / th > MAX_ASPECT:
        th = _even(int(math.ceil(tw / MAX_ASPECT)))
    return tw, th


def _fit_video_filter(width: int, height: int) -> str:
    """Scale to fit, then pad onto a legal H3 canvas without stretching."""
    tw, th = target_video_canvas(width, height)
    return (
        f"scale={tw}:{th}:force_original_aspect_ratio=decrease,"
        f"pad={tw}:{th}:(ow-iw)/2:(oh-ih)/2"
    )


def prepare_identity_image(src: str | Path, dest: str | Path) -> dict[str, Any]:
    from PIL import Image

    src = Path(src)
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(src) as im:
        im = im.convert("RGB")
        width, height = im.size
        if min(width, height) < MIN_DIM:
            scale = MIN_DIM / float(min(width, height))
            im = im.resize((int(width * scale), int(height * scale)), Image.Resampling.LANCZOS)
            width, height = im.size
        if max(width, height) > MAX_DIM:
            scale = MAX_DIM / float(max(width, height))
            im = im.resize((int(width * scale), int(height * scale)), Image.Resampling.LANCZOS)
            width, height = im.size
        aspect = width / height
        if aspect < MIN_ASPECT or aspect > MAX_ASPECT:
            # letterbox onto a legal canvas instead of cropping the face
            target_aspect = min(max(aspect, MIN_ASPECT), MAX_ASPECT)
            if aspect < target_aspect:
                new_w = int(round(height * target_aspect))
                new_h = height
            else:
                new_w = width
                new_h = int(round(width / target_aspect))
            canvas = Image.new("RGB", (new_w, new_h), (0, 0, 0))
            canvas.paste(im, ((new_w - width) // 2, (new_h - height) // 2))
            im = canvas
        dest_path = dest.with_suffix(".jpg")
        im.save(dest_path, format="JPEG", quality=92, optimize=True)
        width, height = im.size
    size = dest_path.stat().st_size
    if size > MAX_IMAGE_BYTES:
        raise PayloadError(f"prepared image still exceeds 30MB: {dest_path}")
    return {
        "path": str(dest_path),
        "width": width,
        "height": height,
        "size": size,
        "aspect": width / height if height else 0.0,
    }


def warn_framing_mismatch(image: Mapping[str, Any], video: Mapping[str, Any]) -> str | None:
    """Identity lock is much weaker when the still is a face crop and the clip is full-body."""
    ia = float(image.get("aspect") or 0)
    va = float(video.get("aspect") or 0)
    if not ia or not va:
        return None
    if (ia > 1.2 and va < 0.8) or (ia < 0.8 and va > 1.2):
        return (
            "Identity image orientation does not match the motion clip. "
            "Use a still with the same framing (full body if the clip is full body)."
        )
    return None


def mm_file_url(file_id: int | str) -> str:
    return f"mm_file://{file_id}"


def parse_upload_file_id(response_json: Mapping[str, Any]) -> str:
    file_obj = response_json.get("file") or {}
    file_id = file_obj.get("file_id")
    if file_id is None:
        raise PayloadError(f"upload response missing file_id: {response_json}")
    base = response_json.get("base_resp") or {}
    if base.get("status_code") not in (0, None):
        raise PayloadError(f"upload failed: {base}")
    return str(file_id)


def summarize_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    content = payload.get("content") or []
    return {
        "model": payload.get("model"),
        "duration": payload.get("duration"),
        "resolution": payload.get("resolution"),
        "ratio": payload.get("ratio"),
        "roles": content_roles(content),
        "n_images": sum(1 for c in content if c.get("type") == "image_url"),
        "n_videos": sum(1 for c in content if c.get("type") == "video_url"),
        "n_audios": sum(1 for c in content if c.get("type") == "audio_url"),
        "mode": "r2va",
    }


_SECRET_RE = re.compile(r"(Bearer\s+)(\S+)", re.I)


def redact(value: str) -> str:
    return _SECRET_RE.sub(r"\1***", value)


def which_ffmpeg() -> str:
    path = shutil.which("ffmpeg")
    if not path:
        raise PayloadError("ffmpeg is not installed")
    return path


def env_api_key() -> str:
    key = (os.environ.get("MINIMAX_API_KEY") or "").strip()
    if not key:
        raise PayloadError("MINIMAX_API_KEY is not set")
    return key


def iter_identity_paths(paths: Iterable[str | Path]) -> list[Path]:
    out: list[Path] = []
    for raw in paths:
        p = Path(raw)
        if p.suffix.lower() not in ALLOWED_IMAGE_EXT:
            raise PayloadError(f"unsupported identity image type: {p}")
        out.append(p)
    if not out:
        raise PayloadError("no identity images")
    return out
