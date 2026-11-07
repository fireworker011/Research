"""The Sakura queue stacks the two LoRAs and refuses to replace an output."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from h3.live_remake import STEPS, RemakeError
from h3.sakura_clip import SOURCE_FRAMES, build_plan
from h3.sakura_queue import (
    FL2VA_FAST,
    FL2VA_FRAMES,
    FL2VA_QUALITY,
    FL2VA_UNET,
    TURBO_FILE,
    TURBO_STEPS,
    build_fl2va_prompt,
    build_sakura_prompt,
    fl2va_choice,
    missing_paths,
    output_paths,
    reference_argv,
)


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

    def test_fl2va_uses_the_sword_still_and_the_8_step_lora(self) -> None:
        prompt = build_fl2va_prompt(
            image_file="sakura-04-sword.jpg",
            video_vae="minimax_h3_video_vae_fp16.safetensors",
            seed=8,
        )
        kinds = [item["class_type"] for item in prompt.values()]
        self.assertIn("MiniMaxH3ImageToVideo", kinds)
        self.assertNotIn("LoadVideo", kinds)
        self.assertEqual(prompt["4"]["inputs"]["unet_name"], FL2VA_UNET)
        self.assertEqual(prompt["30"]["inputs"]["lora_name"], TURBO_FILE)
        self.assertEqual(prompt["30"]["inputs"]["strength_model"], 1.0)
        self.assertEqual(prompt["6"]["inputs"]["steps"], TURBO_STEPS)
        self.assertEqual(FL2VA_FRAMES, 260)
        self.assertEqual(prompt["8"]["inputs"]["length"], 260)
        self.assertIn("[0.000s-0.678s]", prompt["8"]["inputs"]["prompt"])
        self.assertIn("[8.133s-10.833s]", prompt["8"]["inputs"]["prompt"])
        self.assertEqual(prompt["8"]["inputs"]["first_frame"], ["20", 0])
        self.assertEqual(prompt["8"]["inputs"]["last_frame"], ["20", 0])
        self.assertEqual(prompt["20"]["inputs"]["image"], "sakura-04-sword.jpg")
        self.assertEqual(prompt["8"]["inputs"]["width"], 1344)
        self.assertEqual(prompt["8"]["inputs"]["height"], 768)
        self.assertIn("16:9", prompt["8"]["inputs"]["prompt"])
        self.assertIn("giant yokai", prompt["8"]["inputs"]["prompt"])
        self.assertNotIn("<Video 1>", prompt["8"]["inputs"]["prompt"])

    def test_quality_mode_drops_the_turbo_lora(self) -> None:
        prompt = build_fl2va_prompt(
            image_file="sakura-04-sword.jpg",
            video_vae="minimax_h3_video_vae_fp16.safetensors",
            mode=FL2VA_QUALITY,
        )
        kinds = [item["class_type"] for item in prompt.values()]
        self.assertNotIn("LoraLoaderModelOnly", kinds)
        self.assertEqual(prompt["6"]["inputs"]["steps"], STEPS)
        self.assertEqual(prompt["6"]["inputs"]["model"], ["4", 0])
        self.assertEqual(prompt["19"]["inputs"]["filename_prefix"], "video/sakura-fl2va-yokai20")
        self.assertEqual(fl2va_choice(FL2VA_FAST)["steps"], TURBO_STEPS)
        self.assertEqual(fl2va_choice(FL2VA_QUALITY)["wait_minutes"], 90 * STEPS // TURBO_STEPS)
        with self.assertRaises(RemakeError):
            fl2va_choice("other")


if __name__ == "__main__":
    unittest.main()
