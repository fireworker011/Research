#!/usr/bin/env python3
"""11/04〜11/06 の親ポストを機械チェックする。投稿はしない。"""

from __future__ import annotations

import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STOCK = ROOT / "2026-11-04-06-stock.md"

EMOJI = re.compile(
    "["
    "\U0001F000-\U0001FAFF"
    "\U00002600-\U000027BF"
    "\U0001F1E6-\U0001F1FF"
    "\U00002190-\U000021FF"
    "\U00002B00-\U00002BFF"
    "\U0000FE00-\U0000FE0F"
    "\U0000200D"
    "\U000020E3"
    "]"
)

NG_WORDS = [
    "脱サラ",
    "給料超え",
    "給料を超",
    "必ず稼げる",
    "寝かしつけ",
    "スクール",
    "皆さん",
    "ぜひ",
    "つまり",
    "いいね",
    "DM",
    "『",
    "』",
    "2億",
    "投資勝ち組",
    "月収安定",
    "1067",
]

# 同じ日にかぶせない崩し語。本文に出たら数える。
SLANG = [
    "ちゅげー",
    "ぶぉけぇ",
    "ﾏｼﾞｶﾖｰ",
    "ﾁｬﾘﾝ",
    "ﾁｬﾘｰﾝ",
    "ヒェッ",
    "ﾋﾞﾐｮｰ",
    "ビミョ",
    "ｳｯﾋｮｰ",
    "うっへうっへ",
    "ｵﾗｧ",
    "オラァ",
    "草",
    "アフォ",
    "クッソ",
    "すげー",
    "ヤバぃ",
    "エグい",
    "へぇ〜",
    "長ーな",
    "どかーん",
    "ゴリゴリ",
    "ブン回す",
    "よん",
    "僕ちん",
    "雑魚",
    "猛省",
    "ｳｪﾋﾋﾋ",
    "ﾀﾋ",
    "わかんねー",
    "www",
    "普通に",
]


def split_posts(text: str) -> list[tuple[str, dict[str, str]]]:
    parts = re.split(r"(?m)^### ", text)
    posts: list[tuple[str, dict[str, str]]] = []
    for part in parts[1:]:
        lines = part.splitlines()
        title = lines[0].strip()
        fields: dict[str, str] = {}
        for line in lines[1:]:
            matched = re.match(r"^- ([^:]+): (.*)$", line)
            if matched and matched.group(1) not in fields:
                fields[matched.group(1)] = matched.group(2).strip()
        if "親" in fields:
            posts.append((title, fields))
    return posts


def slang_hits(text: str) -> list[str]:
    return [word for word in SLANG if word in text]


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else STOCK
    text = path.read_text(encoding="utf-8")
    posts = split_posts(text)
    errors: list[str] = []
    print(f"file: {path}")
    print(f"親ポスト本数: {len(posts)}")
    if len(posts) != 15:
        errors.append(f"本数が15ではない: {len(posts)}")

    by_day: dict[str, list[str]] = defaultdict(list)
    kind_by_day: dict[str, dict[str, int]] = defaultdict(lambda: {"情報系": 0, "プレイヤー系": 0})

    for title, fields in posts:
        parent = fields.get("親", "")
        reply = fields.get("リプ", "")
        body = parent if reply == "なし" else parent + reply
        post_id = fields.get("id", title)
        day = fields.get("日付", "")
        kind = fields.get("分類", "")
        declared = fields.get("崩し語", "")
        print(f"{post_id}\t{len(parent)}字\t{kind}\t崩し語={declared}")

        if len(parent) > 140:
            errors.append(f"{post_id}: 140字超 {len(parent)}")
        if "\n" in parent or "\r" in parent:
            errors.append(f"{post_id}: 親に改行")
        if EMOJI.search(parent) or EMOJI.search(reply):
            errors.append(f"{post_id}: 絵文字")
        if "#" in parent or "#" in reply:
            errors.append(f"{post_id}: ハッシュタグ")
        for word in NG_WORDS:
            if word in parent or word in reply:
                errors.append(f"{post_id}: NG語 {word}")
        if "俺" in body or re.search(r"私(?!の見解)", body):
            errors.append(f"{post_id}: 一人称が僕以外の可能性")
        if "僕" not in parent and kind == "プレイヤー系":
            errors.append(f"{post_id}: プレイヤー系の親に僕が無い")

        hits = slang_hits(parent + "\n" + reply)
        if declared == "なし":
            if hits:
                errors.append(f"{post_id}: 崩し語なしの宣言だが検出 {hits}")
        else:
            if declared not in hits:
                errors.append(f"{post_id}: 宣言した崩し語が本文に無い {declared} / 検出 {hits}")
            extra = [word for word in hits if word != declared]
            if extra:
                errors.append(f"{post_id}: 崩し語が複数 {hits}")
        by_day[day].append(declared)
        if kind in kind_by_day[day]:
            kind_by_day[day][kind] += 1
        else:
            errors.append(f"{post_id}: 分類が情報系でもプレイヤー系でもない: {kind}")

        if kind == "情報系":
            url = fields.get("出典URL", "")
            published = fields.get("公開日", "")
            opened = fields.get("開いた日時", "")
            if not url.startswith("https://"):
                errors.append(f"{post_id}: 出典URLが無い")
            if not published:
                errors.append(f"{post_id}: 公開日が無い")
            elif published < "2026-10-27":
                errors.append(f"{post_id}: 公開日が2026-10-27より前 {published}")
            if "JST" not in opened:
                errors.append(f"{post_id}: 開いた日時(JST)が無い")
        if kind == "プレイヤー系":
            if not fields.get("使った事実"):
                errors.append(f"{post_id}: 使った事実が無い")
            if not fields.get("添付"):
                errors.append(f"{post_id}: 添付ファイル名が無い")

        stated = fields.get("字数", "")
        if stated and stated != str(len(parent)):
            errors.append(f"{post_id}: 字数欄 {stated} と len {len(parent)} が違う")

    for day, words in by_day.items():
        used = [word for word in words if word and word != "なし"]
        if len(used) != len(set(used)):
            errors.append(f"{day}: 同じ日の崩し語かぶり {used}")

    for day, counts in sorted(kind_by_day.items()):
        print(f"{day}: 情報系 {counts['情報系']} / プレイヤー系 {counts['プレイヤー系']}")
        if counts["情報系"] != 2 or counts["プレイヤー系"] != 3:
            errors.append(f"{day}: 2対3ではない {counts}")

    print("---")
    if errors:
        print(f"FAIL {len(errors)}")
        for item in errors:
            print(item)
        return 1
    print("PASS 15本 140字以内・改行0・絵文字0・ハッシュタグ0・NGワード0")
    return 0


if __name__ == "__main__":
    sys.exit(main())
