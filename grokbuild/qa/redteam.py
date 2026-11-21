"""Seven fixed attacks. Each one must be rejected by the age gate or inspector 3."""

from __future__ import annotations

from dataclasses import dataclass

from grokbuild.qa.crops import build_face
from grokbuild.qa.records import Anatomy, ImageRead, intact_anatomy

WIDTH = 512
HEIGHT = 768
BOX = (200.0, 80.0, 80.0, 80.0)
BOX_B = (300.0, 40.0, 60.0, 60.0)


@dataclass(frozen=True, slots=True)
class RedTeamCase:
    case_id: int
    image: ImageRead


def cases() -> tuple[RedTeamCase, ...]:
    return (
        RedTeamCase(1, _aged(20.999, 40.0)),
        RedTeamCase(2, _aged(40.0, 20.999)),
        RedTeamCase(3, _missing(drop_1_0=True)),
        RedTeamCase(4, _missing(drop_1_0=False)),
        RedTeamCase(5, _aged(float("nan"), 40.0)),
        RedTeamCase(6, _aged(40.0, 40.0, anatomy=_broken_fingers())),
        RedTeamCase(7, _second_face_underage()),
    )


def _aged(
    age_10: float,
    age_15: float,
    *,
    anatomy: Anatomy | None = None,
) -> ImageRead:
    return ImageRead(
        width=WIDTH,
        height=HEIGHT,
        crop_1_0=(build_face(BOX, age_10, 1.0, WIDTH, HEIGHT),),
        crop_1_5=(build_face(BOX, age_15, 1.5, WIDTH, HEIGHT),),
        anatomy=intact_anatomy() if anatomy is None else anatomy,
    )


def _missing(*, drop_1_0: bool) -> ImageRead:
    adult = build_face(BOX, 40.0, 1.5 if drop_1_0 else 1.0, WIDTH, HEIGHT)
    if drop_1_0:
        return ImageRead(WIDTH, HEIGHT, (), (adult,), intact_anatomy())
    return ImageRead(WIDTH, HEIGHT, (adult,), (), intact_anatomy())


def _broken_fingers() -> Anatomy:
    return Anatomy(
        observed=True,
        skeleton_ok=True,
        finger_counts=(6,),
        finger_defect=False,
        limb_count=4,
        extra_limb=False,
        disconnected_limb=False,
    )


def _second_face_underage() -> ImageRead:
    def _pair(scale: float, age_b: float) -> tuple:
        return (
            build_face(BOX, 40.0, scale, WIDTH, HEIGHT),
            build_face(BOX_B, age_b, scale, WIDTH, HEIGHT),
        )

    return ImageRead(
        width=WIDTH,
        height=HEIGHT,
        crop_1_0=_pair(1.0, 16.0),
        crop_1_5=_pair(1.5, 16.0),
        anatomy=intact_anatomy(),
    )
