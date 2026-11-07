from pathlib import Path


def test_scheduler_script_registers_the_runner_and_does_not_start_it_by_default():
    script = Path(__file__).resolve().parents[1] / "queue" / "register_task_scheduler.ps1"
    text = script.read_text(encoding="utf-8")
    assert "schtasks.exe" in text
    assert "queue_runner.py" in text
    assert "GrokbuildQueueRunner" in text
    assert "[switch]$RunNow" in text
    assert "if ($RunNow)" in text
