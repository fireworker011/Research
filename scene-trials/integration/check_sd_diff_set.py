"""End-to-end check of the sd_diff_set backend against the real factory code.

Usage: python integration/check_sd_diff_set.py <path to extensions/sd-diff-set>

The factory's own Python runs in this process. Only the GPU parts are replaced:
the txt2img poster returns a small PNG, the inpaint host copies its input, and
the YOLO detectors return fixed boxes. Everything else is the factory's real
planner, router, pipeline, executor and cutout. scene-trials then plans, exports,
and collects from the files the factory wrote.
"""

from __future__ import annotations

import io
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest import mock

from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))
FACTORY = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(FACTORY))

from sd_diff_set.executor import GenerationHost, InpaintJob  # noqa: E402
from sd_diff_set.factory_line import load_jobs, run_factory  # noqa: E402
from sd_diff_set.pipeline import PipelineSettings  # noqa: E402
from sd_diff_set.png_text import upsert_parameters  # noqa: E402
from sd_diff_set.service import run_job  # noqa: E402

from scene_trials.backends import get_backend  # noqa: E402
from scene_trials.cli import main as scene_main  # noqa: E402
from scene_trials.collector import collect, find_result, find_transparent  # noqa: E402
from scene_trials.layout import Layout  # noqa: E402
from scene_trials.plan import build_plan  # noqa: E402
from scene_trials.project import load_project  # noqa: E402

SIZE = 64
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


_CALLS = {"n": 0}


def png_bytes() -> bytes:
    """A different picture per call, as real seeds give. The factory merges identical files."""
    _CALLS["n"] += 1
    image = Image.new("RGB", (SIZE, SIZE), (255, 255, 255))
    for x in range(20, 44):
        for y in range(10, 54):
            image.putpixel((x, y), (200, 80, (_CALLS["n"] * 17) % 256))
    buffer = io.BytesIO()
    image.save(buffer, "PNG")
    return buffer.getvalue()


class Host(GenerationHost):
    def inpaint(self, job: InpaintJob) -> None:
        job.dest.write_bytes(job.init_path.read_bytes())
        upsert_parameters(job.dest, job.parameters_text)


def regions(_image: Path, _model: Path) -> list[tuple[str, tuple[float, float, float, float]]]:
    return [("anus", (20, 30, 30, 40)), ("penis", (24, 20, 34, 32)), ("female face", (22, 4, 38, 18))]


def run_factory_on(work: Path, batch_file: Path, face_pass_supported: bool) -> None:
    weights = work / "weights"
    weights.mkdir(parents=True, exist_ok=True)
    for name in ("face_yolov8n.pt", "hand_yolov8n.pt", "foot_yolov8x_v2.pt", "nsfw-anime-medium-x1280.pt"):
        (weights / name).write_bytes(b"")
    state = {"face": 0}

    def detect(_image: Path, model: str, dest: Path) -> Path:
        if model == "face_yolov8n.pt":
            state["face"] += 1
        Image.new("L", (SIZE, SIZE), 255).save(dest)
        return dest

    def paint(**kwargs: object) -> dict[str, object]:
        return run_job(**kwargs, host=Host())  # type: ignore[arg-type]

    settings = PipelineSettings(
        inbox=work / "inbox",
        sorted_dir=work / "sorted",
        output_dir=work / "diffs",
        preset_dir=FACTORY / "presets",
        adult_ok=True,
        dry_run=False,
        overwrite=False,
        limbs=True,
    )
    with mock.patch.dict(os.environ, {"SD_DIFF_WEIGHTS_DIR": str(weights)}), mock.patch(
        "sd_diff_set.regions._predict_regions", regions
    ), mock.patch("sd_diff_set.executor.detect_mask", detect):
        payload = run_factory(
            settings=settings,
            jobs=load_jobs(batch_file),
            poster=lambda _api, _payload: png_bytes(),
            dry_run=False,
            once=True,
            run_job=paint,
        )
    statuses = {row["id"]: row["status"] for row in payload["jobs"]}  # type: ignore[index]
    print("factory jobs:", statuses)
    print("face detector calls:", state["face"])
    run_factory_on.face_calls = state["face"]  # type: ignore[attr-defined]


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

        for trial in (1, 2):
            run_factory_on(work, meta / "sd_diff_set" / f"t{trial}-b1.json", face_pass_supported)

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
        face_calls = getattr(run_factory_on, "face_calls", None)
        print("last-run face detector calls:", face_calls)
    print("FAILED" if check.failed else "ALL OK")
    return 1 if check.failed else 0


if __name__ == "__main__":
    sys.exit(main())
