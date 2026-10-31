"""One-time downloads onto Drive. The GPU notebook does not call this."""

from __future__ import annotations

import json
import shutil
import urllib.error
import urllib.request
from pathlib import Path

# Byte counts are Content-Length values read from these public URLs.
# A file already that size is left in place. A short file is downloaded again.

FILES = (
    {
        "url": "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors",
        "dest": "text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors",
        "bytes": 6735906897,
    },
    {
        "url": "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/vae/wan_2.1_vae.safetensors",
        "dest": "vae/wan_2.1_vae.safetensors",
        "bytes": 253815318,
    },
    {
        "url": "https://huggingface.co/lightx2v/Wan2.1-Distill-Loras/resolve/main/wan2.1_t2v_14b_lora_rank64_lightx2v_4step.safetensors",
        "dest": "loras/wan2.1_t2v_14b_lora_rank64_lightx2v_4step.safetensors",
        "bytes": 631344264,
    },
    {
        "url": "https://huggingface.co/Kijai/WanVideo_comfy/resolve/main/Wan21_CausVid_14B_T2V_lora_rank32_v2.safetensors",
        "dest": "loras/Wan21_CausVid_14B_T2V_lora_rank32_v2.safetensors",
        "bytes": 204551064,
    },
    {
        "url": "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.1/RealESRGAN_x2plus.pth",
        "dest": "upscale_models/RealESRGAN_x2plus.pth",
        "bytes": 67061725,
    },
    {
        "url": "https://huggingface.co/marduk191/rife/resolve/main/rife47.pth",
        "dest": "rife/rife47.pth",
        "bytes": 21344827,
    },
    {
        "url": "https://huggingface.co/lllyasviel/Annotators/resolve/main/body_pose_model.pth",
        "dest": "annotators/lllyasviel/Annotators/body_pose_model.pth",
        "bytes": 209267595,
    },
    {
        "url": "https://huggingface.co/lllyasviel/Annotators/resolve/main/hand_pose_model.pth",
        "dest": "annotators/lllyasviel/Annotators/hand_pose_model.pth",
        "bytes": 147341049,
    },
    {
        "url": "https://huggingface.co/lllyasviel/Annotators/resolve/main/facenet.pth",
        "dest": "annotators/lllyasviel/Annotators/facenet.pth",
        "bytes": 153718792,
    },
    {
        "url": "https://huggingface.co/spaces/LiheYoung/Depth-Anything/resolve/main/checkpoints/depth_anything_vits14.pth",
        "dest": "annotators/depth_anything_vits14.pth",
        "bytes": 99219880,
    },
    {
        "url": "https://huggingface.co/spacepxl/Wan2.1_VACE_14B_fp8_scaled/resolve/main/wan2.1_vace_14B_fp8_scaled.safetensors",
        "dest": "diffusion_models/wan2.1_vace_14B_fp8_scaled.safetensors",
        "bytes": 17578334838,
    },
    {
        "url": "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/diffusion_models/wan2.1_vace_14B_fp16.safetensors",
        "dest": "diffusion_models/wan2.1_vace_14B_fp16.safetensors",
        "bytes": 34675323640,
    },
)

EMPTY_DIRS = (
    "checkpoints",
    "clip_vision",
    "controlnet",
    "diffusion_models",
    "loras",
    "text_encoders",
    "upscale_models",
    "vae",
    "rife",
    "annotators",
)

_USER_AGENT = "wan-vace-colab"

# The current Depth Anything preprocessor maps the widget name onto this repo
# and reads it from the Hugging Face cache. The .pth next to the annotators
# is the older file layout.
DEPTH_REPO = "LiheYoung/depth-anything-small-hf"
DEPTH_FILES = (
    ("config.json", 954),
    ("preprocessor_config.json", 437),
    ("model.safetensors", 99173660),
)


def _download(url: str, dest: Path, expected: int) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.is_file() and dest.stat().st_size == expected:
        print("skip", dest.name, flush=True)
        return
    partial = dest.with_suffix(dest.suffix + ".part")
    have = partial.stat().st_size if partial.is_file() else 0
    if have > expected:
        partial.unlink()
        have = 0
    headers = {"User-Agent": _USER_AGENT}
    if 0 < have < expected:
        headers["Range"] = f"bytes={have}-"
    request = urllib.request.Request(url, headers=headers)
    try:
        response = urllib.request.urlopen(request, timeout=180)
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"ダウンロード失敗 {dest.name}: HTTP {exc.code}") from exc
    try:
        code = getattr(response, "status", 200)
        mode = "ab" if code == 206 and have else "wb"
        if mode == "wb":
            have = 0
        with response, partial.open(mode) as handle:
            while True:
                chunk = response.read(16 * 1024 * 1024)
                if not chunk:
                    break
                handle.write(chunk)
                have += len(chunk)
                if have == len(chunk) or have % (512 * 1024 * 1024) < len(chunk):
                    print(f"{dest.name} {have}/{expected}", flush=True)
    finally:
        response.close()
    if partial.stat().st_size != expected:
        raise RuntimeError(f"{dest.name} の大きさが違う: {partial.stat().st_size} != {expected}")
    partial.replace(dest)
    print("wrote", dest, flush=True)


def cache_depth_model(drive_models: Path) -> None:
    """Put the small Depth Anything repo in a Drive Hugging Face cache."""
    api = "https://huggingface.co/api/models/" + DEPTH_REPO
    request = urllib.request.Request(api, headers={"User-Agent": _USER_AGENT})
    with urllib.request.urlopen(request, timeout=60) as response:
        meta = json.loads(response.read().decode("utf-8"))
    sha = str(meta["sha"]).strip()
    repo_dir = Path(drive_models) / "hf-home" / "hub" / "models--LiheYoung--depth-anything-small-hf"
    snapshot = repo_dir / "snapshots" / sha
    snapshot.mkdir(parents=True, exist_ok=True)
    (repo_dir / "refs").mkdir(parents=True, exist_ok=True)
    (repo_dir / "refs" / "main").write_text(sha + "\n", encoding="utf-8")
    for name, expected in DEPTH_FILES:
        url = f"https://huggingface.co/{DEPTH_REPO}/resolve/main/{name}"
        _download(url, snapshot / name, expected)


def download_all(drive_models: Path) -> None:
    root = Path(drive_models)
    for name in EMPTY_DIRS:
        (root / name).mkdir(parents=True, exist_ok=True)
    total = sum(item["bytes"] for item in FILES)
    print(f"合計 {total} bytes。既にあるファイルは飛ばす。", flush=True)
    for item in FILES:
        last_error: Exception | None = None
        for _attempt in (1, 2):
            try:
                _download(item["url"], root / item["dest"], int(item["bytes"]))
                last_error = None
                break
            except Exception as exc:
                last_error = exc
                print("retry", item["dest"], exc, flush=True)
        if last_error is not None:
            raise RuntimeError(str(last_error)) from last_error
    cache_depth_model(root)
    note = root / "loras" / "CHARACTER_LORAS.txt"
    note.write_text(
        "\n".join(
            [
                "ここに自分の LoRA を置く。このノートは落とさない。",
                "ログインや支払いが要るファイルは対象外。",
                "sakura_face.safetensors",
                "dreamcore_style.safetensors",
                "生成ノートの strength が 0 のときは読まない。",
                "",
            ]
        ),
        encoding="utf-8",
    )
    refs = root.parent / "refs"
    refs.mkdir(parents=True, exist_ok=True)
    face_note = refs / "PUT_FACE_HERE.txt"
    if not face_note.exists():
        face_note.write_text(
            "sakura-face-crop.jpg をこのフォルダに置く。顔だけの画像。C2 と C4 で使う。\n",
            encoding="utf-8",
        )
    depth_src = root / "annotators" / "depth_anything_vits14.pth"
    depth_copy = root / "annotators" / "LiheYoung" / "Depth-Anything" / "checkpoints" / "depth_anything_vits14.pth"
    if depth_src.is_file() and not depth_copy.is_file():
        depth_copy.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(depth_src, depth_copy)
    print("done", root, flush=True)
