"""N5: copy a backend's files into the project layout and write manifests.

Files are copied, never moved, so the backend keeps its own ledger intact. A
destination that already holds different bytes is reported as a conflict and
left alone unless ``overwrite`` is set.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from scene_trials.backends.base import BackendOutput, ProducedFile, Role
from scene_trials.layout import MANIFEST_NAME, Layout
from scene_trials.plan import Job, JobKind, TrialPlan

RESULT_STEM = "result"


class Status:
    OK = "ok"
    FAILED = "failed"
    MISSING = "missing"


@dataclass
class SceneTrialResult:
    scene_id: str
    section: str
    trial: int
    job_id: str
    stage: str | None
    status: str
    error_code: str | None
    files: dict[str, str] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)


@dataclass
class CollectReport:
    results: list[SceneTrialResult] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def counts(self) -> dict[str, int]:
        counts = {Status.OK: 0, Status.FAILED: 0, Status.MISSING: 0}
        for result in self.results:
            counts[result.status] += 1
        return counts


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def find_result(trial_dir: Path) -> Path | None:
    for path in sorted(trial_dir.glob(f"{RESULT_STEM}.*")):
        if path.suffix.lower() in (".png", ".webp", ".jpg", ".jpeg") and ".transparent" not in path.name:
            return path
    return None


def find_transparent(trial_dir: Path) -> Path | None:
    for path in sorted(trial_dir.glob(f"{RESULT_STEM}.transparent.*")):
        return path
    return None


def collect(
    plan: TrialPlan, output: BackendOutput, *, backend_name: str, overwrite: bool = False
) -> CollectReport:
    layout = Layout(plan.project)
    report = CollectReport(notes=list(output.notes))
    by_job: dict[str, list[ProducedFile]] = {}
    for produced in output.files:
        by_job.setdefault(produced.job_id, []).append(produced)

    scenes = plan.scene_by_id()
    for job in plan.jobs:
        files = by_job.get(job.job_id, [])
        chain_dir = layout.chain_trial_dir(job.key, job.trial)
        if files:
            _write_chain_copy(chain_dir, job, files, overwrite, report)
        for scene_id, stage in job.scenes:
            scene = scenes[scene_id]
            trial_dir = layout.trial_dir(scene.section, scene_id, job.trial)
            result = _collect_scene(trial_dir, scene_id, scene.section, job, stage, files, overwrite, report)
            _write_manifest(trial_dir, job, result, backend_name)
            report.results.append(result)

    meta = layout.meta()
    meta.mkdir(parents=True, exist_ok=True)
    (meta / "collect-report.json").write_text(
        json.dumps(
            {
                "counts": report.counts(),
                "conflicts": report.conflicts,
                "notes": report.notes,
                "results": [
                    {
                        "scene_id": r.scene_id,
                        "trial": r.trial,
                        "status": r.status,
                        "stage": r.stage,
                        "error_code": r.error_code,
                    }
                    for r in report.results
                ],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return report


def _pick(files: list[ProducedFile], role: Role, stage: str | None) -> ProducedFile | None:
    for produced in files:
        if produced.role is role and produced.stage == stage:
            return produced
    return None


def _copy(src: Path, dst: Path, overwrite: bool, report: CollectReport) -> bool:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        if file_sha256(dst) == file_sha256(src):
            return True
        if not overwrite:
            report.conflicts.append(f"{dst} already holds different bytes than {src}")
            return False
    shutil.copyfile(src, dst)
    return True


def _write_chain_copy(
    chain_dir: Path, job: Job, files: list[ProducedFile], overwrite: bool, report: CollectReport
) -> None:
    for produced in files:
        suffix = produced.path.suffix.lower()
        if produced.role is Role.BASE:
            name = f"base{suffix}"
        elif produced.role is Role.STAGE:
            name = f"stage_{produced.stage}{suffix}"
        elif produced.role is Role.TRANSPARENT:
            name = f"{'base' if produced.stage is None else 'stage_' + produced.stage}.transparent{suffix}"
        else:
            name = f"{'base' if produced.stage is None else 'stage_' + produced.stage}.mask{suffix}"
        _copy(produced.path, chain_dir / name, overwrite, report)
    chain_dir.mkdir(parents=True, exist_ok=True)
    (chain_dir / "job.json").write_text(
        json.dumps(job.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _collect_scene(
    trial_dir: Path,
    scene_id: str,
    section: str,
    job: Job,
    stage: str | None,
    files: list[ProducedFile],
    overwrite: bool,
    report: CollectReport,
) -> SceneTrialResult:
    is_chain = job.kind is JobKind.CHAIN
    target = _pick(files, Role.STAGE if is_chain else Role.BASE, stage if is_chain else None)
    result = SceneTrialResult(
        scene_id=scene_id,
        section=section,
        trial=job.trial,
        job_id=job.job_id,
        stage=stage,
        status=Status.MISSING,
        error_code="not_produced",
    )
    if target is None:
        return result
    result.warnings.extend(target.warnings)
    if not target.ok:
        result.status = Status.FAILED
        result.error_code = target.error_code or "backend_error"
        return result
    suffix = target.path.suffix.lower()
    if not _copy(target.path, trial_dir / f"{RESULT_STEM}{suffix}", overwrite, report):
        result.status = Status.FAILED
        result.error_code = "destination_conflict"
        return result
    result.status = Status.OK
    result.error_code = None
    result.files[f"{RESULT_STEM}{suffix}"] = file_sha256(target.path)

    if is_chain:
        base = _pick(files, Role.BASE, None)
        if base is not None and _copy(base.path, trial_dir / f"base{base.path.suffix.lower()}", overwrite, report):
            result.files[f"base{base.path.suffix.lower()}"] = file_sha256(base.path)
    transparent = _pick(files, Role.TRANSPARENT, stage if is_chain else None)
    if transparent is not None:
        name = f"{RESULT_STEM}.transparent{transparent.path.suffix.lower()}"
        if _copy(transparent.path, trial_dir / name, overwrite, report):
            result.files[name] = file_sha256(transparent.path)
    mask = _pick(files, Role.MASK, stage if is_chain else None)
    if mask is not None:
        name = f"masks/{RESULT_STEM}.mask{mask.path.suffix.lower()}"
        if _copy(mask.path, trial_dir / name, overwrite, report):
            result.files[name] = file_sha256(mask.path)
    return result


def _write_manifest(trial_dir: Path, job: Job, result: SceneTrialResult, backend_name: str) -> None:
    trial_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "scene_id": result.scene_id,
        "section": result.section,
        "trial": result.trial,
        "job_id": result.job_id,
        "chain_key": job.key if job.kind is JobKind.CHAIN else None,
        "stage": result.stage,
        "status": result.status,
        "error_code": result.error_code,
        "backend": backend_name,
        "collected_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "prompt": {
            "positive": job.positive,
            "negative": job.negative,
            "width": job.width,
            "height": job.height,
            "choices": [{"options": opts, "chosen": chosen} for opts, chosen in job.choices],
            "notes": list(job.notes),
            "face_pass": job.face_pass,
        },
        "files": result.files,
        "warnings": result.warnings,
    }
    (trial_dir / MANIFEST_NAME).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
