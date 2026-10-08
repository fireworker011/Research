import copy
import hashlib
import json
import os
import re
import shutil
import signal
import sys
import threading
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "minimaxh3"))
sys.path.insert(0, str(ROOT / "minimaxh3" / "grokbot"))

from h3_episode import (  # noqa: E402
    ANIME2REAL_TRIGGER,
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
    LOWER_TO_FLOOR_CLAUSE,
    WALL_SET_CLAUSE,
    HIPS_BACK_ONCE_CLAUSE,
    TOILET_SIT_CLAUSE,
    SIDE_LIE_JOIN_CLAUSE,
    SIDE_LIE_SETTLE_CLAUSE,
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
    beat_loco,
    beat_prompts,
    beat_props,
    beat_clip_seconds,
    beat_content_sig,
    beat_needs_previous,
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
    ensure_episode_loras,
    fetch_text,
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
    render_start_index,
    resolve_preset,
    resolve_unet,
    WeightsReady,
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
    RIDE_FOOT_CHOICES,
    INVITE_POSE_OVERLAY_KEYS,
    SCENE_ACTION_MODES,
    STORY_MODES,
    TOILET_MODES,
    TSUNO_MODES,
    TSUNO_OVERLAY_KEYS,
    canonical_episode,
    canonical_toilet,
    describe_run,
    form_readme,
    parse_scenes,
    ui_choices,
    ui_default,
)
from h3_i2v_job import default_job, ensure_drive_tree, next_ready_job, save_job  # noqa: E402
from h3_i2v_runtime import comfy_launch_cmd, comfy_vram_flag, is_erotic_unet_name, pick_stock_fl2va, stop_comfy, wait_prompt  # noqa: E402
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
        assert "hips moving" in low or "hands stay at the hips" in action or "hips hold still" in action
    for tok in _SEX_EXTRA_MOTION:
        pat = re.compile(rf"\b{re.escape(tok)}\b")
        assert not pat.search(low), (beat["id"], tok)
        assert not pat.search(action), (beat["id"], tok)


def bandai() -> dict:
    return load_episode(EP_DIR / "episode.json")


def short() -> dict:
    return load_episode(SHORT_DIR / "episode.json")


# ---------------------------------------------------------------- sync / files

def test_wait_prompt_keeps_polling_when_comfy_is_busy(monkeypatch):
    import h3_i2v_runtime

    calls = {"n": 0}

    class Resp:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return json.dumps({"pid": {"status": {"completed": True}, "outputs": {"1": {}}}}).encode()

    def fake_urlopen(url, timeout=None):
        calls["n"] += 1
        if calls["n"] == 1:
            raise TimeoutError("timed out")
        return Resp()

    monkeypatch.setattr(h3_i2v_runtime.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(h3_i2v_runtime.time, "sleep", lambda _s: None)
    ok, payload = wait_prompt("pid", port=8188, timeout=30)
    assert ok is True
    assert payload["status"]["completed"] is True
    assert calls["n"] == 2


def test_colab_and_minimaxh3_copies_in_sync():
    for name in ("h3_hud.py", "h3_episode.py", "h3_episode_packs.py", "h3_episode_colab_main.py"):
        a = (ROOT / "colab" / name).read_text(encoding="utf-8")
        b = (ROOT / "minimaxh3" / name).read_text(encoding="utf-8")
        assert a == b, f"{name} differs between colab/ and minimaxh3/ (copy after editing)"
    runtime_a = (ROOT / "colab" / "h3_i2v_runtime.py").read_text(encoding="utf-8")
    runtime_b = (ROOT / "minimaxh3" / "h3_i2v_runtime.py").read_text(encoding="utf-8")
    assert runtime_a == runtime_b, "h3_i2v_runtime.py differs between colab/ and minimaxh3/"


def test_cpu_runtime_stops_only_when_a_rendered_lora_is_missing(tmp_path, monkeypatch):
    import h3_episode as mod

    monkeypatch.setattr(mod, "preflight", lambda *_a, **_k: [])
    monkeypatch.setattr(mod, "ensure_episode_checkpoint", lambda *_a, **_k: ["checkpoint ready x"])
    monkeypatch.setattr(mod, "download_base_weights", lambda *_a, **_k: ["skip existing unet"])
    monkeypatch.setattr(mod, "ensure_comfy", lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("comfy")))
    monkeypatch.setenv("H3_WEIGHTS_ONLY", "1")
    raw = load_episode(HOSPITAL_DIR / "episode.json")
    prepared = prepare_episode(raw)
    needed = next(iter(mod._rendered_lora_filenames(prepared)))
    monkeypatch.setattr(mod, "ensure_episode_loras", lambda *_a, **_k: [f"fetch failed {needed}"])
    with pytest.raises(EpisodeError, match="LoRA の取得が止まりました"):
        run_episode(raw, tmp_path, models_root=tmp_path / "models", dry_run=False)
    monkeypatch.setattr(
        mod,
        "ensure_episode_loras",
        lambda *_a, **_k: [
            "fetch failed slime_girls-MMH3-v1.0.safetensors",
            "skip page furry-enhancer-video.safetensors",
        ],
    )
    with pytest.raises(WeightsReady):
        run_episode(raw, tmp_path, models_root=tmp_path / "models", dry_run=False)


def test_cpu_runtime_downloads_weights_and_does_not_start_comfy(tmp_path, monkeypatch):
    import h3_episode as mod

    calls: list[str] = []
    monkeypatch.setattr(mod, "preflight", lambda *_a, **_k: [])
    monkeypatch.setattr(mod, "ensure_episode_loras", lambda *_a, **_k: calls.append("lora") or ["skip existing a.safetensors"])
    monkeypatch.setattr(mod, "ensure_episode_checkpoint", lambda *_a, **_k: calls.append("ckpt") or ["checkpoint ready x"])
    monkeypatch.setattr(mod, "download_base_weights", lambda *_a, **_k: calls.append("base") or ["skip existing unet"])
    monkeypatch.setattr(mod, "ensure_comfy", lambda *_a, **_k: calls.append("comfy"))
    monkeypatch.setattr(mod, "start_comfy", lambda *_a, **_k: calls.append("start"))
    monkeypatch.setenv("H3_WEIGHTS_ONLY", "1")
    raw = load_episode(HOSPITAL_DIR / "episode.json")
    with pytest.raises(WeightsReady):
        run_episode(raw, tmp_path, models_root=tmp_path / "models", dry_run=False)
    assert calls == ["lora", "ckpt", "base"]


def test_gpu_run_downloads_before_comfy_starts(tmp_path, monkeypatch):
    import h3_episode as mod

    calls: list[str] = []
    monkeypatch.setattr(mod, "preflight", lambda *_a, **_k: [])
    monkeypatch.setattr(mod, "cuda_available", lambda: True)
    monkeypatch.setattr(mod, "ensure_episode_loras", lambda *_a, **_k: calls.append("lora") or [])
    monkeypatch.setattr(mod, "ensure_episode_checkpoint", lambda *_a, **_k: calls.append("ckpt") or [])
    monkeypatch.setattr(mod, "download_base_weights", lambda *_a, **_k: calls.append("base") or [])
    monkeypatch.setattr(mod, "ensure_comfy", lambda *_a, **_k: calls.append("comfy"))
    monkeypatch.setattr(mod, "comfy_up", lambda *_a, **_k: False)
    monkeypatch.setattr(mod, "stage_erotic_unet", lambda *_a, **_k: calls.append("stage") or "unet.safetensors")

    def _start(*_a, **_k):
        calls.append("start")
        raise RuntimeError("stop after start")

    monkeypatch.setattr(mod, "start_comfy", _start)
    monkeypatch.setenv("H3_WEIGHTS_ONLY", "0")
    raw = load_episode(HOSPITAL_DIR / "episode.json")
    with pytest.raises(RuntimeError, match="stop after start"):
        run_episode(raw, tmp_path, models_root=tmp_path / "models", dry_run=False)
    assert calls.index("lora") < calls.index("ckpt") < calls.index("base")
    assert calls.index("base") < calls.index("comfy") < calls.index("start")


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
    assert 'BRANCH = "cursor/human-cast-anatomy-d736"' in src
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
    assert "MOSAIC" not in src
    assert "H3_EPISODE_MOSAIC" not in src
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
    assert "H3_EPISODE_DOG" in src
    assert "H3_EPISODE_SPECIES" in src
    assert "H3_EPISODE_APPEAR" in src
    assert "H3_EPISODE_AYA_HAIR" in src
    assert 'AYA_HAIR = "今のまま（迷ったらこれ）"' in src
    assert 'AYA_HAIR_COLOR = "今のまま（迷ったらこれ）"' in src
    assert 'AYA_FACE = "今のまま（迷ったらこれ）"' in src
    assert 'AYA_BUST = "今のまま（迷ったらこれ）"' in src
    assert 'AYA_BUTT = "今のまま（迷ったらこれ）"' in src
    assert 'AYA_BUILD = "今のまま（迷ったらこれ）"' in src
    assert 'AYA_HEIGHT = "今のまま（迷ったらこれ）"' in src
    assert 'AYA_DIRT = "今のまま（迷ったらこれ）"' in src
    assert 'AYA_SWEAT = "今のまま（迷ったらこれ）"' in src
    assert 'AYA_CLOTHES = "今のまま（迷ったらこれ）"' in src
    assert 'AYA_SHAFT = "今のまま（迷ったらこれ）"' in src
    for _name in ("AYA_HAIR", "AYA_HAIR_COLOR", "AYA_FACE", "AYA_BUST", "AYA_BUTT", "AYA_BUILD", "AYA_HEIGHT", "AYA_DIRT", "AYA_SWEAT", "AYA_CLOTHES", "AYA_SHAFT"):
        _line = next(line for line in src.splitlines() if line.startswith(f"{_name} = "))
        assert '{type:"string"}' not in _line
    assert "ボブ" in src and "銀髪" in src and "丸顔" in src and "細め" in src
    assert 'LOOK_MIKI = "今のまま（迷ったらこれ）"' in src
    assert "LOOK_REI" in src and "LOOK_KANA" in src and "LOOK_SHINO" in src
    assert "LOOK_GIN" in src and "LOOK_TSUNO" in src
    assert 'FREE_MIKI = ""' in src and 'FREE_TSUNO = ""' in src
    assert "H3_EPISODE_SCENES" in src
    assert "SCENE_MIKI" in src and "SCENE_SHINO" in src
    assert "canonical_episode" in src
    assert 'STORY = "○受け入れる（生存・完了・迷ったらこれ）"' in src
    assert "□誘う（淫欲・失敗）" in src
    assert "△戦って負ける（敗北H・失敗・ハイメモリ）" in src
    assert 'INVITE_POSE = "四つん這い股広げ（迷ったらこれ）"' in src
    assert "騎乗・足を揃えて立ってから下ろす" in src
    assert "騎乗・最初から膝を曲げて下ろす" in src
    assert 'RIDE_BENT = "なし"' in src
    assert 'RIDE_COLUMN = "なし"' in src
    assert "H3_EPISODE_RIDE_BENT" in src
    assert "H3_EPISODE_RIDE_COLUMN" in src
    for name in ("みき", "れい", "かな", "しの", "ギン", "😈"):
        assert name in src
    assert "壁立ちバック" in src
    assert "フルネルソンアナル" in src
    assert "ベロチュー→じゅぼ→騎乗位" not in src
    assert 'TOILET = "トイレに行かない（迷ったらこれ）"' in src
    assert 'GIN = "灰色・出ない（迷ったらこれ）"' in src
    assert 'TSUNO = "角・出ない（迷ったらこれ）"' in src
    assert 'DOG = "犬・出ない（迷ったらこれ）"' in src
    assert 'SPECIES = "異種・出ない（迷ったらこれ）"' in src
    assert "APPEAR_MIKI" in src and "APPEAR_SHINO" in src
    assert 'EPISODE = "kasumi-late-desk"' not in src
    md = "".join("".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "markdown")
    assert "619ea878c0bf2491f6cedd625329c5b3" not in md
    assert "CivitaiのAPIキー" in md
    assert "cursor/human-cast-anatomy-d736" in md
    assert "kasumi-late-desk-adult" in md
    assert "10Eros Max は Drive" in md
    assert "10Eros_Max_h3_TURBO-hybrid_beta5_int8.safetensors" in md
    assert "迷ったら" in md
    assert "5. 構成" in md
    assert "6. 誘うポーズ" in md
    assert "7. トイレ" in md
    assert 'os.environ["H3_WEIGHTS_ONLY"] = "1"' in src
    assert "GPU がオフです。ランタイムのタイプを A100 にしてやり直してください。" not in src
    assert "チェックポイントと LoRA を Drive に取ります" in src
    assert "8. 灰色" in md
    assert "9. 角" in md
    assert "10. 犬" in md
    assert "11. 異種" in md
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
    assert 'RUNTIME_AFTER = "そのまま（迷ったらこれ）"' in src
    assert '["そのまま（迷ったらこれ）", "切る"]' in src
    assert 'os.environ["H3_KEEP_RUNTIME"] = "1"' in src
    assert 'os.environ["H3_UNASSIGN_RUNTIME"] = "1"' in src
    assert "ランタイムはそのまま" in src
    assert "ランタイムを切ります" in src
    assert "maybe_unassign()" in src
    assert src.index('if os.environ.get("H3_WEIGHTS_ONLY") == "1"') < src.index("maybe_unassign()")
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


def test_stop_comfy_signals_the_listener(monkeypatch):
    calls = []
    monkeypatch.setattr(
        "h3_i2v_runtime.comfy_up",
        lambda port=8188: calls.append(port) or len(calls) == 1,
    )
    monkeypatch.setattr("h3_i2v_runtime._listener_pids", lambda _port: [4242])
    killed = []
    monkeypatch.setattr("h3_i2v_runtime.os.kill", lambda pid, sig: killed.append((pid, sig)))
    monkeypatch.setattr("h3_i2v_runtime.time.sleep", lambda _s: None)
    stop_comfy(8188)
    assert killed and killed[0][0] == 4242
    assert killed[0][1] == signal.SIGTERM


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
    if (
        "on either side" in blob
        and "ribs" in blob
        and "straight down" in blob
        and "hold still joined at the base" in blob
    ):
        return
    riding = (
        "sits on" in blob
        or "squats over" in blob
        or ("rock down" in blob and "hold still" in blob)
    )
    tentacle = "tentacle" in blob
    supine = ("stays on her back" in blob or "on her back" in blob) and not riding
    if tentacle:
        assert "hold still joined" in blob
        assert "keep thrusting" not in blob
        _assert_named_hip_motion(action, prompt)
        return
    if riding:
        assert "rock down" in blob or "lower onto" in blob or "lowers her hips" in blob or "squats over" in blob
        assert "hold still" in blob
        assert "rock up" not in blob
        _assert_named_hip_motion(action, prompt)
        return
    if supine:
        if "one continuous press" not in blob:
            assert "thrust" in blob
        assert "rock up" not in blob
        assert "pelvis stays down" in blob or "pelvis stay" in blob
        _assert_named_hip_motion(action, prompt)
        return
    if "one continuous press" not in blob:
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
    assert raw["cast"]["aya"]["age"] == 21 and "C-cup" in raw["cast"]["aya"]["lock"]
    assert "A-cup" not in raw["cast"]["aya"]["lock"] and "ponytail" not in raw["cast"]["aya"]["lock"]
    assert "long straight dark hair past the shoulders" in raw["cast"]["aya"]["lock"]
    assert "small dark mole on the left cheek" in raw["cast"]["aya"]["lock"]
    assert "slender thin body" in raw["cast"]["aya"]["lock"]
    assert "hairless pussy" in raw["cast"]["aya"]["lock"]
    assert "female body" in raw["cast"]["aya"]["lock"]
    assert "no penis" not in raw["cast"]["aya"]["lock"]
    assert "never futanari" not in raw["cast"]["aya"]["lock"]
    assert "no penis" not in raw["cast"]["aya"]["looks"]["white_upper"]
    assert "never futanari" not in raw["cast"]["aya"]["looks"]["white_upper"]
    assert "hospital dirt" in raw["cast"]["aya"]["lock"] and "sweat" in raw["cast"]["aya"]["lock"]
    assert "visible sweat beads" in raw["cast"]["aya"]["lock"]
    assert "grimy brown hospital dirt" in raw["cast"]["aya"]["lock"]
    assert "extremely tall" not in raw["world"]["lock"]
    assert "nobody is giant" in raw["world"]["lock"]
    assert "24cm" in raw["cast"]["miki"]["lock"] and "clear futanari" in raw["cast"]["miki"]["lock"]
    assert "no penis" not in raw["cast"]["miki"]["lock"]
    assert "purple" in raw["cast"]["miki"]["lock"]
    assert "lacerations" in raw["cast"]["miki"]["lock"] and "hollow empty dark eye sockets" in raw["cast"]["miki"]["lock"]
    assert "same vivid purple" in raw["cast"]["miki"]["lock"]
    assert "not pale-tan flesh" in raw["cast"]["miki"]["lock"]
    assert "pale-tan skin" not in raw["cast"]["miki"]["lock"]
    assert "groin" in raw["cast"]["miki"]["lock"] and "rotting" in raw["cast"]["miki"]["lock"]
    assert "24cm shaft" in raw["cast"]["miki"]["lock"]
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
    assert "cracked" in raw["cast"]["tsuno"]["lock"]
    assert "two small dark horns stand at the hairline" in raw["cast"]["tsuno"]["lock"].lower()
    assert "horned mask" not in raw["cast"]["tsuno"]["lock"]
    assert "clawed demon" in raw["cast"]["tsuno"]["lock"] or "decaying clawed" in raw["cast"]["tsuno"]["lock"]
    assert "one large single eye" in raw["cast"]["tsuno"]["lock"]
    assert "not two eyes" not in raw["cast"]["tsuno"]["lock"]
    assert "exactly four long fingers" in raw["cast"]["tsuno"]["lock"]
    assert "both eyes" not in raw["cast"]["tsuno"]["lock"].lower()
    assert raw["cast"]["shino"]["age"] == 29
    assert "35cm" in raw["cast"]["shino"]["lock"] and "elongated" in raw["cast"]["shino"]["lock"]
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
    assert expected_duration(ep) == pytest.approx(140.1, abs=2.0)
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
    assert "tongues intertwine" in miki_walk["action"].lower()
    assert "miki steps out" in miki_walk["action"].lower()
    assert extra_lora_entries(miki_walk)[0] == ("kiss", 0.5)
    assert canonical_toilet("トイレ・ディルド") == "finger"
    assert canonical_toilet("アナル指") == canonical_toilet("トイレ・アナル指") == "anal_finger"
    for mode in ("小便", "オナニー", "触手", "トイレ・ディルド", "和式"):
        solo = prepare_episode(raw, story_override="受け入れる", toilet_override=mode, appear_override={"miki": True, "rei": False, "kana": False, "shino": False})
        out = next(b for b in solo["beats"] if b["id"] == "04-toilet-out")
        assert "tongues intertwine" not in out["action"].lower(), mode
    dog = prepare_episode(raw, story_override="受け入れる", dog_override="受け入れる", appear_override={"miki": True, "rei": False, "kana": False, "shino": False})
    dog_walk = next(b for b in dog["beats"] if b["id"] == "04-dog-walk")
    assert "tongues intertwine" not in dog_walk["action"].lower()
    assert extra_keys(miki) == ["blowjob", "mystic"]
    assert miki.get("trigger") == "bl0w_j0b"
    assert miki_prompt.startswith("bl0w_j0b")
    assert "glans stays inside the mouth" in miki_prompt.lower()
    assert "24cm" in miki_prompt.lower()
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
    assert "tongues intertwine" in walk["action"].lower()
    assert "rei steps out" in walk["action"].lower()
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
    assert "35cm" in shino_meet["action"].lower()
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
    assert "35cm" in exit_prompt.lower()
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
    assert expected_duration(ep) == pytest.approx(269.0, abs=2.0)
    assert ep["beats"][-1]["hud"]["complete"] is False
    assert ep["cards"]["fail"]["reason"] == "淫欲に呑まれた"
    for bid in ("02-ui-miki", "05-ui-rei", "08-ui-kana", "11-ui-shino"):
        ui = next(b for b in ep["beats"] if b["id"] == bid)
        assert ui["menu"]["selected"] == 2
        assert ui["hud"]["hint"] == "□ 誘う"
    doggy = next(b for b in ep["beats"] if b["id"] == "06-doggy-in")
    _assert_insertion_direction(doggy["action"], build_beat_prompt(ep, doggy))
    assert "chest and cheek stay down" in doggy["action"].lower()
    assert "between the open thighs" in doggy["action"].lower()
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
    assert "chest and cheek stay down" in seat["action"].lower()
    assert "erect 35cm" in seat["action"].lower()
    assert "between the open thighs" in peak["action"].lower()
    assert "overflows" in peak["action"].lower()
    assert "pull back" not in peak["action"].lower()
    assert "rolls onto her back" in drop["action"].lower()
    assert "inner thighs rest on the linoleum" in drop["action"].lower()
    assert "heels sit right beside the buttocks" in drop["action"].lower()
    assert "overflows from the anus" in drop["action"].lower()
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
    assert "shino's hips hold still" in sex["action"].lower()
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
    assert "hangs directly above the glans" in six_blob
    six = next(b for b in ride["beats"] if b["id"] == "06-doggy")
    assert "slide down to the base" in six["action"].lower()
    assert "kneels" in six["action"].lower()
    ride_sit = next(b for b in ride["beats"] if b["id"] == "06-doggy-ride")
    _assert_insertion_direction(ride_sit["action"], build_beat_prompt(ride, ride_sit))
    assert extra_keys(six) == ["blowjob", "mystic"]
    assert six.get("trigger") == "bl0w_j0b"
    assert "soles plant" not in six["action"].lower()
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
    assert "left nipple" in four["action"].lower()
    assert "right nipple" in four["action"].lower()
    assert "open mouth" in four["action"].lower()
    assert "hairless pussy" in four["action"].lower()
    assert "corpse" not in four_prompt.lower()
    assert four["trim"]["seconds"] == 10.0
    assert beat_clip_seconds(toilet, four) == 10.0
    assert "already sits" in four["action"].lower()
    assert "keep thrusting" not in four["action"].lower()
    assert "hold still joined at those four places" in four["action"].lower()
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
    assert "24cm" in miki_ride
    assert "kneels" in miki_ride
    assert "slide down to the base" in miki_ride
    assert "hangs directly above the glans" in miki_ride
    assert "hold still joined at the base" in miki_ride
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
    stand_in = next(b for b in stand["beats"] if b["id"] == "06-doggy-in")
    assert "right palm stay on the grey wall" in stand_in["action"].lower()
    assert "between the calves" in stand_in["action"].lower()
    assert "hold still joined at the base" in stand_in["action"].lower()
    _assert_insertion_direction(stand_in["action"], build_beat_prompt(stand, stand_in))
    assert "pussy" in stand_in["action"].lower()
    for bid, who in (("03-kiss", "miki"), ("06-doggy", "rei"), ("09-join", "kana"), ("12-exit", "shino")):
        beat = next(b for b in stand["beats"] if b["id"] == bid)
        aimed = next(b for b in stand["beats"] if b["id"] == f"{bid}-press")
        entered = next(b for b in stand["beats"] if b["id"] == f"{bid}-in")
        act = beat["action"].lower()
        cam = beat["camera"].lower()
        assert "bends forward" in act or "bent forward" in act, bid
        assert "between the calves" in act, bid
        assert "glans stays pressed" not in act, bid
        assert "travels into" not in act, bid
        assert "spreads her left buttock aside" in act, bid
        assert "over her left shoulder" in act, bid
        assert "profile side view" in cam, bid
        assert "faces left" in cam, bid
        assert "side-rear" not in cam, bid
        assert "turns the same way" not in act, bid
        assert "turns her whole body" not in act, bid
        assert extra_lora_entries(beat) == []
        assert "siderear" not in extra_keys(beat)
        assert beat.get("steps") == 8 and beat.get("turbo") is False
        aim = aimed["action"].lower()
        assert f"{who} steps onto the same centerline" in aim, bid
        assert "glans stays pressed on that closed ring" in aim, bid
        assert "travels into" not in aim, bid
        assert extra_lora_entries(aimed) == []
        assert aimed.get("steps") == 8 and aimed.get("turbo") is False
        assert extra_lora_entries(entered)[0] == ("siderear", 0.8)
        assert "already stands on the same centerline" in entered["action"].lower(), bid
        assert entered.get("connect") == "chain"
        assert entered.get("steps") == 8 and entered.get("turbo") is False
        assert "doggy" not in extra_keys(beat)
        assert stand["beats"].index(beat) + 1 == stand["beats"].index(aimed)
        assert stand["beats"].index(aimed) + 1 == stand["beats"].index(entered)
        peak = next(b for b in stand["beats"] if b["id"] == f"{bid}-peak")
        assert "heels down" not in peak["action"].lower(), bid
    kiss_stand = next(b for b in stand["beats"] if b["id"] == "03-kiss")
    kiss_in = next(b for b in stand["beats"] if b["id"] == "03-kiss-in")
    assert "grey wall" in kiss_stand["action"].lower()
    assert WALL_SET_CLAUSE in build_beat_prompt(stand, kiss_stand)
    assert PLANTED_PACE_CLAUSE not in build_beat_prompt(stand, kiss_stand)
    assert "moves the hips forward once" in kiss_in["action"].lower()
    assert "center of the frame" in kiss_stand["camera"].lower()
    assert "both eyes look toward the camera" in kiss_stand["action"].lower()
    assert "rim stretches tight" in kiss_in["action"].lower()
    assert "right hand lets go of the shaft" in kiss_in["action"].lower()
    stand_drop = next(b for b in stand["beats"] if b["id"] == "12-exit-drop")
    assert "shaft already outside" in stand_drop["action"].lower()
    assert "slides out" not in stand_drop["action"].lower()
    wall_close = next(b for b in stand["beats"] if b["id"] == "03-kiss-close")
    assert "drips toward the floor" in wall_close["action"].lower()
    assert "finishes as a small closed ring" in wall_close["action"].lower()
    assert "siderear" not in extra_keys(wall_close)
    assert "jacko" not in extra_keys(wall_close)
    fours = prepare_episode(raw, story_override="誘う", invite_pose_override="四つん這い股広げ")
    for bid in ("03-kiss", "06-doggy", "09-join", "12-exit"):
        beat = next(b for b in fours["beats"] if b["id"] == bid)
        act = beat["action"].lower()
        cam = beat["camera"].lower()
        assert "chest and cheek stay down" in act, bid
        assert "between the open thighs" in act, bid
        assert "profile side view" in cam, bid
        assert "side-rear" not in cam, bid
        assert "turns the same way" not in act, bid
        assert extra_lora_entries(beat) == []
        press_b = next(b for b in fours["beats"] if b["id"] == f"{bid}-press")
        assert extra_lora_entries(press_b) == []
        assert "siderear" not in extra_keys(beat)
        assert "siderear" not in extra_keys(press_b)
        assert extra_lora_entries(next(b for b in fours["beats"] if b["id"] == f"{bid}-in"))[0] == ("siderear", 0.8)
        assert "doggy" not in extra_keys(beat)
    fours_drop = next(b for b in fours["beats"] if b["id"] == "12-exit-drop")
    assert "shaft already outside" in fours_drop["action"].lower()
    assert "palms and knees" not in fours_drop["action"].lower()
    assert "open wide to the left and right" in next(b for b in fours["beats"] if b["id"] == "06-doggy")["action"].lower()
    assert "erect 20cm" in next(b for b in fours["beats"] if b["id"] == "09-join")["action"].lower()
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
    for key in ("blowjob", "mystic", "futatf", "mast", "cumshot", "kiss"):
        assert key in keys
    ride_sit = next(b for b in ride["beats"] if b["id"] == "03-kiss-ride")
    assert extra_keys(ride_sit)[:3] == ["mystic", "penis", "synth"]
    assert "sideride" not in extra_keys(ride_sit)
    assert "thrust" not in extra_keys(ride_sit)
    assert not ride_sit.get("trigger")
    assert "hangs directly above the glans" in ride_sit["action"].lower()
    assert "straight down" in ride_sit["action"].lower()
    assert "hold still joined at the base" in ride_sit["action"].lower()
    assert "either side of miki's ribs" in ride_sit["action"].lower()
    assert "legs drop straight down" in ride_sit["action"].lower()
    assert "both knees bend" in ride_sit["action"].lower()
    assert "both knees stay bent" not in ride_sit["action"].lower()
    assert "already stands over" in ride_sit["action"].lower()
    assert "hands land on miki's chest" in ride_sit["action"].lower()
    assert "weight stays on both soles" in ride_sit["action"].lower()
    assert "stands up from that kneel" not in ride_sit["action"].lower()
    assert "folds down" not in ride_sit["action"].lower()
    assert "squats" not in ride_sit["action"].lower()
    assert "thigh lifts" not in ride_sit["action"].lower()
    assert "one thigh" not in ride_sit["action"].lower()
    assert "from above" not in ride_sit["action"].lower()
    assert "from directly above" not in ride_sit["camera"].lower()
    assert "the back of her head on the linoleum" in ride_sit["action"].lower()
    assert "shoulders on the linoleum" in ride_sit["action"].lower()
    assert "steps over the hips" not in ride_sit["action"].lower()
    assert "slides both feet" not in ride_sit["action"].lower()
    assert "head on the right" in ride_sit["action"].lower()
    assert "head on the left" in ride_sit["action"].lower()
    assert "miki sits on aya" not in ride_sit["action"].lower()
    ride_prompt = build_beat_prompt(ride, ride_sit, trigger=merge_trigger("", ride_sit))
    assert "folds down onto her back" not in ride_prompt.lower()
    assert "rises into the rider" not in ride_prompt.lower()
    assert "holds that raised thigh" not in ride_prompt.lower()
    assert "travels into the pussy" in ride_prompt.lower()
    assert "either side of the ribs" in ride_prompt.lower()
    assert "feet do not take a step" not in ride_prompt.lower()
    assert "feet do not travel" not in ride_prompt.lower()
    assert "nothing new enters" not in ride_prompt.lower()
    oral = next(b for b in ride["beats"] if b["id"] == "03-kiss")
    oral_prompt = build_beat_prompt(ride, oral, trigger=merge_trigger("", oral))
    assert "this wide full-body frame stays locked" not in oral_prompt.lower()
    assert "both faces stay fully inside the frame" in oral_prompt.lower()
    assert "the partner's whole face stays inside the frame" in oral_prompt.lower()
    assert "the camera stays back enough that both faces stay fully inside" in oral_prompt.lower()
    assert "before the join, the camera sits far back" in oral_prompt.lower()
    assert "miki's whole face stays inside the frame beside the shaft" in oral_prompt.lower()
    assert "short brown bob" in oral_prompt.lower()
    assert "the camera sits far back" in oral_prompt.lower()
    assert "the adults stay the same size" in oral_prompt.lower()
    assert "aya's face and the partner's face stay in frame" in oral_prompt.lower()
    assert "zoom" not in oral_prompt.lower()
    assert "profile side-on" in ride_prompt.lower()
    assert "camera distance stays fixed" in ride_prompt.lower()
    assert "upright shaft stays rooted in the groin" in ride_prompt.lower()
    assert "the rider's head stays on the left" in ride_prompt.lower()
    assert "hips lower in that side view" in ride_prompt.lower()
    assert "same two adults" in ride_prompt.lower()
    assert "the adult on her back is the one with the shaft" in ride_prompt.lower()
    assert "nothing new enters" not in ride_prompt.lower()
    assert SIDERIDE_TRIGGER not in ride_prompt
    assert "cowgirl" not in ride_prompt.lower()
    ride_peak = next(b for b in ride["beats"] if b["id"] == "03-kiss-peak")
    assert "miki stays on her back" in ride_peak["action"].lower()
    assert "keep the glans inside" in ride_peak["action"].lower()
    assert "buried to the root" in ride_peak["action"].lower()
    assert "hips stay down on the groin the whole take" in ride_peak["action"].lower()
    assert "from the first frame to the last frame" in ride_peak["action"].lower()
    assert "already fully formed on the groin at the first frame" in oral["action"].lower()
    assert "both soles beside the ribs" in ride_peak["action"].lower()
    assert "lifts" not in ride_peak["action"].lower()
    assert "rock up" not in ride_peak["action"].lower()
    assert not ride_peak.get("trigger", "").startswith(SIDERIDE_TRIGGER)
    assert "cums inside of her" in ride_peak.get("trigger", "").lower()
    assert "female character" not in ride_peak.get("trigger", "").lower()
    assert "PENISLORA" in ride_peak.get("trigger", "")
    peak_prompt = build_beat_prompt(ride, ride_peak, trigger=merge_trigger("", ride_peak))
    assert "same two adults" in peak_prompt.lower()
    assert "the adult on her back is the one with the shaft" in peak_prompt.lower()
    assert "feet do not take a step" not in peak_prompt.lower()
    assert "nothing new enters" not in peak_prompt.lower()
    assert "female character" not in peak_prompt.lower()
    peak_keys = extra_keys(ride_peak)
    assert "sideride" not in peak_keys
    assert peak_keys[0] == "penis"
    assert "mystic" not in peak_keys
    assert "thrust" in peak_keys and "penis" in peak_keys and "synth" in peak_keys
    assert "cumshot" not in peak_keys and "cumouf" not in peak_keys
    assert "overflows" in ride_peak["action"].lower()
    assert "still buried to the root" in ride_peak["action"].lower()

    def _walk_beats(node, acc):
        if isinstance(node, dict):
            if isinstance(node.get("extra_loras"), list) and node.get("id"):
                acc.append(node)
            for value in node.values():
                _walk_beats(value, acc)
        elif isinstance(node, list):
            for value in node:
                _walk_beats(value, acc)

    sideride_beats = []
    _walk_beats(raw, sideride_beats)
    seat_n = peak_n = 0
    for beat in sideride_beats:
        keys = extra_keys(beat)
        if "sideride" not in keys:
            continue
        if "thrust" in keys:
            peak_n += 1
            assert "mystic" not in keys, beat["id"]
            assert extra_lora_entries(beat)[0] == ("sideride", 0.8), beat["id"]
        else:
            seat_n += 1
            assert extra_lora_entries(beat)[0] == ("sideride", 0.5), beat["id"]
            assert "mystic" in keys, beat["id"]
    assert seat_n == 0 and peak_n == 0


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
    assert "24cm shaft stays visible in front of the hips, outside any other body" in cover_prompt.lower()
    assert "hip-to-shoulder" not in cover_prompt.lower()
    assert "zoom" not in cover_prompt.lower()
    invite_prompt = build_beat_prompt(invite, cover_i)
    assert "camera distance stays fixed" in invite_prompt.lower()
    assert "the camera sits far back" in invite_prompt.lower()
    assert "open floor" in invite_prompt.lower()
    assert "from above both knees to both faces" in invite_prompt.lower()
    assert "miki's whole face stays inside the frame" in invite_prompt.lower()
    assert "both faces stay fully inside the frame" in invite_prompt.lower()
    assert "the erect shaft stays inside the frame" in invite_prompt.lower()
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
    assert "squash flat" in cover_i["action"].lower()
    assert "kneads it from behind" in cover_i["action"].lower()
    assert "strokes the erect 24cm" in cover_i["action"].lower()
    assert "both hands leave the shaft" in cover_i["action"].lower()
    assert "22cm" not in cover_i["action"].lower()
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
    assert "stroking the erect 24cm" in cover_cam
    assert "leaving the shaft" in cover_cam
    assert cover_cam.find("pressed into miki's back") < cover_cam.find("turn whole-body")
    assert "head and chest turn together" in cover_i["action"].lower()
    assert "chin over the breastbone" in cover_i["action"].lower()
    assert "90" not in cover_i["action"]
    assert "180" not in cover_i["action"]
    assert beat_clip_seconds(invite, cover_i) == 10.0
    assert duration_ladder(invite, cover_i) == [10.0, 8.0, 6.0]
    assert cover_i["trim"]["seconds"] == 10.0

    doggy = next(b for b in fours["beats"] if b["id"] == "06-doggy")
    assert "chest and cheek stay down" in doggy["action"].lower()
    assert "between the open thighs" in doggy["action"].lower()
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
    assert extra_lora_entries(kiss_i) == []
    assert "glans stays pressed" in kiss_i["action"].lower()
    assert "travels into" not in kiss_i["action"].lower()
    kiss_in = next(b for b in m_open["beats"] if b["id"] == "03-kiss-in")
    assert extra_keys(kiss_in) == ["mystic", "penis"]
    assert "torso stays upright" in kiss_in["action"].lower()
    assert "the whole shaft is hidden inside the pussy" in kiss_in["action"].lower()
    assert "travels into the pussy" in kiss_in["action"].lower()
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
    assert extra_keys(facial) == ["cumshot", "penis", "jpnmoans"]
    assert facial.get("trigger") == "CUMSH0T\nPENISLORA\njpnMoans"
    assert extra_lora_entries(facial)[0] == ("cumshot", 1.0)
    assert facial.get("facial") is True
    assert "holds kana's erect 20cm in her right hand" in facial["action"].lower()
    assert "across aya's nose, eyes, and into aya's open mouth" in facial["action"].lower()
    assert "smiles shyly and giggles" in facial["action"].lower()
    assert facial["trim"]["seconds"] == 10.0
    assert "slow" not in facial["action"].lower()
    assert "white goo" in facial["action"].lower()
    assert extra_lora_entries(kissb) == [("kiss", 0.5)]
    facial_prompt = build_beat_prompt(m_open, facial)
    kiss_prompt = build_beat_prompt(m_open, kissb)
    assert facial.get("connect") == "cut" and beat_source(facial) == "t2v"
    assert "the camera moves in an arc around aya's face" in facial_prompt.lower()
    assert "looks up" in facial_prompt.lower()
    assert "both adults stay full body" not in facial_prompt.lower()
    assert "white rope" in facial_prompt.lower()
    assert "kana's whole face stays inside the frame" not in facial_prompt.lower()
    assert "both faces stay fully inside the frame" not in facial_prompt.lower()
    assert "zoom" not in facial_prompt.lower()
    assert "kana's whole face stays inside the frame" in kiss_prompt.lower()
    assert "before the join, the camera sits far back" in kiss_prompt.lower()
    assert "zoom" not in kiss_prompt.lower()
    assert "french kiss" in kissb["action"].lower()
    assert "tongue kiss" in kissb["action"].lower()
    assert "tight mutual embrace" in kissb["action"].lower()
    assert "lick around the lips" in kissb["action"].lower()
    order = [b["id"] for b in m_open["beats"]]
    assert order.index("08-ui-kana") < order.index("09-kana-facial") < order.index("09-kana-kiss") < order.index("09-join")
    goo = "sticky white goo clinging to aya's face, hair, neck, breasts, shoulders, and chest"
    aya_lock = raw["cast"]["aya"]["lock"].lower()
    aya_white = raw["cast"]["aya"]["looks"]["white_upper"].lower()
    assert goo not in aya_lock
    assert goo in aya_white
    assert aya_white.startswith(aya_lock)
    assert raw["look_triggers"] == [{"after": "09-kana-facial", "who": "aya", "look": "white_upper"}]
    assert goo not in m_open["cast"]["aya"]["lock"].lower()
    assert "white rope" in facial["action"].lower()
    assert "white goo clinging to aya's face and breasts" in facial["action"].lower()
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
    assert "mouths stay apart" in ten_low
    assert "french kiss" not in ten_low
    assert "lit doorway stays behind shino" in ten_low
    assert beat_loco(ten) == "planted"
    spot = next(b for b in invite["beats"] if b["id"] == "10-shino-spot")
    assert "already stooping" in spot["action"].lower()
    assert "walks in from the right" not in spot["action"].lower()
    assert beat_loco(spot) == "planted"
    assert "eager excited expectation" in ten_low
    assert "front groin" in ten_low
    assert "points forward" in ten_low
    assert "buttocks stay bare" in ten_low
    assert "not purple" in ten_low
    assert "walks forward toward shino" not in ten_low
    assert beat_clip_seconds(invite, ten) == 6.0

    twelve = next(b for b in invite["beats"] if b["id"] == "12-exit")
    twelve_low = action_blob(invite, "12-exit")
    assert "kneels" in twelve["action"].lower()
    assert "slide down to the base" in twelve["action"].lower()
    assert "mouth on the shaft" in twelve["action"].lower()
    assert "hangs directly above the glans" in twelve_low
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
    assert "lemon-yellow" in stall["action"].lower()
    assert "yellow water" in stall["action"].lower()
    assert "see-through" in stall["action"].lower()
    assert "urethra" not in stall["action"].lower()
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
        ("tentacle", ("tentacle", "travels into", "left nipple", "right nipple", "open mouth", "hairless pussy", "hold still joined")),
    ):
        ep = prepare_episode(raw, story_override="受け入れる", toilet_override=mode)
        four = next(b for b in ep["beats"] if b["id"] == "04-toilet")
        low = four["action"].lower()
        assert four["trim"]["start"] == 0 and four["trim"]["seconds"] == 10.0
        assert beat_clip_seconds(ep, four) == 10.0
        assert duration_ladder(ep, four) == [10.0, 8.0, 6.0]
        for n in must:
            assert n in low, (mode, n)
        if mode == "tentacle":
            assert "keep thrusting" not in low
            assert "already sits" in low
        else:
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
            assert "both wrists and both ankles" in fill["action"].lower()
            assert "vine" in fill["action"].lower()
            assert "vine" not in next(b for b in prepare_episode(raw, story_override="受け入れる", toilet_override="pee")["beats"] if b["id"] == "04-toilet")["action"].lower()
            assert "left nipple" in low and "right nipple" in low
            assert "keep thrusting" not in low and "keep thrusting" not in fill["action"].lower()
            assert "exactly three" not in low and "exactly three" not in fill["action"].lower()
            assert "under the toilet seat" not in low
            assert "hold her thighs" not in low
            assert "tentacles3d" in extra_keys(four)
            assert "2d" not in json.dumps(four.get("extra_loras")).lower()
            assert "3293041" not in LORA_URLS["tentacles3d"]
            fill_low = fill["action"].lower()
            assert "both wrists" in fill_low and "both ankles" in fill_low
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
            assert "left nipple" in low and "open mouth" in low
            assert "profile" not in four["camera"].lower()
            assert "facing the camera" in enter["action"].lower()
        else:
            assert "front view" in four["camera"].lower()
            assert "profile" not in four["camera"].lower()
            assert "facing the camera" in low
            assert "shoots forward" in low
            assert "toward the camera" in low
            assert "hips hold still" in low
            assert "toilet bowl stays still" in low
            assert "porcelain western toilet" in low
            assert "porcelain" in (four.get("place") or "").lower()
            assert "brown" in (four.get("place") or "").lower()
            assert "plant-flesh" not in low
            assert "tentacle" not in low
            assert "only the yellow stream moves" in low
            assert "lemon-yellow water" in low
            assert "see-through" in low
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
                assert "kneels" in twelve["action"].lower()
                assert "hugs" not in action_blob(ep, "12-exit")
            if pose and "四つん這い" in pose:
                six = next(b for b in ep["beats"] if b["id"] == "06-doggy")
                assert "chest and cheek stay down" in six["action"].lower()
                assert "between the open thighs" in six["action"].lower()
        for beat, prompt, errs in beat_prompts(ep, trigger=""):
            assert errs == []
            assert "blood" not in [h.lower() for h in forbidden_hits(prompt)]
            for v in beat_vocals(beat):
                assert v["who"] in (ep.get("cast") or {})
                assert v["who"] in (beat.get("cast") or [])


def test_hospital_finger_pose_and_squat_toilet_modes():
    raw = load_episode(HOSPITAL_DIR / "episode.json")
    assert TOILET_MODES["off"].get("recommend") is True
    assert ui_default("toilet").startswith("トイレに行かない")
    assert "wash" in TOILET_MODES and "wash_miki" in TOILET_MODES
    assert "トイレ・和式排出" in ui_choices("toilet")
    assert "トイレ・和式ミキ" in ui_choices("toilet")
    assert LORA_FILES["solodildo"] == "h3_base_dildo_v1.0_9250.safetensors"
    assert "models/3378450" in LORA_URLS["solodildo"]
    assert "fileId=3266906" in LORA_URLS["solodildo"]
    assert LORA_STRENGTHS["solodildo"] == 1.0
    assert LORA_FILES["cumfacial"] == "cum_facial_000005400.safetensors"
    assert "models/3290895" in LORA_URLS["cumfacial"]
    assert "fileId=3175377" in LORA_URLS["cumfacial"]
    assert LORA_STRENGTHS["cumfacial"] == 0.8
    assert LORA_FILES["thumbinbutt"] == "MiniMax H3 - ThumbInButt.safetensors"
    assert "fileId=3168734" in LORA_URLS["thumbinbutt"]
    assert "api/download/models/" in LORA_URLS["thumbinbutt"]
    assert "/models/2904444" not in LORA_URLS["thumbinbutt"]
    assert LORA_STRENGTHS["thumbinbutt"] == 0.55
    assert LORA_FILES["tentacles3d"].startswith("Tentacles-3D")
    assert "fileId=3234017" in LORA_URLS["tentacles3d"]
    assert "3293041" not in LORA_URLS["tentacles3d"]
    assert LORA_STRENGTHS["tentacles3d"] == 0.45
    assert LORA_FILES["cmst"].startswith("face_cum")
    assert "fileId=3175377" in LORA_URLS["cmst"]
    assert LORA_STRENGTHS["cmst"] == 0.65
    assert LORA_FILES["jacko"].startswith("jackoPose")
    assert "fileId=3244536" in LORA_URLS["jacko"]
    assert LORA_STRENGTHS["jacko"] == 0.8
    assert LORA_FILES["jpnmoans"] == "minimax-jav-voice.safetensors"
    assert "fileId=3166743" in LORA_URLS["jpnmoans"]
    assert LORA_STRENGTHS["jpnmoans"] == 0.55
    assert LORA_FILES["doggy"].startswith("MM-H3 - Doggy Style")
    assert "fileId=3202556" in LORA_URLS["doggy"]
    assert LORA_STRENGTHS["doggy"] == 0.5
    assert LORA_FILES["siderear"].startswith("MMH3_NSFW_Doggystyle_Sex")
    assert "models/3362792" in LORA_URLS["siderear"]
    assert "fileId=3250615" in LORA_URLS["siderear"]
    assert LORA_STRENGTHS["siderear"] == 0.8
    assert LORA_FILES["anuspussy"] == "anus_pussy_v2.safetensors"
    assert "models/3371009" in LORA_URLS["anuspussy"]
    assert "fileId=3259145" in LORA_URLS["anuspussy"]
    assert LORA_STRENGTHS["anuspussy"] == 0.4
    off = prepare_episode(raw, story_override="accept")
    assert off["render"]["toilet"] == "off"
    assert not any(b["id"] == "04-toilet" for b in off["beats"])

    finger = prepare_episode(raw, story_override="accept", toilet_override="finger", connect_override="t2v")
    assert validate_episode(finger, root=HOSPITAL_DIR) == []
    toy = next(b for b in finger["beats"] if b["id"] == "04-toilet-toy")
    fact = next(b for b in finger["beats"] if b["id"] == "04-toilet")
    pump = next(b for b in finger["beats"] if b["id"] == "04-toilet-pump")
    gaped = next(b for b in finger["beats"] if b["id"] == "04-toilet-gape")
    low = fact["action"].lower()
    assert "porcelain" in toy["action"].lower() or "porcelain" in (toy.get("place") or "").lower()
    assert "beside the seat" in toy["action"].lower()
    assert "long, thin, flexible sex toy" in toy["action"].lower()
    assert "plant tendril" in toy["action"].lower()
    assert "sits on the porcelain seat facing the camera" in toy["action"].lower()
    assert "solodildo" not in extra_keys(toy)
    aim = next(b for b in finger["beats"] if b["id"] == "04-toilet-aim")
    assert "right hand" in aim["action"].lower()
    assert "outside the vagina" in aim["action"].lower()
    assert "solodildo" not in extra_keys(aim)
    assert "plant-flesh" not in toy["action"].lower()
    assert "tentacle" not in toy["action"].lower()
    assert extra_lora_entries(fact)[0] == ("solodildo", 1.0)
    assert extra_lora_entries(pump)[0] == ("solodildo", 1.0)
    assert merge_trigger("", fact) == ""
    assert "into and out of her vagina with a rhythmic motion" in low
    assert "folds stretch and indent as it enters" in low
    assert "pull outward as the toy exits" in low
    assert "wet glistening juice" in low
    assert "hold still joined" not in low
    assert "quicker rhythmic motion" in pump["action"].lower()
    assert fact.get("steps") == 8 and fact.get("turbo") is False
    assert pump.get("steps") == 8 and pump.get("turbo") is False
    assert gaped.get("steps") == 8 and gaped.get("turbo") is False
    assert "penis" not in extra_keys(fact)
    assert "penis" not in extra_keys(pump)
    assert "あ、いく" in pump["action"]
    assert "fall" in gaped["action"].lower()
    assert "wide ring" in gaped["action"].lower()
    assert "soft closed slit" in gaped["action"].lower()
    for beat in (toy, aim, fact, pump, gaped):
        text = " ".join(str(beat.get(k) or "") for k in ("action", "camera", "place", "environment")).lower()
        assert "penis-shaped" not in text, beat["id"]
        assert "glans" not in text, beat["id"]
        assert "dildo" not in text, beat["id"]
        assert "back toward the camera" not in text, beat["id"]
    for beat in (aim, fact, pump, gaped):
        assert "static shot. medium shot. low angle" in beat["camera"].lower(), beat["id"]
        assert "faces the camera" in beat["camera"].lower(), beat["id"]
    toy_prompt = build_beat_prompt(finger, toy)
    assert TOILET_SIT_CLAUSE in toy_prompt
    assert PLANTED_PACE_CLAUSE not in toy_prompt
    assert PLANTED_PACE_CLAUSE not in build_beat_prompt(finger, aim)
    assert "thumb" not in "\n".join(b["action"].lower() for b in (toy, fact, pump, gaped))
    assert all("thumbinbutt" not in extra_keys(b) for b in (toy, fact, pump, gaped))
    assert "jacko" not in extra_keys(fact)
    assert fact.get("connect") == "chain" and fact.get("source") == "chain"
    assert toy.get("source") == "t2v"
    finger_blob = "\n".join(b["action"] for b in finger["beats"] if str(b["id"]).startswith("04-toilet")).lower()
    assert "brown log" not in finger_blob
    assert "feces" not in finger_blob
    assert "thum1n8utt" not in fact["action"]
    assert fact.get("trigger") != "thum1n8utt"
    prompt = build_beat_prompt(finger, fact, trigger=merge_trigger("", fact))
    assert "feet do not take a step" not in prompt.lower()
    assert "feet do not travel" not in low
    for word in ("zombie", "blood", "corpse", "doggy", "missionary", "cowgirl"):
        assert word not in low
    _assert_hospital_bans(finger)

    wash = prepare_episode(raw, story_override="accept", toilet_override="和式", connect_override="t2v")
    miki = prepare_episode(raw, story_override="accept", toilet_override="和式ミキ", connect_override="t2v")
    assert validate_episode(wash, root=HOSPITAL_DIR) == []
    assert validate_episode(miki, root=HOSPITAL_DIR) == []
    assert any(b["id"] == "04-toilet-squat" for b in wash["beats"])
    for ep in (wash, miki):
        stall = [b for b in ep["beats"] if str(b["id"]).startswith("04-toilet")]
        blob = "\n".join(
            " ".join(str(b.get(k) or "") for k in ("action", "camera", "place", "environment"))
            for b in stall
        )
        assert "western toilet bowl" not in blob
        assert "porcelain" not in blob.lower()
        assert "squat pan" in blob.lower()
        assert "stained squat rim" in blob.lower()
        assert "brown hospital dirt" in blob.lower()
        assert "plant-flesh" not in blob.lower()
        assert "tentacle" not in blob.lower()
        assert "SITS DOWN facing the camera" not in blob
        assert "hood" in blob and "platform" not in blob.lower()
        assert "flush into the tile floor" in blob
        for beat in stall:
            act = beat["action"]
            assert "thum1n8utt" not in act
            for word in ("zombie", "blood", "corpse", "doggy", "missionary", "cowgirl"):
                assert word not in act.lower()
    expel = next(b for b in wash["beats"] if b["id"] == "04-toilet")
    assert "brown log" in expel["action"]
    assert "thumbinbutt" in extra_keys(expel)
    assert next(b for b in wash["beats"] if b["id"] == "04-toilet-in")["source"] == "t2v"
    insert = next(b for b in miki["beats"] if b["id"] == "04-toilet")
    assert "TRAVELS INTO the anus" in insert["action"]
    push = next(b for b in miki["beats"] if b["id"] == "04-toilet-push")
    assert "jacko" in extra_keys(push)
    assert "doggy" not in extra_keys(push)
    assert "Doggy style" not in push["action"]
    assert extra_lora_entries(insert)[0] == ("jacko", 0.4)
    assert "doggy" not in extra_keys(insert)
    assert "thumbinbutt" not in extra_keys(insert)
    assert "synth" not in extra_keys(insert)
    assert "HOLD still joined at the BASE" in insert["action"]
    assert "thumbinbutt" not in extra_keys(insert)
    assert "thrust" not in extra_keys(insert)
    assert insert["source"] == "chain"
    cum = next(b for b in miki["beats"] if b["id"] == "04-toilet-cum")
    assert "LIFTS" not in cum["action"]
    assert "SLIDES OUT" not in cum["action"]
    assert len([b for b in miki["beats"] if str(b["id"]).startswith("04-toilet")]) == 8
    full = prepare_episode(
        raw,
        story_override="誘う",
        invite_pose_override="対面座位",
        toilet_override="wash_miki",
        gin_override="犯される",
        tsuno_override="フルネルソンアナル",
        dog_override="誘う口",
        species_override="スライム",
        connect_override="前の最終フレームから続ける",
        scenes_override="miki=inherit,rei=invite_ride,kana=invite_all_fours,shino=invite_m_open",
    )
    assert validate_episode(full, root=HOSPITAL_DIR) == []
    assert len(full["beats"]) <= MAX_BEATS
    pee = prepare_episode(raw, story_override="accept", toilet_override="pee", connect_override="t2v")
    pee_act = next(b for b in pee["beats"] if b["id"] == "04-toilet")
    assert "facing the camera" in pee_act["action"].lower()
    assert pee_act["source"] == "t2v"


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
    assert len(chosen["beats"]) == 54
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
    assert len(fullest["beats"]) == 57
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
    assert "hangs directly above the glans" in kana_blob
    kana_sit = next(b for b in mixed["beats"] if b["id"] == "09-join-ride")
    assert "pushes kana backward" not in kana_sit["action"].lower()
    assert "already lies fully on her back" in kana_sit["action"].lower()
    assert "the back of her head on the linoleum" in kana_sit["action"].lower()
    assert "either side of kana's ribs" in kana_sit["action"].lower()
    assert "hand holds that raised thigh" not in kana_sit["action"].lower()
    assert "slides both feet" not in kana_sit["action"].lower()
    assert "head on the right" in kana_sit["action"].lower()
    assert "head on the left" in kana_sit["action"].lower()
    assert "kana sits on aya" not in kana_sit["action"].lower()
    assert "squats" not in kana_sit["action"].lower()
    assert "hold still joined at the base" in kana_sit["action"].lower()
    assert "buttocks meet the hips" in kana_sit["action"].lower()
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
    assert "shino" not in kiss_low and "35cm" not in kiss_low and "forked" not in kiss_low
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
    assert "extremely tall" in shino_kiss and "35cm" in shino_kiss and "forked reptile tongue" in shino_kiss
    miki_peak = next(b for b in full["beats"] if b["id"] == "03-kiss-peak")
    assert "whites show" not in miki_peak["action"].lower()

    only = {"rei": False, "kana": False, "shino": False, "miki": True}
    miki = prepare_episode(raw, story_override="誘う", appear_override=only)
    assert miki["beats"][-1]["id"] == "03-kiss-kiss"
    assert miki["beats"][-1]["cast"] == ["aya", "miki"]
    low = miki["beats"][-1]["action"].lower()
    assert "24cm" in low and "short brown bob" in low and "lacerations" in low and "sweat beads" in low
    assert "shino" not in low and "35cm" not in low and "rei" not in low
    assert extra_lora_entries(miki["beats"][-1]) == [("kiss", 0.5)]
    assert "french kiss" in low and "corners of the mouth" in low
    seat = next(b for b in miki["beats"] if b["id"] == "03-kiss-press")
    peak = next(b for b in miki["beats"] if b["id"] == "03-kiss-peak")
    drop = next(b for b in miki["beats"] if b["id"] == "03-kiss-drop")
    assert "tongue hangs out" in seat["action"].lower()
    assert "whites show" in peak["action"].lower()
    assert "rolls onto her back" in drop["action"].lower()
    assert "overflows from the anus" in drop["action"].lower()

    rei = prepare_episode(
        raw,
        story_override="誘う",
        invite_pose_override="フルネルソンアナル",
        appear_override={"miki": False, "rei": True, "kana": False, "shino": False},
    )
    assert rei["beats"][-1]["id"] == "06-doggy-kiss"
    rei_low = rei["beats"][-1]["action"].lower()
    assert "24cm" in rei_low and "dark-brown filthy sludge" in rei_low and "left breast" in rei_low
    assert "22cm" not in rei_low and "35cm" not in rei_low and "miki" not in rei_low
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


def test_hospital_shino_stays_35cm_and_horn_prefix_beats_stay():
    raw = load_episode(HOSPITAL_DIR / "episode.json")
    assert "30cm" not in raw["cast"]["shino"]["lock"]
    assert "35cm" in raw["cast"]["shino"]["lock"]
    handoff = (HOSPITAL_DIR / "HANDOFF.md").read_text(encoding="utf-8")
    assert "膣の立ちバック" not in handoff
    assert "30cm" not in handoff
    assert "35cm" in handoff
    assert "肛門" in SCENE_ACTION_MODES["invite_stand"]["when_ja"]
    assert "膣" not in SCENE_ACTION_MODES["invite_stand"]["when_ja"]
    assert "抱きながら肛門" in TSUNO_MODES["invite_stand"]["when_ja"]
    assert "壁で胸を掴んで" in TSUNO_MODES["anal_back"]["when_ja"]

    bent = prepare_episode(raw, story_override="誘う", ride_bent_override="しの")
    seat = next(b for b in bent["beats"] if b["id"] == "12-exit-ride")
    assert "35cm" in seat["action"]
    assert "30cm" not in seat["action"]
    emb = prepare_episode(raw, story_override="誘う", invite_pose_override="embrace")
    entered = next(b for b in emb["beats"] if b["id"] == "12-exit-in")
    assert "35cm" in entered["action"]
    assert "30cm" not in entered["action"]
    finale = prepare_episode(raw, story_override="誘う")
    kiss = finale["beats"][-1]["action"]
    assert finale["beats"][-1]["id"] == "12-exit-kiss"
    assert "35cm" in kiss
    assert "30cm" not in kiss
    bare = prepare_episode(raw, appearance_override={"enemies": "shino; shaft=なし"})
    assert "erect 35cm" not in bare["cast"]["shino"]["lock"]
    assert "a bare hairless groin" in bare["cast"]["shino"]["lock"]

    invite = prepare_episode(raw, tsuno_override="誘う立ちバック")
    invite_ids = [b["id"] for b in invite["beats"]]
    assert invite_ids.index("04-tsuno-meet") < invite_ids.index("04-tsuno-in")
    invite_meet = next(b for b in invite["beats"] if b["id"] == "04-tsuno-meet")
    invite_in = next(b for b in invite["beats"] if b["id"] == "04-tsuno-in")
    assert "knead them from behind" in invite_meet["action"].lower()
    assert "travels into aya's anus" in invite_meet["action"].lower()
    assert "balls of both feet" in invite_in["action"].lower()
    assert "travels into the anus" in invite_in["action"].lower()

    anal = prepare_episode(raw, tsuno_override="後ろアナル")
    anal_ids = [b["id"] for b in anal["beats"]]
    assert anal_ids.index("04-tsuno-meet") < anal_ids.index("04-tsuno-in")
    anal_meet = next(b for b in anal["beats"] if b["id"] == "04-tsuno-meet")
    anal_in = next(b for b in anal["beats"] if b["id"] == "04-tsuno-in")
    assert "cup aya's breasts" in anal_meet["action"].lower()
    assert "palms hit the wall" in anal_meet["action"].lower()
    assert "travels into aya's anus" in anal_meet["action"].lower()
    assert "chest and cheek" in anal_in["action"].lower()
    assert "open wide" in anal_in["action"].lower()
    assert "travels into the anus" in anal_in["action"].lower()


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
    assert ids.index("04-gin-cunny") == ids.index("04-gin-lick") + 1
    lick = next(b for b in taken["beats"] if b["id"] == "04-gin-lick")
    cunny = next(b for b in taken["beats"] if b["id"] == "04-gin-cunny")
    walk = next(b for b in taken["beats"] if b["id"] == "04-gin-walk")
    lick_prompt = build_beat_prompt(taken, lick)
    walk_prompt = build_beat_prompt(taken, walk)
    assert "keeps licking" in lick["action"].lower()
    assert "grows out of the open mouth" in lick["action"].lower()
    assert "penis growth" not in lick["action"].lower()
    assert extra_keys(lick) == ["mystic", "cunny", "jpnmoans"]
    assert lick.get("trigger") == "performing cunnilingus\njpnMoans"
    assert "hairless pussy" in lick["action"].lower()
    assert "24cm" not in lick["action"]
    assert "penis growth" not in cunny["action"].lower()
    assert "clitoris grows" in cunny["action"].lower()
    assert extra_lora_entries(cunny) == [("cunny", 0.8), ("mystic", 0.5), ("jpnmoans", 0.55)]
    assert cunny.get("steps") == 8
    assert cunny.get("turbo") is False
    assert "turbo" not in extra_keys(cunny)
    assert "larry" not in extra_keys(cunny)
    assert "turbo8" not in extra_keys(cunny)
    speed = {
        "name": "speed",
        "stack": [
            ("minimax_h3_fl2v_turbo_4step_v1.0_768p_comfyui_bf16.safetensors", 1.0),
            ("minimax_h3_turbo_v4_step600_ema_comfy.safetensors", 1.0),
        ],
        "steps": 4,
        "notes": [],
    }
    dropped = apply_extra_loras(speed, cunny, None)
    dropped_names = " ".join(str(item[0]).lower() for item in dropped["stack"])
    assert "fl2v_turbo" not in dropped_names
    assert "turbo_v4" not in dropped_names
    assert dropped["steps"] == 8
    assert "futatf" not in extra_keys(cunny)
    assert "penis" not in extra_keys(cunny)
    assert "licks the new shaft once" in cunny["action"].lower()
    assert "surprised joyful" in cunny["action"].lower()
    assert "falls onto" not in cunny["action"].lower()
    assert "falls onto" not in cunny["camera"].lower()
    assert "sitting" not in cunny["action"].lower()
    assert "already sits toward the right" in cunny["action"].lower()
    assert "tongue still pressed on the clitoris" in cunny["action"].lower()
    assert "on her back" in cunny["action"].lower()
    assert cunny.get("connect") == "chain"
    assert cunny.get("source") == "chain"
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
    assert lick.get("cast_lock") and "24cm" not in lick["cast_lock"]["aya"]
    assert "hairless pussy" in lick["cast_lock"]["aya"]
    assert cunny.get("cast_lock") and "24cm" not in cunny["cast_lock"]["aya"]
    assert "shaft" not in cunny["cast_lock"]["aya"].lower()
    assert "penis" not in cunny["cast_lock"]["aya"].lower()
    assert "pleasure-drunk happy smile" in cunny["cast_lock"]["aya"].lower()
    assert "hairless pussy" in cunny["cast_lock"]["aya"]
    assert "ashen" not in lick["cast_lock"]["aya"].lower()
    assert "pale-tan shaft" in action_blob(taken, "04-gin")
    assert "the shaft stays ashen gray" not in action_blob(taken, "04-gin")
    assert "24cm" not in lick_prompt
    cunny_prompt = build_beat_prompt(taken, cunny)
    assert "24cm" in cunny_prompt
    assert "shaft written" not in cunny_prompt.lower()
    assert "pleasure-drunk happy smile" in cunny_prompt.lower()
    assert "falls onto" not in cunny_prompt.lower()
    assert "aya" in walk["cast"]
    assert "gin" in (walk.get("fade_cast") or [])
    assert "grown shaft is gone" in walk["action"].lower()
    assert "no penis" in walk["action"].lower()
    assert "gone from frame one" not in walk["action"].lower()
    assert "pulls out of gin's pussy" in walk["action"].lower()
    assert "saliva string" in walk["action"].lower()
    assert "pleasure-drunk" in walk["action"].lower()
    assert "t-junction" in walk["action"].lower()
    assert walk.get("connect") == "chain"
    assert not is_end_connect_beat(walk)
    assert beat_source(walk) == "chain"
    assert extra_lora_entries(walk) == [("kiss", 0.5)]
    assert "mouths joined" in walk["action"].lower()
    assert walk["hud"]["complete"] is False
    ids = [b["id"] for b in taken["beats"]]
    assert ids.index("04-gin-walk") < len(ids) - 1
    walk_prompt = build_beat_prompt(taken, walk)
    assert "The lit doorway sits at the RIGHT edge" not in walk_prompt
    assert "zombie" not in lick_prompt.lower() and "corpse" not in lick_prompt.lower()
    assert "tongue hanging out" in action_blob(taken, "04-gin")
    jupo = next(b for b in taken["beats"] if b["id"] == "04-gin-jupo")
    assert extra_keys(jupo) == ["blowjob", "mystic"]
    assert "already lies fully on her back" in jupo["action"].lower()
    assert "already sitting on her butt" not in jupo["action"].lower()
    assert "leaning on both palms" not in jupo["action"].lower()
    assert "lies back" not in jupo["action"].lower()
    assert "closed lips" in jupo["action"].lower()
    assert "base" in jupo["action"].lower()
    assert "tongue stays inside" not in jupo["action"].lower()
    assert "hanging out" not in jupo["action"].lower()
    ride_peak = next(b for b in taken["beats"] if b["id"] == "04-gin-peak")
    assert "on her back" in ride_peak["action"].lower()
    assert "leaning on both palms" not in ride_peak["action"].lower()
    assert "keep the glans inside" in ride_peak["action"].lower()
    assert "lifts" not in ride_peak["action"].lower()
    assert "pull back" not in ride_peak["action"].lower()
    assert "slides off" not in ride_peak["action"].lower()
    assert "the shaft stays buried to the root until the last frame" in ride_peak["action"].lower()
    assert "gin's lips stay closed" in ride_peak["action"].lower()
    assert "holding her raised knee" not in ride_peak["action"].lower()
    assert "buried to the root" in ride_peak["action"].lower()
    assert "beside aya's hip" not in ride_peak["action"].lower()
    assert "knee up" not in ride_peak["action"].lower()
    assert "overflows" in ride_peak["action"].lower()
    assert "finishes inside gin" in ride_peak["action"].lower()
    assert "cums inside" not in ride_peak.get("trigger", "").lower()
    assert "lifts" not in (ride_peak.get("trigger") or "").lower()
    assert "sideride" not in extra_keys(ride_peak)
    assert extra_keys(ride_peak)[0] == "penis"
    assert "thrust" in extra_keys(ride_peak)
    assert "mystic" not in extra_keys(ride_peak)
    assert "pussy hanging directly above the glans" not in jupo["action"].lower()
    assert "cums" not in (ride_peak.get("trigger") or "").lower()
    assert "leaning on both palms" not in (ride_peak.get("trigger") or "").lower()
    assert "on her back" in (ride_peak.get("trigger") or "").lower()
    assert not (ride_peak.get("trigger") or "").startswith(SIDERIDE_TRIGGER)
    assert "kneels" in jupo["action"].lower()
    assert "soles plant" not in jupo["action"].lower()
    assert "stands vertically straight up from the groin" in jupo["action"].lower()
    assert "head right" in jupo["action"].lower()
    assert "feet left" in jupo["action"].lower()
    assert "toward the left" in jupo["action"].lower()
    ride_in = next(b for b in taken["beats"] if b["id"] == "04-gin-ride")
    ride_act = ride_in["action"].lower()
    assert "stands up" not in ride_act
    assert "steps" not in ride_act
    assert "one sole beside each side of the chest" in ride_act
    assert "both knees stay bent" in ride_act
    assert "hips stay over the groin" in ride_act
    assert "weight stays on the soles" in ride_act
    assert "either side of aya's ribs" in ride_act
    assert "on her back" in ride_act
    assert "sits on" not in ride_act
    assert "squats" not in ride_act
    assert "buttocks meet the hips" in ride_act
    assert "one hand on each breast" in ride_act
    assert "rest on aya's breasts" in ride_act
    assert "holds the 24cm" not in ride_act
    assert "holds that raised knee" not in ride_act
    assert "lowers her hips straight down once" in ride_act
    assert "hold still joined at the base until the last frame" in ride_act
    assert "the shaft stays buried to the root until the last frame" in ride_act
    assert "pull back" not in ride_act
    assert "slides off" not in ride_act
    assert "lifts" not in ride_act
    assert "gin's lips stay closed" in ride_act
    assert "beside aya's hip" not in ride_act
    assert "knee rises" not in ride_act
    assert "aya hold still" not in ride_act or "hold still joined" in ride_act
    assert "both knees stay bent" in ride_act
    assert "already stands over" not in ride_act
    assert "travels into gin's pussy to the root" in ride_act
    assert "from above" not in ride_act
    assert "from directly above" not in ride_act
    assert "slides both feet" not in ride_act
    assert "folds down" not in ride_act
    assert "sideride" not in extra_keys(ride_in)
    assert "thrust" not in extra_keys(ride_in)
    assert extra_lora_entries(ride_in)[:3] == [("mystic", 0.5), ("penis", 0.45), ("synth", 0.4)]
    assert "slide down" in jupo["action"].lower()
    assert "kneels at the hips" in jupo["action"].lower()
    assert "full body including both feet" in jupo["action"].lower()
    assert "one clawed hand holds the shaft" not in jupo["action"].lower()
    assert "closed lips" in jupo["action"].lower()
    assert "slide down to the base" in jupo["action"].lower()
    jupo_prompt = build_beat_prompt(taken, jupo)
    assert "camera distance stays fixed" in jupo_prompt.lower()
    assert "zoom" not in jupo_prompt.lower()
    assert "do not push the camera in" not in jupo_prompt.lower()
    assert "aya's face and the partner's face stay in frame" in jupo_prompt.lower()
    assert "this wide full-body frame stays locked" not in jupo_prompt.lower()
    assert "from above both knees" not in jupo_prompt.lower()
    assert "the camera stays back enough that both faces stay fully inside" not in jupo_prompt.lower()
    assert "only two adults share this frame" in jupo_prompt.lower()
    assert "the adult on her back" not in jupo_prompt.lower()
    assert "the rider is the one sitting" not in jupo_prompt.lower()
    assert "hips travel straight up and straight down" not in jupo_prompt.lower()
    assert "feet do not take a step" not in jupo_prompt.lower()
    assert "nobody walks" not in jupo_prompt.lower()
    assert "does not scroll" not in jupo_prompt.lower()
    ride_prompt = build_beat_prompt(taken, ride_in)
    peak_prompt = build_beat_prompt(taken, ride_peak)
    for gin_prompt in (ride_prompt, peak_prompt):
        low = gin_prompt.lower()
        assert "the adult on her back" not in low
        assert "the rider's head stays on the left" not in low
        assert "feet do not take a step" not in low
        assert "nobody walks" not in low
        assert "does not scroll" not in low
        assert "on her back" in low
        assert "leaning on both palms" not in low
        assert "folds down" not in low
        assert "rises into the rider" not in low
        assert "stands up from that kneel" not in low
        assert "do not piston" not in low
        assert "a hip thrust is in place" not in low
        assert "folds down" not in low
        assert "rises into the rider" not in low
        assert "knee rises" not in low
        assert "beside aya's hip" not in low
    assert "stands up" not in ride_prompt.lower()
    assert "steps over" not in ride_prompt.lower()
    assert "one hand on each breast" in ride_prompt.lower()
    assert "hold still joined at the base" in ride_prompt.lower()
    assert "sideride" not in ride_prompt.lower()
    assert "keep the glans inside" in peak_prompt.lower()
    assert "lifts" not in peak_prompt.lower()
    assert "Look that stays for this whole shot" in jupo_prompt
    assert "grimy brown hospital dirt" in jupo_prompt
    assert "pale-tan" in jupo_prompt
    assert "Aya's shaft written" in jupo_prompt
    assert "shaft written" not in cunny_prompt.lower()
    spot = next(b for b in taken["beats"] if b["id"] == "04-gin-lick-spot")
    spot_prompt = build_beat_prompt(taken, spot)
    assert "enters from the left edge" in spot["action"].lower()
    assert "stiff knees" in spot["action"].lower()
    assert "each step lands late" in spot["action"].lower()
    assert "trailing foot slides" in spot["action"].lower()
    assert "short step behind" in spot["action"].lower()
    assert "matching aya's stride" not in spot["action"].lower()
    assert "match stride" not in spot["action"].lower()
    assert "zombie" not in spot["action"].lower()
    assert "shambling" not in spot["action"].lower()
    assert "undead" not in spot["action"].lower()
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
    assert "stays down" not in jupo["action"].lower()
    assert "leans back onto both palms" not in jupo["action"].lower()
    assert "lies back" not in jupo["action"].lower()
    assert "rises to her feet" not in jupo["action"].lower()
    assert "slide down to the base" in jupo["action"].lower()
    assert "the back of her head on the linoleum" in jupo["action"].lower()
    assert "pleasure-drunk happy smile" in jupo["cast_lock"]["aya"].lower()
    lick = next(b for b in taken["beats"] if b["id"] == "04-gin-lick")
    assert "tongue hanging out" in lick["action"].lower() or "long wet gray tongue" in lick["action"].lower()
    for bid in ("04-gin-jupo", "04-gin-ride", "04-gin-peak"):
        b = next(x for x in taken["beats"] if x["id"] == bid)
        gin_lock = b["cast_lock"]["gin"].lower()
        assert "hanging out" not in gin_lock
        assert "lips pulled back" not in gin_lock
        assert "closed lips" in gin_lock
        assert "tongue inside the mouth" in gin_lock
        assert "hanging out" not in build_beat_prompt(taken, b).lower()
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
    assert "one continuous press" in gin_sex
    assert "hips and the buttocks meet flush" in gin_sex
    assert "hips press together" in gin_sex
    assert next(b for b in fuck["beats"] if b["id"] == "04-gin-walk")["cast"] == ["aya"]

    dog = prepare_episode(raw, gin_override="誘う後背")
    dog_lick = next(b for b in dog["beats"] if b["id"] == "04-gin-lick")
    dog_set = next(b for b in dog["beats"] if b["id"] == "04-gin-set")
    dog_aim = next(b for b in dog["beats"] if b["id"] == "04-gin-press")
    dog_in = next(b for b in dog["beats"] if b["id"] == "04-gin-in")
    assert "behind aya toward the left" in dog_lick["action"].lower()
    assert "lands on her feet" not in dog_lick["action"].lower()
    assert "aya's chest meets gin's back" in dog_set["action"].lower()
    assert "already sitting on her butt" in dog_set["action"].lower()
    assert "drops herself to all fours" in dog_set["action"].lower()
    assert "rises to her feet once" in dog_set["action"].lower()
    assert "set the pose together" in dog_set["action"].lower()
    assert extra_lora_entries(dog_set) == []
    assert extra_lora_entries(dog_aim) == []
    assert "steps onto the same centerline" in dog_aim["action"].lower()
    assert "glans stays pressed on the pussy" in dog_aim["action"].lower()
    assert "travels into" not in dog_aim["action"].lower()
    assert "same centerline" in dog_in["action"].lower()
    assert "one continuous press" in dog_in["action"].lower()
    assert extra_lora_entries(dog_in)[0] == ("siderear", 0.8)
    assert "can't-hold-back" in action_blob(dog, "04-gin") or "ass toward aya" in action_blob(dog, "04-gin")

    stand = prepare_episode(raw, tsuno_override="受け入れる立ちバック")
    meet = next(b for b in stand["beats"] if b["id"] == "04-tsuno-meet")
    join = next(b for b in stand["beats"] if b["id"] == "04-tsuno-in")
    peak = next(b for b in stand["beats"] if b["id"] == "04-tsuno-peak")
    out = next(b for b in stand["beats"] if b["id"] == "04-tsuno-walk")
    assert "palms planted" in meet["action"].lower()
    assert "right edge" in meet["camera"].lower()
    assert "iron bed stays" in meet["action"].lower()
    assert "cup aya's breasts" in meet["action"].lower()
    assert "one large single eye" in meet["action"].lower()
    assert "exactly four long fingers" in meet["action"].lower()
    assert "lunges" not in meet["action"].lower()
    assert "happy accepting smile" in meet["action"].lower()
    assert "lewd pleasure-drunk happy smile" in meet["action"].lower()
    assert "in the pose they already hold" in meet["action"].lower()
    assert "already stopped" in meet["action"].lower()
    tsuno_spot = next(b for b in stand["beats"] if b["id"] == "04-tsuno-meet-spot")
    assert tsuno_spot.get("connect") == "cut"
    assert "sickroom" in tsuno_spot["action"].lower()
    assert "mattress edge" in tsuno_spot["action"].lower()
    assert "strokes the erect ashen-gray 24cm" in tsuno_spot["action"].lower()
    assert "corridor" not in tsuno_spot["action"].lower()
    assert "zombie" not in tsuno_spot["action"].lower()
    assert next(b for b in stand["beats"] if b["id"] == "04-tsuno-stand").get("connect") == "cut"
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
    assert "erect ashen-gray 24cm" in join["action"].lower()
    assert "between the calves" in join["action"].lower()
    assert "low view between the calves" in join["camera"].lower()
    assert "faces left" in join["camera"].lower()
    assert "side-rear" not in join["camera"].lower()
    assert "pale-tan skin" not in meet["action"].lower()
    _assert_insertion_direction(join["action"], build_beat_prompt(stand, join))
    assert "overflows" in peak["action"].lower()
    assert "between the calves" in peak["action"].lower()
    assert "lies on one side" not in peak["action"].lower()
    assert "lewd pleasure-drunk" in peak["action"].lower()
    assert "erect ashen-gray 24cm" in peak["action"].lower()
    assert out["cast"] == ["aya"]
    assert "tongues intertwine" in out["action"].lower()
    assert "tsuno steps out" in out["action"].lower()
    blob = action_blob(stand, "04-tsuno")
    assert "doggy" not in blob and "missionary" not in blob
    assert "zombie" not in build_beat_prompt(stand, join).lower()
    _assert_hospital_bans(stand)
    invite = prepare_episode(raw, tsuno_override="誘う立ちバック")
    invite_meet = next(b for b in invite["beats"] if b["id"] == "04-tsuno-meet")
    assert "looks back" in action_blob(invite, "04-tsuno")
    assert "iron bed stays" in invite_meet["action"].lower()
    assert "cup aya's breasts" in invite_meet["action"].lower()
    assert "lunges" not in invite_meet["action"].lower()
    assert "happy accepting smile" in invite_meet["action"].lower()
    assert "knead them from behind" in invite_meet["action"].lower()
    assert "travels into aya's anus" in invite_meet["action"].lower()
    assert "aya stops and tsuno stops" in invite_meet["action"].lower()
    assert invite_meet["voices"][0]["line"] == "んおおおおぉー"
    invite_in = next(b for b in invite["beats"] if b["id"] == "04-tsuno-in")
    invite_peak = next(b for b in invite["beats"] if b["id"] == "04-tsuno-peak")
    assert "balls of both feet" in invite_in["action"].lower()
    assert "travels into the anus" in invite_in["action"].lower()
    assert "right palm stay on the grey wall" in invite_in["action"].lower()
    invite_ids = [b["id"] for b in invite["beats"]]
    assert invite_ids.index("04-tsuno-hold") + 1 == invite_ids.index("04-tsuno-press")
    assert invite_ids.index("04-tsuno-press") + 1 == invite_ids.index("04-tsuno-in")
    invite_hold = next(b for b in invite["beats"] if b["id"] == "04-tsuno-hold")
    invite_aim = next(b for b in invite["beats"] if b["id"] == "04-tsuno-press")
    assert "siderear" not in extra_keys(invite_hold)
    assert "shaft leaves the anus" in invite_hold["action"].lower()
    assert extra_lora_entries(invite_hold) == []
    assert extra_lora_entries(invite_aim) == []
    assert "steps onto the same centerline" in invite_aim["action"].lower()
    assert "glans stays pressed" in invite_aim["action"].lower()
    assert extra_lora_entries(invite_in)[0] == ("siderear", 0.8)
    assert extra_lora_entries(invite_in)[1] == ("anuspussy", 0.4)
    assert "lies on one side" not in invite_peak["action"].lower()
    assert "buried in the anus" in invite_peak["action"].lower()
    assert next(b for b in invite["beats"] if b["id"] == "04-tsuno-walk")["cast"] == ["aya"]
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
    assert "chest and cheek" in anal_in["action"].lower()
    assert "open wide" in anal_in["action"].lower()
    assert "closed slit" in anal_in["action"].lower()
    assert "into the pussy" not in anal_in["action"].lower()
    assert "into the pussy" not in anal_peak["action"].lower()
    assert "lies on one side" not in anal_peak["action"].lower()
    assert extra_lora_entries(anal_in)[0] == ("siderear", 0.8)
    assert extra_lora_entries(anal_in)[1] == ("anuspussy", 0.4)
    assert "overflows" in anal_peak["action"].lower()
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
    assert nel_in.get("connect") == "cut"
    assert "wide blissful smile" in nel_in["action"].lower()
    assert "travels into the anus" in nel_in["action"].lower()
    assert "pussy" not in nel_in["action"].lower()
    assert "lies on one side" not in nel_peak["action"].lower()
    assert "hold still joined at the base" in nel_peak["action"].lower()
    assert "shaft leaves the anus" not in nel_peak["action"].lower()
    assert "lowers one of aya's feet" not in nel_peak["action"].lower()
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
    """Chain/landing follow the dropdown over authored connect:t2v and connect:cut on the ward.

    First shot stays T2V. Every later GPU beat, including -spot newcomers and authored cuts, is I2V.
    Cut stays T2V except non-gin rib ride seats and peaks authored connect:chain.
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
        assert "already kneeling at the hips" not in kiss["camera"].lower(), pose
        six = next(b for b in ep["beats"] if b["id"] == "06-doggy")
        assert beat_source(six) == "chain", pose
        assert "already kneeling in front" not in six["action"].lower(), pose
        nine = next(b for b in ep["beats"] if b["id"] == "09-join")
        assert beat_source(nine) == "chain", pose
        assert "already kneeling in front" not in nine["action"].lower(), pose
        twelve = next(b for b in ep["beats"] if b["id"] == "12-exit")
        assert beat_source(twelve) == "chain", pose
        if pose == "騎乗位":
            for oral in (kiss, six, nine, twelve):
                assert "kneels" in oral["action"].lower()
                assert "slide down to the base" in oral["action"].lower()
                assert "soles plant" not in oral["action"].lower()
            assert "still kneeling" not in nine["action"].lower()
            nine_wait = next(b for b in ep["beats"] if b["id"] == "09-join-wait")
            assert "legs drop straight down" in nine_wait["action"].lower()
            assert "both knees stay bent" not in nine_wait["action"].lower()
            assert "weight stays on both soles" in nine_wait["action"].lower()
            assert "either side of kana's ribs" in nine_wait["action"].lower()
            assert "directly above the glans" in nine_wait["action"].lower()
            assert "travels into" not in nine_wait["action"].lower()
            assert "pussy hanging directly above the glans" not in nine["action"].lower()
            assert "zoom" not in (nine.get("camera") or "").lower()
            nine_prompt = build_beat_prompt(ep, nine, trigger=merge_trigger("", nine))
            assert "camera distance stays fixed" in nine_prompt.lower()
            assert "zoom" not in nine_prompt.lower()
            assert "aya's face and the partner's face stay in frame" in nine_prompt.lower()
        elif pose == "四つん這い股広げ":
            assert "chest and cheek stay down" in kiss["action"].lower(), pose
            assert "profile side view" in kiss["camera"].lower(), pose
            assert "between the open thighs" in six["action"].lower(), pose
            assert "erect 20cm" in nine["action"].lower(), pose
            assert six.get("connect") == "t2v", pose
        else:
            assert "mouths joined" in kiss["action"].lower(), pose
            assert "mouths joined" in kiss["camera"].lower(), pose
            assert "after the wait" in six["action"].lower(), pose
            assert "kana still stands" in nine["action"].lower(), pose

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
    cunny_chain = next(b for b in gin["beats"] if b["id"] == "04-gin-cunny")
    assert beat_source(cunny_chain) == "chain"
    assert cunny_chain.get("connect") == "chain"
    gin_walk_chain = next(b for b in gin["beats"] if b["id"] == "04-gin-walk")
    assert beat_source(gin_walk_chain) != "t2v"
    assert lick.get("connect") == "t2v"
    assert beat_source(lick) == "chain"
    gin_in = next(b for b in gin["beats"] if b["id"] == "04-gin-jupo")
    assert beat_source(gin_in) == "chain"
    assert "follow subject_definitions" in build_beat_prompt(gin, gin_in)
    toilet = prepare_episode(raw, story_override="受け入れる", toilet_override="pee", connect_override="chain")
    tin = next(b for b in toilet["beats"] if b["id"] == "04-toilet-in")
    assert tin.get("connect") == "t2v"
    assert beat_source(tin) == "chain"

    # Chain/landing: only the first GPU beat stays T2V. Authored t2v and cut do not block it.
    sweeps = [
        dict(story_override="受け入れる"),
        dict(story_override="誘う", invite_pose_override="騎乗位"),
        dict(story_override="誘う", invite_pose_override="四つん這い股広げ"),
        dict(story_override="誘う", invite_pose_override="M字"),
        dict(story_override="回避"),
        dict(story_override="戦って勝つ"),
        dict(story_override="受け入れる", gin_override="犯す", tsuno_override="受け入れる立ちバック", toilet_override="tentacle"),
        dict(story_override="受け入れる", tsuno_override="角・病室で横になって挿入", dog_override="犬・受け入れる"),
        dict(story_override="受け入れる", tsuno_override="角・病室でベッドの後ろアナル"),
        dict(story_override="受け入れる", tsuno_override="角・個室", toilet_override="pee"),
        dict(story_override="受け入れる", toilet_override="和式ミキ"),
    ]
    cut_sweeps = [
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
            if beat_source(beat) == "t2v" and not first:
                raise AssertionError(f"chain left T2V {beat['id']} connect={beat.get('connect')} {kw}")
            spot = str(beat.get("id") or "").endswith("-spot")
            if beat_source(beat) == "chain" and (first or (added and not spot)):
                raise AssertionError(f"chain on a new body {beat['id']} {kw}")
            first = False
            prev = cast
    for kw in cut_sweeps:
        cuts = prepare_episode(raw, connect_override="カット", **kw)
        for beat in cuts["beats"]:
            if is_ui_beat(beat):
                continue
            if beat_source(beat) == "t2v":
                continue
            bid = str(beat.get("id") or "")
            low = str(beat.get("action") or "").lower()
            kept = (
                str(beat.get("connect") or "") == "chain"
                and "gin" not in bid
                and (
                    (
                        bid.endswith("-ride")
                        and "already lies" in low
                        and ("already stands over" in low or "both knees stay bent" in low)
                    )
                    or (
                        bid.endswith("-peak")
                        and "keep the glans inside" in low
                        and "either side of" in low
                        and "ribs" in low
                    )
                    or (
                        bid.endswith("-wait")
                        and "directly above" in low
                        and "soles plant" in low
                    )
                )
            )
            assert kept and beat_source(beat) == "chain", (beat["id"], kw)


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
    assert "chest and cheek stay down" in kiss["action"].lower()
    assert kiss.get("loco") == "planted"
    assert peak.get("loco") == "planted"
    assert beat_source(peak) == "chain"
    assert is_end_connect_beat(walk)
    assert beat_source(walk) == "chain"
    assert "miki" in (walk.get("fade_cast") or [])
    assert "gone from frame one" not in walk["action"].lower()
    kiss_prompt = build_beat_prompt(invite, kiss)
    assert LOWER_TO_FLOOR_CLAUSE in kiss_prompt
    assert PLANTED_PACE_CLAUSE not in kiss_prompt
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
    assert "the hips hold still on that join" in gin_in["action"].lower()
    assert "one continuous press" in gin_in["action"].lower()

    tsuno_in = next(b for b in invite["beats"] if b["id"] == "04-tsuno-in")
    assert "between the calves" in tsuno_in["action"].lower()
    assert "moves the hips forward once" in tsuno_in["action"].lower()
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
    assert "straight down" in ride_in["action"].lower()
    assert "hangs directly above the glans" in ride_in["action"].lower()
    assert "hold still joined at the base" in ride_in["action"].lower()
    assert "either side of miki's ribs" in ride_in["action"].lower()
    assert "stands up from that kneel" not in ride_in["action"].lower()
    assert "squats" not in ride_in["action"].lower()
    assert "folds down" not in ride_in["action"].lower()
    assert "hand holds that raised thigh" not in ride_in["action"].lower()
    assert "sideride" not in extra_keys(ride_in)
    assert "thrust" not in extra_keys(ride_in)
    assert "slides both feet" not in ride_in["action"].lower()
    assert "head on the left" in ride_in["action"].lower()
    assert "the back of her head on the linoleum" in ride_in["action"].lower()
    rei_ride = next(b for b in ride["beats"] if b["id"] == "06-doggy-ride")
    shino_ride = next(b for b in ride["beats"] if b["id"] == "12-exit-ride")
    assert "either side of rei's ribs" in rei_ride["action"].lower()
    assert "either side of shino's ribs" in shino_ride["action"].lower()
    assert "the back of her head on the linoleum" in rei_ride["action"].lower()
    assert "the back of her head on the linoleum" in shino_ride["action"].lower()
    assert "hand holds that raised thigh" not in rei_ride["action"].lower()
    assert "hand holds that raised thigh" not in shino_ride["action"].lower()
    assert "slides both feet" not in rei_ride["action"].lower()
    assert "20cm" in next(b for b in ride["beats"] if b["id"] == "09-join-ride")["action"]
    assert "35cm" in shino_ride["action"]
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
    assert "10 犬" in picked
    assert "11 異種" in picked
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


def test_apply_extra_loras_drops_a_saved_model_page(tmp_path):
    loras = tmp_path / "loras"
    loras.mkdir()
    page = loras / LORA_FILES["furryenh"]
    page.write_bytes(b"<!DOCTYPE html><html>civitai model page</html>")
    preset = {"name": "balance", "stack": [("larry.safetensors", 1.0)], "steps": 8, "trigger": "", "notes": []}
    dropped = apply_extra_loras(preset, {"extra_loras": [["furryenh", 0.55]]}, loras)
    assert dropped["stack"] == preset["stack"]
    assert not page.is_file()
    assert any("furry-enhancer-video.safetensors" in n for n in dropped["notes"])


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


def _refuse_symlink(self, _target):
    raise OSError(95, "Operation not supported")


def test_stage_erotic_unet_moves_when_drive_refuses_symlink(tmp_path, monkeypatch):
    adult = load_episode(KASUMI_ADULT_DIR / "episode.json")
    (tmp_path / "diffusion_models").mkdir()
    payload = _sparse_eros(tmp_path / "erotic" / EROS_MAX_UNET)
    size = payload.stat().st_size
    monkeypatch.setattr(Path, "symlink_to", _refuse_symlink)
    assert stage_erotic_unet(adult, tmp_path) == EROS_MAX_UNET
    placed = tmp_path / "diffusion_models" / EROS_MAX_UNET
    assert placed.is_file() and not placed.is_symlink()
    assert placed.stat().st_size == size
    assert not payload.exists()


def test_stage_erotic_unet_hardlinks_when_move_fails(tmp_path, monkeypatch):
    adult = load_episode(KASUMI_ADULT_DIR / "episode.json")
    (tmp_path / "diffusion_models").mkdir()
    payload = _sparse_eros(tmp_path / "erotic" / EROS_MAX_UNET)
    monkeypatch.setattr(Path, "symlink_to", _refuse_symlink)

    def refuse_replace(self, _target):
        raise OSError(18, "Invalid cross-device link")

    monkeypatch.setattr(Path, "replace", refuse_replace)
    assert stage_erotic_unet(adult, tmp_path) == EROS_MAX_UNET
    placed = tmp_path / "diffusion_models" / EROS_MAX_UNET
    assert placed.is_file() and not placed.is_symlink()
    assert payload.is_file()
    assert os.path.samefile(placed, payload)


def test_stage_erotic_unet_errors_when_drive_cannot_place(tmp_path, monkeypatch):
    adult = load_episode(KASUMI_ADULT_DIR / "episode.json")
    (tmp_path / "diffusion_models").mkdir()
    payload = _sparse_eros(tmp_path / "erotic" / EROS_MAX_UNET)
    monkeypatch.setattr(Path, "symlink_to", _refuse_symlink)

    def refuse_replace(self, _target):
        raise OSError(18, "Invalid cross-device link")

    def refuse_link(*_a, **_k):
        raise OSError(95, "Operation not supported")

    monkeypatch.setattr(Path, "replace", refuse_replace)
    monkeypatch.setattr(os, "link", refuse_link)
    with pytest.raises(EpisodeError, match="diffusion_models"):
        stage_erotic_unet(adult, tmp_path)
    assert payload.is_file()
    assert not (tmp_path / "diffusion_models" / EROS_MAX_UNET).exists()


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

    def fake_fetch(url: str, dest: Path, *, min_bytes: int = 100, **_kwargs) -> bool:
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


def test_page_only_loras_are_not_fetched(tmp_path, monkeypatch):
    import h3_episode as mod

    calls: list[str] = []
    monkeypatch.setattr(mod, "fetch_text", lambda *a, **_k: calls.append(a[0]) or False)
    notes = ensure_episode_loras(
        {"render": {"lora_prefetch": ["furryenh", "slime", "anthro", "blowjob"]}},
        tmp_path,
    )
    assert calls == [LORA_URLS["blowjob"]]
    assert notes == [
        "skip page furry-enhancer-video.safetensors",
        "skip page slime_girls-MMH3-v1.0.safetensors",
        "skip page eleptors-furry-anthro-lora-minimax-h3.safetensors",
        "fetch failed MM-H3_Blowjob_v3.safetensors",
    ]


def test_civitai_redirect_drops_authorization_before_the_weight_host(monkeypatch):
    import h3_episode as mod

    header = b'{"a":1}'
    body = len(header).to_bytes(8, "little") + header
    seen: dict[str, str | None] = {}

    class CDN(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def do_GET(self):  # noqa: N802
            seen["cdn_auth"] = self.headers.get("Authorization")
            payload = b"no" if self.headers.get("Authorization") else body
            self.send_response(400 if self.headers.get("Authorization") else 200)
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, fmt, *args):  # noqa: ANN001
            return

    class Hub(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def do_GET(self):  # noqa: N802
            seen["hub_auth"] = self.headers.get("Authorization")
            loc = f"http://127.0.0.1:{cdn.server_address[1]}/w.safetensors"
            self.send_response(307)
            self.send_header("Location", loc)
            self.send_header("Content-Length", "0")
            self.end_headers()

        def log_message(self, fmt, *args):  # noqa: ANN001
            return

    cdn = ThreadingHTTPServer(("127.0.0.1", 0), CDN)
    hub = ThreadingHTTPServer(("127.0.0.1", 0), Hub)
    for srv in (cdn, hub):
        threading.Thread(target=srv.serve_forever, daemon=True).start()
    monkeypatch.setattr(mod, "_civitai_host", lambda netloc: str(netloc).startswith("localhost"))
    try:
        url = f"http://localhost:{hub.server_address[1]}/api/download/models/1"
        resp = mod._open_civitai(
            url,
            {"User-Agent": "h3-episode", "Authorization": "Bearer secret-token"},
            timeout=5,
        )
        got = resp.read()
        resp.close()
    finally:
        hub.shutdown()
        cdn.shutdown()
        hub.server_close()
        cdn.server_close()
    assert seen["hub_auth"] == "Bearer secret-token"
    assert seen["cdn_auth"] is None
    assert got == body
    quoted = mod._quote_http_url("https://cdn.example/Minimax H3.safetensors")
    assert " " not in urllib.parse.urlsplit(quoted).path


def test_fetch_text_sends_civitai_token_only_to_the_opener(tmp_path, monkeypatch):
    import h3_episode as mod

    class Resp:
        def __enter__(self):
            self._sent = False
            return self

        def __exit__(self, *args):
            return False

        def read(self, _n):
            if self._sent:
                return b""
            self._sent = True
            return b"x" * 200

    seen: dict[str, str] = {}

    def fake_open(url, headers, timeout=120):
        seen["url"] = url
        seen["auth"] = headers.get("Authorization")
        return Resp()

    monkeypatch.setattr(mod, "_open_civitai", fake_open)
    monkeypatch.setattr(mod, "_civitai_token", lambda: "secret-token")
    dest = tmp_path / "a.safetensors"
    assert fetch_text("https://civitai.com/api/download/models/1?fileId=2", dest, min_bytes=10)
    assert seen["auth"] == "Bearer secret-token"
    assert b"secret-token" not in dest.read_bytes()


def test_fetch_text_keeps_episode_json_and_drops_a_json_error_page(tmp_path, monkeypatch):
    body = b'{\n  "schema": "h3-episode/v1"\n}' + (b" " * 120)

    def fake_retrieve(url: str, dest) -> None:
        Path(dest).write_bytes(body)

    monkeypatch.setattr("h3_episode.urllib.request.urlretrieve", fake_retrieve)
    script = tmp_path / "episode.json"
    assert fetch_text("https://example.invalid/episode.json", script, allow_json=True)
    assert script.read_bytes().startswith(b"{")
    weight = tmp_path / "page.safetensors"
    assert not fetch_text("https://example.invalid/page.safetensors", weight)
    assert not weight.exists()


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


def _walk_extra_lora_keys(node):
    found = []
    if isinstance(node, dict):
        if "extra_loras" in node:
            found.extend(key for key, _strength in extra_lora_entries(node))
        for value in node.values():
            found.extend(_walk_extra_lora_keys(value))
    elif isinstance(node, list):
        for value in node:
            found.extend(_walk_extra_lora_keys(value))
    return found


def test_charswap_and_anime2real_register_on_ref2va_only(tmp_path):
    assert LORA_FILES["charswap"] == "h3_character_swap_pro4500_1000.safetensors"
    assert LORA_FILES["anime2real"] == "Anime2Realsim__H3.safetensors"
    assert LORA_URLS["charswap"] == (
        "https://huggingface.co/akatz-ai/MiniMax-H3-Character-Swap-LoRA/resolve/main/"
        "h3_character_swap_pro4500_1000.safetensors"
    )
    assert LORA_URLS["anime2real"] == (
        "https://huggingface.co/LiseTY/Minimax-H3-ref2v_Anime_2_Realism/resolve/main/"
        "Anime2Realsim__H3.safetensors"
    )
    assert LORA_URLS["charswap"].endswith(".safetensors")
    assert LORA_URLS["anime2real"].endswith(".safetensors")
    assert "/blob/" not in LORA_URLS["charswap"] and "/blob/" not in LORA_URLS["anime2real"]
    assert LORA_STRENGTHS["charswap"] == 1.0
    assert LORA_STRENGTHS["anime2real"] == 1.0
    assert ANIME2REAL_TRIGGER == "LumiReal"
    assert "charswap" not in _walk_extra_lora_keys(load_episode(HOSPITAL_DIR / "episode.json"))
    assert "anime2real" not in _walk_extra_lora_keys(load_episode(HOSPITAL_DIR / "episode.json"))

    loras = tmp_path / "loras"
    loras.mkdir()
    for key in ("charswap", "anime2real", "combat", "turbo4", "turbo8", "larry", "cinema"):
        (loras / LORA_FILES[key]).write_bytes(b"x")
    ref2va = "minimax_h3_ref2va_pruned_int8_convrot.safetensors"
    fl2va = "minimax_h3_fl2va_pruned_int8_convrot.safetensors"
    preset = {
        "name": "daily",
        "stack": [(LORA_FILES["larry"], 1.0), (LORA_FILES["cinema"], 0.65), (LORA_FILES["turbo4"], 1.0)],
        "steps": 8,
        "trigger": "DY",
        "notes": [],
    }
    both = {"extra_loras": ["charswap", "anime2real"], "trigger": "keep"}
    stacked = apply_extra_loras(preset, both, loras, unet=ref2va)
    names = [item[0] for item in stacked["stack"]]
    assert (LORA_FILES["charswap"], 1.0) in stacked["stack"]
    assert (LORA_FILES["anime2real"], 0.5) in stacked["stack"]
    assert LORA_FILES["larry"] not in names
    assert LORA_FILES["turbo4"] not in names
    assert LORA_FILES["cinema"] not in names
    assert any("turbo4/turbo8/larry skipped" in note for note in stacked["notes"])
    assert any("cinema skipped (anime2real)" in note for note in stacked["notes"])
    assert merge_trigger("DY", both) == "DY\nkeep\nLumiReal"
    assert merge_trigger("DY", {"extra_loras": ["charswap"], "trigger": "keep"}) == "DY\nkeep"
    assert merge_trigger("", {"extra_loras": ["anime2real"], "trigger": "LumiReal"}) == "LumiReal"

    half = {"extra_loras": [["charswap", 0.5], ["anime2real", 0.5]]}
    halved = apply_extra_loras(preset, half, loras, unet=ref2va)
    assert (LORA_FILES["charswap"], 0.5) in halved["stack"]
    assert (LORA_FILES["anime2real"], 0.5) in halved["stack"]

    only_real = apply_extra_loras(
        {
            "name": "speed",
            "stack": [(LORA_FILES["turbo8"], 1.0), (LORA_FILES["cinema"], 0.65)],
            "steps": 8,
            "notes": [],
        },
        {"extra_loras": ["anime2real"]},
        loras,
        unet=ref2va,
    )
    assert (LORA_FILES["anime2real"], 1.0) in only_real["stack"]
    assert LORA_FILES["cinema"] not in [item[0] for item in only_real["stack"]]
    assert LORA_FILES["turbo8"] not in [item[0] for item in only_real["stack"]]

    turbo8 = {
        "name": "speed",
        "stack": [(LORA_FILES["turbo8"], 1.0), (LORA_FILES["cinema"], 0.65)],
        "steps": 8,
        "notes": [],
    }
    only_swap = apply_extra_loras(turbo8, {"extra_loras": ["charswap"]}, loras, unet=ref2va)
    swap_names = [item[0] for item in only_swap["stack"]]
    assert (LORA_FILES["charswap"], 1.0) in only_swap["stack"]
    assert LORA_FILES["turbo8"] not in swap_names
    assert LORA_FILES["cinema"] in swap_names

    fl2 = apply_extra_loras(preset, both, loras, unet=fl2va)
    assert LORA_FILES["charswap"] not in [item[0] for item in fl2["stack"]]
    assert LORA_FILES["anime2real"] not in [item[0] for item in fl2["stack"]]
    assert LORA_FILES["larry"] in [item[0] for item in fl2["stack"]]
    assert LORA_FILES["turbo4"] in [item[0] for item in fl2["stack"]]
    assert any("Ref2VA UNet only" in note for note in fl2["notes"])

    hybrid = apply_extra_loras(preset, both, loras, unet=EROS_MAX_UNET)
    assert LORA_FILES["charswap"] not in [item[0] for item in hybrid["stack"]]
    assert LORA_FILES["anime2real"] not in [item[0] for item in hybrid["stack"]]
    assert any("Ref2VA UNet only" in note for note in hybrid["notes"])

    bare = {"name": "daily", "stack": [(LORA_FILES["larry"], 1.0)], "steps": 8, "trigger": "DY", "notes": []}
    fight = {"extra_loras": ["combat", "charswap", "anime2real"]}
    fought = apply_extra_loras(bare, fight, loras, unet=ref2va)
    assert fought["stack"][-1] == (LORA_FILES["combat"], 1.0)
    assert LORA_FILES["charswap"] not in [item[0] for item in fought["stack"]]
    assert LORA_FILES["anime2real"] not in [item[0] for item in fought["stack"]]
    assert any("combat has priority" in note for note in fought["notes"])
    assert fought["steps"] == COMBAT_STEPS


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
    assert "H3_EPISODE_START'] = ''" in script
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


def test_render_start_follows_the_prepared_route(tmp_path):
    beats = [
        {"id": "a", "source": "t2v", "action": "A walks."},
        {"id": "b", "source": "chain", "action": "B stays."},
        {"id": "c", "source": "chain", "action": "C stays."},
    ]
    raw = tmp_path / "raw"
    raw.mkdir()
    for beat in beats:
        (raw / f"{beat['id']}.mp4").write_bytes(b"x")
    status = {"beats": {beat["id"]: {"sig": beat_content_sig(beat)} for beat in beats}}
    assert render_start_index(beats, "", raw, status) == 0
    assert render_start_index(beats, "最初から", raw, status) == 0
    assert render_start_index(beats, "c", raw, status) == 2
    status["beats"]["b"]["sig"] = "stale"
    assert render_start_index(beats, "c", raw, status) == 1
    status["beats"]["b"]["sig"] = beat_content_sig(beats[1])
    (raw / "b.mp4").unlink()
    assert render_start_index(beats, "c", raw, status) == 1
    (raw / "a.mp4").unlink()
    assert render_start_index(beats, "c", raw, status) == 0
    with pytest.raises(EpisodeError, match="今の話"):
        render_start_index(beats, "04-toilet", raw, status)
    assert beat_needs_previous(beats[2])
    assert not beat_needs_previous(beats[0])


def test_hospital_start_scene_uses_the_colab_route(tmp_path):
    raw_ep = load_episode(HOSPITAL_DIR / "episode.json")
    off = prepare_episode(
        raw_ep,
        story_override="accept",
        gin_override="off",
        toilet_override="tentacle",
        connect_override="chain",
    )
    with pytest.raises(EpisodeError, match="04-gin-cunny"):
        render_start_index(off["beats"], "04-gin-cunny", tmp_path, {"beats": {}})
    on = prepare_episode(
        raw_ep,
        story_override="accept",
        gin_override="taken",
        toilet_override="tentacle",
        connect_override="chain",
    )
    ids = [b["id"] for b in on["beats"]]
    assert ids.index("04-toilet") < ids.index("04-gin-cunny")
    raw = tmp_path / "raw"
    raw.mkdir()
    saved = {"beats": {}}
    for beat in on["beats"]:
        (raw / f"{beat['id']}.mp4").write_bytes(b"x")
        saved["beats"][beat["id"]] = {"sig": beat_content_sig(beat)}
    toilet_at = render_start_index(on["beats"], "04-toilet", raw, saved)
    assert on["beats"][toilet_at]["id"] == "04-toilet"
    assert "left nipple" in on["beats"][toilet_at]["action"]
    cunny_at = render_start_index(on["beats"], "04-gin-cunny", raw, saved)
    assert on["beats"][cunny_at]["id"] == "04-gin-cunny"
    assert "clitoris GROWS" in on["beats"][cunny_at]["action"]


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


def test_hospital_dog_and_species_slots():
    raw = load_episode(HOSPITAL_DIR / "episode.json")
    assert MAX_BEATS == 80
    off = prepare_episode(raw, story_override="受け入れる")
    assert not any(str(b["id"]).startswith("04-dog") for b in off["beats"])
    assert not any("slime" in str(b["id"]) or "anthro" in str(b["id"]) for b in off["beats"])
    assert not any(c in ("slime", "anthro", "dog") for b in off["beats"] for c in (b.get("cast") or []))
    stacked = prepare_episode(
        raw,
        story_override="受け入れる",
        gin_override="犯される",
        tsuno_override="立ちバック",
        dog_override="誘う口",
        species_override="スライム",
        connect_override="chain",
    )
    assert validate_episode(stacked, root=HOSPITAL_DIR) == []
    assert len(stacked["beats"]) <= 80
    ids = [b["id"] for b in stacked["beats"]]
    assert ids.index("04-gin-lick") < ids.index("04-dog-spot") < ids.index("04-slime-spot")
    assert not any("anthro" in bid for bid in ids)
    for beat in stacked["beats"]:
        extra = [c for c in (beat.get("cast") or []) if c != "aya"]
        assert len(extra) <= 1
    slime_only = prepare_episode(raw, species_override="slime")
    anthro_only = prepare_episode(raw, species_override="anthro")
    slime_meet = next(b for b in slime_only["beats"] if b["id"] == "04-slime-meet")
    assert "gel woman's hips move forward once" in slime_meet["action"].lower()
    assert "both stop the instant the glans is inside" in slime_meet["action"].lower()
    slime_peak = next(b for b in slime_only["beats"] if b["id"] == "04-slime-peak")
    assert "short forward moves from behind" in slime_peak["action"].lower()
    anthro_meet = next(b for b in anthro_only["beats"] if b["id"] == "04-anthro-meet")
    assert "furred biped's hips move forward once" in anthro_meet["action"].lower()
    assert any(b["id"].startswith("04-slime") for b in slime_only["beats"])
    assert not any("anthro" in b["id"] for b in slime_only["beats"])
    assert any(b["id"].startswith("04-anthro") for b in anthro_only["beats"])
    assert not any("slime" in b["id"] for b in anthro_only["beats"])
    banned = ("zombie", "blood", "corpse", "futanari")
    for ep in (stacked, anthro_only, prepare_episode(raw, dog_override="invite_rear")):
        for beat in ep["beats"]:
            if not str(beat["id"]).startswith(("04-dog", "04-slime", "04-anthro")):
                continue
            blob = str(beat.get("action") or "").lower()
            for word in banned:
                assert word not in blob
    spot = next(b for b in stacked["beats"] if b["id"] == "04-dog-spot")
    spot_action = spot["action"]
    assert "LEAPS" not in spot_action
    assert "head points LEFT" in spot_action
    assert "tail points to the RIGHT" in spot_action
    assert "WALKS toward the RIGHT" in spot_action
    assert spot["cast"] == ["aya", "dog"]
    assert "gin" in {b.get("encounter") or "" for b in stacked["beats"] if str(b["id"]).startswith("04-gin")} or any(
        str(b["id"]).startswith("04-gin") for b in stacked["beats"]
    )
    assert stacked["render"]["gin"] == "taken"
    assert stacked["render"]["dog"] == "invite_oral"
    gin_i = ids.index("04-gin-walk")
    assert ids[gin_i + 1] == "04-tsuno-meet-spot"
    assert stacked["beats"][gin_i]["hud"]["complete"] is False
    assert stacked["beats"][-1]["id"] != "04-gin-walk"
    full = prepare_episode(
        raw,
        story_override="誘う",
        invite_pose_override="対面座位",
        toilet_override="アナル指",
        gin_override="犯される",
        tsuno_override="フルネルソンアナル",
        dog_override="誘う口",
        species_override="スライム",
        connect_override="前の最終フレームから続ける",
        scenes_override="miki=inherit,rei=invite_ride,kana=invite_all_fours,shino=invite_m_open",
    )
    assert validate_episode(full, root=HOSPITAL_DIR) == []
    full_ids = [b["id"] for b in full["beats"]]
    assert len(full_ids) <= 80
    gin_i = full_ids.index("04-gin-walk")
    assert full_ids[gin_i + 1] == "04-tsuno-meet-spot"
    assert "04-dog-spot" in full_ids and "04-slime-spot" in full_ids
    assert full_ids.index("04-gin-walk") < full_ids.index("04-tsuno-meet-spot") < full_ids.index("05-ui-rei")
    assert full["beats"][-1]["id"] == "12-exit-kiss"
    assert all(not (b.get("hud") or {}).get("complete") for b in full["beats"])
    tsuno_i = full_ids.index("04-tsuno-walk")
    assert full_ids[tsuno_i + 1] == "04-dog-spot"
    assert full_ids.index("04-dog-walk") < full_ids.index("04-slime-spot")
    tsuno_walk = full["beats"][tsuno_i]
    assert "t-junction" in tsuno_walk["action"].lower()
    tsuno_prompt = build_beat_prompt(full, tsuno_walk)
    assert "as the exit" not in tsuno_prompt.lower()
    assert "lit open doorway" not in tsuno_prompt.lower()
    last_prompt = build_beat_prompt(full, full["beats"][-1])
    assert "as the exit" in last_prompt.lower()


def test_hospital_invite_sit_is_face_to_face():
    raw = load_episode(HOSPITAL_DIR / "episode.json")
    assert INVITE_POSE_OVERLAY_KEYS["sit"] == "invite_pose_sit"
    for beat in raw["beats"]:
        if beat.get("id") in ("03-kiss", "06-doggy", "09-join", "12-exit"):
            assert "invite_pose_sit" in beat
    sat = prepare_episode(raw, story_override="誘う", invite_pose_override="対面座位")
    assert validate_episode(sat, root=HOSPITAL_DIR) == []
    assert len(sat["beats"]) <= MAX_BEATS
    miki_zai = next(b for b in sat["beats"] if b["id"] == "03-kiss-zai1")
    miki_act = miki_zai["action"]
    assert "toward the LEFT" in miki_act
    assert "toward the RIGHT" in miki_act
    assert "already SITS on the linoleum" in miki_act
    assert "WRAP OUTSIDE Miki's waist" in miki_act
    assert "calves LOCK behind Miki's back" in miki_act
    assert "feet meet behind Miki, off the linoleum" in miki_act
    assert "HOLD still joined at the BASE until the last frame" in miki_act
    assert "24cm" in miki_act
    assert "hips move straight up" not in miki_act.lower()
    assert "knees plant" not in miki_act.lower()
    assert "ankles cross" not in miki_act.lower()
    assert extra_keys(miki_zai) == ["kiss", "mystic"]
    for bid, cm in (("06-doggy-zai1", "24cm"), ("09-join-zai1", "20cm"), ("12-exit-zai1", "35cm")):
        beat = next(b for b in sat["beats"] if b["id"] == bid)
        act = beat["action"]
        low = act.lower()
        assert "already SITS on the linoleum" in act
        assert "arms around each other's backs" in low
        assert "mouths stay joined" in low
        assert "wrap outside" in low
        assert "calves lock behind" in low
        assert "off the linoleum" in low
        assert "hold still joined at the base until the last frame" in low
        assert cm in act
        assert "knees plant" not in low
        assert "ankles cross" not in low
        assert "hips move straight up" not in low
        assert "thrust" not in extra_keys(beat)
        assert "sideride" not in extra_keys(beat)
        assert extra_keys(beat)[0] == "kiss"
    for bid, name in (
        ("03-kiss-zai2", "Miki"),
        ("06-doggy-zai2", "Rei"),
        ("09-join-zai2", "Kana"),
        ("12-exit-zai2", "Shino"),
    ):
        beat = next(b for b in sat["beats"] if b["id"] == bid)
        low = beat["action"].lower()
        assert f"wrap outside {name.lower()}'s waist" in low
        assert "calves lock behind" in low
        assert "off the linoleum" in low
        assert "hips keep moving straight up" in low
        assert "ankles stayed" not in low
        assert "thrust" not in extra_keys(beat)
        prompt = build_beat_prompt(sat, beat)
        assert "upright on the lap" in prompt.lower()
        assert "feet meet behind the partner, off the linoleum" in prompt.lower()
    for bid in ("03-kiss-peak", "06-doggy-peak", "09-join-peak", "12-exit-peak"):
        beat = next(b for b in sat["beats"] if b["id"] == bid)
        low = beat["action"].lower()
        assert "astride the lap" in low
        assert "wrap outside" in low
        assert "off the linoleum" in low
        assert "finishes inside" in low
        assert "thrust" not in extra_keys(beat)
        assert "sideride" not in extra_keys(beat)
    drop = next(b for b in sat["beats"] if b["id"] == "12-exit-drop")
    assert "thighs wrap outside" in drop["action"].lower()
    assert "tips backward" in drop["action"].lower()
    assert "slides out" in drop["action"].lower()
    walk = next(b for b in sat["beats"] if b["id"] == "03-kiss-walk")
    assert walk["trim"]["seconds"] == 8.0
    assert walk.get("connect") == "end"
    assert "arms around each other's backs" in walk["action"]
    assert "only aya walks right" in walk["action"].lower()
    assert "kiss" in [x[0] if isinstance(x, list) else x for x in walk["extra_loras"]]


def test_hospital_invite_embrace_starts_after_the_spot():
    raw = load_episode(HOSPITAL_DIR / "episode.json")
    ep = prepare_episode(
        raw,
        story_override="誘う",
        invite_pose_override="抱擁ベロチュー→壁片足→クンニ→両足抱え",
        tsuno_override="フルネルソンアナル",
        gin_override="犯される",
        dog_override="誘う口",
        species_override="スライム",
    )
    assert validate_episode(ep, root=HOSPITAL_DIR) == []
    assert len(ep["beats"]) <= MAX_BEATS
    ids = [b["id"] for b in ep["beats"]]
    assert "01-cover" in ids
    assert "03-kiss" not in ids
    hug = next(b for b in ep["beats"] if b["id"] == "03-kiss-hug")
    assert hug["id"].endswith("-hug")
    assert ids.index("03-kiss-hug") > ids.index("01-cover")
    assert "wrap behind aya's back" in hug["action"].lower()
    assert "french kiss" in hug["action"].lower()
    assert "kiss" in [x[0] if isinstance(x, list) else x for x in hug["extra_loras"]]
    wall = next(b for b in ep["beats"] if b["id"] == "03-kiss-wall")["action"].lower()
    assert "back is against the peeling wall" in wall
    assert "one foot" in wall or "other foot stays planted" in wall
    cunny = next(b for b in ep["beats"] if b["id"] == "03-kiss-cunny")
    assert "squats" in cunny["action"].lower()
    assert "tongue licks" in cunny["action"].lower()
    assert cunny["trigger"] == "performing cunnilingus"
    hold_beat = next(b for b in ep["beats"] if b["id"] == "03-kiss-hold")
    hold = hold_beat["action"].lower()
    assert "miki stands." not in hold
    assert "knees come up" in hold
    assert "feet leave the linoleum" in hold
    assert "feet stay in the air" in hold
    assert "shaft stays outside" in hold
    assert "travels into" not in hold
    assert "wrap behind miki's back" in hold
    assert "mouths stay joined" in hold
    assert "thrust" not in extra_keys(hold_beat)
    assert beat_loco(hold_beat) != "planted"
    assert "kiss" in extra_keys(hold_beat)
    entered = next(b for b in ep["beats"] if b["id"] == "03-kiss-in")
    entered_low = entered["action"].lower()
    assert "travels into the hairless pussy" in entered_low
    assert "one continuous press" in entered_low
    assert "hold still joined at the base" in entered_low
    assert "buried to the root" in entered_low
    assert "knees stay up" in entered_low
    assert beat_loco(entered) != "planted"
    assert "04-tsuno-in" not in ids
    tsuno_hold = next(b for b in ep["beats"] if b["id"] == "04-tsuno-hold")["action"].lower()
    assert "travels into the hairless pussy" in tsuno_hold
    assert "feet leave the linoleum" not in tsuno_hold
    peak_beat = next(b for b in ep["beats"] if b["id"] == "03-kiss-peak")
    peak = peak_beat["action"].lower()
    assert "finishes inside" in peak
    assert "orgasm faces" in peak
    assert "both knees held up" in peak
    assert beat_loco(peak_beat) != "planted"
    cunny_act = cunny["action"]
    assert "stands in front of Aya on both feet" in cunny_act
    walk = next(b for b in ep["beats"] if b["id"] == "03-kiss-walk")
    assert walk["trim"]["seconds"] == 8.0
    assert "saliva string" in walk["action"].lower()
    assert "shaft pulls out" in walk["action"].lower()
    for beat in ep["beats"]:
        if beat["id"].startswith("03-kiss-"):
            assert "駅弁" not in beat["action"]
            assert "cowgirl" not in beat["action"].lower()
    spot = next(b for b in ep["beats"] if b["id"] == "06-doggy-hug-spot")
    rei_hug = next(b for b in ep["beats"] if b["id"] == "06-doggy-hug")
    assert ids.index(spot["id"]) < ids.index(rei_hug["id"])
    tsuno = next(b for b in ep["beats"] if b["id"] == "04-tsuno-hug")
    assert "stands directly behind aya" in tsuno["action"].lower()
    assert "leave the shaft" in tsuno["action"].lower()
    assert "04-tsuno-meet" not in ids
    assert "04-tsuno-in" not in ids
    gin_ids = [i for i in ids if i.startswith("04-gin-")]
    assert gin_ids
    assert not any(i.endswith("-hug") for i in gin_ids)
    assert not any(i.startswith("04-dog-hug") or i.startswith("04-slime-hug") for i in ids)
    off = prepare_episode(raw, story_override="誘う", invite_pose_override="embrace", tsuno_override="off")
    off_ids = [b["id"] for b in off["beats"]]
    assert "04-tsuno-hug" not in off_ids
    cover = next(b for b in ep["beats"] if b["id"] == "01-cover")
    assert "strokes the erect 24cm" in cover["action"].lower()
    prompt = build_beat_prompt(ep, cover)
    assert "24cm" in prompt
    assert "22cm" not in prompt


def test_hospital_dog_orientation_and_embrace_lift():
    raw = load_episode(HOSPITAL_DIR / "episode.json")
    marker = next(b for b in raw["beats"] if b["id"] == "04-dog")
    spots = []
    for key in ("on_dog_evade", "on_dog_accept", "on_dog_invite_rear", "on_dog_invite_oral"):
        spot = next(x for x in marker[key] if x["id"] == "04-dog-spot")
        spots.append(spot["action"])
        assert "LEAPS" not in spot["action"].upper()
        assert "ENTERS from the RIGHT" not in spot["action"]
        assert "head points LEFT toward Aya" in spot["action"]
        assert "tail points to the RIGHT wall" in spot["action"]
        assert spot["source"] == "chain" and spot["connect"] == "chain"
    assert len(set(spots)) == 1
    faced = prepare_episode(raw, dog_override="誘う口")
    spot_beat = next(b for b in faced["beats"] if b["id"] == "04-dog-spot")
    spot_prompt = build_beat_prompt(faced, spot_beat).lower()
    assert "leaps" not in spot_prompt and "leap" not in spot_prompt
    assert "nothing new enters" not in spot_prompt
    assert "enters from the right" not in spot_prompt
    leaped = dict(spot_beat)
    leaped["action"] = spot_beat["action"] + " The quadruped LEAPS in from the RIGHT edge and lands on the RIGHT."
    leaped_prompt = build_beat_prompt(faced, leaped).lower()
    assert "leap" not in leaped_prompt
    assert "lands on the right" not in leaped_prompt
    pee = prepare_episode(raw, story_override="受け入れる", toilet_override="pee", tsuno_override="off")
    assert "on_toilet_pee" in next(b for b in raw["beats"] if b["id"] == "04-peek")
    assert any(str(b["id"]).startswith("04-toilet") for b in pee["beats"])
    assert not any(str(b["id"]).startswith("04-tsuno") for b in pee["beats"])
    accept = next(x for x in marker["on_dog_accept"] if x["id"] == "04-dog-accept")
    assert "rises onto its hind paws" in accept["action"]
    assert "hips move forward once" in accept["action"].lower()
    assert "one continuous press" in accept["action"].lower()
    accept_cum = next(x for x in marker["on_dog_accept"] if x["id"] == "04-dog-cum")
    assert "short forward moves" in accept_cum["action"].lower()
    assert "glans stays inside" in accept_cum["action"].lower()
    oral = prepare_episode(raw, dog_override="invite_oral")
    wait = next(b for b in oral["beats"] if b["id"] == "04-dog-wait")
    assert "turns prone" not in wait["action"].lower()
    assert "on her back" in wait["action"].lower()
    jupo = next(b for b in oral["beats"] if b["id"] == "04-dog-jupo")
    assert "under the belly" in jupo["action"]
    assert "hind paws" in jupo["action"].lower()
    assert "long wet dark tongue" not in jupo["action"].lower()
    seated = next(b for b in oral["beats"] if b["id"] == "04-dog-in")
    assert "thrust" not in extra_keys(seated)
    assert "HOLD still joined at the BASE" in seated["action"]
    assert "already lies fully on her back" in seated["action"].lower()
    assert "meet her groin" in seated["action"].lower()
    assert "buttocks" not in seated["action"].lower()
    assert seated.get("turbo") is False
    assert "one clear erect 24cm" in seated["action"].lower()
    assert "MOVE FORWARD once" in seated["action"]
    assert "the glans meets the pussy" in seated["action"].lower()
    rear = prepare_episode(raw, dog_override="invite_rear")
    mount = next(b for b in rear["beats"] if b["id"] == "04-dog-mount")
    assert "thrust" not in extra_keys(mount)
    assert "chest and cheek" in mount["action"]
    rear_wait = next(b for b in rear["beats"] if b["id"] == "04-dog-wait")
    assert "chest and one cheek" in rear_wait["action"]
    pose_ban = ("zombie", "blood", "corpse", "doggy", "missionary", "cowgirl")
    for ep in (oral, rear):
        for beat in ep["beats"]:
            if not str(beat["id"]).startswith("04-dog"):
                continue
            blob = str(beat.get("action") or "").lower()
            for word in pose_ban:
                assert word not in blob, beat["id"]
            assert "駅弁" not in beat["action"]
            assert "anthro" not in extra_keys(beat)
            assert "doggy" not in extra_keys(beat)
            assert "jacko" not in extra_keys(beat)
            assert "Doggy style" not in beat["action"]
    emb = prepare_episode(
        raw,
        story_override="誘う",
        invite_pose_override="embrace",
        tsuno_override="フルネルソンアナル",
    )
    lifts = [b for b in emb["beats"] if "feet leave the linoleum" in str(b.get("action") or "")]
    assert [b["id"] for b in lifts] == ["03-kiss-hold", "06-doggy-hold", "09-join-hold", "12-exit-hold"]
    names = []
    for beat in lifts:
        assert beat["id"].endswith("-hold")
        assert beat_loco(beat) != "planted"
        assert "loco" not in beat
        act = beat["action"]
        low = act.lower()
        assert " stands." not in low
        assert "knees come up" in low
        assert "feet stay in the air" in low
        assert "shaft stays outside" in low
        assert "travels into" not in low
        assert "thrust" not in extra_keys(beat)
        assert " not " not in f" {low} "
        for word in pose_ban:
            assert word not in low
        assert "駅弁" not in act
        names.append(act.split("'")[0].split()[-1] if "'" in act else "")
        prompt = build_beat_prompt(emb, beat)
        assert "feet stay planted" not in prompt.lower()
        assert "do not invent a walk cycle" not in prompt.lower()
        assert "snappy" in prompt.lower()
    tsuno_hold_beat = next(b for b in emb["beats"] if b["id"] == "04-tsuno-hold")
    tsuno_act = tsuno_hold_beat["action"]
    names.append(tsuno_act.split("'")[0].split()[-1] if "'" in tsuno_act else "")
    assert "travels into the hairless pussy" in tsuno_act.lower()
    assert "feet leave the linoleum" not in tsuno_act.lower()
    assert set(names) >= {"Miki", "Rei", "Kana", "Shino", "Tsuno"}
    holds = lifts + [tsuno_hold_beat]
    peaks = [b for b in emb["beats"] if b["id"].endswith("-peak") and "both knees held up" in b["action"].lower()]
    assert len(peaks) == len(holds)
    for beat in peaks:
        assert beat_loco(beat) != "planted"
        assert "thrust" in extra_keys(beat)
        assert "short vertical moves" in beat["action"].lower()


def test_hospital_nongin_ride_seats_beside_the_ribs():
    raw = load_episode(HOSPITAL_DIR / "episode.json")
    ride = prepare_episode(raw, story_override="誘う", invite_pose_override="騎乗位")
    pairs = (
        ("03-kiss", "Miki", "24cm"),
        ("06-doggy", "Rei", "24cm"),
        ("09-join", "Kana", "20cm"),
        ("12-exit", "Shino", "35cm"),
    )
    pose_ban = ("zombie", "blood", "corpse", "doggy", "missionary", "cowgirl")
    cut = prepare_episode(
        raw,
        story_override="誘う",
        invite_pose_override="騎乗位",
        connect_override="t2v",
    )
    for base, partner, cm in pairs:
        oral = next(b for b in ride["beats"] if b["id"] == base)
        assert "lips leaving the shaft" not in oral["action"]
        assert "still kneeling" not in oral["action"].lower()
        assert "already lies fully on her back" in oral["action"].lower()
        assert "kneels" in oral["action"].lower()
        assert "soles plant" not in oral["action"].lower()
        assert "slide down to the base" in oral["action"].lower()
        assert "already stands over" not in oral["action"].lower()
        waited = next(b for b in ride["beats"] if b["id"] == f"{base}-wait")
        assert "rises once from the kneel" in waited["action"].lower()
        assert "legs drop straight down" in waited["action"].lower()
        assert "near foot crosses in front of the belly" in waited["action"].lower()
        assert "both knees stay bent" not in waited["action"].lower()
        assert "weight stays on both soles" in waited["action"].lower()
        assert f"either side of {partner.lower()}'s ribs" in waited["action"].lower()
        assert "DIRECTLY ABOVE" in waited["action"]
        assert "TRAVELS INTO" not in waited["action"]
        assert "LOWERS" in next(b for b in ride["beats"] if b["id"] == f"{base}-ride")["action"]
        assert "HOLD" in next(b for b in ride["beats"] if b["id"] == f"{base}-ride")["action"]
        seat = next(b for b in ride["beats"] if b["id"] == f"{base}-ride")
        peak = next(b for b in ride["beats"] if b["id"] == f"{base}-peak")
        act = seat["action"]
        low = act.lower()
        for banned in (
            "thighs lifts",
            "thigh lifts",
            "folds down",
            "stands up from that kneel",
            "squats",
            "one of aya's thighs",
            "steps over",
        ):
            assert banned not in low, base
        assert "hangs directly above the glans" in low
        assert "straight down" in low
        assert "hold still joined at the base" in low
        assert f"either side of {partner.lower()}'s ribs" in low
        assert cm in act
        assert "pale-tan" not in low
        assert "sideride" not in extra_keys(seat)
        assert "thrust" not in extra_keys(seat)
        assert not seat.get("trigger")
        assert seat.get("connect") == "chain"
        seat_prompt = build_beat_prompt(ride, seat, trigger=merge_trigger("", seat), camera_pack="side2d")
        for banned in (
            "folds down",
            "rises into the rider",
            "stands up from that kneel",
            "side view riding sex",
            "do not piston",
            "kiss smack",
            "22cm",
            "still kneeling",
            "slides both feet",
            "squats and lowers",
            "aya's hips moving",
            "a hip thrust is in place",
            "wet jupo",
        ):
            assert banned not in seat_prompt.lower(), (base, banned)
        assert "directly above the glans" in seat_prompt.lower()
        assert "straight down" in seat_prompt.lower()
        assert "hold still joined at the base" in seat_prompt.lower()
        assert "legs drop straight down" in seat_prompt.lower()
        assert "both knees bend" in seat_prompt.lower()
        assert "both knees stay bent" not in seat_prompt.lower()
        assert f"hands land on {partner.lower()}'s chest" in low
        assert "already stands over" in low
        wait_prompt = build_beat_prompt(ride, waited, trigger=merge_trigger("", waited), camera_pack="side2d")
        assert "legs drop straight down" in wait_prompt.lower()
        assert "both knees stay bent" not in wait_prompt.lower()
        assert "rises once from the kneel" in wait_prompt.lower()
        assert "squats" not in low
        assert "sits beside" not in low
        assert "knees on the linoleum" not in low
        assert "three separate lowers" not in low
        peak_prompt = build_beat_prompt(ride, peak, trigger=merge_trigger("", peak), camera_pack="side2d")
        for banned in (
            "folds down",
            "stands up",
            "soles planted beside the hips",
            "lifts",
            "kiss smack",
        ):
            assert banned not in peak_prompt.lower(), (base, banned)
        assert SIDERIDE_TRIGGER not in peak_prompt
        assert "sideride" not in extra_keys(seat)
        oral_prompt = build_beat_prompt(ride, oral, trigger=merge_trigger("", oral))
        assert "this wide full-body frame stays locked" not in oral_prompt.lower()
        assert "rises into the rider" not in oral_prompt.lower()
        folded = dict(seat)
        folded["action"] = seat["action"] + " The upright adult folds down onto her back."
        folded_prompt = build_beat_prompt(ride, folded, trigger=merge_trigger("", folded))
        assert "rises into the rider" not in folded_prompt.lower()
        plow = peak["action"].lower()
        assert "buried to the root" in low
        assert "buried to the root" in plow
        assert "the shaft stays buried to the root until the last frame" in low
        assert "the shaft stays buried to the root until the last frame" in plow
        assert "keep the glans inside" in plow
        assert "lifts" not in low and "lifts" not in plow
        assert "pull back" not in low and "pull back" not in plow
        assert "slides off" not in low and "slides off" not in plow
        assert "slides out" not in plow
        assert "pleasure-drunk happy smile" in low
        assert f"{partner.lower()}'s face is the same pleasure-drunk happy smile" in plow
        walk = next(b for b in ride["beats"] if b["id"] == f"{base}-walk")
        assert walk.get("connect") == "chain"
        assert walk.get("source") == "chain"
        assert "aya" in walk["cast"]
        assert partner.lower() in (walk.get("fade_cast") or [])
        assert "from 0 to 3 seconds" in walk["action"].lower()
        assert "pulls out of aya's pussy" in walk["action"].lower()
        assert "pleasure-drunk" in walk["action"].lower()
        assert extra_lora_entries(walk) == [("kiss", 0.5)]
        assert "sideride" not in extra_keys(peak)
        assert extra_keys(peak)[0] == "penis"
        assert "thrust" in extra_keys(peak)
        assert "mystic" not in extra_keys(peak)
        assert peak.get("connect") == "chain"
        for word in pose_ban:
            assert word not in low and word not in plow
        assert "駅弁" not in act and "駅弁" not in peak["action"]
        cut_seat = next(b for b in cut["beats"] if b["id"] == f"{base}-ride")
        cut_peak = next(b for b in cut["beats"] if b["id"] == f"{base}-peak")
        assert beat_source(cut_seat) == "chain"
        assert beat_source(cut_peak) == "chain"
        assert cut_seat.get("connect") == "chain"
        assert cut_peak.get("connect") == "chain"
    gin = prepare_episode(raw, story_override="受け入れる", gin_override="犯される")
    gin_ride = next(b for b in gin["beats"] if b["id"] == "04-gin-ride")
    raw_gin = next(x for x in next(b for b in raw["beats"] if b["id"] == "04-gin")["on_gin_taken"] if x["id"] == "04-gin-ride")
    assert gin_ride["action"] == raw_gin["action"]
    assert "both knees stay bent" in gin_ride["action"].lower()
    assert "hips stay over the groin" in gin_ride["action"].lower()
    assert "already stands over" not in gin_ride["action"].lower()
    assert "stands up" not in gin_ride["action"].lower()
    assert "steps" not in gin_ride["action"].lower()
    assert "folds down" not in build_beat_prompt(gin, gin_ride).lower()
    assert "either side of aya's ribs" in gin_ride["action"].lower()
    assert "one sole beside each side of the chest" in gin_ride["action"].lower()
    assert "sideride" not in extra_keys(gin_ride)
    gin_cut = prepare_episode(
        raw,
        story_override="受け入れる",
        gin_override="犯される",
        connect_override="t2v",
    )
    assert beat_source(next(b for b in gin_cut["beats"] if b["id"] == "04-gin-ride")) == "chain"
    assert beat_source(next(b for b in gin_cut["beats"] if b["id"] == "04-gin-peak")) == "chain"
    assert beat_source(next(b for b in gin_cut["beats"] if b["id"] == "04-gin-jupo")) == "chain"
    assert beat_source(next(b for b in gin_cut["beats"] if b["id"] == "04-gin-mouth")) == "chain"
    assert beat_source(next(b for b in gin_cut["beats"] if b["id"] == "04-gin-spitkiss")) == "chain"
    assert beat_source(next(b for b in gin_cut["beats"] if b["id"] == "04-gin-wait")) == "chain"
    assert beat_source(next(b for b in gin_cut["beats"] if b["id"] == "04-gin-cunny")) == "t2v"
    probe = {
        "id": "03-probe",
        "action": "The upright adult folds down onto her back.",
        "cast": ["aya", "miki"],
        "loco": "planted",
    }
    assert "rises into the rider" in build_beat_prompt(ride, probe).lower()
    drop = next(b for b in ride["beats"] if b["id"] == "12-exit-drop")
    assert "slides out" in drop["action"].lower()
    ride_ids = [b["id"] for b in ride["beats"] if str(b["id"]).startswith("12-exit")]
    assert ride_ids[-1] == "12-exit-walk"
    assert ride_ids.index("12-exit-peak") < ride_ids.index("12-exit-drop") < ride_ids.index("12-exit-kiss") < ride_ids.index("12-exit-walk")
    chained = prepare_episode(
        raw,
        story_override="誘う",
        invite_pose_override="騎乗位",
        connect_override="chain",
    )
    for bid in ("03-kiss-walk", "06-doggy-walk", "09-join-walk", "12-exit-walk"):
        walked = next(b for b in chained["beats"] if b["id"] == bid)
        assert beat_source(walked) != "t2v", bid
    sit = prepare_episode(raw, story_override="誘う", invite_pose_override="対面座位")
    sit_walk = next(b for b in sit["beats"] if b["id"] == "03-kiss-walk")
    assert sit_walk.get("connect") == "end"
    assert "arms around each other's backs" in sit_walk["action"]


def test_hospital_ride_foot_fork_keeps_both_seats():
    raw = load_episode(HOSPITAL_DIR / "episode.json")
    assert list(RIDE_FOOT_CHOICES) == ["なし", "みき", "れい", "かな", "しの", "ギン", "😈"]
    bent = prepare_episode(
        raw,
        story_override="誘う",
        invite_pose_override="騎乗位",
        ride_bent_override="みき",
        ride_column_override="れい",
    )
    miki_wait = next(b for b in bent["beats"] if b["id"] == "03-kiss-wait")
    miki_ride = next(b for b in bent["beats"] if b["id"] == "03-kiss-ride")
    rei_wait = next(b for b in bent["beats"] if b["id"] == "06-doggy-wait")
    rei_ride = next(b for b in bent["beats"] if b["id"] == "06-doggy-ride")
    assert "both knees stay bent" in miki_wait["action"].lower()
    assert "legs drop straight down" not in miki_wait["action"].lower()
    assert "miki's hands rest on aya's breasts" in miki_ride["action"].lower()
    assert "legs drop straight down" not in miki_ride["action"].lower()
    assert "rises once from the kneel" in rei_wait["action"].lower()
    assert "hands land on rei's chest" in rei_ride["action"].lower()
    miki_prompt = build_beat_prompt(bent, miki_ride)
    rei_prompt = build_beat_prompt(bent, rei_ride)
    assert "both knees stay bent" in miki_prompt.lower()
    assert "legs drop straight down" not in miki_prompt.lower()
    assert "legs drop straight down" in rei_prompt.lower()
    assert "both knees stay bent" not in rei_prompt.lower()
    assert beat_source(
        next(b for b in prepare_episode(
            raw,
            story_override="誘う",
            invite_pose_override="ride_bent",
            connect_override="t2v",
        )["beats"] if b["id"] == "03-kiss-ride")
    ) == "chain"
    same = prepare_episode(raw, ride_bent_override="かな", ride_column_override="かな")
    kana = next(b for b in same["beats"] if b["id"] == "09-join-wait")
    assert "legs drop straight down" in kana["action"].lower()
    gin_bent = prepare_episode(raw, gin_override="犯される")
    gin_raw = next(
        x for x in next(b for b in raw["beats"] if b["id"] == "04-gin")["on_gin_taken"] if x["id"] == "04-gin-ride"
    )
    assert next(b for b in gin_bent["beats"] if b["id"] == "04-gin-ride")["action"] == gin_raw["action"]
    gin_col = prepare_episode(raw, ride_column_override="ギン")
    gin_seat = next(b for b in gin_col["beats"] if b["id"] == "04-gin-ride")
    assert "legs drop straight down" in gin_seat["action"].lower()
    assert "gin's hands land on aya's chest" in gin_seat["action"].lower()
    assert "both knees stay bent" not in build_beat_prompt(gin_col, gin_seat).lower()
    horn_bent = prepare_episode(raw, tsuno_override="角・騎乗")
    horn_seat = next(b for b in horn_bent["beats"] if b["id"] == "04-tsuno-ride")
    assert "on their sides" in horn_seat["action"].lower()
    assert "travels into the pussy" in horn_seat["action"].lower()
    assert "lifts" not in horn_seat["action"].lower()
    assert "forearms" not in horn_seat["action"].lower()
    assert "feet in the air" not in horn_seat["action"].lower()
    assert "spoonlg" not in horn_seat["action"].lower()
    assert "erect ashen-gray 24cm" in horn_seat["action"]
    jacko = prepare_episode(raw, tsuno_override="角・寝室アナル")
    jacko_ids = [b["id"] for b in jacko["beats"] if str(b["id"]).startswith("04-tsuno-jo")]
    assert jacko_ids == [
        "04-tsuno-jo",
        "04-tsuno-jo-anal",
        "04-tsuno-jo-cum",
        "04-tsuno-jo-gape",
        "04-tsuno-jo-kiss",
        "04-tsuno-jo-walk",
    ]
    assert "04-tsuno-stall" not in [b["id"] for b in jacko["beats"]]
    assert "doggy" not in next(b for b in jacko["beats"] if b["id"] == "04-tsuno-jo")["action"].lower()


def test_hospital_tsuno_ride_and_stall_are_new_stories():
    raw = load_episode(HOSPITAL_DIR / "episode.json")
    assert set(TSUNO_MODES) >= {
        "off",
        "accept_stand",
        "invite_stand",
        "anal_back",
        "nelson",
        "invite_ride",
        "wash_carry",
    }
    assert TSUNO_MODES["off"]["choice_ja"].startswith("角・")
    assert TSUNO_MODES["invite_ride"]["choice_ja"] == "角・病室で横になって挿入"
    assert TSUNO_MODES["invite_jacko"]["choice_ja"] == "角・病室でベッドの後ろアナル"
    assert "角・騎乗・細い柱" not in ui_choices("tsuno")
    assert TSUNO_MODES["wash_carry"]["choice_ja"] == "角・個室"
    assert TSUNO_OVERLAY_KEYS["invite_ride"] == "on_tsuno_invite_ride"
    assert TSUNO_OVERLAY_KEYS["wash_carry"] == "on_tsuno_wash_carry"
    assert "recommend" not in TSUNO_MODES["invite_ride"]

    off = prepare_episode(raw, toilet_override="pee", tsuno_override="off")
    assert any(str(b["id"]).startswith("04-toilet") for b in off["beats"])
    assert all(not str(b["id"]).startswith("04-tsuno") for b in off["beats"])

    ride = prepare_episode(raw, tsuno_override="角・騎乗", connect_override="chain")
    ids = [b["id"] for b in ride["beats"] if str(b["id"]).startswith("04-tsuno")]
    assert ids == [
        "04-tsuno-meet-spot",
        "04-tsuno-kiss",
        "04-tsuno-oral",
        "04-tsuno-wait",
        "04-tsuno-spit",
        "04-tsuno-beckon",
        "04-tsuno-lie",
        "04-tsuno-sidekiss",
        "04-tsuno-aim",
        "04-tsuno-ride",
        "04-tsuno-peak",
        "04-tsuno-ride-kiss",
        "04-tsuno-walk",
    ]
    assert "04-tsuno-meet" not in ids
    horn_aim = next(b for b in ride["beats"] if b["id"] == "04-tsuno-aim")
    assert extra_lora_entries(horn_aim) == []
    assert "lowers the glans onto aya's hairless pussy" in horn_aim["action"].lower()
    assert beat_source(horn_aim) == "chain"
    oral = next(b for b in ride["beats"] if b["id"] == "04-tsuno-oral")
    assert extra_lora_entries(oral)[:3] == [("blowjob", 0.8), ("mystic", 0.5), ("penis", 0.45)]
    assert oral.get("trigger") == "bl0w_j0b"
    oral_prompt = build_beat_prompt(ride, oral, trigger=merge_trigger("", oral))
    assert "bl0w_j0b" in oral_prompt
    assert "deep knee bend" in oral["action"].lower()
    assert "on her back" not in oral["action"].lower()
    assert "STANDS" not in oral["action"]
    assert "STANDS" not in oral_prompt
    assert "lewd pleasure-drunk happy smile" in oral["action"].lower()
    assert "lips stay on the shaft" in oral["action"].lower()
    for bid in (
        "04-tsuno-kiss",
        "04-tsuno-oral",
        "04-tsuno-wait",
        "04-tsuno-spit",
        "04-tsuno-beckon",
        "04-tsuno-lie",
        "04-tsuno-sidekiss",
        "04-tsuno-ride",
        "04-tsuno-peak",
        "04-tsuno-ride-kiss",
    ):
        faced = next(b for b in ride["beats"] if b["id"] == bid)
        assert "lewd pleasure-drunk happy smile" in faced["action"].lower(), bid
        assert "affectionate" in faced["action"].lower(), bid
        faced_prompt = build_beat_prompt(ride, faced, trigger=merge_trigger("", faced))
        assert "lewd pleasure-drunk happy smile" in faced_prompt.lower(), bid
        assert "single eye half-lidded" in faced_prompt.lower(), bid
        assert "tired determined" not in faced_prompt.lower(), bid
        if bid == "04-tsuno-kiss":
            assert "the same aya" in faced["action"].lower()
            assert "single eye half-lidded" in faced["action"].lower()
            assert "same two adults" in faced_prompt.lower()
            assert "the standing woman is the same aya" in faced_prompt.lower()
            assert "nothing new enters" not in faced_prompt.lower()
            assert "two faces" not in faced_prompt.lower()
    jacko_bed = prepare_episode(raw, tsuno_override="角・寝室アナル", connect_override="chain")
    jacko_oral = next(b for b in jacko_bed["beats"] if b["id"] == "04-tsuno-oral")
    assert extra_lora_entries(jacko_oral) == extra_lora_entries(oral)
    assert jacko_oral.get("trigger") == "bl0w_j0b"
    assert jacko_oral.get("connect") == "chain"
    assert "lewd pleasure-drunk happy smile" in jacko_oral["action"].lower()
    assert "lips stay on the shaft" in jacko_oral["action"].lower()
    wait = next(b for b in ride["beats"] if b["id"] == "04-tsuno-wait")
    assert "onto aya's face and tongue" in wait["action"].lower()
    assert extra_lora_entries(wait)[0] == ("cumshot", 1.0)
    assert "penis" in extra_keys(wait)
    assert wait.get("trigger", "").startswith("CUMSH0T")
    assert "PENISLORA" in wait.get("trigger", "")
    assert "aya holds the shaft in her right hand" in wait["action"].lower()
    assert "smiles shyly and giggles" in wait["action"].lower()
    assert wait.get("connect") == "chain"
    assert beat_source(wait) == "chain"
    seat = next(b for b in ride["beats"] if b["id"] == "04-tsuno-ride")
    seat_prompt = build_beat_prompt(ride, seat)
    assert "spoonlg" not in seat["action"].lower()
    assert "spoonlg" in extra_keys(seat)
    assert extra_lora_entries(seat)[0] == ("spoonlg", 1.0)
    assert ("penis", 0.6) in extra_lora_entries(seat)
    assert "folds down" not in seat["action"].lower()
    assert "folds down" not in seat_prompt.lower()
    assert "sideride" not in extra_keys(seat)
    assert "thrust" not in extra_keys(seat)
    assert "hold still joined at the base" in seat["action"].lower()
    assert seat.get("connect") == "cut"
    assert beat_source(seat) == "chain"
    peak = next(b for b in ride["beats"] if b["id"] == "04-tsuno-peak")
    assert extra_lora_entries(peak)[0] == ("spoonlg", 1.0)
    assert ("thrust", 0.55) in extra_lora_entries(peak)
    assert ("synth", 0.4) in extra_lora_entries(peak)
    assert "PENISLORA" in peak.get("trigger", "")
    assert "cums inside" in peak.get("trigger", "").lower()
    assert "female character" not in peak.get("trigger", "").lower()
    walk = next(b for b in ride["beats"] if b["id"] == "04-tsuno-walk")
    assert walk["cast"] == ["aya", "tsuno"]
    assert walk.get("fade_cast") == ["tsuno"]
    assert "No penis" in walk["action"]
    assert "The grown shaft is gone" in walk["action"]
    assert walk.get("connect") == "cut"
    assert beat_source(walk) == "chain"
    assert "pulls out of aya's pussy" in walk["action"].lower()
    spot = next(b for b in ride["beats"] if b["id"] == "04-tsuno-meet-spot")
    assert "sickroom" in spot["action"].lower()
    assert "corridor" not in spot["action"].lower()
    assert "zombie" not in spot["action"].lower()
    for bid in ("04-tsuno-oral", "04-tsuno-wait", "04-tsuno-ride", "04-tsuno-peak", "04-tsuno-ride-kiss"):
        act = next(b for b in ride["beats"] if b["id"] == bid)["action"]
        assert "erect ashen-gray 24cm" in act
    cut = prepare_episode(raw, tsuno_override="invite_ride", connect_override="t2v")
    assert beat_source(next(b for b in cut["beats"] if b["id"] == "04-tsuno-ride")) == "t2v"
    assert beat_source(next(b for b in cut["beats"] if b["id"] == "04-tsuno-spit")) == "t2v"
    assert beat_source(next(b for b in cut["beats"] if b["id"] == "04-tsuno-lie")) == "t2v"
    assert beat_source(next(b for b in cut["beats"] if b["id"] == "04-tsuno-beckon")) == "chain"
    assert beat_source(next(b for b in cut["beats"] if b["id"] == "04-tsuno-sidekiss")) == "chain"
    assert beat_source(next(b for b in cut["beats"] if b["id"] == "04-tsuno-peak")) == "chain"
    kiss_joined = next(b for b in ride["beats"] if b["id"] == "04-tsuno-ride-kiss")
    assert kiss_joined.get("connect") == "chain" and beat_source(kiss_joined) == "chain"
    assert beat_source(next(b for b in cut["beats"] if b["id"] == "04-tsuno-ride-kiss")) == "chain"
    assert "TRAVELS INTO" in seat["action"] and "HOLD" in seat["action"]
    assert "front from the doorway" not in seat["camera"].lower()
    assert "front from the doorway" not in peak["camera"].lower()
    assert "beside the thigh" in seat["camera"].lower()
    assert "beside the thigh" in peak["camera"].lower()
    assert "pelvis stays pushed back" in peak["action"].lower()
    assert "glans stays inside" in peak["action"].lower()
    assert "rests outside along the raised thigh" not in peak["action"].lower()
    assert "lifts" not in seat["action"].lower()
    lie = next(b for b in ride["beats"] if b["id"] == "04-tsuno-lie")
    assert "front from the doorway" not in lie["camera"].lower()
    assert "lowers her hip onto the mattress" in lie["action"].lower()
    assert "glans of the erect ashen-gray 24cm meets aya's hairless pussy" in lie["action"].lower()
    assert "shaft stays outside" in lie["action"].lower()
    assert "short shift toward the left" in lie["action"].lower()
    beckon = next(b for b in ride["beats"] if b["id"] == "04-tsuno-beckon")
    assert "far long edge nearest the window" in beckon["action"].lower()
    beckon_prompt = build_beat_prompt(ride, beckon)
    lie_prompt = build_beat_prompt(ride, lie)
    assert SIDE_LIE_SETTLE_CLAUSE in beckon_prompt
    assert PLANTED_PACE_CLAUSE not in beckon_prompt
    assert SIDE_LIE_JOIN_CLAUSE in lie_prompt
    assert PLANTED_PACE_CLAUSE not in lie_prompt
    spit = next(b for b in ride["beats"] if b["id"] == "04-tsuno-spit")
    assert spit.get("connect") == "cut"
    assert extra_lora_entries(spit)[:2] == [("kiss", 0.5), ("cumouf", 0.5)]
    assert "front from the doorway" in spit["camera"].lower()
    assert "rises from the squat" in spit["action"].lower()
    assert beckon.get("connect") == "chain"
    assert "profile side-on" in beckon["camera"].lower()
    assert "right half of the mattress" in beckon["action"].lower()
    assert "head points to the left" in beckon["action"].lower()
    assert "near half" in lie["action"].lower()
    assert "far half" in lie["action"].lower()
    assert "toward the camera" in lie["action"].lower()
    assert "upper knee rises toward the camera" in lie["action"].lower()
    assert "upper thigh opens wide" in lie["action"].lower()
    assert "hips on the same line as tsuno's hips" in lie["action"].lower()
    assert "glans stays pressed on that pussy" in lie["action"].lower()
    assert "from tsuno's hips" not in lie["action"].lower()
    assert "in the gap between the thighs" in lie_prompt.lower()
    sidekiss = next(b for b in ride["beats"] if b["id"] == "04-tsuno-sidekiss")
    assert sidekiss.get("connect") == "chain"
    assert "front from the doorway" not in sidekiss["camera"].lower()
    assert "chin turns back" in sidekiss["action"].lower()
    assert "shaft stays outside" in sidekiss["action"].lower()
    assert "glans stays against the hairless pussy" in sidekiss["action"].lower()
    jacko_order = [b["id"] for b in jacko_bed["beats"] if str(b["id"]).startswith("04-tsuno")]
    assert "04-tsuno-spit" not in jacko_order
    assert jacko_order[jacko_order.index("04-tsuno-wait") + 1] == "04-tsuno-jo"
    emb_hold = next(
        b
        for b in prepare_episode(raw, story_override="誘う", invite_pose_override="embrace")["beats"]
        if b["id"] == "03-kiss-hold"
    )
    assert "feet leave the linoleum" in emb_hold["action"].lower()
    assert "lift until the feet leave" in emb_hold["action"].lower()
    assert "on their sides" not in emb_hold["action"].lower()
    embraced = prepare_episode(
        raw,
        story_override="誘う",
        invite_pose_override="embrace",
        tsuno_override="角・騎乗",
    )
    embraced_ids = [b["id"] for b in embraced["beats"]]
    assert "04-tsuno-ride" in embraced_ids
    assert "04-tsuno-hug" not in embraced_ids
    assert "04-tsuno-carry" not in embraced_ids
    _assert_hospital_bans(ride)
    assert validate_episode(ride, root=HOSPITAL_DIR) == []

    wash = prepare_episode(raw, tsuno_override="角・個室", connect_override="chain", toilet_override="pee")
    wids = [b["id"] for b in wash["beats"] if str(b["id"]).startswith("04-tsuno")]
    assert wids == [
        "04-tsuno-meet-spot",
        "04-tsuno-carry",
        "04-tsuno-stall",
        "04-tsuno-set",
        "04-tsuno-anal",
        "04-tsuno-cum",
        "04-tsuno-gape",
        "04-tsuno-rise",
        "04-tsuno-stall-kiss",
        "04-tsuno-walk",
    ]
    assert "04-tsuno-spit" not in wids
    stall_anal = next(b for b in wash["beats"] if b["id"] == "04-tsuno-anal")
    assert "hold still joined at the base" in stall_anal["action"].lower()
    assert "lifts" not in stall_anal["action"].lower()
    assert any(str(b["id"]).startswith("04-toilet") for b in wash["beats"])
    assert all(not str(i).startswith("04-toilet") for i in wids)
    tsuno_beats = [b for b in wash["beats"] if str(b["id"]).startswith("04-tsuno")]
    blob = "\n".join(
        f"{b.get('action') or ''} {b.get('camera') or ''} {b.get('extra_loras') or ''}" for b in tsuno_beats
    ).lower()
    assert "thumbinbutt" not in blob
    assert "04-toilet-" not in blob
    assert wids.index("04-tsuno-stall-kiss") == wids.index("04-tsuno-rise") + 1
    kiss = next(b for b in wash["beats"] if b["id"] == "04-tsuno-stall-kiss")
    assert kiss["camera"].startswith("PROFILE")
    assert kiss.get("connect") == "cut"
    assert beat_source(kiss) == "chain"
    stall = next(b for b in wash["beats"] if b["id"] == "04-tsuno-stall")
    assert stall.get("connect") == "cut"
    assert beat_source(stall) == "chain"
    carry = next(b for b in wash["beats"] if b["id"] == "04-tsuno-carry")
    assert "LIFTS Aya against" in carry["action"]
    carry_prompt = build_beat_prompt(wash, carry)
    assert "beside the partner's hips" not in carry_prompt.lower()
    assert "feet stay in the air" not in carry_prompt.lower()
    anal = next(b for b in wash["beats"] if b["id"] == "04-tsuno-anal")
    assert "lifts" not in anal["action"].lower()
    assert "hold still joined at the base" in anal["action"].lower()
    wwalk = next(b for b in wash["beats"] if b["id"] == "04-tsuno-walk")
    assert "No penis" in wwalk["action"]
    assert wwalk["cast"] == ["aya", "tsuno"]
    assert wwalk.get("fade_cast") == ["tsuno"]
    assert wwalk.get("connect") == "cut"
    assert beat_source(wwalk) == "chain"
    _assert_hospital_bans(wash)
    assert validate_episode(wash, root=HOSPITAL_DIR) == []
    assert len(wash["beats"]) <= MAX_BEATS


def test_hospital_wash_gape_oral_wait_overflow_and_dog_lick():
    raw = load_episode(HOSPITAL_DIR / "episode.json")
    miki = prepare_episode(
        raw,
        story_override="accept",
        toilet_override="和式ミキ",
        connect_override="chain",
    )
    stall = [b for b in miki["beats"] if str(b["id"]).startswith("04-toilet")]
    assert [b["id"] for b in stall] == [
        "04-toilet-in",
        "04-toilet-squat",
        "04-toilet-spot",
        "04-toilet-push",
        "04-toilet",
        "04-toilet-cum",
        "04-toilet-gape",
        "04-toilet-out",
    ]
    assert all(b.get("connect") == "chain" and beat_source(b) == "chain" for b in stall)
    gape = next(b for b in stall if b["id"] == "04-toilet-gape")
    assert "wide ring" in gape["action"]
    assert extra_lora_entries(gape) == [("jacko", 0.35)]
    assert "doggy" not in extra_keys(gape)
    push = next(b for b in stall if b["id"] == "04-toilet-push")
    assert "forearms" in push["action"] and "head" in push["action"].lower()
    spot = next(b for b in stall if b["id"] == "04-toilet-spot")
    assert "RUBS" in spot["action"]
    assert "platform" not in " ".join(
        str(b.get(k) or "") for b in stall for k in ("action", "camera", "place", "environment")
    ).lower()
    assert extra_keys(push)[0] == "jacko"
    inserted = next(b for b in stall if b["id"] == "04-toilet")
    assert extra_lora_entries(inserted)[0] == ("jacko", 0.4)
    assert "doggy" not in extra_keys(inserted)
    cum = next(b for b in stall if b["id"] == "04-toilet-cum")
    assert extra_lora_entries(cum)[0] == ("jacko", 0.35)
    assert "doggy" not in extra_keys(cum)
    for beat in (push, inserted, cum, gape):
        blob = f"{beat['action']} {beat['camera']}".lower()
        assert "head rests on the forearms" in blob or "head on the forearms" in blob
        assert "face looks at the camera" in blob or "face at the camera" in blob
        assert "knees rest on the tiles" in blob or "knees on the tiles" in blob
        assert "hip joint" in blob
        assert "miki's back faces the camera" in blob or "miki's back and both buttocks face the camera" in blob
        assert "one neck" in blob
        assert "head stays at the left end" in blob
        assert "crown of the head" not in blob
        assert "face toward the hood" not in blob
    out = next(b for b in stall if b["id"] == "04-toilet-out")
    assert "SLIDES OUT" not in out["action"]
    assert "Tongues intertwine" in out["action"]
    assert "both stand up" in out["action"].lower()
    assert "walks out to the right" in out["action"].lower()
    assert "jacko" not in extra_keys(out)
    expel = prepare_episode(raw, story_override="accept", toilet_override="和式", connect_override="chain")
    assert all(b["id"] != "04-toilet-gape" for b in expel["beats"])
    assert all("jacko" not in extra_keys(b) for b in expel["beats"] if str(b["id"]).startswith("04-toilet"))
    gin = prepare_episode(raw, story_override="accept", gin_override="犯される", connect_override="chain")
    order = [b["id"] for b in gin["beats"] if str(b["id"]).startswith("04-gin")]
    assert order.index("04-gin-jupo") < order.index("04-gin-mouth") < order.index("04-gin-spitkiss")
    assert order.index("04-gin-spitkiss") < order.index("04-gin-wait") < order.index("04-gin-ride") < order.index("04-gin-peak")
    jupo = next(b for b in gin["beats"] if b["id"] == "04-gin-jupo")
    assert "kneels" in jupo["action"]
    assert "soles plant" not in jupo["action"].lower()
    assert "soles plant" not in build_beat_prompt(gin, jupo).lower()
    mouth = next(b for b in gin["beats"] if b["id"] == "04-gin-mouth")
    assert extra_lora_entries(mouth) == [("cumshot", 1.0), ("penis", 0.45)]
    assert mouth.get("facial") is True
    assert "across gin's nose, eyes, and into gin's open mouth" in mouth["action"].lower()
    assert mouth.get("steps") == 8 and mouth.get("turbo") is False
    assert "blowjob" not in extra_keys(mouth) and "cumouf" not in extra_keys(mouth)
    assert "onto gin's face and tongue" in mouth["action"].lower()
    assert "onto aya's face" not in mouth["action"].lower()
    assert "tongue extended under the glans" in mouth["cast_lock"]["gin"].lower()
    assert "cheek faces the slit" in mouth["action"].lower()
    horn = prepare_episode(raw, tsuno_override="フルネルソンアナル", connect_override="chain")
    horn_peak = next(b for b in horn["beats"] if b["id"] == "04-tsuno-peak")
    assert "hold still joined at the base" in horn_peak["action"].lower()
    assert "shaft leaves the anus" not in horn_peak["action"].lower()
    assert "two small dark horns stay at the hairline" in horn_peak["action"].lower()
    miki_nel = prepare_episode(raw, story_override="誘う", invite_pose_override="フルネルソンアナル")
    miki_peak = next(b for b in miki_nel["beats"] if b["id"] == "03-kiss-peak")
    assert "hold still joined at the base" in miki_peak["action"].lower()
    assert "lowers one of" not in miki_peak["action"].lower()
    assert "slides off the glans" in mouth["action"].lower()
    assert "urethral slit" in mouth["action"].lower()
    mouth_prompt = build_beat_prompt(gin, mouth, trigger=merge_trigger("", mouth))
    assert "onto gin's face and tongue" in mouth_prompt.lower()
    assert "onto aya's face" not in mouth_prompt.lower()
    assert "aya's face stays clean" in mouth["action"].lower()
    assert "drowning in climax" not in mouth["cast_lock"]["aya"].lower()
    ride = next(b for b in gin["beats"] if b["id"] == "04-gin-ride")
    assert "overwhelmed joy at a new pleasure" in build_beat_prompt(gin, ride).lower()
    assert "slit" in mouth["action"]
    assert "STANDS" not in mouth["action"]
    assert "STANDS" not in build_beat_prompt(gin, mouth)
    spit = next(b for b in gin["beats"] if b["id"] == "04-gin-spitkiss")
    assert extra_lora_entries(spit) == [("kiss", 0.5), ("cumouf", 0.45)]
    assert "SLIDES OUT" not in spit["action"]
    assert "Mouths JOIN" in spit["action"]
    assert "STANDS" not in spit["action"]
    assert "pushes the white from gin's mouth into aya's mouth" in spit["action"].lower()
    spit_prompt = build_beat_prompt(gin, spit, trigger=merge_trigger("", spit))
    assert "into aya's mouth" in spit_prompt.lower()
    assert "on gin's face" not in spit_prompt.lower()
    waited = next(b for b in gin["beats"] if b["id"] == "04-gin-wait")
    assert "DIRECTLY ABOVE" in waited["action"]
    assert "TRAVELS INTO" not in waited["action"]
    assert "STANDS" in waited["action"]
    seat = next(b for b in gin["beats"] if b["id"] == "04-gin-ride")
    assert "LOWERS" in seat["action"] and "HOLD" in seat["action"]
    assert "STANDS" not in seat["action"]
    peak = next(b for b in gin["beats"] if b["id"] == "04-gin-peak")
    assert "OVERFLOWS" in peak["action"]
    assert "a little" not in peak["action"].lower()
    assert "cmst" not in extra_keys(peak)
    cunny = next(b for b in gin["beats"] if b["id"] == "04-gin-cunny")
    assert cunny.get("connect") == "chain" and beat_source(cunny) == "chain"
    oral = prepare_episode(raw, dog_override="invite_oral", connect_override="chain")
    lick = next(b for b in oral["beats"] if b["id"] == "04-dog-lick")
    lick_peak = next(b for b in oral["beats"] if b["id"] == "04-dog-lick-peak")
    assert lick.get("connect") == "chain" and beat_source(lick) == "chain"
    assert lick_peak.get("connect") == "chain" and beat_source(lick_peak) == "chain"
    assert "hairless pussy" in lick["camera"] and "face" in lick["camera"]
    assert "full-body side view" in lick_peak["action"]
    assert "licks the hairless pussy" in lick["action"]
    dog_wait = next(b for b in oral["beats"] if b["id"] == "04-dog-wait")
    assert dog_wait.get("connect") == "chain" and beat_source(dog_wait) == "chain"
    dog_cum = next(b for b in oral["beats"] if b["id"] == "04-dog-cum")
    assert "OVERFLOWS" in dog_cum["action"]
    walk = next(b for b in oral["beats"] if b["id"] == "04-dog-walk")
    assert walk.get("connect") == "end"
    assert len(miki["beats"]) <= MAX_BEATS
    assert len(gin["beats"]) <= MAX_BEATS
    assert len(oral["beats"]) <= MAX_BEATS


def test_hospital_siderear_keeps_the_join_visible():
    raw = load_episode(HOSPITAL_DIR / "episode.json")
    fours = prepare_episode(raw, story_override="誘う", invite_pose_override="四つん這い")
    seat = next(b for b in fours["beats"] if b["id"] == "06-doggy")
    peak = next(b for b in fours["beats"] if b["id"] == "06-doggy-peak")
    walk = next(b for b in fours["beats"] if b["id"] == "06-doggy-walk")
    assert extra_lora_entries(seat) == []
    closed = next(b for b in fours["beats"] if b["id"] == "06-doggy-close")
    assert "penis" not in extra_keys(closed)
    assert HIPS_BACK_ONCE_CLAUSE in build_beat_prompt(fours, closed)
    assert PLANTED_PACE_CLAUSE not in build_beat_prompt(fours, closed)
    assert extra_lora_entries(peak)[0] == ("siderear", 0.8)
    assert extra_lora_entries(peak)[1] == ("anuspussy", 0.4)
    entered = next(b for b in fours["beats"] if b["id"] == "06-doggy-in")
    assert extra_lora_entries(entered)[0] == ("siderear", 0.8)
    assert seat.get("steps") == 8 and seat.get("turbo") is False
    assert entered.get("steps") == 8 and entered.get("turbo") is False
    assert "lowers her chest and cheek" in seat["action"].lower()
    press = next(b for b in fours["beats"] if b["id"] == "06-doggy-press")
    assert extra_lora_entries(press) == []
    assert "glans stays pressed" in press["action"].lower()
    assert "walks in from the left" not in seat["action"].lower()
    assert "travels into the anus" in entered["action"].lower()
    assert "rim stretches tight" in entered["action"].lower()
    assert "rim stays sealed" in entered["action"].lower()
    assert "walks in from the left" not in entered["action"].lower()
    closed = next(b for b in fours["beats"] if b["id"] == "06-doggy-close")
    assert closed.get("steps") == 8 and closed.get("turbo") is False
    assert "ring finishes small and closed" in closed["action"].lower()
    assert "shaft stays outside" in closed["action"].lower()
    assert "thrust" not in extra_keys(closed)
    assert "right hand" in press["action"].lower()
    assert "siderear" not in extra_keys(walk)
    assert "anuspussy" not in extra_keys(walk)
    assert "profile side view" in seat["camera"].lower()
    assert "center of the frame" in seat["camera"].lower()
    assert "profile side view" in peak["camera"].lower()
    assert "side-rear" not in seat["camera"].lower()
    assert "side-rear" not in peak["camera"].lower()
    assert "doggy" not in seat["action"].lower()
    stand = prepare_episode(raw, story_override="誘う", invite_pose_override="立ちバック")
    wall = next(b for b in stand["beats"] if b["id"] == "03-kiss-in")
    assert extra_lora_entries(wall)[0] == ("siderear", 0.8)
    assert extra_lora_entries(wall)[1] == ("anuspussy", 0.4)
    assert "balls of both feet" in wall["action"].lower()
    assert "left hand stays on aya's shoulder" in wall["action"].lower()
    assert "travels into the anus" in wall["action"].lower()
    wall_set = next(b for b in stand["beats"] if b["id"] == "03-kiss")
    assert extra_lora_entries(wall_set) == []
    wall_aim = next(b for b in stand["beats"] if b["id"] == "03-kiss-press")
    assert extra_lora_entries(wall_aim) == []
    assert "steps onto the same centerline" in wall_aim["action"].lower()
    assert "siderear" not in extra_keys(next(b for b in stand["beats"] if b["id"] == "09-kana-facial"))
    m_open = prepare_episode(raw, story_override="誘う", invite_pose_override="M字")
    assert "siderear" not in extra_keys(next(b for b in m_open["beats"] if b["id"] == "06-doggy"))
    ride = prepare_episode(raw, story_override="誘う", invite_pose_override="騎乗位")
    assert "siderear" not in extra_keys(next(b for b in ride["beats"] if b["id"] == "03-kiss-ride"))
    gin = prepare_episode(raw, gin_override="誘う後背")
    assert extra_lora_entries(next(b for b in gin["beats"] if b["id"] == "04-gin-in"))[0] == ("siderear", 0.8)
    assert "siderear" not in extra_keys(next(b for b in gin["beats"] if b["id"] == "04-gin-lick"))
    tsuno = prepare_episode(raw, tsuno_override="受け入れる立ちバック")
    assert extra_lora_entries(next(b for b in tsuno["beats"] if b["id"] == "04-tsuno-in"))[0] == ("siderear", 0.8)
    assert "siderear" not in extra_keys(next(b for b in tsuno["beats"] if b["id"] == "04-tsuno-meet"))
    anal = prepare_episode(raw, tsuno_override="後ろアナル")
    assert extra_lora_entries(next(b for b in anal["beats"] if b["id"] == "04-tsuno-in"))[0] == ("siderear", 0.8)
    dog = prepare_episode(raw, dog_override="invite_oral")
    assert "siderear" not in extra_keys(next(b for b in dog["beats"] if b["id"] == "04-dog-in"))


def test_appearance_blank_matches_authored_and_custom_stays_on_one_person():
    raw = load_episode(HOSPITAL_DIR / "episode.json")
    plain = prepare_episode(raw, story_override="受け入れる", connect_override="chain")
    blank = prepare_episode(
        raw,
        story_override="受け入れる",
        connect_override="chain",
        appearance_override={
            "aya": {
                "hair": "",
                "color": "今のまま",
                "face": "",
                "dirt": "",
                "sweat": "",
                "clothes": "",
                "shaft": "今のまま",
            },
            "enemies": "",
        },
    )
    assert plain["cast"]["aya"]["lock"] == blank["cast"]["aya"]["lock"]
    assert [(b.get("id"), b.get("action"), b.get("connect"), b.get("source")) for b in plain["beats"]] == [
        (b.get("id"), b.get("action"), b.get("connect"), b.get("source")) for b in blank["beats"]
    ]

    silver = prepare_episode(raw, story_override="受け入れる", appearance_override={"aya": {"color": "silver"}})
    assert "long straight silver hair past the shoulders, blunt bangs across the forehead" in silver["cast"]["aya"]["lock"]
    assert "long straight dark hair past the shoulders" in silver["cast"]["shino"]["lock"]
    assert "short brown bob that sways with each step" in silver["cast"]["miki"]["lock"]
    cover = next(b for b in silver["beats"] if b["id"] == "01-cover")
    cover_prompt = build_beat_prompt(silver, cover)
    assert "long straight silver hair past the shoulders, blunt bangs across the forehead" in cover_prompt
    assert "long straight dark hair past the shoulders, blunt bangs across the forehead" not in cover_prompt

    bob = prepare_episode(
        raw,
        appearance_override={"aya": {"hair": "a blunt pink bob", "color": "silver"}},
    )
    assert "a blunt pink bob" in bob["cast"]["aya"]["lock"]
    assert "silver" not in bob["cast"]["aya"]["lock"]
    assert "blunt bangs" not in bob["cast"]["aya"]["lock"]

    dressed = prepare_episode(raw, appearance_override={"aya": {"clothes": "an open white shirt"}})
    assert "an open white shirt" in dressed["cast"]["aya"]["lock"]
    assert "no gown" not in dressed["cast"]["aya"]["lock"]
    assert "fully nude, no clothes, no gown" in dressed["cast"]["miki"]["lock"]
    assert "fully nude, no clothes, no gown" in dressed["cast"]["gin"]["lock"]
    assert dressed["cast"]["aya"]["lock"].count("an open white shirt") == 1

    clean = prepare_episode(raw, appearance_override={"aya": {"dirt": "clean dry skin"}})
    assert "clean dry skin" in clean["cast"]["aya"]["lock"]
    assert "grimy brown hospital dirt clinging to the whole body" not in clean["cast"]["aya"]["lock"]
    assert "clinging to the intact ashen skin" in clean["cast"]["gin"]["lock"]
    cover_clean = next(b for b in clean["beats"] if b["id"] == "01-cover")
    assert "clean dry skin" in cover_clean["action"]
    assert "grimy brown hospital dirt clinging to her whole body" not in cover_clean["action"]

    enemy = prepare_episode(raw, appearance_override={"enemies": "miki; hair=a shaved head; shaft=なし"})
    assert "a shaved head" in enemy["cast"]["miki"]["lock"]
    assert "short brown bob" not in enemy["cast"]["miki"]["lock"]
    assert "erect 24cm human penis" not in enemy["cast"]["miki"]["lock"]
    assert "a bare hairless groin" in enemy["cast"]["miki"]["lock"]
    assert "erect 24cm human penis" in enemy["cast"]["rei"]["lock"]
    assert "long straight dark hair past the shoulders, blunt bangs across the forehead" in enemy["cast"]["aya"]["lock"]

    shino = prepare_episode(raw, appearance_override={"enemies": "shino; hair=a tight bun"})
    assert "a tight bun" in shino["cast"]["shino"]["lock"]
    assert "long straight dark hair past the shoulders, blunt bangs across the forehead" in shino["cast"]["aya"]["lock"]

    shaft = prepare_episode(raw, appearance_override={"aya": {"shaft": "あり"}})
    assert "erect 24cm human penis" in shaft["cast"]["aya"]["lock"]
    assert shaft["cast"]["aya"]["lock"].count("erect 24cm human penis") == 1
    assert "no penis, never futanari" in shaft["cast"]["gin"]["lock"]
    gin_walk = next(
        b
        for b in prepare_episode(raw, gin_override="犯される", appearance_override={"aya": {"shaft": "あり"}})["beats"]
        if b["id"] == "04-gin-walk"
    )
    assert "No penis" in gin_walk["action"]
    assert "The grown shaft is gone" in gin_walk["action"]
    assert "erect 24cm human penis" not in gin_walk["action"]
    assert "erect 24cm human penis" not in (gin_walk.get("cast_lock") or {}).get("aya", shaft["cast"]["aya"]["lock"])
    assert validate_episode(shaft, root=HOSPITAL_DIR) == []
    assert validate_episode(dressed, root=HOSPITAL_DIR) == []
    assert validate_episode(enemy, root=HOSPITAL_DIR) == []

    with pytest.raises(EpisodeError):
        prepare_episode(raw, appearance_override={"aya": {"hair": "ピンクのボブ"}})
    with pytest.raises(EpisodeError):
        prepare_episode(raw, appearance_override={"enemies": "nobody; hair=a bob"})


def test_aya_appearance_dropdowns_keep_authored_and_a_choice_wins():
    kinds = (
        "aya_hair",
        "aya_color",
        "aya_face",
        "aya_bust",
        "aya_butt",
        "aya_build",
        "aya_height",
        "aya_dirt",
        "aya_sweat",
        "aya_clothes",
        "aya_shaft",
    )
    for kind in kinds:
        choices = ui_choices(kind)
        assert 8 <= len(choices) <= 10
        assert len(choices) == len(set(choices))
        assert ui_default(kind) == "今のまま（迷ったらこれ）"
        assert choices[0] == "今のまま（迷ったらこれ）"
    raw = load_episode(HOSPITAL_DIR / "episode.json")
    plain = prepare_episode(raw, story_override="受け入れる")
    keep = prepare_episode(
        raw,
        story_override="受け入れる",
        aya_look_override="今のまま（迷ったらこれ）",
        appearance_override={
            "aya": {
                "hair": "今のまま（迷ったらこれ）",
                "color": "今のまま（迷ったらこれ）",
                "face": "今のまま（迷ったらこれ）",
                "bust": "今のまま（迷ったらこれ）",
                "butt": "今のまま（迷ったらこれ）",
                "build": "今のまま（迷ったらこれ）",
                "height": "今のまま（迷ったらこれ）",
                "dirt": "今のまま（迷ったらこれ）",
                "sweat": "今のまま（迷ったらこれ）",
                "clothes": "今のまま（迷ったらこれ）",
                "shaft": "今のまま（迷ったらこれ）",
            }
        },
    )
    assert keep["cast"]["aya"]["lock"] == plain["cast"]["aya"]["lock"]

    picked = prepare_episode(
        raw,
        appearance_override={"aya": {"hair": "ボブ", "color": "銀髪", "face": "丸顔"}},
    )
    lock = picked["cast"]["aya"]["lock"]
    assert "a short silver hair bob at the jaw" in lock
    assert "a round face, large dark brown eyes, soft brows, full lips" in lock
    assert "blunt bangs" not in lock
    assert "small dark mole" not in lock
    assert "long straight dark hair past the shoulders" in picked["cast"]["shino"]["lock"]

    country = prepare_episode(raw, aya_look_override="北欧")
    assert "long straight blonde hair past the shoulders" in country["cast"]["aya"]["lock"]
    assert "light blue eyes" in country["cast"]["aya"]["lock"]
    win = prepare_episode(
        raw,
        aya_look_override="北欧",
        appearance_override={"aya": {"hair": "ボブ", "color": "銀髪"}},
    )
    assert "a short silver hair bob at the jaw" in win["cast"]["aya"]["lock"]
    assert "blonde" not in win["cast"]["aya"]["lock"]
    assert "light blue eyes" in win["cast"]["aya"]["lock"]

    slim = prepare_episode(raw, appearance_override={"aya": {"shaft": "細め"}})
    assert "slim girth" in slim["cast"]["aya"]["lock"]
    assert "erect 24cm" in slim["cast"]["aya"]["lock"]
    assert slim["cast"]["aya"]["lock"].count("erect 24cm") == 1
    standard = prepare_episode(raw, appearance_override={"aya": {"shaft": "あり（標準）"}})
    assert "straight heavy pale-tan shaft" in standard["cast"]["aya"]["lock"]
    dry = prepare_episode(raw, appearance_override={"aya": {"sweat": "乾いた肌"}})
    assert "dry skin" in dry["cast"]["aya"]["lock"]
    assert "visible sweat beads and thick" not in dry["cast"]["aya"]["lock"]
    assert "grimy brown hospital dirt clinging to the whole body" in dry["cast"]["aya"]["lock"]

    body = prepare_episode(
        raw,
        appearance_override={"aya": {"bust": "大きめ", "butt": "大きめ", "build": "むっちり", "height": "低め"}},
    )
    body_lock = body["cast"]["aya"]["lock"]
    assert "large full breasts" in body_lock
    assert "C-cup" not in body_lock
    assert "a soft plump adult body" in body_lock
    assert "a soft waist and soft arms" in body_lock
    assert "slender thin body" not in body_lock
    assert "narrow waist, thin arms" not in body_lock
    assert "large buttocks" in body_lock
    assert "a short full-grown adult height" in body_lock
    assert "extremely tall" in body["cast"]["shino"]["lock"]
    assert "large buttocks" not in body["cast"]["shino"]["lock"]
    assert "nobody is giant" in body["world"]["lock"]
    cover = next(b for b in body["beats"] if b["id"] == "01-cover")
    cover_prompt = build_beat_prompt(body, cover)
    assert "large full breasts" in cover_prompt
    assert "a short full-grown adult height" in cover_prompt
    assert validate_episode(body, root=HOSPITAL_DIR) == []


def test_hospital_jacko_rear_and_dildo_leave_the_other_routes():
    raw = load_episode(HOSPITAL_DIR / "episode.json")
    assert "後ろアナル" in ui_choices("invite_pose")
    assert "□誘う・後ろアナル" in ui_choices("scene")
    assert "灰色・後ろアナル" in ui_choices("gin")
    jo = prepare_episode(raw, story_override="誘う", invite_pose_override="後ろアナル")
    assert validate_episode(jo, root=HOSPITAL_DIR) == []
    for base, cm in (("03-kiss", "24cm"), ("06-doggy", "24cm"), ("09-join", "20cm"), ("12-exit", "35cm")):
        set_b = next(b for b in jo["beats"] if b["id"] == f"{base}-jo-set")
        behind = next(b for b in jo["beats"] if b["id"] == f"{base}-jo-behind")
        anal = next(b for b in jo["beats"] if b["id"] == f"{base}-jo-anal")
        assert set_b.get("connect") == "cut"
        assert "jacko" not in extra_keys(set_b)
        assert "jacko" not in extra_keys(behind)
        assert ("mystic", 0.5) in extra_lora_entries(set_b)
        assert ("penis", 0.45) in extra_lora_entries(set_b)
        assert extra_lora_entries(anal)[0] == ("jacko", 0.7)
        assert "doggy" not in extra_keys(set_b) and "doggy" not in extra_keys(anal)
        for beat in (set_b, behind):
            last = beat["action"].lower().split("last frame:", 1)[1]
            assert "buried" not in last
            assert "base inside" not in last
            assert "outside" in last
        assert "hangs down from above" in behind["action"].lower()
        assert "travels into the anus" in anal["action"].lower()
        assert "from above" in anal["action"].lower()
        assert "hip joint" in anal["action"].lower()
        assert "chest faces down" in anal["action"].lower()
        assert "one neck" in anal["action"].lower()
        assert "hairless pussy" in set_b["action"].lower()
        assert "grown erect" not in set_b["action"].lower()
        assert cm in anal["action"]
        assert "気持ちいい" in anal["action"]
        cum = next(b for b in jo["beats"] if b["id"] == f"{base}-jo-cum")
        assert extra_lora_entries(cum)[0] == ("jacko", 0.65)
        assert "あ、いく" in cum["action"]
        gape = next(b for b in jo["beats"] if b["id"] == f"{base}-jo-gape")
        assert "wide ring" in gape["action"].lower()
        assert "drips toward the floor" in gape["action"].lower()
        assert "from inside the open anus" in gape["action"].lower()
        assert "hips stay up" in gape["action"].lower()
        assert "pulls back" in set_b["action"].lower()
        assert "jacko" not in extra_keys(gape)
        assert ("anuspussy", 0.4) in extra_lora_entries(gape)
        assert gape.get("steps") == 8 and gape.get("turbo") is False
    gin = prepare_episode(raw, gin_override="灰色・後ろアナル")
    gin_ids = [b["id"] for b in gin["beats"] if str(b["id"]).startswith("04-gin")]
    assert gin_ids[:6] == [
        "04-gin-lick-spot",
        "04-gin-lick",
        "04-gin-cunny",
        "04-gin-jupo",
        "04-gin-mouth",
        "04-gin-spitkiss",
    ]
    assert gin_ids[6:9] == ["04-gin-jo-set", "04-gin-jo-behind", "04-gin-jo-anal"]
    gin_mouth = next(b for b in gin["beats"] if b["id"] == "04-gin-mouth")
    assert "inside gin's mouth" in gin_mouth["action"].lower()
    assert "cumouf" in extra_keys(gin_mouth)
    assert "onto gin's face" not in gin_mouth["action"].lower()
    gin_cum = next(b for b in gin["beats"] if b["id"] == "04-gin-jo-cum")
    assert "inside gin's anus" in gin_cum["action"].lower()
    assert "bare closed slit" in gin_cum["action"].lower()
    assert "from the first frame to the last frame" in gin_cum["action"].lower()
    gin_set = next(b for b in gin["beats"] if b["id"] == "04-gin-jo-set")
    assert "gin bends" in gin_set["action"].lower()
    assert "aya's grown erect 24cm" in gin_set["action"].lower()
    assert "gin's groin stays a hairless pussy" in gin_set["action"].lower()
    gin_kiss = next(b for b in gin["beats"] if b["id"] == "04-gin-jo-kiss")
    assert "No penis" in gin_kiss["action"]
    assert "The grown shaft is gone" in gin_kiss["action"]
    fuck = prepare_episode(raw, gin_override="犯す")
    assert "04-gin-in" in [b["id"] for b in fuck["beats"]]
    assert "04-gin-jo-set" not in [b["id"] for b in fuck["beats"]]
    pee = prepare_episode(raw, toilet_override="pee")
    pee_act = next(b for b in pee["beats"] if b["id"] == "04-toilet")["action"].lower()
    assert "lemon-yellow" in pee_act or "yellow water" in pee_act
    assert "penis-shaped toy" not in pee_act
    horn = prepare_episode(raw, tsuno_override="角・病室でベッドの後ろアナル")
    assert [b["id"] for b in horn["beats"] if str(b["id"]).startswith("04-tsuno-jo")] == [
        "04-tsuno-jo",
        "04-tsuno-jo-anal",
        "04-tsuno-jo-cum",
        "04-tsuno-jo-gape",
        "04-tsuno-jo-kiss",
        "04-tsuno-jo-walk",
    ]


def test_hospital_place_swaps_nouns_after_the_act_is_chosen():
    raw = load_episode(HOSPITAL_DIR / "episode.json")
    plain = prepare_episode(raw, story_override="誘う", invite_pose_override="壁立ちバック")
    named = prepare_episode(
        raw,
        story_override="誘う",
        invite_pose_override="壁立ちバック",
        place_override="病棟（迷ったらこれ）",
        time_override="夜（迷ったらこれ）",
        weather_override="天候なし（迷ったらこれ）",
        dirt_override="場所に合わせる（迷ったらこれ）",
        camera_distance_override="横固定（迷ったらこれ）",
        seed_override="42",
    )
    beat = next(b for b in plain["beats"] if b["id"] == "03-kiss-in")
    assert build_beat_prompt(plain, beat) == build_beat_prompt(
        named, next(b for b in named["beats"] if b["id"] == "03-kiss-in")
    )
    assert named["render"]["seed"] == 42
    forest = prepare_episode(
        raw,
        story_override="誘う",
        invite_pose_override="壁立ちバック",
        toilet_override="小便",
        place_override="森林",
    )
    entered = next(b for b in forest["beats"] if b["id"] == "03-kiss-in")
    prompt = build_beat_prompt(forest, entered)
    assert "linoleum" not in prompt and "grey wall" not in prompt
    assert "packed earth" in prompt
    assert "travels into the anus" in prompt.lower()
    assert "turns from the opening pose" in build_beat_prompt(
        forest, next(b for b in forest["beats"] if b["id"] == "03-kiss")
    )
    assert "hollow empty" in prompt
    assert "fine dry sand" in prompt
    toilet = next(b for b in forest["beats"] if b["id"] == "04-toilet")
    toilet_prompt = build_beat_prompt(forest, toilet)
    assert "porcelain" not in toilet_prompt
    assert "yellow" in toilet_prompt.lower()
    rain = prepare_episode(raw, story_override="誘う", invite_pose_override="四つん這い", weather_override="雨")
    rain_prompt = build_beat_prompt(rain, next(b for b in rain["beats"] if b["id"] == "03-kiss"))
    assert "The ground is wet." in rain_prompt
    assert "chest and cheek" in rain_prompt.lower()
    low = prepare_episode(
        raw,
        story_override="誘う",
        invite_pose_override="四つん這い",
        camera_distance_override="結合の低い見上げ",
    )
    assert "Low camera between the calves" in build_beat_prompt(
        low, next(b for b in low["beats"] if b["id"] == "03-kiss")
    )
    oral = prepare_episode(
        raw,
        tsuno_override="角・病室で横になって挿入",
        camera_distance_override="結合の低い見上げ",
    )
    assert "Low camera between the calves" not in build_beat_prompt(
        oral, next(b for b in oral["beats"] if b["id"] == "04-tsuno-oral")
    )
    with pytest.raises(EpisodeError):
        prepare_episode(raw, seed_override="abc")
    zombie = prepare_episode(
        raw,
        story_override="誘う",
        invite_pose_override="壁立ちバック",
        enemy_kind_override="ゾンビ（迷ったらこれ）",
        aya_look_override="今のまま（迷ったらこれ）",
        enemy_look_override="今のまま（迷ったらこれ）",
    )
    assert build_beat_prompt(plain, beat) == build_beat_prompt(
        zombie, next(b for b in zombie["beats"] if b["id"] == "03-kiss-in")
    )
    human = prepare_episode(
        raw,
        story_override="誘う",
        invite_pose_override="壁立ちバック",
        enemy_kind_override="人間",
        enemy_looks_override={"miki": "韓国", "rei": "今のまま", "kana": "北欧", "shino": "日本"},
    )
    human_prompt = build_beat_prompt(human, next(b for b in human["beats"] if b["id"] == "03-kiss-in"))
    assert "vivid purple" not in human_prompt
    assert "hollow empty" not in human_prompt
    assert "24cm" in human_prompt
    assert "travels into the anus" in human_prompt.lower()
    assert "monolid" in human["cast"]["miki"]["lock"]
    assert "long brown permed hair" in human["cast"]["rei"]["lock"]
    assert "monolid" not in human["cast"]["rei"]["lock"]
    assert "light blue eyes" in human["cast"]["kana"]["lock"]
    assert "long straight black hair" in human["cast"]["shino"]["lock"]



def test_fantasy_places_replace_the_ward_and_the_default_stays():
    raw = load_episode(HOSPITAL_DIR / "episode.json")
    plain = prepare_episode(raw, story_override="受け入れる")
    held = prepare_episode(raw, story_override="受け入れる", place_override="病棟（迷ったらこれ）")
    cover = next(b for b in plain["beats"] if b["id"] == "01-cover")
    assert build_beat_prompt(plain, cover) == build_beat_prompt(
        held, next(b for b in held["beats"] if b["id"] == "01-cover")
    )
    places = {
        "雄大な草原": "soft grass",
        "丘": "grassy slope",
        "砂漠": "dry sand",
        "大塩湖": "white salt crust",
        "湖": "lake shore",
        "山道": "stone track",
        "鬱蒼とした湿原": "wet peat",
        "下水道": "wet brick",
        "宇宙ステーション": "metal deck",
        "大空の上の空中庭園": "above the clouds",
        "天空のガラス橋": "clear glass",
    }
    ward_words = re.compile(
        r"hospital|linoleum|corridor|sickroom|fluorescent|crumbling|rusted|\bHVAC\b|derelict|T-junction|"
        r"porcelain|beige|\btiles\b|Props in this shot|purple fluorescent|at night",
        re.I,
    )
    choices = ui_choices("place")
    assert choices[0] == "病棟（迷ったらこれ）"
    for label, token in places.items():
        assert label in choices
        ep = prepare_episode(raw, story_override="受け入れる", place_override=label, time_override="昼")
        assert validate_episode(ep, root=HOSPITAL_DIR) == []
        beat = next(b for b in ep["beats"] if b["id"] == "01-cover")
        prompt = build_beat_prompt(ep, beat)
        assert token in prompt, label
        assert not ward_words.search(prompt), (label, ward_words.search(prompt).group(0) if ward_words.search(prompt) else "")
        assert "turns" in prompt or "Aya" in prompt


def test_hospital_off_ward_human_and_insert_fixes():
    raw = load_episode(HOSPITAL_DIR / "episode.json")
    user = dict(
        story_override="□誘う（淫欲・失敗）",
        invite_pose_override="四つん這い股広げ（迷ったらこれ）",
        toilet_override="トイレ・触手",
        gin_override="灰色・騎乗・最初から膝曲げ",
        tsuno_override="角・病室で横になって挿入",
        scenes_override="miki=誘う・騎乗曲げ膝,rei=誘う・四つん這い,kana=誘う・立ちバック,shino=誘う・M字",
        connect_override="前の最終フレームから続ける",
    )
    ward_words = re.compile(
        r"hospital|linoleum|corridor|sickroom|fluorescent|crumbling|rusted|\bHVAC\b|derelict|T-junction|"
        r"porcelain|beige|\btiles\b|Props in this shot|purple fluorescent|at night",
        re.I,
    )
    zombie_words = re.compile(
        r"purple|lacerat|\bgash|hollow empty|shambl|eerie|ashen|gums exposed|"
        r"forked|reptile|scratch mark|red tear|four long fingers|monster eye|gray tongue|"
        r"dusky-gray|pale gray-white|sharp claw|vacant eye|no fifth finger|hands past mid-thigh",
        re.I,
    )
    for place in ("大都会", "森林", "坑道・佐渡"):
        ep = prepare_episode(raw, place_override=place, time_override="昼", enemy_kind_override="人間", **user)
        assert validate_episode(ep, root=HOSPITAL_DIR) == []
        gpu = [b for b in ep["beats"] if not is_ui_beat(b) and beat_renders(b)]
        assert [b["id"] for b in gpu if beat_source(b) == "t2v"] == ["01-cover"]
        for b in gpu:
            prompt = build_beat_prompt(ep, b, trigger=merge_trigger("", b))
            assert not ward_words.search(prompt), (place, b["id"], ward_words.search(prompt).group(0))
            assert not zombie_words.search(prompt), (place, b["id"], zombie_words.search(prompt).group(0))
            env = prompt.split("environment:", 1)[1].split("integrated_multimodal_description:", 1)[0]
            assert "High daylight lights the place" in env, b["id"]
    human_ward = prepare_episode(raw, enemy_kind_override="人間", **user)
    assert "extremely tall" in human_ward["cast"]["shino"]["lock"]
    assert "35cm" in human_ward["cast"]["shino"]["lock"]
    assert "two arms of ordinary length" in human_ward["cast"]["shino"]["lock"]
    assert "a human tongue" in human_ward["cast"]["shino"]["lock"]
    assert "Two small dark horns" in human_ward["cast"]["tsuno"]["lock"]
    assert "one large single eye" in human_ward["cast"]["tsuno"]["lock"]
    assert "five fingers" in human_ward["cast"]["tsuno"]["lock"]
    assert "24cm" in human_ward["cast"]["rei"]["lock"]
    assert "20cm" in human_ward["cast"]["kana"]["lock"]
    assert "intact skin on the hips" in human_ward["cast"]["kana"]["lock"]
    assert "a human tongue" in human_ward["cast"]["gin"]["lock"]
    assert "hanging out past the chin" not in human_ward["cast"]["gin"]["lock"]
    assert "no penis" in human_ward["cast"]["gin"]["lock"]
    lick_beat = next(b for b in human_ward["beats"] if b["id"] == "04-gin-lick")
    lick = build_beat_prompt(human_ward, lick_beat, trigger=merge_trigger("", lick_beat))
    assert "a human tongue hanging out" in lick
    assert "tongue hanging out" in lick
    assert "GROWS OUT of the open mouth" in lick
    assert "DOWN and FORWARD" in lick
    assert "presses on the clitoris" in lick
    assert "gray tongue" not in lick.lower()
    cunny_beat = next(b for b in human_ward["beats"] if b["id"] == "04-gin-cunny")
    cunny = build_beat_prompt(human_ward, cunny_beat, trigger=merge_trigger("", cunny_beat))
    assert "the long tongue still pressed on the clitoris" in cunny
    assert "KEEPS licking the clitoris" in cunny
    assert "GROWS into a clear erect 24cm" in cunny
    assert "licks the new shaft once" in cunny
    assert "clear adult eyes" in human_ward["cast"]["rei"]["lock"]
    zombie = prepare_episode(raw, **user)
    assert "forked reptile tongue" in zombie["cast"]["shino"]["lock"]
    assert "exactly four long fingers" in zombie["cast"]["tsuno"]["lock"]
    assert "vivid purple" in build_beat_prompt(zombie, next(b for b in zombie["beats"] if b["id"] == "03-kiss-in" or b["id"] == "03-kiss"))
    wait = next(b for b in zombie["beats"] if b["id"] == "03-kiss-wait")
    assert "keeps exactly two legs" in build_beat_prompt(zombie, wait)

    rei_press = next(b for b in zombie["beats"] if b["id"] == "06-doggy-press")
    low = rei_press["action"].lower()
    assert "rei's side faces the camera" in low
    assert "between aya's open knees" in low
    assert extra_lora_entries(rei_press) == []
    rei_in = next(b for b in zombie["beats"] if b["id"] == "06-doggy-in")
    assert "the whole shaft is hidden inside the anus" in rei_in["action"].lower()
    kana_press = next(b for b in zombie["beats"] if b["id"] == "09-join-press")
    assert "feet stand on that centerline between aya's feet" in kana_press["action"].lower()
    assert "knees plant" not in kana_press["action"].lower()

    shino_prep = next(b for b in zombie["beats"] if b["id"] == "12-exit")
    assert "kneels upright" in shino_prep["action"].lower()
    assert "already at the base" not in shino_prep["action"].lower()
    assert "towers over" not in shino_prep["action"].lower()
    assert extra_lora_entries(shino_prep) == []
    shino_in = next(b for b in zombie["beats"] if b["id"] == "12-exit-in")
    assert "penis" in extra_keys(shino_in)
    assert "licks forward along aya's neck" not in shino_in["action"].lower()

    order = [b["id"] for b in zombie["beats"]]
    assert order.index("04-tsuno-sidekiss") + 1 == order.index("04-tsuno-aim")
    assert order.index("04-tsuno-aim") + 1 == order.index("04-tsuno-ride")

    kana = next(b for b in zombie["beats"] if b["id"] == "09-kana-facial")
    kana_prompt = build_beat_prompt(zombie, kana, trigger=merge_trigger("", kana))
    assert "the camera moves in an arc around aya's face" in kana_prompt.lower()
    assert "all four feet" not in kana_prompt.lower()
    gin_mouth = next(b for b in zombie["beats"] if b["id"] == "04-gin-mouth")
    gin_prompt = build_beat_prompt(zombie, gin_mouth, trigger=merge_trigger("", gin_mouth))
    assert gin_prompt.startswith("CUMSH0T")
    assert "across gin's nose, eyes, and into gin's open mouth" in gin_prompt.lower()
    assert "all four feet" not in gin_prompt.lower()

    finger = prepare_episode(raw, toilet_override="トイレ・アナル指", connect_override="chain")
    ids = [b["id"] for b in finger["beats"] if str(b["id"]).startswith("04-toilet")]
    assert ids == ["04-toilet-in", "04-toilet-afin", "04-toilet-afast", "04-toilet-out"]
    afin = next(b for b in finger["beats"] if b["id"] == "04-toilet-afin")
    assert extra_lora_entries(afin)[0] == ("analfinger", 1.0)
    assert LORA_FILES["analfinger"] == "af_h3_vids512_imgs1024_000011750.safetensors"
    assert "3388162" in LORA_URLS["analfinger"]
    afin_prompt = build_beat_prompt(finger, afin, trigger=merge_trigger("", afin))
    assert afin_prompt.startswith("anal_finger")
    assert "inserts her index finger into her anus" in afin_prompt
    assert "all four feet" not in afin_prompt
    assert beat_source(afin) == "chain"
    tentacle = prepare_episode(raw, toilet_override="トイレ・触手")
    tent = next(b for b in tentacle["beats"] if b["id"] == "04-toilet")
    assert "tentacles are being inserted" in tent.get("trigger", "")


def test_hospital_review_motion_matches_the_mountain_notes():
    raw = load_episode(HOSPITAL_DIR / "episode.json")
    fours = prepare_episode(raw, story_override="誘う", invite_pose_override="四つん這い股広げ")
    setup = next(b for b in fours["beats"] if b["id"] == "09-join")
    press = next(b for b in fours["beats"] if b["id"] == "09-join-press")
    entered = next(b for b in fours["beats"] if b["id"] == "09-join-in")
    closed = next(b for b in fours["beats"] if b["id"] == "09-join-close")
    assert extra_lora_entries(setup) == []
    assert "siderear" not in extra_keys(setup)
    assert extra_lora_entries(entered)[0] == ("siderear", 0.8)
    assert "forward and back in short presses" in entered["action"].lower()
    assert "hold still joined at the base" not in entered["action"].lower()
    assert "the whole shaft is hidden inside the anus" in entered["action"].lower()
    press_low = press["action"].lower()
    assert "both knees stay planted, open wide to the left and right" in press_low
    assert "heels out" in press_low
    assert "the anus faces the camera at the top of the cleft" in press_low
    assert "starts in left true profile" in press_low
    assert "turns the torso a little toward the right" in press_low
    assert "feet and soles turn with the torso and point the same way as aya's feet and soles" in press_low
    assert "both torsos stay true profile" not in press_low
    assert "spine stays parallel" not in press_low
    assert "turns a little toward the right" in press["camera"].lower()
    assert "feet and soles point the same way as aya" in press["camera"].lower()
    assert "stays a little toward the right from left true profile" in entered["action"].lower()
    assert "the anus faces the camera at the top of the cleft" in entered["action"].lower()
    peak = next(b for b in fours["beats"] if b["id"] == "09-join-peak")
    assert "the partner stays a little toward the right" in peak["camera"].lower()
    assert ". partner " not in peak["camera"].lower()
    assert "pelvises freeze" in closed["action"].lower()
    assert "shaft stays outside" in closed["action"].lower()
    assert "thrust" not in extra_keys(closed)
    wall = prepare_episode(raw, story_override="誘う", invite_pose_override="壁立ちバック")
    wall_in = next(b for b in wall["beats"] if b["id"] == "03-kiss-in")
    assert "hold still joined at the base" in wall_in["action"].lower()
    assert "turns the torso a little" not in wall_in["action"].lower()
    assert "spine stays parallel" in wall_in["action"].lower()

    finger = prepare_episode(raw, toilet_override="トイレ・アナル指")
    afast = next(b for b in finger["beats"] if b["id"] == "04-toilet-afast")
    out = next(b for b in finger["beats"] if b["id"] == "04-toilet-out")
    assert "wide open ring" in afast["action"].lower()
    assert "thick brown feces" in afast["action"].lower()
    assert "analfinger" not in extra_keys(afast)
    assert "licks that fingertip clean" in out["action"].lower()
    assert "walks right" in out["action"].lower()
    assert out["trim"]["seconds"] == 10.0

    jo = prepare_episode(raw, story_override="誘う", invite_pose_override="後ろアナル")
    jo_set = next(b for b in jo["beats"] if b["id"] == "09-join-jo-set")
    assert "pulls back" in jo_set["action"].lower()
    assert "ninety degrees toward the left" in jo_set["action"].lower()
    assert "holds the pose" in jo_set["action"].lower()
    assert "buried" not in jo_set["action"].lower().split("last frame:", 1)[1]
    gin = prepare_episode(raw, gin_override="灰色・後ろアナル")
    gin_set = next(b for b in gin["beats"] if b["id"] == "04-gin-jo-set")
    assert "gin bends" in gin_set["action"].lower()
    assert "ninety degrees toward the left" in gin_set["action"].lower()
    lick = next(b for b in gin["beats"] if b["id"] == "04-gin-lick")
    lick_prompt = build_beat_prompt(gin, lick)
    assert "one continuous take" in lick_prompt.lower()
    spit = next(b for b in gin["beats"] if b["id"] == "04-gin-spitkiss")
    assert "left foot stays inside the frame" in spit["action"].lower()
    assert "aya's left foot" in spit["camera"].lower()

    spot = next(b for b in fours["beats"] if b["id"] == "10-shino-spot")
    assert "already stooping" in spot["action"].lower()
    assert "point left" in spot["action"].lower()
    assert "walks in from the right" not in spot["action"].lower()

    mountain = prepare_episode(
        raw,
        story_override="誘う",
        invite_pose_override="四つん這い股広げ",
        place_override="山道",
    )
    facial = next(b for b in mountain["beats"] if b["id"] == "09-kana-facial")
    facial_prompt = build_beat_prompt(mountain, facial)
    assert "the same door stays behind aya" not in facial_prompt.lower()
    assert "looks up" in facial_prompt.lower()
    assert "one continuous take" in facial_prompt.lower()
    kiss = next(b for b in mountain["beats"] if b["id"] == "09-kana-kiss")
    assert "one continuous take" in kiss["action"].lower()
    assert validate_episode(fours, root=HOSPITAL_DIR) == []
    assert validate_episode(finger, root=HOSPITAL_DIR) == []
    assert validate_episode(jo, root=HOSPITAL_DIR) == []
