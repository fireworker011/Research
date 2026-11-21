"""Observation records. Ages are numbers supplied by a caller, not pixels."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FaceRead:
    box: tuple[float, float, float, float]
    crop_box: tuple[float, float, float, float]
    age_years: float | None
    detected: bool


@dataclass(frozen=True, slots=True)
class Anatomy:
    observed: bool
    skeleton_ok: bool
    finger_counts: tuple[int, ...]
    finger_defect: bool
    limb_count: int | None
    extra_limb: bool
    disconnected_limb: bool


@dataclass(frozen=True, slots=True)
class ImageRead:
    width: int
    height: int
    crop_1_0: tuple[FaceRead, ...]
    crop_1_5: tuple[FaceRead, ...]
    anatomy: Anatomy


def intact_anatomy() -> Anatomy:
    return Anatomy(
        observed=True,
        skeleton_ok=True,
        finger_counts=(5, 5),
        finger_defect=False,
        limb_count=4,
        extra_limb=False,
        disconnected_limb=False,
    )
