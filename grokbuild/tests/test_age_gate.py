import inspect

from grokbuild.qa.age_gate import MIN_AGE, SCALE_1_0, SCALE_1_5, judge
from grokbuild.qa.codes import AGE_BELOW, AGE_OK, CROP_MISMATCH, FACE_MISSING, NON_FINITE_AGE
from grokbuild.qa.crops import build_face
from grokbuild.qa.records import FaceRead, ImageRead, intact_anatomy
from grokbuild.qa.samples import PASS_BOX, PASS_HEIGHT, PASS_WIDTH, passing_image


def _image(age_10, age_15, *, detected_10=True, detected_15=True) -> ImageRead:
    return ImageRead(
        PASS_WIDTH,
        PASS_HEIGHT,
        (build_face(PASS_BOX, age_10, 1.0, PASS_WIDTH, PASS_HEIGHT, detected=detected_10),),
        (build_face(PASS_BOX, age_15, 1.5, PASS_WIDTH, PASS_HEIGHT, detected=detected_15),),
        intact_anatomy(),
    )


def test_threshold_is_21_on_both_scales():
    assert MIN_AGE == 21.0
    assert (SCALE_1_0, SCALE_1_5) == (1.0, 1.5)
    assert set(inspect.signature(judge).parameters) == {"image"}


def test_exact_21_on_both_crops_passes():
    result = judge(_image(21, 21.0))
    assert result.passed is True
    assert result.code == AGE_OK


def test_adult_ages_pass_without_being_averaged():
    assert judge(passing_image()).code == AGE_OK
    assert judge(_image(10.0, 40.0)).code == AGE_BELOW
    assert judge(_image(40.0, 10.0)).code == AGE_BELOW


def test_either_crop_below_21_fails():
    assert judge(_image(20.999, 40.0)).code == AGE_BELOW
    assert judge(_image(21.0, 20.999)).code == AGE_BELOW
    assert judge(_image(20.5, 30.0)).code == AGE_BELOW


def test_missing_face_fails_even_when_the_other_crop_is_adult():
    assert judge(_image(40.0, 40.0, detected_10=False)).code == FACE_MISSING
    assert judge(_image(40.0, 40.0, detected_15=False)).code == FACE_MISSING
    empty = ImageRead(PASS_WIDTH, PASS_HEIGHT, (), _image(40, 40).crop_1_5, intact_anatomy())
    assert judge(empty).code == FACE_MISSING


def test_non_finite_string_bool_and_none_ages_fail():
    base_10 = build_face(PASS_BOX, 30, 1.0, PASS_WIDTH, PASS_HEIGHT)
    base_15 = build_face(PASS_BOX, 30, 1.5, PASS_WIDTH, PASS_HEIGHT)
    for bad in ("30", True, None, float("nan"), float("inf")):
        image = ImageRead(
            PASS_WIDTH,
            PASS_HEIGHT,
            (base_10,),
            (FaceRead(base_15.box, base_15.crop_box, bad, True),),
            intact_anatomy(),
        )
        result = judge(image)
        assert result.passed is False
        assert result.code == NON_FINITE_AGE


def test_same_crop_submitted_for_both_scales_fails():
    face = build_face(PASS_BOX, 30, 1.0, PASS_WIDTH, PASS_HEIGHT)
    image = ImageRead(PASS_WIDTH, PASS_HEIGHT, (face,), (face,), intact_anatomy())
    assert judge(image).code == CROP_MISMATCH


def test_full_frame_still_checks_both_ages():
    box = (0.0, 0.0, 100.0, 100.0)
    crop = (0.0, 0.0, 100.0, 100.0)
    image = ImageRead(
        100,
        100,
        (FaceRead(box, crop, 30.0, True),),
        (FaceRead(box, crop, 18.0, True),),
        intact_anatomy(),
    )
    assert judge(image).code == AGE_BELOW


def test_second_face_under_21_fails():
    box_b = (300.0, 40.0, 60.0, 60.0)
    image = ImageRead(
        PASS_WIDTH,
        PASS_HEIGHT,
        (
            build_face(PASS_BOX, 40, 1.0, PASS_WIDTH, PASS_HEIGHT),
            build_face(box_b, 16, 1.0, PASS_WIDTH, PASS_HEIGHT),
        ),
        (
            build_face(PASS_BOX, 40, 1.5, PASS_WIDTH, PASS_HEIGHT),
            build_face(box_b, 30, 1.5, PASS_WIDTH, PASS_HEIGHT),
        ),
        intact_anatomy(),
    )
    assert judge(image).code == AGE_BELOW


def test_two_adult_faces_pass():
    box_b = (300.0, 40.0, 60.0, 60.0)
    image = ImageRead(
        PASS_WIDTH,
        PASS_HEIGHT,
        (
            build_face(PASS_BOX, 30, 1.0, PASS_WIDTH, PASS_HEIGHT),
            build_face(box_b, 28, 1.0, PASS_WIDTH, PASS_HEIGHT),
        ),
        (
            build_face(PASS_BOX, 31, 1.5, PASS_WIDTH, PASS_HEIGHT),
            build_face(box_b, 29, 1.5, PASS_WIDTH, PASS_HEIGHT),
        ),
        intact_anatomy(),
    )
    assert judge(image).code == AGE_OK
