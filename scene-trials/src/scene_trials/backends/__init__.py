"""Backend registry. Only ``import_only`` exists in this release."""

from __future__ import annotations

from pathlib import Path

from scene_trials.backends.base import Backend
from scene_trials.backends.import_only import ImportOnlyBackend
from scene_trials.errors import BackendError
from scene_trials.project import BackendConfig

_PLANNED = {
    "sd_diff_set": "waits for the factory source (service.py, factory_line.py, pipeline.py, router.py, cutout.py)",
    "webui_api": "not written yet",
}


def get_backend(config: BackendConfig, project_root: Path) -> Backend:
    if config.name == ImportOnlyBackend.name:
        return ImportOnlyBackend(config.options, project_root)
    if config.name in _PLANNED:
        raise BackendError("backend_unavailable", f"backend {config.name} is planned: {_PLANNED[config.name]}")
    raise BackendError("backend_unknown", f"unknown backend {config.name!r}")
