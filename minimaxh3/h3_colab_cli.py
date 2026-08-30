"""Thin wrapper around the official Google Colab CLI (Linux/macOS)."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Callable, Sequence

Runner = Callable[..., subprocess.CompletedProcess[str]]


def colab_bin() -> str:
    path = shutil.which("colab")
    if not path:
        raise RuntimeError(
            "colab CLI がありません。Linux/macOS で `pip install google-colab-cli`。"
            "Windows 本体では動かないので WSL か Cursor Cloud を使う。"
        )
    return path


def run_colab(
    args: Sequence[str],
    *,
    runner: Runner | None = None,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    cmd = [colab_bin(), *args]
    fn = runner or subprocess.run
    proc = fn(cmd, check=False, text=True, capture_output=True)
    if check and proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "")[-4000:]
        raise RuntimeError(f"colab {' '.join(args)} failed ({proc.returncode}): {err}")
    return proc


def start_session(*, name: str = "h3-i2v", gpu: str = "A100", high_mem: bool = True, runner: Runner | None = None) -> None:
    args = ["new", "-s", name, "--gpu", gpu]
    if high_mem:
        args.append("--high-mem")
    run_colab(args, runner=runner)


def mount_drive(*, name: str = "h3-i2v", runner: Runner | None = None) -> None:
    run_colab(["drivemount", "-s", name], runner=runner)


def exec_file(path: Path | str, *, name: str = "h3-i2v", runner: Runner | None = None) -> subprocess.CompletedProcess[str]:
    return run_colab(["exec", "-s", name, "-f", str(path)], runner=runner)


def download(remote: str, local: Path | str, *, name: str = "h3-i2v", runner: Runner | None = None) -> None:
    Path(local).parent.mkdir(parents=True, exist_ok=True)
    run_colab(["download", "-s", name, remote, str(local)], runner=runner)


def stop_session(*, name: str = "h3-i2v", runner: Runner | None = None) -> None:
    run_colab(["stop", "-s", name], runner=runner, check=False)


def orchestrate_commands(
    script: Path | str,
    *,
    gpu: str = "A100",
    name: str = "h3-i2v",
    high_mem: bool = True,
) -> list[list[str]]:
    """Command lists Grokbot runs in order. Last is always stop."""
    new = ["new", "-s", name, "--gpu", gpu]
    if high_mem:
        new.append("--high-mem")
    return [
        new,
        ["drivemount", "-s", name],
        ["exec", "-s", name, "-f", str(script)],
        ["stop", "-s", name],
    ]
