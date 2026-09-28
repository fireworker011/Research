"""Trim H3 clips to the requested seconds and join them at 1080x1920.

H3's video VAE only emits ``17 * n + 5`` frames, so a 6 second request becomes
6.583 seconds and a 9 second request becomes 9.417 seconds. The delivery file
cuts each clip back to the seconds the prompt was written for, then scales to
1080x1920. The uncut files stay beside it.
"""

from __future__ import annotations

import subprocess
from pathlib import Path


def join_command(
    parts: list[tuple[Path, float]],
    out_path: Path,
    *,
    width: int = 1080,
    height: int = 1920,
) -> list[str]:
    if not parts:
        raise ValueError("concat needs at least one clip")
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
        "-c:a",
        "aac",
        "-ar",
        "32000",
        "-ac",
        "2",
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
