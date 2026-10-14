#!/usr/bin/env python3
"""ショートを1本出す。チャンネルの名前と見た目は channels/<id>.yaml。投稿はしない。

    python3 affiliate-shorts/pipeline/run.py --script affiliate-shorts/pipeline/scripts/50-clearfile-coin.json
    python3 affiliate-shorts/pipeline/run.py --theme "クリアファイルの奥の硬貨" --id 50-clearfile-coin --channel draft
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
from channels import assert_outputs_clear, load_channel, render_upload  # noqa: E402
from irasutoya_short.sprites import load_rgba  # noqa: E402
from irasutoya_short.tts import Speaker  # noqa: E402
from qa_gate import evaluate, mouth_self_test, pure_self_test, write_report  # noqa: E402
from scripting import (  # noqa: E402
    existing_titles,
    load_index,
    load_script,
    resolve,
    script_from_theme,
    validate_script,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="ショートを1本書き、レビューフォルダに置く")
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--script", type=Path, help="台本JSON")
    source.add_argument("--theme", help="テーマ一文。中身は型で埋める")
    parser.add_argument("--id", default="", help="--theme のときのフォルダ名")
    parser.add_argument("--channel", default="", help="channels/<id>.yaml。省略すると台本の channel")
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


def write_credits(path: Path, script: dict, channel: dict) -> None:
    payload = {
        "channel": channel["id"],
        "channel_name": str(channel.get("name") or ""),
        "genre": str(channel.get("genre") or ""),
        "voices": list(script.get("credits") or []),
        "images": _dedupe_credits(script),
        "note": channel["credits"]["note"],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _run_self_test() -> None:
    pure_self_test()
    index = load_index()
    asset = index["hero_trouble"]
    path = ensure_asset(asset, CACHE)
    mouth_self_test(load_rgba(path))
    print("self-test pass")


def _load(args: argparse.Namespace) -> tuple[dict, dict]:
    index = load_index()
    titles = existing_titles()
    if args.script:
        script = load_script(args.script)
    else:
        slug = args.id.strip() or "theme-run"
        channel_id = args.channel.strip() or "draft"
        script = script_from_theme(args.theme, slug, channel_id)
    channel_id = args.channel.strip() or str(script.get("channel") or "")
    if args.channel.strip() and script.get("channel") and args.channel.strip() != script.get("channel"):
        raise ValueError("台本の channel と --channel が違います。")
    channel = load_channel(channel_id)
    validate_script(script, index, titles, channel)
    return resolve(script, index, channel), channel


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.self_test and not args.script and not args.theme:
        _run_self_test()
        return 0
    if not args.script and not args.theme:
        raise SystemExit("台本JSONかテーマが要ります。")
    script, channel = _load(args)
    slug = str(script["id"])
    work = args.work or Path(f"/tmp/shorts-pipeline/{slug}")
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
    write_credits(review / "credits.json", script, channel)
    (review / "UPLOAD.md").write_text(render_upload(channel, script), encoding="utf-8")
    public = json.loads(json.dumps(script))
    for line in public["lines"]:
        line.pop("voice_path", None)
    (review / "script.json").write_text(json.dumps(public, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    assert_outputs_clear([
        review / "QA.md",
        review / "QA.json",
        review / "UPLOAD.md",
        review / "credits.json",
        review / "script.json",
    ])
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
