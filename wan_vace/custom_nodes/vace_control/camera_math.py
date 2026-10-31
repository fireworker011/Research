"""2D camera warp for VACE control frames.

WanVaceToVideo takes one control image sequence. It does not take the
Plücker embedding from WanCameraEmbedding (that belongs to the Fun camera
checkpoint, which this pipeline does not load). Translation, rotation, dolly,
and the handheld shake in the control JSON are applied to the pose and depth
frames before they enter VACE.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from PIL import Image


@dataclass(frozen=True)
class CameraSpec:
    tx: float
    ty: float
    tz: float
    rx: float
    ry: float
    rz: float
    shake_x: float
    shake_y: float
    seed: int
    irregular: bool
    face_protect: float = 0.0


def shake_offset(index: int, spec: CameraSpec) -> tuple[float, float]:
    if spec.shake_x == 0 and spec.shake_y == 0:
        return 0.0, 0.0
    if not spec.irregular:
        return (
            spec.shake_x * math.sin(index * 0.9 + spec.seed),
            spec.shake_y * math.cos(index * 1.1 + spec.seed),
        )
    raw_x = math.sin(spec.seed * 12.9898 + index * 78.233) * 43758.5453
    raw_y = math.sin(spec.seed * 4.1414 + index * 39.346) * 24634.6345
    frac_x = raw_x - math.floor(raw_x)
    frac_y = raw_y - math.floor(raw_y)
    return (frac_x * 2 - 1) * spec.shake_x, (frac_y * 2 - 1) * spec.shake_y


def _affine(
    width: int,
    height: int,
    dx: float,
    dy: float,
    angle_deg: float,
    scale: float,
) -> tuple[float, float, float, float, float, float]:
    """PIL inverse map: an output pixel samples the source at ax+by+c, dx+ey+f."""
    scale = max(0.05, scale)
    cx = (width - 1) / 2
    cy = (height - 1) / 2
    theta = math.radians(-angle_deg)
    cos = math.cos(theta)
    sin = math.sin(theta)
    a = cos / scale
    b = sin / scale
    d = -sin / scale
    e = cos / scale
    c = cx - dx - a * cx - b * cy
    f = cy - dy - d * cx - e * cy
    return a, b, c, d, e, f


def warp_frame(image: Image.Image, dx: float, dy: float, angle_deg: float, scale: float) -> Image.Image:
    coeffs = _affine(image.size[0], image.size[1], dx, dy, angle_deg, scale)
    return image.transform(
        image.size,
        Image.Transform.AFFINE,
        coeffs,
        resample=Image.Resampling.BILINEAR,
        fillcolor=0,
    )


def face_mask(width: int, height: int, protect: float) -> Image.Image:
    """255 keeps the control. protect lowers an upper-center ellipse."""
    if protect <= 0:
        return Image.new("L", (width, height), 255)
    keep = max(0.0, min(1.0, 1.0 - protect))
    level = int(round(keep * 255))
    yy, xx = np.mgrid[0:height, 0:width]
    cx = width * 0.5
    cy = height * 0.32
    rx = max(1.0, width * 0.18)
    ry = max(1.0, height * 0.14)
    inside = ((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2 <= 1.0
    mask = np.full((height, width), 255, dtype=np.uint8)
    mask[inside] = level
    return Image.fromarray(mask, "L")


def merge_pose_depth(pose: Image.Image, depth: Image.Image) -> Image.Image:
    """Pose sticks replace the depth map where the stick is not black."""
    pose_rgb = np.asarray(pose.convert("RGB"), dtype=np.uint8)
    depth_rgb = np.asarray(
        depth.convert("RGB").resize((pose_rgb.shape[1], pose_rgb.shape[0]), Image.Resampling.BILINEAR),
        dtype=np.uint8,
    )
    stick = pose_rgb.sum(axis=2) > 24
    merged = depth_rgb.copy()
    merged[stick] = pose_rgb[stick]
    return Image.fromarray(merged, "RGB")


def apply_camera(frames: list[Image.Image], spec: CameraSpec) -> tuple[list[Image.Image], list[Image.Image]]:
    """Warp each frame. translate/rotate ramp across the cut; shake does not."""
    if not frames:
        return [], []
    count = len(frames)
    width, height = frames[0].size
    mask = face_mask(width, height, spec.face_protect)
    warped: list[Image.Image] = []
    masks: list[Image.Image] = []
    for index, frame in enumerate(frames):
        progress = 0.0 if count == 1 else index / (count - 1)
        sx, sy = shake_offset(index, spec)
        dx = spec.tx * width * progress + spec.ry / 45.0 * width * 0.15 * progress + sx
        dy = spec.ty * height * progress + spec.rx / 45.0 * height * 0.15 * progress + sy
        angle = spec.rz * progress
        scale = 1.0 + spec.tz * progress
        warped.append(warp_frame(frame.convert("RGB"), dx, dy, angle, scale))
        masks.append(mask.copy())
    return warped, masks
