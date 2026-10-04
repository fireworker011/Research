"""Reproduction templates stay on the schema, and A/B changes one slot."""

from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

import affi_reference as ref


def test_four_templates_keep_unknowns() -> None:
    items = ref.templates()
    assert {item["handle"] for item in items} == {
        "the.care.logic",
        "nuts0629",
        "junjun_ranran",
        "yako.shiawasekon",
    }
    blob = "\n".join(Path(path).read_text(encoding="utf-8") for path in (ROOT / "reference-accounts" / "templates").glob("*.yaml"))
    assert "推定" in blob
    assert "不明" in blob
    assert "見守りカメラ映像ではない" in blob


def test_sheet_does_not_copy_source_lines() -> None:
    item = ref.template_for("junjun_ranran")
    plan = ref.sheet(item, "夜の窓", ["こっちを見ないで", "ブラシは私がやる"])
    text = ref.render_markdown(plan, "試し")
    assert "おい、そこのデブ" not in text
    assert "こっちを見ないで" in text
    assert "元のアカウントの顔" in text


def test_ab_changes_one_variable() -> None:
    left, right = ref.ab_sheets("H1-1", "髪の悩み", ["困っている", "こうする", "よくなった"])
    assert ref.changed_keys(left, right) == {"opening"}
    assert left["scenes"] == right["scenes"]
    before = ref.hypothesis("H2-3")
    assert before["comparison"] == "before_after"
    a, b = ref.ab_sheets("H2-3", "同じ犬")
    assert ref.changed_keys(a, b) == {"cadence"}
    assert a["scenes"] == b["scenes"]


def test_judge_does_not_treat_blanks_as_zero(tmp_path: Path) -> None:
    path = tmp_path / "results.csv"
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["hypothesis_id", "variant", "views", "two_sec_hold_pct", "saves", "shares", "diagnosis_signups", "follower_gain", "avg_watch_sec"],
        )
        writer.writeheader()
        for index in range(5):
            writer.writerow({"hypothesis_id": "H1-1", "variant": "A", "views": 100 + index, "two_sec_hold_pct": ""})
            writer.writerow({"hypothesis_id": "H1-1", "variant": "B", "views": 40, "two_sec_hold_pct": 20})
        writer.writerow({"hypothesis_id": "H3-2", "variant": "A", "views": 10, "two_sec_hold_pct": ""})
    rows = {item["id"]: item for item in ref.judge(path)}
    assert rows["H1-1"]["verdict"] == "未入力"
    assert rows["H3-2"]["verdict"] == "本数不足"
    assert "0" not in rows["H1-1"]["detail"] or "未入力" in rows["H1-1"]["detail"]


def test_judge_names_a_winner_from_entered_numbers(tmp_path: Path) -> None:
    path = tmp_path / "results.csv"
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["hypothesis_id", "variant", "views", "two_sec_hold_pct"])
        writer.writeheader()
        for views, hold in ((100, 40), (110, 42), (90, 41), (120, 39), (105, 43)):
            writer.writerow({"hypothesis_id": "H1-1", "variant": "A", "views": views, "two_sec_hold_pct": hold})
        for views, hold in ((40, 20), (42, 18), (38, 22), (41, 19), (39, 21)):
            writer.writerow({"hypothesis_id": "H1-1", "variant": "B", "views": views, "two_sec_hold_pct": hold})
    row = next(item for item in ref.judge(path) if item["id"] == "H1-1")
    assert row["ready"] is True
    assert row["verdict"] == "Aが基準を満たした"


def test_feasibility_sheets_exist() -> None:
    text = "\n".join(ref.feasibility_sheet(fid) for fid in ("F1", "F2", "F3"))
    assert "口パク" in text
    assert "同じ顔" in text
    assert "ダンス" in text
    assert "Kling" in text
