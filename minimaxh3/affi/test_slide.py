"""The Orbis slide draft is text only. No Imagine call and no ffmpeg run."""

from __future__ import annotations

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


def test_five_images_cover_the_fixed_shape() -> None:
    assert len(SLIDES) == 5
    assert [item["role"] for item in SLIDES] == ["表紙", "問題提起", "本文", "本文", "締め"]
    assert "画像5枚" in ASSIGNMENT
    assert "8枚には分けない" in ASSIGNMENT
    for item in SLIDES:
        assert len(item["caption"]) <= 2
        assert "9:16" in item["imagine"]
        assert "no people" in item["imagine"].lower()


def test_answer_is_only_at_the_end_of_the_post() -> None:
    screen = on_screen_text()
    assert "無香料" not in screen
    assert "オルビス" not in screen
    assert POST.startswith("アフィリエイト広告を含みます #PR")
    assert "#PR" in POST.splitlines()[0]
    assert "AIで生成" in POST
    assert POST.strip().endswith(ANSWER)
    assert "プロフィール" in SLIDES[-1]["caption"][1]
    assert "5つ目: 不明" in POST


def test_draft_files_match_and_are_not_scheduled() -> None:
    assert score()["verdict"] == "直す"
    assert score()["schedule"] is False
    assert DRAFT.read_text(encoding="utf-8") == render_draft()
    assert CAPTIONS.read_text(encoding="utf-8") == srt()
    script = SCRIPT.read_text(encoding="utf-8")
    assert "1080:1920" in script
    assert "-t 3.0" in script
    assert "bgm/slide.m4a" in script
    assert "-an" in script
    for word in ("治る", "必ず", "稼", "美白", "シミ", "LINE"):
        assert word not in POST
        assert word not in on_screen_text()
