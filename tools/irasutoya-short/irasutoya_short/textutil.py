"""テロップの改行。日本語は文字数で折る。"""

from __future__ import annotations


def _break_line(text: str, width: int) -> list[str]:
    text = text.strip()
    if not text:
        return []
    lines: list[str] = []
    rest = text
    while rest:
        if len(rest) <= width:
            lines.append(rest)
            break
        window = rest[:width]
        target = max(4, min(width, len(rest) // 2))
        cut = 0
        best_dist = 10**6
        for i, ch in enumerate(window):
            if i < 3:
                continue
            if ch in "をはがにでともへの、。！？ 　":
                dist = abs((i + 1) - target)
                if dist < best_dist:
                    best_dist = dist
                    cut = i + 1
        if cut <= 0:
            cut = width
        lines.append(rest[:cut].strip())
        rest = rest[cut:].strip()
    return [ln for ln in lines if ln]


def wrap_telop(text: str, width: int = 12, max_lines: int = 2) -> str:
    """改行位置を決めたテロップ文字列を返す。行数は max_lines まで。"""
    raw = text.replace("\r", "").strip()
    if not raw:
        return ""
    if "\n" in raw:
        parts = [ln.strip() for ln in raw.split("\n") if ln.strip()]
    else:
        parts = _break_line(raw, width)
    fixed: list[str] = []
    for part in parts:
        if len(part) <= width:
            fixed.append(part)
        else:
            fixed.extend(_break_line(part, width))
    if len(fixed) > max_lines:
        head = fixed[: max_lines - 1]
        tail = "".join(fixed[max_lines - 1 :])
        if len(tail) > width:
            tail = tail[:width]
        head.append(tail)
        fixed = head
    return "\n".join(fixed[:max_lines])


def spoken(text: str) -> str:
    return " ".join(text.replace("\n", "").split())


# 行頭に来ると、一行だけの句読点や閉じ括弧になる。
_NO_LINE_START = frozenset("、。！？!?・…，．）)」』】〉》」～ーｰ,.")
_ORPHAN_CHARS = frozenset("、。！？!?・…，．）)」』】〉》」～ーｰ,.「『（(【〈《［[")


def orphan_punctuation_lines(text: str) -> list[str]:
    """句読点や括弧だけになった行を返す。"""
    found: list[str] = []
    for line in text.split("\n"):
        stripped = line.strip()
        if stripped and all(char in _ORPHAN_CHARS for char in stripped):
            found.append(stripped)
    return found


def caption_source(text: str) -> str:
    """表示用に、折り返しの改行だけを外す。"""
    return "".join(part.strip() for part in text.replace("\r", "").split("\n") if part.strip())


def wrap_caption_lines(text: str, max_width: int, measure) -> list[str]:
    """幅で折り返す。句読点だけの行は作らない。"""
    source = caption_source(text)
    if not source:
        return []
    lines: list[str] = []
    current = ""
    for char in source:
        trial = f"{current}{char}"
        if current and measure(trial) > max_width:
            if char in _NO_LINE_START and len(current) >= 2:
                lines.append(current[:-1])
                current = current[-1] + char
            else:
                lines.append(current)
                current = char
        else:
            current = trial
    if current:
        lines.append(current)
    folded: list[str] = []
    for line in lines:
        if folded and orphan_punctuation_lines(line):
            folded[-1] = f"{folded[-1]}{line.strip()}"
        else:
            folded.append(line)
    if folded and orphan_punctuation_lines(folded[0]) and len(folded) > 1:
        folded[1] = f"{folded[0].strip()}{folded[1]}"
        folded = folded[1:]
    return [line for line in folded if line.strip()]


def vertical_columns(text: str, max_rows: int) -> list[str]:
    """縦書きの列。句読点だけで列を始めない。"""
    source = caption_source(text)
    if not source:
        return []
    limit = max(1, max_rows)
    columns: list[str] = []
    current = ""
    for char in source:
        if len(current) >= limit and char not in _NO_LINE_START:
            columns.append(current)
            current = char
        else:
            current += char
    if current:
        columns.append(current)
    folded: list[str] = []
    for column in columns:
        if folded and orphan_punctuation_lines(column):
            folded[-1] = f"{folded[-1]}{column.strip()}"
        else:
            folded.append(column)
    return [column for column in folded if column.strip()]
