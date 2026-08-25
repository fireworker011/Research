import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from h3_motion_graphics import (
    CANVAS_8_9,
    CANVAS_8_9_NATIVE,
    COPY,
    I2VA_HEADER,
    assert_i2va_graph,
    build_i2va_graph,
    build_i2va_prompt,
    prefer_fl2v_lora,
    validate_motion_ad_prompt,
)


def test_i2va_prompt_has_ten_shots_and_cta():
    p = build_i2va_prompt()
    assert p.startswith(I2VA_HEADER)
    assert validate_motion_ad_prompt(p) == []
    assert COPY["cta"] in p
    assert "px.a8.net" not in p


def test_fl2va_prompt_aligns_end_frame():
    p = build_i2va_prompt(with_last_frame=True)
    assert validate_motion_ad_prompt(p, with_last_frame=True) == []
    assert "Picture 2" in p
    assert "10.00-second" in p


def test_prompt_rejects_affiliate_url():
    bad = build_i2va_prompt() + "\nhttps://px.a8.net/svt/ejp?a8mat=x\n"
    errs = validate_motion_ad_prompt(bad)
    assert any("forbidden" in e for e in errs)


def test_i2va_graph_first_frame_only():
    p = build_i2va_prompt()
    g = build_i2va_graph(
        first_image="cast/aya.jpg",
        last_image=None,
        prompt=p,
        unet="minimax_h3_fl2va_pruned_int8_convrot.safetensors",
        lora_name="minimax_h3_fl2v_turbo_4step.safetensors",
        lora_strength=1.0,
        width=CANVAS_8_9[0],
        height=CANVAS_8_9[1],
        duration_s=10,
        seed=1,
        steps=4,
        filename_prefix="video/h3_i2va_ad",
    )
    assert assert_i2va_graph(g, expect_last=False) == []
    assert g["100"]["inputs"]["image"] == "cast/aya.jpg"
    assert g["20"]["inputs"]["first_frame"] == ["100", 0]


def test_fl2va_graph_wires_last_frame():
    p = build_i2va_prompt(with_last_frame=True)
    g = build_i2va_graph(
        first_image="start.jpg",
        last_image="cta_end.jpg",
        prompt=p,
        unet="minimax_h3_fl2va_pruned_int8_convrot.safetensors",
        lora_name=None,
        lora_strength=1.0,
        width=CANVAS_8_9[0],
        height=CANVAS_8_9[1],
        duration_s=10,
        seed=1,
        steps=16,
        filename_prefix="video/h3_fl2va_ad",
        has_lora_loader=False,
        has_audio_decode=False,
    )
    assert assert_i2va_graph(g, expect_last=True) == []
    assert g["101"]["inputs"]["image"] == "cta_end.jpg"


def test_canvas_matches_x_post_8_9():
    for w, h in (CANVAS_8_9, CANVAS_8_9_NATIVE):
        assert w % 32 == 0 and h % 32 == 0
        assert abs(w / h - 8 / 9) < 0.01
    assert CANVAS_8_9_NATIVE == (1280, 1440)


def test_prefer_fl2v_lora(tmp_path):
    a = tmp_path / "minimax_h3_ref2v_turbo.safetensors"
    b = tmp_path / "minimax_h3_fl2v_turbo_4step.safetensors"
    a.write_bytes(b"x")
    b.write_bytes(b"x")
    assert prefer_fl2v_lora([a, b], True) == b.name
