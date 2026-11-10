#!/usr/bin/env python3
"""台本 md と SRT のチェッカー。

判定する項目:
- SRT の番号、時刻（HH:MM:SS,mmm）、開始 < 終了
- セリフ字幕どうしの空きが 1.5 秒以内
  （PR 行とフック行は除く。フック行は {\\an8}、PR 行は {\\an9}PR / #PR / PR｜）
- ペットと金メモの尺は 8.0〜10.5秒。字幕の端は 0.5秒刻み（24fps の区切り）
- ペットは PR を最後の 2 秒だけにする。右上に常時出すのは NG
- 美容は 0.000 秒から右上 PR があり、SRT 終端の最後 2 秒に #PR がある
- 婚活の PR は 8.500〜10.500 秒だけ。それ以外に PR があれば不合格
- ゆあ・金メモは PR が無い。金メモの概要欄に「アフィリエイト広告を含みます」は無い
- 早見表は 3行まで。数字の行は 2秒以上。秒を行に書いた表は文字の高さ 40px 以上
- Imagine のプロンプトは、フック以外の字幕 1本につき 1本。秒は字幕と揃える
- ペットの猫の描写は全カットで同じ文。使い回しの食事カットは不合格。結論は最後の1.5秒より前
- ペットの本編字幕は冒頭1秒のフックだけ。1秒以降のセリフ字幕は不合格
- ペットと金メモは、結論の1文を最後の1.5秒より前に置くことを必須にする
- 台本の台詞と、画面の表・見出しの用語がずれていたら不合格（加給と加算など）
- 禁止語が台詞・字幕に無い（根拠メモや PR 注記は見ない）
- 見出し「0〜1秒フック」「brief」「自己採点」があり、自己採点の最後の合計が 80 以上
- アフィリエイト URL の断片があれば警告（結果は WARN。他が落ちていれば FAIL が優先）

使い方:
  python tools/script_lint.py inputs/20261028
  python tools/script_lint.py --self-test
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

GAP_LIMIT_MS = 1500
PR_TAIL_MS = 2000
PR_WINDOW_BEGIN_MS = 8500
PR_WINDOW_END_MS = 10500
DURATION_LO_MS = 8000
DURATION_HI_MS = 10500
HALF_MS = 500
CAT_SENTENCE = "黒い短毛で、目は黄色、耳は立っている。"
BAN_SENTENCE = "切り抜き・白いふちどり・合成はしない。"
TAIL_SENTENCE = "しっぽは体につながった1本。"
AFFILIATE_LINE = "アフィリエイト広告を含みます"
HOOK_MARKS = ("0\u301c1秒フック", "0\uff5e1秒フック")
BANNED_WORDS = ("必ず稼げる", "若返る", "治る", "絶対", "必ず")
MONEY_RE = re.compile(r"\d[\d,]*\s*円|\d+\s*万\s*円")
# 秒の区切り。基準は同じで、読める表記だけ広げる。
SPAN_RE = re.compile(r"(\d+\.\d+)\s*(?:-|–|〜|～)\s*(\d+\.\d+)")
OPEN_PR = "{\\an9}PR"
HOOK_TAG = "{\\an8}"
SPEED_MARK = "等倍（+0%）"
CTA_WORDS = ("プロフィール", "リンク", "概要欄から", "買って", "申し込んで", "フォロー")
PRODUCT_NAMES = ("毎日腎活",)
TERM_PAIRS = (("加給", "加算"),)
SKIP_MD = frozenset({"REPORT.md", "cuts-for-pc.md"})
BAD_SPEED_RE = re.compile(
    r"早回し\s*[=:]?\s*([0-9]+(?:\.[0-9]+)?)|"
    r"([0-9]+(?:\.[0-9]+)?)\s*倍速|"
    r"倍速\s*[=:]?\s*([0-9]+(?:\.[0-9]+)?)|"
    r"atempo\s*[=:]?\s*([0-9]+(?:\.[0-9]+)?)"
)
TIMESTAMP_RE = re.compile(
    r"(\d{2}):(\d{2}):(\d{2}),(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2}),(\d{3})"
)
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)
SCORE_RE = re.compile(r"(?:合計|[＝=])\s*(\d+)\s*(?:/\s*100|点)")
COLUMNS = (
    "本",
    "SRT書式",
    "字幕の間",
    "PR",
    "禁止語",
    "見出し",
    "自己採点",
    "表",
    "尺",
    "プロンプト",
    "フック",
    "速度",
    "誘導",
    "a8",
    "用語",
    "結論",
    "字幕",
    "結果",
)


@dataclass(frozen=True)
class Cue:
    index: int
    start: int
    end: int
    text: str


@dataclass(frozen=True)
class Section:
    level: int
    title: str
    body: str


@dataclass(frozen=True)
class Row:
    name: str
    srt_format: str
    gap: str
    pr: str
    banned: str
    headings: str
    score: str
    table: str
    timing: str
    prompts: str
    hook: str
    speed: str
    cta: str
    a8: str
    terms: str
    conclusion: str
    captions: str
    result: str


def affiliate_needles() -> tuple[str, str]:
    """URL 断片。ソースに連続した文字列を置かない。"""
    return ("a8" + ".net", "a8" + "mat")


def fmt_sec(ms: int) -> str:
    text = f"{ms / 1000:.3f}".rstrip("0").rstrip(".")
    return text + "秒"


def lane_of(name: str) -> str:
    if any(token in name for token in ("ペット", "美容", "婚活")):
        return "pr"
    if any(token in name for token in ("ゆあ", "金メモ")):
        return "none"
    return "unknown"


def normalize(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def parse_sections(md: str) -> list[Section]:
    matches = list(HEADING_RE.finditer(md))
    sections: list[Section] = []
    for i, match in enumerate(matches):
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(md)
        sections.append(
            Section(len(match.group(1)), match.group(2).strip(), md[start:end])
        )
    return sections


def to_ms(hour: str, minute: str, second: str, millis: str) -> int | None:
    hh = int(hour)
    mm = int(minute)
    ss = int(second)
    ms = int(millis)
    if mm > 59 or ss > 59:
        return None
    return ((hh * 60 + mm) * 60 + ss) * 1000 + ms


def parse_srt(text: str) -> tuple[list[Cue], list[str]]:
    stripped = normalize(text).lstrip("\ufeff").strip()
    if stripped == "":
        return [], ["空ファイル"]
    blocks = re.split(r"\n(?:[ \t]*\n)+", stripped)
    cues: list[Cue] = []
    errors: list[str] = []
    for position, block in enumerate(blocks, start=1):
        lines = block.split("\n")
        number_text = lines[0].strip()
        if not re.fullmatch(r"\d+", number_text):
            errors.append(f"{position}番目の番号が不正")
            continue
        number = int(number_text)
        if number != position:
            errors.append(f"番号が{number}（{position}の位置）")
        if len(lines) < 2:
            errors.append(f"{number}に時刻がない")
            continue
        matched = TIMESTAMP_RE.fullmatch(lines[1].strip())
        if matched is None:
            errors.append(f"{number}の時刻の形が不正")
            continue
        start = to_ms(*matched.group(1, 2, 3, 4))
        end = to_ms(*matched.group(5, 6, 7, 8))
        if start is None or end is None:
            errors.append(f"{number}の時分が範囲外")
            continue
        if start >= end:
            errors.append(f"{number}は開始が終了以上")
            continue
        body = "\n".join(lines[2:]).strip()
        if body == "":
            errors.append(f"{number}に字幕がない")
            continue
        cues.append(Cue(number, start, end, body))
    return cues, errors


def is_pr_cue(text: str) -> bool:
    if OPEN_PR in text or "#PR" in text:
        return True
    for line in text.splitlines():
        visible = re.sub(r"\{[^}]*\}", "", line).strip()
        if visible == "PR" or visible.startswith("PR｜") or visible.startswith("PR|"):
            return True
    return False


def is_hook_cue(text: str) -> bool:
    return HOOK_TAG in text


def dialogue_cues(cues: list[Cue]) -> list[Cue]:
    spoken = [cue for cue in cues if not is_pr_cue(cue.text) and not is_hook_cue(cue.text)]
    spoken.sort(key=lambda cue: (cue.start, cue.end, cue.index))
    return spoken


def find_banned(text: str) -> list[str]:
    found: list[str] = []
    for word in BANNED_WORDS:
        if word == "必ず" and "必ず稼げる" in text:
            if "必ず" in text.replace("必ず稼げる", ""):
                found.append(word)
            continue
        if word in text:
            found.append(word)
    return found


def is_spoken_heading(title: str) -> bool:
    return any(token in title for token in ("画の流れ", "字幕", "台詞", "セリフ"))


def spoken_text(sections: list[Section]) -> str:
    return "\n".join(section.body for section in sections if is_spoken_heading(section.title))


def score_text(sections: list[Section]) -> str:
    chunks: list[str] = []
    index = 0
    while index < len(sections):
        section = sections[index]
        if "自己採点" not in section.title:
            index += 1
            continue
        parts = [section.body]
        index += 1
        while index < len(sections) and sections[index].level > section.level:
            parts.append(sections[index].body)
            index += 1
        chunks.append("\n".join(parts))
    return "\n".join(chunks)


def check_headings(sections: list[Section]) -> str:
    titles = [section.title for section in sections]
    missing: list[str] = []
    if not any(any(mark in title for mark in HOOK_MARKS) for title in titles):
        missing.append("0〜1秒フック")
    if not any(re.search(r"brief", title, re.IGNORECASE) for title in titles):
        missing.append("brief")
    if not any("自己採点" in title for title in titles):
        missing.append("自己採点")
    if missing:
        return "FAIL（無い: " + "、".join(missing) + "）"
    return "PASS"


def check_score(sections: list[Section]) -> str:
    if not any("自己採点" in section.title for section in sections):
        return "FAIL（自己採点の節が無い）"
    totals = [int(match.group(1)) for match in SCORE_RE.finditer(score_text(sections))]
    if not totals:
        return "FAIL（合計が見つからない）"
    total = totals[-1]
    if total >= 80:
        return f"PASS（{total}）"
    return f"FAIL（{total}）"


def check_gap(cues: list[Cue]) -> str:
    spoken = dialogue_cues(cues)
    if not spoken:
        return "PASS（セリフ字幕なし）"
    if len(spoken) == 1:
        return "PASS（セリフ字幕1つ）"
    gaps = [later.start - earlier.end for earlier, later in zip(spoken, spoken[1:])]
    worst = max(gaps)
    if worst > GAP_LIMIT_MS:
        return f"FAIL（最大{fmt_sec(worst)}）"
    return f"PASS（最大{fmt_sec(max(worst, 0))}）"


def check_pet_pr(cues: list[Cue]) -> str:
    """ペットは最後の2秒だけ。それより前のPR（右上の常時表示を含む）はNG。"""
    duration = max(cue.end for cue in cues)
    tail_begin = duration - PR_TAIL_MS
    reasons: list[str] = []
    early = [cue for cue in cues if is_pr_cue(cue.text) and cue.start < tail_begin]
    if any(OPEN_PR in cue.text for cue in early):
        reasons.append("右上PRが最後の2秒より前にある")
    elif early:
        reasons.append("最後の2秒より前にPRがある")
    tail = any(
        "#PR" in cue.text and cue.start >= tail_begin and cue.end >= duration for cue in cues
    )
    if not tail:
        reasons.append("最後2秒の#PRが無い")
    if reasons:
        return "FAIL（" + "、".join(reasons) + "）"
    return "PASS"


def check_konkatsu_pr(cues: list[Cue]) -> str:
    """婚活のPRは8.500〜10.500秒だけ。それ以外のPRは不合格。"""
    reasons: list[str] = []
    outside = [
        cue
        for cue in cues
        if is_pr_cue(cue.text)
        and (cue.start < PR_WINDOW_BEGIN_MS or cue.end > PR_WINDOW_END_MS)
    ]
    if any(OPEN_PR in cue.text for cue in outside):
        reasons.append("8.5〜10.5秒以外に右上PRがある")
    elif outside:
        reasons.append("8.5〜10.5秒以外にPRがある")
    tail = any(
        "#PR" in cue.text
        and cue.start >= PR_WINDOW_BEGIN_MS
        and cue.end == PR_WINDOW_END_MS
        for cue in cues
    )
    if not tail:
        reasons.append("8.5〜10.5秒の#PRが無い")
    if reasons:
        return "FAIL（" + "、".join(reasons) + "）"
    return "PASS"


def check_pr(cues: list[Cue], lane: str, name: str = "") -> str:
    if lane == "unknown":
        return "FAIL（レーン不明）"
    if lane == "pr" and "ペット" in name:
        return check_pet_pr(cues)
    if lane == "pr" and "婚活" in name:
        return check_konkatsu_pr(cues)
    opening = any(cue.start == 0 and OPEN_PR in cue.text for cue in cues)
    duration = max(cue.end for cue in cues)
    tail_begin = duration - PR_TAIL_MS
    tail = any(
        "#PR" in cue.text and cue.start <= tail_begin and cue.end >= duration for cue in cues
    )
    marked = any(is_pr_cue(cue.text) for cue in cues)
    if lane == "pr":
        reasons: list[str] = []
        if not opening:
            reasons.append("0.000秒の右上PRが無い")
        if not tail:
            reasons.append("最後2秒の#PRが無い")
        if reasons:
            return "FAIL（" + "、".join(reasons) + "）"
        return "PASS"
    if lane == "none":
        if marked:
            return "FAIL（PRなしのラインにPRがある）"
        return "PASS（PRなし）"
    return "FAIL（レーン不明）"


def check_money(name: str, text: str) -> str:
    """金額のような数字。金メモだけ実額を出してよい。他のラインは不合格。"""
    hits: list[str] = []
    for match in MONEY_RE.finditer(text):
        found = match.group(0)
        if found not in hits:
            hits.append(found)
    if "金メモ" in name:
        if hits:
            return "PASS（実額は出してよい: " + "、".join(hits) + "）"
        return "PASS（金額なし）"
    if not hits:
        return "PASS"
    return "FAIL（" + "、".join(hits) + "）"


def check_banned(md_spoken: str, srt_text: str | None) -> str:
    parts: list[str] = []
    md_hits = find_banned(md_spoken)
    if md_hits:
        parts.append("台本「" + "・".join(md_hits) + "」")
    if srt_text is None:
        parts.append("SRTなし")
    else:
        srt_hits = find_banned(srt_text)
        if srt_hits:
            parts.append("SRT「" + "・".join(srt_hits) + "」")
    if not parts:
        return "PASS"
    return "FAIL（" + "、".join(parts) + "）"


def check_a8(text: str) -> str:
    host, param = affiliate_needles()
    if host in text or param in text:
        return "WARN（URL断片）"
    return "なし"


def join_status(parts: list[str]) -> str:
    if not parts:
        return "PASS"
    return "FAIL（" + "、".join(parts) + "）"


def _spans_in(text: str) -> list[tuple[float, float]]:
    found: list[tuple[float, float]] = []
    for matched in SPAN_RE.finditer(text):
        found.append((float(matched.group(1)), float(matched.group(2))))
    return found


def check_table(md: str) -> str:
    """早見表は1画面3行まで。数字の行は1行につき2秒以上。

    行の中に秒が書いてあれば、その幅を見る。書いていなければ、
    節内の「N.N秒」の開始時刻の間隔と、尺の2秒前までを見る。
    秒を行に書いた表は、文字の高さ40px以上の指定も要る。
    """
    sections = parse_sections(md)
    blocks = [section for section in sections if "早見表" in section.title]
    if not blocks:
        return "PASS（表なし）"
    body = blocks[0].body
    table_lines = [line.strip() for line in body.splitlines() if line.strip().startswith("|")]
    separator = next((index for index, line in enumerate(table_lines) if "---" in line), None)
    if separator is None:
        return "FAIL（表の区切りが無い）"
    rows = table_lines[separator + 1 :]
    if len(rows) > 3:
        return f"FAIL（表が{len(rows)}行）"
    reasons: list[str] = []
    explicit = False
    missing: list[int] = []
    for index, line in enumerate(rows, start=1):
        if re.search(r"\d", line) is None:
            continue
        matched = SPAN_RE.search(line)
        if matched is None:
            missing.append(index)
            continue
        explicit = True
        span = float(matched.group(2)) - float(matched.group(1))
        if span < 2.0:
            reasons.append(f"{index}行目が{span:.3f}秒")
    if missing:
        starts = [float(item) for item in re.findall(r"(\d+\.\d+)秒", body)]
        unique: list[float] = []
        for start in starts:
            if start not in unique:
                unique.append(start)
        duration_match = re.search(r"尺[:：]\s*(\d+\.\d+)", md)
        content_end = None
        if duration_match is not None:
            content_end = float(duration_match.group(1)) - 2.0
        if len(unique) < len(missing) or content_end is None:
            reasons.append("数字の行に2秒以上の幅が無い")
        else:
            points = unique[: len(missing)] + [content_end]
            for index, start, end in zip(missing, points, points[1:]):
                if end - start < 2.0:
                    reasons.append(f"{index}行目が{end - start:.3f}秒")
    if explicit and "40px" not in body:
        reasons.append("文字の高さが40px以上でない")
    if reasons:
        return "FAIL（" + "、".join(reasons) + "）"
    return "PASS"


def check_timing(cues: list[Cue], name: str) -> str:
    """ペットと金メモだけ。8.0〜10.5秒、端は0.5秒刻み。"""
    if "ペット" not in name and "金メモ" not in name:
        return "PASS（対象外）"
    if not cues:
        return "FAIL（字幕が無い）"
    reasons: list[str] = []
    if any(cue.start % HALF_MS or cue.end % HALF_MS for cue in cues):
        reasons.append("0.5秒刻みでない")
    duration = max(cue.end for cue in cues)
    if duration < DURATION_LO_MS or duration > DURATION_HI_MS:
        reasons.append(f"尺{fmt_sec(duration)}（8.0〜10.5秒）")
    if reasons:
        return "FAIL（" + "、".join(reasons) + "）"
    return f"PASS（{fmt_sec(duration)}）"


def overview_body(md: str) -> str:
    return "\n".join(section.body for section in parse_sections(md) if "概要欄" in section.title)


def check_hook(cues: list[Cue]) -> str:
    """{\\an8} は 0.000 開始、終了は 1.000 秒まで。"""
    hooks = [cue for cue in cues if is_hook_cue(cue.text)]
    if not hooks:
        return "PASS（フックなし）"
    late = [cue for cue in hooks if cue.start != 0 or cue.end > 1000]
    if late:
        return "FAIL（フックは0.000から1.000秒まで）"
    return "PASS"


def check_speed(md: str) -> str:
    """等倍（+0%）が無い、または 1.0 以外の早回し・倍速・atempo は不合格。"""
    if SPEED_MARK not in md:
        return "FAIL（等倍（+0%）が無い）"
    bad: list[str] = []
    for match in BAD_SPEED_RE.finditer(md):
        raw = next(group for group in match.groups() if group is not None)
        if abs(float(raw) - 1.0) > 0.001:
            bad.append(match.group(0))
    if bad:
        return "FAIL（" + "、".join(bad) + "）"
    return "PASS"


def check_cta(name: str, spoken: str, srt: str, md: str) -> str:
    """金メモの台詞・字幕・概要欄に、誘導か商品名がある。"""
    if "金メモ" not in name:
        return "PASS（対象外）"
    blob = "\n".join((spoken, srt, overview_body(md)))
    hits = [word for word in CTA_WORDS + PRODUCT_NAMES if word in blob]
    if hits:
        return "FAIL（" + "・".join(hits) + "）"
    return "PASS"


def check_prompts(md: str, cues: list[Cue], name: str) -> str:
    """プロンプト節があるときだけ。フック以外の字幕と秒を揃える。秒の無い見出しは不合格。"""
    if "プロンプト" not in md:
        return "PASS（プロンプトなし）"
    headings = re.findall(
        r"^###\s+プロンプト[^\n]*?(\d+\.\d+)\s*(?:-|–|〜|～)\s*(\d+\.\d+)",
        md,
        flags=re.MULTILINE,
    )
    blocks = re.split(r"(?m)^### ", md)
    prompt_blocks = [block for block in blocks if block.startswith("プロンプト")]
    if not headings or len(headings) != len(prompt_blocks):
        return "FAIL（プロンプトの秒が無い）"
    reasons: list[str] = []
    ranges = [(float(start), float(end)) for start, end in headings]
    needed = [cue for cue in cues if not is_hook_cue(cue.text)]
    for cue in needed:
        start = cue.start / 1000
        end = cue.end / 1000
        if not any(abs(start - left) < 0.001 and abs(end - right) < 0.001 for left, right in ranges):
            reasons.append(f"{start:.3f}-{end:.3f}のプロンプトが無い")
    if len(ranges) != len(needed):
        reasons.append(f"プロンプト{len(ranges)}本（字幕{len(needed)}本）")
    for block in prompt_blocks:
        if "9:16" not in block or "画面に文字を出さない" not in block:
            reasons.append("9:16か画面文字の指定が無い")
            break
    if "ペット" in name:
        if any(CAT_SENTENCE not in block for block in prompt_blocks):
            reasons.append("猫の描写が揃っていない")
        if any(BAN_SENTENCE not in block for block in prompt_blocks):
            reasons.append("切り抜き・白いふちどり・合成の禁止が無い")
        if any(TAIL_SENTENCE not in block for block in prompt_blocks):
            reasons.append("しっぽが体につながった1本でない")
        if any(all(word in block for word in ("器", "袋", "食べ")) for block in prompt_blocks):
            reasons.append("使い回しの食事カット")
        tail = max((cue.end for cue in cues), default=0) / 1000 - 2.0
        for block, (_start, end) in zip(prompt_blocks, ranges):
            if all(word in block for word in ("器", "袋", "食べ")) and end > tail + 0.001:
                reasons.append("商品カットが最後の2秒にかかる")
                break
        for cue in cues:
            if "食べ" in cue.text and cue.end / 1000 > tail + 0.001:
                reasons.append("商品の字幕が最後の2秒にかかる")
                break
        spoken = dialogue_cues(cues)
        if spoken and spoken[-1].end > max(cue.end for cue in cues) - 1500:
            reasons.append("結論が最後の1.5秒にかかる")
    if reasons:
        return "FAIL（" + "、".join(reasons) + "）"
    return "PASS"


def _split_cells(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _markdown_rows(body: str) -> list[list[str]]:
    lines = [line.strip() for line in body.splitlines() if line.strip().startswith("|")]
    if not lines:
        return []
    return [_split_cells(line) for line in lines if "---" not in line]


def screen_and_speech(md: str) -> tuple[str, str]:
    """画面は早見表と見出し。台詞は音読の列だけ。"""
    screen: list[str] = []
    speech: list[str] = []
    for section in parse_sections(md):
        title = section.title
        if "早見表" in title or "見出し" in title:
            screen.append(title)
            screen.append(section.body)
        if "台詞" not in title and "セリフ" not in title:
            continue
        rows = _markdown_rows(section.body)
        if not rows:
            speech.append(section.body)
            continue
        header = rows[0]
        speech_at = [i for i, cell in enumerate(header) if any(mark in cell for mark in ("台詞", "ナレ", "セリフ"))]
        screen_at = [i for i, cell in enumerate(header) if any(mark in cell for mark in ("画面", "見出し", "表"))]
        if not speech_at and not screen_at:
            speech.append(section.body)
            continue
        for row in rows[1:]:
            for index in speech_at:
                if index < len(row):
                    speech.append(row[index])
            for index in screen_at:
                if index < len(row):
                    screen.append(row[index])
    return "\n".join(screen), "\n".join(speech)


def check_terms(md: str) -> str:
    """表・見出しと台詞で、対になる用語が食い違っていたら不合格。"""
    screen, speech = screen_and_speech(md)
    reasons: list[str] = []
    for left, right in TERM_PAIRS:
        screen_left = left in screen
        screen_right = right in screen
        speech_left = left in speech
        speech_right = right in speech
        if screen_left and not screen_right and speech_right and not speech_left:
            reasons.append(f"画面は{left}、台詞は{right}")
        elif screen_right and not screen_left and speech_left and not speech_right:
            reasons.append(f"画面は{right}、台詞は{left}")
    if reasons:
        return "FAIL（" + "、".join(reasons) + "）"
    return "PASS（対なし）" if not any(word in screen or word in speech for pair in TERM_PAIRS for word in pair) else "PASS"


def check_conclusion(md: str, cues: list[Cue], name: str) -> str:
    """ペットと金メモは、結論の1文が最後の1.5秒より前で終わることを必須にする。"""
    if "ペット" not in name and "金メモ" not in name:
        return "PASS（対象外）"
    duration_ms = max((cue.end for cue in cues), default=DURATION_HI_MS)
    limit = (duration_ms - 1500) / 1000
    found = False
    ends: list[float] = []
    sentence = False
    for line in md.splitlines():
        if "結論" not in line:
            continue
        found = True
        if re.search(r"結論[:：]|[。？?]", line):
            sentence = True
        matched = SPAN_RE.search(line)
        if matched is not None:
            ends.append(float(matched.group(2)))
            continue
        single = re.search(r"(\d+\.\d+)秒", line)
        if single is not None:
            ends.append(float(single.group(1)))
    if not found or not sentence:
        return "FAIL（結論の1文が無い）"
    if not ends:
        return "FAIL（結論の秒が無い）"
    if any(end > limit + 0.001 for end in ends):
        return "FAIL（結論が最後の1.5秒にかかる）"
    return "PASS"


def check_pet_captions(cues: list[Cue], name: str) -> str:
    """ペットの本編字幕は冒頭1秒のフックだけ。PRは最後の2秒で、ここには含めない。"""
    if "ペット" not in name:
        return "PASS（対象外）"
    if dialogue_cues(cues):
        return "FAIL（本編字幕は冒頭1秒のフックだけ）"
    return "PASS（フックだけ）"


def overall_of(row: Row) -> str:
    hard = (
        row.srt_format,
        row.gap,
        row.pr,
        row.banned,
        row.headings,
        row.score,
        row.table,
        row.timing,
        row.prompts,
        row.hook,
        row.speed,
        row.cta,
        row.terms,
        row.conclusion,
        row.captions,
    )
    if any(not item.startswith("PASS") for item in hard):
        return "FAIL"
    if row.a8.startswith("WARN"):
        return "WARN"
    return "PASS"


def lint_texts(name: str, md: str | None, srt: str | None) -> Row:
    lane = lane_of(name)
    if md is None:
        sections: list[Section] = []
        headings = "FAIL（台本なし）"
        score = "FAIL（台本なし）"
        md_body = ""
        spoken = ""
    else:
        md_body = normalize(md)
        sections = parse_sections(md_body)
        headings = check_headings(sections)
        score = check_score(sections)
        spoken = spoken_text(sections)

    cues: list[Cue] = []
    if srt is None:
        srt_format = "FAIL（SRTファイルなし）"
        gap = "FAIL（SRTファイルなし）"
        pr = "FAIL（SRTファイルなし）"
        srt_body = ""
    else:
        srt_body = normalize(srt)
        cues, errors = parse_srt(srt_body)
        srt_format = join_status(errors)
        if cues:
            gap = check_gap(cues)
            pr = check_pr(cues, lane, name)
        else:
            gap = "FAIL（字幕を読めない）"
            pr = "FAIL（字幕を読めない）"
    if pr.startswith("PASS") and "金メモ" in name and AFFILIATE_LINE in overview_body(md_body):
        pr = "FAIL（アフィリエイト広告を含みます）"

    banned = check_banned(spoken, None if srt is None else srt_body)
    money = check_money(name, spoken + "\n" + srt_body)
    if money.startswith("FAIL"):
        banned = money if banned.startswith("PASS") else banned + "、" + money.removeprefix("FAIL（").removesuffix("）")
    table = check_table("" if md is None else md_body)
    timing = check_timing(cues, name)
    prompts = check_prompts("" if md is None else md_body, cues, name)
    hook = check_hook(cues)
    speed = check_speed(md_body)
    cta = check_cta(name, spoken, srt_body, md_body)
    a8 = check_a8(md_body + "\n" + srt_body)
    terms = check_terms(md_body)
    conclusion = check_conclusion(md_body, cues, name)
    captions = check_pet_captions(cues, name)
    row = Row(
        name,
        srt_format,
        gap,
        pr,
        banned,
        headings,
        score,
        table,
        timing,
        prompts,
        hook,
        speed,
        cta,
        a8,
        terms,
        conclusion,
        captions,
        "FAIL",
    )
    return Row(
        row.name,
        row.srt_format,
        row.gap,
        row.pr,
        row.banned,
        row.headings,
        row.score,
        row.table,
        row.timing,
        row.prompts,
        row.hook,
        row.speed,
        row.cta,
        row.a8,
        row.terms,
        row.conclusion,
        row.captions,
        overall_of(row),
    )


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def collect(root: Path) -> list[tuple[str, str | None, str | None]]:
    """scripts/+subs/ と、同じフォルダに md と srt が並ぶ形の両方。"""
    scripts = root / "scripts"
    subs = root / "subs"
    if scripts.is_dir():
        md_paths = {path.stem: path for path in scripts.glob("*.md") if path.name not in SKIP_MD}
        srt_paths = {path.stem: path for path in subs.glob("*.srt")} if subs.is_dir() else {}
    else:
        md_paths = {path.stem: path for path in root.glob("*.md") if path.name not in SKIP_MD}
        srt_paths = {path.stem: path for path in root.glob("*.srt")}
    items: list[tuple[str, str | None, str | None]] = []
    for stem in sorted(set(md_paths) | set(srt_paths)):
        md = read_text(md_paths[stem]) if stem in md_paths else None
        srt = read_text(srt_paths[stem]) if stem in srt_paths else None
        items.append((stem, md, srt))
    return items


def lint_dir(root: Path) -> list[Row]:
    return [lint_texts(name, md, srt) for name, md, srt in collect(root)]


def render(rows: list[Row]) -> str:
    header = "| " + " | ".join(COLUMNS) + " |"
    rule = "| " + " | ".join("---" for _ in COLUMNS) + " |"
    lines = [header, rule]
    for row in rows:
        cells = (
            row.name,
            row.srt_format,
            row.gap,
            row.pr,
            row.banned,
            row.headings,
            row.score,
            row.table,
            row.timing,
            row.prompts,
            row.hook,
            row.speed,
            row.cta,
            row.a8,
            row.terms,
            row.conclusion,
            row.captions,
            row.result,
        )
        lines.append("| " + " | ".join(cells) + " |")
    passed = sum(1 for row in rows if row.result == "PASS")
    failed = sum(1 for row in rows if row.result == "FAIL")
    warned = sum(1 for row in rows if row.result == "WARN")
    lines.append("")
    lines.append(f"合計 {len(rows)}本: PASS {passed} / FAIL {failed} / WARN {warned}")
    return "\n".join(lines)


def minimal_md(score_body: str, extra: str = "") -> str:
    hook = HOOK_MARKS[0]
    return (
        f"# テスト\n\n"
        f"## {hook}（画＋文字）\n"
        f"- テキストフック: 「テスト」\n\n"
        f"## brief\n"
        f"- 尺: 4秒\n"
        f"- 声: {SPEED_MARK}\n\n"
        f"## 台詞\n"
        f"テストの台詞。\n\n"
        f"## 字幕\n"
        f"テスト\n\n"
        f"## 自己採点\n"
        f"{score_body}\n"
        f"{extra}"
    )


def expect(ok: bool, label: str, detail: str) -> bool:
    mark = "OK" if ok else "NG"
    print(f"- {label}: {mark} {detail}")
    return ok


def self_test(fixtures: Path, repo: Path) -> bool:
    print("# 壊したSRT 3つ")
    print()
    rows = lint_dir(fixtures)
    by_name = {row.name: row for row in rows}
    print(render(rows))
    print()
    print("確認:")
    ok = True

    gap = by_name.get("2026-10-28-ゆあ-test-gap")
    pr = by_name.get("2026-10-28-婚活-test-pr")
    banned = by_name.get("2026-10-28-金メモ-test-kinshi")
    if gap is None or pr is None or banned is None or len(rows) != 3:
        print("- テスト用の3本が揃っていない: NG")
        return False

    ok = expect(
        gap.result == "FAIL" and gap.gap.startswith("FAIL") and "2秒" in gap.gap
        and gap.srt_format == "PASS" and gap.pr.startswith("PASS") and gap.banned == "PASS"
        and gap.headings == "PASS" and gap.score == "PASS（80）" and gap.a8 == "なし",
        "間が2秒",
        gap.gap,
    ) and ok
    ok = expect(
        pr.result == "FAIL"
        and pr.pr == "FAIL（8.5〜10.5秒の#PRが無い）"
        and pr.gap.startswith("PASS")
        and pr.banned == "PASS"
        and pr.srt_format == "PASS"
        and pr.headings == "PASS"
        and pr.score == "PASS（80）"
        and pr.a8 == "なし",
        "PR抜け",
        pr.pr,
    ) and ok
    ok = expect(
        banned.result == "FAIL" and banned.banned.startswith("FAIL") and "治る" in banned.banned
        and "台本" not in banned.banned and banned.gap.startswith("PASS")
        and banned.pr.startswith("PASS") and banned.srt_format == "PASS"
        and banned.headings == "PASS" and banned.score == "PASS（80）",
        "禁止語",
        banned.banned,
    ) and ok

    print()
    print("境界:")
    near = lint_texts(
        "2026-10-28-ゆあ-boundary-ok",
        minimal_md("- 合計 80/100"),
        "1\n00:00:00,000 --> 00:00:01,000\nあ\n\n2\n00:00:02,500 --> 00:00:04,000\nい\n",
    )
    over = lint_texts(
        "2026-10-28-ゆあ-boundary-ng",
        minimal_md("- 合計 80/100"),
        "1\n00:00:00,000 --> 00:00:01,000\nあ\n\n2\n00:00:02,501 --> 00:00:04,000\nい\n",
    )
    revised_down = lint_texts(
        "2026-10-28-ゆあ-score",
        minimal_md("### 1回目\n- 合計 90/100\n### 2回目\n- ＝ 79点\n"),
        "1\n00:00:00,000 --> 00:00:01,000\nこんにちは\n",
    )
    same_time = lint_texts(
        "2026-10-28-ゆあ-format",
        minimal_md("- 合計 80/100"),
        "1\n00:00:01,000 --> 00:00:01,000\n同じ\n",
    )
    pet_ok = lint_texts(
        "2026-10-28-ペット-positive",
        minimal_md("- 合計 80/100") + "\n## 台詞\n結論: 置いたまま、触らない。（6.000-8.500）\n",
        "1\n00:00:00,000 --> 00:00:01,000\n"
        + HOOK_TAG
        + "寝てる？\n\n2\n00:00:08,500 --> 00:00:10,500\n広告 #PR\n",
    )
    pet_corner = lint_texts(
        "2026-10-28-ペット-corner",
        minimal_md("- 合計 80/100"),
        "1\n00:00:00,000 --> 00:00:12,000\n"
        + OPEN_PR
        + "\n\n2\n00:00:10,000 --> 00:00:12,000\n広告 #PR\n",
    )
    yua_pr = lint_texts(
        "2026-10-28-ゆあ-has-pr",
        minimal_md("- 合計 80/100"),
        "1\n00:00:00,000 --> 00:00:02,000\n" + OPEN_PR + "\n\n2\n00:00:00,000 --> 00:00:02,000\n#PR\n",
    )
    ok = expect(near.gap == "PASS（最大1.5秒）" and near.result == "PASS", "1.500秒は以内", near.gap) and ok
    ok = expect(over.gap == "FAIL（最大1.501秒）", "1.501秒は超過", over.gap) and ok
    ok = expect(revised_down.score == "FAIL（79）", "自己採点は最後の合計", revised_down.score) and ok
    ok = expect(same_time.srt_format.startswith("FAIL"), "開始と終了が同じ", same_time.srt_format) and ok
    ok = expect(
        pet_ok.result == "PASS" and pet_ok.gap == "PASS（セリフ字幕なし）" and pet_ok.pr == "PASS",
        "ペットは最後の2秒だけ。フックは間隔に入れない",
        pet_ok.gap + " / " + pet_ok.pr,
    ) and ok
    ok = expect(
        pet_corner.pr.startswith("FAIL") and "右上" in pet_corner.pr,
        "ペットの右上常時PRはNG",
        pet_corner.pr,
    ) and ok
    konkatsu_ok = lint_texts(
        "2026-11-07-婚活-window",
        minimal_md("- 合計 80/100"),
        "1\n00:00:00,000 --> 00:00:01,000\n"
        + HOOK_TAG
        + "高そう？\n\n2\n00:00:08,500 --> 00:00:10,500\n広告 #PR\n",
    )
    konkatsu_early = lint_texts(
        "2026-11-07-婚活-corner",
        minimal_md("- 合計 80/100"),
        "1\n00:00:00,000 --> 00:00:10,500\n"
        + OPEN_PR
        + "\n\n2\n00:00:08,500 --> 00:00:10,500\n広告 #PR\n",
    )
    biyou_corner = lint_texts(
        "2026-11-07-美容-corner",
        minimal_md("- 合計 80/100"),
        "1\n00:00:00,000 --> 00:00:10,500\n"
        + OPEN_PR
        + "\n\n2\n00:00:08,500 --> 00:00:10,500\n広告 #PR\n",
    )
    biyou_tail_only = lint_texts(
        "2026-11-07-美容-tail",
        minimal_md("- 合計 80/100"),
        "1\n00:00:00,000 --> 00:00:01,000\n"
        + HOOK_TAG
        + "高そう？\n\n2\n00:00:08,500 --> 00:00:10,500\n広告 #PR\n",
    )
    ok = expect(
        konkatsu_ok.result == "PASS" and konkatsu_ok.pr == "PASS",
        "婚活は8.5〜10.5秒の#PRだけなら通る",
        konkatsu_ok.pr + " / " + konkatsu_ok.result,
    ) and ok
    ok = expect(
        konkatsu_early.pr.startswith("FAIL") and "8.5〜10.5秒以外に右上PRがある" in konkatsu_early.pr,
        "婚活の右上PRは8.5秒より前なら不合格",
        konkatsu_early.pr,
    ) and ok
    ok = expect(
        biyou_corner.result == "PASS" and biyou_corner.pr == "PASS",
        "美容の右上PRと最後2秒は従来どおり",
        biyou_corner.pr,
    ) and ok
    ok = expect(
        biyou_tail_only.pr.startswith("FAIL") and "0.000秒" in biyou_tail_only.pr,
        "美容は0.000秒の右上PRが無いと不合格",
        biyou_tail_only.pr,
    ) and ok
    ok = expect(yua_pr.pr.startswith("FAIL"), "ゆあにPRがあるとFAIL", yua_pr.pr) and ok
    ok = expect(find_banned("必ず稼げる") == ["必ず稼げる"], "必ず稼げるは必ずと二重に数えない", "") and ok
    ok = expect(find_banned("必ず") == ["必ず"], "必ず単体", "") and ok
    ok = expect(find_banned("絶対に治る") == ["治る", "絶対"], "治ると絶対", "") and ok

    print()
    print("2026-11-04 の追加:")
    no_seconds = lint_texts(
        "2026-11-04-ペット-no-seconds",
        minimal_md("- 合計 80/100") + "\n## Imagine\n### プロンプト1（カット1）\n9:16。画面に文字を出さない。\n",
        "1\n00:00:00,000 --> 00:00:01,000\n" + HOOK_TAG + "寝てる？\n\n"
        "2\n00:00:08,500 --> 00:00:10,500\n広告 #PR\n",
    )
    late_hook = lint_texts(
        "2026-11-04-ペット-late-hook",
        minimal_md("- 合計 80/100"),
        "1\n00:00:00,000 --> 00:00:01,500\n" + HOOK_TAG + "寝てる？\n\n"
        "2\n00:00:08,500 --> 00:00:10,500\n広告 #PR\n",
    )
    cta_md = (
        minimal_md("- 合計 80/100")
        + "\n## 台詞\nプロフィールを見て。\n\n## 概要欄\n説明。\n"
    )
    cta_hit = lint_texts(
        "2026-11-04-金メモ-cta",
        cta_md,
        "1\n00:00:00,000 --> 00:00:01,000\n" + HOOK_TAG + "いくら？\n\n"
        "2\n00:00:00,500 --> 00:00:10,500\nプロフィールを見て。\n",
    )
    goods_md = minimal_md("- 合計 80/100") + "\n## 台詞\n毎日腎活を置く。\n\n## 概要欄\n説明。\n"
    goods_hit = lint_texts(
        "2026-11-04-金メモ-goods",
        goods_md,
        "1\n00:00:00,000 --> 00:00:01,000\n" + HOOK_TAG + "いくら？\n\n"
        "2\n00:00:00,500 --> 00:00:10,500\nただの説明。\n",
    )
    slow_md = (
        "# テスト\n\n## 0〜1秒フック（画＋文字）\n- テキストフック: 「テスト」\n\n"
        "## brief\n- 尺: 4秒\n\n## 台詞\nテスト。\n\n## 字幕\nテスト\n\n## 自己採点\n- 合計 80/100\n"
    )
    slow = lint_texts(
        "2026-11-04-ペット-no-speed",
        slow_md,
        "1\n00:00:00,000 --> 00:00:01,000\n" + HOOK_TAG + "寝てる？\n\n"
        "2\n00:00:08,500 --> 00:00:10,500\n広告 #PR\n",
    )
    fast = lint_texts(
        "2026-11-04-ペット-fast",
        minimal_md("- 合計 80/100") + "\natempo=1.2\n",
        "1\n00:00:00,000 --> 00:00:01,000\n" + HOOK_TAG + "寝てる？\n\n"
        "2\n00:00:08,500 --> 00:00:10,500\n広告 #PR\n",
    )
    plain = (
        minimal_md("- 合計 80/100")
        + "\n## Imagine\n### プロンプト1（カット1・8.500-10.500）\n文字あり。\n"
    )
    no_frame = lint_texts(
        "2026-11-04-ペット-no-frame",
        plain,
        "1\n00:00:00,000 --> 00:00:01,000\n" + HOOK_TAG + "寝てる？\n\n"
        "2\n00:00:08,500 --> 00:00:10,500\n広告 #PR\n",
    )
    ok = expect(
        no_seconds.prompts.startswith("FAIL") and "旧表記" not in no_seconds.prompts,
        "1a 秒の無いプロンプトはFAIL",
        no_seconds.prompts,
    ) and ok
    ok = expect(late_hook.hook.startswith("FAIL"), "1b フックが1秒を超える", late_hook.hook) and ok
    ok = expect(cta_hit.cta.startswith("FAIL") and "プロフィール" in cta_hit.cta, "1c 誘導", cta_hit.cta) and ok
    ok = expect(goods_hit.cta.startswith("FAIL") and "毎日腎活" in goods_hit.cta, "1c 商品名", goods_hit.cta) and ok
    ok = expect(slow.speed.startswith("FAIL"), "1d 等倍が無い", slow.speed) and ok
    ok = expect(fast.speed.startswith("FAIL") and "1.2" in fast.speed, "1d 1.0以外", fast.speed) and ok
    ok = expect(
        no_frame.prompts.startswith("FAIL") and "9:16" in no_frame.prompts,
        "1f 9:16と画面文字",
        no_frame.prompts,
    ) and ok
    overlap_still = (
        "縦9:16。画面に文字を出さない。" + CAT_SENTENCE + "無地の器。袋。顔を器に入れて粒を食べる。"
    )
    overlap_md = (
        minimal_md("- 合計 80/100")
        + "\n## Imagine\n"
        + "### プロンプト1（カット1・6.000-9.000）\n"
        + overlap_still
        + "\n### プロンプト2（カット2・8.500-10.500）\n9:16。画面に文字を出さない。\n"
        + CAT_SENTENCE
        + "\n"
    )
    overlap = lint_texts(
        "2026-11-04-ペット-product-overlap",
        overlap_md,
        "1\n00:00:00,000 --> 00:00:01,000\n"
        + HOOK_TAG
        + "寝てる？\n\n2\n00:00:06,000 --> 00:00:09,000\n器の粒を、食べてる。\n\n"
        "3\n00:00:08,500 --> 00:00:10,500\n広告 #PR\n",
    )
    ok = expect(
        overlap.prompts.startswith("FAIL") and "最後の2秒" in overlap.prompts,
        "商品カットが最後の2秒にかかる",
        overlap.prompts,
    ) and ok
    ok = expect(
        "使い回しの食事カット" in overlap.prompts,
        "使い回しの食事カット",
        overlap.prompts,
    ) and ok
    late_still = (
        "9:16。画面に文字を出さない。"
        + CAT_SENTENCE
        + TAIL_SENTENCE
        + BAN_SENTENCE
    )
    late_conclusion = lint_texts(
        "2026-11-05-ペット-late-conclusion",
        minimal_md("- 合計 80/100")
        + "\n## Imagine\n### プロンプト1（カット1・7.000-9.500）\n"
        + late_still
        + "\n### プロンプト2（カット2・8.500-10.500）\n"
        + late_still
        + "\n",
        "1\n00:00:00,000 --> 00:00:01,000\n"
        + HOOK_TAG
        + "寝てる？\n\n2\n00:00:07,000 --> 00:00:09,500\nまた、裾に触ってる。\n\n"
        "3\n00:00:08,500 --> 00:00:10,500\n広告 #PR\n",
    )
    ok = expect(
        late_conclusion.prompts.startswith("FAIL") and "最後の1.5秒" in late_conclusion.prompts,
        "結論が最後の1.5秒にかかる",
        late_conclusion.prompts,
    ) and ok

    empty = Path("/tmp/script-lint-empty-1e")
    if empty.exists():
        for child in empty.iterdir():
            child.unlink()
    else:
        empty.mkdir()
    empty_code = main([str(empty)])
    ok = expect(empty_code != 0, "1e 台本が無いフォルダは0以外", str(empty_code)) and ok
    lonely = Path("/tmp/script-lint-nocuts-1e")
    (lonely / "scripts").mkdir(parents=True, exist_ok=True)
    (lonely / "subs").mkdir(parents=True, exist_ok=True)
    (lonely / "scripts" / "2026-11-04-ペット-lonely.md").write_text(minimal_md("- 合計 80/100"), encoding="utf-8")
    (lonely / "subs" / "2026-11-04-ペット-lonely.srt").write_text(
        "1\n00:00:00,000 --> 00:00:01,000\n" + HOOK_TAG + "寝てる？\n\n"
        "2\n00:00:08,500 --> 00:00:10,500\n広告 #PR\n",
        encoding="utf-8",
    )
    cuts = lonely / "cuts-for-pc.md"
    if cuts.exists():
        cuts.unlink()
    lonely_code = main([str(lonely)])
    ok = expect(lonely_code != 0, "1e cuts-for-pc.md が無い", str(lonely_code)) and ok

    inputs = repo / "inputs" / "20261028"
    if inputs.is_dir():
        print()
        print("実ファイルの抜き取り:")
        real = {row.name: row for row in lint_dir(inputs)}
        pet = real.get("2026-10-28-ペット-kuroneko-hidamari")
        kasa = real.get("2026-10-28-ゆあ-kasa-hairu")
        san = real.get("2026-10-28-婚活-sanoufuku")
        ok = expect(
            pet is not None and pet.result == "FAIL" and "右上" in pet.pr,
            "古い右上PRのペットは不合格",
            "" if pet is None else pet.result + " / " + pet.pr + " / " + pet.timing,
        ) and ok
        ok = expect(
            kasa is not None and kasa.gap == "PASS（最大1.5秒）" and kasa.pr == "PASS（PRなし）",
            "ゆあ傘の間隔1.5秒",
            "" if kasa is None else kasa.gap,
        ) and ok
        ok = expect(
            san is not None and san.banned == "PASS" and san.score == "PASS（81）" and san.pr == "PASS",
            "婚活三往復は注記の語を台詞に数えない",
            "" if san is None else san.banned + " / " + san.score,
        ) and ok

    print()
    print("用語と結論:")
    mismatch = lint_texts(
        "2026-11-09-金メモ-term-mismatch",
        minimal_md("- 合計 80/100")
        + "\n## 早見表\n文字の高さは40px以上。\n| 区分 | 額 | 秒 |\n| --- | --- | --- |\n| 加給 | そのまま | 0.000-10.500 |\n"
        + "\n## 台詞\n| 秒 | 台詞 | 画面文字 |\n| --- | --- | --- |\n| 2.000-8.500 | 結論: 加算は、届く。 | 行 |\n",
        "1\n00:00:00,000 --> 00:00:01,000\n"
        + HOOK_TAG
        + "いくら？\n\n2\n00:00:02,000 --> 00:00:08,500\n加算は、届く。\n\n"
        + "3\n00:00:08,500 --> 00:00:10,500\n表だけ。\n",
    )
    matched = lint_texts(
        "2026-11-09-金メモ-term-match",
        minimal_md("- 合計 80/100")
        + "\n## 早見表\n文字の高さは40px以上。\n| 区分 | 額 | 秒 |\n| --- | --- | --- |\n| 加給 | そのまま | 0.000-10.500 |\n"
        + "\n## 台詞\n| 秒 | 台詞 | 画面文字 |\n| --- | --- | --- |\n| 2.000-8.500 | 結論: 加給は、届く。 | 加給 |\n",
        "1\n00:00:00,000 --> 00:00:01,000\n"
        + HOOK_TAG
        + "いくら？\n\n2\n00:00:02,000 --> 00:00:08,500\n加給は、届く。\n\n"
        + "3\n00:00:08,500 --> 00:00:10,500\n表だけ。\n",
    )
    missing_conclusion = lint_texts(
        "2026-11-09-ペット-no-conclusion",
        minimal_md("- 合計 80/100"),
        "1\n00:00:00,000 --> 00:00:01,000\n"
        + HOOK_TAG
        + "寝てる？\n\n2\n00:00:08,500 --> 00:00:10,500\n広告 #PR\n",
    )
    ok = expect(
        mismatch.result == "FAIL" and mismatch.terms == "FAIL（画面は加給、台詞は加算）",
        "加給と加算のずれ",
        mismatch.terms,
    ) and ok
    ok = expect(matched.terms == "PASS" and matched.conclusion == "PASS", "用語が揃い結論がある", matched.terms) and ok
    ok = expect(
        missing_conclusion.conclusion == "FAIL（結論の1文が無い）" and missing_conclusion.result == "FAIL",
        "結論の1文が必須",
        missing_conclusion.conclusion,
    ) and ok
    print()
    print("秒の区切り:")
    hook_and_pr = (
        "1\n00:00:00,000 --> 00:00:01,000\n"
        + HOOK_TAG
        + "テスト\n\n2\n00:00:08,500 --> 00:00:10,500\n広告 #PR\n"
    )
    for mark in ("〜", "～", "-", "–"):
        waved = lint_texts(
            "2026-11-10-婚活-span",
            minimal_md("- 合計 80/100")
            + f"\n## Imagine\n### プロンプト1（カット1・8.500{mark}10.500）\n9:16。画面に文字を出さない。\n",
            hook_and_pr,
        )
        ok = expect(
            waved.prompts.startswith("PASS"),
            f"区切り {mark} の秒は読める",
            waved.prompts,
        ) and ok
    missing_span = lint_texts(
        "2026-11-10-婚活-no-span",
        minimal_md("- 合計 80/100") + "\n## Imagine\n### プロンプト1（カット1）\n9:16。画面に文字を出さない。\n",
        hook_and_pr,
    )
    ok = expect(
        missing_span.prompts.startswith("FAIL") and "秒が無い" in missing_span.prompts,
        "秒の無いプロンプトは不合格のまま",
        missing_span.prompts,
    ) and ok
    print()
    print("金額:")
    kane_money = check_money("2026-11-10-金メモ-gaku", "納める額は15000円。")
    pet_money = check_money("2026-11-10-ペット-gaku", "料金は15000円。")
    ok = expect(kane_money.startswith("PASS") and "15000円" in kane_money, "金メモの実額は合格", kane_money) and ok
    ok = expect(pet_money.startswith("FAIL") and "15000円" in pet_money, "ペットの金額は不合格", pet_money) and ok

    print()
    print("自己テスト: " + ("OK" if ok else "NG"))
    return ok


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="台本 md と SRT のチェッカー")
    parser.add_argument("root", nargs="?", help="scripts/ と subs/ があるディレクトリ")
    parser.add_argument("--self-test", action="store_true", help="壊したSRT 3つと境界を確認する")
    parser.add_argument("--money-name", help="金額チェックの台本名。金メモだけ実額を通す")
    parser.add_argument("--money-text", help="金額チェックの本文")
    args = parser.parse_args(argv)
    if args.money_name is not None or args.money_text is not None:
        if not args.money_name or args.money_text is None:
            parser.error("--money-name と --money-text は両方要る")
        status = check_money(args.money_name, args.money_text)
        print(f"MONEY\t{status}")
        return 0 if status.startswith("PASS") else 1

    repo = Path(__file__).resolve().parents[1]
    fixtures = Path(__file__).resolve().parent / "script_lint_fixtures"
    exit_code = 0
    if args.self_test:
        if not self_test(fixtures, repo):
            exit_code = 2
        if args.root:
            print()
    if args.root:
        root = Path(args.root)
        try:
            rows = lint_dir(root)
        except FileNotFoundError as exc:
            print(str(exc), file=sys.stderr)
            return 2
        if not rows:
            print("台本が0件", file=sys.stderr)
            return 2
        print(render(rows))
        if not (root / "cuts-for-pc.md").is_file():
            print("FAIL\tcuts-for-pc.md が無い", file=sys.stderr)
            exit_code = max(exit_code, 1)
        if any(row.result != "PASS" for row in rows):
            exit_code = max(exit_code, 1)
    elif not args.self_test:
        parser.error("root か --self-test を指定する")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
