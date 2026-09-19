import ast
import json
import re
from pathlib import Path

from PIL import Image

from qwen_image_edit_nsfw import (
    DEFAULT_EDIT_PROMPT,
    FUTA_LOCK,
    KEEP_LOCK,
    LORA_FILES,
    PIPE_ID,
    SEX_ACT_PRESETS,
    SEX_PRESET_DEFAULT,
    SEX_PRESETS,
    STEPS,
    TRANSFORMER_ID,
    TRUE_CFG,
    apply_futa_partner,
    compose_edit_prompt,
    disable_safety,
    infer_kwargs,
    is_sex_act_preset,
    lora_stack,
    require_l4_or_exit,
    resize_rgb,
    save_jpeg,
    sex_preset_form_options,
    sex_preset_labels,
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


def test_sex_preset_labels_match_space_ui():
    labels = sex_preset_labels()
    assert labels == [
        "服を脱ぐ",
        "ウェットシャワー",
        "レースランジェリー",
        "ビキニ",
        "濡れたTシャツ",
        "フェラチオの視点",
        "セルフタッチ",
        "宣教師",
        "カウガール",
        "乳房プレイ",
        "フェイシャル",
        "肛門リフト",
    ]
    opts = sex_preset_form_options()
    assert opts[0] == SEX_PRESET_DEFAULT
    assert opts[1:] == labels
    assert set(SEX_ACT_PRESETS) <= set(labels)
    assert "Qwen4Play_v2" in LORA_FILES


def test_futa_partner_rewrites_sex_acts_and_drops_man():
    man = re.compile(r"\b(?:man|man's|men|male pov)\b", re.I)
    subject_lock = "standing in front of the crotch"
    for label in (
        "フェラチオの視点",
        "宣教師",
        "カウガール",
        "乳房プレイ",
        "フェイシャル",
        "肛門リフト",
    ):
        assert is_sex_act_preset(label)
        raw = SEX_PRESETS[label]
        out = apply_futa_partner(raw)
        assert man.search(raw), label
        assert man.search(out) is None, (label, out)
        assert "futanari" in out.lower()
        assert "Not a man. The penis is a futanari" not in out
        composed = compose_edit_prompt("", preset=label, futa=True)
        assert man.search(composed) is None, label
        assert subject_lock not in composed
        if "penis" in raw.lower():
            assert "20cm" in composed
        else:
            assert "futanari" in composed.lower()


def test_compose_sex_act_strings():
    oral = compose_edit_prompt("", preset="フェラチオの視点")
    assert "oral sex" in oral.lower()
    assert "futanari POV" in oral
    mission = compose_edit_prompt("", preset="宣教師")
    assert "inserted" in mission.lower()
    assert "vagina" in mission.lower()
    cow = compose_edit_prompt("", preset="カウガール")
    assert "Cowgirl" in cow
    assert "futanari POV" in cow
    anal = compose_edit_prompt("", preset="肛門リフト")
    assert "anus" in anal.lower()
    assert "futanari" in anal.lower()
    bikini = compose_edit_prompt("", preset="ビキニ", undress=True, futa=True)
    assert "string bikini" in bikini
    assert "Remove only the clothes" not in bikini
    assert "20cm" not in bikini


def test_lora_stack_sex_uses_qwen4play():
    names = [row[0] for row in lora_stack(True, True, preset="カウガール")]
    assert names == ["qwen_uncensor", "Qwen4Play_v2", "CockQwen_v3"]
    names = [row[0] for row in lora_stack(True, False, preset="フェラチオの視点")]
    assert names == ["qwen_uncensor", "Qwen4Play_v2"]
    assert lora_stack(True, True, preset="ビキニ") == []
    names = [row[0] for row in lora_stack(True, True)]
    assert names == ["remove_clothing", "qwen_uncensor", "CockQwen_v3"]


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
    for label in (
        "クイックプロンプト",
        "服を脱ぐ",
        "ウェットシャワー",
        "レースランジェリー",
        "ビキニ",
        "濡れたTシャツ",
        "フェラチオの視点",
        "セルフタッチ",
        "宣教師",
        "カウガール",
        "乳房プレイ",
        "フェイシャル",
        "肛門リフト",
        "preset=クイックプロンプト",
        "Qwen4Play",
    ):
        assert label in src
        if label != "preset=クイックプロンプト":
            assert label in joined
