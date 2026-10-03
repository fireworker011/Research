"""The Orbis slide draft is text only. No Imagine call and no production mp4."""

from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from minimaxh3.affi.slide import (  # noqa: E402
    ANSWER,
    ASSIGNMENT,
    POST,
    SLIDES,
    on_screen_text,
    render_draft,
    score,
    srt,
)

DRAFT = ROOT / "minimaxh3" / "affi" / "slides" / "orbis-dot-01" / "draft.md"
SCRIPT = ROOT / "minimaxh3" / "affi" / "slides" / "orbis-dot-01" / "build_slide.sh"
CAPTIONS = ROOT / "minimaxh3" / "affi" / "slides" / "orbis-dot-01" / "captions.srt"
CUTS = ROOT / "minimaxh3" / "affi" / "slides" / "orbis-dot-01" / "cuts.csv"


def test_eight_images_cover_cover_to_close() -> None:
    assert len(SLIDES) == 8
    assert [item["role"] for item in SLIDES] == [
        "表紙",
        "問題提起",
        "本文",
        "本文",
        "本文",
        "本文",
        "本文",
        "締め",
    ]
    assert "8枚" in ASSIGNMENT
    assert "表紙" in ASSIGNMENT and "締め" in ASSIGNMENT
    for item in SLIDES:
        assert len(item["caption"]) <= 2
        assert item["caption"]
        assert "9:16" in item["imagine"]
        assert "sakura-ref.jpg" in item["imagine"]
        assert "no other people" in item["imagine"].lower()
        assert "no hands" in item["imagine"].lower()
        assert "no new face" in item["imagine"].lower()


def test_answer_is_only_at_the_end_of_the_post() -> None:
    screen = on_screen_text()
    assert "無香料" not in screen
    assert "オルビス" not in screen
    assert "無油分" not in screen
    assert "無油分" not in POST
    assert POST.startswith("アフィリエイト広告を含みます #PR")
    assert "#PR" in POST.splitlines()[0]
    assert "AIで生成" in POST
    assert POST.strip().endswith(ANSWER)
    assert POST.count("無香料") == 1
    assert "プロフィール" in SLIDES[-1]["caption"][1]
    assert "買う前" in "".join(SLIDES[0]["caption"])
    assert "100円硬貨" in POST
    assert "パール1～2粒" in POST
    assert "5つ目: 不明" not in POST


def test_draft_files_match_and_are_not_scheduled() -> None:
    assert score()["verdict"] == "直す"
    assert score()["schedule"] is False
    assert "5つ目が不明" not in score()["reason"]
    assert DRAFT.read_text(encoding="utf-8") == render_draft()
    assert CAPTIONS.read_text(encoding="utf-8") == srt()
    script = SCRIPT.read_text(encoding="utf-8")
    assert "cutlist render" in script
    assert "--purpose slide" in script
    assert "cuts.csv" in script
    assert "bgm/slide.m4a" in script
    assert "zoompan" not in script
    with CUTS.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert [row["index"] for row in rows] == [str(i) for i in range(1, 9)]
    assert all(row["subtitle"].strip() for row in rows)
    assert rows[0]["src"] == "images/01.png"
    assert rows[-1]["src"] == "images/08.png"
    assert rows[0]["in"] == "0.0" and rows[0]["out"] == "3.0"
    for word in ("治る", "必ず", "稼", "美白", "シミ", "LINE"):
        assert word not in POST
        assert word not in on_screen_text()
