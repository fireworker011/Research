"""台本JSONの形を確かめ、テーマから同じ形の台本を出す。"""

from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import urlparse

from channels import voice_for
from qa_gate import collaboration_hits

SPEAKERS = ("narrator", "hero", "rival", "boss")
ROLES = ("hook", "develop", "punch", "credit")
EFFECTS = ("none", "zoom", "shake")
SFX = ("none", "paper", "whoosh", "shock", "notify", "coin", "tick", "rise")

PIPELINE_DIR = Path(__file__).resolve().parent
SHORTS_DIR = PIPELINE_DIR.parent
INDEX_PATH = PIPELINE_DIR / "assets" / "index.json"

CTA_TOKENS = ("http://", "https://", "プロフィール", "概要欄", "チャンネル登録", "リンクは", "今すぐ")
YEN_RE = re.compile(r"[0-9０-９]+\s*円")
SOURCE_HOSTS = ("www.kantei.go.jp", "www.bousai.go.jp")
_AMOUNT = re.compile(r"([0-9０-９]+|[一二三四五六七八九十]+)\s*(リットル|日分|週間)")
_KANJI_DIGIT = {"一": "1", "二": "2", "三": "3", "四": "4", "五": "5", "六": "6", "七": "7", "八": "8", "九": "9", "十": "10"}


def load_index(path: Path | None = None) -> dict[str, dict]:
    data = json.loads((path or INDEX_PATH).read_text(encoding="utf-8"))
    assets = {}
    for item in data["assets"]:
        if item["kind"] != "person":
            raise ValueError(f"索引は人物だけにする: {item['id']}")
        assets[item["id"]] = item
    if not assets:
        raise ValueError("素材索引が空です。")
    return assets


def existing_titles(root: Path | None = None) -> set[str]:
    """batch1 から batch5 までの投稿用タイトル。レビュー出力は含めない。"""
    base = root or SHORTS_DIR
    titles: set[str] = set()
    for path in base.rglob("UPLOAD.md"):
        if "pipeline" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        marker = "## タイトル"
        if marker not in text:
            continue
        rest = text.split(marker, 1)[1]
        for line in rest.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith("#"):
                break
            titles.add(stripped)
            break
    return titles


def script_from_theme(theme: str, slug: str, channel_id: str) -> dict:
    """LLM の代わりの型。オチの一文にテーマを入れる。試作は手書きJSONを使う。"""
    punch = " ".join(theme.strip().split())
    if not punch:
        raise ValueError("テーマが空です。")
    title = punch if punch.endswith("話") else f"{punch}の話"
    return {
        "id": slug,
        "channel": channel_id,
        "title": title,
        "theme": punch,
        "hook": "ファイルに入れとけ。後でな",
        "mouth_overlay": False,
        "generator": "template",
        "lines": [
            {
                "speaker": "rival",
                "character": "rival_smug",
                "emotion": "smug",
                "text": "ファイルに入れとけ。後でな",
                "caption": "ファイルに入れとけ。\n後でな",
                "role": "hook",
                "effect": "zoom",
                "sfx": "none",
            },
            {
                "speaker": "narrator",
                "character": "hero_trouble",
                "emotion": "trouble",
                "text": punch,
                "caption": punch,
                "role": "punch",
                "effect": "zoom",
                "sfx": "coin",
            },
        ],
    }


def load_script(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("台本はオブジェクトです。")
    data["generator"] = "json"
    return data


def _require(data: dict, key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"台本の {key} が空です。")
    return value.strip()


def _line_caption(line: dict) -> str:
    caption = line.get("caption")
    if not isinstance(caption, str) or not caption.strip():
        raise ValueError("各行に caption が要ります。")
    return caption.strip()


def validate_script(data: dict, index: dict[str, dict], titles: set[str], channel: dict) -> None:
    _require(data, "id")
    if _require(data, "channel") != channel["id"]:
        raise ValueError(f"台本の channel は設定 id {channel['id']} と揃えます。")
    title = _require(data, "title")
    if title in titles:
        raise ValueError(f"このタイトルは batch1-5 で使われています: {title}")
    _require(data, "theme")
    hook = _require(data, "hook")
    if not isinstance(data.get("mouth_overlay", False), bool):
        raise ValueError("mouth_overlay は true か false です。")
    lines = data.get("lines")
    if not isinstance(lines, list) or not lines:
        raise ValueError("lines が空です。")
    if lines[0].get("text", "").strip() != hook:
        raise ValueError("hook は最初の行の text と揃えます。")
    for index_no, line in enumerate(lines, start=1):
        _check_line(line, index_no, index)
    roles = [str(line.get("role") or "") for line in lines]
    if "hook" not in roles or "punch" not in roles:
        raise ValueError("hook と punch の行が要ります。")
    blob = " ".join(_line_caption(line) + str(line.get("text") or "") for line in lines)
    for token in CTA_TOKENS:
        if token in blob:
            raise ValueError(f"CTA は入れません: {token}")
    if YEN_RE.search(blob):
        raise ValueError("金額は入れません。")
    if "#" in blob:
        raise ValueError("タグは入れません。")
    branding = {
        "name": str(channel.get("name") or ""),
        "genre": str(channel.get("genre") or ""),
        "title": title,
        "theme": str(data.get("theme") or ""),
        "tags": list(channel.get("tags") or []),
        "texts": [hook, blob],
    }
    hits = collaboration_hits(branding)
    if hits:
        raise ValueError("いらすとやとの協力を示す書き方があります: " + "、".join(hits))
    thumb = data.get("thumbnail")
    if thumb is not None:
        if not isinstance(thumb, dict) or thumb.get("character") not in index:
            raise ValueError("thumbnail.character は索引にある id です。")
    _validate_sources(data, channel, blob)


def _check_line(line: dict, index_no: int, index: dict[str, dict]) -> None:
    if not isinstance(line, dict):
        raise ValueError(f"{index_no} 行目がオブジェクトではありません。")
    speaker = line.get("speaker")
    if speaker not in SPEAKERS:
        raise ValueError(f"{index_no} 行目の speaker が未知です: {speaker}")
    text = line.get("text")
    if not isinstance(text, str) or not text.strip():
        raise ValueError(f"{index_no} 行目の text が空です。")
    _line_caption(line)
    if line.get("label") or line.get("tag"):
        raise ValueError(f"{index_no} 行目に名札があります。")
    effect = line.get("effect", "none")
    if effect not in EFFECTS:
        raise ValueError(f"{index_no} 行目の effect が未知です: {effect}")
    sfx = line.get("sfx", "none")
    if sfx not in SFX:
        raise ValueError(f"{index_no} 行目の sfx が未知です: {sfx}")
    role = line.get("role")
    if role is not None and role not in ROLES:
        raise ValueError(f"{index_no} 行目の role が未知です: {role}")
    asset = _asset_for(line, index, index_no)
    if "recolor" in line and not isinstance(line.get("recolor"), bool):
        raise ValueError(f"{index_no} 行目の recolor は true か false です。")
    if line.get("emotion") != asset["emotion"]:
        raise ValueError(
            f"{index_no} 行目の emotion は {asset['id']} の {asset['emotion']} です。"
        )
    if speaker != "narrator" and asset["who"] != speaker:
        raise ValueError(f"{index_no} 行目のキャラが話者と違います。")


def _asset_for(line: dict, index: dict[str, dict], index_no: int) -> dict:
    character = line.get("character")
    if isinstance(character, str) and character:
        asset = index.get(character)
        if asset is None:
            raise ValueError(f"{index_no} 行目の character が索引にありません: {character}")
        return asset
    emotion = line.get("emotion")
    speaker = line.get("speaker")
    matches = [
        asset
        for asset in index.values()
        if asset["emotion"] == emotion and (speaker == "narrator" or asset["who"] == speaker)
    ]
    if len(matches) != 1:
        raise ValueError(f"{index_no} 行目の character を索引から一つに決められません。")
    return matches[0]


def assign_roles(lines: list[dict]) -> None:
    if any(not line.get("role") for line in lines):
        last = len(lines) - 1
        for index_no, line in enumerate(lines):
            if line.get("role"):
                continue
            if index_no == 0:
                line["role"] = "hook"
            elif index_no == last:
                line["role"] = "punch"
            else:
                line["role"] = "develop"


def resolve(data: dict, index: dict[str, dict], channel: dict) -> dict:
    """声と素材URLを足し、クレジットの行を後ろに付ける。"""
    lines = []
    credits: list[str] = []
    for source in data["lines"]:
        line = dict(source)
        asset = index[line["character"]] if line.get("character") else _asset_for(line, index, 0)
        line["character"] = asset["id"]
        line["who"] = asset["who"]
        line["source_url"] = asset["source_url"]
        line["recolor"] = bool(line.get("recolor", False))
        line["effect"] = line.get("effect") or "none"
        line["sfx"] = line.get("sfx") or "none"
        line["label"] = ""
        line["tag"] = ""
        style_id, credit = voice_for(channel, str(line["speaker"]), str(line["emotion"]))
        line["style_id"] = style_id
        line["credit"] = credit
        if credit not in credits:
            credits.append(credit)
        lines.append(line)
    assign_roles(lines)
    credit_text = "\n".join(credits)
    illustration = str(channel["credits"].get("illustration") or "").strip()
    if illustration:
        credit_text = credit_text + "\n" + illustration
    lines.append(
        {
            "speaker": "narrator",
            "character": "",
            "who": "",
            "emotion": "",
            "text": "",
            "caption": credit_text,
            "role": "credit",
            "effect": "none",
            "sfx": "none",
            "label": "",
            "tag": "",
            "style_id": int(channel["voices"]["narrator"]["style_id"]),
            "credit": credits[0],
            "source_url": "",
        }
    )
    resolved = dict(data)
    resolved["channel"] = channel["id"]
    resolved["channel_name"] = str(channel.get("name") or "")
    resolved["genre"] = str(channel.get("genre") or "")
    resolved["mouth_overlay"] = bool(data.get("mouth_overlay", False))
    resolved["caption"] = channel["caption"]
    resolved["lines"] = lines
    resolved["credits"] = credits
    resolved["tags"] = list(channel.get("tags") or [])
    resolved["name_status"] = str(channel.get("name_status") or "")
    resolved["thumbnail"] = _thumbnail(data.get("thumbnail"), index)
    return resolved


def _thumbnail(raw: object, index: dict[str, dict]) -> dict | None:
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise ValueError("thumbnail はオブジェクトです。")
    asset = index[str(raw.get("character") or "")]
    return {"id": asset["id"], "emotion": asset["emotion"], "source_url": asset["source_url"]}


def _amount_token(raw: str) -> str:
    if raw.isdigit() or all(ch in "０１２３４５６７８９" for ch in raw):
        return str(int(raw.translate(str.maketrans("０１２３４５６７８９", "0123456789"))))
    if raw in _KANJI_DIGIT:
        return _KANJI_DIGIT[raw]
    return raw


def amounts_in(text: str) -> set[str]:
    found = set()
    for number, unit in _AMOUNT.findall(text):
        found.add(_amount_token(number) + unit)
    return found


def unexpected_amounts(speech: str, claims: str) -> list[str]:
    return sorted(amounts_in(speech) - amounts_in(claims))


def amount_self_test() -> None:
    claims = "飲料水 3日分（1人1日3リットルが目安）。大規模災害発生時には「1週間分」の備蓄が望ましい。生活用水も必要。"
    speech = "一人一日三リットル。三日分が目安や。備蓄は一週間分が望ましい"
    extra = unexpected_amounts(speech, claims)
    if extra:
        raise RuntimeError(f"出典にある数量を誤って弾きました: {extra}")
    invented = unexpected_amounts("九リットルを二十一日分", claims)
    if not invented:
        raise RuntimeError("出典に無い数量を通しました。")


def _validate_sources(data: dict, channel: dict, speech: str) -> None:
    rows = data.get("sources")
    required = bool(channel.get("require_sources"))
    if rows is None:
        if required:
            raise ValueError("このチャンネルの台本には、公開ページの出典が要ります。")
        return
    if not isinstance(rows, list) or not rows:
        raise ValueError("sources は1件以上の配列です。")
    claims: list[str] = []
    for index_no, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            raise ValueError(f"出典 {index_no} がオブジェクトではありません。")
        name = row.get("name")
        url = row.get("url")
        claim = row.get("claim")
        if not isinstance(name, str) or not name.strip():
            raise ValueError(f"出典 {index_no} の name が空です。")
        if not isinstance(url, str) or not _public_source_url(url):
            raise ValueError(f"出典 {index_no} は首相官邸か内閣府の https のページです。")
        if not isinstance(claim, str) or not claim.strip():
            raise ValueError(f"出典 {index_no} の claim が空です。")
        claims.append(claim.strip())
    facts = data.get("facts_used")
    if required and (not isinstance(facts, list) or not facts):
        raise ValueError("facts_used に、出典の文から使った語句を書きます。")
    blob = "\n".join(claims)
    if isinstance(facts, list):
        for fact in facts:
            if not isinstance(fact, str) or fact not in blob:
                raise ValueError(f"出典の記述に無い語句です: {fact}")
    extra = unexpected_amounts(speech, blob)
    if extra:
        raise ValueError("出典に無い数量です: " + "、".join(extra))


def _public_source_url(url: str) -> bool:
    parsed = urlparse(url.strip())
    return parsed.scheme == "https" and parsed.netloc in SOURCE_HOSTS and not parsed.username
