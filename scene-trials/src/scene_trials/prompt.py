"""N2: turn a CSV prompt into the prompt a backend can send.

Order: brace expansion, route tags, blocked-word check, LoRA mapping, positive
anchor, composition handling, negative merge. Brace expansion happens once per
job, so every stage of a chain keeps the character the base picked.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Callable, Mapping

from scene_trials.errors import ConfigError, SafetyError, unreachable
from scene_trials.project import CharPolicy, CompositionAction, ProjectConfig
from scene_trials.resources import LoraEntry, NegativeSet
from scene_trials.safety import ensure_required_negatives, find_blocked
from scene_trials.tags import dedupe_tags, has_tag, join_tags, split_tags, tag_key

_BRACE_GROUP = re.compile(r"\{([^{}|]*(?:\|[^{}|]*)+)\}")
_LORA_TAG = re.compile(r"^<lora:([^:>]+)(?::[^>]*)?>$", re.IGNORECASE)

Picker = Callable[[int, tuple[str, ...]], int]


@dataclass(frozen=True)
class ResolvedPrompt:
    positive: str
    negative: str
    choices: tuple[tuple[str, str], ...]
    notes: tuple[str, ...]
    lora_files: tuple[str, ...]


def _digest(*parts: object) -> int:
    joined = "|".join(str(part) for part in parts)
    return int(hashlib.sha256(joined.encode("utf-8")).hexdigest(), 16)


def make_picker(project: ProjectConfig, job_key: str, trial: int) -> Picker:
    policy = project.prompt.char_policy
    if policy is CharPolicy.RANDOM_SEEDED:
        return lambda group, options: _digest(project.name, job_key, trial, group) % len(options)
    if policy is CharPolicy.ROTATE:
        return lambda group, options: (
            (trial - 1) + _digest(project.name, job_key, group) % len(options)
        ) % len(options)
    if policy is CharPolicy.FIXED:
        wanted = project.prompt.fixed_choice or ""

        def fixed(_group: int, options: tuple[str, ...]) -> int:
            for index, option in enumerate(options):
                if option.strip() == wanted:
                    return index
            raise ConfigError("fixed_choice_missing", f"fixed_choice {wanted!r} is not in {list(options)}")

        return fixed
    return unreachable(policy)


def expand_braces(text: str, picker: Picker) -> tuple[str, tuple[tuple[str, str], ...]]:
    """Replace each ``{a|b|c}`` with one option. Groups are counted left to right."""
    choices: list[tuple[str, str]] = []
    counter = 0

    def replace(match: re.Match[str]) -> str:
        nonlocal counter
        options = tuple(option.strip() for option in match.group(1).split("|"))
        index = picker(counter, options)
        counter += 1
        chosen = options[index]
        choices.append(("|".join(options), chosen))
        return chosen

    expanded = _BRACE_GROUP.sub(replace, text)
    if _BRACE_GROUP.search(expanded):
        raise ConfigError("braces_nested", "nested {a|b} groups are not supported")
    return expanded, tuple(choices)


def resolve_prompt(
    project: ProjectConfig,
    *,
    positive: str,
    negative: str,
    section: str,
    job_key: str,
    trial: int,
    route_tags: tuple[str, ...],
    loras: Mapping[str, LoraEntry],
    negatives: NegativeSet,
    width: int,
    height: int,
) -> ResolvedPrompt:
    notes: list[str] = []
    choices: tuple[tuple[str, str], ...] = ()
    text = positive
    if project.prompt.expand_braces:
        text, choices = expand_braces(text, make_picker(project, job_key, trial))
    elif _BRACE_GROUP.search(text):
        notes.append("braces_left: {a|b} groups were not expanded because expand_braces is off")

    tags = split_tags(text)
    for route_tag in route_tags:
        if not has_tag(tags, route_tag):
            tags.append(route_tag)
            notes.append(f"route_tag_added: {route_tag}")

    blocked = find_blocked(", ".join(tags), project.safety.extra_blocked_words)
    if blocked:
        raise SafetyError("cast_excluded", f"{job_key}: blocked word {blocked!r} in the positive prompt")

    tags, lora_files = _apply_loras(tags, loras, notes)
    for anchor in project.prompt.positive_anchor:
        if not has_tag(tags, anchor):
            tags.append(anchor)
    tags = _apply_composition(project, tags, width, height, notes)

    negative_tags = split_tags(negative)
    negative_tags.extend(negatives.always)
    negative_tags.extend(negatives.by_section.get(section, ()))
    final_negative = ensure_required_negatives(dedupe_tags(negative_tags))
    return ResolvedPrompt(
        positive=join_tags(tags),
        negative=", ".join(final_negative),
        choices=choices,
        notes=tuple(notes),
        lora_files=lora_files,
    )


def _apply_loras(
    tags: list[str], loras: Mapping[str, LoraEntry], notes: list[str]
) -> tuple[list[str], tuple[str, ...]]:
    present = {
        match.group(1).casefold()
        for tag in tags
        if (match := _LORA_TAG.match(tag.strip()))
    }
    out: list[str] = []
    files: list[str] = sorted(present)
    for tag in tags:
        entry = loras.get(tag.strip()) or _lookup_ci(loras, tag)
        if entry is None:
            out.append(tag)
            continue
        if entry.keep_trigger:
            out.append(tag)
        if entry.file.casefold() not in present:
            out.append(entry.tag)
            present.add(entry.file.casefold())
            files.append(entry.file.casefold())
            notes.append(f"lora_mapped: {entry.word} -> {entry.tag}")
    return out, tuple(sorted(set(files)))


def _lookup_ci(loras: Mapping[str, LoraEntry], tag: str) -> LoraEntry | None:
    wanted = tag_key(tag)
    for word, entry in loras.items():
        if tag_key(word) == wanted:
            return entry
    return None


def _apply_composition(
    project: ProjectConfig, tags: list[str], width: int, height: int, notes: list[str]
) -> list[str]:
    action = project.prompt.composition
    if action is CompositionAction.OFF:
        return tags
    orientation = "portrait" if height > width else "landscape" if width > height else "square"
    conflicts = project.prompt.composition_conflicts.get(orientation, ())
    hits = [tag for tag in tags if any(tag_key(tag) == tag_key(c) for c in conflicts)]
    if not hits:
        return tags
    if action is CompositionAction.WARN:
        for tag in hits:
            notes.append(f"composition_conflict: {tag!r} against a {orientation} {width}x{height} canvas")
        return tags
    if action is CompositionAction.DROP:
        for tag in hits:
            notes.append(f"composition_dropped: {tag!r}")
        return [tag for tag in tags if tag not in hits]
    return unreachable(action)
