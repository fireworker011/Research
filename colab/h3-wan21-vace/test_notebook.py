#!/usr/bin/env python3
"""Static-check the VACE notebook and run the JSON loader against C1-C4."""

import ast
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from types import SimpleNamespace

import nbformat
from nbformat.validator import validate
from PIL import Image, ImageDraw

import build_notebook

ROOT = Path(__file__).resolve().parent
NOTEBOOK = ROOT / "wan21_vace_14b_colab.ipynb"
CONTROLS = ROOT / "controls"
FORBIDDEN = (
    "fal.ai",
    "fal.run",
    "a8.net",
    "px.a8",
    "api_key",
    "apikey",
    "secret_key",
    "sk-",
    "AKIA",
    "ghp_",
    "xoxb-",
    "BEGIN PRIVATE KEY",
    "COMFY_URL",
)


def cell_text(cell):
    source = cell.source
    if isinstance(source, list):
        return "".join(source)
    return source


def mean_abs_diff(left, right):
    raw_left = left.tobytes()
    raw_right = right.tobytes()
    if len(raw_left) != len(raw_right):
        raise AssertionError("image sizes differ")
    return sum(abs(a - b) for a, b in zip(raw_left, raw_right)) / len(raw_left)


def mean_luma(image):
    gray = image.convert("L")
    data = gray.tobytes()
    return sum(data) / len(data)


def write_cut(directory, name, payload):
    path = Path(directory) / name
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def comfy_object_info():
    def spec(required, optional=()):
        return {
            "input": {
                "required": {key: ["*"] for key in required},
                "optional": {key: ["*"] for key in optional},
            }
        }

    info = {
        "UNETLoader": spec(("unet_name", "weight_dtype")),
        "CLIPLoader": spec(("clip_name", "type"), ("device",)),
        "VAELoader": spec(("vae_name",)),
        "CLIPTextEncode": spec(("text", "clip")),
        "LoadImage": spec(("image",)),
        "H3LoadFrameDir": spec(("directory",)),
        "WanVaceToVideo": spec(
            ("positive", "negative", "vae", "width", "height", "length", "batch_size", "strength"),
            ("control_video", "control_masks", "reference_image"),
        ),
        "ModelSamplingSD3": spec(("model", "shift")),
        "KSampler": spec(
            (
                "model",
                "positive",
                "negative",
                "latent_image",
                "seed",
                "steps",
                "cfg",
                "sampler_name",
                "scheduler",
                "denoise",
            ),
            ("control_after_generate",),
        ),
        "TrimVideoLatent": spec(("samples", "trim_amount")),
        "VAEDecodeTiled": spec(
            ("samples", "vae", "tile_size"),
            ("overlap", "temporal_size", "temporal_overlap"),
        ),
        "SaveImage": spec(("images", "filename_prefix")),
    }
    info["H3LoadFrameDir"]["output"] = ["IMAGE", "MASK"]
    return info


def base_cut(**overrides):
    payload = {
        "cut": "T0",
        "source_seconds": [0.0, 1.0],
        "aspect": "9:16",
        "fps": 8,
        "openpose_keyframes": [{"t": 0.0, "cat": "front"}],
        "depth": {"focus_sweep": [[0.0, "near"], [1.0, "far"]]},
        "camera_vector": {"translate": [0, 0, 0], "rotate": [0, 0, 0]},
        "duration_s": 1.0,
    }
    payload.update(overrides)
    return payload


def main():
    notebook = nbformat.read(NOTEBOOK, as_version=4)
    validate(notebook)
    code_cells = [cell for cell in notebook.cells if cell.cell_type == "code"]
    if len(code_cells) != 7:
        raise SystemExit(f"expected 7 code cells, got {len(code_cells)}")
    for index, cell in enumerate(code_cells):
        source = cell_text(cell)
        try:
            ast.parse(source)
            compile(source, f"cell_{index}", "exec")
        except SyntaxError as exc:
            raise SystemExit(f"syntax error in code cell {index}: {exc}") from exc

    expected_sources = [
        (ROOT / "cells/01_gpu.py").read_text(encoding="utf-8"),
        (ROOT / "logic.py").read_text(encoding="utf-8"),
        build_notebook.install_source(),
        (ROOT / "cells/04_download.py").read_text(encoding="utf-8"),
        (ROOT / "cells/05_launch.py").read_text(encoding="utf-8"),
        (ROOT / "cells/06_generate.py").read_text(encoding="utf-8"),
        (ROOT / "cells/07_disconnect.py").read_text(encoding="utf-8"),
    ]
    for index, expected in enumerate(expected_sources):
        if cell_text(code_cells[index]) != expected:
            raise SystemExit(f"code cell {index} does not match its source file")
    logic_src = expected_sources[1]
    generate_src = expected_sources[5]
    disconnect_src = expected_sources[6]
    if "flush_and_unmount" not in generate_src or "unassign" not in generate_src:
        raise SystemExit("generate cell does not flush Drive and delete the runtime")
    if "release_runtime()" not in disconnect_src:
        raise SystemExit("disconnect cell does not flush before unassign")
    if "control_masks" not in generate_src or '["frames", 1]' not in generate_src:
        raise SystemExit("control_masks is not wired to WanVaceToVideo")
    if '["decode", 0]' not in generate_src:
        raise SystemExit("save node is not wired to the VAE decode")
    download_src = expected_sources[3]
    if "LOCAL_BASE" not in download_src or "/content/ComfyUI_models" not in download_src:
        raise SystemExit("missing models are not sent to Colab disk")
    if "h3_vace_local" not in download_src or "h3_vace_drive" not in download_src:
        raise SystemExit("extra_model_paths does not list both model locations")
    compile((ROOT / "h3_load_frames.py").read_text(encoding="utf-8"), "h3_load_frames.py", "exec")

    dl = {"_H3_LOAD_ONLY": True}
    exec(download_src, dl)
    drive_base = "/content/drive/MyDrive/ComfyUI_models"
    local_base = "/content/ComfyUI_models"
    te_name = "umt5_xxl_fp8_e4m3fn_scaled.safetensors"
    resolved, downloads = dl["plan_models"](
        dl["MODEL_SPECS"], drive_base, local_base, lambda _path, _min: False
    )
    te_dest = resolved[te_name]
    if not te_dest.startswith(local_base + "/") or drive_base in te_dest:
        raise SystemExit(f"missing text encoder was not aimed at Colab disk: {te_dest}")
    if any(dl["needs_drive_space"](item["dest"], drive_base) for item in downloads):
        raise SystemExit("a missing model still requires Drive space")

    def local_only_free(path):
        if "MyDrive" in str(path) or str(path).startswith("/content/drive"):
            raise SystemExit(f"Drive free space was checked for a local download: {path}")
        return 80_000_000_000

    dl["ensure_download_space"](downloads, local_only_free, drive_base)
    try:
        dl["ensure_download_space"](
            [{"dest": te_dest, "min_bytes": 6_400_000_000}],
            lambda _path: 6_300_000_000,
            drive_base,
        )
    except RuntimeError as exc:
        text = str(exc)
        if not text.startswith("Colab ディスク"):
            raise SystemExit(f"local disk shortage was reported as Drive: {text}")
    else:
        raise SystemExit("a short Colab disk did not stop the download")
    drive_dest = os.path.join(drive_base, "text_encoders", te_name)
    try:
        dl["ensure_download_space"](
            [{"dest": drive_dest, "min_bytes": 6_400_000_000}],
            lambda _path: 6_300_000_000,
            drive_base,
        )
    except RuntimeError as exc:
        if "Drive の空き" not in str(exc):
            raise SystemExit(f"Drive save did not check Drive space: {exc}")
    else:
        raise SystemExit("saving a model to a full Drive was allowed")

    drive_te = os.path.join(drive_base, "text_encoders", te_name)
    clip_te = os.path.join(drive_base, "clip", te_name)
    reused, reused_downloads = dl["plan_models"](
        dl["MODEL_SPECS"],
        drive_base,
        local_base,
        lambda path, _min: path == drive_te,
    )
    if reused[te_name] != drive_te or any(item["name"] == te_name for item in reused_downloads):
        raise SystemExit("an existing Drive text encoder was downloaded again")
    alt, alt_downloads = dl["plan_models"](
        dl["MODEL_SPECS"],
        drive_base,
        local_base,
        lambda path, _min: path == clip_te,
    )
    if alt[te_name] != clip_te or any(item["name"] == te_name for item in alt_downloads):
        raise SystemExit("Drive clip/ alt was ignored")

    yaml = dl["extra_model_yaml"](drive_base, local_base)
    if yaml.find("h3_vace_local") > yaml.find("h3_vace_drive"):
        raise SystemExit("local model path is not registered before Drive")
    if drive_base not in yaml or local_base not in yaml or "text_encoders/" not in yaml:
        raise SystemExit(f"model yaml is missing a location: {yaml}")

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        fake_drive = root / "drive"
        fake_local = root / "local"
        partial = fake_drive / "text_encoders" / te_name
        partial.parent.mkdir(parents=True)
        partial.write_bytes(b"x" * 64)
        local_partial = fake_local / "text_encoders" / te_name
        local_partial.parent.mkdir(parents=True)
        local_partial.write_bytes(b"y" * 64)
        if dl["removable_incomplete"](str(partial), 1000, str(fake_local), str(fake_drive)):
            raise SystemExit("an incomplete Drive file was marked for deletion")
        if not dl["removable_incomplete"](str(local_partial), 1000, str(fake_local), str(fake_drive)):
            raise SystemExit("an incomplete local download was kept")
        sizes = {str(partial): 64}

        def exists(path, min_bytes):
            return sizes.get(path, 0) >= min_bytes

        planned, planned_downloads = dl["plan_models"](
            dl["MODEL_SPECS"], str(fake_drive), str(fake_local), exists
        )
        if not planned[te_name].startswith(str(fake_local)):
            raise SystemExit("a short Drive file was reused")
        if str(partial) in [item["dest"] for item in planned_downloads]:
            raise SystemExit("download dest is the Drive file")

    blob = "\n".join(
        [cell_text(cell) for cell in notebook.cells]
        + [
            logic_src,
            (ROOT / "README.md").read_text(encoding="utf-8"),
            (ROOT / "h3_load_frames.py").read_text(encoding="utf-8"),
            (ROOT / "controls" / "prompts.json").read_text(encoding="utf-8"),
        ]
    )
    for pattern in FORBIDDEN:
        if pattern in blob:
            raise SystemExit(f"forbidden text present: {pattern}")

    gpu_src = cell_text(code_cells[0])
    real_run = subprocess.run

    def run_gpu(stdout, returncode=0, stderr=""):
        def fake(cmd, **kwargs):
            if isinstance(cmd, (list, tuple)) and cmd and cmd[0] == "nvidia-smi":
                return SimpleNamespace(returncode=returncode, stdout=stdout, stderr=stderr)
            return real_run(cmd, **kwargs)

        subprocess.run = fake
        namespace = {}
        try:
            exec(gpu_src, namespace)
        finally:
            subprocess.run = real_run
        return namespace

    try:
        run_gpu("Tesla T4, 15360\n")
    except RuntimeError as exc:
        text = str(exc)
        if "A100" not in text or "止めます" not in text:
            raise SystemExit(f"GPU stop message is unclear: {text}") from exc
    else:
        raise SystemExit("T4 did not stop the notebook")

    try:
        run_gpu("", returncode=1, stderr="no device")
    except RuntimeError as exc:
        if "nvidia-smi" not in str(exc):
            raise SystemExit(f"missing GPU message is unclear: {exc}") from exc
    else:
        raise SystemExit("missing GPU did not stop the notebook")

    gpu_ns = run_gpu("NVIDIA A100-SXM4-40GB, 40960\n")
    if gpu_ns.get("GPU_OK") is not True:
        raise SystemExit("A100 did not set GPU_OK")
    if gpu_ns["_GPU_VRAM"] != 40960:
        raise SystemExit("A100 VRAM was not recorded")
    checks = (
        ("NVIDIA A100-SXM4-40GB", 40536, True),
        ("NVIDIA A100 80GB", 81920, True),
        ("NVIDIA H100 80GB HBM3", 81559, True),
        ("NVIDIA H200", 141000, True),
        ("Tesla T4", 15360, False),
        ("NVIDIA L4", 23034, False),
        ("NVIDIA A10", 23028, False),
        ("NVIDIA GeForce RTX 4090", 24564, False),
        ("NVIDIA A100-SXM4-40GB", 20000, False),
    )
    for name, vram, expected in checks:
        got = gpu_ns["gpu_is_a100_or_better"](name, vram)
        if got is not expected:
            raise SystemExit(f"gpu check {name} {vram} -> {got}, expected {expected}")
    mib_rows = gpu_ns["parse_nvidia_smi"]("NVIDIA A100-SXM4-40GB, 40960 MiB\n")
    if mib_rows != [("NVIDIA A100-SXM4-40GB", 40960)]:
        raise SystemExit(f"MiB suffix was not parsed: {mib_rows}")
    rows = gpu_ns["parse_nvidia_smi"]("Tesla T4, 15360\nNVIDIA A100-SXM4-40GB, 40960\n")
    ok, name, vram, _message = gpu_ns["evaluate_gpus"](rows)
    if not ok or "A100" not in name or vram != 40960:
        raise SystemExit("evaluate_gpus did not pick the A100")

    logic = {}
    exec(cell_text(code_cells[1]), logic)
    cuts = logic["list_cuts"](CONTROLS)
    ids = [cut["cut"] for cut in cuts]
    if ids != ["C1", "C2", "C3", "C4"]:
        raise SystemExit(f"cut order: {ids}")

    by_id = {cut["cut"]: cut for cut in cuts}
    c1 = by_id["C1"]
    c2 = by_id["C2"]
    c3 = by_id["C3"]
    c4 = by_id["C4"]
    if c1["openpose_keyframes"] is not c1["data"]["openpose_keyframes"]:
        raise SystemExit("loader rewrote openpose keyframes")
    if c1["raw_text"] != Path(c1["path"]).read_text(encoding="utf-8"):
        raise SystemExit("raw text does not match the file")
    if json.loads(c1["raw_text"]) != c1["data"]:
        raise SystemExit("parsed data does not match the file")
    if c1["duration_s"] != 1.5 or c1["fps"] != 24:
        raise SystemExit("C1 duration or fps")
    if c1["data"]["openpose_keyframes"][0]["cat"] != "back_to_camera":
        raise SystemExit("C1 first pose")
    if c1["camera_vector"]["shake"]["seed"] != 1:
        raise SystemExit("C1 shake seed")
    if c1["camera_vector"]["translate"] != [0, 0, 0]:
        raise SystemExit("C1 translate")
    if len(c1["depth"]["focus_sweep"]) != 3:
        raise SystemExit("C1 depth sweep")
    if c2["duration_s"] != 3.5 or c2["data"]["jaw_max_deg"] != 15:
        raise SystemExit("C2 duration or jaw limit")
    if c2["depth"].get("sakura_hands") != "defocused":
        raise SystemExit("C2 sakura_hands")
    if c2["data"]["sakura"] != "static":
        raise SystemExit("C2 sakura")
    if len(c2["data"]["caption"]) != 2:
        raise SystemExit("C2 captions")
    if c3["duration_s"] != 3.0:
        raise SystemExit("C3 duration")
    if [kf["cat"] for kf in c3["openpose_keyframes"]] != [
        "front",
        "forepaw_to_mouth",
        "paw_returned",
    ]:
        raise SystemExit("C3 poses")
    if c4["duration_s"] != 1.6 or c4["data"]["contact"] is not False:
        raise SystemExit("C4 duration or contact")
    if c4["data"]["fingers_visible"] != 4 or c4["data"]["hard_cut_before_touch"] is not True:
        raise SystemExit("C4 fingers or hard cut")
    if [kf["wrist_to_handle_cm"] for kf in c4["openpose_keyframes"]] != [10, 4, 1]:
        raise SystemExit("C4 wrist distances")

    expected_vace = {"C1": 37, "C2": 85, "C3": 73, "C4": 41}
    expected_keep = {"C1": 36, "C2": 84, "C3": 72, "C4": 38}
    for cut_id, expected in expected_vace.items():
        got = logic["wan_frame_count"](by_id[cut_id]["duration_s"], by_id[cut_id]["fps"])
        keep = logic["target_frame_count"](by_id[cut_id]["duration_s"], by_id[cut_id]["fps"])
        if got != expected:
            raise SystemExit(f"{cut_id} vace length {got}, expected {expected}")
        if keep != expected_keep[cut_id]:
            raise SystemExit(f"{cut_id} keep frames {keep}, expected {expected_keep[cut_id]}")
        if got < keep or got % 4 != 1:
            raise SystemExit(f"{cut_id} vace length {got} is not 4n+1 above {keep}")
    if logic["vace_length_for_count"](84) != 85 or logic["vace_length_for_count"](81) != 81:
        raise SystemExit("vace length snap")
    if logic["vace_length_for_count"](1) != 1 or logic["vace_length_for_count"](2) != 5:
        raise SystemExit("short vace length")
    try:
        logic["vace_length_for_count"](242)
    except ValueError:
        pass
    else:
        raise SystemExit("over-long cut was accepted")

    def close(got, expected, label):
        if abs(float(got) - float(expected)) > 1e-6:
            raise SystemExit(f"{label}: {got}")

    close(logic["pose_state_at"](c1["data"], 0.5)["facing"], 0.5, "C1 facing midpoint")
    close(logic["pose_state_at"](c2["data"], 2.3)["jaw_deg"], 7.5, "C2 jaw midpoint")
    close(logic["pose_state_at"](c3["data"], 5.75)["paw"], 0.5, "C3 paw midpoint")
    close(logic["pose_state_at"](c4["data"], 8.4)["wrist_cm"], 7.0, "C4 wrist midpoint")
    left, right, alpha = logic["depth_sample"](c1["data"], 0.125)
    if (left, right) != ("near", "far"):
        raise SystemExit(f"C1 depth sample {(left, right, alpha)}")
    close(alpha, 0.5, "C1 depth alpha")

    prompts_doc = json.loads((CONTROLS / "prompts.json").read_text(encoding="utf-8"))
    if logic["load_scene_prompts"](CONTROLS) != prompts_doc:
        raise SystemExit("load_scene_prompts did not return prompts.json")
    built = {}
    for cut in cuts:
        built[cut["cut"]] = logic["build_prompts"](cut["data"])
        from_file = logic["build_prompts"](cut["data"], prompts_doc)
        if built[cut["cut"]] != from_file:
            raise SystemExit(f"{cut['cut']} prompt lookup drifted")
    c1_pos, c1_neg = built["C1"]
    c2_pos, c2_neg = built["C2"]
    c3_pos, c3_neg = built["C3"]
    c4_pos, c4_neg = built["C4"]
    face_line = "the person's face matches the reference image"
    if "dreamcore liminal space" not in c1_pos:
        raise SystemExit("C1 positive missing dreamcore liminal space")
    if "Sakura" in c1_pos or "Sakura" in c3_pos:
        raise SystemExit("C1 or C3 positive includes Sakura")
    if "crimson kimono" not in c2_pos:
        raise SystemExit("C2 positive missing crimson kimono")
    if "suspended lane ropes with visible anchor points" not in c1_pos:
        raise SystemExit("C1 cut prompt missing")
    if "hands out of focus" not in c2_pos:
        raise SystemExit("C2 cut prompt missing")
    if "giant high-dive tower in clouds" not in c3_pos:
        raise SystemExit("C3 cut prompt missing")
    if "Sakura's hand from side" not in c4_pos or "crimson kimono" not in c4_pos:
        raise SystemExit("C4 cut prompt missing")
    if face_line in c1_pos or face_line in c3_pos:
        raise SystemExit("face reference line on a cut with no person")
    if face_line not in c2_pos or face_line not in c4_pos:
        raise SystemExit("face reference line missing on C2 or C4")
    for cut_id, (positive, negative) in built.items():
        spec = prompts_doc["cuts"][cut_id]
        parts = [prompts_doc["block_a"]]
        if spec["has_person"]:
            parts.append(prompts_doc["block_s"])
        parts.append(spec["prompt"])
        if not positive.startswith(", ".join(parts) + ". "):
            raise SystemExit(f"{cut_id} positive does not start with the script text")
        if "follow the OpenPose control, the depth control, and the camera move" not in positive:
            raise SystemExit(f"{cut_id} dropped the control line")
        neg_head = prompts_doc["negative_common"]
        if spec["negative"]:
            neg_head = neg_head + ", " + spec["negative"]
        if not negative.startswith(neg_head + ", "):
            raise SystemExit(f"{cut_id} negative does not start with the script text")
        if "on-screen text" not in negative:
            raise SystemExit(f"{cut_id} negative prompt does not suppress burned-in text")
    for cut_id in ("C2", "C4"):
        cut_prompt = prompts_doc["cuts"][cut_id]["prompt"]
        if "cat" not in cut_prompt or "40%" not in cut_prompt or "60%" not in cut_prompt:
            raise SystemExit(f"{cut_id} composition is missing the cat or the 40/60 split")
        if "submerged window" not in cut_prompt or "adult Sakura" not in cut_prompt:
            raise SystemExit(f"{cut_id} composition is missing the window or Sakura")
    if "60%" in c1_pos or "submerged window" in c1_pos:
        raise SystemExit("C1 picked up the Sakura composition")
    if "missing cat" not in c2_neg:
        raise SystemExit("C2 does not reject a missing cat")
    if "human-like mouth, extra teeth, deformed jaw" not in c2_neg:
        raise SystemExit("C2 mouth negative missing")
    if "human-like mouth" in c1_neg or "extra knuckles" in c1_neg:
        raise SystemExit("C1 negative has another cut's terms")
    if "extra knuckles, sleeve merging with hand, deformed wrist" not in c4_neg:
        raise SystemExit("C4 hand negative missing")
    if "また昨日のプール。" in c2_pos or "あんたが“明日から本気出す”って言った日の" in c2_pos:
        raise SystemExit("C2 caption leaked into the video prompt")
    if "spoken line" in c2_pos or "not written on screen" in c2_pos:
        raise SystemExit("C2 still asks for a spoken line")
    for cut_id, (positive, _negative) in built.items():
        if "spoken line" in positive or "not written on screen" in positive:
            raise SystemExit(f"{cut_id} still puts dialogue in the video prompt")
    if "「やつ」は意図的に省略" in c2_pos:
        raise SystemExit("C2 production note leaked into the prompt")
    if "the cat stays in place except for its jaw" not in c2_pos:
        raise SystemExit("C2 jaw line missing")
    if "at 0.0s cat pose back to camera" not in c1_pos:
        raise SystemExit("C1 control line missing")
    if "at 1.0s cat pose face to camera" not in c1_pos:
        raise SystemExit("C1 second pose time")
    if "at 0.1s cat jaw 15 degrees" not in c2_pos or "at 3.3s cat jaw 0 degrees" not in c2_pos:
        raise SystemExit("C2 jaw times are not cut-relative")
    if "at 4.8s" in c2_pos or "at 1.6s" in c2_pos:
        raise SystemExit("C2 prompt still uses script-absolute times")
    if "at 0.0s cat pose front" not in c3_pos or "at 1.5s cat pose forepaw to mouth" not in c3_pos:
        raise SystemExit("C3 pose times are not cut-relative")
    if "at 3.0s cat pose paw returned" not in c3_pos:
        raise SystemExit("C3 end pose time")
    if "at 5.0s" in c3_pos or "at 6.5s" in c3_pos or "at 8.0s" in c3_pos:
        raise SystemExit("C3 prompt still uses script-absolute times")
    if "at 0.0s wrist is 10 cm" not in c4_pos or "at 1.6s wrist is 1 cm" not in c4_pos:
        raise SystemExit("C4 wrist times are not cut-relative")
    if "at 8.0s" in c4_pos or "at 9.6s" in c4_pos:
        raise SystemExit("C4 prompt still uses script-absolute times")
    if "does not touch" not in c4_pos or "hand touching" not in c4_neg:
        raise SystemExit("C4 contact constraint missing from prompts")
    for cut_id, expect in (("C1", False), ("C2", True), ("C3", False), ("C4", True)):
        got_ref = logic["uses_face_reference"](cut_id)
        if got_ref is not expect:
            raise SystemExit(f"face reference flag for {cut_id} is {got_ref}")
    gen_ns = {"_H3_LOAD_ONLY": True}
    exec(cell_text(code_cells[1]), gen_ns)
    exec(cell_text(code_cells[5]), gen_ns)
    info = comfy_object_info()
    for cut in cuts:
        graph, positive, negative = gen_ns["prompt_for_cut"](
            info,
            cut,
            f"/content/vace_work/{cut['cut']}/frames",
            8,
            480,
            832,
            "h3_test",
        )
        if (positive, negative) != built[cut["cut"]]:
            raise SystemExit(f"{cut['cut']} prompt_for_cut drifted from build_prompts")
        vace_inputs = graph["vace"]["inputs"]
        if vace_inputs.get("control_video") != ["frames", 0]:
            raise SystemExit(f"{cut['cut']} lost control_video")
        if vace_inputs.get("control_masks") != ["frames", 1]:
            raise SystemExit(f"{cut['cut']} lost control_masks")
        if graph["save"]["inputs"].get("images") != ["decode", 0]:
            raise SystemExit(f"{cut['cut']} save node is not the VAE decode")
        if graph["decode"]["inputs"].get("samples") != ["trim", 0]:
            raise SystemExit(f"{cut['cut']} decode is not the sampler")
        if graph["sample"]["inputs"].get("latent_image") != ["vace", 2]:
            raise SystemExit(f"{cut['cut']} sampler latent is not VACE")
        if vace_inputs.get("strength") != 1.0:
            raise SystemExit(f"{cut['cut']} strength changed")
        has_ref = "reference_image" in vace_inputs
        expect_ref = cut["cut"] in {"C2", "C4"}
        if has_ref is not expect_ref:
            raise SystemExit(f"{cut['cut']} reference_image present={has_ref}")
        blob_graph = json.dumps(graph)
        if expect_ref:
            if vace_inputs["reference_image"] != ["face", 0]:
                raise SystemExit(f"{cut['cut']} reference_image target")
            if graph["face"]["inputs"].get("image") != "face_ref.png":
                raise SystemExit(f"{cut['cut']} face image name")
        elif "face" in graph or "face_ref.png" in blob_graph or "reference_image" in blob_graph:
            raise SystemExit(f"{cut['cut']} graph still names the face reference")
        if graph["sample"]["inputs"]["seed"] != logic["sampler_seed"](cut):
            raise SystemExit(f"{cut['cut']} seed was not passed through")
    if logic["sampler_seed"](c1) != 10001:
        raise SystemExit("sampler seed")

    with tempfile.TemporaryDirectory() as tmp:
        copied = logic["copy_control_json"](c1, tmp)
        if copied.read_bytes() != Path(c1["path"]).read_bytes():
            raise SystemExit("JSON copy is not byte-identical")
        face_dir = Path(tmp) / "faces"
        face_dir.mkdir()
        (face_dir / "face_ref.jpg").write_bytes(b"jpg")
        (face_dir / "face_ref.png").write_bytes(b"png")
        found = logic["find_face_reference"](face_dir)
        if found.name != "face_ref.png":
            raise SystemExit("face lookup did not prefer png")
        try:
            logic["find_face_reference"](tmp)
        except FileNotFoundError:
            pass
        else:
            raise SystemExit("missing face did not fail")

        bad = base_cut()
        del bad["duration_s"]
        try:
            logic["load_cut"](write_cut(tmp, "bad_duration.json", bad))
        except ValueError:
            pass
        else:
            raise SystemExit("missing duration was accepted")

        mismatch = base_cut(duration_s=2.0)
        try:
            logic["load_cut"](write_cut(tmp, "bad_span.json", mismatch))
        except ValueError:
            pass
        else:
            raise SystemExit("duration mismatch was accepted")

        unknown = base_cut()
        unknown["openpose_keyframes"] = [{"t": 0.0, "cat": "sideways"}]
        try:
            logic["load_cut"](write_cut(tmp, "bad_pose.json", unknown))
        except ValueError:
            pass
        else:
            raise SystemExit("unknown pose was accepted")

        wide = base_cut(aspect="16:9")
        try:
            logic["load_cut"](write_cut(tmp, "bad_aspect.json", wide))
        except ValueError:
            pass
        else:
            raise SystemExit("non 9:16 aspect was accepted")

        dup = Path(tmp) / "dup"
        dup.mkdir()
        write_cut(dup, "a.json", base_cut(cut="C9"))
        write_cut(dup, "b.json", base_cut(cut="C9"))
        try:
            logic["list_cuts"](dup)
        except ValueError:
            pass
        else:
            raise SystemExit("duplicate cut was accepted")

        gap = base_cut(
            cut="T1",
            openpose_keyframes=[{"t": 0.0, "wrist_to_handle_cm": 0.2}],
            contact=False,
            fingers_visible=4,
            depth={"focus_sweep": [[0.0, "handle"], [1.0, "cat"]]},
        )
        loaded_gap = logic["load_cut"](write_cut(tmp, "gap.json", gap))
        if logic["pose_state_at"](loaded_gap["data"], 0.0)["wrist_cm"] != 1.0:
            raise SystemExit("contact false did not keep the 1cm gap")

        still = logic["load_cut"](write_cut(tmp, "still.json", base_cut()))
        frame = logic["render_control_frame"](still, 0, 1, 80, 144)
        if frame["pose"] is not frame["pose_raw"]:
            raise SystemExit("zero camera still warped the pose")
        if frame["composite"].size != (80, 144) or frame["composite"].mode != "RGB":
            raise SystemExit("composite size")

    canvas = Image.new("L", (80, 40), 0)
    ImageDraw.Draw(canvas).rectangle((10, 10, 29, 29), fill=255)
    moved = logic["warp_image"](
        canvas, {"dx": 20.0, "dy": 0.0, "roll": 0.0, "scale": 1.0}
    )

    def centroid(image):
        total = 0.0
        weight = 0.0
        for y in range(image.size[1]):
            for x in range(image.size[0]):
                value = image.getpixel((x, y))
                total += x * value
                weight += value
        return total / weight

    shift = centroid(moved) - centroid(canvas)
    if not 18.0 <= shift <= 22.0:
        raise SystemExit(f"camera translate did not move pixels: {shift}")

    zero = logic["camera_delta"](
        {"translate": [8, -3, 0], "rotate": [0, 0, 0]}, 0, 4, 80, 40
    )
    if zero["dx"] != 8 or zero["dy"] != -3 or zero["scale"] != 1 or zero["roll"] != 0:
        raise SystemExit(f"camera delta {zero}")
    yaw = logic["camera_delta"](
        {"translate": [0, 0, 0], "rotate": [0, 45, 0]}, 0, 2, 80, 40
    )
    if abs(yaw["dx"] - 20.0) > 1e-6:
        raise SystemExit(f"yaw shift {yaw['dx']}")
    path_a = logic["handheld_path"](16, 2, 2, 1, True)
    path_b = logic["handheld_path"](16, 2, 2, 1, True)
    path_c = logic["handheld_path"](16, 2, 2, 1, False)
    if path_a != path_b or path_a == path_c:
        raise SystemExit("handheld path is not deterministic")
    if max(abs(point[0]) for point in path_a) - 2.0 > 1e-6:
        raise SystemExit("handheld amplitude exceeded amp_px")

    geo_40 = logic["generation_geometry"](40960)
    geo_80 = logic["generation_geometry"](81920)
    if geo_40["native"] or (geo_40["width"], geo_40["height"]) != (480, 832):
        raise SystemExit(f"40GB geometry {geo_40}")
    if not geo_80["native"] or (geo_80["width"], geo_80["height"]) != (720, 1280):
        raise SystemExit(f"80GB geometry {geo_80}")
    if "pad=" not in logic["ffmpeg_vf"](geo_40):
        raise SystemExit("40GB export does not pad to 9:16")
    if logic["ffmpeg_vf"](geo_80) != "setsar=1":
        raise SystemExit("80GB export filter")
    if logic["ffmpeg_frame_args"](84) != ["-frames:v", "84"]:
        raise SystemExit("frame trim args")
    post = logic["ffmpeg_post_filter"](720, 1280, 84, 24)
    if "2*sin" not in post or "1*sin" not in post or "gblur=sigma=6" not in post:
        raise SystemExit("post filter is missing the 1-2px shake or the focus pull")

    width, height = 96, 160
    c1_count = logic["wan_frame_count"](c1["duration_s"], c1["fps"])
    early = logic["render_control_frame"](c1, 0, c1_count, width, height)
    later_index = logic["index_for_time"](c1, 1.0, c1_count)
    later = logic["render_control_frame"](c1, later_index, c1_count, width, height)
    if mean_abs_diff(early["pose_raw"], later["pose_raw"]) < 2:
        raise SystemExit("C1 back and front poses look the same")
    near = logic["render_control_frame"](
        c1, logic["index_for_time"](c1, 0.0, c1_count), c1_count, width, height
    )
    far = logic["render_control_frame"](
        c1, logic["index_for_time"](c1, 0.25, c1_count), c1_count, width, height
    )
    if abs(mean_luma(near["depth_raw"]) - mean_luma(far["depth_raw"])) < 15:
        raise SystemExit("near and far depth maps are too similar")

    face = Image.new("RGB", (40, 40), (220, 10, 10))
    boxed = logic["letterbox_face"](face, 90, 160)
    if boxed.size != (90, 160):
        raise SystemExit("letterbox size")
    if boxed.getpixel((0, 0)) == (220, 10, 10):
        raise SystemExit("letterbox stretched the face to the corner")
    if not any(boxed.getpixel((x, 20))[0] > 200 for x in range(90)):
        raise SystemExit("letterbox dropped the face")

    with tempfile.TemporaryDirectory() as tmp:
        for cut in cuts:
            rendered = logic["render_cut"](cut, Path(tmp) / cut["cut"], width, height)
            frames = sorted((Path(tmp) / cut["cut"]).glob("frame_*.png"))
            masks = sorted((Path(tmp) / cut["cut"]).glob("mask_*.png"))
            if rendered["count"] != len(frames) or rendered["count"] != len(masks):
                raise SystemExit(f"{cut['cut']} did not write every frame and mask")
            if rendered["count"] < rendered["target_count"]:
                raise SystemExit(f"{cut['cut']} generated fewer frames than the cut")
            sample = Image.open(frames[0])
            if sample.size != (width, height) or sample.mode != "RGB":
                raise SystemExit(f"{cut['cut']} frame is not 9:16 RGB at the test size")
            expected = logic["render_control_frame"](
                cut, 0, rendered["target_count"], width, height
            )
            if sample.tobytes() != expected["pose"].tobytes():
                raise SystemExit(f"{cut['cut']} control video is not the pose")
            if expected["pose"].tobytes() == expected["composite"].tobytes():
                raise SystemExit(f"{cut['cut']} pose and depth composite are identical")
            mask = Image.open(masks[0])
            if mask.mode != "L" or mask.getextrema() != (255, 255):
                raise SystemExit(f"{cut['cut']} control mask is not fully active")

    pose_plate = logic["render_control_frame"](c1, 0, 8, 480, 832)
    pose = pose_plate["pose"]
    pale = Image.new("RGB", pose.size, (210, 198, 176))
    logic["assert_generated_still"](pale, pose)
    kimono = Image.new("RGB", pose.size, (186, 196, 188))
    ImageDraw.Draw(kimono).rectangle((180, 300, 340, 760), fill=(250, 10, 20))
    logic["assert_generated_still"](kimono, pose)
    if logic["saturated_skeleton_families"](pose) < 3:
        raise SystemExit("pose plate did not register skeleton colors")
    if logic["saturated_skeleton_families"](kimono) >= 3:
        raise SystemExit("a red kimono was counted as a skeleton")
    try:
        logic["assert_generated_still"](pose, pose)
    except RuntimeError:
        pass
    else:
        raise SystemExit("control frame was accepted as a generated frame")
    try:
        logic["assert_generated_still"](pose_plate["composite"], pose)
    except RuntimeError:
        pass
    else:
        raise SystemExit("depth composite was accepted as a generated frame")
    face = Image.new("RGB", (80, 80), (220, 30, 40))
    boxed = logic["letterbox_face"](face, pose.size[0], pose.size[1])
    try:
        logic["assert_generated_still"](boxed, pose, boxed)
    except RuntimeError:
        pass
    else:
        raise SystemExit("reference paste was accepted as a generated frame")
    logic["assert_generated_still"](pale, pose, boxed)

    if shutil.which("ffmpeg") and shutil.which("ffprobe"):
        geo = logic["generation_geometry"](40960)

        def mux_frames(directory, images, keep, dest):
            directory.mkdir()
            for index, image in enumerate(images):
                image.save(directory / f"frame_{index:04d}.png")
            staged = dest.with_suffix(".sized.mp4")
            cmd = logic["ffmpeg_sequence_cmd"](
                directory / "frame_%04d.png",
                len(images),
                8,
                1.0,
                geo,
                staged,
                keep_frames=keep,
            )
            mux = subprocess.run(cmd, capture_output=True, text=True)
            if mux.returncode != 0:
                raise SystemExit(f"ffmpeg pad failed: {mux.stderr[-500:]}")
            finish = logic["ffmpeg_finish_cmd"](staged, dest, keep, 8, geo)
            burned = subprocess.run(finish, capture_output=True, text=True)
            if burned.returncode != 0:
                raise SystemExit(f"ffmpeg post failed: {burned.stderr[-500:]}")
            got = logic["assert_export_stream"](dest, keep, 720, 1280)
            if got["frames"] != keep:
                raise SystemExit(f"ffprobe frames {got}")
            return logic["read_first_frame"](dest)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pale_frame = mux_frames(
                root / "pale",
                [Image.new("RGB", (480, 832), (210, 198, 176)) for _ in range(5)],
                4,
                root / "pale.mp4",
            )
            logic["assert_generated_still"](pale_frame, pose, boxed)
            copied = mux_frames(
                root / "pose",
                [pose for _ in range(4)],
                4,
                root / "pose.mp4",
            )
            try:
                logic["assert_generated_still"](copied, pose)
            except RuntimeError:
                pass
            else:
                raise SystemExit("postprocessed control frame was accepted")
    else:
        raise SystemExit("ffmpeg is required to check the 9:16 mux")

    print("ok: notebook valid, cells compile, C1-C4 loader and control frames checked")


if __name__ == "__main__":
    main()
