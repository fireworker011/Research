"""Cut a source video down to the seconds one Ref2VA request can see.

``MiniMaxH3VideoReference.from_file`` keeps the soundtrack with the frames.
The ref2va setup then truncates those frames to the generated length, from
the start of the file. A long source has to be cut first, or a later range
never reaches the model. The cut is re-encoded at 24 fps, the generation
clock, so frame k of the reference and frame k of the target are the same
moment. Audio stays PCM in a ``.mov`` so an AAC prime does not move the sound
off the mouth. H3 makes ``17 * n + 5`` frames, so the generated length is
usually a little longer than the range. The reference then holds its last
frame with silence for that tail, so no mouth moves without sound. The file
is written off the Colab Drive mount.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

from h3_runner.official import FPS

# Below half a frame, there is no tail to hold.
_MIN_PAD_S = 0.5 / FPS


def slice_argv(
    src: Path,
    start_s: float,
    end_s: float,
    dest: Path,
    *,
    pad_s: float = 0.0,
    has_audio: bool = True,
) -> list[str]:
    """ffmpeg argv. ``trim`` picks the exact range, ``fps`` puts it on the 24 fps clock."""
    start = float(start_s)
    end = float(end_s)
    if end <= start:
        raise ValueError("参照動画の範囲が無い")
    span = end - start
    pad = float(pad_s) if float(pad_s) >= _MIN_PAD_S else 0.0
    video = f"[0:v]trim=start={start:.3f}:end={end:.3f},setpts=PTS-STARTPTS,fps={FPS}"
    if pad:
        video += f",tpad=stop_mode=clone:stop_duration={pad:.3f}"
    inputs = ["-i", str(src)]
    if has_audio:
        audio = f"[0:a]atrim=start={start:.3f}:end={end:.3f},asetpts=PTS-STARTPTS"
    else:
        inputs.extend(["-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo"])
        audio = f"[1:a]atrim=duration={span:.3f}"
    if pad:
        audio += f",apad=pad_dur={pad:.3f}"
    return [
        "ffmpeg",
        "-y",
        *inputs,
        "-filter_complex",
        f"{video}[v];{audio}[a]",
        "-map",
        "[v]",
        "-map",
        "[a]",
        "-t",
        f"{span + pad:.3f}",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "pcm_s16le",
        str(dest),
    ]


def slice_dest(src: Path, start_s: float, end_s: float, pad_s: float = 0.0) -> Path:
    root = Path("/content/h3-ref") if Path("/content").is_dir() else Path(tempfile.gettempdir()) / "h3-ref"
    name = f"{src.stem}-{float(start_s):.3f}-{float(end_s):.3f}"
    if float(pad_s) >= _MIN_PAD_S:
        name += f"-p{float(pad_s):.3f}"
    return root / f"{name}.mov"


def _has_audio(src: Path) -> bool:
    ffprobe = shutil.which("ffprobe")
    if ffprobe is None:
        return True
    try:
        text = subprocess.check_output(
            [ffprobe, "-v", "error", "-select_streams", "a", "-show_entries", "stream=codec_type", "-of", "csv=p=0", str(src)],
            text=True,
            stderr=subprocess.STDOUT,
            timeout=60,
        )
    except (OSError, subprocess.SubprocessError):
        return True
    return "audio" in text


def ensure_reference_slice(
    src: Path,
    start_s: float | None,
    end_s: float | None,
    *,
    pad_to_s: float | None = None,
) -> Path:
    """Return a local file that is only the requested range. No range returns ``src``.

    ``pad_to_s`` is the generated length. The range is held on its last frame,
    with silence, up to that length.
    """
    src = Path(src)
    if start_s is None and end_s is None:
        return src
    if start_s is None or end_s is None:
        raise ValueError("--video-start と --video-end は両方要る")
    span = float(end_s) - float(start_s)
    pad = max(0.0, float(pad_to_s) - span) if pad_to_s is not None else 0.0
    dest = slice_dest(src, start_s, end_s, pad)
    dest.parent.mkdir(parents=True, exist_ok=True)
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        raise RuntimeError("ffmpeg が無い。元動画の範囲を切れない。")
    argv = slice_argv(src, start_s, end_s, dest, pad_s=pad, has_audio=_has_audio(src))
    argv[0] = ffmpeg
    subprocess.check_call(argv)
    if not dest.is_file() or dest.stat().st_size <= 0:
        raise RuntimeError(f"参照の切り出しが空: {dest}")
    return dest
