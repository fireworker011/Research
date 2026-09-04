#!/usr/bin/env python3
"""Video agent helper: drop a ready T2V / I2VA / R2V job into Drive inbox."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
for p in (HERE.parents[1], HERE.parents[2] / "colab"):
    sys.path.insert(0, str(p))

from h3_i2v_job import (  # noqa: E402
    DRIVE_ROOT_DEFAULT,
    GROKBOT_DURATION_S,
    default_job,
    ensure_drive_tree,
    new_job_id,
    normalize_mode,
    save_job,
    validate_job,
)
from h3_motion_graphics import resolve_motion_prompt, validate_motion_ad_prompt  # noqa: E402
from h3_t2v import resolve_t2v_prompt, validate_t2v_prompt  # noqa: E402

ASPECT_CANVAS = {
    "16:9": (1024, 576),
    "9:16": (576, 1024),
    "8:9": (768, 864),
}


def resolve_canvas(mode: str, aspect: str, width: int, height: int) -> tuple[int, int] | None:
    if int(width or 0) > 0 and int(height or 0) > 0:
        return int(width), int(height)
    raw = (aspect or "").strip().replace("：", ":")
    if not raw:
        return None
    if raw not in ASPECT_CANVAS:
        raise SystemExit("aspect must be 16:9, 9:16, or 8:9")
    if mode == "t2v" and raw == "8:9":
        raise SystemExit("T2V canvas is 9:16 or 16:9")
    if mode == "i2v" and raw == "9:16":
        raise SystemExit("I2V canvas is 8:9 (homage) or 16:9 (landscape)")
    return ASPECT_CANVAS[raw]


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Drop an H3 job for Grokbot")
    p.add_argument("--drive", default=None)
    p.add_argument("--mode", default="i2v", choices=["t2v", "i2v", "r2v"])
    p.add_argument("--image", default="", help="draft still (I2V/R2V; before Imagine 2.0)")
    p.add_argument("--video", default="", help="motion reference mp4 (R2V required)")
    p.add_argument("--slug", default="")
    p.add_argument("--prompt-file", default="", help="empty = mode default prompt")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--duration", type=float, default=GROKBOT_DURATION_S)
    p.add_argument("--aspect", default="", help="16:9 | 9:16 | 8:9. empty = mode default")
    p.add_argument("--width", type=int, default=0)
    p.add_argument("--height", type=int, default=0)
    p.add_argument("--no-imagine", action="store_true")
    p.add_argument("--created-by", default="video-agent")
    args = p.parse_args(argv)

    import os

    mode = normalize_mode(args.mode)
    drive = ensure_drive_tree(args.drive or os.environ.get("H3_DRIVE_ROOT") or DRIVE_ROOT_DEFAULT)
    slug = args.slug or {"t2v": "t2v", "r2v": "r2v"}.get(mode, "coconala")
    jid = new_job_id(slug)
    folder = drive / "inbox" / jid
    folder.mkdir(parents=True, exist_ok=False)

    prompt = ""
    if args.prompt_file:
        prompt = Path(args.prompt_file).read_text(encoding="utf-8")
    canvas = resolve_canvas(mode, args.aspect, args.width, args.height)
    landscape = bool(canvas and canvas[0] > canvas[1])

    if mode == "t2v":
        resolved = resolve_t2v_prompt(prompt, landscape=landscape)
        errs = validate_t2v_prompt(resolved)
        if errs:
            raise SystemExit(errs)
        job = default_job(
            id=jid,
            mode="t2v",
            created_by=args.created_by,
            prompt=prompt,
            seed=args.seed,
            duration_s=float(args.duration),
        )
    elif mode == "r2v":
        if not args.image:
            raise SystemExit("R2V needs --image")
        if not args.video:
            raise SystemExit("R2V needs --video")
        src = Path(args.image)
        vid = Path(args.video)
        if not src.is_file():
            raise SystemExit(f"image missing: {src}")
        if not vid.is_file():
            raise SystemExit(f"video missing: {vid}")
        shutil.copy2(src, folder / "source.jpg")
        shutil.copy2(vid, folder / "motion.mp4")
        job = default_job(
            id=jid,
            mode="r2v",
            created_by=args.created_by,
            source_image="source.jpg",
            source_video="motion.mp4",
            prompt=prompt,
            seed=args.seed,
            duration_s=float(args.duration),
        )
        if args.no_imagine:
            job["imagine"]["enabled"] = False
    else:
        if not args.image:
            raise SystemExit("I2V needs --image")
        src = Path(args.image)
        if not src.is_file():
            raise SystemExit(f"image missing: {src}")
        shutil.copy2(src, folder / "source.jpg")
        resolved = resolve_motion_prompt(prompt, duration_s=float(args.duration))
        errs = validate_motion_ad_prompt(resolved)
        if errs:
            raise SystemExit(errs)
        job = default_job(
            id=jid,
            mode="i2v",
            created_by=args.created_by,
            source_image="source.jpg",
            prompt=prompt,
            seed=args.seed,
            duration_s=float(args.duration),
        )
        if args.no_imagine:
            job["imagine"]["enabled"] = False

    if canvas:
        job["width"], job["height"] = canvas

    v = validate_job(job, folder=folder)
    if v:
        raise SystemExit(v)
    save_job(folder, job)
    print(folder)
    print("id", jid)
    print("mode", mode)
    print("canvas", job["width"], "x", job["height"])
    runner = {"t2v": "run_t2v.py", "r2v": "run_r2v.py"}.get(mode, "run_i2v.py")
    print("Grokbot: python minimaxh3/grokbot/" + runner, "--drive", drive)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
