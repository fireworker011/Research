"""Live-action remake plan. Measurement math and sheet checks. No ffmpeg run, no generation."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "colab"))

import h3_live_remake as remake
import h3_studio as studio
from _write_studio_nb import make_nb, mirror_engine

SOURCE = {
    "path": "source.mp4",
    "duration_s": 20.0,
    "width": 2560,
    "height": 1440,
    "fps": 60.0,
    "has_audio": True,
}
MOTION = "<Subject 1> on the left folds both arms. <Subject 2> on the right turns his head. The camera holds."


def filled_sheet(**overrides):
    sheet = remake.skeleton_sheet(SOURCE, [4.0, 6.0], cuts_from="test")
    sheet["cast"] = {
        "S1": {"stills": {"default": "s1.png", "armored": "s1-armored.png"}},
        "S2": {"stills": {"default": "s2.png"}},
    }
    sheet["place_still"] = "street.png"
    sheet["props"] = {"P1": {"still": "prop.png"}}
    for span in sheet["spans"]:
        span["cast"] = {"S1": "default", "S2": "default"}
        span["place"] = True
        span["description"] = MOTION
    sheet.update(overrides)
    return sheet


def test_frame_grid_is_17k_plus_5_inside_the_15_second_check():
    assert remake.align_frames(1) == 124
    assert remake.align_frames(124) == 124
    assert remake.align_frames(125) == 141
    assert remake.align_frames(345) == 345
    for frames in range(1, 346):
        aligned = remake.align_frames(frames)
        assert aligned % 17 == 5
        assert 124 <= aligned <= 345


def test_short_flashes_merge_into_the_previous_shot():
    raw = [22.117, 27.817, 27.9, 27.983, 28.117, 29.733, 72.9]
    kept = remake.merge_cuts(raw, 73.05, 0.5)
    assert kept == [22.117, 27.817, 29.733]
    assert all(b - a >= 0.5 for a, b in zip([0.0] + kept, kept + [73.05]))


def test_spans_keep_whole_shots_and_add_up_to_the_source():
    shots = remake.shot_frames([4.0, 6.0, 15.0], 20.0)
    spans = remake.plan_spans(shots, 8.0)
    assert spans[0]["start_frame"] == 0
    assert spans[-1]["end_frame"] == 480
    for left, right in zip(spans, spans[1:]):
        assert left["end_frame"] == right["start_frame"]
        if not left["split_inside_shot"] and not right["split_inside_shot"]:
            assert left["end_frame"] in {96, 144, 360}
    assert all(span["end_frame"] - span["start_frame"] <= 192 for span in spans)


def test_a_long_shot_is_split_evenly_and_flagged():
    spans = remake.plan_spans([(0, 500)], 8.0)
    assert len(spans) == 3
    assert all(span["split_inside_shot"] for span in spans)
    assert sum(span["end_frame"] - span["start_frame"] for span in spans) == 500
    with pytest.raises(remake.RemakeError, match="1本の長さ"):
        remake.plan_spans([(0, 100)], 15.0)


def test_skeleton_leaves_roles_and_text_empty():
    sheet = remake.skeleton_sheet(SOURCE, [4.0, 6.0], cuts_from="test")
    assert sheet["schema"] == remake.SCHEMA
    assert sheet["cast"] == {} and sheet["place_still"] == "" and sheet["props"] == {}
    assert all(span["description"] == remake.SLOT for span in sheet["spans"])
    assert sheet["audio"] == "source"
    plan = remake.build_remake_plan(sheet)
    assert plan["status"] == "blocked"
    assert any("文が無い" in reason for reason in plan["blocked"])
    assert all(span["prompt"] == "" for span in plan["spans"])


def test_filled_sheet_is_one_ref2va_per_span_with_pictures_in_order():
    plan = remake.build_remake_plan(filled_sheet())
    assert plan["status"] == "ready", plan["blocked"]
    assert plan["job"] == "live_remake" and plan["task"] == "ref2va"
    assert (plan["width"], plan["height"], plan["fps"]) == (1344, 768, 24)
    assert plan["loras"] == [{"key": "anime2real", "file": "Anime2Realsim__H3.safetensors", "strength": 1.0}]
    assert plan["generate"] is False and plan["publish"] is False
    first = plan["spans"][0]
    assert [item["path"] for item in first["pictures"]] == ["s1.png", "s2.png", "street.png"]
    assert [item["label"] for item in first["pictures"]] == ["<Picture 1>", "<Picture 2>", "<Picture 3>"]
    prompt = first["prompt"]
    for section in (
        "subject_definitions:",
        "summary:",
        "retention_analysis:",
        "detailed_description:",
        "overall_soundscape:",
        "non_diegetic_music:",
    ):
        assert section in prompt
    assert prompt.index("subject_definitions:") < prompt.index("summary:") < prompt.index("non_diegetic_music:")
    assert "<Picture 1> is the only identity and costume reference for <Subject 1>." in prompt
    assert "<Picture 3> is the environment reference." in prompt
    assert "Not anime" in prompt and "[Shot 1]" in prompt
    assert sum(span["frames"] for span in plan["spans"]) == 480
    assert all(span["request_frames"] % 17 == 5 for span in plan["spans"])


def test_conform_and_join_use_measured_frames():
    plan = remake.build_remake_plan(filled_sheet())
    first = plan["spans"][0]
    argv = first["conform_argv"]
    vf = argv[argv.index("-vf") + 1]
    assert "fps=24" in vf and "crop=1344:768" in vf and "tpad=stop_mode=clone" in vf
    assert argv[argv.index("-frames:v") + 1] == str(first["request_frames"])
    join = plan["join_argv"]
    graph = join[join.index("-filter_complex") + 1]
    for index, span in enumerate(plan["spans"]):
        assert f"[{index}:v]trim=end_frame={span['frames']}" in graph
    assert join[join.index("-map", join.index("-filter_complex")) + 3] == f"{len(plan['spans'])}:a:0"
    generated = remake.build_remake_plan(filled_sheet(audio="generated"))
    graph = generated["join_argv"][generated["join_argv"].index("-filter_complex") + 1]
    assert "atrim" in graph and "a=1" in graph


def test_missing_stills_and_bad_labels_stop():
    sheet = filled_sheet()
    sheet["spans"][1]["cast"] = {"S1": "armored", "S2": "default"}
    sheet["cast"]["S1"]["stills"]["armored"] = ""
    sheet["spans"][2]["props"] = ["P1"]
    sheet["props"]["P1"]["still"] = remake.SLOT
    sheet["spans"][0]["description"] = MOTION + " <Picture 7> drops. <Video 2> plays. <Audio 1> rises."
    plan = remake.build_remake_plan(sheet)
    assert plan["status"] == "blocked"
    text = "\n".join(plan["blocked"])
    assert "S1（armored）に静止画が無い" in text
    assert "P1 に静止画が無い" in text
    assert "<Picture 7>" in text and "<Video 2>" in text and "<Audio>" in text


def test_japanese_outside_dialogue_stops_and_api_refuses():
    sheet = filled_sheet()
    sheet["spans"][0]["description"] = "彼が振り向く。"
    with pytest.raises(remake.RemakeError, match="英語"):
        remake.build_remake_plan(sheet)
    sheet["spans"][0]["description"] = MOTION + ' He says <d>[Japanese] 行くぞ</d>.'
    assert remake.build_remake_plan(sheet)["status"] == "ready"
    with pytest.raises(remake.RemakeError, match="Comfy"):
        remake.build_remake_plan(sheet, runtime="api")


def test_spans_must_cover_the_source_without_gaps():
    sheet = filled_sheet()
    sheet["spans"][1]["start_s"] = 4.5
    with pytest.raises(remake.RemakeError, match="合わない"):
        remake.build_remake_plan(sheet)
    sheet = filled_sheet(audio="source")
    sheet["source"] = {**SOURCE, "has_audio": False}
    with pytest.raises(remake.RemakeError, match="音が無い"):
        remake.build_remake_plan(sheet)


def test_studio_job_reads_the_sheet(tmp_path):
    path = tmp_path / "sheet.json"
    path.write_text(json.dumps(filled_sheet()), encoding="utf-8")
    plan = studio.build_plan(studio.request_from({"job": "live_remake", "remake_sheet": str(path)}))
    assert plan["status"] == "ready"
    assert len(studio.prompts_of(plan)) == len(plan["spans"])
    with pytest.raises(studio.StudioError, match="api"):
        studio.build_plan(studio.request_from({"job": "live_remake", "remake_sheet": str(path), "runtime": "api"}))
    with pytest.raises(studio.StudioError, match="High-Mem"):
        studio.build_plan(studio.request_from({"job": "live_remake", "remake_sheet": str(path), "high_mem": False}))
    with pytest.raises(studio.StudioError, match="シートが要る"):
        studio.build_plan(studio.request_from({"job": "live_remake"}))
    with pytest.raises(studio.StudioError, match="live_remake だけ"):
        studio.request_from({"job": "text_scene", "remake_sheet": str(path)})


def test_notebook_has_the_measure_cell_and_sheet_field():
    nb = make_nb()
    plan_cell = "".join(nb["cells"][1]["source"])
    measure_cell = "".join(nb["cells"][3]["source"])
    assert 'REMAKE_SHEET = ""' in plan_cell
    assert "H3_STUDIO_REMAKE_SHEET" in plan_cell
    assert "h3_live_remake.py" in measure_cell
    assert "measure(SOURCE" in measure_cell
    assert "remake-sheet.json" in measure_cell
    mirror_engine()
    assert (ROOT / "colab" / "h3_live_remake.py").read_bytes() == (ROOT / "minimaxh3" / "h3_live_remake.py").read_bytes()


def test_external_skills_keep_their_licenses():
    for name in ("video-to-h3-prompt", "write-h3-v39-reference-prompts"):
        folder = ROOT / ".cursor" / "skills" / name
        assert (folder / "SKILL.md").is_file()
        assert "MIT License" in (folder / "LICENSE").read_text(encoding="utf-8")
        assert "コミット" in (folder / "SOURCE.md").read_text(encoding="utf-8")
