"""Backend contract. A backend may generate, or only hand over finished files."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Protocol

from scene_trials.plan import TrialPlan


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
