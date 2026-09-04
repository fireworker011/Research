import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from h3_i2v_free import (
    ASPECT_CHOICES,
    BRANCH,
    DEFAULT_I2V_PROMPT,
    HELPER_BRANCHES,
    HELPER_FILES,
    NOTEBOOK,
    aspect_label,
    assert_i2v_graph,
    build_i2v_graph,
    canvas_for_aspect,
    canvas_from_image_size,
    i2v_free_colab_url,
    i2v_retry_plans,
    resolve_i2v_prompt,
    validate_i2v_prompt,
)
from h3_motion_graphics import I2VA_HEADER, underage_prompt_errors, validate_motion_ad_prompt, build_i2va_prompt
from h3_t2v import validate_t2v_prompt

ROOT = Path(__file__).resolve().parents[1]


def test_canvas_from_image_size_follows_orientation():
    assert canvas_from_image_size(1080, 1920) == (576, 1024)
    assert canvas_from_image_size(1920, 1080) == (1024, 576)
    assert canvas_from_image_size(1000, 1000) == (768, 864)
    assert canvas_from_image_size(1280, 1440) == (768, 864)
    assert canvas_from_image_size(0, 0) == (576, 1024)


def test_canvas_for_aspect_auto_and_explicit():
    assert canvas_for_aspect("auto") == (576, 1024)
    assert canvas_for_aspect("auto", image_size=(4000, 3000)) == (1024, 576)
    assert canvas_for_aspect("9:16") == (576, 1024)
    assert canvas_for_aspect("16:9") == (1024, 576)
    assert canvas_for_aspect("16/9") == (1024, 576)
    assert canvas_for_aspect("8:9") == (768, 864)
    for a in ASPECT_CHOICES:
        w, h = canvas_for_aspect(a, image_size=(9, 16))
        assert w % 32 == 0 and h % 32 == 0
    try:
        canvas_for_aspect("4:3")
    except ValueError:
        pass
    else:
        raise AssertionError("4:3 must be rejected")


def test_aspect_label():
    assert aspect_label(576, 1024) == "9:16"
    assert aspect_label(1024, 576) == "16:9"
    assert aspect_label(768, 864) == "8:9"
    assert aspect_label(640, 640) == "640x640"


def test_resolve_prompt_keeps_free_text_and_adds_picture_header():
    p = resolve_i2v_prompt("")
    assert p == DEFAULT_I2V_PROMPT
    assert p.startswith(I2VA_HEADER)
    assert p.count("<Picture 1>") == 2
    assert validate_i2v_prompt(p) == []

    user = "She turns to the camera and smiles. Rain outside the window."
    p2 = resolve_i2v_prompt(user)
    assert p2.startswith(I2VA_HEADER)
    assert user in p2
    assert validate_i2v_prompt(p2) == []

    own = "At 0.00s <Picture 1> is fully referenced. She waves."
    assert resolve_i2v_prompt(own) == own

    p3 = resolve_i2v_prompt(user, with_last_frame=True, duration_s=10)
    assert "Picture 2" in p3 and "10.00-second mark" in p3
    assert validate_i2v_prompt(p3, with_last_frame=True) == []
    assert validate_i2v_prompt(p2, with_last_frame=True)

    p4 = resolve_i2v_prompt("", with_last_frame=True, duration_s=10)
    assert I2VA_HEADER not in p4
    assert p4.count("Picture 1") == 2 and "Picture 2" in p4
    assert validate_i2v_prompt(p4, with_last_frame=True) == []

    wide = resolve_i2v_prompt("", landscape=True)
    assert "16:9" in wide


def test_validate_prompt_forbidden_and_minors():
    assert validate_i2v_prompt("") == ["I2V prompt is empty"]
    assert any("forbidden" in e for e in validate_i2v_prompt("<Picture 1> https://px.a8.net/x"))
    assert any("forbidden" in e for e in validate_i2v_prompt("<Picture 1> 月収100万"))
    assert any("Picture 1" in e for e in validate_i2v_prompt("no header here"))
    for bad in (
        "<Picture 1> young girl, 15 years old, slim",
        "<Picture 1> a teen idol on stage",
        "<Picture 1> 女子高生の制服で踊る",
        "<Picture 1> 12歳の少女",
        "<Picture 1> a 7yo kid runs",
        "<Picture 1> high-school classroom",
    ):
        errs = validate_i2v_prompt(bad)
        assert any("minor" in e for e in errs), bad
    for ok in (
        "<Picture 1> adult woman, mid-20s, 25歳, minor camera move",
        "<Picture 1> 18 years old college student",
        "<Picture 1> aged 30, office at night",
    ):
        assert validate_i2v_prompt(ok) == [], ok


def test_minor_guard_is_shared_by_t2v_and_motion_ad():
    assert underage_prompt_errors("15 years old") != []
    assert underage_prompt_errors("25 years old") == []
    assert any("minor" in e for e in validate_t2v_prompt("vertical, 15 years old girl"))
    assert validate_t2v_prompt("vertical, adult woman in her 20s") == []
    assert validate_motion_ad_prompt(build_i2va_prompt()) == []
    assert any("minor" in e for e in validate_motion_ad_prompt(build_i2va_prompt() + " 女子高生"))


def test_retry_plans_follow_aspect():
    labels = [p["label"] for p in i2v_retry_plans(width=1024, height=576)]
    assert labels[0] == "1024x576"
    assert "512x288" in labels
    assert "576x1024" not in labels
    labels = [p["label"] for p in i2v_retry_plans(width=576, height=1024)]
    assert labels == ["576x1024", "288x512"]
    labels = [p["label"] for p in i2v_retry_plans(width=768, height=864)]
    assert labels == ["768x864", "512x576"]


def _graph(last=None, prompt=None, w=576, h=1024):
    return build_i2v_graph(
        first_image="still.jpg",
        last_image=last,
        prompt=prompt if prompt is not None else resolve_i2v_prompt("She blinks.", with_last_frame=bool(last)),
        unet="minimax_h3_fl2va_pruned_int8_convrot.safetensors",
        lora_name="minimax_h3_fl2v_turbo_4step_v1.0_768p_comfyui_bf16.safetensors",
        lora_strength=1.0,
        width=w,
        height=h,
        duration_s=10,
        seed=1,
        steps=4,
        filename_prefix="video/test",
    )


def test_graph_wires_first_frame_and_validates():
    g = _graph()
    assert assert_i2v_graph(g, expect_last=False) == []
    node = g["20"]
    assert node["class_type"] == "MiniMaxH3ImageToVideo"
    assert node["inputs"]["first_frame"] == ["100", 0]
    assert "last_frame" not in node["inputs"]
    assert g["100"]["class_type"] == "LoadImage"
    assert g["23"]["inputs"]["steps"] == 4
    assert g["22"]["inputs"]["sampler_name"] == "euler"
    assert not any(n.get("class_type") == "MiniMaxH3ReferenceToVideo" for n in g.values())

    g2 = _graph(last="end.jpg")
    assert assert_i2v_graph(g2, expect_last=True) == []
    assert g2["20"]["inputs"]["last_frame"] == ["101", 0]
    assert assert_i2v_graph(g2, expect_last=False)

    g3 = _graph(prompt="<Picture 1> girl, 15 years old")
    assert any("minor" in e for e in assert_i2v_graph(g3, expect_last=False))

    g4 = _graph(w=1024, h=576)
    assert assert_i2v_graph(g4, expect_last=False) == []
    g4["20"]["inputs"]["width"] = 1000
    assert any("multiples of 32" in e for e in assert_i2v_graph(g4, expect_last=False))


def test_urls_and_helper_set():
    url = i2v_free_colab_url()
    assert url.startswith("https://colab.research.google.com/github/fireworker011/Research/blob/")
    assert BRANCH in url and url.endswith(NOTEBOOK)
    assert HELPER_BRANCHES[0] == BRANCH
    assert "colab/h3_i2v_free.py" in HELPER_FILES
    assert "colab/h3_civitai.py" in HELPER_FILES
    assert "colab/h3_t2v.py" in HELPER_FILES and "colab/h3_motion_graphics.py" in HELPER_FILES


def test_mirror_copies_match():
    for name in ("h3_i2v_free.py", "h3_motion_graphics.py", "h3_t2v.py", "h3_civitai.py"):
        a = (ROOT / "colab" / name).read_text(encoding="utf-8")
        b = (ROOT / "minimaxh3" / name).read_text(encoding="utf-8")
        assert a == b, name


def _nb(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_free_phone_notebook_is_three_i2v_cells():
    for path in (ROOT / NOTEBOOK, ROOT / "minimaxh3" / NOTEBOOK):
        nb = _nb(path)
        codes = [c for c in nb["cells"] if c["cell_type"] == "code"]
        assert len(codes) == 3
        blob = "\n".join("".join(c.get("source") or []) for c in nb["cells"])
        assert "MiniMaxH3ImageToVideo" in blob
        assert "MiniMaxH3ReferenceToVideo" not in blob
        assert "WanAnimateToVideo" not in blob
        assert "loca.lt" not in blob
        assert "ref2va" not in blob.lower()
        assert "px.a8.net" not in blob
        assert "a8mat=" not in blob
        assert "稼げる" not in blob
        assert "coconala_creator_ref" not in blob
        assert "display(Video" in blob
        assert "civitai.com/user/account" in blob
        assert "civitai_api_token.txt" in blob
        assert 'CIVITAI_API_TOKEN = ""' in blob
        assert "シークレットは不要" in blob or "シークレットは使わなくてよい" in blob
        assert "sk-live-" not in blob
        for i, cell in enumerate(codes):
            src = "".join(cell.get("source") or [])
            assert not src.strip().startswith("%%")
            compile(src, f"i2v_free_cell{i+1}.py", "exec")


def test_free_phone_setup_cell_probes_helper_branches():
    nb = _nb(ROOT / NOTEBOOK)
    setup = "".join(nb["cells"][2]["source"])
    for b in HELPER_BRANCHES:
        assert b in setup
    for rel in HELPER_FILES:
        assert rel in setup
    assert 'PROBE = "colab/h3_civitai.py"' in setup
    assert "i2v_download_jobs" in setup and "missing_weight_files" in setup
    assert "load_civitai_token" in setup
    assert "CIVITAI_LORA_URL" in setup


def test_free_phone_generate_cell_keeps_i2v_invariants():
    nb = _nb(ROOT / NOTEBOOK)
    gen = "".join(nb["cells"][3]["source"])
    assert 'FIRST_IMAGE = "auto"' in gen
    assert 'LAST_IMAGE = ""' in gen
    assert 'PROMPT = ""' in gen
    assert 'ASPECT = "auto"  #@param ["auto", "9:16", "16:9", "8:9"]' in gen
    assert "WIDTH = 0" in gen and "HEIGHT = 0" in gen
    assert "DURATION_S = 10" in gen
    assert "USE_LORA = True" in gen
    assert "build_i2v_graph" in gen
    assert "assert_i2v_graph" in gen
    assert "i2v_retry_plans" in gen
    assert "resolve_i2v_prompt" in gen
    assert "validate_i2v_prompt" in gen
    assert "canvas_for_aspect(ASPECT, image_size=image_size)" in gen
    assert "is_auto_image_name" in gen
    assert "first_image=first" in gen
    assert "build_t2v_graph" not in gen
