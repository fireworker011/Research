#!/usr/bin/env python3
"""Write the one-click episode Colab notebook (one code cell: bootstrap → render all beats → HUD → stitch → stop)."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "minimaxh3"))

from h3_episode import EPISODE_HELPERS  # noqa: E402
from h3_episode_packs import (  # noqa: E402
    RIDE_FOOT_CHOICES,
    form_markdown,
    form_readme,
    ui_choices,
    ui_default,
)

BRANCH = "cursor/human-cast-anatomy-d736"
EPISODE_DEFAULT = "kasumi-late-desk-adult"
REPO = "fireworker011/Research"
FILE = "minimax_h3_episode_bot.ipynb"
SESSION = "h3-episode"
HELPERS = list(EPISODE_HELPERS)


def colab_url(path: str) -> str:
    return f"https://colab.research.google.com/github/{REPO}/blob/{quote(BRANCH, safe='')}/{path}"


CELL = r'''#@title 一発：話と上から 1〜11、登場とシーンを選んで Run all（迷ったらそのまま）
__EPISODE_HELP__
EPISODE = __EPISODE_DEFAULT__  #@param __EPISODE_CHOICES__
#@markdown ---
__CONNECT_HELP__
CONNECT = __CONNECT_DEFAULT__  #@param __CONNECT_CHOICES__
__CAMERA_HELP__
CAMERA = __CAMERA_DEFAULT__  #@param __CAMERA_CHOICES__
__DISTANCE_HELP__
CAMERA_DISTANCE = __DISTANCE_DEFAULT__  #@param __DISTANCE_CHOICES__
__PLACE_HELP__
PLACE = __PLACE_DEFAULT__  #@param __PLACE_CHOICES__
__TIME_HELP__
TIME_OF_DAY = __TIME_DEFAULT__  #@param __TIME_CHOICES__
__WEATHER_HELP__
WEATHER = __WEATHER_DEFAULT__  #@param __WEATHER_CHOICES__
__DIRT_HELP__
DIRT = __DIRT_DEFAULT__  #@param __DIRT_CHOICES__
__LOOK_HELP__
AYA_LOOK = __LOOK_DEFAULT__  #@param __LOOK_CHOICES__
#@markdown **あやの容姿。各欄の初期値は今のまま。国の見た目より、ここで選んだ欄が優先。**
__AYA_HAIR_HELP__
AYA_HAIR = __AYA_HAIR_DEFAULT__  #@param __AYA_HAIR_CHOICES__
__AYA_COLOR_HELP__
AYA_HAIR_COLOR = __AYA_COLOR_DEFAULT__  #@param __AYA_COLOR_CHOICES__
__AYA_FACE_HELP__
AYA_FACE = __AYA_FACE_DEFAULT__  #@param __AYA_FACE_CHOICES__
__AYA_BUST_HELP__
AYA_BUST = __AYA_BUST_DEFAULT__  #@param __AYA_BUST_CHOICES__
__AYA_BUTT_HELP__
AYA_BUTT = __AYA_BUTT_DEFAULT__  #@param __AYA_BUTT_CHOICES__
__AYA_BUILD_HELP__
AYA_BUILD = __AYA_BUILD_DEFAULT__  #@param __AYA_BUILD_CHOICES__
__AYA_HEIGHT_HELP__
AYA_HEIGHT = __AYA_HEIGHT_DEFAULT__  #@param __AYA_HEIGHT_CHOICES__
__AYA_DIRT_HELP__
AYA_DIRT = __AYA_DIRT_DEFAULT__  #@param __AYA_DIRT_CHOICES__
__AYA_SWEAT_HELP__
AYA_SWEAT = __AYA_SWEAT_DEFAULT__  #@param __AYA_SWEAT_CHOICES__
__AYA_CLOTHES_HELP__
AYA_CLOTHES = __AYA_CLOTHES_DEFAULT__  #@param __AYA_CLOTHES_CHOICES__
__AYA_SHAFT_HELP__
AYA_SHAFT = __AYA_SHAFT_DEFAULT__  #@param __AYA_SHAFT_CHOICES__
__ENEMY_KIND_HELP__
ENEMY_KIND = __ENEMY_KIND_DEFAULT__  #@param __ENEMY_KIND_CHOICES__
__ENEMY_LOOK_HELP__
LOOK_MIKI = __LOOK_DEFAULT__  #@param __LOOK_CHOICES__
LOOK_REI = __LOOK_DEFAULT__  #@param __LOOK_CHOICES__
LOOK_KANA = __LOOK_DEFAULT__  #@param __LOOK_CHOICES__
LOOK_SHINO = __LOOK_DEFAULT__  #@param __LOOK_CHOICES__
LOOK_GIN = __LOOK_DEFAULT__  #@param __LOOK_CHOICES__
LOOK_TSUNO = __LOOK_DEFAULT__  #@param __LOOK_CHOICES__
#@markdown **シード** — 空なら台本の 42。数字を書くとその回だけ絵が変わる。
SEED = "42"  #@param {type:"string"}
__PRESET_HELP__
PRESET = __PRESET_DEFAULT__  #@param __PRESET_CHOICES__
__COMBAT_HELP__
COMBAT = __COMBAT_DEFAULT__  #@param __COMBAT_CHOICES__
__STORY_HELP__
STORY = __STORY_DEFAULT__  #@param __STORY_CHOICES__
__POSE_HELP__
INVITE_POSE = __POSE_DEFAULT__  #@param __POSE_CHOICES__
#@markdown **騎乗・最初から膝曲げ** — 足裏は肋骨の左右。両膝は最初から曲がったまま下ろす。相手の手が乗る人の胸。選んだ人だけ。なしはシーンのまま。
RIDE_BENT = "なし"  #@param __RIDE_CHOICES__
#@markdown **騎乗・足を揃えて立ってから下ろす** — 跪きから一度まっすぐ立ち、足裏は肋骨のすぐ横。それから膝を曲げて下ろす。乗る人の手が仰向けの胸。選んだ人だけ。同じ人を両方で選ぶと、足を揃えて立ってから下ろす。
RIDE_COLUMN = "なし"  #@param __RIDE_CHOICES__
__CHECKPOINT_HELP__
CHECKPOINT = __CHECKPOINT_DEFAULT__  #@param __CHECKPOINT_CHOICES__
__TOILET_HELP__
TOILET = __TOILET_DEFAULT__  #@param __TOILET_CHOICES__
__GIN_HELP__
GIN = __GIN_DEFAULT__  #@param __GIN_CHOICES__
__TSUNO_HELP__
TSUNO = __TSUNO_DEFAULT__  #@param __TSUNO_CHOICES__
__DOG_HELP__
DOG = __DOG_DEFAULT__  #@param __DOG_CHOICES__
__SPECIES_HELP__
SPECIES = __SPECIES_DEFAULT__  #@param __SPECIES_CHOICES__
#@markdown **その他の自由記入。** その人の見た目が「その他」のときだけ使う。`hair=...; face=...`
FREE_MIKI = ""  #@param {type:"string"}
FREE_REI = ""  #@param {type:"string"}
FREE_KANA = ""  #@param {type:"string"}
FREE_SHINO = ""  #@param {type:"string"}
FREE_GIN = ""  #@param {type:"string"}
FREE_TSUNO = ""  #@param {type:"string"}
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
#@markdown **開始シーン** — 空なら最初から。beat id（例 `04-toilet`）を書くと、そのカットから先を今のドロップダウンどおりに作り直す。前のカットは残す。この設定の並びに無い id は止まる。
START = ""  #@param {type:"string"}
FRESH = False  #@param {type:"boolean"}
#@markdown **終わったあと** — 動画ができたあとのランタイム。迷ったらそのまま。チェックポイントだけの取得では切らない。
RUNTIME_AFTER = "そのまま（迷ったらこれ）"  #@param ["そのまま（迷ったらこれ）", "切る"]
#@markdown メモリ不足でそのカットが失敗したときだけ VRAM を下ろし、同じ尺をもう一度描く。それでも足りなければ短い尺に落とす。成功したカットの前には下ろさない。
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
os.environ["H3_EPISODE_CAMERA_DISTANCE"] = CAMERA_DISTANCE
os.environ["H3_EPISODE_PLACE"] = PLACE
os.environ["H3_EPISODE_TIME"] = TIME_OF_DAY
os.environ["H3_EPISODE_WEATHER"] = WEATHER
os.environ["H3_EPISODE_DIRT"] = DIRT
os.environ["H3_EPISODE_AYA_LOOK"] = AYA_LOOK
os.environ["H3_EPISODE_ENEMY_KIND"] = ENEMY_KIND
os.environ["H3_EPISODE_ENEMY_LOOKS"] = ",".join(
    f"{cid}={choice}"
    for cid, choice in (
        ("miki", LOOK_MIKI),
        ("rei", LOOK_REI),
        ("kana", LOOK_KANA),
        ("shino", LOOK_SHINO),
        ("gin", LOOK_GIN),
        ("tsuno", LOOK_TSUNO),
    )
)
_seed = str(SEED or "").strip()
if _seed:
    os.environ["H3_EPISODE_SEED"] = _seed
os.environ["H3_EPISODE_CONNECT"] = CONNECT
os.environ["H3_EPISODE_END_CONNECT"] = "follow"
os.environ["H3_EPISODE_COMBAT"] = COMBAT
os.environ["H3_EPISODE_STORY"] = STORY
os.environ["H3_EPISODE_INVITE_POSE"] = INVITE_POSE
os.environ["H3_EPISODE_RIDE_BENT"] = RIDE_BENT
os.environ["H3_EPISODE_RIDE_COLUMN"] = RIDE_COLUMN
os.environ["H3_EPISODE_CHECKPOINT"] = CHECKPOINT
os.environ["H3_EPISODE_TOILET"] = TOILET
os.environ["H3_EPISODE_GIN"] = GIN
os.environ["H3_EPISODE_TSUNO"] = TSUNO
os.environ["H3_EPISODE_DOG"] = DOG
os.environ["H3_EPISODE_SPECIES"] = SPECIES
os.environ["H3_EPISODE_AYA_HAIR"] = str(AYA_HAIR or "").strip()
os.environ["H3_EPISODE_AYA_COLOR"] = str(AYA_HAIR_COLOR or "").strip()
os.environ["H3_EPISODE_AYA_FACE"] = str(AYA_FACE or "").strip()
os.environ["H3_EPISODE_AYA_BUST"] = str(AYA_BUST or "").strip()
os.environ["H3_EPISODE_AYA_BUTT"] = str(AYA_BUTT or "").strip()
os.environ["H3_EPISODE_AYA_BUILD"] = str(AYA_BUILD or "").strip()
os.environ["H3_EPISODE_AYA_HEIGHT"] = str(AYA_HEIGHT or "").strip()
os.environ["H3_EPISODE_AYA_DIRT"] = str(AYA_DIRT or "").strip()
os.environ["H3_EPISODE_AYA_SWEAT"] = str(AYA_SWEAT or "").strip()
os.environ["H3_EPISODE_AYA_CLOTHES"] = str(AYA_CLOTHES or "").strip()
os.environ["H3_EPISODE_AYA_SHAFT"] = str(AYA_SHAFT or "").strip()
os.environ["H3_EPISODE_ENEMY_LOOK"] = "\n".join(
    f"{cid}; {text}"
    for cid, choice, text in (
        ("miki", LOOK_MIKI, FREE_MIKI),
        ("rei", LOOK_REI, FREE_REI),
        ("kana", LOOK_KANA, FREE_KANA),
        ("shino", LOOK_SHINO, FREE_SHINO),
        ("gin", LOOK_GIN, FREE_GIN),
        ("tsuno", LOOK_TSUNO, FREE_TSUNO),
    )
    if choice == "その他" and str(text or "").strip()
)
os.environ["H3_EPISODE_APPEAR"] = ",".join(
    name for name, on in (("miki", APPEAR_MIKI), ("rei", APPEAR_REI), ("kana", APPEAR_KANA), ("shino", APPEAR_SHINO)) if on
) or "none"
os.environ["H3_EPISODE_SCENES"] = ",".join(
    f"{name}={choice}"
    for name, choice in (("miki", SCENE_MIKI), ("rei", SCENE_REI), ("kana", SCENE_KANA), ("shino", SCENE_SHINO))
)
if RUNTIME_AFTER == "切る":
    os.environ.pop("H3_KEEP_RUNTIME", None)
    os.environ["H3_UNASSIGN_RUNTIME"] = "1"
else:
    os.environ["H3_KEEP_RUNTIME"] = "1"
    os.environ.pop("H3_UNASSIGN_RUNTIME", None)
os.environ["H3_EPISODE_START"] = str(START or "").strip()
os.environ["H3_EPISODE_FRESH"] = "1" if FRESH else "0"
os.environ["H3_HELPER_BRANCH"] = BRANCH
_civitai = str(CivitaiのAPIキー or "").strip()
if _civitai:
    os.environ["CIVITAI_API_TOKEN"] = _civitai
print("Civitai API:", "フォームから読み込み済み（値は出しません）" if _civitai else "フォームは空（シークレットがあればそれを使う）")
del _civitai
Path(DRIVE_ROOT, "models").mkdir(parents=True, exist_ok=True)

import torch
if torch.cuda.is_available():
    os.environ["H3_WEIGHTS_ONLY"] = "0"
    vram = torch.cuda.get_device_properties(0).total_memory / 1024 ** 3
    print("GPU:", torch.cuda.get_device_name(0), "VRAM GiB:", round(vram, 1))
    if vram < 20:
        os.environ["H3_WEIGHTS_ONLY"] = "1"
        print("VRAM が 20GiB 未満です。チェックポイントと LoRA だけ取ります。動画は A100 でもう一度 Run all。")
else:
    os.environ["H3_WEIGHTS_ONLY"] = "1"
    print("GPU はオフです。チェックポイントと LoRA を Drive に取ります。動画は描きません。終わったらランタイムを A100 にして、もう一度 Run all。")

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
from h3_i2v_runtime import maybe_unassign

rc = main()
print("episode exit", rc)
if rc:
    raise SystemExit(rc)
if os.environ.get("H3_WEIGHTS_ONLY") == "1":
    print("取得だけ終わりました。ランタイムを A100 にして、もう一度 Run all すると動画を描きます。")
elif os.environ.get("H3_UNASSIGN_RUNTIME") == "1":
    print("成功。完成動画は Drive episodes/" + slug + "/final/ にあります。ランタイムを切ります。赤い例外は出ません。")
    maybe_unassign()
else:
    print("成功。完成動画は Drive episodes/" + slug + "/final/ にあります。ランタイムはそのままです。赤い例外は出ません。")
'''

MD = f"""# MiniMax H3 エピソード一発（選んで Run all）

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)]({colab_url(FILE)})

**コードセルは1本。迷ったらドロップダウンはそのままで Run all。** Drive `minimax-h3-comfyui/episodes/<slug>/` に
`episode.json` とスチールが無ければ GitHub から取ってくる。全ビートを1つのランタイムで描き、
HUD・タイトル・免責エンドカードを載せて `final/<slug>-<日時>.mp4`（と `latest.mp4`）を書く。終わったあとが「そのまま」ならランタイムは切らない。「切る」なら動画ができたあと切る。チェックポイントだけの取得では切らない。

## 話 + 上から 11 つ + 病棟の追加（迷ったらそのまま）

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

**9. 角の頭** — 病棟の追加オプション。出ないが既定。騎乗と個室は新しい話。霞東は無視

{form_readme("tsuno")}

**10. 犬** — 病棟の追加オプション。出ないが既定。灰色はオフにしない。霞東は無視

{form_readme("dog")}

**11. 異種** — 病棟の追加オプション。スライムとケモノは同時に出ない。出ないが既定。霞東は無視

{form_readme("species")}

**容姿** — 空なら今の見た目のまま。あやは髪型、髪色、顔、肌の汚れ、汗、服装、竿。敵は1行に1人。英語だけ。`no` `never` `not` `without` `blood` は書かない。

登場チェックを外すと、その感染者のシーンを飛ばす（みき / れい / かな / しの）。**4人とも外すと作る場面が無くなって止まる。最低1人は残す。**

**シーンごと（病棟）** — 誘う（誘い方含む）・受け入れる・回避。5番が戦いのときは無視。霞東は無視。最後に残った人の構成で完了／失敗が決まる。

{form_readme("scene")}

シネマ LoRA は積まない。スローモーションの語は書かない。視点は三人称ゲームのまま。

- 本番の inbox / queued / output は触らない。`models/` だけ共有
- チェックポイントと LoRA の取得は CPU で足りる。ランタイムが CPU のときは Drive へ置いて止まり、Comfy は起動しない。動画を描くときだけ A100
- あさの 10Eros Max は Drive `models/diffusion_models/10Eros_Max_h3_TURBO-hybrid_beta5_int8.safetensors` を使う（HuggingFace からは取らない）
- Civitai の LoRA はコードセルの **CivitaiのAPIキー** に貼る（空のまま保存する。キーはコミットしない）。空なら Colab のシークレット `CIVITAI_API_TOKEN`。Drive に 1MB 超の同名ファイルがあれば再取得しない
- 途中で止まっても `raw/<beat>.mp4` があるビートは飛ばして再開（FRESH で作り直し）
- **開始シーン**に beat id を書くと、そのカットから先だけ今のドロップダウン（構成・トイレ・灰色・角・犬・異種・登場・シーンごと・つなぎ方）で作り直す。空なら最初から。前の動画は残して首にする。チェーンの前のカットが今の設定と違うとき、または動画が無いときは、そこまで戻って描く。並びに無い id は止まる
- HUD・字幕は生成後に載せる。H3 に日本語UIを描かせない
- 投稿しない。アフィURL禁止。他のネタは `minimaxh3/episodes/_template` を複製して EPISODE を変える
- 話のドロップダウンで霞東あさ / 病棟出口 / 番台を選ぶ（スラッグは `kasumi-late-desk-adult` / `hospital-exit-adult` / `bandai-district-short`）。霞東は Colab 4 オフが行為ルート（Combat なし）。オン＋ハイメモリは戦いルートで 06 と 10 に Combat。病棟修正版は `BRANCH=cursor/human-cast-anatomy-d736`。霞東本体 `kasumi-late-desk` は PR #141。このノートの Run all で本体 Drive を上書きするな
- 番台ショートは 25 秒・ミッション失敗で落ちる版。`bandai-district/raw/` の暖簾・自転車・軽トラをそのまま使い、新しく描くのは理容室の 1 本だけ
- 成功時は `episode exit 0` のあと「成功。」と出る。終わったあとが「そのまま（迷ったらこれ）」ならランタイムはそのまま。「切る」ならそのとき切る。チェックポイントだけの取得では切らない。`SystemExit: 0` の赤い枠は出さない

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
        .replace("__DISTANCE_HELP__", form_markdown("camera_distance", "カメラの距離 — 口と顔射は今の距離のまま"))
        .replace("__DISTANCE_DEFAULT__", json.dumps(ui_default("camera_distance"), ensure_ascii=False))
        .replace("__DISTANCE_CHOICES__", json.dumps(ui_choices("camera_distance"), ensure_ascii=False))
        .replace("__PLACE_HELP__", form_markdown("place", "場所 — 病棟なら名詞はそのまま。他は通路・壁・床・個室・寝床・出口だけ替わる"))
        .replace("__PLACE_DEFAULT__", json.dumps(ui_default("place"), ensure_ascii=False))
        .replace("__PLACE_CHOICES__", json.dumps(ui_choices("place"), ensure_ascii=False))
        .replace("__TIME_HELP__", form_markdown("time", "時間帯 — 光だけ。夜は文を足さない"))
        .replace("__TIME_DEFAULT__", json.dumps(ui_default("time"), ensure_ascii=False))
        .replace("__TIME_CHOICES__", json.dumps(ui_choices("time"), ensure_ascii=False))
        .replace("__WEATHER_HELP__", form_markdown("weather", "天候 — 床の濡れと光だけ"))
        .replace("__WEATHER_DEFAULT__", json.dumps(ui_default("weather"), ensure_ascii=False))
        .replace("__WEATHER_CHOICES__", json.dumps(ui_choices("weather"), ensure_ascii=False))
        .replace("__DIRT_HELP__", form_markdown("dirt", "あやの汚れ — 傷や敵の腐りは残す"))
        .replace("__DIRT_DEFAULT__", json.dumps(ui_default("dirt"), ensure_ascii=False))
        .replace("__DIRT_CHOICES__", json.dumps(ui_choices("dirt"), ensure_ascii=False))
        .replace("__LOOK_HELP__", form_markdown("look", "あやの国の見た目 — 今のままは下の各欄。国を選ぶと髪と顔。各欄を選ぶとその欄が優先"))
        .replace("__AYA_HAIR_HELP__", form_markdown("aya_hair", "あやの髪型"))
        .replace("__AYA_HAIR_DEFAULT__", json.dumps(ui_default("aya_hair"), ensure_ascii=False))
        .replace("__AYA_HAIR_CHOICES__", json.dumps(ui_choices("aya_hair"), ensure_ascii=False))
        .replace("__AYA_COLOR_HELP__", form_markdown("aya_color", "あやの髪色"))
        .replace("__AYA_COLOR_DEFAULT__", json.dumps(ui_default("aya_color"), ensure_ascii=False))
        .replace("__AYA_COLOR_CHOICES__", json.dumps(ui_choices("aya_color"), ensure_ascii=False))
        .replace("__AYA_FACE_HELP__", form_markdown("aya_face", "あやの顔"))
        .replace("__AYA_FACE_DEFAULT__", json.dumps(ui_default("aya_face"), ensure_ascii=False))
        .replace("__AYA_FACE_CHOICES__", json.dumps(ui_choices("aya_face"), ensure_ascii=False))
        .replace("__AYA_BUST_HELP__", form_markdown("aya_bust", "あやのバスト"))
        .replace("__AYA_BUST_DEFAULT__", json.dumps(ui_default("aya_bust"), ensure_ascii=False))
        .replace("__AYA_BUST_CHOICES__", json.dumps(ui_choices("aya_bust"), ensure_ascii=False))
        .replace("__AYA_BUTT_HELP__", form_markdown("aya_butt", "あやのお尻"))
        .replace("__AYA_BUTT_DEFAULT__", json.dumps(ui_default("aya_butt"), ensure_ascii=False))
        .replace("__AYA_BUTT_CHOICES__", json.dumps(ui_choices("aya_butt"), ensure_ascii=False))
        .replace("__AYA_BUILD_HELP__", form_markdown("aya_build", "あやの身体の細さ"))
        .replace("__AYA_BUILD_DEFAULT__", json.dumps(ui_default("aya_build"), ensure_ascii=False))
        .replace("__AYA_BUILD_CHOICES__", json.dumps(ui_choices("aya_build"), ensure_ascii=False))
        .replace("__AYA_HEIGHT_HELP__", form_markdown("aya_height", "あやの身長 — しのの長身は変えない"))
        .replace("__AYA_HEIGHT_DEFAULT__", json.dumps(ui_default("aya_height"), ensure_ascii=False))
        .replace("__AYA_HEIGHT_CHOICES__", json.dumps(ui_choices("aya_height"), ensure_ascii=False))
        .replace("__AYA_DIRT_HELP__", form_markdown("aya_dirt", "あやの汚れの種類 — 今のままは上の場所の汚れ"))
        .replace("__AYA_DIRT_DEFAULT__", json.dumps(ui_default("aya_dirt"), ensure_ascii=False))
        .replace("__AYA_DIRT_CHOICES__", json.dumps(ui_choices("aya_dirt"), ensure_ascii=False))
        .replace("__AYA_SWEAT_HELP__", form_markdown("aya_sweat", "あやの汗"))
        .replace("__AYA_SWEAT_DEFAULT__", json.dumps(ui_default("aya_sweat"), ensure_ascii=False))
        .replace("__AYA_SWEAT_CHOICES__", json.dumps(ui_choices("aya_sweat"), ensure_ascii=False))
        .replace("__AYA_CLOTHES_HELP__", form_markdown("aya_clothes", "あやの服"))
        .replace("__AYA_CLOTHES_DEFAULT__", json.dumps(ui_default("aya_clothes"), ensure_ascii=False))
        .replace("__AYA_CLOTHES_CHOICES__", json.dumps(ui_choices("aya_clothes"), ensure_ascii=False))
        .replace("__AYA_SHAFT_HELP__", form_markdown("aya_shaft", "あやの竿 — 長さは 24cm のまま"))
        .replace("__AYA_SHAFT_DEFAULT__", json.dumps(ui_default("aya_shaft"), ensure_ascii=False))
        .replace("__AYA_SHAFT_CHOICES__", json.dumps(ui_choices("aya_shaft"), ensure_ascii=False))
        .replace("__LOOK_DEFAULT__", json.dumps(ui_default("look"), ensure_ascii=False))
        .replace("__LOOK_CHOICES__", json.dumps(ui_choices("look"), ensure_ascii=False))
        .replace("__ENEMY_KIND_HELP__", form_markdown("enemy_kind", "敵の種類 — ゾンビは今の感染姿"))
        .replace("__ENEMY_KIND_DEFAULT__", json.dumps(ui_default("enemy_kind"), ensure_ascii=False))
        .replace("__ENEMY_KIND_CHOICES__", json.dumps(ui_choices("enemy_kind"), ensure_ascii=False))
        .replace("__ENEMY_LOOK_HELP__", form_markdown("look", "敵の見た目 — みき、れい、かな、しの、ぎん、角で別々。その他のときだけ自由記入"))
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
        .replace("__RIDE_CHOICES__", json.dumps(list(RIDE_FOOT_CHOICES), ensure_ascii=False))
        .replace("__CHECKPOINT_HELP__", form_markdown("checkpoint", "チェックポイント — 10Eros Max か DaSiWa"))
        .replace("__CHECKPOINT_DEFAULT__", json.dumps(ui_default("checkpoint"), ensure_ascii=False))
        .replace("__CHECKPOINT_CHOICES__", json.dumps(ui_choices("checkpoint"), ensure_ascii=False))
        .replace("__TOILET_HELP__", form_markdown("toilet", "7. トイレ — 洋式汚物、和式汚物、有機物植物の三択。触手は有機物だけ"))
        .replace("__TOILET_DEFAULT__", json.dumps(ui_default("toilet"), ensure_ascii=False))
        .replace("__TOILET_CHOICES__", json.dumps(ui_choices("toilet"), ensure_ascii=False))
        .replace("__GIN_HELP__", form_markdown("gin", "8. 灰色の長い舌 — 病棟の追加。出ないが既定"))
        .replace("__GIN_DEFAULT__", json.dumps(ui_default("gin"), ensure_ascii=False))
        .replace("__GIN_CHOICES__", json.dumps(ui_choices("gin"), ensure_ascii=False))
        .replace("__TSUNO_HELP__", form_markdown("tsuno", "9. 角の頭 — 病棟の追加。出ないが既定"))
        .replace("__TSUNO_DEFAULT__", json.dumps(ui_default("tsuno"), ensure_ascii=False))
        .replace("__TSUNO_CHOICES__", json.dumps(ui_choices("tsuno"), ensure_ascii=False))
        .replace("__DOG_HELP__", form_markdown("dog", "10. 犬 — 病棟の追加。出ないが既定。灰色はオフにしない"))
        .replace("__DOG_DEFAULT__", json.dumps(ui_default("dog"), ensure_ascii=False))
        .replace("__DOG_CHOICES__", json.dumps(ui_choices("dog"), ensure_ascii=False))
        .replace("__SPECIES_HELP__", form_markdown("species", "11. 異種 — 病棟の追加。スライムとケモノは同時に出ない"))
        .replace("__SPECIES_DEFAULT__", json.dumps(ui_default("species"), ensure_ascii=False))
        .replace("__SPECIES_CHOICES__", json.dumps(ui_choices("species"), ensure_ascii=False))
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
