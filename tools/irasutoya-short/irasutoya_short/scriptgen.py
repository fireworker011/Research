"""実測した短い回の秒数（フック→状況→一文→対立→オチ）で台本を作る。"""

from __future__ import annotations

import re

from irasutoya_short.catalog import ASSET_CATALOG, VOICES
from irasutoya_short.constants import MAX_SCENES, MIN_SCENES
from irasutoya_short.textutil import spoken, wrap_telop


def _sentences(text: str) -> list[str]:
    parts = re.split(r"[。！？]", text)
    return [p.strip() for p in parts if p.strip()]


def _quote(chunks: list[str], index: int, default: str) -> str:
    found = re.findall(r"「([^」]+)」", "\n".join(chunks))
    if index < len(found):
        return found[index].strip()
    return default


def _bullet(bullets: list[str], index: int, default: str) -> str:
    if index < len(bullets) and bullets[index].strip():
        cleaned = re.sub(r"「[^」]*」", "", bullets[index])
        cleaned = re.sub(r"[、。]{2,}", "、", cleaned).strip(" 、。")
        return cleaned or default
    return default


def _from(bullets: list[str], start: int) -> str:
    parts = [_bullet(bullets, i, "") for i in range(start, len(bullets))]
    parts = [part for part in parts if part]
    if not parts:
        raise ValueError("対立の箇条書きが空です。")
    return "。".join(parts)


# @junjun_ranran 7655625158299897108（25.45秒）のショット秒。research/script-kata 参照。
BEAT_SECONDS = (2.37, 5.53, 0.97, 5.53, 11.05)


def generate_script(brief: dict) -> dict:
    """箇条書きとオチから、実測の5ビート＋クレジットの台本を作る。"""
    punchline = str(brief.get("punchline") or "").strip()
    if not punchline:
        raise ValueError("オチ（punchline）が空です。締めがフワッとするので必須です。")
    bullets = [str(b).strip() for b in brief.get("bullets") or [] if str(b).strip()]
    if len(bullets) < 3:
        raise ValueError("箇条書きは状況・一文カード・対立の3つが要ります。")
    series = str(brief.get("series_character") or "仕事押し付け君").strip()
    hook = str(brief.get("hook") or brief.get("title") or f"{series}の話").strip()
    closing = str(brief.get("closing") or "").strip()
    blob = bullets + [punchline, hook]
    rival_line = _quote(blob, 0, hook)

    scenes = [
        _scene(
            1, "hook", "rival", rival_line, "office",
            ["rival_smug"], "zoom", "none", BEAT_SECONDS[0], label=series,
        ),
        _scene(
            2, "develop", "narrator", _bullet(bullets, 0, bullets[0]),
            "office", ["hero_trouble"], "none", "paper", BEAT_SECONDS[1], code_props=["papers"],
        ),
        _scene(
            3, "develop", "narrator", _bullet(bullets, 1, bullets[1]),
            "lines", [], "none", "whoosh", BEAT_SECONDS[2],
        ),
        _scene(
            4, "develop", "hero", _from(bullets, 2),
            "office", ["hero_angry"], "shake", "none", BEAT_SECONDS[3], emotion="angry",
        ),
        _scene(
            5, "punch", "narrator", punchline, "office",
            ["rival_bow"], "zoom", "coin", BEAT_SECONDS[4], label=series,
        ),
        _credit_scene(series),
    ]
    _validate(scenes, punchline, closing)
    credits = _credits(scenes)
    return {
        "title": hook,
        "series_character": series,
        "punchline": punchline,
        "closing": closing,
        "scenes": scenes,
        "credits": credits,
        "asset_ids": _asset_ids(scenes),
    }


def _scene(
    sid: int,
    role: str,
    speaker: str,
    text: str,
    bg: str,
    characters: list[str],
    effect: str,
    sfx: str,
    hint: float,
    props: list[str] | None = None,
    code_props: list[str] | None = None,
    label: str = "",
    emotion: str = "",
) -> dict:
    voice = VOICES[speaker]
    style = voice["style_id"]
    if emotion == "angry" and "angry_style_id" in voice:
        style = voice["angry_style_id"]
    telop_width = 12
    max_lines = 2
    return {
        "id": sid,
        "role": role,
        "speaker": speaker,
        "style_id": style,
        "credit": voice["credit"],
        "text": spoken(text),
        "telop": wrap_telop(text, telop_width, max_lines),
        "bg": bg,
        "characters": [
            {"id": cid, "who": ASSET_CATALOG[cid]["who"], "label": label if ASSET_CATALOG[cid]["who"] == "rival" else ""}
            for cid in characters
        ],
        "props": props or [],
        "code_props": code_props or [],
        "effect": effect,
        "sfx": sfx,
        "duration_hint": hint,
    }


def _credit_scene(series: str) -> dict:
    lines = [
        "VOICEVOX:四国めたん",
        "VOICEVOX:白上虎太郎",
        "VOICEVOX:玄野武宏",
        "VOICEVOX:剣崎雌雄",
    ]
    return {
        "id": 6,
        "role": "credit",
        "speaker": "narrator",
        "style_id": VOICES["narrator"]["style_id"],
        "credit": VOICES["narrator"]["credit"],
        "text": "",
        "telop": "\n".join(lines),
        "bg": "credit",
        "characters": [],
        "props": [],
        "effect": "none",
        "sfx": "none",
        "duration_hint": 2.2,
        "series_note": series,
    }


def _asset_ids(scenes: list[dict]) -> list[str]:
    ids: list[str] = []
    for scene in scenes:
        for ch in scene["characters"]:
            if ch["id"] not in ids:
                ids.append(ch["id"])
        for prop in scene["props"]:
            if prop not in ids:
                ids.append(prop)
    return ids


def _credits(scenes: list[dict]) -> list[str]:
    found: list[str] = []
    for scene in scenes:
        credit = scene.get("credit") or ""
        if credit and credit not in found and scene["role"] != "credit":
            found.append(credit)
    for line in ("VOICEVOX:四国めたん", "VOICEVOX:白上虎太郎", "VOICEVOX:玄野武宏", "VOICEVOX:剣崎雌雄"):
        if line not in found:
            found.append(line)
    return found


def _validate(scenes: list[dict], punchline: str, closing: str) -> None:
    if not (MIN_SCENES <= len(scenes) <= MAX_SCENES):
        raise ValueError(f"シーン数は{MIN_SCENES}〜{MAX_SCENES}です。今は{len(scenes)}です。")
    roles = [s["role"] for s in scenes]
    if "hook" not in roles or "punch" not in roles or roles[-1] != "credit":
        raise ValueError("フック、オチ、末尾クレジットが揃っていません。")
    if roles.index("hook") > roles.index("punch"):
        raise ValueError("並びはフックのあとがオチです。")
    punch_text = " ".join(s["text"] + s["telop"] for s in scenes if s["role"] == "punch")
    token = _sentences(punchline)[0][:8]
    if token and token not in punch_text:
        raise ValueError("オチの文言がオチシーンに入っていません。")
    if closing:
        spoken_blob = "\n".join(s["text"] for s in scenes if s["role"] != "credit")
        if closing in spoken_blob:
            raise ValueError("締めの問いかけは読み上げに入れません。短い回の実測に、動画内CTAがありません。")
    assets = _asset_ids(scenes)
    if len(assets) > 20:
        raise ValueError("いらすとや素材が20点を超えます。背景はコードで描いてください。")
    for scene in scenes:
        if scene["role"] == "credit":
            continue
        if "\n" not in scene["telop"] and len(scene["telop"]) > 14:
            raise ValueError(f"シーン{scene['id']}のテロップに改行がありません。")
