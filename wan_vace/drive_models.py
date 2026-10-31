"""Point ComfyUI at the Drive folder. This module does not download."""

from __future__ import annotations

import shutil
from pathlib import Path

from wan_vace.paths import CLIP_NAME, LINK_DIRS, UNET_FP16, UNET_FP8, VAE_NAME


class DriveModelsError(Exception):
    """The Drive models folder cannot be linked as it is."""


_WEIGHT_BYTES = 1_000_000


def _has_weights(path: Path) -> bool:
    return any(item.is_file() and item.stat().st_size > _WEIGHT_BYTES for item in path.rglob("*"))


def link_comfy_models(comfy_models: Path, drive_models: Path) -> list[str]:
    """Symlink each Comfy model folder that already exists on Drive."""
    source_root = Path(drive_models)
    dest_root = Path(comfy_models)
    if not source_root.is_dir():
        raise DriveModelsError(f"Drive の models が無い: {source_root}")
    dest_root.mkdir(parents=True, exist_ok=True)
    linked: list[str] = []
    for name in LINK_DIRS:
        source = source_root / name
        if not source.is_dir():
            continue
        dest = dest_root / name
        if dest.is_symlink():
            if dest.resolve() != source.resolve():
                dest.unlink()
                dest.symlink_to(source, target_is_directory=True)
        elif dest.exists():
            if _has_weights(dest):
                raise DriveModelsError(f"ローカルの {name} に重みがあるので差し替えない")
            shutil.rmtree(dest)
            dest.symlink_to(source, target_is_directory=True)
        else:
            dest.symlink_to(source, target_is_directory=True)
        linked.append(name)
    if "diffusion_models" not in linked or "text_encoders" not in linked or "vae" not in linked:
        raise DriveModelsError("Drive に diffusion_models / text_encoders / vae が無い。先に CPU ノートを実行する。")
    return linked


def require_wan(drive_models: Path, unet_name: str) -> None:
    root = Path(drive_models)
    needed = {
        "diffusion_models/" + unet_name: root / "diffusion_models" / unet_name,
        "text_encoders/" + CLIP_NAME: root / "text_encoders" / CLIP_NAME,
        "vae/" + VAE_NAME: root / "vae" / VAE_NAME,
    }
    if unet_name not in (UNET_FP16, UNET_FP8):
        raise DriveModelsError(f"unet は {UNET_FP16} か {UNET_FP8}")
    missing = [label for label, path in needed.items() if not path.is_file()]
    if missing:
        raise DriveModelsError("Drive に無い: " + ", ".join(missing) + "。CPU ノートで落とす。実行中は落とさない。")


def present_filenames(drive_models: Path) -> set[str]:
    root = Path(drive_models)
    names: set[str] = set()
    for folder in ("loras", "upscale_models", "diffusion_models", "vae", "text_encoders"):
        directory = root / folder
        if not directory.is_dir():
            continue
        for path in directory.iterdir():
            if path.is_file():
                names.add(path.name)
    return names
