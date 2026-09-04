import sys
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from h3_lora_studio import (
    apply_user_prompt,
    civitai_download_url,
    civitai_token,
    civitai_token_help,
    explain_choice,
    friendly_lora,
    friendly_select_error,
    inject_lora_stack,
    is_blank_prompt,
    is_vanilla,
    load_catalog,
    looks_like_safetensors,
    merge_optional,
    missing_civitai_files,
    quote_http_url,
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


def test_inject_thin_turbo_keeps_larry():
    g = build_t2v_graph(
        prompt=DEFAULT_T2V_PROMPT,
        unet="minimax_h3_fl2va_pruned_int8_convrot.safetensors",
        lora_name=None,
        lora_strength=0.0,
        width=CANVAS_9_16[0],
        height=CANVAS_9_16[1],
        duration_s=5,
        seed=1,
        steps=4,
        filename_prefix="video/h3_t2v",
    )
    stack = [
        {"id": "blowjob-h3", "filename": "H3_blowjob_v1.safetensors", "strength_model": 0.75},
        {"id": "penis-lora-h3", "filename": "PENISLORA_H3.safetensors", "strength_model": 0.7},
        {"id": "larry-v4", "filename": "minimax_h3_turbo_v4_step600_ema_comfy.safetensors", "strength_model": 0.7},
    ]
    inject_lora_stack(g, stack, sampler={"sampler_name": "euler", "scheduler": "simple", "steps": 8})
    names = [n["inputs"]["lora_name"] for n in g.values() if n.get("class_type") == "LoraLoaderModelOnly"]
    assert any("turbo_v4" in n.lower() for n in names)
    assert g["22"]["inputs"]["sampler_name"] == "euler"
    assert g["23"]["inputs"]["scheduler"] == "simple"
    assert g["23"]["inputs"]["steps"] == 8
    assert assert_t2v_graph(g) == []


def test_merge_optional_skips_photoreal_on_i2v():
    catalog = load_catalog(Path(__file__).resolve().parents[1] / "h3-lora-studio")
    stack = [{"id": "anal-penetration-coachbate", "filename": "H3_anal_penetration_v1.safetensors", "strength_model": 0.85}]
    out = merge_optional(stack, extras=["photoreal-h3-still", "astro-nsfw-h3"], catalog=catalog, mode="i2v")
    ids = [row["id"] for row in out]
    assert ids == ["anal-penetration-coachbate"]
    assert "astro-nsfw-h3" not in ids


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
    assert resolve_situation("アナル挿入（画質）") == "anal_penetration"
    assert resolve_situation("アナル舐め・指") == "anal_closeup"
    assert resolve_situation("試し打ち") == "preview"
    assert resolve_situation("汎用エロ") == "general_sex"
    help_text = explain_choice("アナル挿入（画質）", "テキストから（写真なし）")
    assert "Turbo なし" in help_text or "CoachBate" in help_text
    assert resolve_situation("日常（速い＋綺麗）") == "sfw_daily"
    assert resolve_situation("最速プレビュー（エロなし）") == "sfw_preview"
    assert resolve_situation("音も残す（エロなし）") == "sfw_audio"
    sfw = explain_choice("日常（速い＋綺麗）", "テキストから（写真なし）")
    assert "Larry" in sfw
    assert "エロ用は入れません" in sfw
    assert "blowjob-h3" not in sfw


def test_vanilla_sfw_shares_phone_path():
    assert resolve_situation("普通（エロなし）") == "vanilla"
    assert is_vanilla("普通（エロなし）")
    assert not is_vanilla("フェラ")
    assert situation_ids("vanilla") == []
    text = explain_choice("普通（エロなし）", "テキストから（写真なし）")
    assert "えっち用の部品は使いません" in text
    assert "Turbo" in text


def test_optional_prompt_uses_custom_or_default():
    assert is_blank_prompt("")
    assert is_blank_prompt("（シーン）")
    default_t2v, custom = apply_user_prompt("", mode="t2v", default_prompt="DEFAULT SCENE")
    assert custom is False
    assert default_t2v == "DEFAULT SCENE"
    own, custom = apply_user_prompt("Adult woman walks through a quiet kitchen.", mode="t2v", default_prompt="DEFAULT SCENE")
    assert custom is True
    assert "kitchen" in own
    assert "Picture 1" not in own
    i2v, custom = apply_user_prompt("she smiles and looks at the camera", mode="i2v", default_prompt="DEFAULT I2V")
    assert custom is True
    assert "<Picture 1>" in i2v
    assert "smiles" in i2v
    locked, custom = apply_user_prompt("Keep <Picture 1> identity. She waves.", mode="i2v")
    assert custom is True
    assert locked.startswith("Keep <Picture 1>")


def test_civitai_redirect_quotes_chinese_filename():
    raw = "https://civitai.com/api/download/models/3289775?fileId=3174203"
    assert civitai_download_url({
        "civitai_version_id": 3289775,
        "civitai_file_id": 3174203,
    }) == raw
    loc = "https://cdn.example/Minimax H3真实电影质感V0.1（解决张量报错）.safetensors"
    quoted = quote_http_url(loc)
    path = urllib.parse.urlsplit(quoted).path
    assert " " not in path
    assert "真实" not in quoted
    assert urllib.parse.unquote(path).endswith(".safetensors")


def test_looks_like_safetensors(tmp_path):
    fake_html = tmp_path / "page.safetensors"
    fake_html.write_bytes(b"<html>login</html>" + b"\0" * 1_200_000)
    assert looks_like_safetensors(fake_html) is False
    header = b'{"__metadata__":{"format":"pt"}}'
    real = tmp_path / "real.safetensors"
    real.write_bytes(len(header).to_bytes(8, "little") + header + b"\0" * 1_200_000)
    assert looks_like_safetensors(real) is True
    tiny = tmp_path / "tiny.safetensors"
    tiny.write_bytes(b'{"error":"no"}')
    assert looks_like_safetensors(tiny) is False


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


def test_studio_cell3_skips_homage_ad_prompt():
    writer = Path(__file__).resolve().parent / "_write_lora_studio_nb.py"
    src = writer.read_text(encoding="utf-8")
    assert "validate_studio_i2v_prompt" in src
    assert "homage = bool(VANILLA and not CUSTOM_PROMPT)" in src
    assert "assert_i2va_graph(g, expect_last=False, homage=homage)" in src
    nb_path = Path(__file__).resolve().parents[1] / "minimax_h3_lora_studio.ipynb"
    blob = nb_path.read_text(encoding="utf-8")
    assert "homage=homage" in blob
    assert "validate_studio_i2v_prompt" in blob
    assert "validate_motion_ad_prompt(prompt, with_last_frame=False)" in blob
    assert "写真用の文が文章欄に残っています" in src
    assert "friendly_select_error" in src
    assert "追加の禁止語" in src
    assert "forbidden.json" in src
    assert "except Exception:" in src
    assert "def extra_terms(" in src


def test_friendly_select_error_for_child_and_picture1():
    assert "空欄" in (friendly_select_error(SystemExit("forbidden subject in prompt: ['child']")) or "")
    assert "写真用" in (friendly_select_error(SystemExit("t2v prompt must not use Picture 1 / first_frame")) or "")
    assert friendly_select_error(SystemExit("CoachBate anal penetration stays turbo off")) is None
