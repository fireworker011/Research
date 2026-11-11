"""Edit the 60-second MV trailer.

The supplied key visual is the final title card, full frame, uncropped.
Scenes before it are stills with a slow move, cut to the score.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

FPS = 25
WIDTH = 1920
HEIGHT = 1080

ROOT = Path(__file__).resolve().parent
BUILD = ROOT / "build"
STILLS = ROOT / "stills"
FONT = ROOT / "fonts" / "ZenOldMincho-Medium.ttf"
POSTER_SRC = Path(
    "/home/ubuntu/.cursor/projects/agent-repos-Research/assets/"
    "3FC89080-EEE4-425A-97E7-DFAC6DE6DC15_L0_001.jpg"
)
STILL_SRC = Path("/opt/cursor/artifacts/assets")
LINE = "愛していたのに、"


def run(cmd: list[str]) -> None:
    print(" ".join(cmd[:8]), "...")
    subprocess.run(cmd, check=True)


def prepare() -> Path:
    BUILD.mkdir(parents=True, exist_ok=True)
    STILLS.mkdir(parents=True, exist_ok=True)
    FONT.parent.mkdir(parents=True, exist_ok=True)
    font_src = Path("/tmp/fonts/ZenOldMincho-Medium.ttf")
    if not FONT.exists() and font_src.exists():
        shutil.copy(font_src, FONT)
    if not FONT.exists():
        raise SystemExit(f"missing font: {FONT}")
    poster = STILLS / "title.jpg"
    if POSTER_SRC.exists():
        shutil.copy(POSTER_SRC, poster)
    if not poster.exists():
        raise SystemExit(f"missing title card: {poster}")
    for name in (
        "shot-tear",
        "shot-wife",
        "shot-phone",
        "shot-hallway",
        "shot-doorway",
        "shot-her",
        "shot-him",
        "shot-choice",
        "shot-window",
    ):
        dest = STILLS / f"{name}.jpg"
        src = STILL_SRC / f"{name}.jpg"
        if src.exists():
            shutil.copy(src, dest)
        if not dest.exists():
            raise SystemExit(f"missing still: {dest}")
    line = BUILD / "line.txt"
    line.write_text(LINE, encoding="utf-8")
    return poster


def black(frames: int, dest: Path) -> None:
    run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"color=c=black:s={WIDTH}x{HEIGHT}:r={FPS}",
            "-frames:v",
            str(frames),
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "16",
            "-pix_fmt",
            "yuv420p",
            "-an",
            str(dest),
        ]
    )


def scene(
    src: Path,
    dest: Path,
    frames: int,
    z0: float,
    z1: float,
    cx: float,
    cy: float,
    fade_in: float = 0.0,
    fade_out: float = 0.0,
    supers: bool = False,
) -> None:
    z = f"{z0}+({z1 - z0})*on/{max(frames - 1, 1)}"
    move = (
        f"scale={WIDTH * 2}:{HEIGHT * 2}:force_original_aspect_ratio=increase:flags=lanczos,"
        f"crop={WIDTH * 2}:{HEIGHT * 2},"
        "eq=saturation=0.86:contrast=1.05:brightness=-0.015,"
        f"zoompan=z='{z}':x='(iw-iw/zoom)*{cx}':y='(ih-ih/zoom)*{cy}':"
        f"d={frames}:s={WIDTH}x{HEIGHT}:fps={FPS},"
        "unsharp=5:5:0.28:5:5:0.0,setsar=1,format=yuv420p"
    )
    if fade_in:
        move += f",fade=t=in:st=0:d={fade_in}"
    if fade_out:
        start = max(0.0, frames / FPS - fade_out)
        move += f",fade=t=out:st={start}:d={fade_out}"
    if supers:
        alpha = (
            "if(lt(t\\,0.7)\\,0\\,"
            "if(lt(t\\,1.4)\\,(t-0.7)/0.7\\,"
            "if(lt(t\\,4.3)\\,1\\,"
            "if(lt(t\\,5.0)\\,(5.0-t)/0.7\\,0))))"
        )
        move += (
            f",drawtext=fontfile={FONT}:textfile={BUILD / 'line.txt'}:"
            "fontsize=58:fontcolor=white:borderw=1:bordercolor=black@0.45:"
            "shadowcolor=black@0.55:shadowx=0:shadowy=2:"
            "x=(w-text_w)/2:y=h-168:"
            f"alpha='{alpha}'"
        )
    run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(src),
            "-vf",
            move,
            "-frames:v",
            str(frames),
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "16",
            "-pix_fmt",
            "yuv420p",
            "-an",
            str(dest),
        ]
    )


def title_card(src: Path, dest: Path, frames: int) -> None:
    # Native poster is 1792x1008. Scale to the master without cropping type.
    run(
        [
            "ffmpeg",
            "-y",
            "-loop",
            "1",
            "-i",
            str(src),
            "-vf",
            (
                f"scale={WIDTH}:{HEIGHT}:flags=lanczos,setsar=1,format=yuv420p,"
                "fade=t=in:st=0:d=0.45"
            ),
            "-frames:v",
            str(frames),
            "-r",
            str(FPS),
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "14",
            "-pix_fmt",
            "yuv420p",
            "-an",
            str(dest),
        ]
    )


def assemble(clips: list[Path], score: Path, dest: Path) -> None:
    concat = BUILD / "concat.txt"
    lines = []
    for clip in clips:
        lines.append(f"file '{clip.resolve()}'")
    concat.write_text("\n".join(lines) + "\n", encoding="utf-8")
    silent = BUILD / "picture.mp4"
    run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat),
            "-c",
            "copy",
            str(silent),
        ]
    )
    run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(silent),
            "-i",
            str(score),
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-t",
            "60",
            "-movflags",
            "+faststart",
            "-metadata",
            "title=寝取られた妻",
            str(dest),
        ]
    )


def main() -> None:
    poster = prepare()
    shots: list[tuple] = [
        ("01-black", None, 50, None),
        ("02-tear", STILLS / "shot-tear.jpg", 140, (1.00, 1.07, 0.40, 0.46, 0.22, 0.0, True)),
        ("03-wife", STILLS / "shot-wife.jpg", 135, (1.00, 1.06, 0.34, 0.42, 0.0, 0.0, False)),
        ("04-phone", STILLS / "shot-phone.jpg", 105, (1.00, 1.08, 0.50, 0.58, 0.0, 0.0, False)),
        ("05-hallway", STILLS / "shot-hallway.jpg", 125, (1.00, 1.07, 0.58, 0.46, 0.0, 0.0, False)),
        ("06-doorway", STILLS / "shot-doorway.jpg", 150, (1.02, 1.08, 0.52, 0.42, 0.0, 0.0, False)),
        ("07-her", STILLS / "shot-her.jpg", 125, (1.00, 1.06, 0.36, 0.50, 0.0, 0.0, False)),
        ("08-him", STILLS / "shot-him.jpg", 110, (1.00, 1.07, 0.56, 0.44, 0.0, 0.0, False)),
        ("09-choice", STILLS / "shot-choice.jpg", 140, (1.01, 1.06, 0.40, 0.42, 0.0, 0.0, False)),
        ("10-flash-tear", STILLS / "shot-tear.jpg", 25, (1.06, 1.12, 0.38, 0.42, 0.0, 0.0, False)),
        ("11-flash-him", STILLS / "shot-him.jpg", 25, (1.05, 1.12, 0.55, 0.42, 0.0, 0.0, False)),
        ("12-flash-her", STILLS / "shot-her.jpg", 25, (1.04, 1.11, 0.34, 0.48, 0.0, 0.0, False)),
        ("13-window", STILLS / "shot-window.jpg", 125, (1.00, 1.045, 0.62, 0.48, 0.0, 0.35, False)),
        ("14-black", None, 20, None),
        ("15-title", poster, 200, None),
    ]
    clips: list[Path] = []
    total = 0
    for name, src, frames, move in shots:
        dest = BUILD / f"{name}.mp4"
        if src is None and name.startswith("01"):
            black(frames, dest)
        elif name.startswith("14"):
            black(frames, dest)
        elif name.startswith("15"):
            title_card(src, dest, frames)
        else:
            z0, z1, cx, cy, fade_in, fade_out, supers = move
            scene(src, dest, frames, z0, z1, cx, cy, fade_in, fade_out, supers)
        clips.append(dest)
        total += frames
    if total != FPS * 60:
        raise SystemExit(f"frame count {total} is not 60 seconds")
    score = BUILD / "score.wav"
    if not score.exists():
        subprocess.run(["python3", str(ROOT / "make_score.py")], check=True)
    out = ROOT / "out" / "yokoku-60s.mp4"
    out.parent.mkdir(parents=True, exist_ok=True)
    assemble(clips, score, out)
    probe = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-show_entries",
            "stream=codec_type,width,height,nb_frames",
            "-of",
            "default=nw=1",
            str(out),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    print(probe.stdout)
    print(out)


if __name__ == "__main__":
    main()
