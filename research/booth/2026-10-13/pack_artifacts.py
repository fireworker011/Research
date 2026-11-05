#!/usr/bin/env python3
"""Copy masters into the artifact store, splitting any file over 95MB."""

from __future__ import annotations

import shutil
import subprocess
import zipfile
from pathlib import Path

SRC = Path("/home/ubuntu/booth-out")
DST = Path("/opt/cursor/artifacts/booth-2026-10-13")
LIMIT = 95 * 1024 * 1024
SEGMENT = 480  # seconds; 44.1kHz 16bit stereo stays under 95MB


def split_wav(src: Path, dest_dir: Path, stem: str) -> list[Path]:
    dest_dir.mkdir(parents=True, exist_ok=True)
    pattern = dest_dir / f"{stem}_%02d.wav"
    subprocess.run(
        [
            "ffmpeg", "-y", "-v", "error", "-i", str(src),
            "-f", "segment", "-segment_time", str(SEGMENT),
            "-c", "copy", str(pattern),
        ],
        check=True,
    )
    parts = sorted(dest_dir.glob(f"{stem}_*.wav"))
    for part in parts:
        if part.stat().st_size > 100 * 1024 * 1024:
            raise RuntimeError(f"still too large: {part} {part.stat().st_size}")
    return parts


def copy_or_split(src: Path, dest_dir: Path) -> list[Path]:
    dest_dir.mkdir(parents=True, exist_ok=True)
    if src.stat().st_size <= LIMIT:
        dest = dest_dir / src.name
        if not dest.exists() or dest.stat().st_size != src.stat().st_size:
            shutil.copy2(src, dest)
        return [dest]
    if src.suffix != ".wav":
        raise RuntimeError(f"non-wav over limit: {src}")
    return split_wav(src, dest_dir, src.stem)


def write_zip(dest: Path, files: list[Path], folder: str) -> None:
    if dest.exists():
        dest.unlink()
    with zipfile.ZipFile(dest, "w", compression=zipfile.ZIP_STORED) as zf:
        for file in files:
            zf.write(file, arcname=f"{folder}/{file.name}")
    with zipfile.ZipFile(dest) as zf:
        bad = zf.testzip()
        names = zf.namelist()
    images = [n for n in names if n.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".webp"))]
    nested = [n for n in names if n.lower().endswith(".zip")]
    size = dest.stat().st_size
    if bad or images or nested or size > 300 * 1024 * 1024 or size > 100 * 1024 * 1024:
        raise RuntimeError(f"zip check failed {dest.name} size={size} bad={bad} images={images} nested={nested}")


def pack_work(work_id: str, readme: str, script: str) -> list[str]:
    audio = SRC / work_id / "audio"
    sample = SRC / work_id / "sample" / "sample.mp3"
    out = DST / work_id
    audio_out = out / "audio"
    lines = []
    stored: list[Path] = []
    for src in sorted(audio.iterdir()):
        if src.suffix not in {".wav", ".mp3"}:
            continue
        stored.extend(copy_or_split(src, audio_out))
    sample_dest = out / "sample"
    sample_dest.mkdir(parents=True, exist_ok=True)
    shutil.copy2(sample, sample_dest / "sample.mp3")
    stored.append(sample_dest / "sample.mp3")
    meta = out / "meta"
    meta.mkdir(parents=True, exist_ok=True)
    (meta / "readme.txt").write_text(readme, encoding="utf-8")
    (meta / "台本.txt").write_text(script, encoding="utf-8")
    # MP3 groups under 90MB, whole files only
    mp3s = [p for p in stored if p.suffix == ".mp3" and p.parent == audio_out]
    mp3s = sorted(mp3s, key=lambda p: p.name)
    groups: list[list[Path]] = []
    cur: list[Path] = []
    size = 0
    for mp3 in mp3s:
        n = mp3.stat().st_size
        if cur and size + n > 90 * 1024 * 1024:
            groups.append(cur)
            cur, size = [], 0
        cur.append(mp3)
        size += n
    if cur:
        groups.append(cur)
    zip_dir = out / "zip"
    zip_dir.mkdir(parents=True, exist_ok=True)
    report = []
    for i, group in enumerate(groups, start=1):
        label = f"{work_id}_MP3_その{i}"
        extras = [meta / "readme.txt", meta / "台本.txt"] if i == 1 else [meta / "readme.txt"]
        dest = zip_dir / f"{label}.zip"
        write_zip(dest, group + extras, label)
        report.append(dest)
    wavs = sorted([p for p in stored if p.suffix == ".wav"], key=lambda p: p.name)
    groups = []
    cur, size = [], 0
    for wav in wavs:
        n = wav.stat().st_size
        if cur and size + n > 90 * 1024 * 1024:
            groups.append(cur)
            cur, size = [], 0
        cur.append(wav)
        size += n
    if cur:
        groups.append(cur)
    for i, group in enumerate(groups, start=1):
        label = f"{work_id}_WAV_その{i}"
        dest = zip_dir / f"{label}.zip"
        write_zip(dest, group + [meta / "readme.txt"], label)
        report.append(dest)
    listing = []
    for zpath in report:
        listing.append(f"{zpath.name}\t{zpath.stat().st_size}")
        with zipfile.ZipFile(zpath) as zf:
            listing.extend(f"  {n}\t{zf.getinfo(n).file_size}" for n in zf.namelist())
    (zip_dir / "files.txt").write_text("\n".join(listing) + "\n", encoding="utf-8")
    for path in stored:
        lines.append(f"{path.relative_to(DST)}\t{path.stat().st_size}")
    return lines


def pack_line19() -> None:
    src = Path("/home/ubuntu/booth-out/line-cache/19")
    dest = DST / "19"
    dest.mkdir(parents=True, exist_ok=True)
    for name in ("kouetsu-line.wav", "kouetsu-line.mp3"):
        shutil.copy2(src / name, dest / name)
    note = dest / "readme.txt"
    note.write_text(
        "19作目の校閲で差し替える1行です。本編の結合は、前回のpart01が無いのでPC待ちです。\n"
        "原稿: 平日は、原稿をチェックする仕事で\n"
        "合成に渡した文: 平日は、書いた原稿をチェックする仕事で\n"
        "話者: COEIROINK アンジーさん ささやき styleId 122、speedScale 0.95\n",
        encoding="utf-8",
    )


def main() -> None:
    research = Path("/workspace/research/booth/2026-10-13")
    lines: list[str] = []
    for work_id in ("20", "21"):
        readme = (research / work_id / "readme.txt").read_text(encoding="utf-8")
        script = (research / work_id / "script.md").read_text(encoding="utf-8")
        lines.extend(pack_work(work_id, readme, script))
        files_src = DST / work_id / "zip" / "files.txt"
        (research / work_id / "files.txt").write_text(files_src.read_text(encoding="utf-8"), encoding="utf-8")
    pack_line19()
    (DST / "files.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("packed", len(lines))


if __name__ == "__main__":
    main()
