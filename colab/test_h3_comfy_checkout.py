"""A broken ComfyUI folder must be removed before the next clone."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from h3_i2v_runtime import (
    clone_comfy,
    comfy_checkout_ok,
    comfy_launch_cmd,
    discard_broken_comfy,
    execution_error_text,
)


def test_broken_folder_is_removed(tmp_path: Path) -> None:
    comfy = tmp_path / "ComfyUI"
    comfy.mkdir()
    (comfy / "models").mkdir()
    (comfy / "models" / "note.txt").write_text("partial", encoding="utf-8")
    assert discard_broken_comfy(comfy) is True
    assert not comfy.exists()


def test_good_checkout_is_kept(tmp_path: Path) -> None:
    comfy = tmp_path / "ComfyUI"
    comfy.mkdir()
    (comfy / "main.py").write_text("print(1)\n", encoding="utf-8")
    assert discard_broken_comfy(comfy) is False
    assert comfy_checkout_ok(comfy)


def test_failed_clone_stops(tmp_path: Path) -> None:
    comfy = tmp_path / "ComfyUI"
    comfy.mkdir()
    (comfy / "leftover").write_text("x", encoding="utf-8")

    def fail(cmd: list[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(cmd, 1, "", "destination path already exists")

    try:
        clone_comfy(comfy, fail)
    except SystemExit as exc:
        assert "取得に失敗" in str(exc)
    else:
        raise AssertionError("clone failure did not stop")
    assert not comfy.exists()


def test_40gb_launch_does_not_pin_all_weights() -> None:
    cmd = comfy_launch_cmd(port=8188, low_vram=True)
    assert "--highvram" not in cmd
    assert "--highvram" in comfy_launch_cmd(port=8188, low_vram=False)


def test_execution_error_is_visible_even_when_marked_completed() -> None:
    text = execution_error_text(
        {
            "status": {
                "completed": True,
                "messages": [["execution_error", {"exception_message": "codec"}]],
            }
        }
    )
    assert "codec" in text


def test_clone_that_writes_main_py_passes(tmp_path: Path) -> None:
    comfy = tmp_path / "ComfyUI"

    def ok(cmd: list[str]) -> subprocess.CompletedProcess[str]:
        comfy.mkdir()
        (comfy / "main.py").write_text("print(1)\n", encoding="utf-8")
        return subprocess.CompletedProcess(cmd, 0)

    clone_comfy(comfy, ok)
    assert comfy_checkout_ok(comfy)
