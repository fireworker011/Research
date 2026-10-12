"""The shot sheet copies structure and leaves person, animal, line, and place empty."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

import affi_structure as structure

_JAPANESE = re.compile(r"[ぁ-んァ-ヶ一-龥]")


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


def test_written_moves_become_paths_and_unmeasured_times_stay_out() -> None:
    pack = structure.load()
    text = structure.picture_prompt(pack, 0.0, float(pack["duration_s"]))
    assert "The retort's weight moves onto the hind legs and the torso rises, then the hind legs fold and the body sits." in text
    assert "The polite one's body stays seated." in text
    assert "The guest's body moves in through the opening." in text
    assert "The two animals' bodies step backward." in text
    assert "The two animals' heads stay in profile." in text
    assert "The camera holds a static shot aimed at the side of the face, through the glass." in text
    assert "30.6" not in text
    assert "38.8" not in text
    pet = structure.load(ROOT / "stories" / "pet_sheet.yaml")
    pet_text = structure.picture_prompt(pet, 0.0, float(pet["duration_s"]))
    assert "The two animals' legs cycle and the bodies travel forward across the grass." in pet_text
    assert "The retort's head turns toward the house." in pet_text
    assert "The retort's forepaw lifts, strikes the water, and returns." in pet_text
    assert "The water turns in a vortex until the pool is empty." in pet_text
    assert "The retort's lower jaw drops and rises, more than once." in pet_text
    assert "The polite one's mouth stays closed. That jaw does not travel." in pet_text
    assert "The person's lower jaw drops and rises, more than once." in pet_text
    assert "The two animals' mouths stay closed. Those jaws do not travel." in pet_text
    assert "The polite one's mouth keeps hold of a flat white pad while the legs step forward." in pet_text
    assert "The polite one's head turns toward the vinyl pool at the edge of the yard." in pet_text
    assert "The person's body stands upright in the doorway." in pet_text
    assert "Only the flat white pad lies there and does not move." in pet_text
    assert "This shot stays at the pool." in pet_text
    assert "This shot stays at the doorway." in pet_text
    assert "shape words" not in pet_text
    paw = structure.load(ROOT / "stories" / "paw_stamp.yaml")
    paw_text = structure.picture_prompt(paw, 0.0, float(paw["duration_s"]))
    assert "The retort's forepaw presses down twice, then once more." in paw_text
    assert "The dog's forepaws fold back under the chest." in paw_text
    assert "The dog's forepaws stay folded under the chest and do not travel." in paw_text
    assert "The polite one's and the dog's mouths stay closed. Those jaws do not travel." in paw_text
    assert "Every mouth stays closed. Those jaws do not travel." in paw_text
    assert "This shot stays on the rug." in paw_text
    assert "shape words" not in paw_text


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
    assert structure.blocked(filled) == []
    text = structure.picture_prompt(filled, 0.0, 1.333)
    assert "文1" not in text
    assert "おい、そこのデブ" not in text
    assert "小さい鳥" not in text
    assert "a small bird" in text
    assert "Place: a different room." in text
    assert "No one speaks." in text
    assert "Mouths do not form words." not in text
    assert "shape words" not in text
    assert "The camera holds a static shot at close range" in text
    assert "口が開閉" not in text
    assert "The small bird's mouth stays open. That jaw does not travel." in text
    assert "A jaw opens and closes" not in text
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
        place="真夏の庭",
        lines=spoken,
    )
    assert structure.blocked(filled) == []
    text = structure.picture_prompt(filled, 0.0, float(filled["duration_s"]))
    for line in spoken.values():
        assert line not in text
    assert "lower jaw drops and rises" in text
    assert "口が開閉" not in text
    assert "砂漠" not in text
    assert "オアシス" not in text
    assert "ナプキン" not in text
    assert "イメージです" not in text
    assert "<d>" not in text
    assert "No one speaks." not in text
    assert "shape words" not in text
    assert not _JAPANESE.search(text)
    assert "Place: a yard in midsummer." in text
    assert "Guest" not in text and "the guest" not in text
    assert "The grey Munchkin cat's lower jaw drops and rises, more than once." in text
    assert "The white Scottish Fold cat's mouth stays closed." in text
    assert "The adult woman's face stays out of frame." in text
    assert "In frame: the grey Munchkin cat and the white Scottish Fold cat." in text
    first = structure.picture_prompt(filled, 0.0, 4.192)
    assert "Cast: a grey Munchkin cat; a white Scottish Fold cat." in first
    assert "pool" not in first
    door = structure.picture_prompt(filled, 42.6, 46.072)
    assert (
        "Cast: an adult woman in their late twenties, wearing loose loungewear, with hair tied back; "
        "a grey Munchkin cat; a white Scottish Fold cat."
    ) in door
    assert "The adult woman's body stands upright in the doorway." in door
    quiet = structure.picture_prompt(filled, 15.8, 20.8)
    assert "No one speaks. No writing. No music. No logo." in quiet
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
    assert structure.pack_file("給水") == path
    assert structure.stock_lines("給水", "").startswith("c01")
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
    assert "lower jaw drops and rises" in text
    assert "口が開閉" not in text
    assert "グレーのマンチカン" not in text
    assert "短い足の茶色い犬" not in text
    assert not _JAPANESE.search(text)
    assert "a grey Munchkin cat" in text
    assert "Place: a living room in daylight, with a thin blanket on the sofa, with a treat dish on the floor." in text
    assert "The short-legged brown dog's lower jaw drops and rises, more than once." in text
    assert "the person" not in text.casefold()
    assert "名刺" not in text
    assert "お尻" not in text
    assert "猫" not in text
    assert "<d>" not in text
    assert "No one speaks." not in text
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
    assert "From 0.2 to 1, the guest's lower jaw drops and rises." in text
    assert "From 4.2 to 5.2, the guest's lower jaw drops and rises." in text
    assert not _JAPANESE.search(text)
    named = structure.fill(loaded, animals={"guest": "茶トラの猫"})
    assert "From 0.2 to 1, the orange tabby cat's lower jaw drops and rises." in structure.picture_prompt(named, 0, 6)
    assert "The other mouths stay closed. Those jaws do not travel." in text
    assert "Every mouth stays closed. Those jaws do not travel." in text
    assert "The lower jaw drops and rises, more than once" not in text
    assert "The camera path was not measured. The camera holds a static shot." in text
    assert "カメラの動きは測っていない" not in text
    with pytest.raises(ValueError, match="せりふが読めない"):
        structure.homage_pack(duration_s=6, cuts=[], lines=[])
    with pytest.raises(ValueError, match="カットが測れない"):
        structure.homage_pack(duration_s=6, cuts=None, lines=_homage_lines())
    many = [{"start_s": index, "end_s": index + 0.4, "speaker": str(index)} for index in range(6)]
    with pytest.raises(ValueError, match="5役より多い"):
        structure.homage_pack(duration_s=8, cuts=[], lines=many)


def test_reference_paths_bind_to_the_role_and_stay_off_locked_sheets() -> None:
    picture = (
        "2匹が背中を向けて座り、頭を向かい合わせる。"
        "客が口に細い棒をくわえる。"
        "客が前足を一本口の棒へ上げて下ろす。"
        "客が前足を一本、胸の前で上げたまま。"
        "客が後ろ脚で立ち、前足二本で縦の棒を胸の前で握る。"
        "客が前足二本で縦の棒を頭の横へ上げる。"
        "客が前足で縦の棒を頭の上に横たえる。"
        "人が片手を頭の上へ上げる。"
        "まぶたをきつく閉じ、歯が見える。"
        "人が両膝を床につけ、両手を床の平たい物に置く。"
        "客が床を離れて前へ飛ぶ。"
        "縦の棒が床へ落ちる。"
        "犬は後ろの体はぼける。"
    )
    lines = structure._body_lines(picture, "", False)
    assert lines == [
        "The two animals' bodies stay seated with the backs toward the lens, and the heads turn toward each other.",
        "The guest's mouth keeps hold of a thin stick. That jaw does not travel.",
        "The guest's forepaw rises to the thin stick at the mouth and then lowers. The stick leaves that mouth.",
        "The guest's forepaw stays raised in front of the chest.",
        "The guest's weight moves onto the hind legs and the torso rises until the body is standing, and both forepaws close around a vertical stick held in front of the chest.",
        "The guest's forepaws raise the vertical stick until it is beside the head.",
        "The guest's forepaw lays the stick across the top of the head.",
        "The person's hand rises onto the top of the head.",
        "The person's eyelids squeeze shut and the jaw drops until the teeth show.",
        "The person's knees stay on the floor and both hands stay on the flat object on the floor.",
        "The guest's body leaves the floor and travels forward through the air.",
        "The stick drops to the floor and stays there.",
        "The dog's body stays behind and out of focus.",
    ]
    grip = structure._body_lines("客が前足二本で縦の棒を胸の前で握る。", "", False)
    assert grip == ["The guest's forepaws close around a vertical stick held in front of the chest."]
    stood = structure._body_lines("ツッコミ役が後ろ脚で立ち、あとで座る。", "", False)
    assert stood == [
        "The retort's weight moves onto the hind legs and the torso rises, then the hind legs fold and the body sits."
    ]
    fresh = [
        "thin stick",
        "vertical stick",
        "eyelids squeeze",
        "through the air",
        "out of focus",
        "toward each other",
    ]
    for path in (
        ROOT / "reference-accounts" / "source" / "repro" / "junjun_825k.yaml",
        ROOT / "stories" / "pet_sheet.yaml",
        ROOT / "stories" / "paw_stamp.yaml",
    ):
        pack = structure.load(path)
        text = structure.picture_prompt(pack, 0.0, float(pack["duration_s"]))
        for word in fresh:
            assert word not in text


def test_slots_reach_h3_in_english_or_stop() -> None:
    assert structure.slot_english("グレーのマンチカン") == ("a grey Munchkin cat", "the grey Munchkin cat")
    assert structure.slot_english("白いスコティッシュフォールド") == (
        "a white Scottish Fold cat",
        "the white Scottish Fold cat",
    )
    assert structure.slot_english("短い足の茶色い犬") == ("a short-legged brown dog", "the short-legged brown dog")
    assert structure.slot_english("20代後半の成人の女性。ゆるい部屋着。髪はひとつ結び") == (
        "an adult woman in their late twenties, wearing loose loungewear, with hair tied back",
        "the adult woman",
    )
    assert structure.slot_english("真夏の庭")[0] == "a yard in midsummer"
    assert structure.slot_english("a grey cat with a red collar") == (
        "a grey cat with a red collar",
        "the grey cat with a red collar",
    )
    assert structure.slot_english("A cat, small, with stripes.")[1] == ""
    with pytest.raises(ValueError, match="ふわふわ"):
        structure.slot_english("ふわふわの猫")
    pack = structure.load(ROOT / "stories" / "pet_sheet.yaml")
    unknown = structure.fill(
        pack,
        person="出さない",
        animals={"guest": "出さない", "retort": "ふわふわの猫", "polite": "白い猫"},
        place="真夏の庭",
    )
    reasons = structure.blocked(unknown)
    assert any(reason.startswith("ツッコミの動物「ふわふわの猫」は英語にできない語がある") for reason in reasons)
    assert "s15 の画面に「出さない」の飼い主がいる" in reasons
    assert "s16 の画面に「出さない」の飼い主がいる" in reasons
    text = structure.picture_prompt(unknown, 0.0, float(pack["duration_s"]))
    assert not _JAPANESE.search(text)
    assert "the retort: not named" in text
    english = structure.fill(
        pack,
        person="an adult man in a plain shirt",
        animals={"guest": "出さない", "retort": "a black cat", "polite": "a white cat"},
        place="a small balcony at noon",
        lines={"c01": "あっつ"},
    )
    assert [reason for reason in structure.blocked(english) if "入力のまま" not in reason] == []
    english_text = structure.picture_prompt(english, 0.0, 4.192)
    assert "Place: a small balcony at noon." in english_text
    assert "The black cat's lower jaw drops and rises, more than once." in english_text
    paw = structure.load(ROOT / "stories" / "paw_stamp.yaml")
    spoken_guest = structure.fill(paw, animals={"guest": "出さない"}, lines={"c07": "休業"})
    assert "c07 は「出さない」の客のせりふ" in structure.blocked(spoken_guest)


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
