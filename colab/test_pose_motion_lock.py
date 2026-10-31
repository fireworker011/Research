import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from pose_motion_lock import (
    H3_NOT_MOCAP,
    assert_graph_pose_lock,
    assign_people_left_to_right,
    build_pose_preview_graph,
    build_wan_animate_graph,
    chunk_count,
    mix_pass_plan,
    snap_video_size,
    wan_length,
)


def test_h3_limitation_is_explicit():
    assert "モーションキャプチャではない" in H3_NOT_MOCAP
    assert "Animate" in H3_NOT_MOCAP


def test_wan_length_is_4k_plus_1_and_capped():
    n = wan_length(14, fps=16, chunk=77)
    assert n == 77
    assert n % 4 == 1
    assert chunk_count(14, fps=16, chunk=77) >= 3


def test_people_assigned_left_to_right():
    mapping = assign_people_left_to_right(
        [("b", 400, 0, 500, 100), ("a", 10, 0, 80, 100)]
    )
    assert mapping["a"] == 0
    assert mapping["b"] == 1


def test_mix_two_pass_keeps_camera_chain():
    jobs = mix_pass_plan(["Image 1.jpg", "Image 2.jpg"], "0815(1).mp4")
    assert len(jobs) == 2
    assert jobs[0]["background_video"] == "0815(1).mp4"
    assert jobs[1]["background_video"] == jobs[0]["filename_prefix"]
    assert jobs[0]["reference_image"] == "Image 1.jpg"
    assert jobs[1]["reference_image"] == "Image 2.jpg"


def test_mix_graph_wires_pose_mask_and_identity():
    g = build_wan_animate_graph(
        image_name="cast/Image 1.jpg",
        video_name="motion/0815(1).mp4",
        mask_name="motion/0815(1)_mask_p1.mp4",
        prompt="samurai mix",
        mode="mix",
        width=640,
        height=368,
        length=77,
    )
    errs = assert_graph_pose_lock(g, mode="mix", expect_mask=True)
    assert errs == []
    assert g["10"]["inputs"]["image"] == "cast/Image 1.jpg"
    assert g["190"]["inputs"]["video"] == "motion/0815(1).mp4"
    assert g["25"]["inputs"]["pose_video"] == ["101", 0]
    assert g["25"]["inputs"]["reference_image"] == ["10", 0]
    assert g["25"]["inputs"]["background_video"] == ["190", 0]
    assert g["25"]["inputs"]["character_mask"] == ["241", 0]
    assert g["14"]["inputs"]["type"] == "wan"
    assert g["101"]["inputs"]["detect_body"] == "enable"
    assert g["101"]["inputs"]["detect_face"] == "disable"
    assert g["100"]["inputs"]["detect_face"] == "enable"


def test_move_graph_has_no_background():
    g = build_wan_animate_graph(
        image_name="Image 1.jpg",
        video_name="clip.mp4",
        prompt="move",
        mode="move",
        mask_name=None,
        relight_lora=None,
    )
    errs = assert_graph_pose_lock(g, mode="move", expect_mask=False)
    assert errs == []
    assert "background_video" not in g["25"]["inputs"]


def test_mix_without_mask_is_rejected():
    try:
        build_wan_animate_graph(
            image_name="Image 1.jpg",
            video_name="clip.mp4",
            prompt="x",
            mode="mix",
            mask_name=None,
        )
    except ValueError as e:
        assert "mask" in str(e)
    else:
        raise AssertionError("expected ValueError")


def test_pose_preview_has_no_h3():
    g = build_pose_preview_graph(video_name="0815(1).mp4", length=77)
    assert g["101"]["class_type"] == "DWPreprocessor"
    assert not any(n["class_type"] == "WanAnimateToVideo" for n in g.values())
    assert snap_video_size(1920, 1080, 640) == (640, 352)
