import json
import sys
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from h3_lora_studio import (
    apply_user_prompt,
    civitai_download_url,
    civitai_token,
    civitai_token_help,
    clamp_studio_duration,
    concat_studio_clips,
    continue_chain_prompt,
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
    situation_ids,
    studio_clip_plan,
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
    assert resolve_situation("レズビアンクンニ") == "lesbian_cunnilingus"
    assert resolve_situation("性器を広げる") == "pussy_spread"
    assert resolve_situation("レズ＋広げる") == "lesbian_spread"
    assert resolve_situation("セックス（女体）") == "futa_sex"
    assert resolve_situation("ふたなりセックス") == "futa_sex"
    assert resolve_situation("アナルセックス（女体）") == "futa_anal"
    assert resolve_situation("アナルセックス") == "futa_anal"
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
    general = explain_choice("汎用エロ", "テキストから（写真なし）")
    assert "Larry" in general
    assert "12step" in general
    assert "LightX2V 12" not in general


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
    assert "homage=homage" in blob
    assert "validate_studio_i2v_prompt" in blob
    assert "validate_motion_ad_prompt(prompt, with_last_frame=False)" in blob
    assert "写真用の文が文章欄に残っています" in src
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
    assert clamp_studio_duration(61, chain=True) == 60.0
    assert clamp_studio_duration("nope", chain=True) == 16.0
    assert situation_ids("general_sex") == ["hmnsfw-aio-v25", "larry-v4"]
    assert situation_ids("riding") == ["hmnsfw-aio-v25", "larry-v4"]
    assert situation_ids("preview") == ["hmnsfw-aio-v25", "minimax-h3-turbo-fl2v-4step"]
    assert situation_ids("futa_sex") == ["hmnsfw-aio-v25", "penis-lora-h3", "synth-pussy-h3"]
    assert situation_ids("futa_blowjob") == ["blowjob-h3", "penis-lora-h3", "synth-pussy-h3", "larry-v4"]
    assert situation_ids("futa_anal") == ["anal-penetration-coachbate", "penis-lora-h3", "synth-pussy-h3"]
    assert situation_ids("oral") == ["blowjob-h3", "penis-lora-h3", "larry-v4"]


def test_studio_clip_plan_chain_stays_under_sixteen():
    assert studio_clip_plan(15) == [15.0]
    assert studio_clip_plan(16, chain=True) == [10.0, 6.0]
    assert studio_clip_plan(25, chain=True) == [10.0, 15.0]
    assert studio_clip_plan(26, chain=True) == [10.0, 10.0, 6.0]
    assert studio_clip_plan(60, chain=True) == [10.0] * 6
    assert all(4 <= c <= 15 for c in studio_clip_plan(60, chain=True))
    total, clips, chain = resolve_studio_length(30, "つなぐ（16〜60秒）")
    assert chain is True
    assert total == 30.0
    assert clips == [10.0, 10.0, 10.0]
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
    structured = next_chain_prompt(
        1,
        first_prompt=first,
        prev_prompt=first,
        extras=["subject_definitions:\nAya\n\nintegrated_multimodal_description:\nKiss only. Aya stays seated."],
    )
    assert structured.count("integrated_multimodal_description:") == 1
    assert "Kiss only" in structured
    assert "Picture 1" in structured


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
    assert "つなぐ（16〜60秒）" in src
    assert "concat_studio_clips" in src
    assert "continue_chain_prompt" in src
    assert "next_chain_prompt" in src
    assert "つなぎ2" in src
    assert "CHAIN_EXTRAS" in src
    assert "homage = bool(VANILLA and not CUSTOM_PROMPT and CLIP_INDEX == 0)" in src
    assert "AIO 0.8 + Larry 0.5 / 12step" in src
    assert "LightX2V 0.5 / 12 step" not in src
    assert "DURATION, CLIPS, CHAIN = resolve_studio_length" in blob
    assert "duration_s=CLIP_DURATION" in blob
    assert "duration_s=float(秒数)" not in blob
    assert "つなぐ（16〜60秒）" in blob
    assert "continue_chain_prompt" in blob
    assert "next_chain_prompt" in blob
    assert "つなぎ2" in blob
    assert "AIO 0.8 + Larry 0.5 / 12step" in blob
