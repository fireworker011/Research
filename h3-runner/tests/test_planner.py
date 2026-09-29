"""Plan, request JSON, and frame grid. No GPU and no diffusers install."""

from __future__ import annotations

import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from h3_runner.cli import main, resolve_vram_gb  # noqa: E402
from h3_runner.ffmpeg_join import clip_is_done, join_command, probe_text_is_done  # noqa: E402
from h3_runner.official import (  # noqa: E402
    align_num_frames,
    build_video_request,
    diffusers_accepts,
    frames_for_seconds,
    resolve_canvas_size,
)
from h3_runner.planner import orbis01_plan, sequence_proxy, within_fit_budget  # noqa: E402
from h3_runner.weights import (  # noqa: E402
    allow_patterns,
    disk_preview,
    folders_for,
    folders_for_tasks,
    snapshot_kwargs_for,
    stored_bytes,
)


class OfficialMathTest(unittest.TestCase):
    def test_portrait_768_matches_diffusers_rounding(self) -> None:
        self.assertEqual(resolve_canvas_size(9, 16, short_edge=768), (1344, 768))
        self.assertEqual(resolve_canvas_size(16, 9, short_edge=768), (768, 1344))
        self.assertEqual(resolve_canvas_size(9, 16, short_edge=512), (896, 512))

    def test_duration_grid(self) -> None:
        self.assertEqual(align_num_frames(frames_for_seconds(15)), 362)
        self.assertFalse(diffusers_accepts(frames_for_seconds(15)))
        self.assertEqual(align_num_frames(frames_for_seconds(6)), 158)
        self.assertTrue(diffusers_accepts(frames_for_seconds(6)))
        self.assertEqual(align_num_frames(frames_for_seconds(9)), 226)
        self.assertTrue(diffusers_accepts(frames_for_seconds(9)))
        self.assertEqual(align_num_frames(frames_for_seconds(5)), 124)
        self.assertFalse(diffusers_accepts(frames_for_seconds(4)))

    def test_request_shape(self) -> None:
        ref = build_video_request(
            task="ref2va",
            prompt="subject_definitions:\n<Picture 1>\n",
            duration_s=9,
            aspect_ratio="9:16",
            short_edge=512,
            seed=7,
            image_uri="file:///tmp/sakura-ref.jpg",
        )
        self.assertEqual(ref["task"], "ref2va")
        self.assertEqual(ref["conditions"], [{"type": "image", "uri": "file:///tmp/sakura-ref.jpg", "role": "reference"}])
        self.assertEqual(ref["target"]["aspect_ratio"], "9:16")
        self.assertEqual(ref["target"]["duration_seconds"], 9)
        self.assertNotIn("video", json.dumps(ref["conditions"]))
        text = build_video_request(
            task="t2va",
            prompt="integrated_multimodal_description: [Shot 1] water\n",
            duration_s=6,
            aspect_ratio="9:16",
            short_edge=768,
            seed=7,
        )
        self.assertEqual(text["conditions"], [])
        self.assertEqual(text["flow_shift"], 12.0)
        self.assertEqual(text["audio_flow_shift"], 3.0)


class PresetTest(unittest.TestCase):
    def test_default_is_split_and_inside_published_budget(self) -> None:
        plan = orbis01_plan(ROOT, Path("/tmp/h3-out"), vram_gb=80, host_ram_gb=83)
        self.assertIsNone(plan.blocked)
        self.assertEqual(plan.offload, "int8")
        self.assertEqual([job.task for job in plan.jobs], ["t2va", "ref2va"])
        self.assertEqual([job.requested_s for job in plan.jobs], [6.0, 9.0])
        self.assertIsNone(plan.jobs[0].image_path)
        self.assertTrue(str(plan.jobs[1].image_path).endswith("sakura-ref.jpg"))
        self.assertEqual(plan.jobs[0].num_frames, 158)
        self.assertEqual(plan.jobs[1].num_frames, 226)
        self.assertEqual(plan.jobs[0].short_edges[0], 768)
        self.assertEqual((plan.jobs[0].height, plan.jobs[0].width), (1344, 768))
        for job in plan.jobs:
            self.assertTrue(within_fit_budget(job.task, job.num_frames, job.height, job.width))
        self.assertLess(
            sequence_proxy("ref2va", 226, plan.jobs[1].height, plan.jobs[1].width),
            sequence_proxy("ref2va", 124, 512, 896) + 1,
        )
        self.assertIn("LoRA は使わない", "\n".join(plan.notes))
        self.assertTrue(plan.trim)
        self.assertEqual(plan.delivery_path.name, "orbis01.mp4")

    def test_bf16_when_host_ram_can_hold_both_weights(self) -> None:
        plan = orbis01_plan(ROOT, Path("/tmp/h3-out"), vram_gb=80, host_ram_gb=160)
        self.assertEqual(plan.offload, "bf16")

    def test_96gb_keeps_ref_canvas_and_uses_bf16(self) -> None:
        plan = orbis01_plan(ROOT, Path("/tmp/h3-out"), vram_gb=95.0, host_ram_gb=176.9)
        self.assertIsNone(plan.blocked)
        self.assertEqual(plan.offload, "bf16")
        self.assertEqual(plan.jobs[1].short_edges[0], 352)
        self.assertEqual((plan.jobs[1].width, plan.jobs[1].height), (352, 640))
        self.assertIn("据え置き", "\n".join(plan.notes))

    def test_40gb_uses_the_official_int8_recipe(self) -> None:
        plan = orbis01_plan(ROOT, Path("/tmp/h3-out"), vram_gb=39.5, host_ram_gb=83.5)
        self.assertIsNone(plan.blocked)
        self.assertEqual(plan.offload, "int8")
        self.assertEqual(plan.jobs[0].short_edges[0], 768)
        self.assertIn("24〜32GB", "\n".join(plan.notes))

    def test_below_consumer_card_is_blocked(self) -> None:
        plan = orbis01_plan(ROOT, Path("/tmp/h3-out"), vram_gb=16, host_ram_gb=83)
        self.assertIsNotNone(plan.blocked)

    def test_force_one_shot_uses_legal_ceiling(self) -> None:
        plan = orbis01_plan(
            ROOT, Path("/tmp/h3-out"), vram_gb=80, host_ram_gb=83, force_one_shot=True
        )
        self.assertEqual(len(plan.jobs), 1)
        self.assertEqual(plan.jobs[0].num_frames, 345)
        self.assertAlmostEqual(plan.jobs[0].aligned_s, 14.375)
        self.assertTrue(within_fit_budget("ref2va", 345, plan.jobs[0].height, plan.jobs[0].width))

    def test_prompts_follow_the_skill_shapes(self) -> None:
        ref = (ROOT / "prompts" / "orbis01_ref2va_15s.txt").read_text(encoding="utf-8")
        t2 = (ROOT / "prompts" / "orbis01_t2va_6s.txt").read_text(encoding="utf-8")
        ref9 = (ROOT / "prompts" / "orbis01_ref2va_9s.txt").read_text(encoding="utf-8")
        for name in (
            "subject_definitions:",
            "summary:",
            "retention_analysis:",
            "detailed_description:",
            "overall_soundscape:",
            "non_diegetic_music:",
        ):
            self.assertIn(name, ref)
            self.assertIn(name, ref9)
        self.assertIn("<Picture 1>", ref)
        self.assertNotIn("<Video ", ref)
        self.assertTrue(t2.startswith("integrated_multimodal_description:"))
        self.assertNotIn("subject_definitions:", t2)
        self.assertNotIn("<Picture ", t2)


class CliTest(unittest.TestCase):
    def test_dry_run_preset(self) -> None:
        code = main(
            [
                "--preset",
                "orbis01",
                "--out-dir",
                "/tmp/h3-out",
                "--dry-run",
                "--vram-gb",
                "95",
                "--host-ram-gb",
                "176.9",
                "--cache-dir",
                "/tmp/h3-cache",
            ]
        )
        self.assertEqual(code, 0)

    def test_unknown_flag_is_argparse_exit_2(self) -> None:
        with self.assertRaises(SystemExit) as caught:
            main(["--not-a-real-flag"])
        self.assertEqual(caught.exception.code, 2)

    def test_four_seconds_is_refused(self) -> None:
        with self.assertRaises(SystemExit) as caught:
            main(
                [
                    "--task",
                    "t2va",
                    "--prompt-file",
                    str(ROOT / "prompts" / "orbis01_t2va_6s.txt"),
                    "--duration",
                    "4",
                    "--out",
                    "/tmp/h3-out/four.mp4",
                    "--dry-run",
                    "--vram-gb",
                    "80",
                    "--host-ram-gb",
                    "83",
                ]
            )
        self.assertIn("5", str(caught.exception))

    def test_same_entry_selects_t2va_without_image(self) -> None:
        code = main(
            [
                "--task",
                "t2va",
                "--prompt-file",
                str(ROOT / "prompts" / "orbis01_t2va_6s.txt"),
                "--duration",
                "6",
                "--aspect",
                "9:16",
                "--seed",
                "3",
                "--out",
                "/tmp/h3-out/t2va.mp4",
                "--dry-run",
                "--vram-gb",
                "80",
                "--host-ram-gb",
                "83",
            ]
        )
        self.assertEqual(code, 0)


class FfmpegTest(unittest.TestCase):
    def test_join_trims_to_six_and_nine_and_scales(self) -> None:
        command = join_command(
            [(Path("a.mp4"), 6.0), (Path("b.mp4"), 9.0)],
            Path("out.mp4"),
        )
        script = " ".join(command)
        self.assertIn("trim=duration=6.000", script)
        self.assertIn("trim=duration=9.000", script)
        self.assertIn("scale=1080:1920", script)
        self.assertIn("[v0][a0][v1][a1]concat=n=2", script)
        self.assertIn("-ar 32000", script)

    def test_resume_probe_requires_video_and_duration(self) -> None:
        text = "codec_type=video\ncodec_type=audio\nduration=6.583\n"
        self.assertTrue(probe_text_is_done(text, 6.0))
        self.assertFalse(probe_text_is_done("codec_type=audio\nduration=6.583\n", 6.0))
        self.assertFalse(probe_text_is_done(text, 9.0))
        self.assertFalse(clip_is_done(Path("/tmp/h3-missing-clip.mp4"), min_seconds=6.0))


class WeightsTest(unittest.TestCase):
    def test_patterns_skip_the_comfy_trees_and_the_other_denoiser(self) -> None:
        t2va = allow_patterns(folders_for("t2va"))
        ref = allow_patterns(folders_for("ref2va"))
        both = allow_patterns(folders_for_tasks(["t2va", "ref2va"]))
        self.assertTrue(any(item.startswith("transformer/") for item in t2va))
        self.assertFalse(any(item.startswith("transformer_ref/") for item in t2va))
        self.assertTrue(any(item.startswith("transformer_ref/") for item in ref))
        self.assertTrue(any(item.startswith("transformer/") for item in both))
        self.assertTrue(any(item.startswith("transformer_ref/") for item in both))
        self.assertFalse(any("FL2VA" in item or "Ref2VA" in item for item in t2va + ref + both))
        ignored = " ".join(snapshot_kwargs_for(folders_for_tasks(["t2va", "ref2va"]))["ignore_patterns"])
        self.assertIn("FL2VA/**", ignored)
        self.assertIn("Ref2VA/**", ignored)
        self.assertAlmostEqual(stored_bytes(["t2va", "ref2va"]) / 1e9, 210.3, places=1)

    def test_tiny_torch_vram_is_not_a_real_card(self) -> None:
        self.assertEqual(resolve_vram_gb(0.0, 95.0), 95.0)
        self.assertIsNone(resolve_vram_gb(0.0, None))
        self.assertEqual(resolve_vram_gb(95.0, 40.0), 95.0)

    def test_both_weights_need_about_210gb(self) -> None:
        tasks = ["t2va", "ref2va"]
        self.assertTrue(
            disk_preview(Path("/tmp/h3-cache-missing"), tasks, free_bytes=220_000_000_000, sizes={}).ok
        )
        tight = disk_preview(Path("/tmp/h3-cache-missing"), tasks, free_bytes=180_000_000_000, sizes={})
        self.assertFalse(tight.ok)
        self.assertIn("止める", tight.text)
        self.assertIn("ゴミ箱", tight.text)

    def test_loader_stays_on_the_local_snapshot(self) -> None:
        text = (ROOT / "h3_runner" / "generate.py").read_text(encoding="utf-8")
        self.assertIn("local_files_only=True", text)
        self.assertNotIn("from_pretrained(\n        MODEL_ID", text)
        self.assertNotIn("from_pretrained(MODEL_ID", text)
        self.assertNotIn("snapshot_download", text)
        self.assertNotIn("prepare_all", text)


class SecretScanTest(unittest.TestCase):
    def test_tree_has_no_tokens(self) -> None:
        pattern = re.compile(r"(hf_[A-Za-z0-9]{8,}|sk-[A-Za-z0-9]{8,}|BEGIN PRIVATE KEY|MINIMAX_API_KEY)")
        for path in ROOT.rglob("*"):
            if not path.is_file() or path.suffix in {".jpg", ".pyc"}:
                continue
            if "__pycache__" in path.parts or path.name == "test_planner.py":
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            self.assertIsNone(pattern.search(text), f"{path} looks like it contains a token")


if __name__ == "__main__":
    unittest.main()
