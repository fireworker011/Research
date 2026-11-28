import json
import re
from pathlib import Path

from grokbuild.qa.age_gate import judge
from grokbuild.qa.observations import load_jsonl, parse_case
from grokbuild.qa.report_runner import (
    MAX_QA_SEC,
    clamp_qa_deadline,
    main,
    run_report,
)
from grokbuild.qa.samples import passing_image

FACE_BOX = [200, 80, 80, 80]


def _case(age_10=34, age_15=36, **extra) -> dict:
    payload = {
        "width": 512,
        "height": 768,
        "crop_1_0": [{"box": FACE_BOX, "age_years": age_10, "detected": True}],
        "crop_1_5": [{"box": FACE_BOX, "age_years": age_15, "detected": True}],
        "anatomy": {
            "observed": True,
            "skeleton_ok": True,
            "finger_counts": [5, 5],
            "finger_defect": False,
            "limb_count": 4,
            "extra_limb": False,
            "disconnected_limb": False,
        },
        "fixes_used": 0,
    }
    payload.update(extra)
    return payload


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def _read_rows(path: Path) -> list[list[int]]:
    text = path.read_text(encoding="utf-8")
    assert re.fullmatch(r"[0-9\t\n]+", text)
    return [[int(cell) for cell in line.split("\t")] for line in text.splitlines()]


def test_golden_batch_writes_14_numeric_rows_and_passes(tmp_path: Path):
    _write_jsonl(tmp_path / "in.jsonl", [_case(mosaic=True)])
    result = run_report(load_jsonl(tmp_path / "in.jsonl"), tmp_path / "out", inspector_5=1)
    assert result.exit_code == 0
    assert result.cutoff is False
    rows = _read_rows(tmp_path / "out" / "qa_results.tsv")
    assert len(rows) == 14
    assert all(row[5] == 1 for row in rows)
    assert not (tmp_path / "out" / "HANDOFF.md").exists()
    assert "mosaic" not in (tmp_path / "out" / "qa_results.tsv").read_text(encoding="utf-8")


def test_mosaic_flag_does_not_rescue_an_underage_record(tmp_path: Path):
    cases = load_jsonl_from(tmp_path, [_case(age_10=18, mosaic=True)])
    result = run_report(cases, tmp_path / "out", inspector_5=1)
    assert result.exit_code == 2
    age = result.rows[0]
    assert age[0] == 1 and age[3] == 1 and age[5] == 0
    assert not (tmp_path / "out" / "HANDOFF.md").exists()


def test_missing_inspector_5_fails_closed(tmp_path: Path):
    result = run_report(load_jsonl_from(tmp_path, [_case()]), tmp_path / "out", inspector_5=None)
    inspector_5 = next(row for row in result.rows if row[0] == 2 and row[1] == 5)
    assert inspector_5 == (2, 5, 0, 1, 1, 0)
    assert result.exit_code == 2


def test_bool_inspector_5_is_not_a_pass(tmp_path: Path):
    result = run_report(load_jsonl_from(tmp_path, [_case()]), tmp_path / "out", inspector_5=True)  # type: ignore[arg-type]
    assert result.exit_code == 2


def test_empty_batch_does_not_pass(tmp_path: Path):
    result = run_report([], tmp_path / "out", inspector_5=1)
    assert result.exit_code == 2
    assert result.rows[0] == (1, 0, 0, 0, 0, 0)


def test_deadline_cannot_be_raised_and_cutoff_removes_a_stale_table(tmp_path: Path):
    assert clamp_qa_deadline(10**9) == float(MAX_QA_SEC)
    assert clamp_qa_deadline(-5) == float(MAX_QA_SEC)
    out = tmp_path / "out"
    out.mkdir()
    stale = out / "qa_results.tsv"
    stale.write_text("1\t0\t1\t0\t1\t1\n", encoding="utf-8")
    calls = {"n": 0}

    def clock() -> float:
        calls["n"] += 1
        return 0.0 if calls["n"] == 1 else 20000.0

    result = run_report(
        load_jsonl_from(tmp_path, [_case()]),
        out,
        inspector_5=1,
        deadline_sec=10**9,
        clock=clock,
    )
    assert result.exit_code == 3
    assert result.cutoff is True
    assert not stale.exists()
    handoff = (out / "HANDOFF.md").read_text(encoding="utf-8")
    assert "reason: qa_deadline" in handoff
    assert "source: qa" in handoff


def test_malformed_line_is_counted_as_a_failure(tmp_path: Path):
    path = tmp_path / "in.jsonl"
    path.write_text("{not json}\n" + json.dumps(_case()) + "\n", encoding="utf-8")
    result = run_report(load_jsonl(path), tmp_path / "out", inspector_5=1)
    assert result.exit_code == 2
    assert result.rows[0][3] >= 1


def test_cli_refuses_image_suffixes(tmp_path: Path):
    image = tmp_path / "face.png"
    image.write_bytes(b"\x89PNG\r\n")
    code = main(["--input", str(image), "--out", str(tmp_path / "out")])
    assert code == 2
    assert not (tmp_path / "out" / "qa_results.tsv").exists()


def test_parser_ignores_mosaic_and_keeps_the_age():
    parsed = parse_case(_case(age_15=20.999, mosaic=True))
    assert parsed.broken is False
    assert parsed.image.crop_1_5[0].age_years == 20.999
    assert judge_passes(parsed) is False


def judge_passes(parsed) -> bool:
    return judge(parsed.image).passed


def load_jsonl_from(tmp_path: Path, rows: list[dict]):
    path = tmp_path / "cases.jsonl"
    _write_jsonl(path, rows)
    return load_jsonl(path)


def test_passing_sample_matches_the_gate():
    from grokbuild.qa.age_gate import judge
    from grokbuild.qa.codes import AGE_OK

    assert judge(passing_image()).code == AGE_OK
