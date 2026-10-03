"""Affi FL2VA prompts that share the grokbot inbox but are not homage ads.

Homage I2V requires a 10-shot coconala layout. Affi shorts keep the three
text_scene fields and a Picture 1 lock, and they refuse income, cure, and
product-name claims inside the prompt.
"""

from __future__ import annotations

import re

AFFI_PROMPT_KIND = "affi-fl2va"

_FIELDS = (
    "integrated_multimodal_description:",
    "overall_soundscape:",
    "non_diegetic_music:",
)

_FORBIDDEN = (
    "px.a8.net",
    "a8mat=",
    "稼げる",
    "必ず",
    "月収",
    "年収",
    "治る",
    "改善",
    "死角ゼロ",
    "美白",
    "エイジング",
)

_PRODUCT = re.compile(
    r"おさかな|金虎|オルビス|ユードット|ユー\s*ドット|ファーボ|(?i:\borbis\b|\bfurbo\b)"
)
_LINE = re.compile(r"(?<![A-Za-z])LINE(?![A-Za-z])|ＬＩＮＥ")
_URL = re.compile(r"https?://", re.I)


def validate_affi_prompt(prompt: str) -> list[str]:
    """Return human-readable errors. Empty means the prompt may enter the inbox."""
    errs: list[str] = []
    text = prompt or ""
    if "Picture 1" not in text and "<Picture 1>" not in text:
        errs.append("Picture 1 が無い")
    cursor = 0
    for field in _FIELDS:
        at = text.find(field, cursor)
        if at < 0:
            errs.append(f"{field} が無い")
            continue
        cursor = at + len(field)
    low = text.lower()
    for bad in _FORBIDDEN:
        if bad.lower() in low:
            errs.append(f"禁止表現: {bad}")
    if _PRODUCT.search(text):
        errs.append("プロンプトに商品名がある")
    if _LINE.search(text):
        errs.append("LINE がある")
    if _URL.search(text):
        errs.append("URL がある")
    return errs
