#!/usr/bin/env python3
"""Write the H3 Studio Colab notebook and mirror colab/h3_studio.py to minimaxh3/."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "colab"))

from h3_studio import JOB_HELP, JOBS, STUDIO_HELPERS  # noqa: E402

BRANCH = "cursor/h3-studio-lane-ec31"
REPO = "fireworker011/Research"
FILE = "minimax_h3_studio_bot.ipynb"
SESSION = "h3-studio"


def colab_url(path: str) -> str:
    return f"https://colab.research.google.com/github/{REPO}/blob/{BRANCH}/{path}"


CELL = r'''#@title H3 Studio：ジョブを1つ選ぶ（生成はしない）
#@markdown 病棟エンジンは使わない。プランとプロンプトだけ書く。Comfy High-Mem の生成ボタンは人間が押す。
JOB = "text_scene"  #@param __JOB_CHOICES__
RUNTIME = "comfy"  #@param ["comfy", "api"]
HIGH_MEM = True  #@param {type:"boolean"}
FINISH = False  #@param {type:"boolean"}
TURBO = False  #@param {type:"boolean"}
DURATION = "5"  #@param ["5", "4"]
ACTION = ""  #@param {type:"string"}
DIALOGUE = ""  #@param {type:"string"}
#@markdown **Hero。空欄は Look に書かない。**
HERO_HAIR = ""  #@param {type:"string"}
HERO_COLOR = ""  #@param {type:"string"}
HERO_RACE = ""  #@param {type:"string"}
HERO_AGE = ""  #@param {type:"string"}
HERO_HEIGHT = ""  #@param {type:"string"}
HERO_WEIGHT = ""  #@param {type:"string"}
HERO_CLOTHES = ""  #@param {type:"string"}
HERO_PLACE = ""  #@param {type:"string"}
#@markdown **Enemy。空欄は Look に書かない。**
ENEMY_HAIR = ""  #@param {type:"string"}
ENEMY_COLOR = ""  #@param {type:"string"}
ENEMY_RACE = ""  #@param {type:"string"}
ENEMY_AGE = ""  #@param {type:"string"}
ENEMY_HEIGHT = ""  #@param {type:"string"}
ENEMY_WEIGHT = ""  #@param {type:"string"}
ENEMY_CLOTHES = ""  #@param {type:"string"}
ENEMY_PLACE = ""  #@param {type:"string"}
HERO_SHEET = ""  #@param {type:"string"}
VIDEO = ""  #@param {type:"string"}
FIRST = ""  #@param {type:"string"}
LAST = ""  #@param {type:"string"}
#@markdown **two_pass のときだけ。B の Video 1 は A の mp4。**
PASS_A = ""  #@param __PASS_CHOICES__
PASS_B = ""  #@param __PASS_CHOICES__
BRANCH = "__BRANCH__"  #@param {type:"string"}

import os, shutil, sys, urllib.request
from pathlib import Path

DRIVE_ROOT = "/content/drive/MyDrive/minimax-h3-comfyui"
RAW = f"https://raw.githubusercontent.com/__REPO__/{BRANCH}"

def _plan_path() -> str:
    drive_out = str(Path(DRIVE_ROOT) / "studio" / "latest-plan.json")
    try:
        from google.colab import drive
    except ImportError:
        print("Colab の外。プランは h3_studio_plan.json に書く。")
        return "h3_studio_plan.json"
    drive.mount("/content/drive")
    Path(drive_out).parent.mkdir(parents=True, exist_ok=True)
    return drive_out

def _fetch(rel: str, dest: Path) -> None:
    url = f"{RAW}/{rel}"
    urllib.request.urlretrieve(url, dest)
    if not dest.is_file() or dest.stat().st_size < 50:
        raise SystemExit(f"helper missing: {rel}")

HELPERS = __HELPERS__
for rel in HELPERS:
    dest = Path("/content") / Path(rel).name
    _fetch(rel, dest)
    print("helper", dest.name)

os.environ["H3_STUDIO_JOB"] = JOB
os.environ["H3_STUDIO_RUNTIME"] = RUNTIME
os.environ["H3_STUDIO_HIGH_MEM"] = "1" if HIGH_MEM else "0"
os.environ["H3_STUDIO_FINISH"] = "1" if FINISH else "0"
os.environ["H3_STUDIO_TURBO"] = "1" if TURBO else "0"
os.environ["H3_STUDIO_DURATION"] = DURATION
os.environ["H3_STUDIO_ACTION"] = ACTION
os.environ["H3_STUDIO_DIALOGUE"] = DIALOGUE
os.environ["H3_STUDIO_HERO_SHEET"] = HERO_SHEET
os.environ["H3_STUDIO_VIDEO"] = VIDEO
os.environ["H3_STUDIO_FIRST"] = FIRST
os.environ["H3_STUDIO_LAST"] = LAST
os.environ["H3_STUDIO_PASS_A"] = PASS_A
os.environ["H3_STUDIO_PASS_B"] = PASS_B
os.environ["H3_STUDIO_GENERATE"] = "0"
os.environ["H3_STUDIO_OUT"] = _plan_path()
for prefix, values in (
    ("HERO", (HERO_HAIR, HERO_COLOR, HERO_RACE, HERO_AGE, HERO_HEIGHT, HERO_WEIGHT, HERO_CLOTHES, HERO_PLACE)),
    ("ENEMY", (ENEMY_HAIR, ENEMY_COLOR, ENEMY_RACE, ENEMY_AGE, ENEMY_HEIGHT, ENEMY_WEIGHT, ENEMY_CLOTHES, ENEMY_PLACE)),
):
    for key, value in zip(("HAIR", "COLOR", "RACE", "AGE", "HEIGHT", "WEIGHT", "CLOTHES", "PLACE"), values):
        os.environ[f"H3_STUDIO_{prefix}_{key}"] = value

sys.path.insert(0, "/content")
from h3_studio_colab_main import main

rc = main()
print("studio exit", rc)
if rc:
    raise SystemExit(rc)
'''


def markdown() -> str:
    lines = "\n".join(f"- `{job}` — {JOB_HELP[job]}" for job in JOBS)
    return f"""# MiniMax H3 Studio（ジョブは1つ。生成は人間）

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)]({colab_url(FILE)})

コードセルはプランとプロンプトだけを書く。Comfy は起動しない。公式 Hailuo API にも投げない。
Drive の `minimax-h3-comfyui/studio/latest-plan.json` に置く。`episodes/` には書かない。

Look の空欄はプロンプトに出ない。swap は Hero シート（絵のパス）が要る。
action は英語1本。日本語は「」か DIALOGUE。商品名は書かない。
runtime が api で Combat / Swap / real を選ぶと止まる。

{lines}

Combat / Swap は Turbo を切る。本体は Comfy High-Mem。
Weapon / GunFu / Continuity は無い。orbit の LoRA ファイル名は未確定。
セッション名 `{SESSION}`。
"""


def make_nb() -> dict:
    cell = (
        CELL.replace("__BRANCH__", BRANCH)
        .replace("__REPO__", REPO)
        .replace("__HELPERS__", json.dumps(list(STUDIO_HELPERS)))
        .replace("__JOB_CHOICES__", json.dumps(list(JOBS)))
        .replace("__PASS_CHOICES__", json.dumps([""] + list(JOBS)))
    )
    return {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python"},
            "colab": {"provenance": [], "name": SESSION},
        },
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {"id": "studio_md"},
                "source": [line + "\n" for line in markdown().strip("\n").split("\n")],
            },
            {
                "cell_type": "code",
                "metadata": {"id": "studio_plan"},
                "execution_count": None,
                "outputs": [],
                "source": [line + "\n" for line in cell.strip("\n").split("\n")],
            },
        ],
    }


def mirror_engine() -> None:
    src = ROOT / "colab" / "h3_studio.py"
    dest = ROOT / "minimaxh3" / "h3_studio.py"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(src.read_bytes())
    print("mirrored", dest)


def main() -> None:
    mirror_engine()
    blob = json.dumps(make_nb(), ensure_ascii=False, indent=1)
    for out in (ROOT / FILE, ROOT / "minimaxh3" / FILE):
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(blob, encoding="utf-8")
        print("wrote", out, "bytes", out.stat().st_size)


if __name__ == "__main__":
    main()
