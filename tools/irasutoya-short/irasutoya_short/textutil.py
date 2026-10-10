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
