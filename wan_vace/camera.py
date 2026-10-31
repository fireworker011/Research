"""Camera math for tests and the prompt builder.

The Comfy node package imports torch. This module loads the same file by path
so a machine without torch can still build prompts and draw guides.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from wan_vace.controls import CameraVector

_PATH = Path(__file__).resolve().parent / "custom_nodes" / "vace_control" / "camera_math.py"
_SPEC = importlib.util.spec_from_file_location("wan_vace_camera_math", _PATH)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"camera math missing: {_PATH}")
_MODULE = importlib.util.module_from_spec(_SPEC)
sys.modules["wan_vace_camera_math"] = _MODULE
_SPEC.loader.exec_module(_MODULE)

CameraSpec = _MODULE.CameraSpec
apply_camera = _MODULE.apply_camera
merge_pose_depth = _MODULE.merge_pose_depth

__all__ = ["CameraSpec", "apply_camera", "merge_pose_depth", "spec_from_vector"]


def spec_from_vector(camera: CameraVector, face_protect: float = 0.0) -> CameraSpec:
    tx, ty, tz = camera.translate
    rx, ry, rz = camera.rotate
    return CameraSpec(
        tx=tx,
        ty=ty,
        tz=tz,
        rx=rx,
        ry=ry,
        rz=rz,
        shake_x=camera.shake.amp_x,
        shake_y=camera.shake.amp_y,
        seed=camera.shake.seed,
        irregular=camera.shake.irregular,
        face_protect=face_protect,
    )
