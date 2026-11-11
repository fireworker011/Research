"""Local staging keeps the reserve and the phase log stays honest."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from h3.fl2va_runtime import (
    HIGH_VRAM_BYTES,
    STAGE_FILES,
    format_phase_report,
    format_stage_report,
    parse_comfy_log,
    select_local_files,
    stage_fl2va_models,
    vram_launch_arg,
)
from h3.live_remake import RemakeError
from h3.sakura_queue import FL2VA_FRAMES, build_fl2va_prompt, validate_frames


class RuntimeTests(unittest.TestCase):
    def test_vram_threshold(self) -> None:
        self.assertEqual(vram_launch_arg(HIGH_VRAM_BYTES, "auto"), "--highvram")
        self.assertEqual(vram_launch_arg(HIGH_VRAM_BYTES - 1, "auto"), "")
        self.assertEqual(vram_launch_arg(HIGH_VRAM_BYTES, ""), "")
        self.assertEqual(vram_launch_arg(1, "--lowvram"), "--lowvram")

    def test_partial_copy_keeps_the_reserve_and_the_priority(self) -> None:
        sizes = {name: 100 for name in STAGE_FILES}
        self.assertEqual(select_local_files(sizes, free_bytes=15 * 1024**3 + 500, reserve=15 * 1024**3), list(STAGE_FILES))
        chosen = select_local_files(sizes, free_bytes=250, reserve=0)
        self.assertEqual(chosen, list(STAGE_FILES[:2]))

    def test_stage_copies_only_the_fl2va_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            drive = root / "drive"
            comfy = root / "comfy"
            local = root / "local"
            ref = drive / "diffusion_models" / "minimax_h3_ref2va_pruned_int8_convrot.safetensors"
            ref.parent.mkdir(parents=True)
            ref.write_bytes(b"r" * 50)
            for rel in STAGE_FILES:
                path = drive / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"w" * 40)
            for folder in ("diffusion_models", "text_encoders", "vae", "loras"):
                dest = comfy / folder
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.symlink_to(drive / folder, target_is_directory=True)
            report = stage_fl2va_models(drive, comfy, local, free_bytes=10_000, reserve=100)
            self.assertEqual(len(report["copied"]), 5)
            fl2va = comfy / "diffusion_models" / "minimax_h3_fl2va_pruned_int8_convrot.safetensors"
            self.assertTrue(fl2va.is_symlink())
            self.assertEqual(fl2va.resolve(), (local / "diffusion_models" / fl2va.name).resolve())
            linked_ref = comfy / "diffusion_models" / ref.name
            self.assertEqual(linked_ref.resolve(), ref.resolve())
            self.assertFalse((local / "diffusion_models" / ref.name).exists())
            text = format_stage_report(report)
            self.assertIn("コピー合計:", text)
            self.assertNotIn("ref2va", text)

    def test_tight_disk_leaves_the_unet_on_drive(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            drive = root / "drive"
            comfy = root / "comfy"
            for rel in STAGE_FILES:
                path = drive / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"w" * 100)
            for folder in ("diffusion_models", "text_encoders", "vae", "loras"):
                dest = comfy / folder
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.symlink_to(drive / folder, target_is_directory=True)
            report = stage_fl2va_models(drive, comfy, root / "local", free_bytes=300, reserve=0)
            copied = [item["path"] for item in report["copied"]]
            self.assertEqual(copied, list(STAGE_FILES[:3]))
            self.assertIn(STAGE_FILES[3], report["drive"])
            unet_name = Path(STAGE_FILES[3]).name
            self.assertEqual((comfy / "diffusion_models" / unet_name).resolve().parent, (drive / "diffusion_models").resolve())

    def test_phase_report_names_gaps(self) -> None:
        log = "\n".join(
            [
                "# CLIPLoader 12.5s",
                "# UNETLoader 20.0s",
                "# SamplerCustomAdvanced 40.0s",
                "# VAEDecode 3.0s",
                "# VAEDecodeAudio 1.5s",
                "100%|##########| 8/8 [00:32<00:00,  4.05s/it]",
                "Prompt executed in 80.00 seconds",
            ]
        )
        phases = parse_comfy_log(log)
        text = format_phase_report(phases, 90.2)
        self.assertIn("1. テキストエンコーダ: 12.5秒", text)
        self.assertIn("60.0秒, 4.05s/it", text)
        self.assertIn("3. 動画VAE: 3.0秒", text)
        self.assertIn("4. 音声VAE: 1.5秒", text)
        self.assertIn("5. 投入から保存まで: 90.2秒", text)
        empty = format_phase_report(parse_comfy_log(""), 1.0)
        self.assertIn("1. テキストエンコーダ: 未計測", empty)
        self.assertIn("2. 拡散ループ: 未計測", empty)

    def test_frames_stay_on_the_grid(self) -> None:
        self.assertEqual(validate_frames(260), 260)
        self.assertEqual(validate_frames(243), 243)
        self.assertEqual(FL2VA_FRAMES, 260)
        for bad in (244, 123, 362):
            with self.assertRaises(RemakeError):
                validate_frames(bad)
        prompt = build_fl2va_prompt(
            first_file="sakura-16x9-open.jpg",
            last_file="sakura-16x9-yokai-end.jpg",
            video_vae="minimax_h3_video_vae_fp16.safetensors",
            frames=243,
        )
        self.assertEqual(prompt["8"]["inputs"]["length"], 243)
        self.assertEqual(prompt["8"]["inputs"]["width"], 1344)
        self.assertEqual(prompt["8"]["inputs"]["height"], 768)
        self.assertIn("[8.133s-10.125s]", prompt["8"]["inputs"]["prompt"])
        self.assertEqual(prompt["6"]["inputs"]["steps"], 8)
        self.assertIn("LoraLoaderModelOnly", [item["class_type"] for item in prompt.values()])


if __name__ == "__main__":
    unittest.main()
