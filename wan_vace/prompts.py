"""Pull the fixed blocks and per-cut prompts out of the trial script."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


class ScriptError(ValueError):
    """The trial script is missing a block the runner copies into the prompt."""


@dataclass(frozen=True)
class CutPrompt:
    cut: str
    positive: str
    negative: str
    uses_sakura: bool


_HEADING = re.compile(r"^## .+$", re.M)
_CUT_LINE = re.compile(r"^- (C\d+):\s*(.+)$", re.M)


def _section(text: str, title_prefix: str) -> str:
    matches = list(_HEADING.finditer(text))
    for index, match in enumerate(matches):
        if match.group(0).startswith(title_prefix):
            end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
            return text[match.end() : end]
    raise ScriptError(f"台本に見出しが無い: {title_prefix}")


def _backtick(block: str, label: str) -> str:
    found = re.findall(r"`([^`]+)`", block)
    if not found:
        raise ScriptError(f"{label} のバッククォートが無い")
    return found[0].strip()


def _negatives(section: str) -> tuple[str, dict[str, str]]:
    common = ""
    extras: dict[str, str] = {}
    for line in section.splitlines():
        if "`" not in line:
            continue
        phrase = _backtick(line, "ネガティブ")
        ids = re.findall(r"C\d+", line)
        if ids:
            for cut_id in ids:
                extras[cut_id] = phrase
        elif "共通" in line:
            common = phrase
    if not common:
        raise ScriptError("共通ネガティブが無い")
    return common, extras


def load_prompts(path: Path) -> dict[str, CutPrompt]:
    text = Path(path).read_text(encoding="utf-8")
    block_a = _backtick(_section(text, "## 固定語ブロックA"), "ブロックA")
    block_s = _backtick(_section(text, "## 固定語ブロックS"), "ブロックS")
    common, extras = _negatives(_section(text, "## ネガティブ"))
    prompt_section = _section(text, "## プロンプト")
    found: dict[str, CutPrompt] = {}
    for match in _CUT_LINE.finditer(prompt_section):
        cut_id, body = match.group(1), match.group(2).strip()
        parts = body.split("/ neg:", 1)
        positive_raw = parts[0].strip().rstrip("/")
        uses_sakura = "[S]" in positive_raw
        positive = positive_raw.replace("[A]", block_a).replace("[S]", block_s)
        positive = re.sub(r"\s+", " ", positive).strip(" ,")
        negative = common
        if cut_id in extras:
            negative = f"{common}, {extras[cut_id]}"
        found[cut_id] = CutPrompt(cut_id, positive, negative, uses_sakura)
    for cut_id in ("C1", "C2", "C3", "C4"):
        if cut_id not in found:
            raise ScriptError(f"台本のプロンプトに {cut_id} が無い")
    return found


def with_face_lock(prompt: CutPrompt, enabled: bool) -> CutPrompt:
    """Add a state phrase when face consistency is on. Sakura cuts only."""
    if not enabled or not prompt.uses_sakura:
        return prompt
    phrase = "same adult face as the reference image, consistent identity"
    if phrase in prompt.positive:
        return prompt
    return CutPrompt(
        prompt.cut,
        f"{prompt.positive}, {phrase}",
        prompt.negative,
        prompt.uses_sakura,
    )
