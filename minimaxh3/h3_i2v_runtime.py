"""Comfy + I2VA runtime used inside Colab (and DRY_RUN tests)."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
import uuid
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from h3_i2v_phone import (
    BRANCH,
    collect_output_videos,
    i2v_download_jobs,
    missing_weight_files,
    newest_mp4,
)
from h3_motion_graphics import (
    assert_i2va_graph,
    build_i2va_graph,
    i2va_retry_plans,
    prefer_fl2v_lora,
    resolve_motion_prompt,
    validate_motion_ad_prompt,
)
from h3_r2v_core import frames, is_oom_error

PORT = 8188
COMFY_DIR_DEFAULT = "/content/ComfyUI"
RAW = f"https://raw.githubusercontent.com/fireworker011/Research/{BRANCH}"


def sh(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    print("+", " ".join(cmd))
    return subprocess.run(cmd, check=False, text=True)


def fetch_text(url: str, dest: Path) -> bool:
    try:
        urllib.request.urlretrieve(url, dest)
        return dest.is_file() and dest.stat().st_size > 100
    except Exception as e:
        print("fetch fail", url, e)
        return False


def fetch_helpers(dest_dir: Path, drive_root: Path) -> None:
    dest_dir.mkdir(parents=True, exist_ok=True)
    for rel in (
        "colab/h3_r2v_core.py",
        "colab/h3_motion_graphics.py",
        "colab/h3_i2v_phone.py",
        "colab/h3_i2v_job.py",
        "colab/h3_i2v_runtime.py",
    ):
        name = Path(rel).name
        dest = dest_dir / name
        ok = fetch_text(f"{RAW}/{rel}", dest)
        if not ok:
            drive_src = drive_root / name
            if drive_src.is_file():
                shutil.copy2(drive_src, dest)
                ok = True
        if not ok and not dest.is_file():
            raise SystemExit(f"helper missing: {name}")
        if dest.is_file():
            shutil.copy2(dest, drive_root / name)


def link_dir(link_path: Path, target: Path) -> None:
    target.mkdir(parents=True, exist_ok=True)
    if link_path.is_symlink():
        link_path.unlink()
    elif link_path.is_dir():
        bak = Path(str(link_path) + ".local_bak")
        if bak.exists():
            shutil.rmtree(bak, ignore_errors=True)
        if any(link_path.iterdir()):
            link_path.rename(bak)
        else:
            link_path.rmdir()
    elif link_path.exists():
        link_path.unlink()
    link_path.symlink_to(target)
    print("link", link_path, "→", target)


def fetch_weight(url: str, dest: Path, min_bytes: int = 1_000_000) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.is_file() and dest.stat().st_size > min_bytes:
        print(f"skip {dest.name} ({dest.stat().st_size/1e9:.2f} GB)")
        return
    tmp = dest.with_name(dest.name + ".part")
    wget = shutil.which("wget")
    if wget:
        r = sh([wget, "-c", "--show-progress", "-O", str(tmp), url])
        if r.returncode != 0:
            raise SystemExit(f"DL 失敗: {dest.name}")
    else:
        urllib.request.urlretrieve(url, tmp)
    if not tmp.is_file() or tmp.stat().st_size < min_bytes:
        if tmp.exists():
            tmp.unlink()
        raise SystemExit(f"DL 失敗: {dest.name}")
    tmp.replace(dest)


def ensure_comfy(comfy_dir: Path, drive_root: Path, drive_models: Path) -> None:
    if not (comfy_dir / "main.py").is_file():
        sh(["git", "clone", "--depth", "1", "https://github.com/Comfy-Org/ComfyUI.git", str(comfy_dir)])
    req = comfy_dir / "requirements.txt"
    if req.is_file():
        sh([sys.executable, "-m", "pip", "install", "-q", "-r", str(req)])
    models_root = comfy_dir / "models"
    models_root.mkdir(parents=True, exist_ok=True)
    for sub in ["diffusion_models", "text_encoders", "vae", "loras"]:
        link_dir(models_root / sub, drive_models / sub)
    link_dir(comfy_dir / "output", drive_root / "output")
    link_dir(comfy_dir / "input", drive_root / "input")
    for url, dest in i2v_download_jobs(drive_models):
        fetch_weight(url, dest)
    left = missing_weight_files(drive_models)
    if left:
        raise SystemExit("weights missing: " + ", ".join(left))


def comfy_up(port: int = PORT) -> bool:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/object_info", timeout=3) as r:
            obj = json.loads(r.read().decode())
        return "MiniMaxH3ImageToVideo" in obj
    except Exception:
        return False


def start_comfy(comfy_dir: Path, *, port: int = PORT) -> None:
    os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")
    if comfy_up(port):
        print("ComfyUI already up")
        return
    log = Path("/content/comfyui.log")
    log.parent.mkdir(parents=True, exist_ok=True)
    log_f = open(log, "w", buffering=1)
    cmd = [
        sys.executable, "main.py",
        "--listen", "127.0.0.1",
        "--port", str(port),
        "--highvram",
        "--disable-auto-launch",
        "--enable-cors-header",
    ]
    subprocess.Popen(cmd, cwd=str(comfy_dir), stdout=log_f, stderr=subprocess.STDOUT, start_new_session=True)
    for _ in range(90):
        if comfy_up(port):
            print("ComfyUI up")
            return
        time.sleep(2)
    print(log.read_text(errors="replace")[-4000:])
    raise SystemExit("ComfyUI start failed")


def comfy_free(port: int = PORT) -> None:
    try:
        req = urllib.request.Request(
            f"http://127.0.0.1:{port}/free",
            data=json.dumps({"unload_models": True, "free_memory": True}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        urllib.request.urlopen(req, timeout=60).read()
        time.sleep(3)
    except Exception as e:
        print("/free skip", e)


def post_prompt(graph: dict[str, Any], port: int = PORT) -> tuple[dict[str, Any] | None, str | None]:
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}/prompt",
        data=json.dumps({"prompt": graph, "client_id": str(uuid.uuid4())}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            return json.loads(r.read().decode()), None
    except urllib.error.HTTPError as e:
        return None, f"HTTP {e.code}: {e.read().decode('utf-8', errors='replace')[:4000]}"


def wait_prompt(pid: str, port: int = PORT, timeout: int = 3600) -> tuple[bool, Any]:
    t0 = time.time()
    while time.time() - t0 < timeout:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/history/{pid}", timeout=60) as r:
            hist = json.loads(r.read().decode())
        entry = hist.get(pid) or {}
        status = entry.get("status") or {}
        if status.get("completed") or entry.get("outputs"):
            return True, entry
        for m in status.get("messages") or []:
            if isinstance(m, list) and m and m[0] == "execution_error":
                return False, m
        time.sleep(2)
    return False, "timeout"


def generate_i2va(
    *,
    first_image: str,
    prompt: str,
    comfy_dir: Path,
    width: int,
    height: int,
    duration_s: float,
    seed: int,
    steps: int,
    use_lora: bool,
    lora_strength: float,
    filename_prefix: str,
    last_image: str | None = None,
    dry_run: bool = False,
    port: int = PORT,
    object_info: dict[str, Any] | None = None,
) -> dict[str, Any]:
    errs = validate_motion_ad_prompt(prompt, with_last_frame=bool(last_image))
    if errs:
        raise SystemExit(errs)
    obj = object_info or {}
    if not dry_run and not obj:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/object_info", timeout=60) as r:
            obj = json.loads(r.read().decode())
        if "MiniMaxH3ImageToVideo" not in obj:
            raise SystemExit("MiniMaxH3ImageToVideo missing")
    diff = list((comfy_dir / "models/diffusion_models").glob("*fl2va*")) if (comfy_dir / "models/diffusion_models").exists() else []
    unet = diff[0].name if diff else "minimax_h3_fl2va_pruned_int8_convrot.safetensors"
    lora_paths = list((comfy_dir / "models/loras").glob("*.safetensors")) if (comfy_dir / "models/loras").exists() else []
    lora = prefer_fl2v_lora(lora_paths, use_lora)
    plans = i2va_retry_plans(width=int(width), height=int(height))
    last_err: Any = None
    used = None
    ok_entry = None
    out_root = comfy_dir / "output"
    before = newest_mp4(out_root)
    for plan in plans:
        g = build_i2va_graph(
            first_image=first_image,
            last_image=last_image,
            prompt=prompt,
            unet=unet,
            lora_name=lora,
            lora_strength=float(lora_strength),
            width=int(plan["width"]),
            height=int(plan["height"]),
            duration_s=float(duration_s),
            seed=int(seed),
            steps=int(steps),
            filename_prefix=filename_prefix,
            has_lora_loader=("LoraLoaderModelOnly" in obj) or dry_run,
            has_audio_decode=("VAEDecodeAudio" in obj) or dry_run,
        )
        g_errs = assert_i2va_graph(g, expect_last=bool(last_image))
        if g_errs:
            raise SystemExit(g_errs)
        print("try", plan["label"], "frames", frames(duration_s))
        if dry_run:
            return {"dry_run": True, "plan": plan, "graph": g, "videos": []}
        res, err = post_prompt(g, port)
        if err:
            last_err = err
            if is_oom_error(err):
                comfy_free(port)
                continue
            raise SystemExit(err)
        if not (res and "prompt_id" in res):
            raise SystemExit(res)
        ok, payload = wait_prompt(res["prompt_id"], port)
        if ok:
            ok_entry = payload
            used = plan
            break
        last_err = payload
        if is_oom_error(payload):
            comfy_free(port)
            continue
        raise SystemExit(payload)
    else:
        raise SystemExit(last_err or "I2VA failed")
    videos = collect_output_videos(ok_entry, out_root)
    fresh = newest_mp4(out_root)
    if fresh and fresh not in videos and (before is None or fresh != before):
        videos.append(fresh)
    return {"plan": used, "videos": [str(p) for p in videos], "entry": ok_entry}


def maybe_unassign() -> None:
    if os.environ.get("H3_KEEP_RUNTIME") == "1":
        print("keep runtime")
        return
    try:
        from google.colab import runtime

        print("unassign Colab runtime")
        runtime.unassign()
    except Exception as e:
        print("unassign skip", e)
