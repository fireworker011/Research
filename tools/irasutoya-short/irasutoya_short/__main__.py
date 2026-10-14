"""使い方: python -m irasutoya_short make ネタ.json --out out.mp4"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from irasutoya_short.picture_first import make_picture_first
from irasutoya_short.pipeline import make, revise
from irasutoya_short.render import bundled_font
from irasutoya_short.templates import describe_templates
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
    make_p.add_argument("--template", default="", help="sukatto / before_after / aruaru / ranking / qa")
    make_p.add_argument("--no-bgm", action="store_true")

    pic_p = sub.add_parser("picture-first", help="口パクの絵を先に固定し、声をあとから合わせる")
    pic_p.add_argument("brief", type=Path)
    pic_p.add_argument("--work", type=Path, default=Path("work"))
    pic_p.add_argument("--out", type=Path, required=True)
    pic_p.add_argument("--screenshots", default="", help="参考動画のスクショが入ったフォルダ（5〜10枚）")
    pic_p.add_argument("--template", default="", help="sukatto / before_after / aruaru / ranking / qa")
    pic_p.add_argument("--no-bgm", action="store_true")

    rev_p = sub.add_parser("revise", help="口語の指示で作り直す")
    rev_p.add_argument("work", type=Path)
    rev_p.add_argument("note")
    rev_p.add_argument("--out", type=Path, required=True)

    sub.add_parser("doctor", help="VOICEVOX と ffmpeg とフォントがあるか確認する")
    sub.add_parser("templates", help="編集テンプレの一覧")

    args = parser.parse_args()
    if args.cmd == "doctor":
        font = bundled_font()
        print("voicevox:", "ok" if runtime_ready() else "missing")
        print("ffmpeg:", "ok" if shutil.which("ffmpeg") else "missing")
        print("font:", font or "missing")
        return
    if args.cmd == "templates":
        print(json.dumps(describe_templates(), ensure_ascii=False, indent=2))
        return
    if args.cmd == "make":
        summary = make(
            args.brief,
            args.work,
            args.out,
            _shots(args.screenshots),
            bgm=not args.no_bgm,
            template=args.template,
        )
    elif args.cmd == "picture-first":
        summary = make_picture_first(
            args.brief,
            args.work,
            args.out,
            _shots(args.screenshots),
            bgm=not args.no_bgm,
            template=args.template,
        )
    else:
        summary = revise(args.work, args.note, args.out)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
