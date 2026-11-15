"""LoRA map and negative-prompt files."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping

from scene_trials.errors import ConfigError
from scene_trials.project import load_yaml_file
from scene_trials.tags import split_tags


@dataclass(frozen=True)
class LoraEntry:
    word: str
    file: str
    weight: float
    keep_trigger: bool = False

    @property
    def tag(self) -> str:
        return f"<lora:{self.file}:{_format_weight(self.weight)}>"


@dataclass(frozen=True)
class NegativeSet:
    always: tuple[str, ...] = ()
    by_section: Mapping[str, tuple[str, ...]] = field(default_factory=dict)


def _format_weight(weight: float) -> str:
    text = f"{weight:.3f}".rstrip("0").rstrip(".")
    return text or "0"


def load_loras(path: Path | None) -> dict[str, LoraEntry]:
    if path is None:
        return {}
    if not path.is_file():
        raise ConfigError("loras_missing", f"{path} does not exist")
    raw = load_yaml_file(path)
    loras = raw.get("loras") or {}
    if not isinstance(loras, dict):
        raise ConfigError("yaml_shape", "loras.yaml `loras` must be a mapping")
    entries: dict[str, LoraEntry] = {}
    for word, body in loras.items():
        if not isinstance(body, dict) or "file" not in body or "weight" not in body:
            raise ConfigError("lora_entry", f"lora {word!r} needs `file` and `weight`")
        unknown = set(body) - {"file", "weight", "keep_trigger"}
        if unknown:
            raise ConfigError("unknown_key", f"lora {word!r} has unknown keys: {sorted(unknown)}")
        entries[str(word)] = LoraEntry(
            word=str(word),
            file=str(body["file"]),
            weight=float(body["weight"]),
            keep_trigger=bool(body.get("keep_trigger", False)),
        )
    return entries


def load_negatives(path: Path | None) -> NegativeSet:
    if path is None:
        return NegativeSet()
    if not path.is_file():
        raise ConfigError("negatives_missing", f"{path} does not exist")
    raw = load_yaml_file(path)
    unknown = set(raw) - {"always", "by_section"}
    if unknown:
        raise ConfigError("unknown_key", f"negatives.yaml has unknown keys: {sorted(unknown)}")
    by_section = raw.get("by_section") or {}
    if not isinstance(by_section, dict):
        raise ConfigError("yaml_shape", "negatives.yaml `by_section` must be a mapping")
    return NegativeSet(
        always=tuple(split_tags(_joined(raw.get("always")))),
        by_section={str(k): tuple(split_tags(_joined(v))) for k, v in by_section.items()},
    )


def _joined(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return ", ".join(str(item) for item in value)
    raise ConfigError("yaml_shape", "negative entries must be a string or a list")
