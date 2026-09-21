#!/usr/bin/env python3
"""Grokbot / Cursor one-shot: render a whole episode on Colab via the official colab CLI, then stop.

    python minimaxh3/grokbot/run_episode.py --episode bandai-district [--preset balance] [--camera side2d] [--connect t2v] [--combat off] [--fresh] [--dry-run]

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
from h3_episode import CAMERA_PACKS, COMBAT_MODES, CONNECT_MODES, EPISODE_HELPERS, PRESETS, SLUG_RE, EpisodeError  # noqa: E402
from h3_episode_packs import (  # noqa: E402
    CAMERA_ALIASES,
    COMBAT_ALIASES,
    CONNECT_ALIASES,
    END_CONNECT_ALIASES,
    END_CONNECT_MODES,
    GIN_ALIASES,
    GIN_MODES,
    INVITE_JUPO_ALIASES,
    INVITE_JUPO_MODES,
    INVITE_KISS_ALIASES,
    INVITE_KISS_MODES,
    INVITE_POSE_ALIASES,
    INVITE_POSE_MODES,
    STORY_ALIASES,
    STORY_MODES,
    TOILET_ALIASES,
    TOILET_MODES,
    TSUNO_ALIASES,
    TSUNO_MODES,
)

DEFAULT_BRANCH = "cursor/h3-kasumi-adult-0402"
REPO = "fireworker011/Research"


def exec_script(slug: str, *, preset: str, fresh: bool, branch: str, main_path: Path, repo: str = REPO, camera: str = "", connect: str = "", end_connect: str = "", combat: str = "", story: str = "", invite_pose: str = "", invite_kiss: str = "", invite_jupo: str = "", toilet: str = "", gin: str = "", tsuno: str = "", appear: str = "", scenes: str = "") -> str:
    """The file `colab exec` runs. Self-contained: fetches helpers into /content, bakes env, runs the main.

    Env is baked in because the CLI does not forward the local environment.
    """
    raw = f"https://raw.githubusercontent.com/{repo}/{branch}"
    return (
        "import os, runpy, shutil, sys, urllib.request\n"
        "from pathlib import Path\n"
        f"os.environ['H3_EPISODE'] = {slug!r}\n"
        f"os.environ['H3_EPISODE_PRESET'] = {preset!r}\n"
        f"os.environ['H3_EPISODE_CAMERA'] = {camera!r}\n"
        f"os.environ['H3_EPISODE_CONNECT'] = {connect!r}\n"
        f"os.environ['H3_EPISODE_END_CONNECT'] = {end_connect!r}\n"
        f"os.environ['H3_EPISODE_COMBAT'] = {combat!r}\n"
        f"os.environ['H3_EPISODE_STORY'] = {story!r}\n"
        f"os.environ['H3_EPISODE_INVITE_POSE'] = {invite_pose!r}\n"
        f"os.environ['H3_EPISODE_INVITE_KISS'] = {invite_kiss!r}\n"
        f"os.environ['H3_EPISODE_INVITE_JUPO'] = {invite_jupo!r}\n"
        f"os.environ['H3_EPISODE_TOILET'] = {toilet!r}\n"
        f"os.environ['H3_EPISODE_GIN'] = {gin!r}\n"
        f"os.environ['H3_EPISODE_TSUNO'] = {tsuno!r}\n"
        f"os.environ['H3_EPISODE_APPEAR'] = {appear!r}\n"
        f"os.environ['H3_EPISODE_SCENES'] = {scenes!r}\n"
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
    p.add_argument("--preset", default="", choices=["", *PRESETS], help="画質: speed / balance / quality（迷ったら balance）")
    p.add_argument("--camera", default="", choices=["", *CAMERA_PACKS, *CAMERA_ALIASES], help="カメラ: side2d / action3d（迷ったら side2d）")
    p.add_argument("--connect", default="", choices=["", *CONNECT_MODES, *CONNECT_ALIASES], help="つなぎ: t2v=カット / chain=前の最終フレームからI2V / landing=用意した最終フレームへ（迷ったら t2v）")
    p.add_argument("--end-connect", default="", choices=["", *END_CONNECT_MODES, *END_CONNECT_ALIASES], help="シーン終わり: t2v=カット / chain=次へ続ける / follow=1番に従う（迷ったら t2v）")
    p.add_argument("--combat", default="", choices=["", *COMBAT_MODES, *COMBAT_ALIASES], help="格闘LoRA: off / on（on はハイメモリ専用。迷ったら off）")
    p.add_argument("--story", default="", choices=["", *STORY_MODES, *STORY_ALIASES], help="構成: accept / invite / evade / fight_win / fight_lose（病棟。迷ったら accept）")
    p.add_argument("--invite-pose", default="", choices=["", *INVITE_POSE_MODES, *INVITE_POSE_ALIASES], help="誘う行為: all_fours / m_open / ride / stand / jupo（病棟。迷ったら all_fours）")
    p.add_argument("--invite-kiss", default="", choices=["", *INVITE_KISS_MODES, *INVITE_KISS_ALIASES], help="誘うキス: off / stand / pin（病棟。迷ったら off）")
    p.add_argument("--invite-jupo", default="", choices=["", *INVITE_JUPO_MODES, *INVITE_JUPO_ALIASES], help="誘うじゅぼ: off / on（病棟。迷ったら off。騎乗とじゅぼのみには重ねない）")
    p.add_argument("--toilet", default="", choices=["", *TOILET_MODES, *TOILET_ALIASES], help="道中トイレ: off / pee / masturbate / tentacle（病棟。迷ったら off）")
    p.add_argument("--gin", default="", choices=["", *GIN_MODES, *GIN_ALIASES], help="灰色オプション: off / taken / fuck / invite_doggy（病棟。迷ったら off）")
    p.add_argument("--tsuno", default="", choices=["", *TSUNO_MODES, *TSUNO_ALIASES], help="角オプション: off / accept_stand / invite_stand（病棟。迷ったら off）")
    p.add_argument("--appear", default="", help="登場: miki,rei,kana,shino（病棟。外すとその人を飛ばす）")
    p.add_argument("--scenes", default="", help="シーンごと: miki=evade,rei=invite_ride,...（病棟。inherit は 5番。戦い構成は無視）")
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
    script = exec_script(
        args.episode,
        preset=args.preset,
        fresh=args.fresh,
        branch=args.branch,
        main_path=main_path,
        camera=args.camera,
        connect=args.connect,
        end_connect=getattr(args, "end_connect", ""),
        combat=args.combat,
        story=args.story,
        invite_pose=getattr(args, "invite_pose", ""),
        invite_kiss=getattr(args, "invite_kiss", ""),
        invite_jupo=getattr(args, "invite_jupo", ""),
        toilet=args.toilet,
        gin=args.gin,
        tsuno=args.tsuno,
        appear=args.appear,
        scenes=args.scenes,
    )
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
