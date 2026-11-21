"""N1: scene table. A scene is one CSV row and one deliverable."""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from typing import Mapping

from scene_trials.errors import ConfigError
from scene_trials.project import ProjectConfig

_ID_OK = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")
_NON_ID = re.compile(r"[^A-Za-z0-9]+")
_SCENE_ID_COLUMN = "scene_id"


@dataclass(frozen=True)
class Scene:
    row: int
    scene_id: str
    section: str
    section_label: str
    positive: str
    negative: str
    fields: Mapping[str, str]


def load_scenes(project: ProjectConfig) -> list[Scene]:
    path = project.scenes_csv
    if not path.is_file():
        raise ConfigError("scenes_missing", f"{path} does not exist")
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        columns = project.columns
        headers = reader.fieldnames or []
        for needed in (columns.section, columns.positive):
            if needed not in headers:
                raise ConfigError("scenes_column", f"{path.name} has no column {needed!r}")
        scenes: list[Scene] = []
        seen: dict[str, int] = {}
        for index, record in enumerate(reader, start=1):
            fields = {key: (value or "").strip() for key, value in record.items() if key is not None}
            positive = fields.get(columns.positive, "")
            if not positive:
                raise ConfigError("scene_empty", f"row {index} has an empty {columns.positive}")
            label = fields.get(columns.section, "")
            scene_id = _scene_id(index, fields, columns.id_columns)
            if scene_id in seen:
                raise ConfigError("scene_duplicate", f"scene id {scene_id} appears on rows {seen[scene_id]} and {index}")
            seen[scene_id] = index
            scenes.append(
                Scene(
                    row=index,
                    scene_id=scene_id,
                    section=_section_slug(project, label, index),
                    section_label=label,
                    positive=positive,
                    negative=fields.get(columns.negative, ""),
                    fields=fields,
                )
            )
    if not scenes:
        raise ConfigError("scenes_empty", f"{path.name} has no rows")
    return scenes


def _scene_id(row: int, fields: Mapping[str, str], id_columns: tuple[str, ...]) -> str:
    explicit = fields.get(_SCENE_ID_COLUMN, "")
    if explicit:
        if not _ID_OK.match(explicit):
            raise ConfigError("scene_id_bad", f"row {row}: scene_id {explicit!r} must be ASCII safe")
        return explicit
    parts = [f"S{row:02d}"]
    for column in id_columns:
        piece = _NON_ID.sub("_", fields.get(column, "")).strip("_")
        if piece:
            parts.append(piece)
    return "_".join(parts)


def _section_slug(project: ProjectConfig, label: str, row: int) -> str:
    mapped = project.section_slugs.get(label)
    if mapped:
        if not _ID_OK.match(mapped):
            raise ConfigError("section_slug_bad", f"section slug {mapped!r} must be ASCII safe")
        return mapped
    slug = _NON_ID.sub("_", label).strip("_").lower()
    if not slug:
        raise ConfigError(
            "section_unmapped",
            f"row {row}: section {label!r} has no ASCII slug. Add it to section_slugs in project.yaml.",
        )
    return slug


def find_scene(scenes: list[Scene], ref: object) -> Scene:
    """Resolve a row number or a scene id."""
    if isinstance(ref, bool):
        raise ConfigError("scene_ref", f"bad scene reference {ref!r}")
    if isinstance(ref, int):
        for scene in scenes:
            if scene.row == ref:
                return scene
    elif isinstance(ref, str):
        text = ref.strip()
        for scene in scenes:
            if scene.scene_id == text:
                return scene
        if text.isdigit():
            return find_scene(scenes, int(text))
    raise ConfigError("scene_ref", f"no scene matches {ref!r}")
