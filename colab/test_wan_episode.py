"""Wan plan for hospital-exit-adult. Checks id order and source.

Chain starts the stall from the previous frame. Cut redraws a connect:cut stall with no start image.

Video pixels are for a human to watch. This file does not render.
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "minimaxh3"))

from h3_episode import load_episode, prepare_episode  # noqa: E402
from wan_episode import (  # noqa: E402
    WAN_SLOT_LORAS,
    onedrive_root,
    build_wan_graph,
    plan_wan_shots,
    wan_beat_prompt,
    wan_needs_start_image,
    wan_weight_jobs,
)

HOSPITAL = ROOT / "minimaxh3" / "episodes" / "hospital-exit-adult" / "episode.json"

RIDE_IDS = (
    "04-tsuno-meet-spot",
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
    "04-tsuno-walk",
)
WASH_IDS = (
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
)

# Cut dropdown: every Tsuno beat is T2V, except rib seats and peaks that stay I2V.
RIDE_CUT = {
    "04-tsuno-meet-spot": "t2v",
    "04-tsuno-kiss": "chain",
    "04-tsuno-oral": "chain",
    "04-tsuno-wait": "chain",
    "04-tsuno-spit": "t2v",
    "04-tsuno-beckon": "chain",
    "04-tsuno-lie": "t2v",
    "04-tsuno-sidekiss": "chain",
    "04-tsuno-ride": "t2v",
    "04-tsuno-peak": "chain",
    "04-tsuno-ride-kiss": "chain",
    "04-tsuno-walk": "t2v",
}
# Chain dropdown. Authored connect:cut yields, so every Tsuno beat here is I2V.
RIDE_CHAIN = {
    "04-tsuno-meet-spot": "chain",
    "04-tsuno-kiss": "chain",
    "04-tsuno-oral": "chain",
    "04-tsuno-wait": "chain",
    "04-tsuno-spit": "chain",
    "04-tsuno-beckon": "chain",
    "04-tsuno-lie": "chain",
    "04-tsuno-sidekiss": "chain",
    "04-tsuno-ride": "chain",
    "04-tsuno-peak": "chain",
    "04-tsuno-ride-kiss": "chain",
    "04-tsuno-walk": "chain",
}
WASH_CUT = {
    "04-tsuno-meet-spot": "t2v",
    "04-tsuno-carry": "t2v",
    "04-tsuno-stall": "t2v",
    "04-tsuno-set": "t2v",
    "04-tsuno-anal": "t2v",
    "04-tsuno-cum": "t2v",
    "04-tsuno-gape": "t2v",
    "04-tsuno-rise": "t2v",
    "04-tsuno-stall-kiss": "t2v",
    "04-tsuno-walk": "t2v",
}
WASH_CHAIN = {
    "04-tsuno-meet-spot": "chain",
    "04-tsuno-carry": "chain",
    "04-tsuno-stall": "chain",
    "04-tsuno-set": "chain",
    "04-tsuno-anal": "chain",
    "04-tsuno-cum": "chain",
    "04-tsuno-gape": "chain",
    "04-tsuno-rise": "chain",
    "04-tsuno-stall-kiss": "chain",
    "04-tsuno-walk": "chain",
}


def _tsuno(ep, prefix_ids):
    rows = [b for b in ep["beats"] if str(b["id"]) in prefix_ids]
    return rows


def _prepare(tsuno: str, connect: str):
    raw = load_episode(HOSPITAL)
    return prepare_episode(
        raw,
        story_override="受け入れる",
        tsuno_override=tsuno,
        connect_override=connect,
    )


def _assert_sources(ep, ids, expected):
    rows = _tsuno(ep, ids)
    assert [b["id"] for b in rows] == list(ids)
    for beat in rows:
        source = beat["source"]
        assert source in ("t2v", "chain")
        assert source == expected[beat["id"]]
        shot = next(s for s in plan_wan_shots(ep) if s["id"] == beat["id"])
        assert shot["source"] == source
        assert shot["start_image"] is wan_needs_start_image(source)


def test_wget_log_hides_civitai_token():
    from wan_colab_setup import _shown

    shown = _shown(["wget", "https://civitai.com/api/download/models/1?token=secret"])
    assert "secret" not in shown
    assert "token=(hidden)" in shown


def test_store_root_can_be_google_drive(monkeypatch):
    monkeypatch.setenv("WAN_ONEDRIVE_ROOT", "/content/drive/MyDrive/wan-hospital")
    assert onedrive_root() == Path("/content/drive/MyDrive/wan-hospital")


def test_notebook_saves_weights_on_google_drive():
    import ast
    from _write_wan_episode_nb import notebook

    nb = notebook()
    sources = ["".join(cell["source"]) for cell in nb["cells"] if cell["cell_type"] == "code"]
    assert len(sources) == 3
    for src in sources:
        ast.parse(src)
    assert 'drive.mount("/content/drive")' in sources[0]
    assert 'CivitaiのAPIキー = ""' in sources[1]
    assert "/content/drive/MyDrive/wan-hospital" in sources[1]
    assert "/content/drive/MyDrive/wan-hospital" in sources[2]
    assert "rclone" not in sources[0]
    assert "rclone" not in sources[1]
    assert "rclone" not in sources[2]


def test_wan_slot_files_are_wan22_pairs_not_h3():
    jobs = wan_weight_jobs()
    assert jobs
    for url, rel in jobs:
        assert url.startswith("https://huggingface.co/") or url.startswith("https://civitai.com/api/download/models/")
        low = rel.lower()
        assert "minimax" not in low and "mh3" not in low and "10eros" not in low
    assert any(rel.endswith("Q8H.gguf") for _url, rel in jobs)
    assert any(rel.endswith("Q8L.gguf") for _url, rel in jobs)
    for slot, spec in WAN_SLOT_LORAS.items():
        assert spec["high_name"].startswith(f"wan-{slot}-")
        assert spec["low_name"].startswith(f"wan-{slot}-")
        assert spec["high_url"] != spec["low_url"] or slot in ("cunny", "thumbinbutt")
    graph = build_wan_graph(
        source="t2v",
        prompt="Aya walks.",
        width=1024,
        height=576,
        seconds=6,
        seed=1,
        filename_prefix="video/wan_test",
        slots=[{"slot": "kiss", "strength": 0.5, "high": "wan-kiss-high.safetensors", "low": "wan-kiss-low.safetensors"}],
        use_lightx2v=False,
    )
    highs = [graph[key]["inputs"]["lora_name"] for key in graph if key.startswith("h")]
    lows = [graph[key]["inputs"]["lora_name"] for key in graph if key.startswith("l")]
    assert highs == ["wan-kiss-high.safetensors"]
    assert lows == ["wan-kiss-low.safetensors"]
    assert graph["4"]["class_type"] == "UnetLoaderGGUF"
    assert graph["4"]["inputs"]["unet_name"].endswith("Q8H.gguf")
    assert graph["5"]["inputs"]["unet_name"].endswith("Q8L.gguf")


def test_every_wan_prompt_uses_the_wan22_shape():
    ep = _prepare("角・騎乗", "カット")
    drawn = [b for b in ep["beats"] if isinstance(b, dict) and b.get("action")]
    assert drawn
    for beat in drawn:
        text = wan_beat_prompt(ep, beat)
        assert "subject_definitions:" not in text
        assert "[Shot 1]" not in text
        assert "integrated_multimodal_description:" not in text
        assert "<Picture 1>" not in text
        assert "Camera:" in text
        assert "By the end, that motion has happened once" in text
        if beat["source"] in ("chain", "still"):
            assert "previous frame" in text
        else:
            assert "previous frame" not in text


def test_invite_ride_order_and_sources():
    cut = _prepare("角・騎乗", "カット")
    chain = _prepare("角・騎乗", "前の最終フレームから続ける")
    _assert_sources(cut, RIDE_IDS, RIDE_CUT)
    _assert_sources(chain, RIDE_IDS, RIDE_CHAIN)


def _slots(ep, beat_id):
    shot = next(s for s in plan_wan_shots(ep) if s["id"] == beat_id)
    return [row["slot"] for row in shot["slots"]]


def _with_toilet(toilet: str):
    raw = load_episode(HOSPITAL)
    return prepare_episode(raw, story_override="受け入れる", toilet_override=toilet, connect_override="カット")


def test_scene_loras_follow_the_prepared_act():
    anal = _prepare("anal_back", "カット")
    assert "anal" in _slots(anal, "04-tsuno-in")
    assert "anal" in _slots(anal, "04-tsuno-peak")
    assert "anal" not in _slots(anal, "04-tsuno-walk")
    assert "anal sex" in wan_beat_prompt(anal, next(b for b in anal["beats"] if b["id"] == "04-tsuno-in")).lower()

    stand = _prepare("accept_stand", "カット")
    assert "anal" in _slots(stand, "04-tsuno-in")
    assert "anal" not in _slots(stand, "04-tsuno-hold")

    nelson = _prepare("nelson", "カット")
    nelson_in = _slots(nelson, "04-tsuno-in")
    assert "anal" in nelson_in and "nelson" in nelson_in
    assert "FU11N31S0N" in wan_beat_prompt(nelson, next(b for b in nelson["beats"] if b["id"] == "04-tsuno-in"))

    wash = _prepare("角・個室", "カット")
    assert "anal" in _slots(wash, "04-tsuno-anal")
    assert "anal" in _slots(wash, "04-tsuno-cum")
    assert "anal sex" in wan_beat_prompt(wash, next(b for b in wash["beats"] if b["id"] == "04-tsuno-anal")).lower()
    assert "anal sex" not in wan_beat_prompt(wash, next(b for b in wash["beats"] if b["id"] == "04-tsuno-cum")).lower()
    assert "anal" not in _slots(wash, "04-tsuno-stall")
    assert "anal" not in _slots(wash, "04-tsuno-gape")

    miki = prepare_episode(
        load_episode(HOSPITAL),
        story_override="受け入れる",
        toilet_override="wash_miki",
        connect_override="カット",
    )
    assert "anal" in _slots(miki, "04-toilet")
    assert "anal" in _slots(miki, "04-toilet-cum")
    assert "anal" not in _slots(miki, "04-toilet-gape")
    assert "anal sex" in wan_beat_prompt(miki, next(b for b in miki["beats"] if b["id"] == "04-toilet")).lower()
    assert "anal sex" not in wan_beat_prompt(miki, next(b for b in miki["beats"] if b["id"] == "04-toilet-cum")).lower()

    seated = prepare_episode(
        load_episode(HOSPITAL),
        story_override="invite",
        invite_pose_override="ride",
        connect_override="カット",
    )
    assert "doggy" not in _slots(seated, "06-doggy")
    assert "missionary" not in _slots(seated, "06-doggy-wait")
    assert "missionary" not in _slots(seated, "09-join")
    assert "anal" not in _slots(seated, "03-kiss")

    dog = prepare_episode(
        load_episode(HOSPITAL),
        story_override="受け入れる",
        dog_override="invite_oral",
        connect_override="前の最終フレームから続ける",
    )
    assert "missionary" not in _slots(dog, "04-dog-lick")
    assert "missionary" not in _slots(dog, "04-dog-wait")
    assert "missionary" not in _slots(dog, "04-dog-jupo")

    ride = _prepare("角・騎乗", "カット")
    assert "anal" not in _slots(ride, "04-tsuno-peak")
    assert "missionary" not in _slots(ride, "04-tsuno-peak")
    assert "doggy" in _slots(ride, "06-doggy")
    assert "doggy" in _slots(ride, "06-doggy-peak")
    assert "missionary" in _slots(ride, "09-join")
    assert "missionary" in _slots(ride, "09-join-peak")

    pee = _with_toilet("pee")
    assert "pee" in _slots(pee, "04-toilet")
    assert "anal" not in _slots(pee, "04-toilet")

    finger = _with_toilet("finger")
    assert "anal" not in _slots(finger, "04-toilet")

    scat = _with_toilet("wash")
    assert "scat" in _slots(scat, "04-toilet")
    assert "anal" not in _slots(scat, "04-toilet")


def test_wash_carry_order_and_chain_starts_stall_from_previous_frame():
    cut = _prepare("角・個室", "カット")
    chain = _prepare("角・個室", "前の最終フレームから続ける")
    _assert_sources(cut, WASH_IDS, WASH_CUT)
    _assert_sources(chain, WASH_IDS, WASH_CHAIN)
    stall = next(b for b in chain["beats"] if b["id"] == "04-tsuno-stall")
    assert stall["source"] == "chain"
    shot = next(s for s in plan_wan_shots(chain) if s["id"] == "04-tsuno-stall")
    assert shot["start_image"] is True
    assert wan_needs_start_image(stall["source"]) is True
