# 11/28〜11/30 の親ポストを機械で見る。投稿はしない。
# 使い方: python3 x-posts/2026-11-28-30-check.py

from __future__ import annotations

import re
import sys
from pathlib import Path

STOCK = Path(__file__).with_name("2026-11-28-30-stock.md")

NG_WORDS = [
    "脱サラ",
    "給料超え",
    "給料を超",
    "必ず稼げる",
    "寝かしつけ",
    "スクール",
    "僕ちん",
    "2億",
    "投資勝ち組",
    "月収安定",
    "皆さん",
    "ぜひ",
    "つまり",
    "いいね",
    "DM",
    "『",
    "』",
]

# 11/01〜11/27 の完成文・点検・ストックで使った崩しは、こちらでは使わない。
BANNED_KUZUSHI = [
    "へぇ〜",
    "雑魚",
    "ヤバぃ",
    "エグい",
    "すげー",
    "長ーな",
    "ちゅげー",
    "ぶぉけぇ",
    "ﾏｼﾞｶﾖｰ",
    "ヒェッ",
    "ｳｯﾋｮｰ",
    "アフォ",
    "クッソ",
    "ﾋﾞﾐｮｰ",
    "わからん",
    "うっへうっへ",
    "よん",
    "www",
    "ww",
    "ゴリゴリ",
    "普通に",
    "コツコツ",
    "草",
    "ﾁｬﾘﾝ",
    "チャリーン",
    "どかーん",
    "ｵﾗｧ",
    "猛省",
    "ねぇ",
    "わかんねー",
    "ポチポチ",
    "ｳｪﾋﾋﾋ",
    "ブン回す",
    "マジ",
    "くね",
    "貧弱",
    "しれん",
    "社畜",
]

KUZUSHI = [
    "猫に小判",
] + BANNED_KUZUSHI

KANSAI = ["やで", "やな", "やん", "どす", "へん", "なん？"]

LAUGH_W = re.compile(r"(?<![A-Za-z])w+(?![A-Za-z])")


def has_emoji(text: str) -> bool:
    for ch in text:
        code = ord(ch)
        if (
            0x1F000 <= code <= 0x1FAFF
            or 0x2600 <= code <= 0x27BF
            or 0x2190 <= code <= 0x21FF
            or 0x2B00 <= code <= 0x2BFF
            or 0xFE0F == code
            or 0x200D == code
        ):
            return True
    return False


def load_posts(text: str) -> list[dict[str, str]]:
    posts: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    for line in text.splitlines():
        if line.startswith("### "):
            current = {
                "id": line[4:].split("（")[0].strip(),
                "kind": "",
                "parent": "",
                "reply": "",
                "count": "",
            }
            posts.append(current)
            continue
        if current is None:
            continue
        if line.startswith("分類::"):
            current["kind"] = line.split("::", 1)[1].strip()
        elif line.startswith("親::"):
            current["parent"] = line.split("::", 1)[1].strip()
        elif line.startswith("リプ::"):
            current["reply"] = line.split("::", 1)[1].strip()
        elif line.startswith("字数::"):
            current["count"] = line.split("::", 1)[1].strip()
    return posts


def without_urls(text: str) -> str:
    return re.sub(r"https?://\S+", "", text)


def kuzushi_in(text: str) -> list[str]:
    found: list[str] = []
    body = without_urls(text)
    for word in KUZUSHI:
        if word in body:
            found.append(word)
    if LAUGH_W.search(body):
        found.append("w")
    return found


def main() -> int:
    raw = STOCK.read_text(encoding="utf-8")
    posts = load_posts(raw)
    print(f"ファイル: {STOCK}")
    print(f"本数: {len(posts)}")
    failed = False

    if len(posts) != 15:
        print("NG 本数が15ではない")
        failed = True

    by_day: dict[str, list[str]] = {}
    kuzushi_by_day: dict[str, list[tuple[str, str]]] = {}

    for post in posts:
        post_id = post["id"]
        parent = post["parent"]
        reply = post["reply"]
        blob = without_urls(parent + reply)
        day = post_id[:5] if len(post_id) >= 5 else post_id
        problems: list[str] = []

        if not parent:
            problems.append("親が空")
        if "\n" in parent or "\r" in parent:
            problems.append("改行")
        if len(parent) > 140:
            problems.append(f"140字超 {len(parent)}")
        if post["count"] and post["count"] != str(len(parent)):
            problems.append(f"字数欄{post['count']} 実測{len(parent)}")
        if has_emoji(parent) or has_emoji(reply):
            problems.append("絵文字")
        if "#" in parent or "#" in reply:
            problems.append("ハッシュタグ")
        for word in NG_WORDS:
            if word.lower() in blob.lower():
                problems.append(f"NG語:{word}")
        for word in KANSAI:
            if word in blob:
                problems.append(f"関西:{word}")
        if "僕ちん" in blob or "俺" in blob or "私" in blob:
            problems.append("一人称")
        if "最新は追わない" in blob or "最新追いかけ" in blob:
            problems.append("最新追わないの繰り返し")

        found = kuzushi_in(blob)
        if len(found) > 1:
            problems.append("崩しが2つ以上:" + ",".join(found))
        for word in found:
            if word in BANNED_KUZUSHI or word == "w":
                problems.append("直近ストックとかぶる崩し:" + word)
            kuzushi_by_day.setdefault(day, []).append((post_id, word))

        by_day.setdefault(day, []).append(post["kind"])
        status = "OK" if not problems else "NG " + ",".join(problems)
        if problems:
            failed = True
        print(f"{post_id}\t{len(parent)}字\t{post['kind']}\t{status}")

    print("--- 日ごとの内訳 ---")
    for day, kinds in by_day.items():
        info = sum(1 for kind in kinds if kind == "情報")
        player = sum(1 for kind in kinds if kind == "プレイヤー")
        line = f"{day}\t情報{info}\tプレイヤー{player}\t計{len(kinds)}"
        if info != 2 or player != 3 or len(kinds) != 5:
            line += "\tNG"
            failed = True
        else:
            line += "\tOK"
        print(line)

    print("--- 日ごとの崩し ---")
    for day, items in kuzushi_by_day.items():
        print(day, items)
        if len(items) > 1:
            print(f"NG {day} の崩しが2つ以上")
            failed = True

    if failed:
        print("結果: NG")
        return 1
    print("結果: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
