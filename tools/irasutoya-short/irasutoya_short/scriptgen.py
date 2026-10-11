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
    """箇条書きとオチから 14 シーンの台本を作る。format=caption は吹き出し型。"""
    if str(brief.get("format") or "").strip() == "caption":
        return generate_caption_script(brief)
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
    telop_width: int = 12,
    max_lines: int = 2,
    bubble: dict | None = None,
) -> dict:
    voice = VOICES[speaker]
    style = voice["style_id"]
    if emotion == "angry" and "angry_style_id" in voice:
        style = voice["angry_style_id"]
    scene = {
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
    if bubble is not None:
        scene["bubble"] = {"kind": bubble["kind"], "side": bubble["side"]}
    return scene


def generate_caption_script(brief: dict) -> dict:
    """横長の独白枠と、しっぽ付き吹き出し。ナレーションと会話で声を分ける。"""
    punchline = str(brief.get("punchline") or "").strip()
    if not punchline:
        raise ValueError("オチ（punchline）が空です。締めがフワッとするので必須です。")
    bullets = [str(b).strip() for b in brief.get("bullets") or [] if str(b).strip()]
    if len(bullets) < 3:
        raise ValueError("吹き出し型は箇条書き（bullets）が3本以上要ります。")
    hook = str(brief.get("hook") or brief.get("title") or "").strip()
    if not hook:
        raise ValueError("フック（hook）が空です。")
    closing = str(brief.get("closing") or "あなたならどうする？").strip()
    narration_bits, speech_lines = _split_quotes(bullets)
    _, punch_quotes = _split_quotes([punchline])
    punch_plain = re.sub(r"「[^」]*」", "", punchline)
    punch_plain = re.sub(r"[、。]{2,}", "、", punch_plain).strip(" 、。")
    punch_bits = _sentences(punch_plain) if punch_plain else []
    if not speech_lines and not punch_quotes:
        raise ValueError("吹き出し型は会話の「」が1つ以上要ります。ナレーションと声を分けます。")
    if not punch_bits and not punch_quotes:
        raise ValueError("オチの文言が空です。")

    beats: list[tuple] = [
        ("hook", "narration", hook, "office", ["hero_trouble"], "none", []),
    ]
    if narration_bits:
        beats.append(("develop", "narration", narration_bits[0], "office", ["hero_trouble"], "paper", ["papers"]))
    if speech_lines:
        beats.append(("develop", "speech", speech_lines[0], "office", ["hero_tired"], "none", []))
    for index, bit in enumerate(narration_bits[1:3]):
        if index == 0:
            beats.append(("develop", "narration", bit, "office", ["rival_smug"], "none", []))
        else:
            beats.append(("develop", "narration", bit, "lines", ["hero_trouble"], "none", []))
    if punch_bits:
        beats.append(("punch", "narration", punch_bits[0], "office", ["hero_tired"], "none", []))
    for line in punch_quotes[:2]:
        beats.append(("punch", "speech", line, "office", ["hero_tired"], "none", []))
    for bit in punch_bits[1:2]:
        beats.append(("punch", "narration", bit, "office", ["hero_tired"], "none", []))
    beats.append(("close", "narration", closing, "lines", ["hero_trouble"], "none", []))

    scenes: list[dict] = []
    for index, (role, mode, text, bg, chars, sfx, props) in enumerate(beats):
        side = "right" if index % 2 == 0 else "left"
        if mode == "speech":
            scenes.append(
                _scene(
                    index + 1, role, "hero", text, bg, chars, "kenburns", sfx, 2.4,
                    code_props=props, bubble={"kind": "speech", "side": side},
                    telop_width=12, max_lines=3,
                )
            )
        else:
            scenes.append(
                _scene(
                    index + 1, role, "narrator", text, bg, chars, "kenburns", sfx, 3.0,
                    code_props=props, bubble={"kind": "caption", "side": side},
                    telop_width=10, max_lines=4,
                )
            )
    used = _credits_used(scenes)
    scenes.append(_caption_credit(len(scenes) + 1, used))
    _validate_caption(scenes, punch_bits[0] if punch_bits else punch_quotes[0], closing)
    return {
        "title": hook,
        "format": "caption",
        "punchline": punchline,
        "closing": closing,
        "scenes": scenes,
        "credits": used,
        "asset_ids": _asset_ids(scenes),
    }


def _split_quotes(chunks: list[str]) -> tuple[list[str], list[str]]:
    narration: list[str] = []
    speech: list[str] = []
    for chunk in chunks:
        speech.extend(q.strip() for q in re.findall(r"「([^」]+)」", chunk) if q.strip())
        rest = re.sub(r"「[^」]*」", "", chunk)
        rest = re.sub(r"[、。]{2,}", "、", rest).strip(" 、。")
        if rest:
            narration.append(rest)
    return narration, speech


def _caption_credit(sid: int, credits: list[str]) -> dict:
    voice = VOICES["narrator"]
    return {
        "id": sid,
        "role": "credit",
        "speaker": "narrator",
        "style_id": voice["style_id"],
        "credit": voice["credit"],
        "text": "",
        "telop": "\n".join(credits),
        "bg": "credit",
        "characters": [],
        "props": [],
        "code_props": [],
        "effect": "none",
        "sfx": "none",
        "duration_hint": 2.0,
    }


def _credits_used(scenes: list[dict]) -> list[str]:
    found: list[str] = []
    for scene in scenes:
        credit = scene.get("credit") or ""
        if credit and credit not in found and scene["role"] != "credit":
            found.append(credit)
    return found


def _validate_caption(scenes: list[dict], punch_token_src: str, closing: str) -> None:
    if not (8 <= len(scenes) <= 12):
        raise ValueError(f"吹き出し型のシーン数は8〜12です。今は{len(scenes)}です。箇条書きの本数を揃えてください。")
    roles = [s["role"] for s in scenes]
    if roles.index("hook") > roles.index("punch") or roles.index("punch") > roles.index("close"):
        raise ValueError("並びはフック→展開→オチ→締めです。")
    kinds = [s.get("bubble", {}).get("kind") for s in scenes if s["role"] != "credit"]
    if "caption" not in kinds or "speech" not in kinds:
        raise ValueError("地の文の枠と、会話の吹き出しが両方要ります。")
    punch_text = " ".join(s["text"] + s["telop"] for s in scenes if s["role"] == "punch")
    token = punch_token_src[:8]
    if token and token not in punch_text:
        raise ValueError("オチの文言がオチシーンに入っていません。")
    close_text = " ".join(s["text"] + s["telop"] for s in scenes if s["role"] == "close")
    if closing[:6] not in close_text:
        raise ValueError("締めの一言が入っていません。")
    if len(_asset_ids(scenes)) > 20:
        raise ValueError("いらすとや素材が20点を超えます。背景はコードで描いてください。")


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
