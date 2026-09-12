#!/usr/bin/env python3
"""Write the one-click episode Colab notebook (one code cell: bootstrap → render all beats → HUD → stitch → stop)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "minimaxh3"))

from h3_episode import EPISODE_HELPERS  # noqa: E402

BRANCH = "cursor/h3-episode-oneclick-f112"
REPO = "fireworker011/Research"
FILE = "minimax_h3_episode_bot.ipynb"
SESSION = "h3-episode"
HELPERS = list(EPISODE_HELPERS)


def colab_url(path: str) -> str:
    return f"https://colab.research.google.com/github/{REPO}/blob/{BRANCH}/{path}"


CELL = r'''#@title 一発：episode.json → 全ビート → HUD → 連結 → episodes/<slug>/final/ → 停止
EPISODE = "bandai-district"  #@param {type:"string"}
PRESET = "daily"  #@param ["daily", "preview", "fast"]
FRESH = False  #@param {type:"boolean"}
BRANCH = "__BRANCH__"  #@param {type:"string"}
print("=" * 60)
print(" H3 episode one-click:", EPISODE, "preset", PRESET)
print("=" * 60)

import os, shutil, subprocess, sys, urllib.request
from pathlib import Path

from google.colab import drive

DRIVE_ROOT = "/content/drive/MyDrive/minimax-h3-comfyui"
COMFY_DIR = "/content/ComfyUI"
RAW = f"https://raw.githubusercontent.com/__REPO__/{BRANCH}"

drive.mount("/content/drive")
os.environ["H3_DRIVE_ROOT"] = DRIVE_ROOT
os.environ["H3_COMFY_DIR"] = COMFY_DIR
os.environ["H3_EPISODE"] = EPISODE
os.environ["H3_EPISODE_PRESET"] = PRESET
os.environ["H3_EPISODE_FRESH"] = "1" if FRESH else "0"
os.environ["H3_HELPER_BRANCH"] = BRANCH
Path(DRIVE_ROOT, "models").mkdir(parents=True, exist_ok=True)
Path(DRIVE_ROOT, "episodes", EPISODE).mkdir(parents=True, exist_ok=True)

import torch
if not torch.cuda.is_available():
    raise SystemExit("GPU がオフです。ランタイムのタイプを A100 にしてやり直してください。")
vram = torch.cuda.get_device_properties(0).total_memory / 1024 ** 3
print("GPU:", torch.cuda.get_device_name(0), "VRAM GiB:", round(vram, 1))
if vram < 20:
    raise SystemExit("VRAM が足りません。A100 を選んでください。")

subprocess.run(["apt-get", "install", "-y", "-qq", "fonts-noto-cjk", "ffmpeg"], check=False, capture_output=True)

def fetch_text(url: str, dest: Path) -> bool:
    try:
        urllib.request.urlretrieve(url, dest)
        return dest.is_file() and dest.stat().st_size > 100
    except Exception as e:
        print("fetch fail", url, e)
        return False

HELPERS = __HELPERS__
LIB = Path(DRIVE_ROOT) / "episodes" / "_lib"
LIB.mkdir(parents=True, exist_ok=True)
for rel in HELPERS:
    name = Path(rel).name
    dest = Path("/content") / name
    ok = fetch_text(f"{RAW}/{rel}", dest)
    if not ok and (LIB / name).is_file():
        shutil.copy2(LIB / name, dest)
        ok = True
    if not ok:
        raise SystemExit(f"helper missing: {name}")
    shutil.copy2(dest, LIB / name)
    print("helper", name)

sys.path.insert(0, "/content")
from h3_episode_colab_main import main

rc = main()
print("episode exit", rc)
raise SystemExit(rc)
'''

MD = f"""# MiniMax H3 エピソード一発（episode.json → 完成動画）

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)]({colab_url(FILE)})

**コードセルは1本。Run all で終わる。** Drive `minimax-h3-comfyui/episodes/<slug>/` に
`episode.json` とスチールが無ければ GitHub から取ってくる。全ビートを1つのランタイムで描き、
HUD・タイトル・免責エンドカードを載せて `final/<slug>-<日時>.mp4`（と `latest.mp4`）を書く。終わったら停止。

- 本番の inbox / queued / output は触らない。`models/` だけ共有
- 途中で止まっても `raw/<beat>.mp4` があるビートは飛ばして再開（FRESH で作り直し）
- HUD・字幕は生成後に載せる。H3 に日本語UIを描かせない
- 投稿しない。アフィURL禁止。他のネタは `minimaxh3/episodes/_template` を複製して EPISODE を変える

セッション名 `{SESSION}`。GPU は A100。手順は `minimaxh3/episodes/README.md`。
"""


def make_nb() -> dict:
    cell = CELL.replace("__BRANCH__", BRANCH).replace("__REPO__", REPO).replace("__HELPERS__", json.dumps(HELPERS, indent=4))
    return {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python"},
            "accelerator": "GPU",
            "colab": {"provenance": [], "gpuType": "A100", "name": SESSION},
        },
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {"id": "episode_md"},
                "source": [line + "\n" for line in MD.strip("\n").split("\n")],
            },
            {
                "cell_type": "code",
                "metadata": {"id": "episode_run"},
                "execution_count": None,
                "outputs": [],
                "source": [line + "\n" for line in cell.strip("\n").split("\n")],
            },
        ],
    }


def main() -> None:
    nb = make_nb()
    blob = json.dumps(nb, ensure_ascii=False, indent=1)
    for out in (ROOT / FILE, ROOT / "minimaxh3" / FILE):
        out.write_text(blob, encoding="utf-8")
        print("wrote", out, "bytes", out.stat().st_size)


if __name__ == "__main__":
    main()
