"""Syntax and behavior checks for the Wan VACE Colab pipeline. No GPU, no network."""

from __future__ import annotations

import ast
import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from wan_vace.camera import CameraSpec, apply_camera, merge_pose_depth
from wan_vace.controls import load_control, wan_length
from wan_vace.download_manifest import DEPTH_FILES, FILES
from wan_vace.drive_models import DriveModelsError, link_comfy_models, present_filenames, require_wan
from wan_vace.guides import focus_at, pose_at, write_guides
from wan_vace.paths import (
    BRANCH,
    CLIP_NAME,
    DRIVE_MODELS,
    FACE_REF,
    LORA_LIGHTX2V,
    LORA_SAKURA,
    LORA_STYLE,
    RUNTIME_FILES,
    UNET_FP16,
    UNET_FP8,
    UPSCALE_NAME,
    VAE_NAME,
)
from wan_vace.prompts import load_prompts, with_face_lock
from wan_vace.queue import finished_history, history_mp4, post_prompt, queue_cuts
from wan_vace.workflow import (
    build_prompt,
    describe,
    fast_options,
    linked_nodes,
    options_for_mode,
    quality_options,
)

ROOT = Path(__file__).resolve().parents[1]
TRIAL = Path(__file__).resolve().parent / "trial"
GPU_NOTEBOOK = ROOT / "wan21_vace_colab.ipynb"
CPU_NOTEBOOK = ROOT / "wan21_vace_download_colab.ipynb"
EXAMPLE = Path(__file__).resolve().parent / "workflows" / "wan21_vace_14b_api.json"


def _present() -> set[str]:
    return {LORA_LIGHTX2V, LORA_SAKURA, LORA_STYLE, UPSCALE_NAME, UNET_FP8, UNET_FP16, CLIP_NAME, VAE_NAME}


def _built(cut: str, options=None, present=None, face="sakura-face-crop.jpg"):
    control = load_control(TRIAL / f"{cut}_control.json")
    prompt = with_face_lock(load_prompts(TRIAL / "trial-01-script_v3.md")[cut], (options or fast_options()).face_consistency)
    built = build_prompt(
        control,
        prompt,
        pose_dir=f"/content/wan-vace-work/{cut}/pose",
        depth_dir=f"/content/wan-vace-work/{cut}/depth",
        face_image=face,
        options=options or fast_options(),
        present_files=present if present is not None else _present(),
    )
    linked_nodes(built.prompt)
    return built


class WanVaceTests(unittest.TestCase):
    def test_frame_counts_match_duration(self) -> None:
        expected = {"C1": 37, "C2": 85, "C3": 73, "C4": 37}
        for name, frames in expected.items():
            control = load_control(TRIAL / f"{name}_control.json")
            self.assertEqual(wan_length(control.duration_s, control.fps), frames)
            self.assertEqual(frames % 4, 1)
            self.assertEqual(control.aspect, "9:16")

    def test_prompts_follow_the_script(self) -> None:
        prompts = load_prompts(TRIAL / "trial-01-script_v3.md")
        self.assertIn("no person", prompts["C1"].positive)
        self.assertIn("flooded window", prompts["C1"].positive)
        self.assertNotIn("Sakura", prompts["C1"].positive)
        self.assertNotIn("deformed jaw", prompts["C1"].negative)
        self.assertIn("extra fingers", prompts["C1"].negative)
        self.assertTrue(prompts["C2"].uses_sakura)
        self.assertIn("Sakura", prompts["C2"].positive)
        self.assertIn("deformed jaw", prompts["C2"].negative)
        self.assertIn("no person", prompts["C3"].positive)
        self.assertIn("four fingers", prompts["C4"].positive)
        self.assertIn("extra knuckles", prompts["C4"].negative)
        locked = with_face_lock(prompts["C2"], True)
        self.assertIn("reference image", locked.positive)
        self.assertEqual(with_face_lock(prompts["C1"], True).positive, prompts["C1"].positive)

    def test_pose_and_depth_follow_keyframes(self) -> None:
        c1 = load_control(TRIAL / "C1_control.json")
        self.assertNotEqual(pose_at(c1, 0.0).joints["head"], pose_at(c1, 1.0).joints["head"])
        self.assertLess(focus_at(c1, 0.0)[0], focus_at(c1, 0.25)[0])
        c2 = load_control(TRIAL / "C2_control.json")
        self.assertEqual(pose_at(c2, 1.6).jaw_deg, 15)
        self.assertEqual(pose_at(c2, 3.0).jaw_deg, 0)
        c4 = load_control(TRIAL / "C4_control.json")
        self.assertEqual(pose_at(c4, 8.0).hand_cm, 10)
        self.assertEqual(pose_at(c4, 9.6).hand_cm, 1)
        self.assertEqual(pose_at(c4, 8.0).fingers, 4)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            count = write_guides(c1, root / "pose", root / "depth", 144, 256)
            names = sorted(path.name for path in (root / "pose").glob("*.png"))
            self.assertEqual(len(names), count)
            self.assertEqual(names[0], "00000.png")
            first = Image.open(root / "pose" / names[0])
            later = Image.open(root / "pose" / f"{count - 1:05d}.png")
            self.assertEqual(first.size, (144, 256))
            self.assertNotEqual(first.tobytes(), later.tobytes())

    def test_camera_shifts_and_face_mask_opens(self) -> None:
        image = Image.new("RGB", (32, 32), 0)
        image.putpixel((8, 16), (255, 255, 255))
        spec = CameraSpec(0.25, 0, 0, 0, 0, 0, 0, 0, 1, True, 0)
        warped, masks = apply_camera([image, image.copy()], spec)
        self.assertEqual(warped[0].getpixel((8, 16)), (255, 255, 255))
        self.assertGreater(warped[1].getpixel((16, 16))[0], 200)
        self.assertEqual(masks[0].getpixel((0, 0)), 255)
        protected = CameraSpec(0, 0, 0, 0, 0, 0, 0, 0, 1, True, 1)
        _, masks = apply_camera([image], protected)
        self.assertEqual(masks[0].getpixel((16, 10)), 0)
        pose = Image.new("RGB", (4, 4), 0)
        pose.putpixel((1, 1), (255, 0, 0))
        depth = Image.new("RGB", (4, 4), (40, 40, 40))
        merged = merge_pose_depth(pose, depth)
        self.assertEqual(merged.getpixel((1, 1)), (255, 0, 0))
        self.assertEqual(merged.getpixel((0, 0)), (40, 40, 40))

    def test_workflow_has_face_pose_depth_camera_and_mp4(self) -> None:
        c1 = _built("C1")
        self.assertNotIn("face", c1.prompt)
        self.assertNotIn("reference_image", c1.prompt["vace"]["inputs"])
        c2 = _built("C2")
        prompt = c2.prompt
        self.assertEqual(prompt["face"]["inputs"]["image"], "sakura-face-crop.jpg")
        self.assertEqual(prompt["vace"]["inputs"]["reference_image"], ["face", 0])
        self.assertEqual(prompt["openpose"]["class_type"], "OpenposePreprocessor")
        self.assertEqual(prompt["depth_pre"]["class_type"], "DepthAnythingPreprocessor")
        self.assertEqual(prompt["camera"]["class_type"], "VacePoseDepthCamera")
        self.assertEqual(prompt["vace"]["class_type"], "WanVaceToVideo")
        self.assertEqual(prompt["vace"]["inputs"]["width"], 576)
        self.assertEqual(prompt["vace"]["inputs"]["height"], 1024)
        save = prompt["save"]["inputs"]
        self.assertEqual(save["format"], "video/h264-mp4")
        self.assertEqual(save["pix_fmt"], "yuv420p")
        self.assertEqual(prompt["sampler"]["inputs"]["steps"], 4)
        self.assertEqual(prompt["sampler"]["inputs"]["cfg"], 1.0)
        self.assertEqual(prompt["shift"]["inputs"]["shift"], 8.0)
        self.assertIn("lora_distill", prompt)
        self.assertNotIn("lora_sakura", prompt)
        with_lora = _built("C2", fast_options(sakura_strength=0.6, style_strength=0.4))
        self.assertEqual(with_lora.prompt["lora_sakura"]["inputs"]["strength_model"], 0.6)
        self.assertEqual(with_lora.prompt["lora_style"]["inputs"]["strength_model"], 0.4)
        with self.assertRaises(Exception):
            _built("C2", fast_options(), present=set())
        quality = _built("C2", quality_options())
        self.assertNotIn("lora_distill", quality.prompt)
        self.assertEqual(quality.prompt["sampler"]["inputs"]["steps"], 20)
        self.assertEqual(quality.prompt["sampler"]["inputs"]["cfg"], 5.0)
        rich = _built("C2", fast_options(upscale=True, rife=True, teacache=True))
        self.assertIn("upscale", rich.prompt)
        self.assertEqual(rich.prompt["rife"]["class_type"], "RIFE VFI")
        self.assertEqual(rich.prompt["rife"]["inputs"]["dtype"], "bfloat16")
        self.assertIn("teacache", rich.prompt)
        self.assertGreater(rich.fps, 24)
        with self.assertRaises(Exception):
            _built("C1", fast_options(width=480, height=832))
        text = "\n".join(describe(fast_options()))
        self.assertIn(UNET_FP8, text)
        saved = json.loads(EXAMPLE.read_text(encoding="utf-8"))
        self.assertEqual(saved, _built("C2").prompt)

    def test_drive_link_does_not_download(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            drive = root / "models"
            comfy = root / "ComfyUI" / "models"
            for name in ("diffusion_models", "text_encoders", "vae", "loras"):
                (drive / name).mkdir(parents=True)
            (drive / "diffusion_models" / UNET_FP8).write_bytes(b"x" * 20)
            (drive / "text_encoders" / CLIP_NAME).write_bytes(b"x" * 20)
            (drive / "vae" / VAE_NAME).write_bytes(b"x" * 20)
            (comfy / "vae").mkdir(parents=True)
            (comfy / "vae" / "put_here.txt").write_text("placeholder", encoding="utf-8")
            linked = link_comfy_models(comfy, drive)
            self.assertIn("vae", linked)
            self.assertTrue((comfy / "vae").is_symlink())
            require_wan(drive, UNET_FP8)
            with self.assertRaises(DriveModelsError):
                require_wan(drive, UNET_FP16)
            local = comfy / "loras"
            if local.is_symlink() or local.exists():
                if local.is_symlink():
                    local.unlink()
                else:
                    import shutil
                    shutil.rmtree(local)
            local.mkdir()
            (local / "big.safetensors").write_bytes(b"x" * 1_000_001)
            with self.assertRaises(DriveModelsError):
                link_comfy_models(comfy, drive)
            names = present_filenames(drive)
            self.assertIn(UNET_FP8, names)

    def test_history_and_manifest(self) -> None:
        self.assertIsNone(finished_history({}, "missing"))
        item = finished_history({"p": {"status": {"completed": True}, "outputs": {}}}, "p")
        self.assertIsNotNone(item)
        with self.assertRaises(Exception):
            finished_history({"p": {"status": {"status_str": "error", "messages": []}}}, "p")
        with tempfile.TemporaryDirectory() as tmp:
            mp4 = Path(tmp) / "trial-01" / "C1_00001.mp4"
            mp4.parent.mkdir()
            mp4.write_bytes(b"mp4")
            found = history_mp4(
                {"outputs": {"save": {"gifs": [{"filename": mp4.name, "subfolder": "trial-01", "fullpath": str(mp4)}]}}},
                Path(tmp),
            )
            self.assertEqual(found, mp4)

        class Response:
            def __init__(self, payload: dict) -> None:
                self.payload = json.dumps(payload).encode("utf-8")

            def read(self) -> bytes:
                return self.payload

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

        def opener(request, timeout=30):
            del timeout
            self.assertTrue(request.full_url.endswith("/prompt"))
            return Response({"prompt_id": "abc"})

        self.assertEqual(post_prompt("http://127.0.0.1:8188", {"1": {}}, opener=opener), "abc")

    def test_queue_names_the_four_mp4s(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            drive = root / "models"
            (drive / "loras").mkdir(parents=True)
            (drive / "loras" / LORA_LIGHTX2V).write_bytes(b"x")
            face = root / "sakura-face-crop.jpg"
            face.write_bytes(b"face")
            output = root / "output"
            output.mkdir()
            source = output / "clip.mp4"
            source.write_bytes(b"mp4")
            work = root / "work"
            ids: list[str] = []

            class Response:
                def __init__(self, payload: dict) -> None:
                    self.payload = json.dumps(payload).encode("utf-8")

                def read(self) -> bytes:
                    return self.payload

                def __enter__(self):
                    return self

                def __exit__(self, *args):
                    return False

            def opener(request, timeout=30):
                del timeout
                url = request.full_url
                if url.endswith("/prompt"):
                    ids.append(f"id{len(ids) + 1}")
                    return Response({"prompt_id": ids[-1]})
                prompt_id = url.rstrip("/").rsplit("/", 1)[-1]
                return Response(
                    {
                        prompt_id: {
                            "status": {"completed": True, "status_str": "success"},
                            "outputs": {
                                "save": {
                                    "gifs": [
                                        {
                                            "filename": "clip.mp4",
                                            "subfolder": "",
                                            "fullpath": str(source),
                                        }
                                    ]
                                }
                            },
                        }
                    }
                )

            written = queue_cuts(
                "http://127.0.0.1:8188",
                TRIAL / "trial-01-script_v3.md",
                TRIAL,
                face,
                work,
                output,
                root / "input",
                root / "drive-out",
                drive,
                fast_options(width=144, height=256),
                opener=opener,
            )
            self.assertEqual([path.name for path in written], ["C1.mp4", "C2.mp4", "C3.mp4", "C4.mp4"])
            self.assertTrue((root / "input" / "sakura-face-crop.jpg").is_file())
            c1 = json.loads((root / "drive-out" / "C1.job.json").read_text(encoding="utf-8"))
            self.assertEqual(c1["frames"], 37)
            self.assertEqual(len(ids), 4)
        dests = [item["dest"] for item in FILES]
        self.assertEqual(len(dests), len(set(dests)))
        for item in FILES:
            self.assertTrue(item["url"].startswith("https://"))
            self.assertGreater(item["bytes"], 0)
            self.assertNotIn("token", item["url"])
        self.assertEqual(sum(size for _, size in DEPTH_FILES), 954 + 437 + 99173660)

    def test_notebooks_and_package_list(self) -> None:
        for path in RUNTIME_FILES:
            self.assertTrue((ROOT / path).is_file(), path)
        for notebook_path, gpu in ((GPU_NOTEBOOK, True), (CPU_NOTEBOOK, False)):
            notebook = json.loads(notebook_path.read_text(encoding="utf-8"))
            self.assertEqual(notebook["nbformat"], 4)
            code = []
            for cell in notebook["cells"]:
                source = "".join(cell["source"])
                if cell["cell_type"] == "code":
                    ast.parse(source)
                    code.append(source)
            text = "\n".join(code)
            self.assertIn(BRANCH, text)
            self.assertNotIn("ys73497349", text)
            self.assertNotIn("api_key", text.lower())
            self.assertNotIn("fal.ai", text)
            self.assertNotIn("sk-", text)
            if gpu:
                self.assertNotIn("huggingface.co", text)
                self.assertIn("COMFY_URL", text)
                self.assertIn("runtime.unassign", text)
                self.assertIn("HF_HUB_OFFLINE", text)
                self.assertIn("A100", text)
                self.assertIn(DRIVE_MODELS, text)
                self.assertIn(FACE_REF, text)
                for rel in RUNTIME_FILES:
                    self.assertIn(rel, text)
                self.assertEqual(notebook["metadata"]["accelerator"], "GPU")
                self.assertEqual(notebook["metadata"]["colab"]["gpuType"], "A100")
            else:
                self.assertIn("huggingface.co", text)
                self.assertIn("download_all", text)
                self.assertIn("runtime.unassign", text)
                self.assertNotIn("COMFY_URL", text)
                self.assertEqual(notebook["metadata"]["accelerator"], "CPU")


if __name__ == "__main__":
    unittest.main()
