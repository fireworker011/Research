"""Commands: plan, run, package, slide, cutlist render. Does not generate or post."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from minimaxh3.affi.cutlist import render_cutlist
from minimaxh3.affi.package import write_waiting
from minimaxh3.affi.pipeline import plan_one, run_batch
from minimaxh3.affi.products import PLATFORMS, PRODUCTS
from minimaxh3.affi.slide import SLIDE_DIR, score as slide_score


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="アフィ縦ショートを採点し、使える1件だけ inbox に置く")
    sub = parser.add_subparsers(dest="cmd", required=True)

    plan = sub.add_parser("plan")
    run = sub.add_parser("run")
    package = sub.add_parser("package")
    slide = sub.add_parser("slide")
    slide.add_argument("--id", default="orbis-dot-01")
    cutlist = sub.add_parser("cutlist")
    cut_sub = cutlist.add_subparsers(dest="cut_cmd", required=True)
    render = cut_sub.add_parser("render")
    render.add_argument("--csv", required=True)
    render.add_argument("--out", required=True)
    render.add_argument("--purpose", required=True)
    render.add_argument("--bgm", default="")
    for cmd in (plan, run):
        cmd.add_argument("--product", required=True, choices=[*PRODUCTS, "all"])
        cmd.add_argument("--platform", default="youtube", choices=PLATFORMS)
        cmd.add_argument("--commonalities", default="research/affi/commonalities.yaml")
        cmd.add_argument("--ref-dir", default="")
    run.add_argument("--one", action="store_true")
    run.add_argument("--count", type=int, default=0)
    run.add_argument("--drive", default=os.environ.get("H3_DRIVE_ROOT") or "affi-drive")
    package.add_argument("--drive", required=True)
    package.add_argument("--waiting", default="affi-waiting")
    args = parser.parse_args(argv)

    if args.cmd == "cutlist":
        bgm = Path(args.bgm) if args.bgm else None
        return render_cutlist(Path(args.csv), Path(args.out), args.purpose, bgm)

    if args.cmd == "slide":
        if args.id != "orbis-dot-01":
            print("初稿は orbis-dot-01 だけ", file=sys.stderr)
            return 2
        result = slide_score()
        print(SLIDE_DIR / "draft.md")
        print(SLIDE_DIR / "cuts.csv")
        print(json.dumps(result, ensure_ascii=False))
        print(
            "ffmpeg: python -m minimaxh3.affi cutlist render --csv",
            SLIDE_DIR / "cuts.csv",
            "--out",
            SLIDE_DIR / "orbis-dot-01.mp4",
            "--purpose slide",
        )
        return 0 if result["verdict"] != "捨てる" else 1

    if args.cmd == "plan":
        if args.product == "all":
            print("plan は商品を1つ指定する", file=sys.stderr)
            return 2
        result = plan_one(
            Path(args.commonalities),
            args.product,
            args.platform,
            ref_dir=Path(args.ref_dir) if args.ref_dir else None,
        )
        print(json.dumps(_public(result), ensure_ascii=False, indent=2))
        return 0 if result["verdict"] != "捨てる" else 1

    if args.cmd == "package":
        wrote = write_waiting(Path(args.drive), Path(args.waiting))
        if not wrote:
            print("投稿待ちは作らない。両方の動画が揃っていないか、既にある。")
            return 0
        for path in wrote:
            print(path)
            print(
                "ffmpeg: python -m minimaxh3.affi cutlist render --csv",
                path / "cuts.csv",
                "--out",
                path / "final.mp4",
                "--purpose h3",
            )
        return 0

    count = 1 if args.one else args.count
    if args.one and args.count:
        print("--one と --count は同時に指定しない", file=sys.stderr)
        return 2
    if count < 1:
        print("run は --one か --count N", file=sys.stderr)
        return 2
    result = run_batch(
        Path(args.commonalities),
        args.product,
        args.platform,
        count,
        Path(args.drive),
        ref_dir=Path(args.ref_dir) if args.ref_dir else None,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    verdicts = {item["verdict"] for item in result["plans"]}
    return 1 if verdicts == {"捨てる"} else 0


def _public(result: dict) -> dict:
    return {key: value for key, value in result.items() if key != "script"}


if __name__ == "__main__":
    raise SystemExit(main())
