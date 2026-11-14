"""Both the 1.0x crop and the 1.5x crop must estimate age >= 21.

A missing face, a non-finite age, or an age below 21 on either crop is FAIL.
The two ages are not averaged and are not rounded. There is no mosaic bypass.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from grokbuild.qa.codes import (
    AGE_BELOW,
    AGE_OK,
    BAD_IMAGE,
    CROP_MISMATCH,
    FACE_MISSING,
    NON_FINITE_AGE,
)
from grokbuild.qa.crops import boxes_match, expand_box
from grokbuild.qa.records import FaceRead, ImageRead

MIN_AGE = 21.0
SCALE_1_0 = 1.0
SCALE_1_5 = 1.5


@dataclass(frozen=True, slots=True)
class GateResult:
    passed: bool
    code: int


def judge(image: ImageRead) -> GateResult:
    if not isinstance(image, ImageRead):
        return GateResult(False, BAD_IMAGE)
    if type(image.width) is not int or type(image.height) is not int:
        return GateResult(False, BAD_IMAGE)
    if image.width < 1 or image.height < 1:
        return GateResult(False, BAD_IMAGE)
    faces_10 = image.crop_1_0
    faces_15 = image.crop_1_5
    if not isinstance(faces_10, tuple) or not isinstance(faces_15, tuple):
        return GateResult(False, FACE_MISSING)
    if len(faces_10) == 0 or len(faces_10) != len(faces_15):
        return GateResult(False, FACE_MISSING)
    for face_10, face_15 in zip(faces_10, faces_15):
        verdict = _judge_pair(image.width, image.height, face_10, face_15)
        if verdict is not None:
            return verdict
    return GateResult(True, AGE_OK)


def _judge_pair(
    image_w: int,
    image_h: int,
    face_10: FaceRead,
    face_15: FaceRead,
) -> GateResult | None:
    if not isinstance(face_10, FaceRead) or not isinstance(face_15, FaceRead):
        return GateResult(False, FACE_MISSING)
    if face_10.detected is not True or face_15.detected is not True:
        return GateResult(False, FACE_MISSING)
    if not boxes_match(face_10.box, face_15.box):
        return GateResult(False, FACE_MISSING)
    expected_10 = expand_box(face_10.box, SCALE_1_0, image_w, image_h)
    expected_15 = expand_box(face_15.box, SCALE_1_5, image_w, image_h)
    if not boxes_match(face_10.crop_box, expected_10):
        return GateResult(False, CROP_MISMATCH)
    if not boxes_match(face_15.crop_box, expected_15):
        return GateResult(False, CROP_MISMATCH)
    age_10 = _finite_age(face_10.age_years)
    age_15 = _finite_age(face_15.age_years)
    if age_10 is None or age_15 is None:
        return GateResult(False, NON_FINITE_AGE)
    if age_10 < MIN_AGE or age_15 < MIN_AGE:
        return GateResult(False, AGE_BELOW)
    return None


def _finite_age(age: float | None) -> float | None:
    if age is None or isinstance(age, bool) or not isinstance(age, (int, float)):
        return None
    number = float(age)
    if not math.isfinite(number):
        return None
    return number
