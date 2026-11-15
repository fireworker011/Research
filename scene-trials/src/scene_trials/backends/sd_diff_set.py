"""Backend for the sd-diff-set factory.

This adapter never imports the factory and never runs it. It does three jobs:

* write the factory's ``--jobs`` JSON for each batch (``export_batch``),
* write the command lines a person runs (``run_commands``). With ``--run`` the
  factory posts both txt2img and inpaint to the chosen WebUI API, so the
  command does not have to sit inside the reForge process.
* read what the factory left behind (``pipeline.json``, per-image
  ``manifest.json``, the sorted base and the ``.transparent.png`` files) and
  hand it to the collector (``produced_files``).

The factory keys everything by file stem, so each job id is used as the
factory job ``id``. Job ids therefore must not contain the factory's own
markers.
"""

from __future__ import annotations

import json
import re
import shlex
from pathlib import Path
from typing import Mapping

from scene_trials.backends.base import BackendOutput, ProducedFile, Role
from scene_trials.errors import BackendError
from scene_trials.plan import Batch, Job, JobKind, TrialPlan
from scene_trials.project import anchor_path

NO_STAGES = ["none"]
_FACTORY_OWN = (".mask", "_diff-", ".clip", ".face", ".region", ".detect", ".transparent", ".game", ".album")
_REQUIRED_GENERATION = ("sampler_name", "steps", "cfg_scale", "model")
_OPTIONAL_GENERATION = ("scheduler", "clip_skip")
_FINISH = ("game", "album", "both")
_LORA_CHECK = ("error", "warn", "off")
_ANCHORS = ("diffs", "sorted", "generated", "inbox")
_SUFFIX = "[0-9a-f]{8}"


class SdDiffSetBackend:
    name = "sd_diff_set"

    def __init__(self, options: Mapping[str, object], base_dir: Path | None = None) -> None:
        work = options.get("work_dir")
        if not work:
            raise BackendError("backend_option", "sd_diff_set needs backend.options.work_dir")
        self.work_dir = anchor_path(Path(str(work)), base_dir)
        factory = options.get("factory_dir")
        self.factory_dir = anchor_path(Path(str(factory)), base_dir) if factory else None
        self.python = str(options.get("python") or "python")
        self.colab_api = str(options.get("colab_api") or "").strip()
        self.finish = str(options.get("finish") or "game")
        if self.finish not in _FINISH:
            raise BackendError("backend_option", f"finish must be one of {_FINISH}, got {self.finish!r}")
        self.supports_face_pass = bool(options.get("factory_face_pass", False))
        check = options.get("lora_check")
        if check is not None and check not in _LORA_CHECK:
            raise BackendError("backend_option", f"lora_check must be one of {_LORA_CHECK}, got {check!r}")
        self.lora_check = None if check is None else str(check)
        limbs = options.get("limbs", True)
        if not isinstance(limbs, bool):
            raise BackendError("backend_option", f"limbs must be true or false, got {limbs!r}")
        self.limbs = limbs
        self.generation = _generation(options.get("generation"))

    @property
    def diffs_dir(self) -> Path:
        return self.work_dir / "diffs"

    def export_batch(self, plan: TrialPlan, batch: Batch, directory: Path) -> Path:
        """Write ``{"jobs": [...]}`` in the factory's own format."""
        jobs = {job.job_id: job for job in plan.jobs}
        rows = [self._factory_job(jobs[job_id]) for job_id in batch.job_ids]
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"{batch.batch_id}.json"
        path.write_text(json.dumps({"jobs": rows}, ensure_ascii=False, indent=2), encoding="utf-8")
        return path

    def run_commands(self, plan: TrialPlan, flavor: str, batch_files: Mapping[str, Path]) -> list[str]:
        """One factory command per batch. The caller checks the adult confirmation first."""
        quote = _quote_ps1 if flavor == "ps1" else _quote_sh
        lines: list[str] = []
        if self.factory_dir is not None:
            lines.append(
                f"Set-Location {quote(str(self.factory_dir))}"
                if flavor == "ps1"
                else f"cd {quote(str(self.factory_dir))}"
            )
        for batch in plan.batches:
            args = [
                self.python,
                "-m",
                "sd_diff_set.cli",
                "factory",
                "--inbox",
                quote(str(self.work_dir / "inbox")),
                "--sorted",
                quote(str(self.work_dir / "sorted")),
                "--output",
                quote(str(self.diffs_dir)),
                "--preset-dir",
                "presets",
                "--jobs",
                quote(str(batch_files[batch.batch_id])),
                "--finish",
                self.finish,
                "--adult-ok",
                "--run",
                "--once",
            ]
            if self.colab_api:
                args.extend(["--colab-api", quote(self.colab_api)])
            if self.lora_check:
                args.extend(["--lora-check", self.lora_check])
            if not self.limbs:
                args.append("--no-limbs")
            lines.append(f"# batch {batch.batch_id}")
            lines.append(" ".join(args))
        return lines

    def _factory_job(self, job: Job) -> dict[str, object]:
        _check_id(job.job_id)
        row: dict[str, object] = {
            "id": job.job_id,
            "prompt": job.positive,
            "negative_prompt": job.negative,
            "width": job.width,
            "height": job.height,
            **self.generation,
        }
        if job.kind is JobKind.CHAIN:
            row["stages"] = list(job.stages)
            if job.face_pass and job.face_pass != "required":
                if not self.supports_face_pass:
                    raise BackendError(
                        "face_pass_unsupported",
                        f"{job.key} needs face_pass {job.face_pass!r}. Apply factory-patches/0001 and set "
                        "backend.options.factory_face_pass: true. The unpatched factory would ignore it.",
                    )
                row["face_pass"] = job.face_pass
        else:
            row["stages"] = list(NO_STAGES)
        return row

    def produced_files(self, plan: TrialPlan) -> BackendOutput:
        ledger = self.diffs_dir / "pipeline.json"
        if not ledger.is_file():
            raise BackendError("ledger_missing", f"{ledger} does not exist. Run the factory first.")
        rows = _ledger_rows(ledger)
        output = BackendOutput()
        for job in plan.jobs:
            matches = [row for row in rows if _stem_matches(row, job.job_id)]
            if not matches:
                continue
            if len(matches) > 1:
                output.notes.append(f"duplicate_rows: {len(matches)} ledger rows for {job.job_id}; the last one is used")
            self._job_files(job, matches[-1], output)
        return output

    def _job_files(self, job: Job, row: Mapping[str, object], output: BackendOutput) -> None:
        category = str(row.get("category") or "")
        row_error = _text(row.get("error_code"))
        base_path = self._resolve(row.get("working")) or self._resolve(row.get("sorted"))
        warnings: list[str] = []
        if row_error:
            warnings.append(f"paint: {row_error}")
        lora_notes = tuple(str(note) for note in row.get("lora_notes") or [])
        warnings.extend(lora_notes)
        if category in ("refused", "error"):
            output.files.append(
                ProducedFile(job.job_id, Role.BASE, None, base_path or Path(""), False, row_error or category)
            )
            return
        if base_path is None:
            output.notes.append(f"base_missing: no base file for {job.job_id}")
            return
        output.files.append(ProducedFile(job.job_id, Role.BASE, None, base_path, True, None, tuple(warnings)))
        transparent = _sibling_transparent(base_path) or self._resolve(row.get("transparent"))
        if transparent is not None:
            output.files.append(ProducedFile(job.job_id, Role.TRANSPARENT, None, transparent))
        if job.kind is not JobKind.CHAIN:
            return
        manifest = self._resolve(row.get("manifest")) or _find_manifest(self.diffs_dir, category, base_path.stem)
        items = _manifest_items(manifest) if manifest else {}
        for stage in job.stages:
            item = items.get(stage)
            if item is None:
                output.files.append(
                    ProducedFile(job.job_id, Role.STAGE, stage, Path(""), False, row_error or "not_planned")
                )
                continue
            produced = self._resolve(item.get("path"))
            status = _text(item.get("status"))
            item_warnings = tuple(str(w) for w in item.get("warnings") or []) + lora_notes
            if status != "ok" or produced is None:
                code = _text(item.get("error_code")) or status or "no_output"
                output.files.append(
                    ProducedFile(job.job_id, Role.STAGE, stage, produced or Path(""), False, code, item_warnings)
                )
                continue
            output.files.append(ProducedFile(job.job_id, Role.STAGE, stage, produced, True, None, item_warnings))
            clear = _sibling_transparent(produced)
            if clear is not None:
                output.files.append(ProducedFile(job.job_id, Role.TRANSPARENT, stage, clear))
            mask = self._resolve(item.get("mask_file"))
            if mask is not None:
                output.files.append(ProducedFile(job.job_id, Role.MASK, stage, mask))

    def _resolve(self, value: object) -> Path | None:
        """A path from the ledger. When it is gone, look under work_dir by its folder name."""
        text = _text(value)
        if not text:
            return None
        path = Path(text)
        if path.is_file():
            return path
        parts = re.split(r"[\\/]", text)
        for index in range(len(parts) - 1, -1, -1):
            if parts[index] in _ANCHORS:
                moved = self.work_dir.joinpath(*parts[index:])
                if moved.is_file():
                    return moved
                break
        return None


def _generation(raw: object) -> dict[str, object]:
    if not isinstance(raw, dict):
        raise BackendError("backend_option", "sd_diff_set needs backend.options.generation (a mapping)")
    missing = [key for key in _REQUIRED_GENERATION if raw.get(key) in (None, "")]
    if missing:
        raise BackendError("backend_option", f"backend.options.generation is missing: {', '.join(missing)}")
    unknown = set(raw) - set(_REQUIRED_GENERATION) - set(_OPTIONAL_GENERATION)
    if unknown:
        raise BackendError("backend_option", f"unknown generation keys: {sorted(unknown)}")
    return {key: raw[key] for key in (*_REQUIRED_GENERATION, *_OPTIONAL_GENERATION) if raw.get(key) not in (None, "")}


def _check_id(job_id: str) -> None:
    lowered = job_id.casefold()
    for marker in _FACTORY_OWN:
        if marker in lowered:
            raise BackendError(
                "job_id_reserved",
                f"job id {job_id!r} contains {marker!r}, which the factory uses to skip its own files",
            )



def _text(value: object) -> str:
    return "" if value is None else str(value).strip()


def _ledger_rows(path: Path) -> list[Mapping[str, object]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BackendError("ledger_unreadable", f"{path}: {exc}") from exc
    items = data.get("items") if isinstance(data, dict) else None
    if not isinstance(items, dict):
        raise BackendError("ledger_unreadable", f"{path} has no items mapping")
    return [row for row in items.values() if isinstance(row, dict)]


def _stem_matches(row: Mapping[str, object], job_id: str) -> bool:
    stem = re.split(r"[\\/]", _text(row.get("source")))[-1]
    stem = stem.rsplit(".", 1)[0]
    return stem == job_id or re.fullmatch(rf"{re.escape(job_id)}-{_SUFFIX}", stem) is not None


def _sibling_transparent(path: Path) -> Path | None:
    candidate = path.with_name(f"{path.stem}.transparent.png")
    return candidate if candidate.is_file() else None


def _find_manifest(diffs: Path, category: str, stem: str) -> Path | None:
    if not category:
        return None
    candidate = diffs / category / stem / "manifest.json"
    return candidate if candidate.is_file() else None


def _manifest_items(path: Path) -> dict[str, Mapping[str, object]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    items = data.get("items") if isinstance(data, dict) else None
    if not isinstance(items, list):
        return {}
    return {str(item["variant"]): item for item in items if isinstance(item, dict) and item.get("variant")}


def _quote_ps1(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _quote_sh(value: str) -> str:
    return shlex.quote(value)
