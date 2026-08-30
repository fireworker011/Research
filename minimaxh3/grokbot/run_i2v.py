#!/usr/bin/env python3
"""Grokbot: Imagine 2.0 quality pass → Colab I2VA → download → stop runtime."""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
ROOTS = [HERE.parents[1], HERE.parents[2] / "colab", HERE.parents[1].parent / "colab"]
for p in ROOTS:
    if p.is_dir():
        sys.path.insert(0, str(p))

from h3_colab_cli import exec_file, mount_drive, start_session, stop_session  # noqa: E402
from h3_i2v_job import (  # noqa: E402
    DEFAULT_IMAGINE_PROMPT,
    DRIVE_ROOT_DEFAULT,
    ensure_drive_tree,
    load_job,
    move_job,
    next_ready_job,
    resolve_job_image,
    save_job,
    set_status,
    stage_picture1,
    validate_job,
)
from h3_imagine import enhance_still  # noqa: E402
from h3_motion_graphics import resolve_motion_prompt, validate_motion_ad_prompt  # noqa: E402


def repo_script() -> Path:
    for p in (
        HERE.parents[2] / "colab" / "h3_i2v_colab_main.py",
        HERE.parents[1] / "h3_i2v_colab_main.py",
    ):
        if p.is_file():
            return p
    raise SystemExit("h3_i2v_colab_main.py が見つからない")


def enhance_job(folder: Path, job: dict, drive: Path) -> Path:
    src = resolve_job_image(folder, job)
    imagine = job.get("imagine") or {}
    dest = folder / "picture1.jpg"
    if imagine.get("enabled") is False or os.environ.get("H3_SKIP_IMAGINE") == "1":
        dest.write_bytes(src.read_bytes())
        print("Imagine skip → copy source")
    else:
        set_status(job, "enhancing")
        save_job(folder, job)
        enhance_still(
            src,
            dest,
            prompt=str(imagine.get("prompt") or DEFAULT_IMAGINE_PROMPT),
            model=str(imagine.get("model") or "grok-imagine-image-2.0"),
            quality=str(imagine.get("quality") or "medium"),
            resolution=str(imagine.get("resolution") or "2k"),
            aspect_ratio=str(imagine.get("aspect_ratio") or "3:4"),
        )
    name = stage_picture1(folder, dest, job, drive / "input")
    prompt = resolve_motion_prompt(job.get("prompt"), duration_s=float(job.get("duration_s") or 10))
    errs = validate_motion_ad_prompt(prompt)
    if errs:
        raise SystemExit(errs)
    set_status(job, "queued")
    save_job(folder, job)
    print("queued", job["id"], name)
    return dest


def run(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Grokbot H3 I2VA: Imagine → Colab → download → stop")
    p.add_argument("--drive", default=os.environ.get("H3_DRIVE_ROOT") or DRIVE_ROOT_DEFAULT)
    p.add_argument("--job", default="", help="job folder; default = oldest ready in inbox")
    p.add_argument("--gpu", default=os.environ.get("H3_COLAB_GPU") or "A100")
    p.add_argument("--session", default="h3-i2v")
    p.add_argument("--out", default="", help="local mp4 download path")
    p.add_argument("--imagine-only", action="store_true")
    p.add_argument("--colab-only", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--keep-runtime", action="store_true")
    args = p.parse_args(argv)

    drive = ensure_drive_tree(args.drive)
    folder = Path(args.job) if args.job else next_ready_job(drive)
    if folder is None:
        raise SystemExit("ready ジョブが inbox にありません。動画エージェントが drop_job してください。")
    job = load_job(folder)
    errs = validate_job(job, folder=folder)
    if errs:
        raise SystemExit(errs)

    if not args.colab_only:
        if args.dry_run:
            src = resolve_job_image(folder, job)
            dest = folder / "picture1.jpg"
            dest.write_bytes(src.read_bytes())
            stage_picture1(folder, dest, job, drive / "input")
            if job.get("status") == "ready":
                set_status(job, "enhancing")
            set_status(job, "queued")
            save_job(folder, job)
        else:
            enhance_job(folder, job, drive)
        folder = move_job(folder, "queued", drive)
        job = load_job(folder)

    if args.imagine_only:
        print("imagine-only done", folder)
        return 0

    script = repo_script()
    os.environ["H3_DRIVE_ROOT"] = str(drive)
    os.environ["H3_JOB_ID"] = str(job.get("id") or folder.name)
    if args.dry_run:
        os.environ["H3_DRY_RUN"] = "1"
        print("dry-run colab commands:")
        from h3_colab_cli import orchestrate_commands

        for cmd in orchestrate_commands(script, gpu=args.gpu, name=args.session):
            print("colab", " ".join(cmd))
        return 0

    try:
        start_session(name=args.session, gpu=args.gpu)
        mount_drive(name=args.session)
        exec_file(script, name=args.session)
    finally:
        if not args.keep_runtime:
            stop_session(name=args.session)

    done = drive / "done" / folder.name
    job_done = load_job(done) if (done / "job.json").is_file() else job
    mp4 = job_done.get("output_mp4") or str(drive / "output" / f"{job_done.get('id')}.mp4")
    local = Path(args.out) if args.out else Path.cwd() / f"{job_done.get('id')}.mp4"
    src_mp4 = Path(mp4)
    if src_mp4.is_file():
        shutil.copy2(src_mp4, local)
        print("downloaded", local)
    else:
        print("Drive 上の mp4 を確認:", mp4)
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
