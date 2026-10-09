"""The shot sheet copies structure and leaves person, animal, line, and place empty."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

import affi_structure as structure


def test_sheet_locks_twenty_shots_and_leaves_slots_empty() -> None:
    pack = structure.load()
    prep = structure.prepare()
    assert prep["shots"] == 20
    assert prep["captions"] == 33
    assert prep["duration_s"] == 71.552
    assert len(pack["cuts_s"]) == 19
    assert prep["generates_video"] is False
    assert prep["posts"] is False
    assert pack["narration"].startswith("独立した語りは無い")
    assert all(row["line"] == "入力" for row in structure.captions_of(pack))
    assert all(row["line"] == "入力" for row in structure.narration_of(pack))
    assert "人は入力のまま" in prep["blocked"]
    assert "場所は入力のまま" in prep["blocked"]
    assert sum(1 for reason in prep["blocked"] if reason.endswith("セリフは入力のまま")) == 33


def test_prompt_keeps_the_evidence_lines_out() -> None:
    pack = structure.load()
    text = structure.prompt_text(pack)
    for row in pack["captions"]:
        source = row["source_line"]
        if len(source) >= 4:
            assert source not in text
    for shot in pack["shots"]:
        assert shot["source_seen"] not in text
    assert "おい、そこのデブ" not in text
    assert "入力" in text
    sheet = structure.render_markdown(pack)
    assert "おい、そこのデブ" in sheet
    assert "証拠:" in sheet
    assert structure.SHEET_PATH.read_text(encoding="utf-8") == sheet


def test_fill_changes_only_the_four_slots() -> None:
    pack = structure.load()
    before = [(shot["id"], shot["start_s"], shot["end_s"], shot["camera"]) for shot in pack["shots"]]
    lines = {row["id"]: f"文{index}" for index, row in enumerate(pack["captions"], start=1)}
    filled = structure.fill(
        pack,
        person="大人の人",
        animals={"guest": "小さい鳥", "retort": "太い動物", "polite": "細い動物"},
        place="別の部屋",
        lines=lines,
    )
    after = [(shot["id"], shot["start_s"], shot["end_s"], shot["camera"]) for shot in filled["shots"]]
    assert after == before
    assert structure.blocked(filled) == []
    text = structure.prompt_text(filled)
    assert "文1" in text
    assert "別の部屋" in text
    assert "太い動物" in text
    assert "おい、そこのデブ" not in text
    with pytest.raises(ValueError, match="元のセリフは入れない"):
        structure.fill(pack, lines={"c01": "おい、そこのデブ"})
