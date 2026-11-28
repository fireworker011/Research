"""Backend contract. A backend may generate, or only hand over finished files."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Mapping, Protocol, runtime_checkable

from scene_trials.plan import Batch, TrialPlan


class Role(Enum):
    BASE = "base"
    STAGE = "stage"
    MASK = "mask"
    TRANSPARENT = "transparent"


@dataclass(frozen=True)
class ProducedFile:
    job_id: str
    role: Role
    stage: str | None
    path: Path
    ok: bool = True
    error_code: str | None = None
    warnings: tuple[str, ...] = ()


@dataclass
class BackendOutput:
    files: list[ProducedFile] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


class Backend(Protocol):
    name: str

    def produced_files(self, plan: TrialPlan) -> BackendOutput:
        """Return the files that exist for the plan's jobs. Never invent a file."""
        ...


@runtime_checkable
class ExportingBackend(Protocol):
    """A backend that can hand work to an external tool. It never runs that tool."""

    name: str

    def export_batch(self, plan: TrialPlan, batch: Batch, directory: Path) -> Path:
        """Write the batch in the tool's own format and return the file."""
        ...

    def run_commands(self, plan: TrialPlan, flavor: str, batch_files: Mapping[str, Path]) -> list[str]:
        """Command lines for ``ps1`` or ``sh`` that a person runs."""
        ...
