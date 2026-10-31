"""Draw OpenPose-style sticks and a depth/focus map from a cut's keyframes.

The control JSON has categories and a focus sweep, not source frames. These
pictures are the control video WanVaceToVideo consumes. A plate can replace
them: the workflow also contains OpenposePreprocessor and DepthAnythingPreprocessor.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

import numpy as np
from PIL import Image, ImageDraw

from wan_vace.controls import CutControl, wan_length

# 10 cm in the control JSON maps to a quarter of the frame width. This is a
# guide scale for the stick figure, not a measured room.
HANDLE_CM = 10.0
HANDLE_FRACTION = 0.25

_BONES = (
    ("ear_l", "head", (255, 0, 255)),
    ("ear_r", "head", (255, 0, 255)),
    ("head", "neck", (255, 255, 0)),
    ("neck", "hip", (255, 0, 0)),
    ("hip", "paw_l", (0, 255, 0)),
    ("hip", "paw_r", (0, 255, 0)),
    ("hip", "tail", (0, 255, 255)),
)

_POSES: dict[str, dict[str, tuple[float, float]]] = {
    "back_to_camera": {
        "head": (0.50, 0.22),
        "neck": (0.50, 0.32),
        "hip": (0.50, 0.58),
        "tail": (0.66, 0.72),
        "paw_l": (0.38, 0.84),
        "paw_r": (0.62, 0.84),
        "ear_l": (0.44, 0.14),
        "ear_r": (0.56, 0.14),
    },
    "face_to_camera": {
        "head": (0.50, 0.36),
        "neck": (0.50, 0.48),
        "hip": (0.50, 0.70),
        "tail": (0.64, 0.78),
        "paw_l": (0.36, 0.90),
        "paw_r": (0.64, 0.90),
        "ear_l": (0.40, 0.26),
        "ear_r": (0.60, 0.26),
    },
    "front": {
        "head": (0.50, 0.34),
        "neck": (0.50, 0.46),
        "hip": (0.50, 0.68),
        "tail": (0.62, 0.76),
        "paw_l": (0.34, 0.88),
        "paw_r": (0.66, 0.88),
        "ear_l": (0.40, 0.24),
        "ear_r": (0.60, 0.24),
    },
}


def _pose_named(kind: str) -> dict[str, tuple[float, float]]:
    if kind == "forepaw_to_mouth":
        pose = dict(_POSES["front"])
        pose["paw_l"] = (0.46, 0.40)
        return pose
    if kind == "paw_returned":
        return dict(_POSES["front"])
    if kind not in _POSES:
        raise ValueError(f"未知のポーズ: {kind}")
    return dict(_POSES[kind])


def _lerp_pose(a: dict[str, tuple[float, float]], b: dict[str, tuple[float, float]], amount: float) -> dict[str, tuple[float, float]]:
    out: dict[str, tuple[float, float]] = {}
    for name in a:
        ax, ay = a[name]
        bx, by = b[name]
        out[name] = (ax + (bx - ax) * amount, ay + (by - ay) * amount)
    return out


def _bracket(keys: list[tuple[float, object]], time_s: float) -> tuple[object, object, float]:
    if time_s <= keys[0][0]:
        return keys[0][1], keys[0][1], 0.0
    if time_s >= keys[-1][0]:
        return keys[-1][1], keys[-1][1], 0.0
    for (left_t, left), (right_t, right) in zip(keys, keys[1:]):
        if left_t <= time_s <= right_t:
            span = right_t - left_t
            amount = 0.0 if span == 0 else (time_s - left_t) / span
            return left, right, amount
    return keys[-1][1], keys[-1][1], 0.0


@dataclass(frozen=True)
class PoseState:
    joints: dict[str, tuple[float, float]]
    jaw_deg: float
    hand_cm: float | None
    fingers: int


def _cat_keys(control: CutControl) -> list[tuple[float, str]]:
    found = []
    for item in control.openpose_keyframes:
        if "cat" in item:
            found.append((float(item["t"]), str(item["cat"])))
    return found


def _jaw_keys(control: CutControl) -> list[tuple[float, float]]:
    found = []
    for item in control.openpose_keyframes:
        if "cat_jaw_deg" in item:
            found.append((float(item["t"]), float(item["cat_jaw_deg"])))
    return found


def _hand_keys(control: CutControl) -> list[tuple[float, float]]:
    found = []
    for item in control.openpose_keyframes:
        if "wrist_to_handle_cm" in item:
            found.append((float(item["t"]), float(item["wrist_to_handle_cm"])))
    return found


def pose_at(control: CutControl, time_s: float) -> PoseState:
    cats = _cat_keys(control)
    if cats:
        left, right, amount = _bracket(cats, time_s)
        joints = _lerp_pose(_pose_named(str(left)), _pose_named(str(right)), amount)
    else:
        joints = dict(_POSES["face_to_camera"])
    jaw = 0.0
    jaws = _jaw_keys(control)
    if jaws:
        left_j, right_j, amount = _bracket(jaws, time_s)
        jaw = float(left_j) + (float(right_j) - float(left_j)) * amount
    hand = None
    hands = _hand_keys(control)
    if hands:
        left_h, right_h, amount = _bracket(hands, time_s)
        hand = float(left_h) + (float(right_h) - float(left_h)) * amount
    fingers = control.fingers_visible if control.fingers_visible is not None else 4
    return PoseState(joints, jaw, hand, fingers)


def _xy(point: tuple[float, float], width: int, height: int) -> tuple[int, int]:
    return int(round(point[0] * (width - 1))), int(round(point[1] * (height - 1)))


def draw_pose(state: PoseState, width: int, height: int) -> Image.Image:
    image = Image.new("RGB", (width, height), (0, 0, 0))
    draw = ImageDraw.Draw(image)
    thickness = max(3, width // 96)
    for start, end, color in _BONES:
        draw.line([_xy(state.joints[start], width, height), _xy(state.joints[end], width, height)], fill=color, width=thickness)
    head = _xy(state.joints["head"], width, height)
    radius = max(4, width // 48)
    draw.ellipse([head[0] - radius, head[1] - radius, head[0] + radius, head[1] + radius], outline=(255, 255, 0), width=thickness)
    gap = int(round(abs(state.jaw_deg) / 45.0 * radius * 2))
    draw.line([head[0] - radius, head[1], head[0] + radius, head[1] + gap], fill=(255, 128, 0), width=thickness)
    if state.hand_cm is not None:
        handle = (0.72, 0.48)
        offset = (state.hand_cm / HANDLE_CM) * HANDLE_FRACTION
        wrist = (handle[0] - offset, handle[1] + 0.02)
        hx, hy = _xy(handle, width, height)
        wx, wy = _xy(wrist, width, height)
        box = max(4, width // 80)
        draw.rectangle([hx - box, hy - box * 2, hx + box, hy + box * 2], outline=(255, 0, 128), width=thickness)
        draw.line([wx, wy, hx, hy], fill=(0, 128, 255), width=thickness)
        for finger in range(state.fingers):
            fan = -0.12 + finger * 0.08
            tip = (wrist[0] - 0.03, wrist[1] + fan)
            draw.line([_xy(wrist, width, height), _xy(tip, width, height)], fill=(255, 255, 255), width=max(2, thickness // 2))
    return image


_FOCUS = {"near": 0.0, "cat": 0.0, "far": 1.0, "handle": 1.0}


def focus_at(control: CutControl, time_s: float) -> tuple[float, str]:
    keys = [(time_s_key, _FOCUS[label]) for time_s_key, label in control.focus_sweep]
    labels = {label for _, label in control.focus_sweep}
    mode = "cat_handle" if labels & {"cat", "handle"} else "near_far"
    left, right, amount = _bracket(keys, time_s)
    return float(left) + (float(right) - float(left)) * amount, mode


def draw_depth(focus: float, mode: str, width: int, height: int) -> Image.Image:
    yy = np.linspace(0.0, 1.0, height, dtype=np.float32)[:, None]
    xx = np.linspace(0.0, 1.0, width, dtype=np.float32)[None, :]
    if mode == "cat_handle":
        cat = np.exp(-(((xx - 0.42) ** 2) / 0.03 + ((yy - 0.58) ** 2) / 0.06))
        handle = np.exp(-(((xx - 0.72) ** 2) / 0.004 + ((yy - 0.48) ** 2) / 0.015))
        field = cat * (1.0 - focus) + handle * focus
    else:
        near = np.clip((yy - 0.40) / 0.60, 0.0, 1.0)
        far = np.clip((0.60 - yy) / 0.60, 0.0, 1.0)
        field = (near * (1.0 - focus) + far * focus) * np.ones((1, width), dtype=np.float32)
    gray = (np.clip(field, 0.0, 1.0) * 255.0).astype(np.uint8)
    rgb = np.stack((gray, gray, gray), axis=2)
    return Image.fromarray(rgb, "RGB")


def write_guides(control: CutControl, pose_dir, depth_dir, width: int, height: int) -> int:
    length = wan_length(control.duration_s, control.fps)
    pose_dir.mkdir(parents=True, exist_ok=True)
    depth_dir.mkdir(parents=True, exist_ok=True)
    base = 1_700_000_000
    for index in range(length):
        time_s = control.time_at(index, length)
        pose = draw_pose(pose_at(control, time_s), width, height)
        focus, mode = focus_at(control, time_s)
        depth = draw_depth(focus, mode, width, height)
        pose_path = pose_dir / f"{index:05d}.png"
        depth_path = depth_dir / f"{index:05d}.png"
        pose.save(pose_path)
        depth.save(depth_path)
        stamp = base + index
        os.utime(pose_path, (stamp, stamp))
        os.utime(depth_path, (stamp, stamp))
    return length
