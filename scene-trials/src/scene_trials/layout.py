"""Folder layout: ``{out_root}/{project}/{section}/{scene_id}/trial_N/``."""

from __future__ import annotations

from pathlib import Path

from scene_trials.errors import ConfigError
from scene_trials.project import ProjectConfig

META_DIR = "_meta"
CHAINS_DIR = "_chains"
MANIFEST_NAME = "manifest.json"
SELECTED_DIR = "selected"


class Layout:
    def __init__(self, project: ProjectConfig) -> None:
        self.project = project
        self.root = project.project_out

    def _inside(self, path: Path) -> Path:
        resolved = path.resolve()
        if not resolved.is_relative_to(self.root.resolve()):
            raise ConfigError("path_escape", f"{path} is outside {self.root}")
        return path

    def meta(self) -> Path:
        return self._inside(self.root / META_DIR)

    def scene_dir(self, section: str, scene_id: str) -> Path:
        return self._inside(self.root / section / scene_id)

    def trial_dir(self, section: str, scene_id: str, trial: int) -> Path:
        return self._inside(self.scene_dir(section, scene_id) / f"trial_{trial}")

    def selected_dir(self, section: str, scene_id: str) -> Path:
        return self._inside(self.scene_dir(section, scene_id) / SELECTED_DIR)

    def chain_trial_dir(self, chain_key: str, trial: int) -> Path:
        return self._inside(self.root / CHAINS_DIR / chain_key / f"trial_{trial}")

    def selection_csv(self) -> Path:
        return self.meta() / "selection.csv"

    def sheets_dir(self) -> Path:
        return self.meta() / "sheets"
