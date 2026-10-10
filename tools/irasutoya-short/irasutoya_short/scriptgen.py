"""実測した短い回の秒数（フック→状況→一文→対立→オチ）で台本を作る。"""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request

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


# Grokbot の1本は10秒。care の 10.03 / 9.53 / 8.63 をこの枠に載せたもの。新しい秒は作らない。
H3_SECONDS = (10, 10, 10)
MODEL = "grok-4.7"
API_URL = "https://api.x.ai/v1/chat/completions"
MOUTH = "口は閉じたまま、話していない。"
_DRAFT_KEYS = (
    "series_character",
    "hook",
    "rival_line",
    "situation",
    "card",
    "counter",
    "punchline",
    "worry",
    "action",
    "result",
    "worry_picture",
    "action_picture",
    "result_picture",
)
_BANNED = (
    "http://",
    "https://",
    "#pr",
    "あなたなら",
    "詳しくは",
    "プロフィールのリンク",
    "概要欄",
    "junjun",
    "yako.shiawasekon",
    "nuts0629",
    "the.care.logic",
    "私に手足をくれる人が見つかったの",
    "手術は、無事に成功した",
    "おい、そこのデブ",
)
DRAFT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {key: {"type": "string"} for key in _DRAFT_KEYS},
    "required": list(_DRAFT_KEYS),
}
_SYSTEM = (
    "種から日本語の短い台本の欄だけを返す。"
    "秒、再生数、ショット数は書かない。"
    "参考アカウントの名前、元動画のせりふ、URL、#PR、概要欄、プロフィール誘導、"
    "「あなたならどうする」は書かない。医療の効能は書かない。"
    "rival_line は相手の一言。situation は状況。card は黒地の一文。"
    "counter は主人公の対抗。punchline はオチで、解説で締めない。"
    "worry と action と result はそれぞれ2文まで。"
    "絵の欄にせりふの鍵括弧は入れない。人物は架空の役割名だけ。"
)


def check_draft(draft: dict) -> None:
    """モデルの欄を、実測の型に合うか見る。秒はここには無い。"""
    if not isinstance(draft, dict):
        raise ValueError("台本の欄が揃っていません。")
    missing = [key for key in _DRAFT_KEYS if not str(draft.get(key) or "").strip()]
    if missing:
        raise ValueError("空の欄があります。" + "、".join(missing))
    blob = "\n".join(str(draft[key]) for key in _DRAFT_KEYS)
    lowered = blob.lower()
    for banned in _BANNED:
        if banned.lower() in lowered:
            raise ValueError("参考の文、誘導、URLは台本に入れません。")
    for key in ("rival_line", "card"):
        if re.search(r"[。！？]", str(draft[key])):
            raise ValueError(f"{key}は1文にします。")
    for key in ("worry_picture", "action_picture", "result_picture"):
        if "「" in str(draft[key]) or "」" in str(draft[key]):
            raise ValueError("絵の欄にせりふは入れません。")
    for key in ("worry", "action", "result"):
        count = len(_sentences(str(draft[key])))
        if count < 1 or count > 2:
            raise ValueError(f"{key}は2文までです。今は{count}文です。")


def brief_from_draft(draft: dict) -> dict:
    """既存の generate_script が読む箇条書きにする。最初の「」がフック。"""
    check_draft(draft)
    situation = str(draft["situation"]).strip()
    rival = str(draft["rival_line"]).strip()
    return {
        "hook": str(draft["hook"]).strip(),
        "series_character": str(draft["series_character"]).strip(),
        "bullets": [
            f"{situation}「{rival}」",
            str(draft["card"]).strip(),
            str(draft["counter"]).strip(),
        ],
        "punchline": str(draft["punchline"]).strip(),
        "closing": "",
    }


def _picture(text: str) -> str:
    body = str(text).strip().rstrip("。")
    return f"{body}。{MOUTH}正面、上半身。"


def h3_from_draft(draft: dict) -> dict:
    """3シーン×10秒。テロップは空。口は閉じたまま。動画は作らない。"""
    check_draft(draft)
    narrations = [str(draft[key]).strip() for key in ("worry", "action", "result")]
    pictures = [str(draft[key]).strip() for key in ("worry_picture", "action_picture", "result_picture")]
    scenes = []
    source = []
    for index, (narration, picture) in enumerate(zip(narrations, pictures), start=1):
        name = f"scene_0{index}.mp4"
        scenes.append({"video": name, "narration": narration, "telop_text": ""})
        source.append(
            {
                "video": name,
                "duration": H3_SECONDS[index - 1],
                "image_prompt": _picture(picture),
                "motion_prompt": "口を閉じたまま、話さない。カメラは固定。",
            }
        )
    return {
        "project_id": "script-auto",
        "genre": "スカッと",
        "title": str(draft["hook"]).strip(),
        "description": "\n".join(narrations) + "\n",
        "tags": [],
        "bgm": "",
        "telop": False,
        "final_filename": "script-auto.mp4",
        "character": "人物は全シーンで同じ。口は閉じたまま。",
        "note": "H3は10秒が3つ。テロップは空。アフィURLは無し。このJSONでは動画を作らない。",
        "source_scenes": source,
        "scenes": scenes,
    }


def auto_scripts(seed: str, complete) -> dict:
    """種から、いらすとや台本とH3台本を返す。complete が欄を埋める。"""
    if not str(seed).strip():
        raise ValueError("種が空です。")
    draft = complete(str(seed).strip())
    brief = brief_from_draft(draft)
    return {"irasutoya": generate_script(brief), "h3": h3_from_draft(draft)}


def _draft_from_response(payload: dict) -> dict:
    try:
        content = payload["choices"][0]["message"]["content"]
        draft = json.loads(content)
    except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
        raise ValueError("台本のJSONを読めませんでした。") from exc
    if not isinstance(draft, dict):
        raise ValueError("台本のJSONがオブジェクトではありません。")
    return draft


def _post_json(body: dict, api_key: str) -> dict:
    data = json.dumps(body).encode("utf-8")
    request = urllib.request.Request(
        API_URL,
        data=data,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:300].replace(api_key, "")
        raise ValueError(f"台本の生成が失敗しました。HTTP {exc.code}。{detail}") from None


def grok_complete(seed: str, *, api_key: str | None = None, post=None) -> dict:
    """XAI_API_KEY で欄を埋める。キーの値は表示しない。"""
    key = api_key if api_key is not None else os.environ.get("XAI_API_KEY", "")
    if not str(key).strip():
        raise ValueError("XAI_API_KEY がありません。")
    body = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": _SYSTEM},
            {"role": "user", "content": seed},
        ],
        "response_format": {
            "type": "json_schema",
            "json_schema": {"name": "script_draft", "strict": True, "schema": DRAFT_SCHEMA},
        },
    }
    payload = post(body, key) if post is not None else _post_json(body, key)
    return _draft_from_response(payload)
