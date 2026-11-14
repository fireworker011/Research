#!/usr/bin/env python3
"""8-char LCS overlap check: jobs-v3 vs jobs/ (14階). Exit 1 if clean LCS >= 8."""
from __future__ import annotations
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXED = ["Audible", "オーディブル", "DAY 2", "DAY 3", "DAY", "PR", "フォロー", "コメント"]

def texts_from_job(job):
    out = []
    for s in job["segments"]:
        out.append(s.get("subtitle") or "")
        tc = s.get("top_card") or {}
        if tc:
            out.append(f"{tc.get('badge','')} / {tc.get('title','')}")
        sp = s.get("scene_params") or {}
        for k in ("note_text", "note_text_white", "note_text_red"):
            if sp.get(k):
                out.append(sp[k])
    for key in ("choice_card", "day_end_card"):
        card = job.get(key) or {}
        for f in ("question", "narration", "subtext", "title", "subtitle", "status", "button_text"):
            if card.get(f):
                out.append(card[f])
        for side in ("left_option", "right_option"):
            if card.get(side) and card[side].get("text"):
                out.append(card[side]["text"])
    promo = job.get("promo_outro") or {}
    if promo.get("enabled"):
        for f in ("headline", "narration", "sub_copy", "cta_button_text", "app_name"):
            if promo.get(f):
                out.append(promo[f].replace("\n", " / "))
        for st in promo.get("steps") or []:
            out.append(st.get("text") or "")
    return [t for t in out if t.strip()]

def strip_fixed(s: str) -> str:
    t = s
    for f in FIXED:
        t = t.replace(f, "")
    return t

def lcs_len(a: str, b: str) -> int:
    best = 0
    prev = [0] * (len(b) + 1)
    for ca in a:
        cur = [0] * (len(b) + 1)
        for j, cb in enumerate(b, 1):
            if ca == cb:
                cur[j] = prev[j - 1] + 1
                if cur[j] > best:
                    best = cur[j]
        prev = cur
    return best

def main() -> int:
    old = []
    for name in ("episode_day2.json", "episode_day3.json"):
        old.extend(texts_from_job(json.loads((ROOT / "jobs" / name).read_text(encoding="utf-8"))))
    max_clean = 0
    for name in ("episode_day2.json", "episode_day3.json"):
        job = json.loads((ROOT / "jobs-v3" / name).read_text(encoding="utf-8"))
        for t in texts_from_job(job):
            for ot in old:
                max_clean = max(max_clean, lcs_len(strip_fixed(t), strip_fixed(ot)))
    print(f"max_clean_lcs={max_clean}")
    if max_clean >= 8:
        print("FAIL")
        return 1
    print("PASS")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
