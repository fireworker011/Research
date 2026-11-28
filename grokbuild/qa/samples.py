"""Numeric fixtures. These are not photographs."""

from __future__ import annotations

from grokbuild.qa.crops import build_face
from grokbuild.qa.records import ImageRead, intact_anatomy

PASS_BOX = (200.0, 80.0, 80.0, 80.0)
PASS_WIDTH = 512
PASS_HEIGHT = 768


def passing_image() -> ImageRead:
    return ImageRead(
        width=PASS_WIDTH,
        height=PASS_HEIGHT,
        crop_1_0=(build_face(PASS_BOX, 34, 1.0, PASS_WIDTH, PASS_HEIGHT),),
        crop_1_5=(build_face(PASS_BOX, 36, 1.5, PASS_WIDTH, PASS_HEIGHT),),
        anatomy=intact_anatomy(),
    )
