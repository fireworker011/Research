"""Comfy reads the Drive models folder and does not download it."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from h3.drive_models import (
    COMFY_DIRS,
    DRIVE_MODELS,
    DriveModelsError,
    files_for,
    link_comfy_models,
    require_mode,
)

NOTEBOOK = Path(__file__).resolve().parents[1] / "minimax_h3_comfyui_colab.ipynb"
PLAN_NOTEBOOK = Path(__file__).resolve().parents[1] / "minimax_h3_live_remake.ipynb"


def _tree(root: Path) -> None:
    for name in COMFY_DIRS:
        (root / name).mkdir(parents=True)
    (root / "erotic").mkdir()
    for name in files_for("both"):
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"x" * 20)


class DriveModelTests(unittest.TestCase):
    def test_links_comfy_dirs_and_leaves_erotic(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            drive = root / "models"
            comfy = root / "ComfyUI" / "models"
            _tree(drive)
            (comfy / "vae").mkdir(parents=True)
            (comfy / "vae" / "put_vae_here").write_text("placeholder", encoding="utf-8")
            linked = link_comfy_models(comfy, drive)
            self.assertEqual(linked, list(COMFY_DIRS))
            self.assertTrue((comfy / "vae").is_symlink())
            self.assertEqual((comfy / "vae").resolve(), (drive / "vae").resolve())
            self.assertFalse((comfy / "erotic").exists())
            require_mode(drive, "r2v")
            require_mode(drive, "both")

    def test_local_weights_stay(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            drive = root / "models"
            comfy = root / "ComfyUI" / "models"
            _tree(drive)
            local = comfy / "vae"
            local.mkdir(parents=True)
            (local / "already.safetensors").write_bytes(b"x" * 1_000_001)
            with self.assertRaises(DriveModelsError):
                link_comfy_models(comfy, drive)
            self.assertTrue((local / "already.safetensors").is_file())
            self.assertFalse((comfy / "diffusion_models").exists())

    def test_fp8_and_a_missing_file_stop(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            drive = Path(tmp) / "models"
            _tree(drive)
            with self.assertRaises(DriveModelsError):
                require_mode(drive, "r2v", quant="fp8")
            (drive / "vae" / "minimax_h3_video_vae_fp16.safetensors").unlink()
            with self.assertRaises(DriveModelsError):
                require_mode(drive, "r2v")

    def test_notebooks_use_the_drive_folder_and_do_not_fetch_weights(self) -> None:
        notebook = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
        cells = ["".join(cell.get("source", [])) for cell in notebook["cells"]]
        mount = next(text for text in cells if "DRIVE_ROOT" in text)
        weights = next(text for text in cells if "link_comfy_models" in text)
        self.assertIn("USE_DRIVE = True", mount)
        self.assertIn(DRIVE_MODELS, weights)
        self.assertNotIn("huggingface.co", weights)
        self.assertNotIn("safetensors", weights)
        span = next(text for text in cells if "video_vae_name" in text)
        self.assertNotIn("huggingface.co", span)
        plan = json.loads(PLAN_NOTEBOOK.read_text(encoding="utf-8"))
        plan_cells = ["".join(cell.get("source", [])) for cell in plan["cells"]]
        download = next(text for text in plan_cells if "RUN_DOWNLOAD" in text)
        self.assertNotIn("huggingface.co", download)
        self.assertIn(DRIVE_MODELS, download)


if __name__ == "__main__":
    unittest.main()
