#!/usr/bin/env python3
"""Colab setup for the Wan 2.2 hospital episode. The human runs this. It does not generate video.

Installs ComfyUI, downloads Wan 2.2 fp8 weights and the Wan 2.2 slot LoRAs onto OneDrive,
and links those folders into ComfyUI. Google Drive is not a destination.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

from wan_episode import onedrive_root, wan_weight_jobs

COMFY_DIR_DEFAULT = Path("/content/ComfyUI")
PORT = 8188


def _shown(cmd: list[str]) -> str:
    shown: list[str] = []
    for part in cmd:
        if "token=" in part:
            head, _, _tail = part.partition("token=")
            shown.append(head + "token=(hidden)")
        else:
            shown.append(part)
    return " ".join(shown)


def _sh(cmd: list[str]) -> None:
    print("+", _shown(cmd))
    subprocess.check_call(cmd)


def ensure_comfy(comfy_dir: Path) -> None:
    if not (comfy_dir / "main.py").is_file():
        _sh(["git", "clone", "--depth", "1", "https://github.com/Comfy-Org/ComfyUI.git", str(comfy_dir)])
    req = comfy_dir / "requirements.txt"
    if req.is_file():
        _sh([sys.executable, "-m", "pip", "install", "-q", "-r", str(req)])
    gguf = comfy_dir / "custom_nodes" / "ComfyUI-GGUF"
    if not (gguf / "__init__.py").is_file() and not (gguf / "nodes.py").is_file():
        _sh(["git", "clone", "--depth", "1", "https://github.com/city96/ComfyUI-GGUF.git", str(gguf)])
    _sh([sys.executable, "-m", "pip", "install", "-q", "gguf"])


def _fetch(url: str, dest: Path, *, required: bool) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.is_file() and dest.stat().st_size > 1_000_000:
        print("skip", dest.name)
        return
    token = (os.environ.get("CIVITAI_API_TOKEN") or "").strip()
    if "civitai.com/api/download" in url and token and "token=" not in url:
        url = url + ("&" if "?" in url else "?") + "token=" + token
    part = dest.with_suffix(dest.suffix + ".part")
    if part.is_file() and part.stat().st_size < 1_000_000:
        part.unlink()
    print("get", dest.name)
    try:
        subprocess.check_call(["wget", "-c", "-O", str(part), url])
    except subprocess.CalledProcessError:
        if part.is_file() and part.stat().st_size < 1_000_000:
            part.unlink()
        if required:
            raise
        print("skip failed", dest.name)
        return
    part.replace(dest)


def link_tree(src: Path, dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    if not src.is_dir():
        return
    for item in src.iterdir():
        if not item.is_file():
            continue
        link = dest / item.name
        if link.exists() or link.is_symlink():
            continue
        link.symlink_to(item)


def download_weights(models_root: Path) -> None:
    for url, rel in wan_weight_jobs():
        _fetch(url, models_root / rel, required=not rel.startswith("loras/"))


def wire_comfy(models_root: Path, comfy_dir: Path, work_root: Path) -> None:
    for sub in ("diffusion_models", "text_encoders", "vae", "loras"):
        link_tree(models_root / sub, comfy_dir / "models" / sub)
    link_tree_dir(work_root / "output", comfy_dir / "output")
    link_tree_dir(work_root / "input", comfy_dir / "input")


def link_tree_dir(src: Path, dest: Path) -> None:
    src.mkdir(parents=True, exist_ok=True)
    if dest.is_symlink() or dest.exists():
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.symlink_to(src, target_is_directory=True)


def comfy_ready(port: int = PORT) -> bool:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/object_info", timeout=3) as resp:
            info = json.loads(resp.read().decode())
        return "WanImageToVideo" in info and "UNETLoader" in info
    except Exception:
        return False


def start_wan_comfy(comfy_dir: Path, *, port: int = PORT) -> None:
    os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")
    if comfy_ready(port):
        print("ComfyUI already up")
        return
    log = Path("/content/wan-comfy.log")
    handle = open(log, "w", buffering=1)
    cmd = [
        sys.executable, "main.py",
        "--listen", "127.0.0.1",
        "--port", str(port),
        "--disable-auto-launch",
        "--enable-cors-header",
    ]
    subprocess.Popen(cmd, cwd=str(comfy_dir), stdout=handle, stderr=subprocess.STDOUT, start_new_session=True)
    for _ in range(90):
        if comfy_ready(port):
            print("ComfyUI up")
            return
        time.sleep(2)
    print(log.read_text(errors="replace")[-4000:])
    raise SystemExit("ComfyUI start failed")


def setup(onedrive: Path | None = None, comfy_dir: Path | None = None) -> Path:
    """Download Wan 2.2 weights onto OneDrive and point ComfyUI at them. Does not render."""
    root = Path(onedrive) if onedrive is not None else onedrive_root()
    comfy = Path(comfy_dir) if comfy_dir is not None else COMFY_DIR_DEFAULT
    models = root / "models"
    ensure_comfy(comfy)
    download_weights(models)
    wire_comfy(models, comfy, root)
    print("weights on", models)
    return models
