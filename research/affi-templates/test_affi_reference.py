"""Reproduction templates stay on the schema, and A/B changes one slot."""

from __future__ import annotations

import csv
import json
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


def test_preset_text_enters_every_scene() -> None:
    item = ref.template_for("nuts0629")
    plain = ref.sheet(item, "餌", mode="interview")
    plan = ref.sheet(item, "餌", mode="interview", look={"animal_species": "rabbit"})
    assert len(plan["scenes"]) >= 2
    locked = plan["scenes"][0]["look"]
    assert "うさぎ" in locked
    assert "a rabbit" in locked
    for scene in plan["scenes"]:
        assert scene["look"] == locked
        assert locked in scene["imagine"]
        assert scene["start_s"] == plain["scenes"][plan["scenes"].index(scene)]["start_s"]
        assert scene["end_s"] == plain["scenes"][plan["scenes"].index(scene)]["end_s"]
        assert scene["subtitle"] == plain["scenes"][plan["scenes"].index(scene)]["subtitle"]
    again = ref.sheet(item, "別の話", mode="talk", look={"animal_species": "うさぎ"})
    assert "うさぎ" in again["scenes"][0]["look"]
    assert "a rabbit" in again["scenes"][0]["look"]


def test_other_text_enters_the_prompt() -> None:
    item = ref.template_for("yako.shiawasekon")
    plan = ref.sheet(
        item,
        "待ち合わせ",
        look={"place_style": "その他（直接入力）", "place_style_text": "白いタイルだけの室内"},
    )
    for scene in plan["scenes"]:
        assert "白いタイルだけの室内" in scene["imagine"]
        assert scene["look"] == plan["scenes"][0]["look"]


def test_default_look_is_not_the_source_account() -> None:
    nuts = ref.sheet(ref.template_for("nuts0629"), "餌", mode="interview")
    assert "柴犬" in nuts["look"]["ja"]
    assert "チワワ" not in nuts["look"]["ja"]
    assert "ピクサー" not in nuts["scenes"][0]["imagine"]
    care = ref.sheet(ref.template_for("the.care.logic"), "お茶")
    assert "茶葉" in care["look"]["ja"]
    assert "粘土" in care["look"]["ja"]
    assert "ピクサー" not in care["scenes"][0]["imagine"]
    pair = ref.sheet(ref.template_for("yako.shiawasekon"), "帰り道")
    assert "40代" in pair["look"]["ja"]
    assert "50代" in pair["look"]["ja"]
    for item in ref.templates():
        mode = item.get("default_mode")
        plan = ref.sheet(item, "試し", mode=mode)
        blob = plan["scenes"][0]["imagine"]
        for character in item["characters"]:
            assert character["look"] not in blob


def test_ab_keeps_the_same_look() -> None:
    picked = {"mascot_color": "mint", "ref_image": "drive/my-tea.png", "speech": "polite"}
    left, right = ref.ab_sheets("H1-1", "髪の悩み", ["困っている", "こうする", "よくなった"], look=picked)
    assert left["scenes"] == right["scenes"]
    assert left["look"]["line"] == right["look"]["line"]
    assert "ミント" in left["scenes"][0]["imagine"]
    assert "mint green" in left["scenes"][-1]["imagine"]
    assert "drive/my-tea.png" in left["scenes"][0]["look"]
    assert "drive/my-tea.png" in left["scenes"][-1]["look"]
    speech = ref.ab_sheets("H3-3", "窓辺", look={"animal_coat": "white_short"})
    assert speech[0]["look"]["line"] == speech[1]["look"]["line"]
    assert "白の短毛" in speech[0]["scenes"][0]["imagine"]
    assert speech[0]["scenes"] == speech[1]["scenes"]
    assert ref.changed_keys(speech[0], speech[1]) == {"speech_style"}


def test_rejects_likeness_and_underage() -> None:
    item = ref.template_for("yako.shiawasekon")
    blocked = [
        {"person_age": "other", "person_age_text": "15歳に見える"},
        {"person_hair": "その他（直接入力）", "person_hair_text": "乃やこにそっくり"},
        {"ref_image": "すず丸の写真"},
        {"person_clothes_text": "未成年向けの服"},
    ]
    for look in blocked:
        try:
            ref.sheet(item, "試し", look=look)
        except ValueError as exc:
            assert "似せる" in str(exc) or "成人" in str(exc)
        else:
            raise AssertionError(look)


def test_yaml_look_file(tmp_path: Path) -> None:
    path = tmp_path / "look.yaml"
    path.write_text(
        "schema: affi-look-selection/v1\nanimal_species: rabbit\nref_image: my-ref.png\n",
        encoding="utf-8",
    )
    plan = ref.sheet(ref.template_for("nuts0629"), "餌", look=ref.load_look(path), mode="interview")
    assert "うさぎ" in plan["scenes"][0]["imagine"]
    assert "my-ref.png" in plan["scenes"][-1]["imagine"]


def test_choices_and_notebook_form() -> None:
    cat = ref.catalog()
    assert cat["other_label"] == "その他（直接入力）"
    for fid, field in cat["fields"].items():
        presets = [opt for opt in field["options"] if opt["id"] != "other"]
        assert field["options"][-1]["label"] == "その他（直接入力）"
        assert len(presets) >= (2 if fid == "person_gender" else 4)
        for opt in presets:
            assert opt["ja"] and opt["en"]
    notebook = json.loads((ROOT / "affi.ipynb").read_text(encoding="utf-8"))
    source = "\n".join("".join(cell["source"]) for cell in notebook["cells"])
    assert "reference-accounts/looks.yaml" in source
    assert "その他（直接入力）" in source
    for field in cat["fields"].values():
        for opt in field["options"]:
            assert opt["label"] in source
