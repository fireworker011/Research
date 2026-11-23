# 11/07〜11/09 の親ポストを機械で見る。投稿はしない。
# 使い方: python3 x-posts/2026-11-07-09-check.py

from __future__ import annotations

import re
import sys
from pathlib import Path

STOCK = Path(__file__).with_name("2026-11-07-09-stock.md")

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

# 11/01〜11/06 の完成文・点検で使った崩しは、こちらでは使わない。
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
]

KUZUSHI = [
    "うっへうっへ",
    "よん",
    "www",
    "ゴリゴリ",
    "普通に",
    "コツコツ",
    "ｵﾗｧ",
    "ﾁｬﾘﾝ",
    "どかーん",
    "草",
] + BANNED_KUZUSHI

KANSAI = ["やで", "やな", "やん", "どす", "へん", "なん？"]


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
    return posts


def without_urls(text: str) -> str:
    return re.sub(r"https?://\S+", "", text)


def kuzushi_in(text: str) -> list[str]:
    found: list[str] = []
    body = without_urls(text)
    for word in KUZUSHI:
        if word in body:
            found.append(word)
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

        found = kuzushi_in(blob)
        if len(found) > 1:
            problems.append("崩しが2つ以上:" + ",".join(found))
        for word in found:
            if word in BANNED_KUZUSHI:
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
        print(f"{day} 情報{info} プレイヤー{player} 計{len(kinds)}")
        if info != 2 or player != 3 or len(kinds) != 5:
            print(f"NG {day} の配分")
            failed = True

    print("--- 崩し（同じ日に同じ語がないか） ---")
    for day, items in kuzushi_by_day.items():
        words = [word for _, word in items]
        print(day, items)
        if len(words) != len(set(words)):
            print(f"NG {day} の崩しがかぶり")
            failed = True

    # パターンはファイル内で連結し、検索語そのものをソースに残さない。
    affiliate = re.compile(
        "a8" + r"\.net|" + "a8" + "mat|" + "px" + r"\.a8",
        flags=re.I,
    )
    a8 = affiliate.findall(raw)
    print(f"--- アフィリエイトURLらしき文字列: {len(a8)} ---")
    if a8:
        failed = True

    print("結果:", "不合格" if failed else "合格")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
