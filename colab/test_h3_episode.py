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
    EPISODE_HELPERS,
    I2VA_HEADER,
    PRESETS,
    EpisodeError,
    assert_not_production_root,
    beat_prompts,
    build_beat_prompt,
    build_episode_graph,
    canvas_for,
    duration_ladder,
    episode_assets,
    episode_root,
    finish_episode,
    forbidden_hits,
    load_episode,
    output_size_for,
    preflight,
    render_beat_comfy,
    resolve_preset,
    run_episode,
    stage_still,
    validate_beat_prompt,
    validate_episode,
)
from h3_hud import (  # noqa: E402
    expected_stitch_duration,
    find_font,
    font_covers,
    probe_duration,
    probe_video_size,
    render_complete_layer,
    render_end_card,
    render_hud_layer,
    render_mission_layer,
    render_title_card,
)
from h3_i2v_job import default_job, ensure_drive_tree, next_ready_job, save_job  # noqa: E402
from PIL import Image  # noqa: E402
from run_episode import exec_script  # noqa: E402

EP_DIR = ROOT / "minimaxh3" / "episodes" / "bandai-district"
TEMPLATE = ROOT / "minimaxh3" / "episodes" / "_template" / "episode.json"
HAS_FFMPEG = shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None


def bandai() -> dict:
    return load_episode(EP_DIR / "episode.json")


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
    assert ep["beats"][2]["source"] == "chain"


def test_first_beat_cannot_chain_and_hud_stills_rejected(tmp_path):
    ep = bandai()
    ep["beats"][0]["source"] = "chain"
    assert any("cannot chain" in e for e in validate_episode(ep))
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
