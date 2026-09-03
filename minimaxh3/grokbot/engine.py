#!/usr/bin/env python3
"""Grokbot: Drive inbox → Colab MiniMax H3 (T2V / I2VA / R2V) → download → stop.

One-shot (cron / Cursor Automation): process matching-mode inbox, idle exit 0.
Watch: keep polling. Humans do not re-prompt after the one-time start.
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve()
ROOTS = [HERE.parents[1], HERE.parents[2] / "colab", HERE.parents[1].parent / "colab"]
for p in ROOTS:
    if p.is_dir():
        sys.path.insert(0, str(p))

from h3_colab_cli import exec_file, mount_drive, orchestrate_commands, start_session, stop_session  # noqa: E402
from h3_i2v_job import (  # noqa: E402
    DEFAULT_IMAGINE_PROMPT,
    DRIVE_ROOT_DEFAULT,
    GROKBOT_DURATION_S,
    adopt_orphan_prompts,
    adopt_orphan_r2v_folders,
    adopt_orphan_stills,
    ensure_drive_tree,
    load_job,
    move_job,
    next_ready_job,
    normalize_mode,
    resolve_job_image,
    resolve_job_video,
    save_job,
    set_status,
    stage_motion,
    stage_picture1,
    validate_job,
)
from h3_imagine import enhance_still  # noqa: E402
from h3_motion_graphics import resolve_motion_prompt, validate_motion_ad_prompt  # noqa: E402
from h3_r2v_core import finalize_prompt  # noqa: E402
from h3_t2v import resolve_t2v_prompt, validate_t2v_prompt  # noqa: E402

SCRIPTS = {
    "t2v": "h3_t2v_colab_main.py",
    "i2v": "h3_i2v_colab_main.py",
    "r2v": "h3_r2v_colab_main.py",
}


def repo_script(mode: str) -> Path:
    name = SCRIPTS[normalize_mode(mode)]
    for p in (
        HERE.parents[2] / "colab" / name,
        HERE.parents[1] / name,
    ):
        if p.is_file():
            return p
    raise SystemExit(f"{name} が見つからない")


def _queue_status(job: dict, *, via_enhancing: bool = True) -> None:
    if job.get("status") == "ready":
        if via_enhancing:
            set_status(job, "enhancing")
        else:
            set_status(job, "queued")
            return
    if job.get("status") == "enhancing":
        set_status(job, "queued")


def enhance_still_job(folder: Path, job: dict, drive: Path) -> Path:
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
    print("staged still", name)
    return dest


def prepare_t2v(folder: Path, job: dict) -> None:
    prompt = resolve_t2v_prompt(job.get("prompt"))
    errs = validate_t2v_prompt(prompt)
    if errs:
        raise SystemExit(errs)
    job["prompt"] = prompt
    job["duration_s"] = float(job.get("duration_s") or GROKBOT_DURATION_S)
    _queue_status(job, via_enhancing=False)
    save_job(folder, job)
    print("queued t2v", job["id"], "dur", job["duration_s"])


def prepare_i2v(folder: Path, job: dict, drive: Path, *, dry_run: bool) -> None:
    if dry_run:
        src = resolve_job_image(folder, job)
        dest = folder / "picture1.jpg"
        dest.write_bytes(src.read_bytes())
        stage_picture1(folder, dest, job, drive / "input")
    else:
        enhance_still_job(folder, job, drive)
    prompt = resolve_motion_prompt(job.get("prompt"), duration_s=float(job.get("duration_s") or GROKBOT_DURATION_S))
    errs = validate_motion_ad_prompt(prompt)
    if errs:
        raise SystemExit(errs)
    job["duration_s"] = float(job.get("duration_s") or GROKBOT_DURATION_S)
    _queue_status(job)
    save_job(folder, job)
    print("queued i2v", job["id"])


def prepare_r2v(folder: Path, job: dict, drive: Path, *, dry_run: bool) -> None:
    if dry_run:
        src = resolve_job_image(folder, job)
        dest = folder / "picture1.jpg"
        dest.write_bytes(src.read_bytes())
        stage_picture1(folder, dest, job, drive / "input")
    else:
        enhance_still_job(folder, job, drive)
    vid = resolve_job_video(folder, job)
    stage_motion(folder, vid, job, drive / "input")
    still_name = str(job.get("picture1") or "picture1.jpg")
    motion_name = str(job.get("source_video") or "motion.mp4")
    prompt = finalize_prompt(
        str(job.get("prompt") or ""),
        [still_name],
        [motion_name],
        float(job.get("duration_s") or GROKBOT_DURATION_S),
    )
    if any(w in prompt.lower() for w in ("px.a8.net", "a8mat=", "稼げる", "月収", "年収")):
        raise SystemExit("forbidden string in R2V prompt")
    job["prompt"] = prompt
    job["duration_s"] = float(job.get("duration_s") or GROKBOT_DURATION_S)
    _queue_status(job)
    save_job(folder, job)
    print("queued r2v", job["id"], "dur", job["duration_s"])


def adopt_for_mode(drive: Path, mode: str) -> None:
    if mode == "t2v":
        adopt_orphan_prompts(drive)
    elif mode == "r2v":
        adopt_orphan_r2v_folders(drive)
    else:
        adopt_orphan_stills(drive)


def process_one(args: argparse.Namespace, drive: Path) -> str:
    """Return idle | done. Empty inbox for this mode is success."""
    mode = normalize_mode(args.mode)
    adopt_for_mode(drive, mode)
    folder = Path(args.job) if args.job else next_ready_job(drive, mode=mode)
    if folder is None:
        print("idle: inbox empty")
        return "idle"
    job = load_job(folder)
    job_mode = normalize_mode(job.get("mode"))
    if job_mode != mode:
        raise SystemExit(f"job mode {job_mode} != {mode}")
    errs = validate_job(job, folder=folder)
    if errs:
        raise SystemExit(errs)

    if not args.colab_only:
        if mode == "t2v":
            prepare_t2v(folder, job)
        elif mode == "r2v":
            prepare_r2v(folder, job, drive, dry_run=bool(args.dry_run))
        else:
            prepare_i2v(folder, job, drive, dry_run=bool(args.dry_run))
        folder = move_job(folder, "queued", drive)
        job = load_job(folder)

    if args.imagine_only:
        print("imagine-only done", folder)
        return "done"

    script = repo_script(mode)
    os.environ["H3_DRIVE_ROOT"] = str(drive)
    os.environ["H3_JOB_ID"] = str(job.get("id") or folder.name)
    os.environ["H3_JOB_MODE"] = mode
    if args.dry_run:
        os.environ["H3_DRY_RUN"] = "1"
        print("dry-run colab commands:")
        for cmd in orchestrate_commands(script, gpu=args.gpu, name=args.session):
            print("colab", " ".join(cmd))
        return "done"

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
    return "done"


def run(argv: list[str] | None = None, *, default_mode: str = "i2v", default_session: str | None = None) -> int:
    mode0 = normalize_mode(default_mode)
    p = argparse.ArgumentParser(description=f"Grokbot H3 {mode0}: Colab → download → stop")
    p.add_argument("--drive", default=os.environ.get("H3_DRIVE_ROOT") or DRIVE_ROOT_DEFAULT)
    p.add_argument("--job", default="", help="job folder; default = oldest ready of this mode")
    p.add_argument("--mode", default=mode0, choices=["t2v", "i2v", "r2v"])
    p.add_argument("--gpu", default=os.environ.get("H3_COLAB_GPU") or "A100")
    p.add_argument("--session", default=default_session or f"h3-{mode0}")
    p.add_argument("--out", default="", help="local mp4 download path")
    p.add_argument("--imagine-only", action="store_true")
    p.add_argument("--colab-only", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--keep-runtime", action="store_true")
    p.add_argument("--watch", action="store_true", help="poll inbox forever; do not ask the human again")
    p.add_argument("--interval", type=int, default=int(os.environ.get("H3_WATCH_INTERVAL") or 120))
    p.add_argument("--max-jobs", type=int, default=0, help="test/watch cap; 0 = unlimited")
    args = p.parse_args(argv)
    args.mode = normalize_mode(args.mode)
    if not args.session:
        args.session = f"h3-{args.mode}"

    drive = ensure_drive_tree(args.drive)
    processed = 0
    while True:
        status = process_one(args, drive)
        if status == "done":
            processed += 1
            args.job = ""
            if args.max_jobs and processed >= args.max_jobs:
                return 0
            if not args.watch:
                return 0
            continue
        if not args.watch:
            return 0
        time.sleep(max(5, int(args.interval)))
        if args.max_jobs and processed >= args.max_jobs:
            return 0


if __name__ == "__main__":
    raise SystemExit(run())
