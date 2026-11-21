"""The only fake parts of the integration checks: txt2img, inpaint and the YOLO detectors.

Everything else (router, planner, pipeline, executor, cutout, ledger) is the factory's real code.
Import this module only after the factory folder is on ``sys.path``.
"""

from __future__ import annotations

import io
import os
from pathlib import Path
from unittest import mock

from PIL import Image

from sd_diff_set.executor import GenerationHost, InpaintJob
from sd_diff_set.factory_line import load_jobs, run_factory
from sd_diff_set.pipeline import PipelineSettings
from sd_diff_set.png_text import upsert_parameters, write_l_png
from sd_diff_set.service import run_job

SIZE = 64
WEIGHTS = ("face_yolov8n.pt", "hand_yolov8n.pt", "foot_yolov8x_v2.pt", "nsfw-anime-medium-x1280.pt")
_CALLS = {"poster": 0}


def png_bytes() -> bytes:
    """A different picture per call, as real seeds give. The factory merges identical files."""
    _CALLS["poster"] += 1
    image = Image.new("RGB", (SIZE, SIZE), (255, 255, 255))
    for x in range(20, 44):
        for y in range(10, 54):
            image.putpixel((x, y), (200, 80, (_CALLS["poster"] * 17) % 256))
    buffer = io.BytesIO()
    image.save(buffer, "PNG")
    return buffer.getvalue()


class Host(GenerationHost):
    def inpaint(self, job: InpaintJob) -> None:
        job.dest.write_bytes(job.init_path.read_bytes())
        upsert_parameters(job.dest, job.parameters_text)


def regions(_image: Path, _model: Path) -> list[tuple[str, tuple[float, float, float, float]]]:
    """Every organ the factory looks for, close together, so every act passes its penis check."""
    return [
        ("anus", (20, 30, 30, 40)),
        ("vagina", (30, 30, 40, 40)),
        ("penis", (24, 20, 34, 32)),
        ("female face", (22, 4, 38, 18)),
    ]


def run_batch(factory: Path, work: Path, batch_file: Path) -> dict[str, object]:
    """Run one exported batch through the real factory. Returns the job rows and the face-detector log."""
    weights = work / "weights"
    weights.mkdir(parents=True, exist_ok=True)
    for name in WEIGHTS:
        (weights / name).write_bytes(b"")
    face_calls: list[str] = []

    def detect(image: Path, model: str, dest: Path) -> Path:
        if model == "face_yolov8n.pt":
            face_calls.append(Path(image).name)
        dest.parent.mkdir(parents=True, exist_ok=True)
        write_l_png(dest, SIZE, SIZE, b"\xff" * (SIZE * SIZE))
        return dest

    def paint(**kwargs: object) -> dict[str, object]:
        return run_job(**kwargs, host=Host())  # type: ignore[arg-type]

    settings = PipelineSettings(
        inbox=work / "inbox",
        sorted_dir=work / "sorted",
        output_dir=work / "diffs",
        preset_dir=factory / "presets",
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
    return {"jobs": payload["jobs"], "face_calls": face_calls}
