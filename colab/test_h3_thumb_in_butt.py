#!/usr/bin/env python3
"""ThumbInButt split-list contract for h3-20260913-anal-12."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from h3_lora_studio import (
    CHAIN_PACK_ORDER,
    STORY_ORDER,
    STORY_PLAY_REF_CHAIN,
    load_story,
    prepare_story_clip,
    story_play_label,
)
from h3_scene_split import (
    NONE_LABEL,
    STORY_KEEP_LABEL,
    TIB_LORA_ID,
    TIB_ON_LABEL,
    TIB_STRENGTH,
    TIB_TRIGGER,
    apply_thumbinbutt_stack,
    clip_wants_thumbinbutt,
    compose_scene_choice,
    extra_tib_download_ids,
    generic_wants_thumbinbutt,
    parse_play_ja,
    parse_thumb_in_butt,
    story_title_labels,
    strip_thumb_in_butt_trigger,
)


def test_parse_selectors():
    assert parse_thumb_in_butt(NONE_LABEL) is False
    assert parse_thumb_in_butt("") is False
    assert parse_thumb_in_butt(TIB_ON_LABEL) is True
    assert parse_thumb_in_butt("あり") is True
    assert parse_play_ja("参照つなぐ") == STORY_PLAY_REF_CHAIN
    assert parse_play_ja("専用") == "dedicated"
    assert parse_play_ja("") == STORY_PLAY_REF_CHAIN


def test_story_title_labels_unique_no_play_suffix():
    labels = story_title_labels()
    assert len(labels) == len(STORY_ORDER) + len(CHAIN_PACK_ORDER)
    assert len(set(labels)) == len(labels)
    assert "登校" in labels and "洗い物" in labels and "ハチコウ" in labels
    assert all("（" not in row for row in labels)


def test_compose_scene_choice_story_wins():
    assert compose_scene_choice("なし", "登校", "参照つなぐ") == story_play_label(
        "commute-120s", STORY_PLAY_REF_CHAIN
    )
    assert compose_scene_choice("アナルセックス（女体）", STORY_KEEP_LABEL, "専用") == "アナルセックス（女体）"
    assert compose_scene_choice(NONE_LABEL, STORY_KEEP_LABEL, "") == story_play_label(
        "commute-120s", STORY_PLAY_REF_CHAIN
    )
    assert compose_scene_choice("①口内で終わる", "洗い物", "つなぐ") == story_play_label(
        "dishes-90s", "chain"
    )


def test_generic_wants_not_scat_or_closeup_or_oral_end():
    assert generic_wants_thumbinbutt("futa_anal")
    assert generic_wants_thumbinbutt("anal_penetration")
    assert generic_wants_thumbinbutt("anal-p2-bj-anal")
    assert generic_wants_thumbinbutt("anal-p3-meet-anal")
    assert not generic_wants_thumbinbutt("anal-p1-oral")
    assert not generic_wants_thumbinbutt("scat_act")
    assert not generic_wants_thumbinbutt("anal_fingering")
    assert not generic_wants_thumbinbutt("anal_closeup")
    assert not generic_wants_thumbinbutt("oral")


def test_dishes_wants_prep_insert_first_paco_only():
    story = load_story("dishes-90s")
    sits = [c["situation"] for c in story["clips"]]
    assert sits[8] == "oral"
    assert sits[9] == "futa_anal"
    assert sits[10] == "futa_anal"
    assert sits[11] == "futa_visible"
    assert clip_wants_thumbinbutt(story, 8, thumb_in_butt=True) is True
    assert clip_wants_thumbinbutt(story, 9, thumb_in_butt=True) is True
    assert clip_wants_thumbinbutt(story, 10, thumb_in_butt=True) is True
    assert clip_wants_thumbinbutt(story, 11, thumb_in_butt=True) is False
    assert clip_wants_thumbinbutt(story, 7, thumb_in_butt=True) is False
    assert clip_wants_thumbinbutt(story, 9, thumb_in_butt=False) is False
    assert clip_wants_thumbinbutt(story, 0, thumb_in_butt=True, mode="r2v") is False


def test_skip_oral_end_and_semen_bath():
    last = load_story("last-stop-40s")
    bath = load_story("semen-bath-70s")
    assert all(not clip_wants_thumbinbutt(last, i, thumb_in_butt=True) for i in range(len(last["clips"])))
    assert all(not clip_wants_thumbinbutt(bath, i, thumb_in_butt=True) for i in range(len(bath["clips"])))


def test_apply_stack_off_keeps_existing_scat_tib():
    scat = [
        {"id": "mystic-xxx-h3", "role": "concept"},
        {"id": TIB_LORA_ID, "role": "act", "strength": TIB_STRENGTH, "trigger": ""},
        {"id": "penis-lora-h3", "role": "helper"},
        {"id": "synth-pussy-h3", "role": "helper"},
    ]
    out = apply_thumbinbutt_stack(scat, on=False)
    assert [r["id"] for r in out] == [r["id"] for r in scat]
    assert out[1]["role"] == "act"


def test_apply_stack_on_adds_helper_without_trigger():
    base = [
        {"id": "mystic-xxx-h3", "role": "concept"},
        {"id": "penis-lora-h3", "role": "act"},
        {"id": "synth-pussy-h3", "role": "helper"},
    ]
    out = apply_thumbinbutt_stack(base, on=True)
    ids = [r["id"] for r in out]
    assert ids == ["mystic-xxx-h3", "penis-lora-h3", "synth-pussy-h3", TIB_LORA_ID]
    tib = out[-1]
    assert tib["role"] == "helper"
    assert float(tib["strength"]) == TIB_STRENGTH
    assert tib.get("trigger") == ""
    off = apply_thumbinbutt_stack(base, on=False)
    assert [r["id"] for r in off] == ["mystic-xxx-h3", "penis-lora-h3", "synth-pussy-h3"]


def test_prepare_default_off_keeps_anal_stack(tmp_path):
    story = load_story("dishes-90s")
    planned = prepare_story_clip(story, 9, last_frame="x.png", stills_dir=tmp_path)
    ids = [r["id"] for r in planned["stack"]]
    assert ids == ["mystic-xxx-h3", "penis-lora-h3", "synth-pussy-h3"]
    assert TIB_TRIGGER not in planned["prompt"]
    assert extra_tib_download_ids() == [TIB_LORA_ID]
    assert TIB_TRIGGER not in strip_thumb_in_butt_trigger(f"hello {TIB_TRIGGER} world")
