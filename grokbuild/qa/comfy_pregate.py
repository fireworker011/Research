"""Gate one freshly generated sample before it is kept.

The 1.0x and 1.5x age checks both have to clear 21, and inspector 3 has to
accept the skeleton, fingers, and limbs. A failure asks for another sample.
An age failure asks for a new seed. An anatomy-only failure asks for OpenPose
and Depth together. This module does not call ComfyUI and does not read pixels.
"""

from __future__ import annotations

import math
import sys
from dataclasses import dataclass
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from grokbuild.qa.age_gate import judge
from grokbuild.qa.codes import AGE_BELOW, AGE_OK, ANATOMY, BAD_IMAGE, REASON_RETRY_CAP
from grokbuild.qa.inspectors import MAX_FIX_COUNT
from grokbuild.qa.inspectors import inspector_3
from grokbuild.qa.records import ImageRead

ACTION_ACCEPT = 0
ACTION_SEED = 1
ACTION_CONTROLNET = 2
ACTION_HANDOFF = 3
LITERAL_MIN_AGE = 21.0


@dataclass(frozen=True, slots=True)
class PregateDecision:
    passed: int
    action: int
    openpose: int
    depth: int
    reason: int
    fixes_used: int


def gate_generated_image(
    image: ImageRead,
    *,
    fixes_used: int,
    pose_locked: bool,
) -> PregateDecision:
    if not isinstance(image, ImageRead):
        return _decision(ACTION_HANDOFF, BAD_IMAGE, 0)
    if type(fixes_used) is not int or type(pose_locked) is not bool:
        return _decision(ACTION_HANDOFF, REASON_RETRY_CAP, 0)
    if fixes_used < 0 or fixes_used > MAX_FIX_COUNT:
        stored = fixes_used if fixes_used > 0 else 0
        return _decision(ACTION_HANDOFF, REASON_RETRY_CAP, stored)
    age = judge(image)
    literal_fail = _literal_under_21(image)
    anatomy_ok = inspector_3(image.anatomy)
    age_ok = age.code == AGE_OK and not literal_fail
    if age_ok and anatomy_ok:
        return _decision(ACTION_ACCEPT, AGE_OK, fixes_used)
    if age.code != AGE_OK:
        reason = age.code
    elif literal_fail:
        reason = AGE_BELOW
    else:
        reason = ANATOMY
    if fixes_used >= MAX_FIX_COUNT:
        return _decision(ACTION_HANDOFF, reason, fixes_used)
    if not age_ok:
        return _decision(ACTION_SEED, reason, fixes_used)
    if pose_locked:
        return _decision(ACTION_SEED, ANATOMY, fixes_used)
    return _decision(ACTION_CONTROLNET, ANATOMY, fixes_used)


def _literal_under_21(image: ImageRead) -> bool:
    if len(image.crop_1_0) == 0 or len(image.crop_1_0) != len(image.crop_1_5):
        return True
    for face in (*image.crop_1_0, *image.crop_1_5):
        age = face.age_years
        if age is None or isinstance(age, bool) or not isinstance(age, (int, float)):
            return True
        number = float(age)
        if not math.isfinite(number) or number < LITERAL_MIN_AGE:
            return True
    return False


def _decision(action: int, reason: int, fixes_used: int) -> PregateDecision:
    if action == ACTION_ACCEPT:
        return PregateDecision(1, ACTION_ACCEPT, 0, 0, reason, fixes_used)
    if action == ACTION_CONTROLNET:
        return PregateDecision(0, ACTION_CONTROLNET, 1, 1, reason, fixes_used)
    if action == ACTION_SEED:
        return PregateDecision(0, ACTION_SEED, 0, 0, reason, fixes_used)
    return PregateDecision(0, ACTION_HANDOFF, 0, 0, reason, fixes_used)
