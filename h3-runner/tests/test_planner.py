"""Plan, request JSON, and frame grid. No GPU and no diffusers install."""

from __future__ import annotations

import inspect
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from h3_runner.cli import build_from_args, main, parse_args, resolve_vram_gb  # noqa: E402
from h3_runner.ffmpeg_join import clip_is_done, join_command, probe_text_is_done  # noqa: E402
from h3_runner.loras import (  # noqa: E402
    COMBAT_FILENAME,
    COMBAT_REPO,
    REPAIR_FILENAME,
    REPAIR_REPO,
    TURBO_FILENAME,
    TURBO_REPO,
    classify_lora_header,
    inspect_lora_file,
    parse_lora_args,
    read_safetensors_header,
    prepare_fast_loras,
    reject_pruned_adaln,
)
from h3_runner.official import (  # noqa: E402
    align_num_frames,
    build_video_request,
    diffusers_accepts,
    frames_for_seconds,
    resolve_canvas_size,
)
from h3_runner.planner import choose_short_edges, orbis01_plan, sequence_proxy, within_fit_budget  # noqa: E402
from h3_runner.weights import (  # noqa: E402
    LOCAL_FREE_FLOOR_BYTES,
    allow_patterns,
    bytes_needed,
    disk_preview,
    folders_for,
    folders_for_tasks,
    prepare_all,
    select_repo_files,
    shard_is_current,
    snapshot_kwargs_for,
    stored_bytes,
    wait_for_local_free,
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
        fl2 = build_video_request(
            task="fl2va",
            prompt="integrated_multimodal_description: [Shot 1] water\n",
            duration_s=6,
            aspect_ratio="9:16",
            short_edge=768,
            seed=0,
            steps=9,
            image_uri="file:///tmp/sakura-ref.jpg",
            flow_shift=6.0,
        )
        self.assertEqual(fl2["task"], "fl2va")
        self.assertEqual(
            fl2["conditions"],
            [{"type": "image", "uri": "file:///tmp/sakura-ref.jpg", "role": "keyframe", "frame_index": 0}],
        )
        self.assertEqual(fl2["num_inference_steps"], 9)
        self.assertEqual(fl2["flow_shift"], 6.0)


class PresetTest(unittest.TestCase):
    def test_default_is_split_and_inside_published_budget(self) -> None:
        plan = orbis01_plan(ROOT, Path("/tmp/h3-out"), vram_gb=80, host_ram_gb=83)
        self.assertIsNone(plan.blocked)
        self.assertEqual(plan.offload, "int8")
        self.assertEqual([job.task for job in plan.jobs], ["fl2va", "fl2va"])
        self.assertEqual([job.requested_s for job in plan.jobs], [6.0, 9.0])
        self.assertEqual([job.steps for job in plan.jobs], [9, 9])
        self.assertTrue(str(plan.jobs[0].image_path).endswith("sakura-ref.jpg"))
        self.assertTrue(str(plan.jobs[1].image_path).endswith("sakura-ref.jpg"))
        self.assertEqual(plan.jobs[0].num_frames, 158)
        self.assertEqual(plan.jobs[1].num_frames, 226)
        self.assertEqual(plan.jobs[0].short_edges[0], 768)
        self.assertEqual((plan.jobs[0].height, plan.jobs[0].width), (1344, 768))
        self.assertEqual(plan.jobs[1].short_edges[0], 656)
        self.assertEqual((plan.jobs[1].width, plan.jobs[1].height), (640, 1152))
        self.assertEqual(plan.jobs[0].out_path.name, "orbis01_fl2va_6s.mp4")
        self.assertEqual(plan.jobs[1].out_path.name, "orbis01_fl2va_9s.mp4")
        for job in plan.jobs:
            self.assertTrue(within_fit_budget(job.task, job.num_frames, job.height, job.width))
            body = job.request_json(job.short_edges[0], "file:///tmp/sakura-ref.jpg")
            self.assertEqual(body["conditions"][0]["role"], "keyframe")
            self.assertEqual(body["conditions"][0]["frame_index"], 0)
            self.assertEqual(body["flow_shift"], 6.0)
        self.assertEqual(plan.video_shift, 6.0)
        self.assertNotIn("LoRA は使わない", "\n".join(plan.notes))
        self.assertIn("モデル評価は 8 回", "\n".join(plan.notes))
        self.assertTrue(plan.trim)
        self.assertEqual(plan.delivery_path.name, "orbis01.mp4")

    def test_bf16_when_host_ram_can_hold_both_weights(self) -> None:
        plan = orbis01_plan(ROOT, Path("/tmp/h3-out"), vram_gb=80, host_ram_gb=160)
        self.assertEqual(plan.offload, "bf16")

    def test_96gb_uses_bf16_and_the_fl2va_canvases(self) -> None:
        plan = orbis01_plan(ROOT, Path("/tmp/h3-out"), vram_gb=95.0, host_ram_gb=176.9)
        self.assertIsNone(plan.blocked)
        self.assertEqual(plan.offload, "bf16")
        self.assertEqual(plan.jobs[0].short_edges[0], 768)
        self.assertEqual(plan.jobs[1].short_edges[0], 656)
        self.assertEqual((plan.jobs[1].width, plan.jobs[1].height), (640, 1152))
        self.assertIn("トークン予算", "\n".join(plan.notes))

    def test_ref2va_nine_seconds_stays_on_the_published_canvas(self) -> None:
        self.assertEqual(choose_short_edges("ref2va", 226, "9:16")[0], 352)
        self.assertLess(
            sequence_proxy("ref2va", 226, 640, 352),
            sequence_proxy("ref2va", 124, 512, 896) + 1,
        )

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
        self.assertEqual(folders_for("fl2va"), folders_for("t2va"))
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

    def test_colab_drive_statvfs_does_not_stop(self) -> None:
        tasks = ["t2va", "ref2va"]
        preview = disk_preview(
            Path("/content/drive/MyDrive/h3-weights/MiniMax-H3"),
            tasks,
            free_bytes=209_400_000_000,
            sizes={},
        )
        self.assertTrue(preview.ok)
        self.assertIn("Colab のマウントは VM ディスクの値を返すので Drive 実容量ではない", preview.text)
        self.assertNotIn("止める", preview.text)

    def test_select_repo_files_skips_comfy_trees(self) -> None:
        class Entry:
            def __init__(self, path: str, size: int | None) -> None:
                self.path = path
                self.size = size

        entries = [
            Entry("FL2VA/model.safetensors", 100),
            Entry("Ref2VA/model.safetensors", 100),
            Entry("assets/pic.png", 9),
            Entry("README.md", 9),
            Entry("text_encoder", None),
            Entry("transformer/a.safetensors", 10),
            Entry("transformer_ref/b.safetensors", 20),
            Entry("text_encoder/c.safetensors", 30),
            Entry("vae/d.safetensors", 40),
            Entry("audio_vae/e.safetensors", 5),
            Entry("tokenizer/tokenizer.json", 1),
            Entry("processor/preprocessor_config.json", 1),
            Entry("scheduler/scheduler_config.json", 2),
            Entry("audio_scheduler/scheduler_config.json", 2),
            Entry("modular_model_index.json", 3),
            Entry("model_index.json", 4),
        ]
        picked = dict(select_repo_files(entries, ["t2va", "ref2va"]))
        self.assertNotIn("FL2VA/model.safetensors", picked)
        self.assertNotIn("Ref2VA/model.safetensors", picked)
        self.assertNotIn("README.md", picked)
        self.assertEqual(picked["transformer/a.safetensors"], 10)
        self.assertEqual(picked["transformer_ref/b.safetensors"], 20)
        self.assertEqual(picked["modular_model_index.json"], 3)

    def test_shard_skip_matches_size(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "shard.safetensors"
            path.write_bytes(b"abcd")
            self.assertTrue(shard_is_current(path, 4))
            self.assertFalse(shard_is_current(path, 5))
            self.assertFalse(shard_is_current(Path(tmp) / "missing.safetensors", 4))

    def test_wait_until_local_free_recovers(self) -> None:
        seen = {"n": 0}

        def free() -> int:
            seen["n"] += 1
            if seen["n"] < 3:
                return 10_000_000_000
            return 40_000_000_000

        sleeps: list[float] = []
        got = wait_for_local_free(
            LOCAL_FREE_FLOOR_BYTES,
            free_fn=free,
            sleeper=lambda seconds: sleeps.append(seconds),
            sync_fn=lambda: None,
        )
        self.assertEqual(got, 40_000_000_000)
        self.assertEqual(len(sleeps), 2)
        self.assertEqual(bytes_needed(LOCAL_FREE_FLOOR_BYTES, 5_000_000_000, 3), LOCAL_FREE_FLOOR_BYTES + 15_000_000_000)

    def test_prepare_downloads_one_shard_at_a_time(self) -> None:
        text = inspect.getsource(prepare_all)
        self.assertIn("hf_hub_download", text)
        self.assertNotIn("snapshot_download", text)
        self.assertNotIn("flush_and_unmount()", text)
        self.assertIn("sync_disk()", text)
        module = (ROOT / "h3_runner" / "weights.py").read_text(encoding="utf-8")
        self.assertNotIn("flush_and_unmount()", module)

    def test_loader_stays_on_the_local_snapshot(self) -> None:
        text = (ROOT / "h3_runner" / "generate.py").read_text(encoding="utf-8")
        self.assertIn("local_files_only=True", text)
        self.assertNotIn("from_pretrained(\n        MODEL_ID", text)
        self.assertNotIn("from_pretrained(MODEL_ID", text)
        self.assertNotIn("snapshot_download", text)
        self.assertNotIn("prepare_all", text)
        self.assertIn('kwargs["image"]', text)
        fuse = text[text.index("def _fuse_loras"): text.index("def _load_bf16")]
        self.assertIn("load_into_transformer_ref=into_ref", fuse)
        self.assertIn('task == "ref2va"', fuse)
        self.assertIn("scale={spec.scale:g}", fuse)
        self.assertLess(fuse.index("load_lora_weights"), fuse.index("set_adapters"))
        self.assertLess(fuse.index("set_adapters"), fuse.index("fuse_lora()"))
        self.assertLess(fuse.index("fuse_lora()"), fuse.index("unload_lora_weights()"))
        load = text[text.index("def _load_bf16"): text.index("def _quantized_transformer")]
        self.assertLess(load.index("load_components"), load.index("_fuse_loras("))
        self.assertLess(load.index("_fuse_loras("), load.index("enable_auto_cpu_offload"))
        self.assertLess(load.index("enable_auto_cpu_offload"), load.index("_apply_shifts("))
        self.assertIn("set_shift", text)
        self.assertIn("int8 経路では LoRA を無効にする", text)


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


def _pack_safetensors(path: Path, tensors: dict[str, tuple[int, ...]]) -> None:
    header: dict[str, dict] = {}
    offset = 0
    blobs: list[bytes] = []
    for name, shape in tensors.items():
        count = 1
        for dim in shape:
            count *= dim
        nbytes = count * 4
        header[name] = {"dtype": "F32", "shape": list(shape), "data_offsets": [offset, offset + nbytes]}
        offset += nbytes
        blobs.append(b"\x00" * nbytes)
    raw = json.dumps(header).encode()
    path.write_bytes(len(raw).to_bytes(8, "little") + raw + b"".join(blobs))


class LoraHeaderTest(unittest.TestCase):
    def test_pruned_adaln_width_8_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "pruned.safetensors"
            _pack_safetensors(
                path,
                {
                    "diffusion_model.blocks.0.adaln_proj.linear.lora_A.weight": (16, 8),
                    "diffusion_model.blocks.0.attn.qkv_proj.lora_A.weight": (16, 2688),
                },
            )
            with self.assertRaises(ValueError) as caught:
                reject_pruned_adaln(path)
            self.assertIn("Pruned", str(caught.exception))
            self.assertIn("8", str(caught.exception))

    def test_release_adaln_width_is_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "release.safetensors"
            _pack_safetensors(
                path,
                {"blocks.0.adaln_proj.linear.lora_A.weight": (16, 2688)},
            )
            reject_pruned_adaln(path)

    def test_lora_b_does_not_count_as_the_input_width(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "up_only.safetensors"
            _pack_safetensors(
                path,
                {"blocks.0.adaln_proj.linear.lora_B.weight": (16, 8)},
            )
            reject_pruned_adaln(path)


def _native_lora(path: Path) -> None:
    _pack_safetensors(
        path,
        {
            "diffusion_model.blocks.0.attn.qkv_proj.lora_A.weight": (2, 4),
            "diffusion_model.blocks.0.attn.qkv_proj.lora_B.weight": (6, 2),
        },
    )


class LoraPrepareTest(unittest.TestCase):
    def test_existing_files_are_skipped(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            names = [TURBO_FILENAME, REPAIR_FILENAME, COMBAT_FILENAME]
            for name in names:
                _native_lora(root / name)

            def boom(*_args, **_kwargs):
                raise AssertionError("download was called")

            written = prepare_fast_loras(root, hub_download=boom)
            self.assertEqual([path.name for path in written], names)

    def test_combat_comes_from_huggingface(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            calls: list[tuple[str, str]] = []

            def hub(repo, filename, local_dir):
                calls.append((repo, filename))
                dest = Path(local_dir) / filename
                _native_lora(dest)
                return dest

            written = prepare_fast_loras(root, hub_download=hub)
            self.assertEqual(
                [path.name for path in written],
                [TURBO_FILENAME, REPAIR_FILENAME, COMBAT_FILENAME],
            )
            self.assertEqual(
                calls,
                [
                    (TURBO_REPO, TURBO_FILENAME),
                    (REPAIR_REPO, REPAIR_FILENAME),
                    (COMBAT_REPO, COMBAT_FILENAME),
                ],
            )
            self.assertTrue((root / COMBAT_FILENAME).is_file())

    def test_repair_v2_key_pattern_is_native_and_not_pruned(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / REPAIR_FILENAME
            # Live Motion_Repair_V2.safetensors uses these module names (ai-toolkit, no AdaLN).
            _pack_safetensors(
                path,
                {
                    "diffusion_model.blocks.0.attn.out_proj.lora_A.weight": (2, 4),
                    "diffusion_model.blocks.0.attn.out_proj.lora_B.weight": (4, 2),
                    "diffusion_model.blocks.0.attn.qkv_proj.lora_A.weight": (2, 4),
                    "diffusion_model.blocks.0.attn.qkv_proj.lora_B.weight": (4, 2),
                    "diffusion_model.blocks.0.mlp.fc1.lora_A.weight": (2, 4),
                    "diffusion_model.blocks.0.mlp.fc1.lora_B.weight": (4, 2),
                    "diffusion_model.blocks.0.mlp.fc2.lora_A.weight": (2, 4),
                    "diffusion_model.blocks.0.mlp.fc2.lora_B.weight": (4, 2),
                },
            )
            self.assertEqual(classify_lora_header(read_safetensors_header(path)), "native")
            self.assertEqual(inspect_lora_file(path), "native")

    def test_unknown_lora_keys_are_refused(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "odd.safetensors"
            _pack_safetensors(path, {"not_a_lora.weight": (2, 2)})
            with self.assertRaises(ValueError) as caught:
                inspect_lora_file(path)
            self.assertIn("load_lora_weights", str(caught.exception))

    def test_parse_repeated_lora_args(self) -> None:
        specs = parse_lora_args(
            [
                "/content/drive/MyDrive/h3-weights/loras/turbo.safetensors:1.0",
                "/content/drive/MyDrive/h3-weights/loras/H3_Combat_V2.safetensors:0.7",
            ]
        )
        self.assertEqual([item.scale for item in specs], [1.0, 0.7])
        self.assertEqual(specs[0].name, "turbo")
        self.assertEqual(specs[1].name, "H3_Combat_V2")


class FastCliTest(unittest.TestCase):
    def test_preset_defaults_to_fl2va_and_keeps_lora_on_bf16(self) -> None:
        args = parse_args(
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
                "--offload",
                "bf16",
                "--lora",
                "/tmp/turbo.safetensors:1",
                "--lora",
                "/tmp/combat.safetensors:0.7",
                "--video-shift",
                "6",
            ]
        )
        plan = build_from_args(args)
        self.assertEqual([job.task for job in plan.jobs], ["fl2va", "fl2va"])
        self.assertEqual([job.steps for job in plan.jobs], [9, 9])
        self.assertEqual([(item.name, item.scale) for item in plan.loras], [("turbo", 1.0), ("combat", 0.7)])
        self.assertEqual(plan.video_shift, 6.0)

    def test_int8_disables_lora(self) -> None:
        args = parse_args(
            [
                "--preset",
                "orbis01",
                "--out-dir",
                "/tmp/h3-out",
                "--vram-gb",
                "40",
                "--host-ram-gb",
                "83",
                "--offload",
                "int8",
                "--lora",
                "/tmp/turbo.safetensors:1.0",
            ]
        )
        plan = build_from_args(args)
        self.assertEqual(plan.offload, "int8")
        self.assertEqual(plan.loras, [])
        self.assertIn("無効", plan.report())

    def test_fl2va_explicit_canvas_dry_run(self) -> None:
        code = main(
            [
                "--task",
                "fl2va",
                "--prompt-file",
                str(ROOT / "prompts" / "orbis01_t2va_6s.txt"),
                "--image",
                str(ROOT / "assets" / "sakura-ref.jpg"),
                "--duration",
                "6",
                "--width",
                "768",
                "--height",
                "1344",
                "--steps",
                "9",
                "--seed",
                "0",
                "--out",
                "/tmp/h3-out/test_b.mp4",
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
        self.assertEqual(TURBO_REPO, "lightx2v/Minimax-h3-Turbo")

    def test_notebook_has_the_fast_cells(self) -> None:
        notebook = json.loads((ROOT / "minimax_h3_still.ipynb").read_text(encoding="utf-8"))
        blobs = ["".join(cell["source"]) for cell in notebook["cells"]]
        weight = blobs[9]
        self.assertIn("prepare_fast_loras", weight)
        self.assertNotIn("CIVITAI_TOKEN", weight)
        joined = "".join(blobs)
        self.assertNotIn("fireworker06", joined)
        self.assertIn("force_remount=True", joined)
        self.assertIn("WEIGHTS_FOLDER", joined)
        self.assertIn("H3_Combat_V2.safetensors", joined)
        self.assertIn("minimax_h3_fl2v_turbo_8step_v1.0_768p_comfyui_bf16.safetensors", joined)
        self.assertIn("JOKER141/MiniMax-H3-Combat-Base-V2", blobs[8])
        self.assertIn("JOKER141/MiniMax-H3-General-Motion-Continuity-Repair", blobs[8])
        self.assertIn("Motion_Repair_V2.safetensors", joined)
        self.assertNotIn("3366092", joined)
        self.assertNotIn("3246572", joined)
        self.assertNotIn("combat_base_v2", joined)
        test = blobs[16]
        self.assertIn("test_b_fl2va_turbo.mp4", test)
        self.assertIn("test_c_turbo_combat.mp4", test)
        self.assertIn("test_dp_turbo_repair.mp4", test)
        self.assertIn("次へ進む", test)
        self.assertIn("768", test)
        self.assertIn("1344", test)
        self.assertIn('"--steps", "9"', test)
        self.assertIn("orbis01_6s.mp4", test)


if __name__ == "__main__":
    unittest.main()
