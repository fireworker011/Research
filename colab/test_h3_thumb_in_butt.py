#!/usr/bin/env python3
"""ThumbInButt split-list contract for h3-20260914-anal-17.

Imports locked API from colab/h3_lora_studio.py (not a side module).
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from h3_lora_studio import (
    CHAIN_PACK_ORDER,
    NONE_LABEL,
    STORY_KEEP_LABEL,
    STORY_ORDER,
    STORY_PLAY_CHAIN,
    STORY_PLAY_REF_CHAIN,
    TIB_FILE,
    TIB_LORA_ID,
    TIB_ON_LABEL,
    apply_thumbinbutt_stack,
    clip_is_anal_insert,
    clip_wants_thumbinbutt,
    compose_scene_choice,
    generate_anal_pattern,
    generic_wants_thumbinbutt,
    load_story,
    parse_play_ja,
    parse_thumb_in_butt,
    prepare_story_clip,
    story_play_label,
    story_title_labels,
)

TIB_STRENGTH = 0.55
TIB_TRIGGER = "thum1n8utt"


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
        "commute-120s", STORY_PLAY_CHAIN
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
    assert all(
        not clip_wants_thumbinbutt(last, i, thumb_in_butt=True) for i in range(len(last["clips"]))
    )
    assert all(
        not clip_wants_thumbinbutt(bath, i, thumb_in_butt=True) for i in range(len(bath["clips"]))
    )


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
    assert TIB_LORA_ID in ids
    tib = next(r for r in out if r["id"] == TIB_LORA_ID)
    assert tib["role"] == "helper"
    assert float(tib.get("strength") or tib.get("strength_model") or 0) == TIB_STRENGTH
    assert not str(tib.get("trigger") or "").strip()
    assert tib.get("filename") == TIB_FILE
    assert tib.get("lora_name") == TIB_FILE
    off = apply_thumbinbutt_stack(base, on=False)
    assert TIB_LORA_ID not in [r["id"] for r in off]


def test_apply_stack_on_adds_third_helper_when_oral_full():
    oral = [
        {"id": "mystic-xxx-h3", "role": "concept"},
        {"id": "blowjob-h3", "role": "act"},
        {"id": "penis-lora-h3", "role": "helper"},
        {"id": "synth-pussy-h3", "role": "helper"},
        {"id": "larry-v4", "role": "turbo"},
    ]
    out = apply_thumbinbutt_stack(oral, on=True)
    assert TIB_LORA_ID in [r["id"] for r in out]
    helpers = [r for r in out if r.get("role") == "helper"]
    assert len(helpers) == 3


def test_creampie_into_anus_is_not_insert():
    roof = load_story("rooftop-100s")
    kiss = roof["clips"][3]
    paco_waist = roof["clips"][5]
    cream = roof["clips"][6]
    assert kiss["label"] == "30-40 キス 挿入"
    assert paco_waist["label"] == "50-60 腰"
    assert cream["label"] == "60-70 アナル中出し"
    assert clip_is_anal_insert(kiss["prompt"], kiss["situation"]) is True
    assert clip_is_anal_insert(paco_waist["prompt"], paco_waist["situation"]) is False
    assert clip_is_anal_insert(cream["prompt"], cream["situation"]) is False
    assert clip_wants_thumbinbutt(roof, 5, thumb_in_butt=True) is False
    assert clip_wants_thumbinbutt(roof, 6, thumb_in_butt=True) is False
    p3 = generate_anal_pattern("anal-p3-meet-anal")
    assert clip_is_anal_insert(p3["clips"][0]["prompt"], p3["clips"][0]["situation"]) is True
    assert clip_is_anal_insert(p3["clips"][1]["prompt"], p3["clips"][1]["situation"]) is False
    assert clip_is_anal_insert(p3["clips"][2]["prompt"], p3["clips"][2]["situation"]) is False


def test_prepare_default_off_keeps_anal_stack(tmp_path):
    story = load_story("dishes-90s")
    planned = prepare_story_clip(story, 9, last_frame="x.png", stills_dir=tmp_path)
    ids = [r["id"] for r in planned["stack"]]
    assert ids == ["mystic-xxx-h3", "penis-lora-h3", "synth-pussy-h3"]
    assert TIB_TRIGGER not in planned["prompt"]


def test_prepare_thumb_in_butt_on_adds_helper(tmp_path):
    story = load_story("dishes-90s")
    planned = prepare_story_clip(
        story, 9, last_frame="x.png", stills_dir=tmp_path, thumb_in_butt=True
    )
    ids = [r["id"] for r in planned["stack"]]
    assert ids[:3] == ["mystic-xxx-h3", "penis-lora-h3", "synth-pussy-h3"]
    assert TIB_LORA_ID in ids
    tib = next(r for r in planned["stack"] if r["id"] == TIB_LORA_ID)
    assert not str(tib.get("trigger") or "").strip()
    assert tib.get("filename") == TIB_FILE
    assert TIB_TRIGGER not in planned["prompt"]
    oral_prep = prepare_story_clip(
        story, 8, last_frame="x.png", stills_dir=tmp_path, thumb_in_butt=True
    )
    oral_ids = [r["id"] for r in oral_prep["stack"]]
    assert oral_prep["situation"] == "oral"
    assert TIB_LORA_ID in oral_ids
    oral_end = load_story("last-stop-40s")
    skip = prepare_story_clip(
        oral_end, 1, last_frame="x.png", stills_dir=tmp_path, thumb_in_butt=True
    )
    assert TIB_LORA_ID not in [r["id"] for r in skip["stack"]]


def test_tib_civitai_alias_counts_as_present(tmp_path):
    from h3_lora_studio import comfy_missing_loras, missing_stack_files, resolve_lora_relname

    lora_dir = tmp_path / "loras"
    lora_dir.mkdir()
    alias = lora_dir / "MiniMax H3 - ThumbInButt.safetensors"
    alias.write_bytes(b"x" * 6_000_000)
    assert resolve_lora_relname(lora_dir, TIB_FILE) == "MiniMax H3 - ThumbInButt.safetensors"
    stack = [{"id": TIB_LORA_ID, "filename": TIB_FILE}]
    assert missing_stack_files(stack, lora_dir) == []
    obj = {"LoraLoaderModelOnly": {"lora_name": ["MiniMax H3 - ThumbInButt.safetensors"]}}
    assert comfy_missing_loras(stack, obj) == []


def test_no_side_tib_bind_module():
    bind = Path(__file__).resolve().parent / "h3_tib_bind.py"
    assert not bind.is_file()
