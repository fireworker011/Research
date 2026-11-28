import os
import queue as stdlib_queue
import subprocess
import sys
from pathlib import Path

from grokbuild.queue import queue_runner
from grokbuild.queue.queue_runner import (
    MAX_ATTEMPTS,
    MAX_JOB_SEC,
    NOT_STARTED,
    TIMED_OUT,
    JobOutcome,
    clamp_attempts,
    clamp_job_timeout,
    resolve_job_script,
    run_queue,
)


def test_allowlist_is_the_four_jobs_and_leaves_stdlib_queue_alone():
    assert queue_runner.JOB_NAMES == (
        "1-takasou",
        "2-nurse_engagement_job",
        "3-order21-mosaic",
        "4-order19-eagle",
    )
    joined = " ".join(queue_runner.JOB_NAMES)
    assert "30b" not in joined
    assert "ken5" not in joined
    assert hasattr(stdlib_queue, "Queue")


def test_caps_cannot_be_raised():
    assert clamp_attempts(10) == MAX_ATTEMPTS
    assert clamp_attempts(0) == MAX_ATTEMPTS
    assert clamp_attempts(True) == MAX_ATTEMPTS  # type: ignore[arg-type]
    assert clamp_job_timeout(99999) == float(MAX_JOB_SEC)
    assert clamp_job_timeout(0) == float(MAX_JOB_SEC)
    assert clamp_job_timeout(float("inf")) == float(MAX_JOB_SEC)
    assert clamp_attempts(2) == 2
    assert clamp_job_timeout(12.5) == 12.5


def test_script_file_wins_over_a_directory_entrypoint(tmp_path: Path):
    queue = tmp_path / "queue"
    folder = queue / "1-takasou"
    folder.mkdir(parents=True)
    (folder / "run.py").write_text("raise SystemExit(7)\n", encoding="utf-8")
    script = queue / "1-takasou.py"
    script.write_text("raise SystemExit(0)\n", encoding="utf-8")
    assert resolve_job_script(queue, "1-takasou") == script


def test_jobs_run_in_order_and_a_stray_script_is_not_executed(tmp_path: Path):
    log = tmp_path / "order.txt"
    queue = tmp_path / "queue"
    queue.mkdir()
    for name in queue_runner.JOB_NAMES:
        _write_marker(queue / f"{name}.py", log, name)
    (queue / "evil.py").write_text(
        f"from pathlib import Path\nPath({str(log)!r}).open('a', encoding='utf-8').write('evil\\n')\n",
        encoding="utf-8",
    )
    result = run_queue(tmp_path, timeout_sec=30, max_attempts=3)
    assert result.exit_code == 0
    assert result.handoff_reason is None
    assert log.read_text(encoding="utf-8").splitlines() == list(queue_runner.JOB_NAMES)
    text = (tmp_path / "out" / "queue_results.tsv").read_text(encoding="utf-8")
    assert text == "1\t1\t0\t1\n2\t1\t0\t1\n3\t1\t0\t1\n4\t1\t0\t1\n"
    assert not (tmp_path / "out" / "HANDOFF.md").exists()


def test_third_success_continues_and_three_failures_stop_the_queue(tmp_path: Path):
    queue = tmp_path / "queue"
    queue.mkdir()
    (queue / "1-takasou.py").write_text(
        "from pathlib import Path\n"
        "p = Path(__file__).with_name('attempts.txt')\n"
        "n = int(p.read_text(encoding='utf-8')) if p.exists() else 0\n"
        "n += 1\n"
        "p.write_text(str(n), encoding='utf-8')\n"
        "raise SystemExit(0 if n >= 3 else 1)\n",
        encoding="utf-8",
    )
    for name in queue_runner.JOB_NAMES[1:]:
        (queue / f"{name}.py").write_text("raise SystemExit(0)\n", encoding="utf-8")
    result = run_queue(tmp_path, timeout_sec=30, max_attempts=10)
    assert result.exit_code == 0
    assert result.outcomes[0] == JobOutcome(1, 3, 0, 1)
    assert all(item.ok == 1 for item in result.outcomes)

    failed = tmp_path / "failed"
    failed_queue = failed / "queue"
    failed_queue.mkdir(parents=True)
    (failed_queue / "1-takasou.py").write_text("raise SystemExit(7)\n", encoding="utf-8")
    marker = failed_queue / "2-nurse_engagement_job.py"
    marker.write_text(
        "from pathlib import Path\nPath(__file__).with_name('ran').write_text('yes', encoding='utf-8')\n",
        encoding="utf-8",
    )
    for name in queue_runner.JOB_NAMES[2:]:
        (failed_queue / f"{name}.py").write_text("raise SystemExit(0)\n", encoding="utf-8")
    stopped = run_queue(failed, timeout_sec=30, max_attempts=9)
    assert stopped.exit_code == 3
    assert stopped.handoff_reason == "max_attempts"
    assert stopped.outcomes[0] == JobOutcome(1, 3, 7, 0)
    assert stopped.outcomes[1].exit_code == NOT_STARTED
    assert not (failed_queue / "ran").exists()
    handoff = (failed / "out" / "HANDOFF.md").read_text(encoding="utf-8")
    assert "job: 1-takasou" in handoff
    assert "reason: max_attempts" in handoff
    assert "attempts: 3" in handoff


def test_missing_job_writes_handoff_and_does_not_skip_ahead(tmp_path: Path):
    queue = tmp_path / "queue"
    queue.mkdir()
    (queue / "1-takasou.py").write_text("raise SystemExit(0)\n", encoding="utf-8")
    (queue / "3-order21-mosaic.py").write_text("raise SystemExit(0)\n", encoding="utf-8")
    result = run_queue(tmp_path, timeout_sec=30)
    assert result.handoff_reason == "missing_job"
    assert result.outcomes[1] == JobOutcome(2, 0, NOT_STARTED, 0)
    assert result.outcomes[2].exit_code == NOT_STARTED
    assert "job: 2-nurse_engagement_job" in (tmp_path / "out" / "HANDOFF.md").read_text(encoding="utf-8")


def test_directory_entrypoint_and_timeout_stop(tmp_path: Path):
    queue = tmp_path / "queue"
    folder = queue / "1-takasou"
    folder.mkdir(parents=True)
    (folder / "run.py").write_text("import time\ntime.sleep(30)\n", encoding="utf-8")
    for name in queue_runner.JOB_NAMES[1:]:
        target = queue / f"{name}.py"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("raise SystemExit(0)\n", encoding="utf-8")
    result = run_queue(tmp_path, timeout_sec=0.5, max_attempts=3)
    assert result.exit_code == 3
    assert result.handoff_reason == "timeout"
    assert result.outcomes[0].exit_code == TIMED_OUT
    assert result.outcomes[1].exit_code == NOT_STARTED


def test_live_lock_does_not_start_another_run(tmp_path: Path):
    out = tmp_path / "out"
    out.mkdir()
    (out / "queue.lock").write_text(str(os.getpid()), encoding="utf-8")
    (out / "queue_results.tsv").write_text("keep\n", encoding="utf-8")
    calls = {"n": 0}

    def runner(script, timeout):
        del script, timeout
        calls["n"] += 1
        return 0

    result = run_queue(tmp_path, runner=runner)
    assert result.already_running == 1
    assert result.exit_code == 0
    assert calls["n"] == 0
    assert (out / "queue_results.tsv").read_text(encoding="utf-8") == "keep\n"


def test_fake_timeout_hands_off_without_a_retry_past_the_budget(tmp_path: Path):
    queue = tmp_path / "queue"
    queue.mkdir()
    script = queue / "1-takasou.py"
    script.write_text("raise SystemExit(0)\n", encoding="utf-8")

    def runner(path, timeout):
        del path, timeout
        raise subprocess.TimeoutExpired(cmd=[sys.executable, "job"], timeout=1)

    result = run_queue(tmp_path, timeout_sec=30, runner=runner)
    assert result.handoff_reason == "timeout"
    assert result.outcomes[0].attempts == 1
    assert result.outcomes[0].exit_code == TIMED_OUT


def _write_marker(path: Path, log: Path, label: str) -> None:
    path.write_text(
        "from pathlib import Path\n"
        f"Path({str(log)!r}).open('a', encoding='utf-8').write({label!r} + '\\n')\n",
        encoding="utf-8",
    )
