import json
import os
import re
import sys
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from h3_lora_studio import (
    apply_user_prompt,
    cap_fl2va_clip_s,
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
    rewrite_take_seconds,
    strip_chain_restart_language,
    situation_ids,
    studio_clip_plan,
    load_story,
    prepare_story_clip,
    STORY_IDS,
    CHAIN_PACK_IDS,
)
from h3_t2v import CANVAS_9_16, DEFAULT_T2V_PROMPT, assert_t2v_graph, build_t2v_graph


def _check_visible_plan(planned, clip_prompt):
    """futa_visible: spoken 「line」 clips drop Larry (jaw melt); walk/kiss keep thin Larry 8step."""
    from h3_lora_studio import soundscape_text

    ids = [row["id"] for row in planned["stack"]]
    sound = soundscape_text(planned["prompt"])
    assert "lip-synced" not in sound.lower()
    assert "no other speech" not in sound.lower()
    assert "no spoken words" not in sound.lower()
    assert "spoken_transcript" not in planned["prompt"]
    assert "other_text" not in planned["prompt"]
    assert "プロンプトは読まない" not in planned["prompt"]
    assert "台詞だけ" not in planned["prompt"]
    assert "[AUDIO-LOCK]" not in planned["prompt"]
    if "「" in clip_prompt:
        assert ids == ["penis-lora-h3", "synth-pussy-h3"], ids
        assert planned["cfg"]["turbo"] is False
        assert planned["turbo"] is False
        assert planned["sampler"]["steps"] == 12
        assert planned["sampler"]["sampler_name"] == "res_multistep"
        assert "「" in sound
    else:
        assert ids == ["penis-lora-h3", "synth-pussy-h3", "larry-v4"], ids
        assert planned["cfg"]["turbo"] is True
        assert planned["turbo"] is True
        assert planned["sampler"]["steps"] == 8
        assert planned["sampler"]["sampler_name"] == "euler"
        assert "誰も話さない" not in planned["prompt"]
        assert "no speech" not in sound.lower()
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
    assert "穴の見え方" in general
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


def test_unpack_github_archive_and_studio_dest(tmp_path):
    import tarfile
    from h3_lora_studio import (
        fetch_github_files_raw,
        github_member_rel,
        has_fl2va_weight,
        studio_colab_dest,
        unpack_github_archive,
    )

    assert github_member_rel("Research-branch/colab/h3_lora_studio.py") == "colab/h3_lora_studio.py"
    assert studio_colab_dest("colab/h3_lora_studio.py", content_root=tmp_path) == tmp_path / "h3_lora_studio.py"
    assert studio_colab_dest("h3-lora-studio/stories/manhole-30s.json", content_root=tmp_path) == (
        tmp_path / "h3-lora-studio/stories/manhole-30s.json"
    )
    empty = tmp_path / "models"
    empty.mkdir()
    assert has_fl2va_weight(empty) is False
    (empty / "minimax_h3_fl2va_pruned_int8_convrot.safetensors").write_text("x", encoding="utf-8")
    assert has_fl2va_weight(empty) is True

    tar_path = tmp_path / "repo.tgz"
    with tarfile.open(tar_path, "w:gz") as tar:
        py = tmp_path / "src.py"
        py.write_text("# studio helper\n" + "x" * 40, encoding="utf-8")
        story = tmp_path / "src.json"
        story.write_text('{"id":"manhole-30s"}\n' + "y" * 40, encoding="utf-8")
        tar.add(py, arcname="Research-branch/colab/h3_lora_studio.py")
        tar.add(story, arcname="Research-branch/h3-lora-studio/stories/manhole-30s.json")
    out = tmp_path / "out"
    missing = unpack_github_archive(
        tar_path,
        [
            "colab/h3_lora_studio.py",
            "h3-lora-studio/stories/manhole-30s.json",
            "missing.json",
        ],
        lambda rel: studio_colab_dest(rel, content_root=out),
    )
    assert missing == ["missing.json"]
    assert (out / "h3_lora_studio.py").read_text(encoding="utf-8").startswith("# studio helper")
    assert (out / "h3-lora-studio/stories/manhole-30s.json").is_file()
    assert fetch_github_files_raw("unused", [], lambda rel: out / rel) == []


def test_ensure_select_loras_copies_from_scripts_and_drive(tmp_path):
    from h3_lora_studio import ensure_select_loras_on_path

    body = "MAX_HELPERS = 2\n" + ("x" * 80)
    scripts = tmp_path / "h3-lora-studio" / "scripts"
    scripts.mkdir(parents=True)
    (scripts / "select_loras.py").write_text(body, encoding="utf-8")
    dest = ensure_select_loras_on_path(content_root=tmp_path, branch="")
    assert dest == tmp_path / "select_loras.py"
    assert dest.read_text(encoding="utf-8") == body

    other = tmp_path / "other"
    drive = other / "drive"
    drive.mkdir(parents=True)
    (drive / "select_loras.py").write_text(body, encoding="utf-8")
    dest2 = ensure_select_loras_on_path(content_root=other, drive_root=drive, branch="")
    assert dest2 == other / "select_loras.py"
    assert dest2.is_file()
    assert (other / "h3-lora-studio" / "scripts" / "select_loras.py").is_file()


def test_ensure_select_loras_missing_tells_to_rerun_cell2(tmp_path):
    from h3_lora_studio import ensure_select_loras_on_path

    try:
        ensure_select_loras_on_path(content_root=tmp_path, branch="")
    except SystemExit as exc:
        assert "select_loras" in str(exc)
        assert "②" in str(exc)
    else:
        raise AssertionError("expected SystemExit")


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
    assert 'FETCH_REV = "h3-20260909-semen-volume-1"' in src
    assert "ensure_select_loras_on_path" in src
    assert 'shutil.copy2(sel, Path("/content/select_loras.py"))' in src
    assert "部品 select_loras がありません" in src
    assert "from select_loras import forbidden_hits" in src
    assert "--reserve-vram" in src
    assert "keep_canvas = bool(STORY)" in src
    assert "cap_fl2va_clip_s" in src
    assert "rewrite_take_seconds" in src
    assert "1本（最大10秒）" in src
    assert "garbage_collection_threshold:0.8" in src
    assert "15秒の本は10秒にします" in src
    assert '("colab/h3_r2v_core.py", Path("/content/h3_r2v_core.py"))' in src
    assert '("h3-lora-studio/scripts/select_loras.py", Path("/content/select_loras.py"))' in src
    assert src.find('"colab/h3_r2v_core.py"') < src.find(
        "from h3_lora_studio import fetch_github_tree"
    )
    helper_text = helper.read_text(encoding="utf-8")
    assert "except ImportError:" in helper_text
    assert "r2v_finalize_prompt = None" in helper_text
    assert "**ふたなりの既定:**" in src
    assert "竿＋マンコ、金玉なし" in src
    assert "「」の中は話し言葉" in src
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
    assert "h3-20260909-semen-volume-1" in blob
    assert "h3-20260907-r2v-node-1" not in blob
    assert "h3-20260907-pussy-1" not in blob
    assert "h3-20260907-shorts-1" not in blob
    assert "h3-20260907-who-1" not in blob
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
    assert "ensure_r2v_in_object_info" in src
    assert "ensure_comfy_r2v_node" in src
    assert "lock_oral_in_mouth" in src
    assert '"to the BASE" not in getattr(_h3_studio, "ORAL_IN_MOUTH_LINE", "")' in src
    assert "lock_penis_inside" in src
    assert "lock_semen_share_kiss" in src
    assert "who_hidden_at_start" in src
    assert "lock_start_cast" in src
    assert "lock_spoken_emotion" in src
    assert "lock_urine_look" in src
    assert "lock_pleasure_face" in src
    assert "lock_pleasure_voice_and_wait" in src
    assert "lock_act_silent" in src
    assert "lock_act_sfx" in src
    assert "comfy_alive" in src
    assert "wait_comfy_ready" in src
    assert "comfy_free(PORT)" in src
    assert "同じサイズ再試行" in src
    assert "if CLIP_INDEX + 1 < len(CLIPS):\n            comfy_free(PORT)" not in src
    assert "prompt_now = lock_spoken_japanese(GRAPH_PROMPT)" in src
    assert 'AUDIO_LOCK_MARK", "") != "[AUDIO-LOCK]"' in src
    assert 'sanitize_story_soundscape", None)' in src
    assert "prompt=prompt_now" in src
    assert "前の LoRA を VRAM から下ろし" not in src
    assert "土台は載せたまま。この本の LoRA だけ繋ぎます" in src
    swap = src.find('elif CLIP_INDEX > 0 and planned.get("stack_changed"):')
    assert swap != -1
    swap_chunk = src[swap: src.find("else:", swap)]
    assert "comfy_free" not in swap_chunk
    assert "warmup_h3_engine" not in swap_chunk
    assert "よく使う部品を全部ディスクへ入れます" in src
    assert "設定だけ更新する = True" in src
    assert "fetch_github_tree" in src
    assert "has_fl2va_weight" in src
    assert "update=not fast" in src
    assert "ローカルに土台あり。Drive からのコピーは飛ばします。" in src
    assert "土台がまだ無いので、設定だけではなく全部入れます。" in src
    assert "LoRA は Drive のまま" in src
    assert "土台だけローカル（FL2VA・文字・VAE）。LoRA は Drive のまま。" in src
    assert "include_ref2v=need_r2v" in src
    assert "cores_only=True" in src
    assert 'link_dir(COMFY_DIR / "models" / "loras", DRIVE_MODELS / "loras")' in src
    assert 'getattr(_h3_studio, "is_ref2v_weight", None)' in src
    assert '"cores_only" not in getattr(_h3_studio.stage_models_to_local, "__code__").co_varnames' in src
    assert '"SAME EYE LEVEL" not in getattr(_h3_studio, "SEMEN_SHARE_LINE", "")' in src
    assert '"clingy" not in getattr(_h3_studio, "SEMEN_LOOK_LINE", "")' in src
    assert '"heavy-oil" not in getattr(_h3_studio, "SEMEN_LOOK_LINE", "")' in src
    assert '"TOO MUCH" not in getattr(_h3_studio, "SEMEN_LOOK_LINE", "")' in src
    assert '"SHAFT LOOK:" not in getattr(_h3_studio, "SHAFT_LOOK_LINE", "")' in src
    assert '"tongues wrap" not in getattr(_h3_studio, "SEMEN_SHARE_LINE", "")' in src
    assert "参照用の土台（約21GB）をローカルへ載せます" in src
    assert "fetch_weight(url, dest, token=token, auth=auth, fallback_urls=fallbacks, strict=False)\n        stage_models_to_local(DRIVE_MODELS, COMFY_DIR / \"models\")" not in src
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


def test_clamp_studio_duration_is_four_to_ten():
    assert clamp_studio_duration(10) == 10.0
    assert clamp_studio_duration(5) == 5.0
    assert clamp_studio_duration(4) == 4.0
    assert clamp_studio_duration(3) == 4.0
    assert clamp_studio_duration(15) == 10.0
    assert clamp_studio_duration(16) == 10.0
    assert clamp_studio_duration(10.4) == 10.0
    assert clamp_studio_duration("8") == 8.0
    assert clamp_studio_duration("nope") == 10.0
    assert clamp_studio_duration(12, chain=False) == 10.0
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
    assert cap_fl2va_clip_s(15) == 10.0
    assert cap_fl2va_clip_s(8) == 8.0
    assert rewrite_take_seconds("ONE UNBROKEN 15-second take. the whole 15-second take.", 10) == (
        "ONE UNBROKEN 10-second take. the whole 10-second take."
    )
    assert situation_ids("general_sex") == ["hmnsfw-aio-v25", "penis-lora-h3", "synth-pussy-h3"]
    assert situation_ids("riding") == ["cowgirl-position-h3", "penis-lora-h3", "synth-pussy-h3"]
    assert situation_ids("doggy") == ["doggy-h3", "penis-lora-h3", "synth-pussy-h3"]
    assert situation_ids("missionary_pov") == ["missionary-pov-h3", "penis-lora-h3", "synth-pussy-h3", "larry-v4"]
    assert situation_ids("after_ejaculation") == ["hmcumshot-v2", "penis-lora-h3", "synth-pussy-h3", "larry-v4"]
    assert situation_ids("facial") == ["facial-cumshot-h3", "penis-lora-h3", "synth-pussy-h3", "larry-v4"]
    assert situation_ids("creampie") == ["final-thrust-h3", "penis-lora-h3", "synth-pussy-h3"]
    assert situation_ids("oral_creampie") == ["cumouf-h3", "penis-lora-h3", "synth-pussy-h3", "larry-v4"]
    assert situation_ids("fingering") == ["fingering-h3", "synth-pussy-h3", "larry-v4"]
    assert situation_ids("anal_fingering") == ["thumbinbutt-h3", "synth-pussy-h3", "larry-v4"]
    assert situation_ids("masturbation") == ["hmmasturbation-h3", "synth-pussy-h3", "larry-v4"]
    assert situation_ids("footjob") == ["footjob-h3", "penis-lora-h3", "synth-pussy-h3", "larry-v4"]
    assert situation_ids("remote_orgasm") == ["remote-orgasm-h3", "synth-pussy-h3", "larry-v4"]
    assert situation_ids("preview") == ["hmnsfw-aio-v25", "synth-pussy-h3", "minimax-h3-turbo-fl2v-4step"]
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


def test_studio_clip_plan_chain_stays_under_eleven():
    assert studio_clip_plan(15) == [10.0]
    assert studio_clip_plan(16, chain=True) == [10.0, 6.0]
    assert studio_clip_plan(25, chain=True) == [10.0, 10.0, 5.0]
    assert studio_clip_plan(26, chain=True) == [10.0, 10.0, 6.0]
    assert studio_clip_plan(20, chain=True) == [10.0] * 2
    assert studio_clip_plan(21, chain=True) == [10.0, 7.0, 4.0]
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
    assert all(4 <= c <= 10 for c in studio_clip_plan(120, chain=True))
    assert all(4 <= c <= 10 for c in studio_clip_plan(21, chain=True))
    total, clips, chain = resolve_studio_length(30, "つなぐ（16〜60秒）")
    assert chain is True
    assert total == 30.0
    assert clips == [10.0, 10.0, 10.0]
    total, clips, chain = resolve_studio_length(45, "つなぐ（秒数欄・16〜120）")
    assert chain is True
    assert total == 45.0
    assert clips == [10.0, 10.0, 10.0, 10.0, 5.0]
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
    assert total == 10.0
    assert clips == [10.0]
    assert resolve_length_mode("つなぐ") is True
    assert resolve_length_mode("1本（最大15秒）") is False
    total, clips, chain = resolve_studio_length(30, "1本（最大10秒）")
    assert chain is False
    assert total == 10.0
    assert clips == [10.0]
    assert resolve_length_mode("1本（最大10秒）") is False


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
        if u.endswith("/object_info/MiniMaxH3ReferenceToVideo"):
            return _FakeHttp({"MiniMaxH3ReferenceToVideo": {"input": {}}})
        if u.endswith("/object_info/VAEDecodeAudio"):
            return _FakeHttp({"VAEDecodeAudio": {"input": {}}})
        if u.rstrip("/").endswith("/object_info"):
            raise AssertionError("full /object_info dump should not be used")
        return _FakeHttp({})

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    obj = fetch_comfy_object_info(8188)
    assert "MiniMaxH3ImageToVideo" in obj
    assert "MiniMaxH3ReferenceToVideo" in obj
    assert "LoraLoaderModelOnly" in obj
    assert not any(u.rstrip("/").endswith("/object_info") for u in hits)
    assert any(u.endswith("/object_info/MiniMaxH3ReferenceToVideo") for u in hits)


def test_studio_object_info_nodes_include_r2v():
    from h3_lora_studio import R2V_NODE, STUDIO_OBJECT_INFO_NODES

    assert R2V_NODE == "MiniMaxH3ReferenceToVideo"
    assert "MiniMaxH3ReferenceToVideo" in STUDIO_OBJECT_INFO_NODES


def test_fetch_comfy_object_info_does_not_full_dump_when_r2v_missing(monkeypatch):
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
        if u.endswith("/object_info/MiniMaxH3ReferenceToVideo"):
            raise OSError("404")
        if u.rstrip("/").endswith("/object_info"):
            raise AssertionError("full /object_info dump should not be used")
        return _FakeHttp({})

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    obj = fetch_comfy_object_info(8188)
    assert "MiniMaxH3ImageToVideo" in obj
    assert "MiniMaxH3ReferenceToVideo" not in obj
    assert any(u.endswith("/object_info/MiniMaxH3ReferenceToVideo") for u in hits)


def test_ensure_r2v_in_object_info_probes_when_i2v_cache_skipped_it(monkeypatch):
    from h3_lora_studio import ensure_r2v_in_object_info

    monkeypatch.setattr(
        "h3_lora_studio.fetch_comfy_node_info",
        lambda *_a, **_k: {"MiniMaxH3ReferenceToVideo": {"input": {}}},
    )
    called = []
    monkeypatch.setattr(
        "h3_lora_studio.ensure_comfy_r2v_node",
        lambda *_a, **_k: called.append(1) or True,
    )
    obj = ensure_r2v_in_object_info({"MiniMaxH3ImageToVideo": {}}, 8188, comfy_dir="/tmp/comfy")
    assert "MiniMaxH3ReferenceToVideo" in obj
    assert called == []


def test_ensure_r2v_in_object_info_pulls_comfy_when_truly_missing(monkeypatch, tmp_path):
    from h3_lora_studio import ensure_r2v_in_object_info

    monkeypatch.setattr("h3_lora_studio.fetch_comfy_node_info", lambda *_a, **_k: {})
    pulls = []
    monkeypatch.setattr(
        "h3_lora_studio.ensure_comfy_r2v_node",
        lambda *_a, **_k: pulls.append(1) or False,
    )
    obj = ensure_r2v_in_object_info({"MiniMaxH3ImageToVideo": {}}, 8188, comfy_dir=tmp_path)
    assert "MiniMaxH3ReferenceToVideo" not in obj
    assert pulls == [1]


def test_ensure_comfy_r2v_node_skips_git_when_present(monkeypatch, tmp_path):
    from h3_lora_studio import ensure_comfy_r2v_node

    monkeypatch.setattr("h3_lora_studio.comfy_has_r2v", lambda *_a, **_k: True)
    runs = []
    monkeypatch.setattr(
        "h3_lora_studio.subprocess.run",
        lambda *a, **k: runs.append(a[0]) or type("R", (), {"returncode": 0})(),
    )
    assert ensure_comfy_r2v_node(tmp_path, port=8188) is True
    assert runs == []


def test_ensure_comfy_r2v_node_fetches_when_missing(monkeypatch, tmp_path):
    from h3_lora_studio import ensure_comfy_r2v_node

    (tmp_path / "main.py").write_text("# comfy\n", encoding="utf-8")
    monkeypatch.setattr("h3_lora_studio.comfy_has_r2v", lambda *_a, **_k: False)
    runs = []

    def fake_run(cmd, **kw):
        runs.append(list(cmd))
        return type("R", (), {"returncode": 0})()

    monkeypatch.setattr("h3_lora_studio.subprocess.run", fake_run)
    monkeypatch.setattr("h3_lora_studio.restart_studio_comfy", lambda *_a, **_k: None)
    monkeypatch.setattr("h3_lora_studio.wait_comfy_ready", lambda *_a, **_k: True)
    # after pull, still missing
    assert ensure_comfy_r2v_node(tmp_path, port=8188) is False
    assert any(cmd[:3] == ["git", "-C", str(tmp_path)] and "fetch" in cmd for cmd in runs)
    assert any(cmd[:3] == ["git", "-C", str(tmp_path)] and "reset" in cmd for cmd in runs)


def test_ensure_comfy_r2v_node_skips_git_when_update_false(monkeypatch, tmp_path):
    from h3_lora_studio import ensure_comfy_r2v_node

    (tmp_path / "main.py").write_text("# comfy\n", encoding="utf-8")
    monkeypatch.setattr("h3_lora_studio.comfy_has_r2v", lambda *_a, **_k: False)
    runs = []
    monkeypatch.setattr(
        "h3_lora_studio.subprocess.run",
        lambda *a, **k: runs.append(a[0]) or type("R", (), {"returncode": 0})(),
    )
    assert ensure_comfy_r2v_node(tmp_path, port=8188, update=False) is False
    assert runs == []


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


def test_is_ref2v_weight_matches_ref2va_only():
    from h3_lora_studio import is_ref2v_weight

    assert is_ref2v_weight("minimax_h3_ref2va_pruned_int8.safetensors")
    assert is_ref2v_weight("minimax_h3_ref2v_turbo.safetensors")
    assert not is_ref2v_weight("minimax_h3_fl2va_pruned_int8_convrot.safetensors")
    assert not is_ref2v_weight("qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors")


def test_stage_models_cores_only_skips_loras_and_ref2va(tmp_path):
    from h3_lora_studio import stage_models_to_local

    drive = tmp_path / "drive" / "models"
    local = tmp_path / "local" / "models"
    (drive / "diffusion_models").mkdir(parents=True)
    (drive / "text_encoders").mkdir()
    (drive / "vae").mkdir()
    (drive / "loras").mkdir()
    (drive / "diffusion_models" / "minimax_h3_fl2va.safetensors").write_bytes(b"f" * 4000)
    (drive / "diffusion_models" / "minimax_h3_ref2va.safetensors").write_bytes(b"r" * 8000)
    (drive / "text_encoders" / "qwen.safetensors").write_bytes(b"t" * 2000)
    (drive / "vae" / "vae.safetensors").write_bytes(b"v" * 500)
    (drive / "loras" / "larry.safetensors").write_bytes(b"l" * 3000)
    stats = stage_models_to_local(drive, local, min_free_bytes=0)
    assert (local / "vae" / "vae.safetensors").is_file()
    assert (local / "text_encoders" / "qwen.safetensors").is_file()
    assert (local / "diffusion_models" / "minimax_h3_fl2va.safetensors").is_file()
    assert not (local / "diffusion_models" / "minimax_h3_ref2va.safetensors").exists()
    assert not (local / "loras" / "larry.safetensors").exists()
    assert "minimax_h3_ref2va.safetensors" not in stats["copied"]
    assert "larry.safetensors" not in stats["copied"]
    with_r2v = stage_models_to_local(drive, local, min_free_bytes=0, include_ref2v=True)
    assert (local / "diffusion_models" / "minimax_h3_ref2va.safetensors").is_file()
    assert "minimax_h3_ref2va.safetensors" in with_r2v["copied"]
    assert not (local / "loras" / "larry.safetensors").exists()
    all_files = stage_models_to_local(drive, local, min_free_bytes=0, cores_only=False, include_ref2v=True)
    assert (local / "loras" / "larry.safetensors").is_file()
    assert "larry.safetensors" in all_files["copied"]


def test_stage_weight_file_resumes_partial_copy(tmp_path):
    from h3_lora_studio import stage_weight_file

    src = tmp_path / "clip.safetensors"
    dest = tmp_path / "out" / "clip.safetensors"
    payload = b"abcdefgh" * 8000
    src.write_bytes(payload)
    part = dest.with_name(dest.name + ".part")
    dest.parent.mkdir(parents=True)
    part.write_bytes(payload[: len(payload) // 2])
    assert stage_weight_file(src, dest) == "copied"
    assert dest.read_bytes() == payload
    assert not part.exists()
    dest.unlink()
    dest.write_bytes(payload[: 1000])
    assert stage_weight_file(src, dest) == "copied"
    assert dest.read_bytes() == payload


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
    assert [r["id"] for r in vis["stack"]] == ["penis-lora-h3", "synth-pussy-h3", "larry-v4"]
    vis_speech = select_loras(profile_name="futa_visible", mode="t2v", prompt_arg="（シーン）", turbo_override=False)
    assert vis_speech["turbo"] is False
    assert vis_speech["sampler"]["steps"] == 12
    assert vis_speech["sampler"]["sampler_name"] == "res_multistep"
    assert [r["id"] for r in vis_speech["stack"]] == ["penis-lora-h3", "synth-pussy-h3"]
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
        "futa_visible",
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
        "futa_visible",
        "futa_visible",
        "futa_visible",
    ]
    assert [c["situation"] for c in story["clips"]] == want
    assert [float(c["duration_s"]) for c in story["clips"]] == [10.0] * 10
    assert sum(1 for c in story["clips"] if c["situation"] == "cunnilingus_futa") == 1
    assert "Close-up" in story["clips"][4]["prompt"]
    assert "Do not pull back to full bodies" in story["clips"][4]["prompt"]
    assert "Not a crotch close-up" in story["clips"][3]["prompt"]
    assert "yellow" in story["clips"][3]["prompt"].lower()
    assert "urethral" in story["clips"][3]["prompt"].lower()
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
        "futa_visible",
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
        "futa_visible",
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
    assert "さきにあらってて" in story["clips"][2]["prompt"]
    assert "おふろだとよけいムクってる" in story["clips"][5]["prompt"]
    assert "あがったらごはんね" in story["clips"][11]["prompt"]
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
        "futa_visible",
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
    assert "たべなさい" in story["clips"][2]["prompt"]
    assert "ごはんのとちゅうなのに" in story["clips"][5]["prompt"]
    assert "うえもちゃんとたべなさい" in story["clips"][11]["prompt"]
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
        "futa_visible",
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
    assert "ねるまえなのに" in story["clips"][5]["prompt"]
    assert "でんき、けしたよ" in story["clips"][11]["prompt"]
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
    assert "やすみなのにアサからムクってる" in story["clips"][3]["prompt"]
    assert "ひるごはん、まだだよ" in story["clips"][11]["prompt"]
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
    assert "ひるからもムクってる" in story["clips"][2]["prompt"]
    assert "さらあらっとくから" in story["clips"][11]["prompt"]
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
            sound_out = re.search(r"overall_soundscape:\n(.+?)\n\n", out, re.S).group(1).strip()
            assert "lip-synced" not in sound_out.lower(), where
            assert "no other speech" not in sound_out.lower(), where
            assert "no spoken words" not in sound_out.lower(), where
            for spoken in re.findall(r"「[^」]+」", sound):
                assert spoken in sound_out, (where, spoken)
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
    assert text.startswith("PENISLORA\n")
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
    lipsync_oral = {
        "clip_s": 10,
        "clips": [
            {
                "duration_s": 10,
                "situation": "oral",
                "prompt": "medium-close on the mouth. Already oral.\nLIP SYNC: face large.",
            }
        ],
    }
    errs = validate_story_follow(lipsync_oral)
    assert any("must not lip-sync" in e for e in errs)
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
    assert any("duration_s must be 10" in e for e in errs)
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
    errs = validate_story_follow(silent_15)
    assert any("duration_s must be 10" in e for e in errs)
    addon_talk_10 = {
        "id": "manhole-30s",
        "addon": True,
        "spoken_max": 2,
        "clip_s": 10,
        "clips": [
            {
                "duration_s": 10,
                "situation": "futa_visible",
                "prompt": "ONE UNBROKEN 10-second take. LIP SYNC: face large.\n「このフタ、ズレてる」\n「いまなおす」",
            }
        ],
    }
    assert validate_story_follow(addon_talk_10) == []
    addon_act_speech = {
        "id": "manhole-30s",
        "addon": True,
        "clip_s": 10,
        "clips": [
            {
                "duration_s": 10,
                "situation": "oral_creampie",
                "prompt": "ONE UNBROKEN 10-second take. medium-close on the mouth. Already oral.\n「だめ」",
            }
        ],
    }
    errs = validate_story_follow(addon_act_speech)
    assert any("must not speak" in e for e in errs)


def test_validate_story_follow_addon_pose_prep():
    from h3_lora_studio import validate_story_follow

    talk = "ONE UNBROKEN 10-second take. LIP SYNC: face large.\n「クーラーしんでる」\n「フィルタ、みて」"
    sex = (
        "hmmotion\nONE UNBROKEN 10-second take. ALREADY IN. Joining point visible. "
        "No spoken words."
    )
    oral = (
        "ONE UNBROKEN 10-second take. medium-close on the mouth. Already oral. "
        "Already at the BASE. No spoken words."
    )
    cunni = (
        "ONE UNBROKEN 10-second take. close-up. Already cunnilingus. No spoken words."
    )
    bad_sex = {
        "id": "roof-ac-30s",
        "addon": True,
        "spoken_max": 2,
        "clip_s": 10,
        "clips": [
            {"duration_s": 10, "situation": "futa_visible", "prompt": talk},
            {"duration_s": 10, "situation": "futa_sex", "prompt": sex},
        ],
    }
    errs = validate_story_follow(bad_sex)
    assert any("hand's width" in e for e in errs)
    assert any("NOT in" in e for e in errs)
    assert any("accepting pose" in e for e in errs)
    good_sex = dict(bad_sex)
    good_sex["clips"] = [
        {
            "duration_s": 10,
            "situation": "futa_visible",
            "prompt": talk
            + " After the lines she is in the accepting standing pose, hips back. "
            "Erect 20cm a hand's width from her hairless pussy, NOT in.",
        },
        {"duration_s": 10, "situation": "futa_sex", "prompt": sex},
    ]
    assert validate_story_follow(good_sex) == []
    bad_oral = {
        "id": "manhole-30s",
        "addon": True,
        "spoken_max": 2,
        "clip_s": 10,
        "clips": [
            {"duration_s": 10, "situation": "futa_visible", "prompt": talk},
            {"duration_s": 10, "situation": "oral_creampie", "prompt": oral},
        ],
    }
    errs = validate_story_follow(bad_oral)
    assert any("hand's width" in e for e in errs)
    assert any("mouth open" in e for e in errs)
    good_oral = dict(bad_oral)
    good_oral["clips"] = [
        {
            "duration_s": 10,
            "situation": "futa_visible",
            "prompt": talk
            + " She opens her mouth. Tip a hand's width from her lips, not touching.",
        },
        {"duration_s": 10, "situation": "oral_creampie", "prompt": oral},
    ]
    assert validate_story_follow(good_oral) == []
    bad_cunni = {
        "id": "lookout-30s",
        "addon": True,
        "spoken_max": 2,
        "clip_s": 10,
        "clips": [
            {"duration_s": 10, "situation": "futa_visible", "prompt": talk},
            {"duration_s": 10, "situation": "cunnilingus_futa", "prompt": cunni},
        ],
    }
    errs = validate_story_follow(bad_cunni)
    assert any("knees open" in e for e in errs)
    good_cunni = dict(bad_cunni)
    good_cunni["clips"] = [
        {
            "duration_s": 10,
            "situation": "futa_visible",
            "prompt": talk + " Aya on her back, knees open. Nobody licks yet.",
        },
        {"duration_s": 10, "situation": "cunnilingus_futa", "prompt": cunni},
    ]
    assert validate_story_follow(good_cunni) == []


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
    assert {"sales-visit-60s", "checkup-100s", "clinic-75s", "last-stop-40s"} <= CHAIN_PACK_IDS
    from h3_lora_studio import ADDON_PACK_IDS, resolve_situation

    assert ADDON_PACK_IDS <= CHAIN_PACK_IDS
    assert len(ADDON_PACK_IDS) == 10
    assert "manhole-30s" in ADDON_PACK_IDS and "riverbank-30s" in ADDON_PACK_IDS
    assert not (CHAIN_PACK_IDS & STORY_IDS)
    labels = story_play_labels()
    assert len(labels) == 55
    assert labels[:5] == ["帰宅（専用）", "帰宅（つなぐ）", "帰宅（つなぐ修）", "帰宅（参照つなぐ）", "帰宅（参照つなぐ修）"]
    assert labels[10:15] == ["登校（専用）", "登校（つなぐ）", "登校（つなぐ修）", "登校（参照つなぐ）", "登校（参照つなぐ修）"]
    pack_labels = chain_pack_labels()
    assert len(pack_labels) == 5 * len(CHAIN_PACK_IDS)
    assert pack_labels[:5] == ["訪問販売（専用）", "訪問販売（つなぐ）", "訪問販売（つなぐ修）", "訪問販売（参照つなぐ）", "訪問販売（参照つなぐ修）"]
    assert pack_labels[10:15] == ["ケンシン（専用）", "ケンシン（つなぐ）", "ケンシン（つなぐ修）", "ケンシン（参照つなぐ）", "ケンシン（参照つなぐ修）"]
    assert "ケンシン（専用）" in pack_labels
    assert "ハイスイコウ（専用）" in pack_labels
    assert "川原のゴミ（参照つなぐ修）" in pack_labels
    assert is_chain_pack("ハイスイコウ（専用）")
    assert resolve_situation("ハイスイコウ") == "manhole-30s"
    assert resolve_situation("川原のゴミ（つなぐ）") == "riverbank-30s"
    assert chain_pack_legacy_labels() == ["訪問販売60秒（つなぐ）", "定期検診100秒（つなぐ）", "終点40秒（つなぐ）"]
    assert resolve_situation("ケンシン") == "clinic-75s"
    assert resolve_situation("医院ケンシン") == "clinic-75s"
    assert resolve_situation("ケンシン（専用）") == "clinic-75s"
    assert is_chain_pack("clinic-75s") and not is_story("clinic-75s")
    assert resolve_situation("終電") == "last-train-120s"
    assert resolve_situation("終電（専用）") == "last-train-120s"
    assert resolve_situation("ザーメン風呂") == "semen-bath-70s"
    assert resolve_situation("ザーメンフロ") == "semen-bath-70s"
    assert resolve_situation("ザーメン風呂（つなぐ）") == "semen-bath-70s"
    assert resolve_situation("ニクカベ") == "meat-wall-85s"
    assert resolve_situation("肉壁") == "meat-wall-85s"
    assert resolve_situation("ニクカベ（専用）") == "meat-wall-85s"
    assert resolve_situation("ニクカベ肥溜め") == "meat-wall-cesspit-70s"
    assert resolve_situation("肉壁肥溜め") == "meat-wall-cesspit-70s"
    assert resolve_situation("ニクヘキ肥溜め") == "meat-wall-cesspit-70s"
    assert resolve_situation("ニクカベ肥溜め（専用）") == "meat-wall-cesspit-70s"
    assert is_chain_pack("last-train-120s") and not is_story("last-train-120s")
    assert is_chain_pack("semen-bath-70s") and not is_story("semen-bath-70s")
    assert is_chain_pack("meat-wall-85s") and not is_story("meat-wall-85s")
    assert is_chain_pack("meat-wall-cesspit-70s") and not is_story("meat-wall-cesspit-70s")
    assert "終電（専用）" in pack_labels
    assert "ザーメン風呂（専用）" in pack_labels
    assert "ニクカベ（専用）" in pack_labels
    assert "ニクカベ肥溜め（専用）" in pack_labels
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
    assert "短編集" in text and "10秒" in text and "R2V" in text
    text = explain_choice("生成し直し", "テキストから（写真なし）")
    assert "生成し直し" in text and "起点" in text


def test_redo_from_clip_helpers(tmp_path):
    from h3_lora_studio import (
        REDO_LABEL,
        apply_redo_play,
        find_existing_story_clip,
        is_redo,
        is_story,
        load_story,
        parse_redo_start,
        redo_start_frame_name,
        redo_story_labels,
        resolve_situation,
        stock_completed_clips,
    )

    assert is_redo(REDO_LABEL) and is_redo("生成し直し")
    assert resolve_situation("生成し直し") == "redo"
    assert not is_story("生成し直し")
    assert parse_redo_start("3", 9) == 3
    assert parse_redo_start("0", 9) == 1
    assert parse_redo_start("99", 8) == 8
    assert parse_redo_start("x", 8) == 1
    assert redo_start_frame_name(1) is None
    assert redo_start_frame_name(3) == "h3_chain_1.png"
    assert redo_start_frame_name(2) == "h3_chain_0.png"
    labels = redo_story_labels()
    assert "ニクカベ（つなぐ）" in labels
    assert "生成し直し" not in labels
    assert "短編集（参照）" not in labels
    story = load_story("meat-wall-85s")
    mid = apply_redo_play(story, "dedicated", 3)
    assert mid["redo"] is True and mid["redo_start"] == 3
    assert mid["seamless"] is True
    assert mid["use_cast_ref"] is False
    assert mid["rewrite_chain_prompts"] is False
    assert mid["play"] == "chain"
    first = apply_redo_play(story, "dedicated", 1)
    assert first["redo_start"] == 1
    assert first["seamless"] is False
    assert first["play"] == "dedicated"
    out = tmp_path / "output"
    inp = tmp_path / "input"
    out.mkdir()
    inp.mkdir()
    good = out / "video"
    good.mkdir()
    (good / "h3_meat-wall-85s_p0_00001.mp4").write_bytes(b"clip0")
    (good / "h3_meat-wall-85s_p1_00001.mp4").write_bytes(b"clip1")
    (inp / "h3_chain_0.png").write_bytes(b"x" * 120)
    found = find_existing_story_clip(out, "meat-wall-85s", 0)
    assert found is not None and found.name.startswith("h3_meat-wall-85s_p0")
    stock = stock_completed_clips(
        out_dir=out,
        input_dir=inp,
        story_id="meat-wall-85s",
        start_1based=3,
        stamp="test",
    )
    assert stock["dir"] is not None
    assert len(stock["clips"]) == 2
    assert any(p.name.startswith("h3_meat-wall-85s_p0") for p in stock["clips"])
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
            ["あちぃー", "あー、すずしい！いきかえるー！"],
            ["いらっしゃいませ。ごちゅうもんはいかがしますか", "アイスコーヒーで"],
            ["あ、おミズください", "あ、はい、どうぞ"],
            [],
            ["んっ、おチンチン、あつくて、おいしい、、、", "ありがとうございます。コーヒー、すぐおもちしますね"],
            ["おまたせしました", "あ、ミルクください！"],
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
    assert "both faces" not in c1
    cam = c1.split("CAMERA:", 1)[1].split("\n", 1)[0]
    assert "medium two-shot" not in cam.lower()
    assert "both faces" not in cam.lower()
    assert "Aya alone" in cam
    assert "midsummer" in c1.lower() or "miserably hot" in c1.lower()
    assert "あちぃー" in c1
    assert "to the BASE" in story["clips"][3]["prompt"] or "to the base" in story["clips"][3]["prompt"]
    for clip in story["clips"][1:]:
        assert story_cast_present(clip["prompt"]) == ["Aya", "Clerk"]
    assert "jupo-jupo" in story["clips"][3]["prompt"]
    assert "yellow stream" not in story["clips"][3]["prompt"]
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
            ["おちゃ、コーヒー、いかがですか", "おちゃ、ください"],
            ["はい。あついのとひやし、どっち", "ひやしで"],
            [],
            ["んっ、おチンチン、あつい、、、", "ほかにごようは？"],
            ["ミルクコーヒーも"],
            [],
            [],
            ["ん、あつい。ミルクきいてる", "ありがとうございました"],
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
        lines=[["あかだね", "つぎ、みぎだよ"], ["エアコン、よわくする？", "このままでいい"], [], [], ["あおになった。みぎね", "うん"]],
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
        lines=[["こし、おとして", "ここ？"], ["もうすこし、まえ", "こつばん、おとしたまま"], [], [], ["いきをととのえて", "すいぶん、とってね"]],
        cast_defs=["Aya", "Instructor"],
        download=["penis-lora-h3", "cinema-dy", "doggy-h3", "synth-pussy-h3", "larry-v4"],
    )
    for clip in story["clips"][2:4]:
        assert ("ALREADY IN" in clip["prompt"] or "Still joined" in clip["prompt"]) and "Joining point" in clip["prompt"]
        assert "Do not pull out" in clip["prompt"]
    assert "Not oral" in story["clips"][2]["prompt"]
    assert "NOT in" in story["clips"][1]["prompt"]


def test_back_wash_pack_cunnilingus_then_jupo(tmp_path):
    story = _check_pretext_pack(
        "back-wash-60s", tmp_path, n_clips=6,
        situations=["futa_visible", "futa_visible", "cunnilingus_futa", "futa_visible", "oral", "futa_visible"],
        lines=[["かたいね", "かた、やって"], ["あわ、たすよ", "したも"], [], ["あがりゆ"], [], ["んっ、おくまで、はいってた、、。あがっていいよ"]],
        cast_defs=["Madoka", "Sayaka"],
        download=["penis-lora-h3", "cinema-dy", "lesbian-cunnilingus-h3", "synth-pussy-h3", "blowjob-h3", "larry-v4"],
    )
    cunni = story["clips"][2]["prompt"]
    assert "close-up" in cunni.lower() and "Not oral on the penis" in cunni and "20cm unused" in cunni
    assert "jupo-jupo" in story["clips"][4]["prompt"] and "BASE" in story["clips"][4]["prompt"]
    assert "yellow stream" not in story["clips"][4]["prompt"]
    for clip in story["clips"]:
        assert "Aya" not in clip["prompt"] and "Rei" not in clip["prompt"].replace("different face from Rei", "")


def test_karaoke_pack_jupo_during_song(tmp_path):
    story = _check_pretext_pack(
        "karaoke-50s", tmp_path, n_clips=5,
        situations=["futa_visible", "futa_visible", "oral", "oral_creampie", "futa_visible"],
        lines=[["このきょく、サビたかい", "キー、さげないの"], ["このまま"], [], [], ["きゅうよんてん", "サビ、きれてた"]],
        cast_defs=["Aya", "Madoka"],
        download=["penis-lora-h3", "cinema-dy", "blowjob-h3", "larry-v4", "cumouf-h3", "synth-pussy-h3"],
    )
    assert "mic" in story["clips"][2]["prompt"].lower()
    assert "last note" in story["clips"][3]["prompt"].lower()


def test_laundromat_pack_aio_on_machine(tmp_path):
    story = _check_pretext_pack(
        "laundromat-50s", tmp_path, n_clips=5,
        situations=["futa_visible", "futa_visible", "futa_sex", "futa_sex", "futa_visible"],
        lines=[["あとなんぷん", "じゅうはちふん"], ["ながいね", "すわる？"], [], [], ["おわった", "たたもう"]],
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
        lines=[["ここ、しけんにでます", "はい"], ["ノート、とって"], [], [], ["しゅくだい、にじゅうページ", "はい"]],
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
        lines=[["か、いる", "スプレー、どこ"], ["テントのなか", "ここ、やられた？"], [], [], ["スプレー、だしてくる", "ライト、もっていって"]],
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
        lines=[["いちはつめ", "あおい"], ["うちあげ、おそいね"], [], [], ["かえろっか", "ゴミ、ひろって"]],
        cast_defs=["Madoka", "Sayaka"],
        download=["penis-lora-h3", "cinema-dy", "hmnsfw-aio-v25", "synth-pussy-h3", "larry-v4"],
    )
    for clip in story["clips"][2:4]:
        assert clip["prompt"].startswith("hmmotion, PENISLORA")
        assert "from behind" in clip["prompt"].lower() or "Still joined" in clip["prompt"]
        assert "sky" in clip["prompt"].lower()
    for clip in story["clips"]:
        assert "Aya" not in clip["prompt"]


def test_addon_packs_10s_talk_then_silent_act(tmp_path):
    """物語の追加: 10秒×2、台詞は1本目だけ、hmmotion は挿入本だけ、canvas のみ 9:16。"""
    from h3_lora_studio import (
        ADDON_PACK_IDS,
        ADDON_PACK_ORDER,
        ACT_SITUATIONS,
        HMMOTION_SITUATIONS,
        _KANJI_RE,
        is_chain_pack,
        is_story,
        load_story,
        prepare_story_clip,
        semen_share_plan,
        situation_ids,
        spoken_lines,
        story_canvas_wh,
        validate_story_follow,
    )

    expect = {
        "manhole-30s": (["futa_visible", "oral_creampie"], ["このフタ、ズレてる", "いまなおす"], ["Aya", "Rei"]),
        "roof-ac-30s": (["futa_visible", "futa_sex"], ["クーラーしんでる", "フィルタ、みて"], ["Sayaka", "Madoka"]),
        "tetrapod-30s": (["futa_visible", "oral_creampie"], ["カゼ、ヤバい", "カゲ、こっち"], ["Aya", "Rei"]),
        "locker-30s": (["futa_visible", "oral_creampie"], ["カギ、ない", "ウチのバンゴウ"], ["Aya", "Madoka"]),
        "crossing-30s": (["futa_visible", "oral_creampie"], ["シンゴウ、きえてる", "マツ"], ["Sayaka", "Rei"]),
        "lookout-30s": (["futa_visible", "cunnilingus_futa"], ["ナニモみえない", "シバラク、いよ"], ["Aya", "Rei"]),
        "factory-30s": (["futa_visible", "futa_sex"], ["サビ、ふむな", "キをつけて"], ["Sayaka", "Madoka"]),
        "gas-station-30s": (["futa_visible", "oral_creampie"], ["おチンチン、ミズ、ちょうだい、、、", "はい、おくち、あけて"], ["Aya", "Rei"]),
        "tunnel-phone-30s": (["futa_visible", "oral_creampie"], ["ツウじてる？", "ダセない"], ["Aya", "Rei"]),
        "riverbank-30s": (["futa_visible", "oral_creampie"], ["フクロ、やぶれてる", "テープ、ない"], ["Sayaka", "Madoka"]),
    }
    assert tuple(ADDON_PACK_ORDER) == tuple(expect)
    assert ADDON_PACK_IDS == set(expect)
    for sid, (sits, lines, cast) in expect.items():
        story = load_story(sid)
        assert story["addon"] is True
        assert story["id"] == sid and story["kind"] == "chain" and story["seamless"] is True
        assert story["clip_s"] == 10 and story["duration_s"] == 20
        assert story["spoken_max"] == 2 and story["spoken_no_kanji"] is True
        assert story["canvas"] == {"width": 576, "height": 1024, "aspect": "9:16"}
        assert story_canvas_wh(story) == (576, 1024)
        assert len(story["clips"]) == 2
        assert [c["situation"] for c in story["clips"]] == sits
        assert validate_story_follow(story) == []
        assert is_chain_pack(sid) and not is_story(sid)
        assert set(story["download"]) == set(situation_ids(sid))
        share = semen_share_plan(story)
        if sits[1] == "oral_creampie":
            assert share == [(1, "on_cumouf")], sid
        else:
            assert share == [], sid
        prev = None
        prev_stack = None
        for i, clip in enumerate(story["clips"]):
            prompt = clip["prompt"]
            assert clip["duration_s"] == 10
            assert "10-second take" in prompt
            assert "576x1024" not in prompt and "9:16" not in prompt and "16:9" not in prompt
            assert "Full bodies from head to feet" not in prompt
            got = spoken_lines(prompt)
            uniq = []
            for s in got:
                if s not in uniq:
                    uniq.append(s)
            for s in uniq:
                assert not _KANJI_RE.search(s), (sid, s)
                assert not re.search(r"[A-Za-z]", s), (sid, s)
            if i == 0:
                assert clip["situation"] == "futa_visible"
                assert uniq == lines, (sid, uniq)
                assert "LIP SYNC" in prompt
                assert "hmmotion" not in prompt.lower()
                c1 = prompt.lower()
                sit2 = sits[1]
                if sit2 in {"futa_sex", "doggy"}:
                    assert "hand's width" in c1, sid
                    assert "not in" in c1, sid
                    assert any(k in c1 for k in ("accepting", "hips back", "knees apart")), sid
                    assert "already in" not in c1, sid
                elif sit2 in {"oral", "oral_creampie"}:
                    assert "hand's width" in c1, sid
                    assert (
                        "mouth open" in c1
                        or "open mouth" in c1
                        or "opens her mouth" in c1
                    ), sid
                    assert "already oral" not in c1, sid
                elif sit2 == "cunnilingus_futa":
                    assert "knees open" in c1, sid
                    assert "not licking" in c1, sid
                    assert "already licking" not in c1, sid
            else:
                assert not uniq, sid
                assert "No spoken words" in prompt
                assert clip["situation"] in ACT_SITUATIONS
            if clip["situation"] in HMMOTION_SITUATIONS:
                assert prompt.startswith("hmmotion")
            else:
                assert "hmmotion" not in prompt.lower()
            if "Aya" in prompt or "Sayaka" in prompt:
                assert "NO penis" in prompt
            planned = prepare_story_clip(
                story,
                i,
                last_frame=("h3_chain_%d.png" % (i - 1)) if i else None,
                stills_dir=tmp_path,
                prev_situation=prev,
                prev_stack=prev_stack,
            )
            prev = planned["situation"]
            prev_stack = planned["stack"]
            assert {row["id"] for row in planned["stack"]} <= set(story["download"]), (sid, i + 1)
            assert planned["width"] == 576 and planned["height"] == 1024
            assert planned["duration_s"] == 10
            if uniq:
                assert "SPEECH FACE:" in planned["prompt"]
                assert "HEAT FACE:" not in planned["prompt"]
            if clip["situation"] == "oral_creampie":
                assert "ORGASM FACE:" in planned["prompt"]
                assert "mouth-to-mouth" in planned["prompt"].lower()
                assert "SEMEN SHARE:" in planned["prompt"]
                assert "ORAL LOCK:" in planned["prompt"]
                assert "STANDS UP" in planned["prompt"]
                assert "EYE LEVEL" in planned["prompt"]
                assert "they lean in" not in planned["prompt"].lower()
            if clip["situation"] == "cunnilingus_futa":
                assert "close-up" in prompt.lower()
                assert "口移し" not in planned["prompt"]
            if clip["situation"] == "futa_sex":
                assert "joining" in prompt.lower() or "already in" in prompt.lower()
                assert "口移し" not in planned["prompt"]
                assert "INSIDE LOCK:" in planned["prompt"]
        assert all(name in " ".join(c["prompt"] for c in story["clips"]) for name in cast)

    gas = load_story("gas-station-30s")
    c1 = gas["clips"][0]["prompt"]
    assert "mouth OPEN" in c1
    assert "hand's width" in c1
    assert "おチンチン、ミズ、ちょうだい、、、" in c1
    assert "はい、おくち、あけて" in c1
    assert "yellow" not in c1.lower() and "pees a" not in c1.lower()
    assert "drinks the yellow" not in c1.lower()
    assert "jupo-jupo" not in c1.lower() and "already oral" not in c1.lower()
    c2 = gas["clips"][1]["prompt"]
    assert "urine" not in c2.lower() and "yellow stream" not in c2.lower()
    locker = load_story("locker-30s")
    assert "kiss" in locker["clips"][0]["prompt"].lower()
    assert "jupo" not in locker["clips"][0]["prompt"].lower()
    tunnel = load_story("tunnel-phone-30s")
    assert "receiver" in tunnel["clips"][1]["prompt"].lower()
    look = load_story("lookout-30s")
    assert "20cm hangs unused" in look["clips"][1]["prompt"]
    assert "Not oral on a penis" in look["clips"][1]["prompt"]


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
    assert "いってらっしゃい" in c1["prompt"]
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
    assert r0["prompt"].startswith("PENISLORA\n")
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
    assert all(d == 10.0 for d in durs)
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
        assert dur == 10
        assert "15-second" not in prompt
        assert "Hard cut" not in prompt
        assert "Do not copy the previous clip" not in prompt
        assert "576x1024" in prompt
        spoken_cap = max(1, min(2, int(story.get("spoken_max") or 1)))
        assert len(set(lines)) <= spoken_cap, (sid, i + 1, lines)
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
    assert story["duration_s"] == 80
    assert [float(c["duration_s"]) for c in story["clips"]] == [10, 10, 10, 10, 10, 10, 10, 10]
    assert [c["situation"] for c in story["clips"]] == (
        ["futa_visible"] * 3 + ["oral", "futa_visible", "oral", "oral_creampie", "futa_visible"]
    )
    want = [
        "こんにちは。おミズ、とどけにきました",
        "おそいわよ",
        "はやくおミズちょうだい",
        None,
        "んっ、おチンチン、あつい、、、",
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
    c1 = story["clips"][0]["prompt"]
    assert "HIDDEN at the start" in c1
    assert "ENTERS FROM THE RIGHT" in c1
    assert "LEFT" in c1
    assert "Door on the right" in c1 or "door on the right" in c1
    assert "CLOSED front door" in c1 or "CLOSED genkan door" in c1 or "front door is CLOSED" in c1
    assert "already at the open door" not in c1.lower()
    assert "faces Aya in the open door" not in c1
    assert "spoken AFTER the door opens" in c1 or "AFTER the door opens" in c1
    assert "こんにちは。おミズ、とどけにきました" in c1
    assert "two-shot at the start" in c1.lower() or "Not a two-shot at the start" in c1
    assert "jupo-jupo" in story["clips"][3]["prompt"]
    assert "BASE" in story["clips"][3]["prompt"]
    assert "yellow" not in story["clips"][3]["prompt"].lower()
    assert "BASE" in story["clips"][5]["prompt"]
    assert story["clips"][5]["duration_s"] == 10
    assert "CUMOUF" in story["clips"][6]["prompt"] or "ejaculat" in story["clips"][6]["prompt"].lower()
    assert "cumouf-h3" in story["download"]
    assert "sticky" in story["clips"][6]["prompt"].lower() or "viscous" in story["clips"][6]["prompt"].lower()


def test_checkup_pack_nine_clips_doorway_kana_lines(tmp_path):
    from h3_lora_studio import _KANJI_RE, load_story, spoken_lines

    story = _check_pack_common(load_story("checkup-100s"), "checkup-100s", tmp_path)
    assert story["spoken_no_kanji"] is True
    assert len(story["clips"]) == 9
    assert story["duration_s"] == 90
    assert [float(c["duration_s"]) for c in story["clips"]] == (
        [10, 10, 10, 10, 10, 10, 10, 10, 10]
    )
    assert [c["situation"] for c in story["clips"]] == (
        ["futa_visible"] * 6 + ["oral", "oral_creampie", "futa_visible"]
    )
    want = [
        ["こんにちは", "はい"],
        ["テイキケンシンにきました", "あ、ヨロシクオネガイします！"],
        ["ふふ、オチンチンかたくておっきい！", "では、シツレイしまーす！"],
        None,
        "クチとムネはモンダイないですね",
        "では、つぎはおチンチンのカクニンをします",
        None,
        None,
        "モンダイありますね",
    ]
    for clip, line in zip(story["clips"], want):
        got = spoken_lines(clip["prompt"])
        uniq = []
        for s in got:
            if s not in uniq:
                uniq.append(s)
        if line is None:
            assert uniq == [], (clip["label"], uniq)
        elif isinstance(line, list):
            assert uniq == line, (clip["label"], uniq)
        else:
            assert uniq == [line], (clip["label"], uniq)
        for spoken in uniq:
            assert not _KANJI_RE.search(spoken), spoken
        assert "Doctor: Adult Japanese woman, 32" in clip["prompt"]
        assert "stethoscope" in clip["prompt"]
        assert "Rei: Adult Japanese woman, 24" in clip["prompt"]
        assert "exam room" not in clip["prompt"].lower()
        assert "genkan" in clip["prompt"].lower() or "door" in clip["prompt"].lower()
    assert "Not a clinic" in story["clips"][0]["prompt"]
    c1 = story["clips"][0]["prompt"]
    assert "already at the open door" not in c1
    assert "HIDDEN at the start" in c1
    assert "ENTERS FROM THE RIGHT" in c1
    assert "LEFT" in c1
    assert "Door on the right" in c1 or "door on the right" in c1
    assert "CLOSED front door" in c1 or "CLOSED genkan door" in c1 or "CLOSED front door at the start" in c1
    assert "Do not show Rei until the door opens" in c1
    assert "こんにちは" in c1
    assert "「はい」" in c1
    assert "テイキケンシンにきました" not in c1
    peck = story["clips"][2]["prompt"]
    assert "ふふ、オチンチンかたくておっきい！" in peck
    assert "では、シツレイしまーす！" in peck
    assert "SEDUCTIVE" in peck
    assert "peck" in peck.lower()
    assert "NOT oral" in peck or "not oral" in peck.lower()
    assert "NOT jupo" in peck or "not jupo" in peck.lower()
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
    kiss = story["clips"][3]["prompt"].lower()
    assert "grind" in kiss or "stomach" in kiss
    assert "no freeze" in story["clips"][0]["prompt"].lower() or "not frozen" in story["clips"][0]["prompt"].lower()
    assert "bob" in story["clips"][6]["prompt"].lower()
    assert "ONLY Rei looks pleasured" not in story["clips"][6]["prompt"]
    assert "straight clinical face" not in story["clips"][8]["prompt"]
    assert "immoral" in story["clips"][8]["prompt"].lower()


def test_clinic_kenshin_pack_aya_visits_futa_doctor(tmp_path):
    """医院ケンシン: アヤが来る。医師が20cm。10本＝100秒。パイプ椅子。問診のあと立ち上がりディープキス。押し倒して仰向けジュボ。セックスなし。仰向け口移し。"""
    from h3_lora_studio import (
        ACT_SITUATIONS,
        _KANJI_RE,
        apply_story_play,
        clip_cast_people,
        is_chain_pack,
        is_story,
        load_story,
        prepare_story_clip,
        resolve_situation,
        semen_share_plan,
        situation_ids,
        spoken_lines,
        story_canvas_wh,
        validate_story_follow,
        who_hidden_at_start,
    )

    assert resolve_situation("ケンシン") == "clinic-75s"
    story = load_story("clinic-75s")
    assert story["id"] == "clinic-75s"
    assert story["kind"] == "chain"
    assert story["seamless"] is True
    assert story["spoken_no_kanji"] is True
    assert story["spoken_max"] == 2
    assert story["min_age"] >= 21
    assert story["clip_s"] == 10
    assert story["duration_s"] == 100
    assert story["title_ja"] == "ケンシン100秒"
    assert len(story["clips"]) == 10
    assert [float(c["duration_s"]) for c in story["clips"]] == [10] * 10
    assert [c["situation"] for c in story["clips"]] == [
        "futa_visible",
        "futa_visible",
        "futa_visible",
        "oral",
        "futa_visible",
        "oral",
        "oral",
        "oral_creampie",
        "futa_visible",
        "futa_visible",
    ]
    assert story["canvas"] == {"width": 576, "height": 1024, "aspect": "9:16"}
    assert story_canvas_wh(story) == (576, 1024)
    assert validate_story_follow(story) == []
    assert is_chain_pack("clinic-75s") and not is_story("clinic-75s")
    assert set(story["download"]) == set(situation_ids("clinic-75s"))
    assert "cowgirl-position-h3" not in story["download"]
    assert "cumouf-h3" in story["download"]
    assert "hmnsfw-aio-v25" not in story["download"]
    assert semen_share_plan(story) == [(8, "on_back")]
    want = [
        ["ヨロシクオネガイします！あ、オチンチンおっきい！", "どうぞおすわりください"],
        ["キョウはどうしました？", "サイキンおマンコがウズウズして、、、"],
        ["それはタイヘンですね！じゃあ、みていきますね"],
        [],
        ["もう、ガマンできない！"],
        [],
        [],
        [],
        [],
        ["ゲンキになりましたね", "ありがとうございます"],
    ]
    listed = set(story["download"])
    prev = None
    prev_stack = None
    planned_by_i = []
    for i, clip in enumerate(story["clips"]):
        prompt = clip["prompt"]
        dur = float(clip["duration_s"])
        got = spoken_lines(prompt)
        uniq = []
        for s in got:
            if s not in uniq:
                uniq.append(s)
        assert uniq == want[i], (clip["label"], uniq)
        for s in uniq:
            assert not _KANJI_RE.search(s), s
            assert not re.search(r"[A-Za-z]", s), s
        assert "hmmotion" not in prompt.lower()
        assert "576x1024" not in prompt and "9:16" not in prompt and "16:9" not in prompt
        assert "Full bodies from head to feet" not in prompt
        assert "Doctor: Adult Japanese woman, 32" in prompt
        assert "Clear futanari" in prompt
        assert "Penis plus vagina, never balls" in prompt
        assert "no scrotum" in prompt
        assert "Aya: Adult Japanese woman, 22" in prompt
        assert "NO penis" in prompt
        assert "NEVER futanari" in prompt
        assert "stethoscope" in prompt.lower()
        assert "Rei" not in prompt and "Madoka" not in prompt and "Sayaka" not in prompt
        assert "No men" in prompt
        assert "No feces" in prompt
        assert dur == 10
        assert "15-second" not in prompt
        if uniq:
            assert "LIP SYNC" in prompt
            assert clip["situation"] == "futa_visible"
        if clip["situation"] in ACT_SITUATIONS:
            assert not uniq
            assert "close" in prompt.lower()
        planned = prepare_story_clip(
            story,
            i,
            last_frame=("h3_chain_%d.png" % (i - 1)) if i else None,
            stills_dir=tmp_path,
            prev_situation=prev,
            prev_stack=prev_stack,
        )
        prev = planned["situation"]
        prev_stack = planned["stack"]
        planned_by_i.append(planned)
        assert {row["id"] for row in planned["stack"]} <= listed
        assert planned["width"] == 576 and planned["height"] == 1024
        assert planned["duration_s"] == dur
        assert "SHAFT LOOK:" in planned["prompt"]
        assert "When erect: 20cm" in planned["prompt"]
        if clip["situation"] == "futa_visible":
            _check_visible_plan(planned, prompt)
        for spoken in uniq:
            assert spoken in planned["prompt"]
    c1 = story["clips"][0]["prompt"]
    assert who_hidden_at_start(c1) == {"aya"}
    assert clip_cast_people(story["clips"][0]) == []
    assert "aya" in clip_cast_people(story["clips"][1])
    assert "HIDDEN at the start" in c1
    assert "ENTERS FROM THE RIGHT" in c1
    assert "CLOSED" in c1
    assert "Do not show Aya until the door opens" in c1
    assert "exam" in c1.lower() or "clinic" in c1.lower()
    assert "LEFT" in c1
    assert "legs spread" in c1.lower()
    assert "strok" in c1.lower() or "シコシコ" in c1
    assert "expressionless" in c1.lower()
    assert "どうぞおすわりください" in c1
    assert "RIGHT" in c1
    assert "ツギのヒト" not in c1
    assert "brief wet kiss" in c1.lower()
    assert "STANDS UP" in c1
    assert "BOTH STANDING" in c1 or "both STAND" in c1
    assert "doctor stays STANDING" in c1.lower() or "doctor STANDING" in c1
    assert "steel-pipe" in c1.lower() or "pipe chair" in c1.lower()
    assert "パイプ椅子" not in c1
    multi = c1[c1.find("integrated_multimodal_description:"):]
    assert multi.find("ヨロシクオネガイします！あ、オチンチンおっきい！") < multi.lower().find("brief wet kiss") < multi.find("どうぞおすわりください")
    p0 = planned_by_i[0]
    assert p0["mode"] == "t2v"
    assert "START CAST:" in p0["prompt"]
    assert "SHAFT LOOK:" in p0["prompt"]
    assert "opening of one continuous long take" in p0["prompt"]
    consult = story["clips"][1]["prompt"]
    assert "キョウはどうしました？" in consult
    assert "サイキンおマンコがウズウズして、、、" in consult
    assert "SITS" in consult or "SEATED" in consult
    assert "No deep kiss this clip" in consult
    assert "クチとムネはモンダイないですね" not in consult
    kiss_raw = story["clips"][2]["prompt"]
    kiss = kiss_raw.lower()
    assert "それはタイヘンですね！じゃあ、みていきますね" in kiss_raw
    assert "STANDS UP" in kiss_raw
    assert "SEDUCTIVE" in kiss_raw
    assert "kiss" in kiss
    assert "knead" in kiss or "cup and knead" in kiss
    assert "hands" in kiss and "breast" in kiss
    assert "hand's width" in kiss_raw or "hand’s width" in kiss_raw
    assert "mouth OPEN" in kiss_raw
    assert "ウンチ" not in kiss_raw
    assert "胸は揉まない" not in kiss_raw
    assert "クチとムネはモンダイないですね" not in kiss_raw
    oral = story["clips"][3]["prompt"]
    assert "Already at the BASE" in oral or "already at the BASE" in oral
    assert "NEVER on the shaft" in oral
    assert "pussy" in oral.lower()
    assert "rub" in oral.lower()
    jubo = planned_by_i[3]
    assert "ORAL LOCK:" in jubo["prompt"]
    assert "PLEASURE FACE:" in jubo["prompt"]
    assert "PLEASURE VOICE:" in jubo["prompt"]
    assert "EROTIC WAIT:" in jubo["prompt"]
    assert "blowjob-h3" in [row["id"] for row in jubo["stack"]]
    push = story["clips"][4]["prompt"]
    assert "もう、ガマンできない！" in push
    assert "hand's width" in push or "hand’s width" in push
    assert "NOT in" in push
    assert "LYING ON THEIR BACK" in push
    assert "SEDUCTIVE" in push
    assert "NOT cowgirl" in push or "not cowgirl" in push.lower()
    assert "kneel" in push.lower()
    assert "mouth OPEN" in push
    assert "cowgirl pose" not in push.lower()
    assert "straddl" not in push.lower()
    back1 = story["clips"][5]["prompt"]
    assert not back1.startswith("cowgirl position")
    assert "INSERTION ON CAMERA" not in back1
    assert "LYING ON THEIR BACK" in back1
    assert "Already at the BASE" in back1 or "already at the BASE" in back1
    assert "NEVER on the shaft" in back1
    assert "hmmotion" not in back1.lower()
    back1_p = planned_by_i[5]
    assert "blowjob-h3" in [row["id"] for row in back1_p["stack"]]
    assert "cowgirl-position-h3" not in [row["id"] for row in back1_p["stack"]]
    assert "hmnsfw-aio-v25" not in [row["id"] for row in back1_p["stack"]]
    assert "ORAL LOCK:" in back1_p["prompt"]
    assert "INSIDE LOCK:" not in back1_p["prompt"]
    assert "PLEASURE FACE:" in back1_p["prompt"]
    back2 = story["clips"][6]["prompt"]
    assert "Already at the BASE" in back2 or "already at the BASE" in back2
    assert "LYING ON THEIR BACK" in back2
    assert "jupo" in back2.lower()
    cum = story["clips"][7]["prompt"]
    assert "CUMOUF" in cum
    assert "LYING ON THEIR BACK" in cum
    assert "End: still in her mouth" in cum
    cum_p = planned_by_i[7]
    assert "cumouf-h3" in [row["id"] for row in cum_p["stack"]]
    assert "cowgirl-position-h3" not in [row["id"] for row in cum_p["stack"]]
    share_raw = story["clips"][8]["prompt"]
    assert "STAYS LYING ON THEIR BACK" in share_raw
    assert "leans DOWN" in share_raw
    share = planned_by_i[8]
    assert "SEMEN SHARE:" in share["prompt"]
    assert "STAYS LYING" in share["prompt"]
    assert "mouth-to-mouth" in share["prompt"].lower()
    assert "SAME EYE LEVEL" not in share["prompt"]
    assert "STANDS UP" not in share["prompt"]
    last = planned_by_i[9]
    assert "SEMEN SHARE:" not in last["prompt"]
    assert "ゲンキになりましたね" in last["prompt"]
    assert "ありがとうございます" in last["prompt"]
    assert "LYING ON THEIR BACK" in story["clips"][9]["prompt"]
    assert "STANDING" not in story["clips"][9]["prompt"]
    cast = _write_cast_stills(tmp_path / "cast")
    clinic_ref = apply_story_play(story, "ref_chain")
    r0 = prepare_story_clip(clinic_ref, 0, stills_dir=tmp_path, cast_dir=cast)
    assert r0["mode"] == "t2v"
    assert not r0["still_paths"]
    assert "START CAST:" in r0["prompt"]


def test_speech_drops_cinema_locks_japanese_and_unloads_on_stack_change(tmp_path):
    from h3_lora_studio import (
        audio_lock_line,
        drop_speech_face_killers,
        jp_outside_quotes,
        load_story,
        lock_spoken_japanese,
        prepare_story_clip,
        soundscape_text,
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
    sound = soundscape_text(locked)
    assert "overall_soundscape:" in locked
    assert "[AUDIO-LOCK]" not in locked
    assert locked.count("「こんにちは」") == 1
    assert "「こんにちは」" in sound
    assert "Clinic hum" in sound
    assert "lip-synced" not in sound.lower()
    assert "no other speech" not in sound.lower()
    assert "spoken_transcript" not in locked
    assert "other_text" not in locked
    assert "not_spoken" not in locked
    assert "プロンプトは読まない" not in locked
    assert "台詞だけ" not in locked
    assert jp_outside_quotes(sound) == ""
    from h3_lora_studio import english_except_speech
    mixed = english_except_speech("viscous ドロドロ 「あ、おフロ。。。」 イキ顔")
    assert "「あ、おフロ。。。」" in mixed
    assert "ドロドロ" not in mixed
    assert "イキ顔" not in mixed
    assert "thick gooey" in mixed
    assert "heavy-oil" in mixed
    assert "climax face" in mixed
    silent_lock = lock_spoken_japanese("overall_soundscape:\nKiss. No spoken words.\n", [])
    silent_sound = soundscape_text(silent_lock)
    assert "[AUDIO-LOCK]" not in silent_lock
    assert "spoken_transcript" not in silent_lock
    assert "No spoken words" not in silent_sound
    assert "Kiss" in silent_sound
    assert "誰も話さない" not in silent_lock
    assert "プロンプトは読まない" not in silent_lock
    old = lock_spoken_japanese(
        "overall_soundscape:\n【音声ルール】プロンプトは読まない。英語を音読しない。声に出していいのは日本語の台詞だけ。「こんにちは」英語・中国語・韓国語・ローマ字・意味のわからない音は禁止。台詞のあとに言葉を足さない。余った秒数は無音。口は閉じて部屋の音だけ。\nClinic hum.\n",
        ["こんにちは"],
    )
    assert old.count("[AUDIO-LOCK]") == 0
    assert old.count("「こんにちは」") == 1
    assert "プロンプトは読まない" not in old
    assert "台詞だけ" not in old
    assert "「こんにちは」" in soundscape_text(old)
    assert lock_spoken_japanese(old, ["こんにちは"]).count("[AUDIO-LOCK]") == 0
    assert audio_lock_line(["こんにちは"]) == ""
    from h3_lora_studio import strip_lipsync_speech_meta

    stripped = strip_lipsync_speech_meta(
        "LIP SYNC: One short conversational Japanese line, natural adult voice, not recited, not stretched. "
        "Then the mouth closes. After the line: silence, but bodies keep moving. "
        "She speaks one short conversational line: 「いってらっしゃい」. "
        "Mouth closes. Remaining seconds, silence: bodies keep moving — a look, a weight shift, skin still alive. Do not freeze. End: done."
    )
    assert "Then the mouth closes" not in stripped
    assert "Remaining seconds, silence" not in stripped
    assert "One short conversational Japanese line" not in stripped
    assert "speaks: 「いってらっしゃい」" in stripped
    assert "End: done." in stripped
    assert "prompt" not in audio_lock_line(["こんにちは"]).lower()
    assert strip_audio_lock(old).count("[AUDIO-LOCK]") == 0

    story = load_story("checkup-100s")
    speech = prepare_story_clip(story, 0, stills_dir=tmp_path)
    assert [row["id"] for row in speech["stack"]] == ["penis-lora-h3", "synth-pussy-h3"]
    assert speech["stack_changed"] is False
    assert "[AUDIO-LOCK]" not in speech["prompt"]
    assert "spoken_transcript" not in speech["prompt"]
    assert speech["prompt"].count("「こんにちは」") >= 1
    assert "「こんにちは」" in soundscape_text(speech["prompt"])
    assert "「はい」" in speech["prompt"]
    assert "こんにちは。テイキケンシンにきました" not in speech["prompt"]
    assert "lip-synced" not in soundscape_text(speech["prompt"]).lower()
    assert "SPEECH FACE:" in speech["prompt"]
    assert "こんにちは" in speech["prompt"]
    assert "プロンプトは読まない" not in speech["prompt"]
    assert "DY" not in speech["prompt"].split("\n", 1)[0]
    next_speech = prepare_story_clip(
        story, 1, last_frame="x.png", stills_dir=tmp_path, prev_situation=speech["situation"], prev_stack=speech["stack"]
    )
    assert next_speech["situation"] == "futa_visible"
    assert next_speech["stack_changed"] is False
    assert next_speech["mode"] == "i2v"
    assert "Picture 1" in next_speech["prompt"]
    assert "[AUDIO-LOCK]" not in next_speech["prompt"]
    kiss = prepare_story_clip(
        story, 3, last_frame="x.png", stills_dir=tmp_path, prev_situation=next_speech["situation"], prev_stack=next_speech["stack"]
    )
    assert kiss["situation"] == "futa_visible"
    assert kiss["stack_changed"] is True
    assert stack_signature(kiss["stack"]) != stack_signature(speech["stack"])
    assert [row["id"] for row in kiss["stack"]] == ["penis-lora-h3", "synth-pussy-h3", "larry-v4"]
    assert "spoken_transcript" not in kiss["prompt"]
    assert "誰も話さない" not in kiss["prompt"]
    assert "No spoken words" not in soundscape_text(kiss["prompt"])
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


def test_all_stories_soundscape_is_sfx_and_quotes(tmp_path):
    from h3_lora_studio import load_story, prepare_story_clip, soundscape_text, spoken_lines

    cases = (
        ("sales-visit-60s", 0),
        ("commute-120s", 1),
        ("manhole-30s", 0),
        ("cafe-100s", 1),
    )
    for sid, idx in cases:
        story = load_story(sid)
        planned = prepare_story_clip(story, idx, stills_dir=tmp_path)
        sound = soundscape_text(planned["prompt"])
        lines = spoken_lines(story["clips"][idx]["prompt"])
        assert "lip-synced" not in sound.lower(), (sid, sound)
        assert "no other speech" not in sound.lower(), (sid, sound)
        assert "no spoken words" not in sound.lower(), (sid, sound)
        assert "under a close" not in sound.lower(), (sid, sound)
        assert "adult female voice" not in sound.lower(), (sid, sound)
        assert "[AUDIO-LOCK]" not in planned["prompt"]
        assert "other_text" not in planned["prompt"]
        assert "台詞だけ" not in planned["prompt"]
        for ln in lines:
            assert f"「{ln}」" in sound, (sid, ln, sound)


def test_last_stop_pack_four_clips_rei_seated(tmp_path):
    from h3_lora_studio import _KANJI_RE, load_story, prepare_story_clip, spoken_lines

    story = _check_pack_common(load_story("last-stop-40s"), "last-stop-40s", tmp_path)
    assert story["spoken_no_kanji"] is True
    assert len(story["clips"]) == 4
    assert [c["situation"] for c in story["clips"]] == ["futa_visible", "oral", "oral_creampie", "futa_visible"]
    want = ["しゅうてんです、おきてください", None, None, "おきましたか？おきゃくさん、しゅうてんだからおりてください"]
    for clip, line in zip(story["clips"], want):
        got = spoken_lines(clip["prompt"])
        assert (got[0] if got else None) == line, clip["label"]
        for spoken in got:
            assert not _KANJI_RE.search(spoken), spoken
        assert "Conductor: Adult Japanese woman, 29" in clip["prompt"]
        assert "whistle" in clip["prompt"]
        assert "seated" in clip["prompt"].lower() or "sits" in clip["prompt"].lower()
    assert "does NOT wake" in story["clips"][0]["prompt"]
    assert "already kneeling, mouth open at the tip" in story["clips"][0]["prompt"]
    assert "does not kneel yet" not in story["clips"][0]["prompt"]
    assert "flutter open" in story["clips"][1]["prompt"]
    assert "slides down" not in story["clips"][1]["prompt"]
    assert "Glans already inside" in story["clips"][1]["prompt"]
    assert "not licking" in story["clips"][1]["prompt"].lower()
    assert "tight ring around the shaft" in story["clips"][1]["prompt"]
    assert "conductor again" in story["clips"][3]["prompt"]
    jubo = prepare_story_clip(story, 1, last_frame="x.png", stills_dir=tmp_path)
    assert "ORAL LOCK:" in jubo["prompt"]
    assert "not licking" in jubo["prompt"].lower()
    talk = prepare_story_clip(story, 0, stills_dir=tmp_path)
    assert "ORAL LOCK:" not in talk["prompt"]


def test_last_train_pack_platform_jupo_after_waking(tmp_path):
    """終電: 2人だけ。声かけはレイに向ける。ジュボ20秒→口内口移しで起こす→ホームへ。濃厚キス→ピロートーク→立ちジュボ→口内→抱擁口移し。セックスなし。全部10秒（15秒禁止）。"""
    from h3_lora_studio import (
        ACT_SITUATIONS,
        _KANJI_RE,
        clip_cast_people,
        is_chain_pack,
        is_story,
        load_story,
        prepare_story_clip,
        resolve_situation,
        semen_share_plan,
        situation_ids,
        spoken_lines,
        story_canvas_wh,
        validate_story_follow,
    )

    assert resolve_situation("終電") == "last-train-120s"
    assert resolve_situation("終点（専用）") == "last-stop-40s"
    story = load_story("last-train-120s")
    assert story["id"] == "last-train-120s"
    assert story["kind"] == "chain"
    assert story["seamless"] is True
    assert story["spoken_no_kanji"] is True
    assert story["spoken_max"] == 2
    assert story["min_age"] >= 21
    assert story["duration_s"] == 100
    assert "15秒禁止" in story["comment_ja"]
    assert "10本＝100秒" in story["comment_ja"]
    assert len(story["clips"]) == 10
    assert [float(c["duration_s"]) for c in story["clips"]] == [10] * 10
    assert [c["situation"] for c in story["clips"]] == [
        "futa_visible",
        "oral",
        "oral",
        "oral_creampie",
        "futa_visible",
        "futa_visible",
        "futa_visible",
        "oral",
        "oral_creampie",
        "futa_visible",
    ]
    assert story["canvas"] == {"width": 576, "height": 1024, "aspect": "9:16"}
    assert story_canvas_wh(story) == (576, 1024)
    assert validate_story_follow(story) == []
    assert is_chain_pack("last-train-120s") and not is_story("last-train-120s")
    assert set(story["download"]) == set(situation_ids("last-train-120s"))
    assert "cowgirl-position-h3" not in story["download"]
    assert "hmcumshot-v2" not in story["download"]
    assert "cumouf-h3" in story["download"]
    assert "final-thrust-h3" not in story["download"]
    assert semen_share_plan(story) == [(3, "on_cumouf"), (9, "silent_next")]
    want = [
        ["しゅうてんです、おきてください"],
        [],
        [],
        [],
        [],
        [],
        ["んっ、おくちにだしてもらって、からだがあつい、、、", "おくち、あったかい、、、もっとして、、、"],
        [],
        [],
        [],
    ]
    listed = set(story["download"])
    prev = None
    prev_stack = None
    planned_by_i = []
    for i, clip in enumerate(story["clips"]):
        prompt = clip["prompt"]
        dur = float(clip["duration_s"])
        got = spoken_lines(prompt)
        uniq = []
        for s in got:
            if s not in uniq:
                uniq.append(s)
        assert uniq == want[i], (clip["label"], uniq)
        for s in uniq:
            assert not _KANJI_RE.search(s), s
            assert not re.search(r"[A-Za-z]", s), s
        assert "hmmotion" not in prompt.lower()
        assert "576x1024" not in prompt and "9:16" not in prompt and "16:9" not in prompt
        assert "Full bodies from head to feet" not in prompt
        assert "Conductor: Adult Japanese woman, 29" in prompt
        assert "NO penis" in prompt
        assert "NEVER futanari" in prompt
        assert "whistle" in prompt.lower()
        assert "Rei: Adult Japanese woman, 24" in prompt
        assert "Clear futanari" in prompt
        assert "Penis plus vagina, never balls" in prompt
        assert "no scrotum" in prompt
        if i < 4:
            assert "does not stand" in prompt.lower() or "never stands" in prompt.lower() or "stays on the bench" in prompt.lower()
        else:
            assert "STANDING" in prompt or "STANDS UP" in prompt
            assert "never stands" not in prompt.lower()
            assert "does not stand" not in prompt.lower()
        assert "No men" in prompt
        assert "No feces" in prompt
        assert "TWO WOMEN ONLY" in prompt
        assert "Do not add a third person" in prompt
        assert not re.search(r"\bAya\b", prompt)
        assert "Sayaka" not in prompt
        assert "Madoka" not in prompt
        assert "15-second" not in prompt
        assert "10-second take" in prompt
        assert dur == 10
        if uniq:
            assert "LIP SYNC" in prompt
            assert clip["situation"] == "futa_visible"
        if clip["situation"] in ACT_SITUATIONS:
            assert not uniq
            assert "close" in prompt.lower()
        planned = prepare_story_clip(
            story,
            i,
            last_frame=("h3_chain_%d.png" % (i - 1)) if i else None,
            stills_dir=tmp_path,
            prev_situation=prev,
            prev_stack=prev_stack,
        )
        prev = planned["situation"]
        prev_stack = planned["stack"]
        planned_by_i.append(planned)
        assert {row["id"] for row in planned["stack"]} <= listed
        assert planned["width"] == 576 and planned["height"] == 1024
        assert planned["duration_s"] == dur
        assert "SHAFT LOOK:" in planned["prompt"]
        for spoken in uniq:
            assert spoken in planned["prompt"]
    c1 = story["clips"][0]["prompt"]
    assert "does NOT wake" in c1
    assert "already kneeling, mouth OPEN at the tip" in c1 or "mouth OPEN at the tip" in c1
    assert "hand's width" in c1
    assert "whole body and face toward seated Rei" in c1
    assert "not to the camera" in c1
    assert "not down the aisle" in c1
    assert "not into the camera" in c1
    oral1 = story["clips"][1]["prompt"]
    assert "Already at the BASE" in oral1 or "already at the BASE" in oral1
    assert "flutter open" in oral1
    assert "Glans already inside" in oral1
    assert "not licking" in oral1.lower()
    oral2 = story["clips"][2]["prompt"]
    assert "Already at the BASE" in oral2 or "already at the BASE" in oral2
    assert "already awake" in oral2.lower()
    cum = story["clips"][3]["prompt"]
    assert "CUMOUF" in cum
    assert "End: still in her mouth" in cum
    assert "viscous" in cum.lower() or "sticky" in cum.lower() or "ドロドロ" in cum
    walk = story["clips"][4]["prompt"]
    assert "station platform" in walk.lower()
    assert "STANDS UP" in walk
    assert spoken_lines(walk) == []
    kiss = story["clips"][5]["prompt"]
    assert "station platform" in kiss.lower()
    assert "kiss" in kiss.lower()
    assert spoken_lines(kiss) == []
    talk = story["clips"][6]["prompt"]
    assert "hand's width" in talk
    assert "NOT in" in talk
    assert "mouth OPEN" in talk
    assert "kneel" in talk.lower()
    assert "STANDING" in talk
    jubo2 = story["clips"][7]["prompt"]
    assert "Already at the BASE" in jubo2 or "already at the BASE" in jubo2
    assert "STANDING" in jubo2
    assert "kneel" in jubo2.lower()
    plat_cum = story["clips"][8]["prompt"]
    assert "CUMOUF" in plat_cum
    assert "End: still in her mouth" in plat_cum
    hug = story["clips"][9]["prompt"]
    assert "STANDS UP" in hug
    assert "SAME EYE LEVEL" in hug
    assert "embrac" in hug.lower() or "hug" in hug.lower()
    p0 = planned_by_i[0]
    assert p0["mode"] == "t2v"
    jubo = planned_by_i[1]
    assert "ORAL LOCK:" in jubo["prompt"]
    assert "PLEASURE FACE:" in jubo["prompt"]
    assert "cowgirl-position-h3" not in [row["id"] for row in jubo["stack"]]
    share = planned_by_i[3]
    assert "SEMEN SHARE:" in share["prompt"]
    assert "SAME EYE LEVEL" in share["prompt"]
    assert "mouth-to-mouth" in share["prompt"].lower()
    assert "ORGASM FACE:" in share["prompt"]
    walk_p = planned_by_i[4]
    assert "SEMEN SHARE:" not in walk_p["prompt"]
    kiss_p = planned_by_i[5]
    assert "SEMEN SHARE:" not in kiss_p["prompt"]
    plat_jubo = planned_by_i[7]
    assert "ORAL LOCK:" in plat_jubo["prompt"]
    assert "cowgirl-position-h3" not in [row["id"] for row in plat_jubo["stack"]]
    assert "INSIDE LOCK:" not in plat_jubo["prompt"]
    plat_cum_p = planned_by_i[8]
    assert "cumouf-h3" in [row["id"] for row in plat_cum_p["stack"]]
    assert "SEMEN SHARE:" not in plat_cum_p["prompt"]
    hug_p = planned_by_i[9]
    assert "SEMEN SHARE:" in hug_p["prompt"]
    assert "SAME EYE LEVEL" in hug_p["prompt"]
    assert "STANDS UP" in hug_p["prompt"]
    assert "mouth-to-mouth" in hug_p["prompt"].lower()
    assert "INSIDE LOCK:" not in jubo["prompt"]
    assert "ORAL LOCK:" in jubo["prompt"]
    for clip in story["clips"]:
        assert clip_cast_people(clip) == ["rei"], clip["id"]


def test_semen_bath_pack_aya_rei_ofuro(tmp_path):
    """ザーメン風呂: アヤが湯船、レイが20cmで白い粘液を溜める。口移しなし。"""
    from h3_lora_studio import (
        ACT_SITUATIONS,
        _KANJI_RE,
        is_chain_pack,
        is_story,
        load_story,
        prepare_story_clip,
        resolve_situation,
        semen_share_plan,
        situation_ids,
        spoken_lines,
        story_canvas_wh,
        validate_story_follow,
    )

    assert resolve_situation("ザーメン風呂") == "semen-bath-70s"
    story = load_story("semen-bath-70s")
    assert story["id"] == "semen-bath-70s"
    assert story["kind"] == "chain"
    assert story["seamless"] is True
    assert story["spoken_no_kanji"] is True
    assert story["spoken_max"] == 2
    assert story["duration_s"] == 50
    assert len(story["clips"]) == 5
    assert [float(c["duration_s"]) for c in story["clips"]] == [10, 10, 10, 10, 10]
    assert [c["situation"] for c in story["clips"]] == [
        "futa_visible",
        "after_ejaculation",
        "after_ejaculation",
        "after_ejaculation",
        "after_ejaculation",
    ]
    assert story["canvas"] == {"width": 576, "height": 1024, "aspect": "9:16"}
    assert story_canvas_wh(story) == (576, 1024)
    assert validate_story_follow(story) == []
    assert is_chain_pack("semen-bath-70s") and not is_story("semen-bath-70s")
    assert set(story["download"]) == set(situation_ids("semen-bath-70s"))
    assert "hmcumshot-v2" in story["download"]
    assert "blowjob-h3" not in story["download"]
    assert "cumouf-h3" not in story["download"]
    assert semen_share_plan(story) == []
    want = [
        ["ザーメンフロにして", "いっぱいだすね"],
        [],
        [],
        [],
        [],
    ]
    listed = set(story["download"])
    prev = None
    prev_stack = None
    for i, clip in enumerate(story["clips"]):
        prompt = clip["prompt"]
        dur = float(clip["duration_s"])
        got = spoken_lines(prompt)
        uniq = []
        for s in got:
            if s not in uniq:
                uniq.append(s)
        assert uniq == want[i], (clip["label"], uniq)
        for s in uniq:
            assert not _KANJI_RE.search(s), s
            assert not re.search(r"[A-Za-z]", s), s
        assert "hmmotion" not in prompt.lower()
        assert "576x1024" not in prompt and "9:16" not in prompt and "16:9" not in prompt
        assert "Aya: Adult Japanese woman, 22" in prompt
        assert "NO penis" in prompt
        assert "NEVER futanari" in prompt
        assert "Rei: Adult Japanese woman, 24" in prompt
        assert "Clear futanari" in prompt
        assert "Penis plus vagina, never balls" in prompt
        assert "ofuro" in prompt.lower()
        assert "No men" in prompt
        assert "Doctor" not in prompt and "Conductor" not in prompt
        assert "Madoka" not in prompt and "Sayaka" not in prompt
        if clip["situation"] == "after_ejaculation":
            assert "viscous" in prompt.lower() or "sticky" in prompt.lower() or "ドロドロ" in prompt
            assert "white liquid" in prompt.lower()
        if uniq:
            assert "LIP SYNC" in prompt
        else:
            assert dur == 10
            assert "15-second" not in prompt
        if clip["situation"] in ACT_SITUATIONS:
            assert not uniq
            assert "close" in prompt.lower()
        planned = prepare_story_clip(
            story,
            i,
            last_frame=("h3_chain_%d.png" % (i - 1)) if i else None,
            stills_dir=tmp_path,
            prev_situation=prev,
            prev_stack=prev_stack,
        )
        prev = planned["situation"]
        prev_stack = planned["stack"]
        assert {row["id"] for row in planned["stack"]} <= listed
        assert planned["width"] == 576 and planned["height"] == 1024
        assert "SHAFT LOOK:" in planned["prompt"]
        assert "SEMEN SHARE:" not in planned["prompt"]
        if clip["situation"] == "after_ejaculation":
            assert "hmcumshot-v2" in [row["id"] for row in planned["stack"]]
            assert "ORGASM FACE:" in planned["prompt"]
    c1 = story["clips"][0]["prompt"]
    assert "NOT in Aya" in c1 or "not in Aya" in c1
    assert "aimed" in c1.lower()
    soak = story["clips"][2]["prompt"]
    assert "bath" in soak.lower() or "ofuro" in soak.lower()
    scoop = story["clips"][3]["prompt"]
    assert "scoop" in scoop.lower()
    overflow = story["clips"][4]["prompt"]
    assert "overflow" in overflow.lower()


def test_meat_wall_pack_brown_slime_white_tub(tmp_path):
    """ニクカベ: 肉壁の中。茶色い粘液＋白いおフロ。顔は液面より上。口内のあと立ち上がって口移し。家のザーメン風呂とは別。"""
    from h3_lora_studio import (
        ACT_SITUATIONS,
        _KANJI_RE,
        is_chain_pack,
        is_story,
        load_story,
        prepare_story_clip,
        resolve_situation,
        semen_share_plan,
        situation_ids,
        spoken_lines,
        story_canvas_wh,
        validate_story_follow,
    )

    assert resolve_situation("ニクカベ") == "meat-wall-85s"
    assert resolve_situation("肉壁") == "meat-wall-85s"
    assert resolve_situation("肉壁のザーメン風呂") == "meat-wall-85s"
    assert resolve_situation("ニクカベ風呂") == "meat-wall-85s"
    assert resolve_situation("ニクカベ（専用）") == "meat-wall-85s"
    assert resolve_situation("ザーメン風呂") == "semen-bath-70s"
    story = load_story("meat-wall-85s")
    assert story["id"] == "meat-wall-85s"
    assert story["kind"] == "chain"
    assert story["seamless"] is True
    assert story["spoken_no_kanji"] is True
    assert story["spoken_max"] == 2
    assert story["min_age"] >= 21
    assert story["duration_s"] == 70
    assert len(story["clips"]) == 7
    assert [float(c["duration_s"]) for c in story["clips"]] == [10, 10, 10, 10, 10, 10, 10]
    assert [c["situation"] for c in story["clips"]] == [
        "futa_visible",
        "futa_visible",
        "futa_visible",
        "futa_visible",
        "oral",
        "oral_creampie",
        "futa_visible",
    ]
    assert story["canvas"] == {"width": 576, "height": 1024, "aspect": "9:16"}
    assert story_canvas_wh(story) == (576, 1024)
    assert validate_story_follow(story) == []
    assert is_chain_pack("meat-wall-85s") and not is_story("meat-wall-85s")
    assert set(story["download"]) == set(situation_ids("meat-wall-85s"))
    assert "blowjob-h3" in story["download"]
    assert "cumouf-h3" in story["download"]
    assert "hmnsfw-aio-v25" not in story["download"]
    assert semen_share_plan(story) == [(6, "after_speech")]
    want = [
        ["うわぁ。。。すごいところだね。。。"],
        ["あ、おフロ。。。でもこれって", "ザーメンの、、、おフロ、、、すごいニオイ、、、"],
        ["ザーメンのおフロ。。。あったかーい"],
        ["もうガマンできない！おチンチンジュボジュボするの！"],
        [],
        [],
        ["レイのザーメンおいしかった！"],
    ]
    listed = set(story["download"])
    prev = None
    prev_stack = None
    planned_by_i = []
    for i, clip in enumerate(story["clips"]):
        prompt = clip["prompt"]
        dur = float(clip["duration_s"])
        got = spoken_lines(prompt)
        uniq = []
        for s in got:
            if s not in uniq:
                uniq.append(s)
        assert uniq == want[i], (clip["label"], uniq)
        for s in uniq:
            assert not _KANJI_RE.search(s), s
            assert not re.search(r"[A-Za-z]", s), s
        assert "hmmotion" not in prompt.lower()
        assert "576x1024" not in prompt and "9:16" not in prompt and "16:9" not in prompt
        assert "Full bodies from head to feet" not in prompt
        assert "Aya: Adult Japanese woman, 22" in prompt
        assert "NO penis" in prompt
        assert "NEVER futanari" in prompt
        assert "Rei: Adult Japanese woman, 24" in prompt
        assert "Clear futanari" in prompt
        assert "Penis plus vagina, never balls" in prompt
        assert "no scrotum" in prompt
        assert "No men" in prompt
        if story["id"] == "meat-wall-85s":
            assert "No feces" in prompt
        assert "Doctor" not in prompt and "Conductor" not in prompt
        assert "Madoka" not in prompt and "Sayaka" not in prompt
        if clip["situation"] not in ACT_SITUATIONS and i not in {3, 4, 5}:
            assert "above" in prompt.lower()
        if clip["situation"] in ACT_SITUATIONS or i == 3:
            assert "Do not dunk" not in prompt
            assert "only her lower body" not in prompt.lower()
        assert "brown" in prompt.lower()
        assert "no concrete" in prompt.lower()
        assert "ORGANISM LOCK:" in prompt
        assert "giant living organism" in prompt.lower()
        assert "living flesh" in prompt.lower() or "living fleshy" in prompt.lower()
        assert dur == 10
        assert "15-second" not in prompt
        if uniq:
            assert "LIP SYNC" in prompt
            assert clip["situation"] == "futa_visible"
        if clip["situation"] in ACT_SITUATIONS:
            assert not uniq
            assert "close" in prompt.lower()
        planned = prepare_story_clip(
            story,
            i,
            last_frame=("h3_chain_%d.png" % (i - 1)) if i else None,
            stills_dir=tmp_path,
            prev_situation=prev,
            prev_stack=prev_stack,
        )
        prev = planned["situation"]
        prev_stack = planned["stack"]
        planned_by_i.append(planned)
        assert {row["id"] for row in planned["stack"]} <= listed
        assert planned["width"] == 576 and planned["height"] == 1024
        assert planned["duration_s"] == dur
        assert "SHAFT LOOK:" in planned["prompt"]
        if i != 6:
            assert "SEMEN SHARE:" not in planned["prompt"]
        for spoken in uniq:
            assert spoken in planned["prompt"]
    walk = story["clips"][0]["prompt"]
    assert "Walk only" in walk or "walking" in walk.lower()
    assert "No tub yet" in walk
    assert "LIP SYNC" in walk
    assert "fingers laced" in walk.lower()
    assert "French" in walk
    assert "leave at once" in walk.lower()
    assert "NOT oral" in walk or "not oral" in walk.lower()
    assert "NOT jupo" in walk or "not jupo" in walk.lower()
    assert "Do not squat" in walk or "does not squat" in walk.lower()
    assert "Do not stop walking" in walk or "keep walking" in walk.lower()
    assert "No kiss yet" not in walk
    assert "No speech" not in walk
    assert "Already oral" not in walk
    assert "jupo-jupo" not in walk.lower()
    assert "slime" in walk.lower()
    assert "FLOOR LOCK" in walk
    assert "springy" in walk.lower() and "elastic" in walk.lower()
    assert "gives under" not in walk.lower()
    assert "quicksand" in walk.lower()
    assert "feet stay on the surface" in walk.lower()
    assert "swallow feet" in walk.lower() or "swallow walkers" in walk.lower()
    assert "soft meat floor" not in walk.lower()
    assert "ALREADY a clear futanari" in walk
    assert "ALWAYS" in walk or "LOWER THIRD" in walk
    assert "does NOT grow out" in walk or "does not grow out" in walk.lower()
    assert "whole body" in walk.lower() or "face, hair" in walk.lower()
    p_walk = planned_by_i[0]
    _check_visible_plan(p_walk, walk)
    assert [row["id"] for row in p_walk["stack"]] == ["penis-lora-h3", "synth-pussy-h3"]
    assert p_walk["sampler"]["steps"] == 12
    assert "larry-v4" not in [row["id"] for row in p_walk["stack"]]
    assert "PLEASURE VOICE:" in p_walk["prompt"]
    assert "EROTIC WAIT:" in p_walk["prompt"]
    assert "FUTA LOCK:" in p_walk["prompt"]
    assert "BROWN SLIME:" in p_walk["prompt"]
    assert "BATH LOOK:" in p_walk["prompt"]
    assert "glue" in p_walk["prompt"].lower() or "paste-thick" in p_walk["prompt"].lower()
    assert "heavy-oil" in p_walk["prompt"].lower()
    assert "industrial-sludge" in p_walk["prompt"].lower() or "waste-oil" in p_walk["prompt"].lower()
    assert "never brown" in p_walk["prompt"].lower() or "never black" in p_walk["prompt"].lower()
    enter = story["clips"][1]["prompt"]
    assert "climb" in enter.lower()
    assert "chest" in enter.lower()
    assert "not water" in enter.lower() or "glue" in enter.lower() or "paste-thick" in enter.lower()
    kiss = story["clips"][2]["prompt"]
    assert "kiss" in kiss.lower()
    assert "STANDS OUT" in kiss
    assert "LOWER THIRD" in kiss or "above the white" in kiss.lower()
    kiss_p = planned_by_i[2]
    assert [row["id"] for row in kiss_p["stack"]] == ["penis-lora-h3", "synth-pussy-h3"]
    assert kiss_p["sampler"]["steps"] == 12
    prep = story["clips"][3]["prompt"]
    assert "hand's width" in prep
    assert "NOT in" in prep or "not in her mouth" in prep.lower()
    jupo = story["clips"][4]["prompt"]
    assert "Already at the BASE" in jupo or "already at the BASE" in jupo
    assert "Glans already inside" in jupo
    assert "not licking" in jupo.lower()
    assert "Do not dunk" not in jupo
    assert "only her lower body" not in jupo.lower()
    cum = story["clips"][5]["prompt"]
    assert "CUMOUF" in cum
    assert "viscous" in cum.lower() or "sticky" in cum.lower() or "ドロドロ" in cum
    assert "HOLD" in cum or "Do not swallow it all" in cum
    assert "swallows every drop" not in cum.lower()
    tasty = story["clips"][6]["prompt"]
    assert "レイのザーメンおいしかった！" in tasty
    assert "STANDS UP" in tasty
    assert planned_by_i[0]["mode"] == "t2v"
    oral_p = planned_by_i[4]
    assert "ORAL LOCK:" in oral_p["prompt"]
    assert "JUPO DEPTH:" in oral_p["prompt"]
    assert "Ignore how deep" in oral_p["prompt"]
    assert "Do not dunk" not in oral_p["prompt"]
    assert "PLEASURE FACE:" in oral_p["prompt"]
    assert "blowjob-h3" in [row["id"] for row in oral_p["stack"]]
    cum_p = planned_by_i[5]
    assert "ORGASM FACE:" in cum_p["prompt"]
    assert "JUPO DEPTH:" in cum_p["prompt"]
    assert "SEMEN SHARE:" not in cum_p["prompt"]
    assert "cumouf-h3" in [row["id"] for row in cum_p["stack"]]
    last_p = planned_by_i[6]
    assert "SEMEN SHARE:" in last_p["prompt"]
    assert "STANDS UP" in last_p["prompt"]
    assert "SAME EYE LEVEL" in last_p["prompt"]
    assert "mouth-to-mouth" in last_p["prompt"].lower()


def test_meat_wall_cesspit_pack_semen_coat_then_filth(tmp_path):
    """ニクカベ肥溜め: 白いザーメンまみれ→肥溜め肩まで→濃厚ニクカベと同じエロ。ジュボは深さ判定なし。"""
    from h3_lora_studio import (
        ACT_SITUATIONS,
        _KANJI_RE,
        english_except_speech,
        is_chain_pack,
        is_story,
        jp_outside_quotes,
        load_story,
        prepare_story_clip,
        resolve_situation,
        semen_share_plan,
        situation_ids,
        spoken_lines,
        story_canvas_wh,
        validate_story_follow,
    )

    assert resolve_situation("ニクカベ") == "meat-wall-85s"
    assert resolve_situation("ニクカベ肥溜め") == "meat-wall-cesspit-70s"
    assert resolve_situation("肉壁肥溜め") == "meat-wall-cesspit-70s"
    assert resolve_situation("ニクヘキ肥溜め") == "meat-wall-cesspit-70s"
    assert resolve_situation("ニクカベ肥溜め（専用）") == "meat-wall-cesspit-70s"
    story = load_story("meat-wall-cesspit-70s")
    assert story["id"] == "meat-wall-cesspit-70s"
    assert story["kind"] == "chain"
    assert story["seamless"] is True
    assert story["spoken_no_kanji"] is True
    assert story["spoken_max"] == 2
    assert story["min_age"] >= 21
    assert story["duration_s"] == 70
    assert len(story["clips"]) == 7
    assert [float(c["duration_s"]) for c in story["clips"]] == [10] * 7
    assert [c["situation"] for c in story["clips"]] == [
        "futa_visible",
        "futa_visible",
        "futa_visible",
        "futa_visible",
        "oral",
        "oral_creampie",
        "futa_visible",
    ]
    assert story["canvas"] == {"width": 576, "height": 1024, "aspect": "9:16"}
    assert story_canvas_wh(story) == (576, 1024)
    assert validate_story_follow(story) == []
    assert is_chain_pack("meat-wall-cesspit-70s") and not is_story("meat-wall-cesspit-70s")
    assert set(story["download"]) == set(situation_ids("meat-wall-cesspit-70s"))
    assert semen_share_plan(story) == [(6, "after_speech")]
    want = [
        ["うわぁ。。。あんなにおおきいコエダメだね。。。しろいのがからだじゅうについてる、、、あたままで、あしさきまで"],
        ["このニオイ、、、アタマおかしくなりそう、、、こんなにこくて、うんこのニオイ、いきもできない、、、アタマおかしくなりそう、、、"],
        ["んっ、キスして、、、あたまおかしくなりそう、、、こんなこえだめのなかで、あたままでうんこまみれなのに、キスして、、、"],
        ["もうガマンできない！おチンチンジュボジュボするの！こんなこえだめのなかでも、れいのおチンチン、おくまでジュボジュボするの！"],
        [],
        [],
        ["レイのザーメンおいしかった！こんなにこくてしろいの、おくまでだしてもらって、あたまおかしくなりそう、、、"],
    ]
    listed = set(story["download"])
    prev = None
    prev_stack = None
    planned_by_i = []
    for i, clip in enumerate(story["clips"]):
        prompt = clip["prompt"]
        uniq = list(dict.fromkeys(spoken_lines(prompt)))
        assert uniq == want[i], (clip["label"], uniq)
        for s in uniq:
            assert not _KANJI_RE.search(s), s
            assert not re.search(r"[A-Za-z]", s), s
        assert "No feces" not in prompt
        assert "Then the mouth closes" not in prompt
        assert "Remaining seconds, silence" not in prompt
        assert "Do not dunk" not in prompt
        assert "only her lower body" not in prompt.lower()
        assert "hmmotion" not in prompt.lower()
        assert "ORGANISM LOCK:" in prompt
        assert "cesspit" in prompt.lower()
        if i == 0:
            assert "fecal" in prompt.lower() or "cesspit" in prompt.lower()
            assert "HEAD TO TOE" in prompt
            assert "WHITE" in prompt
        else:
            assert "fecal" in prompt.lower()
            assert "HEAD TO TOE" in prompt
        if clip["situation"] in ACT_SITUATIONS:
            assert not uniq
            assert "close" in prompt.lower()
        leftover = jp_outside_quotes(english_except_speech(prompt))
        assert leftover == "", leftover[:80]
        planned = prepare_story_clip(
            story,
            i,
            last_frame=("h3_chain_%d.png" % (i - 1)) if i else None,
            stills_dir=tmp_path,
            prev_situation=prev,
            prev_stack=prev_stack,
        )
        prev = planned["situation"]
        prev_stack = planned["stack"]
        planned_by_i.append(planned)
        assert {row["id"] for row in planned["stack"]} <= listed
        assert planned["width"] == 576 and planned["height"] == 1024
        assert "SHAFT LOOK:" in planned["prompt"]
        assert "FUTA LOCK:" in planned["prompt"]
        leftover_p = jp_outside_quotes(planned["prompt"])
        assert leftover_p == "", leftover_p[:80]
        if i == 0:
            assert "SEMEN COAT:" in planned["prompt"]
            assert "CESSPIT LOOK:" not in planned["prompt"]
        else:
            assert "CESSPIT LOOK:" in planned["prompt"]
        if clip["situation"] in ACT_SITUATIONS:
            assert "JUPO DEPTH:" in planned["prompt"]
            assert "Ignore how deep" in planned["prompt"]
    walk = story["clips"][0]["prompt"]
    assert "FLOOR LOCK" in walk
    assert "No tub yet" not in walk
    assert "French" in walk
    enter = story["clips"][1]["prompt"]
    assert "shoulder-deep" in enter.lower()
    assert "このニオイ、、、アタマおかしくなりそう、、、" in enter
    kiss = story["clips"][2]["prompt"]
    assert "kiss" in kiss.lower()
    prep = story["clips"][3]["prompt"]
    assert "hand's width" in prep
    jupo = story["clips"][4]["prompt"]
    assert "Already at the BASE" in jupo or "already at the BASE" in jupo
    tasty = story["clips"][6]["prompt"]
    assert "STANDS UP" in tasty
    assert "レイのザーメンおいしかった！" in tasty
    last_p = planned_by_i[6]
    assert "SEMEN SHARE:" in last_p["prompt"]
    assert "SAME EYE LEVEL" in last_p["prompt"]


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


def test_lock_futa_shaft_pins_20cm_and_skips_never_futanari(tmp_path):
    from h3_lora_studio import lock_futa_shaft, load_story, prepare_story_clip

    raw = (
        "Clear futanari. Erect 20cm, pale shaft, pink glans.\n"
        "overall_soundscape:\nStreet."
    )
    out = lock_futa_shaft(raw)
    assert "SHAFT LOOK:" in out
    assert "When erect: 20cm" in out
    assert "thick human girth" in out
    assert "NO testicles" in out
    assert "never balls" in out.lower()
    assert "NEVER futanari stay NO penis" in out
    assert out.find("SHAFT LOOK:") < out.find("overall_soundscape:")
    assert lock_futa_shaft(out) == out
    never = "Aya: Adult Japanese woman, 22, fully nude, hairless, NO penis, NEVER futanari."
    assert "SHAFT LOOK:" not in lock_futa_shaft(never)

    sales = prepare_story_clip(load_story("sales-visit-60s"), 0, stills_dir=tmp_path)
    assert "SHAFT LOOK:" in sales["prompt"]
    assert "When erect: 20cm" in sales["prompt"]
    cafe0 = prepare_story_clip(load_story("cafe-100s"), 0, stills_dir=tmp_path)
    assert "SHAFT LOOK:" not in cafe0["prompt"]
    cafe1 = prepare_story_clip(
        load_story("cafe-100s"), 1, last_frame="x.png", stills_dir=tmp_path
    )
    assert "SHAFT LOOK:" in cafe1["prompt"]
    commute1 = prepare_story_clip(
        load_story("commute-120s"), 1, last_frame="x.png", stills_dir=tmp_path
    )
    assert "SHAFT LOOK:" in commute1["prompt"]


def test_lock_semen_look_names_white_liquid():
    from h3_lora_studio import lock_semen_look

    semen = lock_semen_look("CUMOUF. She cums inside the mouth. Not a facial.")
    assert "white liquid" in semen.lower()
    assert "viscous" in semen.lower()
    assert "clingy" in semen.lower()
    assert "heavy-oil" in semen.lower()
    assert "never brown" in semen.lower()
    assert "never black" in semen.lower()
    assert "paste-thick" in semen.lower() or "glue" in semen.lower()
    assert "clings" in semen.lower()
    assert "slick" in semen.lower()
    assert "glans tip" in semen.lower()
    assert "stays on the face" in semen.lower()
    assert "too much" in semen.lower()
    assert "overflow" in semen.lower()
    assert "mouthful" in semen.lower()
    assert lock_semen_look(semen) == semen
    assert "SEMEN LOOK:" not in lock_semen_look("Already oral. Mouth already on. No climax.")
    by_sit = lock_semen_look("Close side view. Lips wrapped.", situation="oral_creampie")
    assert "white liquid" in by_sit.lower()
    face = lock_semen_look("Already a facial. Thick white cum on her cheek.", situation="facial")
    assert "clingy" in face.lower()
    assert "clings" in face.lower()
    assert "slick" in face.lower()
    assert "heavy-oil" in face.lower()
    after = lock_semen_look("Already after ejaculation. The semen stays.", situation="after_ejaculation")
    assert "stays on the face" in after.lower()


def test_lock_speech_urine_pleasure_and_heat_face():
    from h3_lora_studio import (
        lock_pleasure_face,
        lock_spoken_emotion,
        lock_urine_look,
    )

    speech = lock_spoken_emotion(
        "LIP SYNC: face large.\n「こんにちは」\n\noverall_soundscape:\nVoice.\n"
    )
    assert "SPEECH FACE:" in speech
    assert "Not monotone" in speech
    assert lock_spoken_emotion(speech) == speech
    heat = lock_spoken_emotion(
        "LIP SYNC: face large.\n「あちぃー」\n「あー、すずしい！いきかえるー！」\n\noverall_soundscape:\nCicadas.\n"
    )
    assert "HEAT FACE:" in heat
    assert "Midsummer" in heat
    tea = lock_spoken_emotion(
        "LIP SYNC: both faces.\n「はい。あついのとひやし、どっち」\n「ひやしで」\n\noverall_soundscape:\nRail.\n"
    )
    assert "SPEECH FACE:" in tea
    assert "HEAT FACE:" not in tea

    pee = lock_urine_look(
        "She drinks the yellow stream.\n\noverall_soundscape:\nHiss.\n"
    )
    assert "URINE LOOK:" in pee
    assert "urethral opening at the glans tip" in pee
    assert "yellow urine" in pee.lower()
    assert lock_urine_look(pee) == pee
    not_yet = lock_urine_look("Door and talk only. No urine yet. No oral yet.")
    assert "URINE LOOK:" not in not_yet

    jupo = lock_pleasure_face(
        "Already oral. Mouth already on.\nDeep jupo-jupo.\n\noverall_soundscape:\nWet.\n",
        situation="oral",
    )
    assert "PLEASURE FACE:" in jupo
    assert "enjoying the jupo" in jupo
    pee_oral = lock_pleasure_face(
        "Already oral. Mouth already on the tip. She drinks the yellow stream.\n",
        situation="oral",
    )
    assert "PLEASURE FACE:" not in pee_oral
    cum = lock_pleasure_face("CUMOUF. Already deep in the mouth.\n", situation="oral_creampie")
    assert "ORGASM FACE:" in cum
    assert "climax face" in cum.lower()
    assert lock_pleasure_face(cum, situation="oral_creampie") == cum


def test_pleasure_voice_and_erotic_wait_do_not_rewrite_beats(tmp_path):
    from h3_lora_studio import (
        jp_outside_quotes,
        load_story,
        lock_pleasure_voice_and_wait,
        prepare_story_clip,
        soundscape_text,
    )

    jupo = lock_pleasure_voice_and_wait(
        "Already oral. Mouth already on.\nHands NEVER on the shaft.\n\noverall_soundscape:\nWet.\n",
        situation="oral",
    )
    assert "PLEASURE VOICE:" in jupo
    assert "EROTIC WAIT:" in jupo
    assert "just to wait" in jupo.lower()
    assert "NEVER on the shaft" in jupo
    assert "SEDUCTIVE SMILE" in jupo
    assert "light French peck" in jupo
    assert "leave at once" in jupo
    assert "own breasts" in jupo
    assert "Do not start oral" in jupo
    assert "keep that mouth on the penis" in jupo
    assert "leaked female moans" in soundscape_text(jupo).lower()
    assert jp_outside_quotes(jupo) == ""
    assert lock_pleasure_voice_and_wait(jupo, situation="oral") == jupo

    ride = lock_pleasure_voice_and_wait(
        "Already in. Cowgirl. She rides.\n\noverall_soundscape:\nWet.\n",
        situation="riding",
    )
    assert "EROTIC WAIT:" in ride
    assert "Do not add, skip, or replace the written beat" in ride
    assert "do not replace a written deep kiss" in ride.lower() or "does not replace a written deep kiss" in ride

    pee = lock_pleasure_voice_and_wait(
        "Already oral. Mouth already on the tip. She drinks the yellow stream.\n\noverall_soundscape:\nHiss.\n",
        situation="oral",
    )
    assert "PLEASURE VOICE:" not in pee
    assert "EROTIC WAIT:" not in pee

    walk = lock_pleasure_voice_and_wait(
        "She walks down the street. Everyday faces. No oral.\n"
        "Hairless female pussy at the base of the shaft where a scrotum would be.\n"
        "\noverall_soundscape:\nSteps.\n",
        situation="futa_visible",
    )
    assert "EROTIC WAIT:" not in walk
    assert "PLEASURE VOICE:" not in walk

    talk = lock_pleasure_voice_and_wait(
        "They stand at the door. SPEAKS.\nNobody sucks. No oral.\n"
        "「こんにちは」\n\noverall_soundscape:\n「こんにちは」\n",
        situation="futa_visible",
    )
    assert "EROTIC WAIT:" in talk
    assert "first partner peck" in talk
    assert "light self-touch only" in talk
    assert jp_outside_quotes(talk) == ""

    clinic = load_story("clinic-75s")
    oral = prepare_story_clip(clinic, 3, last_frame="x.png", stills_dir=tmp_path)
    assert "PLEASURE VOICE:" in oral["prompt"]
    assert "EROTIC WAIT:" in oral["prompt"]
    assert "Already at the BASE" in oral["prompt"] or "already at the BASE" in oral["prompt"]
    assert "NEVER on the shaft" in oral["prompt"]
    consult = prepare_story_clip(clinic, 1, last_frame="x.png", stills_dir=tmp_path)
    assert "PLEASURE VOICE:" in consult["prompt"]
    assert "EROTIC WAIT:" in consult["prompt"]
    assert "キョウはどうしました？" in consult["prompt"]
    opening = prepare_story_clip(clinic, 0, stills_dir=tmp_path)
    assert "EROTIC WAIT:" not in opening["prompt"]
    assert "PLEASURE VOICE:" not in opening["prompt"]
    commute = load_story("commute-120s")
    hall = prepare_story_clip(commute, 0, stills_dir=tmp_path, force_t2v=True)
    assert "EROTIC WAIT:" not in hall["prompt"]
    assert "PLEASURE VOICE:" not in hall["prompt"]
    cafe0 = prepare_story_clip(load_story("cafe-100s"), 0, stills_dir=tmp_path)
    assert "EROTIC WAIT:" not in cafe0["prompt"]
    assert "Heat and relief only" in cafe0["prompt"]
    cafe1 = prepare_story_clip(
        load_story("cafe-100s"), 1, last_frame="x.png", stills_dir=tmp_path
    )
    assert "EROTIC WAIT:" in cafe1["prompt"]
    assert "いらっしゃいませ" in cafe1["prompt"]
    assert "first partner peck" in cafe1["prompt"]
    genkan = prepare_story_clip(commute, 1, stills_dir=tmp_path, force_t2v=True)
    assert "EROTIC WAIT:" in genkan["prompt"]
    assert "いってらっしゃい" in genkan["prompt"]
    meat1 = prepare_story_clip(
        load_story("meat-wall-85s"), 1, last_frame="x.png", stills_dir=tmp_path
    )
    assert "EROTIC WAIT:" in meat1["prompt"]
    assert "あ、おフロ。。。でもこれって" in meat1["prompt"]
    bath0 = prepare_story_clip(load_story("semen-bath-70s"), 0, stills_dir=tmp_path)
    assert "EROTIC WAIT:" in bath0["prompt"]
    checkup_talk = prepare_story_clip(
        load_story("checkup-100s"), 1, last_frame="x.png", stills_dir=tmp_path
    )
    assert "EROTIC WAIT:" in checkup_talk["prompt"]
    assert "No kiss yet" in checkup_talk["prompt"]
    assert "do not add a kiss" in checkup_talk["prompt"].lower()
    assert "does not kiss this clip" in consult["prompt"] or "No deep kiss this clip" in consult["prompt"]


def test_all_scenes_speech_urine_pleasure_after_prepare(tmp_path):
    from h3_lora_studio import (
        ACT_SITUATIONS,
        CHAIN_PACK_IDS,
        SEMEN_SITUATIONS,
        SEX_INSIDE_SITUATIONS,
        STORY_IDS,
        _SEX_PULL_OUT_RE,
        generate_immoral_shorts,
        jp_outside_quotes,
        load_story,
        prepare_story_clip,
        soundscape_text,
        spoken_lines,
    )

    stories = [load_story(sid) for sid in sorted(STORY_IDS | CHAIN_PACK_IDS)]
    stories.append(generate_immoral_shorts())
    cast = _write_cast_stills(tmp_path / "cast")
    heat_re = __import__("re").compile(r"あち[ぃい]+ー?|あっちー")
    urine_re = __import__("re").compile(
        r"yellow stream|yellow urine|pees a |drinks the yellow|peeing|Urine from .+ urethra",
        __import__("re").I,
    )
    seen_speech = seen_heat = seen_urine = seen_jupo = seen_cum = 0
    for story in stories:
        for i, clip in enumerate(story["clips"]):
            last = f"h3_chain_{i - 1}.png" if i and str(story.get("kind") or "") != "anthology" else None
            planned = prepare_story_clip(
                story, i, last_frame=last, stills_dir=tmp_path, cast_dir=cast
            )
            prompt = planned["prompt"]
            leftover = jp_outside_quotes(prompt)
            assert leftover == "", (story["id"], i + 1, leftover[:80])
            sit = planned["situation"]
            raw = clip["prompt"]
            lines = spoken_lines(raw)
            if lines:
                seen_speech += 1
                assert "SPEECH FACE:" in prompt, (story["id"], i + 1)
                assert "Not monotone" in prompt
                sound = soundscape_text(prompt)
                assert "lip-synced" not in sound.lower(), (story["id"], i + 1, sound)
                assert "no other speech" not in sound.lower(), (story["id"], i + 1, sound)
                assert "spoken_transcript" not in prompt
                assert "[AUDIO-LOCK]" not in prompt
                for ln in lines:
                    assert f"「{ln}」" in sound, (story["id"], i + 1, ln, sound)
                if any(heat_re.search(ln) for ln in lines):
                    seen_heat += 1
                    assert "HEAT FACE:" in prompt, (story["id"], i + 1, lines)
                else:
                    assert "HEAT FACE:" not in prompt, (story["id"], i + 1, lines)
            else:
                sound = soundscape_text(prompt)
                assert "no spoken words" not in sound.lower(), (story["id"], i + 1, sound)
                assert "no other speech" not in sound.lower(), (story["id"], i + 1, sound)
                assert "lip-synced" not in sound.lower(), (story["id"], i + 1, sound)
                assert "spoken_transcript" not in prompt
                assert "[AUDIO-LOCK]" not in prompt
            if urine_re.search(raw) and "No urine yet" not in raw and "No urine." not in raw:
                seen_urine += 1
                assert "URINE LOOK:" in prompt, (story["id"], i + 1)
                assert "urethral" in prompt.lower(), (story["id"], i + 1)
                assert "yellow" in prompt.lower(), (story["id"], i + 1)
            orig_sit = str(clip.get("situation") or "")
            if orig_sit in ACT_SITUATIONS:
                assert spoken_lines(prompt) == [], (story["id"], i + 1, spoken_lines(prompt))
                assert "ACT SILENCE:" in prompt, (story["id"], i + 1)
                assert "KEEP wet sounds loud" in prompt, (story["id"], i + 1)
                assert "LIP SYNC" not in prompt, (story["id"], i + 1)
                assert "SPEECH FACE:" not in prompt, (story["id"], i + 1)
                if not urine_re.search(raw):
                    sound = soundscape_text(prompt)
                    assert "moan" in sound.lower(), (story["id"], i + 1, sound)
                    if orig_sit in {"oral", "futa_blowjob"}:
                        assert "jupo" in sound.lower(), (story["id"], i + 1, sound)
                        assert "saliva" in sound.lower(), (story["id"], i + 1, sound)
                    elif orig_sit == "oral_creampie":
                        assert "saliva" in sound.lower() or "in-mouth" in sound.lower(), (
                            story["id"],
                            i + 1,
                            sound,
                        )
                    elif orig_sit == "cunnilingus_futa":
                        assert "lick" in sound.lower() or "saliva" in sound.lower(), (
                            story["id"],
                            i + 1,
                            sound,
                        )
                    elif orig_sit in SEX_INSIDE_SITUATIONS:
                        assert "thrust" in sound.lower() or "wet" in sound.lower(), (
                            story["id"],
                            i + 1,
                            sound,
                        )
            if "Clear futanari" in prompt or "futanari: erect" in prompt.lower():
                assert "SHAFT LOOK:" in prompt, (story["id"], i + 1)
                assert "When erect: 20cm" in prompt, (story["id"], i + 1)
                assert "thick human girth" in prompt, (story["id"], i + 1)
            elif "NEVER futanari" in prompt and "Clear futanari" not in raw:
                assert "SHAFT LOOK:" not in prompt, (story["id"], i + 1)
            if orig_sit in {"oral", "futa_blowjob"} and urine_re.search(raw):
                assert "PLEASURE FACE:" not in prompt, (story["id"], i + 1)
            elif orig_sit in {"oral", "futa_blowjob"}:
                seen_jupo += 1
                assert "PLEASURE FACE:" in prompt, (story["id"], i + 1)
                if "ORAL LOCK:" in prompt:
                    assert "to the BASE" in prompt or "Start deep at the BASE" in prompt, (story["id"], i + 1)
                    assert "not a tip suck" in prompt.lower(), (story["id"], i + 1)
            if orig_sit == "oral_creampie":
                seen_cum += 1
                assert "ORGASM FACE:" in prompt, (story["id"], i + 1)
                assert "clingy" in prompt.lower(), (story["id"], i + 1)
                assert "clings" in prompt.lower(), (story["id"], i + 1)
                assert "heavy-oil" in prompt.lower(), (story["id"], i + 1)
                assert "ORAL LOCK:" in prompt, (story["id"], i + 1)
                assert "to the BASE" in prompt, (story["id"], i + 1)
            if orig_sit in SEMEN_SITUATIONS:
                assert "SEMEN LOOK:" in prompt, (story["id"], i + 1)
                assert "heavy-oil" in prompt.lower(), (story["id"], i + 1)
                assert "never brown" in prompt.lower(), (story["id"], i + 1)
                assert "too much" in prompt.lower(), (story["id"], i + 1)
                assert "overflow" in prompt.lower(), (story["id"], i + 1)
            if orig_sit in SEX_INSIDE_SITUATIONS and not _SEX_PULL_OUT_RE.search(raw):
                assert "INSIDE LOCK:" in prompt, (story["id"], i + 1)
            elif orig_sit in {"oral", "oral_creampie", "cunnilingus_futa", "after_ejaculation", "futa_visible"}:
                assert "INSIDE LOCK:" not in prompt, (story["id"], i + 1)
    assert seen_speech >= 70
    assert seen_heat == 1
    assert seen_urine >= 1
    assert seen_jupo >= 10
    assert seen_cum >= 8


def test_lock_oral_in_mouth_blocks_shaft_lick():
    from h3_lora_studio import lock_oral_in_mouth

    suck = lock_oral_in_mouth(
        "Already oral. Mouth already on.\nDeep jupo-jupo.\n\noverall_soundscape:\nWet. No spoken words.\n",
        situation="oral",
    )
    assert "ORAL LOCK:" in suck
    assert "not licking" in suck.lower()
    assert "glans is already fully inside" in suck.lower()
    assert "to the BASE" in suck
    assert "not a tip suck" in suck.lower()
    assert "not around the glans" in suck.lower()
    assert suck.index("ORAL LOCK:") < suck.index("overall_soundscape:")
    assert lock_oral_in_mouth(suck, situation="oral") == suck
    pee = lock_oral_in_mouth(
        "Already oral. Mouth already on the tip. She drinks the yellow stream.\n",
        situation="oral",
    )
    assert "ORAL LOCK:" not in pee
    pull = lock_oral_in_mouth(
        "Already oral. Mouth already on. She pulls her mouth off the 20cm.\n",
        situation="oral",
    )
    # 抜く本も frame 1 は根元。そこから一気に抜く。先端だけ咥えるに逃げない。
    assert "ORAL LOCK:" in pull
    assert "Start deep at the BASE" in pull
    assert "slides all the way OFF" in pull
    assert "Do not stop at the glans" in pull
    assert "already swallowed. The glans is already fully inside" not in pull
    walk = lock_oral_in_mouth("Nobody sucks. They walk the platform.", situation="futa_visible")
    assert "ORAL LOCK:" not in walk
    creampie = lock_oral_in_mouth("CUMOUF. Already deep in the mouth.", situation="oral_creampie")
    assert "ORAL LOCK:" in creampie
    assert "to the BASE" in creampie
    assert "not a tip suck" in creampie.lower()
    stay = lock_oral_in_mouth(
        "CUMOUF. Mouth stays on. Nobody pulls off. She climaxes IN the mouth.\n",
        situation="oral_creampie",
    )
    assert "ORAL LOCK:" in stay
    assert "to the BASE" in stay
    pull_show = lock_oral_in_mouth(
        "CUMOUF. Climaxes IN the mouth, then PULLS OFF and shows the semen.\n",
        situation="oral_creampie",
    )
    assert "ORAL LOCK:" in pull_show
    assert "to the BASE" in pull_show
    assert "While it pulses" in pull_show
    share = lock_oral_in_mouth(
        "CUMOUF. Already deep in the mouth. After the last pulse she pulls her mouth off.\n",
        situation="oral_creampie",
        ending="share",
    )
    assert "ORAL LOCK:" in share
    assert "KEEP the lips at the BASE" in share
    assert "Do not pull back to the glans" in share
    assert "mouth-to-mouth" in share.lower()
    assert "STANDS UP" in share
    assert "EYE LEVEL" in share


def test_lock_penis_inside_pussy_anus_entry_and_skips(tmp_path):
    from h3_lora_studio import (
        INSIDE_ANAL_LINE,
        INSIDE_ENTRY_LINE,
        INSIDE_PUSSY_LINE,
        lock_penis_inside,
        lock_oral_in_mouth,
        load_story,
        prepare_story_clip,
        sex_inside_hole,
    )

    already = (
        "Already in. Joining point visible. Vaginal only. No anal.\n"
        "\noverall_soundscape:\nWet. No spoken words.\n"
    )
    pussy = lock_penis_inside(already, situation="futa_sex")
    assert "INSIDE LOCK:" in pussy
    assert "already inside the pussy" in pussy.lower()
    assert pussy.index("INSIDE LOCK:") < pussy.index("overall_soundscape:")
    assert lock_penis_inside(pussy, situation="futa_sex") == pussy
    assert sex_inside_hole(already, situation="futa_sex") == "pussy"
    anal_raw = (
        "Already in. The shaft is buried in the anal canal. Joining point visible.\n"
        "\noverall_soundscape:\nWet.\n"
    )
    assert sex_inside_hole(anal_raw, situation="futa_anal") == "anus"
    anal = lock_penis_inside(anal_raw, situation="futa_anal")
    assert INSIDE_ANAL_LINE in anal
    assert "not in the pussy this clip" in anal
    entry_raw = (
        "INSERTION ON CAMERA. Show the entry. Then ride.\n"
        "\noverall_soundscape:\nWet insertion.\n"
    )
    entry = lock_penis_inside(entry_raw, situation="riding")
    assert INSIDE_ENTRY_LINE in entry
    oral = lock_penis_inside(
        "Already oral. Mouth already on.\nDeep jupo-jupo.\n",
        situation="oral",
    )
    assert "INSIDE LOCK:" not in oral
    walk = lock_penis_inside("Nobody is inside yet. Tip a hand's width, NOT in.", situation="futa_visible")
    assert "INSIDE LOCK:" not in walk
    pull = lock_penis_inside(
        "Starts inside, then pulls OUT. Sex ends. Joining point as it comes apart.\n",
        situation="futa_sex",
    )
    assert "INSIDE LOCK:" not in pull
    gush = lock_penis_inside("Already after ejaculation. Pull-out gush.", situation="after_ejaculation")
    assert "INSIDE LOCK:" not in gush
    negative_anal = lock_penis_inside(
        "Already in. Vaginal only. Not anal. Joining point visible.\n",
        situation="futa_sex",
    )
    assert INSIDE_PUSSY_LINE in negative_anal
    roof = load_story("roof-ac-30s")
    sex = lock_penis_inside(roof["clips"][1]["prompt"], situation="futa_sex")
    assert "INSIDE LOCK:" in sex
    oral_lock = lock_oral_in_mouth(roof["clips"][0]["prompt"], situation="futa_visible")
    assert "ORAL LOCK:" not in oral_lock
    assert "INSIDE LOCK:" not in lock_penis_inside(roof["clips"][0]["prompt"], situation="futa_visible")
    planned = prepare_story_clip(
        roof, 1, last_frame="h3_chain_0.png", stills_dir=tmp_path
    )
    assert "INSIDE LOCK:" in planned["prompt"]


def test_semen_share_plan_hold_then_kiss(tmp_path):
    from h3_lora_studio import (
        SEMEN_SHARE_SKIP,
        inject_semen_share_into_prompt,
        load_story,
        lock_semen_share_kiss,
        prepare_story_clip,
        semen_share_plan,
    )

    assert semen_share_plan({"id": "yoga-50s", "clips": []}) == []
    assert "lecture-desk-50s" in SEMEN_SHARE_SKIP
    assert semen_share_plan(load_story("lecture-desk-50s")) == []
    assert semen_share_plan(load_story("commute-120s")) == []
    assert semen_share_plan(load_story("bath-120s")) == [(10, "silent_next")]
    assert semen_share_plan(load_story("last-stop-40s")) == [(2, "on_cumouf")]
    assert semen_share_plan(load_story("last-train-120s")) == [(3, "on_cumouf"), (9, "silent_next")]
    assert semen_share_plan(load_story("semen-bath-70s")) == []
    assert "semen-bath-70s" in SEMEN_SHARE_SKIP
    assert semen_share_plan(load_story("meat-wall-85s")) == [(6, "after_speech")]
    assert "meat-wall-85s" not in SEMEN_SHARE_SKIP
    assert semen_share_plan(load_story("meat-wall-cesspit-70s")) == [(6, "after_speech")]
    assert "meat-wall-cesspit-70s" not in SEMEN_SHARE_SKIP
    assert semen_share_plan(load_story("red-light-50s")) == [(3, "on_cumouf")]
    assert semen_share_plan(load_story("manhole-30s")) == [(1, "on_cumouf")]
    assert semen_share_plan(load_story("roof-ac-30s")) == []
    assert semen_share_plan(load_story("lookout-30s")) == []
    assert semen_share_plan(load_story("engawa-120s")) == [(10, "on_cumouf")]
    assert semen_share_plan(load_story("cafe-100s")) == [(9, "after_speech")]
    assert semen_share_plan(load_story("clinic-75s")) == [(8, "on_back")]
    shorts = load_story("shorts-immoral")
    assert semen_share_plan(shorts) == [(1, "on_cumouf"), (6, "on_cumouf")]
    for i, mode in semen_share_plan(shorts):
        assert shorts["clips"][i]["situation"] == "oral_creampie"
        assert "HOLD STILL" in shorts["clips"][i]["prompt"]
        assert "mouth-to-mouth" in shorts["clips"][i]["prompt"].lower() or "SEMEN_SHARE_KISS" in shorts["clips"][i]["prompt"] or "tongues wrap" in shorts["clips"][i]["prompt"].lower()
        assert "Full bodies from head to feet" not in shorts["clips"][i]["prompt"]

    locked = lock_semen_share_kiss("CUMOUF.\n\noverall_soundscape:\nWet.\n")
    assert "SEMEN SHARE:" in locked
    assert "HOLD STILL" in locked
    assert "mouth-to-mouth" in locked.lower()
    assert "wet kiss" in locked.lower() or "tongue" in locked.lower()
    assert "STANDS UP" in locked
    assert "SAME EYE LEVEL" in locked
    assert "deep wet kiss" in locked.lower() or "filthy" in locked.lower()
    assert "tongues wrap" in locked.lower()
    assert "STAYS on both faces" in locked
    assert "they lean in" not in locked.lower()
    assert locked.index("SEMEN SHARE:") < locked.index("overall_soundscape:")
    assert lock_semen_share_kiss(locked) == locked

    supine = lock_semen_share_kiss("CUMOUF.\n\noverall_soundscape:\nWet.\n", supine=True)
    assert "SEMEN SHARE:" in supine
    assert "STAYS LYING" in supine
    assert "leans DOWN" in supine
    assert "SAME EYE LEVEL" not in supine
    assert "STANDS UP" not in supine
    assert lock_semen_share_kiss(supine, supine=True) == supine
    on_back = inject_semen_share_into_prompt(
        "Remaining seconds, silence: she leans down. Do not freeze.\n\noverall_soundscape:\nWet.\n",
        where="on_back",
    )
    assert "STAYS LYING" in on_back
    assert "leans DOWN" in on_back
    assert "sits up" not in on_back.lower()
    assert "STANDS UP" not in on_back

    after = inject_semen_share_into_prompt(
        "She speaks: 「モンダイありますね」. Remaining seconds, silence: she stays squatting. Do not freeze.",
        where="after_speech",
    )
    assert "mouth-to-mouth" in after.lower() or "SEMEN SHARE" in after or "HOLD STILL" in after
    assert "HOLD STILL" in after
    assert "モンダイありますね" in after

    bath = load_story("bath-120s")
    assert bath["duration_s"] == 120
    share_clip = prepare_story_clip(bath, 10, last_frame="x.png", stills_dir=tmp_path)
    assert share_clip["situation"] == "futa_visible"
    assert share_clip["duration_s"] == 10
    assert "mouth-to-mouth" in share_clip["prompt"].lower()
    assert "HOLD STILL" in share_clip["prompt"]
    assert "SEMEN SHARE:" in share_clip["prompt"]
    assert "STANDS UP" in share_clip["prompt"]
    assert "SAME EYE LEVEL" in share_clip["prompt"]
    assert "tongues wrap" in share_clip["prompt"].lower()
    assert "clingy" in share_clip["prompt"].lower()
    assert "they lean in" not in share_clip["prompt"].lower()
    assert "blowjob-h3" not in [row["id"] for row in share_clip["stack"]]
    assert "cumouf-h3" not in [row["id"] for row in share_clip["stack"]]
    cumouf = prepare_story_clip(bath, 9, last_frame="x.png", stills_dir=tmp_path)
    assert cumouf["situation"] == "oral_creampie"
    assert "SEMEN SHARE:" not in cumouf["prompt"]

    stop = load_story("last-stop-40s")
    assert sum(float(c["duration_s"]) for c in stop["clips"]) == 40
    cum_share = prepare_story_clip(stop, 2, last_frame="x.png", stills_dir=tmp_path)
    assert cum_share["situation"] == "oral_creampie"
    assert "ORAL LOCK:" in cum_share["prompt"]
    assert "not licking" in cum_share["prompt"].lower()
    assert "mouth-to-mouth" in cum_share["prompt"].lower()
    assert "SEMEN SHARE:" in cum_share["prompt"]
    assert "STANDS UP" in cum_share["prompt"]
    assert "SAME EYE LEVEL" in cum_share["prompt"]
    assert "tongues wrap" in cum_share["prompt"].lower()
    assert "clingy" in cum_share["prompt"].lower()
    assert "slick" in cum_share["prompt"].lower()
    speech = prepare_story_clip(stop, 3, last_frame="x.png", stills_dir=tmp_path)
    assert "おきましたか？おきゃくさん、しゅうてんだからおりてください" in speech["prompt"]
    assert "SEMEN SHARE:" not in speech["prompt"]

    desk = load_story("lecture-desk-50s")
    under = prepare_story_clip(desk, 3, last_frame="x.png", stills_dir=tmp_path)
    assert under["situation"] == "oral_creampie"
    assert "SEMEN SHARE:" not in under["prompt"]
    assert "口移し" not in under["prompt"]

    sex = load_story("yoga-50s")
    last = prepare_story_clip(sex, 4, last_frame="x.png", stills_dir=tmp_path)
    assert "SEMEN SHARE:" not in last["prompt"]
    assert "口移し" not in last["prompt"]


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


def test_dedicated_talk_clips_fill_the_take():
    """Dedicated talk clips occupy the mouth with one long kana line, not a short line then silence."""
    from h3_lora_studio import (
        ACT_SITUATIONS,
        STORY_ORDER,
        load_story,
        spoken_lines,
        validate_story_follow,
    )

    punct = re.compile(r"[。、…・！？?\s]")
    seen = 0
    for sid in STORY_ORDER:
        story = load_story(sid)
        assert validate_story_follow(story) == [], sid
        for i, clip in enumerate(story["clips"]):
            if clip["situation"] in ACT_SITUATIONS:
                continue
            uniq = list(dict.fromkeys(spoken_lines(clip["prompt"])))
            if not uniq:
                continue
            seen += 1
            kana = sum(len(punct.sub("", s)) for s in uniq)
            assert len(uniq) == 1, (sid, i + 1, uniq)
            assert kana >= 40, (sid, i + 1, kana, uniq)
            prompt = clip["prompt"]
            assert "One short conversational Japanese line" not in prompt
            assert "Then the mouth closes" not in prompt
            assert "Remaining seconds, silence" not in prompt
            assert "keep matching the quotes" in prompt
    assert seen == 24


def test_all_act_clips_stay_silent():
    """Every story/pack/short act clip stays mute. lock_act_silent strips leaked 「」."""
    from h3_lora_studio import (
        ACT_SITUATIONS,
        CHAIN_PACK_IDS,
        STORY_IDS,
        generate_immoral_shorts,
        jp_outside_quotes,
        load_story,
        lock_act_sfx,
        lock_act_silent,
        soundscape_text,
        spoken_lines,
        validate_story_follow,
    )

    seen = 0
    stories = [load_story(sid) for sid in sorted(STORY_IDS | CHAIN_PACK_IDS)]
    stories.append(generate_immoral_shorts())
    for story in stories:
        assert validate_story_follow(story) == [], story.get("id")
        for i, clip in enumerate(story["clips"]):
            sit = str(clip.get("situation") or "")
            if sit not in ACT_SITUATIONS:
                continue
            seen += 1
            raw = clip["prompt"]
            assert spoken_lines(raw) == [], (story["id"], i + 1)
            assert "LIP SYNC" not in raw, (story["id"], i + 1)
            assert "lip-synced" not in raw.lower(), (story["id"], i + 1)
            locked = lock_act_silent(raw, situation=sit)
            assert spoken_lines(locked) == [], (story["id"], i + 1)
            assert "ACT SILENCE:" in locked, (story["id"], i + 1)
            assert "KEEP wet sounds loud" in locked, (story["id"], i + 1)
            assert lock_act_silent(locked, situation=sit) == locked
            wet = lock_act_sfx(locked, situation=sit)
            assert spoken_lines(wet) == [], (story["id"], i + 1)
            assert "jupo-jupo" in wet.lower() or "moan" in soundscape_text(wet).lower(), (
                story["id"],
                i + 1,
            )
            assert lock_act_sfx(wet, situation=sit) == wet
    assert seen >= 80

    leaked = (
        "medium-close on the mouth. Already oral.\n"
        "「こんにちは」\n"
        "overall_soundscape:\nWet jupo.\n"
    )
    silent = lock_act_silent(leaked, situation="oral")
    assert spoken_lines(silent) == []
    assert "こんにちは" not in silent
    assert "ACT SILENCE:" in silent
    assert "No spoken Japanese" in silent
    assert "KEEP wet sounds loud" in silent
    assert jp_outside_quotes(silent) == ""
    wet = lock_act_sfx(silent, situation="oral")
    assert "jupo-jupo" in soundscape_text(wet).lower()
    assert "saliva" in soundscape_text(wet).lower()
    assert "moan" in soundscape_text(wet).lower()
    kiss = lock_act_sfx(
        "Silent deep filthy wet kiss.\nmouth-to-mouth.\n\noverall_soundscape:\nNight.\n",
        situation="futa_visible",
    )
    assert spoken_lines(kiss) == []
    assert "ACT SFX:" in kiss
    assert "chu" in soundscape_text(kiss).lower()
    assert "saliva" in soundscape_text(kiss).lower()
    assert jp_outside_quotes(kiss) == ""
    talk = "LIP SYNC: face large.\n「こんにちは」\noverall_soundscape:\n「こんにちは」\n"
    assert lock_act_silent(talk, situation="futa_visible") == talk
    assert lock_act_sfx(talk, situation="futa_visible") == talk


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
    for pack in ("訪問販売", "定期検診", "ケンシン", "終点", "終電", "ザーメン風呂", "ニクカベ", "ニクカベ肥溜め", "カフェ", "車内販売", "赤信号", "ヨガ", "背中流し", "カラオケ", "ランドリー", "講義机", "キャンプ", "花火", "ハイスイコウ", "屋上クーラー", "ハマのテトラ", "廃校ロッカー", "ドウロのど真ん中", "ガケの展望台", "コウジョウあと", "ガソリンスタンド跡", "トンネル非常電話", "川原のゴミ"):
        for suffix in ("（専用）", "（つなぐ）", "（つなぐ修）", "（参照つなぐ）", "（参照つなぐ修）"):
            assert f'"{pack}{suffix}"' in cell3, pack + suffix
    # legacy long pack labels are aliases only, not dropdown rows
    assert '"訪問販売60秒（つなぐ）"' not in cell3 and '"終点40秒（つなぐ）"' not in cell3
    # order: 55 story rows, then 24 packs × 5, then 短編集, then the act scenes
    assert cell3.index('"縁側（参照つなぐ修）"') < cell3.index('"訪問販売（専用）"') < cell3.index('"ケンシン（専用）"') < cell3.index('"終点（専用）"') < cell3.index('"終電（専用）"') < cell3.index('"ザーメン風呂（専用）"') < cell3.index('"ニクカベ（専用）"') < cell3.index('"ニクカベ肥溜め（専用）"') < cell3.index('"カフェ（専用）"') < cell3.index('"花火（参照つなぐ修）"') < cell3.index('"ハイスイコウ（専用）"') < cell3.index('"川原のゴミ（参照つなぐ修）"') < cell3.index('"短編集（参照）"') < cell3.index('"アナル挿入（画質）"')
    assert cell3.index('"普通（エロなし）"') < cell3.index('"生成し直し"') < cell3.index('"帰宅（専用）"')
    assert cell3.index('"普通（エロなし）"') < cell3.index('"帰宅（専用）"')
    assert "作り直しの物語" in cell3 and "作り直し開始の本" in cell3
    assert "is_redo" in src and "apply_redo_play" in src and "stock_completed_clips" in src
    from h3_lora_studio import CHAIN_PACK_ORDER, STORY_ORDER  # noqa: E402

    m = re.search(r'やりたいシーン = "[^"]+"  #@param (\[.*?\])\n', cell3)
    opts = json.loads(m.group(1))
    assert len(opts) == 4 + 1 + 5 * len(STORY_ORDER) + 5 * len(CHAIN_PACK_ORDER) + 1 + 23
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
    assert "FIT_CLIP0 = bool(最終シーン合わせ and not STORY_SEAMLESS and not STORY.get(\"use_cast_ref\") and REDO_PLAN_IDX == 0)" in src
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
    assert '"last-train-120s" not in getattr(_h3_studio, "CHAIN_PACK_IDS", set())' in src
    assert '"semen-bath-70s" not in getattr(_h3_studio, "CHAIN_PACK_IDS", set())' in src
    assert '"meat-wall-85s" not in getattr(_h3_studio, "CHAIN_PACK_IDS", set())' in src
    assert '"meat-wall-cesspit-70s" not in getattr(_h3_studio, "CHAIN_PACK_IDS", set())' in src
    assert '"clinic-75s" not in getattr(_h3_studio, "CHAIN_PACK_IDS", set())' in src
    assert '"fireworks-50s" not in getattr(_h3_studio, "CHAIN_PACK_IDS", set())' in src
    assert '"manhole-30s" not in getattr(_h3_studio, "ADDON_PACK_IDS", set())' in src
    assert '"riverbank-30s" not in getattr(_h3_studio, "ADDON_PACK_IDS", set())' in src
    assert 'getattr(_h3_studio, "sanitize_story_soundscape", None)' in src
    assert '"clingy" not in getattr(_h3_studio, "SEMEN_LOOK_LINE", "")' in src
    assert '"heavy-oil" not in getattr(_h3_studio, "SEMEN_LOOK_LINE", "")' in src
    assert '"TOO MUCH" not in getattr(_h3_studio, "SEMEN_LOOK_LINE", "")' in src
    assert '"SHAFT LOOK:" not in getattr(_h3_studio, "SHAFT_LOOK_LINE", "")' in src
    assert '"tongues wrap" not in getattr(_h3_studio, "SEMEN_SHARE_LINE", "")' in src
    assert 'getattr(_h3_studio, "addon_pose_prep_errors", None)' in src
    assert 'getattr(_h3_studio, "lock_penis_inside", None)' in src
    assert '"to the BASE" not in getattr(_h3_studio, "ORAL_IN_MOUTH_LINE", "")' in src
    assert '"INSIDE LOCK:" not in getattr(_h3_studio, "INSIDE_PUSSY_LINE", "")' in src
    assert 'getattr(_h3_studio, "fetch_github_tree", None)' in src
    assert 'getattr(_h3_studio, "ensure_select_loras_on_path", None)' in src
    assert 'getattr(_h3_studio, "has_fl2va_weight", None)' in src
    assert 'getattr(_h3_studio, "is_ref2v_weight", None)' in src
    for pid in CHAIN_PACK_ORDER:
        assert f"h3-lora-studio/stories/{pid}.json" in src, pid
        assert f'"{pid}"' in cell2, pid
    assert CHAIN_PACK_ORDER[:4] == ("sales-visit-60s", "checkup-100s", "clinic-75s", "last-stop-40s")
    assert CHAIN_PACK_ORDER[4:7] == ("last-train-120s", "semen-bath-70s", "meat-wall-85s")
    assert CHAIN_PACK_ORDER[7] == "meat-wall-cesspit-70s"
    assert src.find("stories/sales-visit-60s.json") < src.find("stories/checkup-100s.json") < src.find("stories/clinic-75s.json") < src.find("stories/last-stop-40s.json") < src.find("stories/last-train-120s.json") < src.find("stories/semen-bath-70s.json") < src.find("stories/meat-wall-85s.json") < src.find("stories/meat-wall-cesspit-70s.json")
    assert '"カフェ（専用）"' in cell2 and '"ケンシン（専用）"' in cell2 and '"終電（専用）"' in cell2 and '"ザーメン風呂（専用）"' in cell2 and '"ニクカベ（専用）"' in cell2 and '"ニクカベ肥溜め（専用）"' in cell2 and '"花火（専用）"' in cell2 and '"ハイスイコウ（専用）"' in cell2 and '"川原のゴミ（専用）"' in cell2
    assert "専用（専用）" in md0 and "専用（つなぐ）" in md0 and "専用（つなぐ修）" in md0
    assert "名前付きパック（専用 / つなぐ / つなぐ修 / 参照つなぐ / 参照つなぐ修）" in md0
    assert "旧名「訪問販売60秒（つなぐ）」" in md0
    assert "登校（専用）" in md0
    assert "竿＋マンコ、金玉なし" in md0
    assert "「」の中は話し言葉" in md0
    assert "漢字のまま" not in md0
    assert "h3-20260909-semen-volume-1" in cell2
    assert "h3-20260907-r2v-node-1" not in cell2
    assert "h3-20260907-pussy-1" not in cell2
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
    assert "ensure_r2v_in_object_info" in src
    assert "ensure_comfy_r2v_node" in src
    assert "参照ノード: あり" in cell2
    assert "参照（R2V）ノードがありません。②をもう一度実行してください。" not in cell3
    assert "raise SystemExit(R2V_NODE_MISSING)" in cell3
    assert "ensure_r2v_in_object_info" in cell3
    assert "lock_oral_in_mouth" in src
    assert '"to the BASE" not in getattr(_h3_studio, "ORAL_IN_MOUTH_LINE", "")' in src
    assert "lock_penis_inside" in src
    assert "lock_semen_share_kiss" in src
    assert "who_hidden_at_start" in src
    assert "lock_start_cast" in src
    assert "lock_spoken_emotion" in src
    assert "lock_urine_look" in src
    assert "lock_pleasure_face" in src
    assert "lock_pleasure_voice_and_wait" in src
    assert "lock_act_silent" in src
    assert "lock_act_sfx" in src
    helper_src = Path(__file__).resolve().parent.joinpath("h3_lora_studio.py").read_text(encoding="utf-8")
    assert "def lock_pleasure_voice_and_wait" in helper_src
    assert "def lock_act_silent" in helper_src
    assert "def lock_act_sfx" in helper_src
    assert "短い参照動画の部品" in helper_src
    assert "def lock_futa_shaft" in helper_src
    assert "def lock_penis_inside" in helper_src
    assert "Deep jupo to the BASE" in helper_src
    assert "INSIDE LOCK:" in helper_src
    assert "SHAFT LOOK:" in helper_src
    assert "MiniMaxH3ReferenceToVideo" in helper_src
    assert '"MiniMaxH3ReferenceToVideo"' in helper_src or "R2V_NODE" in helper_src
    assert '("colab/h3_r2v_core.py", Path("/content/h3_r2v_core.py"))' in cell2
    assert '("h3-lora-studio/scripts/select_loras.py", Path("/content/select_loras.py"))' in cell2
    assert cell2.find('"colab/h3_r2v_core.py"') < cell2.find(
        "from h3_lora_studio import fetch_github_tree"
    )
    assert "except ImportError:" in helper_src
    assert "r2v_finalize_prompt = None" in helper_src
    assert "tongues wrap" in helper_src
    assert 'Then mouth-to-mouth semen share, a filthy deep wet kiss. tongues wrap' in helper_src


def test_studio_imports_when_r2v_core_is_missing(tmp_path, monkeypatch):
    """Colab ② writes h3_lora_studio.py first. Import must not require h3_r2v_core yet."""
    import builtins
    import importlib.util

    dest = tmp_path / "h3_lora_studio.py"
    dest.write_text(
        Path(__file__).resolve().parent.joinpath("h3_lora_studio.py").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    real_import = builtins.__import__

    def blocked(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "h3_r2v_core" or name.startswith("h3_r2v_core."):
            raise ImportError("No module named 'h3_r2v_core'")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", blocked)
    spec = importlib.util.spec_from_file_location("h3_lora_studio_colab2_bootstrap", dest)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    try:
        assert mod.r2v_finalize_prompt is None
        assert callable(mod.fetch_github_tree)
        assert callable(mod.studio_colab_dest)
    finally:
        sys.modules.pop(spec.name, None)


def test_lock_r2v_cast_prompt_loads_finalize_after_bootstrap():
    import h3_lora_studio as studio

    saved = studio.r2v_finalize_prompt
    studio.r2v_finalize_prompt = None
    try:
        out = studio.lock_r2v_cast_prompt("A woman walks.", [Path("aya-bust.jpg")], duration_s=10.0)
    finally:
        studio.r2v_finalize_prompt = saved
    assert "ROLE LOCK" in out or "Identity for character 1" in out
    assert "aya-bust.jpg" in out
    assert "Invent cinematic motion" in out


def test_cell3_freshness_gate_passes_on_current_helper():
    """③'s one-liner is case-sensitive. 'Tongues wrap' made every run look stale."""
    import h3_lora_studio as _h3_studio

    scripts = Path(__file__).resolve().parents[1] / "h3-lora-studio" / "scripts"
    if str(scripts) not in sys.path:
        sys.path.insert(0, str(scripts))
    import select_loras as _select_loras

    writer = Path(__file__).resolve().parent.joinpath("_write_lora_studio_nb.py").read_text(encoding="utf-8")
    start = writer.find('if not getattr(_select_loras, "MAX_HELPERS"')
    end = writer.find(':\n    raise SystemExit("部品の読み込みが古いです', start)
    assert start != -1 and end != -1
    stale = eval(writer[start + 3 : end], {"_select_loras": _select_loras, "_h3_studio": _h3_studio})
    assert stale is False
    assert "tongues wrap" in _h3_studio.SEMEN_SHARE_LINE
    assert "Tongues wrap" not in _h3_studio.SEMEN_SHARE_LINE


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
    assert "synth-pussy-h3" in [row["id"] for row in p0["stack"]]
    assert all(row.get("arch") != "fl2va" for row in p0["stack"])
    p1 = prepare_story_clip(story, 1, last_frame="h3_chain_0.png", stills_dir=tmp_path, cast_dir=cast)
    assert p1["first_kind"] == "last_frame"
    assert p1["mode"] == "i2v"
    assert "penis-lora-h3" in [row["id"] for row in p1["stack"]]
    raw = apply_story_play(load_story("commute-120s"), "chain")
    c0 = prepare_story_clip(raw, 0, stills_dir=tmp_path, force_t2v=True)
    assert c0["first_kind"] == "t2v"


def test_visit_opening_starts_solo_then_resident_enters(tmp_path):
    from h3_lora_studio import (
        apply_story_play,
        clip_cast_people,
        load_story,
        lock_start_cast,
        prepare_story_clip,
        who_hidden_at_start,
    )

    sales = load_story("sales-visit-60s")
    checkup = load_story("checkup-100s")
    clinic = load_story("clinic-75s")
    cafe = load_story("cafe-100s")
    s1 = sales["clips"][0]
    k1 = checkup["clips"][0]
    n1 = clinic["clips"][0]
    assert who_hidden_at_start(s1["prompt"]) == {"aya"}
    assert who_hidden_at_start(k1["prompt"]) == {"rei"}
    assert who_hidden_at_start(n1["prompt"]) == {"aya"}
    assert clip_cast_people(s1) == []
    assert clip_cast_people(k1) == []
    assert clip_cast_people(n1) == []
    assert "aya" in clip_cast_people(sales["clips"][1])
    assert "rei" in clip_cast_people(checkup["clips"][1])
    assert "aya" in clip_cast_people(clinic["clips"][1])
    for raw in (s1["prompt"], k1["prompt"]):
        assert "LEFT" in raw
        assert "ENTERS FROM THE RIGHT" in raw
        assert "Door on the right" in raw or "door on the right" in raw
    assert who_hidden_at_start(cafe["clips"][0]["prompt"]) == {"clerk"}
    assert clip_cast_people(cafe["clips"][0]) == ["aya"]
    locked = lock_start_cast(s1["prompt"])
    assert "START CAST:" in locked
    assert lock_start_cast(locked) == locked
    assert "START CAST:" not in lock_start_cast(cafe["clips"][0]["prompt"])

    cast = _write_cast_stills(tmp_path / "cast")
    sales_ref = apply_story_play(sales, "ref_chain")
    p0 = prepare_story_clip(sales_ref, 0, stills_dir=tmp_path, cast_dir=cast)
    assert p0["mode"] == "t2v"
    assert p0["first_kind"] == "t2v"
    assert not p0["still_paths"]
    assert "START CAST:" in p0["prompt"]
    assert "HIDDEN at the start" in p0["prompt"]
    p1 = prepare_story_clip(sales_ref, 1, last_frame="h3_chain_0.png", stills_dir=tmp_path, cast_dir=cast)
    assert p1["mode"] == "i2v" and p1["first_kind"] == "last_frame"
    check_ref = apply_story_play(checkup, "ref_chain")
    k0 = prepare_story_clip(check_ref, 0, stills_dir=tmp_path, cast_dir=cast)
    assert k0["mode"] == "t2v"
    clinic_ref = apply_story_play(clinic, "ref_chain")
    n0 = prepare_story_clip(clinic_ref, 0, stills_dir=tmp_path, cast_dir=cast)
    assert n0["mode"] == "t2v"
    assert "START CAST:" in n0["prompt"]
    commute = apply_story_play(load_story("commute-120s"), "ref_chain")
    c0 = prepare_story_clip(commute, 0, stills_dir=tmp_path, cast_dir=cast, force_t2v=True)
    assert c0["mode"] == "r2v" and c0["first_kind"] == "cast"


def test_validate_story_follow_full_body_ok_on_sex_not_oral():
    from h3_lora_studio import validate_story_follow

    oral = {
        "clip_s": 10,
        "clips": [{
            "duration_s": 10,
            "situation": "oral",
            "prompt": "medium-close two-shot. Full bodies from head to feet.",
        }],
    }
    assert any("full-body" in e for e in validate_story_follow(oral))
    sex = {
        "clip_s": 10,
        "clips": [{
            "duration_s": 10,
            "situation": "futa_sex",
            "prompt": "hmmotion, PENISLORA\nAlready in. joining point. Full bodies from head to feet.",
        }],
    }
    assert validate_story_follow(sex) == []


def test_anthology_shorts_immoral(tmp_path):
    from h3_lora_studio import (
        SHORTS_RECEIVER,
        SHORTS_SHAFT,
        is_anthology,
        is_story,
        load_story,
        prepare_story_clip,
        situation_ids,
        story_canvas_wh,
        validate_story_follow,
    )

    assert is_anthology("短編集（参照）")
    assert not is_story("短編集（参照）")
    assert "aftermidnight-ref2va" in situation_ids("shorts-immoral")
    assert "blowjob-h3" in situation_ids("shorts-immoral")
    assert "minimax-h3-turbo-ref2v-4step" in situation_ids("shorts-immoral")
    assert "synth-pussy-h3" in situation_ids("shorts-immoral")
    assert "penis-lora-h3" not in situation_ids("shorts-immoral")
    assert "larry-v4" not in situation_ids("shorts-immoral")
    assert "futa-h3-v51" not in situation_ids("shorts-immoral")
    story = load_story("shorts-immoral")
    assert story["kind"] == "anthology"
    assert story["clip_s"] == 10
    assert len(story["clips"]) == 12
    assert story["duration_s"] == 120
    assert validate_story_follow(story) == []
    want = [
        "oral",
        "oral_creampie",
        "oral",
        "cunnilingus_futa",
        "futa_sex",
        "oral",
        "oral_creampie",
        "futa_sex",
        "futa_sex",
        "futa_sex",
        "doggy",
        "futa_sex",
    ]
    assert [c["situation"] for c in story["clips"]] == want
    assert [c["label"] for c in story["clips"]] == [
        "玄関・サヤカがレイをジュボ",
        "シンク・アヤがレイの口内",
        "路地・アヤがレイを根元",
        "トイレ・サヤカがレイのマンコ舐め",
        "屋上・レイがアヤに挿入",
        "洗い場・サヤカがマドカをジュボ",
        "食卓下・アヤがマドカの口内",
        "布団・レイがサヤカに挿入",
        "ソファ・レイがアヤに挿入",
        "縁側・マドカがアヤに挿入",
        "台所・マドカがサヤカに後背",
        "廊下・マドカがサヤカに立ち挿入",
    ]
    for clip in story["clips"]:
        assert float(clip["duration_s"]) == 10
        assert "10-second take" in clip["prompt"]
        assert "Saleswoman" not in clip["prompt"]
        assert "Instructor" not in clip["prompt"]
        names = {str(n).strip().lower() for n in clip["names"]}
        assert len(names) == 2
        assert names <= (SHORTS_SHAFT | SHORTS_RECEIVER)
        assert names & SHORTS_SHAFT
        assert names & SHORTS_RECEIVER
        if "Clear futanari" in clip["prompt"]:
            assert "Penis plus vagina, never balls" in clip["prompt"]
            assert "no scrotum" in clip["prompt"]
        if "Aya:" in clip["prompt"] or "Sayaka:" in clip["prompt"]:
            assert "NO penis" in clip["prompt"]
        sit = clip["situation"]
        if sit in {"oral", "oral_creampie", "cunnilingus_futa"}:
            assert "Full bodies from head to feet" not in clip["prompt"]
            assert "Vertical 9:16 576x1024" in clip["prompt"]
        else:
            assert "Full bodies from head to feet" in clip["prompt"]
        if sit == "oral_creampie":
            assert "white liquid" in clip["prompt"].lower()
            assert "ドロドロ" in clip["prompt"]
            assert "viscous" in clip["prompt"].lower()
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
        assert planned["duration_s"] == 10
        assert "ROLE LOCK" in planned["prompt"]
        assert "at 0.00 seconds" not in planned["prompt"]
        cw, ch = story_canvas_wh(story, clip)
        assert (planned["width"], planned["height"]) == (cw, ch)
        assert (cw, ch) == (int(clip["canvas"]["width"]), int(clip["canvas"]["height"]))
        ids = [row["id"] for row in planned["stack"]]
        assert "futa-h3-v51" not in ids
        assert "penis-lora-h3" not in ids
        assert "synth-pussy-h3" in ids
        assert "larry-v4" not in ids
        assert all(row.get("arch") != "fl2va" for row in planned["stack"])
        if planned["situation"] == "oral":
            assert "blowjob-h3" in ids
            assert "minimax-h3-turbo-ref2v-4step" in ids or not planned.get("turbo")
        if planned["situation"] == "oral_creampie":
            assert ids == ["aftermidnight-ref2va", "synth-pussy-h3"]
            assert "white liquid" in planned["prompt"].lower()
            assert "viscous" in planned["prompt"].lower() or "sticky" in planned["prompt"].lower() or "thick gooey" in planned["prompt"].lower()
        if planned["situation"] == "futa_sex":
            assert ids == ["aftermidnight-ref2va", "synth-pussy-h3"]
            assert clip["prompt"].startswith("hmmotion, PENISLORA")
            assert "hmmotion" in planned["prompt"]
            assert "INSIDE LOCK:" in planned["prompt"]
            assert "INSIDE LOCK:" in clip["prompt"]
        if planned["situation"] == "doggy":
            assert ids == ["aftermidnight-ref2va", "synth-pussy-h3"]
            assert "INSIDE LOCK:" in planned["prompt"]
            assert "INSIDE LOCK:" in clip["prompt"]
        if planned["situation"] in {"oral", "oral_creampie"}:
            assert "ORAL LOCK:" in planned["prompt"]
            assert "INSIDE LOCK:" not in planned["prompt"]
        if planned["situation"] == "cunnilingus_futa":
            assert ids == ["aftermidnight-ref2va", "synth-pussy-h3"]
            assert "blowjob-h3" not in ids


def test_final_audit_no_thin_semen_no_water_bath_pull_off_starts_deep(tmp_path):
    """総点検: 抜く本も frame 1 は根元。精液は全話で重油級（thin 禁止）。ザーメン風呂に湯は無い。題の秒数は実際の合計。"""
    cast = tmp_path / "cast"
    _write_cast_stills(cast)
    thin = re.compile(r"(?<!not )\bthin white\b|hits the water|stays on the water|clinging to the water", re.I)
    seen_pull_off = 0
    for sid in sorted(STORY_IDS | CHAIN_PACK_IDS):
        story = load_story(sid)
        total = int(sum(float(c.get("duration_s") or story.get("clip_s") or 10) for c in story["clips"]))
        m = re.search(r"(\d+)秒", str(story.get("title_ja") or ""))
        if m:
            assert int(m.group(1)) == total, (sid, story.get("title_ja"), total)
        for i, clip in enumerate(story["clips"]):
            planned = prepare_story_clip(
                story, i, last_frame=(f"h3_chain_{i-1}.png" if i else None), stills_dir=tmp_path, cast_dir=cast
            )
            prompt = planned["prompt"]
            assert not thin.search(prompt), (sid, i + 1, thin.search(prompt).group(0))
            sit = planned["situation"]
            if sit in {"oral", "futa_blowjob", "oral_creampie"} and not re.search(r"urine|yellow", prompt, re.I):
                assert "ORAL LOCK:" in prompt, (sid, i + 1)
                assert "at the BASE" in prompt or "to the BASE" in prompt, (sid, i + 1)
                if "Start deep at the BASE" in prompt:
                    seen_pull_off += 1
                    assert "slides all the way OFF" in prompt
    assert seen_pull_off >= 3
    bath = load_story("semen-bath-70s")
    blob = "\n".join(c["prompt"] for c in bath["clips"])
    assert "aimed down at the water" not in blob
    assert "hits the water" not in blob
