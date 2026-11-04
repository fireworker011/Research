"""The Sakura clip keeps the measured length and the two distinct LoRAs."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from h3.live_remake import STEPS, align_frames
from h3.sakura_clip import (
    ACTION_FILE,
    COMBAT_FILE,
    SOURCE_FRAMES,
    TRIGGER,
    build_plan,
    render,
)

NOTEBOOK = Path(__file__).resolve().parents[1] / "minimax_h3_comfyui_colab.ipynb"


class SakuraClipTests(unittest.TestCase):
    def test_plan_uses_two_loras_and_the_measured_span(self) -> None:
        plan = build_plan([COMBAT_FILE])
        self.assertEqual(plan["source_frames"], SOURCE_FRAMES)
        self.assertEqual(plan["request_frames"], align_frames(SOURCE_FRAMES))
        self.assertEqual(plan["request_frames"], 260)
        self.assertEqual(plan["steps"], STEPS)
        self.assertEqual(plan["width"], 1344)
        self.assertEqual(plan["height"], 768)
        self.assertEqual([row["file"] for row in plan["loras"]], [ACTION_FILE, COMBAT_FILE])
        self.assertEqual([row["strength"] for row in plan["loras"]], [0.6, 0.7])
        self.assertEqual(plan["missing"], [ACTION_FILE])
        self.assertFalse(plan["generate"])
        self.assertFalse(plan["queue"])
        prompt = str(plan["prompt"])
        self.assertEqual(len(plan["pictures"]), 5)
        self.assertEqual([item["role"] for item in plan["pictures"]], ["face", "front", "back", "sword", "night"])
        self.assertIn("sakura-01-face.jpg", plan["pictures"][0]["path"])
        self.assertIn("sakura-04-sword.jpg", plan["pictures"][3]["path"])
        self.assertNotIn("sakura_ref_04", str(plan["pictures"]))
        self.assertIn("<Picture 1>", prompt)
        self.assertIn("<Picture 5>", prompt)
        self.assertIn("cosmic night sky is not the place", prompt)
        self.assertIn("<Video 1>", prompt)
        self.assertIn("tachi", prompt)
        self.assertIn("Japanese temple and garden", prompt)
        self.assertIn(TRIGGER, prompt)
        self.assertNotIn("15-second", prompt)
        self.assertNotIn("silver-white", prompt)
        self.assertNotIn("ruined", prompt)
        text = render(plan)
        self.assertIn("LoRA は2枚", text)
        self.assertIn("生成: しない", text)
        self.assertIn("落とさない", text)

    def test_notebook_cell_does_not_queue_or_download(self) -> None:
        notebook = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
        cells = ["".join(cell.get("source", [])) for cell in notebook["cells"]]
        clip = [text for text in cells if "sakura_clip" in text]
        self.assertEqual(len(clip), 1)
        self.assertNotIn("post_prompt", clip[0])
        self.assertNotIn("civitai.com", clip[0])
        self.assertIn("生成ボタンは押していない。", clip[0])


if __name__ == "__main__":
    unittest.main()
