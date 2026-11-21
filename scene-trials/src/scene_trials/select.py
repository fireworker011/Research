"""N6: contact sheets, the selection file, and the ``selected/`` folder."""

from __future__ import annotations

import csv
import html
import json
import shutil
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw

from scene_trials.collector import RESULT_STEM, file_sha256, find_result, find_transparent
from scene_trials.errors import SceneTrialsError
from scene_trials.layout import Layout
from scene_trials.plan import TrialPlan

THUMB_HEIGHT = 320
_MARGIN = 12
_LABEL_HEIGHT = 22
_FIELDS = ["scene_id", "trial", "note"]


@dataclass(frozen=True)
class Pick:
    scene_id: str
    trial: int
    note: str = ""


def read_selection(path: Path) -> dict[str, Pick]:
    if not path.is_file():
        return {}
    with path.open(encoding="utf-8-sig", newline="") as handle:
        picks = {}
        for row in csv.DictReader(handle):
            scene_id = (row.get("scene_id") or "").strip()
            if not scene_id:
                continue
            picks[scene_id] = Pick(scene_id, int(row["trial"]), (row.get("note") or "").strip())
        return picks


def write_selection(path: Path, picks: dict[str, Pick]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=_FIELDS)
        writer.writeheader()
        for pick in sorted(picks.values(), key=lambda item: item.scene_id):
            writer.writerow({"scene_id": pick.scene_id, "trial": pick.trial, "note": pick.note})


def set_pick(plan: TrialPlan, scene_id: str, trial: int, note: str = "") -> Pick:
    scene = plan.scene_by_id().get(scene_id)
    if scene is None:
        raise SceneTrialsError("pick_invalid", f"unknown scene {scene_id}")
    if not 1 <= trial <= plan.project.trial_count:
        raise SceneTrialsError("pick_invalid", f"trial must be 1..{plan.project.trial_count}")
    layout = Layout(plan.project)
    if find_result(layout.trial_dir(scene.section, scene_id, trial)) is None:
        raise SceneTrialsError("pick_invalid", f"{scene_id} trial {trial} has no result to pick")
    path = layout.selection_csv()
    picks = read_selection(path)
    picks[scene_id] = Pick(scene_id, trial, note)
    write_selection(path, picks)
    return picks[scene_id]


def make_sheet(plan: TrialPlan, scene_id: str) -> Path:
    scene = plan.scene_by_id()[scene_id]
    layout = Layout(plan.project)
    tiles: list[Image.Image] = []
    for trial in range(1, plan.project.trial_count + 1):
        found = find_result(layout.trial_dir(scene.section, scene_id, trial))
        tiles.append(_tile(found, f"T{trial}"))
    width = sum(tile.width for tile in tiles) + _MARGIN * (len(tiles) + 1)
    height = max(tile.height for tile in tiles) + _MARGIN * 2
    sheet = Image.new("RGB", (width, height), (40, 40, 44))
    x = _MARGIN
    for tile in tiles:
        sheet.paste(tile, (x, _MARGIN))
        x += tile.width + _MARGIN
    dest = layout.sheets_dir() / scene.section / f"{scene_id}.png"
    dest.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(dest)
    return dest


def _tile(path: Path | None, label: str) -> Image.Image:
    if path is None:
        tile = Image.new("RGB", (int(THUMB_HEIGHT * 0.75), THUMB_HEIGHT + _LABEL_HEIGHT), (70, 40, 40))
        ImageDraw.Draw(tile).text((8, THUMB_HEIGHT // 2), f"{label} missing", fill=(255, 255, 255))
        return tile
    with Image.open(path) as source:
        rgba = source.convert("RGBA")
    ratio = THUMB_HEIGHT / rgba.height
    thumb = rgba.resize((max(1, round(rgba.width * ratio)), THUMB_HEIGHT), Image.LANCZOS)
    backdrop = Image.new("RGBA", thumb.size, (200, 200, 200, 255))
    backdrop.alpha_composite(thumb)
    tile = Image.new("RGB", (thumb.width, THUMB_HEIGHT + _LABEL_HEIGHT), (40, 40, 44))
    tile.paste(backdrop.convert("RGB"), (0, _LABEL_HEIGHT))
    ImageDraw.Draw(tile).text((6, 4), label, fill=(255, 255, 255))
    return tile


def make_index(plan: TrialPlan, sheets: list[Path]) -> Path:
    layout = Layout(plan.project)
    base = layout.sheets_dir()
    items = "\n".join(
        f'<h3>{html.escape(sheet.stem)}</h3><img src="{html.escape(sheet.relative_to(base).as_posix())}">'
        for sheet in sheets
    )
    dest = base / "index.html"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(
        f"<!doctype html><meta charset=utf-8><title>{html.escape(plan.project.name)}</title>"
        f'<body style="background:#222;color:#eee;font-family:sans-serif">{items}</body>',
        encoding="utf-8",
    )
    return dest


@dataclass(frozen=True)
class Finalized:
    scene_id: str
    trial: int
    path: Path
    transparent: Path | None


def finalize(plan: TrialPlan, picks: dict[str, Pick]) -> list[Finalized]:
    layout = Layout(plan.project)
    scenes = plan.scene_by_id()
    done: list[Finalized] = []
    for scene_id, pick in sorted(picks.items()):
        scene = scenes.get(scene_id)
        if scene is None:
            raise SceneTrialsError("pick_invalid", f"unknown scene {scene_id} in the selection")
        trial_dir = layout.trial_dir(scene.section, scene_id, pick.trial)
        result = find_result(trial_dir)
        if result is None:
            raise SceneTrialsError("pick_invalid", f"{scene_id} trial {pick.trial} has no result")
        target_dir = layout.selected_dir(scene.section, scene_id)
        target_dir.mkdir(parents=True, exist_ok=True)
        chosen = target_dir / f"{scene_id}{result.suffix.lower()}"
        shutil.copyfile(result, chosen)
        transparent_src = find_transparent(trial_dir)
        transparent: Path | None = None
        if transparent_src is not None:
            transparent = target_dir / f"{scene_id}.transparent{transparent_src.suffix.lower()}"
            shutil.copyfile(transparent_src, transparent)
        (target_dir / "selected.json").write_text(
            json.dumps(
                {
                    "scene_id": scene_id,
                    "trial": pick.trial,
                    "note": pick.note,
                    "source": f"trial_{pick.trial}/{RESULT_STEM}{result.suffix.lower()}",
                    "sha256": file_sha256(result),
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        done.append(Finalized(scene_id, pick.trial, chosen, transparent))
    return done
