"""フック→展開→オチ→締め。記事の応用①。"""

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


def generate_script(brief: dict) -> dict:
    """箇条書きとオチから 14 シーンの台本を作る。"""
    punchline = str(brief.get("punchline") or "").strip()
    if not punchline:
        raise ValueError("オチ（punchline）が空です。締めがフワッとするので必須です。")
    bullets = [str(b).strip() for b in brief.get("bullets") or [] if str(b).strip()]
    if not bullets:
        raise ValueError("ネタの箇条書き（bullets）が空です。")
    series = str(brief.get("series_character") or "仕事押し付け君").strip()
    hook = str(brief.get("hook") or brief.get("title") or f"{series}を撃退した話").strip()
    closing = str(brief.get("closing") or "あなたならどうする？").strip()
    punch_parts = _sentences(punchline)
    punch_action = punch_parts[0]
    punch_result = punch_parts[-1] if len(punch_parts) > 1 else punchline
    blob = bullets + [punchline]
    rival_line = _quote(blob, 0, "お前の方が早いだろ")
    panic_line = _quote(blob, 1, "今送るから")

    scenes = [
        _scene(
            1, "hook", "narrator", hook, "office",
            ["rival_smug", "hero_trouble"], "zoom", "none", 2.2, label=series,
        ),
        _scene(
            2, "develop", "narrator", _bullet(bullets, 0, "金曜の17時、机に書類が置かれた"),
            "office",             ["hero_trouble"], "none", "paper", 2.4, code_props=["papers"],
        ),
        _scene(
            3, "develop", "rival", rival_line, "office",
            ["rival_smug"], "none", "none", 2.2, label=series,
        ),
        _scene(
            4, "develop", "narrator", _bullet(bullets, 1, "そう言い残して定時で帰っていった"),
            "office", ["rival_smug"], "none", "whoosh", 2.2, label=series,
        ),
        _scene(
            5, "develop", "hero", "俺の仕事じゃねえだろ", "office",
            ["hero_angry"], "shake", "none", 2.0, emotion="angry",
        ),
        _scene(
            6, "develop", "narrator", _bullet(bullets, 2, "誰もいない夜、終電まで残った"),
            "office_night", ["hero_tired"], "none", "none", 2.5,
        ),
        _scene(
            7, "develop", "narrator", _bullet(bullets, 3, "月曜の朝、何事もなかった顔だった"),
            "office",             ["rival_smug"], "none", "none", 2.2, label=series, props=["mug"],
        ),
        _scene(
            8, "develop", "hero", "まだ気づいてないのか", "office",
            ["hero_angry"], "lines", "none", 2.0, emotion="angry",
        ),
        _scene(
            9, "punch", "narrator", punch_action, "chat",
            ["hero_smile"], "zoom", "notify", 2.4,
        ),
        _scene(
            10, "punch", "boss", "どういうことだ", "office",
            ["boss_angry"], "shake", "shock", 2.0,
        ),
        _scene(
            11, "punch", "rival", panic_line, "office",
            ["rival_pale"], "none", "none", 2.2, label=series,
        ),
        _scene(
            12, "punch", "narrator", punch_result, "office",
            ["rival_bow"], "zoom", "coin", 2.4, label=series,
        ),
        _scene(
            13, "close", "narrator", closing, "lines",
            ["hero_smile"], "zoom", "none", 2.2,
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
        "id": 14,
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
    if "hook" not in roles or "punch" not in roles or "close" not in roles:
        raise ValueError("フック、オチ、締めが揃っていません。")
    if roles.index("hook") > roles.index("punch") or roles.index("punch") > roles.index("close"):
        raise ValueError("並びはフック→展開→オチ→締めです。")
    punch_text = " ".join(s["text"] + s["telop"] for s in scenes if s["role"] == "punch")
    token = _sentences(punchline)[0][:8]
    if token and token not in punch_text:
        raise ValueError("オチの文言がオチシーンに入っていません。")
    close_text = " ".join(s["text"] + s["telop"] for s in scenes if s["role"] == "close")
    if closing[:6] not in close_text:
        raise ValueError("締めの一言が入っていません。")
    assets = _asset_ids(scenes)
    if len(assets) > 20:
        raise ValueError("いらすとや素材が20点を超えます。背景はコードで描いてください。")
    for scene in scenes:
        if scene["role"] == "credit":
            continue
        if "\n" not in scene["telop"] and len(scene["telop"]) > 14:
            raise ValueError(f"シーン{scene['id']}のテロップに改行がありません。")
