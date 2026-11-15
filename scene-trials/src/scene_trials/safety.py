"""Safety rules that no project file can switch off.

The required negatives and the blocked-word check are fixed in code. A project
may add words. It cannot remove any. The adult confirmation is a human
declaration: this module only checks that the declaration is filled in.
"""

from __future__ import annotations

import re

from scene_trials.errors import SafetyError
from scene_trials.tags import dedupe_tags

REQUIRED_NEGATIVES: tuple[str, ...] = ("child", "loli", "teen")

_BLOCKED_WORDS = frozenset(
    {
        "loli",
        "lolita",
        "lolicon",
        "lori",
        "shota",
        "shotacon",
        "child",
        "children",
        "kid",
        "kids",
        "toddler",
        "infant",
        "preteen",
        "teen",
        "teens",
        "teenage",
        "teenager",
        "underage",
    }
)
_BLOCKED_PHRASES = ("小学生", "幼女", "ロリ", "ショタ", "児童")
_WORD = re.compile(r"[a-z0-9]+")


def find_blocked(positive_prompt: str, extra_words: tuple[str, ...] = ()) -> str | None:
    """Return the first blocked word or phrase in a positive prompt, else None.

    Words match whole tokens, so ``glorious`` is fine and ``lolita`` is not.
    """
    lowered = positive_prompt.casefold()
    blocked = _BLOCKED_WORDS | {word.casefold() for word in extra_words}
    for token in _WORD.findall(lowered):
        if token in blocked:
            return token
    for phrase in _BLOCKED_PHRASES:
        if phrase in positive_prompt:
            return phrase
    return None


def ensure_required_negatives(negative_tags: list[str]) -> list[str]:
    return dedupe_tags([*negative_tags, *REQUIRED_NEGATIVES])


def require_adult_confirmation(confirmed_by: str, confirmed_on: str) -> None:
    if not confirmed_by.strip() or not confirmed_on.strip():
        raise SafetyError(
            "adult_not_confirmed",
            "project.yaml safety.adult_confirmed_by and adult_confirmed_on must be "
            "filled in by a person before any job is exported or run.",
        )
