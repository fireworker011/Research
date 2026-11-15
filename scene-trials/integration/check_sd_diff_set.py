"""End-to-end check of the sd_diff_set backend against the real factory code.

Usage: python integration/check_sd_diff_set.py <path to extensions/sd-diff-set>

The factory's own Python runs in this process. Only the GPU parts are replaced:
the txt2img poster returns a small PNG, the inpaint host copies its input, and
the YOLO detectors return fixed boxes. Everything else is the factory's real
planner, router, pipeline, executor and cutout. scene-trials then plans, exports,
and collects from the files the factory wrote.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))
FACTORY = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(FACTORY))
sys.path.insert(0, str(HERE))

import fake_gpu  # noqa: E402  (needs the factory on sys.path)

from scene_trials.backends import get_backend  # noqa: E402
from scene_trials.cli import main as scene_main  # noqa: E402
from scene_trials.collector import collect, find_result, find_transparent  # noqa: E402
from scene_trials.layout import Layout  # noqa: E402
from scene_trials.plan import build_plan  # noqa: E402
from scene_trials.project import load_project  # noqa: E402

SCENES = """category,subcategory,pose,diff_stage,positive_prompt,negative_prompt
sprite,idle,standing,01,"solo, 1girl, standing, simple background","low quality"
act,one,pose_a,01,"1girl, 1boy, solo focus, simple background","low quality"
act,two,pose_a,02,"1girl, 1boy, solo focus, simple background","low quality"
act,three,pose_b,01,"1girl, 1boy, from behind, simple background","low quality"
"""
CHAINS = """chains:
  rear_chain:
    category: anal
    base: 4
    route_tags: [anal sex]
    stage_order: [imminent, tip, hilt, creampie, withdrawn]
    scenes: {4: hilt}
    face_pass: skip
  front_chain:
    category: anal
    base: 2
    route_tags: [anal sex]
    stage_order: [imminent, tip, hilt, creampie, withdrawn]
    scenes: {2: hilt, 3: creampie}
"""
PROJECT = """schema: 1
project: itest
paths: {{out_root: out, scenes_csv: scenes.csv, chains: chains.yaml}}
columns: {{section: category, positive: positive_prompt, negative: negative_prompt, id_columns: [pose, diff_stage]}}
trials: {{count: 2, order: trial_major}}
size: {{width: 1024, height: 1344}}
face_visible_hints: [looking at viewer]
safety: {{adult_confirmed_by: tester, adult_confirmed_on: "2026-11-15"}}
backend:
  name: sd_diff_set
  options:
    work_dir: {work}
    factory_dir: {factory}
    factory_face_pass: {face_pass}
    generation: {{sampler_name: Euler a, steps: 28, cfg_scale: 6, model: demoMix_v1}}
"""


def check(condition: bool, message: str) -> None:
    print(("ok   " if condition else "FAIL ") + message)
    if not condition:
        check.failed += 1


check.failed = 0


def main() -> int:
    face_pass_supported = "face_pass" in (FACTORY / "sd_diff_set" / "planner.py").read_text(encoding="utf-8")
    print(f"factory: {FACTORY}  face_pass patch present: {face_pass_supported}")
    keep = os.environ.get("SCENE_TRIALS_ITEST_DIR", "").strip()
    scratch = tempfile.TemporaryDirectory()
    with scratch as tmp:
        root = Path(keep) if keep else Path(tmp)
        root.mkdir(parents=True, exist_ok=True)
        project_dir = root / "project"
        work = root / "work"
        project_dir.mkdir(exist_ok=True)
        (project_dir / "scenes.csv").write_text(SCENES, encoding="utf-8")
        (project_dir / "chains.yaml").write_text(CHAINS, encoding="utf-8")
        (project_dir / "project.yaml").write_text(
            PROJECT.format(work=work.as_posix(), factory=FACTORY.as_posix(), face_pass=str(face_pass_supported).lower()),
            encoding="utf-8",
        )
        if not face_pass_supported:
            print("unpatched factory: the rear chain's face_pass skip must be refused")
            check(scene_main(["export", "--project", str(project_dir)]) == 2, "export refuses face_pass skip")
            (project_dir / "chains.yaml").write_text(CHAINS.replace("    face_pass: skip\n", ""), encoding="utf-8")

        check(scene_main(["export", "--project", str(project_dir)]) == 0, "scene-trials export")
        meta = Layout(load_project(project_dir)).meta()
        batch = meta / "sd_diff_set" / "t1-b1.json"
        jobs = json.loads(batch.read_text(encoding="utf-8"))["jobs"]
        print("factory job keys:", sorted(jobs[0]))
        check(all(job["stages"] for job in jobs), "every factory job carries stages")
        rear = next(job for job in jobs if job["id"].startswith("itest-rear_chain"))
        check(rear["stages"] == ["imminent", "tip", "hilt"], "rear chain asks for the prefix up to hilt")
        solo = next(job for job in jobs if job["id"].startswith("itest-S01"))
        check(solo["stages"] == ["none"], "solo scene asks for no stages")
        if face_pass_supported:
            check(rear.get("face_pass") == "skip", "rear chain carries face_pass skip")
        script = (meta / "sd_diff_set_run.sh").read_text(encoding="utf-8")
        check("--adult-ok" in script and "--jobs" in script and "--run" in script, "run script written")

        face_calls: list[str] = []
        for trial in (1, 2):
            result = fake_gpu.run_batch(FACTORY, work, meta / "sd_diff_set" / f"t{trial}-b1.json")
            print(f"trial {trial} factory jobs:", {row["id"]: row["status"] for row in result["jobs"]})  # type: ignore[union-attr]
            face_calls = result["face_calls"]  # type: ignore[assignment]

        plan = build_plan(load_project(project_dir))
        backend = get_backend(plan.project.backend, project_dir)
        output = backend.produced_files(plan)
        print("backend notes:", output.notes)
        report = collect(plan, output, backend_name=backend.name)
        print("collect counts:", report.counts())
        by = {(r.scene_id, r.trial): r for r in report.results}
        check(all(r.status == "ok" for r in report.results), "every scene-trial is ok")
        layout = Layout(plan.project)
        for scene, trial in (("S02_pose_a_01", 1), ("S03_pose_a_02", 2), ("S01_standing_01", 1), ("S04_pose_b_01", 2)):
            section = plan.scene_by_id()[scene].section
            trial_dir = layout.trial_dir(section, scene, trial)
            check(find_result(trial_dir) is not None, f"{scene} trial {trial} has result")
            check(find_transparent(trial_dir) is not None, f"{scene} trial {trial} has a transparent result")
        solo_stage_files = [
            path
            for folder in (work / "diffs").glob("*/itest-S01_standing_01-t*")
            for path in folder.glob("*.png")
        ]
        check(solo_stage_files == [], "the solo scene produced no stage image (hands and feet live under limbs/)")
        creampie = by[("S03_pose_a_02", 1)]
        check(creampie.stage == "creampie", "S03 is served by stage creampie")
        rear_result = by[("S04_pose_b_01", 1)]
        check(any("face_pass_skipped" in w for w in rear_result.warnings) == face_pass_supported, "rear chain face pass skipped only with the patch")
        rear_calls = [name for name in face_calls if "rear_chain" in name]
        check(bool(rear_calls) != face_pass_supported, "the face detector ignores the rear chain only with the patch")
    print("FAILED" if check.failed else "ALL OK")
    return 1 if check.failed else 0


if __name__ == "__main__":
    sys.exit(main())
