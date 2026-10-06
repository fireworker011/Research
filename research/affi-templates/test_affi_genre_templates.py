"""Counts, unknown exclusion, and reference rows for genre templates."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

import affi_genre_templates as agt

DATA = ROOT / "data" / "2026-10-03"
COLUMNS = [
    "platform",
    "genre",
    "bucket",
    "handle",
    "notes",
    "opening_type",
    "face_shown",
    "main_subject",
    "template_fixed",
    "duration_sec",
    "hashtag_count",
    "pr_label",
    "audio",
    "product_display",
    "feature_source",
    "first_frame_text",
    "opening_type_evidence",
    "median_views",
    "followers",
    "posts_last30_seen",
]


def row(**overrides: str) -> dict[str, str]:
    base = {column: "" for column in COLUMNS}
    base.update(genre="美容スキンケア", platform="TikTok", bucket=agt.GROWING, feature_source="推定（説明文）")
    base.update(overrides)
    return base


def test_unknown_values_leave_the_denominator() -> None:
    rows = [
        row(handle="a", opening_type="A商品名紹介"),
        row(handle="b", opening_type="A商品名紹介"),
        row(handle="c", opening_type="不明"),
        row(handle="d", opening_type=""),
        row(handle="e", bucket=agt.STRUGGLING, opening_type="不明"),
    ]
    built = agt.build_from_rows(rows, [], agt.Thresholds(), "test")
    choice = built.genres[0].choice("opening_type")
    assert choice.growing_n == 2
    assert choice.struggling_n == 0
    assert choice.confidence == "比較不能"


def test_confidence_thresholds_are_configurable() -> None:
    assert agt.confidence(10, 10, agt.Thresholds()) == "強い"
    assert agt.confidence(10, 3, agt.Thresholds()) == "弱い"
    assert agt.confidence(9, 9, agt.Thresholds()) == "弱い"
    assert agt.confidence(2, 16, agt.Thresholds()) == "比較不能"
    strict = agt.Thresholds(strong_min=20, compare_min=5)
    assert agt.confidence(10, 10, strict) == "弱い"
    assert agt.confidence(4, 20, strict) == "比較不能"


def test_product_display_splits_on_semicolon_and_drops_unknown_tokens() -> None:
    rows = [
        row(handle="a", product_display="使用・実演;価格表示"),
        row(handle="b", product_display="使用・実演;その他/不明"),
        row(handle="c", product_display="不明"),
        row(handle="d", product_display="その他/不明"),
        row(handle="e", bucket=agt.STRUGGLING, product_display="使用・実演"),
    ]
    prepared = [agt.prepared(item) for item in rows]
    counts, judged = agt._product_tally(prepared[:4])
    assert judged == 2
    assert counts["使用・実演"] == 2
    assert counts["価格表示"] == 1
    assert "その他/不明" not in counts
    struggle_counts, struggle_n = agt._product_tally(prepared[4:])
    assert struggle_n == 1
    assert struggle_counts["使用・実演"] == 1


def test_reference_accounts_are_excluded_from_counts() -> None:
    rows = [
        row(handle="kept", opening_type="その他"),
        row(handle="the.care.logic", notes="ユーザー参考アカウント。集計に入れない", opening_type="A商品名紹介", bucket="参考（区分外）"),
        row(handle="also-ref", notes="ユーザー参考アカウント", bucket=agt.GROWING, opening_type="B買う前の悩み・不一致"),
    ]
    analysis, references = agt.split_rows(rows)
    assert [item["handle"] for item in analysis] == ["kept"]
    assert len(references) == 2
    built = agt.build_from_rows(analysis, references, agt.Thresholds(), "test")
    assert built.n_accounts == 1
    assert built.n_reference == 2
    assert built.genres[0].n_growing == 1


def test_snapshot_matches_the_report_counts() -> None:
    built = agt.load_snapshot(DATA)
    assert built.n_accounts == 266
    assert built.n_reference == 4
    by_genre = {item.genre: item for item in built.genres}
    beauty = by_genre["美容スキンケア"]
    assert (beauty.n_growing, beauty.n_struggling) == (139, 30)
    assert beauty.account_confidence == "強い"
    assert beauty.basis == "比較"
    demo = next(gap for gap in beauty.gaps if gap.label == "商品の見せ方" and gap.value == "使用・実演")
    assert (demo.growing.m, demo.growing.n) == (19, 55)
    assert (demo.struggling.m, demo.struggling.n) == (11, 11)
    assert demo.gap_pt == -65
    face = beauty.choice("face_shown")
    assert face.choice == "あり"
    assert face.growing is not None and (face.growing.m, face.growing.n) == (54, 60)
    subject = beauty.choice("main_subject")
    assert subject.growing is not None and (subject.growing.m, subject.growing.n) == (55, 103)
    audio = next(gap for gap in beauty.gaps if gap.label == "音" and gap.value == "オリジナル")
    assert (audio.growing.m, audio.growing.n) == (19, 68)
    assert (audio.struggling.m, audio.struggling.n) == (9, 16)
    long = next(gap for gap in beauty.gaps if gap.label == "尺" and gap.value == "61秒以上")
    assert (long.growing.m, long.growing.n) == (21, 65)
    assert (long.struggling.m, long.struggling.n) == (2, 17)

    wedding = by_genre["婚活"]
    assert (wedding.n_growing, wedding.n_struggling) == (54, 12)
    original = next(gap for gap in wedding.gaps if gap.label == "音" and gap.value == "オリジナル")
    assert (original.struggling.m, original.struggling.n) == (4, 4)
    assert (original.growing.m, original.growing.n) == (14, 29)
    assert wedding.choice("face_shown").choice == "あり"
    assert wedding.choice("template_fixed").choice == "あり"

    camera = by_genre["見守りカメラ"]
    assert (camera.n_growing, camera.n_struggling) == (10, 3)
    assert camera.basis == "伸びてる群の傾向"
    assert camera.account_confidence == "弱い"
    assert camera.choice("main_subject").choice == "動物"

    food = by_genre["ドッグフード"]
    assert (food.n_growing, food.n_struggling) == (16, 2)
    assert food.account_confidence == "比較不能"
    assert food.basis == "伸びてる群の傾向"
    assert food.choice("opening_type").choice == "A商品名紹介"
    assert food.choice("opening_type").growing is not None
    assert (food.choice("opening_type").growing.m, food.choice("opening_type").growing.n) == (8, 15)
    assert food.choice("main_subject").choice == "手元"
    assert food.choice("duration_band").choice == "31〜60秒"
    assert food.gaps == []
    food_homage = agt.homage_for("ドッグフード")
    camera_homage = agt.homage_for("見守りカメラ")
    assert food_homage is not None and camera_homage is not None
    assert food_homage["in_count"] is False and food_homage["measured"] is False
    assert "median_views" not in food_homage
    assert "同じ子" in "".join(food_homage["borrow"])
    assert "商品は後" in "".join(food_homage["borrow"])
    assert "ごはん" in food_homage["first_3_seconds"]
    assert "飼い主" in camera_homage["fit"]
    assert agt.homage_for("美容スキンケア") is None
    assert agt.homage_for("婚活") is None
    food_md = agt.render_genre(food)
    assert "オマージュ（集計外）" in food_md
    assert "@cat-yu-chan" in food_md
    assert "浮気がバレ" not in food_md
    assert "オマージュ" not in agt.render_genre(beauty)

    handles = {item.reference["handle"] for item in built.genres}
    assert handles == {"the.care.logic", "nuts0629", "junjun_ranran", "yako.shiawasekon"}
    assert all(item.reference["present"] for item in built.genres)
    wedding_ref = wedding.reference
    assert wedding_ref["platform"] == "TikTok"
    assert wedding_ref["followers"] == 617
    accounts = agt.load_csv(DATA / "accounts.csv")
    analysis, references = agt.split_rows(accounts)
    assert ("yako.shiawasekon", "TikTok") not in {(row["handle"], row["platform"]) for row in analysis}
    assert ("yako.shiawasekon", "Instagram") in {(row["handle"], row["platform"]) for row in analysis}
    assert any(row["handle"] == "yako.shiawasekon" and row["platform"] == "TikTok" for row in references)


def test_thin_below_can_switch_a_genre_back_to_comparison() -> None:
    built = agt.load_snapshot(DATA, agt.Thresholds(thin_below=1))
    camera = next(item for item in built.genres if item.genre == "見守りカメラ")
    assert camera.basis == "比較"
    assert camera.choice("main_subject").choice == "動物"


def test_notebook_reads_local_files_or_raw_url() -> None:
    notebook = json.loads((ROOT / "affi.ipynb").read_text(encoding="utf-8"))
    source = "\n".join("".join(cell.get("source", [])) for cell in notebook["cells"])
    assert "raw.githubusercontent.com" in source
    assert "accounts.csv" in source
    assert "research/affi-templates" in source
    assert "affi_genre_templates" in source
    assert "affi_av.py" in source


def test_write_outputs_round_trip(tmp_path: Path) -> None:
    built = agt.load_snapshot(DATA)
    written = agt.write_outputs(built, tmp_path)
    assert (tmp_path / "compare.md").is_file()
    payload = json.loads((tmp_path / "美容スキンケア.json").read_text(encoding="utf-8"))
    assert payload["schema"] == agt.SCHEMA
    assert payload["script_brief"]["first_3_seconds"]["opening_type"]
    assert payload["n_growing"] == 139
    assert "ユーザー参考" not in payload["script_brief"]["first_3_seconds"]["instruction"]
    assert any(path.name == "all.json" for path in written)
