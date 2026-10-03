"""After both parts exist, write the waiting folder. This does not post."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any


def write_waiting(drive: Path, waiting: Path) -> list[Path]:
    groups: dict[str, list[tuple[Path, dict[str, Any]]]] = {}
    for folder, side in _sides(drive):
        groups.setdefault(str(side["short_id"]), []).append((folder, side))
    wrote: list[Path] = []
    waiting.mkdir(parents=True, exist_ok=True)
    for short_id, items in sorted(groups.items()):
        if len(items) < 2:
            continue
        clips: list[tuple[str, Path]] = []
        ready = True
        for _folder, side in sorted(items, key=lambda item: int(item[1]["part_index"])):
            raw = str(side.get("output_mp4") or "")
            path = Path(raw) if raw else None
            if path is None or not path.is_file():
                ready = False
                break
            clips.append((str(side["part_key"]), path))
        if not ready:
            continue
        side0 = items[0][1]
        dest = waiting / short_id
        if dest.exists():
            continue
        dest.mkdir(parents=True)
        description = str(side0["description"])
        if not description.startswith("アフィリエイト広告を含みます"):
            raise ValueError("概要欄の先頭が開示文ではない")
        (dest / "description.txt").write_text(description if description.endswith("\n") else description + "\n", encoding="utf-8")
        (dest / "title.txt").write_text(str(side0["title"]) + "\n", encoding="utf-8")
        (dest / "subtitles.srt").write_text(_srt(side0["beats"]), encoding="utf-8")
        (dest / "voice.txt").write_text(_voice(side0["beats"]), encoding="utf-8")
        (dest / "POST.txt").write_text("投稿は人間が押す。このフォルダからは投稿しない。\n", encoding="utf-8")
        for key, src in clips:
            shutil.copy2(src, dest / f"part-{key}.mp4")
        wrote.append(dest)
    return wrote


def _sides(drive: Path) -> list[tuple[Path, dict[str, Any]]]:
    found: list[tuple[Path, dict[str, Any]]] = []
    for bucket in ("inbox", "queued", "running", "done", "failed"):
        base = drive / bucket
        if not base.is_dir():
            continue
        for child in sorted(base.iterdir()):
            path = child / "affi.json"
            if path.is_file():
                found.append((child, json.loads(path.read_text(encoding="utf-8"))))
    return found


def _srt(beats: list[dict[str, Any]]) -> str:
    blocks = []
    for index, beat in enumerate(beats, start=1):
        text = str(beat["caption"]).replace(" / ", "\n")
        blocks.append(f"{index}\n{_ts(float(beat['start']))} --> {_ts(float(beat['end']))}\n{text}\n")
    return "\n".join(blocks)


def _ts(seconds: float) -> str:
    ms = int(round(seconds * 1000))
    hours, ms = divmod(ms, 3_600_000)
    minutes, ms = divmod(ms, 60_000)
    secs, ms = divmod(ms, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{ms:03d}"


def _voice(beats: list[dict[str, Any]]) -> str:
    lines = ["声: Gemini TTS Achernar（後乗せ）", "H3の声: 使わない", ""]
    for beat in beats:
        lines.append(f"{beat['start']:.1f}-{beat['end']:.1f} {beat['spoken']}")
    return "\n".join(lines) + "\n"
