"""Planner checks for the existing MiniMax H3 Ref2VA environment."""

from __future__ import annotations

import contextlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from h3.live_remake import (
    LIGHTNING_FILE,
    LIGHTNING_STEPS,
    MODEL_FILE,
    STEPS,
    VIDEO_VAE,
    RemakeError,
    align_frames,
    build_remake_plan,
    main,
)


def _sheet(description: str = "", roles: int = 1, place: bool = False) -> dict:
    cast = {}
    span_cast = {}
    for number in range(1, roles + 1):
        role = f"S{number}"
        cast[role] = {"stills": {"default": f"/stills/{role}.jpg"}}
        span_cast[role] = "default"
    return {
        "schema": "h3-live-remake/v1",
        "source": {
            "path": "/content/drive/MyDrive/source.mp4",
            "duration_s": 6.0,
            "width": 1920,
            "height": 1080,
            "fps": 24.0,
            "has_audio": True,
        },
        "audio": "source",
        "max_span_s": 8.0,
        "cast": cast,
        "place_still": "/stills/place.jpg" if place else "",
        "props": {},
        "spans": [
            {
                "index": 1,
                "start_s": 0.0,
                "end_s": 6.0,
                "shots": 1,
                "split_inside_shot": False,
                "cast": span_cast,
                "place": place,
                "props": [],
                "description": description,
                "soundscape": "",
                "music": "N/A",
            }
        ],
    }


class PlanTests(unittest.TestCase):
    def test_empty_description_stays_blocked_and_does_not_queue(self) -> None:
        plan = build_remake_plan(_sheet(""))
        self.assertEqual(plan["status"], "blocked")
        self.assertFalse(plan["generate"])
        self.assertFalse(plan["publish"])
        self.assertFalse(plan["comfy"]["queue"])
        self.assertEqual(plan["spans"][0]["prompt"], "")
        self.assertEqual(plan["model"]["file"], MODEL_FILE)
        self.assertEqual(plan["model"]["video_vae"], VIDEO_VAE)
        self.assertEqual(plan["model"]["steps"], STEPS)
        self.assertEqual(plan["loras"], [])
        self.assertIn("文が無い", plan["blocked"][0])

    def test_english_motion_is_ready_without_a_lora(self) -> None:
        text = "[Shot 1] The person crosses the road and the camera tracks alongside."
        plan = build_remake_plan(_sheet(text, place=True))
        self.assertEqual(plan["status"], "ready")
        self.assertFalse(plan["generate"])
        prompt = plan["spans"][0]["prompt"]
        self.assertIn("<Picture 1>", prompt)
        self.assertIn("<Picture 2>", prompt)
        self.assertIn("<Video 1>", prompt)
        self.assertIn(text, prompt)
        self.assertEqual(plan["spans"][0]["ref_images"], ["ref_image_0", "ref_image_1"])
        self.assertEqual(plan["spans"][0]["request_frames"], 158)
        self.assertEqual(plan["spans"][0]["length"], 158)

    def test_japanese_motion_is_refused(self) -> None:
        with self.assertRaises(RemakeError):
            build_remake_plan(_sheet("人が道を渡る"))

    def test_more_than_nine_stills_blocks(self) -> None:
        plan = build_remake_plan(_sheet("The person stands still.", roles=9, place=True))
        self.assertEqual(plan["status"], "blocked")
        self.assertTrue(any("9 枚まで" in item for item in plan["blocked"]))

    def test_lightning_is_opt_in(self) -> None:
        plan = build_remake_plan(_sheet("The person stands still."), lightning=True)
        self.assertEqual(plan["model"]["steps"], LIGHTNING_STEPS)
        self.assertEqual(plan["loras"][0]["file"], LIGHTNING_FILE)
        self.assertTrue(plan["lightning"])
        self.assertFalse(plan["generate"])

    def test_other_runtime_is_refused(self) -> None:
        with self.assertRaises(RemakeError):
            build_remake_plan(_sheet("The person stands still."), runtime="api")

    def test_five_seconds_lands_on_the_template_length(self) -> None:
        self.assertEqual(align_frames(120), 124)

    def test_cli_refuses_generate(self) -> None:
        with contextlib.redirect_stdout(io.StringIO()):
            code = main(["plan", "missing.json", "--generate"])
        self.assertEqual(code, 1)

    def test_cli_writes_a_blocked_plan(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sheet.json"
            path.write_text(json.dumps(_sheet("")), encoding="utf-8")
            completed = subprocess.run(
                [sys.executable, "-m", "h3.live_remake", "plan", str(path)],
                check=False,
                capture_output=True,
                text=True,
            )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        plan = json.loads(completed.stdout)
        self.assertEqual(plan["status"], "blocked")
        self.assertFalse(plan["generate"])
        self.assertEqual(plan["comfy"]["unet"], MODEL_FILE)


if __name__ == "__main__":
    unittest.main()
