"""Shot sheet for one source video. Structure stays. Four slots stay empty.

Person, animals, lines, and place are the only fields a later script may
replace. Source lines stay on the sheet as evidence and are kept out of the
prompt. This module does not render video and does not post.
"""

from __future__ import annotations

import argparse
import copy
import re
from pathlib import Path
from typing import Any, Mapping, Sequence

import yaml

import affi_reference as ref

ROOT = Path(__file__).resolve().parent
PACK_PATH = ROOT / "reference-accounts" / "source" / "repro" / "junjun_825k.yaml"
SHEET_PATH = ROOT / "reference-accounts" / "source" / "repro" / "junjun_825k.md"

SLOT = "入力"
ROLES = ("guest", "retort", "polite", "owner", "indoor_pair")
ROLE_JA = {
    "guest": "客",
    "retort": "ツッコミ",
    "polite": "丁寧",
    "owner": "飼い主",
    "indoor_pair": "室内の2匹",
}
ANIMAL_SLOTS = ("guest", "retort", "polite")
# Locked picture and camera must not name the source cast.
_LOCKED_BANNED = (
    "カラス",
    "猫",
    "女性",
    "リン",
    "ジュン",
    "ランラン",
    "ポテチ",
    "カルビー",
    "junjun",
)
_NORM = re.compile(r"[\s、。！？!?・,.\-「」『』]")


def _num(value: float) -> str:
    text = f"{float(value):.3f}".rstrip("0").rstrip(".")
    return text or "0"


def _norm(text: str) -> str:
    return _NORM.sub("", str(text or ""))


def load(path: Path | None = None) -> dict[str, Any]:
    """Read the pack and check that the shots, cuts, and slots still match."""
    data = yaml.safe_load((path or PACK_PATH).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("構成がオブジェクトではない")
    if data.get("schema") != "affi-repro-structure/v1":
        raise ValueError("構成の schema が違う")
    shots = list(data.get("shots") or [])
    captions = list(data.get("captions") or [])
    if not shots or not captions:
        raise ValueError("ショットか字幕が無い")
    duration = round(float(data["duration_s"]), 3)
    if round(float(shots[0]["start_s"]), 3) != 0:
        raise ValueError("最初のショットが 0 秒ではない")
    if round(float(shots[-1]["end_s"]), 3) != duration:
        raise ValueError("最後のショットが尺と違う")
    cuts = [round(float(item), 3) for item in data["cuts_s"]]
    edges = [round(float(shot["end_s"]), 3) for shot in shots[:-1]]
    if edges != cuts:
        raise ValueError("カットとショットの境目が違う")
    previous = 0.0
    seen_ids: set[str] = set()
    for shot in shots:
        start = round(float(shot["start_s"]), 3)
        end = round(float(shot["end_s"]), 3)
        if start != previous or end <= start:
            raise ValueError(f"ショットが連続していない: {shot['id']}")
        previous = end
        if shot["id"] in seen_ids:
            raise ValueError(f"ショット id が重複: {shot['id']}")
        seen_ids.add(shot["id"])
        for field in ("picture", "camera"):
            for word in _LOCKED_BANNED:
                if word.casefold() in str(shot.get(field) or "").casefold():
                    raise ValueError(f"固定の絵に元の名がある: {shot['id']} {word}")
    by_shot = {shot["id"]: shot for shot in shots}
    seen_caps: set[str] = set()
    for row in captions:
        if row["id"] in seen_caps:
            raise ValueError(f"字幕 id が重複: {row['id']}")
        seen_caps.add(row["id"])
        if row["role"] not in ROLES:
            raise ValueError(f"役が無い: {row['id']}")
        shot = by_shot.get(row["shot"])
        if shot is None:
            raise ValueError(f"字幕のショットが無い: {row['id']}")
        if str(row.get("line") or "") != SLOT:
            raise ValueError(f"セリフ欄が空ではない: {row['id']}")
        source = str(row.get("source_line") or "").strip()
        if not source:
            raise ValueError(f"証拠の文が無い: {row['id']}")
        start = float(shot["start_s"])
        end = float(shot["end_s"])
        for sample in row.get("seen_s") or []:
            if float(sample) < start - 0.05 or float(sample) > end + 0.05:
                raise ValueError(f"見えた秒がショットの外: {row['id']} {sample}")
    slots = data.get("slots") or {}
    if slots.get("person") != SLOT or slots.get("place") != SLOT:
        raise ValueError("人か場所が入力ではない")
    animals = slots.get("animals") or {}
    if any(animals.get(key) != SLOT for key in ANIMAL_SLOTS):
        raise ValueError("動物が入力ではない")
    return data


def captions_of(pack: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Caption rows. ``line`` is the slot. ``source_line`` is evidence."""
    rows = []
    for row in pack["captions"]:
        rows.append(
            {
                "id": row["id"],
                "shot": row["shot"],
                "role": row["role"],
                "role_ja": ROLE_JA[row["role"]],
                "seen_s": [float(item) for item in row["seen_s"]],
                "source_line": row["source_line"],
                "line": row["line"],
                "function": row.get("function") or "",
            }
        )
    return rows


def narration_of(pack: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Speech turns. There is no narrator apart from these lines."""
    rows = []
    for row in captions_of(pack):
        rows.append(
            {
                "id": row["id"],
                "shot": row["shot"],
                "role": row["role"],
                "role_ja": row["role_ja"],
                "register": pack["registers"][row["role"]],
                "seen_s": row["seen_s"],
                "line": row["line"],
                "function": row["function"],
            }
        )
    return rows


def fill(
    pack: Mapping[str, Any],
    *,
    person: str = "",
    animals: Mapping[str, str] | None = None,
    place: str = "",
    lines: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Replace only the four slots. Shot times, roles, and cameras stay."""
    filled = copy.deepcopy(dict(pack))
    slots = filled["slots"]
    if str(person or "").strip():
        ref.reject_likeness(person)
        slots["person"] = str(person).strip()
    given_animals = dict(animals or {})
    unknown = set(given_animals) - set(ANIMAL_SLOTS)
    if unknown:
        raise ValueError(f"動物の欄が無い: {', '.join(sorted(unknown))}")
    for key, value in given_animals.items():
        text = str(value or "").strip()
        if not text:
            continue
        ref.reject_likeness(text)
        slots["animals"][key] = text
    if str(place or "").strip():
        ref.reject_likeness(place)
        slots["place"] = str(place).strip()
    by_id = {row["id"]: row for row in filled["captions"]}
    for key, value in dict(lines or {}).items():
        if key not in by_id:
            raise ValueError(f"セリフの id が無い: {key}")
        text = str(value or "").strip()
        if not text:
            continue
        ref.reject_likeness(text)
        if _norm(text) == _norm(by_id[key]["source_line"]):
            raise ValueError(f"元のセリフは入れない: {key}")
        by_id[key]["line"] = text
    return filled


def blocked(pack: Mapping[str, Any]) -> list[str]:
    """Slots that are still empty. Empty means the prompt must not invent them."""
    reasons = []
    slots = pack["slots"]
    if slots.get("person") == SLOT:
        reasons.append("人は入力のまま")
    animals = slots.get("animals") or {}
    for key in ANIMAL_SLOTS:
        if animals.get(key) == SLOT:
            reasons.append(f"{ROLE_JA[key]}の動物は入力のまま")
    if slots.get("place") == SLOT:
        reasons.append("場所は入力のまま")
    for row in pack["captions"]:
        if row.get("line") == SLOT:
            reasons.append(f"{row['id']} のセリフは入力のまま")
    return reasons


def prompt_text(pack: Mapping[str, Any]) -> str:
    """English shot prompt. Evidence lines and the source cast stay out."""
    slots = pack["slots"]
    animals = slots["animals"]
    identity = {
        "guest": animals["guest"],
        "retort": animals["retort"],
        "polite": animals["polite"],
        "owner": slots["person"],
        "indoor_pair": f"{animals['retort']} and {animals['polite']}",
    }
    lines = [
        "The shot order, camera, timing, and which role speaks stay as listed.",
        f"Place: {slots['place']}.",
        "No source account name, logo, or watermark is drawn.",
        "Caption: one line, white gothic, thin shadow, lower center, no box.",
        "The words on screen are the supplied line for that turn.",
        "",
    ]
    grouped: dict[str, list] = {}
    for row in pack["captions"]:
        grouped.setdefault(row["shot"], []).append(row)
    for index, shot in enumerate(pack["shots"], start=1):
        who = ", ".join(ROLE_JA[role] for role in shot["on_screen"]) or "なし"
        lines.append(
            f"[Shot {index}] {_num(shot['start_s'])} to {_num(shot['end_s'])}. "
            f"{shot['camera']} {shot['picture']} On screen: {who}."
        )
        for row in grouped.get(shot["id"], []):
            speaker = identity[row["role"]]
            if row["line"] == SLOT:
                lines.append(f"{ROLE_JA[row['role']]} ({speaker}) speaks. The words are not supplied.")
            else:
                lines.append(f"{ROLE_JA[row['role']]} ({speaker}) says: {row['line']}")
    text = "\n".join(lines) + "\n"
    for row in pack["captions"]:
        source = str(row["source_line"])
        if len(source) >= 4 and source in text:
            raise ValueError(f"元のセリフがプロンプトに入った: {row['id']}")
        if row["line"] == SLOT and source in text:
            raise ValueError(f"元のセリフがプロンプトに入った: {row['id']}")
    for shot in pack["shots"]:
        seen = str(shot.get("source_seen") or "")
        if seen and seen in text:
            raise ValueError(f"元の画面がプロンプトに入った: {shot['id']}")
    return text


def render_markdown(pack: Mapping[str, Any]) -> str:
    """Human sheet. Evidence stays labeled. The four slots stay empty until filled."""
    reasons = blocked(pack)
    out = [
        f"# 構成 {pack['source_id']}",
        "",
        "ショット順、カメラ、秒、誰が話すか、字幕の形、オチの形は固定。",
        "変えるのは人、動物、セリフ、場所。元の動画ファイルはこのリポジトリに置かない。",
        "独立したナレーションは無い。声はせりふ。",
        "",
        "## 測り方",
        "",
        f"- 尺 {_num(pack['duration_s'])} 秒。画面 {pack['canvas']}。{pack['fps']} fps。",
        f"- カット: {pack['measure']['cuts']}",
        f"- 無音: {pack['measure']['silences']}",
        f"- 字幕: {pack['measure']['captions']}",
        f"- 曲: {pack['measure']['music']}",
        f"- 字幕の高さ: {pack['measure']['caption_y']}",
        "",
        "## 欄",
        "",
        f"- 人: {pack['slots']['person']}",
        f"- 客の動物: {pack['slots']['animals']['guest']}",
        f"- ツッコミの動物: {pack['slots']['animals']['retort']}",
        f"- 丁寧の動物: {pack['slots']['animals']['polite']}",
        f"- 場所: {pack['slots']['place']}",
        f"- セリフ: {sum(1 for row in pack['captions'] if row['line'] == SLOT)} 件が入力",
        "",
        "## 口調",
        "",
    ]
    for role in ROLES:
        out.append(f"- {ROLE_JA[role]}: {pack['registers'][role]}")
    out.extend(["", "## 字幕", ""])
    style = pack["subtitle"]
    out.append(
        f"{style['font']}。{style['edge']}。{style['lines']}行。枠は{'あり' if style['box'] else 'なし'}。"
        f"{style['place']}。{style['content']}"
    )
    mark = pack["watermark"]
    out.append(f"透かしは{mark['places']}。文字は{mark['text']}。")
    out.extend(["", "## オチの形", ""])
    out.extend(f"- {step}" for step in pack["punch"])
    out.extend(["", "## ショット", ""])
    for shot in pack["shots"]:
        who = "、".join(ROLE_JA[role] for role in shot["on_screen"]) or "なし"
        note = f" {shot['note']}" if shot.get("note") else ""
        out.append(
            f"- {shot['id']} {_num(shot['start_s'])}–{_num(shot['end_s'])}秒。"
            f"{shot['picture']} カメラ: {shot['camera']} 画面: {who}。{note}"
        )
    out.extend(
        [
            "",
            "## ナレーション",
            "",
            "語り手は置かない。下のせりふが声。見えた秒は画面文字が出ていた時刻で、発話の頭と尻ではない。",
            "",
        ]
    )
    for row in narration_of(pack):
        seen = "、".join(_num(item) for item in row["seen_s"])
        extra = f" 働き: {row['function']}。" if row["function"] else ""
        out.append(
            f"- {row['id']} {row['role_ja']}。{row['register']} ショット {row['shot']}。"
            f"見えた秒 {seen}。{extra}セリフ: {row['line']}。"
        )
    out.extend(["", "## キャプション", ""])
    for row in captions_of(pack):
        seen = "、".join(_num(item) for item in row["seen_s"])
        out.append(
            f"- {row['id']} {row['role_ja']}。見えた秒 {seen}。"
            f"出す文: {row['line']}。証拠: {row['source_line']}。"
        )
    out.extend(["", "## 未入力", ""])
    if reasons:
        out.extend(f"- {reason}" for reason in reasons)
    else:
        out.append("- なし")
    out.append("")
    return "\n".join(out)


def prepare(path: Path | None = None) -> dict[str, Any]:
    """Load the pack. Slots stay empty. Nothing is rendered."""
    pack = load(path)
    return {
        "schema": "affi-repro-prep/v1",
        "source_id": pack["source_id"],
        "duration_s": pack["duration_s"],
        "shots": len(pack["shots"]),
        "captions": len(pack["captions"]),
        "narration": pack["narration"],
        "blocked": blocked(pack),
        "generates_video": False,
        "posts": False,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="構成シートを出す。動画は焼かない。")
    parser.add_argument("--write", action="store_true", help="同じ内容を md に書く")
    args = parser.parse_args(argv)
    pack = load()
    text = render_markdown(pack)
    if args.write:
        SHEET_PATH.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
