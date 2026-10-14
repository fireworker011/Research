"""チャンネルの名前、ジャンル、声、字幕、クレジット、投稿文。"""

from __future__ import annotations

from pathlib import Path

import yaml

from irasutoya_short.constants import BLOCKED_STYLE_IDS
from qa_gate import COLLAB_RE

PIPELINE_DIR = Path(__file__).resolve().parent
CHANNELS_DIR = PIPELINE_DIR / "channels"
SPEAKERS = ("narrator", "hero", "rival", "boss")
CAPTION_KEYS = (
    "bar",
    "stroke",
    "credit_stroke",
    "size",
    "credit_size",
    "min_size",
    "credit_min_size",
    "y_ratio",
    "credit_y_ratio",
    "colors",
)
# 以前のチャンネル名。出力にも、新しい yaml の name にも書かない。
REMOVED_CHANNEL_NAME = "会社員の金メモ"


def channel_ids() -> list[str]:
    return sorted(path.stem for path in CHANNELS_DIR.glob("*.yaml"))


def load_channel(channel_id: str) -> dict:
    path = CHANNELS_DIR / f"{channel_id}.yaml"
    if not path.is_file():
        known = "、".join(channel_ids()) or "なし"
        raise ValueError(f"チャンネル設定がありません: {channel_id}。あるのは {known} です。")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"チャンネル設定がオブジェクトではありません: {path.name}")
    if str(data.get("id") or "") != channel_id:
        raise ValueError(f"{path.name} の id はファイル名と揃えます。")
    _require_text_field(data, "name", allow_empty=True)
    _require_text_field(data, "genre", allow_empty=True)
    _reject_removed_name(str(data.get("name") or ""), "name")
    _reject_removed_name(str(data.get("genre") or ""), "genre")
    _reject_collab(str(data.get("name") or ""), "name")
    _reject_collab(str(data.get("genre") or ""), "genre")
    data["voices"] = _voices(data.get("voices"))
    data["caption"] = _caption(data.get("caption"))
    data["credits"] = _credits(data.get("credits"))
    template = data.get("upload_template")
    if not isinstance(template, str) or not template.strip():
        raise ValueError("upload_template が空です。")
    _reject_removed_name(template, "upload_template")
    tags = data.get("tags") or []
    if not isinstance(tags, list) or any(not isinstance(tag, str) for tag in tags):
        raise ValueError("tags は文字列の配列です。")
    for tag in tags:
        _reject_removed_name(tag, "tags")
        _reject_collab(tag, "tags")
    data["tags"] = [tag.strip() for tag in tags if tag.strip()]
    status = data.get("name_status", "")
    if status not in ("", "working", "final"):
        raise ValueError("name_status は working か final か、省略です。")
    data["name_status"] = status
    if not isinstance(data.get("require_sources", False), bool):
        raise ValueError("require_sources は true か false です。")
    data["require_sources"] = bool(data.get("require_sources", False))
    return data


def voice_for(channel: dict, speaker: str, emotion: str) -> tuple[int, str]:
    spec = channel["voices"].get(speaker)
    if spec is None:
        raise ValueError(f"チャンネルに話者 {speaker} の声がありません。")
    style_id = int(spec["angry_style_id"] if speaker == "hero" and emotion == "angry" and "angry_style_id" in spec else spec["style_id"])
    if style_id in BLOCKED_STYLE_IDS:
        raise ValueError(f"スタイル {style_id} は事前許可が必要な声なので使いません。")
    return style_id, str(spec["credit"])


def render_upload(channel: dict, script: dict) -> str:
    name = str(channel.get("name") or "").strip()
    genre = str(channel.get("genre") or "").strip()
    voices = "\n".join(script.get("credits") or [])
    fields = {
        "title": str(script.get("title") or ""),
        "theme": str(script.get("theme") or ""),
        "name": name,
        "genre": genre,
        "channel_line": f"チャンネル: {name}\n" if name else "",
        "genre_line": f"ジャンル: {genre}\n" if genre else "",
        "voices": voices,
        "tags": " ".join(channel.get("tags") or []),
        "credits_note": str(channel["credits"]["note"]),
        "sources": _sources_block(script),
        "name_note": "チャンネル名は仮称です。確定ではありません。\n" if channel.get("name_status") == "working" else "",
    }
    try:
        text = str(channel["upload_template"]).format_map(_Safe(fields))
    except KeyError as exc:
        raise ValueError(f"upload_template の欄が未知です: {exc}") from exc
    _reject_removed_name(text, "UPLOAD.md")
    return text if text.endswith("\n") else text + "\n"


def assert_outputs_clear(paths: list[Path]) -> None:
    for path in paths:
        if not path.is_file():
            continue
        if path.suffix.lower() not in {".md", ".json", ".txt", ".yaml", ".yml"}:
            continue
        _reject_removed_name(path.read_text(encoding="utf-8"), str(path))


def _voices(raw: object) -> dict:
    if not isinstance(raw, dict):
        raise ValueError("voices がありません。")
    voices = {}
    for speaker in SPEAKERS:
        spec = raw.get(speaker)
        if not isinstance(spec, dict):
            raise ValueError(f"voices.{speaker} がありません。")
        if not isinstance(spec.get("style_id"), int) or not isinstance(spec.get("credit"), str) or not spec["credit"].strip():
            raise ValueError(f"voices.{speaker} には style_id と credit が要ります。")
        if "angry_style_id" in spec and not isinstance(spec["angry_style_id"], int):
            raise ValueError(f"voices.{speaker}.angry_style_id は整数です。")
        _reject_removed_name(spec["credit"], f"voices.{speaker}.credit")
        voices[speaker] = spec
    return voices


def _caption(raw: object) -> dict:
    if not isinstance(raw, dict):
        raise ValueError("caption がありません。")
    missing = [key for key in CAPTION_KEYS if key not in raw]
    if missing:
        raise ValueError("caption に足りない欄: " + "、".join(missing))
    if raw["bar"] != "none":
        raise ValueError("caption.bar は none です。字幕の帯は使いません。")
    colors = raw["colors"]
    if not isinstance(colors, dict) or "hook" not in colors or "develop" not in colors:
        raise ValueError("caption.colors に hook と develop が要ります。")
    parsed = {}
    for role, value in colors.items():
        if not isinstance(value, list) or len(value) != 4:
            raise ValueError(f"caption.colors.{role} は RGBA の4数です。")
        parsed[str(role)] = tuple(int(channel) for channel in value)
    style = dict(raw)
    style["colors"] = parsed
    return style


def _credits(raw: object) -> dict:
    if not isinstance(raw, dict):
        raise ValueError("credits がありません。")
    if raw.get("on_screen") != "voices":
        raise ValueError("credits.on_screen は voices です。画面に出すのは使った声の名前だけです。")
    note = raw.get("note")
    if not isinstance(note, str) or not note.strip():
        raise ValueError("credits.note が空です。")
    _reject_removed_name(note, "credits.note")
    return {"on_screen": "voices", "note": note.strip()}


def _require_text_field(data: dict, key: str, allow_empty: bool) -> None:
    value = data.get(key)
    if not isinstance(value, str):
        raise ValueError(f"{key} は文字列です。未定なら空文字にします。")
    if not allow_empty and not value.strip():
        raise ValueError(f"{key} が空です。")


def _sources_block(script: dict) -> str:
    rows = script.get("sources") or []
    if not rows:
        return "（出典の指定なし）"
    lines = []
    for row in rows:
        lines.append(f"- {row['name']}")
        lines.append(f"  {row['url']}")
        lines.append(f"  使った記述: {row['claim']}")
    return "\n".join(lines)


def _reject_removed_name(text: str, where: str) -> None:
    if REMOVED_CHANNEL_NAME in text:
        raise ValueError(f"{where} に、使わないチャンネル名が入っています。")


def _reject_collab(text: str, where: str) -> None:
    if COLLAB_RE.search(text):
        raise ValueError(f"{where} が、いらすとやとの協力を示す名前になっています。")


class _Safe(dict):
    def __missing__(self, key: str) -> str:
        raise KeyError(key)
