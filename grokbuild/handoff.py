"""Write the cutoff record for a job that hit its attempt or time cap."""

from __future__ import annotations

from pathlib import Path

REASONS = frozenset({"timeout", "max_attempts", "missing_job", "qa_deadline"})


def write_handoff(
    path: Path,
    *,
    source: str,
    job: str,
    reason: str,
    attempts: int,
    elapsed_sec: float,
    exit_code: int,
) -> None:
    if reason not in REASONS:
        raise ValueError(f"unknown handoff reason: {reason}")
    if type(attempts) is not int or type(exit_code) is not int:
        raise TypeError("attempts and exit_code must be ints")
    path.parent.mkdir(parents=True, exist_ok=True)
    body = "\n".join(
        (
            "# HANDOFF",
            f"source: {_one_line(source)}",
            f"job: {_one_line(job)}",
            f"reason: {reason}",
            f"attempts: {attempts}",
            f"elapsed_sec: {int(elapsed_sec)}",
            f"exit_code: {exit_code}",
            "",
        )
    )
    path.write_text(body, encoding="utf-8")


def clear_handoff(path: Path) -> None:
    if path.is_file():
        path.unlink()


def _one_line(value: str) -> str:
    return value.replace("\r", " ").replace("\n", " ")
