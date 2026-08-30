#!/usr/bin/env python3
"""Headless Colab entry: pick a queued H3 I2VA job from Drive and render it."""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

sys.path.insert(0, "/content")
sys.path.insert(0, str(Path(__file__).resolve().parent))

from h3_i2v_job import (
    DRIVE_ROOT_DEFAULT,
    ensure_drive_tree,
    find_jobs,
    load_job,
    move_job,
    resolve_job_image,
    save_job,
    set_status,
    stage_picture1,
    validate_job,
)
from h3_i2v_phone import stage_image_into_input
from h3_i2v_runtime import (
    COMFY_DIR_DEFAULT,
    ensure_comfy,
    fetch_helpers,
    generate_i2va,
    maybe_unassign,
    start_comfy,
)
from h3_motion_graphics import resolve_motion_prompt


def main() -> int:
    drive_root = Path(os.environ.get("H3_DRIVE_ROOT") or DRIVE_ROOT_DEFAULT)
    comfy_dir = Path(os.environ.get("H3_COMFY_DIR") or COMFY_DIR_DEFAULT)
    dry = os.environ.get("H3_DRY_RUN") == "1"
    ensure_drive_tree(drive_root)
    fetch_helpers(Path("/content"), drive_root)
    sys.path.insert(0, "/content")

    job_id = (os.environ.get("H3_JOB_ID") or "").strip()
    folder = None
    if job_id:
        for cand in find_jobs(drive_root):
            if cand.name == job_id or load_job(cand).get("id") == job_id:
                folder = cand
                break
    if folder is None:
        queued = find_jobs(drive_root, status="queued")
        folder = queued[0] if queued else None
    if folder is None:
        raise SystemExit("queued のジョブがありません。Grokbot が Imagine まで済ませて queued にしてください。")

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
    elif job.get("status") != "running":
        raise SystemExit(f"job status must be queued/running, got {job.get('status')}")

    still = resolve_job_image(folder, job)
    name = stage_picture1(folder, still, job, drive_root / "input")
    save_job(folder, job)
    first = stage_image_into_input(drive_root / "input" / name, comfy_dir / "input")

    prompt = resolve_motion_prompt(
        job.get("prompt"),
        duration_s=float(job.get("duration_s") or 10),
        with_last_frame=False,
    )

    if not dry:
        ensure_comfy(comfy_dir, drive_root, drive_root / "models")
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
        folder = move_job(folder, "failed", drive_root)
        maybe_unassign()
        return 1

    job["output_mp4"] = str(dest) if dest else ""
    job["canvas"] = (result.get("plan") or {}).get("label")
    set_status(job, "done")
    save_job(folder, job)
    folder = move_job(folder, "done", drive_root)
    print("DONE", job["id"], job.get("output_mp4"))
    maybe_unassign()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
