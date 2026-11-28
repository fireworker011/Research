"""Ask the real factory, offline, what it would do with each planned job.

Usage: python integration/preflight_routes.py <extensions/sd-diff-set> <project folder> [--trial N]

For every job of one trial this writes a tiny PNG that carries the job's prompt, then runs the
factory's own router and planner in dry-run. It needs no GPU, no weights and no network.
It reports every job where the factory would pick another category than the chain says, plan
other stages than the job asks for, or refuse the prompt.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("factory", type=Path)
    parser.add_argument("project", type=Path)
    parser.add_argument("--trial", type=int, default=1)
    args = parser.parse_args()
    sys.path.insert(0, str(args.factory.resolve()))

    from sd_diff_set.png_text import write_rgb_png
    from sd_diff_set.router import route_file
    from sd_diff_set.service import run_job

    from scene_trials.plan import JobKind, build_plan
    from scene_trials.project import load_project

    plan = build_plan(load_project(args.project))
    jobs = [job for job in plan.jobs if job.trial == args.trial]
    problems = 0
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        weights = root / "weights"
        weights.mkdir()
        for name in ("face_yolov8n.pt", "hand_yolov8n.pt", "foot_yolov8x_v2.pt", "nsfw-anime-medium-x1280.pt"):
            (weights / name).write_bytes(b"")
        with mock.patch.dict(os.environ, {"SD_DIFF_WEIGHTS_DIR": str(weights)}):
            for job in jobs:
                png = root / f"{job.job_id}.png"
                text = "\n".join(
                    [
                        job.positive,
                        f"Negative prompt: {job.negative}",
                        "Steps: 28, Sampler: Euler a, CFG scale: 6, Seed: 1, Size: 64x64, Model: demoMix_v1",
                    ]
                )
                write_rgb_png(png, 64, 64, parameters=text)
                kwargs: dict[str, object] = {}
                if job.face_pass:
                    kwargs["face_pass"] = job.face_pass
                row = route_file(
                    png,
                    preset_dir=args.factory / "presets",
                    output_dir=root / "out",
                    adult_ok=True,
                    dry_run=True,
                    overwrite=True,
                    use_controlnet=False,
                    run_job=run_job,
                    stages=tuple(job.stages) or ("none",),
                    **kwargs,  # type: ignore[arg-type]
                )
                found: list[str] = []
                items: list[dict[str, object]] = []
                manifest = row.get("manifest")
                if manifest:
                    items = json.loads(Path(str(manifest)).read_text(encoding="utf-8")).get("items", [])
                    found = [str(item["variant"]) for item in items]
                issues: list[str] = []
                if row.get("status") in ("refused", "error") and row.get("error_code") != "no_preset":
                    issues.append(f"{row.get('error_code')}: {row.get('error')}")
                if job.kind is JobKind.CHAIN:
                    if row.get("category") != job.category:
                        issues.append(f"factory routes to {row.get('category')!r}, chain says {job.category!r}")
                    if found != list(job.stages):
                        issues.append(f"factory plans {found}, job asks {list(job.stages)}")
                    bad = [str(i["variant"]) for i in items if i.get("status") != "planned"]
                    if bad:
                        issues.append(f"not planned: {bad}")
                elif found:
                    issues.append(f"solo scene would paint {found}")
                label = f"{job.key:<28} -> {str(row.get('category')):<9} {found}"
                print(("ok   " if not issues else "FAIL ") + label)
                for issue in issues:
                    print("       " + issue)
                problems += bool(issues)
    print(f"\n{len(jobs)} jobs, {problems} with problems")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
