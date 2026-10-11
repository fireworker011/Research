"""使い方: python -m irasutoya_short make ネタ.json --out out.mp4"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from irasutoya_short.imagine import write_bot_order
from irasutoya_short.pipeline import make, revise
from irasutoya_short.scriptgen import generate_script
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
    make_p.add_argument("--images", type=Path, default=None, help="Grok Imagine が返した scene_01.png 以降")
    make_p.add_argument("--no-bgm", action="store_true")

    img_p = sub.add_parser("imagine", help="Imagine ボットへ渡す Grok Imagine 指示を書く")
    img_p.add_argument("brief", type=Path)
    img_p.add_argument("--out", type=Path, required=True)

    rev_p = sub.add_parser("revise", help="口語の指示で作り直す")
    rev_p.add_argument("work", type=Path)
    rev_p.add_argument("note")
    rev_p.add_argument("--out", type=Path, required=True)

    sub.add_parser("doctor", help="VOICEVOX があるか確認する")

    args = parser.parse_args()
    if args.cmd == "doctor":
        print("voicevox:", "ok" if runtime_ready() else "missing")
        return
    if args.cmd == "imagine":
        brief = json.loads(args.brief.read_text(encoding="utf-8"))
        script = generate_script(brief)
        path = write_bot_order(script["title"], script["scenes"], args.out)
        print(path.read_text(encoding="utf-8"))
        return
    if args.cmd == "make":
        summary = make(
            args.brief,
            args.work,
            args.out,
            _shots(args.screenshots),
            bgm=not args.no_bgm,
            images=args.images,
        )
    else:
        summary = revise(args.work, args.note, args.out)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
