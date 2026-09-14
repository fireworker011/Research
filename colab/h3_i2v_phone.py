"""Phone Colab helpers for MiniMax H3 I2VA (one still → video).

I2V only: FL2VA unet + turbo LoRA. No R2V, no Wan, no loca.lt.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable
REPO = "fireworker011/Research"
BRANCH = "cursor/minimax-h3-motion-identity-e959"
DEFAULT_FIRST_IMAGE = "coconala_creator_ref.jpg"
DRIVE_ROOT_DEFAULT = "/content/drive/MyDrive/minimax-h3-comfyui"
COMFY_DIR_DEFAULT = "/content/ComfyUI"
PORT = 8188
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}
HF_COMFY = "https://huggingface.co/Comfy-Org/MiniMax-H3/resolve/main"
TURBO_LORA_NAME = "minimax_h3_fl2v_turbo_4step_v1.0_768p_comfyui_bf16.safetensors"
TURBO_LORA_URL = (
    "https://huggingface.co/lightx2v/Minimax-h3-Turbo/resolve/main/"
    + TURBO_LORA_NAME
)
HELPER_FILES = (
    "colab/h3_r2v_core.py",
    "colab/h3_motion_graphics.py",
    "colab/h3_i2v_phone.py",
)
I2V_WEIGHTS = (
    ("text_encoders/qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors", "text_encoders"),
    ("vae/minimax_h3_video_vae_fp16.safetensors", "vae"),
    ("vae/minimax_h3_audio_vae_fp32.safetensors", "vae"),
    ("diffusion_models/minimax_h3_fl2va_pruned_int8_convrot.safetensors", "diffusion_models"),
)
AUTO_NAMES = frozenset({"", "auto", "latest", "newest", "最新"})


def github_raw(rel: str, *, repo: str = REPO, branch: str = BRANCH) -> str:
    rel = str(rel).lstrip("/")
    return f"https://raw.githubusercontent.com/{repo}/{branch}/{rel}"


BOT_NOTEBOOKS = {
    "t2v": "minimax_h3_t2v_bot.ipynb",
    "i2v": "minimax_h3_i2v_bot.ipynb",
    "r2v": "minimax_h3_r2v_bot.ipynb",
}


def colab_open_url(*, repo: str = REPO, branch: str = BRANCH, path: str = "minimax_h3_i2v_phone.ipynb") -> str:
    return f"https://colab.research.google.com/github/{repo}/blob/{branch}/{path}"


def bot_colab_url(mode: str, *, repo: str = REPO, branch: str = BRANCH) -> str:
    key = str(mode or "i2v").strip().lower()
    aliases = {"i2va": "i2v", "fl2va": "i2v", "text": "t2v", "ref2v": "r2v", "ref2va": "r2v"}
    key = aliases.get(key, key)
    path = BOT_NOTEBOOKS.get(key)
    if not path:
        raise ValueError(f"unknown bot mode: {mode}")
    return colab_open_url(repo=repo, branch=branch, path=path)


def ref_image_url(*, repo: str = REPO, branch: str = BRANCH) -> str:
    return github_raw("minimaxh3/coconala_creator_ref.jpg", repo=repo, branch=branch)


def i2v_download_jobs(drive_models: Path | str) -> list[tuple[str, Path]]:
    root = Path(drive_models)
    jobs = [(f"{HF_COMFY}/{rel}", root / sub / Path(rel).name) for rel, sub in I2V_WEIGHTS]
    jobs.append((TURBO_LORA_URL, root / "loras" / TURBO_LORA_NAME))
    return jobs


def i2v_jobs_are_fl2va_only(jobs: Iterable[tuple[str, Path]]) -> bool:
    blob = " ".join(url.lower() for url, _ in jobs)
    return "fl2va" in blob and "ref2va" not in blob and "ref2v" not in blob


def missing_weight_files(drive_models: Path | str, min_bytes: int = 1_000_000) -> list[str]:
    missing: list[str] = []
    for _url, dest in i2v_download_jobs(drive_models):
        if not dest.is_file() or dest.stat().st_size < min_bytes:
            missing.append(dest.name)
    return missing


def is_auto_image_name(name: str | None) -> bool:
    return (name or "").strip().lower() in AUTO_NAMES


def newest_image(folders: Iterable[Path | str]) -> Path | None:
    hits: list[Path] = []
    for folder in folders:
        root = Path(folder)
        if not root.is_dir():
            continue
        for p in root.iterdir():
            if not p.is_file():
                continue
            if p.name.startswith("."):
                continue
            if p.suffix.lower() in IMAGE_SUFFIXES:
                hits.append(p)
    if not hits:
        return None
    hits.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return hits[0]


def stage_image_into_input(src: Path, input_dir: Path) -> str:
    """Copy into Comfy input/ and return the LoadImage-relative name."""
    input_dir.mkdir(parents=True, exist_ok=True)
    dest = input_dir / src.name
    if src.resolve() != dest.resolve():
        dest.write_bytes(src.read_bytes())
    return dest.name


def collect_output_videos(entry: dict[str, Any] | None, output_root: Path | str) -> list[Path]:
    root = Path(output_root)
    found: list[Path] = []
    seen: set[str] = set()
    for node in ((entry or {}).get("outputs") or {}).values():
        if not isinstance(node, dict):
            continue
        for key in ("videos", "gifs"):
            for item in node.get(key) or []:
                if not isinstance(item, dict):
                    continue
                fn = item.get("filename")
                if not fn:
                    continue
                sub = item.get("subfolder") or ""
                path = (root / sub / fn) if sub else (root / fn)
                key_s = str(path)
                if key_s in seen:
                    continue
                seen.add(key_s)
                found.append(path)
    return found


def newest_mp4(output_root: Path | str) -> Path | None:
    root = Path(output_root)
    if not root.exists():
        return None
    hits = [p for p in root.rglob("*.mp4") if p.is_file()]
    if not hits:
        return None
    hits.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return hits[0]


def default_canvas_for_vram(vram_gib: float) -> tuple[int, int]:
    """Keep 8:9. 1024x1152 OOMs on A100 40GB at 10s I2VA."""
    if vram_gib >= 70:
        return (768, 864)
    if vram_gib >= 32:
        return (768, 864)
    return (512, 576)


def gpu_ok_for_i2v(vram_gib: float) -> bool:
    return vram_gib >= 20
