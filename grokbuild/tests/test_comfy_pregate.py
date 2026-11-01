import inspect
from dataclasses import replace

from grokbuild.qa.codes import AGE_BELOW, AGE_OK, ANATOMY, FACE_MISSING
from grokbuild.qa.comfy_pregate import (
    ACTION_ACCEPT,
    ACTION_CONTROLNET,
    ACTION_HANDOFF,
    ACTION_SEED,
    LITERAL_MIN_AGE,
    gate_generated_image,
)
from grokbuild.qa.crops import build_face
from grokbuild.qa.records import ImageRead, intact_anatomy
from grokbuild.qa.samples import PASS_BOX, PASS_HEIGHT, PASS_WIDTH, passing_image


def _under(age_10=18.0, age_15=40.0) -> ImageRead:
    return ImageRead(
        PASS_WIDTH,
        PASS_HEIGHT,
        (build_face(PASS_BOX, age_10, 1.0, PASS_WIDTH, PASS_HEIGHT),),
        (build_face(PASS_BOX, age_15, 1.5, PASS_WIDTH, PASS_HEIGHT),),
        intact_anatomy(),
    )


def _broken_body() -> ImageRead:
    image = passing_image()
    return replace(image, anatomy=replace(image.anatomy, finger_counts=(6,)))


def test_signature_exposes_no_threshold_or_mosaic_override():
    assert LITERAL_MIN_AGE == 21.0
    assert set(inspect.signature(gate_generated_image).parameters) == {
        "image",
        "fixes_used",
        "pose_locked",
    }


def test_adult_sample_is_accepted():
    decision = gate_generated_image(passing_image(), fixes_used=0, pose_locked=False)
    assert decision.passed == 1
    assert decision.action == ACTION_ACCEPT
    assert decision.openpose == 0 and decision.depth == 0
    assert decision.reason == AGE_OK


def test_exact_21_is_accepted_and_20_999_asks_for_a_new_seed():
    accepted = gate_generated_image(_under(21, 21), fixes_used=0, pose_locked=False)
    assert accepted.action == ACTION_ACCEPT
    rejected = gate_generated_image(_under(20.999, 40), fixes_used=0, pose_locked=False)
    assert rejected.passed == 0
    assert rejected.action == ACTION_SEED
    assert rejected.openpose == 0 and rejected.depth == 0
    assert rejected.reason == AGE_BELOW


def test_missing_face_asks_for_a_seed_not_controlnet():
    image = ImageRead(PASS_WIDTH, PASS_HEIGHT, (), passing_image().crop_1_5, intact_anatomy())
    decision = gate_generated_image(image, fixes_used=1, pose_locked=False)
    assert decision.action == ACTION_SEED
    assert decision.reason == FACE_MISSING
    assert decision.openpose == 0 and decision.depth == 0


def test_anatomy_failure_locks_openpose_and_depth_together():
    decision = gate_generated_image(_broken_body(), fixes_used=0, pose_locked=False)
    assert decision.passed == 0
    assert decision.action == ACTION_CONTROLNET
    assert decision.openpose == 1 and decision.depth == 1
    assert decision.reason == ANATOMY


def test_anatomy_failure_after_pose_lock_changes_the_seed():
    decision = gate_generated_image(_broken_body(), fixes_used=1, pose_locked=True)
    assert decision.action == ACTION_SEED
    assert decision.openpose == 0 and decision.depth == 0


def test_age_and_anatomy_failure_changes_the_seed():
    image = replace(_under(18, 18), anatomy=_broken_body().anatomy)
    decision = gate_generated_image(image, fixes_used=0, pose_locked=False)
    assert decision.action == ACTION_SEED
    assert decision.openpose == 0 and decision.depth == 0


def test_third_failed_fix_hands_off_and_a_good_third_fix_is_kept():
    failed = gate_generated_image(_under(), fixes_used=3, pose_locked=False)
    assert failed.action == ACTION_HANDOFF
    assert failed.passed == 0
    kept = gate_generated_image(passing_image(), fixes_used=3, pose_locked=True)
    assert kept.action == ACTION_ACCEPT
    assert kept.passed == 1


def test_a_fourth_fix_is_refused_even_when_the_sample_is_adult():
    decision = gate_generated_image(passing_image(), fixes_used=4, pose_locked=False)
    assert decision.action == ACTION_HANDOFF
    assert decision.passed == 0


def test_bad_inputs_hand_off():
    assert gate_generated_image(object(), fixes_used=0, pose_locked=False).action == ACTION_HANDOFF  # type: ignore[arg-type]
    assert gate_generated_image(passing_image(), fixes_used=0, pose_locked=1).action == ACTION_HANDOFF  # type: ignore[arg-type]
