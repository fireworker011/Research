"""Parse numeric observation records. Image files are not accepted."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from grokbuild.qa.crops import build_face
from grokbuild.qa.records import Anatomy, FaceRead, ImageRead

IMAGE_SUFFIXES = frozenset({".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif", ".avif"})


@dataclass(frozen=True, slots=True)
class ParsedCase:
    image: ImageRead
    fixes_used: int
    broken: bool


def load_jsonl(path: Path) -> list[ParsedCase]:
    if path.suffix.lower() in IMAGE_SUFFIXES:
        raise ValueError("image input is refused")
    cases: list[ParsedCase] = []
    text = path.read_text(encoding="utf-8")
    for line in text.splitlines():
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            cases.append(broken_case())
            continue
        cases.append(parse_case(obj))
    return cases


def parse_case(obj: object) -> ParsedCase:
    if not isinstance(obj, dict):
        return broken_case()
    try:
        image = _image_from_mapping(obj)
        fixes = obj.get("fixes_used", 0)
        if type(fixes) is not int:
            return broken_case()
        return ParsedCase(image=image, fixes_used=fixes, broken=False)
    except (KeyError, TypeError, ValueError):
        return broken_case()


def broken_case() -> ParsedCase:
    image = ImageRead(
        width=0,
        height=0,
        crop_1_0=(),
        crop_1_5=(),
        anatomy=Anatomy(
            observed=False,
            skeleton_ok=False,
            finger_counts=(),
            finger_defect=True,
            limb_count=None,
            extra_limb=True,
            disconnected_limb=True,
        ),
    )
    return ParsedCase(image=image, fixes_used=0, broken=True)


def _image_from_mapping(obj: dict[str, object]) -> ImageRead:
    width = obj["width"]
    height = obj["height"]
    if type(width) is not int or type(height) is not int:
        raise TypeError("width and height must be ints")
    anatomy = _anatomy(obj["anatomy"])
    crop_1_0 = _faces(obj["crop_1_0"], 1.0, width, height)
    crop_1_5 = _faces(obj["crop_1_5"], 1.5, width, height)
    return ImageRead(
        width=width,
        height=height,
        crop_1_0=crop_1_0,
        crop_1_5=crop_1_5,
        anatomy=anatomy,
    )


def _faces(raw: object, scale: float, width: int, height: int) -> tuple[FaceRead, ...]:
    if not isinstance(raw, list):
        raise TypeError("crop list required")
    faces: list[FaceRead] = []
    for item in raw:
        if not isinstance(item, dict):
            raise TypeError("face object required")
        box = _box(item["box"])
        detected = item["detected"]
        if type(detected) is not bool:
            raise TypeError("detected must be a bool")
        age = item["age_years"]
        if age is not None and (isinstance(age, bool) or not isinstance(age, (int, float))):
            raise TypeError("age must be a number or null")
        faces.append(
            build_face(box, None if age is None else float(age), scale, width, height, detected=detected)
        )
    return tuple(faces)


def _box(raw: object) -> tuple[float, float, float, float]:
    if not isinstance(raw, list) or len(raw) != 4:
        raise TypeError("box must have 4 numbers")
    values: list[float] = []
    for item in raw:
        if isinstance(item, bool) or not isinstance(item, (int, float)):
            raise TypeError("box values must be numbers")
        values.append(float(item))
    x, y, w, h = values
    return (x, y, w, h)


def _anatomy(raw: object) -> Anatomy:
    if not isinstance(raw, dict):
        raise TypeError("anatomy object required")
    observed = raw["observed"]
    skeleton_ok = raw["skeleton_ok"]
    finger_defect = raw["finger_defect"]
    extra_limb = raw["extra_limb"]
    disconnected_limb = raw["disconnected_limb"]
    flags = (observed, skeleton_ok, finger_defect, extra_limb, disconnected_limb)
    if any(type(flag) is not bool for flag in flags):
        raise TypeError("anatomy flags must be bools")
    counts_raw = raw["finger_counts"]
    if not isinstance(counts_raw, list):
        raise TypeError("finger_counts must be a list")
    counts: list[int] = []
    for count in counts_raw:
        if type(count) is not int:
            raise TypeError("finger counts must be ints")
        counts.append(count)
    limb = raw["limb_count"]
    if limb is not None and type(limb) is not int:
        raise TypeError("limb_count must be an int or null")
    return Anatomy(
        observed=observed,
        skeleton_ok=skeleton_ok,
        finger_counts=tuple(counts),
        finger_defect=finger_defect,
        limb_count=limb,
        extra_limb=extra_limb,
        disconnected_limb=disconnected_limb,
    )
