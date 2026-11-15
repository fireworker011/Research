"""Lint findings. Errors stop a plan. Warnings are reported."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from scene_trials.tags import split_tags, tag_key


class Level(Enum):
    ERROR = "error"
    WARNING = "warning"


@dataclass(frozen=True)
class LintIssue:
    level: Level
    code: str
    subject: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return {
            "level": self.level.value,
            "code": self.code,
            "subject": self.subject,
            "message": self.message,
        }


def face_hint_issue(
    subject: str, positive: str, hints: tuple[str, ...]
) -> LintIssue | None:
    """Warn when a chain with face-pass stages shows no hint that a face is visible."""
    if not hints:
        return None
    keys = {tag_key(tag) for tag in split_tags(positive)}
    if any(tag_key(hint) in keys for hint in hints):
        return None
    return LintIssue(
        Level.WARNING,
        "face_hint_missing",
        subject,
        "no face-visible hint in the base prompt; a stage that detects the face may stop the chain",
    )
