"""Run the four allowlisted queue jobs in numeric order.

Each job is a local Python process. The attempt count is capped at 3 and the
per-job budget is capped at 3600 seconds. Callers cannot raise either cap.
A timeout, a third failure, or a missing script writes out/HANDOFF.md and
does not start the remaining jobs.

Jobs 30 and 30b are not in this allowlist.
"""

from __future__ import annotations

import argparse
import math
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from grokbuild.handoff import clear_handoff, write_handoff

MAX_ATTEMPTS = 3
MAX_JOB_SEC = 3600
JOB_NAMES = (
    "1-takasou",
    "2-nurse_engagement_job",
    "3-order21-mosaic",
    "4-order19-eagle",
)
EXIT_OK = 0
EXIT_HANDOFF = 3
NOT_STARTED = -1
TIMED_OUT = -2
TABLE_NAME = "queue_results.tsv"


@dataclass(frozen=True, slots=True)
class JobOutcome:
    index: int
    attempts: int
    exit_code: int
    ok: int


@dataclass(frozen=True, slots=True)
class QueueRun:
    outcomes: tuple[JobOutcome, ...]
    exit_code: int
    handoff_reason: str | None
    already_running: int


def clamp_attempts(value: int) -> int:
    if type(value) is not int or value < 1 or value > MAX_ATTEMPTS:
        return MAX_ATTEMPTS
    return value


def clamp_job_timeout(value: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return float(MAX_JOB_SEC)
    number = float(value)
    if not math.isfinite(number) or number <= 0 or number > MAX_JOB_SEC:
        return float(MAX_JOB_SEC)
    return number


def default_root() -> Path:
    env = os.environ.get("GROKBUILD_ROOT")
    if env:
        return Path(env)
    return Path(__file__).resolve().parents[1]


def resolve_job_script(queue: Path, name: str) -> Path | None:
    candidates = (
        queue / f"{name}.py",
        queue / name / "run.py",
        queue / name / "main.py",
        queue / name / "__main__.py",
    )
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


def run_queue(
    root: Path,
    *,
    timeout_sec: float = MAX_JOB_SEC,
    max_attempts: int = MAX_ATTEMPTS,
    runner=None,
    clock=time.monotonic,
    python: str | None = None,
) -> QueueRun:
    root = Path(root)
    out = root / "out"
    out.mkdir(parents=True, exist_ok=True)
    lock = out / "queue.lock"
    if not _acquire_lock(lock):
        return QueueRun((), EXIT_OK, None, 1)
    try:
        return _run_locked(
            root,
            timeout_sec=clamp_job_timeout(timeout_sec),
            max_attempts=clamp_attempts(max_attempts),
            runner=runner,
            clock=clock,
            python=python or sys.executable,
        )
    finally:
        _release_lock(lock)


def render_queue(outcomes: tuple[JobOutcome, ...]) -> str:
    lines: list[str] = []
    for item in outcomes:
        cells = (item.index, item.attempts, item.exit_code, item.ok)
        if any(type(cell) is not int for cell in cells):
            raise TypeError("queue cells must be ints")
        lines.append("\t".join(str(cell) for cell in cells))
    if not lines:
        return ""
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the allowlisted grokbuild queue.")
    parser.add_argument("--root", default="")
    parser.add_argument("--timeout-sec", type=float, default=float(MAX_JOB_SEC))
    parser.add_argument("--max-attempts", type=int, default=MAX_ATTEMPTS)
    args = parser.parse_args(argv)
    root = Path(args.root) if args.root else default_root()
    result = run_queue(root, timeout_sec=args.timeout_sec, max_attempts=args.max_attempts)
    return result.exit_code


def _run_locked(
    root: Path,
    *,
    timeout_sec: float,
    max_attempts: int,
    runner,
    clock,
    python: str,
) -> QueueRun:
    queue = root / "queue"
    out = root / "out"
    handoff_path = out / "HANDOFF.md"
    clear_handoff(handoff_path)
    active = runner or _subprocess_runner(python, out)
    outcomes: list[JobOutcome] = []
    handoff_reason: str | None = None
    stopped = False
    for index, name in enumerate(JOB_NAMES, start=1):
        if stopped:
            outcomes.append(JobOutcome(index, 0, NOT_STARTED, 0))
            continue
        script = resolve_job_script(queue, name)
        if script is None:
            outcomes.append(JobOutcome(index, 0, NOT_STARTED, 0))
            handoff_reason = "missing_job"
            write_handoff(
                handoff_path,
                source="queue",
                job=name,
                reason="missing_job",
                attempts=0,
                elapsed_sec=0,
                exit_code=NOT_STARTED,
            )
            stopped = True
            continue
        outcome, reason = _run_job(
            script,
            index=index,
            name=name,
            timeout_sec=timeout_sec,
            max_attempts=max_attempts,
            runner=active,
            clock=clock,
            handoff_path=handoff_path,
        )
        outcomes.append(outcome)
        if reason is not None:
            handoff_reason = reason
            stopped = True
    table = tuple(outcomes)
    (out / TABLE_NAME).write_text(render_queue(table), encoding="utf-8")
    if handoff_reason is None:
        clear_handoff(handoff_path)
        return QueueRun(table, EXIT_OK, None, 0)
    return QueueRun(table, EXIT_HANDOFF, handoff_reason, 0)


def _run_job(
    script: Path,
    *,
    index: int,
    name: str,
    timeout_sec: float,
    max_attempts: int,
    runner,
    clock,
    handoff_path: Path,
) -> tuple[JobOutcome, str | None]:
    start = float(clock())
    attempts = 0
    code = NOT_STARTED
    reason: str | None = None
    while attempts < max_attempts:
        remaining = timeout_sec - (float(clock()) - start)
        if remaining <= 0:
            code = TIMED_OUT
            reason = "timeout"
            break
        attempts += 1
        try:
            produced = runner(script, remaining)
            code = int(produced)
        except subprocess.TimeoutExpired:
            code = TIMED_OUT
            reason = "timeout"
            break
        except (TypeError, ValueError):
            code = 1
        if code == 0:
            return JobOutcome(index, attempts, 0, 1), None
    if reason is None:
        reason = "max_attempts"
    write_handoff(
        handoff_path,
        source="queue",
        job=name,
        reason=reason,
        attempts=attempts,
        elapsed_sec=max(0.0, float(clock()) - start),
        exit_code=code,
    )
    return JobOutcome(index, attempts, code, 0), reason


def _subprocess_runner(python: str, out: Path):
    def _run(script: Path, timeout: float) -> int:
        log_path = out / f"job_{_job_index(script)}.log"
        try:
            completed = subprocess.run(
                [python, str(script)],
                cwd=str(script.parent),
                timeout=timeout,
                check=False,
                capture_output=True,
            )
        except subprocess.TimeoutExpired as exc:
            _write_log(log_path, exc.stdout, exc.stderr)
            raise
        _write_log(log_path, completed.stdout, completed.stderr)
        return int(completed.returncode)

    return _run


def _job_index(script: Path) -> int:
    candidates = {script.stem, script.parent.name}
    for index, name in enumerate(JOB_NAMES, start=1):
        if name in candidates:
            return index
    return 0


def _write_log(path: Path, stdout: bytes | str | None, stderr: bytes | str | None) -> None:
    chunks: list[bytes] = []
    for part in (stdout, stderr):
        if part is None:
            continue
        if isinstance(part, str):
            chunks.append(part.encode("utf-8", errors="replace"))
        else:
            chunks.append(part)
    path.write_bytes(b"\n".join(chunks))


def _acquire_lock(lock: Path) -> bool:
    if lock.exists():
        try:
            pid = int(lock.read_text(encoding="utf-8").strip())
        except (OSError, ValueError):
            pid = -1
        if _pid_alive(pid):
            return False
    lock.write_text(str(os.getpid()), encoding="utf-8")
    return True


def _release_lock(lock: Path) -> None:
    try:
        current = int(lock.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        return
    if current == os.getpid():
        lock.unlink(missing_ok=True)


def _pid_alive(pid: int) -> bool:
    if type(pid) is not int or pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False
    return True


if __name__ == "__main__":
    raise SystemExit(main())
