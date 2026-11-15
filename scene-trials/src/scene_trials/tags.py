"""Prompt tag helpers shared by every module."""

from __future__ import annotations

import re

_OPEN = "({[<"
_CLOSE = ")}]>"
_WEIGHTED = re.compile(r"^\((?P<inner>.+?):[0-9]*\.?[0-9]+\)$")


def split_tags(text: str) -> list[str]:
    """Split on commas that are not inside (), {}, [] or <>."""
    tags: list[str] = []
    depth = 0
    current: list[str] = []
    for char in text:
        if char in _OPEN:
            depth += 1
        elif char in _CLOSE and depth > 0:
            depth -= 1
        if char == "," and depth == 0:
            tags.append("".join(current).strip())
            current = []
        else:
            current.append(char)
    tags.append("".join(current).strip())
    return [tag for tag in tags if tag]


def tag_key(tag: str) -> str:
    """Comparison key: weight wrapper removed, spaces collapsed, case folded."""
    stripped = tag.strip()
    match = _WEIGHTED.match(stripped)
    if match:
        stripped = match.group("inner")
    return " ".join(stripped.split()).casefold()


def dedupe_tags(tags: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for tag in tags:
        key = tag_key(tag)
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(tag.strip())
    return out


def join_tags(tags: list[str]) -> str:
    return ", ".join(dedupe_tags(tags))


def has_tag(tags: list[str], name: str) -> bool:
    wanted = tag_key(name)
    return any(tag_key(tag) == wanted for tag in tags)
