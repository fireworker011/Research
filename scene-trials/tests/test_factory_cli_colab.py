from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "colab"))

import factory_cli  # noqa: E402


class FactoryCliColabTests(unittest.TestCase):
    def test_a_done_job_with_a_png_is_skipped_and_a_missing_png_is_not(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            generated = Path(tmp)
            (generated / "standing-irito-01.png").write_bytes(b"png")
            state = {
                "jobs": [
                    {"id": "standing-irito-01", "status": "done"},
                    {"id": "standing-jueri-01", "status": "done"},
                    {"id": "standing-nieva-01", "status": "error"},
                ]
            }
            done = factory_cli.completed_ids(state, generated)
            self.assertEqual(done, {"standing-irito-01"})
            jobs = [
                {"id": "standing-irito-01"},
                {"id": "standing-jueri-01"},
                {"id": "standing-nieva-01"},
            ]
            self.assertEqual([job["id"] for job in factory_cli.pending_jobs(jobs, done)], ["standing-jueri-01", "standing-nieva-01"])

    def test_patch_action_does_not_apply_a_mismatch(self) -> None:
        self.assertEqual(factory_cli.patch_action(0, 1), "apply")
        self.assertEqual(factory_cli.patch_action(1, 0), "present")
        self.assertEqual(factory_cli.patch_action(1, 1), "skip")

    def test_the_command_uses_localhost_and_only_flags_the_current_cli_has(self) -> None:
        command = factory_cli.cli_command(Path("/ext"), Path("/drive/sd-diff-set"), Path("/drive/jobs/standing.json"))
        text = " ".join(command)
        self.assertIn("--colab-api http://127.0.0.1:7860", text)
        self.assertIn("--local-api http://127.0.0.1:7860", text)
        self.assertIn("--run --once", text)
        self.assertNotIn("--no-limbs", text)
        self.assertNotIn("--lora-check", text)
        self.assertIn("sd_diff_set.cli factory", text)

    def test_load_jobs_reads_the_factory_envelope(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "standing.json"
            path.write_text(json.dumps({"jobs": [{"id": "standing-irito-01"}]}), encoding="utf-8")
            self.assertEqual(factory_cli.load_jobs(path)[0]["id"], "standing-irito-01")
            path.write_text("[]", encoding="utf-8")
            with self.assertRaises(ValueError):
                factory_cli.load_jobs(path)
