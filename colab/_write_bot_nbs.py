#!/usr/bin/env python3
"""Write dedicated Grokbot Colab notebooks: one per mode, one code cell, idle-or-run then stop."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BRANCH = "cursor/minimax-h3-motion-identity-e959"
REPO = "fireworker011/Research"


def colab_url(path: str) -> str:
    return f"https://colab.research.google.com/github/{REPO}/blob/{BRANCH}/{path}"


MODES = {
    "t2v": {
        "title": "MiniMax H3 T2V bot（専用・10秒・9:16）",
        "file": "minimax_h3_t2v_bot.ipynb",
        "session": "h3-t2v",
        "blurb": "テキストから10秒。first_frame は繋がない。inbox の `.txt` を1件処理して stop。",
        "forbid": "I2V/R2V ジョブは触らない。",
    },
    "i2v": {
        "title": "MiniMax H3 I2V bot（専用・10秒・8:9）",
        "file": "minimax_h3_i2v_bot.ipynb",
        "session": "h3-i2v",
        "blurb": "1枚から10秒。FL2VA + first_frame。inbox の jpg を1件処理して stop。",
        "forbid": "T2V/R2V ジョブは触らない。",
    },
    "r2v": {
        "title": "MiniMax H3 R2V bot（専用・10秒）",
        "file": "minimax_h3_r2v_bot.ipynb",
        "session": "h3-r2v",
        "blurb": "still=identity、mp4=motion。ref2va。参照動画は外さない。inbox の still+mp4 を1件処理して stop。",
        "forbid": "I2V/T2V ジョブは触らない。ponz 原作を motion にしない。",
    },
}


CELL = r'''#@title {mode} bot — inbox 1件 → 10秒 mp4 → 停止
MODE = "{mode}"
print("=" * 60)
print(" H3", MODE.upper(), "bot Colab")
print("=" * 60)

import os, shutil, subprocess, sys, urllib.request
from pathlib import Path

from google.colab import drive

DRIVE_ROOT = "/content/drive/MyDrive/minimax-h3-comfyui"
COMFY_DIR = "/content/ComfyUI"
BRANCH = "cursor/minimax-h3-motion-identity-e959"
RAW = f"https://raw.githubusercontent.com/fireworker011/Research/{{BRANCH}}"

drive.mount("/content/drive")
os.environ["H3_DRIVE_ROOT"] = DRIVE_ROOT
os.environ["H3_COMFY_DIR"] = COMFY_DIR
os.environ["H3_JOB_MODE"] = MODE
os.environ["H3_BOT_IDLE_OK"] = "1"
Path(DRIVE_ROOT).mkdir(parents=True, exist_ok=True)
for name in ("inbox", "queued", "running", "done", "failed", "input", "output", "models"):
    (Path(DRIVE_ROOT) / name).mkdir(parents=True, exist_ok=True)

import torch
if not torch.cuda.is_available():
    raise SystemExit("GPU がオフです。ランタイムのタイプを A100 にしてやり直してください。")
vram = torch.cuda.get_device_properties(0).total_memory / 1024 ** 3
print("GPU:", torch.cuda.get_device_name(0), "VRAM GiB:", round(vram, 1))
if vram < 20:
    raise SystemExit("VRAM が足りません。A100 を選んでください。")

def fetch_text(url: str, dest: Path) -> bool:
    try:
        urllib.request.urlretrieve(url, dest)
        return dest.is_file() and dest.stat().st_size > 100
    except Exception as e:
        print("fetch fail", url, e)
        return False

HELPERS = [
    "colab/h3_r2v_core.py",
    "colab/h3_motion_graphics.py",
    "colab/h3_t2v.py",
    "colab/h3_i2v_phone.py",
    "colab/h3_i2v_job.py",
    "colab/h3_i2v_runtime.py",
    "colab/h3_colab_main.py",
]
for rel in HELPERS:
    name = Path(rel).name
    dest = Path("/content") / name
    ok = fetch_text(f"{{RAW}}/{{rel}}", dest)
    if not ok:
        drive_src = Path(DRIVE_ROOT) / name
        if drive_src.is_file():
            shutil.copy2(drive_src, dest)
            ok = True
    if not ok:
        raise SystemExit(f"helper missing: {{name}}")
    shutil.copy2(dest, Path(DRIVE_ROOT) / name)
    print("helper", name)

sys.path.insert(0, "/content")
from h3_colab_main import bot_prepare, main

bot_prepare(MODE, Path(DRIVE_ROOT))
rc = main()
print("bot exit", rc)
raise SystemExit(rc)
'''


def markdown(mode: str, spec: dict) -> str:
    path = spec["file"]
    url = colab_url(path)
    return f"""# {spec["title"]}

Grokbot 専用。人間がセルをいじらない。**コードセルは1本。** 空 inbox は idle で終わってランタイムを手放す。

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)]({url})

{spec["blurb"]}
セッション名 `{spec["session"]}`。GPU は A100。{spec["forbid"]}

投稿しない。アフィURLは禁止。リンクはプロフィール。完全版ノート / loca.lt / Wan / Max は使わない。

手順は `minimaxh3/GROKBOT.md`。inbox に置いたあと、このノートを実行するか `python minimaxh3/grokbot/run_{mode}.py`。
"""


def make_nb(mode: str, spec: dict) -> dict:
    md = markdown(mode, spec)
    cell = CELL.format(mode=mode)
    return {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python"},
            "accelerator": "GPU",
            "colab": {"provenance": [], "gpuType": "A100", "name": spec["session"]},
        },
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {"id": f"{mode}_bot_md"},
                "source": [line + "\n" for line in md.strip("\n").split("\n")],
            },
            {
                "cell_type": "code",
                "metadata": {"id": f"{mode}_bot_run"},
                "execution_count": None,
                "outputs": [],
                "source": [line + "\n" for line in cell.strip("\n").split("\n")],
            },
        ],
    }


def main() -> None:
    for mode, spec in MODES.items():
        nb = make_nb(mode, spec)
        blob = json.dumps(nb, ensure_ascii=False, indent=1)
        outs = [ROOT / spec["file"], ROOT / "minimaxh3" / spec["file"]]
        for out in outs:
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(blob, encoding="utf-8")
            print("wrote", out, "bytes", out.stat().st_size)


if __name__ == "__main__":
    main()
