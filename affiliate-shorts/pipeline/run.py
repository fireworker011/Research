#!/usr/bin/env python3
"""会社員の金メモを1本出す。投稿はしない。

    python3 affiliate-shorts/pipeline/run.py --script affiliate-shorts/pipeline/scripts/50-kinmemo-file.json
    python3 affiliate-shorts/pipeline/run.py --theme "クリアファイルの奥の硬貨" --id 50-kinmemo-file
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

PIPELINE_DIR = Path(__file__).resolve().parent
REPO = PIPELINE_DIR.parents[1]
TOOL = REPO / "tools" / "irasutoya-short"
if str(TOOL) not in sys.path:
    sys.path.insert(0, str(TOOL))
if str(PIPELINE_DIR) not in sys.path:
    sys.path.insert(0, str(PIPELINE_DIR))

from assemble import CACHE, build, ensure_asset  # noqa: E402
from irasutoya_short.sprites import load_rgba  # noqa: E402
from irasutoya_short.tts import Speaker  # noqa: E402
from qa_gate import evaluate, mouth_self_test, pure_self_test, write_report  # noqa: E402
from scripting import (  # noqa: E402
    CHANNEL,
    existing_titles,
    load_index,
    load_script,
    resolve,
    script_from_theme,
    validate_script,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="金メモのショートを1本書き、レビューフォルダに置く")
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--script", type=Path, help="台本JSON")
    source.add_argument("--theme", help="テーマ一文。中身は型で埋める")
    parser.add_argument("--id", default="", help="--theme のときのフォルダ名")
    parser.add_argument("--work", type=Path, default=None)
    parser.add_argument("--review", type=Path, default=None)
    parser.add_argument("--self-test", action="store_true", help="口と字幕の帯の検査だけ行う")
    return parser


def _dedupe_credits(script: dict) -> list[dict]:
    seen: set[str] = set()
    rows = []
    for line in script["lines"]:
        character = line.get("character") or ""
        url = line.get("source_url") or ""
        if not character or not url or character in seen:
            continue
        seen.add(character)
        rows.append({
            "id": character,
            "emotion": line.get("emotion") or "",
            "source_url": url,
        })
    return rows


def write_credits(path: Path, script: dict) -> None:
    payload = {
        "voices": list(script.get("credits") or []),
        "images": _dedupe_credits(script),
        "note": "いらすとやはクレジット表記不要。出典URLはレビュー用。動画の中にURLは出していない。効果音とBGMは合成したオリジナル。",
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_upload(path: Path, script: dict) -> None:
    voices = "\n".join(script.get("credits") or [])
    text = f"""# 投稿用

## タイトル

{script["title"]}

## 説明

{script["title"]}

#PR
フィクションです。体験談でも、収益の保証でもありません。
テーマ: {script["theme"]}

{voices}

（リンクをプロフィールに置く前に出すときは、`#PR` の行とタグの #PR を外す。URL はどこにも書かない。イラストの出典URLは credits.json。）

## タグ

金メモ 会社員 硬貨 shorts

## 事実の根拠

{script["theme"]}の寸劇。金額は無い。

## 投稿

しない。
"""
    path.write_text(text, encoding="utf-8")


def _run_self_test() -> None:
    pure_self_test()
    index = load_index()
    asset = index["hero_trouble"]
    path = ensure_asset(asset, CACHE)
    mouth_self_test(load_rgba(path))
    print("self-test pass")


def _load(args: argparse.Namespace) -> dict:
    index = load_index()
    titles = existing_titles()
    if args.script:
        script = load_script(args.script)
    else:
        slug = args.id.strip() or "theme-run"
        script = script_from_theme(args.theme, slug)
    validate_script(script, index, titles)
    if script.get("channel") != CHANNEL:
        raise ValueError(f"チャンネルは {CHANNEL} です。")
    return resolve(script, index)


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.self_test and not args.script and not args.theme:
        _run_self_test()
        return 0
    if not args.script and not args.theme:
        raise SystemExit("台本JSONかテーマが要ります。")
    script = _load(args)
    slug = str(script["id"])
    work = args.work or Path(f"/tmp/kanememo-pipeline/{slug}")
    review = args.review or (PIPELINE_DIR / "review" / slug)
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)
    review.mkdir(parents=True, exist_ok=True)
    _run_self_test()
    speaker = Speaker()
    built = build(script, work, speaker)
    mp4 = built["mp4"]
    report = evaluate(built["plan"], mp4 if mp4 is not None and Path(mp4).is_file() else None)
    write_report(review / "QA.md", script, report)
    (review / "QA.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    write_credits(review / "credits.json", script)
    write_upload(review / "UPLOAD.md", script)
    public = json.loads(json.dumps(script))
    for line in public["lines"]:
        line.pop("voice_path", None)
    (review / "script.json").write_text(json.dumps(public, ensure_ascii=False, indent=2), encoding="utf-8")
    out_mp4 = review / "out.mp4"
    sheet = review / "contact-sheet.jpg"
    if out_mp4.exists():
        out_mp4.unlink()
    if sheet.exists():
        sheet.unlink()
    if not report["pass"] or mp4 is None:
        print(json.dumps({"pass": False, "qa": str(review / "QA.md")}, ensure_ascii=False))
        return 1
    shutil.copy2(mp4, out_mp4)
    shutil.copy2(built["sheet"], sheet)
    print(json.dumps({
        "pass": True,
        "out": str(out_mp4),
        "duration_sec": report["duration_sec"],
        "qa": str(review / "QA.md"),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
