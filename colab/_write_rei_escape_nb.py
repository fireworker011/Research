#!/usr/bin/env python3
"""Write the dedicated futanari-rei-escape Colab notebook (one code cell)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "minimaxh3"))
sys.path.insert(0, str(ROOT / "colab"))

from h3_episode import EPISODE_HELPERS  # noqa: E402
from h3_episode_packs import form_markdown, form_readme, ui_choices, ui_default  # noqa: E402

BRANCH = "cursor/futanari-rei-escape-34e4"
EPISODE = "futanari-rei-escape"
REPO = "fireworker011/Research"
FILE = "minimax_h3_rei_escape_bot.ipynb"
SESSION = "h3-rei-escape"
HELPERS = list(EPISODE_HELPERS)


def colab_url(path: str) -> str:
    return f"https://colab.research.google.com/github/{REPO}/blob/{BRANCH}/{path}"


CELL = r'''#@title 一発：レイ脱出。迷ったらそのまま Run all
#@markdown **話は固定。病棟・霞東のドロップダウンは出さない。**
EPISODE = "futanari-rei-escape"
#@markdown ---
__CONNECT_HELP__
CONNECT = __CONNECT_DEFAULT__  #@param __CONNECT_CHOICES__
__CAMERA_HELP__
CAMERA = __CAMERA_DEFAULT__  #@param __CAMERA_CHOICES__
__PRESET_HELP__
PRESET = __PRESET_DEFAULT__  #@param __PRESET_CHOICES__
__COMBAT_HELP__
COMBAT = __COMBAT_DEFAULT__  #@param __COMBAT_CHOICES__
__MAST_HELP__
REI_MAST = __MAST_DEFAULT__  #@param __MAST_CHOICES__
__TOILET_HELP__
REI_TOILET = __TOILET_DEFAULT__  #@param __TOILET_CHOICES__
__MOTH_HELP__
REI_MOTH = __MOTH_DEFAULT__  #@param __MOTH_CHOICES__
__ATTACK_HELP__
REI_ATTACK = __ATTACK_DEFAULT__  #@param __ATTACK_CHOICES__
__KISS_HELP__
REI_KISS = __KISS_DEFAULT__  #@param __KISS_CHOICES__
__ORAL_HELP__
REI_ORAL = __ORAL_DEFAULT__  #@param __ORAL_CHOICES__
__POSE_HELP__
REI_POSE = __POSE_DEFAULT__  #@param __POSE_CHOICES__
FRESH = False  #@param {type:"boolean"}
BRANCH = "__BRANCH__"  #@param {type:"string"}
print("=" * 60)
print(" H3 rei-escape one-click:", EPISODE)
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
os.environ["H3_EPISODE_CAMERA"] = CAMERA
os.environ["H3_EPISODE_CONNECT"] = CONNECT
os.environ["H3_EPISODE_COMBAT"] = COMBAT
os.environ["H3_EPISODE_REI_MAST"] = REI_MAST
os.environ["H3_EPISODE_REI_TOILET"] = REI_TOILET
os.environ["H3_EPISODE_REI_MOTH"] = REI_MOTH
os.environ["H3_EPISODE_REI_ATTACK"] = REI_ATTACK
os.environ["H3_EPISODE_REI_KISS"] = REI_KISS
os.environ["H3_EPISODE_REI_ORAL"] = REI_ORAL
os.environ["H3_EPISODE_REI_POSE"] = REI_POSE
os.environ["H3_EPISODE_FRESH"] = "1" if FRESH else "0"
os.environ["H3_HELPER_BRANCH"] = BRANCH
Path(DRIVE_ROOT, "models").mkdir(parents=True, exist_ok=True)

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
from h3_episode_packs import canonical_episode
slug = canonical_episode(EPISODE) or EPISODE
os.environ["H3_EPISODE"] = slug
Path(DRIVE_ROOT, "episodes", slug).mkdir(parents=True, exist_ok=True)
from h3_episode_colab_main import main

rc = main()
print("episode exit", rc)
if rc:
    raise SystemExit(rc)
print("成功。完成動画は Drive episodes/" + slug + "/final/ にあります。ランタイムは停止済みです。赤い例外は出ません。")
'''

MD = f"""# MiniMax H3 レイ脱出一発（選んで Run all）

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)]({colab_url(FILE)})

**コードセルは1本。話は `futanari-rei-escape` 固定。迷ったらドロップダウンはそのままで Run all。**
Drive `minimax-h3-comfyui/episodes/futanari-rei-escape/` に `episode.json` が無ければ GitHub から取ってくる。
全ビートを1つのランタイムで描き、HUD・タイトル・免責エンドカードを載せて `final/` に書く。終わったら停止。

病棟・霞東のノートとは別。このノートの Run all で本体 Drive を上書きするな。

## 上から（迷ったらそのまま）

**1. つなぎ方** — これ1つ。遭遇の入りと消滅走りは常にカット（相手が残らない）

{form_readme("connect")}

**2. カメラ** — 各カットは真横固定（doorway を足さない）

{form_readme("camera")}

**3. 画質**

{form_readme("preset")}

**4. 格闘 LoRA** — 既定オフ。オンはハイメモリ

{form_readme("combat")}

**5. 合間おな** — しないが既定

{form_readme("rei_mast")}

**6. トイレ** — 着座おなが既定。以後汚れが残る

{form_readme("rei_toilet")}

**7. 蛾女** — 尾端の第二口が既定

{form_readme("rei_moth")}

**8. 襲う側**

{form_readme("rei_attack")}

**9. キス** — しないが既定

{form_readme("rei_kiss")}

**口** — しないが既定。行為は名称ではなく唇と舌の軌道

{form_readme("rei_oral")}

**体位** — 名称ではなく動き。四つん這い後ろからが既定

{form_readme("rei_pose")}

S00 はタイトルカード。Prompt にレイを入れない。敵1の円口は mystic のみ（口LoRA禁止）。完了で終わる。失敗カードなし。Combat 既定オフ。

- 本番の inbox / queued / output は触らない。`models/` だけ共有
- 10Eros Max は Drive `models/diffusion_models/10Eros_Max_h3_TURBO-hybrid_beta5_int8.safetensors` を使う
- HUD・字幕は生成後に載せる。H3 に日本語UIを描かせない
- 投稿しない。アフィURL禁止
- マージ前は `BRANCH` もこの枝（`{BRANCH}`）
- 成功時は `episode exit 0` のあと「成功。」と出る。ランタイム切断は予定どおり。`SystemExit: 0` の赤い枠は出さない

セッション名 `{SESSION}`。GPU は A100。正本カットは `stories/futanari-rei-escape/`。
"""


def make_nb() -> dict:
    cell = (
        CELL.replace("__BRANCH__", BRANCH)
        .replace("__REPO__", REPO)
        .replace("__HELPERS__", json.dumps(HELPERS, indent=4))
        .replace("__CONNECT_HELP__", form_markdown("connect", "1. つなぎ方 — 動画をどう繋げるか。遭遇の入りと消滅は常にカット"))
        .replace("__CONNECT_DEFAULT__", json.dumps(ui_default("connect"), ensure_ascii=False))
        .replace("__CONNECT_CHOICES__", json.dumps(ui_choices("connect"), ensure_ascii=False))
        .replace("__CAMERA_HELP__", form_markdown("camera", "2. カメラ"))
        .replace("__CAMERA_DEFAULT__", json.dumps(ui_default("camera"), ensure_ascii=False))
        .replace("__CAMERA_CHOICES__", json.dumps(ui_choices("camera"), ensure_ascii=False))
        .replace("__PRESET_HELP__", form_markdown("preset", "3. 画質"))
        .replace("__PRESET_DEFAULT__", json.dumps(ui_default("preset"), ensure_ascii=False))
        .replace("__PRESET_CHOICES__", json.dumps(ui_choices("preset"), ensure_ascii=False))
        .replace("__COMBAT_HELP__", form_markdown("combat", "4. 格闘 LoRA — ハイメモリ専用の任意"))
        .replace("__COMBAT_DEFAULT__", json.dumps(ui_default("combat"), ensure_ascii=False))
        .replace("__COMBAT_CHOICES__", json.dumps(ui_choices("combat"), ensure_ascii=False))
        .replace("__MAST_HELP__", form_markdown("rei_mast", "5. 合間おな"))
        .replace("__MAST_DEFAULT__", json.dumps(ui_default("rei_mast"), ensure_ascii=False))
        .replace("__MAST_CHOICES__", json.dumps(ui_choices("rei_mast"), ensure_ascii=False))
        .replace("__TOILET_HELP__", form_markdown("rei_toilet", "6. トイレ — どれでも次へ。以後汚れ"))
        .replace("__TOILET_DEFAULT__", json.dumps(ui_default("rei_toilet"), ensure_ascii=False))
        .replace("__TOILET_CHOICES__", json.dumps(ui_choices("rei_toilet"), ensure_ascii=False))
        .replace("__MOTH_HELP__", form_markdown("rei_moth", "7. 蛾女"))
        .replace("__MOTH_DEFAULT__", json.dumps(ui_default("rei_moth"), ensure_ascii=False))
        .replace("__MOTH_CHOICES__", json.dumps(ui_choices("rei_moth"), ensure_ascii=False))
        .replace("__ATTACK_HELP__", form_markdown("rei_attack", "8. 襲う側"))
        .replace("__ATTACK_DEFAULT__", json.dumps(ui_default("rei_attack"), ensure_ascii=False))
        .replace("__ATTACK_CHOICES__", json.dumps(ui_choices("rei_attack"), ensure_ascii=False))
        .replace("__KISS_HELP__", form_markdown("rei_kiss", "9. キス"))
        .replace("__KISS_DEFAULT__", json.dumps(ui_default("rei_kiss"), ensure_ascii=False))
        .replace("__KISS_CHOICES__", json.dumps(ui_choices("rei_kiss"), ensure_ascii=False))
        .replace("__ORAL_HELP__", form_markdown("rei_oral", "口 — 唇と舌の軌道"))
        .replace("__ORAL_DEFAULT__", json.dumps(ui_default("rei_oral"), ensure_ascii=False))
        .replace("__ORAL_CHOICES__", json.dumps(ui_choices("rei_oral"), ensure_ascii=False))
        .replace("__POSE_HELP__", form_markdown("rei_pose", "体位 — 名称ではなく動き"))
        .replace("__POSE_DEFAULT__", json.dumps(ui_default("rei_pose"), ensure_ascii=False))
        .replace("__POSE_CHOICES__", json.dumps(ui_choices("rei_pose"), ensure_ascii=False))
    )
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
                "metadata": {"id": "rei_escape_md"},
                "source": [line + "\n" for line in MD.strip("\n").split("\n")],
            },
            {
                "cell_type": "code",
                "metadata": {"id": "rei_escape_run"},
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
