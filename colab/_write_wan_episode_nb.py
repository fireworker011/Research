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
STORE = "/content/drive/MyDrive/wan-hospital"  #@param {{type:"string"}}

import os, sys
from pathlib import Path
from google.colab import drive
drive.mount("/content/drive")

os.environ["WAN_ONEDRIVE_ROOT"] = STORE
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
os.environ["WAN_FETCH_LORAS"] = "0" if DRY_RUN else "1"
os.environ["WAN_COMFY_DIR"] = "/content/ComfyUI"

_root = Path(STORE)
if Path("/content/drive/MyDrive").exists():
    _root.mkdir(parents=True, exist_ok=True)
_ready = _root.exists()
if not _ready:
    print("Google Drive がまだ見えない。上のセルを先に実行する: " + STORE)

if _ready:
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
    import importlib
    import h3_i2v_phone
    import h3_i2v_runtime
    import wan_colab_setup
    import wan_episode
    import wan_episode_colab_main
    importlib.reload(h3_i2v_phone)
    importlib.reload(h3_i2v_runtime)
    importlib.reload(wan_colab_setup)
    importlib.reload(wan_episode)
    importlib.reload(wan_episode_colab_main)
    main = wan_episode_colab_main.main
    raise SystemExit(main())
'''


MARKDOWN = """# 病棟出口 Wan 2.2（H3 の横）

H3 のノートはそのまま残す。このノートは描画だけ Wan 2.2 T2V / I2V。

保存先は Google ドライブのマイドライブ `wan-hospital`。

生成は最後のセルを人間が実行したときだけ動く。このファイルを開いただけでは描かない。

1. 最初のセルで Google ドライブを接続する。GPU は要らない。
2. 次のセルで、まだ無い重みだけドライブへ取る。CPU ランタイムでよい。すでにあるファイルは飛ばす。Civitai のキーはここ。
3. 最後のセルは GPU で、ドライブにある重みを使って描く。重みの取り直しはしない。
"""


MOUNT = r'''#@title 0. Google Drive を接続（描画しない。GPU 不要）
#@markdown マイドライブに wan-hospital を作る。重みは次のセル。
from google.colab import drive
from pathlib import Path
drive.mount("/content/drive")
root = Path("/content/drive/MyDrive/wan-hospital")
(root / "models").mkdir(parents=True, exist_ok=True)
(root / "episodes").mkdir(parents=True, exist_ok=True)
print("保存先:", root)
'''

SETUP = '''#@title 1. 初回だけ重みを Google Drive へ（GPU 不要）
STORE = "/content/drive/MyDrive/wan-hospital"  #@param {type:"string"}
#@markdown **CivitaiのAPIキー** — このセルを実行する前に貼る。空のままノートを保存する。値は表示しない。空なら Colab のシークレット `CIVITAI_API_TOKEN`。すでにある重みは飛ばす。
CivitaiのAPIキー = ""  #@param {type:"string"}

import os, sys, urllib.request
from pathlib import Path
from google.colab import drive
drive.mount("/content/drive")

_root = Path(STORE)
if not Path("/content/drive/MyDrive").exists():
    print("Google Drive がまだ見えない。上のセルを先に実行する。")
else:
    _root.mkdir(parents=True, exist_ok=True)
    _civitai = str(CivitaiのAPIキー or "").strip()
    if not _civitai:
        try:
            from google.colab import userdata
            _civitai = str(userdata.get("CIVITAI_API_TOKEN") or "").strip()
        except Exception:
            _civitai = ""
    if _civitai:
        os.environ["CIVITAI_API_TOKEN"] = _civitai
    print("Civitai API:", "読み込み済み（値は出しません）" if _civitai else "空。Civitai のファイルは取れません")
    del _civitai

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
    os.environ["WAN_ONEDRIVE_ROOT"] = STORE
    import importlib
    import wan_colab_setup
    import wan_episode
    importlib.reload(wan_episode)
    importlib.reload(wan_colab_setup)
    wan_colab_setup.setup(Path(STORE), Path("/content/ComfyUI"))
    print("重みの場所:", STORE)
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
            {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [], "source": _lines(MOUNT)},
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
