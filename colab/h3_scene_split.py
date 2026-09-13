#!/usr/bin/env python3
"""Split Colab ③ lists and optional ThumbInButt helper (rev h3-20260913-anal-12).

Does not change default futa_anal stacks. Import from h3_lora_studio / notebook CELL3.
"""
from __future__ import annotations

from typing import Any

from h3_lora_studio import (
    CHAIN_PACK_ORDER,
    STORY_ORDER,
    STORY_PLAY_JA,
    STORY_PLAY_REF_CHAIN,
    STORY_PLAYS,
    STORY_TITLE_JA,
    clip_is_anal_insert,
    story_play_label,
)

NONE_LABEL = "なし"
STORY_KEEP_LABEL = "（シーンのまま）"
TIB_ON_LABEL = "あり（挿入前後）"
TIB_OFF_LABEL = "なし"
TIB_LORA_ID = "thumbinbutt-h3"
TIB_STRENGTH = 0.55
TIB_TRIGGER = "thum1n8utt"
MAX_HELPERS = 2

TIB_SKIP_SITUATIONS = frozenset(
    {
        "scat_act",
        "anal_fingering",
        "oral",
        "oral_creampie",
        "futa_blowjob",
    }
)
TIB_SKIP_STORY_IDS = frozenset(
    {
        "semen-bath-70s",
        "last-stop-40s",
        "karaoke-50s",
        "red-light-50s",
        "lecture-desk-50s",
        "gas-station-30s",
        "tunnel-phone-30s",
        "hachiko-30s",
    }
)
GENERIC_TIB_SITS = frozenset(
    {
        "futa_anal",
        "anal_penetration",
        "anal-p2-bj-anal",
        "anal-p3-meet-anal",
    }
)
SEX_ANAL_SITS = frozenset({"futa_anal", "anal_penetration"})
_KEEP = frozenset({"", NONE_LABEL, STORY_KEEP_LABEL, "シーンのまま"})
_PLAY_JA_TO_KEY = {ja: key for key, ja in STORY_PLAY_JA.items()}
_TITLE_TO_ID = {title: sid for sid, title in STORY_TITLE_JA.items()}


def parse_thumb_in_butt(name: str | None) -> bool:
    raw = str(name or "").strip()
    if raw in {"", NONE_LABEL, TIB_OFF_LABEL, "off", "false", "False", "0"}:
        return False
    return raw == TIB_ON_LABEL or raw.startswith("あり") or raw.lower() in {"on", "true", "yes"}


def parse_play_ja(name: str | None) -> str:
    raw = str(name or "").strip()
    if raw in STORY_PLAYS:
        return raw
    if raw in _PLAY_JA_TO_KEY:
        return _PLAY_JA_TO_KEY[raw]
    if raw.endswith("（参照つなぐ修）") or raw == "参照つなぐ修":
        return "ref_chain_rewrite"
    if raw.endswith("（参照つなぐ）") or raw == "参照つなぐ":
        return "ref_chain"
    if raw.endswith("（つなぐ修）") or raw == "つなぐ修":
        return "chain_rewrite"
    if raw.endswith("（つなぐ）") or raw == "つなぐ":
        return "chain"
    if raw.endswith("（専用）") or raw == "専用":
        return "dedicated"
    return STORY_PLAY_REF_CHAIN


def resolve_story_title(name: str | None) -> str:
    raw = str(name or "").strip()
    if raw in STORY_TITLE_JA:
        return raw
    if raw in _TITLE_TO_ID:
        return _TITLE_TO_ID[raw]
    for suffix in ("（参照つなぐ修）", "（参照つなぐ）", "（つなぐ修）", "（つなぐ）", "（専用）"):
        if raw.endswith(suffix):
            return resolve_story_title(raw[: -len(suffix)])
    raise SystemExit(f"物語が分かりません: {name}")


def story_title_labels() -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for sid in list(STORY_ORDER) + list(CHAIN_PACK_ORDER):
        title = STORY_TITLE_JA[sid]
        if title in seen:
            raise SystemExit(f"duplicate story title: {title}")
        seen.add(title)
        out.append(title)
    return out


def compose_scene_choice(scene: str | None, story: str | None, play: str | None) -> str:
    title = str(story or "").strip()
    if title not in _KEEP:
        sid = resolve_story_title(title)
        return story_play_label(sid, parse_play_ja(play))
    raw_scene = str(scene or "").strip()
    if raw_scene not in _KEEP:
        return raw_scene
    return story_play_label("commute-120s", STORY_PLAY_REF_CHAIN)


def generic_wants_thumbinbutt(situation: str | None) -> bool:
    sit = str(situation or "").strip()
    return sit in GENERIC_TIB_SITS


def strip_thumb_in_butt_trigger(prompt: str | None) -> str:
    raw = str(prompt or "")
    if not raw:
        return raw
    return raw.replace(TIB_TRIGGER, "").replace(TIB_TRIGGER.upper(), "")


def extra_tib_download_ids() -> list[str]:
    return [TIB_LORA_ID]


def _first_paco_index(clips: list[dict[str, Any]]) -> int | None:
    insert_at: int | None = None
    for i, clip in enumerate(clips):
        if clip_is_anal_insert(str(clip.get("prompt") or ""), str(clip.get("situation") or "")):
            insert_at = i
            break
    if insert_at is None:
        return None
    for j in range(insert_at + 1, len(clips)):
        sit = str(clips[j].get("situation") or "")
        prompt = str(clips[j].get("prompt") or "")
        if sit not in SEX_ANAL_SITS:
            continue
        if clip_is_anal_insert(prompt, sit):
            continue
        return j
    return None


def clip_wants_thumbinbutt(
    story: dict[str, Any],
    idx: int,
    *,
    thumb_in_butt: bool = False,
    mode: str | None = None,
) -> bool:
    if not thumb_in_butt:
        return False
    clips = list(story.get("clips") or [])
    if idx < 0 or idx >= len(clips):
        return False
    sid = str(story.get("id") or "")
    if sid in TIB_SKIP_STORY_IDS:
        return False
    mode_key = str(mode or story.get("mode") or "").strip().lower()
    if mode_key == "r2v" and idx == 0:
        return False
    if story.get("use_cast_ref") and idx == 0:
        return False
    clip = clips[idx]
    sit = str(clip.get("situation") or "")
    prompt = str(clip.get("prompt") or "")
    nxt = clips[idx + 1] if idx + 1 < len(clips) else None
    next_insert = False
    if nxt is not None:
        next_insert = clip_is_anal_insert(
            str(nxt.get("prompt") or ""), str(nxt.get("situation") or "")
        )
    if sit in TIB_SKIP_SITUATIONS and not next_insert:
        return False
    if next_insert:
        return True
    if clip_is_anal_insert(prompt, sit):
        return True
    return idx == _first_paco_index(clips)


def apply_thumbinbutt_stack(
    stack: list[dict[str, Any]] | None,
    on: bool = False,
    *,
    thumb_in_butt: bool | None = None,
) -> list[dict[str, Any]]:
    rows = [dict(r) for r in (stack or [])]
    enabled = bool(on) if thumb_in_butt is None else bool(thumb_in_butt)
    if not enabled:
        return rows
    if any(str(r.get("id") or "") == TIB_LORA_ID for r in rows):
        for row in rows:
            if str(row.get("id") or "") == TIB_LORA_ID:
                row["trigger"] = ""
                row.setdefault("strength", TIB_STRENGTH)
                row.setdefault("strength_model", TIB_STRENGTH)
        return rows
    helper_n = sum(1 for r in rows if str(r.get("role") or "") == "helper")
    if helper_n >= MAX_HELPERS:
        return rows
    rows.append(
        {
            "id": TIB_LORA_ID,
            "role": "helper",
            "strength": TIB_STRENGTH,
            "strength_model": TIB_STRENGTH,
            "trigger": "",
        }
    )
    return rows


resolve_thumb_in_butt = parse_thumb_in_butt
resolve_split_scene = compose_scene_choice
inject_thumb_in_butt = apply_thumbinbutt_stack
clip_wants_thumb_in_butt = clip_wants_thumbinbutt
