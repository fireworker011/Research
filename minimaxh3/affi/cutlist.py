"""cut-list-ffmpeg: stitch H3 clips or still slides. Does not post.

The edit is a CSV with columns index,src,in,out,subtitle.
ffmpeg writes 1080x1920 at 30fps. No color grade, zoom, pan, or fade.
Conversation filler is out of scope.
"""

from __future__ import annotations

import csv
import subprocess
import tempfile
from pathlib import Path
from typing import Any

COLUMNS = ("index", "src", "in", "out", "subtitle")
PURPOSES = frozenset({"h3", "slide"})
WIDTH = 1080
HEIGHT = 1920
FPS = 30
PART_SPLIT_S = 6.0

FONT_CANDIDATES = (
    "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
    "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
)
STILL_SUFFIXES = frozenset({".png", ".jpg", ".jpeg", ".webp"})
VIDEO_SUFFIXES = frozenset({".mp4", ".mov", ".mkv", ".webm"})
REFUSAL = "対象外。H3のクリップか画像スライドをつなぐときだけ使う。会話動画のフィラー除去には使わない。"


class CutError(Exception):
    def __init__(self, message: str, code: int) -> None:
        super().__init__(message)
        self.code = code


def format_seconds(value: float) -> str:
    text = f"{float(value):.3f}".rstrip("0").rstrip(".")
    if "." not in text:
        text += ".0"
    return text


def write_cuts(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "index": int(row["index"]),
                    "src": row["src"],
                    "in": format_seconds(float(row["in"])),
                    "out": format_seconds(float(row["out"])),
                    "subtitle": row["subtitle"],
                }
            )


def read_cuts(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        names = tuple(reader.fieldnames or ())
        if names != COLUMNS:
            raise CutError("列は index,src,in,out,subtitle", 1)
        rows: list[dict[str, str]] = []
        for raw in reader:
            if any(raw.get(column) is None for column in COLUMNS):
                raise CutError("字幕が無いか空の行がある。final.mp4 は作らない。", 1)
            rows.append({column: raw[column] for column in COLUMNS})
    if not rows:
        raise CutError("カット表が空。final.mp4 は作らない。", 1)
    return rows


def subtitle_empty(value: str | None) -> bool:
    if value is None:
        return True
    text = value.strip()
    if not text:
        return True
    leftover = text.replace("/", "").replace("／", "").strip()
    return leftover == ""


def h3_cut_rows(beats: list[dict[str, Any]], part_files: dict[str, str]) -> list[dict[str, Any]]:
    """One row per beat. in/out are inside the 6s or 9s source, not a new timeline."""
    rows: list[dict[str, Any]] = []
    for index, beat in enumerate(beats, start=1):
        start = float(beat["start"])
        end = float(beat["end"])
        if end <= PART_SPLIT_S + 1e-6:
            src = part_files["6s"]
            inn, out = start, end
        elif start >= PART_SPLIT_S - 1e-6:
            src = part_files["9s"]
            inn = start - PART_SPLIT_S
            out = end - PART_SPLIT_S
        else:
            raise ValueError("カットが6秒の境をまたぐ")
        rows.append(
            {
                "index": index,
                "src": src,
                "in": inn,
                "out": out,
                "subtitle": str(beat.get("caption") or ""),
            }
        )
    return rows


def render_cutlist(csv_path: Path, out: Path, purpose: str, bgm: Path | None = None) -> int:
    kind = purpose.strip().lower()
    if kind not in PURPOSES:
        print(REFUSAL)
        return 2
    try:
        rows = read_cuts(csv_path)
        _require_subtitles(rows)
        sources = [_resolve(csv_path, row["src"]) for row in rows]
        _require_sources(sources)
        font = _font()
    except CutError as exc:
        print(exc)
        return exc.code

    partial = out.with_name(out.stem + ".partial.mp4")
    out.parent.mkdir(parents=True, exist_ok=True)
    try:
        with tempfile.TemporaryDirectory(prefix="cutlist-") as tmp_name:
            tmp = Path(tmp_name)
            segments = [_segment(rows[i], sources[i], font, tmp / f"seg-{i:02d}.mp4") for i in range(len(rows))]
            _concat(segments, partial)
            if bgm is not None and bgm.is_file():
                mixed = out.with_name(out.stem + ".mixed.mp4")
                _mix(partial, bgm, mixed)
                partial.unlink(missing_ok=True)
                partial = mixed
        partial.replace(out)
    except CutError as exc:
        partial.unlink(missing_ok=True)
        out.unlink(missing_ok=True)
        print(exc)
        return exc.code
    except Exception:
        partial.unlink(missing_ok=True)
        out.unlink(missing_ok=True)
        raise
    print(out.resolve())
    print(csv_path.resolve())
    return 0


def _require_subtitles(rows: list[dict[str, str]]) -> None:
    for row in rows:
        if subtitle_empty(row["subtitle"]):
            raise CutError("字幕が無いか空の行がある。final.mp4 は作らない。", 1)
        inn = float(row["in"])
        out = float(row["out"])
        if out <= inn:
            raise CutError("in と out が逆。final.mp4 は作らない。", 1)


def _require_sources(sources: list[Path]) -> None:
    for path in sources:
        if not path.is_file():
            raise CutError(f"素材が無い: {path}", 1)
        if path.suffix.lower() not in STILL_SUFFIXES | VIDEO_SUFFIXES:
            raise CutError(f"素材の種類が対象外: {path.name}", 1)


def _resolve(csv_path: Path, src: str) -> Path:
    path = Path(src)
    if path.is_absolute():
        return path
    return csv_path.parent / path


def _font() -> Path:
    for item in FONT_CANDIDATES:
        path = Path(item)
        if path.is_file():
            return path
    raise CutError("日本語フォントが無い。final.mp4 は作らない。", 1)


def _segment(row: dict[str, str], source: Path, font: Path, dest: Path) -> Path:
    inn = float(row["in"])
    out = float(row["out"])
    duration = out - inn
    text_path = dest.with_suffix(".txt")
    text_path.write_text(_caption(row["subtitle"]), encoding="utf-8")
    vf = _vf(text_path, font)
    if source.suffix.lower() in STILL_SUFFIXES:
        command = [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-loop", "1", "-framerate", str(FPS), "-t", f"{duration:.3f}", "-i", str(source),
            "-vf", vf, "-r", str(FPS), "-fps_mode", "cfr",
            "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p", "-an",
            str(dest),
        ]
    else:
        command = [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-i", str(source), "-ss", f"{inn:.3f}", "-to", f"{out:.3f}",
            "-vf", vf, "-r", str(FPS), "-fps_mode", "cfr",
            "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p", "-an",
            str(dest),
        ]
    _run(command)
    return dest


def _caption(subtitle: str) -> str:
    lines = [part.strip() for part in subtitle.split("/")]
    return "\n".join(line for line in lines if line)


def _vf(text_path: Path, font: Path) -> str:
    font_e = _esc(font)
    text_e = _esc(text_path)
    # 色補正・ズーム・パン・フェードは入れない。文字と右上の PR だけ。
    return (
        f"scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=increase,"
        f"crop={WIDTH}:{HEIGHT},fps={FPS},setsar=1,"
        f"drawtext=fontfile={font_e}:textfile={text_e}:expansion=none:fontsize=64:"
        f"fontcolor=black:box=1:boxcolor=white:boxborderw=16:"
        f"x=(w-text_w)/2:y=160:line_spacing=10,"
        f"drawtext=fontfile={font_e}:text=PR:expansion=none:fontsize=36:"
        f"fontcolor=black:box=1:boxcolor=white:boxborderw=8:x=w-tw-48:y=48"
    )


def _esc(path: Path) -> str:
    return str(path).replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")


def _concat(segments: list[Path], dest: Path) -> None:
    listing = dest.with_suffix(".txt")
    lines = []
    for segment in segments:
        lines.append("file '" + str(segment).replace("'", "'\\''") + "'")
    listing.write_text("\n".join(lines) + "\n", encoding="utf-8")
    try:
        _run(
            [
                "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                "-f", "concat", "-safe", "0", "-i", str(listing),
                "-c", "copy", str(dest),
            ]
        )
    finally:
        listing.unlink(missing_ok=True)


def _mix(video: Path, bgm: Path, dest: Path) -> None:
    _run(
        [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-i", str(video), "-i", str(bgm),
            "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-shortest",
            str(dest),
        ]
    )


def _run(command: list[str]) -> None:
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "ffmpeg が失敗した").strip()
        raise CutError(detail, 1)
