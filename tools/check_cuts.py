#!/usr/bin/env python3
"""cuts-for-pc.md を見る。mp4 も音声も要らない。

使い方: python tools/check_cuts.py <cuts-for-pc.md> <pet|kane|both>
"""

from __future__ import annotations

import re
import sys

CAT = "黒い短毛で、目は黄色、耳は立っている。"
AFFILIATE = "アフィリエイト広告を含みます"


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: check_cuts.py <cuts-for-pc.md> <pet|kane|both>", file=sys.stderr)
        return 2
    path, lane = sys.argv[1], sys.argv[2]
    if lane not in ("pet", "kane", "both"):
        print("lane は pet か kane か both", file=sys.stderr)
        return 2
    text = open(path, encoding="utf-8").read()
    fail = 0

    def say(ok: bool, detail: str) -> None:
        nonlocal fail
        if not ok:
            fail = 1
        print(f"{'PASS' if ok else 'FAIL'}\t{detail}")

    say("mp4は書き出していない" in text, "mp4は書き出していない")
    say("40px" in text, "文字の高さは40px以上")
    durations = [float(item) for item in re.findall(r"尺[:：]\s*(\d+\.\d+)", text)]
    say(bool(durations) and all(8.0 <= item <= 10.5 for item in durations), "尺が8.0〜10.5秒")
    too_long = [f"{float(a):.3f}-{float(b):.3f}" for a, b in re.findall(r"(\d+\.\d+)\s*[-–]\s*(\d+\.\d+)", text) if float(b) > 10.5 + 0.001]
    say(not too_long, "カットは10.5秒以内" if not too_long else "10.5秒を超える " + ",".join(too_long))
    say("プロンプト" in text, "プロンプトがある")
    say("等倍" in text, "声は等倍")
    sections = re.split(r"(?m)^## ", text)
    saw_pet = saw_kane = False
    for section in sections:
        head = section.split("\n", 1)[0]
        if "金メモ" in head:
            saw_kane = True
            say("#PR" not in section and AFFILIATE not in section, head + " にPR表記なし")
        if "ペット" in head:
            saw_pet = True
            say(CAT in section, head + " の猫の描写")
            say("広告 #PR" in section, head + " の最後の広告")
            say("切り抜き・白いふちどり・合成はしない" in section, head + " の切り抜き禁止")
            say("しっぽは体につながった1本" in section, head + " のしっぽ")
            say(not ("袋" in section and "器" in section and "食べ" in section), head + " に食事カットが無い")
    if lane in ("pet", "both"):
        say(saw_pet, "ペットの節がある")
    if lane in ("kane", "both"):
        say(saw_kane, "金メモの節がある")
    return fail


if __name__ == "__main__":
    sys.exit(main())
