import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "h3-lora-studio" / "scripts" / "dump_grok_prompts.py"
INDEX = ROOT / "h3-lora-studio" / "GROK_PROMPTS.md"
DUMP = ROOT / "h3-lora-studio" / "dump" / "G_h3_prompts.txt"
STORIES = ROOT / "h3-lora-studio" / "stories"


def test_grok_prompt_pack_is_current():
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--check"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    index = INDEX.read_text(encoding="utf-8")
    dump = DUMP.read_text(encoding="utf-8")
    missing = [p.name for p in sorted(STORIES.glob("*.json")) if p.stem not in index]
    assert not missing, missing
    assert "ANAL HOLE LOCK" in dump
    assert "##### GENERATED anal-p3-meet-anal" in dump
    assert "G_hq_boot" in index
    assert "触るな" in index or "Do not open HQ dumps" in dump
