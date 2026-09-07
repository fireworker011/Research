import json
import os
import re
import sys
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from h3_lora_studio import (
    apply_user_prompt,
    has_i2v_lock,
    t2v_user_text,
    civitai_download_url,
    civitai_token,
    civitai_token_help,
    clamp_studio_duration,
    concat_studio_clips,
    continue_chain_prompt,
    download_jobs_for,
    explain_choice,
    extract_last_frame,
    format_job_fail,
    friendly_lora,
    friendly_select_error,
    inject_lora_stack,
    is_blank_prompt,
    is_vanilla,
    load_catalog,
    looks_like_safetensors,
    already_have_weight,
    merge_optional,
    missing_civitai_files,
    next_chain_prompt,
    quote_http_url,
    resolve_length_mode,
    resolve_mode,
    resolve_situation,
    resolve_studio_length,
    rewrite_chain_opening_prompt,
    strip_chain_restart_language,
    situation_ids,
    studio_clip_plan,
)
from h3_t2v import CANVAS_9_16, DEFAULT_T2V_PROMPT, assert_t2v_graph, build_t2v_graph


def _check_visible_plan(planned, clip_prompt):
    """futa_visible: spoken 「line」 clips drop cinema+Larry (jaw melt); walk/kiss keep thin Larry 8step."""
    ids = [row["id"] for row in planned["stack"]]
    if "「" in clip_prompt:
        assert ids == ["penis-lora-h3"], ids
        assert planned["cfg"]["turbo"] is False
        assert planned["turbo"] is False
        assert planned["sampler"]["steps"] == 12
        assert planned["sampler"]["sampler_name"] == "res_multistep"
        assert "[AUDIO-LOCK]" in planned["prompt"]
        assert "spoken_transcript: once" in planned["prompt"]
        assert "repeat: 0" in planned["prompt"]
        assert "プロンプトは読まない" not in planned["prompt"]
    else:
        assert ids == ["penis-lora-h3", "larry-v4", "cinema-dy"], ids
        assert planned["cfg"]["turbo"] is True
        assert planned["turbo"] is True
        assert planned["sampler"]["steps"] == 8
        assert planned["sampler"]["sampler_name"] == "euler"
        assert "spoken_transcript: mute" in planned["prompt"]
        assert "誰も話さない" not in planned["prompt"]
    assert "LIP SYNC" not in planned["prompt"] or "「" in clip_prompt


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
    assert resolve_situation("フェラ") == "oral"
    assert resolve_situation("フェラ（女体）") == "oral"
    text = explain_choice("フェラ（女体）", "テキストから（写真なし）")
    assert "写真は使いません" in text
    assert "フェラ" in text
    assert "竿" in text
    assert "男なし" in text
    assert "blowjob-h3" not in text
    assert friendly_lora("synth-pussy-h3") == "穴の見え方"
    assert resolve_situation("アナル挿入（画質）") == "anal_penetration"
    assert resolve_situation("アナル舐め・指") == "anal_closeup"
    assert resolve_situation("アナル指入れ") == "anal_fingering"
    assert resolve_situation("アナル指いれ") == "anal_fingering"
    assert resolve_situation("試し打ち") == "preview"
    assert resolve_situation("汎用エロ") == "general_sex"
    assert resolve_situation("汎用エロ（女体）") == "general_sex"
    assert resolve_situation("レズビアンクンニ") == "lesbian_cunnilingus"
    assert resolve_situation("性器を広げる") == "pussy_spread"
    assert resolve_situation("レズ＋広げる") == "lesbian_spread"
    assert resolve_situation("セックス（女体）") == "futa_sex"
    assert resolve_situation("ふたなりセックス") == "futa_sex"
    assert resolve_situation("アナルセックス（女体）") == "futa_anal"
    assert resolve_situation("アナルセックス") == "futa_anal"
    assert resolve_situation("騎乗位（女体）") == "riding"
    assert resolve_situation("騎乗位") == "riding"
    assert resolve_situation("後背位（女体）") == "doggy"
    assert resolve_situation("正常位POV（女体）") == "missionary_pov"
    assert resolve_situation("後射精（女体）") == "after_ejaculation"
    assert resolve_situation("後射精") == "after_ejaculation"
    assert resolve_situation("顔射（女体）") == "facial"
    assert resolve_situation("顔射") == "facial"
    assert resolve_situation("中出し（女体）") == "creampie"
    assert resolve_situation("中出し") == "creampie"
    assert resolve_situation("膣中出し") == "creampie"
    assert resolve_situation("口内射精（女体）") == "oral_creampie"
    assert resolve_situation("口内射精") == "oral_creampie"
    assert resolve_situation("口内") == "oral_creampie"
    assert resolve_situation("指入れ") == "fingering"
    assert resolve_situation("オナニー") == "masturbation"
    assert resolve_situation("足コキ") == "footjob"
    assert resolve_situation("絶頂") == "remote_orgasm"
    futa_sex = explain_choice("セックス（女体）", "テキストから（写真なし）")
    assert "総合えっち" in futa_sex or "竿" in futa_sex
    assert "男" in futa_sex
    assert "hmnsfw-aio-v25" not in futa_sex
    futa_anal = explain_choice("アナルセックス（女体）", "テキストから（写真なし）")
    assert "Turbo" in futa_anal or "CoachBate" in futa_anal
    assert "竿" in futa_anal
    assert friendly_lora("lesbian-cunnilingus-h3") == "レズクンニ"
    assert friendly_lora("pussy-spread-h3") == "性器を広げる"
    les = explain_choice("レズビアンクンニ", "テキストから（写真なし）")
    assert "クンニ" in les
    assert "穴の見え方" in les
    help_text = explain_choice("アナル挿入（画質）", "テキストから（写真なし）")
    assert "Turbo なし" in help_text or "CoachBate" in help_text
    assert resolve_situation("日常（速い＋綺麗）") == "sfw_daily"
    assert resolve_situation("最速プレビュー（エロなし）") == "sfw_preview"
    assert resolve_situation("音も残す（エロなし）") == "sfw_audio"
    sfw = explain_choice("日常（速い＋綺麗）", "テキストから（写真なし）")
    assert "Larry" in sfw
    assert "エロ用は入れません" in sfw
    assert "blowjob-h3" not in sfw
    general = explain_choice("汎用エロ（女体）", "テキストから（写真なし）")
    assert "Larry" in general
    assert "12step" in general
    assert "男なし" in general
    assert "LightX2V 12" not in general
    riding = explain_choice("騎乗位（女体）", "テキストから（写真なし）")
    assert "騎乗" in riding
    assert "AIO は積まない" in riding
    assert "ヘルパー0〜2" in riding
    assert "cowgirl-position-h3" not in riding
    after = explain_choice("後射精（女体）", "テキストから（写真なし）")
    assert "射精" in after
    assert "絶頂" in after
    assert "hmcumshot-v2" not in after
    facial = explain_choice("顔射（女体）", "テキストから（写真なし）")
    assert "顔射" in facial
    assert "後射精" in facial
    assert "facial-cumshot-h3" not in facial
    anal_finger = explain_choice("アナル指入れ", "写真から（1枚必要）")
    assert "アナル指入れ" in anal_finger or "ThumbInButt" in anal_finger
    assert "指入れ（膣）" in anal_finger or "アナルセックス" in anal_finger
    assert "thumbinbutt-h3" not in anal_finger
    assert "写真" in anal_finger
    cream = explain_choice("中出し（女体）", "写真から（1枚必要）")
    assert "中出し" in cream
    assert "口内" in cream or "顔射" in cream or "後射精" in cream
    assert "final-thrust-h3" not in cream
    assert "男なし" in cream
    oral_c = explain_choice("口内射精（女体）", "写真から（1枚必要）")
    assert "口内" in oral_c
    assert "CUMOUF" in oral_c
    assert "cumouf-h3" not in oral_c
    assert friendly_lora("final-thrust-h3") == "中出し"
    assert friendly_lora("cumouf-h3") == "口内射精"
    assert friendly_lora("cowgirl-position-h3") == "騎乗"
    assert friendly_lora("doggy-h3") == "後背位"
    assert friendly_lora("hmcumshot-v2") == "射精"
    assert friendly_lora("facial-cumshot-h3") == "顔射"
    assert "ThumbInButt" in friendly_lora("thumbinbutt-h3")
    futa_anal_help = explain_choice("アナルセックス（女体）", "写真から（1枚必要）")
    assert "ThumbInButt" in futa_anal_help
    assert "Turbo なし" in futa_anal_help
    assert "12step" in futa_anal_help
    assert "CoachBate" not in futa_anal_help
    assert "男なし" in futa_anal_help
    assert friendly_lora("remote-orgasm-h3") == "絶頂"


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
    leftover = (
        "For the target video, at 0.00 seconds into the target video, "
        "<Picture 1> (from [Shot 1]) is fully referenced.\nAya waves."
    )
    assert has_i2v_lock(leftover) is True
    assert t2v_user_text(leftover) == ""
    dropped, custom = apply_user_prompt(leftover, mode="t2v", default_prompt="（シーン）")
    assert custom is False
    assert dropped == "（シーン）"
    assert "Picture 1" not in dropped
    kept, custom = apply_user_prompt("Adult woman rides, already in.", mode="t2v", default_prompt="（シーン）")
    assert custom is True
    assert "rides" in kept
    assert has_i2v_lock("") is False


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
    big = tmp_path / "big.bin"
    big.write_bytes(b"not-safetensors" + b"\0" * 6_000_000)
    assert already_have_weight(big) is True
    assert already_have_weight(fake_html) is False
    assert already_have_weight(real) is True
    assert already_have_weight(tiny) is False


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
    assert "homage = bool(VANILLA and not CUSTOM_PROMPT and CLIP_INDEX == 0)" in src
    assert "assert_i2va_graph(g, expect_last=False, homage=homage)" in src
    nb_path = Path(__file__).resolve().parents[1] / "minimax_h3_lora_studio.ipynb"
    blob = nb_path.read_text(encoding="utf-8")
    code = "\n".join("".join(c["source"]) for c in json.loads(blob)["cells"])
    assert "homage=homage" in blob
    assert "validate_studio_i2v_prompt" in blob
    assert "validate_motion_ad_prompt(prompt, with_last_frame=False)" in blob
    assert "写真用の文" in src
    assert "写真欄はテキストからでは使いません" in src
    assert "残っていたので外します" in src
    assert "テキストから作るときは、写真ロックの文を入れません" not in src
    assert "friendly_select_error" in src
    assert "forbidden.json" in src
    assert "追加の禁止語 =" not in src
    assert "FORBIDDEN_FILE" in src
    assert "forbidden_path=FORBIDDEN_FILE" in src
    assert "forbidden_words.py" not in src
    assert "h3-lora-studio/scripts/forbidden_words.py" not in blob
    assert "from forbidden_words" not in blob
    assert "format_job_fail" in src
    assert "timeout=3600" in src
    assert "format_job_fail(GRAPH_MODE, payload)" in src
    assert "format_prompt_http_fail(err, stack)" in src
    assert "失敗しました。②からやり直すか、シーンを変えてみてください。" not in src
    assert "apply_stack_fallbacks" in src
    assert "restart_studio_comfy" in src
    assert "apply_stack_fallbacks" in blob
    assert "format_prompt_http_fail(err, stack)" in blob
    assert "写真から作るなら input の jpg" not in src
    assert ".h3_pip_ok" in src
    assert "更新はしません" in src
    helper = Path(__file__).resolve().parent / "h3_lora_studio.py"
    assert "テキストから作れませんでした" in helper.read_text(encoding="utf-8")
    assert "already_have_weight" in helper.read_text(encoding="utf-8")
    assert "騎乗位（女体）" in src
    assert "後射精（女体）" in src
    assert "h3-lora-studio/profiles/after_ejaculation.json" in src
    assert "h3-lora-studio/profiles/facial.json" in src
    assert "h3-lora-studio/profiles/anal_fingering.json" in src
    assert "h3-lora-studio/profiles/creampie.json" in src
    assert "h3-lora-studio/profiles/oral_creampie.json" in src
    assert "h3-lora-studio/profiles/doggy.json" in src
    assert 'FETCH_REV = "h3-20260907-audio-2"' in src
    assert "**ふたなりの既定:**" in src
    assert "竿＋マンコ、金玉なし" in src
    assert "「」の中はカタカナ" in src
    assert "漢字のまま" not in src
    assert "中出し（女体）" in src
    assert "口内射精（女体）" in src
    for short in ("帰宅", "洗い物", "登校", "授業", "屋上", "おかえり", "風呂", "食卓", "布団", "休日", "縁側"):
        for play in ("専用", "つなぐ", "つなぐ修", "参照つなぐ", "参照つなぐ修"):
            assert f"{short}（{play}）" in blob, (short, play)
    assert "訪問販売60秒（つなぐ）" in blob
    assert "定期検診100秒（つなぐ）" in blob
    assert "終点40秒（つなぐ）" in blob
    # Legacy long labels stay as SITUATION_JA aliases, not as the dropdown default.
    assert resolve_situation("登校120秒（専用）") == "commute-120s"
    assert 'やりたいシーン = "登校120秒（専用）"' not in code
    assert "validate_story_follow" in src
    assert "カット編集" in src
    assert "h3-lora-studio/stories/homecoming-90s.json" in src
    assert "h3-lora-studio/stories/dishes-90s.json" in src
    assert "h3-lora-studio/stories/commute-120s.json" in src
    assert "h3-lora-studio/stories/lecture-120s.json" in src
    assert "h3-lora-studio/stories/rooftop-100s.json" in src
    assert "h3-lora-studio/stories/okaeri-120s.json" in src
    assert "h3-lora-studio/stories/bath-120s.json" in src
    assert "h3-lora-studio/stories/dinner-120s.json" in src
    assert "h3-lora-studio/stories/futon-120s.json" in src
    assert "h3-lora-studio/stories/sunday-120s.json" in src
    assert "h3-lora-studio/stories/engawa-120s.json" in src
    assert 'if STORY:\n    w, h = int(planned0["width"]), int(planned0["height"])' in src
    assert 'FILENAME_PREFIX = "video/h3_" + str(STORY.get("id") or "story")' in src
    assert "input/dishes-90s/" in src
    assert "h3-lora-studio/profiles/futa_visible.json" in src
    assert "CoachBate 0.85" not in src
    assert "穴が膣より上" in src
    assert "フェラ（女体）" in src
    assert "汎用エロ（女体）" in src
    assert "顔射（女体）" in src
    assert "アナル指入れ" in src
    assert "騎乗位（女体）" in blob
    assert "後射精（女体）" in blob
    assert "顔射（女体）" in blob
    assert "アナル指入れ" in blob
    assert "h3-20260907-audio-2" in blob
    assert "h3-20260907-act15-1" not in blob
    assert "h3-20260907-door-visit-1" not in blob
    assert "h3-20260907-checkup-face-1" not in blob
    assert "input/commute-120s/" in src
    assert 'やりたいシーン = "登校（専用）"' in code
    assert '今使うシーン = "登校（専用）"' in code
    assert "force_t2v=FORCE_T2V" in src
    assert "作り方はテキストから。専用フォルダの写真は使いません。" in src
    assert "rewrite_chain_opening_prompt" in src
    assert "つなぐモード" in src
    assert "を（専用）で選んでいるので「つなぐ」は使いません" in src
    assert "（専用＝カット）" in src
    assert "CHAIN = False" in src
    assert "input/lecture-120s/" in src
    assert "input/rooftop-100s/" in src
    assert "input/okaeri-120s/" in src
    assert "input/bath-120s/" in src
    assert "input/dinner-120s/" in src
    assert "input/futon-120s/" in src
    assert "input/sunday-120s/" in src
    assert "input/engawa-120s/" in src
    assert "apply_drive_cache_env" in src
    assert "stage_models_to_local" in src
    assert "warmup_h3_engine" in src
    assert "PIP_CACHE_DIR" in src
    assert "CUDA_MODULE_LOADING" in src
    assert 'HF_HOME' in src
    assert "link_dir(models_root / sub, DRIVE_MODELS / sub)" not in src
    assert "中出し（女体）" in blob
    assert "口内射精（女体）" in blob
    assert "fetch_comfy_object_info" in src
    assert "comfy_alive" in src
    assert "wait_comfy_ready" in src
    assert "comfy_free(PORT)" in src
    assert "同じサイズ再試行" in src
    assert "if CLIP_INDEX + 1 < len(CLIPS):\n            comfy_free(PORT)" not in src
    assert "prompt_now = lock_spoken_japanese(GRAPH_PROMPT)" in src
    assert 'AUDIO_LOCK_MARK", "") != "[AUDIO-LOCK]"' in src
    assert "prompt=prompt_now" in src
    assert "前の LoRA を VRAM から下ろし" not in src
    assert "土台は載せたまま。この本の LoRA だけ繋ぎます" in src
    swap = src.find('elif CLIP_INDEX > 0 and planned.get("stack_changed"):')
    assert swap != -1
    swap_chunk = src[swap: src.find("else:", swap)]
    assert "comfy_free" not in swap_chunk
    assert "warmup_h3_engine" not in swap_chunk
    assert "よく使う部品を全部ディスクへ入れます" in src
    assert "土台と文章モデルは載せたまま。メモリ不足のときだけ解放" not in src
    assert 'urlopen(f"http://127.0.0.1:{PORT}/object_info", timeout=60)' not in src
    assert 'urlopen(f"http://127.0.0.1:{PORT}/object_info", timeout=3)' not in src


def test_format_job_fail_t2v_does_not_ask_for_jpg():
    t2v = format_job_fail("t2v", ["execution_error", {"node_type": "MiniMaxH3ImageToVideo", "exception_message": "length too large"}])
    assert "テキストから" in t2v
    assert "jpg" not in t2v.lower()
    assert "length too large" in t2v
    i2v = format_job_fail("i2v", "missing image")
    assert "jpg" in i2v
    assert format_job_fail("t2v", "timeout").startswith("テキストから")


def test_coachbate_falls_back_to_aio_when_missing(tmp_path):
    from h3_lora_studio import apply_stack_fallbacks, comfy_missing_loras, format_prompt_http_fail, missing_stack_files

    catalog = load_catalog(Path(__file__).resolve().parents[1] / "h3-lora-studio")
    lora_dir = tmp_path / "loras"
    lora_dir.mkdir()
    aio = lora_dir / "HMNSFW-AIO-V2.5.safetensors"
    aio.write_bytes(b"x" * 6_000_000)
    synth = lora_dir / "SynthPussy_H3_closeups_v1-step00008300.safetensors"
    synth.write_bytes(b"x" * 6_000_000)
    stack = [
        {"id": "anal-penetration-coachbate", "filename": "H3_anal_penetration_v1.safetensors", "strength_model": 0.85, "role": "act"},
        {"id": "synth-pussy-h3", "filename": "SynthPussy_H3_closeups_v1-step00008300.safetensors", "strength_model": 0.55, "role": "helper"},
    ]
    assert missing_stack_files(stack, lora_dir) == ["H3_anal_penetration_v1.safetensors"]
    out, replaced = apply_stack_fallbacks(stack, lora_dir, catalog)
    assert replaced is True
    assert [row["id"] for row in out] == ["hmnsfw-aio-v25", "synth-pussy-h3"]
    assert missing_stack_files(out, lora_dir) == []
    obj = {"LoraLoaderModelOnly": {"input": {"required": {"lora_name": [["larry.safetensors"]]}}}}
    assert comfy_missing_loras(out, obj) == ["HMNSFW-AIO-V2.5.safetensors", "SynthPussy_H3_closeups_v1-step00008300.safetensors"]
    msg = format_prompt_http_fail("lora_name 'H3_anal_penetration_v1.safetensors' not in list", stack)
    assert "②からやり直すか" not in msg
    assert "H3_anal_penetration_v1.safetensors" in msg or "HMNSFW" in msg
    assert "エンジン" in msg
    cowgirl_missing = [
        {"id": "cowgirl-position-h3", "filename": "Minimaxh3-cowgirl_position-Ref2V-512_000000550.safetensors", "strength_model": 0.8, "role": "act"},
        {"id": "penis-lora-h3", "filename": "Penis_Lora_H3.safetensors", "strength_model": 0.7, "role": "helper"},
        {"id": "synth-pussy-h3", "filename": "SynthPussy_H3_closeups_v1-step00008300.safetensors", "strength_model": 0.55, "role": "helper"},
    ]
    penis = lora_dir / "Penis_Lora_H3.safetensors"
    penis.write_bytes(b"x" * 6_000_000)
    out2, replaced2 = apply_stack_fallbacks(cowgirl_missing, lora_dir, catalog)
    assert replaced2 is True
    assert [row["id"] for row in out2] == ["hmnsfw-aio-v25", "penis-lora-h3", "synth-pussy-h3"]
    g = build_t2v_graph(
        prompt=DEFAULT_T2V_PROMPT,
        unet="minimax_h3_fl2va_pruned_int8_convrot.safetensors",
        lora_name=None,
        lora_strength=0.0,
        width=CANVAS_9_16[0],
        height=CANVAS_9_16[1],
        duration_s=5,
        seed=1,
        steps=16,
        filename_prefix="video/h3_lora_studio",
    )
    inject_lora_stack(g, out, sampler={"sampler_name": "res_multistep", "scheduler": "beta", "steps": 16})
    names = [n["inputs"]["lora_name"] for n in g.values() if n.get("class_type") == "LoraLoaderModelOnly"]
    assert names == ["HMNSFW-AIO-V2.5.safetensors", "SynthPussy_H3_closeups_v1-step00008300.safetensors"]
    assert all("turbo" not in n.lower() and "larry" not in n.lower() for n in names)
    assert assert_t2v_graph(g) == []


def test_friendly_select_error_for_child_and_picture1():
    assert "空欄" in (friendly_select_error(SystemExit("forbidden subject in prompt: ['child']")) or "")
    assert "21" in (friendly_select_error(SystemExit("forbidden subject in prompt: ['15 years old']")) or "")
    assert "写真用" in (friendly_select_error(SystemExit("t2v prompt must not use Picture 1 / first_frame")) or "")
    assert friendly_select_error(SystemExit("CoachBate anal penetration stays turbo off")) is None
    assert "②" in (friendly_select_error(SystemExit("stack_plan.helper needs an id")) or "")


def test_clamp_studio_duration_is_four_to_fifteen():
    assert clamp_studio_duration(10) == 10.0
    assert clamp_studio_duration(5) == 5.0
    assert clamp_studio_duration(4) == 4.0
    assert clamp_studio_duration(3) == 4.0
    assert clamp_studio_duration(15) == 15.0
    assert clamp_studio_duration(16) == 15.0
    assert clamp_studio_duration(10.4) == 10.0
    assert clamp_studio_duration("8") == 8.0
    assert clamp_studio_duration("nope") == 10.0
    assert clamp_studio_duration(12, chain=False) == 12.0
    assert clamp_studio_duration(10, chain=True) == 16.0
    assert clamp_studio_duration(16, chain=True) == 16.0
    assert clamp_studio_duration(60, chain=True) == 60.0
    assert clamp_studio_duration(61, chain=True) == 61.0
    assert clamp_studio_duration(70, chain=True) == 70.0
    assert clamp_studio_duration(90, chain=True) == 90.0
    assert clamp_studio_duration(91, chain=True) == 91.0
    assert clamp_studio_duration(120, chain=True) == 120.0
    assert clamp_studio_duration(121, chain=True) == 120.0
    assert clamp_studio_duration("nope", chain=True) == 16.0
    assert situation_ids("general_sex") == ["hmnsfw-aio-v25", "larry-v4"]
    assert situation_ids("riding") == ["cowgirl-position-h3", "penis-lora-h3", "synth-pussy-h3"]
    assert situation_ids("doggy") == ["doggy-h3", "penis-lora-h3", "synth-pussy-h3"]
    assert situation_ids("missionary_pov") == ["missionary-pov-h3", "penis-lora-h3", "larry-v4"]
    assert situation_ids("after_ejaculation") == ["hmcumshot-v2", "penis-lora-h3", "larry-v4"]
    assert situation_ids("facial") == ["facial-cumshot-h3", "penis-lora-h3", "larry-v4"]
    assert situation_ids("creampie") == ["final-thrust-h3", "penis-lora-h3", "synth-pussy-h3"]
    assert situation_ids("oral_creampie") == ["cumouf-h3", "penis-lora-h3", "synth-pussy-h3", "larry-v4"]
    assert situation_ids("fingering") == ["fingering-h3", "synth-pussy-h3", "larry-v4"]
    assert situation_ids("anal_fingering") == ["thumbinbutt-h3", "synth-pussy-h3", "larry-v4"]
    assert situation_ids("masturbation") == ["hmmasturbation-h3", "synth-pussy-h3", "larry-v4"]
    assert situation_ids("footjob") == ["footjob-h3", "penis-lora-h3", "larry-v4"]
    assert situation_ids("remote_orgasm") == ["remote-orgasm-h3", "synth-pussy-h3", "larry-v4"]
    assert situation_ids("preview") == ["hmnsfw-aio-v25", "minimax-h3-turbo-fl2v-4step"]
    assert situation_ids("futa_sex") == ["hmnsfw-aio-v25", "penis-lora-h3", "synth-pussy-h3"]
    assert situation_ids("futa_blowjob") == ["blowjob-h3", "penis-lora-h3", "synth-pussy-h3", "larry-v4"]
    assert situation_ids("futa_anal") == ["thumbinbutt-h3", "penis-lora-h3", "synth-pussy-h3"]
    assert situation_ids("anal_penetration") == ["thumbinbutt-h3", "penis-lora-h3", "synth-pussy-h3"]
    assert situation_ids("oral") == ["blowjob-h3", "penis-lora-h3", "synth-pussy-h3", "larry-v4"]


def test_facial_download_job_uses_hf_and_clean_filename(tmp_path):
    catalog = load_catalog(Path(__file__).resolve().parents[1] / "h3-lora-studio")
    jobs = download_jobs_for(["facial-cumshot-h3"], tmp_path, catalog=catalog)
    assert len(jobs) == 1
    url, dest, row = jobs[0]
    assert "EllaPriest45/MinimaxH3_Actions" in url
    assert dest.name == "H3_facial_cumshot_cmst.safetensors"
    assert row["id"] == "facial-cumshot-h3"
    encoded = quote_http_url(url)
    assert " " not in encoded.split("?")[0]
    assert "cmst.safetensors" in encoded


def test_thumbinbutt_download_job_uses_civitai_file_id_and_clean_filename(tmp_path):
    catalog = load_catalog(Path(__file__).resolve().parents[1] / "h3-lora-studio")
    jobs = download_jobs_for(["thumbinbutt-h3"], tmp_path, catalog=catalog)
    assert len(jobs) == 1
    url, dest, row = jobs[0]
    assert "fileId=3168734" in url
    assert "3284492" in url
    assert dest.name == "H3_ThumbInButt.safetensors"
    assert " " not in dest.name
    assert row["id"] == "thumbinbutt-h3"
    assert row["trigger"] == "thum1n8utt"


def test_final_thrust_download_job_uses_civitai_file_id_and_clean_filename(tmp_path):
    catalog = load_catalog(Path(__file__).resolve().parents[1] / "h3-lora-studio")
    jobs = download_jobs_for(["final-thrust-h3"], tmp_path, catalog=catalog)
    assert len(jobs) == 1
    url, dest, row = jobs[0]
    assert "fileId=3157295" in url
    assert "3269564" in url
    assert dest.name == "H3_FinalThrust.safetensors"
    assert dest.name != "V1.safetensors"
    assert " " not in dest.name
    assert row["id"] == "final-thrust-h3"
    assert (row.get("trigger") or "") == ""


def test_cumouf_download_job_uses_civitai_file_id_and_half_strength(tmp_path):
    catalog = load_catalog(Path(__file__).resolve().parents[1] / "h3-lora-studio")
    jobs = download_jobs_for(["cumouf-h3"], tmp_path, catalog=catalog)
    assert len(jobs) == 1
    url, dest, row = jobs[0]
    assert "fileId=3105419" in url
    assert "3223411" in url
    assert dest.name == "CUMOUF_oral_creampie_H3_v1.safetensors"
    assert row["id"] == "cumouf-h3"
    assert row["trigger"] == "CUMOUF"
    assert row["default_strength"] == 0.5


def test_studio_clip_plan_chain_stays_under_sixteen():
    assert studio_clip_plan(15) == [15.0]
    assert studio_clip_plan(16, chain=True) == [10.0, 6.0]
    assert studio_clip_plan(25, chain=True) == [10.0, 15.0]
    assert studio_clip_plan(26, chain=True) == [10.0, 10.0, 6.0]
    assert studio_clip_plan(20, chain=True) == [10.0] * 2
    assert studio_clip_plan(30, chain=True) == [10.0] * 3
    assert studio_clip_plan(40, chain=True) == [10.0] * 4
    assert studio_clip_plan(50, chain=True) == [10.0] * 5
    assert studio_clip_plan(60, chain=True) == [10.0] * 6
    assert studio_clip_plan(70, chain=True) == [10.0] * 7
    assert studio_clip_plan(80, chain=True) == [10.0] * 8
    assert studio_clip_plan(90, chain=True) == [10.0] * 9
    assert studio_clip_plan(100, chain=True) == [10.0] * 10
    assert studio_clip_plan(110, chain=True) == [10.0] * 11
    assert studio_clip_plan(120, chain=True) == [10.0] * 12
    assert all(4 <= c <= 15 for c in studio_clip_plan(120, chain=True))
    total, clips, chain = resolve_studio_length(30, "つなぐ（16〜60秒）")
    assert chain is True
    assert total == 30.0
    assert clips == [10.0, 10.0, 10.0]
    total, clips, chain = resolve_studio_length(45, "つなぐ（秒数欄・16〜120）")
    assert chain is True
    assert total == 45.0
    assert clips == [10.0, 10.0, 10.0, 15.0]
    total, clips, chain = resolve_studio_length(45, "つなぐ（秒数欄・16〜90）")
    assert chain is True
    assert total == 45.0
    for label, n in (
        ("つなぐ 20秒", 20),
        ("つなぐ 30秒", 30),
        ("つなぐ 40秒", 40),
        ("つなぐ 50秒", 50),
        ("つなぐ 60秒", 60),
        ("つなぐ 70秒", 70),
        ("つなぐ 80秒", 80),
        ("つなぐ 90秒", 90),
        ("つなぐ 100秒", 100),
        ("つなぐ 110秒", 110),
        ("つなぐ 120秒", 120),
        ("つなぐ 2分", 120),
    ):
        total, clips, chain = resolve_studio_length(10, label)
        assert chain is True
        assert total == float(n)
        assert clips == [10.0] * (n // 10)
        assert resolve_length_mode(label) is True
    total, clips, chain = resolve_studio_length(30, "1本（最大15秒）")
    assert chain is False
    assert total == 15.0
    assert clips == [15.0]
    assert resolve_length_mode("つなぐ") is True
    assert resolve_length_mode("1本（最大15秒）") is False


def test_continue_chain_prompt_keeps_picture1_and_does_not_restart():
    base = (
        "For the target video, at 0.00 seconds into the target video, "
        "<Picture 1> (from [Shot 1]) is fully referenced.\nConsenting adults over 21."
    )
    out = continue_chain_prompt(base)
    assert "Continue from this exact last frame" in out
    assert "<Picture 1>" in out
    assert "Do not restart" in out
    again = continue_chain_prompt(out)
    assert again.count("Continue from this exact last frame") == 1
    wrapped = continue_chain_prompt("keep walking in the same room")
    assert "Picture 1" in wrapped
    assert "Continue from this exact last frame" in wrapped


def test_next_chain_prompt_uses_extras_or_continues_prev():
    first = "Clip one seated sex. feminine_lock: Every visible person is an adult woman, clearly over 21."
    extras = ["", "Immediate deep tongue kiss. Keep Aya seated.", "", "Keep thrusting. Joining point visible."]
    clip0 = next_chain_prompt(0, first_prompt=first, prev_prompt=first, extras=extras)
    assert clip0 == first
    clip1 = next_chain_prompt(1, first_prompt=first, prev_prompt=first, extras=extras)
    assert "Continue from this exact last frame" in clip1
    assert "Picture 1" in clip1
    assert "seated sex" in clip1
    clip2 = next_chain_prompt(2, first_prompt=first, prev_prompt=clip1, extras=extras)
    assert "deep tongue kiss" in clip2
    assert "seated sex" not in clip2
    assert "feminine_lock:" in clip2.lower()
    clip3 = next_chain_prompt(3, first_prompt=first, prev_prompt=clip2, extras=extras)
    assert "deep tongue kiss" in clip3
    clip4 = next_chain_prompt(4, first_prompt=first, prev_prompt=clip3, extras=extras)
    assert "Keep thrusting" in clip4
    empty = next_chain_prompt(1, first_prompt=first, prev_prompt=first, extras=["", "", "", "", ""])
    assert "seated sex" in empty
    long_extras = [""] * 8
    long_extras[7] = "Clip nine keeps the same pose."
    clip8 = next_chain_prompt(8, first_prompt=first, prev_prompt=first, extras=long_extras)
    assert "Clip nine keeps the same pose" in clip8
    clip7 = next_chain_prompt(7, first_prompt=first, prev_prompt=first, extras=long_extras)
    assert "seated sex" in clip7
    long12 = [""] * 11
    long12[10] = "Clip twelve walks to the fridge."
    clip11 = next_chain_prompt(11, first_prompt=first, prev_prompt=first, extras=long12)
    assert "Clip twelve walks to the fridge" in clip11
    structured = next_chain_prompt(
        1,
        first_prompt=first,
        prev_prompt=first,
        extras=["subject_definitions:\nAya\n\nintegrated_multimodal_description:\nKiss only. Aya stays seated."],
    )
    assert structured.count("integrated_multimodal_description:") == 1
    assert "Kiss only" in structured
    assert "Picture 1" in structured
    dirty = next_chain_prompt(
        1,
        first_prompt=first,
        prev_prompt=first,
        extras=["New 10-second take. Hard cut. Do not copy the previous clip.\nImmediate deep tongue kiss."],
    )
    assert "New 10-second take" not in dirty
    assert "Hard cut." not in dirty
    assert "Do not copy the previous clip" not in dirty
    assert "deep tongue kiss" in dirty
    assert "without a cut" in dirty


def test_strip_and_rewrite_chain_opening_for_join():
    dirty = (
        "New 10-second take. Hard cut. Do not copy the previous clip.\n"
        "Clip 2 of 12.\n"
        "A woman sits on the sofa and talks."
    )
    cleaned = strip_chain_restart_language(dirty)
    assert "New 10-second take" not in cleaned
    assert "Hard cut." not in cleaned
    assert "Do not copy the previous clip" not in cleaned
    assert "Clip 2 of 12" not in cleaned
    assert "sits on the sofa" in cleaned
    raw = "PENISLORA, DY\nA woman sits on the sofa and talks."
    out = rewrite_chain_opening_prompt(raw)
    assert out.startswith("PENISLORA, DY")
    assert "opening of one continuous long take" in out
    assert "End this clip mid-motion" in out
    assert "sits on the sofa" in out
    again = rewrite_chain_opening_prompt(out)
    assert again.count("opening of one continuous long take") == 1
    cont = continue_chain_prompt(out)
    assert "Continue from this exact last frame" in cont
    assert "Do not restart" in cont
    assert "Picture 1" in cont
    assert "no teleport" in cont.lower() or "No teleport" in cont


def test_concat_studio_clips_prefers_stream_copy(tmp_path):
    import subprocess

    ff = "ffmpeg"

    def tiny(path, color):
        subprocess.run(
            [
                ff, "-y", "-f", "lavfi", "-i", f"color=c={color}:s=64x64:d=0.5:r=24",
                "-c:v", "libx264", "-pix_fmt", "yuv420p", str(path),
            ],
            check=True,
            capture_output=True,
        )

    a = tmp_path / "a.mp4"
    b = tmp_path / "b.mp4"
    tiny(a, "red")
    tiny(b, "blue")
    dest = tmp_path / "joined.mp4"
    out = concat_studio_clips([a, b], dest)
    assert out == dest
    assert dest.is_file() and dest.stat().st_size > 1000
    frame = tmp_path / "last.png"
    extract_last_frame(b, frame)
    assert frame.is_file() and frame.stat().st_size >= 100
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(dest)],
        capture_output=True,
        text=True,
    )
    dur = float((probe.stdout or "0").strip() or "0")
    assert 0.85 <= dur <= 1.25


def test_notebook_clamps_duration_and_uses_it_in_graphs():
    writer = Path(__file__).resolve().parent / "_write_lora_studio_nb.py"
    nb_path = Path(__file__).resolve().parents[1] / "minimax_h3_lora_studio.ipynb"
    src = writer.read_text(encoding="utf-8")
    blob = nb_path.read_text(encoding="utf-8")
    nb = json.loads(nb_path.read_text(encoding="utf-8"))
    for i, cell in enumerate(nb["cells"]):
        if cell.get("cell_type") != "code":
            continue
        body = "".join(cell.get("source") or [])
        compile(body, f"notebook-cell-{i}", "exec")
    assert "resolve_studio_length" in src
    assert "DURATION, CLIPS, CHAIN = resolve_studio_length(秒数, 長さの作り方)" in src
    assert "duration_s=CLIP_DURATION" in src
    assert "duration_s=float(秒数)" not in src
    assert "duration_s=5.0" not in src
    assert "DURATION = float(秒数)" not in src
    assert "長さの作り方" in src
    assert "つなぐ 20秒" in src
    assert "つなぐ 90秒" in src
    assert "つなぐ 120秒" in src
    assert "つなぐ 2分" in src
    assert "つなぐ（秒数欄・16〜120）" in src
    assert "concat_studio_clips" in src
    assert "continue_chain_prompt" in src
    assert "next_chain_prompt" in src
    assert "rewrite_chain_opening_prompt" in src
    assert "つなぐモード" in src
    assert "つなぎ2" in src
    assert "つなぎ9" in src
    assert "つなぎ12" in src
    assert "CHAIN_EXTRAS" in src
    assert "CHAIN_MAX_S" in src
    assert "homage = bool(VANILLA and not CUSTOM_PROMPT and CLIP_INDEX == 0)" in src
    assert "AIO 0.8 + Larry 0.5 / 12step" in src
    assert "LightX2V 0.5 / 12 step" not in src
    assert "DURATION, CLIPS, CHAIN = resolve_studio_length" in blob
    assert "duration_s=CLIP_DURATION" in blob
    assert "duration_s=float(秒数)" not in blob
    assert "つなぐ 20秒" in blob
    assert "つなぐ 90秒" in blob
    assert "つなぐ 120秒" in blob
    assert "つなぐ（秒数欄・16〜120）" in blob
    assert "つなぎ9" in blob
    assert "つなぎ12" in blob
    assert "continue_chain_prompt" in blob
    assert "next_chain_prompt" in blob
    assert "rewrite_chain_opening_prompt" in blob
    assert "つなぐモード" in blob
    assert "つなぎ2" in blob
    assert "AIO 0.8 + Larry 0.5 / 12step" in blob
    helper = Path(__file__).resolve().parent / "h3_lora_studio.py"
    assert "つなぐ（16〜60秒）" in helper.read_text(encoding="utf-8")
    assert "CHAIN_MAX_S = 120" in helper.read_text(encoding="utf-8")


class _FakeHttp:
    def __init__(self, payload, status=200):
        self._payload = json.dumps(payload).encode()
        self.status = status

    def read(self):
        return self._payload

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def test_comfy_alive_uses_system_stats_not_object_info(monkeypatch):
    import urllib.request
    from h3_lora_studio import comfy_alive

    hits = []

    def fake_urlopen(url, timeout=None):
        hits.append(str(url))
        if str(url).endswith("/system_stats"):
            return _FakeHttp({"system": {}})
        raise AssertionError(f"unexpected url {url}")

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    assert comfy_alive(8188) is True
    assert hits == ["http://127.0.0.1:8188/system_stats"]
    assert all("/object_info" not in u for u in hits)


def test_fetch_comfy_object_info_uses_per_node_and_skips_full_dump(monkeypatch):
    import urllib.request
    from h3_lora_studio import fetch_comfy_object_info

    hits = []

    def fake_urlopen(url, timeout=None):
        u = str(url)
        hits.append(u)
        if u.endswith("/system_stats"):
            return _FakeHttp({"system": {}})
        if u.endswith("/object_info/MiniMaxH3ImageToVideo"):
            return _FakeHttp({"MiniMaxH3ImageToVideo": {"input": {}}})
        if u.endswith("/object_info/LoraLoaderModelOnly"):
            return _FakeHttp({"LoraLoaderModelOnly": {"input": {"required": {"lora_name": [["larry.safetensors"]]}}}})
        if u.endswith("/object_info/MiniMaxH3TextToVideo"):
            return _FakeHttp({"MiniMaxH3TextToVideo": {"input": {}}})
        if u.endswith("/object_info/VAEDecodeAudio"):
            return _FakeHttp({"VAEDecodeAudio": {"input": {}}})
        if u.rstrip("/").endswith("/object_info"):
            raise AssertionError("full /object_info dump should not be used")
        return _FakeHttp({})

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    obj = fetch_comfy_object_info(8188)
    assert "MiniMaxH3ImageToVideo" in obj
    assert "LoraLoaderModelOnly" in obj
    assert not any(u.rstrip("/").endswith("/object_info") for u in hits)


def test_fetch_comfy_object_info_times_out_with_japanese_exit(monkeypatch):
    import urllib.request
    from h3_lora_studio import fetch_comfy_object_info

    def fake_urlopen(url, timeout=None):
        u = str(url)
        if u.endswith("/system_stats") or u.endswith("/queue"):
            return _FakeHttp({"system": {}})
        raise TimeoutError("timed out")

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr("h3_lora_studio.time.sleep", lambda *_a, **_k: None)
    try:
        fetch_comfy_object_info(8188)
    except SystemExit as exc:
        assert "部品表" in str(exc)
    else:
        raise AssertionError("expected SystemExit")


def test_fetch_comfy_object_info_says_engine_down(monkeypatch):
    from h3_lora_studio import fetch_comfy_object_info

    monkeypatch.setattr("h3_lora_studio.comfy_alive", lambda *_a, **_k: False)
    monkeypatch.setattr("h3_lora_studio.wait_comfy_ready", lambda *_a, **_k: False)
    try:
        fetch_comfy_object_info(8188)
    except SystemExit as exc:
        assert "応答していません" in str(exc)
    else:
        raise AssertionError("expected SystemExit")


def test_comfy_free_posts_unload(monkeypatch):
    import urllib.request
    from h3_lora_studio import comfy_free

    hits = []

    def fake_urlopen(req, timeout=None):
        hits.append(getattr(req, "full_url", str(req)))
        return _FakeHttp({"ok": True})

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr("h3_lora_studio.time.sleep", lambda *_a, **_k: None)
    comfy_free(8188)
    assert hits
    assert hits[0].endswith("/free")


def test_apply_drive_cache_env_points_at_drive(tmp_path, monkeypatch):
    from h3_lora_studio import DRIVE_CACHE_SUBS, apply_drive_cache_env

    monkeypatch.delenv("HF_HOME", raising=False)
    monkeypatch.delenv("PIP_CACHE_DIR", raising=False)
    applied = apply_drive_cache_env(tmp_path)
    assert applied["CUDA_MODULE_LOADING"] == "EAGER"
    for key, rel in DRIVE_CACHE_SUBS.items():
        dest = tmp_path / rel
        assert dest.is_dir(), rel
        assert os.environ[key] == str(dest)
    assert os.environ["CUDA_MODULE_LOADING"] == "EAGER"


def test_stage_models_to_local_copies_once_and_breaks_symlink(tmp_path):
    from h3_lora_studio import (
        model_dir_is_drive_link,
        prepare_local_model_roots,
        stage_models_to_local,
        stage_weight_file,
    )

    drive = tmp_path / "drive" / "models"
    comfy = tmp_path / "ComfyUI"
    (drive / "text_encoders").mkdir(parents=True)
    payload = b"x" * (2 * 1024 * 1024)
    src = drive / "text_encoders" / "clip.safetensors"
    src.write_bytes(payload)
    models = comfy / "models"
    models.mkdir(parents=True)
    (models / "text_encoders").symlink_to(drive / "text_encoders")
    assert model_dir_is_drive_link(comfy)
    assert prepare_local_model_roots(comfy) is True
    assert not (comfy / "models" / "text_encoders").is_symlink()
    stats = stage_models_to_local(drive, comfy / "models", min_free_bytes=0)
    dest = comfy / "models" / "text_encoders" / "clip.safetensors"
    assert dest.is_file() and not dest.is_symlink()
    assert dest.stat().st_size == len(payload)
    assert src.name in stats["copied"]
    again = stage_models_to_local(drive, comfy / "models", min_free_bytes=0)
    assert src.name in again["skipped"]
    assert stage_weight_file(src, dest) == "skipped"


def test_stage_models_to_local_falls_back_when_disk_is_tight(tmp_path, monkeypatch):
    from h3_lora_studio import stage_models_to_local

    drive = tmp_path / "drive" / "models"
    local = tmp_path / "local" / "models"
    (drive / "vae").mkdir(parents=True)
    (drive / "vae" / "vae.safetensors").write_bytes(b"y" * (3 * 1024 * 1024))
    monkeypatch.setattr(
        "h3_lora_studio.shutil.disk_usage",
        lambda _p: type("U", (), {"free": 100})(),
    )
    stats = stage_models_to_local(drive, local, min_free_bytes=2 * 1024 ** 3)
    assert stats["drive_direct"] is True
    assert not (local / "vae" / "vae.safetensors").exists()


def test_build_studio_warmup_graph_is_one_step_tiny():
    from h3_lora_studio import build_studio_warmup_graph
    from h3_t2v import CANVAS_9_16_MIN

    g = build_studio_warmup_graph("minimax_h3_fl2va_pruned_int8_convrot.safetensors")
    assert g["20"]["class_type"] == "MiniMaxH3ImageToVideo"
    assert "Picture 1" not in g["20"]["inputs"]["prompt"]
    assert g["20"]["inputs"]["width"] == CANVAS_9_16_MIN[0]
    assert g["20"]["inputs"]["height"] == CANVAS_9_16_MIN[1]
    assert g["23"]["inputs"]["steps"] == 1
    assert g["22"]["inputs"]["sampler_name"] == "euler"
    assert "2" not in g


def test_warmup_h3_engine_skips_when_stamped(tmp_path, monkeypatch):
    from h3_lora_studio import warmup_h3_engine, warmup_stamp_path

    stamp = warmup_stamp_path(tmp_path)
    stamp.write_text("ok")
    called = []
    monkeypatch.setattr("h3_lora_studio._post_comfy_prompt", lambda *_a, **_k: called.append(1) or (None, "nope"))
    assert warmup_h3_engine(tmp_path, 8188, "unet.safetensors") is True
    assert called == []


def test_restart_studio_comfy_clears_warmup_stamp(tmp_path, monkeypatch):
    from h3_lora_studio import restart_studio_comfy, warmup_stamp_path

    stamp = warmup_stamp_path(tmp_path)
    stamp.write_text("ok")

    class _P:
        def __init__(self, *a, **k):
            pass

    monkeypatch.setattr("h3_lora_studio.subprocess.run", lambda *_a, **_k: None)
    monkeypatch.setattr("h3_lora_studio.subprocess.Popen", _P)
    monkeypatch.setattr("h3_lora_studio.time.sleep", lambda *_a, **_k: None)
    monkeypatch.setattr("h3_lora_studio.wait_comfy_ready", lambda *_a, **_k: True)
    restart_studio_comfy(tmp_path, port=8188)
    assert not stamp.exists()


def test_homecoming_story_twelve_clips_switch_loras(tmp_path):
    from h3_lora_studio import (
        is_story,
        load_story,
        prepare_story_clip,
        situation_ids,
        resolve_situation,
        studio_sys_path,
    )

    studio_sys_path()
    from select_loras import forbidden_hits, select_loras

    assert resolve_situation("帰宅120秒（専用）") == "homecoming-90s"
    assert resolve_situation("帰宅90秒（専用）") == "homecoming-90s"
    assert is_story("帰宅120秒（専用）")
    assert is_story("帰宅90秒（専用）")
    assert "cumouf-h3" in situation_ids("homecoming-90s")
    story = load_story("homecoming-90s")
    assert story["duration_s"] == 120
    assert len(story["clips"]) == 12
    assert story["canvas"] == {"width": 576, "height": 1024, "aspect": "9:16"}
    assert story.get("seamless") is False
    want = [
        "futa_visible",
        "oral",
        "oral",
        "futa_visible",
        "futa_visible",
        "cunnilingus_futa",
        "futa_visible",
        "futa_masturbation",
        "oral",
        "oral_creampie",
        "futa_visible",
        "futa_visible",
    ]
    assert [c["situation"] for c in story["clips"]] == want
    assert sum(1 for c in story["clips"] if c["situation"] == "cunnilingus_futa") == 1
    assert "Close-up" in story["clips"][5]["prompt"]
    assert "mini breasts and full bodies" not in story["clips"][5]["prompt"]
    assert "Do not pull back to full bodies" in story["clips"][5]["prompt"]
    assert "Not a crotch close-up" in story["clips"][4]["prompt"]
    assert "LIP SYNC" in story["clips"][10]["prompt"]
    assert "LIP SYNC" not in story["clips"][0]["prompt"]
    prev = None
    prev_stack = None
    for i, clip in enumerate(story["clips"]):
        hits = forbidden_hits(clip["prompt"])
        assert hits == [], hits
        assert "21" in clip["prompt"] or "22" in clip["prompt"] or "24" in clip["prompt"] or "39" in clip["prompt"]
        assert "15," not in clip["prompt"]
        planned = prepare_story_clip(
            story,
            i,
            last_frame="h3_chain_0.png",
            stills_dir=tmp_path,
            prev_situation=prev,
            prev_stack=prev_stack,
        )
        if i > 0 and want[i] != want[i - 1]:
            assert planned["stack_changed"]
        prev = planned["situation"]
        prev_stack = planned["stack"]
        assert planned["mode"] == "t2v"
        assert planned["first_kind"] == "t2v"
        assert "Picture 1" not in planned["prompt"]
        assert planned["missing_still"]
        ids = [row["id"] for row in planned["stack"]]
        if planned["situation"] == "oral":
            assert ids[0] == "blowjob-h3"
            assert "cumouf-h3" not in ids
            assert "synth-pussy-h3" in ids
            assert "penis-lora-h3" in ids
            assert "futa-h3-v51" not in ids
        if planned["situation"] == "oral_creampie":
            assert ids[0] == "cumouf-h3"
            assert "blowjob-h3" not in ids
        if planned["situation"] == "futa_visible":
            _check_visible_plan(planned, clip["prompt"])
        if planned["situation"] == "cunnilingus_futa":
            assert "lesbian-cunnilingus-h3" in ids
            assert "blowjob-h3" not in ids
            assert "penis-lora-h3" in ids
        if planned["situation"] == "futa_masturbation":
            assert ids[0] == "hmmasturbation-h3"
            assert "penis-lora-h3" in ids
    vis = select_loras(profile_name="futa_visible", mode="t2v", prompt_arg="（シーン）")
    assert vis["turbo"] is True
    assert vis["sampler"]["steps"] == 8
    assert [r["id"] for r in vis["stack"]] == ["penis-lora-h3", "larry-v4", "cinema-dy"]
    vis_speech = select_loras(profile_name="futa_visible", mode="t2v", prompt_arg="（シーン）", turbo_override=False)
    assert vis_speech["turbo"] is False
    assert vis_speech["sampler"]["steps"] == 12
    assert vis_speech["sampler"]["sampler_name"] == "res_multistep"
    assert [r["id"] for r in vis_speech["stack"]] == ["penis-lora-h3", "cinema-dy"]
    mast = select_loras(profile_name="futa_masturbation", mode="t2v", prompt_arg="（シーン）")
    assert [r["id"] for r in mast["stack"]] == ["hmmasturbation-h3", "penis-lora-h3", "synth-pussy-h3", "larry-v4"]
    cun = select_loras(profile_name="cunnilingus_futa", mode="t2v", prompt_arg="（シーン）")
    assert [r["id"] for r in cun["stack"]] == [
        "lesbian-cunnilingus-h3",
        "synth-pussy-h3",
        "penis-lora-h3",
        "larry-v4",
    ]
    (tmp_path / "01-genkan.jpg").write_bytes(b"fake-jpg")
    with_still = prepare_story_clip(story, 0, stills_dir=tmp_path, last_frame="ignored.png")
    assert with_still["mode"] == "i2v"
    assert with_still["first_kind"] == "still"
    assert "Picture 1" in with_still["prompt"]


def test_dishes_story_twelve_clips_sink_locked(tmp_path):
    from h3_lora_studio import (
        is_story,
        load_story,
        prepare_story_clip,
        situation_ids,
        resolve_situation,
        studio_sys_path,
    )

    studio_sys_path()
    from select_loras import forbidden_hits

    assert resolve_situation("洗い物120秒（専用）") == "dishes-90s"
    assert resolve_situation("洗い物90秒（専用）") == "dishes-90s"
    assert is_story("洗い物120秒（専用）")
    ids = situation_ids("dishes-90s")
    assert ids == [
        "penis-lora-h3",
        "cinema-dy",
        "blowjob-h3",
        "larry-v4",
        "cumouf-h3",
        "synth-pussy-h3",
    ]
    assert "lesbian-cunnilingus-h3" not in ids
    story = load_story("dishes-90s")
    assert story["duration_s"] == 120
    assert story["clip_s"] == 10
    assert len(story["clips"]) == 12
    assert story["canvas"] == {"width": 576, "height": 1024, "aspect": "9:16"}
    assert story.get("seamless") is False
    assert story.get("stills_dir") == "dishes-90s"
    want = [
        "futa_visible",
        "futa_visible",
        "futa_visible",
        "futa_visible",
        "futa_visible",
        "futa_visible",
        "oral",
        "oral",
        "oral",
        "oral",
        "oral_creampie",
        "oral_creampie",
    ]
    assert [c["situation"] for c in story["clips"]] == want
    assert "hairless pussy readable" not in "".join(c["prompt"] for c in story["clips"])
    assert all(
        "CAMERA:" in c["prompt"]
        for c in story["clips"]
        if c["situation"] in {"oral", "oral_creampie"}
    )
    prev = None
    prev_stack = None
    for i, clip in enumerate(story["clips"]):
        hits = forbidden_hits(clip["prompt"])
        assert hits == [], hits
        assert "15," not in clip["prompt"]
        assert "woman, 15" not in clip["prompt"].lower()
        assert "Sayaka never leaves the sink" in clip["prompt"]
        assert "Rei is the seated penis" in clip["prompt"]
        assert "Aya is the mouth on the floor" in clip["prompt"]
        if i >= 1:
            assert "Adult 22" in clip["prompt"]
            assert "mini breasts" in clip["prompt"].lower() or "Mini breasts" in clip["prompt"]
        planned = prepare_story_clip(
            story,
            i,
            last_frame="h3_chain_0.png",
            stills_dir=tmp_path,
            prev_situation=prev,
            prev_stack=prev_stack,
        )
        if i > 0 and want[i] != want[i - 1]:
            assert planned["stack_changed"]
        prev = planned["situation"]
        prev_stack = planned["stack"]
        assert planned["mode"] == "t2v"
        assert planned["first_kind"] == "t2v"
        assert "Picture 1" not in planned["prompt"]
        assert planned["missing_still"]
        stack_ids = [row["id"] for row in planned["stack"]]
        if planned["situation"] == "oral":
            assert stack_ids[0] == "blowjob-h3"
            assert "cumouf-h3" not in stack_ids
        if planned["situation"] == "oral_creampie":
            assert stack_ids[0] == "cumouf-h3"
            assert "blowjob-h3" not in stack_ids
        if planned["situation"] == "futa_visible":
            _check_visible_plan(planned, clip["prompt"])
    (tmp_path / "01-sink.jpg").write_bytes(b"fake-jpg")
    with_still = prepare_story_clip(story, 0, stills_dir=tmp_path, last_frame="ignored.png")
    assert with_still["mode"] == "i2v"
    assert with_still["first_kind"] == "still"
    assert "Picture 1" in with_still["prompt"]


def test_commute_story_twelve_clips_landscape(tmp_path):
    from h3_lora_studio import (
        is_story,
        load_story,
        prepare_story_clip,
        situation_ids,
        resolve_situation,
        story_canvas_wh,
        studio_sys_path,
    )

    studio_sys_path()
    from select_loras import forbidden_hits

    assert resolve_situation("登校120秒（専用）") == "commute-120s"
    assert resolve_situation("朝〜正門120秒（専用）") == "commute-120s"
    assert is_story("登校120秒（専用）")
    assert is_story("commute-120s")
    ids = situation_ids("commute-120s")
    assert ids == [
        "penis-lora-h3",
        "cinema-dy",
        "blowjob-h3",
        "larry-v4",
        "synth-pussy-h3",
    ]
    assert "cumouf-h3" not in ids
    story = load_story("commute-120s")
    assert story["duration_s"] == 120
    assert story["clip_s"] == 10
    assert story["min_age"] == 22
    assert len(story["clips"]) == 12
    assert story["canvas"] == {"width": 1024, "height": 576, "aspect": "16:9"}
    assert story_canvas_wh(story) == (1024, 576)
    assert story.get("seamless") is False
    assert story.get("stills_dir") == "commute-120s"
    want = [
        "futa_visible",
        "futa_visible",
        "futa_visible",
        "oral",
        "oral",
        "futa_visible",
        "futa_visible",
        "futa_visible",
        "futa_visible",
        "oral",
        "oral",
        "futa_visible",
    ]
    assert [c["situation"] for c in story["clips"]] == want
    assert [float(c["duration_s"]) for c in story["clips"]] == [10.0] * 12
    assert "LIP SYNC" in story["clips"][1]["prompt"]
    assert "LIP SYNC" in story["clips"][5]["prompt"]
    assert "LIP SYNC" in story["clips"][7]["prompt"]
    assert "LIP SYNC" not in story["clips"][0]["prompt"]
    assert "LIP SYNC" not in story["clips"][3]["prompt"]
    prev = None
    prev_stack = None
    for i, clip in enumerate(story["clips"]):
        hits = forbidden_hits(clip["prompt"])
        assert hits == [], hits
        assert "schoolgirl" not in clip["prompt"].lower()
        assert "15," not in clip["prompt"]
        assert "woman, 15" not in clip["prompt"].lower()
        assert "15-second take" not in clip["prompt"]
        assert "Adult 22" in clip["prompt"] or "woman, 22" in clip["prompt"]
        assert "Adult university" in clip["prompt"]
        assert "Not a high school" in clip["prompt"]
        assert "CAST LOCK" in clip["prompt"]
        assert "10-second take" in clip["prompt"]
        if i == 0 or i >= 6:
            assert "Sayaka = NOT IN FRAME" in clip["prompt"] or "NOT IN FRAME" in clip["prompt"]
        if i >= 6:
            assert "She stayed at home" in clip["prompt"] or "Home." in clip["prompt"] or "NOT IN THIS CLIP" in clip["prompt"]
        planned = prepare_story_clip(
            story,
            i,
            last_frame="h3_chain_0.png",
            stills_dir=tmp_path,
            prev_situation=prev,
            prev_stack=prev_stack,
        )
        if i > 0 and want[i] != want[i - 1]:
            assert planned["stack_changed"]
        prev = planned["situation"]
        prev_stack = planned["stack"]
        # Unplayed JSON (seamless False): a passed last_frame is ignored → T2V hard cut.
        assert planned["mode"] == "t2v"
        assert planned["first_kind"] == "t2v"
        assert planned["seamless"] is False
        assert "Picture 1" not in planned["prompt"]
        assert planned["missing_still"]
        assert planned["width"] == 1024
        assert planned["height"] == 576
        assert planned["duration_s"] == 10
        stack_ids = [row["id"] for row in planned["stack"]]
        if planned["situation"] == "oral":
            assert stack_ids[0] == "blowjob-h3"
            assert "cumouf-h3" not in stack_ids
        if planned["situation"] == "futa_visible":
            _check_visible_plan(planned, clip["prompt"])
    assert "No classroom" in story["clips"][-1]["prompt"]
    assert "No going home" in story["clips"][-1]["prompt"]
    (tmp_path / "01-hall.jpg").write_bytes(b"fake-jpg")
    with_still = prepare_story_clip(story, 0, stills_dir=tmp_path, last_frame="ignored.png")
    assert with_still["mode"] == "i2v"
    assert with_still["first_kind"] == "still"
    assert "Picture 1" in with_still["prompt"]
    assert with_still["width"] == 1024
    assert with_still["height"] == 576
    forced = prepare_story_clip(story, 0, stills_dir=tmp_path, force_t2v=True)
    assert forced["mode"] == "t2v"
    assert forced["first_kind"] == "t2v"
    assert forced["still_path"] is None
    assert "Picture 1" not in forced["prompt"]
    assert "opening of one continuous long take" not in forced["prompt"]
    assert "Continue from this exact last frame" not in forced["prompt"]


def test_lecture_story_ten_clips_campus_noon(tmp_path):
    from h3_lora_studio import (
        is_story,
        load_story,
        prepare_story_clip,
        situation_ids,
        resolve_situation,
        story_canvas_wh,
        studio_sys_path,
    )

    studio_sys_path()
    from select_loras import forbidden_hits

    assert resolve_situation("授業120秒（専用）") == "lecture-120s"
    assert resolve_situation("授業〜昼120秒（専用）") == "lecture-120s"
    assert is_story("授業120秒（専用）")
    assert is_story("lecture-120s")
    ids = situation_ids("lecture-120s")
    assert ids == [
        "penis-lora-h3",
        "cinema-dy",
        "blowjob-h3",
        "larry-v4",
        "hmmasturbation-h3",
        "lesbian-cunnilingus-h3",
        "synth-pussy-h3",
        "cumouf-h3",
    ]
    story = load_story("lecture-120s")
    assert story["duration_s"] == 100
    assert story["clip_s"] == 10
    assert story["min_age"] == 22
    assert len(story["clips"]) == 10
    assert story["canvas"] == {"width": 1024, "height": 576, "aspect": "16:9"}
    assert story_canvas_wh(story) == (1024, 576)
    assert story.get("seamless") is False
    assert story.get("stills_dir") == "lecture-120s"
    want = [
        "futa_visible",
        "futa_masturbation",
        "futa_visible",
        "futa_visible",
        "cunnilingus_futa",
        "oral",
        "oral_creampie",
        "oral",
        "futa_visible",
        "futa_visible",
    ]
    assert [c["situation"] for c in story["clips"]] == want
    assert [float(c["duration_s"]) for c in story["clips"]] == [10.0] * 10
    assert sum(1 for c in story["clips"] if c["situation"] == "cunnilingus_futa") == 1
    assert "Close-up" in story["clips"][4]["prompt"]
    assert "Do not pull back to full bodies" in story["clips"][4]["prompt"]
    assert "Not a crotch close-up" in story["clips"][3]["prompt"]
    assert "already stroking" in story["clips"][1]["prompt"].lower() or "already seated" in story["clips"][1]["prompt"]
    assert "LIP SYNC" in story["clips"][8]["prompt"]
    assert "LIP SYNC" not in story["clips"][0]["prompt"]
    prev = None
    prev_stack = None
    for i, clip in enumerate(story["clips"]):
        hits = forbidden_hits(clip["prompt"])
        assert hits == [], hits
        assert "schoolgirl" not in clip["prompt"].lower()
        assert "15," not in clip["prompt"]
        assert "woman, 15" not in clip["prompt"].lower()
        assert "15-second take" not in clip["prompt"]
        assert "Adult 22" in clip["prompt"] or "woman, 22" in clip["prompt"]
        assert "Adult university" in clip["prompt"]
        assert "Not a high school" in clip["prompt"]
        assert "CAST LOCK" in clip["prompt"]
        assert "10-second take" in clip["prompt"]
        assert "Sayaka = NOT IN THIS STORY" in clip["prompt"] or "NOT IN THIS STORY" in clip["prompt"]
        planned = prepare_story_clip(
            story,
            i,
            last_frame="h3_chain_0.png",
            stills_dir=tmp_path,
            prev_situation=prev,
            prev_stack=prev_stack,
        )
        if i > 0 and want[i] != want[i - 1]:
            assert planned["stack_changed"]
        prev = planned["situation"]
        prev_stack = planned["stack"]
        assert planned["width"] == 1024
        assert planned["height"] == 576
        assert planned["duration_s"] == 10
        stack_ids = [row["id"] for row in planned["stack"]]
        if planned["situation"] == "oral":
            assert stack_ids[0] == "blowjob-h3"
            assert "cumouf-h3" not in stack_ids
        if planned["situation"] == "oral_creampie":
            assert stack_ids[0] == "cumouf-h3"
            assert "blowjob-h3" not in stack_ids
        if planned["situation"] == "futa_visible":
            _check_visible_plan(planned, clip["prompt"])
        if planned["situation"] == "futa_masturbation":
            assert stack_ids == ["hmmasturbation-h3", "penis-lora-h3", "synth-pussy-h3", "larry-v4"]
        if planned["situation"] == "cunnilingus_futa":
            assert "lesbian-cunnilingus-h3" in stack_ids
            assert "blowjob-h3" not in stack_ids
            assert "penis-lora-h3" in stack_ids
    assert "No rooftop" in story["clips"][-1]["prompt"] or "No sex" in story["clips"][-1]["prompt"]
    assert "No going home" in story["clips"][-1]["prompt"]
    (tmp_path / "01-corridor.jpg").write_bytes(b"fake-jpg")
    with_still = prepare_story_clip(story, 0, stills_dir=tmp_path, last_frame="ignored.png")
    assert with_still["mode"] == "i2v"
    assert with_still["first_kind"] == "still"
    assert "Picture 1" in with_still["prompt"]


def test_rooftop_story_ten_clips_one_place_each(tmp_path):
    from h3_lora_studio import (
        is_story,
        load_story,
        prepare_story_clip,
        situation_ids,
        resolve_situation,
        story_canvas_wh,
        studio_sys_path,
    )

    studio_sys_path()
    from select_loras import forbidden_hits

    assert resolve_situation("屋上〜下校（専用）") == "rooftop-100s"
    assert resolve_situation("屋上100秒（専用）") == "rooftop-100s"
    assert is_story("屋上〜下校（専用）")
    ids = situation_ids("rooftop-100s")
    assert ids == [
        "penis-lora-h3",
        "cinema-dy",
        "larry-v4",
        "hmnsfw-aio-v25",
        "synth-pussy-h3",
    ]
    assert "blowjob-h3" not in ids
    story = load_story("rooftop-100s")
    assert story["duration_s"] == 100
    assert story["clip_s"] == 10
    assert story["min_age"] == 22
    assert len(story["clips"]) == 10
    assert story["canvas"] == {"width": 1024, "height": 576, "aspect": "16:9"}
    assert story_canvas_wh(story) == (1024, 576)
    assert story.get("seamless") is False
    assert story.get("stills_dir") == "rooftop-100s"
    want = [
        "futa_visible",
        "futa_visible",
        "futa_visible",
        "futa_visible",
        "futa_sex",
        "futa_sex",
        "futa_sex",
        "futa_visible",
        "futa_visible",
        "futa_visible",
    ]
    assert [c["situation"] for c in story["clips"]] == want
    assert [float(c["duration_s"]) for c in story["clips"]] == [10.0] * 10
    assert "LIP SYNC" in story["clips"][2]["prompt"]
    assert "LIP SYNC" in story["clips"][7]["prompt"]
    assert "LIP SYNC" not in story["clips"][0]["prompt"]
    assert "Already in" in story["clips"][4]["prompt"] or "ALREADY IN" in story["clips"][4]["prompt"]
    assert "horizontal close" in story["clips"][4]["prompt"].lower() or "joining point" in story["clips"][4]["prompt"].lower()
    assert "Madoka = NOT IN FRAME" in story["clips"][4]["prompt"]
    assert "Not a courtyard" in story["clips"][0]["prompt"]
    assert "One place" in story["clips"][8]["prompt"] or "the campus gate" in story["clips"][8]["prompt"]
    prev = None
    prev_stack = None
    for i, clip in enumerate(story["clips"]):
        hits = forbidden_hits(clip["prompt"])
        assert hits == [], hits
        assert "schoolgirl" not in clip["prompt"].lower()
        assert "15," not in clip["prompt"]
        assert "woman, 15" not in clip["prompt"].lower()
        assert "Adult 22" in clip["prompt"] or "woman, 22" in clip["prompt"]
        assert "Adult university" in clip["prompt"]
        assert "Not a high school" in clip["prompt"]
        assert "CAST LOCK" in clip["prompt"]
        assert "10-second take" in clip["prompt"]
        assert "NOT IN THIS STORY" in clip["prompt"]
        planned = prepare_story_clip(
            story,
            i,
            last_frame="h3_chain_0.png",
            stills_dir=tmp_path,
            prev_situation=prev,
            prev_stack=prev_stack,
        )
        if i > 0 and want[i] != want[i - 1]:
            assert planned["stack_changed"]
        prev = planned["situation"]
        prev_stack = planned["stack"]
        assert planned["width"] == 1024
        assert planned["height"] == 576
        assert planned["duration_s"] == 10
        stack_ids = [row["id"] for row in planned["stack"]]
        if planned["situation"] == "futa_visible":
            _check_visible_plan(planned, clip["prompt"])
        if planned["situation"] == "futa_sex":
            assert stack_ids == ["hmnsfw-aio-v25", "penis-lora-h3", "synth-pussy-h3"]
            assert "larry-v4" not in stack_ids
            assert "blowjob-h3" not in stack_ids
            assert planned["cfg"]["turbo"] is False
    assert "Genkan BJ is the next chapter" in story["clips"][-1]["prompt"] or "next chapter" in story["clips"][-1]["prompt"]
    (tmp_path / "01-stairs.jpg").write_bytes(b"fake-jpg")
    with_still = prepare_story_clip(story, 0, stills_dir=tmp_path, last_frame="ignored.png")
    assert with_still["mode"] == "i2v"
    assert with_still["first_kind"] == "still"
    assert "Picture 1" in with_still["prompt"]


def test_okaeri_story_twelve_clips_genkan(tmp_path):
    from h3_lora_studio import (
        is_story,
        load_story,
        prepare_story_clip,
        situation_ids,
        resolve_situation,
        story_canvas_wh,
        studio_sys_path,
    )

    studio_sys_path()
    from select_loras import forbidden_hits

    assert resolve_situation("おかえり120秒（専用）") == "okaeri-120s"
    assert resolve_situation("玄関おかえり（専用）") == "okaeri-120s"
    assert resolve_situation("玄関120秒（専用）") == "okaeri-120s"
    assert is_story("おかえり120秒（専用）")
    ids = situation_ids("okaeri-120s")
    assert ids == [
        "penis-lora-h3",
        "cinema-dy",
        "blowjob-h3",
        "larry-v4",
        "cumouf-h3",
        "synth-pussy-h3",
    ]
    assert "hmnsfw-aio-v25" not in ids
    story = load_story("okaeri-120s")
    assert story["duration_s"] == 120
    assert story["clip_s"] == 10
    assert story["min_age"] == 22
    assert len(story["clips"]) == 12
    assert story["canvas"] == {"width": 1024, "height": 576, "aspect": "16:9"}
    assert story_canvas_wh(story) == (1024, 576)
    assert story.get("seamless") is False
    assert story.get("stills_dir") == "okaeri-120s"
    want = [
        "futa_visible",
        "futa_visible",
        "futa_visible",
        "futa_visible",
        "futa_visible",
        "oral",
        "oral",
        "oral_creampie",
        "oral",
        "futa_visible",
        "futa_visible",
        "futa_visible",
    ]
    assert [c["situation"] for c in story["clips"]] == want
    assert [float(c["duration_s"]) for c in story["clips"]] == [10.0] * 12
    assert "LIP SYNC" in story["clips"][1]["prompt"]
    assert "LIP SYNC" in story["clips"][3]["prompt"]
    assert "LIP SYNC" in story["clips"][9]["prompt"]
    assert "LIP SYNC" not in story["clips"][0]["prompt"]
    assert "LIP SYNC" not in story["clips"][5]["prompt"]
    assert "medium-close" in story["clips"][5]["prompt"].lower() or "close" in story["clips"][5]["prompt"].lower()
    assert "NOT IN FRAME" in story["clips"][5]["prompt"]
    assert "NOT IN FRAME" in story["clips"][7]["prompt"]
    prev = None
    prev_stack = None
    for i, clip in enumerate(story["clips"]):
        hits = forbidden_hits(clip["prompt"])
        assert hits == [], hits
        assert "schoolgirl" not in clip["prompt"].lower()
        assert "15," not in clip["prompt"]
        assert "woman, 15" not in clip["prompt"].lower()
        assert "15-second take" not in clip["prompt"]
        assert "hmmotion" not in clip["prompt"]
        assert "Adult 22" in clip["prompt"] or "woman, 22" in clip["prompt"] or "woman, 39" in clip["prompt"]
        assert "Adult university" in clip["prompt"]
        assert "Not a high school" in clip["prompt"]
        assert "CAST LOCK" in clip["prompt"]
        assert "10-second take" in clip["prompt"]
        assert "No feces" in clip["prompt"] or "no feces" in clip["prompt"]
        planned = prepare_story_clip(
            story,
            i,
            last_frame="h3_chain_0.png",
            stills_dir=tmp_path,
            prev_situation=prev,
            prev_stack=prev_stack,
        )
        if i > 0 and want[i] != want[i - 1]:
            assert planned["stack_changed"]
        prev = planned["situation"]
        prev_stack = planned["stack"]
        assert planned["width"] == 1024
        assert planned["height"] == 576
        assert planned["duration_s"] == 10
        stack_ids = [row["id"] for row in planned["stack"]]
        if planned["situation"] == "oral":
            assert stack_ids[0] == "blowjob-h3"
            assert "cumouf-h3" not in stack_ids
        if planned["situation"] == "oral_creampie":
            assert stack_ids[0] == "cumouf-h3"
            assert "blowjob-h3" not in stack_ids
        if planned["situation"] == "futa_visible":
            _check_visible_plan(planned, clip["prompt"])
    assert "Pudding is the next chapter" in story["clips"][-1]["prompt"] or "dishes chapter" in story["clips"][-1]["prompt"]
    (tmp_path / "01-gate.jpg").write_bytes(b"fake-jpg")
    with_still = prepare_story_clip(story, 0, stills_dir=tmp_path, last_frame="ignored.png")
    assert with_still["mode"] == "i2v"
    assert with_still["first_kind"] == "still"
    assert "Picture 1" in with_still["prompt"]


def test_bath_story_twelve_clips_wash_area(tmp_path):
    from h3_lora_studio import (
        is_story,
        load_story,
        prepare_story_clip,
        situation_ids,
        resolve_situation,
        story_canvas_wh,
        studio_sys_path,
    )

    studio_sys_path()
    from select_loras import forbidden_hits

    assert resolve_situation("風呂120秒（専用）") == "bath-120s"
    assert resolve_situation("夜風呂（専用）") == "bath-120s"
    assert resolve_situation("風呂夜（専用）") == "bath-120s"
    assert is_story("風呂120秒（専用）")
    ids = situation_ids("bath-120s")
    assert ids == [
        "penis-lora-h3",
        "cinema-dy",
        "blowjob-h3",
        "larry-v4",
        "cumouf-h3",
        "synth-pussy-h3",
    ]
    assert "hmnsfw-aio-v25" not in ids
    story = load_story("bath-120s")
    assert story["duration_s"] == 120
    assert story["clip_s"] == 10
    assert story["min_age"] == 22
    assert len(story["clips"]) == 12
    assert story["canvas"] == {"width": 1024, "height": 576, "aspect": "16:9"}
    assert story_canvas_wh(story) == (1024, 576)
    assert story.get("seamless") is False
    assert story.get("stills_dir") == "bath-120s"
    want = [
        "futa_visible",
        "futa_visible",
        "futa_visible",
        "futa_visible",
        "futa_visible",
        "futa_visible",
        "futa_visible",
        "oral",
        "oral",
        "oral_creampie",
        "oral",
        "futa_visible",
    ]
    assert [c["situation"] for c in story["clips"]] == want
    assert [float(c["duration_s"]) for c in story["clips"]] == [10.0] * 12
    assert "LIP SYNC" in story["clips"][2]["prompt"]
    assert "LIP SYNC" in story["clips"][5]["prompt"]
    assert "LIP SYNC" in story["clips"][11]["prompt"]
    assert "LIP SYNC" not in story["clips"][0]["prompt"]
    assert "LIP SYNC" not in story["clips"][6]["prompt"]
    assert "LIP SYNC" not in story["clips"][7]["prompt"]
    assert "LIP SYNC" not in story["clips"][9]["prompt"]
    assert "medium-close" in story["clips"][7]["prompt"].lower() or "close" in story["clips"][7]["prompt"].lower()
    assert "NOT IN FRAME" in story["clips"][7]["prompt"]
    assert "NOT IN FRAME" in story["clips"][9]["prompt"]
    assert "サキにアラって" in story["clips"][2]["prompt"]
    assert "ユだとヨケイムクってる" in story["clips"][5]["prompt"]
    assert "アガッたらゴハン" in story["clips"][11]["prompt"]
    prev = None
    prev_stack = None
    for i, clip in enumerate(story["clips"]):
        hits = forbidden_hits(clip["prompt"])
        assert hits == [], hits
        assert "schoolgirl" not in clip["prompt"].lower()
        assert "15," not in clip["prompt"]
        assert "woman, 15" not in clip["prompt"].lower()
        assert "15-second take" not in clip["prompt"]
        assert "hmmotion" not in clip["prompt"]
        assert "Adult 22" in clip["prompt"] or "woman, 22" in clip["prompt"] or "woman, 39" in clip["prompt"]
        assert "Adult university" in clip["prompt"]
        assert "Not a high school" in clip["prompt"]
        assert "CAST LOCK" in clip["prompt"]
        assert "10-second take" in clip["prompt"]
        assert "No feces" in clip["prompt"] or "no feces" in clip["prompt"]
        planned = prepare_story_clip(
            story,
            i,
            last_frame="h3_chain_0.png",
            stills_dir=tmp_path,
            prev_situation=prev,
            prev_stack=prev_stack,
        )
        if i > 0 and want[i] != want[i - 1]:
            assert planned["stack_changed"]
        prev = planned["situation"]
        prev_stack = planned["stack"]
        assert planned["width"] == 1024
        assert planned["height"] == 576
        assert planned["duration_s"] == 10
        stack_ids = [row["id"] for row in planned["stack"]]
        if planned["situation"] == "oral":
            assert stack_ids[0] == "blowjob-h3"
            assert "cumouf-h3" not in stack_ids
        if planned["situation"] == "oral_creampie":
            assert stack_ids[0] == "cumouf-h3"
            assert "blowjob-h3" not in stack_ids
        if planned["situation"] == "futa_visible":
            _check_visible_plan(planned, clip["prompt"])
    last = story["clips"][-1]["prompt"]
    assert "next chapter" in last
    assert "Dinner" in last or "dining" in last.lower()
    (tmp_path / "01-hall.jpg").write_bytes(b"fake-jpg")
    with_still = prepare_story_clip(story, 0, stills_dir=tmp_path, last_frame="ignored.png")
    assert with_still["mode"] == "i2v"
    assert with_still["first_kind"] == "still"
    assert "Picture 1" in with_still["prompt"]


def test_dinner_story_twelve_clips_table(tmp_path):
    from h3_lora_studio import (
        is_story,
        load_story,
        prepare_story_clip,
        situation_ids,
        resolve_situation,
        story_canvas_wh,
        studio_sys_path,
    )

    studio_sys_path()
    from select_loras import forbidden_hits

    assert resolve_situation("食卓120秒（専用）") == "dinner-120s"
    assert resolve_situation("ご飯120秒（専用）") == "dinner-120s"
    assert resolve_situation("食卓ご飯（専用）") == "dinner-120s"
    assert is_story("食卓120秒（専用）")
    ids = situation_ids("dinner-120s")
    assert ids == [
        "penis-lora-h3",
        "cinema-dy",
        "blowjob-h3",
        "larry-v4",
        "cumouf-h3",
        "synth-pussy-h3",
    ]
    assert "hmnsfw-aio-v25" not in ids
    story = load_story("dinner-120s")
    assert story["duration_s"] == 120
    assert story["clip_s"] == 10
    assert story["min_age"] == 22
    assert len(story["clips"]) == 12
    assert story["canvas"] == {"width": 1024, "height": 576, "aspect": "16:9"}
    assert story_canvas_wh(story) == (1024, 576)
    assert story.get("seamless") is False
    assert story.get("stills_dir") == "dinner-120s"
    want = [
        "futa_visible",
        "futa_visible",
        "futa_visible",
        "futa_visible",
        "futa_visible",
        "futa_visible",
        "futa_visible",
        "oral",
        "oral",
        "oral_creampie",
        "oral",
        "futa_visible",
    ]
    assert [c["situation"] for c in story["clips"]] == want
    assert [float(c["duration_s"]) for c in story["clips"]] == [10.0] * 12
    assert "LIP SYNC" in story["clips"][2]["prompt"]
    assert "LIP SYNC" in story["clips"][5]["prompt"]
    assert "LIP SYNC" in story["clips"][11]["prompt"]
    assert "LIP SYNC" not in story["clips"][0]["prompt"]
    assert "LIP SYNC" not in story["clips"][6]["prompt"]
    assert "LIP SYNC" not in story["clips"][7]["prompt"]
    assert "LIP SYNC" not in story["clips"][9]["prompt"]
    assert "medium-close" in story["clips"][7]["prompt"].lower() or "close" in story["clips"][7]["prompt"].lower()
    assert "NOT IN FRAME" in story["clips"][7]["prompt"]
    assert "NOT IN FRAME" in story["clips"][9]["prompt"]
    assert "タベなさい" in story["clips"][2]["prompt"]
    assert "ゴハンチュウなのに" in story["clips"][5]["prompt"]
    assert "ちゃんとウエもタベなさい" in story["clips"][11]["prompt"]
    prev = None
    prev_stack = None
    for i, clip in enumerate(story["clips"]):
        hits = forbidden_hits(clip["prompt"])
        assert hits == [], hits
        assert "schoolgirl" not in clip["prompt"].lower()
        assert "15," not in clip["prompt"]
        assert "woman, 15" not in clip["prompt"].lower()
        assert "15-second take" not in clip["prompt"]
        assert "hmmotion" not in clip["prompt"]
        assert "Adult 22" in clip["prompt"] or "woman, 22" in clip["prompt"] or "woman, 39" in clip["prompt"]
        assert "Adult university" in clip["prompt"]
        assert "Not a high school" in clip["prompt"]
        assert "CAST LOCK" in clip["prompt"]
        assert "10-second take" in clip["prompt"]
        assert "No feces" in clip["prompt"] or "no feces" in clip["prompt"]
        planned = prepare_story_clip(
            story,
            i,
            last_frame="h3_chain_0.png",
            stills_dir=tmp_path,
            prev_situation=prev,
            prev_stack=prev_stack,
        )
        if i > 0 and want[i] != want[i - 1]:
            assert planned["stack_changed"]
        prev = planned["situation"]
        prev_stack = planned["stack"]
        assert planned["width"] == 1024
        assert planned["height"] == 576
        assert planned["duration_s"] == 10
        stack_ids = [row["id"] for row in planned["stack"]]
        if planned["situation"] == "oral":
            assert stack_ids[0] == "blowjob-h3"
            assert "cumouf-h3" not in stack_ids
        if planned["situation"] == "oral_creampie":
            assert stack_ids[0] == "cumouf-h3"
            assert "blowjob-h3" not in stack_ids
        if planned["situation"] == "futa_visible":
            _check_visible_plan(planned, clip["prompt"])
    last = story["clips"][-1]["prompt"]
    assert "next chapter" in last
    assert "futon" in last.lower() or "bedroom" in last.lower()
    (tmp_path / "01-change.jpg").write_bytes(b"fake-jpg")
    with_still = prepare_story_clip(story, 0, stills_dir=tmp_path, last_frame="ignored.png")
    assert with_still["mode"] == "i2v"
    assert with_still["first_kind"] == "still"
    assert "Picture 1" in with_still["prompt"]


def test_futon_story_twelve_clips_washitsu(tmp_path):
    from h3_lora_studio import (
        is_story,
        load_story,
        prepare_story_clip,
        situation_ids,
        resolve_situation,
        story_canvas_wh,
        studio_sys_path,
    )

    studio_sys_path()
    from select_loras import forbidden_hits

    assert resolve_situation("布団120秒（専用）") == "futon-120s"
    assert resolve_situation("和室120秒（専用）") == "futon-120s"
    assert resolve_situation("夜布団（専用）") == "futon-120s"
    assert is_story("布団120秒（専用）")
    ids = situation_ids("futon-120s")
    assert ids == [
        "penis-lora-h3",
        "cinema-dy",
        "blowjob-h3",
        "larry-v4",
        "cumouf-h3",
        "synth-pussy-h3",
    ]
    assert "hmnsfw-aio-v25" not in ids
    assert "thumbinbutt-h3" not in ids
    story = load_story("futon-120s")
    assert story["duration_s"] == 120
    assert story["clip_s"] == 10
    assert story["min_age"] == 22
    assert len(story["clips"]) == 12
    assert story["canvas"] == {"width": 1024, "height": 576, "aspect": "16:9"}
    assert story_canvas_wh(story) == (1024, 576)
    assert story.get("seamless") is False
    assert story.get("stills_dir") == "futon-120s"
    want = [
        "futa_visible",
        "futa_visible",
        "futa_visible",
        "futa_visible",
        "futa_visible",
        "futa_visible",
        "futa_visible",
        "oral",
        "oral",
        "oral_creampie",
        "oral",
        "futa_visible",
    ]
    assert [c["situation"] for c in story["clips"]] == want
    assert [float(c["duration_s"]) for c in story["clips"]] == [10.0] * 12
    assert "LIP SYNC" in story["clips"][5]["prompt"]
    assert "LIP SYNC" in story["clips"][11]["prompt"]
    assert "LIP SYNC" not in story["clips"][0]["prompt"]
    assert "LIP SYNC" not in story["clips"][2]["prompt"]
    assert "LIP SYNC" not in story["clips"][6]["prompt"]
    assert "LIP SYNC" not in story["clips"][7]["prompt"]
    assert "LIP SYNC" not in story["clips"][9]["prompt"]
    assert "medium-close" in story["clips"][7]["prompt"].lower() or "close" in story["clips"][7]["prompt"].lower()
    assert "NOT IN FRAME" in story["clips"][7]["prompt"]
    assert "NOT IN FRAME" in story["clips"][9]["prompt"]
    assert "ネルマエなのに" in story["clips"][5]["prompt"]
    assert "デンキケしたよ" in story["clips"][11]["prompt"]
    prev = None
    prev_stack = None
    for i, clip in enumerate(story["clips"]):
        hits = forbidden_hits(clip["prompt"])
        assert hits == [], hits
        assert "schoolgirl" not in clip["prompt"].lower()
        assert "15," not in clip["prompt"]
        assert "woman, 15" not in clip["prompt"].lower()
        assert "15-second take" not in clip["prompt"]
        assert "hmmotion" not in clip["prompt"]
        assert "Adult 22" in clip["prompt"] or "woman, 22" in clip["prompt"] or "woman, 39" in clip["prompt"]
        assert "Adult university" in clip["prompt"]
        assert "Not a high school" in clip["prompt"]
        assert "CAST LOCK" in clip["prompt"]
        assert "10-second take" in clip["prompt"]
        assert "No feces" in clip["prompt"] or "no feces" in clip["prompt"]
        planned = prepare_story_clip(
            story,
            i,
            last_frame="h3_chain_0.png",
            stills_dir=tmp_path,
            prev_situation=prev,
            prev_stack=prev_stack,
        )
        if i > 0 and want[i] != want[i - 1]:
            assert planned["stack_changed"]
        prev = planned["situation"]
        prev_stack = planned["stack"]
        assert planned["width"] == 1024
        assert planned["height"] == 576
        assert planned["duration_s"] == 10
        stack_ids = [row["id"] for row in planned["stack"]]
        if planned["situation"] == "oral":
            assert stack_ids[0] == "blowjob-h3"
            assert "cumouf-h3" not in stack_ids
        if planned["situation"] == "oral_creampie":
            assert stack_ids[0] == "cumouf-h3"
            assert "blowjob-h3" not in stack_ids
        if planned["situation"] == "futa_visible":
            _check_visible_plan(planned, clip["prompt"])
    last = story["clips"][-1]["prompt"]
    assert "next chapter" in last
    assert "morning" in last.lower()
    (tmp_path / "01-dishes.jpg").write_bytes(b"fake-jpg")
    with_still = prepare_story_clip(story, 0, stills_dir=tmp_path, last_frame="ignored.png")
    assert with_still["mode"] == "i2v"
    assert with_still["first_kind"] == "still"
    assert "Picture 1" in with_still["prompt"]


def test_sunday_story_twelve_clips_sofa(tmp_path):
    from h3_lora_studio import (
        is_story,
        load_story,
        prepare_story_clip,
        situation_ids,
        resolve_situation,
        story_canvas_wh,
        studio_sys_path,
    )

    studio_sys_path()
    from select_loras import forbidden_hits

    assert resolve_situation("休日120秒（専用）") == "sunday-120s"
    assert resolve_situation("日曜120秒（専用）") == "sunday-120s"
    assert resolve_situation("休日午前（専用）") == "sunday-120s"
    assert is_story("休日120秒（専用）")
    ids = situation_ids("sunday-120s")
    assert ids == [
        "penis-lora-h3",
        "cinema-dy",
        "hmnsfw-aio-v25",
        "synth-pussy-h3",
        "blowjob-h3",
        "larry-v4",
        "cumouf-h3",
    ]
    story = load_story("sunday-120s")
    assert story["duration_s"] == 120
    assert story["clip_s"] == 10
    assert story["min_age"] == 22
    assert len(story["clips"]) == 12
    assert story["canvas"] == {"width": 1024, "height": 576, "aspect": "16:9"}
    assert story_canvas_wh(story) == (1024, 576)
    assert story.get("seamless") is False
    assert story.get("stills_dir") == "sunday-120s"
    want = [
        "futa_visible",
        "futa_visible",
        "futa_visible",
        "futa_visible",
        "futa_visible",
        "futa_sex",
        "futa_sex",
        "futa_sex",
        "oral",
        "oral",
        "oral_creampie",
        "futa_visible",
    ]
    assert [c["situation"] for c in story["clips"]] == want
    assert [float(c["duration_s"]) for c in story["clips"]] == [10.0] * 12
    assert "LIP SYNC" in story["clips"][3]["prompt"]
    assert "LIP SYNC" in story["clips"][11]["prompt"]
    assert "LIP SYNC" not in story["clips"][0]["prompt"]
    assert "LIP SYNC" not in story["clips"][4]["prompt"]
    assert "LIP SYNC" not in story["clips"][5]["prompt"]
    assert "LIP SYNC" not in story["clips"][8]["prompt"]
    assert "LIP SYNC" not in story["clips"][10]["prompt"]
    assert "joining point" in story["clips"][5]["prompt"].lower()
    assert "Already in" in story["clips"][5]["prompt"] or "ALREADY IN" in story["clips"][5]["prompt"]
    assert "NOT IN FRAME" in story["clips"][5]["prompt"]
    assert "NOT IN FRAME" in story["clips"][8]["prompt"]
    assert "キュウジツなのにアサからムクってる" in story["clips"][3]["prompt"]
    assert "ヒルごはんまだよ" in story["clips"][11]["prompt"]
    prev = None
    prev_stack = None
    for i, clip in enumerate(story["clips"]):
        hits = forbidden_hits(clip["prompt"])
        assert hits == [], hits
        assert "schoolgirl" not in clip["prompt"].lower()
        assert "15," not in clip["prompt"]
        assert "woman, 15" not in clip["prompt"].lower()
        assert "15-second take" not in clip["prompt"]
        if planned_hmmotion := ("hmmotion" in clip["prompt"]):
            assert clip["situation"] == "futa_sex", i
        else:
            assert clip["situation"] != "futa_sex" or "hmmotion" in clip["prompt"]
        if clip["situation"] != "futa_sex":
            assert "hmmotion" not in clip["prompt"]
        else:
            assert clip["prompt"].startswith("hmmotion")
        assert "Adult 22" in clip["prompt"] or "woman, 22" in clip["prompt"] or "woman, 39" in clip["prompt"]
        assert "Adult university" in clip["prompt"]
        assert "Not a high school" in clip["prompt"]
        assert "CAST LOCK" in clip["prompt"]
        assert "10-second take" in clip["prompt"]
        assert "No feces" in clip["prompt"] or "no feces" in clip["prompt"]
        assert "Do not leave the house" in clip["prompt"] or "stay home" in clip["prompt"].lower()
        planned = prepare_story_clip(
            story,
            i,
            last_frame="h3_chain_0.png",
            stills_dir=tmp_path,
            prev_situation=prev,
            prev_stack=prev_stack,
        )
        if i > 0 and want[i] != want[i - 1]:
            assert planned["stack_changed"]
        prev = planned["situation"]
        prev_stack = planned["stack"]
        assert planned["width"] == 1024
        assert planned["height"] == 576
        assert planned["duration_s"] == 10
        stack_ids = [row["id"] for row in planned["stack"]]
        if planned["situation"] == "oral":
            assert stack_ids[0] == "blowjob-h3"
            assert "cumouf-h3" not in stack_ids
            assert "hmnsfw-aio-v25" not in stack_ids
        if planned["situation"] == "oral_creampie":
            assert stack_ids[0] == "cumouf-h3"
            assert "blowjob-h3" not in stack_ids
            assert "hmnsfw-aio-v25" not in stack_ids
        if planned["situation"] == "futa_sex":
            assert stack_ids == ["hmnsfw-aio-v25", "penis-lora-h3", "synth-pussy-h3"]
            assert "larry-v4" not in stack_ids
            assert "blowjob-h3" not in stack_ids
            assert planned["cfg"]["turbo"] is False
        if planned["situation"] == "futa_visible":
            _check_visible_plan(planned, clip["prompt"])
    last = story["clips"][-1]["prompt"]
    assert "next chapter" in last
    assert "afternoon" in last.lower() or "shopping" in last.lower()
    (tmp_path / "01-wake.jpg").write_bytes(b"fake-jpg")
    with_still = prepare_story_clip(story, 0, stills_dir=tmp_path, last_frame="ignored.png")
    assert with_still["mode"] == "i2v"
    assert with_still["first_kind"] == "still"
    assert "Picture 1" in with_still["prompt"]


def test_engawa_story_twelve_clips_madoka_shaft(tmp_path):
    from h3_lora_studio import (
        is_story,
        load_story,
        prepare_story_clip,
        situation_ids,
        resolve_situation,
        story_canvas_wh,
        studio_sys_path,
    )

    studio_sys_path()
    from select_loras import forbidden_hits

    assert resolve_situation("縁側120秒（専用）") == "engawa-120s"
    assert resolve_situation("休日午後（専用）") == "engawa-120s"
    assert resolve_situation("縁側二回戦（専用）") == "engawa-120s"
    assert is_story("縁側120秒（専用）")
    assert situation_ids("engawa-120s") == situation_ids("sunday-120s")
    story = load_story("engawa-120s")
    assert story["duration_s"] == 120
    assert story["clip_s"] == 10
    assert story["min_age"] == 22
    assert len(story["clips"]) == 12
    assert story["canvas"] == {"width": 1024, "height": 576, "aspect": "16:9"}
    assert story_canvas_wh(story) == (1024, 576)
    assert story.get("seamless") is False
    assert story.get("stills_dir") == "engawa-120s"
    want = [
        "futa_visible",
        "futa_visible",
        "futa_visible",
        "futa_visible",
        "futa_sex",
        "futa_sex",
        "futa_sex",
        "oral",
        "oral",
        "oral",
        "oral_creampie",
        "futa_visible",
    ]
    assert [c["situation"] for c in story["clips"]] == want
    assert [float(c["duration_s"]) for c in story["clips"]] == [10.0] * 12
    assert "LIP SYNC" in story["clips"][2]["prompt"]
    assert "LIP SYNC" in story["clips"][11]["prompt"]
    for idx in (0, 1, 3, 4, 5, 6, 7, 8, 9, 10):
        assert "LIP SYNC" not in story["clips"][idx]["prompt"], idx
    assert "ゴゴもムクってる" in story["clips"][2]["prompt"]
    assert "サラアラっとくから" in story["clips"][11]["prompt"]
    assert "joining point" in story["clips"][4]["prompt"].lower()
    assert "ALREADY IN" in story["clips"][4]["prompt"]
    assert "Do not put Rei inside" in story["clips"][4]["prompt"]
    for idx in (4, 5, 6, 7, 8, 9, 10):
        assert "Rei = NOT IN FRAME" in story["clips"][idx]["prompt"], idx
    for idx in (7, 8, 9, 10):
        assert "MADOKA" in story["clips"][idx]["prompt"], idx
        assert "Madoka's 20cm" in story["clips"][idx]["prompt"] or "Madoka's wet" in story["clips"][idx]["prompt"] or "Madoka's base" in story["clips"][idx]["prompt"], idx
        assert "Rei looks pleasured" not in story["clips"][idx]["prompt"], idx
    assert "Do not suck Rei" in story["clips"][7]["prompt"]
    assert "In-mouth climax from MADOKA" in story["clips"][10]["prompt"]
    prev = None
    prev_stack = None
    for i, clip in enumerate(story["clips"]):
        hits = forbidden_hits(clip["prompt"])
        assert hits == [], hits
        assert "schoolgirl" not in clip["prompt"].lower()
        assert "15-second take" not in clip["prompt"]
        if clip["situation"] != "futa_sex":
            assert "hmmotion" not in clip["prompt"]
        else:
            assert clip["prompt"].startswith("hmmotion")
        low = clip["prompt"].lower()
        for neg in ("not anal", "no anal", "switch to anal"):
            low = low.replace(neg, "")
        assert "anal" not in low, i
        assert "Adult university" in clip["prompt"]
        assert "Not a high school" in clip["prompt"]
        assert "CAST LOCK" in clip["prompt"]
        assert "10-second take" in clip["prompt"]
        assert "No feces" in clip["prompt"] or "no feces" in clip["prompt"]
        planned = prepare_story_clip(
            story,
            i,
            last_frame="h3_chain_0.png",
            stills_dir=tmp_path,
            prev_situation=prev,
            prev_stack=prev_stack,
        )
        if i > 0 and want[i] != want[i - 1]:
            assert planned["stack_changed"]
        prev = planned["situation"]
        prev_stack = planned["stack"]
        assert planned["width"] == 1024
        assert planned["height"] == 576
        assert planned["duration_s"] == 10
        stack_ids = [row["id"] for row in planned["stack"]]
        if planned["situation"] == "oral":
            assert stack_ids[0] == "blowjob-h3"
            assert "hmnsfw-aio-v25" not in stack_ids
        if planned["situation"] == "oral_creampie":
            assert stack_ids[0] == "cumouf-h3"
            assert "blowjob-h3" not in stack_ids
        if planned["situation"] == "futa_sex":
            assert stack_ids == ["hmnsfw-aio-v25", "penis-lora-h3", "synth-pussy-h3"]
            assert planned["cfg"]["turbo"] is False
        if planned["situation"] == "futa_visible":
            _check_visible_plan(planned, clip["prompt"])
    (tmp_path / "05-in.jpg").write_bytes(b"fake-jpg")
    with_still = prepare_story_clip(story, 4, stills_dir=tmp_path, last_frame="ignored.png")
    assert with_still["mode"] == "i2v"
    assert with_still["first_kind"] == "still"


def test_story_download_lists_cover_every_planned_stack(tmp_path):
    """② downloads SITUATION_DOWNLOAD[story]; every LoRA any clip plans must be in it."""
    from h3_lora_studio import CHAIN_PACK_IDS, STORY_IDS, load_story, prepare_story_clip, situation_ids

    for sid in sorted(STORY_IDS | CHAIN_PACK_IDS):
        story = load_story(sid)
        listed = set(situation_ids(sid))
        assert set(story.get("download") or []) == listed, sid
        assert "futa-h3-v51" not in listed
        if sid not in STORY_IDS:
            continue
        for i in range(len(story["clips"])):
            planned = prepare_story_clip(story, i, last_frame=None, stills_dir=tmp_path)
            need = {row["id"] for row in planned["stack"]}
            assert need <= listed, (sid, i + 1, sorted(need - listed))
            assert "futa-h3-v51" not in need


def test_all_stories_pass_follow():
    from h3_lora_studio import STORY_IDS, load_story, validate_story_follow

    for sid in sorted(STORY_IDS):
        story = load_story(sid)
        assert validate_story_follow(story) == [], sid
        assert abs(float(story["clip_s"]) - 10) < 0.01
        assert all(
            abs(float(c.get("duration_s") or story["clip_s"]) - 10) < 0.01
            for c in story["clips"]
        )


def test_compact_story_prompt_drops_absent_cast_and_editor_meta():
    from h3_lora_studio import (
        CAST_LOCK_SERIES_LINE,
        CHAIN_PACK_IDS,
        STORY_CAST_DEF_RE,
        STORY_IDS,
        compact_story_prompt,
        load_story,
        story_cast_present,
        studio_sys_path,
    )

    studio_sys_path()
    from select_loras import forbidden_hits

    assert STORY_CAST_DEF_RE.pattern.startswith("^(Sayaka|Rei|Aya|Madoka|Saleswoman|Doctor|Conductor|Clerk|Seller|Instructor|Professor): Adult")
    canon = ["subject_definitions:", "environment:", "integrated_multimodal_description:", "overall_soundscape:", "non_diegetic_music:"]
    total_raw = total_out = 0
    for sid in sorted(STORY_IDS | CHAIN_PACK_IDS):
        story = load_story(sid)
        for i, clip in enumerate(story["clips"]):
            raw = clip["prompt"]
            out = compact_story_prompt(raw)
            where = f"{sid} clip {i + 1}"
            total_raw += len(raw)
            total_out += len(out)
            assert len(out) < len(raw), where
            positions = [out.find(k) for k in canon]
            assert all(p >= 0 for p in positions), where
            assert positions == sorted(positions), where
            assert out.count("subject_definitions:") == 1, where
            assert "Do not copy the previous clip" not in out, where
            assert "NOT IN THIS CLIP" not in out, where
            assert not re.search(r"Clip \d+ of \d+\.", out), where
            assert "stories." not in out, where
            if "CAST LOCK" in raw:
                assert CAST_LOCK_SERIES_LINE in out, where
            assert forbidden_hits(out) == [], where
            absent = set(re.findall(r"^([A-Z][a-z]+) = (?:NOT IN FRAME|NOT IN THIS STORY|OFF SCREEN)", raw, re.M))
            absent |= set(re.findall(r"^([A-Z][a-z]+):\s.*NOT IN THIS CLIP", raw, re.M))
            present = set(story_cast_present(raw)) - absent
            assert present, where
            for name in absent:
                assert f"\n{name}: Adult" not in out, (where, name)
                assert f"{name} = NOT IN FRAME" not in out, (where, name)
            for name in present:
                line = re.search(rf"^{name}: Adult[^\n]*", raw, re.M).group(0)
                assert line in out, (where, name)
            if absent:
                assert "Not in this clip: " in out, where
            for spoken in re.findall(r"「[^」]+」", raw):
                assert spoken in out, where
            for key in ("LIP SYNC:", "CAMERA:", "HARD LOCK", "No men.", "Breast sizes stay locked"):
                if key in raw and key != "HARD LOCK":
                    assert key in out, (where, key)
            desc = re.search(r"integrated_multimodal_description:\n(.+?)\n\n", raw, re.S).group(1).strip()
            assert desc in out, where
            sound = re.search(r"overall_soundscape:\n(.+?)\n\n", raw, re.S).group(1).strip()
            assert sound in out, where
            # WHO blocking of the women who are in frame stays word for word.
            who = re.search(r"WHO:\n(.+?)\n\n", raw, re.S)
            if who:
                for row in who.group(1).split("\n"):
                    row = row.strip()
                    if row and not re.match(r"^[A-Z][a-z]+ = (?:NOT IN FRAME|NOT IN THIS STORY|OFF SCREEN)", row):
                        assert row in out, (where, row)
    assert total_out < total_raw * 0.92


def test_compact_story_prompt_unstructured_text_only_gets_line_cleanup():
    from h3_lora_studio import compact_story_prompt

    plain = "A woman walks.\nNew 10-second take. Hard cut. Do not copy the previous clip.\nShe smiles."
    assert compact_story_prompt(plain) == "A woman walks.\nShe smiles."
    assert compact_story_prompt("") == ""
    assert compact_story_prompt("   ") == ""


def test_prepend_triggers_uses_whole_tokens():
    from h3_lora_studio import has_trigger_word, prepend_triggers

    stack = [
        {"id": "penis-lora-h3", "trigger": "PENISLORA"},
        {"id": "cinema-dy", "trigger": "DY"},
        {"id": "hmnsfw-aio-v25", "trigger": ""},
    ]
    assert not has_trigger_word("Full bodies from head to feet. Everybody nude.", "DY")
    assert has_trigger_word("PENISLORA, DY\nFull bodies", "DY")
    assert has_trigger_word("hmmotion, PENISLORA\nx", "PENISLORA")
    out = prepend_triggers("Full bodies from head to feet.", stack)
    assert out.startswith("PENISLORA, DY\n")
    assert prepend_triggers("PENISLORA, DY\nFull bodies", stack) == "PENISLORA, DY\nFull bodies"
    assert prepend_triggers("bl0w_j0b close", [{"trigger": "bl0w_j0b"}]) == "bl0w_j0b close"


def test_story_clip_prompt_keeps_schema_order_with_lock_inside_description(tmp_path):
    from h3_lora_studio import load_story, prepare_story_clip

    story = load_story("engawa-120s")
    planned = prepare_story_clip(story, 1, last_frame=None, stills_dir=tmp_path)
    text = planned["prompt"]
    assert text.startswith("PENISLORA, DY\n")
    order = [text.find(k) for k in ("subject_definitions:", "environment:", "integrated_multimodal_description:", "feminine_lock:", "overall_soundscape:", "non_diegetic_music:")]
    assert all(p >= 0 for p in order)
    assert order == sorted(order)
    assert "Sayaka: Adult" not in text
    assert "Not in this clip: Sayaka." in text
    assert text.rstrip().endswith("N/A")


def test_validate_story_follow_hmmotion_only_on_aio_sex():
    from h3_lora_studio import validate_story_follow

    base = "medium-close on the mouth. joining point. No speech."
    bad_oral = {"clip_s": 10, "clips": [{"duration_s": 10, "situation": "oral", "prompt": "hmmotion, PENISLORA\n" + base}]}
    errs = validate_story_follow(bad_oral)
    assert any("hmmotion is only for the AIO sex clip" in e for e in errs)
    no_trigger_sex = {"clip_s": 10, "clips": [{"duration_s": 10, "situation": "futa_sex", "prompt": "PENISLORA\nAlready in. " + base}]}
    errs = validate_story_follow(no_trigger_sex)
    assert any("must start with hmmotion" in e for e in errs)
    good = {"clip_s": 10, "clips": [{"duration_s": 10, "situation": "futa_sex", "prompt": "hmmotion, PENISLORA\nAlready in. " + base}]}
    assert validate_story_follow(good) == []


def test_validate_story_follow_rejects_act_speech_and_spoken_15s():
    from h3_lora_studio import validate_story_follow

    spoken_oral = {
        "clip_s": 10,
        "clips": [
            {
                "duration_s": 10,
                "situation": "oral",
                "prompt": "medium-close on the mouth\n「だめ」",
            }
        ],
    }
    errs = validate_story_follow(spoken_oral)
    assert any("must not speak" in e for e in errs)
    spoken_15 = {
        "clip_s": 10,
        "clips": [
            {
                "duration_s": 15,
                "situation": "futa_visible",
                "prompt": "ONE UNBROKEN 15-second take. LIP SYNC: face large.\n「こんにちは」",
            }
        ],
    }
    errs = validate_story_follow(spoken_15)
    assert any("spoken clips stay 10s" in e for e in errs)
    ten_says_fifteen = {
        "clip_s": 10,
        "clips": [
            {
                "duration_s": 10,
                "situation": "futa_visible",
                "prompt": "ONE UNBROKEN 15-second take. LIP SYNC: face large.\n「こんにちは」",
            }
        ],
    }
    errs = validate_story_follow(ten_says_fifteen)
    assert any("10-second take" in e for e in errs)
    silent_15 = {
        "clip_s": 10,
        "clips": [
            {
                "duration_s": 15,
                "situation": "oral",
                "prompt": "ONE UNBROKEN 15-second take. medium-close on the mouth. Already oral.",
            }
        ],
    }
    assert validate_story_follow(silent_15) == []


def test_story_play_labels_resolve_to_story_and_play():
    from h3_lora_studio import (
        CHAIN_PACK_IDS,
        STORY_IDS,
        STORY_ORDER,
        apply_story_play,
        chain_pack_labels,
        chain_pack_legacy_labels,
        is_chain_pack,
        is_story,
        load_story,
        resolve_story_play,
        story_play_labels,
    )

    assert STORY_IDS == set(STORY_ORDER)
    assert len(STORY_IDS) == 11
    assert "homecoming-90s" in STORY_IDS and "engawa-120s" in STORY_IDS
    assert {"sales-visit-60s", "checkup-100s", "last-stop-40s"} <= CHAIN_PACK_IDS
    assert not (CHAIN_PACK_IDS & STORY_IDS)
    labels = story_play_labels()
    assert len(labels) == 55
    assert labels[:5] == ["帰宅（専用）", "帰宅（つなぐ）", "帰宅（つなぐ修）", "帰宅（参照つなぐ）", "帰宅（参照つなぐ修）"]
    assert labels[10:15] == ["登校（専用）", "登校（つなぐ）", "登校（つなぐ修）", "登校（参照つなぐ）", "登校（参照つなぐ修）"]
    pack_labels = chain_pack_labels()
    assert len(pack_labels) == 5 * len(CHAIN_PACK_IDS)
    assert pack_labels[:5] == ["訪問販売（専用）", "訪問販売（つなぐ）", "訪問販売（つなぐ修）", "訪問販売（参照つなぐ）", "訪問販売（参照つなぐ修）"]
    assert chain_pack_legacy_labels() == ["訪問販売60秒（つなぐ）", "定期検診100秒（つなぐ）", "終点40秒（つなぐ）"]
    assert resolve_situation("登校（つなぐ）") == "commute-120s"
    assert is_story("登校（つなぐ）")
    assert not is_chain_pack("登校（つなぐ）")
    assert resolve_situation("登校（専用）") == "commute-120s"
    assert resolve_situation("登校（つなぐ修）") == "commute-120s"
    assert resolve_story_play("登校（専用）") == "dedicated"
    assert resolve_story_play("登校（つなぐ）") == "chain"
    assert resolve_story_play("登校（つなぐ修）") == "chain_rewrite"
    assert resolve_story_play("登校（参照つなぐ）") == "ref_chain"
    assert resolve_story_play("登校（参照つなぐ修）") == "ref_chain_rewrite"
    assert resolve_story_play("登校120秒（専用）") == "dedicated"
    assert resolve_story_play("朝〜正門120秒（専用）") == "dedicated"
    assert resolve_story_play("縁側二回戦（専用）") == "dedicated"
    assert resolve_story_play("commute-120s") == "dedicated"
    for sid in STORY_ORDER:
        short = labels[STORY_ORDER.index(sid) * 5]
        assert resolve_situation(short) == sid
    # Named packs are chains but never stories.
    assert resolve_situation("訪問販売60秒（つなぐ）") == "sales-visit-60s"
    assert is_chain_pack("訪問販売60秒（つなぐ）")
    assert not is_story("訪問販売60秒（つなぐ）")
    assert is_chain_pack("定期検診100秒（つなぐ）")
    assert is_chain_pack("終点40秒（つなぐ）")
    assert not is_story("checkup-100s") and not is_story("last-stop-40s")
    story = load_story("commute-120s")
    assert story.get("seamless") is False
    ded = apply_story_play(story, "dedicated")
    assert ded["seamless"] is False and ded["rewrite_chain_prompts"] is False
    assert all(c["start"] == "still_or_t2v" for c in ded["clips"])
    ch = apply_story_play(story, "chain")
    assert ch["seamless"] is True and ch["rewrite_chain_prompts"] is False
    assert ch["clips"][0]["start"] == "still_or_t2v"
    assert all(c["start"] == "continue" for c in ch["clips"][1:])
    rw = apply_story_play(story, "chain_rewrite")
    assert rw["seamless"] is True and rw["rewrite_chain_prompts"] is True
    assert all(c["start"] == "continue" for c in rw["clips"][1:])
    ref = apply_story_play(story, "ref_chain")
    assert ref["seamless"] is True and ref["rewrite_chain_prompts"] is False
    assert ref["use_cast_ref"] is True
    assert ref["clips"][0]["start"] == "still_or_t2v"
    ref_rw = apply_story_play(story, "ref_chain_rewrite")
    assert ref_rw["seamless"] is True and ref_rw["rewrite_chain_prompts"] is True
    assert ref_rw["use_cast_ref"] is True
    assert ded.get("use_cast_ref") is False
    # The loaded JSON is untouched by apply_story_play.
    assert story.get("seamless") is False
    assert all(c["start"] == "still_or_t2v" for c in story["clips"])
    assert "rewrite_chain_prompts" not in story
    text = explain_choice("登校（専用）", "テキストから（写真なし）")
    assert "再生: 専用（カット" in text
    text = explain_choice("登校（つなぐ）", "テキストから（写真なし）")
    assert "つなぐ・文そのまま" in text
    text = explain_choice("登校（つなぐ修）", "テキストから（写真なし）")
    assert "つなぐ・1本目を長回しに直す" in text
    text = explain_choice("登校（参照つなぐ）", "テキストから（写真なし）")
    assert "参照つなぐ" in text and "input/cast" in text and "R2V" in text
    text = explain_choice("短編集（参照）", "テキストから（写真なし）")
    assert "短編集" in text and "15秒" in text and "R2V" in text
    text = explain_choice("訪問販売60秒（つなぐ）", "テキストから（写真なし）")
    assert "つなぐ・1本目を長回しに直す" in text and "名前付きパック" in text and "専用ストーリーではありません" in text
    text = explain_choice("カフェ（専用）", "テキストから（写真なし）")
    assert "再生: 専用（カット" in text and "名前付きパック" in text


def test_chain_pack_three_plays(tmp_path):
    """Packs replay in the same three plays as the stories. Legacy long labels stay つなぐ修."""
    from h3_lora_studio import (
        CHAIN_OPENING_LINE,
        CHAIN_PACK_ORDER,
        STORY_TITLE_JA,
        apply_story_play,
        is_chain_pack,
        is_story,
        load_story,
        prepare_story_clip,
        resolve_story_play,
        story_play_label,
    )

    for pid in CHAIN_PACK_ORDER:
        assert pid in STORY_TITLE_JA
        for play in ("dedicated", "chain", "chain_rewrite", "ref_chain", "ref_chain_rewrite"):
            label = story_play_label(pid, play)
            assert resolve_situation(label) == pid, label
            assert resolve_story_play(label) == play, label
            assert is_chain_pack(label) and not is_story(label)
        # bare id keeps the pack default (last-frame chain, clip 1 rewritten)
        assert resolve_story_play(pid) == "chain_rewrite"
    for legacy in ("訪問販売60秒（つなぐ）", "定期検診100秒（つなぐ）", "終点40秒（つなぐ）", "訪問販売（つなぐ）"):
        assert is_chain_pack(legacy)
    assert resolve_story_play("訪問販売60秒（つなぐ）") == "chain_rewrite"
    assert resolve_story_play("定期検診100秒（つなぐ）") == "chain_rewrite"
    assert resolve_story_play("終点40秒（つなぐ）") == "chain_rewrite"
    # 「訪問販売（つなぐ）」 is the new short label: chain without rewrite.
    assert resolve_story_play("訪問販売（つなぐ）") == "chain"
    assert resolve_story_play("訪問販売（専用）") == "dedicated"
    assert resolve_story_play("訪問販売（つなぐ修）") == "chain_rewrite"
    assert resolve_story_play("訪問販売（参照つなぐ）") == "ref_chain"
    assert resolve_story_play("訪問販売（参照つなぐ修）") == "ref_chain_rewrite"

    story = load_story("sales-visit-60s")
    assert story["seamless"] is True and all(c["start"] == "continue" for c in story["clips"][1:])
    ded = apply_story_play(story, "dedicated")
    assert ded["seamless"] is False and ded["rewrite_chain_prompts"] is False
    assert all(c["start"] == "still_or_t2v" for c in ded["clips"])
    p0 = prepare_story_clip(ded, 0, stills_dir=tmp_path)
    p1 = prepare_story_clip(ded, 1, last_frame="h3_chain_0.png", stills_dir=tmp_path)
    assert p0["mode"] == "t2v" and CHAIN_OPENING_LINE not in p0["prompt"]
    assert p1["mode"] == "t2v" and p1["first_kind"] == "t2v" and p1["seamless"] is False
    assert "Picture 1" not in p1["prompt"]
    ch = apply_story_play(story, "chain")
    assert ch["seamless"] is True and ch["rewrite_chain_prompts"] is False
    c0 = prepare_story_clip(ch, 0, stills_dir=tmp_path)
    c1 = prepare_story_clip(ch, 1, last_frame="h3_chain_0.png", stills_dir=tmp_path)
    assert CHAIN_OPENING_LINE not in c0["prompt"] and "opening of one continuous long take" not in c0["prompt"]
    assert c1["mode"] == "i2v" and c1["first_kind"] == "last_frame" and "Picture 1" in c1["prompt"]
    assert c1["rewrite_chain_prompts"] is False
    rw = apply_story_play(story, "chain_rewrite")
    r0 = prepare_story_clip(rw, 0, stills_dir=tmp_path)
    assert "opening of one continuous long take" in r0["prompt"]
    # JSON on disk untouched
    assert story["seamless"] is True and "rewrite_chain_prompts" not in story and "play" not in story


def _check_pretext_pack(sid, tmp_path, *, n_clips, situations, lines, cast_defs, download):
    """建前 packs: 10s × N, kana lines (≤2 per face clip), silent acts, per-clip LoRA, canvas from JSON only."""
    from h3_lora_studio import (
        ACT_SITUATIONS,
        HMMOTION_SITUATIONS,
        _KANJI_RE,
        load_story,
        prepare_story_clip,
        situation_ids,
        spoken_lines,
        story_canvas_wh,
        story_cast_present,
        validate_story_follow,
    )

    story = load_story(sid)
    assert story["id"] == sid and story["kind"] == "chain" and story["seamless"] is True
    assert story["spoken_no_kanji"] is True and story["spoken_max"] == 2
    assert story["min_age"] >= 21 and story["clip_s"] == 10
    assert len(story["clips"]) == n_clips
    assert story["duration_s"] == 10 * n_clips
    assert story["canvas"] == {"width": 576, "height": 1024, "aspect": "9:16"}
    assert story_canvas_wh(story) == (576, 1024)
    assert validate_story_follow(story) == []
    assert story["clips"][0]["start"] == "still_or_t2v"
    assert all(c["start"] == "continue" for c in story["clips"][1:])
    assert set(story["download"]) == set(download)
    assert set(situation_ids(sid)) == set(download)
    assert [c["situation"] for c in story["clips"]] == situations
    prev = None
    prev_stack = None
    for i, clip in enumerate(story["clips"]):
        prompt = clip["prompt"]
        assert clip["duration_s"] == 10
        assert "15-second" not in prompt and "Hard cut" not in prompt
        # the canvas is decided by the JSON; no size text in the prompt
        assert "576x1024" not in prompt and "9:16" not in prompt and "16:9" not in prompt
        got = spoken_lines(prompt)
        uniq = []
        for s in got:
            if s not in uniq:
                uniq.append(s)
        assert uniq == lines[i], (sid, i + 1, uniq)
        for s in uniq:
            assert not _KANJI_RE.search(s), (sid, s)
        if clip["situation"] in HMMOTION_SITUATIONS:
            assert prompt.startswith("hmmotion")
        else:
            assert "hmmotion" not in prompt.lower()
        if clip["situation"] in ACT_SITUATIONS:
            assert not uniq
            assert "close" in prompt.lower()
            assert "No spoken words" in prompt
        else:
            assert clip["situation"] == "futa_visible"
            assert uniq and "LIP SYNC" in prompt
        present = story_cast_present(prompt)
        assert present and set(present) <= set(cast_defs), (sid, i + 1, present)
        for name in present:
            assert f"{name}: Adult Japanese woman" in prompt, (sid, i + 1, name)
        if "Clear futanari" in prompt:
            assert "Penis plus vagina, never balls" in prompt
            assert "no scrotum" in prompt
        if "Aya" in present or "Sayaka" in present:
            assert "NO penis" in prompt
        assert "No men" in prompt
        planned = prepare_story_clip(
            story, i, last_frame=("h3_chain_%d.png" % (i - 1)) if i else None, stills_dir=tmp_path, prev_situation=prev, prev_stack=prev_stack
        )
        prev = planned["situation"]
        prev_stack = planned["stack"]
        assert {row["id"] for row in planned["stack"]} <= set(download)
        assert planned["width"] == 576 and planned["height"] == 1024
        assert planned["duration_s"] == 10
        if i == 0:
            assert planned["mode"] == "t2v" and "opening of one continuous long take" in planned["prompt"]
        else:
            assert planned["mode"] == "i2v" and planned["first_kind"] == "last_frame"
            assert "Picture 1" in planned["prompt"]
        if uniq:
            assert planned["turbo"] is False and planned["sampler"]["steps"] == 12
        for s in uniq:
            assert s in planned["prompt"]
    return story


def test_cafe_pack_pretext_water_and_milk(tmp_path):
    story = _check_pretext_pack(
        "cafe-100s", tmp_path, n_clips=10,
        situations=["futa_visible"] * 3 + ["oral"] + ["futa_visible"] * 3 + ["oral", "oral_creampie", "futa_visible"],
        lines=[
            ["あちぃー", "あー、スズシイ！いきかえるー！"],
            ["いらっしゃいませ。ゴチュウモンはいかがしますか？", "アイスコーヒーで"],
            ["あ、おミズください", "あ、はい、どうぞ"],
            [],
            ["あー！おいし！いきかえる！", "ありがとうございます。コーヒー、すぐおもちしますね"],
            ["おマたせしました", "あ、ミルクください！"],
            ["かしこまりました。はい、どうぞ"],
            [],
            [],
            ["んー、やっぱしぼりたてはおいしい！"],
        ],
        cast_defs=["Aya", "Clerk"],
        download=["penis-lora-h3", "cinema-dy", "blowjob-h3", "larry-v4", "cumouf-h3", "synth-pussy-h3"],
    )
    # clip 1: the clerk is not in frame yet, but her definition is not written either
    c1 = story["clips"][0]["prompt"]
    assert "Clerk = NOT IN FRAME" in c1 and "Clerk: Adult" not in c1
    from h3_lora_studio import story_cast_present
    assert story_cast_present(c1) == ["Aya"]
    for clip in story["clips"][1:]:
        assert story_cast_present(clip["prompt"]) == ["Aya", "Clerk"]
    assert "yellow stream" in story["clips"][3]["prompt"]
    assert "BASE" in story["clips"][7]["prompt"]
    assert "CUMOUF" in story["clips"][8]["prompt"]
    assert "iced coffee" in story["clips"][9]["prompt"] and "kiss" in story["clips"][9]["prompt"].lower()
    for clip in story["clips"]:
        assert "Rei" not in clip["prompt"] and "Madoka" not in clip["prompt"] and "Sayaka" not in clip["prompt"]


def test_train_sales_pack_rei_receiver_penis_unused(tmp_path):
    story = _check_pretext_pack(
        "train-sales-80s", tmp_path, n_clips=8,
        situations=["futa_visible", "futa_visible", "oral", "futa_visible", "futa_visible", "oral", "oral_creampie", "futa_visible"],
        lines=[
            ["おチャ、コーヒー、いかがですか", "おチャ、ください"],
            ["はい。アツいのとヒヤシ、どっち", "ヒヤシで"],
            [],
            ["あー、シミる", "ほかにごヨウは？"],
            ["ミルクコーヒーも"],
            [],
            [],
            ["ん、アツイ。ミルクきいてる", "ありがとうございました"],
        ],
        cast_defs=["Rei", "Seller"],
        download=["penis-lora-h3", "cinema-dy", "blowjob-h3", "larry-v4", "cumouf-h3", "synth-pussy-h3"],
    )
    for clip in story["clips"]:
        assert "20cm hangs unused" in clip["prompt"]
        assert "Aya" not in clip["prompt"]


def test_red_light_pack_hands_on_wheel(tmp_path):
    story = _check_pretext_pack(
        "red-light-50s", tmp_path, n_clips=5,
        situations=["futa_visible", "futa_visible", "oral", "oral_creampie", "futa_visible"],
        lines=[["アカだね", "つぎ、ミギだよ"], ["エアコン、ヨワくする？", "このままでいい"], [], [], ["アオになった。ミギね", "うん"]],
        cast_defs=["Aya", "Rei"],
        download=["penis-lora-h3", "cinema-dy", "blowjob-h3", "larry-v4", "cumouf-h3", "synth-pussy-h3"],
    )
    for clip in story["clips"][2:4]:
        assert "wheel" in clip["prompt"].lower()
    assert "stream" not in story["clips"][2]["prompt"].lower()


def test_yoga_pack_doggy_already_in(tmp_path):
    story = _check_pretext_pack(
        "yoga-50s", tmp_path, n_clips=5,
        situations=["futa_visible", "futa_visible", "doggy", "doggy", "futa_visible"],
        lines=[["コシ、オトして", "ここ？"], ["もうスコし、マエ", "コツバン、オトしたまま"], [], [], ["イキをトトのえて", "スイブン、とってね"]],
        cast_defs=["Aya", "Instructor"],
        download=["penis-lora-h3", "cinema-dy", "doggy-h3", "synth-pussy-h3", "larry-v4"],
    )
    for clip in story["clips"][2:4]:
        assert ("ALREADY IN" in clip["prompt"] or "Still joined" in clip["prompt"]) and "Joining point" in clip["prompt"]
        assert "Do not pull out" in clip["prompt"]
    assert "Not oral" in story["clips"][2]["prompt"]
    assert "NOT in" in story["clips"][1]["prompt"]


def test_back_wash_pack_cunnilingus_then_pee(tmp_path):
    story = _check_pretext_pack(
        "back-wash-60s", tmp_path, n_clips=6,
        situations=["futa_visible", "futa_visible", "cunnilingus_futa", "futa_visible", "oral", "futa_visible"],
        lines=[["カタいね", "カタ、やって"], ["アワ、タすよ", "シタも"], [], ["アガリユ"], [], ["シミる。アガっていいよ"]],
        cast_defs=["Madoka", "Sayaka"],
        download=["penis-lora-h3", "cinema-dy", "lesbian-cunnilingus-h3", "synth-pussy-h3", "blowjob-h3", "larry-v4"],
    )
    cunni = story["clips"][2]["prompt"]
    assert "close-up" in cunni.lower() and "Not oral on the penis" in cunni and "20cm unused" in cunni
    assert "yellow stream" in story["clips"][4]["prompt"] and "No jupo" in story["clips"][4]["prompt"]
    for clip in story["clips"]:
        assert "Aya" not in clip["prompt"] and "Rei" not in clip["prompt"].replace("different face from Rei", "")


def test_karaoke_pack_jupo_during_song(tmp_path):
    story = _check_pretext_pack(
        "karaoke-50s", tmp_path, n_clips=5,
        situations=["futa_visible", "futa_visible", "oral", "oral_creampie", "futa_visible"],
        lines=[["このキョク、サビたかい", "キー、サげないの"], ["このまま"], [], [], ["キュウヨンてん", "サビ、キレてた"]],
        cast_defs=["Aya", "Madoka"],
        download=["penis-lora-h3", "cinema-dy", "blowjob-h3", "larry-v4", "cumouf-h3", "synth-pussy-h3"],
    )
    assert "mic" in story["clips"][2]["prompt"].lower()
    assert "last note" in story["clips"][3]["prompt"].lower()


def test_laundromat_pack_aio_on_machine(tmp_path):
    story = _check_pretext_pack(
        "laundromat-50s", tmp_path, n_clips=5,
        situations=["futa_visible", "futa_visible", "futa_sex", "futa_sex", "futa_visible"],
        lines=[["あとナンプン", "ジュウハチふん"], ["ナガいね", "スワる？"], [], [], ["オわった", "たたもう"]],
        cast_defs=["Aya", "Rei"],
        download=["penis-lora-h3", "cinema-dy", "hmnsfw-aio-v25", "synth-pussy-h3", "larry-v4"],
    )
    for clip in story["clips"][2:4]:
        assert clip["prompt"].startswith("hmmotion, PENISLORA")
        assert "ALREADY IN" in clip["prompt"] or "Still joined" in clip["prompt"]
        assert "machine" in clip["prompt"].lower()


def test_lecture_desk_pack_under_the_lectern(tmp_path):
    story = _check_pretext_pack(
        "lecture-desk-50s", tmp_path, n_clips=5,
        situations=["futa_visible", "futa_visible", "oral", "oral_creampie", "futa_visible"],
        lines=[["ここ、シケンにでます", "ハイ"], ["ノート、トって"], [], [], ["シュクダイ、ニジュウページ", "ハイ"]],
        cast_defs=["Aya", "Professor"],
        download=["penis-lora-h3", "cinema-dy", "blowjob-h3", "larry-v4", "cumouf-h3", "synth-pussy-h3"],
    )
    assert "lectern" in story["clips"][2]["prompt"].lower()
    assert "chalk" in story["clips"][3]["prompt"].lower()
    # a different story from the dedicated 授業 (lecture-120s)
    assert resolve_situation("講義机（専用）") == "lecture-desk-50s"
    assert resolve_situation("授業（専用）") == "lecture-120s"


def test_camp_pack_cunnilingus_only(tmp_path):
    story = _check_pretext_pack(
        "camp-50s", tmp_path, n_clips=5,
        situations=["futa_visible", "futa_visible", "cunnilingus_futa", "cunnilingus_futa", "futa_visible"],
        lines=[["カ、いる", "スプレー、どこ"], ["テントのナカ", "ココ、ヤラれた？"], [], [], ["スプレー、ダしてくる", "ライト、モっていって"]],
        cast_defs=["Aya", "Rei"],
        download=["penis-lora-h3", "cinema-dy", "lesbian-cunnilingus-h3", "synth-pussy-h3", "larry-v4"],
    )
    for clip in story["clips"]:
        assert "20cm hangs unused" in clip["prompt"]
    for clip in story["clips"][2:4]:
        assert "Not oral on a penis" in clip["prompt"] and "Not insertion" in clip["prompt"]
    assert "blowjob-h3" not in story["download"] and "cumouf-h3" not in story["download"]


def test_fireworks_pack_standing_from_behind(tmp_path):
    story = _check_pretext_pack(
        "fireworks-50s", tmp_path, n_clips=5,
        situations=["futa_visible", "futa_visible", "futa_sex", "futa_sex", "futa_visible"],
        lines=[["いちハツめ", "アオい"], ["ウチアゲ、オソいね"], [], [], ["かえろっか", "ゴミ、ヒロって"]],
        cast_defs=["Madoka", "Sayaka"],
        download=["penis-lora-h3", "cinema-dy", "hmnsfw-aio-v25", "synth-pussy-h3", "larry-v4"],
    )
    for clip in story["clips"][2:4]:
        assert clip["prompt"].startswith("hmmotion, PENISLORA")
        assert "from behind" in clip["prompt"].lower() or "Still joined" in clip["prompt"]
        assert "sky" in clip["prompt"].lower()
    for clip in story["clips"]:
        assert "Aya" not in clip["prompt"]


def test_validate_story_follow_spoken_max_and_doggy():
    from h3_lora_studio import validate_story_follow

    two = {
        "clip_s": 10,
        "spoken_max": 2,
        "clips": [{"duration_s": 10, "situation": "futa_visible", "prompt": "LIP SYNC: face large.\n「はい」「いいえ」"}],
    }
    assert validate_story_follow(two) == []
    three = dict(two)
    three["clips"] = [{"duration_s": 10, "situation": "futa_visible", "prompt": "LIP SYNC: face large.\n「はい」「いいえ」「うん」"}]
    assert any("at most 2 spoken lines" in e for e in validate_story_follow(three))
    # spoken_max never goes above 2
    big = dict(three)
    big["spoken_max"] = 9
    assert any("at most 2 spoken lines" in e for e in validate_story_follow(big))
    dog = {
        "clip_s": 10,
        "clips": [{"duration_s": 10, "situation": "doggy", "prompt": "medium-close side view. They thrust."}],
    }
    assert any("already be in" in e for e in validate_story_follow(dog))
    dog["clips"][0]["prompt"] = "medium-close side view. ALREADY IN. Joining point visible."
    assert validate_story_follow(dog) == []


def test_story_play_chain_prepares_last_frame_i2v(tmp_path):
    from h3_lora_studio import (
        CHAIN_OPENING_LINE,
        DEDICATED_SCENE_IMAGE_LINE,
        FINAL_SCENE_LINE,
        apply_story_play,
        load_story,
        prepare_story_clip,
    )

    story = load_story("commute-120s")
    n = len(story["clips"])

    chain = apply_story_play(story, "chain")
    c0 = prepare_story_clip(chain, 0, last_frame=None, stills_dir=tmp_path, force_t2v=True)
    assert c0["mode"] == "t2v"
    assert c0["seamless"] is True and c0["rewrite_chain_prompts"] is False
    assert "opening of one continuous long take" not in c0["prompt"]
    assert CHAIN_OPENING_LINE not in c0["prompt"]
    assert "Picture 1" not in c0["prompt"]
    c1 = prepare_story_clip(chain, 1, last_frame="h3_chain_0.png", stills_dir=tmp_path, force_t2v=True)
    assert c1["mode"] == "i2v"
    assert c1["first_kind"] == "last_frame"
    assert c1["missing_still"] is None
    assert "Picture 1" in c1["prompt"]
    assert "Continue from this exact last frame" in c1["prompt"]
    assert "イってらっしゃい" in c1["prompt"]
    # chain-raw: ③ fit does nothing, even on the last clip.
    c_last = prepare_story_clip(chain, n - 1, last_frame="x.png", stills_dir=tmp_path, fit_scene=True)
    assert c_last["fit_scene"] is False
    assert FINAL_SCENE_LINE not in c_last["prompt"]
    # No last frame yet (clip 0 or a broken chain) → hard fallback to T2V, not an error.
    c1_nolast = prepare_story_clip(chain, 1, last_frame=None, stills_dir=tmp_path, force_t2v=True)
    assert c1_nolast["mode"] == "t2v"

    rewrite = apply_story_play(story, "chain_rewrite")
    r0 = prepare_story_clip(rewrite, 0, last_frame=None, stills_dir=tmp_path, force_t2v=True)
    assert r0["mode"] == "t2v"
    assert "opening of one continuous long take" in r0["prompt"]
    assert r0["prompt"].startswith("PENISLORA, DY\n")
    assert "Picture 1" not in r0["prompt"]
    r1 = prepare_story_clip(rewrite, 1, last_frame="h3_chain_0.png", stills_dir=tmp_path, force_t2v=True)
    assert r1["mode"] == "i2v" and r1["first_kind"] == "last_frame"
    assert FINAL_SCENE_LINE not in r1["prompt"]
    r_mid = prepare_story_clip(rewrite, 5, last_frame="x.png", stills_dir=tmp_path, fit_scene=True)
    assert r_mid["fit_scene"] is False
    assert FINAL_SCENE_LINE not in r_mid["prompt"]
    r_last = prepare_story_clip(rewrite, n - 1, last_frame="x.png", stills_dir=tmp_path, fit_scene=True)
    assert r_last["fit_scene"] is True
    assert FINAL_SCENE_LINE in r_last["prompt"]
    assert "Picture 1" in r_last["prompt"]
    assert r_last["mode"] == "i2v"
    r_last_off = prepare_story_clip(rewrite, n - 1, last_frame="x.png", stills_dir=tmp_path, fit_scene=False)
    assert FINAL_SCENE_LINE not in r_last_off["prompt"]

    # Dedicated: last_frame is never used; ③ fit only touches still-based I2V.
    ded = apply_story_play(story, "dedicated")
    d1 = prepare_story_clip(ded, 1, last_frame="h3_chain_0.png", stills_dir=tmp_path, fit_scene=True)
    assert d1["mode"] == "t2v" and d1["first_kind"] == "t2v"
    assert d1["fit_scene"] is False
    assert DEDICATED_SCENE_IMAGE_LINE not in d1["prompt"]
    (tmp_path / "01-hall.jpg").write_bytes(b"fake-jpg")
    d0 = prepare_story_clip(ded, 0, last_frame=None, stills_dir=tmp_path, fit_scene=True)
    assert d0["mode"] == "i2v" and d0["first_kind"] == "still"
    assert d0["fit_scene"] is True
    assert DEDICATED_SCENE_IMAGE_LINE in d0["prompt"]
    assert FINAL_SCENE_LINE not in d0["prompt"]
    assert "Continue from this exact last frame" not in d0["prompt"]
    assert "opening of one continuous long take" not in d0["prompt"]
    d0_off = prepare_story_clip(ded, 0, last_frame=None, stills_dir=tmp_path, fit_scene=False)
    assert DEDICATED_SCENE_IMAGE_LINE not in d0_off["prompt"]
    assert "Picture 1" in d0_off["prompt"]
    # chain play prefers the last frame over a Drive still on clip 2+.
    (tmp_path / "02-ittekimasu.jpg").write_bytes(b"fake-jpg")
    c1_still = prepare_story_clip(chain, 1, last_frame="h3_chain_0.png", stills_dir=tmp_path)
    assert c1_still["first_kind"] == "last_frame"
    assert c1_still["still_path"] is None


def test_should_fit_scene_image_prompt_rules():
    from h3_lora_studio import should_fit_scene_image_prompt as fit

    assert fit(fit=False, mode="i2v", clip_index=0, clip_count=1) is False
    assert fit(fit=True, mode="t2v", clip_index=0, clip_count=1) is False
    # single photo I2V
    assert fit(fit=True, mode="i2v", clip_index=0, clip_count=1) is True
    # normal chain: last clip only, never the first T2V→I2V join (clip_index 1)
    assert fit(fit=True, mode="i2v", clip_index=1, clip_count=2, chain=True) is False
    assert fit(fit=True, mode="i2v", clip_index=1, clip_count=6, chain=True) is False
    assert fit(fit=True, mode="i2v", clip_index=3, clip_count=6, chain=True) is False
    assert fit(fit=True, mode="i2v", clip_index=5, clip_count=6, chain=True) is True
    assert fit(fit=True, mode="i2v", clip_index=0, clip_count=6, chain=True) is False
    # dedicated story: still-based clips (prepare_story_clip checks the still itself)
    assert fit(fit=True, mode="i2v", clip_index=0, clip_count=12, is_story=True, seamless=False) is True
    # chain-raw story: never
    assert fit(fit=True, mode="i2v", clip_index=11, clip_count=12, is_story=True, seamless=True, rewrite_chain_prompts=False) is False
    # chain_rewrite story: last only
    assert fit(fit=True, mode="i2v", clip_index=11, clip_count=12, is_story=True, seamless=True, rewrite_chain_prompts=True) is True
    assert fit(fit=True, mode="i2v", clip_index=1, clip_count=12, is_story=True, seamless=True, rewrite_chain_prompts=True) is False


def test_rewrite_final_and_dedicated_scene_prompts():
    from h3_lora_studio import (
        CHAIN_CONTINUE_LINE,
        DEDICATED_SCENE_IMAGE_LINE,
        FINAL_SCENE_LINE,
        FINAL_SCENE_TARGET_LINE,
        I2V_PICTURE1_HEADER,
        rewrite_dedicated_scene_i2v_prompt,
        rewrite_final_scene_i2v_prompt,
    )

    base = "PENISLORA, DY\nNew 10-second take. Hard cut. Do not copy the previous clip.\nTwo adult women, 22, talk in a kitchen."
    scene = I2V_PICTURE1_HEADER + "bl0w_j0b, PENISLORA\nAlready a blow job. No man appears."
    out = rewrite_final_scene_i2v_prompt(base, scene_prompt=scene)
    assert out.startswith("PENISLORA, DY\n")
    assert CHAIN_CONTINUE_LINE in out
    assert FINAL_SCENE_LINE in out
    assert FINAL_SCENE_TARGET_LINE in out
    assert "Already a blow job" in out
    assert "Picture 1" in out
    assert out.count("fully referenced") == 1
    assert "Hard cut" not in out
    assert "Do not copy the previous clip" not in out
    assert rewrite_final_scene_i2v_prompt(out, scene_prompt=scene) == out
    plain = rewrite_final_scene_i2v_prompt("She keeps walking.")
    assert FINAL_SCENE_LINE in plain and "Picture 1" in plain and FINAL_SCENE_TARGET_LINE not in plain

    ded = rewrite_dedicated_scene_i2v_prompt("PENISLORA, DY\nsubject_definitions:\nAya: Adult Japanese woman, 22.")
    assert ded.startswith("PENISLORA, DY\n")
    assert DEDICATED_SCENE_IMAGE_LINE in ded
    assert "Picture 1" in ded
    assert "Continue from this exact last frame" not in ded
    assert FINAL_SCENE_LINE not in ded
    assert "this clip's own still" in DEDICATED_SCENE_IMAGE_LINE
    assert "own cut" in DEDICATED_SCENE_IMAGE_LINE
    assert "Do not continue from a previous last frame" in DEDICATED_SCENE_IMAGE_LINE
    locked = I2V_PICTURE1_HEADER + "Aya waits in the hall."
    ded2 = rewrite_dedicated_scene_i2v_prompt(locked)
    assert ded2.count("fully referenced") == 1
    assert ded2.index("fully referenced") < ded2.index(DEDICATED_SCENE_IMAGE_LINE) < ded2.index("Aya waits")
    assert rewrite_dedicated_scene_i2v_prompt(ded2) == ded2


def _check_pack_common(story, sid, tmp_path):
    from h3_lora_studio import (
        ACT_SITUATIONS,
        prepare_story_clip,
        situation_ids,
        spoken_lines,
        story_canvas_wh,
        validate_story_follow,
    )

    assert story["id"] == sid
    assert story["kind"] == "chain"
    assert story["seamless"] is True
    assert "rewrite_chain_prompts" not in story
    assert story["min_age"] >= 21
    assert story["clip_s"] == 10
    durs = [float(c.get("duration_s") or story["clip_s"]) for c in story["clips"]]
    assert all(d in (10.0, 15.0) for d in durs)
    assert story["duration_s"] == sum(durs)
    assert story["canvas"] == {"width": 576, "height": 1024, "aspect": "9:16"}
    assert story_canvas_wh(story) == (576, 1024)
    assert validate_story_follow(story) == []
    assert story["clips"][0]["start"] == "still_or_t2v"
    assert all(c["start"] == "continue" for c in story["clips"][1:])
    listed = set(situation_ids(sid))
    assert listed == set(story["download"])
    prev = None
    prev_stack = None
    for i, clip in enumerate(story["clips"]):
        prompt = clip["prompt"]
        lines = spoken_lines(prompt)
        assert "hmmotion" not in prompt.lower()
        dur = float(clip.get("duration_s") or story["clip_s"])
        if dur == 15:
            assert "15-second take" in prompt
            assert "10-second take" not in prompt
            assert not lines
        else:
            assert dur == 10
            assert "15-second" not in prompt
        assert "Hard cut" not in prompt
        assert "Do not copy the previous clip" not in prompt
        assert "576x1024" in prompt
        assert len(set(lines)) <= 1, (sid, i + 1, lines)
        if clip["situation"] in ACT_SITUATIONS:
            assert not lines
            assert "close" in prompt.lower()
        if lines:
            assert clip["situation"] == "futa_visible"
            assert "LIP SYNC" in prompt
        if "Clear futanari" in prompt:
            assert "Penis plus vagina, never balls" in prompt
            assert "no scrotum" in prompt
        planned = prepare_story_clip(
            story, i, last_frame=("h3_chain_%d.png" % (i - 1)) if i else None, stills_dir=tmp_path, prev_situation=prev, prev_stack=prev_stack
        )
        prev = planned["situation"]
        prev_stack = planned["stack"]
        assert {row["id"] for row in planned["stack"]} <= listed
        assert planned["width"] == 576 and planned["height"] == 1024
        assert planned["duration_s"] == dur
        assert planned["seamless"] is True and planned["rewrite_chain_prompts"] is True
        if i == 0:
            assert planned["mode"] == "t2v"
            assert "opening of one continuous long take" in planned["prompt"]
            assert "Picture 1" not in planned["prompt"]
        else:
            assert planned["mode"] == "i2v"
            assert planned["first_kind"] == "last_frame"
            assert planned["missing_still"] is None
            assert "Picture 1" in planned["prompt"]
            assert "Continue from this exact last frame" in planned["prompt"]
        if planned["situation"] == "futa_visible":
            _check_visible_plan(planned, prompt)
        for spoken in lines:
            assert spoken in planned["prompt"]
    return story


def test_sales_visit_pack_eight_clips_aya_mouth(tmp_path):
    from h3_lora_studio import load_story, spoken_lines

    story = _check_pack_common(load_story("sales-visit-60s"), "sales-visit-60s", tmp_path)
    assert story.get("spoken_no_kanji") is True
    assert len(story["clips"]) == 8
    assert story["duration_s"] == 85
    assert [float(c["duration_s"]) for c in story["clips"]] == [10, 10, 10, 10, 10, 15, 10, 10]
    assert [c["situation"] for c in story["clips"]] == (
        ["futa_visible"] * 3 + ["oral", "futa_visible", "oral", "oral_creampie", "futa_visible"]
    )
    want = [
        "こんにちは。おミズをおトドケにきました",
        "オソいわよ",
        "ハヤクおミズちょうだい",
        None,
        "あー、シミる",
        None,
        None,
        "ありがとうございました",
    ]
    for clip, line in zip(story["clips"], want):
        got = spoken_lines(clip["prompt"])
        assert (got[0] if got else None) == line, clip["label"]
        assert "Saleswoman: Adult Japanese woman, 25" in clip["prompt"]
        assert "Aya: Adult Japanese woman, 22" in clip["prompt"]
        assert "NO penis" in clip["prompt"]
        assert "no testicles" in clip["prompt"]
        assert "no scrotum" in clip["prompt"]
        assert "Penis plus vagina, never balls" in clip["prompt"]
        assert "Sayaka" not in clip["prompt"] and "Rei" not in clip["prompt"] and "Madoka" not in clip["prompt"].replace("not Madoka", "")
        assert "clinic" not in clip["prompt"].lower()
        assert "exam room" not in clip["prompt"].lower()
    assert "already kneeling" in story["clips"][2]["prompt"]
    assert "Then she kneels" not in story["clips"][2]["prompt"]
    assert "yellow" in story["clips"][3]["prompt"].lower()
    assert "BASE" in story["clips"][5]["prompt"]
    assert story["clips"][5]["duration_s"] == 15
    assert "CUMOUF" in story["clips"][6]["prompt"] or "ejaculat" in story["clips"][6]["prompt"].lower()
    assert "cumouf-h3" in story["download"]
    assert "sticky" in story["clips"][6]["prompt"].lower() or "viscous" in story["clips"][6]["prompt"].lower()


def test_checkup_pack_nine_clips_doorway_kana_lines(tmp_path):
    from h3_lora_studio import _KANJI_RE, load_story, spoken_lines

    story = _check_pack_common(load_story("checkup-100s"), "checkup-100s", tmp_path)
    assert story["spoken_no_kanji"] is True
    assert len(story["clips"]) == 9
    assert story["duration_s"] == 100
    assert [float(c["duration_s"]) for c in story["clips"]] == (
        [10, 10, 10, 15, 10, 10, 15, 10, 10]
    )
    assert [c["situation"] for c in story["clips"]] == (
        ["futa_visible"] * 6 + ["oral", "oral_creampie", "futa_visible"]
    )
    want = [
        "こんにちは。テイキケンシンにきました",
        "あ…はい、ヨロシクオネガイします",
        "では、シツレイします",
        None,
        "クチとムネはモンダイないですね",
        "では、つぎはおチンチンのカクニンをします",
        None,
        None,
        "モンダイありますね",
    ]
    for clip, line in zip(story["clips"], want):
        got = spoken_lines(clip["prompt"])
        assert (got[0] if got else None) == line, (clip["label"], got)
        for spoken in got:
            assert not _KANJI_RE.search(spoken), spoken
        assert "Doctor: Adult Japanese woman, 32" in clip["prompt"]
        assert "stethoscope" in clip["prompt"]
        assert "Rei: Adult Japanese woman, 24" in clip["prompt"]
        assert "exam room" not in clip["prompt"].lower()
        assert "genkan" in clip["prompt"].lower() or "door" in clip["prompt"].lower()
    assert "Not a clinic" in story["clips"][0]["prompt"]
    assert "already at the open door" in story["clips"][0]["prompt"]
    kiss = story["clips"][3]["prompt"].lower()
    assert "kiss" in kiss
    assert "breast" in kiss
    assert "both hands" in kiss
    kakunin = story["clips"][5]["prompt"]
    assert "does NOT squat" in kakunin
    assert "begins to squat" not in kakunin
    assert "already squatting" in story["clips"][6]["prompt"]
    assert "CUMOUF" in story["clips"][7]["prompt"] or "ejaculat" in story["clips"][7]["prompt"].lower()
    assert "cumouf-h3" in story["download"]


def test_speech_drops_cinema_locks_japanese_and_unloads_on_stack_change(tmp_path):
    from h3_lora_studio import (
        audio_lock_line,
        drop_speech_face_killers,
        jp_outside_quotes,
        load_story,
        lock_spoken_japanese,
        prepare_story_clip,
        stack_signature,
        strip_audio_lock,
        validate_story_follow,
    )

    stack = [
        {"id": "penis-lora-h3", "strength": 0.7, "strength_model": 0.7},
        {"id": "cinema-dy", "strength": 0.5, "strength_model": 0.5},
    ]
    i2v = drop_speech_face_killers(stack, speaks=True, mode="i2v")
    assert [x["id"] for x in i2v] == ["penis-lora-h3"]
    silent = drop_speech_face_killers(stack, speaks=False, mode="i2v")
    assert [x["id"] for x in silent] == ["penis-lora-h3", "cinema-dy"]
    r2v = drop_speech_face_killers(
        [{"id": "cinema-dy", "strength": 0.5, "strength_model": 0.5}],
        speaks=True,
        mode="r2v",
    )
    assert r2v[0]["id"] == "cinema-dy"
    assert r2v[0]["strength_model"] == 0.35

    locked = lock_spoken_japanese(
        "overall_soundscape:\nClinic hum. Rei speaks, lip-synced: 「こんにちは」. No other speech.\n",
        ["こんにちは"],
    )
    assert locked.index("overall_soundscape:") < locked.index("[AUDIO-LOCK]")
    assert locked.count("「こんにちは」") == 1
    assert "spoken_transcript: once" in locked
    assert "repeat: 0" in locked
    assert "stretch: off" in locked
    assert "プロンプトは読まない" not in locked
    lock_line = next(ln for ln in locked.splitlines() if ln.startswith("[AUDIO-LOCK]"))
    assert "「" not in lock_line
    assert jp_outside_quotes(lock_line) == ""
    silent_lock = lock_spoken_japanese("overall_soundscape:\nKiss. No spoken words.\n", [])
    assert "spoken_transcript: mute" in silent_lock
    assert "誰も話さない" not in silent_lock
    assert "プロンプトは読まない" not in silent_lock
    old = lock_spoken_japanese(
        "overall_soundscape:\n【音声ルール】プロンプトは読まない。英語を音読しない。声に出していいのは日本語の台詞だけ。「こんにちは」英語・中国語・韓国語・ローマ字・意味のわからない音は禁止。台詞のあとに言葉を足さない。余った秒数は無音。口は閉じて部屋の音だけ。\nClinic hum.\n",
        ["こんにちは"],
    )
    assert old.count("[AUDIO-LOCK]") == 1
    assert old.count("「こんにちは」") == 1
    assert "プロンプトは読まない" not in old
    assert lock_spoken_japanese(old, ["こんにちは"]).count("[AUDIO-LOCK]") == 1
    assert audio_lock_line(["こんにちは"]).startswith("[AUDIO-LOCK]")
    assert "「" not in audio_lock_line(["こんにちは"])
    assert "prompt" not in audio_lock_line(["こんにちは"]).lower()
    assert strip_audio_lock(old).count("[AUDIO-LOCK]") == 0

    story = load_story("checkup-100s")
    speech = prepare_story_clip(story, 0, stills_dir=tmp_path)
    assert [row["id"] for row in speech["stack"]] == ["penis-lora-h3"]
    assert speech["stack_changed"] is False
    assert "[AUDIO-LOCK]" in speech["prompt"]
    assert speech["prompt"].count("「こんにちは。テイキケンシンにきました」") == 1
    assert "repeat: 0" in speech["prompt"]
    assert "こんにちは" in speech["prompt"]
    assert "プロンプトは読まない" not in speech["prompt"]
    assert "DY" not in speech["prompt"].split("\n", 1)[0]
    next_speech = prepare_story_clip(
        story, 1, last_frame="x.png", stills_dir=tmp_path, prev_situation=speech["situation"], prev_stack=speech["stack"]
    )
    assert next_speech["situation"] == "futa_visible"
    assert next_speech["stack_changed"] is False
    assert next_speech["mode"] == "i2v"
    assert next_speech["prompt"].index("Picture 1") < next_speech["prompt"].index("[AUDIO-LOCK]")
    kiss = prepare_story_clip(
        story, 3, last_frame="x.png", stills_dir=tmp_path, prev_situation=next_speech["situation"], prev_stack=next_speech["stack"]
    )
    assert kiss["situation"] == "futa_visible"
    assert kiss["stack_changed"] is True
    assert stack_signature(kiss["stack"]) != stack_signature(speech["stack"])
    assert [row["id"] for row in kiss["stack"]] == ["penis-lora-h3", "larry-v4", "cinema-dy"]
    assert "spoken_transcript: mute" in kiss["prompt"]
    assert "誰も話さない" not in kiss["prompt"]
    oral = prepare_story_clip(
        story, 6, last_frame="x.png", stills_dir=tmp_path, prev_situation=kiss["situation"], prev_stack=kiss["stack"]
    )
    assert oral["situation"] == "oral"
    assert oral["stack_changed"] is True
    assert "blowjob-h3" in [row["id"] for row in oral["stack"]]

    bad = dict(story)
    clip0 = dict(story["clips"][0])
    clip0["prompt"] = clip0["prompt"].replace("こんにちは", "hello")
    bad["clips"] = [clip0, *story["clips"][1:]]
    errs = validate_story_follow(bad)
    assert any("Japanese only" in e for e in errs)


def test_last_stop_pack_four_clips_rei_seated(tmp_path):
    from h3_lora_studio import _KANJI_RE, load_story, spoken_lines

    story = _check_pack_common(load_story("last-stop-40s"), "last-stop-40s", tmp_path)
    assert story["spoken_no_kanji"] is True
    assert len(story["clips"]) == 4
    assert [c["situation"] for c in story["clips"]] == ["futa_visible", "oral", "oral_creampie", "futa_visible"]
    want = ["シュウテンです、オキテください", None, None, "オキましたか？オキャクサン、シュウテンだからオリテください"]
    for clip, line in zip(story["clips"], want):
        got = spoken_lines(clip["prompt"])
        assert (got[0] if got else None) == line, clip["label"]
        for spoken in got:
            assert not _KANJI_RE.search(spoken), spoken
        assert "Conductor: Adult Japanese woman, 29" in clip["prompt"]
        assert "whistle" in clip["prompt"]
        assert "seated" in clip["prompt"].lower() or "sits" in clip["prompt"].lower()
    assert "does NOT wake" in story["clips"][0]["prompt"]
    assert "flutter open" in story["clips"][1]["prompt"]
    assert "conductor again" in story["clips"][3]["prompt"]


def test_validate_story_follow_spoken_no_kanji():
    from h3_lora_studio import _KANJI_RE, validate_story_follow

    assert _KANJI_RE.pattern == "[\\u4e00-\\u9fff]"
    kanji = {
        "clip_s": 10,
        "spoken_no_kanji": True,
        "clips": [{"duration_s": 10, "situation": "futa_visible", "prompt": "LIP SYNC: face large.\n「定期検診に来ました」"}],
    }
    errs = validate_story_follow(kanji)
    assert any("kana" in e for e in errs)
    kana = {
        "clip_s": 10,
        "spoken_no_kanji": True,
        "clips": [{"duration_s": 10, "situation": "futa_visible", "prompt": "LIP SYNC: face large.\n「テイキケンシンにきました」"}],
    }
    assert validate_story_follow(kana) == []
    # 台詞の漢字はフラグ無しでも通さない（読み間違え防止）。
    free = dict(kanji)
    free.pop("spoken_no_kanji")
    assert any("kana" in e for e in validate_story_follow(free))
    two = {
        "clip_s": 10,
        "clips": [{"duration_s": 10, "situation": "futa_visible", "prompt": "LIP SYNC: face large.\n「はい」「いいえ」"}],
    }
    assert any("one spoken line only" in e for e in validate_story_follow(two))
    missing = {
        "clip_s": 10,
        "clips": [{"duration_s": 10, "situation": "futa_visible", "prompt": "LIP SYNC: face large.\nClear futanari. Erect 20cm.\n「ほしい」"}],
    }
    errs = validate_story_follow(missing)
    assert any("penis plus vagina" in e for e in errs)
    assert any("no scrotum" in e for e in errs)


def test_lock_futa_anatomy_default_and_never_futanari():
    from h3_lora_studio import lock_futa_anatomy

    old = "Clear futanari with a penis. pale shaft, pink glans, no testicles. Not a man."
    out = lock_futa_anatomy(old)
    assert "Penis plus vagina, never balls" in out
    assert "no scrotum" in out
    assert "Hairless female pussy at the base of the shaft" in out
    assert lock_futa_anatomy(out) == out
    never = "Aya: Adult Japanese woman, 22, fully nude, hairless, NO penis, NEVER futanari."
    assert lock_futa_anatomy(never) == never
    hanging = lock_futa_anatomy("futanari with a penis that hangs unused")
    assert "Her penis hangs unused" in hanging
    assert "never balls that" not in hanging


def test_all_stories_and_packs_futa_anatomy_and_spoken_kana():
    from h3_lora_studio import (
        CHAIN_PACK_IDS,
        STORY_IDS,
        _KANJI_RE,
        compact_story_prompt,
        load_story,
        spoken_lines,
        validate_story_follow,
    )

    for sid in sorted(STORY_IDS | CHAIN_PACK_IDS):
        story = load_story(sid)
        assert story.get("spoken_no_kanji") is True, sid
        assert validate_story_follow(story) == [], sid
        for i, clip in enumerate(story["clips"]):
            prompt = clip["prompt"]
            where = f"{sid} clip {i + 1}"
            for spoken in spoken_lines(prompt):
                assert not _KANJI_RE.search(spoken), (where, spoken)
                assert not re.search(r"[A-Za-z]", spoken), (where, spoken)
            if "Clear futanari" in prompt:
                assert "Penis plus vagina, never balls" in prompt, where
                assert "no scrotum" in prompt, where
            compact = compact_story_prompt(prompt)
            if "Clear futanari" in compact:
                assert "Penis plus vagina, never balls" in compact, where
                assert "no scrotum" in compact, where
            for name in ("Aya", "Sayaka"):
                match = re.search(rf"^{name}: Adult[^\n]*", prompt, re.M)
                if match:
                    line = match.group(0)
                    assert "NO penis" in line or "NEVER futanari" in line, (where, name)
                    assert "Clear futanari" not in line, (where, name)
                    assert "futanari:" not in line, (where, name)


def test_notebook_story_play_flow():
    writer = Path(__file__).resolve().parent / "_write_lora_studio_nb.py"
    src = writer.read_text(encoding="utf-8")
    nb_path = Path(__file__).resolve().parents[1] / "minimax_h3_lora_studio.ipynb"
    blob = nb_path.read_text(encoding="utf-8")
    nb = json.loads(blob)
    cell3 = "".join(nb["cells"][6]["source"])
    cell2 = "".join(nb["cells"][4]["source"])
    md0 = "".join(nb["cells"][0]["source"])
    assert 'やりたいシーン = "登校（専用）"' in cell3
    assert '今使うシーン = "登校（専用）"' in cell2
    for suffix in ("（専用）", "（つなぐ）", "（つなぐ修）", "（参照つなぐ）", "（参照つなぐ修）"):
        assert f'"登校{suffix}"' in cell3
    for pack in ("訪問販売", "定期検診", "終点", "カフェ", "車内販売", "赤信号", "ヨガ", "背中流し", "カラオケ", "ランドリー", "講義机", "キャンプ", "花火"):
        for suffix in ("（専用）", "（つなぐ）", "（つなぐ修）", "（参照つなぐ）", "（参照つなぐ修）"):
            assert f'"{pack}{suffix}"' in cell3, pack + suffix
    # legacy long pack labels are aliases only, not dropdown rows
    assert '"訪問販売60秒（つなぐ）"' not in cell3 and '"終点40秒（つなぐ）"' not in cell3
    # order: 55 story rows, then 13 packs × 5, then 短編集, then the act scenes
    assert cell3.index('"縁側（参照つなぐ修）"') < cell3.index('"訪問販売（専用）"') < cell3.index('"花火（参照つなぐ修）"') < cell3.index('"短編集（参照）"') < cell3.index('"アナル挿入（画質）"')
    assert cell3.index('"普通（エロなし）"') < cell3.index('"帰宅（専用）"')
    from h3_lora_studio import CHAIN_PACK_ORDER, STORY_ORDER  # noqa: E402

    m = re.search(r'やりたいシーン = "[^"]+"  #@param (\[.*?\])\n', cell3)
    opts = json.loads(m.group(1))
    assert len(opts) == 4 + 5 * len(STORY_ORDER) + 5 * len(CHAIN_PACK_ORDER) + 1 + 23
    assert len(set(opts)) == len(opts)
    for opt in opts:
        resolve_situation(opt)
    assert "resolve_story_play" in src and "apply_story_play" in src
    assert "STORY_PLAY = resolve_story_play(やりたいシーン)" in src
    assert "STORY = apply_story_play(STORY, STORY_PLAY)" in src
    assert "is_chain_pack" in src
    assert "最終シーン合わせ = False  #@param" in src
    assert 'last_now = first_name if (STORY.get("seamless") and CLIP_INDEX > 0) else None' in src
    assert "last_frame=last_now" in src
    assert "fit_scene=fit_now" in src
    assert "FIT_CLIP0 = bool(最終シーン合わせ and not STORY_SEAMLESS and not STORY.get(\"use_cast_ref\"))" in src
    assert "fit_scene=FIT_CLIP0" in src
    assert "rewrite_chain_prompts=STORY_REWRITE" in src
    assert "is_story=False, chain=CHAIN" in src
    assert "rewrite_final_scene_i2v_prompt(GRAPH_PROMPT, scene_prompt=" in src
    assert "if CHAIN and not STORY:\n    prompt = rewrite_chain_opening_prompt(prompt)" in src
    assert "if CLIP_INDEX + 1 < len(CLIPS) and CHAIN:" in src
    assert "if CLIP_INDEX + 1 < len(CLIPS) and not STORY:" not in src
    assert "CHAIN = STORY_SEAMLESS" in src
    assert "CHAIN = False" in src
    assert "を（専用）で選んでいるので「つなぐ」は使いません" in src
    assert "if is_story(やりたいシーン) or is_chain_pack(やりたいシーン):\n    STORY_PLAY = resolve_story_play(やりたいシーン)" in src
    assert 'getattr(_h3_studio, "resolve_story_play", None)' in src
    assert 'getattr(_h3_studio, "apply_story_play", None)' in src
    assert 'getattr(_h3_studio, "rewrite_dedicated_scene_i2v_prompt", None)' in src
    assert '"last-stop-40s" not in getattr(_h3_studio, "CHAIN_PACK_IDS", set())' in src
    assert '"fireworks-50s" not in getattr(_h3_studio, "CHAIN_PACK_IDS", set())' in src
    for pid in CHAIN_PACK_ORDER:
        assert f"h3-lora-studio/stories/{pid}.json" in src, pid
        assert f'"{pid}"' in cell2, pid
    assert '"sales-visit-60s", "checkup-100s", "last-stop-40s"' in cell2
    assert '"カフェ（専用）"' in cell2 and '"花火（専用）"' in cell2
    assert "専用（専用）" in md0 and "専用（つなぐ）" in md0 and "専用（つなぐ修）" in md0
    assert "名前付きパック（専用 / つなぐ / つなぐ修 / 参照つなぐ / 参照つなぐ修）" in md0
    assert "旧名「訪問販売60秒（つなぐ）」" in md0
    assert "登校（専用）" in md0
    assert "竿＋マンコ、金玉なし" in md0
    assert "「」の中はカタカナ" in md0
    assert "漢字のまま" not in md0
    assert "h3-20260907-audio-2" in cell2
    assert "本ごとの秒:" in src
    assert "cast_dir=CAST_DIR" in src
    assert "is_anthology" in src
    assert "短編集（参照）" in cell3
    assert "pick_cast_still" in src
    assert "pick_cast_stills" in src
    assert "lock_r2v_cast_prompt" in src
    assert "build_r2v_graph" in src
    assert "r2v_download_jobs" in src
    assert "STORY_PLAY_REF_CHAIN" in src
    assert "shorts-immoral" in cell2
    assert "専用（参照つなぐ）" in md0
    assert "短編集（参照）" in md0
    assert "R2V" in md0


def _write_cast_stills(root):
    root.mkdir(parents=True, exist_ok=True)
    for name in (
        "sayaka-bust",
        "sayaka-full",
        "rei-bust",
        "rei-full",
        "aya-bust",
        "aya-full",
        "madoka-bust",
        "madoka-full",
    ):
        (root / f"{name}.jpg").write_bytes(b"fake-jpg")
    return root


def test_pick_cast_still_and_ref_chain(tmp_path):
    from h3_lora_studio import (
        apply_story_play,
        load_story,
        pick_cast_lead,
        pick_cast_still,
        pick_cast_stills,
        prepare_story_clip,
    )

    cast = _write_cast_stills(tmp_path / "cast")
    oral = {"situation": "oral", "names": ["aya", "rei"], "prompt": "Already oral. medium-close."}
    person, kind = pick_cast_lead(oral)
    assert (person, kind) == ("aya", "bust")
    still = pick_cast_still(oral, cast)
    assert still.name == "aya-bust.jpg"
    paths = pick_cast_stills(oral, cast)
    assert [p.name for p in paths] == ["aya-bust.jpg", "aya-full.jpg", "rei-bust.jpg", "rei-full.jpg"]
    sex = {"situation": "futa_sex", "names": ["rei", "aya"], "prompt": "hmmotion already in joining"}
    assert pick_cast_lead(sex) == ("rei", "full")
    dog = {"situation": "doggy", "names": ["aya"], "prompt": "already in from behind joining"}
    assert pick_cast_lead(dog) == ("aya", "full")
    try:
        pick_cast_still(oral, tmp_path / "missing")
    except SystemExit as exc:
        assert "input/cast" in str(exc) or "8" in str(exc) or "人物" in str(exc)
    else:
        raise AssertionError("expected SystemExit")

    story = apply_story_play(load_story("commute-120s"), "ref_chain")
    assert story["use_cast_ref"] is True
    p0 = prepare_story_clip(story, 0, stills_dir=tmp_path, cast_dir=cast, force_t2v=True)
    assert p0["mode"] == "r2v"
    assert p0["first_kind"] == "cast"
    assert p0["still_path"].name.endswith(".jpg")
    assert p0["still_paths"]
    assert "ROLE LOCK" in p0["prompt"]
    assert "at 0.00 seconds" not in p0["prompt"]
    assert "penis-lora-h3" not in [row["id"] for row in p0["stack"]]
    assert all(row.get("arch") != "fl2va" for row in p0["stack"])
    p1 = prepare_story_clip(story, 1, last_frame="h3_chain_0.png", stills_dir=tmp_path, cast_dir=cast)
    assert p1["first_kind"] == "last_frame"
    assert p1["mode"] == "i2v"
    assert "penis-lora-h3" in [row["id"] for row in p1["stack"]]
    raw = apply_story_play(load_story("commute-120s"), "chain")
    c0 = prepare_story_clip(raw, 0, stills_dir=tmp_path, force_t2v=True)
    assert c0["first_kind"] == "t2v"


def test_anthology_shorts_immoral(tmp_path):
    from h3_lora_studio import (
        is_anthology,
        is_story,
        load_story,
        prepare_story_clip,
        situation_ids,
        validate_story_follow,
    )

    assert is_anthology("短編集（参照）")
    assert not is_story("短編集（参照）")
    assert "aftermidnight-ref2va" in situation_ids("shorts-immoral")
    assert "blowjob-h3" in situation_ids("shorts-immoral")
    assert "minimax-h3-turbo-ref2v-4step" in situation_ids("shorts-immoral")
    assert "synth-pussy-h3" not in situation_ids("shorts-immoral")
    assert "penis-lora-h3" not in situation_ids("shorts-immoral")
    assert "larry-v4" not in situation_ids("shorts-immoral")
    assert "futa-h3-v51" not in situation_ids("shorts-immoral")
    story = load_story("shorts-immoral")
    assert story["kind"] == "anthology"
    assert story["clip_s"] == 15
    assert len(story["clips"]) == 12
    assert story["duration_s"] == 180
    assert validate_story_follow(story) == []
    want = [
        "oral",
        "oral_creampie",
        "oral",
        "cunnilingus_futa",
        "futa_sex",
        "oral",
        "oral_creampie",
        "oral",
        "futa_sex",
        "futa_sex",
        "oral",
        "doggy",
    ]
    assert [c["situation"] for c in story["clips"]] == want
    for clip in story["clips"]:
        assert float(clip["duration_s"]) == 15
        assert "15-second take" in clip["prompt"]
        if "Clear futanari" in clip["prompt"]:
            assert "Penis plus vagina, never balls" in clip["prompt"]
            assert "no scrotum" in clip["prompt"]
        assert "Aya:" not in clip["prompt"] or "NO penis" in clip["prompt"] or "NEVER futanari" in clip["prompt"]
    cast = _write_cast_stills(tmp_path / "cast")
    prev = None
    prev_stack = None
    for i, clip in enumerate(story["clips"]):
        planned = prepare_story_clip(
            story,
            i,
            last_frame="h3_chain_0.png",
            stills_dir=tmp_path,
            cast_dir=cast,
            prev_situation=prev,
            prev_stack=prev_stack,
            force_t2v=True,
        )
        prev = planned["situation"]
        prev_stack = planned["stack"]
        assert planned["mode"] == "r2v"
        assert planned["first_kind"] == "cast"
        assert planned["duration_s"] == 15
        assert "ROLE LOCK" in planned["prompt"]
        assert "at 0.00 seconds" not in planned["prompt"]
        ids = [row["id"] for row in planned["stack"]]
        assert "futa-h3-v51" not in ids
        assert "penis-lora-h3" not in ids
        assert "synth-pussy-h3" not in ids
        assert "larry-v4" not in ids
        assert all(row.get("arch") != "fl2va" for row in planned["stack"])
        if planned["situation"] == "oral":
            assert "blowjob-h3" in ids
            assert "minimax-h3-turbo-ref2v-4step" in ids or not planned.get("turbo")
        if planned["situation"] == "oral_creampie":
            assert ids == ["aftermidnight-ref2va"]
        if planned["situation"] == "futa_sex":
            assert ids == ["aftermidnight-ref2va"]
            assert clip["prompt"].startswith("hmmotion, PENISLORA")
            assert "hmmotion" in planned["prompt"]
        if planned["situation"] == "doggy":
            assert ids == ["aftermidnight-ref2va"]
        if planned["situation"] == "cunnilingus_futa":
            assert ids == ["aftermidnight-ref2va"]
            assert "blowjob-h3" not in ids
