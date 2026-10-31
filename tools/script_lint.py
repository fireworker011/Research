#!/usr/bin/env python3
"""台本 md と SRT のチェッカー。

判定する項目:
- SRT の番号、時刻（HH:MM:SS,mmm）、開始 < 終了
- セリフ字幕どうしの空きが 1.5 秒以内
  （PR 行とフック行は除く。フック行は {\\an8}、PR 行は {\\an9}PR / #PR / PR｜）
- ペット・美容・婚活は 0.000 秒から右上 PR があり、SRT 終端の最後 2 秒に #PR がある
- ゆあ・金メモは PR が無い
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
HOOK_MARKS = ("0\u301c1秒フック", "0\uff5e1秒フック")
BANNED_WORDS = ("必ず稼げる", "若返る", "治る", "絶対", "必ず")
OPEN_PR = "{\\an9}PR"
HOOK_TAG = "{\\an8}"
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
    "a8",
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
    a8: str
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


def check_pr(cues: list[Cue], lane: str) -> str:
    if lane == "unknown":
        return "FAIL（レーン不明）"
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


def overall_of(row: Row) -> str:
    hard = (row.srt_format, row.gap, row.pr, row.banned, row.headings, row.score)
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
            pr = check_pr(cues, lane)
        else:
            gap = "FAIL（字幕を読めない）"
            pr = "FAIL（字幕を読めない）"

    banned = check_banned(spoken, None if srt is None else srt_body)
    a8 = check_a8(md_body + "\n" + srt_body)
    row = Row(name, srt_format, gap, pr, banned, headings, score, a8, "FAIL")
    return Row(
        row.name,
        row.srt_format,
        row.gap,
        row.pr,
        row.banned,
        row.headings,
        row.score,
        row.a8,
        overall_of(row),
    )


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def collect(root: Path) -> list[tuple[str, str | None, str | None]]:
    scripts = root / "scripts"
    subs = root / "subs"
    if not scripts.is_dir():
        raise FileNotFoundError(f"scripts がありません: {scripts}")
    md_paths = {path.stem: path for path in scripts.glob("*.md")}
    srt_paths = {path.stem: path for path in subs.glob("*.srt")} if subs.is_dir() else {}
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
            row.a8,
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
        f"- 尺: 4秒\n\n"
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
        pr.result == "FAIL" and pr.pr.startswith("FAIL") and "0.000秒" in pr.pr and "#PR" in pr.pr
        and pr.gap.startswith("PASS") and pr.banned == "PASS" and pr.srt_format == "PASS"
        and pr.headings == "PASS" and pr.score == "PASS（80）" and pr.a8 == "なし",
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
        minimal_md("- 合計 80/100"),
        "1\n00:00:00,000 --> 00:00:10,000\n"
        + OPEN_PR
        + "\n\n2\n00:00:00,000 --> 00:00:01,500\n"
        + HOOK_TAG
        + "寝てる？\n\n3\n00:00:10,000 --> 00:00:12,000\nPR｜広告を含みます\n#PR\n",
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
        "PR行とフック行は間隔に入れない",
        pet_ok.gap + " / " + pet_ok.pr,
    ) and ok
    ok = expect(yua_pr.pr.startswith("FAIL"), "ゆあにPRがあるとFAIL", yua_pr.pr) and ok
    ok = expect(find_banned("必ず稼げる") == ["必ず稼げる"], "必ず稼げるは必ずと二重に数えない", "") and ok
    ok = expect(find_banned("必ず") == ["必ず"], "必ず単体", "") and ok
    ok = expect(find_banned("絶対に治る") == ["治る", "絶対"], "治ると絶対", "") and ok

    inputs = repo / "inputs" / "20261028"
    if inputs.is_dir():
        print()
        print("実ファイルの抜き取り:")
        real = {row.name: row for row in lint_dir(inputs)}
        pet = real.get("2026-10-28-ペット-kuroneko-hidamari")
        kasa = real.get("2026-10-28-ゆあ-kasa-hairu")
        san = real.get("2026-10-28-婚活-sanoufuku")
        ok = expect(
            pet is not None and pet.result == "PASS" and pet.pr == "PASS" and "セリフ字幕なし" in pet.gap,
            "ペット実ファイル",
            "" if pet is None else pet.result + " / " + pet.pr + " / " + pet.gap,
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
    print("自己テスト: " + ("OK" if ok else "NG"))
    return ok


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="台本 md と SRT のチェッカー")
    parser.add_argument("root", nargs="?", help="scripts/ と subs/ があるディレクトリ")
    parser.add_argument("--self-test", action="store_true", help="壊したSRT 3つと境界を確認する")
    args = parser.parse_args(argv)

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
        if any(row.result != "PASS" for row in rows):
            exit_code = max(exit_code, 1)
    elif not args.self_test:
        parser.error("root か --self-test を指定する")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
