"""Trim H3 clips to the requested seconds and join them at 1080x1920.

H3's video VAE only emits ``17 * n + 5`` frames, so a 6 second request becomes
6.583 seconds and a 9 second request becomes 9.417 seconds. The delivery file
cuts each clip back to the seconds the prompt was written for, then scales to
1080x1920. The uncut files stay beside it.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

# A finished H3 clip is many megabytes. Smaller than this is not a resume point.
MIN_CLIP_BYTES = 1_000_000


def probe_text_is_done(text: str, min_seconds: float | None) -> bool:
    if "codec_type=video" not in text:
        return False
    if min_seconds is None:
        return True
    duration = None
    for line in text.splitlines():
        if line.startswith("duration="):
            try:
                duration = float(line.split("=", 1)[1])
            except ValueError:
                return False
    if duration is None:
        return False
    return duration + 0.05 >= min_seconds


def clip_is_done(path: Path, *, min_seconds: float | None = None) -> bool:
    """True when Drive already has a clip worth resuming from."""
    if not path.is_file() or path.stat().st_size < MIN_CLIP_BYTES:
        return False
    probe = shutil.which("ffprobe")
    if probe is None:
        return True
    try:
        text = subprocess.check_output(
            [
                probe,
                "-v",
                "error",
                "-show_entries",
                "format=duration:stream=codec_type",
                "-of",
                "default=nw=1",
                str(path),
            ],
            text=True,
            stderr=subprocess.STDOUT,
            timeout=60,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return probe_text_is_done(text, min_seconds)


def join_command(
    parts: list[tuple[Path, float]],
    out_path: Path,
    *,
    width: int = 1080,
    height: int = 1920,
    audio: str = "aac",
) -> list[str]:
    """``audio="pcm"`` writes a master with PCM sound. The mp4 is made from it once, later."""
    if not parts:
        raise ValueError("concat needs at least one clip")
    if audio == "aac":
        sound = ["-c:a", "aac", "-ar", "32000", "-ac", "2"]
    elif audio == "pcm":
        sound = ["-c:a", "pcm_s16le", "-ac", "2"]
    else:
        raise ValueError(f"audio must be aac or pcm, got {audio!r}")
    inputs: list[str] = []
    filters: list[str] = []
    for index, (path, seconds) in enumerate(parts):
        if seconds <= 0:
            raise ValueError(f"trim seconds must be positive, got {seconds}")
        inputs.extend(["-i", str(path)])
        filters.append(
            f"[{index}:v]trim=duration={seconds:.3f},setpts=PTS-STARTPTS,"
            f"scale={width}:{height}:flags=lanczos,setsar=1[v{index}]"
        )
        filters.append(
            f"[{index}:a]atrim=duration={seconds:.3f},asetpts=PTS-STARTPTS[a{index}]"
        )
    count = len(parts)
    # concat wants each segment's video pad, then that segment's audio pad.
    paired = "".join(f"[v{index}][a{index}]" for index in range(count))
    filters.append(f"{paired}concat=n={count}:v=1:a=1[v][a]")
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
        *sound,
        str(out_path),
    ]


def join_clips(
    parts: list[tuple[Path, float]],
    out_path: Path,
    *,
    width: int = 1080,
    height: int = 1920,
) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    command = join_command(parts, out_path, width=width, height=height)
    completed = subprocess.run(command, check=False, capture_output=True, text=True)
    if completed.returncode != 0:
        tail = (completed.stderr or "")[-2000:]
        raise RuntimeError(f"ffmpeg failed ({completed.returncode}): {tail}")
    return out_path
