import json
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TRAIN = ROOT / "train"
sys.path.insert(0, str(TRAIN))

from pack_dataset import (  # noqa: E402
    PackError,
    camera_after_action,
    caption_starts_with_trigger,
    collect_rows,
    coverage_report,
    format_checklist,
    format_grid,
    format_list,
    get_concept,
    grid_cells,
    list_concepts,
    load_bundle,
    main,
    other_triggers,
    pack_zip,
    parse_filename_tags,
    recommend_fal,
    render_caption,
    skipped_concepts,
    write_captions,
    write_kit,
    ingest_phone_raw,
    resolve_concept_id,
)


def _touch_clip(folder: Path, name: str, caption: str | None = None) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / name
    path.write_bytes(b"fake-mp4")
    if caption is not None:
        path.with_suffix(".txt").write_text(caption + "\n", encoding="utf-8")
    return path


def test_bundle_has_three_separate_concept_loras():
    bundle = load_bundle()
    rows = list_concepts(bundle)
    ids = [row["id"] for row in rows]
    triggers = [row["trigger"] for row in rows]
    assert ids == ["anal-any-h3", "urine-drink-h3", "scat-act-h3"]
    assert triggers == ["AN4LIN", "URNKISS", "DFCTH3"]
    assert len(set(triggers)) == 3
    skipped = skipped_concepts(bundle)
    assert skipped[0]["id"] == "sex-any-h3"
    assert "aio" in skipped[0]["reason_ja"].lower()
    for row in rows:
        foreign = other_triggers(row["id"], bundle)
        assert row["trigger"] not in foreign
        assert row["trigger"] not in row["caption"].replace("{trigger}", "")
        for token in foreign:
            assert token not in row["caption"]
        assert "22+" in row["caption"]
        assert "No men" in row["caption"]
        assert "{pose}" in row["caption"]
        assert "{camera}" in row["caption"]


def test_sex_any_is_skipped():
    try:
        get_concept("sex-any-h3")
    except PackError as exc:
        assert "AIO" in str(exc)
    else:
        raise AssertionError("sex-any-h3 must stay skipped")


def test_unknown_concept_lists_known():
    try:
        get_concept("thumbinbutt-clone")
    except PackError as exc:
        assert "anal-any-h3" in str(exc)
    else:
        raise AssertionError("unknown concept must fail")


def test_parse_filename_tags_reads_composition():
    tags = parse_filename_tags("standing_front_close_9x16_01.mp4")
    assert tags == {
        "pose": "standing",
        "camera": "front",
        "shot": "close",
        "aspect": "9:16",
        "unknown": "01",
    }
    doggy = parse_filename_tags("doggy-behind-medium-16x9-02.mov")
    assert doggy["pose"] == "doggy"
    assert doggy["camera"] == "behind"
    assert doggy["shot"] == "medium"
    assert doggy["aspect"] == "16:9"
    side = parse_filename_tags("side_above_close_03.mp4")
    assert side["pose"] == "side"
    assert side["camera"] == "above"


def test_captions_are_action_first_camera_last():
    anal = get_concept("anal-any-h3")
    urine = get_concept("urine-drink-h3")
    scat = get_concept("scat-act-h3")
    tags = {
        "pose": "standing",
        "camera": "front",
        "shot": "close",
        "aspect": "9:16",
    }
    anal_text = render_caption(anal, tags)
    urine_text = render_caption(urine, tags)
    scat_text = render_caption(scat, tags)
    assert caption_starts_with_trigger(anal_text, "AN4LIN")
    assert caption_starts_with_trigger(urine_text, "URNKISS")
    assert caption_starts_with_trigger(scat_text, "DFCTH3")
    assert camera_after_action(anal_text)
    assert camera_after_action(urine_text)
    assert camera_after_action(scat_text)
    assert anal_text.lower().index("inside the anus") < anal_text.lower().index("camera")
    assert "not the vagina" in anal_text
    assert "hands on the hips" in anal_text
    assert "glans tip" in urine_text
    assert "drinks the yellow" in urine_text
    assert "pussy at the base" in urine_text
    assert "coming out of the anus" in scat_text
    assert "already coated" in scat_text
    assert "URNKISS" not in anal_text
    assert "DFCTH3" not in urine_text
    assert "AN4LIN" not in scat_text


def test_fal_bakes_trigger_only_in_captions():
    anal = get_concept("anal-any-h3")
    fal = recommend_fal(anal, 96)
    assert fal["trigger_phrase"] == ""
    assert fal["trigger_strategy"] == "baked_in_captions"
    assert fal["rank"] == 16
    assert fal["trainer"] == "minimax/h3/i2v/trainer"
    assert fal["debug_dataset"] is True
    assert fal["number_of_steps"] == 3000
    assert fal["learning_rate"] == 2e-4
    slow = recommend_fal(anal, 140)
    assert slow["number_of_steps"] == 5000
    assert slow["learning_rate"] == 1e-4


def test_pose_share_warns_when_one_pose_dominates(tmp_path):
    bundle = load_bundle()
    concept = get_concept("anal-any-h3", bundle)
    src = tmp_path / "clips"
    for index in range(8):
        _touch_clip(src, f"standing_front_close_9x16_{index:02d}.mp4")
    rows, warnings, errors = collect_rows(
        concept, src, bundle, rewrite=True, skip_probe=True
    )
    assert not errors
    coverage, cover_warns = coverage_report(rows, concept, bundle)
    assert coverage["poses"]["standing"] == 8
    assert any("standing" in item and "25%" in item for item in cover_warns)
    assert any("ThumbInButt" in item for item in cover_warns)


def test_keeps_existing_caption_when_trigger_present(tmp_path):
    bundle = load_bundle()
    concept = get_concept("anal-any-h3", bundle)
    src = tmp_path / "clips"
    custom = (
        "AN4LIN, custom already fully inside the anus standing pose. "
        "front camera, close shot, 9:16."
    )
    _touch_clip(src, "standing_front_close_9x16_01.mp4", custom)
    rows, warnings, errors = collect_rows(
        concept, src, bundle, rewrite=False, skip_probe=True
    )
    assert not errors
    assert rows[0]["caption"] == custom


def test_rejects_minor_filename(tmp_path):
    bundle = load_bundle()
    concept = get_concept("anal-any-h3", bundle)
    src = tmp_path / "clips"
    _touch_clip(src, "standing_front_close_9x16_loli_01.mp4")
    _rows, _warnings, errors = collect_rows(
        concept, src, bundle, rewrite=True, skip_probe=True
    )
    assert any("minor terms" in item for item in errors)


def test_rejects_other_concept_trigger(tmp_path):
    bundle = load_bundle()
    concept = get_concept("anal-any-h3", bundle)
    src = tmp_path / "clips"
    _touch_clip(
        src,
        "standing_front_close_9x16_01.mp4",
        "AN4LIN and URNKISS mixed acts",
    )
    _rows, _warnings, errors = collect_rows(
        concept, src, bundle, rewrite=False, skip_probe=True
    )
    assert any("URNKISS" in item for item in errors)


def test_pack_zip_uses_fal_pairs(tmp_path):
    src = tmp_path / "clips"
    out = tmp_path / "out"
    _touch_clip(src, "standing_front_close_9x16_01.mp4")
    _touch_clip(src, "doggy_behind_medium_16x9_02.mp4")
    code = main(
        [
            "--concept",
            "anal-any-h3",
            "--src",
            str(src),
            "--out",
            str(out),
            "--skip-probe",
            "--allow-small",
            "--rewrite-captions",
        ]
    )
    assert code == 0
    zpath = out / "anal-any-h3.zip"
    report = json.loads((out / "anal-any-h3-pack-report.json").read_text(encoding="utf-8"))
    assert report["schema"] == "h3-lora-studio-train-pack/v1"
    assert report["trigger"] == "AN4LIN"
    assert report["fal"]["trigger_phrase"] == ""
    assert Path(src / "standing_front_close_9x16_01.txt").read_text(encoding="utf-8").startswith(
        "AN4LIN"
    )
    with zipfile.ZipFile(zpath) as zf:
        names = set(zf.namelist())
        assert names == {"01.mp4", "01.txt", "02.mp4", "02.txt"}
        text = zf.read("01.txt").decode("utf-8")
        assert text.startswith("AN4LIN")
        assert "inside the anus" in text


def test_cli_list_and_grid():
    listed = format_list()
    assert "anal-any-h3" in listed
    assert "URNKISS" in listed
    assert "DFCTH3" in listed
    assert "sex-any-h3" in listed
    assert main(["--list"]) == 0
    anal = get_concept("anal-any-h3")
    cells = grid_cells(anal)
    poses = {cell["pose"] for cell in cells}
    assert poses == {"standing", "doggy", "missionary", "cowgirl", "side", "pov"}
    assert len(cells) == 6 * 4 * 2 * 2
    grid = format_grid(anal)
    assert "standing_front_close_9x16_01.mp4" in grid
    assert "AN4LIN" in grid


def test_cli_unknown_concept_is_exit_2():
    assert main(["--concept", "nope"]) == 2


def test_checklist_splits_prepare_and_do():
    text = format_checklist()
    assert text.startswith("# 学習キット — 準備すること / やること")
    assert "## 準備（撮る／集める前。これがないと始めない）" in text
    assert "## やること（1概念ずつ。3本並行で混ぜない）" in text
    for token in ("anal-any-h3", "urine-drink-h3", "scat-act-h3", "AN4LIN", "URNKISS", "DFCTH3"):
        assert token in text
    assert "sex-any-h3" in text
    assert "80" in text
    assert "25%" in text
    assert "trigger_phrase" in text
    assert "debug_dataset" in text
    assert "Lora_Trainer_XL.ipynb" in text
    assert "No feces" in text
    assert "PHONE.md" in text
    assert "スマホだけなら不要" in text
    assert main(["--print-checklist"]) == 0


def test_write_kit_matches_repo_docs(tmp_path):
    written = write_kit(tmp_path)
    names = {path.name for path in written}
    assert names == {
        "CHECKLIST.md",
        "anal-any-h3.txt",
        "urine-drink-h3.txt",
        "scat-act-h3.txt",
    }
    assert (tmp_path / "CHECKLIST.md").read_text(encoding="utf-8") == format_checklist()
    anal = get_concept("anal-any-h3")
    assert (tmp_path / "grids" / "anal-any-h3.txt").read_text(encoding="utf-8") == format_grid(anal)
    repo_list = TRAIN / "CHECKLIST.md"
    assert repo_list.read_text(encoding="utf-8") == format_checklist()
    for concept in list_concepts():
        grid_path = TRAIN / "grids" / f"{concept['id']}.txt"
        assert grid_path.read_text(encoding="utf-8") == format_grid(concept)


def test_write_captions_only(tmp_path):
    src = tmp_path / "clips"
    _touch_clip(src, "cowgirl_side_close_9x16_01.mp4")
    code = main(
        [
            "--concept",
            "urine-drink-h3",
            "--src",
            str(src),
            "--out",
            str(tmp_path / "out"),
            "--skip-probe",
            "--allow-small",
            "--write-captions-only",
            "--rewrite-captions",
        ]
    )
    assert code == 0
    text = (src / "cowgirl_side_close_9x16_01.txt").read_text(encoding="utf-8")
    assert text.startswith("URNKISS")
    assert "glans tip" in text
    assert not (tmp_path / "out" / "urine-drink-h3.zip").exists()


def test_pack_zip_helper_direct(tmp_path):
    src = tmp_path / "clips"
    video = _touch_clip(src, "squat_behind_close_9x16_01.mp4")
    rows = [
        {
            "src": str(video),
            "name": video.name,
            "tags": parse_filename_tags(video.name),
            "caption": "DFCTH3, act",
            "probe": None,
        }
    ]
    zpath = tmp_path / "scat.zip"
    pack_zip(rows, zpath)
    write_captions(rows)
    assert video.with_suffix(".txt").read_text(encoding="utf-8") == "DFCTH3, act\n"
    with zipfile.ZipFile(zpath) as zf:
        assert zf.read("01.txt").decode("utf-8") == "DFCTH3, act\n"


def test_resolve_concept_id_maps_phone_labels():
    assert resolve_concept_id("アナル（どの構図）") == "anal-any-h3"
    assert resolve_concept_id("放尿（性器から）") == "urine-drink-h3"
    assert resolve_concept_id("飲尿（どの構図）") == "urine-drink-h3"
    assert resolve_concept_id("脱糞（どの構図）") == "scat-act-h3"


def test_ingest_phone_raw_from_pose_folders(tmp_path):
    concept = get_concept("anal-any-h3")
    raw = tmp_path / "raw"
    (raw / "standing").mkdir(parents=True)
    (raw / "後背").mkdir(parents=True)
    (raw / "standing" / "IMG_0001.MOV").write_bytes(b"fake-a")
    (raw / "後背" / "clip.mp4").write_bytes(b"fake-b")
    leftover = tmp_path / "work"
    leftover.mkdir()
    (leftover / "old_front_close_9x16_99.mp4").write_bytes(b"stale")
    dest, names = ingest_phone_raw(raw, concept, leftover, skip_transcode=True)
    assert dest == leftover
    assert len(names) == 2
    poses = {name.split("_", 1)[0] for name in names}
    assert poses == {"standing", "doggy"}
    assert not (leftover / "old_front_close_9x16_99.mp4").exists()
    blobs = {name: (leftover / name).read_bytes() for name in names}
    assert set(blobs.values()) == {b"fake-a", b"fake-b"}


def test_ingest_phone_top_level_file_errors(tmp_path):
    concept = get_concept("scat-act-h3")
    raw = tmp_path / "raw"
    raw.mkdir()
    (raw / "IMG_0001.MOV").write_bytes(b"loose")
    try:
        ingest_phone_raw(raw, concept, tmp_path / "work", skip_transcode=True)
    except PackError as exc:
        assert "pose folder" in str(exc)
    else:
        raise AssertionError("expected PackError")


def test_ingest_phone_empty_errors(tmp_path):
    concept = get_concept("urine-drink-h3")
    raw = tmp_path / "raw"
    (raw / "standing").mkdir(parents=True)
    try:
        ingest_phone_raw(raw, concept, tmp_path / "work", skip_transcode=True)
    except PackError as exc:
        assert "no clips" in str(exc)
    else:
        raise AssertionError("expected PackError")


def test_cli_ingest_phone_skip_transcode(tmp_path):
    src = tmp_path / "raw"
    (src / "standing").mkdir(parents=True)
    (src / "standing" / "IMG_0001.MOV").write_bytes(b"clip")
    out = tmp_path / "packed"
    code = main(
        [
            "--concept",
            "anal-any-h3",
            "--src",
            str(src),
            "--out",
            str(out),
            "--ingest-phone",
            "--skip-transcode",
            "--skip-probe",
            "--allow-small",
            "--check-only",
        ]
    )
    assert code == 0
    report = json.loads((out / "anal-any-h3-pack-report.json").read_text(encoding="utf-8"))
    assert len(report["clips"]) >= 1
