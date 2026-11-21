"""Decide how a chain treats stages that repaint the face.

A backend that detects the face fails the stage when no face is found. A
rear-view base image has no face to find, so the chain can be told to skip the
face repaint. ``auto`` skips only when the prompt names a rear view and gives
no sign that the face is visible (``looking back`` wins over ``from behind``).
"""

from __future__ import annotations

from scene_trials.errors import unreachable
from scene_trials.project import FacePass
from scene_trials.tags import split_tags, tag_key


def resolve_face_pass(
    setting: FacePass,
    positive: str,
    face_hints: tuple[str, ...],
    rear_hints: tuple[str, ...],
) -> tuple[FacePass, str | None]:
    """Return a concrete mode (never AUTO) and, for an automatic skip, the reason."""
    if setting is FacePass.AUTO:
        keys = {tag_key(tag) for tag in split_tags(positive)}
        if any(tag_key(hint) in keys for hint in face_hints):
            return FacePass.REQUIRED, None
        for hint in rear_hints:
            if tag_key(hint) in keys:
                return FacePass.SKIP, f"rear-view word {hint!r} and no face-visible hint"
        return FacePass.REQUIRED, None
    if setting is FacePass.REQUIRED or setting is FacePass.SKIP or setting is FacePass.OPTIONAL:
        return setting, None
    return unreachable(setting)
