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


# 行頭に来ると、一行だけの句読点や閉じ括弧、小さい仮名になる。
_NO_LINE_START = frozenset("、。！？!?・…，．）)」』】〉》」～ーｰ,.ぁぃぅぇぉっゃゅょゎァィゥェォッャュョヮ")
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


# 2行にするとき、片方だけが短い行にならない下限。
MIN_CAPTION_LINE = 7
_NO_LINE_END = frozenset("（(「『【〈《［[")


def short_caption_lines(text: str, minimum: int = MIN_CAPTION_LINE) -> list[str]:
    """2行以上のとき、minimum 字未満の行を返す。1行だけの字幕は対象外。"""
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    if len(lines) <= 1:
        return []
    return [line for line in lines if len(line) < minimum]


def _break_score(left: str, right: str) -> int:
    if not left or not right:
        return -1
    if right[0] in _NO_LINE_START or left[-1] in _NO_LINE_END:
        return -1
    if left[-1] in "、。！？":
        return 3
    if left[-1] in "をはがにでともへの":
        return 2
    return 1


def _layout_caption(text: str, min_score: int) -> list[str]:
    """最大2行。2行にするときは、どちらも7字以上で、禁則を守る。"""
    source = caption_source(text)
    if not source:
        return []
    if len(source) < MIN_CAPTION_LINE * 2:
        return [source]
    best: tuple[tuple[int, float], int] | None = None
    for cut in range(MIN_CAPTION_LINE, len(source) - MIN_CAPTION_LINE + 1):
        score = _break_score(source[:cut], source[cut:])
        if score < min_score:
            continue
        ranked = (score, -abs(cut - len(source) / 2))
        if best is None or ranked > best[0]:
            best = (ranked, cut)
    if best is None:
        return [source]
    cut = best[1]
    return [source[:cut], source[cut:]]


def layout_caption(text: str) -> list[str]:
    """句読点か助詞で分ける。単語の途中では分けない。"""
    return _layout_caption(text, 2)


def layout_caption_loose(text: str) -> list[str]:
    """1行に入らないときだけ使う。禁則は守り、切れ目は助詞でなくてよい。"""
    return _layout_caption(text, 1)


def wrap_caption_lines(text: str, max_width: int = 0, measure=None) -> list[str]:
    """表示用の改行。幅の測定は描画側で字を縮めて合わせる。"""
    del max_width, measure
    return layout_caption(text)


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
