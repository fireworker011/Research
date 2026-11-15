"""Backend that only imports images that already exist.

Two ways to say which job a file belongs to:

* an index CSV with columns ``path,scene_id,trial,role,stage`` (``ok`` and
  ``error_code`` are optional), or
* file names, ``{scene_id}__t{N}.png`` for the base, ``{scene_id}__t{N}__{stage}.png``
  for a stage, and the ``.transparent`` or ``.mask`` suffix before the extension.

Nothing is generated and no adult confirmation is needed: the person who made
the files owns that decision.
"""

from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Mapping

from scene_trials.backends.base import BackendOutput, ProducedFile, Role
from scene_trials.errors import BackendError
from scene_trials.plan import Job, TrialPlan
from scene_trials.project import anchor_path

_IMAGE_SUFFIXES = frozenset({".png", ".webp", ".jpg", ".jpeg"})
_NAME = re.compile(
    r"^(?P<scene>[A-Za-z0-9][A-Za-z0-9_-]*?)__t(?P<trial>\d+)"
    r"(?:__(?P<stage>[A-Za-z0-9][A-Za-z0-9_-]*))?"
    r"(?P<kind>\.transparent|\.mask)?$"
)


class ImportOnlyBackend:
    name = "import_only"

    def __init__(self, options: Mapping[str, object], base_dir: Path | None = None) -> None:
        source = options.get("source_dir")
        if not source:
            raise BackendError("backend_option", "import_only needs backend.options.source_dir")
        self.source_dir = anchor_path(Path(str(source)), base_dir)
        index = options.get("index_csv")
        self.index_csv = anchor_path(Path(str(index)), base_dir) if index else None

    def produced_files(self, plan: TrialPlan) -> BackendOutput:
        if not self.source_dir.is_dir():
            raise BackendError("source_missing", f"{self.source_dir} is not a directory")
        output = BackendOutput()
        seen: dict[tuple[str, Role, str | None], Path] = {}
        for entry in self._entries():
            self._accept(plan, entry, output, seen)
        return output

    def _entries(self) -> list[dict[str, str]]:
        if self.index_csv is not None:
            with self.index_csv.open(encoding="utf-8-sig", newline="") as handle:
                return [
                    {key: (value or "").strip() for key, value in row.items() if key}
                    for row in csv.DictReader(handle)
                ]
        entries: list[dict[str, str]] = []
        for path in sorted(self.source_dir.rglob("*")):
            if not path.is_file() or path.suffix.lower() not in _IMAGE_SUFFIXES:
                continue
            match = _NAME.match(path.stem)
            relative = str(path.relative_to(self.source_dir))
            if match is None:
                entries.append({"path": relative, "scene_id": "", "trial": "", "role": "", "stage": ""})
                continue
            kind = match.group("kind")
            stage = match.group("stage") or ""
            if kind == ".transparent":
                role = Role.TRANSPARENT.value
            elif kind == ".mask":
                role = Role.MASK.value
            else:
                role = Role.STAGE.value if stage else Role.BASE.value
            entries.append(
                {
                    "path": relative,
                    "scene_id": match.group("scene"),
                    "trial": match.group("trial"),
                    "role": role,
                    "stage": stage,
                }
            )
        return entries

    def _accept(
        self,
        plan: TrialPlan,
        entry: dict[str, str],
        output: BackendOutput,
        seen: dict[tuple[str, Role, str | None], Path],
    ) -> None:
        relative = entry.get("path", "")
        if not entry.get("scene_id"):
            output.notes.append(f"unmatched: {relative} does not follow the naming convention")
            return
        try:
            trial = int(entry["trial"])
            role = Role(entry["role"])
        except (KeyError, ValueError):
            output.notes.append(f"bad_entry: {relative} has a bad trial or role")
            return
        job = plan.job_for(entry["scene_id"], trial)
        if job is None:
            output.notes.append(f"unknown_scene: {relative} ({entry['scene_id']} trial {trial})")
            return
        stage = entry.get("stage") or None
        if not _stage_ok(job, role, stage):
            output.notes.append(f"unknown_stage: {relative} (stage {stage!r} is not in {list(job.stages)})")
            return
        path = self.source_dir / relative
        if not path.is_file():
            output.notes.append(f"file_missing: {relative}")
            return
        key = (job.job_id, role, stage)
        earlier = seen.get(key)
        if earlier is not None:
            if earlier.read_bytes() != path.read_bytes():
                output.notes.append(f"duplicate_differs: {relative} vs {earlier.name} for {job.job_id} {role.value} {stage}")
            return
        seen[key] = path
        ok_text = entry.get("ok", "true").casefold()
        output.files.append(
            ProducedFile(
                job_id=job.job_id,
                role=role,
                stage=stage,
                path=path,
                ok=ok_text not in ("false", "0", "no"),
                error_code=entry.get("error_code") or None,
            )
        )



def _stage_ok(job: Job, role: Role, stage: str | None) -> bool:
    if role is Role.BASE:
        return stage is None
    if role is Role.STAGE:
        return stage is not None and stage in job.stages
    if role is Role.TRANSPARENT or role is Role.MASK:
        return stage is None or stage in job.stages
    return False
