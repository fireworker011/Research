"""箇条書きを、選んだ編集テンプレのシーン列にする。"""

from __future__ import annotations

import re

from irasutoya_short.catalog import ASSET_CATALOG, VOICES
from irasutoya_short.constants import BLOCKED_STYLE_IDS, MAX_SCENES, MIN_SCENES
from irasutoya_short.templates import TEMPLATES, require_template
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


def _context(brief: dict) -> dict:
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
    blob = bullets + [punchline]
    lines = {
        str(key): str(value).strip()
        for key, value in (brief.get("lines") or {}).items()
        if str(value).strip()
    }
    return {
        "series": series,
        "hook": hook,
        "closing": closing,
        "bullets": bullets,
        "punchline": punchline,
        "punch_action": punch_parts[0],
        "punch_result": punch_parts[-1] if len(punch_parts) > 1 else punchline,
        "rival_line": _quote(blob, 0, "お前の方が早いだろ"),
        "panic_line": _quote(blob, 1, "今送るから"),
        "lines": lines,
        "item_voice": str(brief.get("item_voice") or "").strip(),
    }


def generate_script(brief: dict) -> dict:
    """箇条書きとオチから 12〜14 シーンの台本を作る。"""
    name = str(brief.get("template") or "sukatto").strip()
    require_template(name)
    ctx = _context(brief)
    scenes = _build(name, ctx)
    credits = _credits(scenes)
    scenes.append(_credit_scene(credits, ctx["series"]))
    for index, scene in enumerate(scenes, start=1):
        scene["id"] = index
    _validate(scenes, ctx["punchline"], ctx["closing"])
    return {
        "template": name,
        "title": ctx["hook"],
        "series_character": ctx["series"],
        "punchline": ctx["punchline"],
        "closing": ctx["closing"],
        "scenes": scenes,
        "credits": credits,
        "asset_ids": _asset_ids(scenes),
    }


def _build(name: str, ctx: dict) -> list[dict]:
    if name == "sukatto":
        return _sukatto(ctx)
    if name == "before_after":
        return _before_after(ctx)
    if name == "aruaru":
        return _aruaru(ctx)
    if name == "ranking":
        return _ranking(ctx)
    if name == "qa":
        return _qa(ctx)
    known = "、".join(TEMPLATES)
    raise ValueError(f"未知のテンプレです: {name}。使えるのは {known} です。")


def _line(ctx: dict, key: str, default: str) -> str:
    return ctx["lines"].get(key) or default


def _sukatto(ctx: dict) -> list[dict]:
    series = ctx["series"]
    bullets = ctx["bullets"]
    return [
        _scene(1, "hook", "narrator", ctx["hook"], "office", ["rival_smug", "hero_trouble"], "zoom", "none", label=series),
        _scene(2, "develop", "narrator", _bullet(bullets, 0, "金曜の17時、机に書類が置かれた"), "office", ["hero_trouble"], "none", "paper", code_props=["papers"]),
        _scene(3, "develop", "rival", ctx["rival_line"], "office", ["rival_smug"], "none", "none", label=series),
        _scene(4, "develop", "narrator", _bullet(bullets, 1, "そう言い残して定時で帰っていった"), "office", ["rival_smug"], "none", "whoosh", label=series),
        _scene(5, "develop", "hero", _line(ctx, "hero_refuse", "俺の仕事じゃねえだろ"), "office", ["hero_angry"], "shake", "none", emotion="angry"),
        _scene(6, "develop", "narrator", _bullet(bullets, 2, "誰もいない夜、終電まで残った"), "office_night", ["hero_tired"], "none", "none"),
        _scene(7, "develop", "narrator", _bullet(bullets, 3, "月曜の朝、何事もなかった顔だった"), "office", ["rival_smug"], "none", "none", label=series),
        _scene(8, "develop", "hero", _line(ctx, "hero_aside", "まだ気づいてないのか"), "office", ["hero_angry"], "lines", "none", emotion="angry"),
        _scene(9, "punch", "narrator", ctx["punch_action"], "chat", ["hero_smile"], "zoom", "notify"),
        _scene(10, "punch", "boss", _line(ctx, "boss_line", "どういうことだ"), "office", ["boss_angry"], "shake", "shock"),
        _scene(11, "punch", "rival", ctx["panic_line"], "office", ["rival_smug"], "none", "none", label=series),
        _scene(12, "punch", "narrator", ctx["punch_result"], "office", ["hero_smile"], "zoom", "coin", label=series),
        _scene(13, "close", "narrator", ctx["closing"], "lines", ["hero_smile"], "zoom", "none"),
    ]


def _before_after(ctx: dict) -> list[dict]:
    series = ctx["series"]
    bullets = ctx["bullets"]
    return [
        _scene(1, "hook", "narrator", ctx["hook"], "office", ["hero_trouble", "hero_smile"], "zoom", "whoosh", label=series, tone="after"),
        _scene(2, "develop", "narrator", "ビフォー、" + _bullet(bullets, 0, "机に書類が置かれた"), "office", ["hero_trouble"], "none", "paper", code_props=["papers"], tone="before"),
        _scene(3, "develop", "rival", ctx["rival_line"], "office", ["rival_smug"], "none", "none", label=series, tone="before"),
        _scene(4, "develop", "narrator", _bullet(bullets, 1, "定時で帰っていった"), "office", ["rival_smug"], "none", "whoosh", label=series, tone="before"),
        _scene(5, "develop", "hero", _line(ctx, "hero_refuse", "俺の仕事じゃねえだろ"), "office", ["hero_angry"], "shake", "none", emotion="angry", tone="before"),
        _scene(6, "develop", "narrator", _bullet(bullets, 2, "終電まで残った"), "office_night", ["hero_tired"], "none", "none", tone="before"),
        _scene(7, "develop", "narrator", _line(ctx, "turn_line", "ここから、アフター"), "office", ["hero_smile"], "lines", "rise", tone="turn", hold=1.6),
        _scene(8, "punch", "narrator", ctx["punch_action"], "chat", ["hero_smile"], "zoom", "coin", tone="after"),
        _scene(9, "punch", "boss", _line(ctx, "boss_line", "どういうことだ"), "office", ["boss_angry"], "shake", "shock", tone="after"),
        _scene(10, "punch", "rival", ctx["panic_line"], "office", ["rival_smug"], "none", "none", label=series, tone="after"),
        _scene(11, "punch", "narrator", ctx["punch_result"], "office", ["hero_smile"], "zoom", "coin", label=series, tone="after"),
        _scene(12, "close", "narrator", ctx["closing"], "lines", ["hero_smile"], "zoom", "none", tone="close"),
        _scene(13, "close", "narrator", _line(ctx, "after_gap", "ビフォーとアフターは、この差"), "lines", ["hero_trouble", "hero_smile"], "none", "none", tone="after"),
    ]


def _aruaru(ctx: dict) -> list[dict]:
    series = ctx["series"]
    items = _list_items(ctx)
    casts = ("hero_trouble", "rival_smug", "hero_tired", "hero_angry", "hero_trouble", "rival_smug")
    scenes = [
        _scene(1, "hook", "narrator", ctx["hook"], "office", ["hero_trouble", "rival_smug"], "zoom", "notify", label=series, tone="hook"),
    ]
    use_list = ctx.get("item_voice") == "list"
    for index, (item, cast) in enumerate(zip(items, casts), start=1):
        if use_list:
            who = "narrator"
            text = item
            emotion = ""
        elif cast.startswith("rival"):
            who = "rival"
            text = ctx["rival_line"]
            emotion = ""
        else:
            who = "hero"
            text = f"その{index}、{item}"
            emotion = "angry" if cast == "hero_angry" else ""
        scenes.append(
            _scene(
                index + 1, "develop", who, text, "office", [cast], "none", "tick",
                label=series if who == "rival" else "", tone="item",
                emotion=emotion,
            )
        )
    scenes.extend(
        [
            _scene(8, "develop", "narrator", _line(ctx, "more_line", "まだある。一番はここからだ"), "office", ["hero_smile"], "lines", "rise", tone="item"),
            _scene(9, "punch", "narrator", ctx["punch_action"], "chat", ["hero_smile"], "zoom", "rise", tone="punch"),
            _scene(10, "punch", "boss", _line(ctx, "boss_line", "どういうことだ"), "office", ["boss_angry"], "shake", "shock", tone="punch"),
            _scene(11, "punch", "narrator", ctx["punch_result"], "office", ["hero_smile"], "zoom", "coin", label=series, tone="punch"),
            _scene(12, "close", "narrator", ctx["closing"], "lines", ["hero_smile"], "zoom", "none", tone="close"),
            _scene(13, "close", "narrator", _line(ctx, "count_line", "何個、当てはまった？"), "lines", ["hero_smile"], "none", "tick", tone="close"),
        ]
    )
    return scenes


def _ranking(ctx: dict) -> list[dict]:
    series = ctx["series"]
    bullets = ctx["bullets"]
    third = _bullet(bullets, 0, "机に書類が置かれた")
    second = _bullet(bullets, 1, "定時で帰っていった")
    second_detail = _bullet(bullets, 2, "終電まで残った")
    return [
        _scene(1, "hook", "narrator", ctx["hook"], "office", ["rival_smug", "hero_trouble"], "zoom", "rise", label=series, tone="rank"),
        _scene(2, "develop", "narrator", f"第3位、{third}", "office", ["rival_smug"], "zoom", "rise", label=series, tone="rank"),
        _scene(3, "develop", "rival", ctx["rival_line"], "office", ["rival_smug"], "none", "tick", label=series, tone="rank"),
        _scene(4, "develop", "hero", _line(ctx, "rank_aside", "まだ序の口だ"), "office", ["hero_angry"], "none", "none", emotion="angry", tone="rank"),
        _scene(5, "develop", "narrator", f"第2位、{second}", "office", ["hero_tired"], "zoom", "rise", tone="rank"),
        _scene(6, "develop", "narrator", second_detail, "office_night", ["hero_tired"], "none", "tick", tone="rank"),
        _scene(7, "develop", "narrator", _bullet(bullets, 3, "何事もなかった顔だった"), "office", ["rival_smug"], "none", "none", label=series, tone="rank"),
        _scene(8, "punch", "narrator", f"第1位、{ctx['punch_action']}", "chat", ["hero_smile"], "zoom", "shock", tone="rank", hold=1.8),
        _scene(9, "punch", "boss", _line(ctx, "boss_line", "どういうことだ"), "office", ["boss_angry"], "shake", "shock", tone="punch"),
        _scene(10, "punch", "rival", ctx["panic_line"], "office", ["rival_smug"], "none", "none", label=series, tone="punch"),
        _scene(11, "punch", "narrator", ctx["punch_result"], "office", ["hero_smile"], "zoom", "coin", label=series, tone="punch"),
        _scene(12, "close", "narrator", ctx["closing"], "lines", ["hero_smile"], "zoom", "none", tone="close"),
        _scene(13, "close", "narrator", _line(ctx, "rank_close", "1位だけ、覚えとくといい"), "lines", ["hero_smile"], "none", "rise", tone="close"),
    ]


def _qa(ctx: dict) -> list[dict]:
    series = ctx["series"]
    bullets = ctx["bullets"]
    question = _question(ctx)
    return [
        _scene(1, "hook", "narrator", question, "office", ["hero_trouble"], "zoom", "notify", tone="question", hold=1.6),
        _scene(2, "develop", "narrator", "よくある答え、" + _bullet(bullets, 0, "書類が置かれた"), "office", ["hero_trouble"], "none", "tick", code_props=["papers"], tone="guess"),
        _scene(3, "develop", "rival", ctx["rival_line"], "office", ["rival_smug"], "none", "none", label=series, tone="guess"),
        _scene(4, "develop", "narrator", _bullet(bullets, 1, "定時で帰っていった"), "office", ["rival_smug"], "none", "tick", label=series, tone="guess"),
        _scene(5, "develop", "narrator", _bullet(bullets, 2, "終電まで残った"), "office_night", ["hero_tired"], "none", "tick", tone="guess"),
        _scene(6, "develop", "hero", _line(ctx, "not_answer", "それは、答えじゃない"), "office", ["hero_angry"], "lines", "none", emotion="angry", tone="guess"),
        _scene(7, "develop", "narrator", _bullet(bullets, 3, "何事もなかった顔だった"), "office", ["hero_trouble"], "none", "tick", label=series, tone="guess"),
        _scene(8, "punch", "narrator", "答えは、" + ctx["punch_action"], "chat", ["hero_smile"], "zoom", "shock", tone="answer"),
        _scene(9, "punch", "boss", _line(ctx, "boss_line", "どういうことだ"), "office", ["boss_angry"], "shake", "shock", tone="answer"),
        _scene(10, "punch", "rival", ctx["panic_line"], "office", ["rival_smug"], "none", "none", label=series, tone="answer"),
        _scene(11, "punch", "narrator", ctx["punch_result"], "office", ["hero_smile"], "zoom", "coin", label=series, tone="answer"),
        _scene(12, "close", "narrator", ctx["closing"], "lines", ["hero_smile"], "zoom", "notify", tone="question"),
        _scene(13, "close", "narrator", _line(ctx, "answer_landed", "答えは、もう出てる"), "lines", ["hero_smile"], "none", "none", tone="answer"),
    ]


def _list_items(ctx: dict) -> list[str]:
    items: list[str] = []
    for index in range(len(ctx["bullets"])):
        item = _bullet(ctx["bullets"], index, "")
        if item:
            items.append(item)
    if ctx["rival_line"] and ctx["rival_line"] not in items:
        items.append(ctx["rival_line"])
    if not items:
        items.append(ctx["hook"])
    seed = list(items)
    cursor = 0
    while len(items) < 6:
        items.append(seed[cursor % len(seed)])
        cursor += 1
    return items[:6]


def _question(ctx: dict) -> str:
    if "？" in ctx["closing"] or "?" in ctx["closing"]:
        return ctx["closing"]
    if "？" in ctx["hook"] or "?" in ctx["hook"]:
        return ctx["hook"]
    return ctx["closing"]


def _scene(
    sid: int,
    role: str,
    speaker: str,
    text: str,
    bg: str,
    characters: list[str],
    effect: str,
    sfx: str,
    props: list[str] | None = None,
    code_props: list[str] | None = None,
    label: str = "",
    emotion: str = "",
    tone: str = "",
    hold: float | None = None,
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
        "telop": wrap_telop(text, 12, 2),
        "bg": bg,
        "characters": [
            {"id": cid, "who": ASSET_CATALOG[cid]["who"], "label": label if ASSET_CATALOG[cid]["who"] == "rival" else ""}
            for cid in characters
        ],
        "props": props or [],
        "code_props": code_props or [],
        "effect": effect,
        "sfx": sfx,
        "duration_hint": 2.2,
    }
    if tone:
        scene["tone"] = tone
    if hold is not None:
        scene["hold"] = hold
    return scene


def _credit_scene(credits: list[str], series: str) -> dict:
    return {
        "id": 0,
        "role": "credit",
        "speaker": "narrator",
        "style_id": VOICES["narrator"]["style_id"],
        "credit": VOICES["narrator"]["credit"],
        "text": "",
        "telop": "\n".join(credits),
        "bg": "credit",
        "characters": [],
        "props": [],
        "code_props": [],
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
    if not found:
        found.append(VOICES["narrator"]["credit"])
    return found


def _validate(scenes: list[dict], punchline: str, closing: str) -> None:
    if not (MIN_SCENES <= len(scenes) <= MAX_SCENES):
        raise ValueError(f"シーン数は{MIN_SCENES}〜{MAX_SCENES}です。今は{len(scenes)}です。")
    roles = [s["role"] for s in scenes]
    if "hook" not in roles or "punch" not in roles or "close" not in roles:
        raise ValueError("フック、オチ、締めが揃っていません。")
    if roles.index("hook") > roles.index("punch") or roles.index("punch") > roles.index("close"):
        raise ValueError("並びはフックが先、オチ、締めの順です。")
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
        if scene["style_id"] in BLOCKED_STYLE_IDS:
            raise ValueError(f"シーン{scene['id']}は使えない声です。")
