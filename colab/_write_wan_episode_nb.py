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
_root = Path(ONEDRIVE)
if not _root.exists() and _root.parent.exists():
    _root.mkdir(parents=True, exist_ok=True)
_ready = _root.exists()
if not _ready:
    print("OneDrive がまだ見えない。上の「0. OneDrive をマウント」を先に実行する: " + ONEDRIVE)

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
    from wan_episode_colab_main import main
    raise SystemExit(main())
'''


MARKDOWN = """# 病棟出口 Wan 2.2（H3 の横）

H3 のノートはそのまま残す。このノートは描画だけ Wan 2.2 T2V / I2V。

データの保存先は OneDrive。Google Drive には書かない。

生成は下のセルを人間が実行したときだけ動く。このファイルを開いただけでは描かない。

1. 最初のコードセルで OneDrive を `/content/onedrive` にマウントする。使いたい Microsoft アカウントのトークンを貼る。
2. 次のセルの **CivitaiのAPIキー** にキーを貼って実行する。ComfyUI、チェックポイント、シーン LoRA の high / low をその OneDrive に取る。H3 の重みは取らない。キーは空のまま保存する。
3. 最後のセルを人間が実行する。開いただけでは描かない。
"""


MOUNT = r'''#@title 0. OneDrive をマウント（描画はしない）
#@markdown 使いたい Microsoft アカウントのトークンを貼る。ノートは空のまま保存する。値は表示しない。
#@markdown トークンは自分の PC の PowerShell で一度だけ取る。`winget install --id Rclone.Rclone -e` のあと、新しい PowerShell で `rclone authorize "onedrive"`。ブラウザでそのアカウントにログインし、矢印の間の JSON を下へ貼る。
ONEDRIVE_TOKEN = ""  #@param {type:"string"}

import json, os, shutil, subprocess, time, urllib.error, urllib.request
from pathlib import Path

def _run(args):
    env = dict(os.environ)
    env["PATH"] = "/usr/bin:/bin:" + env.get("PATH", "")
    return subprocess.run(args, capture_output=True, text=True, env=env)

if shutil.which("rclone") is None:
    subprocess.check_call(["bash", "-lc", "curl -fsSL https://rclone.org/install.sh | bash"])
if shutil.which("fusermount3") is None:
    subprocess.check_call(["bash", "-lc", "apt-get update -qq && DEBIAN_FRONTEND=noninteractive apt-get install -y -qq fuse3"])
if shutil.which("fusermount3") is None and Path("/bin/fusermount3").is_file():
    os.environ["PATH"] = "/bin:/usr/bin:" + os.environ.get("PATH", "")

raw = str(ONEDRIVE_TOKEN or "").strip()
start = raw.find("{")
end = raw.rfind("}")
token = raw[start:end + 1] if start >= 0 and end > start else ""
mount_point = Path("/content/onedrive")
project = mount_point / "wan-hospital"
if mount_point.is_mount():
    project.mkdir(parents=True, exist_ok=True)
    print("すでにマウント済み:", project)
elif not token:
    print('トークンが空です。PowerShell で rclone authorize "onedrive" を実行し、出た JSON を上の欄に貼ってから、このセルをもう一度実行する。')
else:
    try:
        parsed, _end = json.JSONDecoder().raw_decode(token)
    except json.JSONDecodeError:
        parsed = None
        print("JSON として読めません。{ から } までを1回だけ貼る。値は表示しません。")
    if isinstance(parsed, dict) and parsed.get("access_token") and parsed.get("refresh_token"):
        drive = None
        req = urllib.request.Request(
            "https://graph.microsoft.com/v1.0/me/drive",
            headers={"Authorization": "Bearer " + str(parsed["access_token"])},
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                drive = json.loads(resp.read().decode())
        except urllib.error.HTTPError as exc:
            print("ドライブの確認に失敗しました。HTTP", exc.code)
            print('rclone authorize "onedrive" をやり直して、{ から } までを1回だけ貼る。')
        except Exception:
            print("ドライブの確認に失敗しました。通信を確認して、このセルをもう一度実行する。")
        drive_id = str((drive or {}).get("id") or "")
        drive_type = str((drive or {}).get("driveType") or "")
        if not drive_id or not drive_type:
            print("drive_id が取れませんでした。{ から } までを1回だけ貼って、もう一度実行する。")
        else:
            conf = Path.home() / ".config" / "rclone" / "rclone.conf"
            conf.parent.mkdir(parents=True, exist_ok=True)
            conf.write_text(
                "[onedrive]\n"
                "type = onedrive\n"
                "drive_id = " + drive_id + "\n"
                "drive_type = " + drive_type + "\n"
                "token = " + json.dumps(parsed, separators=(",", ":")) + "\n",
                encoding="utf-8",
            )
            print("ドライブを確認した:", drive_type)
            del parsed, token, raw
            mount_point.mkdir(parents=True, exist_ok=True)
            proc = _run([
                "rclone", "mount", "onedrive:", str(mount_point),
                "--daemon",
                "--vfs-cache-mode", "writes",
                "--dir-cache-time", "5s",
                "--log-file", "/tmp/rclone-mount.log",
                "--log-level", "NOTICE",
            ])
            for _ in range(30):
                if mount_point.is_mount():
                    break
                time.sleep(1)
            if mount_point.is_mount():
                project.mkdir(parents=True, exist_ok=True)
                print("マウントした:", project)
            else:
                print("マウントできませんでした。")
                log = Path("/tmp/rclone-mount.log")
                if log.is_file():
                    tail = log.read_text(encoding="utf-8", errors="replace").splitlines()[-20:]
                    print("\n".join(tail))
                elif proc.stderr:
                    print(proc.stderr[-500:])
    elif parsed is not None:
        print("access_token と refresh_token がある JSON を貼る。")
        del parsed
'''

SETUP = '''#@title 1. OneDrive へ Wan 2.2 の重みを取る（描画はしない）
ONEDRIVE = "/content/onedrive/wan-hospital"  #@param {type:"string"}
#@markdown **CivitaiのAPIキー** — このセルを実行する前に貼る。空のままノートを保存する。値は表示しない。空なら Colab のシークレット `CIVITAI_API_TOKEN`。
CivitaiのAPIキー = ""  #@param {type:"string"}

import os, sys, urllib.request
from pathlib import Path

if "mydrive" in ONEDRIVE.lower() or "/content/drive" in ONEDRIVE.replace("\\\\", "/").lower():
    raise SystemExit("OneDrive 以外には書かない: " + ONEDRIVE)
_root = Path(ONEDRIVE)
if not _root.exists() and _root.parent.exists():
    _root.mkdir(parents=True, exist_ok=True)
if not _root.exists():
    print("OneDrive がまだ見えない。上の「0. OneDrive をマウント」を先に実行する: " + ONEDRIVE)
else:
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
