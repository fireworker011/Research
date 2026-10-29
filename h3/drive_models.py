"""Point ComfyUI at the Drive models folder. This module does not download."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Sequence

# minimax-h3-comfyui/models. Drive folder 1zd4IaS-pw1RJrx4TaGDGgS1ZpBsjeVRK.
DRIVE_MODELS = "/content/drive/MyDrive/minimax-h3-comfyui/models"

# ComfyUI model types that exist under that folder. ``erotic`` is not one of them.
COMFY_DIRS = (
    "checkpoints",
    "clip_vision",
    "controlnet",
    "diffusion_models",
    "loras",
    "text_encoders",
    "vae",
)

# The files that folder actually holds for the official Ref2VA and FL2VA graphs.
# The int8 video VAE is not in the folder. The video VAE there is fp16.
R2V_FILES = (
    "diffusion_models/minimax_h3_ref2va_pruned_int8_convrot.safetensors",
    "text_encoders/qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors",
    "vae/minimax_h3_video_vae_fp16.safetensors",
    "vae/minimax_h3_audio_vae_fp32.safetensors",
)
FL2VA_FILES = (
    "diffusion_models/minimax_h3_fl2va_pruned_int8_convrot.safetensors",
    "text_encoders/qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors",
    "vae/minimax_h3_video_vae_fp16.safetensors",
    "vae/minimax_h3_audio_vae_fp32.safetensors",
)
WEIGHT_BYTES = 1_000_000


class DriveModelsError(Exception):
    """The Drive models folder cannot be linked as it is."""


def files_for(mode: str) -> tuple[str, ...]:
    if mode == "r2v":
        return R2V_FILES
    if mode == "t2v_i2v":
        return FL2VA_FILES
    if mode == "both":
        return tuple(dict.fromkeys(R2V_FILES + FL2VA_FILES))
    raise DriveModelsError("MODE は r2v、t2v_i2v、both")


def missing_files(drive_models: Path, names: Sequence[str]) -> list[str]:
    root = Path(drive_models)
    return [name for name in names if not (root / name).is_file()]


def _has_weights(path: Path) -> bool:
    return any(item.is_file() and item.stat().st_size > WEIGHT_BYTES for item in path.rglob("*"))


def link_comfy_models(comfy_models: Path, drive_models: Path) -> list[str]:
    """Symlink each Comfy model type at the matching Drive directory.

    A local directory that already holds a weight file is left in place.
    """
    source_root = Path(drive_models)
    dest_root = Path(comfy_models)
    if not source_root.is_dir():
        raise DriveModelsError(f"Drive の models が無い: {source_root}")
    dest_root.mkdir(parents=True, exist_ok=True)
    for name in COMFY_DIRS:
        source = source_root / name
        if not source.is_dir():
            raise DriveModelsError(f"Drive に {name} が無い")
        dest = dest_root / name
        if dest.exists() and not dest.is_symlink() and _has_weights(dest):
            raise DriveModelsError(f"ローカルの {name} に重みがあるので差し替えない")
    linked: list[str] = []
    for name in COMFY_DIRS:
        source = source_root / name
        if not source.is_dir():
            raise DriveModelsError(f"Drive に {name} が無い")
        dest = dest_root / name
        if dest.is_symlink():
            if dest.resolve() != source.resolve():
                dest.unlink()
                dest.symlink_to(source, target_is_directory=True)
            linked.append(name)
            continue
        if dest.exists():
            if _has_weights(dest):
                raise DriveModelsError(f"ローカルの {name} に重みがあるので差し替えない")
            shutil.rmtree(dest)
        dest.symlink_to(source, target_is_directory=True)
        linked.append(name)
    return linked


def require_mode(drive_models: Path, mode: str, quant: str = "int8") -> None:
    """Stop when the selected graph's files are not already in the Drive folder."""
    if quant != "int8":
        raise DriveModelsError("Drive にある本体は int8。fp8 は落とさない")
    gone = missing_files(drive_models, files_for(mode))
    if gone:
        raise DriveModelsError("Drive に無い: " + ", ".join(gone))
