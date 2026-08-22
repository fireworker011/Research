import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from h3_r2v_core import (
    assert_graph_identity_motion,
    build_r2v_graph,
    cap_duration_for_vram,
    comfy_media_name,
    finalize_prompt,
    frames,
    is_oom_error,
    prefer_ref2v_lora,
    r2v_retry_plans,
    vhs_load_video_inputs,
)


def test_frames_grid_is_17k_plus_5():
    n = frames(6)
    assert n % 17 == 5
    assert n >= 5


def test_comfy_media_keeps_subdirectory():
    assert comfy_media_name("sub\\Image 1.jpg") == "sub/Image 1.jpg"
    assert comfy_media_name("Image 1.jpg") == "Image 1.jpg"


def test_prefer_ref2v_over_fl2v(tmp_path):
    fl = tmp_path / "minimax_h3_fl2v_turbo_4step_v1.0_768p_comfyui_bf16.safetensors"
    rf = tmp_path / "minimax_h3_ref2v_turbo_4step_v0.1_comfyui_bf16.safetensors"
    fl.write_bytes(b"x")
    rf.write_bytes(b"x")
    assert prefer_ref2v_lora([fl, rf], True) == rf.name


def test_graph_wires_relative_video_and_picture_tags():
    prompt = finalize_prompt("", ["cast/Image 1.jpg", "cast/Image 2.jpg"], ["motion/0815(1).mp4"], 6)
    g = build_r2v_graph(
        img_names=["cast/Image 1.jpg", "cast/Image 2.jpg"],
        vid_names=["motion/0815(1).mp4"],
        prompt=prompt,
        unet="minimax_h3_ref2va_pruned_int8_convrot.safetensors",
        lora_name="minimax_h3_ref2v_turbo_4step_v0.1_comfyui_bf16.safetensors",
        lora_strength=1.0,
        width=960,
        height=544,
        duration_s=6,
        seed=42,
        steps=4,
        filename_prefix="video/h3_r2v_flex",
        ref_image_size="max",
        object_info={
            "VHS_LoadVideo": {
                "input": {
                    "required": {
                        "video": ["STRING", {"default": ""}],
                        "force_rate": ["FLOAT", {"default": 0}],
                        "frame_load_cap": ["INT", {"default": 0}],
                    }
                }
            }
        },
    )
    assert g["100"]["inputs"]["image"] == "cast/Image 1.jpg"
    assert g["190"]["class_type"] == "VHS_LoadVideo"
    assert g["190"]["inputs"]["video"] == "motion/0815(1).mp4"
    assert g["190"]["inputs"]["force_rate"] == 24
    assert g["20"]["inputs"]["ref_images.ref_image_0"] == ["100", 0]
    assert g["20"]["inputs"]["ref_videos.ref_video_0"] == ["190", 0]
    assert "ref_videos" not in g["20"]["inputs"]
    errs = assert_graph_identity_motion(
        g, expect_images=2, expect_videos=1, prompt=prompt
    )
    assert errs == []
    assert "<Picture 1>" in prompt
    assert "<Video 1>" in prompt
    assert "MOTION ONLY" in prompt.upper()


def test_graph_rejects_non_multiple_of_32():
    try:
        build_r2v_graph(
            img_names=["a.jpg"],
            vid_names=[],
            prompt=finalize_prompt("", ["a.jpg"], [], 5),
            unet="u.safetensors",
            lora_name=None,
            lora_strength=1.0,
            width=961,
            height=544,
            duration_s=5,
            seed=1,
            steps=20,
            filename_prefix="x",
            use_videos=False,
        )
    except ValueError as e:
        assert "32" in str(e)
    else:
        raise AssertionError("expected ValueError")


def test_cap_duration_prevents_14s_max_on_40gb():
    capped = cap_duration_for_vram(
        14,
        vram_gb=39.5,
        n_images=2,
        has_video=True,
        ref_image_size="max",
    )
    assert capped <= 6
    assert frames(capped) < 200


def test_retry_plans_never_drop_video():
    plans = r2v_retry_plans(
        duration_s=14,
        ref_image_size="max",
        width=960,
        height=544,
        n_images=2,
        has_video=True,
        vram_gb=39.5,
    )
    assert plans[0]["duration_s"] <= 6
    assert all(p["motion_max_edge"] for p in plans)
    assert any(p["ref_image_size"] == "match" for p in plans)
    assert is_oom_error(["execution_error", {"exception_message": "torch.OutOfMemoryError"}])
    inputs = vhs_load_video_inputs(
        {"VHS_LoadVideo": {"input": {"required": {"file": ["COMBO", {}]}}}},
        "clip.mp4",
        124,
    )
    assert inputs["file"] == "clip.mp4"


def test_original_cell8_had_syntax_error():
    src = Path("/home/ubuntu/.cursor/projects/workspace/uploads/minimax_h3_colab_____8ae3.ipynb")
    if not src.exists():
        return
    nb = json.loads(src.read_text())
    cell = "".join(nb["cells"][9].get("source") or [])
    assert "print(= * 60)" in cell


def test_fixed_notebook_cell8_compiles():
    nb_path = Path(__file__).resolve().parents[1] / "minimax_h3_colab_完全版.ipynb"
    if not nb_path.exists():
        return
    nb = json.loads(nb_path.read_text(encoding="utf-8"))
    cell8 = None
    for c in nb["cells"]:
        text = "".join(c.get("source") or [])
        if "セル8：R2V" in text and c["cell_type"] == "code":
            cell8 = text
            break
    assert cell8 is not None
    assert "print(= * 60)" not in cell8
    assert 'print("=" * 60)' in cell8
    assert "attempts.append" not in cell8
    compile(cell8, "cell8.py", "exec")
    blob = "\n".join("".join(c.get("source") or []) for c in nb["cells"])
    assert r"C:\Users\ys734\Desktop\minimaxh3" in blob
    assert "%%writefile h3_r2v_core.py" in blob
