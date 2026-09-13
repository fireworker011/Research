"""Colab helper for stacking MiniMax H3 LoRAs.

Temporary restore wrapper: load the intact minimaxh3 copy, then apply ANAL PREP.
"""
from __future__ import annotations

import urllib.request

_BASE_URL = (
    "https://raw.githubusercontent.com/fireworker011/Research/"
    "cursor/h3-anal-stories-f112/minimaxh3/h3_lora_studio.py"
)

_IDLE = (
    "ANAL_HOLE_IDLE_LINE = (\n"
    '    "ANAL HOLE LOCK: Unused pussy stays shut, not spread, not gaping, not entered. "\n'
    '    "WHITE goo comes OUT OF THE ANUS only. Semen does not come out of the vagina. "\n'
    '    "Not a vaginal creampie."\n'
    ")\n"
)

_PREP_BLOCK = _IDLE + (
    'PREP_MARK = "ANAL PREP:"\n'
    "ANAL_PREP_LINE = (\n"
    '    "ANAL PREP: After the written act, BOTH women settle the next anal pose together. "\n'
    '    "Receiver takes the accepting pose written for the coming insertion. "\n'
    '    "Giver aligns hips behind or between, both hands on the waist, never on the hole, never on the shaft. "\n'
    '    "The erect 20cm tip stays a hand\'s width from the anus, not touching the hole, NOT in. "\n'
    '    "Unused pussy stays shut. No vaginal. No thumb. No fingers in the anus. "\n'
    '    "No extra walk. No solo heat. Do not start insertion in this prep beat."\n'
    ")\n"
    "\n"
    "def clip_is_anal_insert(prompt: str, situation: str = \"\") -> bool:\n"
    "    raw = str(prompt or \"\")\n"
    "    if PACO_MARK in raw or \"Already in. Piston\" in raw:\n"
    "        return False\n"
    "    if \"INSERTION ON CAMERA\" in raw:\n"
    "        return True\n"
    "    sit = str(situation or \"\").strip()\n"
    "    return sit in SEX_ANAL_SITUATIONS and bool(_ANAL_IN_RE.search(raw))\n"
    "\n"
    "\n"
    "def lock_anal_prep(\n"
    "    text: str,\n"
    "    *,\n"
    "    next_is_insert: bool = False,\n"
    "    same_clip_insert: bool = False,\n"
    ") -> str:\n"
    "    raw = str(text or \"\")\n"
    "    if not raw:\n"
    "        return raw\n"
    "    if PREP_MARK in raw:\n"
    "        return raw\n"
    "    if same_clip_insert or next_is_insert:\n"
    "        return _inject_before_soundscape(raw, ANAL_PREP_LINE)\n"
    "    return raw\n"
    "\n"
)

_OLD_LEFTOVER = (
    "    if TALK_THEN_INSERT_MARK in raw or KISS_THEN_INSERT_MARK in raw:\n"
    "        return (\n"
    '            "After the last unique quoted line: the written remaining beat first "\n'
    '            "(kiss / fondle / pose if written), then INSERTION ON CAMERA into the anus "\n'
    '            "to the BASE. Both wrecked-ecstatic, loud moans, a little drool. No climax. "\n'
    '            "Mouths stay closed except the act. No more quoted speech. No replay. Do not freeze."\n'
    "        )\n"
)

_NEW_LEFTOVER = (
    "    if TALK_THEN_INSERT_MARK in raw or KISS_THEN_INSERT_MARK in raw:\n"
    "        return (\n"
    '            "After the last unique quoted line: kiss or fondle if written, then ANAL PREP "\n'
    '            "(both settle the accepting pose, giver hips aligned, hands on the waist, "\n'
    '            "20cm tip a hand\'s width from the anus, NOT in), then last seconds "\n'
    '            "INSERTION ON CAMERA into the anus to the BASE. Both wrecked-ecstatic, "\n'
    '            "loud moans, a little drool. No climax. Mouths stay closed except the act. "\n'
    '            "No more quoted speech. No replay. Do not freeze."\n'
    "        )\n"
    "    if PREP_MARK in raw and \"INSERTION ON CAMERA\" not in raw:\n"
    "        return (\n"
    '            "ANAL PREP: both settle the next anal pose together. Receiver accepting pose. "\n'
    '            "Giver hips aligned, hands on the waist. 20cm tip a hand\'s width from the anus, "\n'
    '            "not touching, NOT in. Unused pussy shut. No entry. No extra walk. "\n'
    '            "No more quoted speech. No replay. Do not freeze."\n'
    "        )\n"
)

_OLD_ACT = (
    "    if (sit in ACT_SITUATIONS and not talks_then_insert(text)) or not lines:\n"
    "        return (\n"
    '            f"TIMELINE: 0.0-{dur:.1f}s one unbroken take. The written beat fills the whole take. "\n'
    '            "No quoted speech. No lip-sync words. No replay. Do not freeze."\n'
    "        )\n"
)

_NEW_ACT = (
    "    if PREP_MARK in text and \"INSERTION ON CAMERA\" not in text:\n"
    "        prep_start = max(dur - 4.0, dur * 0.6)\n"
    "        return (\n"
    '            f"TIMELINE: 0.0-{prep_start:.1f}s the written act. "\n'
    '            f"{prep_start:.1f}-{dur:.1f}s ANAL PREP: both settle the next pose, "\n'
    '            "20cm tip a hand\'s width from the anus, NOT in. No entry. "\n'
    '            "No quoted speech. No lip-sync words. No replay. Do not freeze."\n'
    "        )\n"
    + _OLD_ACT
)

_OLD_PREP = (
    "    raw_prompt = lock_anal_hole(\n"
    "        raw_prompt,\n"
    '        situation=str(clip.get("situation") or situation),\n'
    "        prev_situation=prev_situation,\n"
    "    )\n"
    "    raw_prompt = lock_pleasure_voice_and_wait(raw_prompt, situation=situation)\n"
)

_NEW_PREP = (
    "    raw_prompt = lock_anal_hole(\n"
    "        raw_prompt,\n"
    '        situation=str(clip.get("situation") or situation),\n'
    "        prev_situation=prev_situation,\n"
    "    )\n"
    "    nxt = clips[index + 1] if index + 1 < len(clips) else {}\n"
    "    next_is_insert = clip_is_anal_insert(str(nxt.get(\"prompt\") or \"\"), str(nxt.get(\"situation\") or \"\"))\n"
    "    same_clip_insert = clip_is_anal_insert(raw_prompt, situation) and (\n"
    "        TALK_THEN_INSERT_MARK in raw_prompt or KISS_THEN_INSERT_MARK in raw_prompt or talks_then_insert(raw_prompt)\n"
    "    )\n"
    "    raw_prompt = lock_anal_prep(\n"
    "        raw_prompt,\n"
    "        next_is_insert=next_is_insert and not clip_is_anal_insert(raw_prompt, situation),\n"
    "        same_clip_insert=same_clip_insert,\n"
    "    )\n"
    "    raw_prompt = lock_pleasure_voice_and_wait(raw_prompt, situation=situation)\n"
)


def _apply_anal_prep_overlay(src: str) -> str:
    src = src.replace("h3-20260913-anal-9", "h3-20260913-anal-10")
    if "ANAL_PREP_LINE" not in src:
        if _IDLE not in src:
            raise RuntimeError("base helper missing ANAL_HOLE_IDLE_LINE")
        src = src.replace(_IDLE, _PREP_BLOCK, 1)
    src = src.replace(_OLD_LEFTOVER, _NEW_LEFTOVER, 1)
    src = src.replace(_OLD_ACT, _NEW_ACT, 1)
    src = src.replace(_OLD_PREP, _NEW_PREP, 1)
    return src


_src = urllib.request.urlopen(_BASE_URL, timeout=60).read().decode("utf-8")
if _src.strip() == "PLACEHOLDER":
    raise RuntimeError("minimaxh3 helper is also placeholder; abort")
_src = _apply_anal_prep_overlay(_src)
exec(_src, globals())
STUDIO_REV = "h3-20260913-anal-10"
FETCH_REV = "h3-20260913-anal-10"
