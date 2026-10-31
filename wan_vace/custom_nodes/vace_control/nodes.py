"""ComfyUI nodes that merge OpenPose and depth, then apply the camera vector."""

from __future__ import annotations

import numpy as np
import torch
from PIL import Image

from .camera_math import CameraSpec, apply_camera, merge_pose_depth


def _to_images(batch: torch.Tensor) -> list[Image.Image]:
    array = batch.detach().cpu().clamp(0, 1).numpy()
    frames = (array * 255.0).round().astype(np.uint8)
    return [Image.fromarray(frame, "RGB") for frame in frames]


def _fit(image: Image.Image, width: int, height: int, pose: bool) -> Image.Image:
    resample = Image.Resampling.NEAREST if pose else Image.Resampling.BILINEAR
    return image.convert("RGB").resize((width, height), resample)


def _repeat(images: list[Image.Image], length: int) -> list[Image.Image]:
    if not images:
        raise ValueError("制御フレームが空")
    if len(images) >= length:
        return images[:length]
    return images + [images[-1]] * (length - len(images))


class VaceControlSource:
    """Pick prerendered guides or preprocessor output without running both."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "source": (["prerendered", "preprocess"],),
                "pose_prerendered": ("IMAGE",),
                "depth_prerendered": ("IMAGE",),
                "pose_preprocessed": ("IMAGE", {"lazy": True}),
                "depth_preprocessed": ("IMAGE", {"lazy": True}),
            }
        }

    RETURN_TYPES = ("IMAGE", "IMAGE")
    RETURN_NAMES = ("pose", "depth")
    FUNCTION = "select"
    CATEGORY = "wan_vace"

    def check_lazy_status(
        self,
        source,
        pose_prerendered,
        depth_prerendered,
        pose_preprocessed=None,
        depth_preprocessed=None,
    ):
        del pose_prerendered, depth_prerendered
        if source != "preprocess":
            return []
        needed = []
        if pose_preprocessed is None:
            needed.append("pose_preprocessed")
        if depth_preprocessed is None:
            needed.append("depth_preprocessed")
        return needed

    def select(
        self,
        source,
        pose_prerendered,
        depth_prerendered,
        pose_preprocessed=None,
        depth_preprocessed=None,
    ):
        if source == "preprocess":
            if pose_preprocessed is None or depth_preprocessed is None:
                raise ValueError("preprocess を選んだが OpenPose / Depth が無い")
            return pose_preprocessed, depth_preprocessed
        return pose_prerendered, depth_prerendered


class VacePoseDepthCamera:
    """Merge pose and depth, then apply translate / rotate / shake."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "pose": ("IMAGE",),
                "depth": ("IMAGE",),
                "width": ("INT", {"default": 576, "min": 16, "max": 4096, "step": 16}),
                "height": ("INT", {"default": 1024, "min": 16, "max": 4096, "step": 16}),
                "length": ("INT", {"default": 81, "min": 1, "max": 4096, "step": 4}),
                "tx": ("FLOAT", {"default": 0.0, "min": -4.0, "max": 4.0, "step": 0.001}),
                "ty": ("FLOAT", {"default": 0.0, "min": -4.0, "max": 4.0, "step": 0.001}),
                "tz": ("FLOAT", {"default": 0.0, "min": -4.0, "max": 4.0, "step": 0.001}),
                "rx": ("FLOAT", {"default": 0.0, "min": -180.0, "max": 180.0, "step": 0.1}),
                "ry": ("FLOAT", {"default": 0.0, "min": -180.0, "max": 180.0, "step": 0.1}),
                "rz": ("FLOAT", {"default": 0.0, "min": -180.0, "max": 180.0, "step": 0.1}),
                "shake_x": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 64.0, "step": 0.1}),
                "shake_y": ("FLOAT", {"default": 2.0, "min": 0.0, "max": 64.0, "step": 0.1}),
                "shake_seed": ("INT", {"default": 1, "min": 0, "max": 2**31 - 1}),
                "irregular": ("BOOLEAN", {"default": True}),
                "face_protect": ("FLOAT", {"default": 0.0, "min": 0.0, "max": 1.0, "step": 0.01}),
            }
        }

    RETURN_TYPES = ("IMAGE", "MASK")
    RETURN_NAMES = ("control_video", "control_mask")
    FUNCTION = "build"
    CATEGORY = "wan_vace"

    def build(
        self,
        pose,
        depth,
        width,
        height,
        length,
        tx,
        ty,
        tz,
        rx,
        ry,
        rz,
        shake_x,
        shake_y,
        shake_seed,
        irregular,
        face_protect,
    ):
        pose_frames = _repeat([_fit(frame, width, height, True) for frame in _to_images(pose)], length)
        depth_frames = _repeat([_fit(frame, width, height, False) for frame in _to_images(depth)], length)
        merged = [merge_pose_depth(item, depth_frames[index]) for index, item in enumerate(pose_frames)]
        spec = CameraSpec(
            tx=float(tx),
            ty=float(ty),
            tz=float(tz),
            rx=float(rx),
            ry=float(ry),
            rz=float(rz),
            shake_x=float(shake_x),
            shake_y=float(shake_y),
            seed=int(shake_seed),
            irregular=bool(irregular),
            face_protect=float(face_protect),
        )
        warped, masks = apply_camera(merged, spec)
        video = torch.from_numpy(
            np.stack([np.asarray(frame, dtype=np.float32) / 255.0 for frame in warped])
        )
        mask = torch.from_numpy(
            np.stack([np.asarray(frame.convert("L"), dtype=np.float32) / 255.0 for frame in masks])
        )
        return video, mask


NODE_CLASS_MAPPINGS = {
    "VaceControlSource": VaceControlSource,
    "VacePoseDepthCamera": VacePoseDepthCamera,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "VaceControlSource": "VACE Control Source",
    "VacePoseDepthCamera": "VACE Pose Depth Camera",
}
