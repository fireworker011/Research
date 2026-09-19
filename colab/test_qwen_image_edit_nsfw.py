import ast
import json
from pathlib import Path

from PIL import Image

from qwen_image_edit_nsfw import (
    DEFAULT_EDIT_PROMPT,
    FUTA_LOCK,
    KEEP_LOCK,
    PIPE_ID,
    STEPS,
    TRANSFORMER_ID,
    TRUE_CFG,
    compose_edit_prompt,
    disable_safety,
    infer_kwargs,
    lora_stack,
    require_l4_or_exit,
    resize_rgb,
    save_jpeg,
    snapped_size,
)

ROOT = Path(__file__).resolve().parent
WRITER = ROOT / "_write_qwen_edit_nb.py"


def test_stack_is_mk1227_class():
    assert PIPE_ID == "Qwen/Qwen-Image-Edit-2511"
    assert TRANSFORMER_ID == "prithivMLmods/Qwen-Image-Edit-Rapid-AIO-V23"
    assert STEPS == 4
    assert TRUE_CFG == 1.0
    assert "20cm" in FUTA_LOCK
    assert "no testicles" in FUTA_LOCK
    assert "Change clothing only" in KEEP_LOCK
    assert "Remove only the clothes" in DEFAULT_EDIT_PROMPT


def test_compose_empty_adds_futa_undress():
    out = compose_edit_prompt("")
    assert "Change clothing only" in out
    assert "Remove only the clothes" in out
    assert "20cm" in out
    assert "no testicles" in out


def test_compose_keeps_user_and_still_locks():
    out = compose_edit_prompt("same green dress stairs", undress=True, futa=True)
    assert "same green dress stairs" in out
    assert "Remove only the clothes" in out
    assert "20cm" in out


def test_lora_stack_undress_futa():
    names = [row[0] for row in lora_stack(True, True)]
    assert names == ["remove_clothing", "qwen_uncensor", "CockQwen_v3"]
    assert lora_stack(False, False) == []


def test_require_l4_rejects_t4():
    try:
        require_l4_or_exit(15.0, "Tesla T4")
    except SystemExit as e:
        assert "L4" in str(e)
    else:
        raise AssertionError("T4 must exit")
    require_l4_or_exit(22.5, "L4")


def test_resize_and_jpeg(tmp_path):
    im = Image.new("RGB", (1008, 1792), (10, 20, 30))
    out = resize_rgb(im, 576, 1024)
    assert out.size == (576, 1024)
    assert snapped_size(577, 1025) == (576, 1024)
    dest = save_jpeg(out, tmp_path / "x.jpg")
    assert dest.is_file()


def test_disable_safety_and_infer_kwargs():
    class Fake:
        safety_checker = object()
        requires_safety_checker = True

    pipe = disable_safety(Fake())
    assert pipe.safety_checker is None
    assert pipe.requires_safety_checker is False
    kw = infer_kwargs("hello", true_cfg=1.0)
    assert kw["num_inference_steps"] == 4
    assert kw["true_cfg_scale"] == 1.0
    assert kw["negative_prompt"] == " "


def test_writer_notebook_is_separate_l4_nsfw():
    ast.parse(WRITER.read_text(encoding="utf-8"))
    src = WRITER.read_text(encoding="utf-8")
    assert "prithivMLmods/Qwen-Image-Edit-Rapid-AIO-V23" in src
    assert "Qwen/Qwen-Image-Edit-2511" in src
    assert '"gpuType": "L4"' in src
    assert "disable_safety" in src
    assert "from h3_lora_studio" not in src
    assert "import h3_lora_studio" not in src
    assert "minimax_h3_lora_studio" in src  # link only
    assert "同時に動かさない" in src
    assert "qwen-image-edit-nsfw/output" in src
    nb_path = ROOT.parent / "qwen_image_edit_nsfw.ipynb"
    nb = json.loads(nb_path.read_text(encoding="utf-8"))
    assert nb["metadata"]["colab"]["gpuType"] == "L4"
    joined = "".join("".join(c["source"]) for c in nb["cells"])
    assert "Rapid-AIO-V23" in joined
    assert "Qwen-Image-Edit-2511" in joined
    assert "disable_safety" in joined
    assert "files.upload" in joined
