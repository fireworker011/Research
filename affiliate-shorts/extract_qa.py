"""書き出した mp4 から、話している場面のフレームを抜く。"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from PIL import Image


def _run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL)


def _crop_face(src: Path, dest: Path) -> None:
    with Image.open(src) as im:
        im = im.convert("RGB")
        w, h = im.size
        box = (int(w * 0.18), int(h * 0.18), int(w * 0.82), int(h * 0.78))
        face = im.crop(box)
        face.thumbnail((360, 640))
        dest.parent.mkdir(parents=True, exist_ok=True)
        face.save(dest, quality=80)


def _sheet(images: list[Path], dest: Path, columns: int = 4) -> None:
    thumbs = []
    for path in images:
        with Image.open(path) as im:
            im = im.convert("RGB")
            im.thumbnail((240, 426))
            thumbs.append(im.copy())
    if not thumbs:
        return
    cell_w = max(im.width for im in thumbs)
    cell_h = max(im.height for im in thumbs)
    rows = (len(thumbs) + columns - 1) // columns
    sheet = Image.new("RGB", (columns * cell_w, rows * cell_h), (20, 20, 20))
    for index, im in enumerate(thumbs):
        x = (index % columns) * cell_w
        y = (index // columns) * cell_h
        sheet.paste(im, (x, y))
    dest.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(dest, quality=80)


def extract(folder: Path) -> None:
    video = folder / "out.mp4"
    project_path = folder / "project.json"
    if not video.is_file() or not project_path.is_file():
        return
    project = json.loads(project_path.read_text(encoding="utf-8"))
    qa = folder / "qa"
    speak = qa / "speak"
    sec = qa / "sec"
    faces = qa / "faces"
    for path in (speak, sec, faces):
        path.mkdir(parents=True, exist_ok=True)
        for old in path.glob("*.jpg"):
            old.unlink()
    _run([
        "ffmpeg", "-y", "-loglevel", "error", "-i", str(video),
        "-vf", "fps=1", str(sec / "t_%03d.jpg"),
    ])
    offset = 0.0
    speak_faces: list[Path] = []
    for scene in project["scenes"]:
        duration = float(scene["duration"])
        if scene.get("role") == "credit" or not str(scene.get("text") or "").strip():
            offset += duration
            continue
        stamp = offset + min(duration * 0.45, max(0.2, duration - 0.2))
        frame = speak / f"scene_{int(scene['id']):02d}.jpg"
        _run([
            "ffmpeg", "-y", "-loglevel", "error", "-ss", f"{stamp:.3f}",
            "-i", str(video), "-frames:v", "1", str(frame),
        ])
        face = faces / f"scene_{int(scene['id']):02d}.jpg"
        _crop_face(frame, face)
        speak_faces.append(face)
        offset += duration
    sec_faces = []
    for frame in sorted(sec.glob("*.jpg")):
        face = faces / f"sec_{frame.stem}.jpg"
        _crop_face(frame, face)
        sec_faces.append(face)
    _sheet(speak_faces, qa / "speak_faces.jpg", 4)
    _sheet(sec_faces, qa / "sec_faces.jpg", 5)


def main() -> None:
    root = Path(sys.argv[1])
    for folder in sorted(path for path in root.iterdir() if path.is_dir() and (path / "brief.json").is_file()):
        print(folder.name, flush=True)
        extract(folder)


if __name__ == "__main__":
    main()
