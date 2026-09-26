#!/usr/bin/env python3
"""Write the Wan hospital notebook beside the H3 notebook. Does not touch the H3 notebook."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "minimaxh3"))

from h3_episode_packs import ui_choices, ui_default  # noqa: E402

BRANCH = "cursor/h3-hospital-ward-34e4"
NAME = "wan_hospital_episode_bot.ipynb"


def _param(kind: str) -> str:
    choices = json.dumps(ui_choices(kind), ensure_ascii=False)
    return choices


def _field(name: str, kind: str) -> str:
    return (
        f"{name} = {json.dumps(ui_default(kind), ensure_ascii=False)}"
        f"  #@param {_param(kind)}"
    )


def code_cell() -> str:
    return f'''#@title 病棟出口を Wan 2.2 で描く（人間がこのセルを実行する）
EPISODE = "hospital-exit-adult"
#@markdown **1. つなぎ方**
{_field("CONNECT", "connect")}
#@markdown **2. カメラ**
{_field("CAMERA", "camera")}
#@markdown **3. 速さ**
{_field("PRESET", "preset")}
#@markdown **4. 格闘**
{_field("COMBAT", "combat")}
#@markdown **5. 構成（病棟全体。シーンごとの指定が「従う」のとき使う）**
{_field("STORY", "story")}
#@markdown **6. 誘うときの体**
{_field("INVITE_POSE", "invite_pose")}
#@markdown **7. トイレ**
{_field("TOILET", "toilet")}
#@markdown **8. 灰色**
{_field("GIN", "gin")}
#@markdown **9. 角**
{_field("TSUNO", "tsuno")}
#@markdown **10. 犬**
{_field("DOG", "dog")}
#@markdown **11. 異種**
{_field("SPECIES", "species")}
#@markdown **登場（病棟）。外すとその人のシーンを飛ばす。4人とも外すと止まる。**
APPEAR_MIKI = True  #@param {{type:"boolean"}}
APPEAR_REI = True  #@param {{type:"boolean"}}
APPEAR_KANA = True  #@param {{type:"boolean"}}
APPEAR_SHINO = True  #@param {{type:"boolean"}}
#@markdown **シーンごと。誘うは誘い方も含む。戦い構成は無視。**
{_field("SCENE_MIKI", "scene")}
{_field("SCENE_REI", "scene")}
{_field("SCENE_KANA", "scene")}
{_field("SCENE_SHINO", "scene")}
FRESH = False  #@param {{type:"boolean"}}
DRY_RUN = False  #@param {{type:"boolean"}}
ONEDRIVE = "/content/onedrive/wan-hospital"  #@param {{type:"string"}}

import os, sys
from pathlib import Path

os.environ["WAN_ONEDRIVE_ROOT"] = ONEDRIVE
os.environ["WAN_EPISODE"] = EPISODE
os.environ["WAN_EPISODE_JSON"] = "/content/minimaxh3/episodes/hospital-exit-adult/episode.json"
os.environ["WAN_EPISODE_CONNECT"] = CONNECT
os.environ["WAN_EPISODE_CAMERA"] = CAMERA
os.environ["WAN_EPISODE_PRESET"] = PRESET
os.environ["WAN_EPISODE_COMBAT"] = COMBAT
os.environ["WAN_EPISODE_STORY"] = STORY
os.environ["WAN_EPISODE_INVITE_POSE"] = INVITE_POSE
os.environ["WAN_EPISODE_TOILET"] = TOILET
os.environ["WAN_EPISODE_GIN"] = GIN
os.environ["WAN_EPISODE_TSUNO"] = TSUNO
os.environ["WAN_EPISODE_DOG"] = DOG
os.environ["WAN_EPISODE_SPECIES"] = SPECIES
os.environ["WAN_EPISODE_APPEAR"] = ",".join(
    name for name, on in (("miki", APPEAR_MIKI), ("rei", APPEAR_REI), ("kana", APPEAR_KANA), ("shino", APPEAR_SHINO)) if on
) or "none"
os.environ["WAN_EPISODE_SCENES"] = ",".join(
    f"{{name}}={{choice}}"
    for name, choice in (("miki", SCENE_MIKI), ("rei", SCENE_REI), ("kana", SCENE_KANA), ("shino", SCENE_SHINO))
)
os.environ["WAN_EPISODE_FRESH"] = "1" if FRESH else "0"
os.environ["WAN_DRY_RUN"] = "1" if DRY_RUN else "0"
os.environ["WAN_COMFY_DIR"] = "/content/ComfyUI"

if "mydrive" in ONEDRIVE.lower() or "/content/drive" in ONEDRIVE.replace("\\\\", "/").lower():
    raise SystemExit("OneDrive 以外には書かない: " + ONEDRIVE)
if not Path(ONEDRIVE).exists():
    raise SystemExit("OneDrive がまだ見えない: " + ONEDRIVE + " — rclone でマウントしてから、もう一度このセルを実行する")

RAW = "https://raw.githubusercontent.com/fireworker011/Research/{BRANCH}"
NEEDED = [
    "colab/h3_episode.py",
    "colab/h3_episode_packs.py",
    "colab/h3_hud.py",
    "colab/h3_t2v.py",
    "colab/h3_i2v_phone.py",
    "colab/h3_i2v_runtime.py",
    "colab/h3_i2v_job.py",
    "colab/h3_motion_graphics.py",
    "colab/h3_r2v_core.py",
    "colab/wan_episode.py",
    "colab/wan_episode_colab_main.py",
    "colab/wan_colab_setup.py",
    "minimaxh3/episodes/hospital-exit-adult/episode.json",
]
import urllib.request
for rel in NEEDED:
    dest = Path("/content") / Path(rel).name if rel.startswith("colab/") else Path("/content") / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(f"{{RAW}}/{{rel}}", dest)
    print("fetched", rel)
sys.path.insert(0, "/content")
from wan_episode_colab_main import main
raise SystemExit(main())
'''


MARKDOWN = """# 病棟出口 Wan 2.2（H3 の横）

H3 のノートはそのまま残す。このノートは描画だけ Wan 2.2 T2V / I2V。

データの保存先は OneDrive。Google Drive には書かない。

生成は下のセルを人間が実行したときだけ動く。このファイルを開いただけでは描かない。

1. Colab では rclone で OneDrive を `/content/onedrive` にマウントする。
2. 次のセルで ComfyUI と Wan 2.2 の fp8 重み、スロット LoRA（high / low）を OneDrive に取る。H3 の重みは取らない。
3. アナル、小便、脱糞、四つん這い、正常位の追加 LoRA は `colab/WAN_CIVITAI_LINKS.md`。Civitai API で自分で取る。このノートは落とさない。
4. 最後のセルを人間が実行する。開いただけでは描かない。
"""


SETUP = '''#@title 1. OneDrive へ Wan 2.2 の重みを取る（描画はしない）
ONEDRIVE = "/content/onedrive/wan-hospital"  #@param {type:"string"}

import os, sys, urllib.request
from pathlib import Path

if "mydrive" in ONEDRIVE.lower() or "/content/drive" in ONEDRIVE.replace("\\\\", "/").lower():
    raise SystemExit("OneDrive 以外には書かない: " + ONEDRIVE)
if not Path(ONEDRIVE).exists():
    raise SystemExit("OneDrive がまだ見えない: " + ONEDRIVE + " — rclone で /content/onedrive にマウントしてから、このセルをもう一度実行する")

RAW = "https://raw.githubusercontent.com/fireworker011/Research/cursor/h3-hospital-ward-34e4"
for rel in (
    "colab/wan_episode.py",
    "colab/wan_colab_setup.py",
    "colab/h3_episode.py",
    "colab/h3_episode_packs.py",
    "colab/h3_hud.py",
    "colab/h3_t2v.py",
    "colab/h3_i2v_phone.py",
    "colab/h3_i2v_runtime.py",
    "colab/h3_i2v_job.py",
    "colab/h3_motion_graphics.py",
    "colab/h3_r2v_core.py",
):
    dest = Path("/content") / Path(rel).name
    urllib.request.urlretrieve(f"{RAW}/{rel}", dest)
    print("fetched", rel)
sys.path.insert(0, "/content")
os.environ["WAN_ONEDRIVE_ROOT"] = ONEDRIVE
from wan_colab_setup import setup
setup(Path(ONEDRIVE), Path("/content/ComfyUI"))
'''


def _lines(text: str) -> list[str]:
    return [line + "\n" for line in text.splitlines()]


def notebook() -> dict:
    code = code_cell()
    return {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {
            "colab": {"name": NAME, "provenance": []},
            "kernelspec": {"display_name": "Python 3", "name": "python3"},
        },
        "cells": [
            {"cell_type": "markdown", "metadata": {}, "source": _lines(MARKDOWN)},
            {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [], "source": _lines(SETUP)},
            {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [], "source": _lines(code)},
        ],
    }


def main() -> None:
    text = json.dumps(notebook(), ensure_ascii=False, indent=1) + "\n"
    for path in (ROOT / NAME, ROOT / "minimaxh3" / NAME):
        path.write_text(text, encoding="utf-8")
        print("wrote", path)


if __name__ == "__main__":
    main()
