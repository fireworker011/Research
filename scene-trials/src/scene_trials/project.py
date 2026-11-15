"""Load and validate ``project.yaml``. Everything project specific lives there."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Mapping, TypeVar

import yaml

from scene_trials.errors import ConfigError, unreachable

OUT_ROOT_ENV = "SCENE_TRIALS_OUT_ROOT"
_DRIVE_PATH = re.compile(r"^[A-Za-z]:[\\/]")
_TOP_KEYS = frozenset(
    {
        "schema",
        "project",
        "paths",
        "columns",
        "section_slugs",
        "trials",
        "batch",
        "safety",
        "prompt",
        "size",
        "face_visible_hints",
        "cutout",
        "backend",
        "forbidden_path_fragments",
        "skip_scenes",
    }
)
_E = TypeVar("_E", bound=Enum)
_DEFAULT_FORBIDDEN = ("Picture/CG", ".library")
_DEFAULT_CONFLICTS: Mapping[str, tuple[str, ...]] = {
    "portrait": ("landscape composition", "horizontal framing"),
    "landscape": ("portrait composition", "vertical framing"),
}


class TrialOrder(Enum):
    TRIAL_MAJOR = "trial_major"
    SCENE_MAJOR = "scene_major"


class CharPolicy(Enum):
    RANDOM_SEEDED = "random_seeded"
    ROTATE = "rotate"
    FIXED = "fixed"


class CompositionAction(Enum):
    WARN = "warn"
    DROP = "drop"
    OFF = "off"


@dataclass(frozen=True)
class ColumnMap:
    section: str = "category"
    positive: str = "positive_prompt"
    negative: str = "negative_prompt"
    id_columns: tuple[str, ...] = ("pose",)


@dataclass(frozen=True)
class SafetyConfig:
    adult_confirmed_by: str = ""
    adult_confirmed_on: str = ""
    extra_blocked_words: tuple[str, ...] = ()


@dataclass(frozen=True)
class PromptConfig:
    expand_braces: bool = True
    char_policy: CharPolicy = CharPolicy.RANDOM_SEEDED
    fixed_choice: str | None = None
    positive_anchor: tuple[str, ...] = ()
    composition: CompositionAction = CompositionAction.WARN
    composition_conflicts: Mapping[str, tuple[str, ...]] = field(
        default_factory=lambda: dict(_DEFAULT_CONFLICTS)
    )


@dataclass(frozen=True)
class CutoutConfig:
    templates: Mapping[str, str] = field(default_factory=dict)
    skip_if_transparent: bool = True


@dataclass(frozen=True)
class BackendConfig:
    name: str = "import_only"
    options: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class ProjectConfig:
    name: str
    root: Path
    out_root: Path
    scenes_csv: Path
    chains_path: Path | None
    loras_path: Path | None
    negatives_path: Path | None
    lora_dir: Path | None
    columns: ColumnMap
    section_slugs: Mapping[str, str]
    trial_count: int
    trial_order: TrialOrder
    batch_max_jobs: int
    safety: SafetyConfig
    prompt: PromptConfig
    width: int
    height: int
    face_visible_hints: tuple[str, ...]
    cutout: CutoutConfig
    backend: BackendConfig
    skip_scenes: tuple[str | int, ...]

    @property
    def project_out(self) -> Path:
        return self.out_root / self.name


def load_project(project_dir: Path) -> ProjectConfig:
    root = Path(project_dir).resolve()
    config_path = root / "project.yaml"
    if not config_path.is_file():
        raise ConfigError("project_missing", f"{config_path} does not exist")
    raw = _load_yaml_mapping(config_path)
    unknown = set(raw) - _TOP_KEYS
    if unknown:
        raise ConfigError("unknown_key", f"project.yaml has unknown keys: {sorted(unknown)}")
    if raw.get("schema") != 1:
        raise ConfigError("bad_schema", "project.yaml needs `schema: 1`")
    name = _text(raw, "project")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", name):
        raise ConfigError("bad_project_name", f"project name must be ASCII safe: {name!r}")

    paths = _mapping(raw, "paths")
    columns = _columns(_mapping(raw, "columns", required=False))
    trials = _mapping(raw, "trials", required=False)
    batch = _mapping(raw, "batch", required=False)
    size = _mapping(raw, "size", required=False)
    forbidden = tuple(_str_list(raw.get("forbidden_path_fragments", _DEFAULT_FORBIDDEN)))
    out_root = _resolve_out_root(_text(paths, "out_root"), root, forbidden)

    count = int(trials.get("count", 3))
    max_jobs = int(batch.get("max_jobs", 50))
    width = int(size.get("width", 1024))
    height = int(size.get("height", 1344))
    if count < 1 or max_jobs < 1:
        raise ConfigError("bad_number", "trials.count and batch.max_jobs must be >= 1")
    if width < 8 or height < 8 or width % 8 or height % 8:
        raise ConfigError("bad_size", "size.width and size.height must be multiples of 8")

    return ProjectConfig(
        name=name,
        root=root,
        out_root=out_root,
        scenes_csv=_relative(root, _text(paths, "scenes_csv")),
        chains_path=_optional_path(root, paths, "chains"),
        loras_path=_optional_path(root, paths, "loras"),
        negatives_path=_optional_path(root, paths, "negatives"),
        lora_dir=_optional_path(root, paths, "lora_dir"),
        columns=columns,
        section_slugs={str(k): str(v) for k, v in _mapping(raw, "section_slugs", required=False).items()},
        trial_count=count,
        trial_order=_enum(TrialOrder, str(trials.get("order", TrialOrder.TRIAL_MAJOR.value)), "trials.order"),
        batch_max_jobs=max_jobs,
        safety=_safety(_mapping(raw, "safety", required=False)),
        prompt=_prompt(_mapping(raw, "prompt", required=False)),
        width=width,
        height=height,
        face_visible_hints=tuple(_str_list(raw.get("face_visible_hints", ()))),
        cutout=_cutout(_mapping(raw, "cutout", required=False)),
        backend=_backend(_mapping(raw, "backend", required=False)),
        skip_scenes=_scene_refs(raw.get("skip_scenes")),
    )


def load_yaml_file(path: Path) -> Mapping[str, object]:
    return _load_yaml_mapping(path)


def _load_yaml_mapping(path: Path) -> Mapping[str, object]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ConfigError("yaml_error", f"{path}: {exc}") from exc
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ConfigError("yaml_shape", f"{path} must be a mapping at the top level")
    return data


def _mapping(raw: Mapping[str, object], key: str, *, required: bool = True) -> Mapping[str, object]:
    value = raw.get(key)
    if value is None:
        if required:
            raise ConfigError("missing_key", f"project.yaml needs `{key}`")
        return {}
    if not isinstance(value, dict):
        raise ConfigError("yaml_shape", f"`{key}` must be a mapping")
    return value


def _text(raw: Mapping[str, object], key: str) -> str:
    value = raw.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ConfigError("missing_key", f"`{key}` must be a non-empty string")
    return value.strip()


def _str_list(value: object) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, (list, tuple)):
        raise ConfigError("yaml_shape", f"expected a list, got {type(value).__name__}")
    return [str(item) for item in value]


def _relative(root: Path, text: str) -> Path:
    path = Path(text)
    return path if path.is_absolute() else (root / path).resolve()


def _optional_path(root: Path, raw: Mapping[str, object], key: str) -> Path | None:
    value = raw.get(key)
    if value is None or not str(value).strip():
        return None
    return _relative(root, str(value))


def _resolve_out_root(text: str, root: Path, forbidden: tuple[str, ...]) -> Path:
    override = os.environ.get(OUT_ROOT_ENV, "").strip()
    chosen = override or text
    if _DRIVE_PATH.match(chosen) and os.name != "nt":
        raise ConfigError(
            "out_root_platform",
            f"out_root {chosen!r} is a Windows path. Set {OUT_ROOT_ENV} for this machine.",
        )
    path = _relative(root, chosen)
    normalized = str(path).replace("\\", "/").casefold()
    for fragment in forbidden:
        if fragment.replace("\\", "/").casefold() in normalized:
            raise ConfigError(
                "out_root_forbidden",
                f"out_root {chosen!r} contains the reserved location {fragment!r}",
            )
    return path


def _enum(kind: type[_E], value: str, label: str) -> _E:
    for member in kind:
        if member.value == value:
            return member
    allowed = ", ".join(member.value for member in kind)
    raise ConfigError("bad_value", f"{label} must be one of: {allowed} (got {value!r})")


def _columns(raw: Mapping[str, object]) -> ColumnMap:
    defaults = ColumnMap()
    return ColumnMap(
        section=str(raw.get("section", defaults.section)),
        positive=str(raw.get("positive", defaults.positive)),
        negative=str(raw.get("negative", defaults.negative)),
        id_columns=tuple(_str_list(raw.get("id_columns", defaults.id_columns))),
    )


def _safety(raw: Mapping[str, object]) -> SafetyConfig:
    return SafetyConfig(
        adult_confirmed_by=str(raw.get("adult_confirmed_by", "") or ""),
        adult_confirmed_on=str(raw.get("adult_confirmed_on", "") or ""),
        extra_blocked_words=tuple(_str_list(raw.get("extra_blocked_words", ()))),
    )


def _prompt(raw: Mapping[str, object]) -> PromptConfig:
    policy = _enum(CharPolicy, str(raw.get("char_policy", CharPolicy.RANDOM_SEEDED.value)), "prompt.char_policy")
    composition = _enum(
        CompositionAction, str(raw.get("composition", CompositionAction.WARN.value)), "prompt.composition"
    )
    fixed = raw.get("fixed_choice")
    if policy is CharPolicy.FIXED and not fixed:
        raise ConfigError("missing_key", "prompt.fixed_choice is required when char_policy is fixed")
    conflicts = raw.get("composition_conflicts")
    if conflicts is None:
        merged: Mapping[str, tuple[str, ...]] = dict(_DEFAULT_CONFLICTS)
    elif isinstance(conflicts, dict):
        merged = {str(k): tuple(_str_list(v)) for k, v in conflicts.items()}
    else:
        raise ConfigError("yaml_shape", "prompt.composition_conflicts must be a mapping")
    return PromptConfig(
        expand_braces=bool(raw.get("expand_braces", True)),
        char_policy=policy,
        fixed_choice=None if fixed is None else str(fixed),
        positive_anchor=tuple(_str_list(raw.get("positive_anchor", ()))),
        composition=composition,
        composition_conflicts=merged,
    )


def _cutout(raw: Mapping[str, object]) -> CutoutConfig:
    templates = raw.get("templates", {})
    if not isinstance(templates, dict):
        raise ConfigError("yaml_shape", "cutout.templates must be a mapping")
    for flavor in templates:
        if flavor not in ("ps1", "sh"):
            raise ConfigError("bad_value", f"cutout.templates keys are ps1 or sh, got {flavor!r}")
    return CutoutConfig(
        templates={str(k): str(v) for k, v in templates.items()},
        skip_if_transparent=bool(raw.get("skip_if_transparent", True)),
    )


def _backend(raw: Mapping[str, object]) -> BackendConfig:
    options = raw.get("options", {})
    if not isinstance(options, dict):
        raise ConfigError("yaml_shape", "backend.options must be a mapping")
    return BackendConfig(name=str(raw.get("name", "import_only")), options=dict(options))


def _scene_refs(value: object) -> tuple[str | int, ...]:
    if value is None:
        return ()
    if not isinstance(value, (list, tuple)):
        raise ConfigError("yaml_shape", "skip_scenes must be a list of row numbers or scene ids")
    refs: list[str | int] = []
    for item in value:
        if isinstance(item, bool) or not isinstance(item, (str, int)):
            raise ConfigError("yaml_shape", f"bad skip_scenes entry {item!r}")
        refs.append(item)
    return tuple(refs)


def describe_order(order: TrialOrder) -> str:
    if order is TrialOrder.TRIAL_MAJOR:
        return "trial_major"
    if order is TrialOrder.SCENE_MAJOR:
        return "scene_major"
    return unreachable(order)
