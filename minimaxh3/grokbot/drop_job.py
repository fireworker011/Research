#!/usr/bin/env python3
"""Video agent helper: drop a ready I2VA job into Drive inbox."""

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
    default_job,
    ensure_drive_tree,
    new_job_id,
    save_job,
    validate_job,
)
from h3_motion_graphics import resolve_motion_prompt, validate_motion_ad_prompt  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Drop an H3 I2VA job for Grokbot")
    p.add_argument("--drive", default=None)
    p.add_argument("--image", required=True, help="draft still (before Imagine 2.0)")
    p.add_argument("--slug", default="coconala")
    p.add_argument("--prompt-file", default="", help="empty = official 10-shot homage prompt")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--no-imagine", action="store_true")
    p.add_argument("--created-by", default="video-agent")
    args = p.parse_args(argv)

    import os

    drive = ensure_drive_tree(args.drive or os.environ.get("H3_DRIVE_ROOT") or DRIVE_ROOT_DEFAULT)
    src = Path(args.image)
    if not src.is_file():
        raise SystemExit(f"image missing: {src}")
    jid = new_job_id(args.slug)
    folder = drive / "inbox" / jid
    folder.mkdir(parents=True, exist_ok=False)
    dest_img = folder / "source.jpg"
    shutil.copy2(src, dest_img)
    prompt = ""
    if args.prompt_file:
        prompt = Path(args.prompt_file).read_text(encoding="utf-8")
    resolved = resolve_motion_prompt(prompt, duration_s=10)
    errs = validate_motion_ad_prompt(resolved)
    if errs:
        raise SystemExit(errs)
    job = default_job(
        id=jid,
        created_by=args.created_by,
        source_image="source.jpg",
        prompt=prompt,
        seed=args.seed,
    )
    if args.no_imagine:
        job["imagine"]["enabled"] = False
    v = validate_job(job, folder=folder)
    if v:
        raise SystemExit(v)
    save_job(folder, job)
    print(folder)
    print("id", jid)
    print("Grokbot: python minimaxh3/grokbot/run_i2v.py --drive", drive)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
