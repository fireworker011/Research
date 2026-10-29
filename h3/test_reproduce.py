"""Reproduction prompts bind a measured video and do not invent motion."""

from __future__ import annotations

import contextlib
import io
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from h3.live_remake import LIGHTNING_FILE, LIGHTNING_STEPS, MODEL_FILE, STEPS
from h3.reproduce import ReproduceError, build_reproduction, main

NOTEBOOK = Path(__file__).resolve().parents[1] / "minimax_h3_live_remake.ipynb"


def _video(directory: Path, seconds: float) -> Path:
    path = directory / "source.mp4"
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "lavfi",
            "-i",
            f"color=c=black:s=320x180:d={seconds}",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            str(path),
        ],
        check=True,
    )
    return path


class ReproduceTests(unittest.TestCase):
    def test_local_video_gets_a_ref2va_prompt_and_no_lora(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            video = _video(Path(tmp), 2)
            plan = build_reproduction(str(video))
        self.assertEqual(plan["status"], "ready")
        self.assertFalse(plan["generate"])
        self.assertFalse(plan["publish"])
        self.assertFalse(plan["queue"])
        self.assertEqual(plan["loras"], [])
        self.assertEqual(plan["steps"], STEPS)
        self.assertEqual(plan["model_file"], MODEL_FILE)
        self.assertEqual(plan["canvas"], {"width": 1344, "height": 768, "fps": 24})
        prompt = plan["prompts"][0]["prompt"]
        for section in (
            "subject_definitions:",
            "summary:",
            "retention_analysis:",
            "detailed_description:",
            "overall_soundscape:",
            "non_diegetic_music:",
        ):
            self.assertIn(section, prompt)
        self.assertIn("<Video 1>", prompt)
        self.assertNotIn("<Picture", prompt)
        self.assertNotIn("walk", prompt.lower())
        self.assertNotIn("anime", prompt.lower())
        self.assertEqual(plan["prompts"][0]["request_frames"], 124)
        unused = {item["key"]: item["used"] for item in plan["lora_plan"]}
        self.assertTrue(unused["none"])
        self.assertFalse(unused["speed"])
        self.assertFalse(unused["combat"])
        self.assertFalse(unused["charswap"])
        self.assertFalse(unused["anime2real"])
        self.assertIn(MODEL_FILE, prompt + plan["model_file"])

    def test_link_stays_blocked_and_writes_no_prompt(self) -> None:
        plan = build_reproduction("https://example.com/source.mp4")
        self.assertEqual(plan["status"], "blocked")
        self.assertEqual(plan["prompts"], [])
        self.assertIn("リンクだけでは", plan["blocked"][0])
        self.assertEqual(plan["loras"], [])
        self.assertFalse(any(item["used"] and item["key"] == "combat" for item in plan["lora_plan"]))

    def test_identity_still_locks_picture_one_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            video = _video(Path(tmp), 2)
            plan = build_reproduction(str(video), stills=(("S1", "/stills/S1.jpg"), ("place", "/stills/road.jpg")))
        prompt = plan["prompts"][0]["prompt"]
        self.assertEqual(plan["status"], "ready")
        self.assertLess(prompt.index("<Picture 1>"), prompt.index("<Picture 2>"))
        self.assertIn("<Subject 1>", prompt)
        self.assertIn("/stills/S1.jpg", json.dumps(plan["prompts"][0]["pictures"]))
        self.assertNotIn("Rendering stays", prompt)

    def test_motion_line_stays_on_its_own_span(self) -> None:
        line = "The camera stays fixed for this measured span."
        with tempfile.TemporaryDirectory() as tmp:
            video = _video(Path(tmp), 10)
            plan = build_reproduction(str(video), motion=(line,))
        self.assertGreaterEqual(len(plan["prompts"]), 2)
        self.assertIn(line, plan["prompts"][0]["prompt"])
        self.assertNotIn(line, plan["prompts"][1]["prompt"])

    def test_japanese_motion_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            video = _video(Path(tmp), 2)
            with self.assertRaises(ReproduceError):
                build_reproduction(str(video), motion=("カメラが寄る",))

    def test_lightning_is_the_only_loaded_lora(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            video = _video(Path(tmp), 2)
            plan = build_reproduction(str(video), lightning=True)
        self.assertEqual(plan["steps"], LIGHTNING_STEPS)
        self.assertEqual(plan["loras"], [{"key": "lightning", "file": LIGHTNING_FILE, "strength": 1.0}])
        used = [item["key"] for item in plan["lora_plan"] if item["used"]]
        self.assertEqual(used, ["lightning"])

    def test_unlabeled_stills_in_a_folder_do_not_become_a_prompt(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _video(root, 2)
            (root / "face.jpg").write_bytes(b"not-a-real-jpeg")
            plan = build_reproduction(str(root))
        self.assertEqual(plan["status"], "blocked")
        self.assertEqual(plan["prompts"], [])
        self.assertIn("役が無い", plan["blocked"][0])

    def test_generate_flag_stops(self) -> None:
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main(["--generate", "https://example.com/a.mp4"]), 1)
            blocked = io.StringIO()
            with contextlib.redirect_stdout(blocked):
                self.assertEqual(main(["https://example.com/a.mp4"]), 1)
        self.assertIn("載せる LoRA: なし", blocked.getvalue())
        self.assertIn("生成: しない", blocked.getvalue())
        self.assertNotIn("detailed_description:", blocked.getvalue())

    def test_colab_cell_plans_and_does_not_queue(self) -> None:
        notebook = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
        cells = ["".join(cell.get("source", [])) for cell in notebook["cells"]]
        reproduce = [text for text in cells if "reproduce.py" in text and "build_reproduction" in text]
        self.assertEqual(len(reproduce), 1)
        cell = reproduce[0]
        self.assertIn("LIGHTNING = False", cell)
        self.assertIn("既にあるので書かない", cell)
        self.assertIn("生成ボタンは押していない。", cell)
        self.assertNotIn("post_prompt", cell)
        self.assertNotIn("/prompt", cell)


if __name__ == "__main__":
    unittest.main()
