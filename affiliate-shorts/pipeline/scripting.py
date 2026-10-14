"""台本JSONの形を確かめ、テーマから同じ形の台本を出す。"""

from __future__ import annotations

import json
import re
from pathlib import Path

SPEAKERS = ("narrator", "hero", "rival", "boss")
ROLES = ("hook", "develop", "punch", "credit")
EFFECTS = ("none", "zoom", "shake")
SFX = ("none", "paper", "whoosh", "shock", "notify", "coin", "tick", "rise")
CHANNEL = "会社員の金メモ"

PIPELINE_DIR = Path(__file__).resolve().parent
SHORTS_DIR = PIPELINE_DIR.parent
INDEX_PATH = PIPELINE_DIR / "assets" / "index.json"

CTA_TOKENS = ("http://", "https://", "プロフィール", "概要欄", "チャンネル登録", "リンクは", "今すぐ")
YEN_RE = re.compile(r"[0-9０-９]+\s*円")


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


def script_from_theme(theme: str, slug: str) -> dict:
    """LLM の代わりの型。オチの一文にテーマを入れる。試作は手書きJSONを使う。"""
    punch = " ".join(theme.strip().split())
    if not punch:
        raise ValueError("テーマが空です。")
    title = punch if punch.endswith("話") else f"{punch}の話"
    return {
        "id": slug,
        "channel": CHANNEL,
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


def validate_script(data: dict, index: dict[str, dict], titles: set[str]) -> None:
    _require(data, "id")
    if _require(data, "channel") != CHANNEL:
        raise ValueError(f"チャンネルは {CHANNEL} です。")
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


def voice_for(speaker: str, emotion: str) -> tuple[int, str]:
    if speaker == "narrator":
        return 2, "VOICEVOX:四国めたん"
    if speaker == "hero":
        if emotion == "angry":
            return 34, "VOICEVOX:白上虎太郎"
        return 12, "VOICEVOX:白上虎太郎"
    if speaker == "rival":
        return 11, "VOICEVOX:玄野武宏"
    if speaker == "boss":
        return 21, "VOICEVOX:剣崎雌雄"
    raise ValueError(f"未知の話者です: {speaker}")


def resolve(data: dict, index: dict[str, dict]) -> dict:
    """声と素材URLを足し、クレジットの行を後ろに付ける。"""
    lines = []
    credits: list[str] = []
    for source in data["lines"]:
        line = dict(source)
        asset = index[line["character"]] if line.get("character") else _asset_for(line, index, 0)
        line["character"] = asset["id"]
        line["who"] = asset["who"]
        line["source_url"] = asset["source_url"]
        line["effect"] = line.get("effect") or "none"
        line["sfx"] = line.get("sfx") or "none"
        line["label"] = ""
        line["tag"] = ""
        style_id, credit = voice_for(str(line["speaker"]), str(line["emotion"]))
        line["style_id"] = style_id
        line["credit"] = credit
        if credit not in credits:
            credits.append(credit)
        lines.append(line)
    assign_roles(lines)
    credit_text = "\n".join(credits)
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
            "style_id": 2,
            "credit": credits[0],
            "source_url": "",
        }
    )
    resolved = dict(data)
    resolved["mouth_overlay"] = bool(data.get("mouth_overlay", False))
    resolved["lines"] = lines
    resolved["credits"] = credits
    return resolved
