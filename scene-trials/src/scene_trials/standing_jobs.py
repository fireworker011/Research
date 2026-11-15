"""Standing-picture rows to a factory ``--jobs`` file.

The scene table names the character and the pose. The prompt text comes from the
standing templates in the delusion prompt CSV. A pose that CSV does not contain
starts from one of those templates and only replaces the pose tags.
"""

from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from scene_trials.backends.sd_diff_set import _check_id
from scene_trials.errors import ConfigError
from scene_trials.project import _DEFAULT_CONFLICTS, load_yaml_file
from scene_trials.prompt import _apply_loras
from scene_trials.resources import LoraEntry
from scene_trials.safety import ensure_required_negatives
from scene_trials.tags import join_tags, split_tags, tag_key

STANDING = "立ち絵"
SKIP_CHARS = frozenset({"sora"})
CHAR_WORD = {
    "irito": "irito_xl",
    "jueri": "jueri_xl",
    "seraphina": "seraphina_xl",
    "nieva": "nieva_xl",
}
JOB_KEYS = (
    "id",
    "prompt",
    "negative_prompt",
    "width",
    "height",
    "sampler_name",
    "steps",
    "cfg_scale",
    "model",
    "clip_skip",
    "stages",
)
_BRACE = re.compile(r"^\{([^{}]+)\}$")
_STAGE_NUMBER = re.compile(r"^(\d+)")


@dataclass(frozen=True)
class PoseEdit:
    """A pose the template CSV does not list, built from one template it does list."""

    base: str
    drop: tuple[str, ...] = ()
    add: tuple[str, ...] = ()
    after: str = ""


# The template CSV has 通常, 微笑み, 誘い and 後ろ姿. These six are in the scene
# table only. Each one keeps that template and swaps the pose tags named here.
POSE_EDITS: dict[str, PoseEdit] = {
    "恥じらい": PoseEdit("微笑み", drop=("gentle smile", "slight head tilt"), add=("blush",)),
    "横向き": PoseEdit("通常", drop=("dynamic pose", "neutral expression"), add=("from side",)),
    "腰突き出し": PoseEdit("後ろ姿", add=("bent over", "presenting ass"), after="ass focus"),
    "胸寄せ": PoseEdit("通常", drop=("dynamic pose", "neutral expression"), add=("breasts squeezed together",)),
    "股開き": PoseEdit("通常", drop=("dynamic pose", "neutral expression"), add=("spread legs", "m legs")),
    "跪き": PoseEdit("通常", drop=("dynamic pose", "neutral expression"), add=("kneeling",)),
}


@dataclass(frozen=True)
class StandingSettings:
    width: int
    height: int
    sampler_name: str
    steps: int
    cfg_scale: object
    model: str
    clip_skip: int
    positive_anchor: tuple[str, ...]
    drop_tags: tuple[str, ...]


@dataclass(frozen=True)
class _Template:
    positive: str
    negative: str


def load_standing_settings(project_yaml: Path) -> tuple[StandingSettings, Path]:
    """Generation settings, and the project's loras.yaml. Does not resolve out_root."""
    raw = load_yaml_file(project_yaml)
    if not isinstance(raw, Mapping):
        raise ConfigError("yaml_shape", f"{project_yaml} is not a mapping")
    size = raw.get("size") if isinstance(raw.get("size"), dict) else {}
    prompt = raw.get("prompt") if isinstance(raw.get("prompt"), dict) else {}
    backend = raw.get("backend") if isinstance(raw.get("backend"), dict) else {}
    options = backend.get("options") if isinstance(backend.get("options"), dict) else {}
    generation = options.get("generation") if isinstance(options.get("generation"), dict) else {}
    for key in ("sampler_name", "steps", "cfg_scale", "model", "clip_skip"):
        if generation.get(key) in (None, ""):
            raise ConfigError("generation_missing", f"backend.options.generation.{key} is empty")
    width = int(size.get("width", 0))
    height = int(size.get("height", 0))
    if width < 8 or height < 8:
        raise ConfigError("bad_size", "size.width and size.height must be set")
    anchor = prompt.get("positive_anchor") or []
    if isinstance(anchor, str):
        anchor = [anchor]
    if not isinstance(anchor, list):
        raise ConfigError("yaml_shape", "prompt.positive_anchor must be a list")
    drop: tuple[str, ...] = ()
    if str(prompt.get("composition") or "") == "drop":
        orientation = "portrait" if height > width else "landscape" if width > height else "square"
        custom = prompt.get("composition_conflicts")
        table = custom if isinstance(custom, dict) else _DEFAULT_CONFLICTS
        names = table.get(orientation) or ()
        drop = tuple(str(item) for item in names)
    paths = raw.get("paths") if isinstance(raw.get("paths"), dict) else {}
    loras_name = paths.get("loras")
    if not loras_name:
        raise ConfigError("loras_missing", "paths.loras is empty")
    loras_path = Path(str(loras_name))
    if not loras_path.is_absolute():
        loras_path = project_yaml.parent / loras_path
    settings = StandingSettings(
        width=width,
        height=height,
        sampler_name=str(generation["sampler_name"]),
        steps=int(generation["steps"]),
        cfg_scale=generation["cfg_scale"],
        model=str(generation["model"]),
        clip_skip=int(generation["clip_skip"]),
        positive_anchor=tuple(str(item) for item in anchor if str(item).strip()),
        drop_tags=drop,
    )
    return settings, loras_path


def build_standing_jobs(
    scenes_csv: Path,
    templates_csv: Path,
    *,
    loras: Mapping[str, LoraEntry],
    settings: StandingSettings,
) -> tuple[list[dict[str, object]], int]:
    """Return factory jobs and how many sora rows were left out."""
    templates = _templates(templates_csv)
    jobs: list[dict[str, object]] = []
    skipped = 0
    seen: dict[str, str] = {}
    for row_number, row in _rows(scenes_csv, ("category", "subcategory", "char", "diff_stage")):
        if row.get("category", "") != STANDING:
            continue
        char = row.get("char", "").strip()
        if char.casefold() in SKIP_CHARS:
            skipped += 1
            continue
        word = CHAR_WORD.get(char)
        if word is None:
            raise ConfigError("standing_char", f"row {row_number}: no LoRA for char {char!r}")
        subcategory = row.get("subcategory", "").strip()
        positive, negative = _prompt_for(subcategory, templates, row_number)
        prompt = _with_character(positive, word, loras, settings)
        job_id = _job_id(char, row.get("diff_stage", ""), row_number)
        _check_id(job_id)
        if job_id in seen:
            raise ConfigError("standing_id", f"{job_id} is used by {seen[job_id]} and row {row_number}")
        seen[job_id] = f"row {row_number}"
        jobs.append(
            {
                "id": job_id,
                "prompt": prompt,
                "negative_prompt": join_tags(ensure_required_negatives(split_tags(negative))),
                "width": settings.width,
                "height": settings.height,
                "sampler_name": settings.sampler_name,
                "steps": settings.steps,
                "cfg_scale": settings.cfg_scale,
                "model": settings.model,
                "clip_skip": settings.clip_skip,
                "stages": ["none"],
            }
        )
    if not jobs:
        raise ConfigError("standing_empty", f"{scenes_csv} has no {STANDING} rows")
    return jobs, skipped


def write_jobs(path: Path, jobs: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"jobs": [{key: job[key] for key in JOB_KEYS} for job in jobs]}
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _rows(path: Path, columns: tuple[str, ...]) -> list[tuple[int, dict[str, str]]]:
    if not path.is_file():
        raise ConfigError("scenes_missing", f"{path} does not exist")
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        headers = reader.fieldnames or []
        for column in columns:
            if column not in headers:
                raise ConfigError("scenes_column", f"{path.name} has no column {column!r}")
        return [
            (index, {key: (value or "").strip() for key, value in row.items() if key is not None})
            for index, row in enumerate(reader, start=2)
        ]


def _templates(path: Path) -> dict[str, _Template]:
    found: dict[str, _Template] = {}
    for row_number, row in _rows(path, ("category", "subcategory", "positive_prompt", "negative_prompt")):
        if row.get("category", "") != STANDING:
            continue
        name = row.get("subcategory", "")
        if not name:
            raise ConfigError("template_empty", f"{path.name} row {row_number} has no subcategory")
        if name in found:
            raise ConfigError("template_duplicate", f"{path.name} lists {STANDING}/{name} twice")
        positive = row.get("positive_prompt", "")
        if not positive:
            raise ConfigError("template_empty", f"{path.name} row {row_number} has no positive_prompt")
        found[name] = _Template(positive, row.get("negative_prompt", ""))
    if not found:
        raise ConfigError("template_empty", f"{path.name} has no {STANDING} templates")
    return found


def _prompt_for(subcategory: str, templates: Mapping[str, _Template], row_number: int) -> tuple[str, str]:
    direct = templates.get(subcategory)
    if direct is not None:
        return direct.positive, direct.negative
    edit = POSE_EDITS.get(subcategory)
    if edit is None or edit.base not in templates:
        known = ", ".join([*templates, *POSE_EDITS])
        raise ConfigError(
            "template_missing",
            f"row {row_number}: no standing template for {subcategory!r}. Known: {known}",
        )
    base = templates[edit.base]
    tags = _edit_tags(split_tags(base.positive), edit, subcategory)
    return join_tags(tags), base.negative


def _edit_tags(tags: list[str], edit: PoseEdit, subcategory: str) -> list[str]:
    drop_keys = {tag_key(item) for item in edit.drop}
    missing = [item for item in edit.drop if not any(tag_key(tag) == tag_key(item) for tag in tags)]
    if missing:
        raise ConfigError("pose_edit", f"{subcategory}: template {edit.base} has no tag {missing}")
    kept: list[str] = []
    insert_at: int | None = None
    for tag in tags:
        if tag_key(tag) in drop_keys:
            if insert_at is None:
                insert_at = len(kept)
            continue
        kept.append(tag)
    if edit.after:
        indexes = [index for index, tag in enumerate(kept) if tag_key(tag) == tag_key(edit.after)]
        if not indexes:
            raise ConfigError("pose_edit", f"{subcategory}: template {edit.base} has no tag {edit.after!r}")
        insert_at = indexes[0] + 1
    if insert_at is None:
        insert_at = len(kept)
    return [*kept[:insert_at], *edit.add, *kept[insert_at:]]


def _with_character(positive: str, word: str, loras: Mapping[str, LoraEntry], settings: StandingSettings) -> str:
    tags = split_tags(positive)
    replaced = False
    rewritten: list[str] = []
    for tag in tags:
        options = _brace_options(tag)
        if options is None:
            rewritten.append(tag)
            continue
        if word not in options:
            raise ConfigError("lora_brace", f"{word} is not in {tag}")
        rewritten.append(word)
        replaced = True
    if not replaced:
        raise ConfigError("lora_brace", f"the standing template has no character brace for {word}")
    drop = {tag_key(item) for item in settings.drop_tags}
    rewritten = [tag for tag in rewritten if tag_key(tag) not in drop]
    mapped, _files = _apply_loras(rewritten, loras, [])
    for anchor in settings.positive_anchor:
        if tag_key(anchor) not in {tag_key(tag) for tag in mapped}:
            mapped.append(anchor)
    if word not in {entry.file for entry in loras.values()}:
        raise ConfigError("lora_missing", f"loras.yaml has no file for {word}")
    return join_tags(mapped)


def _brace_options(tag: str) -> tuple[str, ...] | None:
    match = _BRACE.match(tag.strip())
    if match is None or "|" not in match.group(1):
        return None
    return tuple(part.strip() for part in match.group(1).split("|"))


def _job_id(char: str, diff_stage: str, row_number: int) -> str:
    match = _STAGE_NUMBER.match(diff_stage.strip())
    if match is None:
        raise ConfigError("diff_stage", f"row {row_number}: diff_stage {diff_stage!r} does not start with a number")
    return f"standing-{char}-{int(match.group(1)):02d}"
