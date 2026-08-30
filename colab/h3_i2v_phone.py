"""Phone Colab helpers for MiniMax H3 I2VA (one still → video).

I2V only: FL2VA unet + turbo LoRA. No R2V, no Wan, no loca.lt.
"""

from __future__ import annotations

import os
import urllib.request
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
    "colab/h3_imagine.py",
    "colab/h3_fal_max.py",
    "colab/h3_i2v_job.py",
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


def colab_open_url(*, repo: str = REPO, branch: str = BRANCH, path: str = "minimax_h3_i2v_phone.ipynb") -> str:
    return f"https://colab.research.google.com/github/{repo}/blob/{branch}/{path}"


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


def resolve_phone_still(drive_root: Path | str, name: str) -> Path:
    """Pick Picture 1 from Drive input/, else the hoodie reference still."""
    root = Path(drive_root)
    inp = root / "input"
    inp.mkdir(parents=True, exist_ok=True)
    raw = (name or "").strip().strip('"').strip("'")
    if is_auto_image_name(raw):
        hit = newest_image([inp])
        if hit:
            return hit
        raw = DEFAULT_FIRST_IMAGE
    if not raw:
        raw = DEFAULT_FIRST_IMAGE
    for cand in (inp / raw, inp / Path(raw).name, Path("/content") / Path(raw).name):
        if cand.is_file():
            return cand
    if Path(raw).name == DEFAULT_FIRST_IMAGE:
        dest = inp / DEFAULT_FIRST_IMAGE
        urllib.request.urlretrieve(ref_image_url(), dest)
        if dest.is_file() and dest.stat().st_size > 1000:
            return dest
    raise FileNotFoundError(
        f"画像が見つかりません: {raw}。スマホの Drive で {inp} に jpg を置くか、FIRST_IMAGE を auto にしてください。"
    )


def _maybe_imagine(src: Path, dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    skip = os.environ.get("H3_SKIP_IMAGINE") == "1"
    from h3_imagine import DEFAULT_MODEL, enhance_still, secret_value
    from h3_i2v_job import DEFAULT_IMAGINE_PROMPT

    if skip or not secret_value("XAI_API_KEY", "GROK_API_KEY"):
        dest.write_bytes(Path(src).read_bytes())
        return dest
    return enhance_still(
        src,
        dest,
        prompt=DEFAULT_IMAGINE_PROMPT,
        model=DEFAULT_MODEL,
        quality="medium",
        resolution="2k",
        aspect_ratio="3:4",
    )


def generate_fal_homage(
    still: Path,
    dest: Path,
    *,
    duration_s: float = 10,
    seed: int = 42,
    prompt: str = "",
    dry_run: bool = False,
    key: str | None = None,
) -> Path:
    from h3_fal_max import generate_i2v
    from h3_motion_graphics import resolve_motion_prompt, validate_motion_ad_prompt

    text = resolve_motion_prompt(prompt, duration_s=float(duration_s))
    errs = validate_motion_ad_prompt(text)
    if errs:
        raise SystemExit(errs)
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dry_run:
        dest.write_bytes(b"dry-run-fal-mp4\n" * 80)
        return dest
    return generate_i2v(
        Path(still),
        dest,
        prompt=text,
        duration_s=int(float(duration_s)),
        seed=int(seed),
        prompt_expansion_mode="disabled",
        key=key,
    )


def run_phone_session(
    drive_root: Path | str,
    *,
    first_image: str = DEFAULT_FIRST_IMAGE,
    duration_s: float = 10,
    seed: int = 42,
    prompt: str = "",
    dry_run: bool = False,
    drain_inbox: bool = True,
    key: str | None = None,
) -> list[Path]:
    """Phone Colab entry: fal H3 Max 10s. No A100. Inbox jpgs if present, else FIRST_IMAGE."""
    from h3_i2v_job import (
        adopt_orphan_stills,
        ensure_drive_tree,
        find_jobs,
        load_job,
        move_job,
        new_job_id,
        resolve_job_image,
        save_job,
        set_status,
        stage_picture1,
    )

    root = ensure_drive_tree(drive_root)
    out_dir = root / "output"
    out_dir.mkdir(parents=True, exist_ok=True)
    rendered: list[Path] = []

    folders: list[Path] = []
    if drain_inbox:
        adopt_orphan_stills(root)
        folders = find_jobs(root, status="ready")

    if folders:
        for folder in folders:
            job = load_job(folder)
            src = resolve_job_image(folder, job)
            pic = folder / "picture1.jpg"
            _maybe_imagine(src, pic)
            stage_picture1(folder, pic, job, root / "input")
            if job.get("status") == "ready":
                set_status(job, "queued")
            set_status(job, "running")
            save_job(folder, job)
            folder = move_job(folder, "running", root)
            still_run = folder / "picture1.jpg"
            if not still_run.is_file():
                still_run = resolve_job_image(folder, job)
            dest = out_dir / f"{job['id']}.mp4"
            try:
                generate_fal_homage(
                    still_run,
                    dest,
                    duration_s=float(job.get("duration_s") or duration_s),
                    seed=int(job.get("seed") or seed),
                    prompt=str(job.get("prompt") or prompt),
                    dry_run=dry_run,
                    key=key,
                )
            except Exception as e:
                job["error"] = str(e)
                set_status(job, "failed")
                save_job(folder, job)
                move_job(folder, "failed", root)
                raise
            job["output_mp4"] = str(dest)
            job["backend"] = "fal-max"
            set_status(job, "done")
            save_job(folder, job)
            move_job(folder, "done", root)
            rendered.append(dest)
        return rendered

    still = resolve_phone_still(root, first_image)
    jid = new_job_id("phone")
    pic = root / "input" / "picture1.jpg"
    _maybe_imagine(still, pic)
    dest = out_dir / f"{jid}.mp4"
    generate_fal_homage(
        pic,
        dest,
        duration_s=duration_s,
        seed=seed,
        prompt=prompt,
        dry_run=dry_run,
        key=key,
    )
    return [dest]
