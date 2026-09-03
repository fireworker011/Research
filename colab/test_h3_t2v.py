import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from h3_t2v import (
    CANVAS_9_16,
    CANVAS_9_16_MIN,
    DEFAULT_T2V_PROMPT,
    assert_t2v_graph,
    build_t2v_graph,
    is_9_16,
    resolve_t2v_prompt,
    t2v_colab_url,
    t2v_retry_plans,
    validate_t2v_prompt,
)


def test_9_16_canvas():
    assert is_9_16(576, 1024)
    assert is_9_16(*CANVAS_9_16)
    assert is_9_16(*CANVAS_9_16_MIN)
    assert not is_9_16(768, 864)


def test_t2v_prompt_default_and_forbidden():
    p = resolve_t2v_prompt("")
    assert p == DEFAULT_T2V_PROMPT
    assert validate_t2v_prompt(p) == []
    assert "px.a8.net" not in p
    assert "広告" in p
    assert validate_t2v_prompt("ok https://px.a8.net/x")
    assert any("forbidden" in e for e in validate_t2v_prompt("月収100万"))
    assert validate_t2v_prompt("") == ["T2V prompt is empty"]


def test_t2v_graph_has_no_first_frame():
    g = build_t2v_graph(
        prompt=DEFAULT_T2V_PROMPT,
        unet="minimax_h3_fl2va_pruned_int8_convrot.safetensors",
        lora_name="minimax_h3_fl2v_turbo_4step.safetensors",
        lora_strength=1.0,
        width=CANVAS_9_16[0],
        height=CANVAS_9_16[1],
        duration_s=5,
        seed=1,
        steps=4,
        filename_prefix="video/h3_t2v",
    )
    assert assert_t2v_graph(g) == []
    assert "first_frame" not in g["20"]["inputs"]
    assert g["20"]["inputs"]["width"] == 576
    assert g["20"]["inputs"]["height"] == 1024
    assert "100" not in g


def test_t2v_retry_plans_stay_vertical():
    plans = t2v_retry_plans(width=576, height=1024)
    assert plans[0]["label"] == "576x1024"
    assert any(p["label"] == "288x512" for p in plans)


def test_t2v_colab_url():
    url = t2v_colab_url()
    assert url.endswith("minimax_h3_t2v_phone.ipynb")
    assert "cursor/minimax-h3-motion-identity-e959" in url


def _t2v_nb():
    root = Path(__file__).resolve().parents[1]
    return json.loads((root / "minimax_h3_t2v_phone.ipynb").read_text(encoding="utf-8"))


def test_t2v_phone_notebook_is_three_cells():
    import json

    nb = _t2v_nb()
    codes = [c for c in nb["cells"] if c["cell_type"] == "code"]
    assert len(codes) == 3
    blob = "\n".join("".join(c.get("source") or []) for c in nb["cells"])
    assert "build_t2v_graph" in blob
    assert "first_frame" not in blob or "must not wire first_frame" in blob or "no first frame" in blob.lower() or "T2V" in blob
    assert "WIDTH = 576" in blob
    assert "HEIGHT = 1024" in blob
    assert "MiniMaxH3ReferenceToVideo" not in blob
    assert "px.a8.net" not in blob
    assert "display(Video" in blob
    for i, cell in enumerate(codes):
        src = "".join(cell.get("source") or [])
        compile(src, f"t2v_cell{i+1}.py", "exec")
