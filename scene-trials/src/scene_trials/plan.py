"""Expand scenes and chains into jobs, batches and a scene index."""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Mapping

from scene_trials.chains import ResolvedChain, load_chain_specs, resolve_chains
from scene_trials.errors import ConfigError, SafetyError, unreachable
from scene_trials.facepass import resolve_face_pass
from scene_trials.lint import Level, LintIssue, face_hint_issue
from scene_trials.project import FacePass, ProjectConfig, TrialOrder
from scene_trials.prompt import resolve_prompt
from scene_trials.resources import LoraEntry, NegativeSet, load_loras, load_negatives
from scene_trials.scenes import Scene, find_scene, load_scenes


class JobKind(Enum):
    CHAIN = "chain"
    SOLO = "solo"


@dataclass(frozen=True)
class Job:
    job_id: str
    key: str
    trial: int
    kind: JobKind
    category: str | None
    base_scene_id: str
    section: str
    positive: str
    negative: str
    width: int
    height: int
    stages: tuple[str, ...]
    scenes: tuple[tuple[str, str | None], ...]
    choices: tuple[tuple[str, str], ...]
    lora_files: tuple[str, ...]
    notes: tuple[str, ...]
    face_pass: str | None = None

    def serves(self, scene_id: str) -> bool:
        return any(found == scene_id for found, _ in self.scenes)

    def stage_for(self, scene_id: str) -> str | None:
        for found, stage in self.scenes:
            if found == scene_id:
                return stage
        return None

    def to_dict(self) -> dict[str, object]:
        return {
            "job_id": self.job_id,
            "key": self.key,
            "trial": self.trial,
            "kind": self.kind.value,
            "category": self.category,
            "base_scene_id": self.base_scene_id,
            "section": self.section,
            "positive": self.positive,
            "negative": self.negative,
            "width": self.width,
            "height": self.height,
            "stages": list(self.stages),
            "scenes": [{"scene_id": sid, "stage": stage} for sid, stage in self.scenes],
            "choices": [{"options": opts, "chosen": chosen} for opts, chosen in self.choices],
            "lora_files": list(self.lora_files),
            "notes": list(self.notes),
            "face_pass": self.face_pass,
        }


@dataclass(frozen=True)
class Batch:
    batch_id: str
    trial: int | None
    job_ids: tuple[str, ...]


@dataclass
class TrialPlan:
    project: ProjectConfig
    scenes: list[Scene]
    chains: list[ResolvedChain]
    jobs: list[Job]
    batches: list[Batch]
    issues: list[LintIssue] = field(default_factory=list)
    skipped: frozenset[str] = frozenset()

    def planned_scene_ids(self) -> list[str]:
        return [scene.scene_id for scene in self.scenes if scene.scene_id not in self.skipped]

    def job_for(self, scene_id: str, trial: int) -> Job | None:
        for job in self.jobs:
            if job.trial == trial and job.serves(scene_id):
                return job
        return None

    @property
    def errors(self) -> list[LintIssue]:
        return [issue for issue in self.issues if issue.level is Level.ERROR]

    @property
    def warnings(self) -> list[LintIssue]:
        return [issue for issue in self.issues if issue.level is Level.WARNING]

    def scene_by_id(self) -> Mapping[str, Scene]:
        return {scene.scene_id: scene for scene in self.scenes}


def build_plan(project: ProjectConfig) -> TrialPlan:
    scenes = load_scenes(project)
    chains = resolve_chains(load_chain_specs(project.chains_path), scenes)
    loras = load_loras(project.loras_path)
    negatives = load_negatives(project.negatives_path)
    issues: list[LintIssue] = []

    in_chain = {scene_id for chain in chains for scene_id, _ in chain.scene_stages}
    skipped = {find_scene(scenes, ref).scene_id for ref in project.skip_scenes}
    shared = sorted(skipped & in_chain)
    if shared:
        raise ConfigError("skip_in_chain", f"skip_scenes cannot remove chain members: {shared}")
    units: list[tuple[int, str, ResolvedChain | None, Scene]] = []
    for chain in chains:
        units.append((chain.base.row, chain.chain_id, chain, chain.base))
    for scene in scenes:
        if scene.scene_id not in in_chain and scene.scene_id not in skipped:
            units.append((scene.row, scene.scene_id, None, scene))
    units.sort(key=lambda unit: unit[0])

    per_trial: dict[int, list[Job]] = {}
    for trial in range(1, project.trial_count + 1):
        jobs: list[Job] = []
        for _row, key, chain, base in units:
            try:
                job = _build_job(project, trial, key, chain, base, loras, negatives)
            except SafetyError as exc:
                issues.append(LintIssue(Level.ERROR, exc.code, key, exc.message))
                continue
            jobs.append(job)
            if trial == 1:
                issues.extend(_job_issues(project, chain, job))
        per_trial[trial] = jobs

    jobs_in_order, batches = _order_and_batch(project, per_trial)
    issues.extend(_lora_dir_issues(project, jobs_in_order))
    issues = list(dict.fromkeys(issues))
    return TrialPlan(
        project=project,
        scenes=scenes,
        chains=chains,
        jobs=jobs_in_order,
        batches=batches,
        issues=issues,
        skipped=frozenset(skipped),
    )


def _build_job(
    project: ProjectConfig,
    trial: int,
    key: str,
    chain: ResolvedChain | None,
    base: Scene,
    loras: Mapping[str, LoraEntry],
    negatives: NegativeSet,
) -> Job:
    resolved = resolve_prompt(
        project,
        positive=base.positive,
        negative=base.negative,
        section=base.section,
        job_key=key,
        trial=trial,
        route_tags=chain.route_tags if chain else (),
        loras=loras,
        negatives=negatives,
        width=project.width,
        height=project.height,
    )
    notes = list(resolved.notes)
    face_pass: str | None = None
    if chain is not None:
        kind = JobKind.CHAIN
        scene_pairs: tuple[tuple[str, str | None], ...] = tuple(chain.scene_stages)
        stages = chain.stages
        category: str | None = chain.category
        mode, reason = resolve_face_pass(
            chain.face_pass or project.face_pass,
            resolved.positive,
            project.face_visible_hints,
            project.rear_view_hints,
        )
        face_pass = mode.value
        if reason:
            notes.append(f"face_pass_skipped: {reason}")
    else:
        kind = JobKind.SOLO
        scene_pairs = ((base.scene_id, None),)
        stages = ()
        category = None
    return Job(
        job_id=f"{project.name}-{key}-t{trial}",
        key=key,
        trial=trial,
        kind=kind,
        category=category,
        base_scene_id=base.scene_id,
        section=base.section,
        positive=resolved.positive,
        negative=resolved.negative,
        width=project.width,
        height=project.height,
        stages=stages,
        scenes=scene_pairs,
        choices=resolved.choices,
        lora_files=resolved.lora_files,
        notes=tuple(notes),
        face_pass=face_pass,
    )


def _job_issues(project: ProjectConfig, chain: ResolvedChain | None, job: Job) -> list[LintIssue]:
    issues: list[LintIssue] = []
    for note in job.notes:
        if note.startswith(("composition_conflict", "braces_left")):
            code, _, message = note.partition(": ")
            issues.append(LintIssue(Level.WARNING, code, job.key, message))
    if chain is not None and chain.needs_face_visible and job.face_pass == FacePass.REQUIRED.value:
        found = face_hint_issue(job.key, job.positive, project.face_visible_hints)
        if found is not None:
            issues.append(found)
    return issues


def _lora_dir_issues(project: ProjectConfig, jobs: list[Job]) -> list[LintIssue]:
    if project.lora_dir is None:
        return []
    wanted = sorted({name for job in jobs for name in job.lora_files})
    missing = [
        name
        for name in wanted
        if not any((project.lora_dir / f"{name}{suffix}").is_file() for suffix in (".safetensors", ".pt", ".ckpt"))
    ]
    return [
        LintIssue(Level.ERROR, "lora_missing", name, f"no file for LoRA {name!r} in {project.lora_dir}")
        for name in missing
    ]


def _order_and_batch(
    project: ProjectConfig, per_trial: dict[int, list[Job]]
) -> tuple[list[Job], list[Batch]]:
    order = project.trial_order
    size = project.batch_max_jobs
    if order is TrialOrder.TRIAL_MAJOR:
        ordered: list[Job] = []
        batches: list[Batch] = []
        for trial in sorted(per_trial):
            jobs = per_trial[trial]
            ordered.extend(jobs)
            for index, start in enumerate(range(0, len(jobs), size), start=1):
                chunk = jobs[start : start + size]
                batches.append(
                    Batch(f"t{trial}-b{index}", trial, tuple(job.job_id for job in chunk))
                )
        return ordered, batches
    if order is TrialOrder.SCENE_MAJOR:
        by_key: dict[str, list[Job]] = {}
        for trial in sorted(per_trial):
            for job in per_trial[trial]:
                by_key.setdefault(job.key, []).append(job)
        flat = [job for jobs in by_key.values() for job in jobs]
        scene_batches = [
            Batch(f"all-b{index}", None, tuple(job.job_id for job in flat[start : start + size]))
            for index, start in enumerate(range(0, len(flat), size), start=1)
        ]
        return flat, scene_batches
    return unreachable(order)


def write_scene_index(plan: TrialPlan, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    chain_of: dict[str, tuple[str, str]] = {}
    for chain in plan.chains:
        for scene_id, stage in chain.scene_stages:
            chain_of[scene_id] = (chain.chain_id, stage)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["scene_id", "row", "section", "section_label", "source", "chain", "stage", "base_scene"])
        for scene in plan.scenes:
            chain_id, stage = chain_of.get(scene.scene_id, ("", ""))
            base = next(
                (c.base.scene_id for c in plan.chains if c.chain_id == chain_id), scene.scene_id
            )
            writer.writerow(
                [
                    scene.scene_id,
                    scene.row,
                    scene.section,
                    scene.section_label,
                    "chain" if chain_id else "skipped" if scene.scene_id in plan.skipped else "solo",
                    chain_id,
                    stage,
                    base,
                ]
            )
