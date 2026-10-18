#!/usr/bin/env python3
"""Write the H3 Studio Colab notebook and mirror colab/h3_studio.py to minimaxh3/."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "colab"))

from h3_studio import JOB_HELP, JOBS, STUDIO_HELPERS  # noqa: E402

BRANCH = "cursor/h3-sfw-colab-6dc5"
REPO = "fireworker011/Research"
FILE = "minimax_h3_studio_bot.ipynb"
SESSION = "h3-studio"

SCENES_CELL = r'''#@title text_scene を7本書く（生成はしない）
import json
import sys
from pathlib import Path

sys.path.insert(0, "/content")
from h3_studio import GENERATE_MSG, build_text_scenes

plan = build_text_scenes()
if plan.get("generate"):
    raise SystemExit(GENERATE_MSG)
dest = Path("h3_studio_text_scenes.json")
try:
    from google.colab import drive
    drive.mount("/content/drive")
    dest = Path("/content/drive/MyDrive/minimax-h3-comfyui/studio/text-scenes.json")
    dest.parent.mkdir(parents=True, exist_ok=True)
except ImportError:
    print("Colab の外。プランは h3_studio_text_scenes.json に書く。")
dest.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("WROTE", dest)
print("clips", [clip["scene_id"] for clip in plan["clips"]])
print(GENERATE_MSG)
'''


MEASURE_CELL = r'''#@title live_remake：元動画を測ってシートの骨組みを書く（生成はしない）
#@markdown 元動画の秒、大きさ、fps、音、カットを測る。役の静止画と範囲の文は「入力」のまま残る。
SOURCE = ""  #@param {type:"string"}
MAX_SPAN = "8"  #@param ["8", "6", "10", "12", "14.375"]
THRESHOLD = "0.35"  #@param ["0.35", "0.25", "0.45"]
MIN_SHOT = "0.5"  #@param ["0.5", "0.3", "1.0"]
BRANCH = "__BRANCH__"  #@param {type:"string"}

import json, sys, urllib.request
from pathlib import Path

RAW = f"https://raw.githubusercontent.com/__REPO__/{BRANCH}"
for rel in ("colab/h3_sfw.py", "colab/h3_live_remake.py"):
    dest = Path("/content") / Path(rel).name
    urllib.request.urlretrieve(f"{RAW}/{rel}", dest)
    if not dest.is_file() or dest.stat().st_size < 50:
        raise SystemExit(f"helper missing: {rel}")
sys.path.insert(0, "/content")
from h3_live_remake import GENERATE_MSG, measure

if not SOURCE:
    raise SystemExit("SOURCE に元動画の場所を書く")
sheet = measure(SOURCE, threshold=float(THRESHOLD), min_shot_s=float(MIN_SHOT), max_span_s=float(MAX_SPAN))
dest = Path("remake-sheet.json")
try:
    from google.colab import drive
    drive.mount("/content/drive")
    dest = Path("/content/drive/MyDrive/minimax-h3-comfyui/studio/remake-sheet.json")
    dest.parent.mkdir(parents=True, exist_ok=True)
except ImportError:
    print("Colab の外。シートは remake-sheet.json に書く。")
dest.write_text(json.dumps(sheet, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("WROTE", dest)
print(sheet["cuts_from"])
for span in sheet["spans"]:
    print(f"範囲 {span['index']}: {span['start_s']}–{span['end_s']}秒 ショット{span['shots']}" + ("（ショットの中で割った）" if span["split_inside_shot"] else ""))
print("cast に役の静止画、各範囲に cast と文を入れてから、上のセルで JOB=live_remake、REMAKE_SHEET にこのパス。")
print(GENERATE_MSG)
'''


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
FAST_SECONDS = "6"  #@param ["6", "9"]
WITH_ACTION = False  #@param {type:"boolean"}
WITH_COMBAT = False  #@param {type:"boolean"}
TEMPLATE = "buy_before"  #@param ["buy_before", "daily_food", "daily_camera"]
PARTS = "6,9"  #@param {type:"string"}
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
#@markdown **longform_chunk だけ。総尺とチャンク秒。チャンクは 5–8。runtime=comfy のときだけ Continuum を custom_nodes に足す。**
TOTAL = "10"  #@param {type:"string"}
CHUNK = "5"  #@param ["5", "6", "7", "8"]
#@markdown **live_remake だけ。下の「元動画を測る」が書いたシートに、役の静止画と範囲の文を入れたもの。**
REMAKE_SHEET = ""  #@param {type:"string"}
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
os.environ["H3_STUDIO_DURATION"] = TOTAL if JOB == "longform_chunk" else DURATION
os.environ["H3_STUDIO_CHUNK_SECONDS"] = CHUNK
os.environ["H3_STUDIO_REMAKE_SHEET"] = REMAKE_SHEET
os.environ["H3_STUDIO_FAST_SECONDS"] = FAST_SECONDS
os.environ["H3_STUDIO_WITH_ACTION"] = "1" if WITH_ACTION else "0"
os.environ["H3_STUDIO_WITH_COMBAT"] = "1" if WITH_COMBAT else "0"
os.environ["H3_STUDIO_TEMPLATE"] = TEMPLATE
os.environ["H3_STUDIO_PARTS"] = PARTS
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

`fast_motion` はスピード LoRA（Turbo 8step、steps 9、video shift 6）。アクション 0.6 とコンバット 0.7 はチェックで足す。格闘の `prfight2` は `combat_motion` だけ。
キャラは Hero の項目と `swap_character`。場所は Hero / Enemy の place。空欄は Look に出ない。シーンは `text_scene`。
`join` は 6 秒と 9 秒を足して 15 秒以上にする。1 本の 15 秒生成はしない。ffmpeg は実行しない。
`affi_template` は既存のバズ型台本を指す。台本は書き換えない。
Combat の格闘と Swap は Turbo を切る。本体は Comfy High-Mem。
Weapon / GunFu / Continuity は無い。orbit の LoRA ファイル名は未確定。アダルト用ノートはこのブランチに無い。
`longform_chunk` は Comfy だけ。`runtime=comfy` のプランに `git clone https://github.com/ukr8b3g-cmyk/ComfyUI-H3-Continuum.git` を custom_nodes へ書く。追加の pip は無い。api では止まる。
`live_remake` は Comfy だけ。一番下のセルで元動画を測り、シートに役の静止画と範囲ごとの文を入れる。範囲の文は Grok Build の `video-to-h3-prompt` の出力から貼る。静止画が顔と衣装、元動画が秒とカメラ。範囲ごとに Ref2VA + anime2real 1.0。足りない静止画や文があると止まる。手順は `artifacts/LIVE-REMAKE-H3.md`。
生成ノートは `h3-runner/minimax_h3_still.ipynb`。

下の2つ目のコードセルは `text_scene` を7本書く。公式 Hailuo の T2VA。LoRA なし。Combat も charswap も切る。各本6秒、16:9、768P、24fps、1ショット。ポスターは静止画。顔固定はこの7本に載せない。生成ボタンは押さない。
並び: `hana-gate`、`host-live`、`hana-cart`、`hana-shelf`、`host-drop`、`hana-box`、`hana-exit`。
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
    measure = MEASURE_CELL.replace("__BRANCH__", BRANCH).replace("__REPO__", REPO)
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
            {
                "cell_type": "code",
                "metadata": {"id": "studio_scenes"},
                "execution_count": None,
                "outputs": [],
                "source": [line + "\n" for line in SCENES_CELL.strip("\n").split("\n")],
            },
            {
                "cell_type": "code",
                "metadata": {"id": "studio_remake_measure"},
                "execution_count": None,
                "outputs": [],
                "source": [line + "\n" for line in measure.strip("\n").split("\n")],
            },
        ],
    }


def mirror_engine() -> None:
    for name in ("h3_studio.py", "h3_live_remake.py"):
        src = ROOT / "colab" / name
        dest = ROOT / "minimaxh3" / name
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
