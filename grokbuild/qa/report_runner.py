"""Aggregate age, inspectors 1-6, and red-team 1-7 into a numeric table.

The table file has no header and no words. Columns are
kind_id, check_id, pass_count, fail_count, total, ok.
kind_id 1 is age, 2 is an inspector, 3 is a red-team case.
Inspector 5 is not executed; a missing result stays a failure.
The run stops at 4 hours and then writes HANDOFF.md instead of a pass table.
"""

from __future__ import annotations

import argparse
import sys
import time
from dataclasses import dataclass
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from grokbuild.handoff import clear_handoff, write_handoff
from grokbuild.qa.age_gate import judge
from grokbuild.qa.codes import AGE_OK
from grokbuild.qa.inspectors import (
    inspector_1,
    inspector_2,
    inspector_3,
    inspector_4,
    inspector_6,
)
from grokbuild.qa.observations import ParsedCase, load_jsonl
from grokbuild.qa.redteam import cases as redteam_cases

MAX_QA_SEC = 4 * 60 * 60
KIND_AGE = 1
KIND_INSPECTOR = 2
KIND_REDTEAM = 3
EXIT_OK = 0
EXIT_CHECKS = 2
EXIT_CUTOFF = 3
TABLE_NAME = "qa_results.tsv"

Row = tuple[int, int, int, int, int, int]


@dataclass(frozen=True, slots=True)
class AggregateResult:
    rows: tuple[Row, ...]
    exit_code: int
    cutoff: bool
    processed: int
    elapsed_sec: float


def clamp_qa_deadline(value: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return float(MAX_QA_SEC)
    number = float(value)
    if number != number or number in (float("inf"), float("-inf")):
        return float(MAX_QA_SEC)
    if number < 0:
        return float(MAX_QA_SEC)
    if number > MAX_QA_SEC:
        return float(MAX_QA_SEC)
    return number


def aggregate(
    cases: list[ParsedCase],
    *,
    inspector_5: int | None = None,
    deadline_sec: float = MAX_QA_SEC,
    clock=time.monotonic,
) -> AggregateResult:
    deadline = clamp_qa_deadline(deadline_sec)
    start = float(clock())
    age_pass = 0
    age_fail = 0
    processed = 0
    counts = {check_id: [0, 0] for check_id in (1, 2, 3, 4, 6)}
    for case in cases:
        if _expired(start, deadline, clock):
            return _cutoff(start, clock, processed)
        if judge(case.image).code == AGE_OK:
            age_pass += 1
        else:
            age_fail += 1
        flags = {
            1: inspector_1(case.image),
            2: inspector_2(case.image),
            3: inspector_3(case.image.anatomy),
            4: inspector_4(case.image),
            6: inspector_6(case.image, fixes_used=case.fixes_used),
        }
        for check_id, passed in flags.items():
            counts[check_id][0 if passed else 1] += 1
        processed += 1
    rows: list[Row] = [_count_row(KIND_AGE, 0, age_pass, age_fail)]
    for check_id in (1, 2, 3, 4):
        passed, failed = counts[check_id]
        rows.append(_count_row(KIND_INSPECTOR, check_id, passed, failed))
    rows.append(_inspector_5_row(inspector_5))
    passed_6, failed_6 = counts[6]
    rows.append(_count_row(KIND_INSPECTOR, 6, passed_6, failed_6))
    for attack in redteam_cases():
        if _expired(start, deadline, clock):
            return _cutoff(start, clock, processed)
        blocked = inspector_6(attack.image, fixes_used=0) is False
        held = 1 if blocked else 0
        rows.append(_count_row(KIND_REDTEAM, attack.case_id, held, 1 - held))
    exit_code = EXIT_OK if all(row[5] == 1 for row in rows) else EXIT_CHECKS
    return AggregateResult(tuple(rows), exit_code, False, processed, _elapsed(start, clock))


def run_report(
    cases: list[ParsedCase],
    out_dir: Path,
    *,
    inspector_5: int | None = None,
    deadline_sec: float = MAX_QA_SEC,
    clock=time.monotonic,
) -> AggregateResult:
    out_dir.mkdir(parents=True, exist_ok=True)
    table_path = out_dir / TABLE_NAME
    handoff_path = out_dir / "HANDOFF.md"
    clear_handoff(handoff_path)
    result = aggregate(
        cases,
        inspector_5=inspector_5,
        deadline_sec=deadline_sec,
        clock=clock,
    )
    if result.cutoff:
        if table_path.exists():
            table_path.unlink()
        write_handoff(
            handoff_path,
            source="qa",
            job="qa",
            reason="qa_deadline",
            attempts=result.processed,
            elapsed_sec=result.elapsed_sec,
            exit_code=EXIT_CUTOFF,
        )
        return result
    table_path.write_text(render_rows(result.rows), encoding="utf-8")
    clear_handoff(handoff_path)
    return result


def render_rows(rows: tuple[Row, ...] | list[Row]) -> str:
    lines: list[str] = []
    for row in rows:
        if len(row) != 6 or any(type(cell) is not int for cell in row):
            raise TypeError("table cells must be ints")
        pass_count, fail_count, total, ok = row[2], row[3], row[4], row[5]
        if pass_count + fail_count != total:
            raise ValueError("pass_count + fail_count must equal total")
        if ok not in (0, 1):
            raise ValueError("ok must be 0 or 1")
        lines.append("\t".join(str(cell) for cell in row))
    if not lines:
        return ""
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Write the numeric QA table.")
    parser.add_argument("--input", required=True)
    parser.add_argument("--out", default="")
    parser.add_argument("--deadline-sec", type=float, default=float(MAX_QA_SEC))
    parser.add_argument("--inspector-5", dest="inspector_5", default=None)
    args = parser.parse_args(argv)
    source = Path(args.input)
    if source.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif", ".avif"}:
        print("image input is refused", file=sys.stderr)
        return EXIT_CHECKS
    try:
        cases = load_jsonl(source)
    except ValueError:
        print("image input is refused", file=sys.stderr)
        return EXIT_CHECKS
    if args.out:
        out = Path(args.out)
    else:
        out = Path(__file__).resolve().parents[1] / "out"
    result = run_report(
        cases,
        out,
        inspector_5=_normalize_inspector_5(args.inspector_5),
        deadline_sec=args.deadline_sec,
    )
    return result.exit_code


def _normalize_inspector_5(raw: str | None) -> int | None:
    if raw is None:
        return None
    if not raw.isascii() or not raw.isdecimal():
        return None
    return int(raw)


def _cutoff(start: float, clock, processed: int) -> AggregateResult:
    return AggregateResult((), EXIT_CUTOFF, True, processed, _elapsed(start, clock))


def _elapsed(start: float, clock) -> float:
    return max(0.0, float(clock()) - start)


def _expired(start: float, deadline: float, clock) -> bool:
    return _elapsed(start, clock) >= deadline


def _count_row(kind: int, check_id: int, pass_count: int, fail_count: int) -> Row:
    total = pass_count + fail_count
    if kind == KIND_REDTEAM:
        ok = 1 if pass_count == 1 and fail_count == 0 and total == 1 else 0
    elif total > 0 and fail_count == 0:
        ok = 1
    else:
        ok = 0
    return (kind, check_id, pass_count, fail_count, total, ok)


def _inspector_5_row(inspector_5: int | None) -> Row:
    if type(inspector_5) is int and inspector_5 == 1:
        return _count_row(KIND_INSPECTOR, 5, 1, 0)
    return _count_row(KIND_INSPECTOR, 5, 0, 1)


if __name__ == "__main__":
    raise SystemExit(main())
