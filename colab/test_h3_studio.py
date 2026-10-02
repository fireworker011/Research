"""H3 Studio lane. Plans and prompts only. The ward engine is not imported."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "colab"))

import h3_studio as studio
from h3_studio_colab_main import main
from _write_studio_nb import make_nb, mirror_engine

ACTION = "She sets one plain bottle on the counter and looks up."
HERO = {
    "hair": "black bob",
    "color": "fair",
    "race": "Japanese",
    "age": "28",
    "height": "160 cm",
    "weight": "52 kg",
    "clothes": "grey lounge top",
    "place": "night kitchen",
}


def plan(job: str, **overrides):
    raw = {
        "job": job,
        "action": ACTION,
        "hero": dict(HERO),
        "runtime": "comfy",
        "high_mem": True,
    }
    raw.update(overrides)
    return studio.build_plan(studio.request_from(raw))


def test_lora_registry_adds_only_swap_and_real():
    assert set(studio.LORA_FILES) == {"combat", "charswap", "anime2real"}
    assert studio.LORA_FILES["combat"] == "H3_Combat_V2.safetensors"
    assert studio.LORA_FILES["charswap"] == "h3_character_swap_pro4500_1000.safetensors"
    assert studio.LORA_FILES["anime2real"] == "Anime2Realsim__H3.safetensors"
    assert list(studio.LORA_FILES).count("combat") == 1
    source = (ROOT / "colab" / "h3_studio.py").read_text(encoding="utf-8")
    assert "prfight1" not in source
    assert "prfight2" in source
    assert "import h3_episode" not in source
    assert "from h3_episode" not in source
    for banned in ("kasumi", "HANDOFF", "episode.json"):
        assert banned not in source


def test_helpers_are_the_studio_pair():
    assert studio.STUDIO_HELPERS == (
        "colab/h3_studio.py",
        "colab/h3_studio_colab_main.py",
    )
    assert set(studio.JOB_HELP) == set(studio.JOBS)


def test_empty_look_fields_are_omitted():
    built = plan(
        "text_scene",
        hero={"hair": "black bob", "color": "", "clothes": "grey top"},
        enemy={"hair": "  ", "place": ""},
    )
    assert built["look"] == "Look: Hero hair black bob, clothes grey top."
    assert "color" not in built["look"]
    assert "Enemy" not in built["look"]
    assert "Look:" in built["prompt"]


def test_all_blank_sheets_skip_look():
    built = plan("text_scene", hero={}, enemy={})
    assert built["look"] == ""
    assert "Look:" not in built["prompt"]


def test_japanese_look_stops():
    with pytest.raises(studio.StudioError, match="英語"):
        plan("text_scene", hero={"hair": "黒髪"})


def test_swap_requires_hero_sheet_and_splits_locks():
    with pytest.raises(studio.StudioError, match="Hero シート"):
        plan("swap_character", video="motion.mp4", hero_sheet="")
    common = {"hero_sheet": "hero.png", "video": "motion.mp4"}
    body = plan("swap_character", **common)
    face = plan("swap_face", **common)
    outfit = plan("swap_outfit", **common)
    assert body["task"] == face["task"] == outfit["task"] == "ref2va"
    for built in (body, face, outfit):
        assert built["loras"] == [
            {"key": "charswap", "file": studio.LORA_FILES["charswap"], "strength": 1.0}
        ]
        assert built["turbo"] is False
        assert built["inputs"]["video"] == "motion.mp4"
        assert "subject_definitions:" in built["prompt"]
        assert built["prompt"].index("subject_definitions:") < built["prompt"].index("summary:")
        assert built["prompt"].index("summary:") < built["prompt"].index("retention_analysis:")
        assert built["prompt"].index("retention_analysis:") < built["prompt"].index("detailed_description:")
        assert built["prompt"].index("detailed_description:") < built["prompt"].index("overall_soundscape:")
        assert built["prompt"].index("overall_soundscape:") < built["prompt"].index("non_diegetic_music:")
    assert "Picture 1 locks the full body." in body["prompt"]
    assert "Picture 1 locks the face and hair only." in face["prompt"]
    assert "The clothes follow Video 1." in face["prompt"]
    assert "Picture 1 locks the clothes only." in outfit["prompt"]
    assert "The face follows Video 1." in outfit["prompt"]
    assert "locks the full body" not in face["prompt"]
    assert "combat" not in {item["key"] for item in face["loras"]}


def test_combat_is_fl2va_and_finish_changes_only_the_trigger():
    with pytest.raises(studio.StudioError, match="最初の絵"):
        plan("combat_motion")
    plain = plan("combat_motion", first_still="a.png", last_still="b.png")
    finish = plan("combat_motion", first_still="a.png", last_still="b.png", finish=True, turbo=True)
    assert plain["task"] == "fl2va"
    assert plain["prompt"].startswith(studio.COMBAT_TRIGGER + "\n")
    assert finish["prompt"].startswith(studio.COMBAT_FINISH_TRIGGER + "\n")
    assert "How the reference pictures align with the target video —" in plain["prompt"]
    assert "5.00-second mark" in plain["prompt"]
    assert plain["loras"][0]["strength"] == 1.0
    assert plain["loras"][0]["file"] == "H3_Combat_V2.safetensors"
    assert finish["turbo"] is False
    assert any("Turbo" in note for note in finish["notes"])
    assert plain["generate"] is False
    assert "charswap" not in {item["key"] for item in plain["loras"]}


def test_api_stops_combat_swap_and_real_and_allows_text():
    with pytest.raises(studio.StudioError, match="runtime=api"):
        plan("combat_motion", runtime="api", high_mem=True, first_still="a.png", last_still="b.png")
    with pytest.raises(studio.StudioError, match="runtime=api"):
        plan("swap_face", runtime="api", hero_sheet="h.png", video="m.mp4")
    with pytest.raises(studio.StudioError, match="runtime=api"):
        plan("real", runtime="api", hero_sheet="h.png")
    text = plan("text_scene", runtime="api", high_mem=False)
    assert text["task"] == "t2va"
    assert text["loras"] == []
    assert text["prompt"].startswith("integrated_multimodal_description:")
    assert "How the reference pictures align" not in text["prompt"]


def test_high_mem_off_stops_lora_jobs():
    with pytest.raises(studio.StudioError, match="High-Mem"):
        plan("combat_motion", high_mem=False, first_still="a.png", last_still="b.png")
    with pytest.raises(studio.StudioError, match="High-Mem"):
        plan("swap_character", high_mem=False, hero_sheet="h.png", video="m.mp4")


def test_blocked_inputs_stop():
    samples = [
        {"action": "She points at a YouTube screen."},
        {"video": "https://youtu.be/abc"},
        {"hero": {"clothes": "Marvel shirt"}},
        {"dialogue": "マーベル"},
        {"action": "She films a 公式CM."},
        {"action": "She films a 公式 CM."},
        {"place_on_hero": "オルビスの棚"},
        {"action": "She holds the Furbo box."},
    ]
    for sample in samples:
        raw = {"job": "text_scene", "action": ACTION, "hero": dict(HERO)}
        if "place_on_hero" in sample:
            raw["hero"]["place"] = sample["place_on_hero"]
        else:
            raw.update(sample)
        with pytest.raises(studio.StudioError, match="止める"):
            studio.build_plan(studio.request_from(raw))


def test_age_gate_and_duration_canvas():
    with pytest.raises(studio.StudioError, match="21"):
        plan("text_scene", hero={"age": "20"})
    with pytest.raises(studio.StudioError, match="21"):
        plan("text_scene", hero={"age": "teen"})
    built = plan("text_scene", hero={"age": "21"})
    assert "age 21" in built["look"]
    blank_age = dict(HERO)
    blank_age["age"] = ""
    assert "age" not in plan("text_scene", hero=blank_age)["look"]
    with pytest.raises(studio.StudioError, match="4–5"):
        plan("text_scene", duration=6)
    short = plan("text_scene", duration=4)
    assert short["duration"] == 4
    assert short["fps"] == 24
    assert short["width"] == 768
    assert short["height"] == 1344
    assert short["resolution"] == "768P"
    assert studio.request_from({"job": "text_scene", "action": ACTION}).duration == 5.0


def test_dialogue_stays_inside_the_official_tag():
    built = plan("text_scene", dialogue="見て")
    assert "<d>[Japanese] 見て</d>" in built["prompt"]
    outside = studio.DIALOGUE_BLOCK_RE.sub("", built["prompt"])
    assert studio.CJK_RE.search(outside) is None
    quoted = plan("text_scene", action=ACTION + " 「見て」")
    assert "<d>[Japanese] 見て</d>" in quoted["prompt"]
    with pytest.raises(studio.StudioError, match="英語1本"):
        plan("text_scene", action="見て")
    with pytest.raises(studio.StudioError, match="英語1本"):
        plan("text_scene", action="She nods.\nShe leaves.")


def test_real_and_refused_overlay():
    still = plan("real", hero_sheet="anime.png")
    assert still["task"] == "fl2va"
    assert still["loras"][0]["key"] == "anime2real"
    assert still["loras"][0]["strength"] == 1.0
    assert still["inputs"]["first_still"] == still["inputs"]["last_still"] == "anime.png"
    assert "LumiReal" not in still["prompt"]
    moving = plan("real", hero_sheet="anime.png", video="take.mp4")
    assert moving["task"] == "ref2va"
    with pytest.raises(studio.StudioError, match="0.5"):
        studio.assert_loras_exclusive({"charswap", "anime2real"})
    with pytest.raises(studio.StudioError, match="LumiReal"):
        studio.assert_loras_exclusive({"charswap", "anime2real"})


def test_two_pass_links_video_and_does_not_merge_loras():
    built = studio.build_plan(
        studio.request_from(
            {
                "job": "two_pass",
                "action": ACTION,
                "passes": [
                    {
                        "job": "swap_character",
                        "action": ACTION,
                        "hero_sheet": "hero.png",
                        "video": "motion.mp4",
                    },
                    {
                        "job": "real",
                        "action": ACTION,
                        "hero_sheet": "hero.png",
                        "video": "ignored.mp4",
                    },
                ],
            }
        )
    )
    assert built["loras"] == []
    assert built["generate"] is False
    first, second = built["passes"]
    assert first["output_mp4"] == "pass-a.mp4"
    assert second["inputs"]["video"] == "{pass-a.mp4}"
    assert {item["key"] for item in first["loras"]} == {"charswap"}
    assert first["loras"][0]["strength"] == 1.0
    assert {item["key"] for item in second["loras"]} == {"anime2real"}
    assert second["loras"][0]["strength"] == 1.0
    assert "LumiReal" in second["prompt"]
    assert "LumiReal" not in first["prompt"]
    assert first["sampler_id"] != second["sampler_id"]
    with pytest.raises(studio.StudioError, match="入れ子"):
        studio.build_plan(
            studio.request_from(
                {
                    "job": "two_pass",
                    "passes": [
                        {"job": "two_pass", "action": ACTION, "passes": []},
                        {"job": "real", "action": ACTION, "hero_sheet": "a.png"},
                    ],
                }
            )
        )


def test_orbit_uses_one_picture_and_no_lora_file():
    built = plan("orbit360", first_still="turn.png")
    assert built["task"] == "fl2va"
    assert built["loras"] == []
    assert built["inputs"]["first_still"] == built["inputs"]["last_still"] == "turn.png"
    assert "same picture" in built["prompt"]
    with pytest.raises(studio.StudioError, match="同じ絵"):
        plan("orbit360", first_still="a.png", last_still="b.png")
    with pytest.raises(studio.StudioError, match="ファイル名確定後"):
        studio.request_from({"job": "orbit360", "action": ACTION, "orbit_file": "orbit.safetensors"})


def test_refused_lanes_and_unknown_job():
    for key in ("weapon", "gunfu", "continuity"):
        with pytest.raises(studio.StudioError, match="今足さない"):
            studio.request_from({"job": "text_scene", "action": ACTION, key: True})
    with pytest.raises(studio.StudioError, match="ジョブが違う"):
        studio.request_from({"job": "ward", "action": ACTION})


def test_seven_text_scenes_are_official_t2va_without_lora():
    batch = studio.build_text_scenes()
    assert batch["generate"] is False
    assert batch["runtime"] == "api"
    assert batch["task"] == "t2va"
    assert batch["loras"] == []
    assert batch["poster"] == {"kind": "still", "video": False}
    assert batch["face_lock"] == "later_ref2va"
    assert batch["duration"] == 6.0
    assert batch["fps"] == 24
    assert batch["width"] == 1344
    assert batch["height"] == 768
    assert batch["aspect"] == "16:9"
    assert batch["resolution"] == "768P"
    ids = [clip["scene_id"] for clip in batch["clips"]]
    assert ids == [
        "hana-gate",
        "host-live",
        "hana-cart",
        "hana-shelf",
        "host-drop",
        "hana-box",
        "hana-exit",
    ]
    spoken = {
        "host-live": "よし…金曜だけどライブ、いける…",
        "host-drop": "ライブが落ちたあああ！",
        "hana-exit": "ふう…温め直しゃ直るだろ。",
    }
    banned = ("HUD", "minimap", "MISSION PASSED", "GTA")
    for clip in batch["clips"]:
        assert clip["job"] == "text_scene"
        assert clip["task"] == "t2va"
        assert clip["runtime"] == "api"
        assert clip["loras"] == []
        assert clip["turbo"] is False
        assert clip["generate"] is False
        assert clip["duration"] == 6.0
        assert clip["fps"] == 24
        assert clip["width"] == 1344
        assert clip["height"] == 768
        assert clip["aspect"] == "16:9"
        assert clip["shots"] == 1
        assert clip["inputs"] == {"hero_sheet": "", "video": "", "first_still": "", "last_still": ""}
        prompt = clip["prompt"]
        assert prompt.startswith("integrated_multimodal_description: [Shot 1] Live-action, horizontal 16:9.")
        assert prompt.count("[Shot 1]") == 1
        assert "[Shot 2]" not in prompt
        assert "overall_soundscape:" in prompt
        assert prompt.index("integrated_multimodal_description:") < prompt.index("overall_soundscape:")
        assert prompt.index("overall_soundscape:") < prompt.index("non_diegetic_music:")
        assert "non_diegetic_music: N/A" in prompt
        assert "Picture" not in prompt
        assert "Video" not in prompt
        assert "charswap" not in prompt.lower()
        assert "combat" not in prompt.lower()
        assert "vertical 9:16" not in prompt
        outside = studio.DIALOGUE_BLOCK_RE.sub("", prompt)
        assert studio.CJK_RE.search(outside) is None
        for word in banned:
            assert word not in prompt
        line = spoken.get(clip["scene_id"])
        if line:
            assert f"<d>[Japanese] {line}</d>" in prompt
            assert "off-screen voiceover" not in prompt
            assert "lips remain completely closed" not in prompt
            sound = prompt.split("overall_soundscape:", 1)[1].split("non_diegetic_music:", 1)[0]
            assert line not in sound
            assert studio.CJK_RE.search(sound) is None
        else:
            assert "<d>" not in prompt
    code = studio.main(["scenes"])
    assert code == 0


def test_notebook_does_not_fetch_the_ward():
    nb = make_nb()
    blob = json.dumps(nb, ensure_ascii=False)
    source = "".join(nb["cells"][1]["source"])
    assert "h3_studio.py" in blob
    assert "h3_studio_colab_main.py" in blob
    assert 'H3_STUDIO_GENERATE"] = "0"' in source
    for banned in (
        "h3_episode",
        "kasumi",
        "HANDOFF",
        "episode.json",
        "hospital-exit",
        "rei_escape",
        "futanari",
    ):
        assert banned not in blob
    assert nb["cells"][1]["cell_type"] == "code"


def test_mirror_matches_colab_engine():
    mirror_engine()
    left = (ROOT / "colab" / "h3_studio.py").read_bytes()
    right = (ROOT / "minimaxh3" / "h3_studio.py").read_bytes()
    assert left == right


def test_colab_main_writes_a_plan_and_refuses_generate(tmp_path, monkeypatch):
    out = tmp_path / "plan.json"
    monkeypatch.delenv("H3_STUDIO_JSON", raising=False)
    monkeypatch.setenv("H3_STUDIO_JOB", "text_scene")
    monkeypatch.setenv("H3_STUDIO_ACTION", ACTION)
    monkeypatch.setenv("H3_STUDIO_HERO_HAIR", "black bob")
    monkeypatch.setenv("H3_STUDIO_HERO_COLOR", "")
    monkeypatch.setenv("H3_STUDIO_DURATION", "5")
    monkeypatch.setenv("H3_STUDIO_GENERATE", "0")
    monkeypatch.setenv("H3_STUDIO_OUT", str(out))
    monkeypatch.setenv("H3_STUDIO_RUNTIME", "comfy")
    monkeypatch.setenv("H3_STUDIO_HIGH_MEM", "1")
    assert main() == 0
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["task"] == "t2va"
    assert data["generate"] is False
    assert "color" not in data["look"]
    monkeypatch.setenv("H3_STUDIO_GENERATE", "1")
    blocked = tmp_path / "nope.json"
    monkeypatch.setenv("H3_STUDIO_OUT", str(blocked))
    assert main() == 1
    assert not blocked.exists()
