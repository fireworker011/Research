"""Write factory --jobs JSON for the standing pictures only.

    python tools/standing_jobs.py --scenes pronant_all_scenes.csv --templates pronant_delusion_prompts_full.csv

sora rows are skipped. The default output is
C:\\sd-out\\auto\\scenes\\pronant\\_meta\\sd_diff_set\\standing.json
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from scene_trials.errors import SceneTrialsError  # noqa: E402
from scene_trials.resources import load_loras  # noqa: E402
from scene_trials.standing_jobs import build_standing_jobs, load_standing_settings, write_jobs  # noqa: E402

DEFAULT_OUTPUT = Path(r"C:\sd-out\auto\scenes\pronant\_meta\sd_diff_set\standing.json")
DEFAULT_PROJECT = ROOT / "projects" / "pronant" / "project.yaml"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="立ち絵の行だけを工場の --jobs JSON にする。sora は出さない。")
    parser.add_argument("--scenes", type=Path, required=True, help="pronant_all_scenes.csv")
    parser.add_argument("--templates", type=Path, required=True, help="pronant_delusion_prompts_full.csv")
    parser.add_argument("--project", type=Path, default=DEFAULT_PROJECT, help="project.yaml (generation, size, loras)")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)
    try:
        settings, loras_path = load_standing_settings(args.project)
        jobs, skipped = build_standing_jobs(
            args.scenes,
            args.templates,
            loras=load_loras(loras_path),
            settings=settings,
        )
        write_jobs(args.output, jobs)
    except SceneTrialsError as exc:
        print(f"{exc.code}: {exc.message}", file=sys.stderr)
        return 2
    print(f"{len(jobs)} standing jobs -> {args.output}")
    if skipped:
        print(f"skipped sora: {skipped}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
