#!/usr/bin/env python3
"""Headless Colab entry: pick a queued H3 T2V / I2VA / R2V job from Drive and render it."""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

sys.path.insert(0, "/content")
sys.path.insert(0, str(Path(__file__).resolve().parent))

from h3_i2v_job import (
    DRIVE_ROOT_DEFAULT,
    GROKBOT_DURATION_S,
    adopt_orphan_prompts,
    adopt_orphan_r2v_folders,
    adopt_orphan_stills,
    ensure_drive_tree,
    find_jobs,
    load_job,
    move_job,
    normalize_mode,
    resolve_job_image,
    resolve_job_video,
    save_job,
    set_status,
    stage_motion,
    stage_picture1,
    validate_job,
)
from h3_i2v_phone import stage_image_into_input
from h3_i2v_runtime import (
    COMFY_DIR_DEFAULT,
    ensure_comfy,
    fetch_helpers,
    generate_i2va,
    generate_r2v,
    generate_t2v,
    maybe_unassign,
    start_comfy,
)
from h3_motion_graphics import resolve_motion_prompt
from h3_r2v_core import finalize_prompt
from h3_t2v import resolve_t2v_prompt, validate_t2v_prompt


def _pick_folder(drive_root: Path) -> Path | None:
    job_id = (os.environ.get("H3_JOB_ID") or "").strip()
    folder = None
    if job_id:
        for cand in find_jobs(drive_root):
            if cand.name == job_id or load_job(cand).get("id") == job_id:
                folder = cand
                break
    if folder is None:
        want = (os.environ.get("H3_JOB_MODE") or "").strip()
        queued = find_jobs(drive_root, status="queued")
        if want:
            want = normalize_mode(want)
            queued = [p for p in queued if normalize_mode(load_job(p).get("mode")) == want]
        folder = queued[0] if queued else None
    if folder is None:
        if os.environ.get("H3_BOT_IDLE_OK") == "1":
            return None
        raise SystemExit("queued のジョブがありません。Grokbot が Imagine まで済ませて queued にしてください。")
    return folder


def _queue_ready_without_imagine(folder: Path, job: dict, drive_root: Path, mode: str) -> Path:
    """Colab bot notebook path: no Imagine. Grokbot host still does Imagine before exec."""
    mode = normalize_mode(mode)
    if mode == "t2v":
        landscape = int(job.get("width") or 0) > int(job.get("height") or 0)
        prompt = resolve_t2v_prompt(job.get("prompt"), landscape=landscape)
        errs = validate_t2v_prompt(prompt)
        if errs:
            raise SystemExit(errs)
        job["prompt"] = prompt
    else:
        still = resolve_job_image(folder, job)
        dest = folder / "picture1.jpg"
        dest.write_bytes(still.read_bytes())
        stage_picture1(folder, dest, job, drive_root / "input")
        if mode == "r2v":
            vid = resolve_job_video(folder, job)
            stage_motion(folder, vid, job, drive_root / "input")
            job["prompt"] = finalize_prompt(
                str(job.get("prompt") or ""),
                [str(job.get("picture1") or "picture1.jpg")],
                [str(job.get("source_video") or "motion.mp4")],
                float(job.get("duration_s") or GROKBOT_DURATION_S),
            )
    job["duration_s"] = float(job.get("duration_s") or GROKBOT_DURATION_S)
    if job.get("status") == "ready":
        set_status(job, "queued")
    save_job(folder, job)
    if folder.parent.name != "queued":
        folder = move_job(folder, "queued", drive_root)
    return folder


def bot_prepare(mode: str, drive_root: Path | None = None) -> None:
    mode = normalize_mode(mode)
    os.environ["H3_JOB_MODE"] = mode
    root = Path(drive_root or os.environ.get("H3_DRIVE_ROOT") or DRIVE_ROOT_DEFAULT)
    ensure_drive_tree(root)
    if mode == "t2v":
        adopt_orphan_prompts(root)
    elif mode == "r2v":
        adopt_orphan_r2v_folders(root)
    else:
        adopt_orphan_stills(root)
    for folder in find_jobs(root, status="ready"):
        job = load_job(folder)
        if normalize_mode(job.get("mode")) != mode:
            continue
        _queue_ready_without_imagine(folder, job, root, mode)


def _finish(job: dict, folder: Path, drive_root: Path, result: dict, dry: bool) -> int:
    dest = None
    for v in result.get("videos") or []:
        src = Path(v)
        if src.is_file():
            dest = drive_root / "output" / f"{job['id']}.mp4"
            shutil.copy2(src, dest)
            break
    if dest is None and not dry:
        job["error"] = "mp4 missing"
        set_status(job, "failed")
        save_job(folder, job)
        move_job(folder, "failed", drive_root)
        maybe_unassign()
        return 1
    job["output_mp4"] = str(dest) if dest else ""
    job["canvas"] = (result.get("plan") or {}).get("label")
    set_status(job, "done")
    save_job(folder, job)
    move_job(folder, "done", drive_root)
    print("DONE", job["id"], job.get("mode"), job.get("output_mp4"))
    maybe_unassign()
    return 0


def main() -> int:
    drive_root = Path(os.environ.get("H3_DRIVE_ROOT") or DRIVE_ROOT_DEFAULT)
    comfy_dir = Path(os.environ.get("H3_COMFY_DIR") or COMFY_DIR_DEFAULT)
    dry = os.environ.get("H3_DRY_RUN") == "1"
    ensure_drive_tree(drive_root)
    if not dry:
        fetch_helpers(Path("/content"), drive_root)
        sys.path.insert(0, "/content")

    folder = _pick_folder(drive_root)
    if folder is None:
        print("idle: inbox empty")
        maybe_unassign()
        return 0
    job = load_job(folder)
    errs = validate_job(job, folder=folder)
    if errs:
        job["error"] = "; ".join(errs)
        set_status(job, "failed")
        save_job(folder, job)
        raise SystemExit(errs)

    if job.get("status") == "queued":
        set_status(job, "running")
        save_job(folder, job)
        folder = move_job(folder, "running", drive_root)
        job = load_job(folder)
    elif job.get("status") != "running":
        raise SystemExit(f"job status must be queued/running, got {job.get('status')}")

    mode = normalize_mode(job.get("mode"))

    if mode == "t2v":
        if not dry:
            ensure_comfy(comfy_dir, drive_root, drive_root / "models", need_r2v=False)
            start_comfy(comfy_dir)
        prompt = resolve_t2v_prompt(
            job.get("prompt"),
            landscape=int(job.get("width") or 0) > int(job.get("height") or 0),
        )
        errs = validate_t2v_prompt(prompt)
        if errs:
            raise SystemExit(errs)
        result = generate_t2v(
            prompt=prompt,
            comfy_dir=comfy_dir,
            width=int(job["width"]),
            height=int(job["height"]),
            duration_s=float(job.get("duration_s") or 10),
            seed=int(job.get("seed") or 42),
            steps=int(job.get("steps") or 4),
            use_lora=bool(job.get("use_lora", True)),
            lora_strength=float(job.get("lora_strength") or 1.0),
            filename_prefix=str(job.get("filename_prefix") or f"video/h3_t2v_{job['id']}"),
            dry_run=dry,
        )
        return _finish(job, folder, drive_root, result, dry)

    still = resolve_job_image(folder, job)
    name = stage_picture1(folder, still, job, drive_root / "input")
    save_job(folder, job)
    first = stage_image_into_input(drive_root / "input" / name, comfy_dir / "input")

    if mode == "r2v":
        vid = resolve_job_video(folder, job)
        motion_name = stage_motion(folder, vid, job, drive_root / "input")
        save_job(folder, job)
        motion = stage_image_into_input(drive_root / "input" / motion_name, comfy_dir / "input")
        prompt = finalize_prompt(
            str(job.get("prompt") or ""),
            [first],
            [motion],
            float(job.get("duration_s") or 10),
        )
        if not dry:
            ensure_comfy(comfy_dir, drive_root, drive_root / "models", need_r2v=True)
            start_comfy(comfy_dir)
        result = generate_r2v(
            img_names=[first],
            vid_names=[motion],
            prompt=prompt,
            comfy_dir=comfy_dir,
            width=int(job["width"]),
            height=int(job["height"]),
            duration_s=float(job.get("duration_s") or 10),
            seed=int(job.get("seed") or 42),
            steps=int(job.get("steps") or 4),
            use_lora=bool(job.get("use_lora", True)),
            lora_strength=float(job.get("lora_strength") or 1.0),
            filename_prefix=str(job.get("filename_prefix") or f"video/h3_r2v_{job['id']}"),
            ref_image_size=str(job.get("ref_image_size") or "max"),
            dry_run=dry,
        )
        return _finish(job, folder, drive_root, result, dry)

    prompt = resolve_motion_prompt(
        job.get("prompt"),
        duration_s=float(job.get("duration_s") or 10),
        with_last_frame=False,
    )
    if not dry:
        ensure_comfy(comfy_dir, drive_root, drive_root / "models", need_r2v=False)
        start_comfy(comfy_dir)
    result = generate_i2va(
        first_image=first,
        prompt=prompt,
        comfy_dir=comfy_dir,
        width=int(job["width"]),
        height=int(job["height"]),
        duration_s=float(job["duration_s"]),
        seed=int(job.get("seed") or 42),
        steps=int(job.get("steps") or 4),
        use_lora=bool(job.get("use_lora", True)),
        lora_strength=float(job.get("lora_strength") or 1.0),
        filename_prefix=str(job.get("filename_prefix") or f"video/h3_i2va_{job['id']}"),
        dry_run=dry,
    )
    return _finish(job, folder, drive_root, result, dry)


if __name__ == "__main__":
    raise SystemExit(main())
