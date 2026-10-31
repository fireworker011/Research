#!/usr/bin/env python3
"""Static-check the VACE notebook and run the JSON loader against C1-C4."""

import ast
import json
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
    compile((ROOT / "h3_load_frames.py").read_text(encoding="utf-8"), "h3_load_frames.py", "exec")

    blob = "\n".join(
        [cell_text(cell) for cell in notebook.cells]
        + [
            logic_src,
            (ROOT / "README.md").read_text(encoding="utf-8"),
            (ROOT / "h3_load_frames.py").read_text(encoding="utf-8"),
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

    expected_frames = {"C1": 37, "C2": 81, "C3": 73, "C4": 37}
    for cut_id, expected in expected_frames.items():
        got = logic["wan_frame_count"](by_id[cut_id]["duration_s"], by_id[cut_id]["fps"])
        if got != expected:
            raise SystemExit(f"{cut_id} frame count {got}, expected {expected}")

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

    positive, negative = logic["build_prompts"](c2["data"])
    if "また昨日のプール。" not in positive:
        raise SystemExit("C2 caption missing from prompt")
    if "あんたが“明日から本気出す”って言った日の" not in positive:
        raise SystemExit("C2 second caption missing")
    if "「やつ」は意図的に省略" in positive:
        raise SystemExit("C2 production note leaked into the prompt")
    if "on-screen text" not in negative:
        raise SystemExit("negative prompt does not suppress burned-in text")
    c4_positive, c4_negative = logic["build_prompts"](c4["data"])
    if "does not touch" not in c4_positive or "hand touching" not in c4_negative:
        raise SystemExit("C4 contact constraint missing from prompts")
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
    if logic["ffmpeg_duration_args"](37, 24, 1.5) != ["-t", "1.500"]:
        raise SystemExit("C1 duration trim")
    if logic["ffmpeg_duration_args"](81, 24, 3.5) != []:
        raise SystemExit("C2 should keep every generated frame")

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
            if rendered["count"] != len(frames):
                raise SystemExit(f"{cut['cut']} did not write every frame")
            sample = Image.open(frames[0])
            if sample.size != (width, height) or sample.mode != "RGB":
                raise SystemExit(f"{cut['cut']} frame is not 9:16 RGB at the test size")

    if shutil.which("ffmpeg") and shutil.which("ffprobe"):
        with tempfile.TemporaryDirectory() as tmp:
            seq = Path(tmp) / "seq"
            seq.mkdir()
            for index in range(4):
                Image.new("RGB", (480, 832), (20, 40, index * 20)).save(seq / f"frame_{index:04d}.png")
            dest = Path(tmp) / "padded.mp4"
            cmd = logic["ffmpeg_sequence_cmd"](
                seq / "frame_%04d.png",
                4,
                8,
                1.0,
                logic["generation_geometry"](40960),
                dest,
            )
            mux = subprocess.run(cmd, capture_output=True, text=True)
            if mux.returncode != 0:
                raise SystemExit(f"ffmpeg pad failed: {mux.stderr[-500:]}")
            probe = subprocess.run(
                [
                    "ffprobe",
                    "-v",
                    "error",
                    "-select_streams",
                    "v:0",
                    "-show_entries",
                    "stream=width,height",
                    "-of",
                    "csv=p=0:s=x",
                    str(dest),
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            if probe.stdout.strip() != "720x1280":
                raise SystemExit(f"padded mp4 size {probe.stdout.strip()}")
    else:
        raise SystemExit("ffmpeg is required to check the 9:16 mux")

    print("ok: notebook valid, cells compile, C1-C4 loader and control frames checked")


if __name__ == "__main__":
    main()
