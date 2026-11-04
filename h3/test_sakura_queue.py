"""The Sakura queue stacks the two LoRAs and refuses to replace an output."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from h3.live_remake import RemakeError
from h3.sakura_clip import SOURCE_FRAMES, build_plan
from h3.sakura_queue import build_sakura_prompt, missing_paths, output_paths, reference_argv


class SakuraQueueTests(unittest.TestCase):
    def test_prompt_stacks_action_then_combat(self) -> None:
        plan = build_plan()
        images = [f"sakura-0{number}.jpg" for number in range(1, 6)]
        prompt = build_sakura_prompt(
            plan,
            image_files=images,
            video_file="sakura-ref.mp4",
            video_vae="minimax_h3_video_vae_fp16.safetensors",
            seed=260,
        )
        self.assertEqual(prompt["30"]["inputs"]["lora_name"], "Motion_Repair_V2.safetensors")
        self.assertEqual(prompt["30"]["inputs"]["strength_model"], 0.6)
        self.assertEqual(prompt["30"]["inputs"]["model"], ["4", 0])
        self.assertEqual(prompt["31"]["inputs"]["lora_name"], "H3_Combat_V2.safetensors")
        self.assertEqual(prompt["31"]["inputs"]["strength_model"], 0.7)
        self.assertEqual(prompt["31"]["inputs"]["model"], ["30", 0])
        self.assertEqual(prompt["6"]["inputs"]["model"], ["31", 0])
        self.assertEqual(prompt["14"]["inputs"]["model"], ["31", 0])
        self.assertEqual(prompt["6"]["inputs"]["steps"], 20)
        self.assertEqual(prompt["8"]["inputs"]["length"], plan["request_frames"])
        self.assertEqual(prompt["8"]["inputs"]["length"], 260)
        self.assertEqual(prompt["8"]["inputs"]["ref_images.ref_image_0"], ["20", 0])
        self.assertEqual(prompt["8"]["inputs"]["ref_images.ref_image_4"], ["24", 0])
        self.assertEqual(prompt["12"]["inputs"]["file"], "sakura-ref.mp4")
        self.assertIn("prfight2, prfin1", prompt["8"]["inputs"]["prompt"])

    def test_reference_pads_the_measured_clip(self) -> None:
        plan = build_plan()
        argv = reference_argv(plan, "/tmp/sakura-ref.mp4")
        self.assertIn(f"tpad=stop_mode=clone:stop_duration={(260 - SOURCE_FRAMES) / 24:.3f}", " ".join(argv))
        self.assertIn("-frames:v", argv)
        self.assertEqual(argv[argv.index("-frames:v") + 1], "260")
        self.assertEqual(argv[-1], "/tmp/sakura-ref.mp4")

    def test_existing_output_is_not_replaced(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "sakura-sword.mp4"
            target.write_bytes(b"keep")
            with self.assertRaises(RemakeError):
                output_paths(tmp)
            self.assertEqual(target.read_bytes(), b"keep")

    def test_missing_paths_names_every_absent_file(self) -> None:
        plan = build_plan()
        absent = missing_paths(plan)
        self.assertIn(plan["pictures"][0]["path"], absent)
        self.assertIn(plan["video"], absent)
        self.assertTrue(any(item.endswith("H3_Combat_V2.safetensors") for item in absent))


if __name__ == "__main__":
    unittest.main()
