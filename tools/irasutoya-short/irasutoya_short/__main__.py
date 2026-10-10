"""使い方: python -m irasutoya_short make ネタ.json --out out.mp4"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from irasutoya_short.pipeline import make, revise
from irasutoya_short.scriptgen import auto_scripts, grok_complete
from irasutoya_short.tts import runtime_ready


def _shots(path: str) -> list[Path]:
    if not path:
        return []
    folder = Path(path)
    if folder.is_file():
        return [folder]
    files = []
    for pattern in ("*.png", "*.jpg", "*.jpeg", "*.webp"):
        files.extend(sorted(folder.glob(pattern)))
    return files[:10]


def main() -> None:
    parser = argparse.ArgumentParser(description="いらすとやスカッとショートを作る")
    sub = parser.add_subparsers(dest="cmd", required=True)

    make_p = sub.add_parser("make", help="箇条書きとオチから1本作る")
    make_p.add_argument("brief", type=Path)
    make_p.add_argument("--work", type=Path, default=Path("work"))
    make_p.add_argument("--out", type=Path, required=True)
    make_p.add_argument("--screenshots", default="", help="参考動画のスクショが入ったフォルダ（5〜10枚）")
    make_p.add_argument("--no-bgm", action="store_true")

    rev_p = sub.add_parser("revise", help="口語の指示で作り直す")
    rev_p.add_argument("work", type=Path)
    rev_p.add_argument("note")
    rev_p.add_argument("--out", type=Path, required=True)

    sub.add_parser("doctor", help="VOICEVOX があるか確認する")

    script_p = sub.add_parser("script", help="種から台本JSONを2枚書く。動画は作らない")
    script_p.add_argument("seed")
    script_p.add_argument("--out", type=Path, required=True)

    args = parser.parse_args()
    if args.cmd == "doctor":
        print("voicevox:", "ok" if runtime_ready() else "missing")
        return
    if args.cmd == "script":
        scripts = auto_scripts(args.seed, grok_complete)
        args.out.mkdir(parents=True, exist_ok=True)
        irasu = args.out / "irasutoya.json"
        h3 = args.out / "h3.json"
        irasu.write_text(json.dumps(scripts["irasutoya"], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        h3.write_text(json.dumps(scripts["h3"], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(irasu)
        print(h3)
        return
    if args.cmd == "make":
        summary = make(args.brief, args.work, args.out, _shots(args.screenshots), bgm=not args.no_bgm)
    else:
        summary = revise(args.work, args.note, args.out)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
