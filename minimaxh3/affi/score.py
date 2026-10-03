"""Rule score. Five axes, 20 points each. Verdicts: 使える / 直す / 捨てる."""

from __future__ import annotations

import re
from typing import Any

from minimaxh3.affi.script import char_count

AXES = ("最初3秒", "テンポ", "見やすさ", "プロフィール誘導", "リスク")
PASS_AT = 12
OK = 16

_HARD = (
    "治る",
    "必ず",
    "稼げる",
    "月収",
    "年収",
    "改善",
    "死角ゼロ",
    "美白",
    "エイジング",
    "px.a8.net",
    "a8mat=",
)
_LINE = re.compile(r"(?<![A-Za-z])LINE(?![A-Za-z])|ＬＩＮＥ|ライン登録")
_URL = re.compile(r"https?://", re.I)


def score_script(script: dict[str, Any], product: dict[str, Any]) -> dict[str, Any]:
    beats = list(script.get("beats") or [])
    spoken = "\n".join(b["spoken"] for b in beats)
    captions = "\n".join(b["caption"] for b in beats)
    prompts = "\n".join(p.get("prompt") or "" for p in script.get("parts") or [])
    blob = "\n".join((spoken, captions, prompts, script.get("hook") or ""))
    description = script.get("description") or ""
    hard = [w for w in _HARD if w in blob or w in description]
    if _LINE.search(blob) or _LINE.search(description):
        hard.append("LINE")
    if _URL.search(prompts) or _URL.search(spoken) or _URL.search(captions):
        hard.append("URL")
    names = tuple(product.get("names_in_video") or ())
    name_hits = sum(spoken.count(n) + captions.count(n) + prompts.count(n) for n in names)
    if name_hits >= 2:
        hard.append("商品名")

    if hard:
        points = {axis: (0 if axis == "リスク" else OK) for axis in AXES}
        points["リスク"] = 0
        return _result(points, "捨てる", "禁止: " + "、".join(hard))

    hook_ok = bool(beats) and beats[0]["role"] == "フック" and beats[0]["start"] == 0.0 and beats[0]["end"] == 3.0
    hook_ok = hook_ok and _rate_ok(beats[0]) and beats[0]["spoken"] == script.get("hook")
    rates_ok = bool(beats) and all(_rate_ok(b) for b in beats)
    span_ok = _covers(beats)
    caption_ok = bool(beats) and all(" / " in b["caption"] for b in beats)
    cta_ok = any(b["start"] >= 10 and "プロフィール" in b["spoken"] for b in beats)
    cta_ok = cta_ok and "プロフィール" in captions and not _URL.search(spoken)
    disclosure_ok = description.startswith("アフィリエイト広告を含みます") and "#PR" in description.splitlines()[0]
    ai_ok = "AI" in description
    a8_ok = product.get("a8_status") == "提携中"
    fields_ok = all(
        token in prompts
        for token in (
            "integrated_multimodal_description:",
            "overall_soundscape:",
            "non_diegetic_music:",
            "Picture 1",
        )
    )
    once = name_hits == 1

    points = {
        "最初3秒": OK if hook_ok else 8,
        "テンポ": OK if rates_ok and span_ok else 8,
        "見やすさ": OK if caption_ok else 8,
        "プロフィール誘導": OK if cta_ok else 8,
        "リスク": OK if disclosure_ok and ai_ok and a8_ok and fields_ok and not once else 8,
    }
    if any(v < PASS_AT for v in points.values()):
        return _result(points, "直す", "型か表示が足りない")
    return _result(points, "使える", "禁止表現なし。軸はいずれも基準以上。")


def _rate_ok(beat: dict[str, Any]) -> bool:
    span = float(beat["end"]) - float(beat["start"])
    if span <= 0:
        return False
    return char_count(beat["spoken"]) / span <= 6.5


def _covers(beats: list[dict[str, Any]]) -> bool:
    if not beats:
        return False
    return beats[0]["start"] == 0.0 and beats[-1]["end"] == 15.0


def _result(points: dict[str, int], verdict: str, reason: str) -> dict[str, Any]:
    return {
        "axes": points,
        "total": sum(points.values()),
        "verdict": verdict,
        "reason": reason,
    }
