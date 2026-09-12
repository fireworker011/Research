import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from minimax_h3_motion_identity import (
    PayloadError,
    assert_r2va_motion_identity,
    build_generation_payload,
    build_motion_identity_prompt,
    build_r2va_content,
    choose_duration_from_video,
    content_roles,
    ensure_identity_lock_in_prompt,
    mm_file_url,
    parse_upload_file_id,
    summarize_payload,
)


def test_duration_clamps_to_h3_range():
    assert choose_duration_from_video(2.0) == 4
    assert choose_duration_from_video(3.4) == 4
    assert choose_duration_from_video(5.4) == 5
    assert choose_duration_from_video(15.0) == 15
    assert choose_duration_from_video(20.0) == 15


def test_prompt_assigns_image_appearance_and_video_motion():
    prompt = build_motion_identity_prompt(2, extra_scene="dance in a studio")
    lowered = prompt.lower()
    assert "reference image 1" in lowered
    assert "reference image 2" in lowered
    assert "reference video 1" in lowered
    assert "appearance follows reference image" in lowered
    assert "motion in reference video" in lowered
    assert "ignore the person" in lowered
    assert "<picture 1>" in lowered
    assert "dance in a studio" in lowered


def test_r2va_payload_never_omits_image_role():
    content = build_r2va_content(
        build_motion_identity_prompt(1),
        ["mm_file://111"],
        ["mm_file://222"],
    )
    assert content_roles(content) == ["reference_image", "reference_video"]
    assert content[0]["type"] == "text"
    assert content[1]["role"] == "reference_image"
    assert content[2]["role"] == "reference_video"
    payload = build_generation_payload(content, duration=5, resolution="768P")
    summary = summarize_payload(payload)
    assert summary["mode"] == "r2va"
    assert summary["n_images"] == 1
    assert summary["n_videos"] == 1
    assert summary["n_audios"] == 0


def test_missing_role_is_rejected_because_it_becomes_i2va():
    content = [
        {"type": "text", "text": build_motion_identity_prompt(1)},
        {"type": "image_url", "image_url": {"url": "https://example.com/a.png"}},
        {"type": "video_url", "video_url": {"url": "https://example.com/a.mp4"}, "role": "reference_video"},
    ]
    with pytest.raises(PayloadError, match="defaults a single image to first_frame"):
        assert_r2va_motion_identity(content)


def test_first_frame_mixed_with_reference_video_is_rejected():
    content = [
        {"type": "text", "text": build_motion_identity_prompt(1)},
        {"type": "image_url", "image_url": {"url": "https://example.com/a.png"}, "role": "first_frame"},
        {"type": "video_url", "video_url": {"url": "https://example.com/a.mp4"}, "role": "reference_video"},
    ]
    with pytest.raises(PayloadError, match="mutually exclusive"):
        assert_r2va_motion_identity(content)


def test_prompt_without_job_assignment_is_rejected():
    content = [
        {"type": "text", "text": "a person dancing"},
        {"type": "image_url", "image_url": {"url": "https://example.com/a.png"}, "role": "reference_image"},
        {"type": "video_url", "video_url": {"url": "https://example.com/a.mp4"}, "role": "reference_video"},
    ]
    with pytest.raises(PayloadError, match="assign jobs"):
        assert_r2va_motion_identity(content)


def test_ir_prompt_gets_identity_lock_prepended():
    ir = "integrated_multimodal_description: [Shot 1] A dancer spins."
    locked = ensure_identity_lock_in_prompt(ir, n_images=1)
    assert locked.startswith("subject_definitions:")
    assert "a dancer spins" in locked.lower()


def test_ir_prompt_kept_when_already_locked():
    prompt = build_motion_identity_prompt(1)
    assert ensure_identity_lock_in_prompt(prompt, 1) == prompt


def test_upload_file_id_and_mm_file_url():
    file_id = parse_upload_file_id(
        {"file": {"file_id": 424010985738629}, "base_resp": {"status_code": 0}}
    )
    assert mm_file_url(file_id) == "mm_file://424010985738629"


def test_payload_json_is_serializable():
    content = build_r2va_content(
        build_motion_identity_prompt(1, extra_scene="walk toward camera"),
        ["data:image/jpeg;base64,xxxx"],
        ["mm_file://9"],
    )
    payload = build_generation_payload(content, duration=6, resolution="2K", ratio="9:16")
    dumped = json.dumps(payload)
    loaded = json.loads(dumped)
    assert loaded["content"][1]["role"] == "reference_image"
    assert loaded["content"][2]["role"] == "reference_video"


def test_ffmpeg_available_for_colab_preprocess():
    result = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True)
    if result.returncode != 0:
        pytest.skip("ffmpeg not installed in this environment")
    assert "ffmpeg version" in result.stdout.splitlines()[0].lower() or "ffmpeg" in result.stdout.lower()


def test_prepare_identity_image_fits_h3_limits(tmp_path):
    from PIL import Image
    from minimax_h3_motion_identity import prepare_identity_image

    tiny = tmp_path / "tiny.png"
    Image.new("RGB", (64, 64), (12, 80, 160)).save(tiny)
    out = prepare_identity_image(tiny, tmp_path / "out.jpg")
    assert out["width"] >= 256
    assert out["height"] >= 256
    assert 0.4 <= out["aspect"] <= 2.5
    assert Path(out["path"]).exists()


def test_target_video_canvas_lifts_short_edge():
    from minimax_h3_motion_identity import target_video_canvas

    w, h = target_video_canvas(320, 240)
    assert min(w, h) >= 256
    assert max(w, h) <= 5760
    assert 0.4 <= w / h <= 2.5
    assert w % 2 == 0 and h % 2 == 0


def test_prepare_motion_video_meets_h3_floor(tmp_path):
    result = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True)
    if result.returncode != 0:
        pytest.skip("ffmpeg not installed in this environment")
    from minimax_h3_motion_identity import MIN_DIM, MIN_REF_VIDEO_SEC, prepare_motion_video

    src = tmp_path / "src.mp4"
    subprocess.run(
        [
            "ffmpeg", "-y", "-f", "lavfi", "-i", "testsrc=size=320x240:rate=30",
            "-t", "1.5", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(src),
        ],
        check=True,
        capture_output=True,
    )
    out = prepare_motion_video(src, tmp_path / "out.mp4", strip_audio=True)
    assert out["duration"] >= MIN_REF_VIDEO_SEC - 0.08
    assert out["width"] >= MIN_DIM
    assert out["height"] >= MIN_DIM
    assert 0.4 <= out["aspect"] <= 2.5
    assert out["codec"] == "h264"


def test_notebook_locks_r2va_roles():
    nb = json.loads(Path(__file__).resolve().parents[1].joinpath("minimax_h3_motion_identity_colab.ipynb").read_text())
    blob = "\n".join("".join(c.get("source") or []) for c in nb["cells"])
    assert "role=reference_image" in blob or 'R2VA_IMAGE_ROLE = "reference_image"' in blob
    assert "role=reference_video" in blob or 'R2VA_VIDEO_ROLE = "reference_video"' in blob
    assert "first_frame" in blob
    magic = "".join(nb["cells"][2]["source"])
    assert magic.startswith("%%writefile /content/minimax_h3_motion_identity.py")
