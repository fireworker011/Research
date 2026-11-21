"""Inspectors 1-4 and 6. Inspector 5 stays with the separate OCR job and is not run here."""

from __future__ import annotations

from grokbuild.qa.age_gate import judge
from grokbuild.qa.codes import AGE_OK
from grokbuild.qa.crops import boxes_match, expand_box
from grokbuild.qa.records import Anatomy, FaceRead, ImageRead

MAX_FIX_COUNT = 3


def inspector_1(image: ImageRead) -> bool:
    pairs = _pairs(image)
    if pairs is None:
        return False
    for face_10, face_15 in pairs:
        if face_10.detected is not True or face_15.detected is not True:
            return False
        if not _box_inside(face_10.box, image.width, image.height):
            return False
        if not _box_inside(face_15.box, image.width, image.height):
            return False
        if not _box_inside(face_10.crop_box, image.width, image.height):
            return False
        if not _box_inside(face_15.crop_box, image.width, image.height):
            return False
    return True


def inspector_2(image: ImageRead) -> bool:
    pairs = _pairs(image)
    if pairs is None:
        return False
    for face_10, face_15 in pairs:
        if not boxes_match(face_10.box, face_15.box):
            return False
        expected_10 = expand_box(face_10.box, 1.0, image.width, image.height)
        expected_15 = expand_box(face_15.box, 1.5, image.width, image.height)
        if not boxes_match(face_10.crop_box, expected_10):
            return False
        if not boxes_match(face_15.crop_box, expected_15):
            return False
    return True


def inspector_3(anatomy: Anatomy) -> bool:
    """Skeleton, finger, and limb defects fail. An unobserved body fails closed."""
    if not isinstance(anatomy, Anatomy):
        return False
    if anatomy.observed is not True or anatomy.skeleton_ok is not True:
        return False
    if anatomy.finger_defect is not False:
        return False
    if anatomy.extra_limb is not False or anatomy.disconnected_limb is not False:
        return False
    if not isinstance(anatomy.finger_counts, tuple):
        return False
    for count in anatomy.finger_counts:
        if type(count) is not int or count != 5:
            return False
    limb = anatomy.limb_count
    if limb is None:
        return True
    return type(limb) is int and limb == 4


def inspector_4(image: ImageRead) -> bool:
    if not isinstance(image, ImageRead):
        return False
    return (
        type(image.width) is int
        and type(image.height) is int
        and image.width >= 1
        and image.height >= 1
    )


def inspector_6(image: ImageRead, *, fixes_used: int) -> bool:
    if type(fixes_used) is not int or fixes_used < 0 or fixes_used > MAX_FIX_COUNT:
        return False
    if not inspector_4(image):
        return False
    if judge(image).code != AGE_OK:
        return False
    if not inspector_1(image) or not inspector_2(image):
        return False
    return inspector_3(image.anatomy)


def _pairs(image: ImageRead) -> tuple[tuple[FaceRead, FaceRead], ...] | None:
    if not inspector_4(image):
        return None
    faces_10 = image.crop_1_0
    faces_15 = image.crop_1_5
    if not isinstance(faces_10, tuple) or not isinstance(faces_15, tuple):
        return None
    if len(faces_10) == 0 or len(faces_10) != len(faces_15):
        return None
    pairs: list[tuple[FaceRead, FaceRead]] = []
    for face_10, face_15 in zip(faces_10, faces_15):
        if not isinstance(face_10, FaceRead) or not isinstance(face_15, FaceRead):
            return None
        pairs.append((face_10, face_15))
    return tuple(pairs)


def _box_inside(
    box: tuple[float, float, float, float],
    image_w: int,
    image_h: int,
) -> bool:
    if not isinstance(box, tuple) or len(box) != 4:
        return False
    x, y, w, h = box
    if any(isinstance(v, bool) or not isinstance(v, (int, float)) for v in (x, y, w, h)):
        return False
    fx, fy, fw, fh = float(x), float(y), float(w), float(h)
    if fw <= 0.0 or fh <= 0.0:
        return False
    if fx < -1e-6 or fy < -1e-6:
        return False
    if fx + fw > float(image_w) + 1e-6:
        return False
    if fy + fh > float(image_h) + 1e-6:
        return False
    return True
