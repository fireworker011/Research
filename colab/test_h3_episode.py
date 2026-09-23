import copy
import hashlib
import json
import os
import re
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
    CAMERA_PACKS,
    CANVAS,
    CHECKPOINTS,
    COMBAT_SAMPLER,
    COMBAT_SCHEDULER,
    COMBAT_STEPS,
    CONTINUITY_CLAUSE,
    DEFAULT_CAMERA_PACK,
    EPISODE_HELPERS,
    EROS_MAX_UNET,
    I2VA_HEADER,
    LORA_FILES,
    LORA_STRENGTHS,
    LORA_URLS,
    MAX_BEATS,
    MUNDANE_CLAUSE,
    PLANTED_CLAUSE,
    PLANTED_PACE_CLAUSE,
    PEE_STILL_CLAUSE,
    NELSON_PLANTED_CLAUSE,
    GAMEPLAY_PACE_CLAUSE,
    SIDERIDE_TRIGGER,
    PRESET_ALIASES,
    PRESET_CANON,
    PRESETS,
    STOCK_ONLY_SLUGS,
    STILL_LAST_HEADER,
    EpisodeError,
    apply_combat_route,
    apply_story_route,
    apply_rei_escape_route,
    apply_connect_mode,
    comfy_vram_for_lane,
    combat_lora_allowed,
    apply_extra_loras,
    apply_unet_preset_rules,
    assert_not_production_root,
    beat_prompts,
    beat_props,
    beat_clip_seconds,
    beat_renders,
    beat_source,
    beat_still_as,
    beat_vocals,
    beat_window,
    episode_voice,
    bootstrap_episode,
    build_beat_prompt,
    build_episode_graph,
    camera_angle,
    camera_line,
    canonical_connect,
    canonical_combat,
    canonical_preset,
    canvas_for,
    duration_ladder,
    ending_story,
    episode_assets,
    episode_camera_pack,
    episode_checkpoint,
    episode_connect,
    episode_combat,
    episode_lane,
    episode_root,
    ensure_episode_checkpoint,
    is_erotic_weight_path,
    is_high_mem,
    is_turbo_hybrid_unet,
    locate_erotic_checkpoint,
    expected_duration,
    extra_lora_entries,
    finish_episode,
    forbidden_hits,
    gpu_index_map,
    is_end_connect_beat,
    is_ui_beat,
    load_episode,
    materialize_reuse,
    merge_trigger,
    output_size_for,
    plan_lines,
    prepare_episode,
    preflight,
    render_beat_comfy,
    resolve_preset,
    resolve_unet,
    run_episode,
    stage_erotic_unet,
    stage_still,
    stills_trailer,
    subtitle_windows,
    uses_last_still,
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
from h3_episode_packs import (  # noqa: E402
    HOSPITAL_ENCOUNTERS,
    INVITE_POSE_MODES,
    STORY_MODES,
    TOILET_MODES,
    canonical_episode,
    describe_run,
    form_readme,
    parse_scenes,
    ui_choices,
    ui_default,
)
from h3_i2v_job import default_job, ensure_drive_tree, next_ready_job, save_job  # noqa: E402
from h3_i2v_runtime import comfy_launch_cmd, comfy_vram_flag, is_erotic_unet_name, pick_stock_fl2va  # noqa: E402
from PIL import Image  # noqa: E402
from run_episode import DEFAULT_BRANCH, exec_script  # noqa: E402

EP_DIR = ROOT / "minimaxh3" / "episodes" / "bandai-district"
SHORT_DIR = ROOT / "minimaxh3" / "episodes" / "bandai-district-short"
KASUMI_DIR = ROOT / "minimaxh3" / "episodes" / "kasumi-late-desk"
KASUMI_ADULT_DIR = ROOT / "minimaxh3" / "episodes" / "kasumi-late-desk-adult"
HOSPITAL_DIR = ROOT / "minimaxh3" / "episodes" / "hospital-exit-adult"
REI_ESCAPE_DIR = ROOT / "minimaxh3" / "episodes" / "futanari-rei-escape"
TEMPLATE = ROOT / "minimaxh3" / "episodes" / "_template" / "episode.json"
HAS_FFMPEG = shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None


def beats_prefixed(ep, prefix: str):
    return [
        b
        for b in ep["beats"]
        if str(b.get("id") or "") == prefix or str(b.get("id") or "").startswith(prefix + "-")
    ]


def action_blob(ep, prefix: str = "") -> str:
    beats = beats_prefixed(ep, prefix) if prefix else ep["beats"]
    return "\n".join(str(b.get("action") or "") for b in beats).lower()


_SEX_EXTRA_MOTION = (
    "kiss",
    "hug",
    "peck",
    "french",
    "chu",
    "semen share",
    "mouth-to-mouth",
    "tongue wrap",
    "embrace",
    "cuddle",
    "nuzzle",
    "caress",
)


def _assert_sex_beat_both_pleasure_no_extra_kiss(beat: dict, prompt: str) -> None:
    low = prompt.lower()
    action = str(beat.get("action") or "").lower()
    assert "both look like it feels really good" in low
    assert "flushed" in low
    assert "brows knit" in low
    if beat["id"].endswith("oral"):
        assert "enjoying the jupo" in low or "wet mouth on the shaft" in low
        assert "melting with pleasure" in low
        assert "hands stay on" in action and "hips" in action
    else:
        assert "hips moving" in low or "hands stay at the hips" in action
    for tok in _SEX_EXTRA_MOTION:
        pat = re.compile(rf"\b{re.escape(tok)}\b")
        assert not pat.search(low), (beat["id"], tok)
        assert not pat.search(action), (beat["id"], tok)


def bandai() -> dict:
    return load_episode(EP_DIR / "episode.json")


def short() -> dict:
    return load_episode(SHORT_DIR / "episode.json")


# ---------------------------------------------------------------- sync / files

def test_colab_and_minimaxh3_copies_in_sync():
    for name in ("h3_hud.py", "h3_episode.py", "h3_episode_packs.py", "h3_episode_colab_main.py"):
        a = (ROOT / "colab" / name).read_text(encoding="utf-8")
        b = (ROOT / "minimaxh3" / name).read_text(encoding="utf-8")
        assert a == b, f"{name} differs between colab/ and minimaxh3/ (copy after editing)"
    runtime_a = (ROOT / "colab" / "h3_i2v_runtime.py").read_text(encoding="utf-8")
    runtime_b = (ROOT / "minimaxh3" / "h3_i2v_runtime.py").read_text(encoding="utf-8")
    assert runtime_a == runtime_b, "h3_i2v_runtime.py differs between colab/ and minimaxh3/"


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
    assert 'EPISODE = "霞東フロア あさ（迷ったらこれ）"' in src
    assert "病棟出口" in src
    assert "番台ショート（25秒）" in src
    assert 'BRANCH = "cursor/h3-hospital-ward-34e4"' in src
    assert 'CivitaiのAPIキー = ""' in src
    assert 'os.environ["CIVITAI_API_TOKEN"] = _civitai' in src
    assert "619ea878c0bf2491f6cedd625329c5b3" not in src
    assert 'PRESET = "バランス（迷ったらこれ）"' in src
    assert "スピード（最速）" in src and "質（きれい・時間かかる）" in src
    assert 'CAMERA = "横スク（真横・全身・迷ったらこれ）"' in src
    assert "3Dアクション（引きの三人称）" in src
    assert 'CONNECT = "カット（本ごと独立・迷ったらこれ）"' in src
    assert "前の最終フレームから続ける" in src
    assert "用意した最終フレームへ着く" in src
    assert 'COMBAT = "格闘LoRAオフ（迷ったらこれ）"' in src
    assert "格闘LoRAオン（ハイメモリ専用）" in src
    assert "H3_EPISODE_CAMERA" in src
    assert "H3_EPISODE_CONNECT" in src
    assert 'os.environ["H3_EPISODE_END_CONNECT"] = "follow"' in src
    assert "END_CONNECT =" not in src
    assert "1番のつなぎに従う" not in src
    assert "次のシーンへ続ける" not in src
    assert "H3_EPISODE_COMBAT" in src
    assert "H3_EPISODE_STORY" in src
    assert "H3_EPISODE_INVITE_POSE" in src
    assert "H3_EPISODE_TOILET" in src
    assert "H3_EPISODE_GIN" in src
    assert "H3_EPISODE_TSUNO" in src
    assert "H3_EPISODE_APPEAR" in src
    assert "H3_EPISODE_SCENES" in src
    assert "SCENE_MIKI" in src and "SCENE_SHINO" in src
    assert "canonical_episode" in src
    assert 'STORY = "○受け入れる（生存・完了・迷ったらこれ）"' in src
    assert "□誘う（淫欲・失敗）" in src
    assert "△戦って負ける（敗北H・失敗・ハイメモリ）" in src
    assert 'INVITE_POSE = "四つん這い股広げ（迷ったらこれ）"' in src
    assert "対面M字騎乗（口のあと）" in src
    assert "壁立ちバック" in src
    assert "フルネルソンアナル" in src
    assert "ベロチュー→じゅぼ→騎乗位" not in src
    assert 'TOILET = "トイレに行かない（迷ったらこれ）"' in src
    assert 'GIN = "灰色・出ない（迷ったらこれ）"' in src
    assert 'TSUNO = "角・出ない（迷ったらこれ）"' in src
    assert "APPEAR_MIKI" in src and "APPEAR_SHINO" in src
    assert 'EPISODE = "kasumi-late-desk"' not in src
    md = "".join("".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "markdown")
    assert "619ea878c0bf2491f6cedd625329c5b3" not in md
    assert "CivitaiのAPIキー" in md
    assert "cursor/h3-hospital-ward-34e4" in md
    assert "kasumi-late-desk-adult" in md
    assert "10Eros Max は Drive" in md
    assert "10Eros_Max_h3_TURBO-hybrid_beta5_int8.safetensors" in md
    assert "迷ったら" in md
    assert "5. 構成" in md
    assert "6. 誘うポーズ" in md
    assert "7. トイレ" in md
    assert "8. 灰色" in md
    assert "9. 角" in md
    assert "シーンごと" in md
    assert "hospital-exit-adult" in md
    assert "病棟の話" in md
    assert "1. つなぎ方" in md or "つなぎ方" in md
    assert "シーン終わりのつなぎ" not in md
    assert "チェーンならフェード" in md
    assert "前の最終フレームから続ける" in md
    assert "episodes" in src and "_lib" in src
    assert "adopt_orphan" not in src and "bot_prepare" not in src
    assert "inbox" not in src
    # Colab IPython treats SystemExit(0) as a red traceback; only fail on nonzero.
    assert "if rc:" in src
    assert 'raise SystemExit(rc)' in src
    assert src.index("if rc:") < src.index("raise SystemExit(rc)")
    assert 'os.environ["H3_KEEP_RUNTIME"] = "1"' in src
    assert "ランタイムはそのまま" in src
    main_src = (ROOT / "colab" / "h3_episode_colab_main.py").read_text(encoding="utf-8")
    assert "maybe_unassign" not in main_src
    assert "runtime.unassign" not in main_src
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
    ep["beats"][2]["speech"] = [{"who": "aki", "line": "hello"}]
    assert any("Japanese kana only" in e or "no English" in e for e in validate_episode(ep))
    ep = bandai()
    ep["beats"][2]["speech"] = [{"who": "gen", "line": "おい"}]  # not in beat cast
    assert any("not in this beat's cast" in e for e in validate_episode(ep))
    ep = bandai()
    ep["beats"][0]["voices"] = [{"who": "aki", "line": "んっ"}]
    assert validate_episode(ep, root=EP_DIR) == []
    ep["beats"][0]["voices"] = [{"who": "aki", "line": "ahhh"}]
    assert any("Japanese kana only" in e for e in validate_episode(ep))


def test_adult_voices_japanese_only_in_quotes():
    for root in (KASUMI_ADULT_DIR, HOSPITAL_DIR):
        ep = load_episode(root / "episode.json")
        assert episode_voice(ep) == "japanese"
        assert validate_episode(ep, root=root) == []
        gpu = [b for b in ep["beats"] if beat_source(b) != "ui"]
        assert gpu and all(beat_vocals(b) for b in gpu)
        for beat, prompt, errs in beat_prompts(ep):
            assert errs == [], (ep["slug"], beat["id"], errs)
            assert "overall_soundscape:" in prompt
            assert "「" in prompt
            for item in beat_vocals(beat):
                line = item["line"]
                assert f"「{line}」" in prompt
            bad = dict(beat, voices=[{"who": beat["cast"][0], "line": "yes"}])
            p = build_beat_prompt(ep, bad)
            assert any("Japanese kana only" in e for e in validate_beat_prompt(p, source=beat_source(beat)))
        silent = copy.deepcopy(ep)
        for beat in silent["beats"]:
            beat.pop("voices", None)
            beat.pop("speech", None)
        assert any("japanese voice needs" in e for e in validate_episode(silent, root=root))


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
        resolve_preset("speed", loras)  # turbo LoRA not downloaded yet → nothing to fall back to
    (loras / "minimax_h3_fl2v_turbo_4step_v1.0_768p_comfyui_bf16.safetensors").write_bytes(b"x")
    speed = resolve_preset("speed", loras)
    assert speed["name"] == "speed" and speed["canonical"] == "speed"
    assert [s[0] for s in speed["stack"]] == ["minimax_h3_fl2v_turbo_4step_v1.0_768p_comfyui_bf16.safetensors"]
    assert speed["steps"] == 4 and speed["sampler"] == "euler" and speed["trigger"] == ""
    fast = resolve_preset("fast", loras)
    assert fast["name"] == "fast" and fast["canonical"] == "speed"
    assert [s[0] for s in fast["stack"]] == [s[0] for s in speed["stack"]]
    daily = resolve_preset("daily", loras, fallback="speed")
    assert daily["name"] == "speed" and any("required LoRA missing" in n for n in daily["notes"])
    (loras / "minimax_h3_turbo_v4_step600_ema_comfy.safetensors").write_bytes(b"x")
    daily = resolve_preset("daily", loras, fallback="speed")
    assert daily["name"] == "daily" and daily["canonical"] == "balance"
    assert len(daily["stack"]) == 1 and daily["steps"] == 8 and daily["trigger"] == ""
    balance = resolve_preset("balance", loras)
    assert [s[0] for s in balance["stack"]] == [s[0] for s in daily["stack"]] and balance["steps"] == 8
    quality = resolve_preset("quality", loras)
    assert quality["steps"] == 12 and quality["sampler"] == "euler" and quality["scheduler"] == "beta"
    assert len(quality["stack"]) == 1
    (loras / "Minimax_H3_cinematic_DY.safetensors").write_bytes(b"x")
    still_balance = resolve_preset("balance", loras, fallback="speed")
    assert [round(s[1], 2) for s in still_balance["stack"]] == [1.0]
    for name, spec in PRESETS.items():
        keys = [k for k, _s, _o in spec["stack"]]
        assert "cinema" not in keys, name
        assert not ("larry" in keys and any(k.startswith("turbo") for k in keys)), name
    assert set(PRESET_CANON) == {"speed", "balance", "quality"}
    assert PRESET_ALIASES["fast"] == "speed" and PRESET_ALIASES["daily"] == "balance"
    assert canonical_preset("スピード") == "speed" and canonical_preset("質優先") == "quality"
    assert "combat" in LORA_FILES and "combat" not in {k for spec in PRESETS.values() for k, _s, _o in spec["stack"]}
    assert "cinema" not in {k for spec in PRESET_CANON.values() for k, _s, _o in spec["stack"]}
    speed_on_hybrid = apply_unet_preset_rules(speed, EROS_MAX_UNET)
    assert speed_on_hybrid["stack"] == []
    assert any("TURBO-hybrid" in n for n in speed_on_hybrid["notes"])
    balance_on_hybrid = apply_unet_preset_rules(balance, EROS_MAX_UNET)
    assert balance_on_hybrid["stack"] == []
    assert balance_on_hybrid["steps"] == 8 and balance_on_hybrid["sampler"] == "euler"


def test_kasumi_late_desk_validates_and_stills_are_clean():
    ep = load_episode(KASUMI_DIR / "episode.json")
    assert validate_episode(ep, root=KASUMI_DIR) == []
    assert ep["tone"] == "action" and ep["violence"] == "game"
    assert len(ep["beats"]) == 12
    assert expected_duration(ep) == pytest.approx(44.9, abs=0.2)
    ids = [b["id"] for b in ep["beats"]]
    assert ids == [
        "01-cover",
        "02-ui-guard",
        "03-shove",
        "04-peek",
        "05-ui-boss",
        "06-files",
        "07-talk",
        "08-nana",
        "09-ui-nana",
        "10-mug",
        "11-bag",
        "12-desk",
    ]
    fights = [b for b in ep["beats"] if b.get("extra_loras") == ["combat"]]
    assert [b["id"] for b in fights] == ["03-shove", "06-files", "10-mug"]
    assert all(b.get("physics") and b.get("trigger") == "prfight2, prfin1" for b in fights)
    assert all(b.get("steps") == COMBAT_STEPS and b.get("sampler") == COMBAT_SAMPLER and b.get("scheduler") == COMBAT_SCHEDULER for b in fights)
    assert ep["beats"][2]["source"] == "chain" and ep["beats"][2].get("still")
    assert beat_still_as(ep["beats"][0]) == "both"
    assert all(beat_still_as(ep["beats"][i]) == "last" for i in (2, 5, 9, 11))
    assert uses_last_still(ep["beats"][2]) and not uses_last_still(ep["beats"][3])
    assert beat_window(ep, ep["beats"][2]) == (5.0, 5.0)
    assert ep["beats"][5]["source"] == "still" and beat_still_as(ep["beats"][5]) == "last"
    assert ep["beats"][9]["source"] == "still" and beat_still_as(ep["beats"][9]) == "last"
    assert ep["beats"][6]["source"] == "chain" and ep["beats"][6].get("face_visible")
    shove_prompt = build_beat_prompt(ep, ep["beats"][2], trigger=merge_trigger("DY", ep["beats"][2]))
    assert STILL_LAST_HEADER in shove_prompt and "<Picture 2>" in shove_prompt
    assert "lands on <Picture 2>" in shove_prompt
    assert "real-time third-person game speed" in shove_prompt
    assert "walking-and-hit pace" in shove_prompt
    assert "slow motion" not in shove_prompt.lower() and "slow-motion" not in shove_prompt.lower()
    assert not any(is_ui_beat(a) and is_ui_beat(b) for a, b in zip(ep["beats"], ep["beats"][1:]))
    for beat in ep["beats"]:
        still = beat.get("still")
        if still:
            p = KASUMI_DIR / still
            assert p.is_file()
            assert "-hud" not in p.stem
            assert Image.open(p).size == (1280, 720)
    for _b, prompt, errs in beat_prompts(ep, trigger="DY"):
        assert errs == []
        if "prfight2" in prompt:
            assert prompt.startswith("DY\nprfight2, prfin1")
        assert "badges carry no readable letters" in prompt


def test_kasumi_adult_is_erotic_eros_max_and_stock_kasumi_cannot_use_it():
    adult = load_episode(KASUMI_ADULT_DIR / "episode.json")
    stock = load_episode(KASUMI_DIR / "episode.json")
    assert validate_episode(adult, root=KASUMI_ADULT_DIR) == []
    assert episode_lane(adult) == "erotic"
    assert episode_checkpoint(adult) == "eros-max"
    assert CHECKPOINTS["eros-max"]["erotic"] is True
    assert CHECKPOINTS["eros-max"]["file"] == EROS_MAX_UNET
    assert EROS_MAX_UNET == "10Eros_Max_h3_TURBO-hybrid_beta5_int8.safetensors"
    assert is_turbo_hybrid_unet(EROS_MAX_UNET)
    assert is_erotic_unet_name(EROS_MAX_UNET)
    assert episode_lane(stock) == "stock"
    assert episode_checkpoint(stock) == "stock"
    assert "kasumi-late-desk" in STOCK_ONLY_SLUGS
    leaked = dict(stock)
    leaked["render"] = dict(stock["render"], lane="erotic", checkpoint="eros-max")
    assert any("stock episode" in e for e in validate_episode(leaked))
    stripped = dict(adult)
    stripped["render"] = {k: v for k, v in adult["render"].items() if k not in ("lane", "checkpoint")}
    assert any("render.lane erotic" in e for e in validate_episode(stripped))


def test_erotic_comfy_omits_removed_normalvram_flag():
    assert comfy_vram_for_lane("erotic") == "default"
    assert comfy_vram_for_lane("stock") == "highvram"
    assert comfy_vram_flag("default") == ""
    assert comfy_vram_flag("normalvram") == ""
    cmd = comfy_launch_cmd(port=8188, vram=comfy_vram_for_lane("erotic"))
    assert "--normalvram" not in cmd
    assert "--highvram" not in cmd
    assert cmd[:4] == [sys.executable, "main.py", "--listen", "127.0.0.1"]
    stock_cmd = comfy_launch_cmd(port=8188, vram=comfy_vram_for_lane("stock"))
    assert "--highvram" in stock_cmd
    assert "--normalvram" not in stock_cmd


def extra_keys(beat):
    return [k for k, _s in extra_lora_entries(beat)]


def _kasumi_adult_cast(ep):
    assert ep["cast"]["mio"]["age"] == 21
    assert ep["cast"]["nana"]["age"] == 23
    assert ep["cast"]["aoki"]["age"] == 27
    assert ep["cast"]["kuroki"]["age"] == 29
    assert "A-cup" in ep["cast"]["mio"]["lock"] and "slim" in ep["cast"]["mio"]["lock"]
    assert "cinched waist" in ep["cast"]["mio"]["lock"]
    assert "medium-length black hair" in ep["cast"]["mio"]["lock"]
    assert "cute pretty adult face" in ep["cast"]["mio"]["lock"]
    assert "tote" not in ep["cast"]["mio"]["lock"].lower()
    assert "B-cup" in ep["cast"]["nana"]["lock"] and "futanari" in ep["cast"]["nana"]["lock"]
    assert "brown bob" in ep["cast"]["nana"]["lock"]
    assert "24cm" in ep["cast"]["nana"]["lock"] and "thick human girth" in ep["cast"]["nana"]["lock"]
    assert "C-cup" in ep["cast"]["aoki"]["lock"] and "slim" in ep["cast"]["aoki"]["lock"]
    assert "long brown permed hair" in ep["cast"]["aoki"]["lock"]
    assert "24cm" in ep["cast"]["aoki"]["lock"] and "corona" in ep["cast"]["aoki"]["lock"]
    assert "D-cup" in ep["cast"]["kuroki"]["lock"] and "slim" in ep["cast"]["kuroki"]["lock"]
    assert "ponytail" in ep["cast"]["kuroki"]["lock"]
    assert "24cm" in ep["cast"]["kuroki"]["lock"]
    assert "glasses" not in ep["cast"]["kuroki"]["lock"].lower()
    assert "frenulum" in ep["cast"]["nana"]["lock"]
    assert "veins along the shaft" in ep["cast"]["aoki"]["lock"]
    assert "unhurried" not in ep["cast"]["kuroki"]["lock"]
    raw_txt = (KASUMI_ADULT_DIR / "episode.json").read_text(encoding="utf-8")
    assert "20cm" not in raw_txt
    assert "glasses" not in raw_txt.lower()
    assert "E-cup" not in raw_txt
    assert ep["cast"]["mio"]["name_ja"] == "白石 みお"
    for c in ep["cast"].values():
        lock = str(c["lock"]).lower()
        assert c["age"] >= 21
        assert "16y" not in lock and "girl" not in lock
        assert "woman" in lock and "adult" in lock


def test_kasumi_adult_combat_off_is_sex_route_not_fights():
    raw = load_episode(KASUMI_ADULT_DIR / "episode.json")
    assert validate_episode(raw, root=KASUMI_ADULT_DIR) == []
    _kasumi_adult_cast(raw)
    assert raw["render"]["combat"] == "off"
    assert "mystic" in LORA_FILES
    assert "blowjob" in LORA_FILES
    assert LORA_FILES["blowjob"] == "MM-H3_Blowjob_v3.safetensors"
    assert "civitai.com" in LORA_URLS["blowjob"]
    assert LORA_STRENGTHS["blowjob"] == 0.8
    assert LORA_FILES["futatf"].endswith("V5.1.safetensors")
    assert "3212000" in LORA_URLS["futatf"]
    assert LORA_FILES["mast"].startswith("H3_masturbate")
    assert LORA_FILES["cumshot"].startswith("epic_cumshots")
    assert LORA_STRENGTHS["kiss"] == 0.5
    assert "3208556" in LORA_URLS["kiss"]
    assert LORA_FILES["sideride"] == "cowgirl-side-2-mh3-e50-az420.safetensors"
    assert "3327446" in LORA_URLS["sideride"]
    assert LORA_STRENGTHS["sideride"] == 0.8
    assert LORA_FILES["thrust"] == "H3_FinalThrust.safetensors"
    assert "3269564" in LORA_URLS["thrust"]
    assert LORA_STRENGTHS["thrust"] == 0.55
    assert LORA_FILES["penis"].startswith("PLORA_H3")
    assert LORA_STRENGTHS["penis"] == 0.45
    assert LORA_FILES["synth"].startswith("SynthPussy")
    assert LORA_STRENGTHS["synth"] == 0.4
    assert LORA_FILES["cumouf"].startswith("CUMOUF")
    assert "3223411" in LORA_URLS["cumouf"]
    assert LORA_STRENGTHS["cumouf"] == 0.5
    assert SIDERIDE_TRIGGER == "side view riding sex, straddling the hips, facing the partner"
    assert "cowgirl" not in SIDERIDE_TRIGGER.lower()
    ep = apply_combat_route(raw, combat="off")
    assert [b["id"] for b in ep["beats"]] == [
        "01-cover",
        "02-ui-nana",
        "03-kiss",
        "04-aisle",
        "05-ui-guard",
        "06-doggy",
        "07-creampie",
        "08-walk",
        "09-ui-boss",
        "10-kiss",
        "11-missionary",
        "12-hold",
    ]
    assert expected_duration(ep) == pytest.approx(55.2, abs=1.0)
    assert not any(b.get("extra_loras") == ["combat"] for b in ep["beats"])
    assert all("combat_on" not in b for b in ep["beats"])
    assert ep["beats"][1]["menu"]["selected"] == 2
    assert ep["beats"][4]["menu"]["selected"] == 2
    assert ep["beats"][8]["menu"]["selected"] == 2
    assert ep["cards"]["fail"]["reason"] == "正常位で動けない"
    doggy = next(b for b in ep["beats"] if b["id"] == "06-doggy")
    doggy_prompt = build_beat_prompt(ep, doggy, trigger=merge_trigger("", doggy))
    assert "prfight2" not in doggy_prompt
    _assert_no_pose_names(doggy["action"], doggy_prompt)
    _assert_insertion_direction(doggy["action"], doggy_prompt)
    assert "tote" not in doggy_prompt.lower()
    assert "full bodies" in doggy_prompt.lower()
    assert "including feet" in doggy_prompt.lower()
    assert "aoki's face stays readable" in doggy_prompt.lower()
    assert "turned down" not in doggy_prompt.lower()
    _assert_sex_beat_both_pleasure_no_extra_kiss(doggy, doggy_prompt)
    assert doggy["hud"]["hint"] == "□ 口説く"
    assert "sit-down" not in str(doggy.get("music") or "").lower()
    cream = next(b for b in ep["beats"] if b["id"] == "07-creampie")
    cream_prompt = build_beat_prompt(ep, cream)
    assert "prfight2" not in cream_prompt
    _assert_no_pose_names(cream["action"], cream_prompt)
    _assert_insertion_direction(cream["action"], cream_prompt)
    assert "tote" not in cream_prompt.lower()
    assert "full bodies" in cream_prompt.lower()
    assert "aoki's face stays readable" in cream_prompt.lower()
    assert "finishes inside" in cream_prompt.lower() or "white goo" in cream_prompt.lower()
    assert "orgasm faces" in cream_prompt.lower()
    assert "french kiss" in cream_prompt.lower()
    assert "drips" in cream_prompt.lower()
    assert cream["trim"]["seconds"] == 7.5
    assert "after aoki sits" not in str(cream.get("place") or "").lower()
    jupo = next(b for b in ep["beats"] if b["id"] == "03-kiss")
    jupo_prompt = build_beat_prompt(ep, jupo, trigger=merge_trigger("", jupo))
    assert "jupo-jupo" in jupo_prompt.lower()
    assert "french kiss" in jupo_prompt.lower()
    assert extra_keys(jupo) == ["blowjob", "mystic"]
    assert extra_lora_entries(jupo) == [("blowjob", 0.8), ("mystic", 1.0)]
    assert jupo.get("trigger") == "bl0w_j0b"
    assert jupo_prompt.startswith("bl0w_j0b")
    assert "keep the lips at the base" in jupo_prompt.lower() or "climaxes in" in jupo_prompt.lower()
    assert "saliva" in jupo_prompt.lower()
    assert "semen share" in jupo_prompt.lower()
    assert jupo["trim"]["seconds"] == 10.0
    assert jupo["trim"]["start"] == 0
    assert "stays seated" in jupo["action"].lower()
    assert "fades out of frame" in jupo["action"].lower()
    assert "does not stand" in jupo["action"].lower()
    aisle = next(b for b in ep["beats"] if b["id"] == "04-aisle")
    aisle_prompt = build_beat_prompt(ep, aisle)
    assert "nana is not in frame" in aisle_prompt.lower() or "nana is gone" in aisle_prompt.lower()
    assert "fades completely out of frame" in cream_prompt.lower()
    assert "aoki gone" in cream_prompt.lower() or "aoki is gone" in cream["action"].lower() or "aoki gone" in cream["action"].lower()
    sex = next(b for b in ep["beats"] if b["id"] == "11-missionary")
    sex_prompt = build_beat_prompt(ep, sex)
    _assert_sex_beat_both_pleasure_no_extra_kiss(sex, sex_prompt)
    _assert_no_pose_names(sex["action"], sex_prompt)
    _assert_insertion_direction(sex["action"], sex_prompt)
    assert "pelvis stays down" in sex["action"].lower()
    assert "rock up" not in sex["action"].lower()
    assert "kuroki's hips moving" in sex["action"].lower()
    assert ", hips moving" not in sex["action"].lower()
    assert "finishes inside" in sex_prompt.lower()
    assert "stays on her back the whole take" in sex_prompt.lower()
    assert "sits up" not in sex_prompt.lower() and "sits down" not in sex_prompt.lower()
    assert "penis shaft" in sex_prompt.lower()
    assert "not an arm" in sex_prompt.lower()
    assert "do not walk" in sex_prompt.lower()
    assert "does not raise her torso" in sex_prompt.lower()
    ten = next(b for b in ep["beats"] if b["id"] == "10-kiss")
    ten_prompt = build_beat_prompt(ep, ten)
    assert "french kiss" in ten_prompt.lower()
    assert "stays outside" not in ten_prompt.lower()
    _assert_no_pose_names(ten["action"], ten_prompt)
    _assert_insertion_direction(ten["action"], ten_prompt)
    assert "starts inside" in ten_prompt.lower() or "going into" in ten_prompt.lower()
    assert ten["hud"]["hint"] == "□ 口説く"
    hold = next(b for b in ep["beats"] if b["id"] == "12-hold")
    hold_prompt = build_beat_prompt(ep, hold)
    assert "french kiss" in hold_prompt.lower()
    assert "stays on her back the whole take" in hold_prompt.lower()
    assert hold["voices"][1]["line"] == "ちゅっ"
    assert "penis shaft" in hold_prompt.lower()
    assert "do not walk" in hold_prompt.lower()
    _assert_no_pose_names(hold["action"], hold_prompt)
    _assert_insertion_direction(hold["action"], hold_prompt)
    for _b, prompt, errs in beat_prompts(ep, trigger=""):
        assert errs == []
        assert "prfight2" not in prompt
        low = prompt.lower()
        assert "slow motion" not in low and "slow-mo" not in low
        assert "brisk" in low or "snappy" in low
        _assert_no_pose_names(prompt)


def test_kasumi_adult_profile_camera_starts_landscape():
    raw = load_episode(KASUMI_ADULT_DIR / "episode.json")
    assert raw["canvas"] == "16:9"
    assert "shallow depth of field" not in raw["style"].lower()
    assert "left to right" in raw["world"]["lock"].lower()
    cover = next(b for b in raw["beats"] if b["id"] == "01-cover")
    assert "profile" in cover["camera"].lower()
    assert "walks right" in cover["action"].lower()
    assert "standing in the aisle" not in cover["camera"].lower()
    for combat in ("off", "on"):
        ep = apply_combat_route(raw, combat=combat)
        for beat in ep["beats"]:
            if beat_source(beat) == "ui":
                continue
            cam = str(beat.get("camera") or "").lower()
            act = str(beat.get("action") or "").lower()
            place = str(beat.get("place") or "").lower()
            assert "profile" in cam, beat["id"]
            assert "left to right" in cam, beat["id"]
            assert "facing away" not in cam
            assert "standing ahead" not in cam
            assert "down the aisle" not in act and "down the aisle" not in cam
            assert "toward a window wall" not in place
            assert "deep background" not in place
            prompt = build_beat_prompt(ep, beat)
            assert "horizontal 16:9" in prompt.lower(), beat["id"]
            assert "profile" in prompt.lower(), beat["id"]
            assert validate_beat_prompt(prompt, source="t2v") == []


def test_kasumi_adult_combat_on_is_fight_route_not_doggy():
    raw = load_episode(KASUMI_ADULT_DIR / "episode.json")
    ep = apply_combat_route(raw, combat="on")
    prepared = prepare_episode(raw, combat_override="on")
    assert [b["id"] for b in prepared["beats"]] == [b["id"] for b in ep["beats"]]
    assert [b["id"] for b in ep["beats"]] == [
        "01-cover",
        "02-ui-nana",
        "03-kiss",
        "04-aisle",
        "05-ui-guard",
        "06-fight",
        "07-oral",
        "08-peek",
        "09-ui-boss",
        "10-lose",
        "11-missionary",
        "12-hold",
    ]
    fights = [b for b in ep["beats"] if b.get("extra_loras") == ["combat"]]
    assert expected_duration(ep) == pytest.approx(47.7, abs=1.0)
    assert [b["id"] for b in fights] == ["06-fight", "10-lose"]
    assert all(b.get("physics") and b.get("trigger") == "prfight2, prfin1" for b in fights)
    assert all(b.get("steps") == COMBAT_STEPS and b.get("sampler") == COMBAT_SAMPLER and b.get("scheduler") == COMBAT_SCHEDULER for b in fights)
    assert ep["beats"][4]["menu"]["selected"] == 0
    assert ep["beats"][8]["menu"]["selected"] == 0
    assert fights[0]["hud"]["hint"] == "△ 戦い"
    assert next(b for b in ep["beats"] if b["id"] == "10-lose")["hud"]["hint"] == "△ 戦い"
    fight_prompt = build_beat_prompt(ep, fights[0], trigger=merge_trigger("", fights[0]))
    assert fight_prompt.startswith("prfight2, prfin1")
    assert "doggy" not in fight_prompt.lower()
    assert "side-on" in fight_prompt
    oral = next(b for b in ep["beats"] if b["id"] == "07-oral")
    oral_prompt = build_beat_prompt(ep, oral, trigger=merge_trigger("", oral))
    assert "prfight2" not in oral_prompt
    assert "jupo-jupo" in oral_prompt.lower()
    assert extra_keys(oral) == ["blowjob", "mystic"]
    assert oral.get("trigger") == "bl0w_j0b"
    assert oral_prompt.startswith("bl0w_j0b")
    assert "keep the lips at the base" in oral_prompt.lower()
    _assert_sex_beat_both_pleasure_no_extra_kiss(oral, oral_prompt)
    kiss = next(b for b in ep["beats"] if b["id"] == "03-kiss")
    kiss_prompt = build_beat_prompt(ep, kiss, trigger=merge_trigger("", kiss))
    assert "jupo-jupo" not in kiss_prompt.lower()
    assert "french kiss" in kiss_prompt.lower()
    assert extra_keys(kiss) == []
    assert not kiss.get("trigger")
    assert "bl0w_j0b" not in kiss_prompt.lower()
    assert kiss["trim"]["seconds"] == 5.0
    assert "stays seated" in kiss["action"].lower()
    assert "fades out of frame" in kiss["action"].lower()
    oral = next(b for b in ep["beats"] if b["id"] == "07-oral")
    assert oral["trim"]["seconds"] == 5.0
    assert "after aoki sits" in str(oral.get("place") or "").lower()
    assert "semen share" not in oral_prompt.lower()
    sex = next(b for b in ep["beats"] if b["id"] == "11-missionary")
    sex_prompt = build_beat_prompt(ep, sex)
    _assert_sex_beat_both_pleasure_no_extra_kiss(sex, sex_prompt)
    _assert_no_pose_names(sex["action"], sex_prompt)
    _assert_insertion_direction(sex["action"], sex_prompt)
    assert "pelvis stays down" in sex["action"].lower()
    assert "rock up" not in sex["action"].lower()
    assert "kuroki's hips moving" in sex["action"].lower()
    assert ", hips moving" not in sex["action"].lower()
    assert "finishes inside" not in sex_prompt.lower()
    assert "stays on her back the whole take" in sex_prompt.lower()
    hold = next(b for b in ep["beats"] if b["id"] == "12-hold")
    hold_prompt = build_beat_prompt(ep, hold)
    assert "french kiss" not in hold_prompt.lower()
    assert "stays on her back the whole take" in hold_prompt.lower()
    assert "penis shaft" in sex_prompt.lower()
    assert "not an arm" in sex_prompt.lower()
    _assert_no_pose_names(hold["action"], hold_prompt)
    _assert_insertion_direction(hold["action"], hold_prompt)
    for beat in ep["beats"]:
        still = beat.get("still")
        if still:
            path = KASUMI_ADULT_DIR / still
            assert path.is_file()
            assert Image.open(path).size == (1280, 720)
    for _b, prompt, errs in beat_prompts(ep, trigger=""):
        assert errs == []
        if "prfight2" in prompt:
            assert prompt.startswith("prfight2, prfin1")
        low = prompt.lower()
        assert "slow motion" not in low and "slow-mo" not in low
        assert "brisk" in low or "snappy" in low
        _assert_no_pose_names(prompt)


def _assert_hospital_bans(ep):
    for beat, prompt, errs in beat_prompts(ep, trigger=""):
        assert errs == []
        low = prompt.lower()
        assert "corpse" not in low and "zombie" not in low
        assert "slow motion" not in low and "slow-mo" not in low
        assert "brisk" in low or "snappy" in low
        _assert_no_pose_names(beat.get("action") or "", prompt)
        assert beat["hud"]["health"] == 0.9
        assert beat["hud"]["money"] == "¥0"


def _assert_insertion_direction(action: str, prompt: str) -> None:
    blob = f"{action}\n{prompt}".lower()
    assert "travels into" in blob or "travels in" in blob
    riding = (
        "sits on" in blob
        or "squats over" in blob
        or ("rock down" in blob and "hold still" in blob)
    )
    tentacle = "tentacle" in blob
    supine = ("stays on her back" in blob or "on her back" in blob) and not riding
    if tentacle:
        assert "thrust" in blob
        _assert_named_hip_motion(action, prompt)
        return
    if riding:
        assert "rock down" in blob or "lower onto" in blob or "lowers her hips" in blob or "squats over" in blob
        assert "hold still" in blob
        assert "rock up" not in blob
        _assert_named_hip_motion(action, prompt)
        return
    if supine:
        assert "thrust" in blob
        assert "rock up" not in blob
        assert "pelvis stays down" in blob or "pelvis stay" in blob
        _assert_named_hip_motion(action, prompt)
        return
    assert "thrust" in blob
    _assert_named_hip_motion(action, prompt)


def _assert_named_hip_motion(action: str, prompt: str) -> None:
    blob = f"{action}\n{prompt}"
    if "hips moving" not in blob.lower():
        return
    assert ", hips moving" not in blob.lower(), blob[:240]
    assert re.search(
        r"(Mio|Aoki|Kuroki|Aya|Miki|Rei|Kana|Shino|Gin|Tsuno)'s hips moving",
        blob,
    ), blob[:240]


def _assert_no_pose_names(*texts: str) -> None:
    blob = "\n".join(texts).lower()
    for tok in ("doggy", "missionary", "cowgirl"):
        assert tok not in blob, tok


def test_hospital_exit_adult_accept_is_survival_complete():
    raw = load_episode(HOSPITAL_DIR / "episode.json")
    assert validate_episode(raw, root=HOSPITAL_DIR) == []

    def _voice_lines(node, acc):
        if isinstance(node, dict):
            for voice in node.get("voices") or []:
                if isinstance(voice, dict):
                    acc.append(str(voice.get("line") or ""))
            for value in node.values():
                _voice_lines(value, acc)
        elif isinstance(node, list):
            for value in node:
                _voice_lines(value, acc)

    spoken = []
    _voice_lines(raw["beats"], spoken)
    assert not any("ちゅ" in line for line in spoken)
    assert raw["slug"] == "hospital-exit-adult"
    assert episode_lane(raw) == "erotic"
    assert episode_checkpoint(raw) == "eros-max"
    assert raw["render"]["combat"] == "off"
    assert raw["render"]["story"] == "accept"
    assert raw["cards"]["fail"]["reason"] == "淫欲に呑まれた"
    assert all(c["age"] >= 21 for c in raw["cast"].values())
    assert raw["cast"]["aya"]["age"] == 21 and "A-cup" in raw["cast"]["aya"]["lock"]
    assert "no penis" in raw["cast"]["aya"]["lock"] and "never futanari" in raw["cast"]["aya"]["lock"]
    assert "hospital dirt" in raw["cast"]["aya"]["lock"] and "sweat" in raw["cast"]["aya"]["lock"]
    assert "visible sweat beads" in raw["cast"]["aya"]["lock"]
    assert "grimy brown hospital dirt" in raw["cast"]["aya"]["lock"]
    assert "extremely tall" not in raw["world"]["lock"]
    assert "nobody is giant" in raw["world"]["lock"]
    assert "22cm" in raw["cast"]["miki"]["lock"] and "clear futanari" in raw["cast"]["miki"]["lock"]
    assert "no penis" not in raw["cast"]["miki"]["lock"]
    assert "purple" in raw["cast"]["miki"]["lock"]
    assert "lacerations" in raw["cast"]["miki"]["lock"] and "hollow empty dark eye sockets" in raw["cast"]["miki"]["lock"]
    assert "same vivid purple" in raw["cast"]["miki"]["lock"]
    assert "not pale-tan flesh" in raw["cast"]["miki"]["lock"]
    assert "pale-tan skin" not in raw["cast"]["miki"]["lock"]
    assert "groin" in raw["cast"]["miki"]["lock"] and "rotting" in raw["cast"]["miki"]["lock"]
    assert "22cm shaft" in raw["cast"]["miki"]["lock"]
    assert "blood" not in raw["cast"]["miki"]["lock"].lower()
    assert "across the face, neck" in raw["cast"]["miki"]["lock"]
    assert "hands" in raw["cast"]["miki"]["lock"] and "feet" in raw["cast"]["miki"]["lock"]
    assert "visible sweat beads" in raw["cast"]["miki"]["lock"]
    assert "between the open gashes" in raw["cast"]["miki"]["lock"]
    assert "sticky grimy brown hospital dirt" in raw["cast"]["miki"]["lock"]
    assert "intact purple skin" in raw["cast"]["miki"]["lock"]
    assert "crumbling" in raw["world"]["lock"] and "pandemic" in raw["world"]["lock"]
    assert "no blood" not in raw["world"]["lock"].lower()
    assert "24cm" in raw["cast"]["rei"]["lock"] and "corona" in raw["cast"]["rei"]["lock"]
    assert "dark-brown filthy sludge" in raw["cast"]["rei"]["lock"]
    assert "WHITE filthy slime" not in raw["cast"]["rei"]["lock"]
    assert "LEFT half of the face" in raw["cast"]["rei"]["lock"]
    assert "obviously festering" in raw["cast"]["rei"]["lock"]
    assert "raw red flesh" in raw["cast"]["rei"]["lock"]
    assert "right half of the face and body stays vivid purple" in raw["cast"]["rei"]["lock"]
    peek = next(b for b in raw["beats"] if b["id"] == "04-peek")
    assert "raw red flesh" in peek["action"].lower()
    assert "left cheek" in peek["action"].lower()
    assert "left breast" in peek["action"].lower()
    assert "same vivid purple" in raw["cast"]["rei"]["lock"]
    assert "not pale-tan flesh" in raw["cast"]["rei"]["lock"]
    assert "pale-tan skin" not in raw["cast"]["rei"]["lock"]
    assert "rotting" in raw["cast"]["rei"]["lock"]
    assert "feces" not in raw["cast"]["rei"]["lock"].lower()
    assert "20cm" in raw["cast"]["kana"]["lock"] and "frenulum" in raw["cast"]["kana"]["lock"]
    assert "glasses" not in raw["cast"]["kana"]["lock"].lower()
    assert "purple" in raw["cast"]["kana"]["lock"]
    assert "fang" in raw["cast"]["kana"]["lock"].lower()
    assert "hollow empty dark eye sockets" in raw["cast"]["kana"]["lock"]
    assert "filthy slime" in raw["cast"]["kana"]["lock"]
    assert "same vivid purple" in raw["cast"]["kana"]["lock"]
    assert "not pale-tan flesh" in raw["cast"]["kana"]["lock"]
    assert "pale-tan skin" not in raw["cast"]["kana"]["lock"]
    assert "rotting" in raw["cast"]["kana"]["lock"]
    assert "semen-like" not in raw["cast"]["kana"]["lock"]
    assert "vivid red" not in raw["cast"]["kana"]["lock"]
    assert "24cm" not in raw["cast"]["kana"]["lock"]
    assert "gin" in raw["cast"] and "tsuno" in raw["cast"]
    assert "no penis" in raw["cast"]["gin"]["lock"]
    assert "gums" in raw["cast"]["gin"]["lock"] and "muscle fiber" in raw["cast"]["gin"]["lock"]
    assert "sunken hollow" in raw["cast"]["gin"]["lock"]
    assert "hunched" not in raw["cast"]["gin"]["lock"]
    assert "sticky grimy brown hospital dirt" in raw["cast"]["gin"]["lock"]
    assert "intact ashen skin" in raw["cast"]["gin"]["lock"]
    assert "red muscle fiber showing in the peeled patches" in raw["cast"]["gin"]["lock"]
    assert "24cm" in raw["cast"]["tsuno"]["lock"] and "ashen gray" in raw["cast"]["tsuno"]["lock"]
    assert "cracked" in raw["cast"]["tsuno"]["lock"] and "horned mask" in raw["cast"]["tsuno"]["lock"]
    assert "clawed demon" in raw["cast"]["tsuno"]["lock"] or "decaying clawed" in raw["cast"]["tsuno"]["lock"]
    assert "one large single eye" in raw["cast"]["tsuno"]["lock"]
    assert "not two eyes" in raw["cast"]["tsuno"]["lock"]
    assert "exactly four long fingers" in raw["cast"]["tsuno"]["lock"]
    assert "both eyes" not in raw["cast"]["tsuno"]["lock"].lower()
    assert raw["cast"]["shino"]["age"] == 29
    assert "30cm" in raw["cast"]["shino"]["lock"] and "elongated" in raw["cast"]["shino"]["lock"]
    assert "24cm" not in raw["cast"]["shino"]["lock"]
    assert "alluring" in raw["cast"]["shino"]["lock"] and "stoop" in raw["cast"]["shino"]["lock"]
    assert "reptile tongue" in raw["cast"]["shino"]["lock"]
    assert "pale gray-white" in raw["cast"]["shino"]["lock"]
    shino_lock = raw["cast"]["shino"]["lock"].lower()
    assert "front of the groin" in shino_lock
    assert "pointing forward and up" in shino_lock
    assert "buttocks stay bare" in shino_lock
    assert "not purple" in shino_lock
    assert "not pale-tan flesh" in raw["cast"]["shino"]["lock"]
    assert "pale-tan skin" not in raw["cast"]["shino"]["lock"]
    assert "rotting" in raw["cast"]["shino"]["lock"]
    assert "nightgown" not in raw["cast"]["shino"]["lock"]
    assert "nightgown" in raw["homage"]["never"]
    menu = ["△ 戦う", "○ 受け入れる", "□ 誘う", "× 回避"]
    ep = prepare_episode(raw, story_override="受け入れる")
    assert ep["render"]["combat"] == "off"
    assert not (ep.get("cards") or {}).get("fail")
    assert [b["id"] for b in ep["beats"]] == [
        "01-cover",
        "02-ui-miki",
        "03-kiss",
        "03-kiss-walk",
        "04-peek-spot",
        "04-peek",
        "05-ui-rei",
        "06-doggy",
        "06-doggy-peak",
        "06-doggy-walk",
        "07-kana-spot",
        "07-kana",
        "08-ui-kana",
        "09-join",
        "09-join-peak",
        "09-join-walk",
        "10-shino-spot",
        "10-shino",
        "11-ui-shino",
        "12-exit",
        "12-exit-peak",
        "12-exit-out",
    ]
    assert expected_duration(ep) == pytest.approx(124.1, abs=2.0)
    assert ep["beats"][-1]["hud"]["complete"] is True
    assert not any(b.get("extra_loras") == ["combat"] for b in ep["beats"])
    assert all("on_invite" not in b for b in ep["beats"])
    assert all("invite_pose_all_fours" not in b for b in ep["beats"])
    for bid in ("02-ui-miki", "05-ui-rei", "08-ui-kana", "11-ui-shino"):
        ui = next(b for b in ep["beats"] if b["id"] == bid)
        assert ui["menu"]["items"] == menu
        assert ui["menu"]["selected"] == 1
        assert ui["menu"]["title"] == "感染者"
    miki = next(b for b in ep["beats"] if b["id"] == "03-kiss")
    miki_prompt = build_beat_prompt(ep, miki, trigger=merge_trigger("", miki))
    miki_walk = next(b for b in ep["beats"] if b["id"] == "03-kiss-walk")
    assert miki_walk["cast"] == ["aya"]
    assert "miki is gone from frame one" in miki_walk["action"].lower()
    assert extra_keys(miki) == ["blowjob", "mystic"]
    assert miki.get("trigger") == "bl0w_j0b"
    assert miki_prompt.startswith("bl0w_j0b")
    assert "glans stays inside the mouth" in miki_prompt.lower()
    assert "22cm" in miki_prompt.lower()
    assert "licks upward" not in miki_prompt.lower()
    assert miki["trim"]["seconds"] == 10.0
    doggy = next(b for b in ep["beats"] if b["id"] == "06-doggy")
    doggy_prompt = build_beat_prompt(ep, doggy, trigger=merge_trigger("", doggy))
    assert "prfight2" not in doggy_prompt
    assert "rei's face stays readable" in doggy_prompt.lower()
    assert "same vivid purple" in doggy["action"].lower()
    assert "rotting" in doggy["action"].lower()
    assert "pale-tan skin" not in doggy_prompt.lower()
    _assert_insertion_direction(doggy["action"], doggy_prompt)
    assert "hold still joined at the base" in doggy["action"].lower()
    peak = next(b for b in ep["beats"] if b["id"] == "06-doggy-peak")
    peak_prompt = build_beat_prompt(ep, peak)
    assert "orgasm" in peak_prompt.lower()
    assert "french kiss" in peak["action"].lower() or "french kiss" in doggy["action"].lower()
    assert "drips" in peak["action"].lower()
    assert "pull back" in peak["action"].lower()
    assert peak["trim"]["seconds"] == 10.0
    walk = next(b for b in ep["beats"] if b["id"] == "06-doggy-walk")
    assert walk["cast"] == ["aya"]
    assert "walks right" in walk["action"].lower()
    assert "gone from frame one" in walk["action"].lower()
    kana_meet = next(b for b in ep["beats"] if b["id"] == "07-kana")
    assert kana_meet["cast"] == ["aya", "kana"]
    assert "shino is not in frame" in kana_meet["action"].lower()
    assert "stands up from all fours" not in kana_meet["action"].lower()
    assert "glasses" not in kana_meet["action"].lower()
    assert "purple skin" in kana_meet["action"].lower()
    assert "visible fangs" in kana_meet["action"].lower()
    assert "hollow empty dark eye sockets" in kana_meet["action"].lower()
    assert "filthy slime" in kana_meet["action"].lower()
    assert "semen-like" not in kana_meet["action"].lower()
    assert "stroking the erect 20cm" in kana_meet["action"].lower()
    assert "white goo" in kana_meet["action"].lower()
    assert "linoleum around her" in kana_meet["action"].lower()
    assert "stops in front of kana" in kana_meet["action"].lower()
    assert "stands still in one spot" in kana_meet["action"].lower()
    assert "erect penis up" in kana_meet["action"].lower()
    assert "feet stay planted" not in kana_meet["action"].lower()
    assert "only aya's feet walk" in kana_meet["action"].lower()
    assert "one short step" in kana_meet["action"].lower()
    assert "the wall" not in kana_meet["action"].lower()
    assert "rail" not in kana_meet["action"].lower()
    assert not re.search(r"\brei\b", kana_meet["action"], re.I)
    assert kana_meet.get("camera_pack") == "none"
    assert "adults move left or right" not in kana_meet["camera"].lower()
    kana_prompt = build_beat_prompt(ep, kana_meet)
    assert "adults move left or right" not in kana_prompt.lower()
    assert "this shot:" not in kana_prompt.lower()
    peek = next(b for b in ep["beats"] if b["id"] == "04-peek")
    assert "imposing waiting stance" in peek["action"].lower()
    assert "walks right behind" not in peek["action"].lower()
    assert "stands ahead" in peek["action"].lower()
    cover = next(b for b in ep["beats"] if b["id"] == "01-cover")
    assert "walks right with her" in cover["action"].lower()
    assert "stands in the corridor facing her" not in cover["action"].lower()
    assert beat_clip_seconds(ep, cover) == 4.0
    assert duration_ladder(ep, cover) == [4.0]
    assert "lacerations" in cover["action"].lower()
    assert "shambling" in cover["action"].lower()
    assert "sways" in cover["action"].lower()
    assert "chin over the breastbone" in cover["action"].lower()
    kana = next(b for b in ep["beats"] if b["id"] == "09-join")
    kana_prompt = build_beat_prompt(ep, kana)
    _assert_insertion_direction(kana["action"], kana_prompt)
    assert "pelvis stays down" in kana["action"].lower()
    assert "rock up" not in kana["action"].lower()
    assert "20cm" in kana["action"]
    assert "same vivid purple" in kana["action"].lower()
    assert "rotting" in kana["action"].lower()
    assert "pale-tan skin" not in kana_prompt.lower()
    assert "penis shaft" in kana_prompt.lower()
    assert "not an arm" in kana_prompt.lower()
    shino_meet = next(b for b in ep["beats"] if b["id"] == "10-shino")
    assert shino_meet["cast"] == ["aya", "shino"]
    assert "stoop" in shino_meet["action"].lower()
    assert "30cm" in shino_meet["action"].lower()
    assert "same pale gray-white" in shino_meet["action"].lower()
    assert "rotting" in shino_meet["action"].lower()
    assert "pale-tan skin" not in shino_meet["action"].lower()
    assert "alluring" in shino_meet["action"].lower()
    assert "reptile tongue" in shino_meet["action"].lower()
    assert "kana is gone" in shino_meet["action"].lower() or "kana is not in frame" in shino_meet["action"].lower()
    assert "eager excited expectation" in shino_meet["action"].lower()
    assert "shaft that size is new to her" in shino_meet["action"].lower()
    exit_beat = next(b for b in ep["beats"] if b["id"] == "12-exit")
    exit_prompt = build_beat_prompt(ep, exit_beat)
    _assert_sex_beat_both_pleasure_no_extra_kiss(exit_beat, exit_prompt)
    _assert_insertion_direction(exit_beat["action"], exit_prompt)
    assert "stays on her back the whole take" in exit_prompt.lower()
    assert "pelvis stays down" in exit_beat["action"].lower()
    assert "rock up" not in exit_beat["action"].lower()
    assert "looming" in exit_beat["action"].lower()
    assert "towers" in exit_beat["action"].lower()
    assert "looks small under shino" in exit_beat["action"].lower()
    assert "pull" in exit_beat["action"].lower()
    assert "30cm" in exit_prompt.lower()
    assert "licks forward" in exit_prompt.lower()
    assert exit_beat["voices"][1]["who"] == "shino"
    assert exit_beat["voices"][1]["line"] == "くっ"
    out = next(b for b in ep["beats"] if b["id"] == "12-exit-out")
    assert out["cast"] == ["aya"]
    assert "through the lit open doorway" in out["action"].lower()
    _assert_hospital_bans(ep)


def test_hospital_exit_adult_invite_fails_from_lust():
    raw = load_episode(HOSPITAL_DIR / "episode.json")
    ep = prepare_episode(raw, story_override="誘う")
    assert ep["render"]["combat"] == "off"
    assert ep["render"]["story"] == "invite"
    assert ep["render"]["invite_pose"] == "all_fours"
    assert expected_duration(ep) == pytest.approx(181.2, abs=2.0)
    assert ep["beats"][-1]["hud"]["complete"] is False
    assert ep["cards"]["fail"]["reason"] == "淫欲に呑まれた"
    for bid in ("02-ui-miki", "05-ui-rei", "08-ui-kana", "11-ui-shino"):
        ui = next(b for b in ep["beats"] if b["id"] == bid)
        assert ui["menu"]["selected"] == 2
        assert ui["hud"]["hint"] == "□ 誘う"
    doggy = next(b for b in ep["beats"] if b["id"] == "06-doggy")
    _assert_insertion_direction(doggy["action"], build_beat_prompt(ep, doggy))
    assert "drops herself" in doggy["action"].lower()
    assert "planted on the same linoleum marks" in doggy["action"].lower()
    assert "walks right" in action_blob(ep, "06-doggy")
    twelve_blob = action_blob(ep, "12-exit")
    assert "do not cross the threshold" in twelve_blob or "do not slide to the lit doorway" in twelve_blob
    assert "left the building" not in twelve_blob
    assert ep["beats"][-1]["id"] == "12-exit-kiss"
    assert "12-exit-walk" not in [b["id"] for b in ep["beats"]]
    seat = next(b for b in ep["beats"] if b["id"] == "12-exit")
    peak = next(b for b in ep["beats"] if b["id"] == "12-exit-peak")
    drop = next(b for b in ep["beats"] if b["id"] == "12-exit-drop")
    kiss = ep["beats"][-1]
    assert "tongue hangs out" in seat["action"].lower()
    assert "lost in pleasure" in seat["action"].lower()
    assert "whites show" in peak["action"].lower()
    assert "leaks around the base" in peak["action"].lower()
    assert "pull back" not in peak["action"].lower()
    assert "rolls onto her back" in drop["action"].lower()
    assert "inner thighs rest on the linoleum" in drop["action"].lower()
    assert "heels sit right beside the buttocks" in drop["action"].lower()
    assert "overflows from the pussy" in drop["action"].lower()
    assert extra_lora_entries(kiss) == [("kiss", 0.5)]
    assert "french kiss" in kiss["action"].lower()
    assert "tongue kiss" in kiss["action"].lower()
    assert "lick" in kiss["action"].lower() and "corners of the mouth" in kiss["action"].lower()
    assert "forked reptile tongue" in kiss["action"].lower()
    assert kiss.get("connect") == "t2v"
    assert kiss.get("loco") == "planted"
    _assert_hospital_bans(ep)


def test_hospital_exit_adult_evade_exits_alone():
    raw = load_episode(HOSPITAL_DIR / "episode.json")
    ep = prepare_episode(raw, story_override="回避")
    assert ep["render"]["combat"] == "off"
    assert expected_duration(ep) == pytest.approx(63.7, abs=1.0)
    assert ep["beats"][-1]["hud"]["complete"] is True
    assert not (ep.get("cards") or {}).get("fail")
    assert [b["id"] for b in ep["beats"]] == [
        "01-cover",
        "02-ui-miki",
        "03-kiss",
        "04-peek-spot",
        "04-peek",
        "05-ui-rei",
        "06-slip",
        "07-run",
        "08-ui-kana",
        "09-slip-spot",
        "09-slip",
        "10-shino",
        "11-door",
        "12-exit",
    ]
    for i in (1, 5, 8):
        assert ep["beats"][i]["menu"]["selected"] == 3
    kiss = next(b for b in ep["beats"] if b["id"] == "03-kiss")
    kiss_prompt = build_beat_prompt(ep, kiss, trigger=merge_trigger("", kiss))
    assert extra_keys(kiss) == []
    assert "jupo-jupo" not in kiss_prompt.lower()
    assert "licks" not in kiss_prompt.lower()
    assert kiss["trim"]["seconds"] == 5.0
    slip = next(b for b in ep["beats"] if b["id"] == "06-slip")
    assert "travels into" not in slip["action"].lower()
    assert extra_keys(slip) == []
    twelve = next(b for b in ep["beats"] if b["id"] == "12-exit")
    twelve_prompt = build_beat_prompt(ep, twelve)
    assert twelve["cast"] == ["aya"]
    assert "alone" in twelve_prompt.lower()
    _assert_hospital_bans(ep)


def test_hospital_exit_adult_fight_win_exits_after_knockdowns():
    raw = load_episode(HOSPITAL_DIR / "episode.json")
    ep = prepare_episode(raw, story_override="戦って勝つ")
    assert ep["render"]["combat"] == "on"
    assert expected_duration(ep) == pytest.approx(70.35, abs=1.0)
    assert ep["beats"][-1]["hud"]["complete"] is True
    assert not (ep.get("cards") or {}).get("fail")
    assert [b["id"] for b in ep["beats"]] == [
        "01-cover",
        "02-ui-miki",
        "03-kiss",
        "04-peek-spot",
        "04-peek",
        "05-ui-rei",
        "06-fight",
        "07-oral",
        "08-ui-kana",
        "09-pass-spot",
        "09-pass",
        "10-win-spot",
        "10-win",
        "11-pass",
        "12-exit",
    ]
    fights = [b for b in ep["beats"] if b.get("extra_loras") == ["combat"]]
    assert [b["id"] for b in fights] == ["06-fight", "10-win"]
    assert all(b.get("physics") and b.get("trigger") == "prfight2, prfin1" for b in fights)
    assert all(b.get("steps") == COMBAT_STEPS and b.get("sampler") == COMBAT_SAMPLER and b.get("scheduler") == COMBAT_SCHEDULER for b in fights)
    assert ep["beats"][1]["menu"]["selected"] == 3
    assert ep["beats"][5]["menu"]["selected"] == 0
    assert ep["beats"][8]["menu"]["selected"] == 3
    fight_prompt = build_beat_prompt(ep, fights[0], trigger=merge_trigger("", fights[0]))
    assert fight_prompt.startswith("prfight2, prfin1")
    assert "travels into" not in fight_prompt.lower()
    oral = next(b for b in ep["beats"] if b["id"] == "07-oral")
    oral_prompt = build_beat_prompt(ep, oral, trigger=merge_trigger("", oral))
    assert extra_keys(oral) == ["blowjob", "mystic", "penis", "synth", "cumouf"]
    assert oral.get("trigger", "").startswith("bl0w_j0b")
    assert "CUMOUF" in oral.get("trigger", "")
    assert "thrust" not in extra_keys(oral)
    assert oral_prompt.startswith("bl0w_j0b")
    assert "glans stays inside the mouth" in oral_prompt.lower()
    assert "short strokes to the base" in oral["action"].lower()
    assert "jupo" in str(oral.get("sfx") or "").lower()
    assert all("じゅ" not in str(v.get("line") or "") for v in oral.get("voices") or [])
    assert "keep the lips at the base" in oral_prompt.lower()
    assert "camera distance stays fixed" in oral_prompt.lower()
    assert "do not push the camera in" not in oral_prompt.lower()
    assert "zoom" not in oral_prompt.lower()
    assert "aya's face and the partner's face stay in frame" in oral_prompt.lower()
    assert "head moves forward" in oral["action"].lower()
    assert "semen share" not in oral_prompt.lower()
    assert oral["trim"]["seconds"] == 5.0
    assert oral["cast"] == ["aya", "rei"]
    assert oral.get("camera_pack") == "side2d"
    _assert_sex_beat_both_pleasure_no_extra_kiss(oral, oral_prompt)
    twelve = next(b for b in ep["beats"] if b["id"] == "12-exit")
    assert twelve["cast"] == ["aya"]
    _assert_hospital_bans(ep)
    for beat in ep["beats"]:
        still = beat.get("still")
        if still:
            path = HOSPITAL_DIR / still
            assert path.is_file()
            assert Image.open(path).size == (1280, 720)


def test_hospital_exit_adult_fight_lose_is_defeat_h():
    raw = load_episode(HOSPITAL_DIR / "episode.json")
    ep = prepare_episode(raw, story_override="敗北")
    assert ep["render"]["combat"] == "on"
    assert expected_duration(ep) == pytest.approx(72.8, abs=1.0)
    assert ep["beats"][-1]["hud"]["complete"] is False
    assert ep["cards"]["fail"]["reason"] == "感染者に倒された"
    assert [b["id"] for b in ep["beats"]] == [
        "01-cover",
        "02-ui-miki",
        "03-kiss",
        "04-peek-spot",
        "04-peek",
        "05-ui-rei",
        "06-fight",
        "07-oral",
        "08-ui-kana",
        "09-pass-spot",
        "09-pass",
        "10-lose-spot",
        "10-lose",
        "11-join",
        "12-exit",
    ]
    fights = [b for b in ep["beats"] if b.get("extra_loras") == ["combat"]]
    assert [b["id"] for b in fights] == ["06-fight", "10-lose"]
    ten = next(b for b in ep["beats"] if b["id"] == "10-lose")
    assert "travels into" not in ten["action"].lower()
    sex = next(b for b in ep["beats"] if b["id"] == "11-join")
    sex_prompt = build_beat_prompt(ep, sex)
    _assert_sex_beat_both_pleasure_no_extra_kiss(sex, sex_prompt)
    _assert_insertion_direction(sex["action"], sex_prompt)
    assert "pelvis stay" in sex["action"].lower()
    assert "rock up" not in sex["action"].lower()
    assert "looming" in sex["action"].lower()
    assert "towers" in sex["action"].lower()
    assert "looks small under shino" in sex["action"].lower()
    assert "wrap aya's small waist" in sex["action"].lower()
    assert "shino's hips moving" in sex["action"].lower()
    assert ", hips moving" not in sex["action"].lower()
    assert "finishes inside" in sex_prompt.lower()
    assert "stays on her back the whole take" in sex_prompt.lower()
    twelve = next(b for b in ep["beats"] if b["id"] == "12-exit")
    twelve_prompt = build_beat_prompt(ep, twelve)
    assert "do not leave" in twelve_prompt.lower() or "do not slide to it" in twelve_prompt.lower()
    assert "french kiss" not in twelve_prompt.lower()
    _assert_hospital_bans(ep)


def test_hospital_invite_pose_and_toilet_and_skip():
    raw = load_episode(HOSPITAL_DIR / "episode.json")
    ride = prepare_episode(raw, story_override="誘う", invite_pose_override="騎乗位")
    assert ride["render"]["invite_pose"] == "ride"
    six_blob = action_blob(ride, "06-doggy")
    assert "sits on" in six_blob
    six = next(b for b in ride["beats"] if b["id"] == "06-doggy")
    assert "glans stays inside the mouth" in six["action"].lower()
    ride_sit = next(b for b in ride["beats"] if b["id"] == "06-doggy-ride")
    _assert_insertion_direction(ride_sit["action"], build_beat_prompt(ride, ride_sit))
    assert extra_keys(six) == ["blowjob", "mystic"]
    assert six.get("trigger") == "bl0w_j0b"
    assert "points only a little above horizontal into the mouth" in six["action"].lower()
    assert "stays up into the mouth" not in six["action"].lower()
    m_open = prepare_episode(raw, story_override="誘う", invite_pose_override="M字")
    nine = next(b for b in m_open["beats"] if b["id"] == "09-join")
    assert "m-shape" in nine["action"].lower()
    assert nine["trim"]["seconds"] == 10.0
    toilet = prepare_episode(raw, story_override="受け入れる", toilet_override="触手")
    four = next(b for b in toilet["beats"] if b["id"] == "04-toilet")
    four_prompt = build_beat_prompt(toilet, four)
    assert "tentacle" in four["action"].lower()
    assert "travels into" in four["action"].lower()
    _assert_insertion_direction(four["action"], four_prompt)
    assert "anus" in four["action"].lower()
    assert "corpse" not in four_prompt.lower()
    assert four["trim"]["seconds"] == 10.0
    assert beat_clip_seconds(toilet, four) == 10.0
    assert "already seated" in four["action"].lower()
    assert "keep thrusting" in four["action"].lower()
    assert "first frame to the last frame" in four["action"].lower()
    assert "does not stand" not in four["action"].lower()
    pee = prepare_episode(raw, story_override="accept", toilet_override="pee")
    assert next(b for b in pee["beats"] if b["id"] == "04-toilet")["action"].lower().find("yellow water") >= 0
    skip_rei = prepare_episode(raw, story_override="accept", appear_override="miki,kana,shino")
    ids = [b["id"] for b in skip_rei["beats"]]
    assert "05-ui-rei" not in ids and "06-doggy" not in ids
    assert "02-ui-miki" in ids and "08-ui-kana" in ids and "11-ui-shino" in ids
    skip_shino = prepare_episode(raw, story_override="accept", appear_override="miki,rei,kana")
    assert skip_shino["beats"][-1]["id"] == "09-join-walk"
    assert skip_shino["beats"][-1]["hud"]["complete"] is True
    miki_ride = action_blob(ride, "03-kiss")
    assert "22cm" in miki_ride
    assert "drops down onto her knees" in miki_ride
    assert "glans stays inside the mouth" in miki_ride
    assert "form an m" in miki_ride
    assert "sits on" in miki_ride
    assert "hugs" not in miki_ride
    ride_miki = next(b for b in ride["beats"] if b["id"] == "03-kiss-ride")
    _assert_insertion_direction(ride_miki["action"], build_beat_prompt(ride, ride_miki))
    assert "steps out" not in four["action"].lower()
    assert "front view" in four["camera"].lower()
    assert "facing the camera" in four["action"].lower()
    _assert_hospital_bans(toilet)
    _assert_hospital_bans(ride)
    stand = prepare_episode(raw, story_override="誘う", invite_pose_override="壁立ちバック")
    assert stand["render"]["invite_pose"] == "stand"
    stand_in = next(b for b in stand["beats"] if b["id"] == "06-doggy")
    assert "palms on the wall" in stand_in["action"].lower()
    assert "hips press together" in stand_in["action"].lower() or "press flush" in stand_in["action"].lower()
    _assert_insertion_direction(stand_in["action"], build_beat_prompt(stand, stand_in))
    assert "pussy" in stand_in["action"].lower()
    for bid, who in (("03-kiss", "miki"), ("06-doggy", "rei"), ("09-join", "kana"), ("12-exit", "shino")):
        beat = next(b for b in stand["beats"] if b["id"] == bid)
        act = beat["action"].lower()
        assert "aya does not turn" in act, bid
        assert f"{who} leaves the gap between aya and the wall" in act, bid
        assert "circles behind aya" in act, bid
        assert f"{who}'s chest meets aya's back" in act, bid
        assert f"{who}'s feet stay on the linoleum" in act, bid
        assert "turns the same way" not in act, bid
        assert "turns her whole body" not in act, bid
    kiss_stand = next(b for b in stand["beats"] if b["id"] == "03-kiss")
    assert "in front of the t-junction" in kiss_stand["action"].lower()
    assert "mouths joined" in kiss_stand["action"].lower()
    assert "mouths joined" in kiss_stand["camera"].lower()
    fours = prepare_episode(raw, story_override="誘う", invite_pose_override="四つん這い股広げ")
    for bid in ("03-kiss", "06-doggy", "09-join", "12-exit"):
        act = next(b for b in fours["beats"] if b["id"] == bid)["action"].lower()
        assert "aya does not turn" in act, bid
        assert "circles behind aya" in act, bid
        assert "turns the same way" not in act, bid
    assert "after the wait" in next(b for b in fours["beats"] if b["id"] == "06-doggy")["action"].lower()
    assert "kana still stands" in next(b for b in fours["beats"] if b["id"] == "09-join")["action"].lower()
    nelson_inv = prepare_episode(raw, story_override="誘う", invite_pose_override="フルネルソンアナル")
    assert nelson_inv["render"]["invite_pose"] == "nelson"
    nel = next(b for b in nelson_inv["beats"] if b["id"] == "09-join")
    nel_low = nel["action"].lower()
    assert "woman facing the camera" in nel_low
    assert "kana's face stays behind aya's head" in nel_low
    assert "kana's torso stays behind aya's back" in nel_low
    assert "travels into the anus" in nel_low
    assert "pussy" not in nel_low
    assert "feet stay in the air" in nel_low
    assert "feet leave the linoleum" not in nel_low
    assert "both forearms go under" in nel_low
    assert " and lift" in nel_low
    assert "circles behind aya" in nel_low
    assert nel_low.find("circles behind") < nel_low.find("both forearms go under")
    assert "mouths joined" in nel_low
    assert "turns the same way" not in nel_low
    assert "palms plant on the wall" not in nel_low
    for bid, who in (("03-kiss", "miki"), ("06-doggy", "rei"), ("09-join", "kana"), ("12-exit", "shino")):
        act = next(b for b in nelson_inv["beats"] if b["id"] == bid)["action"].lower()
        assert "mouths joined" in act, bid
        assert f"{who} leaves the gap between aya and the wall" in act, bid
        assert act.find("circles behind") < act.find("both forearms go under"), bid
        assert "turns the same way" not in act, bid
    nel_kiss = next(b for b in nelson_inv["beats"] if b["id"] == "03-kiss")
    assert "in front of the t-junction" in nel_kiss["action"].lower()
    assert "in front of the t-junction" in nel_kiss["camera"].lower()
    tsuno_stand = prepare_episode(raw, tsuno_override="受け入れる立ちバック")
    for bid in ("04-tsuno-meet", "04-tsuno-in"):
        act = next(b for b in tsuno_stand["beats"] if b["id"] == bid)["action"].lower()
        assert "turns her whole body" not in act, bid
        assert "turns the same way" not in act, bid
    assert nel.get("loco") == "planted"
    assert nel.get("camera_pack") == "none"
    assert nel.get("connect") == "t2v"
    nel_prompt = build_beat_prompt(nelson_inv, nel)
    assert NELSON_PLANTED_CLAUSE in nel_prompt
    assert PLANTED_CLAUSE not in nel_prompt
    assert PLANTED_PACE_CLAUSE not in nel_prompt
    assert "feet do not travel" not in nel["action"].lower()
    assert "does not travel" not in nel_prompt.lower()
    assert "does not scroll" not in nel_prompt.lower()
    assert "feet do not take a step" not in nel_prompt.lower()
    assert "nobody walks" not in nel_prompt.lower()
    miki_nel = next(b for b in nelson_inv["beats"] if b["id"] == "03-kiss")
    assert "feet do not travel" not in miki_nel["action"].lower()
    assert "the pair stays on this same floor spot" in miki_nel["action"].lower()
    assert "adults move left or right" not in nel_prompt.lower()
    _assert_insertion_direction(nel["action"], nel_prompt)
    _assert_hospital_bans(stand)
    _assert_hospital_bans(nelson_inv)
    keys = ride["render"]["lora_prefetch"]
    for key in ("blowjob", "mystic", "futatf", "mast", "cumshot", "kiss", "sideride"):
        assert key in keys
    ride_sit = next(b for b in ride["beats"] if b["id"] == "03-kiss-ride")
    assert extra_lora_entries(ride_sit)[0][0] == "sideride"
    assert ride_sit.get("trigger") == SIDERIDE_TRIGGER
    assert "straddles the hips" in ride_sit["action"].lower()
    assert "facing the partner" in ride_sit["action"].lower()
    assert "torso leaned forward over the partner's chest" in ride_sit["action"].lower()
    assert "beside the partner's hips" in ride_sit["action"].lower()
    assert "three separate lowers" in ride_sit["action"].lower()
    assert "straight down" in ride_sit["action"].lower()
    assert "from above" not in ride_sit["action"].lower()
    assert "squats from above" not in ride_sit["action"].lower()
    assert "from directly above" not in ride_sit["camera"].lower()
    assert "before the shaft enters, miki lies on her back" in ride_sit["action"].lower()
    assert "the back of her head on the linoleum" in ride_sit["action"].lower()
    assert "shoulders on the linoleum" in ride_sit["action"].lower()
    assert "then the insertion scene begins" in ride_sit["action"].lower()
    assert "slides both feet right" in ride_sit["action"].lower()
    assert "raises her hips" in ride_sit["action"].lower()
    assert "aya on top" in ride_sit["action"].lower()
    assert "miki sits on aya" not in ride_sit["action"].lower()
    ride_prompt = build_beat_prompt(ride, ride_sit, trigger=merge_trigger("", ride_sit))
    assert "the adult with the shaft lies back first" in ride_prompt.lower()
    assert "both feet slide along the linoleum" in ride_prompt.lower()
    assert "keeps the back of the head on the linoleum" in ride_prompt.lower()
    assert "feet do not take a step" not in ride_prompt.lower()
    assert "feet do not travel" not in ride_prompt.lower()
    assert "profile side-on" in ride_prompt.lower()
    assert "camera distance stays fixed" in ride_prompt.lower()
    assert "hips lower in that side view" in ride_prompt.lower()
    assert "only two adults share this frame" in ride_prompt.lower()
    assert SIDERIDE_TRIGGER in ride_prompt
    assert "cowgirl" not in ride_prompt.lower()
    ride_peak = next(b for b in ride["beats"] if b["id"] == "03-kiss-peak")
    assert "miki stays on her back" in ride_peak["action"].lower()
    assert "the back of her head on the linoleum" in ride_peak["action"].lower()
    assert "short upward thrusts from the back" in ride_peak["action"].lower()
    assert "aya is already sitting on miki's hips" in ride_peak["action"].lower()
    assert "aya's hips rock down" in ride_peak["action"].lower()
    assert ride_peak.get("trigger", "").startswith(SIDERIDE_TRIGGER)
    assert "cums inside of her" in ride_peak.get("trigger", "").lower()
    assert "PENISLORA" in ride_peak.get("trigger", "")
    peak_keys = extra_keys(ride_peak)
    assert peak_keys[0] == "sideride"
    assert "thrust" in peak_keys and "penis" in peak_keys and "synth" in peak_keys
    assert "cumshot" not in peak_keys and "cumouf" not in peak_keys
    assert "leaks around the base" in ride_peak["action"].lower()
    assert "stays inside the pussy" in ride_peak["action"].lower()


def test_hospital_review_takes_camera_invite_split_and_clip_length():
    raw = load_episode(HOSPITAL_DIR / "episode.json")
    accept = prepare_episode(raw, story_override="受け入れる")
    invite = prepare_episode(raw, story_override="誘う", invite_pose_override="騎乗位")
    fours = prepare_episode(raw, story_override="誘う", invite_pose_override="四つん這い股広げ")
    toilet = prepare_episode(raw, story_override="受け入れる", toilet_override="pee")

    cover_a = next(b for b in accept["beats"] if b["id"] == "01-cover")
    cover_i = next(b for b in invite["beats"] if b["id"] == "01-cover")
    assert "visible sweat beads" in cover_a["action"].lower()
    assert "grimy brown hospital dirt" in cover_a["action"].lower()
    assert "sticky grimy brown hospital dirt clinging to her whole body" in cover_a["action"].lower()
    cover_prompt = build_beat_prompt(accept, cover_a)
    assert "top of the head to the tips of both feet" in cover_prompt.lower()
    assert "both heads and all four feet" in cover_prompt.lower()
    assert "camera distance stays fixed" in cover_prompt.lower()
    assert "the camera sits far back" in cover_prompt.lower()
    assert "open floor shows past the tips of both feet" in cover_prompt.lower()
    assert "half-step closer" not in cover_prompt.lower()
    assert "the adults stay the same size" in cover_prompt.lower()
    assert "tracks only left and right" not in cover_prompt.lower()
    assert "tight on" not in cover_prompt.lower()
    pee_beat = next(b for b in toilet["beats"] if b["id"] == "04-toilet")
    pee_prompt = build_beat_prompt(toilet, pee_beat)
    assert "top of the head to the tips of both feet" in pee_prompt.lower()
    assert "tight on" not in pee_prompt.lower()
    ride_beat = next(b for b in invite["beats"] if b["id"] == "03-kiss-ride")
    ride_wide = build_beat_prompt(invite, ride_beat)
    assert "both heads and all four feet" in ride_wide.lower()
    assert "22cm shaft stays inside the frame" in cover_prompt.lower()
    assert "hip-to-shoulder" not in cover_prompt.lower()
    assert "zoom" not in cover_prompt.lower()
    invite_prompt = build_beat_prompt(invite, cover_i)
    assert "camera distance stays fixed" in invite_prompt.lower()
    assert "the camera sits far back" in invite_prompt.lower()
    assert "open floor" in invite_prompt.lower()
    assert "through the kiss" in invite_prompt.lower()
    assert "half-step closer" not in invite_prompt.lower()
    assert "standing close" not in invite_prompt.lower()
    assert "tracks only left and right" not in invite_prompt.lower()
    assert "no track, no pan, no scroll" not in invite_prompt.lower()
    assert "zoom" not in invite_prompt.lower()
    assert "visible sweat beads" in cover_i["action"].lower()
    assert "walks right with her" in cover_a["action"].lower()
    assert "shambling" in cover_a["action"].lower()
    assert "sways" in cover_a["action"].lower()
    assert beat_clip_seconds(accept, cover_a) == 4.0
    assert duration_ladder(accept, cover_a) == [4.0]
    assert "lewd wet smiling ecstatic inviting face" in cover_i["action"].lower()
    assert "french kiss" in cover_i["action"].lower()
    assert "catches up" in cover_i["action"].lower()
    assert "walking right faster" in cover_i["action"].lower()
    assert "snaps her body" in cover_i["action"].lower()
    assert "press flush" in cover_i["action"].lower()
    assert "squash and change shape" in cover_i["action"].lower()
    assert "knead them from behind" in cover_i["action"].lower()
    assert "cup miki's breasts" in cover_i["action"].lower()
    assert "stands behind miki" in cover_i["action"].lower()
    assert "the walk until the hug is short" in cover_i["action"].lower()
    assert "the moment aya's body presses into miki's back, miki's feet stop" in cover_i["action"].lower()
    assert "comes into view at the right edge" in cover_i["action"].lower()
    assert "open linoleum stays between miki's feet and the wall" in cover_i["action"].lower()
    assert "right knee lifts" not in cover_i["action"].lower()
    assert "t-junction wall" in cover_i["action"].lower()
    assert "comes into view at the right edge" in cover_i["camera"].lower()
    assert "eerie smile" in cover_i["action"].lower()
    assert "hollow empty dark eye sockets" in cover_i["action"].lower()
    cover_cam = cover_i["camera"].lower()
    assert "aya's breasts pressed into miki's back" in cover_cam
    assert "kneading miki's breasts from behind" in cover_cam
    assert cover_cam.find("pressed into miki's back") < cover_cam.find("turn whole-body")
    assert "head and chest turn together" in cover_i["action"].lower()
    assert "chin over the breastbone" in cover_i["action"].lower()
    assert "90" not in cover_i["action"]
    assert "180" not in cover_i["action"]
    assert beat_clip_seconds(invite, cover_i) == 10.0
    assert duration_ladder(invite, cover_i) == [10.0, 8.0, 6.0]
    assert cover_i["trim"]["seconds"] == 10.0

    doggy = next(b for b in fours["beats"] if b["id"] == "06-doggy")
    assert "planted on the same linoleum marks" in doggy["action"].lower()
    assert "same linoleum spot" in doggy["action"].lower()
    assert "french kiss" not in doggy["action"].lower()
    m_open = prepare_episode(raw, story_override="誘う", invite_pose_override="M字")
    nine = next(b for b in m_open["beats"] if b["id"] == "09-join")
    assert "m-shape" in nine["action"].lower()
    assert "back of her head on the linoleum" in nine["action"].lower()
    assert "eyes narrowed" in nine["action"].lower()
    assert "french kiss" not in nine["action"].lower()
    kiss_i = next(b for b in m_open["beats"] if b["id"] == "03-kiss")
    assert "in front of the t-junction" in kiss_i["action"].lower()
    assert "mouths joined" in kiss_i["action"].lower()
    seven = next(b for b in m_open["beats"] if b["id"] == "07-kana")
    assert "stroking the erect 20cm" in seven["action"].lower()
    assert "white goo" in seven["action"].lower()
    assert "lewd wet smiling ecstatic inviting face" in seven["action"].lower()
    assert "french kiss" not in seven["action"].lower()
    assert "face moves forward" in seven["action"].lower()
    assert "short gap from the erect 20cm" in seven["action"].lower()
    assert "the wall" not in seven["action"].lower()
    exit_raw = next(b for b in raw["beats"] if b["id"] == "12-exit")
    assert "shino finishes inside" in exit_raw["on_invite"]["action"].lower()
    assert "shino finishes inside" in exit_raw["on_fight_lose"]["action"].lower()
    exit_l = next(b for b in prepare_episode(raw, story_override="戦って負ける")["beats"] if b["id"] == "12-exit")
    assert "shino finishes inside" in exit_l["action"].lower()
    assert seven["trim"]["seconds"] == 8.0
    facial = next(b for b in m_open["beats"] if b["id"] == "09-kana-facial")
    kissb = next(b for b in m_open["beats"] if b["id"] == "09-kana-kiss")
    assert extra_keys(facial) == ["cumshot"]
    assert facial.get("trigger") == "CUMSH0T"
    assert facial["trim"]["seconds"] == 10.0
    assert "slow" not in facial["action"].lower()
    assert "white goo" in facial["action"].lower()
    assert extra_lora_entries(kissb) == [("kiss", 0.5)]
    assert "french kiss" in kissb["action"].lower()
    assert "tongue kiss" in kissb["action"].lower()
    assert "tight mutual embrace" in kissb["action"].lower()
    assert "lick around the lips" in kissb["action"].lower()
    order = [b["id"] for b in m_open["beats"]]
    assert order.index("08-ui-kana") < order.index("09-kana-facial") < order.index("09-kana-kiss") < order.index("09-join")
    goo = "sticky white goo clinging to the upper body"
    aya_lock = raw["cast"]["aya"]["lock"].lower()
    aya_white = raw["cast"]["aya"]["looks"]["white_upper"].lower()
    assert goo not in aya_lock
    assert goo in aya_white
    assert aya_white.startswith(aya_lock)
    assert raw["look_triggers"] == [{"after": "09-kana-facial", "who": "aya", "look": "white_upper"}]
    assert goo not in m_open["cast"]["aya"]["lock"].lower()
    assert "upper body" in facial["action"].lower()
    assert "shoulders" in facial["action"].lower()
    assert "aya" not in (facial.get("cast_lock") or {})
    assert goo not in build_beat_prompt(m_open, facial).lower()
    assert goo not in build_beat_prompt(m_open, seven).lower()
    assert goo in build_beat_prompt(m_open, kissb).lower()
    assert "already on aya's face" not in kissb["action"].lower()
    ten_m = next(b for b in m_open["beats"] if b["id"] == "10-shino")
    assert goo in (ten_m.get("cast_lock") or {}).get("aya", "").lower()
    assert goo in build_beat_prompt(m_open, ten_m).lower()
    accept_late = next(b for b in accept["beats"] if b["id"] == "10-shino")
    assert "09-kana-facial" not in [b["id"] for b in accept["beats"]]
    assert goo not in build_beat_prompt(accept, accept_late).lower()
    assert "aya" not in (accept_late.get("cast_lock") or {})

    ten = next(b for b in invite["beats"] if b["id"] == "10-shino")
    ten_low = ten["action"].lower()
    assert "stops in front of her" in ten_low
    assert "mouth is at aya's mouth height" in ten_low
    assert "french kiss" in ten_low
    assert "eager excited expectation" in ten_low
    assert "front groin" in ten_low
    assert "points forward" in ten_low
    assert "buttocks stay bare" in ten_low
    assert "not purple" in ten_low
    assert "walks forward toward shino" not in ten_low
    assert beat_clip_seconds(invite, ten) == 6.0

    twelve = next(b for b in invite["beats"] if b["id"] == "12-exit")
    twelve_low = action_blob(invite, "12-exit")
    assert "drops down onto her knees" in twelve["action"].lower()
    assert "mouths joined" in twelve["action"].lower()
    assert "glans stays inside the mouth" in twelve["action"].lower()
    assert "sits on" in twelve_low
    assert "steps in" not in twelve_low
    assert "hugs" not in twelve_low
    assert extra_keys(twelve) == ["blowjob", "mystic"]
    assert twelve.get("trigger") == "bl0w_j0b"
    assert beat_clip_seconds(invite, twelve) == 10.0
    sit = next(b for b in invite["beats"] if b["id"] == "12-exit-ride")
    _assert_insertion_direction(sit["action"], build_beat_prompt(invite, sit))

    accept_six = next(b for b in accept["beats"] if b["id"] == "06-doggy")
    assert "planted on the same linoleum marks" in accept_six["action"].lower()
    assert "profile" in accept_six["camera"].lower()
    assert "facing right" in accept_six["camera"].lower() or "left to right" in accept_six["camera"].lower()
    twelve_a = next(b for b in accept["beats"] if b["id"] == "12-exit")
    assert "hold still joined at the base" in twelve_a["action"].lower()
    assert "profile" in twelve_a["camera"].lower()
    out = next(b for b in accept["beats"] if b["id"] == "12-exit-out")
    assert "walks right" in out["action"].lower()
    assert "through the lit open doorway" in out["action"].lower()

    stall = next(b for b in toilet["beats"] if b["id"] == "04-toilet")
    assert "front view" in stall["camera"].lower()
    assert "profile" not in stall["camera"].lower()
    assert "shoots forward" in stall["action"].lower()
    assert "hips hold still" in stall["action"].lower()
    assert "bowl stays still" in stall["action"].lower()
    assert "only the yellow stream moves" in stall["action"].lower()
    assert "breathing bob" not in stall["action"].lower()
    assert "steps out" not in stall["action"].lower()
    assert "stays seated" in stall["action"].lower()
    assert "already seated" in stall["action"].lower()
    assert "first frame to the last frame" in stall["action"].lower()
    assert "does not stand" not in stall["action"].lower()
    assert stall["trim"]["seconds"] == 10.0
    assert beat_clip_seconds(toilet, stall) == 10.0

    kana = next(b for b in accept["beats"] if b["id"] == "07-kana")
    assert "glasses" not in kana["action"].lower()
    assert "filthy slime" in kana["action"].lower()
    assert "semen-like" not in kana["action"].lower()
    assert "stroking the erect 20cm" in kana["action"].lower()
    assert "white goo" in kana["action"].lower()
    miki_p = build_beat_prompt(accept, cover_a)
    assert "lacerations" in miki_p.lower()
    assert "hollow empty dark eye sockets" in miki_p.lower()
    assert "same vivid purple" in miki_p.lower()
    assert "not pale-tan flesh" in miki_p.lower()
    assert "pale-tan skin" not in miki_p.lower()
    assert "rotting" in miki_p.lower()
    assert "blood" not in [h.lower() for h in forbidden_hits(miki_p)]
    _assert_hospital_bans(accept)
    _assert_hospital_bans(invite)


def test_hospital_toilet_and_routes_stay_consistent():
    raw = load_episode(HOSPITAL_DIR / "episode.json")
    assert not re.search(r"\bblood\b", json.dumps(raw), re.I)
    assert "glasses" not in json.dumps(raw).lower()
    for mode, must in (
        ("pee", ("yellow water", "keeps streaming", "already seated")),
        ("masturbate", ("rubbing", "keeps going", "already seated")),
        ("tentacle", ("tentacle", "travels into", "keep thrusting", "already seated", "m-shape", "only the tentacles move", "hips hold still")),
    ):
        ep = prepare_episode(raw, story_override="受け入れる", toilet_override=mode)
        four = next(b for b in ep["beats"] if b["id"] == "04-toilet")
        low = four["action"].lower()
        assert four["trim"]["start"] == 0 and four["trim"]["seconds"] == 10.0
        assert beat_clip_seconds(ep, four) == 10.0
        assert duration_ladder(ep, four) == [10.0, 8.0, 6.0]
        for n in must:
            assert n in low, (mode, n)
        assert "stays seated" in low and "first frame to the last frame" in low
        assert "rock down" not in low
        assert "does not stand" not in low
        assert not re.search(r"\bstands?\b", low)
        assert "steps out" not in low and "walk" not in low
        enter = next(b for b in ep["beats"] if b["id"] == "04-toilet-in")
        leave = next(b for b in ep["beats"] if b["id"] == "04-toilet-out")
        assert "sits down" in enter["action"].lower()
        assert "stands" in leave["action"].lower()
        assert "walks right" in leave["action"].lower()
        if mode != "tentacle":
            assert "tentacle" not in leave["action"].lower()
        if mode == "tentacle":
            fill = next(b for b in ep["beats"] if b["id"] == "04-toilet-fill")
            assert "pump extra-viscous dirty liquid" in fill["action"].lower()
            assert "m-shape" in fill["action"].lower()
            assert "only the tentacles move" in fill["action"].lower()
            assert "hips hold still" in fill["action"].lower()
            assert "exactly three" in low
            assert "under the toilet seat" in low
            assert "inside of the toilet bowl" in low
            assert "hole in the wall on the right" in low
            assert "lower than the mouth hole" in low
            assert "comes up out of the inside of the toilet bowl, from under the toilet seat, and travels into her anus" in low
            assert "rises to her open mouth" in low
            assert "travels into her hairless pussy" in low
            assert "presses on her tongue" in low
            assert "hold her thighs" not in low
            fill_low = fill["action"].lower()
            assert "exactly three" in fill_low
            assert "under the toilet seat" in fill_low
            assert "inside of the toilet bowl" in fill_low
            assert "hole in the wall on the right" in fill_low
            assert "lower than the mouth hole" in fill_low
            assert "rock down" not in fill["action"].lower()
            assert fill["trim"]["seconds"] == 10.0
            assert fill.get("camera_pack") == "none"
        assert "both look" not in low
        assert "stall door" not in str(four.get("sfx") or "").lower()
        assert "stall door" not in low
        assert beat_props(ep, four) == []
        assert four["cast"] == ["aya"]
        assert four.get("camera_pack") == "none"
        prompt = build_beat_prompt(ep, four, trigger=merge_trigger("", four))
        assert validate_beat_prompt(prompt, source="t2v") == []
        if mode == "masturbate":
            assert "m-shape" in low
            assert "facing the camera" in low
            assert "orgasmic contractions" in low
            assert extra_keys(four) == ["mast"]
            assert "profile" not in four["camera"].lower()
            assert "facing the camera" in enter["action"].lower()
        elif mode == "tentacle":
            assert "facing the camera" in low
            assert "presses on her tongue" in low
            assert "profile" not in four["camera"].lower()
            assert "facing the camera" in enter["action"].lower()
        else:
            assert "front view" in four["camera"].lower()
            assert "profile" not in four["camera"].lower()
            assert "facing the camera" in low
            assert "shoots forward" in low
            assert "toward the camera" in low
            assert "hips hold still" in low
            assert "western toilet bowl stays still" in low
            assert "only the yellow stream moves" in low
            assert "only the yellow stream moves" in prompt.lower()
            assert "only hips, hands, and mouths move" not in prompt.lower()
            assert "feet do not take a step" not in prompt.lower()
            assert "does not travel" not in prompt.lower()
            assert "breathing bob" not in low
            assert "hairless pussy" in low
            assert "smiles" in low
            assert "into the bowl" not in low
            assert "outside the seat" not in low
            assert "urethra" not in low
            assert "does not move" not in low
        assert "hospital door" not in prompt.lower()
        assert "doorway" not in prompt.lower()
        assert "this shot:" not in prompt.lower()
        assert "tight on this one toilet stall" in four["camera"].lower()
        assert validate_episode(ep, root=HOSPITAL_DIR) == []
        _assert_hospital_bans(ep)

    for story, pose in (("受け入れる", None), ("誘う", "騎乗位"), ("誘う", "四つん這い股広げ"), ("誘う", "M字"), ("回避", None)):
        kw = {"story_override": story}
        if pose:
            kw["invite_pose_override"] = pose
        ep = prepare_episode(raw, **kw)
        assert validate_episode(ep, root=HOSPITAL_DIR) == []
        assert len(ep["beats"]) <= MAX_BEATS
        blob = "\n".join(str(b.get("action") or "") for b in ep["beats"]).lower()
        assert "walks forward toward the lit" not in blob
        assert "corridor depth ahead" not in blob
        if story == "誘う":
            one = next(b for b in ep["beats"] if b["id"] == "01-cover")
            ten = next(b for b in ep["beats"] if b["id"] == "10-shino")
            assert "french kiss" in one["action"].lower()
            assert "stops in front of her" in ten["action"].lower()
            if pose and "騎乗" in pose:
                twelve = next(b for b in ep["beats"] if b["id"] == "12-exit")
                assert "drops down onto her knees" in twelve["action"].lower()
                assert "hugs" not in action_blob(ep, "12-exit")
            if pose and "四つん這い" in pose:
                six = next(b for b in ep["beats"] if b["id"] == "06-doggy")
                assert "planted on the same linoleum marks" in six["action"].lower()
        for beat, prompt, errs in beat_prompts(ep, trigger=""):
            assert errs == []
            assert "blood" not in [h.lower() for h in forbidden_hits(prompt)]
            for v in beat_vocals(beat):
                assert v["who"] in (ep.get("cast") or {})
                assert v["who"] in (beat.get("cast") or [])


def test_hospital_full_form_stays_under_beat_cap():
    """Tentacle + gin + tsuno + per-scene invite used to die at the 40-beat preflight."""
    raw = load_episode(HOSPITAL_DIR / "episode.json")
    chosen = prepare_episode(
        raw,
        story_override="誘う",
        invite_pose_override="フルネルソンアナル",
        toilet_override="触手",
        gin_override="犯される",
        tsuno_override="後ろアナル",
        connect_override="chain",
        scenes_override="miki=invite_m_open,rei=invite_nelson,kana=invite_ride,shino=invite_ride",
    )
    assert validate_episode(chosen, root=HOSPITAL_DIR) == []
    assert len(chosen["beats"]) == 42
    fullest = prepare_episode(
        raw,
        story_override="受け入れる",
        invite_pose_override="四つん這い",
        toilet_override="tentacle",
        gin_override="犯される",
        tsuno_override="受け入れる立ちバック",
        connect_override="chain",
        scenes_override="miki=invite_ride,rei=invite_ride,kana=invite_ride,shino=invite_ride",
    )
    assert validate_episode(fullest, root=HOSPITAL_DIR) == []
    assert len(fullest["beats"]) == 44
    assert len(fullest["beats"]) <= MAX_BEATS


def test_hospital_per_scene_accept_invite_evade_and_ending():
    raw = load_episode(HOSPITAL_DIR / "episode.json")
    mixed = prepare_episode(
        raw,
        story_override="受け入れる",
        scenes_override="miki=回避,rei=全体に従う,kana=□誘う・ベロチュー→じゅぼ→騎乗位,shino=○受け入れる",
    )
    assert mixed["render"]["story"] == "accept"
    assert mixed["render"]["scenes"]["miki"] == "evade"
    assert mixed["render"]["scenes"]["rei"] == "inherit"
    assert mixed["render"]["scenes"]["kana"] == "invite_ride"
    assert mixed["render"]["scenes"]["shino"] == "accept"
    kiss = next(b for b in mixed["beats"] if b["id"] == "03-kiss")
    kiss_prompt = build_beat_prompt(mixed, kiss, trigger=merge_trigger("", kiss))
    assert extra_keys(kiss) == []
    assert "jupo-jupo" not in kiss_prompt.lower()
    doggy = next(b for b in mixed["beats"] if b["id"] == "06-doggy")
    _assert_insertion_direction(doggy["action"], build_beat_prompt(mixed, doggy))
    kana_blob = action_blob(mixed, "09-join")
    assert "sits on" in kana_blob
    kana_sit = next(b for b in mixed["beats"] if b["id"] == "09-join-ride")
    assert "pushes kana backward" not in kana_sit["action"].lower()
    assert "already on her back" not in kana_sit["action"].lower()
    assert "still kneeling" in kana_sit["action"].lower()
    assert "lips at the base" in kana_sit["action"].lower()
    assert "lays kana down" in kana_sit["action"].lower()
    assert "before the shaft enters, kana lies on her back" in kana_sit["action"].lower()
    assert "the back of her head on the linoleum" in kana_sit["action"].lower()
    assert "slides both feet right" in kana_sit["action"].lower()
    assert "aya on top" in kana_sit["action"].lower()
    assert "kana sits on aya" not in kana_sit["action"].lower()
    assert "one shaft" in kana_sit["action"].lower()
    assert "three separate lowers" in kana_sit["action"].lower()
    _assert_insertion_direction(kana_sit["action"], build_beat_prompt(mixed, kana_sit))
    kana_jupo = next(b for b in mixed["beats"] if b["id"] == "09-join")
    assert extra_keys(kana_jupo) == ["blowjob", "mystic"]
    exit_beat = next(b for b in mixed["beats"] if b["id"] == "12-exit-out")
    assert exit_beat["hud"]["complete"] is True
    assert not (mixed.get("cards") or {}).get("fail")
    assert ending_story(mixed) == "accept"
    assert validate_episode(mixed, root=HOSPITAL_DIR) == []
    _assert_hospital_bans(mixed)

    last_invite = prepare_episode(
        raw,
        story_override="受け入れる",
        scenes_override="miki=accept,rei=accept,kana=accept,shino=□誘う・四つん這い股広げ",
    )
    twelve = next(b for b in last_invite["beats"] if b["id"] == "12-exit-kiss")
    assert "12-exit-walk" not in [b["id"] for b in last_invite["beats"]]
    twelve_prompt = build_beat_prompt(last_invite, twelve)
    assert twelve["hud"]["complete"] is False
    assert last_invite["cards"]["fail"]["reason"] == "淫欲に呑まれた"
    assert "do not cross the threshold" in twelve_prompt.lower() or "do not slide to the lit doorway" in twelve_prompt.lower()
    miki = next(b for b in last_invite["beats"] if b["id"] == "03-kiss")
    assert extra_keys(miki) == ["blowjob", "mystic"]
    assert ending_story(last_invite) == "invite"

    skip_last = prepare_episode(
        raw,
        story_override="受け入れる",
        appear_override="miki,rei,kana",
        scenes_override="kana=誘う",
    )
    finale = skip_last["beats"][-1]
    assert finale["id"] == "09-join-kiss"
    assert "09-join-walk" not in [b["id"] for b in skip_last["beats"]]
    assert finale["cast"] == ["aya", "kana"]
    assert finale["hud"]["complete"] is False
    assert skip_last["cards"]["fail"]["reason"] == "淫欲に呑まれた"
    assert ending_story(skip_last) == "invite"
    kiss_low = finale["action"].lower()
    assert "20cm" in kiss_low and "visible fangs" in kiss_low and "filthy slime" in kiss_low
    assert "shino" not in kiss_low and "30cm" not in kiss_low and "forked" not in kiss_low
    assert extra_lora_entries(finale) == [("kiss", 0.5)]

    last_evade = prepare_episode(
        raw,
        story_override="誘う",
        scenes_override="shino=回避",
    )
    assert last_evade["beats"][-1]["hud"]["complete"] is True
    assert not (last_evade.get("cards") or {}).get("fail")
    assert ending_story(last_evade) == "evade"
    twelve_e = next(b for b in last_evade["beats"] if b["id"] == "12-exit")
    assert twelve_e["cast"] == ["aya"]

    fight = prepare_episode(
        raw,
        story_override="戦って勝つ",
        scenes_override="miki=回避,rei=○受け入れる,kana=誘う,shino=回避",
    )
    assert [b["id"] for b in fight["beats"] if b.get("extra_loras") == ["combat"]] == ["06-fight", "10-win"]
    assert fight["beats"][-1]["hud"]["complete"] is True
    assert ending_story(fight) == "fight_win"
    assert validate_episode(fight, root=HOSPITAL_DIR) == []

    kasumi = prepare_episode(
        load_episode(KASUMI_ADULT_DIR / "episode.json"),
        scenes_override="miki=回避,shino=誘う",
    )
    assert [b["id"] for b in kasumi["beats"]] == [
        b["id"] for b in prepare_episode(load_episode(KASUMI_ADULT_DIR / "episode.json"))["beats"]
    ]

    with pytest.raises(EpisodeError, match="scenes"):
        prepare_episode(raw, scenes_override="miki=戦って勝つ")
    with pytest.raises(EpisodeError, match="scenes"):
        prepare_episode(raw, scenes_override="nobody=回避")
    parsed = parse_scenes("みき=回避,れい=□誘う・M字開脚仰向け")
    assert parsed["miki"] == ("evade", None)
    assert parsed["rei"] == ("invite", "m_open")
    assert parsed["kana"] == (None, None)


def test_hospital_invite_finale_follows_the_last_partner():
    raw = load_episode(HOSPITAL_DIR / "episode.json")
    full = prepare_episode(raw, story_override="誘う")
    assert full["beats"][-1]["id"] == "12-exit-kiss"
    assert "03-kiss-walk" in [b["id"] for b in full["beats"]]
    shino_kiss = full["beats"][-1]["action"].lower()
    assert "extremely tall" in shino_kiss and "30cm" in shino_kiss and "forked reptile tongue" in shino_kiss
    miki_peak = next(b for b in full["beats"] if b["id"] == "03-kiss-peak")
    assert "whites show" not in miki_peak["action"].lower()

    only = {"rei": False, "kana": False, "shino": False, "miki": True}
    miki = prepare_episode(raw, story_override="誘う", appear_override=only)
    assert miki["beats"][-1]["id"] == "03-kiss-kiss"
    assert miki["beats"][-1]["cast"] == ["aya", "miki"]
    low = miki["beats"][-1]["action"].lower()
    assert "22cm" in low and "short brown bob" in low and "lacerations" in low and "sweat beads" in low
    assert "shino" not in low and "30cm" not in low and "rei" not in low
    assert extra_lora_entries(miki["beats"][-1]) == [("kiss", 0.5)]
    assert "french kiss" in low and "corners of the mouth" in low
    seat = next(b for b in miki["beats"] if b["id"] == "03-kiss")
    peak = next(b for b in miki["beats"] if b["id"] == "03-kiss-peak")
    drop = next(b for b in miki["beats"] if b["id"] == "03-kiss-drop")
    assert "tongue hangs out" in seat["action"].lower()
    assert "whites show" in peak["action"].lower()
    assert "rolls onto her back" in drop["action"].lower()
    assert "overflows from the pussy" in drop["action"].lower()

    rei = prepare_episode(
        raw,
        story_override="誘う",
        invite_pose_override="フルネルソンアナル",
        appear_override={"miki": False, "rei": True, "kana": False, "shino": False},
    )
    assert rei["beats"][-1]["id"] == "06-doggy-kiss"
    rei_low = rei["beats"][-1]["action"].lower()
    assert "24cm" in rei_low and "dark-brown filthy sludge" in rei_low and "left breast" in rei_low
    assert "22cm" not in rei_low and "30cm" not in rei_low and "miki" not in rei_low
    rei_drop = next(b for b in rei["beats"] if b["id"] == "06-doggy-drop")
    assert "overflows from the anus" in rei_drop["action"].lower()
    assert "overflows from the pussy" not in rei_drop["action"].lower()

    gin = prepare_episode(
        raw,
        story_override="誘う",
        appear_override=only,
        gin_override="犯される",
    )
    assert gin["beats"][-1]["id"] == "04-gin-walk"
    assert "04-gin-kiss" not in [b["id"] for b in gin["beats"]]


def test_hospital_appear_none_and_option_matrix():
    raw = load_episode(HOSPITAL_DIR / "episode.json")
    with pytest.raises(EpisodeError, match="at least one encounter"):
        prepare_episode(raw, appear_override="none")
    with pytest.raises(EpisodeError, match="at least one encounter"):
        prepare_episode(raw, toilet_override="pee", appear_override="none")
    names = HOSPITAL_ENCOUNTERS
    appears = [{n: True for n in names}]
    for enc in names:
        appears.append({n: n != enc for n in names})
        appears.append({n: n == enc for n in names})
    from itertools import combinations

    for a, b in combinations(names, 2):
        appears.append({n: n not in (a, b) for n in names})
    for story in STORY_MODES:
        toilets = TOILET_MODES if story == "accept" else {"off": TOILET_MODES["off"]}
        poses = INVITE_POSE_MODES if story == "invite" else {"all_fours": INVITE_POSE_MODES["all_fours"]}
        for toilet in toilets:
            for pose in poses:
                for shown in appears:
                    ep = prepare_episode(
                        raw,
                        story_override=story,
                        toilet_override=toilet,
                        invite_pose_override=pose,
                        appear_override=shown,
                    )
                    assert ep["beats"], (story, toilet, pose, shown)
                    assert not is_ui_beat(ep["beats"][0]), (story, ep["beats"][0]["id"])
                    ids = [b["id"] for b in ep["beats"]]
                    assert ids == list(dict.fromkeys(ids)), (story, ids)
                    assert validate_episode(ep, root=HOSPITAL_DIR) == [], (story, toilet, pose, shown, ids)
                    for _b, prompt, errs in beat_prompts(ep, trigger=""):
                        assert errs == []
                        _assert_no_pose_names(prompt)
                    spec = STORY_MODES[story]
                    assert ep["beats"][-1]["hud"]["complete"] is bool(spec.get("complete"))
                    if spec.get("complete"):
                        assert not (ep.get("cards") or {}).get("fail")
                    else:
                        assert (ep.get("cards") or {}).get("fail")


def test_hospital_gin_tsuno_optional_events():
    raw = load_episode(HOSPITAL_DIR / "episode.json")
    off = prepare_episode(raw, story_override="受け入れる")
    assert all(not str(b["id"]).startswith("04-gin") and not str(b["id"]).startswith("04-tsuno") for b in off["beats"])
    taken = prepare_episode(raw, story_override="受け入れる", gin_override="犯される")
    ids = [b["id"] for b in taken["beats"]]
    assert ids.index("04-gin-lick-spot") == ids.index("04-peek") + 1
    assert ids.index("04-gin-lick") == ids.index("04-gin-lick-spot") + 1
    lick = next(b for b in taken["beats"] if b["id"] == "04-gin-lick")
    walk = next(b for b in taken["beats"] if b["id"] == "04-gin-walk")
    lick_prompt = build_beat_prompt(taken, lick)
    walk_prompt = build_beat_prompt(taken, walk)
    assert "licks once" in lick["action"].lower()
    assert "grows out of the open mouth" in lick["action"].lower()
    assert "penis growth" in lick["action"].lower()
    assert extra_keys(lick) == ["mystic", "futatf"]
    assert "clitoris grows" in lick["action"].lower()
    assert "24cm" in lick["action"]
    assert "behind aya toward the left" in lick["action"].lower()
    assert "falls onto her butt toward the right" in lick["action"].lower()
    assert "head lands on the right" in lick["action"].lower()
    assert "toes point left" in lick["action"].lower()
    assert "hesitant and afraid" in lick["action"].lower()
    assert "ceiling" not in lick["action"].lower()
    assert "wall" not in lick["action"].lower()
    assert "lands on her feet" not in lick["action"].lower()
    assert "in front of aya" not in lick["action"].lower()
    assert "crouches toward the left" in lick["action"].lower()
    assert "sits toward the right" in lick["action"].lower()
    assert "both knees open" in lick["action"].lower()
    assert "dark corridor continuing on" in lick["action"].lower()
    assert "falls onto her butt" in lick["action"].lower()
    assert "futanari" not in lick["action"].lower()
    assert "thighs open" in lick["action"].lower()
    assert "shocked wide-eyed" in lick["action"].lower()
    assert "french kiss" not in lick["action"].lower()
    assert lick.get("loco") == "planted"
    assert lick.get("cast_lock") and "24cm" in lick["cast_lock"]["aya"]
    assert "pale-tan" in lick["cast_lock"]["aya"]
    assert "ashen" not in lick["cast_lock"]["aya"].lower()
    assert "pale-tan human shaft" in action_blob(taken, "04-gin")
    assert "the shaft stays ashen gray" not in action_blob(taken, "04-gin")
    assert "24cm" in lick_prompt
    assert walk["cast"] == ["aya"]
    assert "grown shaft is gone" in walk["action"].lower()
    assert "no penis" in walk["action"].lower()
    assert "gone from frame one" in walk["action"].lower()
    assert "t-junction" in walk["action"].lower()
    assert is_end_connect_beat(walk)
    assert beat_source(walk) == "t2v"
    assert "zombie" not in lick_prompt.lower() and "corpse" not in lick_prompt.lower()
    assert "drool" in action_blob(taken, "04-gin")
    jupo = next(b for b in taken["beats"] if b["id"] == "04-gin-jupo")
    assert extra_keys(jupo) == ["blowjob", "mystic"]
    assert "already sitting on her butt" in jupo["action"].lower()
    assert "waist bent" in jupo["action"].lower()
    assert "tongue pulls back into gin's mouth" in jupo["action"].lower()
    assert "lips seal" in jupo["action"].lower()
    assert "tongue stays inside the mouth" in jupo["action"].lower()
    assert "wide blissful smile" in jupo["action"].lower()
    ride_peak = next(b for b in taken["beats"] if b["id"] == "04-gin-peak")
    assert "aya stays on her back" in ride_peak["action"].lower()
    assert "the back of her head on the linoleum" in ride_peak["action"].lower()
    assert "short upward thrusts from the back" in ride_peak["action"].lower()
    assert "gin is already sitting on aya's hips" in ride_peak["action"].lower()
    assert "gin's hips rock down" in ride_peak["action"].lower()
    assert "leaks around the base" in ride_peak["action"].lower()
    assert "thrust" in extra_keys(ride_peak)
    assert "pussy hanging directly above the glans" in jupo["action"].lower()
    assert "standing vertically straight up from her groin" in jupo["action"].lower()
    assert "head on the right" in jupo["action"].lower()
    assert "toes pointing left" in jupo["action"].lower()
    assert "gin's head on the left" in jupo["action"].lower()
    ride_in = next(b for b in taken["beats"] if b["id"] == "04-gin-ride")
    ride_act = ride_in["action"].lower()
    assert "squats from above" in ride_act
    assert "from directly above" in ride_act
    assert "before the shaft enters, aya lies on her back" in ride_act
    assert "the back of her head on the linoleum" in ride_act
    assert "head on the right" in ride_act
    assert "feet pointing left" in ride_act
    assert "gin's head is on the left" in ride_act
    assert "gin sits on aya's hips" in ride_act
    assert "travels into gin's pussy" in ride_act
    assert "straight down" in ride_act
    assert "slides both feet" not in ride_act
    assert "both feet stay in frame" in jupo["action"].lower()
    assert "one clawed hand holds the shaft" in jupo["action"].lower()
    jupo_prompt = build_beat_prompt(taken, jupo)
    assert "camera distance stays fixed" in jupo_prompt.lower()
    assert "zoom" not in jupo_prompt.lower()
    assert "do not push the camera in" not in jupo_prompt.lower()
    assert "aya's face and the partner's face stay in frame" in jupo_prompt.lower()
    assert "only two adults share this frame" in jupo_prompt.lower()
    assert "Look that stays for this whole shot" in jupo_prompt
    assert "grimy brown hospital dirt" in jupo_prompt
    assert "pale-tan" in jupo_prompt
    assert "Aya's shaft written" in jupo_prompt
    spot = next(b for b in taken["beats"] if b["id"] == "04-gin-lick-spot")
    spot_prompt = build_beat_prompt(taken, spot)
    assert "behind aya toward the left" in spot["action"].lower()
    assert "enters from the left edge" in spot["action"].lower()
    assert "matching aya's stride" in spot["action"].lower()
    assert "gradually slows" in spot["action"].lower()
    assert "hesitant and afraid" in spot["action"].lower()
    assert "grimy brown hospital dirt" in spot["action"].lower()
    assert "wall" not in spot["action"].lower()
    assert "ceiling" not in spot["action"].lower()
    assert "Look that stays for this whole shot" in spot_prompt
    assert "grimy brown hospital dirt" in spot_prompt
    assert "shaft written" not in spot_prompt.lower()
    assert spot.get("fade_cast") in (None, [])
    assert set(spot.get("cast") or []) == {"aya", "gin"}
    kana_spot = next(b for b in taken["beats"] if b["id"] == "07-kana-spot")
    assert "grimy brown hospital dirt" in kana_spot["action"].lower()
    assert "stroking the erect 20cm" in kana_spot["action"].lower()
    assert "white goo" in kana_spot["action"].lower()
    assert "enters from the right edge" in kana_spot["action"].lower()
    assert "wall" not in kana_spot["action"].lower()
    assert "Look that stays for this whole shot" in build_beat_prompt(taken, kana_spot)
    assert "24cm" not in walk_prompt
    kiss = next(b for b in taken["beats"] if b["id"] == "03-kiss")
    kiss_prompt = build_beat_prompt(taken, kiss)
    assert "Look that stays for this whole shot" in kiss_prompt
    assert "grimy" in kiss_prompt.lower()
    kasumi = prepare_episode(load_episode(KASUMI_ADULT_DIR / "episode.json"))
    kasumi_beat = next(b for b in kasumi["beats"] if not is_ui_beat(b))
    assert "Look that stays" not in build_beat_prompt(kasumi, kasumi_beat)
    assert "stays down" in jupo["action"].lower()
    assert "lies back from the sit" in jupo["action"].lower()
    assert "rises to her feet" not in jupo["action"].lower()
    assert "stays up into the mouth" in jupo["action"].lower()
    _assert_hospital_bans(taken)
    assert validate_episode(taken, root=HOSPITAL_DIR) == []

    fuck = prepare_episode(raw, gin_override="犯す")
    fuck_lick = next(b for b in fuck["beats"] if b["id"] == "04-gin-lick")
    fuck_in = next(b for b in fuck["beats"] if b["id"] == "04-gin-in")
    assert "behind aya toward the left" in fuck_lick["action"].lower()
    assert "lands on her feet" not in fuck_lick["action"].lower()
    assert "shocked wide-eyed" in fuck_lick["action"].lower()
    assert "already sitting on her butt" in fuck_in["action"].lower()
    assert "rises to her feet once" in fuck_in["action"].lower()
    assert "set the pose together" in fuck_in["action"].lower()
    gin_sex = action_blob(fuck, "04-gin")
    assert "travels into the pussy, glans only" in gin_sex
    assert "hips press together" in gin_sex
    assert next(b for b in fuck["beats"] if b["id"] == "04-gin-walk")["cast"] == ["aya"]

    dog = prepare_episode(raw, gin_override="誘う後背")
    dog_lick = next(b for b in dog["beats"] if b["id"] == "04-gin-lick")
    dog_in = next(b for b in dog["beats"] if b["id"] == "04-gin-in")
    assert "behind aya toward the left" in dog_lick["action"].lower()
    assert "lands on her feet" not in dog_lick["action"].lower()
    assert "aya's chest meets gin's back" in dog_in["action"].lower()
    assert "already sitting on her butt" in dog_in["action"].lower()
    assert "drops herself to all fours" in dog_in["action"].lower()
    assert "rises to her feet once" in dog_in["action"].lower()
    assert "set the pose together" in dog_in["action"].lower()
    assert "can't-hold-back" in action_blob(dog, "04-gin") or "ass toward aya" in action_blob(dog, "04-gin")

    stand = prepare_episode(raw, tsuno_override="受け入れる立ちバック")
    meet = next(b for b in stand["beats"] if b["id"] == "04-tsuno-meet")
    join = next(b for b in stand["beats"] if b["id"] == "04-tsuno-in")
    peak = next(b for b in stand["beats"] if b["id"] == "04-tsuno-peak")
    out = next(b for b in stand["beats"] if b["id"] == "04-tsuno-walk")
    assert "palms planted" in meet["action"].lower()
    assert "right edge" in meet["camera"].lower()
    assert "t-junction" in meet["action"].lower()
    assert "cup aya's breasts" in meet["action"].lower()
    assert "one large single eye" in meet["action"].lower()
    assert "exactly four long fingers" in meet["action"].lower()
    assert "lunges" not in meet["action"].lower()
    assert "happy accepting smile" in meet["action"].lower()
    assert "already stopped" in meet["action"].lower()
    tsuno_spot = next(b for b in stand["beats"] if b["id"] == "04-tsuno-meet-spot")
    assert tsuno_spot.get("connect") == "chain"
    assert "enters from the left edge" in tsuno_spot["action"].lower()
    assert "this take ends on that stop" in tsuno_spot["action"].lower()
    assert "back of her head on the linoleum" in next(b for b in prepare_episode(raw, gin_override="犯す")["beats"] if b["id"] == "04-gin-in")["action"].lower()
    assert "snappy real-time" in meet["action"].lower()
    assert "press flush" in meet["action"].lower()
    assert "squash and change shape" in meet["action"].lower()
    assert "knead them from behind" in meet["action"].lower()
    assert "snaps her body against" in meet["action"].lower()
    assert "travels into aya's anus" in meet["action"].lower()
    assert "aya stops and tsuno stops" in meet["action"].lower()
    assert "surprise and pleasure" in meet["action"].lower()
    assert meet["voices"][0]["line"] == "んおおおおぉー"
    assert "tsuno's breasts pressed into aya's back" in meet["camera"].lower()
    assert "do not turn to face each other" in meet["action"].lower()
    assert "pushes aya forward onto the peeling wall" in meet["action"].lower()
    assert meet.get("loco") == "walk"
    assert "24cm" in meet["action"]
    assert "ashen gray" in meet["action"].lower()
    assert "rotting" in meet["action"].lower()
    assert "rotting" in join["action"].lower()
    assert "ashen-gray shaft" in join["action"].lower()
    assert "pale-tan skin" not in meet["action"].lower()
    _assert_insertion_direction(join["action"], build_beat_prompt(stand, join))
    assert "drool" in peak["action"].lower()
    assert out["cast"] == ["aya"]
    assert "gone from frame one" in out["action"].lower()
    blob = action_blob(stand, "04-tsuno")
    assert "doggy" not in blob and "missionary" not in blob
    assert "zombie" not in build_beat_prompt(stand, join).lower()
    _assert_hospital_bans(stand)
    invite = prepare_episode(raw, tsuno_override="誘う立ちバック")
    invite_meet = next(b for b in invite["beats"] if b["id"] == "04-tsuno-meet")
    assert "looks back" in action_blob(invite, "04-tsuno")
    assert "t-junction" in invite_meet["action"].lower()
    assert "cup aya's breasts" in invite_meet["action"].lower()
    assert "lunges" not in invite_meet["action"].lower()
    assert "happy accepting smile" in invite_meet["action"].lower()
    assert "knead them from behind" in invite_meet["action"].lower()
    assert "travels into aya's anus" in invite_meet["action"].lower()
    assert "aya stops and tsuno stops" in invite_meet["action"].lower()
    assert invite_meet["voices"][0]["line"] == "んおおおおぉー"
    assert validate_episode(stand, root=HOSPITAL_DIR) == []
    assert validate_episode(invite, root=HOSPITAL_DIR) == []

    anal = prepare_episode(raw, tsuno_override="後ろアナル")
    anal_meet = next(b for b in anal["beats"] if b["id"] == "04-tsuno-meet")
    anal_in = next(b for b in anal["beats"] if b["id"] == "04-tsuno-in")
    anal_peak = next(b for b in anal["beats"] if b["id"] == "04-tsuno-peak")
    assert "cup aya's breasts" in anal_meet["action"].lower()
    assert "snaps her body against" in anal_meet["action"].lower()
    assert "travels into aya's anus" in anal_meet["action"].lower()
    assert "aya stops and tsuno stops" in anal_meet["action"].lower()
    assert "surprise and pleasure" in anal_meet["action"].lower()
    assert "half-step to the side" not in anal_meet["action"].lower()
    assert anal_meet["voices"][0]["line"] == "んおおおおぉー"
    assert "lunges" not in anal_meet["action"].lower()
    assert "happy accepting smile" in anal_meet["action"].lower()
    assert "knead them from behind" in anal_meet["action"].lower()
    assert "squash and change shape" in anal_meet["action"].lower()
    assert "exactly four long fingers" in anal_meet["action"].lower()
    assert "one large single eye" in anal_meet["action"].lower()
    assert "travels into the anus" in anal_in["action"].lower()
    assert "pussy" not in anal_in["action"].lower()
    assert "pussy" not in anal_peak["action"].lower()
    assert "white goo fills the anus" in anal_peak["action"].lower()
    _assert_insertion_direction(anal_in["action"], build_beat_prompt(anal, anal_in))
    nelson = prepare_episode(raw, tsuno_override="フルネルソン")
    nel_in = next(b for b in nelson["beats"] if b["id"] == "04-tsuno-in")
    nel_peak = next(b for b in nelson["beats"] if b["id"] == "04-tsuno-peak")
    nel_meet = next(b for b in nelson["beats"] if b["id"] == "04-tsuno-meet")
    assert "feet stay in the air" in nel_in["action"].lower()
    assert "feet leave the linoleum" not in nel_in["action"].lower()
    assert "glans on the anus" in nel_in["action"].lower()
    assert "both forearms go under" in nel_in["action"].lower()
    assert "walks right" not in nel_meet["action"].lower()
    assert "snaps in behind" not in nel_meet["action"].lower()
    assert "snaps her body against" in nel_meet["action"].lower()
    assert "travels into aya's anus" in nel_meet["action"].lower()
    assert "aya stops and tsuno stops" in nel_meet["action"].lower()
    assert "surprise and pleasure" in nel_meet["action"].lower()
    assert nel_meet["voices"][0]["line"] == "んおおおおぉー"
    assert "lunges" not in nel_meet["action"].lower()
    assert "happy accepting smile" in nel_meet["action"].lower()
    assert "wraps aya from behind" in nel_meet["action"].lower()
    assert "snappy real-time" in nel_meet["action"].lower()
    assert "press flush" in nel_meet["action"].lower()
    assert "knead them from behind" in nel_meet["action"].lower()
    assert nel_meet.get("loco") == "planted"
    assert nel_in.get("loco") == "planted"
    assert nel_in.get("camera_pack") == "none"
    assert nel_in.get("connect") == "t2v"
    assert "wide blissful smile" in nel_in["action"].lower()
    assert "travels into the anus" in nel_in["action"].lower()
    assert "pussy" not in nel_in["action"].lower()
    assert "lowers one of aya's feet" in nel_peak["action"].lower()
    assert "white goo fills the anus" in nel_peak["action"].lower()
    assert "woman facing the camera" in nel_in["action"].lower()
    assert "tsuno's face stays behind aya's head" in nel_in["action"].lower()
    assert "tsuno's torso stays behind aya's back" in nel_in["action"].lower()
    _assert_insertion_direction(nel_in["action"], build_beat_prompt(nelson, nel_in))
    _assert_hospital_bans(anal)
    _assert_hospital_bans(nelson)
    assert validate_episode(anal, root=HOSPITAL_DIR) == []
    assert validate_episode(nelson, root=HOSPITAL_DIR) == []


def test_hospital_chain_dropdown_overrides_t2v_locks():
    """Chain/landing follow the dropdown over authored connect:t2v on the ward.

    First shot stays T2V. A -spot newcomer stays I2V. Other new people stay T2V.
    Same-cast acts, including pose, toilet, gin, tsuno, and fight, become I2V.
    Cut stays all T2V.
    """
    raw = load_episode(HOSPITAL_DIR / "episode.json")
    accept = prepare_episode(raw, story_override="受け入れる", connect_override="chain")
    kiss = next(b for b in accept["beats"] if b["id"] == "03-kiss")
    assert beat_source(kiss) == "chain"
    assert kiss.get("connect") == "t2v"
    assert "both standing" in kiss["action"].lower()
    assert "drops down" in kiss["action"].lower()
    six = next(b for b in accept["beats"] if b["id"] == "06-doggy")
    assert beat_source(six) == "chain"
    nine = next(b for b in accept["beats"] if b["id"] == "09-join")
    assert beat_source(nine) == "chain"
    twelve = next(b for b in accept["beats"] if b["id"] == "12-exit")
    assert beat_source(twelve) == "chain"
    peek_spot = next(b for b in accept["beats"] if b["id"] == "04-peek-spot")
    peek = next(b for b in accept["beats"] if b["id"] == "04-peek")
    assert beat_source(peek_spot) == "chain"
    assert beat_source(peek) == "chain"
    kana_spot = next(b for b in accept["beats"] if b["id"] == "07-kana-spot")
    kana = next(b for b in accept["beats"] if b["id"] == "07-kana")
    assert beat_source(kana_spot) == "chain"
    assert beat_source(kana) == "chain"
    shino_spot = next(b for b in accept["beats"] if b["id"] == "10-shino-spot")
    shino = next(b for b in accept["beats"] if b["id"] == "10-shino")
    assert beat_source(shino_spot) == "chain"
    assert beat_source(shino) == "chain"

    assert "steps right" not in nine["action"].lower()
    assert "already in place" not in nine["action"].lower()
    assert "steps in close" in nine["action"].lower()
    assert "standing in the corridor" in kiss["camera"].lower()

    for pose in ("四つん這い股広げ", "M字", "騎乗位"):
        ep = prepare_episode(
            raw,
            story_override="誘う",
            invite_pose_override=pose,
            connect_override="chain",
        )
        kiss = next(b for b in ep["beats"] if b["id"] == "03-kiss")
        assert beat_source(kiss) == "chain", pose
        assert kiss.get("connect") == "t2v", pose
        assert "mouths joined" in kiss["action"].lower(), pose
        assert "mouths joined" in kiss["camera"].lower(), pose
        assert "already kneeling at the hips" not in kiss["camera"].lower(), pose
        six = next(b for b in ep["beats"] if b["id"] == "06-doggy")
        assert beat_source(six) == "chain", pose
        assert "after the wait" in six["action"].lower(), pose
        assert "already kneeling in front" not in six["action"].lower(), pose
        nine = next(b for b in ep["beats"] if b["id"] == "09-join")
        assert beat_source(nine) == "chain", pose
        assert "kana still stands" in nine["action"].lower(), pose
        assert "already kneeling in front" not in nine["action"].lower(), pose
        twelve = next(b for b in ep["beats"] if b["id"] == "12-exit")
        assert beat_source(twelve) == "chain", pose
        if pose == "騎乗位":
            assert "drops down onto her knees" in kiss["action"].lower()
            assert "drops down onto her knees" in six["action"].lower()
            assert "drops down onto her knees" in nine["action"].lower()
            assert "drops down onto her knees" in twelve["action"].lower()
            assert "still kneeling" in nine["action"].lower()
            assert "lips at the base" in nine["action"].lower()
            assert "pussy hanging directly above the glans" not in nine["action"].lower()
            assert "kana on her back" not in nine["action"].lower()
            assert "zoom" not in (nine.get("camera") or "").lower()
            nine_prompt = build_beat_prompt(ep, nine, trigger=merge_trigger("", nine))
            assert "camera distance stays fixed" in nine_prompt.lower()
            assert "zoom" not in nine_prompt.lower()
            assert "aya's face and the partner's face stay in frame" in nine_prompt.lower()

    evade = prepare_episode(raw, story_override="回避", connect_override="chain")
    evade_kiss = next(b for b in evade["beats"] if b["id"] == "03-kiss")
    assert beat_source(evade_kiss) == "chain"

    gin = prepare_episode(raw, story_override="受け入れる", gin_override="犯される", connect_override="chain")
    lick_spot = next(b for b in gin["beats"] if b["id"] == "04-gin-lick-spot")
    lick = next(b for b in gin["beats"] if b["id"] == "04-gin-lick")
    assert lick_spot.get("connect") == "chain"
    assert beat_source(lick_spot) == "chain"
    measured = prepare_episode(
        raw,
        story_override="受け入れる",
        gin_override="犯される",
        tsuno_override="受け入れる立ちバック",
        toilet_override="pee",
        connect_override="chain",
    )
    gpu = [b for b in measured["beats"] if not is_ui_beat(b) and beat_renders(b)]
    assert [b["id"] for b in gpu if beat_source(b) == "t2v"] == ["01-cover"]
    assert lick.get("connect") == "t2v"
    assert beat_source(lick) == "chain"
    gin_in = next(b for b in gin["beats"] if b["id"] == "04-gin-jupo")
    assert beat_source(gin_in) == "chain"
    assert "follow subject_definitions" in build_beat_prompt(gin, gin_in)
    toilet = prepare_episode(raw, story_override="受け入れる", toilet_override="pee", connect_override="chain")
    tin = next(b for b in toilet["beats"] if b["id"] == "04-toilet-in")
    assert tin.get("connect") == "t2v"
    assert beat_source(tin) == "chain"

    # Unexpected T2V is only the first shot or a new person outside a -spot. Authored t2v no longer blocks chain.
    sweeps = [
        dict(story_override="受け入れる"),
        dict(story_override="誘う", invite_pose_override="騎乗位"),
        dict(story_override="誘う", invite_pose_override="四つん這い股広げ"),
        dict(story_override="回避"),
        dict(story_override="戦って勝つ"),
        dict(story_override="受け入れる", gin_override="犯す", tsuno_override="受け入れる立ちバック", toilet_override="tentacle"),
    ]
    for kw in sweeps:
        ep = prepare_episode(raw, connect_override="chain", **kw)
        prev: set[str] = set()
        first = True
        for beat in ep["beats"]:
            if is_ui_beat(beat):
                continue
            cast = {str(c) for c in (beat.get("cast") or [])}
            added = cast - prev
            if beat_source(beat) == "t2v" and not first and not added:
                raise AssertionError(f"same-cast T2V {beat['id']} {kw}")
            spot = str(beat.get("id") or "").endswith("-spot")
            if beat_source(beat) == "chain" and (first or (added and not spot)):
                raise AssertionError(f"chain on a new body {beat['id']} {kw}")
            first = False
            prev = cast
        cuts = prepare_episode(raw, connect_override="カット", **kw)
        assert all(beat_source(b) == "t2v" for b in cuts["beats"] if not is_ui_beat(b)), kw


def test_hospital_end_connect_is_runtime_selectable():
    raw = load_episode(HOSPITAL_DIR / "episode.json")
    assert raw["render"]["end_connect"] == "follow"
    defaulted = prepare_episode(raw, story_override="受け入れる", connect_override="chain")
    walk = next(b for b in defaulted["beats"] if b["id"] == "06-doggy-walk")
    assert is_end_connect_beat(walk)
    assert beat_source(walk) == "chain"
    assert walk.get("fade_cast") == ["rei"]
    nxt = None
    seen = False
    for beat in defaulted["beats"]:
        if beat["id"] == "06-doggy-walk":
            seen = True
            continue
        if seen and not is_ui_beat(beat):
            nxt = beat
            break
    assert nxt is not None
    # The next encounter is a -spot. Chain keeps it I2V so Kana walks into Aya's last frame.
    assert str(nxt["id"]).endswith("-spot")
    assert beat_source(nxt) == "chain"

    chained = prepare_episode(
        raw,
        story_override="受け入れる",
        connect_override="カット",
        end_connect_override="次のシーンへ続ける",
    )
    # Scene-end chain keeps the leftover partner in-frame and fades her.
    walk_c = next(b for b in chained["beats"] if b["id"] == "06-doggy-walk")
    assert beat_source(walk_c) == "chain"
    assert walk_c.get("fade_cast") == ["rei"]
    seen = False
    follow = None
    for beat in chained["beats"]:
        if beat["id"] == "06-doggy-walk":
            seen = True
            continue
        if seen and not is_ui_beat(beat):
            follow = beat
            break
    assert follow is not None
    assert str(follow["id"]).endswith("-spot")
    assert beat_source(follow) == "chain"
    assert chained["render"]["end_connect"] == "chain"

    followed = prepare_episode(
        raw,
        story_override="受け入れる",
        connect_override="chain",
        end_connect_override="1番のつなぎに従う",
    )
    walk_f = next(b for b in followed["beats"] if b["id"] == "06-doggy-walk")
    assert beat_source(walk_f) == "chain"
    gin_walk = next(
        b
        for b in prepare_episode(raw, gin_override="犯される", end_connect_override="follow", connect_override="chain")["beats"]
        if b["id"] == "04-gin-walk"
    )
    assert beat_source(gin_walk) == "chain"
    assert "gin" in (gin_walk.get("fade_cast") or [])
    assert validate_episode(chained, root=HOSPITAL_DIR) == []


def test_hospital_clip_failures_are_rewritten():
    """Fixes from the ward speed run: giants, peak→walk, gin/tsuno/rei looks, planted sex, hilt then piston."""
    raw = load_episode(HOSPITAL_DIR / "episode.json")
    assert CAMERA_PACKS["side2d"].get("planted_lock")
    assert "Adults move LEFT or RIGHT" in CAMERA_PACKS["side2d"]["lock"]
    assert "Adults move LEFT or RIGHT" not in CAMERA_PACKS["side2d"]["planted_lock"]
    assert "Nobody is giant" in CAMERA_PACKS["side2d"]["planted_lock"]

    invite = prepare_episode(
        raw,
        story_override="誘う",
        invite_pose_override="ベロチュー→じゅぼ→騎乗位",
        connect_override="chain",
        toilet_override="小便",
        gin_override="犯す",
        tsuno_override="誘う立ちバック",
        scenes_override="miki=invite_all_fours,rei=invite_m_open,kana=invite_ride,shino=inherit",
    )
    kiss = next(b for b in invite["beats"] if b["id"] == "03-kiss")
    peak = next(b for b in invite["beats"] if b["id"] == "03-kiss-peak")
    walk = next(b for b in invite["beats"] if b["id"] == "03-kiss-walk")
    assert kiss.get("connect") == "t2v"
    assert beat_source(kiss) == "chain"
    assert "mouths joined" in kiss["action"].lower()
    assert kiss.get("loco") == "planted"
    assert peak.get("loco") == "planted"
    assert beat_source(peak) == "chain"
    assert is_end_connect_beat(walk)
    assert beat_source(walk) == "chain"
    assert "miki" in (walk.get("fade_cast") or [])
    assert "gone from frame one" not in walk["action"].lower()
    kiss_prompt = build_beat_prompt(invite, kiss)
    assert PLANTED_CLAUSE in kiss_prompt
    assert PLANTED_PACE_CLAUSE in kiss_prompt
    assert GAMEPLAY_PACE_CLAUSE not in kiss_prompt
    assert "idle breathing" not in kiss_prompt.lower()
    assert "unless the action names running or walking" not in kiss_prompt.lower()
    assert "walks right" not in kiss["action"].lower()
    assert "steps right" not in kiss["action"].lower()
    assert "walking-and-hit" not in kiss["action"].lower()
    assert "Adults move LEFT or RIGHT" not in kiss_prompt
    assert "The lit doorway sits at the RIGHT edge" not in kiss_prompt
    assert "nobody is giant" in kiss_prompt.lower()

    toilet = next(b for b in invite["beats"] if b["id"] == "04-toilet")
    assert toilet.get("loco") == "planted"
    assert beat_source(toilet) == "chain"
    toilet_prompt = build_beat_prompt(invite, toilet)
    assert PEE_STILL_CLAUSE in toilet_prompt
    assert PLANTED_CLAUSE not in toilet_prompt
    assert PLANTED_PACE_CLAUSE not in toilet_prompt
    assert "only the yellow stream moves" in toilet_prompt.lower()
    assert "walks right" not in toilet["action"].lower()
    assert "Adults move LEFT or RIGHT" not in toilet_prompt

    gin_in = next(b for b in invite["beats"] if b["id"] == "04-gin-in")
    gin_lick = next(b for b in invite["beats"] if b["id"] == "04-gin-lick")
    assert gin_lick.get("connect") == "t2v"
    assert gin_in.get("connect") == "t2v"
    assert beat_source(gin_in) == "chain"
    assert gin_in.get("loco") == "planted"
    assert "gums" in gin_lick["action"].lower() or "gums" in (invite["cast"]["gin"]["lock"].lower())
    assert "muscle fiber" in invite["cast"]["gin"]["lock"]
    _assert_insertion_direction(gin_in["action"], build_beat_prompt(invite, gin_in))
    assert "do not piston yet" in gin_in["action"].lower()

    tsuno_in = next(b for b in invite["beats"] if b["id"] == "04-tsuno-in")
    assert "hips from the sides" in tsuno_in["action"].lower()
    assert "cracked" in invite["cast"]["tsuno"]["lock"]
    _assert_insertion_direction(tsuno_in["action"], build_beat_prompt(invite, tsuno_in))

    six_spot = next(b for b in invite["beats"] if b["id"] == "06-doggy-spot")
    six = next(b for b in invite["beats"] if b["id"] == "06-doggy")
    six_peak = next(b for b in invite["beats"] if b["id"] == "06-doggy-peak")
    assert six_spot.get("connect") == "chain"
    assert beat_source(six_spot) == "chain"
    assert six.get("connect") == "t2v"
    assert beat_source(six) == "chain"
    assert beat_source(six_peak) == "chain"
    assert six["cast"] == ["aya", "rei"]
    assert "kana" not in six["cast"]
    assert "dark-brown filthy sludge" in invite["cast"]["rei"]["lock"]
    assert "WHITE filthy slime" not in invite["cast"]["rei"]["lock"]
    assert "LEFT half of the face" in invite["cast"]["rei"]["lock"]

    ride = prepare_episode(raw, story_override="誘う", invite_pose_override="騎乗位")
    ride_in = next(b for b in ride["beats"] if b["id"] == "03-kiss-ride")
    ride_prompt = build_beat_prompt(ride, ride_in)
    assert "squats from above" not in ride_in["action"].lower()
    assert "from directly above" not in ride_in["action"].lower()
    assert "straddles the hips" in ride_in["action"].lower()
    assert "facing the partner" in ride_in["action"].lower()
    assert "straight down" in ride_in["action"].lower()
    assert "three separate lowers" in ride_in["action"].lower()
    assert "beside the partner's hips" in ride_in["action"].lower()
    assert "knees stay raised" in ride_in["action"].lower()
    assert "soles stay on the linoleum" in ride_in["action"].lower()
    assert "thighs form an m" in ride_in["action"].lower()
    assert "press flush" in ride_in["action"].lower()
    assert "do not piston yet" in ride_in["action"].lower()
    assert "slides both feet right" in ride_in["action"].lower()
    assert "raises her hips" in ride_in["action"].lower()
    assert "directly above the glans" in ride_in["action"].lower()
    assert "before the shaft enters, miki lies on her back" in ride_in["action"].lower()
    assert "the back of her head on the linoleum" in ride_in["action"].lower()
    rei_ride = next(b for b in prepare_episode(raw, story_override="誘う", invite_pose_override="騎乗位")["beats"] if b["id"] == "06-doggy-ride")
    shino_ride = next(b for b in prepare_episode(raw, story_override="誘う", invite_pose_override="騎乗位")["beats"] if b["id"] == "12-exit-ride")
    assert "before the shaft enters, rei lies on her back" in rei_ride["action"].lower()
    assert "before the shaft enters, shino lies on her back" in shino_ride["action"].lower()
    assert "the back of her head on the linoleum" in rei_ride["action"].lower()
    assert "the back of her head on the linoleum" in shino_ride["action"].lower()
    assert "slides both feet right" in rei_ride["action"].lower()
    assert "slides both feet right" in shino_ride["action"].lower()
    _assert_insertion_direction(ride_in["action"], ride_prompt)
    assert ride_in.get("loco") == "planted"
    runtime_src = (ROOT / "colab" / "h3_i2v_runtime.py").read_text(encoding="utf-8")
    assert "H3_UNASSIGN_RUNTIME" in runtime_src
    assert "keep runtime" in runtime_src


def test_hospital_stills_are_not_kasumi_copies():
    kasumi = {
        hashlib.md5(p.read_bytes()).digest()
        for p in (KASUMI_ADULT_DIR / "stills").glob("*.jpg")
    }
    assert kasumi
    for p in (HOSPITAL_DIR / "stills").glob("*.jpg"):
        digest = hashlib.md5(p.read_bytes()).digest()
        assert digest not in kasumi, p.name
    stills = {b.get("still") for b in load_episode(HOSPITAL_DIR / "episode.json")["beats"] if b.get("still")}
    assert stills <= {
        "stills/01-cover.jpg",
        "stills/04-peek.jpg",
        "stills/06-fight.jpg",
        "stills/08-door.jpg",
        "stills/10-lose.jpg",
    }


def test_camera_packs_rotate_and_t2v_rejects_last_frame_lock():
    assert set(CAMERA_PACKS) == {"side2d", "action3d"}
    assert DEFAULT_CAMERA_PACK == "side2d"
    for name, pack in CAMERA_PACKS.items():
        angles = pack["angles"]
        assert len(angles) >= 2
        assert len(set(angles)) == len(angles), name
        for i in range(len(angles) * 2):
            assert camera_angle(name, i) != camera_angle(name, i + 1), (name, i)
            low = camera_angle(name, i).lower()
            assert "slow" not in low and "first-person" not in low
        lock = str(pack["lock"]).lower()
        assert "third-person" in lock and "slow motion" not in lock
    side_lock = str(CAMERA_PACKS["side2d"]["lock"]).lower()
    assert "profile" in side_lock and "right edge" in side_lock and "left to right" in side_lock
    ep = load_episode(KASUMI_ADULT_DIR / "episode.json")
    assert episode_camera_pack(ep) == "side2d"
    assert episode_camera_pack(ep, "action3d") == "action3d"
    indexes = gpu_index_map(ep)
    gpu = [b for b in ep["beats"] if beat_source(b) == "t2v"]
    assert len(gpu) >= 4
    prompts = []
    for beat in gpu:
        p = build_beat_prompt(ep, beat, camera_pack="side2d", gpu_index=indexes[beat["id"]])
        prompts.append(p)
        assert "This shot:" in p
        assert "side-on" in p
        assert validate_beat_prompt(p, source="t2v") == []
    shots = [p.split("This shot:", 1)[1].split(".", 1)[0] for p in prompts]
    assert shots[0] != shots[1] != shots[2]
    side = camera_line(ep, gpu[0], pack_name="side2d", gpu_index=0)
    three = camera_line(ep, gpu[0], pack_name="action3d", gpu_index=0)
    assert "side-on" in side and "behind-left" in three
    locked_beats = [dict(b) for b in ep["beats"]]
    later = next(b for b in locked_beats if b.get("source") == "t2v" and b["id"] != locked_beats[0]["id"])
    later["still_as"] = "last"
    assert any("t2v cannot use still_as last" in e for e in validate_episode(dict(ep, beats=locked_beats)))
    bad = dict(gpu[0], camera="slow-motion close-up")
    assert any("slow motion" in e for e in validate_episode(dict(ep, beats=[bad, *ep["beats"][1:]])))
    assert any("slow-mo" in h.lower() or "slow" in h.lower() for h in forbidden_hits("no slow-mo please"))


def test_connect_modes_t2v_chain_landing_and_ui_labels():
    assert canonical_connect("カット") == "t2v"
    assert canonical_connect("カット（本ごと独立・迷ったらこれ）") == "t2v"
    assert canonical_connect("前の尻から続ける") == "chain"
    assert canonical_connect("前の最終フレームから続ける") == "chain"
    assert canonical_connect("着地スチールへ着く") == "landing"
    assert canonical_connect("用意した最終フレームへ着く") == "landing"
    assert canonical_connect("最終フレームi2v") == "chain"
    assert canonical_connect("最終フレーム用意") == "landing"
    assert canonical_connect("i2v_chain") == "chain"
    assert ui_default("connect") == "カット（本ごと独立・迷ったらこれ）"
    assert ui_default("end_connect") == "シーン終わりはカット（迷ったらこれ）"
    assert ui_choices("end_connect") == [
        "シーン終わりはカット（迷ったらこれ）",
        "次のシーンへ続ける",
        "1番のつなぎに従う",
    ]
    assert ui_default("camera") == "横スク（真横・全身・迷ったらこれ）"
    assert ui_default("preset") == "バランス（迷ったらこれ）"
    assert ui_choices("connect") == [
        "カット（本ごと独立・迷ったらこれ）",
        "前の最終フレームから続ける",
        "用意した最終フレームへ着く",
    ]
    help_txt = form_readme("connect")
    assert "プロンプトで直したい" in help_txt
    assert "1本目は T2V" in help_txt
    assert "stills の jpg" in help_txt
    assert ui_default("combat") == "格闘LoRAオフ（迷ったらこれ）"
    assert ui_choices("combat") == [
        "格闘LoRAオフ（迷ったらこれ）",
        "格闘LoRAオン（ハイメモリ専用）",
    ]
    picked = describe_run(connect="カット", camera="横スク", preset="バランス", episode="demo")
    assert "カット（本ごと独立・迷ったらこれ）" in picked
    assert "新しい相手の入りはカット" in picked
    assert "迷ったら既定のままで Run all" in picked
    assert "6 誘う" in picked
    assert "7 トイレ" in picked
    assert "8 灰色" in picked
    assert "9 角" in picked
    assert "シーン" in picked
    assert "話" in picked
    assert ui_default("episode") == "霞東フロア あさ（迷ったらこれ）"
    assert "病棟出口" in ui_choices("episode")
    assert canonical_episode("病棟出口") == "hospital-exit-adult"
    assert canonical_episode("霞東フロア あさ（迷ったらこれ）") == "kasumi-late-desk-adult"
    assert ui_default("scene") == "全体に従う（迷ったらこれ）"
    assert "□誘う・四つん這い股広げ" in ui_choices("scene")
    assert "格闘LoRAオフ" in picked
    assert "○受け入れる（生存・完了・迷ったらこれ）" in picked
    assert ui_default("story") == "○受け入れる（生存・完了・迷ったらこれ）"
    assert ui_choices("story")[0].startswith("○受け入れる")
    ep = load_episode(KASUMI_ADULT_DIR / "episode.json")
    assert episode_connect(ep) == "t2v"
    stock = load_episode(KASUMI_DIR / "episode.json")
    assert apply_connect_mode(stock) is stock
    assert [beat_source(b) for b in apply_connect_mode(stock)["beats"][:3]] == [beat_source(b) for b in stock["beats"][:3]]

    chained = apply_connect_mode(ep, "chain")
    assert validate_episode(chained, root=KASUMI_ADULT_DIR) == []
    gpu = [b for b in chained["beats"] if not is_ui_beat(b)]
    assert beat_source(gpu[0]) == "t2v"
    assert gpu[0].get("still_as") not in ("last", "both")
    first_prompt = build_beat_prompt(chained, gpu[0])
    assert "<Picture 1>" not in first_prompt
    assert validate_beat_prompt(first_prompt, source="t2v") == []
    assert all(beat_source(b) == "chain" for b in gpu[1:])
    assert all(b.get("still_as") not in ("last", "both") for b in gpu[1:])
    chain_prompt = build_beat_prompt(chained, gpu[1])
    assert "<Picture 1>" in chain_prompt
    assert "This shot continues the previous one without a cut" in chain_prompt
    assert "The camera stays in this setup" in chain_prompt
    assert "This shot:" not in chain_prompt

    cuts = apply_connect_mode(ep, "カット")
    gpu_cut = [b for b in cuts["beats"] if not is_ui_beat(b)]
    assert beat_source(gpu_cut[0]) == "t2v"
    assert all(beat_source(b) == "t2v" for b in gpu_cut)

    hospital = apply_connect_mode(load_episode(HOSPITAL_DIR / "episode.json"), "前の最終フレームから続ける")
    hgpu = [b for b in hospital["beats"] if not is_ui_beat(b)]
    assert beat_source(hgpu[0]) == "t2v"
    assert any(str(b.get("connect") or "").strip().lower() == "t2v" and beat_source(b) == "chain" for b in hgpu[1:])
    assert all(beat_source(b) == "chain" for b in hgpu[1:])
    landed_h = apply_connect_mode(load_episode(HOSPITAL_DIR / "episode.json"), "用意した最終フレームへ着く")
    land_gpu = [b for b in landed_h["beats"] if not is_ui_beat(b) and str(b.get("connect") or "").strip().lower() == "t2v"]
    assert land_gpu and all(beat_source(b) != "t2v" or b["id"] == land_gpu[0]["id"] for b in land_gpu)

    landed = apply_connect_mode(ep, "用意した最終フレームへ着く")
    assert validate_episode(landed, root=KASUMI_ADULT_DIR) == []
    gpu_l = [b for b in landed["beats"] if not is_ui_beat(b)]
    assert beat_source(gpu_l[0]) == "still" and beat_still_as(gpu_l[0]) == "first"
    later = [b for b in gpu_l[1:] if b.get("still")]
    assert later and all(beat_still_as(b) == "last" for b in later)
    aisle = next(b for b in landed["beats"] if b["id"] == "04-aisle")
    start, seconds = beat_window(landed, aisle)
    assert start + seconds == pytest.approx(beat_clip_seconds(landed, aisle), abs=0.05)
    land_prompt = build_beat_prompt(landed, later[0])
    assert "<Picture 2>" in land_prompt and STILL_LAST_HEADER in land_prompt
    assert "The camera stays in this setup" in land_prompt

    cuts = apply_connect_mode(landed, "カット")
    assert all(beat_source(b) == "t2v" for b in cuts["beats"] if not is_ui_beat(b))


def test_apply_extra_loras_drops_cinema(tmp_path):
    loras = tmp_path / "loras"
    loras.mkdir()
    (loras / LORA_FILES["cinema"]).write_bytes(b"x")
    preset = {"name": "balance", "stack": [("larry.safetensors", 1.0)], "steps": 8, "trigger": "", "notes": []}
    dropped = apply_extra_loras(preset, {"extra_loras": ["cinema"]}, loras)
    assert dropped["stack"] == preset["stack"]
    assert any("cinematic LoRA skipped" in n for n in dropped["notes"])


def test_apply_extra_loras_blowjob_stacks_on_hybrid(tmp_path):
    beat = {"extra_loras": ["blowjob", "mystic"], "trigger": "bl0w_j0b"}
    daily = {"name": "daily", "stack": [("larry.safetensors", 1.0)], "steps": 8, "trigger": "", "notes": []}
    loras = tmp_path / "loras"
    loras.mkdir()
    (loras / LORA_FILES["blowjob"]).write_bytes(b"x")
    (loras / LORA_FILES["mystic"]).write_bytes(b"x")
    stacked = apply_extra_loras(daily, beat, loras, unet=EROS_MAX_UNET)
    assert stacked["stack"][-2:] == [(LORA_FILES["blowjob"], 0.8), (LORA_FILES["mystic"], 1.0)]
    empty = tmp_path / "empty"
    empty.mkdir()
    missing = apply_extra_loras(daily, beat, empty, unet=EROS_MAX_UNET)
    assert missing["stack"] == daily["stack"]
    assert any("MM-H3_Blowjob_v3.safetensors" in n for n in missing["notes"])


def test_cast_lock_rejects_underage_tags():
    raw = load_episode(KASUMI_ADULT_DIR / "episode.json")
    bad_age = copy.deepcopy(raw)
    bad_age["cast"]["mio"]["age"] = 16
    assert any("age" in e and "adult" in e for e in validate_episode(bad_age, root=KASUMI_ADULT_DIR))
    twenty = copy.deepcopy(raw)
    twenty["cast"]["mio"]["age"] = 20
    assert any(">= 21" in e for e in validate_episode(twenty, root=KASUMI_ADULT_DIR))
    bad_lock = copy.deepcopy(raw)
    bad_lock["cast"]["mio"]["lock"] = "16y, Japanese girl, pretty face, slim body, C-cup breasts"
    assert any("lock" in e and "adult" in e for e in validate_episode(bad_lock, root=KASUMI_ADULT_DIR))


def test_stock_unet_never_auto_picks_eros_max(tmp_path):
    diff = tmp_path / "diffusion_models"
    diff.mkdir()
    (diff / EROS_MAX_UNET).write_bytes(b"eros")
    (diff / "minimax_h3_fl2va_pruned_int8_convrot.safetensors").write_bytes(b"stock")
    assert is_erotic_unet_name(EROS_MAX_UNET)
    assert is_erotic_unet_name("Eros Max.safetensors")
    assert is_erotic_unet_name("ErosMax.safetensors")
    assert is_erotic_weight_path("hub/models--x--MiniMax-H3-10Eros-Max-Quants/blobs/abc")
    assert not is_erotic_unet_name("minimax_h3_fl2va_pruned_int8_convrot.safetensors")
    assert pick_stock_fl2va(diff) == "minimax_h3_fl2va_pruned_int8_convrot.safetensors"
    stock_ep = {"render": {"lane": "stock", "checkpoint": "stock"}}
    assert resolve_unet(stock_ep, diff) == "minimax_h3_fl2va_pruned_int8_convrot.safetensors"
    adult = load_episode(KASUMI_ADULT_DIR / "episode.json")
    with pytest.raises(EpisodeError, match="stock fallback is forbidden"):
        resolve_unet(adult, diff, models_root=tmp_path)
    erotic_root = tmp_path / "erotic"
    erotic_root.mkdir()
    payload = erotic_root / EROS_MAX_UNET
    payload.touch()
    payload.write_bytes(b"eros")
    os.truncate(payload, 20_000_000_001)
    assert resolve_unet(adult, diff, models_root=tmp_path) == EROS_MAX_UNET
    assert ensure_episode_checkpoint(stock_ep, tmp_path) == []
    with pytest.raises(EpisodeError, match="refusing to fetch"):
        ensure_episode_checkpoint({"render": {"lane": "stock", "checkpoint": "eros-max"}}, tmp_path)
    assert stage_erotic_unet(adult, tmp_path) == EROS_MAX_UNET
    link = diff / EROS_MAX_UNET
    assert link.is_symlink() and link.resolve() == (erotic_root / EROS_MAX_UNET).resolve()
    assert pick_stock_fl2va(diff) == "minimax_h3_fl2va_pruned_int8_convrot.safetensors"


def test_eros_checkpoint_fetch_keeps_partial(tmp_path, monkeypatch):
    adult = load_episode(KASUMI_ADULT_DIR / "episode.json")
    dest = tmp_path / "erotic" / EROS_MAX_UNET
    dest.parent.mkdir()
    dest.write_bytes(b"partial")
    os.truncate(dest, 5_556_846_100)

    def fake_resume(url: str, dest_path: Path, *, min_bytes: int, expected_bytes: int = 0, tries: int = 4) -> bool:
        part = dest_path.with_name(dest_path.name + ".part")
        if dest_path.is_file() and dest_path.stat().st_size < min_bytes:
            dest_path.replace(part)
        return False

    monkeypatch.setattr("h3_episode.fetch_resumable", fake_resume)
    with pytest.raises(EpisodeError, match="fetch incomplete"):
        ensure_episode_checkpoint(adult, tmp_path)
    part = dest.with_name(dest.name + ".part")
    assert part.is_file() and part.stat().st_size == 5_556_846_100
    assert not dest.is_file()


def _sparse_eros(path: Path, size: int = 20_000_000_001) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"eros")
    os.truncate(path, size)
    return path


def _forbid_eros_fetch(monkeypatch):
    def boom(*_a, **_k):
        raise AssertionError("must not fetch Eros Max when a Drive copy exists")

    monkeypatch.setattr("h3_episode.fetch_resumable", boom)


def test_eros_reuses_drive_copy_without_huggingface(tmp_path, monkeypatch):
    adult = load_episode(KASUMI_ADULT_DIR / "episode.json")
    _forbid_eros_fetch(monkeypatch)
    payload = _sparse_eros(tmp_path / "diffusion_models" / EROS_MAX_UNET)
    notes = ensure_episode_checkpoint(adult, tmp_path)
    assert any("reused Drive copy" in n for n in notes)
    assert not (tmp_path / "erotic" / EROS_MAX_UNET).is_symlink()
    assert stage_erotic_unet(adult, tmp_path) == EROS_MAX_UNET
    hit = locate_erotic_checkpoint(tmp_path)
    assert hit is not None and hit.resolve() == payload.resolve()


def test_eros_reuses_alias_filename(tmp_path, monkeypatch):
    adult = load_episode(KASUMI_ADULT_DIR / "episode.json")
    _forbid_eros_fetch(monkeypatch)
    payload = _sparse_eros(tmp_path / "diffusion_models" / "Eros Max.safetensors")
    notes = ensure_episode_checkpoint(adult, tmp_path)
    assert any("reused Drive copy" in n for n in notes)
    assert resolve_unet(adult, tmp_path / "diffusion_models", models_root=tmp_path) == payload.name
    assert stage_erotic_unet(adult, tmp_path) == payload.name
    assert pick_stock_fl2va(tmp_path / "diffusion_models") != payload.name


def test_eros_reuses_drive_root_and_hf_cache(tmp_path, monkeypatch):
    adult = load_episode(KASUMI_ADULT_DIR / "episode.json")
    _forbid_eros_fetch(monkeypatch)
    drive = tmp_path / "minimax-h3-comfyui"
    models = drive / "models"
    (models / "diffusion_models").mkdir(parents=True)
    payload = _sparse_eros(drive / "10Eros-Max.safetensors")
    notes = ensure_episode_checkpoint(adult, models)
    assert any("reused Drive copy" in n for n in notes)
    assert stage_erotic_unet(adult, models) == payload.name

    other = tmp_path / "other-comfy"
    other_models = other / "models"
    (other_models / "diffusion_models").mkdir(parents=True)
    cached = _sparse_eros(
        other
        / "cache"
        / "hf"
        / "hub"
        / "models--DmitryDB--MiniMax-H3-10Eros-Max-Quants"
        / "snapshots"
        / "abc123def"
        / "FL2VA"
        / EROS_MAX_UNET
    )
    notes = ensure_episode_checkpoint(adult, other_models)
    assert any("reused Drive copy" in n for n in notes)
    assert stage_erotic_unet(adult, other_models) == cached.name


def test_eros_reuses_h3_eros_max_env(tmp_path, monkeypatch):
    adult = load_episode(KASUMI_ADULT_DIR / "episode.json")
    _forbid_eros_fetch(monkeypatch)
    payload = _sparse_eros(tmp_path / "somewhere" / "ErosMax.safetensors")
    monkeypatch.setenv("H3_EROS_MAX", str(payload))
    notes = ensure_episode_checkpoint(adult, tmp_path / "weights")
    assert any("reused Drive copy" in n for n in notes)
    assert stage_erotic_unet(adult, tmp_path / "weights") == payload.name


def test_eros_incomplete_canonical_uses_complete_elsewhere(tmp_path, monkeypatch):
    adult = load_episode(KASUMI_ADULT_DIR / "episode.json")
    _forbid_eros_fetch(monkeypatch)
    dest = tmp_path / "erotic" / EROS_MAX_UNET
    dest.parent.mkdir()
    dest.write_bytes(b"partial")
    os.truncate(dest, 5_556_846_100)
    payload = _sparse_eros(tmp_path / "diffusion_models" / "Eros Max.safetensors")
    notes = ensure_episode_checkpoint(adult, tmp_path)
    assert any("reused Drive copy" in n for n in notes)
    assert stage_erotic_unet(adult, tmp_path) == payload.name
    dest = tmp_path / "erotic" / EROS_MAX_UNET
    assert dest.is_file() and not dest.is_symlink() and dest.stat().st_size == 5_556_846_100


def test_eros_tiny_alias_still_fetches(tmp_path, monkeypatch):
    adult = load_episode(KASUMI_ADULT_DIR / "episode.json")
    tiny = tmp_path / "diffusion_models" / "Eros Max.safetensors"
    tiny.parent.mkdir()
    tiny.write_bytes(b"tiny")

    def fake_resume(url: str, dest_path: Path, *, min_bytes: int, expected_bytes: int = 0, tries: int = 4) -> bool:
        return False

    monkeypatch.setattr("h3_episode.fetch_resumable", fake_resume)
    with pytest.raises(EpisodeError, match="fetch incomplete"):
        ensure_episode_checkpoint(adult, tmp_path)


def test_bootstrap_refreshes_stale_episode_json_keeps_stills(tmp_path, monkeypatch):
    drive = tmp_path / "kasumi-late-desk"
    (drive / "stills").mkdir(parents=True)
    old = {"schema": "h3-episode/v1", "slug": "kasumi-late-desk", "beats": [{"id": "01-cover"}, {"id": "02-peek"}, {"id": "05-desk"}]}
    (drive / "episode.json").write_text(json.dumps(old), encoding="utf-8")
    kept = drive / "stills" / "01-cover.jpg"
    kept.write_bytes(b"keep-me")
    fresh = load_episode(KASUMI_DIR / "episode.json")

    def fake_fetch(url: str, dest: Path, *, min_bytes: int = 100) -> bool:
        dest = Path(dest)
        dest.parent.mkdir(parents=True, exist_ok=True)
        if str(url).endswith("episode.json"):
            dest.write_text(json.dumps(fresh), encoding="utf-8")
            return dest.stat().st_size > min_bytes
        dest.write_bytes(b"SHOULD-NOT-CLOBBER-EXISTING" if dest.name == "01-cover.jpg" else (b"x" * (min_bytes + 1)))
        return True

    monkeypatch.setattr("h3_episode.fetch_text", fake_fetch)
    fetched = bootstrap_episode("kasumi-late-desk", drive, branch="cursor/h3-ol-late-desk-33d9")
    assert "episode.json" in fetched
    ids = [b["id"] for b in load_episode(drive / "episode.json")["beats"]]
    assert ids == [
        "01-cover",
        "02-ui-guard",
        "03-shove",
        "04-peek",
        "05-ui-boss",
        "06-files",
        "07-talk",
        "08-nana",
        "09-ui-nana",
        "10-mug",
        "11-bag",
        "12-desk",
    ]
    assert kept.read_bytes() == b"keep-me"
    assert expected_duration(load_episode(drive / "episode.json")) == pytest.approx(44.9, abs=0.2)


def test_bootstrap_keeps_drive_json_when_github_fails(tmp_path, monkeypatch):
    drive = tmp_path / "kasumi-late-desk"
    drive.mkdir()
    (drive / "episode.json").write_text(
        json.dumps({"schema": "h3-episode/v1", "slug": "kasumi-late-desk", "beats": [{"id": "05-desk"}]}),
        encoding="utf-8",
    )
    monkeypatch.setattr("h3_episode.fetch_text", lambda *a, **k: False)
    assert bootstrap_episode("kasumi-late-desk", drive) == []
    assert [b["id"] for b in load_episode(drive / "episode.json")["beats"]] == ["05-desk"]


def test_apply_extra_loras_combat_skips_turbo_and_chains(tmp_path):
    beat = {"extra_loras": ["combat"], "trigger": "prfight2, prfin1"}
    assert merge_trigger("DY", beat) == "DY\nprfight2, prfin1"
    daily = {"name": "daily", "stack": [("larry.safetensors", 1.0), ("cinema.safetensors", 0.65)], "steps": 8, "trigger": "DY", "notes": []}
    loras = tmp_path / "loras"
    loras.mkdir()
    (loras / LORA_FILES["combat"]).write_bytes(b"x")
    stacked = apply_extra_loras(daily, beat, loras)
    assert stacked["stack"][-1] == (LORA_FILES["combat"], 1.0)
    assert stacked["steps"] == COMBAT_STEPS
    assert stacked["sampler"] == COMBAT_SAMPLER and stacked["scheduler"] == COMBAT_SCHEDULER
    turbo = {"name": "fast", "stack": [("minimax_h3_fl2v_turbo_4step_v1.0_768p_comfyui_bf16.safetensors", 1.0)], "steps": 4, "trigger": "", "notes": []}
    skipped = apply_extra_loras(turbo, beat, loras)
    assert skipped["stack"] == turbo["stack"]
    assert skipped.get("steps") == 4
    assert any("never with LightX2V turbo" in n for n in skipped["notes"])
    hybrid = apply_extra_loras(daily, beat, loras, unet=EROS_MAX_UNET)
    assert hybrid["stack"] == daily["stack"]
    assert any("TURBO-hybrid" in n for n in hybrid["notes"])
    opted = apply_extra_loras(
        daily, beat, loras, unet=EROS_MAX_UNET, allow_combat=True, skip_note="combat LoRA on (High-Memory)"
    )
    assert opted["stack"][-1] == (LORA_FILES["combat"], 1.0)
    assert opted["steps"] == COMBAT_STEPS
    offed = apply_extra_loras(
        daily, beat, loras, unet=EROS_MAX_UNET, allow_combat=False, skip_note="combat LoRA skipped (off)"
    )
    assert offed["stack"] == daily["stack"]
    assert any("off" in n for n in offed["notes"])
    assert canonical_combat("格闘LoRAオン（ハイメモリ専用）") == "on"
    assert canonical_combat("オフ") == "off"
    assert not is_high_mem(vram_gb=40, ram_gb=12)
    assert is_high_mem(vram_gb=80, ram_gb=12)
    assert is_high_mem(vram_gb=40, ram_gb=80)
    allowed, note = combat_lora_allowed(unet=EROS_MAX_UNET, combat="on", high_mem=True)
    assert allowed and "High-Memory" in note
    denied, dnote = combat_lora_allowed(unet=EROS_MAX_UNET, combat="on", high_mem=False)
    assert not denied and "High-Memory only" in dnote
    ep = load_episode(KASUMI_DIR / "episode.json")
    fight = next(b for b in ep["beats"] if b["id"] == "03-shove")
    prompt = build_beat_prompt(ep, fight, trigger=merge_trigger("DY", fight))
    g = build_episode_graph(
        source="still",
        first_image="01.jpg",
        prompt=prompt,
        unet="fl2va.safetensors",
        preset=stacked,
        width=1024,
        height=576,
        duration_s=10,
        seed=1,
        filename_prefix="video/x",
    )
    assert g["2c"]["inputs"]["lora_name"] == LORA_FILES["combat"]
    assert g["23"]["inputs"]["model"] == ["2c", 0]
    assert g["22"]["inputs"]["sampler_name"] == COMBAT_SAMPLER
    assert g["23"]["inputs"]["scheduler"] == COMBAT_SCHEDULER
    assert g["23"]["inputs"]["steps"] == COMBAT_STEPS
    last_g = build_episode_graph(
        source="chain",
        first_image="from.jpg",
        last_image="03.jpg",
        prompt=prompt,
        unet="fl2va.safetensors",
        preset=stacked,
        width=1024,
        height=576,
        duration_s=10,
        seed=1,
        filename_prefix="video/x",
    )
    assert last_g["101"]["inputs"]["image"] == "03.jpg"
    assert last_g["20"]["inputs"]["last_frame"] == ["101", 0]
    assert last_g["20"]["inputs"]["first_frame"] == ["100", 0]


def test_combat_steps_cap_and_author_override(tmp_path):
    ep = load_episode(KASUMI_DIR / "episode.json")
    ep["beats"][2]["steps"] = 20
    assert any("steps must be 4-16" in e for e in validate_episode(ep, root=KASUMI_DIR))
    ep = load_episode(KASUMI_DIR / "episode.json")
    ep["beats"][1]["steps"] = 12
    assert any("ui beat cannot have steps" in e for e in validate_episode(ep, root=KASUMI_DIR))
    ep = load_episode(KASUMI_DIR / "episode.json")
    ep["beats"][0]["still_as"] = "last"
    assert any("first beat cannot be still_as last" in e for e in validate_episode(ep, root=KASUMI_DIR))
    ep = load_episode(KASUMI_DIR / "episode.json")
    ep["beats"][2]["trim"] = {"start": 2.0, "seconds": 5.0}
    assert any("trim must include the last frame" in e for e in validate_episode(ep, root=KASUMI_DIR))
    daily = {"name": "daily", "stack": [("larry.safetensors", 1.0)], "steps": 8, "trigger": "DY", "notes": []}
    loras = tmp_path / "loras"
    loras.mkdir()
    (loras / LORA_FILES["combat"]).write_bytes(b"x")
    authored = {"extra_loras": ["combat"], "steps": 16, "sampler": "res_multistep", "scheduler": "simple"}
    stacked = apply_extra_loras(daily, authored, loras)
    assert stacked["steps"] == 16 and stacked["sampler"] == "res_multistep" and stacked["scheduler"] == "simple"


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
    assert g["22"]["inputs"]["sampler_name"] == "euler"
    assert g["23"]["inputs"]["scheduler"] == "simple"
    assert "first_frame" in g["20"]["inputs"] and "last_frame" not in g["20"]["inputs"]
    t2v = build_episode_graph(source="t2v", first_image=None, prompt=build_beat_prompt(ep, dict(ep["beats"][0], source="t2v")), unet="fl2va.safetensors", preset=preset, width=1024, height=576, duration_s=10, seed=1, filename_prefix="video/t")
    assert not any(n.get("class_type") == "LoadImage" for n in t2v.values())
    with pytest.raises(EpisodeError):
        build_episode_graph(source="still", first_image=None, prompt=prompt, unet="u", preset=preset, width=1024, height=576, duration_s=10, seed=1, filename_prefix="x")
    bare = apply_unet_preset_rules(resolve_preset("balance", None), EROS_MAX_UNET)
    assert bare["stack"] == []
    t2v_bare = build_episode_graph(
        source="t2v",
        first_image=None,
        prompt=build_beat_prompt(ep, dict(ep["beats"][0], source="t2v")),
        unet=EROS_MAX_UNET,
        preset=bare,
        width=1024,
        height=576,
        duration_s=10,
        seed=1,
        filename_prefix="video/bare",
    )
    assert "2" not in t2v_bare
    assert t2v_bare["1"]["inputs"]["unet_name"] == EROS_MAX_UNET
    assert t2v_bare["22"]["inputs"]["sampler_name"] == "euler"
    assert t2v_bare["23"]["inputs"]["steps"] == 8
    assert t2v_bare["23"]["inputs"]["scheduler"] == "simple"


def test_render_beat_keeps_canvas_and_shortens_on_oom(tmp_path):
    comfy = tmp_path / "ComfyUI"
    (comfy / "output" / "video").mkdir(parents=True)
    (comfy / "models" / "diffusion_models").mkdir(parents=True)
    ep = bandai()
    prompt = build_beat_prompt(ep, ep["beats"][0])
    calls = []

    def poster(graph, port):
        calls.append((graph["20"]["inputs"]["width"], graph["20"]["inputs"]["height"], graph["20"]["inputs"]["length"]))
        if len(calls) < 3:
            return None, "HTTP 500: CUDA out of memory"
        return {"prompt_id": "p1"}, None

    def waiter(pid, port):
        (comfy / "output" / "video" / "h3_ep_x_00001.mp4").write_bytes(b"mp4")
        return True, {"outputs": {"29": {"videos": [{"filename": "h3_ep_x_00001.mp4", "subfolder": "video"}]}}}

    res = render_beat_comfy(source="still", first_image="a.jpg", prompt=prompt, comfy_dir=comfy, canvas=(1024, 576), durations=[10.0, 8.0, 6.0], preset=resolve_preset("fast", None), seed=1, filename_prefix="video/h3_ep_x", poster=poster, waiter=waiter)
    assert res["duration_s"] == 8.0 and res["canvas"] == "1024x576"
    assert [c[:2] for c in calls] == [(1024, 576), (1024, 576), (1024, 576)]
    assert calls[0][2] == calls[1][2] > calls[2][2]


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
    assert DEFAULT_BRANCH == "cursor/h3-kasumi-adult-0402"
    script = exec_script("bandai-district", preset="daily", fresh=True, branch="cursor/x", main_path=Path("/content/h3_episode_colab_main.py"))
    assert "os.environ['H3_EPISODE'] = 'bandai-district'" in script
    assert "H3_EPISODE_FRESH'] = '1'" in script
    assert "H3_EPISODE_CAMERA" in script
    assert "H3_EPISODE_CONNECT" in script
    assert "H3_EPISODE_END_CONNECT" in script
    assert "H3_EPISODE_COMBAT" in script
    assert "H3_EPISODE_STORY" in script
    assert "H3_EPISODE_INVITE_POSE" in script
    assert "H3_EPISODE_TOILET" in script
    assert "H3_EPISODE_GIN" in script
    assert "H3_EPISODE_TSUNO" in script
    assert "H3_EPISODE_APPEAR" in script
    assert "H3_EPISODE_SCENES" in script
    assert "raw.githubusercontent.com/fireworker011/Research/cursor/x" in script
    assert "colab/h3_episode.py" in script and "runpy.run_path" in script
    compile(script, "exec_script", "exec")
    adult = exec_script(
        "kasumi-late-desk-adult",
        preset="daily",
        fresh=False,
        branch=DEFAULT_BRANCH,
        main_path=Path("/content/h3_episode_colab_main.py"),
    )
    assert "os.environ['H3_EPISODE'] = 'kasumi-late-desk-adult'" in adult
    assert f"raw.githubusercontent.com/fireworker011/Research/{DEFAULT_BRANCH}" in adult
    compile(adult, "exec_script_adult", "exec")


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


def test_rei_escape_default_validates_complete_under_max():
    raw = load_episode(REI_ESCAPE_DIR / "episode.json")
    assert raw["slug"] == "futanari-rei-escape"
    assert raw["render"]["lane"] == "erotic"
    assert raw["render"]["combat"] == "off"
    assert raw["cards"].get("title") is True
    assert "fail" not in raw["cards"]
    assert not any(k.startswith("on_toilet") or k.startswith("on_accept") or k.startswith("invite_pose") for b in raw["beats"] for k in b)
    errs = validate_episode(raw)
    assert errs == []
    ep = prepare_episode(raw)
    assert len(ep["beats"]) <= MAX_BEATS
    ids = [b["id"] for b in ep["beats"]]
    assert ids[0] == "01-open-stroke"
    assert "03-mast" not in ids and "07-mast" not in ids
    assert "18-kiss" not in ids and "19-oral" not in ids
    assert "09-ta" in ids
    assert "13-tail" in ids
    assert "20-fours-in" in ids and "20-fours-out" in ids
    assert ep["beats"][-1]["hud"]["complete"] is True
    assert "fail" not in ep["cards"]
    assert all(b.get("hud", {}).get("mission_keyword") == "脱出" for b in ep["beats"])
    assert all("異形の体内から脱出" == b.get("hud", {}).get("mission") for b in ep["beats"])
    maw = next(b for b in ep["beats"] if b["id"] == "05-enemy1-maw")
    assert extra_lora_entries(maw) == [("mystic", 1.0)]
    assert "lies on her back" not in maw["action"]
    assert "lizard crawl" in maw["action"]
    tail = next(b for b in ep["beats"] if b["id"] == "13-tail")
    assert extra_lora_entries(tail) == [("mystic", 1.0)]
    for _, prompt, perr in beat_prompts(ep):
        assert perr == []
        low = prompt.lower()
        assert "blowjob" not in low and "fellatio" not in low
        assert "doggy" not in low and "missionary" not in low and "cowgirl" not in low
        assert "hud" not in low
    assert "Rei" not in json.dumps(raw["cards"])
    title_prompt_source = next(b for b in raw["beats"] if b["id"] == "01-open-stroke")
    assert "Rei" in title_prompt_source["action"]


def test_rei_escape_attack_prefix_stays_on_attack_slot():
    raw = load_episode(REI_ESCAPE_DIR / "episode.json")
    rei_prefix = "Rei initiates:"
    her_prefix = "The succubus initiates:"

    def later_ids(ep):
        return [
            b
            for b in ep["beats"]
            if str(b.get("id") or "").startswith(("18-", "19-", "20-", "21-"))
        ]

    default = prepare_episode(raw)
    attack = next(b for b in default["beats"] if b["id"] == "17-from-rei")
    assert rei_prefix in attack["action"]
    assert her_prefix not in attack["action"]
    for beat in later_ids(default):
        assert rei_prefix not in beat["action"], beat["id"]
        assert her_prefix not in beat["action"], beat["id"]
        assert "pounces" not in beat["action"], beat["id"]

    her = prepare_episode(raw, rei_attack_override="her")
    her_attack = next(b for b in her["beats"] if b["id"] == "17-from-her")
    assert her_prefix in her_attack["action"]
    assert rei_prefix not in her_attack["action"]
    fours = next(b for b in her["beats"] if b["id"] == "20-fours-in")
    assert her_prefix not in fours["action"]
    assert "pounces" not in fours["action"]
    orgasm = next(b for b in her["beats"] if b["id"] == "21-orgasm")
    assert her_prefix not in orgasm["action"]
    assert rei_prefix not in orgasm["action"]

    mixed = prepare_episode(
        raw,
        rei_attack_override="her",
        rei_kiss_override="on",
        rei_oral_override="her",
        rei_pose_override="straddle",
    )
    assert any(b["id"] == "17-from-her" for b in mixed["beats"])
    for beat in later_ids(mixed):
        assert her_prefix not in beat["action"], beat["id"]
        assert rei_prefix not in beat["action"], beat["id"]
        assert "pounces" not in beat["action"], beat["id"]


def test_rei_escape_options_filth_and_oral_lora():
    raw = load_episode(REI_ESCAPE_DIR / "episode.json")
    skip = prepare_episode(raw, rei_mast_override="skip")
    stand = prepare_episode(raw, rei_mast_override="stand")
    assert len(stand["beats"]) == len(skip["beats"]) + 4
    assert any(b["id"].endswith("mast-stand") for b in stand["beats"])
    tent = prepare_episode(raw, rei_toilet_override="tc")
    tc = next(b for b in tent["beats"] if b["id"] == "09-tc")
    assert extra_lora_entries(tc) == [("mystic", 1.0)]
    assert "tentacle" in tc["action"].lower()
    run_c = next(b for b in tent["beats"] if b["id"] == "10-run-c")
    assert "DIRTY-STATE" not in run_c["action"]
    assert "feces" not in run_c["action"].lower()
    seat = prepare_episode(raw, rei_toilet_override="ta")
    run_c_seat = next(b for b in seat["beats"] if b["id"] == "10-run-c")
    assert "DIRTY-STATE" not in run_c_seat["action"]
    mouth = prepare_episode(raw, rei_moth_override="mouth")
    moth = next(b for b in mouth["beats"] if b["id"] == "13-mouth")
    assert extra_lora_entries(moth) == [("blowjob", 0.8)]
    oral = prepare_episode(raw, rei_oral_override="her")
    her = next(b for b in oral["beats"] if b["id"] == "19-oral-her")
    assert extra_lora_entries(her) == [("blowjob", 0.8)]
    rei_mouth = prepare_episode(raw, rei_oral_override="rei")
    only_rei = next(b for b in rei_mouth["beats"] if b["id"] == "19-oral-rei")
    assert extra_lora_entries(only_rei) == []
    full = prepare_episode(
        raw,
        rei_mast_override="stand",
        rei_toilet_override="tc",
        rei_moth_override="mouth",
        rei_attack_override="her",
        rei_kiss_override="on",
        rei_oral_override="her",
        rei_pose_override="straddle",
    )
    assert len(full["beats"]) <= MAX_BEATS
    assert any(b["id"] == "18-kiss-on" for b in full["beats"])
    assert any(b["id"] == "20-straddle-ride" for b in full["beats"])
    assert validate_episode(full) == []
    kasumi = load_episode(KASUMI_ADULT_DIR / "episode.json")
    before = json.dumps(kasumi["beats"], ensure_ascii=False)
    after = apply_rei_escape_route(kasumi, mast="stand")
    assert json.dumps(after["beats"], ensure_ascii=False) == before


def test_rei_escape_beast_accept_invite_evade():
    raw = load_episode(REI_ESCAPE_DIR / "episode.json")
    accept = prepare_episode(raw, rei_beast_override="受け入れる")
    maw = next(b for b in accept["beats"] if b["id"] == "05-enemy1-maw")
    assert extra_lora_entries(maw) == [("mystic", 1.0)]
    assert "lizard crawl" in maw["action"]
    assert "lies on her back" not in maw["action"]
    invite = prepare_episode(raw, rei_beast_override="誘う")
    supine = next(b for b in invite["beats"] if b["id"] == "05-enemy1-invite")
    assert extra_lora_entries(supine) == [("mystic", 1.0)]
    assert "lies on her back" in supine["action"]
    assert "knees open" in supine["action"]
    assert "smiling" in supine["action"]
    assert "05-enemy1-maw" not in [b["id"] for b in invite["beats"]]
    evade = prepare_episode(raw, rei_beast_override="回避")
    ids = [b["id"] for b in evade["beats"]]
    assert "05-enemy1-maw" not in ids
    assert "05-enemy1-invite" not in ids
    assert "04-enemy1" in ids and "06-fade-run-b" in ids
    assert len(evade["beats"]) == len(accept["beats"]) - 1
    # The run after enemy1 must not claim a climax that the chosen branch skipped.
    for ep, climaxed in ((accept, True), (invite, True), (evade, False)):
        run_b = next(b for b in ep["beats"] if b["id"] == "06-fade-run-b")
        assert ("after ejaculation" in run_b["action"]) is climaxed
        assert "completely fades out of frame" in run_b["action"]
    assert "misses" in next(b for b in evade["beats"] if b["id"] == "06-fade-run-b")["action"]
    for ep in (accept, invite, evade):
        assert validate_episode(ep) == []
        for _, prompt, perr in beat_prompts(ep):
            assert perr == []
            low = prompt.lower()
            assert "blowjob" not in low and "fellatio" not in low


def test_chain_keeps_leaving_bodies_in_frame_so_they_can_fade():
    """Shrink-only I2V keeps the leftover body and fades it. A new body is T2V."""
    for slug in ("kasumi-late-desk-adult", "hospital-exit-adult", "bandai-district", "futanari-rei-escape"):
        ep = load_episode(ROOT / "minimaxh3" / "episodes" / slug / "episode.json")
        out = prepare_episode(ep, connect_override="chain")
        prev: set[str] = set()
        for beat in out["beats"]:
            if is_ui_beat(beat) or not beat_renders(beat):
                continue
            cast = {str(c) for c in (beat.get("cast") or [])}
            fade = {str(c) for c in (beat.get("fade_cast") or [])}
            remaining = cast - fade
            spot = str(beat.get("id") or "").endswith("-spot")
            if beat_source(beat) == "chain" and not spot:
                assert not prev - cast, f"{slug} {beat['id']} chains off missing {sorted(prev - cast)}"
            prev = remaining
    kasumi = prepare_episode(
        load_episode(KASUMI_ADULT_DIR / "episode.json"), connect_override="chain"
    )
    walk = next(b for b in kasumi["beats"] if b["id"] == "08-walk")
    # Kuroki is new; I2V cannot invent her from Aoki's last frame.
    assert beat_source(walk) == "t2v"
    joined = next(b for b in kasumi["beats"] if b["id"] == "07-creampie")
    assert beat_source(joined) == "chain"
    rei = prepare_episode(
        load_episode(REI_ESCAPE_DIR / "episode.json"),
        connect_override="chain",
        rei_beast_override="誘う",
    )
    six = next(b for b in rei["beats"] if b["id"] == "06-fade-run-b")
    assert beat_source(six) == "chain"
    assert six.get("fade_cast") == ["beast"]
    hosp = prepare_episode(
        load_episode(HOSPITAL_DIR / "episode.json"), connect_override="chain"
    )
    doggy_walk = next(b for b in hosp["beats"] if b["id"] == "06-doggy-walk")
    assert beat_source(doggy_walk) == "chain"
    assert doggy_walk.get("fade_cast") == ["rei"]


def test_rei_escape_pose_never_adds_kiss_or_oral_back():
    """体位ドロップダウンはラベルどおりの動きだけ。キスは18、フェラ/クンニは19が持つ。"""
    raw = load_episode(REI_ESCAPE_DIR / "episode.json")
    for pose in ("fours", "wall", "straddle", "supine"):
        off = prepare_episode(raw, rei_pose_override=pose, rei_kiss_override="off", rei_oral_override="skip")
        for beat in off["beats"]:
            if not str(beat.get("id") or "").startswith("20-"):
                continue
            # POSE_BAN legitimately says "do not pack kiss-to-creampie into one clip".
            action = beat["action"].replace("Do not pack kiss-to-creampie into one clip.", "")
            assert "kiss" not in action, beat["id"]
            assert "lips part over" not in action, beat["id"]
            assert extra_lora_entries(beat) == [], beat["id"]
    straddle = prepare_episode(raw, rei_pose_override="straddle")
    ids = [b["id"] for b in straddle["beats"] if str(b.get("id") or "").startswith("20-")]
    assert ids == ["20-straddle-ride", "20-straddle-out"]


def test_rei_escape_clip_failures_are_rewritten():
    """Fixes from the first speed run: nude, rest face, hypotoco maw, planted sex, meat toilet, I2V fade."""
    raw = load_episode(REI_ESCAPE_DIR / "episode.json")
    assert raw["world"].get("bare_set") is True
    assert "FULLY NUDE" in raw["cast"]["rei"]["lock"]
    assert "tongue fully inside" in raw["cast"]["rei"]["lock"]
    assert "garment" not in raw["cast"]["rei"]["lock"]
    assert "PUCKERED" in raw["cast"]["beast"]["lock"]
    chained = prepare_episode(
        raw,
        connect_override="chain",
        rei_beast_override="誘う",
        rei_toilet_override="触手",
        rei_pose_override="壁に手",
        rei_kiss_override="on",
        rei_oral_override="her",
    )
    blob = json.dumps(chained, ensure_ascii=False).lower()
    assert "garment" not in blob
    assert "feces" not in blob and "shit" not in blob
    invite = next(b for b in chained["beats"] if b["id"] == "05-enemy1-invite")
    assert invite.get("loco") == "planted"
    assert "PUCKERED" in invite["action"] or "puckered" in invite["action"].lower() or "hypotoco" in invite["action"].lower()
    assert "camera iris" not in invite["action"].lower()
    six = next(b for b in chained["beats"] if b["id"] == "06-fade-run-b")
    assert beat_source(six) == "chain"
    assert six.get("fade_cast") == ["beast"]
    run = next(b for b in chained["beats"] if b["id"] == "02-run-a")
    assert run.get("loco") == "run"
    assert "tongue fully inside" in run["action"]
    moth = next(b for b in chained["beats"] if b["id"] == "13-tail")
    assert moth.get("loco") == "planted"
    assert "STANDING STILL" in moth["action"]
    wall = next(b for b in chained["beats"] if b["id"] == "20-wall-in")
    assert "INSIDE the vagina" in wall["action"]
    assert "PALMS FLAT" in wall["action"]
    assert "far side of a thigh" in wall["action"]
    prompt = build_beat_prompt(chained, wall)
    assert PLANTED_CLAUSE in prompt
    assert "Brisk walking stride" not in prompt
    assert "nothing man-made attached" in prompt
    tc = next(b for b in chained["beats"] if b["id"] == "09-tc")
    assert "tentacle" in tc["action"].lower()
    assert extra_lora_entries(tc) == [("mystic", 1.0)]


def test_rei_escape_notebook_is_isolated():
    nb = json.loads((ROOT / "minimax_h3_rei_escape_bot.ipynb").read_text(encoding="utf-8"))
    code = [c for c in nb["cells"] if c["cell_type"] == "code"]
    assert len(code) == 1
    src = "".join(code[0]["source"])
    assert 'EPISODE = "futanari-rei-escape"' in src
    assert "hospital-exit-adult" not in src
    assert "APPEAR_MIKI" not in src
    assert "H3_EPISODE_CONNECT" in src
    assert "H3_EPISODE_END_CONNECT" not in src
    assert "END_CONNECT" not in src
    assert "1番のつなぎに従う" not in src
    assert "H3_EPISODE_REI_MAST" in src
    assert "H3_EPISODE_REI_BEAST" in src
    assert "H3_EPISODE_REI_POSE" in src
    assert "サキュバスがフェラ" in src
    assert "レイがクンニ" in src
    assert "ベロチューする" in src
    assert "敵1・誘う" in src
    assert "トイレ・肉壁の触手がじゅぼ" in src
    assert "全身に塗る" not in src
    assert 'BRANCH = "cursor/futanari-rei-escape-34e4"' in src
    assert "h3_episode_colab_main" in src
    assert "if rc:" in src
    assert 'raise SystemExit(rc)' in src
    md = "".join("".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "markdown")
    assert "futanari-rei-escape" in md
    assert "cursor/futanari-rei-escape-34e4" in md
    assert "シーン終わりのつなぎ" not in md
    assert "フェラ／クンニ" in md
    assert "口 — 唇と舌の軌道" not in md
    assert json.loads((ROOT / "minimaxh3" / "minimax_h3_rei_escape_bot.ipynb").read_text(encoding="utf-8")) == nb


def test_rei_escape_connect_is_one_dropdown_and_cut_locks():
    raw = load_episode(REI_ESCAPE_DIR / "episode.json")
    locked = {"04-enemy1", "08-toilet", "12-moth", "16-succ"}
    for beat in raw["beats"]:
        if beat["id"] in locked:
            assert beat.get("connect") == "t2v", beat["id"]
        else:
            assert beat.get("connect") not in ("t2v", "cut", "off"), beat["id"]
    chained = prepare_episode(raw, connect_override="前の最終フレームから続ける")
    by_id = {b["id"]: b for b in chained["beats"]}
    assert beat_source(by_id["01-open-stroke"]) == "t2v"
    assert beat_source(by_id["02-run-a"]) == "chain"
    assert beat_source(by_id["04-enemy1"]) == "t2v"
    assert beat_source(by_id["05-enemy1-maw"]) == "chain"
    assert beat_source(by_id["06-fade-run-b"]) == "chain"
    assert by_id["06-fade-run-b"].get("fade_cast") == ["beast"]
    assert beat_source(by_id["17-from-rei"]) == "chain"
    assert beat_source(by_id["20-fours-in"]) == "chain"
    assert beat_source(by_id["21-orgasm"]) == "chain"
    assert beat_source(by_id["22-succ-fade"]) == "chain"
    assert by_id["22-succ-fade"].get("fade_cast") == ["succubus"]
    cuts = prepare_episode(raw, connect_override="カット")
    assert all(beat_source(b) == "t2v" for b in cuts["beats"])

