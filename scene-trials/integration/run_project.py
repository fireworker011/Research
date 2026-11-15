"""Run a whole project through the real factory (GPU parts faked), then collect and check it.

Usage: python integration/run_project.py <extensions/sd-diff-set> <project folder> [--trial N]

The project folder is copied to a scratch place first. The copy gets a throw-away adult declaration, the
factory_face_pass flag when the factory has the patch, and a scratch work folder. The real folder is never
changed. The checks answer three questions: is every job planned as the chain says, does a scene without a
chain stay unpainted, and does face_pass skip keep the face detector away from those chains.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))
parser = argparse.ArgumentParser()
parser.add_argument("factory", type=Path)
parser.add_argument("project", type=Path)
parser.add_argument("--trial", type=int, default=1)
ARGS = parser.parse_args()
FACTORY = ARGS.factory.resolve()
sys.path.insert(0, str(FACTORY))
sys.path.insert(0, str(HERE))

import fake_gpu  # noqa: E402  (needs the factory on sys.path)

from scene_trials.backends import get_backend  # noqa: E402
from scene_trials.cli import main as scene_main  # noqa: E402
from scene_trials.collector import collect  # noqa: E402
from scene_trials.layout import Layout  # noqa: E402
from scene_trials.plan import JobKind, build_plan  # noqa: E402
from scene_trials.project import load_project  # noqa: E402

FAILED = {"count": 0}


def check(condition: bool, message: str) -> None:
    print(("ok   " if condition else "FAIL ") + message)
    FAILED["count"] += 0 if condition else 1


def prepare(scratch: Path, patched: bool) -> Path:
    copy = scratch / "project"
    shutil.copytree(ARGS.project, copy)
    text = (copy / "project.yaml").read_text(encoding="utf-8")
    text = re.sub(r'adult_confirmed_by: ".*"', 'adult_confirmed_by: "integration-check"', text)
    text = re.sub(r'adult_confirmed_on: ".*"', 'adult_confirmed_on: "2026-11-15"', text)
    text = re.sub(r"(\n\s+work_dir:)[^\n]*", rf"\1 {(scratch / 'work').as_posix()}", text)
    text = re.sub(r"(\n\s+factory_dir:)[^\n]*", rf"\1 {FACTORY.as_posix()}", text)
    text = re.sub(r"(\n\s+factory_face_pass:)[^\n]*", rf"\1 {str(patched).lower()}", text)
    (copy / "project.yaml").write_text(text, encoding="utf-8")
    return copy


def main() -> int:
    patched = "FACE_PASS_MODES" in (FACTORY / "sd_diff_set" / "planner.py").read_text(encoding="utf-8")
    print(f"factory {FACTORY}\nface_pass patch present: {patched}")
    with tempfile.TemporaryDirectory() as tmp:
        scratch = Path(tmp)
        os.environ["SCENE_TRIALS_OUT_ROOT"] = str(scratch / "out")
        project_dir = prepare(scratch, patched)
        code = scene_main(["export", "--project", str(project_dir)])
        if not patched and code != 0:
            print("export refused face_pass skip on the unpatched factory, as designed")
            return 0
        check(code == 0, "export")
        project = load_project(project_dir)
        plan = build_plan(project)
        trial = [job for job in plan.jobs if job.trial == ARGS.trial]
        batch = next(b for b in plan.batches if b.trial == ARGS.trial)
        meta = Layout(project).meta()
        work = scratch / "work"
        result = fake_gpu.run_batch(FACTORY, work, meta / "sd_diff_set" / f"{batch.batch_id}.json")
        rows = {row["id"]: row for row in result["jobs"]}  # type: ignore[union-attr]
        check(len(rows) == len(trial), f"the factory took all {len(trial)} jobs of trial {ARGS.trial}")
        check(all(row["status"] == "ok" for row in rows.values()), "every factory job finished ok")

        ledger = json.loads((work / "diffs" / "pipeline.json").read_text(encoding="utf-8"))["items"]
        by_id = {Path(row["source"]).stem: row for row in ledger.values()}
        solo_painted: list[str] = []
        wrong_stages: list[str] = []
        wrong_category: list[str] = []
        for job in trial:
            row = by_id[job.job_id]
            folder = work / "diffs" / str(row["category"]) / job.job_id
            stage_files = sorted(p.name for p in folder.glob("*_diff-*.png") if p.name.count(".") == 1)
            made = [re.search(r"_diff-[a-z0-9_]+-([a-z0-9_]+)\.png$", n).group(1) for n in stage_files]  # type: ignore[union-attr]
            if job.kind is JobKind.CHAIN:
                if row["category"] != job.category:
                    wrong_category.append(job.key)
                if made != list(job.stages):
                    wrong_stages.append(f"{job.key}: made {made}, asked {list(job.stages)}")
            elif made:
                solo_painted.append(f"{job.key}: {made}")
        check(not wrong_category, f"every chain landed in its category {wrong_category}")
        check(not wrong_stages, f"every chain produced exactly the requested stages {wrong_stages}")
        solo = [job for job in trial if job.kind is JobKind.SOLO]
        check(not solo_painted, f"none of the {len(solo)} solo scenes got a stage image {solo_painted}")

        skip_jobs = [job for job in trial if job.face_pass == "skip"]
        required = [job for job in trial if job.kind is JobKind.CHAIN and job.face_pass == "required"]
        calls = result["face_calls"]  # type: ignore[assignment]

        def wants_face(job: object) -> bool:
            """True when the factory's own manifest shows a stage with a face repaint for this job."""
            row = by_id[job.job_id]  # type: ignore[attr-defined]
            manifest = json.loads(Path(str(row["manifest"])).read_text(encoding="utf-8"))
            return any(float(item.get("face_denoise") or 0) > 0 for item in manifest["items"])

        face_stages = [job for job in required if wants_face(job)]
        leaked = [job.key for job in skip_jobs if any(name.startswith(job.job_id) for name in calls)]  # type: ignore[union-attr]
        used = [job.key for job in face_stages if any(name.startswith(job.job_id) for name in calls)]  # type: ignore[union-attr]
        print(f"face_pass skip chains: {[j.key for j in skip_jobs]}")
        check(bool(skip_jobs), "the project has chains with face_pass skip")
        check(not leaked, f"the face detector never touched a skip chain {leaked}")
        check(
            len(used) == len(face_stages),
            f"the face detector still ran for the {len(face_stages)} required chains that have a face repaint",
        )
        skipped_jobs_wanting = [job.key for job in skip_jobs if not wants_face(job)]
        check(len(skipped_jobs_wanting) == len(skip_jobs), "skip chains plan no face repaint at all")

        backend = get_backend(project.backend, project_dir)
        output = backend.produced_files(plan)
        report = collect(plan, output, backend_name=backend.name)
        mine = [r for r in report.results if r.trial == ARGS.trial]
        check(all(r.status == "ok" for r in mine), f"collect: all {len(mine)} scenes of trial {ARGS.trial} are ok")
        noted = {r.scene_id for r in mine if r.stage and any("face_pass_skipped" in w for w in r.warnings)}
        in_skip = {sid for job in skip_jobs for sid, _ in job.scenes}
        check(bool(noted) and noted <= in_skip, f"face_pass_skipped is recorded only on skip-chain scenes {sorted(noted)}")
        print(f"collect counts (all trials in the plan): {report.counts()}")
    print("FAILED" if FAILED["count"] else "ALL OK")
    return 1 if FAILED["count"] else 0


if __name__ == "__main__":
    sys.exit(main())
