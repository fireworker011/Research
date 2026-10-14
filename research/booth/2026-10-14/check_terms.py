#!/usr/bin/env python3
"""Scan research/booth/2026-10-14 works 27-31 for terms that cannot ship.

Flags minors, school settings, family roles, and known borrowed IP.
Allows the purchase disclaimer 「18歳未満」 and the negation 「実在の人物では…」.
Does not publish anything. Does not generate audio.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

BANNED = [
    "ロリ",
    "ショタ",
    "幼女",
    "幼男",
    "少女",
    "少年",
    "女子高生",
    "女子中学生",
    "小学生",
    "中学生",
    "高校生",
    "女子校",
    "学生",
    "生徒",
    "学園",
    "制服",
    "童顔",
    "つるぺた",
    "メスガキ",
    "児童",
    "幼児",
    "小児",
    "未成年",
    "子供",
    "子ども",
    "こども",
    "幼い",
    "妹",
    "義妹",
    "実妹",
    "弟",
    "義弟",
    "姪",
    "甥",
    "娘",
    "近親",
    "実母",
    "実父",
    "義母",
    "義父",
    "女の子",
    "男の子",
    "スクール水着",
    "ブルマ",
    "催眠",
    "泥酔",
    "睡眠姦",
    "アークナイツ",
    "対魔忍",
    "初音ミク",
    "芸能人",
    "夢前黎",
    "御子柴",
    "鹿仲茉菜",
    "あみたろ",
]

LETTER_BAN = re.compile(r"(?<![A-Za-z])(JK|JC|JS)(?![A-Za-z])")

AGE = re.compile(r"(?<![0-9０-９])([0-9０-９]{1,2})歳")

ALLOW_LINE = (
    "18歳未満",
    "実在の人物ではありません",
    "実在の人物に似せない",
    "実在の有名人",
    "あみたろの声は使いません",
    "あみたろは使いません",
)

PENETRATION = re.compile(r"挿入|中出し|なかに、だして|なかにだして")
WORK_DIRS = [ROOT / str(n) for n in range(27, 32)]


def to_int(age: str) -> int:
    trans = str.maketrans("０１２３４５６７８９", "0123456789")
    return int(age.translate(trans))


def iter_texts():
    for folder in WORK_DIRS:
        if not folder.is_dir():
            yield folder, "(missing folder)", ""
            continue
        for path in sorted(folder.iterdir()):
            if path.suffix.lower() not in {".txt", ".json", ".md"}:
                continue
            yield folder, path.name, path.read_text(encoding="utf-8")
    for name in ("README.md", "title-tag-proposals.md", "audio-measure.md"):
        path = ROOT / name
        if path.is_file():
            yield ROOT, name, path.read_text(encoding="utf-8")


def main() -> int:
    hits: list[str] = []
    seen_works: set[str] = set()
    for folder, name, text in iter_texts():
        if name == "(missing folder)":
            hits.append(f"missing {folder.name}")
            continue
        label = folder.name if folder != ROOT else "root"
        if folder != ROOT:
            seen_works.add(folder.name)
        for lineno, line in enumerate(text.splitlines(), 1):
            if any(ok in line for ok in ALLOW_LINE):
                continue
            for word in BANNED:
                if word in line:
                    hits.append(f"{label}/{name}:{lineno} banned:{word}")
            if LETTER_BAN.search(line):
                hits.append(f"{label}/{name}:{lineno} banned:JK/JC/JS")
            for match in AGE.finditer(line):
                age = to_int(match.group(1))
                if age < 20:
                    hits.append(f"{label}/{name}:{lineno} age:{age}")
        if name == "script.md":
            if PENETRATION.search(text):
                hits.append(f"{folder.name}/script.md penetration in a hands-or-words work")
            if "いや" not in text and "嫌" not in text:
                hits.append(f"{folder.name}/script.md missing a stop word")
            if "おとな" not in text and "成人" not in text:
                hits.append(f"{folder.name}/script.md missing an adult line")
            if "アンジー" not in text:
                hits.append(f"{folder.name}/script.md missing Angie")
        if name == "product.json":
            data = json.loads(text)
            if data.get("publish") is not False:
                hits.append(f"{folder.name}/product.json publish must be false")
            if data.get("all_characters_adult") is not True:
                hits.append(f"{folder.name}/product.json adult flag")
            if data.get("real_people") is not False:
                hits.append(f"{folder.name}/product.json real_people")
            if data.get("penetration") is not False:
                hits.append(f"{folder.name}/product.json penetration must be false")
            voice = data.get("voice") or {}
            if voice.get("speaker") != "アンジーさん":
                hits.append(f"{folder.name}/product.json speaker must be Angie")
            if "あみたろ" in json.dumps(voice, ensure_ascii=False):
                hits.append(f"{folder.name}/product.json amitáro")
            heroine = data.get("heroine") or {}
            age = heroine.get("age")
            if not isinstance(age, int) or age < 20:
                hits.append(f"{folder.name}/product.json heroine age")
            if not data.get("price_sources"):
                hits.append(f"{folder.name}/product.json missing price_sources")
    for n in range(27, 32):
        if str(n) not in seen_works:
            hits.append(f"missing work {n}")
    if hits:
        print(f"NG {len(hits)}")
        for hit in hits:
            print(hit)
        return 1
    print("OK works 27-31")
    return 0


if __name__ == "__main__":
    sys.exit(main())
