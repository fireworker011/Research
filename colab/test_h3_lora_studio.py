import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from h3_lora_studio import (
    civitai_token,
    civitai_token_help,
    explain_choice,
    friendly_lora,
    inject_lora_stack,
    is_vanilla,
    load_catalog,
    merge_optional,
    missing_civitai_files,
    resolve_mode,
    resolve_situation,
    situation_ids,
)
from h3_t2v import CANVAS_9_16, DEFAULT_T2V_PROMPT, assert_t2v_graph, build_t2v_graph


def test_inject_stack_drops_turbo_and_chains():
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
    stack = [
        {"id": "synth-pussy-h3", "filename": "SynthPussy_H3_closeups_v1-step00008300.safetensors", "strength_model": 0.75},
        {"id": "anal-penetration-coachbate", "filename": "H3_anal_penetration_v1.safetensors", "strength_model": 0.85},
    ]
    inject_lora_stack(g, stack, steps=16)
    assert "2" not in g
    assert g["201"]["inputs"]["lora_name"] == "SynthPussy_H3_closeups_v1-step00008300.safetensors"
    assert g["202"]["inputs"]["model"] == ["201", 0]
    assert g["23"]["inputs"]["model"] == ["202", 0]
    assert g["22"]["inputs"]["sampler_name"] == "res_multistep"
    assert g["23"]["inputs"]["scheduler"] == "beta"
    assert g["23"]["inputs"]["steps"] >= 16
    assert assert_t2v_graph(g) == []
    names = [n["inputs"]["lora_name"] for n in g.values() if n.get("class_type") == "LoraLoaderModelOnly"]
    assert all("turbo" not in n.lower() for n in names)


def test_prefer_turbo_ignores_nsfw_files(tmp_path):
    from h3_motion_graphics import prefer_fl2v_lora

    turbo = tmp_path / "minimax_h3_fl2v_turbo_4step.safetensors"
    nsfw = tmp_path / "SynthPussy_H3_closeups_v1.safetensors"
    turbo.write_bytes(b"x")
    nsfw.write_bytes(b"x")
    assert prefer_fl2v_lora([nsfw, turbo], True) == turbo.name


def test_merge_optional_skips_photoreal_on_i2v():
    catalog = load_catalog(Path(__file__).resolve().parents[1] / "h3-lora-studio")
    stack = [{"id": "anal-penetration-coachbate", "filename": "H3_anal_penetration_v1.safetensors", "strength_model": 0.85}]
    out = merge_optional(stack, extras=["photoreal-h3-still", "astro-nsfw-h3"], catalog=catalog, mode="i2v")
    ids = [row["id"] for row in out]
    assert "photoreal-h3-still" not in ids
    assert "astro-nsfw-h3" in ids


def test_japanese_form_labels():
    assert resolve_situation("穴アップ（舐め・指）") == "anal_closeup"
    assert resolve_situation("アナル挿入") == "anal_penetration"
    assert resolve_mode("テキストから（写真なし）") == "t2v"
    assert resolve_mode("写真から（1枚必要）") == "i2v"
    text = explain_choice("フェラ", "テキストから（写真なし）")
    assert "写真は使いません" in text
    assert "フェラ" in text
    assert "竿" in text
    assert "blowjob-h3" not in text
    assert friendly_lora("synth-pussy-h3") == "穴の見え方"


def test_vanilla_sfw_shares_phone_path():
    assert resolve_situation("普通（エロなし）") == "vanilla"
    assert is_vanilla("普通（エロなし）")
    assert not is_vanilla("フェラ")
    assert situation_ids("vanilla") == []
    text = explain_choice("普通（エロなし）", "テキストから（写真なし）")
    assert "えっち用の部品は使いません" in text
    assert "Turbo" in text


def test_civitai_token_prefers_form(monkeypatch):
    monkeypatch.delenv("CIVITAI_API_TOKEN", raising=False)
    assert civitai_token(form_value="  pasted-key  ") == "pasted-key"
    monkeypatch.setenv("CIVITAI_API_TOKEN", "from-env")
    assert civitai_token(form_value="") == "from-env"
    assert civitai_token(form_value="form-wins") == "form-wins"
    help_text = civitai_token_help()
    assert "CivitaiのAPIキー" in help_text
    assert "user/account" in help_text
    dest = Path("/tmp/h3-missing-lora.safetensors")
    if dest.exists():
        dest.unlink()
    jobs = [("https://example.invalid", dest, {"source": "civitai"})]
    assert missing_civitai_files(jobs) == ["h3-missing-lora.safetensors"]
