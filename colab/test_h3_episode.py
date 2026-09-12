import copy
import json
import shutil
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "minimaxh3"))
sys.path.insert(0, str(ROOT / "minimaxh3" / "grokbot"))

from h3_episode import (  # noqa: E402
    CANVAS,
    CONTINUITY_CLAUSE,
    EPISODE_HELPERS,
    I2VA_HEADER,
    MUNDANE_CLAUSE,
    PRESETS,
    EpisodeError,
    assert_not_production_root,
    beat_props,
    beat_prompts,
    beat_window,
    build_beat_prompt,
    build_episode_graph,
    canvas_for,
    duration_ladder,
    episode_assets,
    episode_root,
    expected_duration,
    finish_episode,
    forbidden_hits,
    load_episode,
    materialize_reuse,
    output_size_for,
    plan_lines,
    preflight,
    render_beat_comfy,
    resolve_preset,
    run_episode,
    stage_still,
    stills_trailer,
    subtitle_windows,
    validate_beat_prompt,
    validate_episode,
)
from h3_hud import (  # noqa: E402
    compose_beat,
    expected_stitch_duration,
    extract_frame,
    find_font,
    font_covers,
    keyword_segments,
    probe_duration,
    probe_video_size,
    render_complete_layer,
    render_end_card,
    render_fail_card,
    render_hud_layer,
    render_menu_layer,
    render_mission_layer,
    render_subtitle_layer,
    render_title_card,
    synthetic_clip,
    window_for,
)
from h3_i2v_job import default_job, ensure_drive_tree, next_ready_job, save_job  # noqa: E402
from PIL import Image  # noqa: E402
from run_episode import exec_script  # noqa: E402

EP_DIR = ROOT / "minimaxh3" / "episodes" / "bandai-district"
SHORT_DIR = ROOT / "minimaxh3" / "episodes" / "bandai-district-short"
TEMPLATE = ROOT / "minimaxh3" / "episodes" / "_template" / "episode.json"
HAS_FFMPEG = shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None


def bandai() -> dict:
    return load_episode(EP_DIR / "episode.json")


def short() -> dict:
    return load_episode(SHORT_DIR / "episode.json")


# ---------------------------------------------------------------- sync / files

def test_colab_and_minimaxh3_copies_in_sync():
    for name in ("h3_hud.py", "h3_episode.py", "h3_episode_colab_main.py"):
        a = (ROOT / "colab" / name).read_text(encoding="utf-8")
        b = (ROOT / "minimaxh3" / name).read_text(encoding="utf-8")
        assert a == b, f"{name} differs between colab/ and minimaxh3/ (copy after editing)"


def test_helpers_list_matches_files():
    for rel in EPISODE_HELPERS:
        assert (ROOT / rel).is_file(), rel
    assert "colab/h3_episode.py" in EPISODE_HELPERS
    assert "colab/h3_colab_main.py" not in EPISODE_HELPERS  # the Grokbot dispatcher is not part of episodes


def test_notebook_is_one_cell_and_isolated():
    nb = json.loads((ROOT / "minimax_h3_episode_bot.ipynb").read_text(encoding="utf-8"))
    code = [c for c in nb["cells"] if c["cell_type"] == "code"]
    assert len(code) == 1
    src = "".join(code[0]["source"])
    assert "h3_episode_colab_main" in src
    assert 'EPISODE = "bandai-district"' in src
    assert "episodes" in src and "_lib" in src
    assert "adopt_orphan" not in src and "bot_prepare" not in src
    assert "inbox" not in src
    # Colab IPython treats SystemExit(0) as a red traceback; only fail on nonzero.
    assert "if rc:" in src
    assert 'raise SystemExit(rc)' in src
    assert src.index("if rc:") < src.index("raise SystemExit(rc)")
    assert json.loads((ROOT / "minimaxh3" / "minimax_h3_episode_bot.ipynb").read_text(encoding="utf-8")) == nb


def test_stills_are_clean_and_720p():
    ep = bandai()
    for beat in ep["beats"]:
        p = EP_DIR / beat["still"]
        assert p.is_file()
        assert "-hud" not in p.stem
        assert Image.open(p).size == (1280, 720)


# ---------------------------------------------------------------- schema

def test_bandai_episode_validates_and_preflights():
    ep = bandai()
    assert validate_episode(ep, root=EP_DIR) == []
    errs = preflight(ep, EP_DIR, need_ffmpeg=False)
    assert errs == []
    assert canvas_for(ep) == CANVAS["16:9"] == (1024, 576)
    assert output_size_for(ep) == (1280, 720)
    assert len(ep["beats"]) == 9
    assert duration_ladder(ep) == [10.0, 8.0, 6.0]


def test_template_validates_without_disk():
    ep = load_episode(TEMPLATE)
    assert validate_episode(ep) == []
    assert ep["tone"] == "mundane" and ep["cards"]["fail"]["text"] == "ミッション失敗"
    assert ep["beats"][2]["source"] == "ui" and ep["beats"][3]["source"] == "chain"
    assert [b["id"] for b, _p, _e in beat_prompts(ep)] == ["01-open", "02-talk", "04-end"]  # ui beat has no prompt


# ---------------------------------------------------------------- short (mundane / failed) grammar

def test_short_episode_validates_and_plans_under_25s():
    ep = short()
    assert validate_episode(ep, root=SHORT_DIR) == []
    assert preflight(ep, SHORT_DIR, need_ffmpeg=False) == []
    assert ep["tone"] == "mundane" and ep["violence"] == "none" and ep["cards"]["title"] is False
    assert 20.0 <= expected_duration(ep) <= 25.0
    ids = [b["id"] for b in ep["beats"]]
    assert ids == ["01-exit-noren", "02-bike", "03-barber", "04-tools", "05-truck"]
    assert [b.get("reuse") for b in ep["beats"]] == ["bandai-district/01-exit-noren", "bandai-district/02-bike", None, None, "bandai-district/05-truck"]
    assert ep["beats"][2]["hud"]["visible"] is False and ep["beats"][2]["hud"]["complete"] is True
    assert ep["beats"][4]["hud"]["complete"] is False  # Failed, not Complete
    # the only GPU beat is the barbershop re-render; windows are 3-6s like the reference's cuts
    assert [beat_window(ep, b) for b in ep["beats"]] == [(0.0, 3.0), (0.0, 5.0), (0.0, 6.0), (0.0, 2.2), (0.0, 4.8)]
    assert [b["id"] for b, _p, _e in beat_prompts(ep, trigger="DY")] == ["01-exit-noren", "02-bike", "03-barber", "05-truck"]
    for rel in episode_assets(ep):
        assert (SHORT_DIR / rel).is_file(), rel
    lines = plan_lines(ep, SHORT_DIR)
    assert len(lines) == 5 and "cutscene" in lines[2] and "menu" in lines[3] and "reuse bandai-district/05-truck" in lines[4]


def test_per_beat_props_and_continuity_lock_in_prompts():
    ep = bandai()
    rows = {b["id"]: p for b, p, _e in beat_prompts(ep, trigger="DY")}
    truck = ep["props"]["truck"]
    # the leak that put a firewood truck into the noren shot, the bicycle shot and the barbershop
    for bid in ("01-exit-noren", "02-bike", "03-barber", "04-talk"):
        assert truck not in rows[bid], bid
        assert "kei pickup" not in rows[bid], bid
    assert truck in rows["05-truck"] and truck in rows["08-boiler-blast"]
    assert ep["props"]["bicycle"] in rows["02-bike"] and ep["props"]["bicycle"] not in rows["01-exit-noren"]
    assert "Props in this shot stay locked" not in rows["04-talk"]
    for p in rows.values():
        assert CONTINUITY_CLAUSE in p
        assert MUNDANE_CLAUSE not in p  # action tone
        assert p.index("is the identity, costume, prop, and set lock") < p.index(CONTINUITY_CLAUSE)
    assert rows["05-truck"].index(CONTINUITY_CLAUSE) < rows["05-truck"].index("Props in this shot stay locked")
    assert beat_props(ep, ep["beats"][0]) == ["tenugui"]
    # without an explicit list only props named in the beat text are attached
    auto = dict(ep["beats"][1])
    auto.pop("props")
    assert beat_props(ep, auto) == ["bicycle"]
    assert beat_props(ep, dict(auto, action="she walks", camera="camera behind her", place="street")) == []
    assert any("unknown prop" in e for e in validate_episode(dict(ep, beats=[dict(ep["beats"][0], props=["laser"])] + ep["beats"][1:])))


def test_mundane_tone_rules():
    ep = short()
    assert MUNDANE_CLAUSE in build_beat_prompt(ep, ep["beats"][2])
    bad = copy.deepcopy(ep)
    bad["beats"][0]["action"] += ", no explosion, nobody jumps"
    errs = validate_episode(bad)
    assert any("set-piece words" in e and "explosion" in e for e in errs)
    bad = copy.deepcopy(ep)
    bad["beats"][0]["physics"] = True
    assert any("forbids physics" in e for e in validate_episode(bad))
    bad = copy.deepcopy(ep)
    bad["violence"] = "game"
    assert any("violence none" in e for e in validate_episode(bad))
    bad = copy.deepcopy(ep)
    for b in bad["beats"]:
        if b["source"] != "ui":
            b["face_visible"] = True
    assert any("at most 2 face_visible" in e for e in validate_episode(bad))
    bad = copy.deepcopy(ep)
    bad["tone"] = "epic"
    assert any("tone must be" in e for e in validate_episode(bad))
    # the long action episode is untouched by the mundane rules
    assert validate_episode(bandai(), root=EP_DIR) == []


def test_trim_reuse_ui_and_fail_schema():
    ep = short()
    bad = copy.deepcopy(ep)
    bad["beats"][0]["trim"] = {"start": 8, "seconds": 4}
    assert any("ends after" in e for e in validate_episode(bad))
    bad = copy.deepcopy(ep)
    bad["beats"][0]["trim"] = {"start": 0, "seconds": 1}
    assert any(">= 1.5s" in e for e in validate_episode(bad))
    bad = copy.deepcopy(ep)
    bad["beats"][0]["reuse"] = "Bad Slug/01"
    assert any("reuse must look like" in e for e in validate_episode(bad))
    bad = copy.deepcopy(ep)
    bad["beats"][0]["reuse"] = "bandai-district-short/01-exit-noren"
    assert any("point at itself" in e for e in validate_episode(bad))
    bad = copy.deepcopy(ep)
    bad["beats"][3]["seconds"] = 9
    assert any("ui beat needs seconds" in e for e in validate_episode(bad))
    bad = copy.deepcopy(ep)
    bad["beats"][3]["menu"]["items"] = ["one"]
    assert any("2-8 entries" in e for e in validate_episode(bad))
    bad = copy.deepcopy(ep)
    bad["beats"][3]["menu"]["selected"] = 7
    assert any("selected out of range" in e for e in validate_episode(bad))
    bad = copy.deepcopy(ep)
    bad["beats"].insert(0, copy.deepcopy(ep["beats"][3]))
    assert any("first beat cannot be ui" in e for e in validate_episode(bad))
    bad = copy.deepcopy(ep)
    bad["beats"].insert(4, dict(copy.deepcopy(ep["beats"][3]), id="04-again"))
    assert any("two ui beats in a row" in e for e in validate_episode(bad))
    bad = copy.deepcopy(ep)
    bad["beats"][3]["speech"] = [{"who": "aki", "line": "あ"}]
    assert any("frozen frame" in e for e in validate_episode(bad))
    bad = copy.deepcopy(ep)
    bad["beats"][2]["hud"]["mission_keyword"] = "薪"
    assert any("mission_keyword must be part" in e for e in validate_episode(bad))
    bad = copy.deepcopy(ep)
    bad["beats"][-1]["hud"]["complete"] = True
    assert any("cannot flash ミッション完了" in e for e in validate_episode(bad))
    bad = copy.deepcopy(ep)
    bad["cards"]["fail"]["reason"] = "あ" * 31
    assert any("reason <= 30" in e for e in validate_episode(bad))
    bad = copy.deepcopy(ep)
    bad["cards"]["fail"]["image"] = "stills/nope.jpg"
    assert "stills/nope.jpg" in episode_assets(bad)
    assert any("asset missing" in e for e in validate_episode(bad, root=SHORT_DIR))
    bad = copy.deepcopy(ep)
    bad["beats"][2]["speech"][0]["at"] = 7.0  # window is 6s
    assert any("inside the beat window" in e for e in validate_episode(bad))
    bad = copy.deepcopy(ep)
    bad["beats"][2]["speech"][0]["text"] = "x" * 31
    assert any("subtitle" in e for e in validate_episode(bad))


def test_subtitle_windows_and_keyword_segments():
    lines = [{"line": "a"}, {"line": "b"}]
    win = subtitle_windows(lines, 6.0)
    assert len(win) == 2 and win[0][0] == pytest.approx(0.3) and win[0][1] < win[1][0] and win[1][1] <= 6.0
    assert subtitle_windows([{"line": "a", "at": 1.0, "until": 2.5}], 6.0) == [(1.0, 2.5)]
    assert subtitle_windows([], 6.0) == []
    assert keyword_segments("薪を白湯へ運べ", "薪") == [("薪", True), ("を白湯へ運べ", False)]
    assert keyword_segments("手ぬぐいを理容室へ返せ", "理容室") == [("手ぬぐいを", False), ("理容室", True), ("へ返せ", False)]
    assert keyword_segments("手ぬぐいを返せ", "") == [("手ぬぐいを返せ", False)]
    assert keyword_segments("手ぬぐいを返せ", "薪") == [("手ぬぐいを返せ", False)]


def test_new_layers_render():
    size = (1280, 720)
    plain = render_mission_layer(size, "薪を白湯へ運べ")
    accent = render_mission_layer(size, "薪を白湯へ運べ", keyword="薪")
    assert accent.getbbox() == plain.getbbox()
    assert accent.tobytes() != plain.tobytes()  # the keyword took the accent colour
    sub = render_subtitle_layer(size, "おお、助かる。薪も頼むよ")
    assert sub.getbbox() is not None and render_subtitle_layer(size, "").getbbox() is None
    low = render_subtitle_layer(size, "字幕", above_mission=False).getbbox()
    high = render_subtitle_layer(size, "字幕", above_mission=True).getbbox()
    assert high[1] < low[1]
    menu = render_menu_layer(size, title="番台の道具", items=["手ぬぐい", "桶", "軍手"], selected=2)
    assert menu.size == size and menu.mode == "RGBA"
    fail = render_fail_card(size, reason="薪を積みすぎて軽トラが動かなかった")
    assert fail.size == size and fail.mode == "RGB"
    assert render_fail_card((720, 1280), text="失敗").size == (720, 1280)


def test_first_beat_cannot_chain_and_hud_stills_rejected(tmp_path):
    ep = bandai()
    ep["beats"][0]["source"] = "chain"
    assert any("first beat cannot be chain" in e for e in validate_episode(ep))
    ep = bandai()
    ep["beats"][1]["still"] = "stills/02-bike-hud.jpg"
    assert any("HUD-burned" in e for e in validate_episode(ep))


def test_speech_rules():
    ep = bandai()
    ep["beats"][0]["speech"] = [{"who": "aki", "line": "いくよ"}]  # face not visible
    assert any("face_visible" in e for e in validate_episode(ep))
    ep = bandai()
    ep["beats"][2]["speech"] = [{"who": "aki", "line": "手ぬぐいです"}]  # kanji
    assert any("kana only" in e for e in validate_episode(ep))
    ep = bandai()
    ep["beats"][2]["speech"] = [{"who": "gen", "line": "おい"}]  # not in beat cast
    assert any("not in this beat's cast" in e for e in validate_episode(ep))


def test_minor_cast_rejected_and_disclaimer_required():
    ep = bandai()
    ep["cast"]["aki"]["age"] = 16
    assert any("adult" in e for e in validate_episode(ep))
    ep = bandai()
    ep["cards"]["disclaimer"] = ""
    ep["cards"]["end_lines"] = []
    assert any("disclaimer" in e for e in validate_episode(ep))


# ---------------------------------------------------------------- prompts

def test_prompts_english_with_japanese_only_in_quotes():
    ep = bandai()
    never = ep["homage"]["never"]
    rows = beat_prompts(ep, trigger="DY")
    assert len(rows) == 9
    for beat, prompt, errs in rows:
        assert errs == [], (beat["id"], errs)
        assert prompt.startswith("DY\n")
        assert I2VA_HEADER in prompt and "<Picture 1>" in prompt
        for key in ("subject_definitions:", "environment:", "integrated_multimodal_description:", "overall_soundscape:", "non_diegetic_music:"):
            assert key in prompt
        assert "Adults only in frame" in prompt
        assert "no readable letters" in prompt
        assert "lip-synced" not in prompt.lower()
        for bad in never:
            assert bad.lower() not in prompt.lower()
    talk = rows[3][1]
    assert "「まきが ぜんぶ もっていかれた」" in talk
    assert talk.count("「まきが ぜんぶ もっていかれた」") == 2  # once visual, once audio
    uppercut = rows[6][1]
    assert "ragdolls" in uppercut and "no blood" in uppercut
    assert "Shoryuken" not in uppercut and "shoryuken" not in uppercut.lower()


def test_forbidden_tokens():
    assert forbidden_hits("A grandma delivers the 回覧板 to Tanaka", never=["回覧板", "grandma"]) == ["回覧板", "grandma"]
    hits = forbidden_hits("Street Fighter style Shoryuken with a GTA minimap and HUD, blood everywhere, lip-synced line")
    low = [h.lower() for h in hits]
    for tok in ("street fighter", "shoryuken", "gta", "minimap", "hud", "blood", "lip-synced"):
        assert tok in low, (tok, hits)
    assert forbidden_hits("Nobody is hurt, no blood, no injuries, no children anywhere. No HUD, no watermark.") == []
    assert forbidden_hits("visit px.a8.net for 月収") != []
    assert "loli" in [h.lower() for h in forbidden_hits("a loli character waves")]


def test_validate_beat_prompt_shapes():
    ep = bandai()
    beat = ep["beats"][0]
    good = build_beat_prompt(ep, beat)
    assert validate_beat_prompt(good, source="still") == []
    assert any("T2V beat must not reference Picture 1" in e for e in validate_beat_prompt(good, source="t2v"))
    t2v_beat = dict(beat, source="t2v")
    t2v = build_beat_prompt(ep, t2v_beat)
    assert validate_beat_prompt(t2v, source="t2v") == []
    assert "<Picture 1>" not in t2v and "Horizontal 16:9" in t2v
    bad = good.replace("Aki pushes", "Aki 押す")
    assert any("Japanese outside" in e for e in validate_beat_prompt(bad, source="still"))


# ---------------------------------------------------------------- presets / graphs

def test_resolve_preset_fallbacks(tmp_path):
    loras = tmp_path / "loras"
    loras.mkdir()
    with pytest.raises(EpisodeError):
        resolve_preset("fast", loras)  # turbo LoRA not downloaded yet → nothing to fall back to
    (loras / "minimax_h3_fl2v_turbo_4step_v1.0_768p_comfyui_bf16.safetensors").write_bytes(b"x")
    fast = resolve_preset("fast", loras)
    assert fast["name"] == "fast" and [s[0] for s in fast["stack"]] == ["minimax_h3_fl2v_turbo_4step_v1.0_768p_comfyui_bf16.safetensors"]
    daily = resolve_preset("daily", loras, fallback="fast")
    assert daily["name"] == "fast" and any("required LoRA missing" in n for n in daily["notes"])
    (loras / "minimax_h3_turbo_v4_step600_ema_comfy.safetensors").write_bytes(b"x")
    daily = resolve_preset("daily", loras, fallback="fast")
    assert daily["name"] == "daily" and len(daily["stack"]) == 1 and daily["steps"] == 8 and daily["trigger"] == "DY"
    (loras / "Minimax_H3_cinematic_DY.safetensors").write_bytes(b"x")
    daily = resolve_preset("daily", loras, fallback="fast")
    assert [round(s[1], 2) for s in daily["stack"]] == [1.0, 0.65]
    for name, spec in PRESETS.items():
        keys = [k for k, _s, _o in spec["stack"]]
        assert not ("larry" in keys and any(k.startswith("turbo") for k in keys)), name


def test_graph_chains_loras_and_passes_studio_assert():
    ep = bandai()
    prompt = build_beat_prompt(ep, ep["beats"][0], trigger="DY")
    preset = {"name": "daily", "stack": [("larry.safetensors", 1.0), ("cinema.safetensors", 0.65)], "steps": 8, "trigger": "DY"}
    g = build_episode_graph(source="still", first_image="01.jpg", prompt=prompt, unet="fl2va.safetensors", preset=preset, width=1024, height=576, duration_s=10, seed=42, filename_prefix="video/h3_ep_test")
    assert g["2"]["inputs"]["lora_name"] == "larry.safetensors"
    assert g["2b"]["inputs"]["lora_name"] == "cinema.safetensors"
    assert g["2b"]["inputs"]["model"] == ["2", 0]
    assert g["23"]["inputs"]["model"] == ["2b", 0] and g["24"]["inputs"]["model"] == ["2b", 0]
    assert g["23"]["inputs"]["steps"] == 8
    assert "first_frame" in g["20"]["inputs"] and "last_frame" not in g["20"]["inputs"]
    t2v = build_episode_graph(source="t2v", first_image=None, prompt=build_beat_prompt(ep, dict(ep["beats"][0], source="t2v")), unet="fl2va.safetensors", preset=preset, width=1024, height=576, duration_s=10, seed=1, filename_prefix="video/t")
    assert not any(n.get("class_type") == "LoadImage" for n in t2v.values())
    with pytest.raises(EpisodeError):
        build_episode_graph(source="still", first_image=None, prompt=prompt, unet="u", preset=preset, width=1024, height=576, duration_s=10, seed=1, filename_prefix="x")


def test_render_beat_keeps_canvas_and_shortens_on_oom(tmp_path):
    comfy = tmp_path / "ComfyUI"
    (comfy / "output" / "video").mkdir(parents=True)
    (comfy / "models" / "diffusion_models").mkdir(parents=True)
    ep = bandai()
    prompt = build_beat_prompt(ep, ep["beats"][0])
    calls = []

    def poster(graph, port):
        calls.append((graph["20"]["inputs"]["width"], graph["20"]["inputs"]["height"], graph["20"]["inputs"]["length"]))
        if len(calls) == 1:
            return None, "HTTP 500: CUDA out of memory"
        return {"prompt_id": "p1"}, None

    def waiter(pid, port):
        (comfy / "output" / "video" / "h3_ep_x_00001.mp4").write_bytes(b"mp4")
        return True, {"outputs": {"29": {"videos": [{"filename": "h3_ep_x_00001.mp4", "subfolder": "video"}]}}}

    res = render_beat_comfy(source="still", first_image="a.jpg", prompt=prompt, comfy_dir=comfy, canvas=(1024, 576), durations=[10.0, 8.0, 6.0], preset=resolve_preset("fast", None), seed=1, filename_prefix="video/h3_ep_x", poster=poster, waiter=waiter)
    assert res["duration_s"] == 8.0 and res["canvas"] == "1024x576"
    assert [c[:2] for c in calls] == [(1024, 576), (1024, 576)]
    assert calls[0][2] > calls[1][2]


# ---------------------------------------------------------------- isolation

def test_episode_root_is_outside_grokbot_buckets(tmp_path):
    main = tmp_path / "minimax-h3-comfyui"
    root = episode_root("bandai-district", main)
    assert root == main / "episodes" / "bandai-district"
    assert_not_production_root(root, main)
    with pytest.raises(EpisodeError):
        assert_not_production_root(main / "inbox", main)
    with pytest.raises(EpisodeError):
        episode_root("Bad Slug", main)


def test_grokbot_i2v_never_sees_episode_clips(tmp_path):
    main = ensure_drive_tree(tmp_path / "minimax-h3-comfyui")
    root = episode_root("bandai-district", main)
    (root / "raw").mkdir(parents=True)
    (root / "stills").mkdir(parents=True)
    (root / "stills" / "01.jpg").write_bytes(b"jpg")
    (root / "raw" / "01.mp4").write_bytes(b"mp4")
    assert next_ready_job(main, mode="i2v") is None
    job = default_job(id="real-coconala", mode="i2v")
    folder = main / "inbox" / job["id"]
    folder.mkdir()
    (folder / "source.jpg").write_bytes(b"still")
    save_job(folder, job)
    assert next_ready_job(main, mode="i2v") == folder


def test_exec_script_is_self_contained():
    script = exec_script("bandai-district", preset="daily", fresh=True, branch="cursor/x", main_path=Path("/content/h3_episode_colab_main.py"))
    assert "os.environ['H3_EPISODE'] = 'bandai-district'" in script
    assert "H3_EPISODE_FRESH'] = '1'" in script
    assert "raw.githubusercontent.com/fireworker011/Research/cursor/x" in script
    assert "colab/h3_episode.py" in script and "runpy.run_path" in script
    compile(script, "exec_script", "exec")


# ---------------------------------------------------------------- hud

def test_font_and_layers():
    font = find_font()
    assert font_covers(font)
    size = (1280, 720)
    hud = render_hud_layer(size, {"health": 0.5, "stamina": 0.2, "money": "¥1", "heat": 3, "hint": "F 乗車"}, district="白湯 Dist.", icons=["湯", "薪"])
    assert hud.size == size and hud.mode == "RGBA"
    assert hud.getbbox() is not None
    assert render_mission_layer(size, "薪を白湯へ取り返せ").getbbox() is not None
    assert render_mission_layer(size, "").getbbox() is None
    assert render_complete_layer(size).size == size
    assert render_title_card(size, title="番台", subtitle="予告", kicker="オリジナル").size == size
    assert render_end_card((720, 1280), title="番台", lines=["架空のゲームです"]).size == (720, 1280)


def test_stage_still_scales_and_crops(tmp_path):
    src = tmp_path / "wide.png"
    Image.new("RGB", (1280, 720), (10, 20, 30)).save(src)
    out = stage_still(src, tmp_path / "a.jpg", (1024, 576))
    assert Image.open(out).size == (1024, 576)
    Image.new("RGB", (1000, 1000), (1, 2, 3)).save(src)
    out = stage_still(src, tmp_path / "b.jpg", (576, 1024))
    assert Image.open(out).size == (576, 1024)


def test_expected_duration_math():
    assert expected_stitch_duration([10, 10, 10], xfade_s=0.35) == pytest.approx(29.3)
    assert expected_stitch_duration([10, 10], transition="cut") == 20


@pytest.mark.skipif(not HAS_FFMPEG, reason="ffmpeg missing")
def test_dry_run_pipeline_end_to_end(tmp_path):
    ep = bandai()
    ep = copy.deepcopy(ep)
    ep["beats"] = ep["beats"][:2]
    ep["beats"][1]["source"] = "chain"
    ep["beats"][1].pop("still")
    ep["clip_seconds"] = 4
    root = tmp_path / "episodes" / "bandai-district"
    (root / "stills").mkdir(parents=True)
    for rel in episode_assets(ep):
        shutil.copy2(EP_DIR / rel, root / rel)
    final = run_episode(ep, root, dry_run=True)
    assert final.is_file() and (root / "final" / "latest.mp4").is_file()
    assert (root / "raw" / "01-exit-noren.mp4").is_file() and (root / "raw" / "02-bike.mp4").is_file()
    assert (root / "input" / "02-bike-last.jpg").is_file(), "chain beat must take the previous clip's last frame"
    assert probe_video_size(final) == (1280, 720)
    want = expected_stitch_duration([2.6, 4.0, 4.0, 3.2], xfade_s=0.35)
    assert probe_duration(final) == pytest.approx(want, abs=0.25)
    status = json.loads((root / "status.json").read_text(encoding="utf-8"))
    assert status["beats"]["02-bike"]["state"] == "done" and status["final"] == str(final)
    # resume: nothing re-rendered, finish still works
    before = (root / "raw" / "01-exit-noren.mp4").stat().st_mtime
    run_episode(ep, root, dry_run=True)
    assert (root / "raw" / "01-exit-noren.mp4").stat().st_mtime == before
    again = finish_episode(ep, root, out_name="again.mp4")
    assert again.is_file()


@pytest.mark.skipif(not HAS_FFMPEG, reason="ffmpeg missing")
def test_compose_beat_trim_subtitles_menu_and_frames(tmp_path):
    clip = synthetic_clip(tmp_path / "raw.mp4", seconds=6.0, canvas=(1024, 576))
    assert window_for(clip, trim_start=1.0, trim_seconds=3.0) == (1.0, pytest.approx(3.0, abs=0.05))
    assert window_for(clip)[1] == pytest.approx(6.0, abs=0.1)
    with pytest.raises(Exception):
        window_for(clip, trim_start=5.9)
    size = (1280, 720)
    sub = tmp_path / "sub.png"
    render_subtitle_layer(size, "字幕").save(sub)
    menu = tmp_path / "menu.png"
    render_menu_layer(size, title="道具", items=["一", "二"], selected=1).save(menu)
    mission = tmp_path / "mission.png"
    render_mission_layer(size, "薪を運べ", keyword="薪").save(mission)
    out = compose_beat(clip, tmp_path / "hud.mp4", out_size=size, hud_png=None, mission_png=mission, trim_start=1.0, trim_seconds=3.0, subtitles=[(sub, 0.3, 1.5)], menu_png=menu)
    assert probe_duration(out) == pytest.approx(3.0, abs=0.15) and probe_video_size(out) == size
    cutscene = compose_beat(clip, tmp_path / "cut.mp4", out_size=size, trim_seconds=2.0, subtitles=[(sub, 0.0, 2.0)])
    assert probe_duration(cutscene) == pytest.approx(2.0, abs=0.15)
    frame = extract_frame(clip, tmp_path / "f.jpg", at_s=2.0)
    assert Image.open(frame).size == (1024, 576)
    late = extract_frame(clip, tmp_path / "late.jpg", at_s=99.0)  # clamps to the last frame
    assert late.is_file()


def _short_tree(tmp_path: Path, *, clip_seconds: float) -> tuple[dict, Path, Path]:
    ep = copy.deepcopy(short())
    ep["clip_seconds"] = clip_seconds
    episodes = tmp_path / "episodes"
    sibling = episodes / "bandai-district" / "raw"
    sibling.mkdir(parents=True)
    root = episodes / "bandai-district-short"
    (root / "stills").mkdir(parents=True)
    for rel in episode_assets(ep):
        shutil.copy2(SHORT_DIR / rel, root / rel)
    return ep, root, sibling


@pytest.mark.skipif(not HAS_FFMPEG, reason="ffmpeg missing")
def test_short_pipeline_reuse_trim_ui_fail_end_to_end(tmp_path):
    ep, root, sibling = _short_tree(tmp_path, clip_seconds=6)
    for i, bid in enumerate(("01-exit-noren", "02-bike", "05-truck")):
        synthetic_clip(sibling / f"{bid}.mp4", seconds=6.0, canvas=(1024, 576), color=f"0x{40 + i * 60:02x}5060", tone_hz=300 + i * 50)
    assert validate_episode(ep, root=root) == []
    final = run_episode(ep, root, dry_run=True)
    assert final.is_file() and (root / "final" / "latest.mp4").is_file()
    status = json.loads((root / "status.json").read_text(encoding="utf-8"))
    assert status["beats"]["01-exit-noren"]["source"] == "reuse" and status["beats"]["01-exit-noren"]["reused"].endswith("bandai-district/raw/01-exit-noren.mp4")
    assert status["beats"]["05-truck"]["source"] == "reuse"
    assert status["beats"]["03-barber"]["source"] == "still" and status["beats"]["03-barber"]["state"] == "done"
    assert status["beats"]["04-tools"] == {"state": "done", "source": "ui"}
    # reused takes are byte-identical copies, the ui beat is a freeze of 03 at its cut point
    assert (root / "raw" / "02-bike.mp4").read_bytes() == (sibling / "02-bike.mp4").read_bytes()
    assert (root / "input" / "04-tools-freeze.jpg").is_file() and (root / "raw" / "04-tools.mp4").is_file()
    assert probe_duration(root / "raw" / "04-tools.mp4") == pytest.approx(2.2, abs=0.15)
    # windows applied: 3.0 / 5.0 / 6.0 / 2.2 / 4.8
    got = [probe_duration(root / "hud" / f"{b['id']}.mp4") for b in ep["beats"]]
    assert got == pytest.approx([3.0, 5.0, 6.0, 2.2, 4.8], abs=0.15)
    png = root / "hud" / "png"
    assert not (png / "03-barber-hud.png").exists() and not (png / "03-barber-mission.png").exists()  # cutscene
    assert (png / "03-barber-sub0.png").is_file() and (png / "03-barber-sub1.png").is_file() and (png / "03-barber-complete.png").is_file()
    assert (png / "04-tools-menu.png").is_file() and (png / "01-exit-noren-mission.png").is_file()
    assert (png / "card-fail.png").is_file() and (root / "input" / "fail-freeze.jpg").is_file()
    assert (root / "hud" / "98-fail.mp4").is_file() and (root / "hud" / "99-end.mp4").is_file()
    assert not (root / "hud" / "00-title.mp4").exists()  # cold open
    assert probe_duration(final) == pytest.approx(expected_duration(ep), abs=0.3)
    assert 20.0 <= probe_duration(final) <= 25.0
    # a second run re-renders nothing and still finishes
    before = (root / "raw" / "03-barber.mp4").stat().st_mtime
    run_episode(ep, root, dry_run=True)
    assert (root / "raw" / "03-barber.mp4").stat().st_mtime == before
    # without the sibling take the reuse beat falls back to rendering from its still
    ep2, root2, _sib2 = _short_tree(tmp_path / "b", clip_seconds=6)
    run_episode(ep2, root2, dry_run=True)
    st2 = json.loads((root2 / "status.json").read_text(encoding="utf-8"))
    assert st2["beats"]["01-exit-noren"]["source"] == "still" and (root2 / "input" / "01-exit-noren.jpg").is_file()


@pytest.mark.skipif(not HAS_FFMPEG, reason="ffmpeg missing")
def test_finish_materializes_reuse_and_stills_preview_ignores_trim(tmp_path):
    ep, root, sibling = _short_tree(tmp_path, clip_seconds=6)
    assert materialize_reuse(ep, root) == {}  # nothing on disk yet, nothing copied, no error
    for bid in ("01-exit-noren", "02-bike", "05-truck"):
        synthetic_clip(sibling / f"{bid}.mp4", seconds=6.0, canvas=(1024, 576))
    synthetic_clip(root / "raw" / "03-barber.mp4", seconds=6.0, canvas=(1024, 576), color="0x804020")
    final = finish_episode(ep, root, out_name="f.mp4")
    assert final.is_file() and (root / "raw" / "01-exit-noren.mp4").is_file()
    assert probe_duration(final) == pytest.approx(expected_duration(ep), abs=0.3)
    preview = stills_trailer(ep, root)
    assert preview.name == "bandai-district-short-stills-preview.mp4"
    want = expected_stitch_duration([2.5, 2.5, 2.5, 2.2, 2.5, 2.8, 3.0], xfade_s=0.35)
    assert probe_duration(preview) == pytest.approx(want, abs=0.3)
