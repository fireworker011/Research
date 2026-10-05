"""Bake jobs keep the template clock. They do not render video."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT.parents[2]))

import affi_bake as bake
import affi_genre_templates as genre


def _ids(job: dict) -> list[str]:
    return [cut["id"] for cut in job["cuts"]]


def test_genre_handles_match_the_table() -> None:
    assert bake.GENRE_HANDLES == genre.REFERENCE_HANDLES


def test_dance_is_one_ten_second_clip_and_needs_a_still(tmp_path: Path) -> None:
    job = bake.bake_reference("nuts0629", mode="dance", theme="夕方の散歩")
    assert job["duration_s"] == 10
    assert job["aspect"] == "9:16"
    assert job["canvas"] == "720x1280"
    assert [cut["duration_s"] for cut in job["cuts"]] == [10]
    assert [(clip["trim_s"], clip["request_s"]) for clip in job["clips"]] == [(10, 10)]
    assert job["status"] == "blocked"
    assert any("静止画" in reason for reason in job["blocked"])
    assert job["generates_video"] is False
    assert job["posts"] is False
    still = tmp_path / "still.jpg"
    still.write_bytes(b"jpeg")
    ready = bake.bake_reference("nuts0629", mode="dance", theme="夕方の散歩", image=str(still))
    assert ready["status"] == "ready"
    assert ready["blocked"] == []
    path = bake.write_job(ready, tmp_path / "job")
    saved = json.loads(path.read_text(encoding="utf-8"))
    assert "python3 h3-runner/run_h3.py" in saved["commands"][2]
    assert "--task fl2va" in saved["commands"][2]
    assert f"--image {still}" in saved["commands"][2]
    assert "すず丸" not in path.read_text(encoding="utf-8")


def test_interview_stays_one_generation_and_blocks_without_lines(tmp_path: Path) -> None:
    still = tmp_path / "still.jpg"
    still.write_bytes(b"jpeg")
    job = bake.bake_reference(
        "nuts0629",
        mode="interview",
        theme="夕方の散歩",
        image=str(still),
    )
    assert job["duration_s"] == 8
    assert job["aspect"] == "16:9"
    assert _ids(job) == ["ask", "answer"]
    assert len(job["clips"]) == 1
    assert job["clips"][0]["trim_s"] == 8
    assert job["clips"][0]["cut_ids"] == ["ask", "answer"]
    assert job["status"] == "blocked"
    assert any("台詞" in reason for reason in job["blocked"])


def test_asmr_repeats_four_cuts_of_eight_seconds() -> None:
    job = bake.bake_reference("nuts0629", mode="asmr", theme="夕方の散歩")
    assert job["duration_s"] == 32
    assert [cut["duration_s"] for cut in job["cuts"]] == [8, 8, 8, 8]
    assert [clip["trim_s"] for clip in job["clips"]] == [8, 8, 8, 8]
    assert sum(clip["trim_s"] for clip in job["clips"]) == 32


def test_talk_does_not_invent_the_missing_seconds() -> None:
    job = bake.bake_reference("nuts0629", mode="talk", theme="夕方の散歩")
    assert job["clips"] == []
    assert any("足さない" in reason for reason in job["blocked"])
    assert job["cuts"][0]["end_s"] == 19


def test_beauty_is_three_ten_second_cuts_without_the_cover() -> None:
    job = bake.bake_reference("the.care.logic", theme="夕方の散歩")
    assert job["duration_s"] == 30
    assert _ids(job) == ["problem", "action", "result"]
    assert [clip["trim_s"] for clip in job["clips"]] == [10, 10, 10]
    assert job["aspect"] == "9:16"
    look = job["look"]["ja"]
    assert all(look in clip["prompt"] for clip in job["clips"])
    assert all("画面の文字は" in clip["prompt"] for clip in job["clips"])


def test_long_templates_keep_their_runtime_and_split_only_for_h3() -> None:
    cats = bake.bake_reference("junjun_ranran", theme="夕方の散歩")
    assert cats["duration_s"] == 45
    assert _ids(cats) == ["hook", "argument", "punch"]
    assert sum(clip["trim_s"] for clip in cats["clips"]) == 45
    hook = cats["clips"][0]
    assert hook["trim_s"] == 3
    assert hook["request_s"] == 5
    assert all(bake._accepts(clip["request_s"]) for clip in cats["clips"])

    drama = bake.bake_reference("yako.shiawasekon", theme="夕方の散歩")
    assert drama["duration_s"] == 60
    assert sum(clip["trim_s"] for clip in drama["clips"]) == 60
    assert all(5 <= clip["request_s"] <= 15 for clip in drama["clips"])
    assert all(bake._accepts(clip["request_s"]) for clip in drama["clips"])


def test_look_is_the_same_on_every_clip_and_likeness_stops() -> None:
    job = bake.bake_genre("見守りカメラ", theme="夕方の散歩")
    assert all(job["look"]["ja"] in clip["prompt"] for clip in job["clips"])
    assert all(job["look"]["en"] in clip["prompt"] for clip in job["clips"])
    assert job["source"] == "genre"
    assert job["seconds_from"] == "reference-template"
    assert job["duration_s"] == 45
    try:
        bake.bake_reference("nuts0629", mode="dance", theme="すず丸のまね")
    except ValueError as exc:
        assert "すず丸" in str(exc)
    else:
        raise AssertionError("likeness was accepted")


def test_genre_table_does_not_change_the_cut_clock() -> None:
    job = bake.bake_genre("ドッグフード", theme="夕方の散歩")
    before = [cut["duration_s"] for cut in job["cuts"]]
    bake.annotate_table(
        job,
        duration_band="31〜60秒",
        opening_type="その他",
        main_subject="動物",
        face_shown="なし",
        basis="伸びてる群の傾向",
        account_confidence="弱い",
        homage={"first_3_seconds": "同じ子", "borrow": ["同じ子を最初から出す"], "do_not_copy": ["すず丸本人"]},
    )
    assert [cut["duration_s"] for cut in job["cuts"]] == before
    assert job["genre_table"]["duration_band"] == "31〜60秒"
    assert job["duration_s"] == 8
    assert "すず丸" not in job["clips"][0]["prompt"]


def test_h3_acceptance_matches_the_runner_when_it_is_installed() -> None:
    from h3_runner.official import diffusers_accepts, frames_for_seconds

    for seconds in (5, 8, 10, 13.5, 14, 15):
        assert bake._accepts(seconds) is bool(diffusers_accepts(frames_for_seconds(seconds)))
