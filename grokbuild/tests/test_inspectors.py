from dataclasses import replace

from grokbuild.qa.age_gate import judge
from grokbuild.qa.codes import AGE_BELOW
from grokbuild.qa.crops import build_face
from grokbuild.qa.inspectors import inspector_1, inspector_2, inspector_3, inspector_6
from grokbuild.qa.records import Anatomy, ImageRead, intact_anatomy
from grokbuild.qa.samples import PASS_BOX, PASS_HEIGHT, PASS_WIDTH, passing_image


def test_inspector_3_rejects_body_defects_and_unobserved_bodies():
    intact = intact_anatomy()
    assert inspector_3(intact) is True
    hidden = replace(intact, finger_counts=(), limb_count=None)
    assert inspector_3(hidden) is True
    assert inspector_3(replace(intact, observed=False)) is False
    assert inspector_3(replace(intact, skeleton_ok=False)) is False
    assert inspector_3(replace(intact, finger_counts=(6,))) is False
    assert inspector_3(replace(intact, finger_counts=(4,))) is False
    assert inspector_3(replace(intact, finger_defect=True)) is False
    assert inspector_3(replace(intact, limb_count=3)) is False
    assert inspector_3(replace(intact, limb_count=5)) is False
    assert inspector_3(replace(intact, extra_limb=True)) is False
    assert inspector_3(replace(intact, disconnected_limb=True)) is False


def test_inspector_1_does_not_replace_the_age_gate():
    under = ImageRead(
        PASS_WIDTH,
        PASS_HEIGHT,
        (build_face(PASS_BOX, 18, 1.0, PASS_WIDTH, PASS_HEIGHT),),
        (build_face(PASS_BOX, 40, 1.5, PASS_WIDTH, PASS_HEIGHT),),
        intact_anatomy(),
    )
    assert inspector_1(under) is True
    assert judge(under).code == AGE_BELOW
    assert inspector_6(under, fixes_used=0) is False


def test_reused_crop_fails_inspector_2_and_the_closure():
    face = build_face(PASS_BOX, 30, 1.0, PASS_WIDTH, PASS_HEIGHT)
    image = ImageRead(PASS_WIDTH, PASS_HEIGHT, (face,), (face,), intact_anatomy())
    assert inspector_2(image) is False
    assert inspector_6(image, fixes_used=0) is False


def test_closure_accepts_three_fixes_and_rejects_a_fourth():
    image = passing_image()
    assert inspector_6(image, fixes_used=0) is True
    assert inspector_6(image, fixes_used=3) is True
    assert inspector_6(image, fixes_used=4) is False
    assert inspector_6(image, fixes_used=True) is False  # type: ignore[arg-type]


def test_anatomy_type_must_be_the_record():
    assert inspector_3(Anatomy(True, True, (5,), False, 4, False, False)) is True
    assert inspector_3({"observed": True}) is False  # type: ignore[arg-type]
