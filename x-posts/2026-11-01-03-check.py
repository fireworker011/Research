# -*- coding: utf-8 -*-
"""2026-11-01〜03 のX下書きを機械チェックする。投稿はしない。"""

from __future__ import annotations

import re
import sys
from collections import defaultdict
from pathlib import Path

HEADING = re.compile(r"^### (11/0[123]) ([IP]\d+)（(情報系|プレイヤー系)）\s*$")
BODY_LABEL = re.compile(r"^- 本文（(\d+)字）:\s*$")
REPLY_LABEL = re.compile(r"^- リプ（(\d+)字）:\s*$")
REPLY_NONE = "- リプ: なし（完結型）"
DATE_OK = re.compile(r"2026-10-(2[5-9]|3[01])|2026-11-0[1-3]")

NG_WORDS = (
    "脱サラ",
    "給料",
    "必ず稼げる",
    "必ず伸び",
    "寝かしつけ",
    "スクール",
    "2億",
    "投資勝ち組",
    "月収安定",
    "皆さん",
    "ぜひ",
    "つまり",
    "いいね",
    "フォローして",
    "DMください",
)

KUZUSHI = (
    "うっへうっへ",
    "ちゅげー",
    "ぶぉけぇ",
    "ブォケェ",
    "ﾏｼﾞｶﾖｰ",
    "マジカヨー",
    "ﾋﾞﾐｮｰ",
    "ビミョ〜",
    "ビミョー",
    "ｳｯﾋｮｰ",
    "ウッヒョー",
    "ｵﾗｧ",
    "オラァ",
    "ヒェッ",
    "ﾁｬﾘﾝﾁｬﾘﾝ",
    "ﾁｬﾘｰﾝ",
    "ﾁｬﾘﾝ",
    "クッソ",
    "アフォ",
    "へぇ",
    "ヤバぃ",
    "すげー",
    "わからん",
    "わかんね",
    "エグい",
    "どかーん",
    "ゴリゴリ",
    "草",
)


def find_emoji(text: str) -> str | None:
    for ch in text:
        code = ord(ch)
        if 0x1F300 <= code <= 0x1FAFF or 0x2600 <= code <= 0x27BF:
            return ch
        if code in (0xFE0F, 0x200D, 0x2B50):
            return ch
    return None


def find_kuzushi(text: str) -> list[tuple[str, int]]:
    masked = text
    hits: list[tuple[str, int]] = []
    for phrase in sorted(KUZUSHI, key=len, reverse=True):
        count = masked.count(phrase)
        if count:
            hits.append((phrase, count))
            masked = masked.replace(phrase, "□" * len(phrase))
    return hits


def split_sections(text: str) -> list[tuple[tuple[str, str, str], list[str]]]:
    found: list[tuple[tuple[str, str, str], list[str]]] = []
    current: tuple[str, str, str] | None = None
    buf: list[str] = []
    for line in text.splitlines():
        match = HEADING.match(line)
        if match:
            if current is not None:
                found.append((current, buf))
            current = (match.group(1), match.group(2), match.group(3))
            buf = [line]
        elif current is not None:
            buf.append(line)
    if current is not None:
        found.append((current, buf))
    return found


def quote_after(lines: list[str], index: int) -> tuple[str | None, str | None]:
    cursor = index + 1
    while cursor < len(lines) and lines[cursor].strip() == "":
        cursor += 1
    if cursor >= len(lines) or not lines[cursor].startswith("> "):
        return None, "引用行が無い"
    body = lines[cursor][2:]
    if body.startswith(" "):
        return None, "引用の先頭に空白がある"
    return body, None


def field_value(lines: list[str], prefix: str) -> str | None:
    for line in lines:
        if line.startswith(prefix):
            return line[len(prefix) :].strip()
    return None


def check_public_text(label: str, text: str, declared: int | None, problems: list[str]) -> None:
    if declared is not None and declared != len(text):
        problems.append(f"{label}の表示字数{declared}と実測{len(text)}が違う")
    if len(text) > 140:
        problems.append(f"{label}が140字を超えている（{len(text)}）")
    if "\n" in text:
        problems.append(f"{label}に改行がある")
    if "#" in text or "＃" in text:
        problems.append(f"{label}にハッシュタグがある")
    if "『" in text or "』" in text:
        problems.append(f"{label}に『』がある")
    emoji = find_emoji(text)
    if emoji is not None:
        problems.append(f"{label}に絵文字がある（{emoji}）")
    for word in NG_WORDS:
        if word in text:
            problems.append(f"{label}にNGワード「{word}」がある")
    if "要確認" in text or ".md" in text:
        problems.append(f"{label}に作業メモが混ざっている")


def check_file(path: Path) -> tuple[list[str], list[str]]:
    text = path.read_text(encoding="utf-8")
    sections = split_sections(text)
    problems: list[str] = []
    logs: list[str] = []
    if len(sections) != 15:
        problems.append(f"本数が15ではない（{len(sections)}）")

    seen_ids: set[str] = set()
    per_day: dict[str, list[tuple[str, str]]] = defaultdict(list)
    day_kuzushi: dict[str, dict[str, str]] = defaultdict(dict)

    for (day, post_id, kind), lines in sections:
        key = f"{day} {post_id}"
        if key in seen_ids:
            problems.append(f"{key} が重複")
        seen_ids.add(key)
        per_day[day].append((post_id, kind))
        local: list[str] = []

        body = None
        body_declared = None
        reply = None
        reply_declared = None
        reply_none = False
        for index, line in enumerate(lines):
            body_match = BODY_LABEL.match(line)
            if body_match:
                body_declared = int(body_match.group(1))
                body, err = quote_after(lines, index)
                if err:
                    local.append(f"本文: {err}")
            reply_match = REPLY_LABEL.match(line)
            if reply_match:
                reply_declared = int(reply_match.group(1))
                reply, err = quote_after(lines, index)
                if err:
                    local.append(f"リプ: {err}")
            if line.strip() == REPLY_NONE:
                reply_none = True

        if body is None:
            local.append("本文が取れない")
        else:
            check_public_text("本文", body, body_declared, local)
        if reply_none and reply is not None:
            local.append("リプなしとリプ本文が両方ある")
        if not reply_none and reply is None:
            local.append("リプ本文が取れない")
        if reply is not None:
            check_public_text("リプ", reply, reply_declared, local)

        kind_line = field_value(lines, "- 種別: ")
        if kind_line is None or not kind_line.startswith(kind):
            local.append("種別の行が見出しと違う")
        if body is not None and kind_line is not None:
            if body.endswith("。") and "完結型" not in kind_line:
                local.append("本文は完結なのに種別が完結型ではない")
            if body.endswith("、") and "切っ" not in kind_line:
                local.append("本文は切りなのに種別が切りではない")
            if not body.endswith(("。", "、")):
                local.append("本文の末尾が。でも、でもない")

        fact = field_value(lines, "- 使った事実と出典: ")
        if not fact:
            local.append("使った事実と出典が無い")
        elif kind == "プレイヤー系" and ".md" not in fact:
            local.append("プレイヤー系なのに添付ファイル名が無い")

        mark = field_value(lines, "- 印: ")
        question = field_value(lines, "- ナオミチに聞くこと: ")
        if mark is None:
            local.append("印の行が無い")
        if question is None:
            local.append("ナオミチに聞くことの行が無い")
        if mark == "要確認" and (question is None or question == "なし"):
            local.append("要確認なのに聞くことが無い")

        if not field_value(lines, "- 素材プラン: "):
            local.append("素材プランが無い")
        if not field_value(lines, "- 素材の種類: "):
            local.append("素材の種類が無い")

        published = field_value(lines, "- 公開日: ")
        opened = field_value(lines, "- 開いた日時: ")
        source = field_value(lines, "- 出典URL: ")
        if kind == "情報系":
            if published is None or DATE_OK.search(published) is None:
                local.append(f"情報系の公開日が2026-10-25以降ではない（{published}）")
            if opened is None or "2026-10-28" not in opened or "JST" not in opened:
                local.append("開いた日時（JST）が無い")
            if source is None or not source.startswith("https://"):
                local.append("情報系の出典URLが無い")
        if kind == "プレイヤー系" and published != "なし":
            local.append("プレイヤー系の公開日がなしではない")

        public = body or ""
        if reply:
            public = public + "\n" + reply
        hits = find_kuzushi(public)
        names = [phrase for phrase, count in hits if count > 0]
        if len(names) > 1:
            local.append(f"崩し言葉が複数（{'、'.join(names)}）")
        for phrase, count in hits:
            if count > 1:
                local.append(f"崩し言葉「{phrase}」が{count}回")
            previous = day_kuzushi[day].get(phrase)
            if previous and previous != post_id:
                local.append(f"崩し言葉「{phrase}」が同日の{previous}とかぶる")
            else:
                day_kuzushi[day][phrase] = post_id

        status = "OK" if not local else "NG"
        shown = body_declared if body_declared is not None else "-"
        kuzushi_name = names[0] if len(names) == 1 else ("なし" if not names else "複数")
        logs.append(f"{status} {key} {kind} 本文{shown}字 崩し={kuzushi_name}")
        for item in local:
            logs.append(f"  - {item}")
            problems.append(f"{key}: {item}")

    for day in ("11/01", "11/02", "11/03"):
        rows = per_day.get(day, [])
        info = sum(1 for _, kind in rows if kind == "情報系")
        player = sum(1 for _, kind in rows if kind == "プレイヤー系")
        if len(rows) != 5 or info != 2 or player != 3:
            problems.append(f"{day} の配分が情報2・プレイヤー3ではない（情報{info}、プレイヤー{player}、計{len(rows)}）")

    return problems, logs


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).with_name("2026-11-01-03-stock.md")
    problems, logs = check_file(path)
    print(f"対象: {path}")
    print("添削AI: このスクリプトでは見ていない")
    for line in logs:
        print(line)
    print(f"問題: {len(problems)}")
    if problems:
        print("結果: NG")
        return 1
    print("結果: OK（親15本が140字以内、改行0、絵文字0、ハッシュタグ0、NGワード0）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
