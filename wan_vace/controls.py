"""Read one cut's control JSON. No images are invented from nowhere: the
guide renderer turns these keyframes into frames."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping


class ControlError(ValueError):
    """The control JSON is missing a field the runner needs."""


@dataclass(frozen=True)
class Shake:
    amp_x: float
    amp_y: float
    irregular: bool
    seed: int


@dataclass(frozen=True)
class CameraVector:
    translate: tuple[float, float, float]
    rotate: tuple[float, float, float]
    shake: Shake


@dataclass(frozen=True)
class CutControl:
    cut: str
    source_start: float
    source_end: float
    duration_s: float
    fps: int
    aspect: str
    openpose_keyframes: tuple[Mapping[str, Any], ...]
    focus_sweep: tuple[tuple[float, str], ...]
    camera: CameraVector
    jaw_max_deg: float | None
    fingers_visible: int | None
    raw: Mapping[str, Any]

    def time_at(self, index: int, length: int) -> float:
        if length <= 1:
            return self.source_start
        span = self.source_end - self.source_start
        return self.source_start + (index / (length - 1)) * span


def wan_length(duration_s: float, fps: int) -> int:
    """Nearest Wan frame count (4n+1) for this duration."""
    raw = max(1, int(round(duration_s * fps)))
    steps = max(1, int(round((raw - 1) / 4)))
    return 4 * steps + 1


def _triple(value: Any, label: str) -> tuple[float, float, float]:
    if not isinstance(value, list) or len(value) != 3:
        raise ControlError(f"{label} は3つの数")
    return float(value[0]), float(value[1]), float(value[2])


def load_control(path: Path) -> CutControl:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ControlError(f"{path} がオブジェクトではない")
    for key in ("cut", "source_seconds", "aspect", "fps", "openpose_keyframes", "depth", "camera_vector", "duration_s"):
        if key not in data:
            raise ControlError(f"{path.name} に {key} が無い")
    if data["aspect"] != "9:16":
        raise ControlError(f"{data['cut']} の aspect は 9:16")
    source = data["source_seconds"]
    if not isinstance(source, list) or len(source) != 2:
        raise ControlError(f"{data['cut']} の source_seconds は開始と終了")
    sweep = data["depth"].get("focus_sweep")
    if not isinstance(sweep, list) or not sweep:
        raise ControlError(f"{data['cut']} の focus_sweep が無い")
    focus: list[tuple[float, str]] = []
    for item in sweep:
        if not isinstance(item, list) or len(item) != 2:
            raise ControlError(f"{data['cut']} の focus_sweep の形が違う")
        focus.append((float(item[0]), str(item[1])))
    keys = data["openpose_keyframes"]
    if not isinstance(keys, list) or not keys:
        raise ControlError(f"{data['cut']} の openpose_keyframes が無い")
    camera = data["camera_vector"]
    shake = camera.get("shake") or {}
    amp = shake.get("amp_px") or [0, 0]
    if not isinstance(amp, list) or len(amp) != 2:
        raise ControlError(f"{data['cut']} の amp_px は2つの数")
    fingers = data.get("fingers_visible")
    jaw = data.get("jaw_max_deg")
    return CutControl(
        cut=str(data["cut"]),
        source_start=float(source[0]),
        source_end=float(source[1]),
        duration_s=float(data["duration_s"]),
        fps=int(data["fps"]),
        aspect=str(data["aspect"]),
        openpose_keyframes=tuple(keys),
        focus_sweep=tuple(focus),
        camera=CameraVector(
            translate=_triple(camera.get("translate"), "translate"),
            rotate=_triple(camera.get("rotate"), "rotate"),
            shake=Shake(
                amp_x=float(amp[0]),
                amp_y=float(amp[1]),
                irregular=bool(shake.get("irregular", True)),
                seed=int(shake.get("seed", 0)),
            ),
        ),
        jaw_max_deg=float(jaw) if jaw is not None else None,
        fingers_visible=int(fingers) if fingers is not None else None,
        raw=data,
    )


def control_paths(directory: Path) -> list[Path]:
    paths: list[Path] = []
    for name in ("C1", "C2", "C3", "C4"):
        path = Path(directory) / f"{name}_control.json"
        if not path.is_file():
            raise ControlError(f"制御 JSON が無い: {path}")
        paths.append(path)
    return paths
