#!/usr/bin/env python3
"""Write the phone I2V Colab notebook (fal H3 Max, no PC / no A100)."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTS = [
    ROOT / "minimax_h3_i2v_phone.ipynb",
    ROOT / "minimaxh3" / "minimax_h3_i2v_phone.ipynb",
]

MD0 = r"""# MiniMax H3 I2V（スマホ・PC不要）

**セルは3本だけ。GPUもA100もPCも不要。** 1枚の画像から10秒の動画（I2VA / fal H3 Max）。

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/fireworker011/Research/blob/cursor/minimax-h3-motion-identity-e959/minimax_h3_i2v_phone.ipynb)

## スマホでの手順（これが最善手）

1. 上の **Open in Colab** を開く
2. 左の **鍵アイコン** → シークレットに `FAL_KEY`（このノートにアクセス許可）。Git に書かない
3. ランタイムは **CPU のままでよい**（GPU にしなくていい）
4. メニュー **⋮ → ランタイム → すべてのセルを実行**
5. ①で Google Drive の許可を出す
6. ③が終わると、この画面に動画が出る。同じファイルは Drive の `MyDrive/minimax-h3-comfyui/output`

自分の写真: スマホの Drive アプリで `マイドライブ/minimax-h3-comfyui/input/` に jpg を置く。③の `FIRST_IMAGE` を `auto` にする。

inbox に jpg を置いた分は、③がまとめて回す。

空のままだとパーカーの参考画像 `coconala_creator_ref.jpg` を使う。

任意: 同じ鍵に `XAI_API_KEY` があると Imagine 2.0 で1枚目を整えてから I2V する。無くても動画は作る。

動画の中にアフィURLは出さない。リンクはプロフィール。画面上は「広告」。

Comfy の公式重みで寄せたいときだけ、完全版ノート＋A100。PC が無い今は fal が最善手。
"""

CELL1 = r'''#@title ① Driveをつなぐ（最初の許可だけ）
print("=" * 60)
print(" ① Google Drive（GPU 不要）")
print("=" * 60)

from google.colab import drive, userdata
from pathlib import Path
import os

DRIVE_ROOT = "/content/drive/MyDrive/minimax-h3-comfyui"  #@param {type:"string"}

drive.mount("/content/drive")

for sub in ["inbox", "queued", "running", "done", "failed", "input", "output", "models"]:
    os.makedirs(f"{DRIVE_ROOT}/{sub}", exist_ok=True)

with open("/content/h3_paths.env", "w") as f:
    f.write(f"DRIVE_ROOT={DRIVE_ROOT}\n")

print("Drive:", DRIVE_ROOT)
print("写真を置く場所:", f"{DRIVE_ROOT}/input")
print("inbox:", f"{DRIVE_ROOT}/inbox")
print("動画の保存先:", f"{DRIVE_ROOT}/output")

try:
    key = (userdata.get("FAL_KEY") or "").strip()
except Exception:
    key = ""
if not key:
    raise SystemExit(
        "FAL_KEY がありません。左の鍵アイコン → シークレットに FAL_KEY を追加し、"
        "このノートへのアクセスを許可してから ① をやり直してください。Git に書かない。"
    )
print("FAL_KEY: 読み込みOK（値は表示しない）")
print("OK → 次は②")
'''

CELL2 = r'''#@title ② ヘルパーを取る（モデル42GBはダウンロードしない）
print("=" * 60)
print(" ② fal 準備（Comfy / A100 なし）")
print("=" * 60)

import os, shutil, sys, urllib.request
from pathlib import Path

env = {}
with open("/content/h3_paths.env") as f:
    for line in f:
        k, v = line.strip().split("=", 1)
        env[k] = v
DRIVE_ROOT = Path(env["DRIVE_ROOT"])
BRANCH = "cursor/minimax-h3-motion-identity-e959"
RAW = f"https://raw.githubusercontent.com/fireworker011/Research/{BRANCH}"
HELPERS = [
    "colab/h3_r2v_core.py",
    "colab/h3_motion_graphics.py",
    "colab/h3_i2v_phone.py",
    "colab/h3_imagine.py",
    "colab/h3_fal_max.py",
    "colab/h3_i2v_job.py",
]

def fetch_text(url: str, dest: Path) -> bool:
    try:
        urllib.request.urlretrieve(url, dest)
        return dest.is_file() and dest.stat().st_size > 100
    except Exception as e:
        print("fetch fail", url, e)
        return False

for rel in HELPERS:
    name = Path(rel).name
    dest = Path("/content") / name
    ok = fetch_text(f"{RAW}/{rel}", dest)
    if not ok:
        drive_src = DRIVE_ROOT / name
        if drive_src.is_file():
            shutil.copy2(drive_src, dest)
            ok = True
    if not ok:
        raise SystemExit(f"ヘルパー取得失敗: {name}")
    shutil.copy2(dest, DRIVE_ROOT / name)
    print("helper", name, dest.stat().st_size)

sys.path.insert(0, "/content")
from h3_fal_max import ENDPOINT
print("endpoint", ENDPOINT)
print("OK → 次は③（動画をつくる）")
'''

CELL3 = r'''#@title ③ 1枚から動画をつくる（fal H3 Max / I2VA）
print("=" * 60)
print(" ③ fal H3 Max I2VA（10秒・first frame 固定）")
print("=" * 60)

import os, sys
from pathlib import Path
from IPython.display import display, Video, HTML

FIRST_IMAGE = "coconala_creator_ref.jpg"  #@param {type:"string"}
DURATION_S = 10  #@param {type:"number"}
SEED = 42  #@param {type:"integer"}
WIDTH = 768  #@param {type:"integer"}
HEIGHT = 864  #@param {type:"integer"}
DRAIN_INBOX = True  #@param {type:"boolean"}
DRY_RUN = False  #@param {type:"boolean"}
PROMPT = ""  #@param {type:"string"}

sys.path.insert(0, "/content")
from h3_i2v_phone import run_phone_session
from h3_motion_graphics import resolve_motion_prompt, validate_motion_ad_prompt

env = {}
with open("/content/h3_paths.env") as f:
    for line in f:
        k, v = line.strip().split("=", 1)
        env[k] = v
DRIVE_ROOT = Path(env["DRIVE_ROOT"])

prompt = resolve_motion_prompt(PROMPT, duration_s=float(DURATION_S))
errs = validate_motion_ad_prompt(prompt)
if errs:
    raise SystemExit(errs)
print("8:9 homage canvas noted:", int(WIDTH), "x", int(HEIGHT), "(fal follows the still)")
print(prompt[:400], "...")

paths = run_phone_session(
    DRIVE_ROOT,
    first_image=FIRST_IMAGE,
    duration_s=float(DURATION_S),
    seed=int(SEED),
    prompt=PROMPT,
    dry_run=bool(DRY_RUN),
    drain_inbox=bool(DRAIN_INBOX),
)
if not paths:
    print("動画がありません。Drive の input/ か inbox/ を確認してください。")
else:
    for p in paths:
        print("保存:", p)
        if p.is_file():
            display(HTML(f"<p style='font-size:16px'>保存: <code>{p}</code></p>"))
            display(Video(str(p), embed=True, width=360))
print("リンクは動画に出さずプロフィールへ。")
'''

nb = {
    "nbformat": 4,
    "nbformat_minor": 5,
    "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python"},
        "colab": {"provenance": []},
    },
    "cells": [
        {"cell_type": "markdown", "metadata": {}, "source": [line + "\n" for line in MD0.strip("\n").split("\n")]},
        {"cell_type": "code", "metadata": {"id": "phone1_drive"}, "execution_count": None, "outputs": [], "source": [line + "\n" for line in CELL1.strip("\n").split("\n")]},
        {"cell_type": "code", "metadata": {"id": "phone2_setup"}, "execution_count": None, "outputs": [], "source": [line + "\n" for line in CELL2.strip("\n").split("\n")]},
        {"cell_type": "code", "metadata": {"id": "phone3_i2va"}, "execution_count": None, "outputs": [], "source": [line + "\n" for line in CELL3.strip("\n").split("\n")]},
    ],
}
blob = json.dumps(nb, ensure_ascii=False, indent=1)
for out in OUTS:
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(blob, encoding="utf-8")
    print("wrote", out, "bytes", out.stat().st_size)
