"""The shot sheet copies structure and leaves person, animal, line, and place empty."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
import yaml

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


def test_parse_lines_keeps_blanks_empty() -> None:
    ids = ["c01", "c02", "c03"]
    assert structure.parse_lines("", ids) == {}
    assert structure.parse_lines("文1\n\n文3", ids) == {"c01": "文1", "c03": "文3"}
    assert structure.parse_lines("c02 文2\nc01 文1", ids) == {"c01": "文1", "c02": "文2"}
    with pytest.raises(ValueError, match="どちらか"):
        structure.parse_lines("c01 文1\n文2", ids)


def test_picture_prompt_leaves_the_spoken_line_out() -> None:
    pack = structure.load()
    lines = {row["id"]: f"文{index}" for index, row in enumerate(pack["captions"], start=1)}
    filled = structure.fill(
        pack,
        person="大人の人",
        animals={"guest": "小さい鳥", "retort": "太い動物", "polite": "細い動物"},
        place="別の部屋",
        lines=lines,
    )
    text = structure.picture_prompt(filled, 0.0, 1.333)
    assert "文1" not in text
    assert "おい、そこのデブ" not in text
    assert "小さい鳥" in text
    assert "別の部屋" in text
    assert "No one speaks." in text
    assert "Mouths do not form words." not in text
    assert "does not shape words." in text
    assert "From " not in text
    assert filled["shots"][0]["source_seen"] not in text


def test_pet_sheet_is_another_pack_of_the_same_sheet() -> None:
    locked = structure.load()
    path = ROOT / "stories" / "pet_sheet.yaml"
    pack = structure.load(path)
    assert locked["source_id"] == "7692378853490167046"
    assert pack["source_id"] == "pet-sheet-summer-yard"
    assert len(locked["shots"]) == 20
    assert pack["duration_s"] == 51.572
    lines_text = (ROOT / "stories" / "pet_sheet_lines.txt").read_text(encoding="utf-8")
    spoken = structure.parse_lines(lines_text, [row["id"] for row in pack["captions"]])
    assert len(spoken) == 11
    filled = structure.fill(
        pack,
        person="20代後半の成人の女性。ゆるい部屋着。髪はひとつ結び",
        animals={"guest": "出さない", "retort": "グレーのマンチカン", "polite": "白いスコティッシュフォールド"},
        place="真夏の庭。空の水入れと小さなビニールプール",
        lines=spoken,
    )
    assert structure.blocked(filled) == []
    text = structure.picture_prompt(filled, 0.0, float(filled["duration_s"]))
    for line in spoken.values():
        assert line not in text
    assert "口が開閉" in text
    assert "砂漠" not in text
    assert "オアシス" not in text
    assert "ナプキン" not in text
    assert "イメージです" not in text
    assert "<d>" not in text
    assert "No one speaks." in text
    assert filled["shots"][0]["camera"]
    assert structure.load()["duration_s"] == 71.552
    url = (
        "https://github.com/fireworker011/Research/blob/"
        "cursor/affi-template-bake-44d6/research/affi-templates/stories/pet_sheet.yaml"
    )
    assert structure.pack_file(url) == path
    assert structure.pack_file("pet_sheet.yaml") == path
    assert structure.pack_file("") is None
    with pytest.raises(ValueError, match="構成ファイルが無い"):
        structure.pack_file("stories/missing.yaml")
    from_path = structure.read_lines("stories/pet_sheet_lines.txt")
    assert from_path.startswith("c01")
    assert structure.parse_lines(from_path, [row["id"] for row in pack["captions"]]) == spoken
    assert structure.read_lines("c01 あっつ") == "c01 あっつ"
    with pytest.raises(ValueError, match="セリフファイルが無い"):
        structure.read_lines("stories/missing_lines.txt")
    assert "voices" not in pack
    index = structure.story_index()
    assert [row["name"] for row in index] == ["pet_sheet", "paw_stamp"]
    assert index[0]["duration"] == "51.572秒"
    assert index[1]["duration"] == "50.556秒"
    assert index[0]["pattern"] == "junjun_ranran"
    assert index[1]["baked"] == "まだ"
    assert structure.pack_file("pet_sheet") == path
    assert structure.pack_file("paw_stamp") == ROOT / "stories" / "paw_stamp.yaml"
    assert structure.pack_file("71.552秒") is None
    assert structure.stock_lines("paw_stamp", "").startswith("c01")
    assert structure.stock_lines("71.552秒", "") == ""
    assert structure.stock_lines("", "") == ""
    assert structure.stock_lines("paw_stamp", "c01 別") == "c01 別"


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


def test_paw_stamp_is_another_pack_of_the_same_sheet() -> None:
    path = ROOT / "stories" / "paw_stamp.yaml"
    pack = structure.load(path)
    assert pack["source_id"] == "paw-stamp-living-room"
    assert pack["duration_s"] == 50.556
    assert 45 <= pack["duration_s"] <= 60
    assert len(pack["shots"]) == 14
    assert len(pack["captions"]) == 10
    lines_text = (ROOT / "stories" / "paw_stamp_lines.txt").read_text(encoding="utf-8")
    spoken = structure.parse_lines(lines_text, [row["id"] for row in pack["captions"]])
    assert len(spoken) == 10
    filled = structure.fill(
        pack,
        person="出さない",
        animals={"guest": "短い足の茶色い犬", "retort": "グレーのマンチカン", "polite": "白いスコティッシュフォールド"},
        place="昼のリビング。ソファの薄い毛布。床におやつ皿",
        lines=spoken,
    )
    assert structure.blocked(filled) == []
    text = structure.picture_prompt(filled, 0.0, float(filled["duration_s"]))
    for line in spoken.values():
        assert line not in text
    assert "口が開閉" in text
    assert "グレーのマンチカン" in text
    assert "短い足の茶色い犬" in text
    assert "名刺" not in text
    assert "お尻" not in text
    assert "猫" not in text
    assert "<d>" not in text
    assert "No one speaks." in text
    assert structure.load()["duration_s"] == 71.552
    voices = pack["voices"]
    assert voices["guest"] == "espeak:ja"
    assert voices["retort"] == "ja-JP-KeitaNeural"
    assert voices["polite"] == "ja-JP-NanamiNeural"
    assert voices["owner"] == "gtts:ja"
    assert len(set(voices.values())) == len(voices)
    broken = {**voices, "owner": voices["guest"]}
    with pytest.raises(ValueError, match="同じ声が2役に当たっている"):
        structure.check_voices({**pack, "voices": broken})


def _homage_lines() -> list[dict[str, float | str]]:
    return [
        {"start_s": 0.2, "end_s": 1.0, "speaker": "A"},
        {"start_s": 4.2, "end_s": 5.2, "speaker": "A"},
    ]


def test_homage_pack_keeps_measured_times_and_drops_the_words(tmp_path: Path) -> None:
    pack = structure.homage_pack(duration_s=6, cuts=[2.0, 4.0], lines=_homage_lines())
    path = tmp_path / "homage.yaml"
    path.write_text(yaml.safe_dump(pack, allow_unicode=True, sort_keys=False), encoding="utf-8")
    loaded = structure.load(path)
    assert loaded["line_must_fit"] is True
    assert loaded["duration_s"] == 6
    assert loaded["cuts_s"] == [2.0, 4.0]
    assert [shot["camera"] for shot in loaded["shots"]] == ["カメラの動きは測っていない。"] * 3
    assert loaded["shots"][0]["on_screen"] == ["guest"]
    assert loaded["shots"][1]["on_screen"] == []
    assert loaded["shots"][1]["picture"].startswith("誰も口を開かない")
    assert loaded["shots"][2]["on_screen"] == ["guest"]
    assert all(row["line"] == "入力" for row in loaded["captions"])
    assert [row["source_line"] for row in loaded["captions"]] == ["e-01", "e-02"]
    assert loaded["slots"]["place"] == "入力"
    text = structure.picture_prompt(loaded, 0, 6)
    assert "砂漠" not in text
    assert "オアシス" not in text
    assert "e-01" not in text
    assert "Mouths do not form words." not in text
    assert "From 0.2 to 1, the 客 jaw opens and closes." in text
    assert "From 4.2 to 5.2, the 客 jaw opens and closes." in text
    assert "カメラの動きは測っていない。" in text
    with pytest.raises(ValueError, match="せりふが読めない"):
        structure.homage_pack(duration_s=6, cuts=[], lines=[])
    with pytest.raises(ValueError, match="カットが測れない"):
        structure.homage_pack(duration_s=6, cuts=None, lines=_homage_lines())
    many = [{"start_s": index, "end_s": index + 0.4, "speaker": str(index)} for index in range(6)]
    with pytest.raises(ValueError, match="5役より多い"):
        structure.homage_pack(duration_s=8, cuts=[], lines=many)


def test_line_fit_stops_only_when_the_sheet_asks() -> None:
    pack = structure.homage_pack(duration_s=6, cuts=[2.5], lines=[{"start_s": 0.2, "end_s": 1.0, "speaker": "A"}])
    filled = structure.fill(pack, lines={"c01": "長い一文"})
    assert structure.line_fit_reasons(filled, lambda _text, _role: None) == ["c01 の秒が測れない"]
    blocked = structure.line_fit_reasons(filled, lambda _text, _role: 5)
    assert blocked == ["c01 は 5 秒。せりふの秒は 0.8 秒。カットは動かさない。"]
    assert structure.line_fit_reasons(filled, lambda _text, _role: 0.5) == []
    pet = structure.load(ROOT / "stories" / "pet_sheet.yaml")
    assert not pet.get("line_must_fit")
    pet_filled = structure.fill(pet, lines={"c01": "短い"})
    assert structure.line_fit_reasons(pet_filled, lambda _text, _role: 99) == []
