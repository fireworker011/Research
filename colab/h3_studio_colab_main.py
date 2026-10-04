#!/usr/bin/env python3
"""Colab entry for one H3 Studio job.

Writes a plan JSON and prints the prompt. Does not start Comfy and does not
call the official Hailuo API. Generation stays with the human.

Env:
  H3_STUDIO_JSON       optional request object (JSON text, or a path to a file)
  H3_STUDIO_JOB        one exclusive job (default text_scene)
  H3_STUDIO_RUNTIME    comfy | api
  H3_STUDIO_HIGH_MEM   1 | 0
  H3_STUDIO_ACTION     one English line; Japanese only inside 「」
  H3_STUDIO_DIALOGUE   optional Japanese line
  H3_STUDIO_HERO_*     hair, color, race, age, height, weight, clothes, place
  H3_STUDIO_ENEMY_*    same fields; blanks stay out of Look
  H3_STUDIO_HERO_SHEET swap requires this picture
  H3_STUDIO_VIDEO      motion source
  H3_STUDIO_FIRST      FL2VA first still
  H3_STUDIO_LAST       FL2VA last still
  H3_STUDIO_FINISH     1 puts the combat finish trigger on the prompt
  H3_STUDIO_DURATION   4 to 5 seconds (default 5). fast_motion uses H3_STUDIO_FAST_SECONDS (6 or 9)
  H3_STUDIO_FAST_SECONDS  6 or 9 for fast_motion
  H3_STUDIO_WITH_ACTION   1 adds Motion Repair V2 at 0.6 on fast_motion
  H3_STUDIO_WITH_COMBAT   1 adds combat at 0.7 on fast_motion (no fight trigger)
  H3_STUDIO_TEMPLATE   buy_before, daily_food, or daily_camera
  H3_STUDIO_PARTS      join clips, comma-separated 6 and 9, sum at least 15
  H3_STUDIO_TURBO      ignored for fight Combat and Swap (forced off). fast_motion forces it on
  H3_STUDIO_PASS_A     two_pass job A
  H3_STUDIO_PASS_B     two_pass job B (Video 1 becomes A's mp4)
  H3_STUDIO_OUT        plan path (default h3_studio_plan.json)
  H3_STUDIO_GENERATE   must stay 0. 1 stops.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from h3_studio import GENERATE_MSG, StudioError, build_plan, format_plan, request_from_env


def main() -> int:
    if os.environ.get("H3_STUDIO_GENERATE") == "1":
        print("STUDIO STOP:", GENERATE_MSG)
        return 1
    dest = Path(os.environ.get("H3_STUDIO_OUT") or "h3_studio_plan.json")
    try:
        plan = build_plan(request_from_env())
    except (StudioError, json.JSONDecodeError, OSError) as exc:
        print("STUDIO STOP:", exc)
        return 1
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("WROTE", dest)
    print(format_plan(plan))
    print(GENERATE_MSG)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
