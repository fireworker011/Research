#!/usr/bin/env python3
"""Write the one-click episode Colab notebook (one code cell: bootstrap → render all beats → HUD → stitch → stop)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "minimaxh3"))

from h3_episode import EPISODE_HELPERS  # noqa: E402
from h3_episode_packs import form_markdown, form_readme, ui_choices, ui_default  # noqa: E402

BRANCH = "cursor/h3-hospital-ward-34e4"
EPISODE_DEFAULT = "kasumi-late-desk-adult"
REPO = "fireworker011/Research"
FILE = "minimax_h3_episode_bot.ipynb"
SESSION = "h3-episode"
HELPERS = list(EPISODE_HELPERS)


def colab_url(path: str) -> str:
    return f"https://colab.research.google.com/github/{REPO}/blob/{BRANCH}/{path}"


CELL = r'''#@title 一発：話と上から 1〜9、登場とシーンを選んで Run all（迷ったらそのまま）
__EPISODE_HELP__
EPISODE = __EPISODE_DEFAULT__  #@param __EPISODE_CHOICES__
#@markdown ---
__CONNECT_HELP__
CONNECT = __CONNECT_DEFAULT__  #@param __CONNECT_CHOICES__
__CAMERA_HELP__
CAMERA = __CAMERA_DEFAULT__  #@param __CAMERA_CHOICES__
__PRESET_HELP__
PRESET = __PRESET_DEFAULT__  #@param __PRESET_CHOICES__
__COMBAT_HELP__
COMBAT = __COMBAT_DEFAULT__  #@param __COMBAT_CHOICES__
__STORY_HELP__
STORY = __STORY_DEFAULT__  #@param __STORY_CHOICES__
__POSE_HELP__
INVITE_POSE = __POSE_DEFAULT__  #@param __POSE_CHOICES__
__TOILET_HELP__
TOILET = __TOILET_DEFAULT__  #@param __TOILET_CHOICES__
__GIN_HELP__
GIN = __GIN_DEFAULT__  #@param __GIN_CHOICES__
__TSUNO_HELP__
TSUNO = __TSUNO_DEFAULT__  #@param __TSUNO_CHOICES__
#@markdown **登場（病棟）。外すとその人のシーンを飛ばす。4人とも外すと止まる。霞東は無視。**
APPEAR_MIKI = True  #@param {type:"boolean"}
APPEAR_REI = True  #@param {type:"boolean"}
APPEAR_KANA = True  #@param {type:"boolean"}
APPEAR_SHINO = True  #@param {type:"boolean"}
#@markdown **シーンごと（病棟）。誘うは誘い方も含む。戦い構成と霞東は無視。**
SCENE_MIKI = __SCENE_DEFAULT__  #@param __SCENE_CHOICES__
SCENE_REI = __SCENE_DEFAULT__  #@param __SCENE_CHOICES__
SCENE_KANA = __SCENE_DEFAULT__  #@param __SCENE_CHOICES__
SCENE_SHINO = __SCENE_DEFAULT__  #@param __SCENE_CHOICES__
FRESH = False  #@param {type:"boolean"}
BRANCH = "__BRANCH__"  #@param {type:"string"}
#@markdown **CivitaiのAPIキー** — 必要な LoRA を Drive に取るときだけ貼る。空なら Colab のシークレット `CIVITAI_API_TOKEN`。値は表示しない。
CivitaiのAPIキー = ""  #@param {type:"string"}
print("=" * 60)
print(" H3 episode one-click:", EPISODE)
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
os.environ["H3_EPISODE_END_CONNECT"] = "follow"
os.environ["H3_EPISODE_COMBAT"] = COMBAT
os.environ["H3_EPISODE_STORY"] = STORY
os.environ["H3_EPISODE_INVITE_POSE"] = INVITE_POSE
os.environ["H3_EPISODE_TOILET"] = TOILET
os.environ["H3_EPISODE_GIN"] = GIN
os.environ["H3_EPISODE_TSUNO"] = TSUNO
os.environ["H3_EPISODE_APPEAR"] = ",".join(
    name for name, on in (("miki", APPEAR_MIKI), ("rei", APPEAR_REI), ("kana", APPEAR_KANA), ("shino", APPEAR_SHINO)) if on
) or "none"
os.environ["H3_EPISODE_SCENES"] = ",".join(
    f"{name}={choice}"
    for name, choice in (("miki", SCENE_MIKI), ("rei", SCENE_REI), ("kana", SCENE_KANA), ("shino", SCENE_SHINO))
)
os.environ["H3_KEEP_RUNTIME"] = "1"
os.environ["H3_EPISODE_FRESH"] = "1" if FRESH else "0"
os.environ["H3_HELPER_BRANCH"] = BRANCH
_civitai = str(CivitaiのAPIキー or "").strip()
if _civitai:
    os.environ["CIVITAI_API_TOKEN"] = _civitai
print("Civitai API:", "フォームから読み込み済み（値は出しません）" if _civitai else "フォームは空（シークレットがあればそれを使う）")
del _civitai
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
print("成功。完成動画は Drive episodes/" + slug + "/final/ にあります。ランタイムはそのままです。赤い例外は出ません。")
'''

MD = f"""# MiniMax H3 エピソード一発（選んで Run all）

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)]({colab_url(FILE)})

**コードセルは1本。迷ったらドロップダウンはそのままで Run all。** Drive `minimax-h3-comfyui/episodes/<slug>/` に
`episode.json` とスチールが無ければ GitHub から取ってくる。全ビートを1つのランタイムで描き、
HUD・タイトル・免責エンドカードを載せて `final/<slug>-<日時>.mp4`（と `latest.mp4`）を書く。終わってもランタイムは切らない。

## 話 + 上から 9 つ + 病棟の追加（迷ったらそのまま）

**話** — どの予告を描くか

{form_readme("episode")}

**1. つなぎ方** — 動画をどう繋げるか。遭遇の入り（新しい相手）はカット。消滅はチェーンならフェード（飛ばない）

{form_readme("connect")}

**2. カメラ**

{form_readme("camera")}

**3. 画質**

{form_readme("preset")}

**4. 格闘 LoRA** — ハイメモリ専用の任意

{form_readme("combat")}

**5. 構成** — 病棟の話。完了か失敗かがここで分かれる

{form_readme("story")}

**6. 誘うポーズ** — 病棟の □誘う だけ。霞東は無視

{form_readme("invite_pose")}

**7. トイレ** — 病棟の道中。どれを選んでも次のシーンへ。霞東は無視

{form_readme("toilet")}

**8. 灰色の長い舌** — 病棟の追加オプション。出ないが既定。霞東は無視

{form_readme("gin")}

**9. 角の頭** — 病棟の追加オプション。立ちバックのみ。出ないが既定。霞東は無視

{form_readme("tsuno")}

登場チェックを外すと、その感染者のシーンを飛ばす（みき / れい / かな / しの）。**4人とも外すと作る場面が無くなって止まる。最低1人は残す。**

**シーンごと（病棟）** — 誘う（誘い方含む）・受け入れる・回避。5番が戦いのときは無視。霞東は無視。最後に残った人の構成で完了／失敗が決まる。

{form_readme("scene")}

シネマ LoRA は積まない。スローモーションの語は書かない。視点は三人称ゲームのまま。

- 本番の inbox / queued / output は触らない。`models/` だけ共有
- あさの 10Eros Max は Drive `models/diffusion_models/10Eros_Max_h3_TURBO-hybrid_beta5_int8.safetensors` を使う（HuggingFace からは取らない）
- Civitai の LoRA はコードセルの **CivitaiのAPIキー** に貼る（空のまま保存する。キーはコミットしない）。空なら Colab のシークレット `CIVITAI_API_TOKEN`。Drive に 1MB 超の同名ファイルがあれば再取得しない
- 途中で止まっても `raw/<beat>.mp4` があるビートは飛ばして再開（FRESH で作り直し）
- HUD・字幕は生成後に載せる。H3 に日本語UIを描かせない
- 投稿しない。アフィURL禁止。他のネタは `minimaxh3/episodes/_template` を複製して EPISODE を変える
- 話のドロップダウンで霞東あさ / 病棟出口 / 番台を選ぶ（スラッグは `kasumi-late-desk-adult` / `hospital-exit-adult` / `bandai-district-short`）。霞東は Colab 4 オフが行為ルート（Combat なし）。オン＋ハイメモリは戦いルートで 06 と 10 に Combat。病棟修正版は `BRANCH=cursor/h3-hospital-ward-34e4`。霞東本体 `kasumi-late-desk` は PR #141。このノートの Run all で本体 Drive を上書きするな
- 番台ショートは 25 秒・ミッション失敗で落ちる版。`bandai-district/raw/` の暖簾・自転車・軽トラをそのまま使い、新しく描くのは理容室の 1 本だけ
- 成功時は `episode exit 0` のあと「成功。」と出る。ランタイムは切らない。`SystemExit: 0` の赤い枠は出さない

セッション名 `{SESSION}`。GPU は A100。手順は `minimaxh3/episodes/README.md`。
"""


def make_nb() -> dict:
    cell = (
        CELL.replace("__BRANCH__", BRANCH)
        .replace("__REPO__", REPO)
        .replace("__HELPERS__", json.dumps(HELPERS, indent=4))
        .replace("__EPISODE_HELP__", form_markdown("episode", "話 — どの予告を描くか"))
        .replace("__EPISODE_DEFAULT__", json.dumps(ui_default("episode"), ensure_ascii=False))
        .replace("__EPISODE_CHOICES__", json.dumps(ui_choices("episode"), ensure_ascii=False))
        .replace("__CONNECT_HELP__", form_markdown("connect", "1. つなぎ方 — 動画をどう繋げるか。新しい相手の入りはカット。消滅はチェーンならフェード"))
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
        .replace("__STORY_HELP__", form_markdown("story", "5. 構成 — 病棟はここで完了か失敗かが分かれる"))
        .replace("__STORY_DEFAULT__", json.dumps(ui_default("story"), ensure_ascii=False))
        .replace("__STORY_CHOICES__", json.dumps(ui_choices("story"), ensure_ascii=False))
        .replace("__POSE_HELP__", form_markdown("invite_pose", "6. 誘うポーズ — 病棟の□誘うだけ"))
        .replace("__POSE_DEFAULT__", json.dumps(ui_default("invite_pose"), ensure_ascii=False))
        .replace("__POSE_CHOICES__", json.dumps(ui_choices("invite_pose"), ensure_ascii=False))
        .replace("__TOILET_HELP__", form_markdown("toilet", "7. トイレ — 病棟の道中。どれでも次へ"))
        .replace("__TOILET_DEFAULT__", json.dumps(ui_default("toilet"), ensure_ascii=False))
        .replace("__TOILET_CHOICES__", json.dumps(ui_choices("toilet"), ensure_ascii=False))
        .replace("__GIN_HELP__", form_markdown("gin", "8. 灰色の長い舌 — 病棟の追加。出ないが既定"))
        .replace("__GIN_DEFAULT__", json.dumps(ui_default("gin"), ensure_ascii=False))
        .replace("__GIN_CHOICES__", json.dumps(ui_choices("gin"), ensure_ascii=False))
        .replace("__TSUNO_HELP__", form_markdown("tsuno", "9. 角の頭 — 病棟の追加。立ちバックのみ"))
        .replace("__TSUNO_DEFAULT__", json.dumps(ui_default("tsuno"), ensure_ascii=False))
        .replace("__TSUNO_CHOICES__", json.dumps(ui_choices("tsuno"), ensure_ascii=False))
        .replace("__SCENE_DEFAULT__", json.dumps(ui_default("scene"), ensure_ascii=False))
        .replace("__SCENE_CHOICES__", json.dumps(ui_choices("scene"), ensure_ascii=False))
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
