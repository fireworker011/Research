"""Cut a source video down to the seconds one Ref2VA request can see.

``MiniMaxH3VideoReference.from_file`` keeps the soundtrack. The ref2va setup
then truncates those frames to the generated length, from the start of the
file. A long source has to be cut first, or a later range never reaches the
model. The cut is re-encoded so the first frame is the requested time, and
it is written off the Colab Drive mount.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path


def slice_argv(src: Path, start_s: float, end_s: float, dest: Path) -> list[str]:
    """ffmpeg argv. ``-ss`` is after ``-i`` so the cut is not the previous keyframe."""
    if float(end_s) <= float(start_s):
        raise ValueError("参照動画の範囲が無い")
    return [
        "ffmpeg",
        "-y",
        "-i",
        str(src),
        "-ss",
        f"{float(start_s):.3f}",
        "-to",
        f"{float(end_s):.3f}",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        str(dest),
    ]


def slice_dest(src: Path, start_s: float, end_s: float) -> Path:
    root = Path("/content/h3-ref") if Path("/content").is_dir() else Path(tempfile.gettempdir()) / "h3-ref"
    name = f"{src.stem}-{float(start_s):.3f}-{float(end_s):.3f}.mp4"
    return root / name


def ensure_reference_slice(
    src: Path,
    start_s: float | None,
    end_s: float | None,
) -> Path:
    """Return a local file that is only the requested range. No range returns ``src``."""
    src = Path(src)
    if start_s is None and end_s is None:
        return src
    if start_s is None or end_s is None:
        raise ValueError("--video-start と --video-end は両方要る")
    dest = slice_dest(src, start_s, end_s)
    dest.parent.mkdir(parents=True, exist_ok=True)
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        raise RuntimeError("ffmpeg が無い。元動画の範囲を切れない。")
    argv = slice_argv(src, start_s, end_s, dest)
    argv[0] = ffmpeg
    subprocess.check_call(argv)
    if not dest.is_file() or dest.stat().st_size <= 0:
        raise RuntimeError(f"参照の切り出しが空: {dest}")
    return dest
