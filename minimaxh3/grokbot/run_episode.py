#!/usr/bin/env python3
"""Grokbot / Cursor one-shot: render a whole episode on Colab via the official colab CLI, then stop.

    python minimaxh3/grokbot/run_episode.py --episode bandai-district [--preset daily] [--fresh] [--dry-run]

Not an Automation. One explicit run = one finished mp4 under Drive episodes/<slug>/final/.
The production T2V / I2V / R2V runners and their inbox are not involved.
"""

from __future__ import annotations

import argparse
import os
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve()
for p in (HERE.parents[1], HERE.parents[2] / "colab"):
    if p.is_dir():
        sys.path.insert(0, str(p))

from h3_colab_cli import exec_file, mount_drive, orchestrate_commands, start_session, stop_session  # noqa: E402
from h3_episode import EPISODE_HELPERS, PRESETS, SLUG_RE, EpisodeError  # noqa: E402

DEFAULT_BRANCH = "cursor/h3-episode-oneclick-f112"
REPO = "fireworker011/Research"


def exec_script(slug: str, *, preset: str, fresh: bool, branch: str, main_path: Path, repo: str = REPO) -> str:
    """The file `colab exec` runs. Self-contained: fetches helpers into /content, bakes env, runs the main.

    Env is baked in because the CLI does not forward the local environment.
    """
    raw = f"https://raw.githubusercontent.com/{repo}/{branch}"
    return (
        "import os, runpy, shutil, sys, urllib.request\n"
        "from pathlib import Path\n"
        f"os.environ['H3_EPISODE'] = {slug!r}\n"
        f"os.environ['H3_EPISODE_PRESET'] = {preset!r}\n"
        f"os.environ['H3_EPISODE_FRESH'] = {('1' if fresh else '0')!r}\n"
        f"os.environ['H3_HELPER_BRANCH'] = {branch!r}\n"
        "os.environ.setdefault('H3_DRIVE_ROOT', '/content/drive/MyDrive/minimax-h3-comfyui')\n"
        "lib = Path(os.environ['H3_DRIVE_ROOT']) / 'episodes' / '_lib'\n"
        "lib.mkdir(parents=True, exist_ok=True)\n"
        f"for rel in {list(EPISODE_HELPERS)!r}:\n"
        "    name = Path(rel).name\n"
        "    dest = Path('/content') / name\n"
        "    try:\n"
        f"        urllib.request.urlretrieve(f'{raw}/' + rel, dest)\n"
        "    except Exception as e:\n"
        "        print('fetch fail', rel, e)\n"
        "    if not dest.is_file() and (lib / name).is_file():\n"
        "        shutil.copy2(lib / name, dest)\n"
        "    if not dest.is_file():\n"
        "        raise SystemExit('helper missing: ' + name)\n"
        "    shutil.copy2(dest, lib / name)\n"
        "sys.path.insert(0, '/content')\n"
        f"runpy.run_path({str(main_path)!r}, run_name='__main__')\n"
    )


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="One-click H3 episode on Colab")
    p.add_argument("--episode", required=True, help="slug under minimaxh3/episodes and Drive episodes/")
    p.add_argument("--preset", default="", choices=["", *PRESETS], help="override episode.json render.preset")
    p.add_argument("--fresh", action="store_true", help="re-render beats that already have raw clips")
    p.add_argument("--branch", default=os.environ.get("H3_HELPER_BRANCH") or DEFAULT_BRANCH)
    p.add_argument("--gpu", default=os.environ.get("H3_COLAB_GPU") or "A100")
    p.add_argument("--session", default="h3-episode")
    p.add_argument("--keep-runtime", action="store_true")
    p.add_argument("--dry-run", action="store_true", help="print the colab commands, do not start a runtime")
    args = p.parse_args(argv)
    if not SLUG_RE.match(args.episode):
        raise EpisodeError(f"bad slug {args.episode!r}")
    main_path = Path("/content/h3_episode_colab_main.py")
    script = exec_script(args.episode, preset=args.preset, fresh=args.fresh, branch=args.branch, main_path=main_path)
    with tempfile.NamedTemporaryFile("w", suffix="_h3_episode.py", delete=False, encoding="utf-8") as fh:
        fh.write(script)
        local = Path(fh.name)
    if args.dry_run:
        print(script)
        for cmd in orchestrate_commands(local, gpu=args.gpu, name=args.session):
            print("colab", " ".join(cmd))
        return 0
    try:
        start_session(name=args.session, gpu=args.gpu)
        mount_drive(name=args.session)
        exec_file(local, name=args.session)
    finally:
        if not args.keep_runtime:
            stop_session(name=args.session)
    print("Drive: minimax-h3-comfyui/episodes/" + args.episode + "/final/latest.mp4")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
