"""Run the factory CLI against the reForge already running in this Colab session.

The factory package itself is not modified here. Patches already on Drive are
applied only when ``git apply --check`` accepts them. A patch that is already
in the tree, or that does not match, is left untouched.

Completed jobs are those ``outputs/job_state.json`` marks done and whose
generated PNG is already on Drive. A new session skips those and appends the
log under ``logs/``.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path("/content/gdrive/MyDrive/sd-diff-set")
API = "http://127.0.0.1:7860"
WEBUI = Path("/content/stable-diffusion-webui-reForge")
EXTENSION = WEBUI / "extensions" / "sd-diff-set"


def api_ready(api: str = API, timeout: float = 10) -> bool:
    try:
        with urllib.request.urlopen(api.rstrip("/") + "/sdapi/v1/memory", timeout=timeout) as response:
            return int(getattr(response, "status", 200)) < 500
    except (OSError, urllib.error.URLError):
        return False


def wait_for_api(api: str = API, seconds: float = 45 * 60) -> bool:
    deadline = time.time() + seconds
    while time.time() < deadline:
        if api_ready(api):
            return True
        print("API を待っています", api)
        time.sleep(10)
    return False


def completed_ids(state: object, generated: Path) -> set[str]:
    """Ids that already finished and still have a PNG on Drive."""
    rows = state.get("jobs") if isinstance(state, dict) else None
    done: set[str] = set()
    if not isinstance(rows, list):
        return done
    for row in rows:
        if not isinstance(row, dict) or row.get("status") != "done":
            continue
        job_id = str(row.get("id") or "")
        if not job_id:
            continue
        png = generated / f"{job_id}.png"
        try:
            ready = png.is_file() and png.stat().st_size > 0
        except OSError:
            ready = False
        if ready:
            done.add(job_id)
    return done


def pending_jobs(jobs: list[dict[str, object]], done: set[str]) -> list[dict[str, object]]:
    return [job for job in jobs if str(job.get("id") or "") not in done]


def load_jobs(path: Path) -> list[dict[str, object]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    rows = data.get("jobs") if isinstance(data, dict) else None
    if not isinstance(rows, list):
        raise ValueError(f"{path} に jobs の配列がありません")
    return [row for row in rows if isinstance(row, dict)]


def patch_action(check_code: int, reverse_code: int) -> str:
    """``apply`` when the patch fits, ``present`` when it is already there, else ``skip``."""
    if check_code == 0:
        return "apply"
    if reverse_code == 0:
        return "present"
    return "skip"


def cli_command(extension: Path, root: Path, jobs_path: Path, api: str = API) -> list[str]:
    """Flags the factory CLI already accepts. No new switches."""
    return [
        sys.executable,
        "-m",
        "sd_diff_set.cli",
        "factory",
        "--inbox",
        str(root / "outputs" / "inbox"),
        "--sorted",
        str(root / "outputs" / "sorted"),
        "--output",
        str(root / "outputs" / "diffs"),
        "--preset-dir",
        str(extension / "presets"),
        "--jobs",
        str(jobs_path),
        "--colab-api",
        api,
        "--local-api",
        api,
        "--finish",
        "game",
        "--adult-ok",
        "--run",
        "--once",
    ]


def _git_apply(webui: Path, patch: Path, *extra: str) -> int:
    result = subprocess.run(
        ["git", "apply", *extra, "-p1", str(patch)],
        cwd=webui,
        capture_output=True,
        text=True,
    )
    return result.returncode


def apply_drive_patches(root: Path, webui: Path, extension: Path) -> None:
    """Apply ``patches/*.patch`` only when they match. Leave the tree alone otherwise."""
    patches = sorted((root / "patches").glob("*.patch"))
    if not patches:
        print("patches/ にパッチはありません")
        return
    if not (extension / "sd_diff_set" / "ui.py").is_file():
        print("工場の拡張がまだ無いので、パッチは飛ばします")
        return
    record_path = root / "logs" / "patches-applied.json"
    try:
        record = json.loads(record_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        record = {}
    applied = record.get("applied") if isinstance(record, dict) and isinstance(record.get("applied"), dict) else {}
    changed = False
    for patch in patches:
        digest = hashlib.sha256(patch.read_bytes()).hexdigest()
        if applied.get(patch.name) == digest:
            print("パッチ適用済み:", patch.name)
            continue
        action = patch_action(_git_apply(webui, patch, "--check"), _git_apply(webui, patch, "--reverse", "--check"))
        if action == "apply":
            if _git_apply(webui, patch) != 0:
                print("パッチは当てず、工場はそのままです:", patch.name)
                continue
            print("パッチを当てました:", patch.name)
            changed = True
        elif action == "present":
            print("パッチは入っています:", patch.name)
        else:
            print("パッチは一致しないので飛ばします:", patch.name)
            continue
        applied[patch.name] = digest
    record_path.parent.mkdir(parents=True, exist_ok=True)
    record_path.write_text(json.dumps({"applied": applied}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if changed:
        _keep_extension(extension, root / "extension")


def _keep_extension(extension: Path, drive_copy: Path) -> None:
    import shutil

    if drive_copy.exists():
        shutil.rmtree(drive_copy)
    shutil.copytree(extension, drive_copy, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".git"))
    print("パッチ済みの工場を Drive に残しました:", drive_copy)


def ensure_dirs(root: Path) -> None:
    for name in (
        "jobs",
        "patches",
        "logs",
        "outputs",
        "outputs/inbox",
        "outputs/sorted",
        "outputs/diffs",
        "outputs/generated",
    ):
        (root / name).mkdir(parents=True, exist_ok=True)


def run_jobs(root: Path = ROOT, extension: Path = EXTENSION, api: str = API) -> int:
    ensure_dirs(root)
    if not wait_for_api(api):
        print("reForge の API が開いていません:", api)
        return 2
    print("API:", api)
    apply_drive_patches(root, extension.parent.parent, extension)
    state_path = root / "outputs" / "job_state.json"
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        state = {}
    done = completed_ids(state, root / "outputs" / "generated")
    job_files = sorted((root / "jobs").glob("*.json"))
    if not job_files:
        print("jobs/ に JSON がありません")
        return 2
    preset = extension / "presets"
    if not preset.is_dir():
        print("presets がありません:", preset)
        return 2
    log = root / "logs" / "factory.log"
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    with log.open("a", encoding="utf-8") as handle:
        handle.write(f"\n# {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')} api={api}\n")
        for job_file in job_files:
            try:
                rows = load_jobs(job_file)
            except (OSError, json.JSONDecodeError, ValueError) as exc:
                print(job_file.name, exc)
                handle.write(f"{job_file.name}: {exc}\n")
                return 2
            pending = pending_jobs(rows, done)
            print(f"{job_file.name}: {len(pending)} 件実行、{len(rows) - len(pending)} 件は完了済み")
            handle.write(f"{job_file.name}: run {len(pending)} skip {len(rows) - len(pending)}\n")
            handle.flush()
            if not pending:
                continue
            run_file = root / "logs" / f".pending-{job_file.name}"
            run_file.write_text(json.dumps({"jobs": pending}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            command = cli_command(extension, root, run_file, api)
            print(" ".join(command))
            proc = subprocess.Popen(
                command,
                cwd=str(extension),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                env=env,
            )
            assert proc.stdout is not None
            for line in proc.stdout:
                sys.stdout.write(line)
                handle.write(line)
                handle.flush()
            code = proc.wait()
            handle.write(f"exit {code}\n")
            print("exit", code)
            if code != 0:
                return code
    print("工場CLIが終わりました。出力:", root / "outputs")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_jobs())
