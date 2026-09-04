#!/usr/bin/env python3
"""Write a beginner-friendly MiniMax H3 LoRA studio Colab."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTS = [
    ROOT / "minimax_h3_lora_studio.ipynb",
    ROOT / "minimaxh3" / "minimax_h3_lora_studio.ipynb",
    ROOT / "h3-lora-studio" / "minimax_h3_lora_studio.ipynb",
]

MD0 = r"""# MiniMax H3 で動画を作る（速い＋綺麗 / えっち）

写真なしの文章から、または写真1枚から、短い動画を作ります。

**18歳未満は使えません。出演者は全員 21歳以上の設定です。**

このノートは Google Colab の画面の中で完結します。難しいソフトの画面は開きません。

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/fireworker011/Research/blob/cursor/minimax-h3-motion-identity-e959/minimax_h3_lora_studio.ipynb)

## やること（3つだけ）

1. **①** を実行 → Google Drive の許可を出す
2. **②** を実行 → 初回だけ待ちます（部品のダウンロード。2回目は速い）
3. **③** でシーンを選んで実行 → 下に動画が出る

初めてなら **日常（速い＋綺麗）** のままで大丈夫です。シネマ質感を取るので **②の「CivitaiのAPIキー」を貼って**、上から順に ▶ を押す。**普通（エロなし）だけ**（専用ノートと同じ LightX2V）ならキーは空でOK。

## 準備（最初の1回）

1. 上の **Open in Colab** を開く
2. 右上の **ランタイム → ランタイムのタイプを変更 → GPU を A100**
3. **Civitai の API キー**（シネマ質感とえっち用。**普通（エロなし）だけなら不要**）
   - https://civitai.com/user/account を開く → 下の **API Keys** → **Add API key** → コピー
   - **②の「CivitaiのAPIキー」欄に貼る**（このノートのフォーム。左の鍵マークは使わなくてよい）
   - キーは画面に出ません。ノートを保存する前に欄を空に戻す
4. メニュー **ランタイム → すべてのセルを実行** でも、①②③を順に押しても同じ

できた動画は Google Drive の  
`マイドライブ / minimax-h3-comfyui / output`

このフォルダは、普通の I2V / T2V ノートと**同じ**です。土台（FL2VA）と速いモード（Turbo）を共用します。ノートを別々に開いても、同じ Colab の③で「普通（エロなし）」を選んでも大丈夫です。同時に2つのノートを動かさないでください。

写真から作るときは、同じ Drive の `input` フォルダに jpg を置いてから ③ を実行。

普通の専用ノート:
- [I2V（写真から・エロなし）](https://colab.research.google.com/github/fireworker011/Research/blob/cursor/minimax-h3-motion-identity-e959/minimax_h3_i2v_phone.ipynb)
- [T2V（文章から・エロなし）](https://colab.research.google.com/github/fireworker011/Research/blob/cursor/minimax-h3-motion-identity-e959/minimax_h3_t2v_phone.ipynb)

## シーンの選び方（③で選ぶ）

| ③で選ぶ名前 | どんな動画 | 自動で入る部品 |
|---|---|---|
| 日常（速い＋綺麗） | 会話・商品・風景 | Larry v4 1.0 + シネマ 0.65 / 8step |
| 最速プレビュー（エロなし） | 量産プレビュー | LightX2V 4step 1.0 + シネマ 0.4 |
| 音も残す（エロなし） | 音を残して速く | LightX2V 8step 1.0 + シネマ 0.4 |
| 普通（エロなし） | 専用 I2V / T2V と同じ | LightX2V 4step だけ。画質 LoRA なし |
| アナル挿入（画質） | 穴が見える挿入。本線 | CoachBate 0.85 + 穴の見え方 0.55。Turbo なし |
| アナル舐め・指 | 舐め・指のアップ | 穴の見え方 0.7 + Larry 0.5 + シネマ 0.4 |
| フェラ | フェラ本線 | フェラ 0.75 + 竿 0.7 + Larry 0.7 |
| ふたなりフェラ | フェラと同じ積み。AIO なし | フェラ + 竿 + Larry |
| 汎用エロ | 挿入が曖昧でいい | AIO 0.75 + LightX2V 0.5 / 12 step |
| 試し打ち | エロの量産プレビュー | AIO 0.7 + LightX2V 4step。当たりは本線で焼き直し |

**エロなしの重ね:** Turbo1 + 画質1。速さ用と画質用を分ける。Larry と LightX2V は同時に積まない。
**エロの重ね:** 行為1 + ヘルパー1 + Turbo1。シネマを足すならヘルパーを落とす。挿入ショットに Turbo は切る。Fal には載せない。

**プロンプトは任意。** 空ならシーンのおすすめ文。自分の文を③の欄に貼ってもよい。写真からのときは顔ロック（Picture 1）を自動で足します。禁止語の extra は Drive の `forbidden.json` か③の欄。未成年ロックは外せません。

上級の追加部品（リアル寄せ・胸など）は重ね上限のため無視します。
"""

MD1 = r"""## ① Google Drive をつなぐ

下のセルを実行すると、許可のポップアップが出ます。**許可** を押してください。

フォームは触らなくて大丈夫です。GPU が A100 でないとここで止まります。
"""

CELL1 = r'''#@title ① Drive の許可を出す（ここは触らなくてOK）
print("① Google Drive につないでいます…")

from google.colab import drive
import os

DRIVE_ROOT = "/content/drive/MyDrive/minimax-h3-comfyui"  #@param {type:"string"}
COMFY_DIR = "/content/ComfyUI"

drive.mount("/content/drive")

DRIVE_MODELS = f"{DRIVE_ROOT}/models"
for sub in ["diffusion_models", "text_encoders", "vae", "loras"]:
    os.makedirs(f"{DRIVE_MODELS}/{sub}", exist_ok=True)
os.makedirs(f"{DRIVE_ROOT}/output", exist_ok=True)
os.makedirs(f"{DRIVE_ROOT}/input", exist_ok=True)

with open("/content/h3_paths.env", "w") as f:
    f.write(f"DRIVE_ROOT={DRIVE_ROOT}\n")
    f.write(f"DRIVE_MODELS={DRIVE_MODELS}\n")
    f.write(f"COMFY_DIR={COMFY_DIR}\n")

import torch
if not torch.cuda.is_available():
    raise SystemExit("GPU がオフです。上のメニュー「ランタイム」→「ランタイムのタイプを変更」→ GPU を A100 にして、①からやり直してください。")
props = torch.cuda.get_device_properties(0)
vram = props.total_memory / 1024 ** 3
print("つながった Drive:", DRIVE_ROOT)
print("動画の保存先:", f"{DRIVE_ROOT}/output")
print("写真を置く場所:", f"{DRIVE_ROOT}/input")
print("GPU:", torch.cuda.get_device_name(0), "メモリ:", round(vram, 1), "GB")
if vram < 20:
    raise SystemExit("メモリが足りません。GPU を A100 にしてください。")
print()
print("① 完了。次は②を実行してください。初回は待ちます。")
'''

MD2 = r"""## ② 部品を用意する（初回だけ長い）

下のセルで、動画の土台と部品を Drive に入れます。普通の I2V / T2V ノートと同じ場所です。

- **初めて** … 20〜40分かかることがあります。途中で止まっても、もう一度押せば続きから入ります
- **2回目以降** … すでに入っているファイルは飛ばすので速いです
- 初めてなら「よく使う部品を全部入れる」は **オンのまま**（③でシーンを変えても困らない）
- 土台と速いモード（Turbo）は必ず入れます。えっち用ノートと普通ノートで共用します

**Civitai の API キー** は、えっち用の部品を取るときだけ。**普通（エロなし）だけなら空でOK。** 左の鍵（シークレット）は使わなくて大丈夫です。

1. [civitai.com のアカウント画面](https://civitai.com/user/account) を開く
2. **API Keys** → **Add API key** でキーを作ってコピー
3. ②の **CivitaiのAPIキー** 欄に貼って実行

401 / 403 が出たら、キーの貼り忘れです。欄に貼って②をもう一度。キー自体は画面に出ません。
"""

CELL2 = r'''#@title ② 土台と部品を入れる（初回は待つ）
print("② 準備を始めています…")

#@markdown ### Civitai の API キー（ここに貼る。シークレット不要）
#@markdown 取り方: [civitai.com/user/account](https://civitai.com/user/account) → API Keys → Add API key
CivitaiのAPIキー = ""  #@param {type:"string"}
#@markdown **よく使う部品を全部入れる（初めてならオンのまま）**
よく使う部品を全部入れる = True  #@param {type:"boolean"}
#@markdown 全部オフにするなら、今使うシーンだけ:
今使うシーン = "日常（速い＋綺麗）"  #@param ["日常（速い＋綺麗）", "最速プレビュー（エロなし）", "音も残す（エロなし）", "普通（エロなし）", "アナル挿入（画質）", "アナル舐め・指", "フェラ", "ふたなりフェラ", "汎用エロ", "試し打ち"]

import json, os, shutil, subprocess, sys, time, urllib.request
from pathlib import Path

env = {}
with open("/content/h3_paths.env") as f:
    for line in f:
        k, v = line.strip().split("=", 1)
        env[k] = v
DRIVE_ROOT = Path(env["DRIVE_ROOT"])
DRIVE_MODELS = Path(env["DRIVE_MODELS"])
COMFY_DIR = Path(env["COMFY_DIR"])
PORT = 8188
BRANCH = "cursor/minimax-h3-motion-identity-e959"
RAW = f"https://raw.githubusercontent.com/fireworker011/Research/{BRANCH}"
STUDIO = Path("/content/h3-lora-studio")

def sh(cmd, **kw):
    return subprocess.run(cmd, check=False, **kw)

def fetch_text(url: str, dest: Path) -> bool:
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        urllib.request.urlretrieve(url, dest)
        return dest.is_file() and dest.stat().st_size > 100
    except Exception:
        print("ファイル取得に失敗:", dest.name)
        return False

print("説明書を取っています…")
helpers = [
    "colab/h3_r2v_core.py",
    "colab/h3_motion_graphics.py",
    "colab/h3_i2v_phone.py",
    "colab/h3_t2v.py",
    "colab/h3_lora_studio.py",
]
studio_files = [
    "h3-lora-studio/catalog/loras.json",
    "h3-lora-studio/catalog/forbidden.json",
    "h3-lora-studio/scripts/select_loras.py",
    "h3-lora-studio/scripts/forbidden_words.py",
    "h3-lora-studio/profiles/anal_closeup.json",
    "h3-lora-studio/profiles/anal_penetration.json",
    "h3-lora-studio/profiles/futa_blowjob.json",
    "h3-lora-studio/profiles/oral.json",
    "h3-lora-studio/profiles/general_sex.json",
    "h3-lora-studio/profiles/preview.json",
    "h3-lora-studio/profiles/riding.json",
    "h3-lora-studio/profiles/sfw_daily.json",
    "h3-lora-studio/profiles/sfw_preview.json",
    "h3-lora-studio/profiles/sfw_audio.json",
    "h3-lora-studio/profiles/sfw_r2v.json",
]
for rel in helpers:
    dest = Path("/content") / Path(rel).name
    if not fetch_text(f"{RAW}/{rel}", dest):
        raise SystemExit("説明書の取得に失敗しました。ネットを確認して②をもう一度。")
    shutil.copy2(dest, DRIVE_ROOT / dest.name)
for rel in studio_files:
    dest = Path("/content") / rel
    if not fetch_text(f"{RAW}/{rel}", dest):
        raise SystemExit("シーン設定の取得に失敗しました。②をもう一度。")
drive_fb = DRIVE_ROOT / "forbidden.json"
git_fb = Path("/content/h3-lora-studio/catalog/forbidden.json")
if drive_fb.is_file() and drive_fb.stat().st_size > 20:
    shutil.copy2(drive_fb, git_fb)
    print("禁止語: Drive の forbidden.json を使います")
else:
    shutil.copy2(git_fb, drive_fb)
    print("禁止語の編集ファイル:", drive_fb)

sys.path.insert(0, "/content")
from h3_i2v_phone import i2v_download_jobs
from h3_lora_studio import (
    SITUATION_HELP, civitai_token, civitai_token_help, download_jobs_for,
    fetch_weight, load_catalog, missing_civitai_files, resolve_situation, situation_ids,
)

print("今のシーン:", 今使うシーン)
print(SITUATION_HELP[resolve_situation(今使うシーン)])
print()

if not (COMFY_DIR / "main.py").is_file():
    print("動画ソフトを入れています…")
    sh(["git", "clone", "--depth", "1", "https://github.com/Comfy-Org/ComfyUI.git", str(COMFY_DIR)])
else:
    sh(["git", "-C", str(COMFY_DIR), "pull", "--ff-only"])
req = COMFY_DIR / "requirements.txt"
if req.is_file():
    sh([sys.executable, "-m", "pip", "install", "-q", "-r", str(req)])

def link_dir(link_path: Path, target: Path):
    target.mkdir(parents=True, exist_ok=True)
    if link_path.is_symlink() or link_path.is_file():
        link_path.unlink()
    elif link_path.is_dir():
        shutil.rmtree(link_path)
    link_path.symlink_to(target)

models_root = COMFY_DIR / "models"
models_root.mkdir(parents=True, exist_ok=True)
for sub in ["diffusion_models", "text_encoders", "vae", "loras"]:
    link_dir(models_root / sub, DRIVE_MODELS / sub)
link_dir(COMFY_DIR / "output", DRIVE_ROOT / "output")
link_dir(COMFY_DIR / "input", DRIVE_ROOT / "input")

print("大きな土台を入れています（すでにあれば飛ばします）…")
for url, dest in i2v_download_jobs(DRIVE_MODELS):
    if "turbo" in dest.name.lower():
        print("  速いモード（Turbo）も入れます。普通の I2V / T2V と共用します:", dest.name)
    fetch_weight(url, dest)

sid = resolve_situation(今使うシーン)
ids = situation_ids(sid)
if よく使う部品を全部入れる:
    ids = []
    for key in ("sfw_daily", "sfw_preview", "sfw_audio", "anal_closeup", "anal_penetration", "futa_blowjob", "oral", "general_sex", "preview"):
        ids.extend(situation_ids(key))
    print("よく使う部品を全部入れます。③でシーンを変えても大丈夫です。")
else:
    print("今のシーン用だけ入れます:", 今使うシーン)

catalog = load_catalog(STUDIO)
# Civitai API をここで読む。名前は CIVITAI_API_TOKEN。値は print しない。
token = civitai_token(CivitaiのAPIキー)
print("Civitai API:", "読み込み済み（値は出しません）" if token else "空")
jobs = download_jobs_for(ids, DRIVE_MODELS / "loras", catalog=catalog)
need = missing_civitai_files(jobs)
if need and not token:
    raise SystemExit(civitai_token_help())
skipped = []
for url, dest, row in jobs:
    auth = "civitai" if str(row.get("source")) == "civitai" else ""
    if not fetch_weight(url, dest, token=token, auth=auth):
        skipped.append(dest.name)
if skipped:
    print("一部スキップ:", ", ".join(skipped))
    print("今のシーンに不要なら③へ。必要なら②をあとで再実行。")

os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")

def comfy_up() -> bool:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{PORT}/object_info", timeout=3) as r:
            obj = json.loads(r.read().decode())
        return "MiniMaxH3ImageToVideo" in obj
    except Exception:
        return False

if comfy_up():
    print("動画エンジンはすでに起動しています")
else:
    print("動画エンジンを起動しています…")
    log = Path("/content/comfyui.log")
    log_f = open(log, "w", buffering=1)
    cmd = [sys.executable, "main.py", "--listen", "127.0.0.1", "--port", str(PORT),
           "--highvram", "--disable-auto-launch", "--enable-cors-header"]
    subprocess.Popen(cmd, cwd=str(COMFY_DIR), stdout=log_f, stderr=subprocess.STDOUT, start_new_session=True)
    ok = False
    for _ in range(90):
        if comfy_up():
            ok = True
            break
        time.sleep(2)
    if not ok:
        print(log.read_text(errors="replace")[-2000:])
        raise SystemExit("起動に失敗しました。ランタイムを再起動して①からやり直してください。")
    print("起動できました")

print()
print("② 完了。次は③でシーンを選んで実行してください。")
'''

MD3 = r"""## ③ 動画を作る

**シーン** と **作り方** を選んで実行します。**プロンプトは任意**（空ならおすすめ文）。

| 作り方 | 必要なもの |
|---|---|
| テキストから（写真なし） | なし。縦動画（9:16） |
| 写真から（1枚必要） | Drive の `input` に jpg。顔や体を固定したいとき |

自分の文を書くときは、出演者は「21歳以上の成人」と書いてください。未成年の表現は拒否されます。写真からのときに Picture 1 を書かなくても、顔ロックは自動で足します。

**禁止語の編集:** Drive の `minimax-h3-comfyui/forbidden.json` の `extra`。③の「追加の禁止語」欄でもカンマで足せます。ロリ・ショタ・child などは消せません。

おすすめ文の例（空欄のときに自動で近い内容になります）:

- **日常（速い＋綺麗）** … Larry + シネマ。8step
- **最速プレビュー（エロなし）** … LightX2V 4step。当たりは日常で焼き直し
- **音も残す（エロなし）** … LightX2V 8step
- **普通（エロなし）** … 専用 I2V / T2V ノートと同じおすすめ文
- **アナル挿入（画質）** … 穴が見えるクローズ。Turbo なし
- **アナル舐め・指** … 舐め、それから指
- **フェラ / ふたなりフェラ** … 正面から竿。`bl0w_j0b` と `PENISLORA` は自動
- **汎用エロ / 試し打ち** … 挿入は曖昧でいい。試し打ちの当たりは本線で焼き直す
"""

CELL3 = r'''#@title ③ 動画を作る（ここだけ選ぶ）
#@markdown ### まずここ
やりたいシーン = "日常（速い＋綺麗）"  #@param ["日常（速い＋綺麗）", "最速プレビュー（エロなし）", "音も残す（エロなし）", "普通（エロなし）", "アナル挿入（画質）", "アナル舐め・指", "フェラ", "ふたなりフェラ", "汎用エロ", "試し打ち"]
作り方 = "テキストから（写真なし）"  #@param ["テキストから（写真なし）", "写真から（1枚必要）"]
#@markdown ### プロンプト（任意）
#@markdown 空ならシーンのおすすめ文。自分の文を貼ってよい。写真からで Picture 1 が無いときは自動で足します。
文章 = ""  #@param {type:"string"}
#@markdown ### 禁止語（任意）
#@markdown Drive の `minimax-h3-comfyui/forbidden.json` の extra を編集するか、ここにカンマで足す。未成年の語は消せません。
追加の禁止語 = ""  #@param {type:"string"}
#@markdown 写真からのときだけ。`auto` なら input フォルダの一番新しい jpg
写真ファイル = "auto"  #@param {type:"string"}
秒数 = 10  #@param {type:"number"}

#@markdown ---
#@markdown ### 触らなくていい（上級）
画面の向き = "おまかせ"  #@param ["おまかせ", "縦（スマホ）", "横", "やや正方形"]
リアル寄り = False  #@param {type:"boolean"}
胸を強調 = False  #@param {type:"boolean"}
動きの底上げ = False  #@param {type:"boolean"}
静止画用の写実 = False  #@param {type:"boolean"}
試し打ちだけ = False  #@param {type:"boolean"}

print("③ 設定を読みます…")

import json, os, sys, time, uuid, urllib.request, urllib.error
from pathlib import Path
from IPython.display import display, Video, HTML

sys.path.insert(0, "/content")
sys.path.insert(0, "/content/h3-lora-studio/scripts")
from h3_r2v_core import is_oom_error, frames
from h3_i2v_phone import (
    DEFAULT_FIRST_IMAGE, collect_output_videos, newest_mp4, newest_image,
    stage_image_into_input, is_auto_image_name, ref_image_url,
)
from h3_t2v import (
    CANVAS_9_16, assert_t2v_graph, build_t2v_graph, canvas_for_aspect,
    resolve_t2v_prompt, t2v_retry_plans, validate_t2v_prompt,
)
from h3_motion_graphics import (
    CANVAS_8_9, assert_i2va_graph, build_i2va_graph, i2va_retry_plans,
    prefer_fl2v_lora, resolve_motion_prompt, validate_motion_ad_prompt,
    validate_studio_i2v_prompt,
)
from h3_lora_studio import (
    apply_user_prompt, explain_choice, friendly_lora, friendly_select_error,
    inject_lora_stack, is_blank_prompt, is_vanilla, prepend_triggers,
    resolve_mode, resolve_situation,
)
from select_loras import select_loras
from forbidden_words import extra_terms, parse_extra_terms

env = {}
with open("/content/h3_paths.env") as f:
    for line in f:
        k, v = line.strip().split("=", 1)
        env[k] = v
COMFY_DIR = Path(env["COMFY_DIR"])
DRIVE_ROOT = Path(env["DRIVE_ROOT"])
OUT = COMFY_DIR / "output"
PORT = 8188
STUDIO = Path("/content/h3-lora-studio")
SEED = 42

SITUATION = resolve_situation(やりたいシーン)
MODE = resolve_mode(作り方)
VANILLA = is_vanilla(やりたいシーン)
print()
print(explain_choice(やりたいシーン, 作り方))
print()
print("禁止語の編集:", DRIVE_ROOT / "forbidden.json")
print("追加の禁止語:", ", ".join(extra_terms()) or "（json の extra は空）")
EXTRA_FORBIDDEN = parse_extra_terms(追加の禁止語)
if EXTRA_FORBIDDEN:
    print("③で足した禁止語:", ", ".join(EXTRA_FORBIDDEN))
print()

CUSTOM_PROMPT = not is_blank_prompt(文章)

if VANILLA:
    stack = []
    STEPS = 4
    FILENAME_PREFIX = "video/h3_t2v_phone" if MODE == "t2v" else "video/h3_i2va_phone"
    if MODE == "t2v":
        w, h = CANVAS_9_16
        prompt, CUSTOM_PROMPT = apply_user_prompt(文章, mode="t2v", default_prompt=resolve_t2v_prompt("", landscape=False))
        errs = validate_t2v_prompt(prompt)
        if errs:
            raise SystemExit(errs)
    else:
        w, h = CANVAS_8_9
        default_i2v = resolve_motion_prompt("", duration_s=float(秒数), with_last_frame=False)
        prompt, CUSTOM_PROMPT = apply_user_prompt(文章, mode="i2v", default_prompt=default_i2v)
        if CUSTOM_PROMPT:
            errs = validate_studio_i2v_prompt(prompt, extra=EXTRA_FORBIDDEN)
        else:
            errs = validate_motion_ad_prompt(prompt, with_last_frame=False)
        if errs:
            raise SystemExit(errs)
    print("入る部品: 速いモード（Turbo）だけ。えっち用は使いません。")
    print("文章:", "自分のプロンプト" if CUSTOM_PROMPT else "おすすめ文（空欄）")
    SAMPLER = {"sampler_name": "euler", "scheduler": "simple", "steps": 4}
    cfg = None
else:
    FILENAME_PREFIX = "video/h3_preview" if SITUATION in {"preview", "sfw_preview"} else "video/h3_lora_studio"
    prompt_arg, CUSTOM_PROMPT = apply_user_prompt(文章, mode=MODE, default_prompt="（シーン）")
    print("文章:", "自分のプロンプト" if CUSTOM_PROMPT else "シーンのおすすめ文（空欄）")
    if CUSTOM_PROMPT:
        print("文章欄（先頭）:", prompt_arg[:180].replace("\n", " "))
    if MODE == "t2v" and ("Picture 1" in prompt_arg or "first_frame" in prompt_arg.lower()):
        raise SystemExit("テキストから作るときは、写真用の文が文章欄に残っています。欄を空にするとこのシーンのおすすめ文になります。")
    try:
        cfg = select_loras(
            profile_name=SITUATION,
            mode=MODE,
            prompt_arg=prompt_arg,
            catalog_path=STUDIO / "catalog" / "loras.json",
            profiles_dir=STUDIO / "profiles",
            turbo_override=None,
            extra_forbidden=EXTRA_FORBIDDEN,
            forbidden_path=STUDIO / "catalog" / "forbidden.json",
        )
    except SystemExit as exc:
        hint = friendly_select_error(exc)
        raise SystemExit(hint or str(exc)) from None
    if 動きの底上げ or 胸を強調 or リアル寄り or 静止画用の写実:
        print("上級の追加部品は重ね上限（行為1+ヘルパー1+Turbo1）のため無視します。")
    stack = cfg["stack"]
    prompt = prepend_triggers(cfg["prompt"], stack)
    SAMPLER = cfg["sampler"]
    STEPS = int(SAMPLER["steps"])
    if MODE == "t2v" and ("Picture 1" in prompt or "first_frame" in prompt.lower()):
        raise SystemExit("テキストから作るときは、写真ロックの文を入れません。文章欄を空にするか、Picture 1 を消してください。")
    print("入る部品:")
    for x in stack:
        role = x.get("role") or ""
        print(" -", friendly_lora(x["id"]), "強さ", x.get("strength_model"), role)
    w, h = int(cfg["canvas"]["width"]), int(cfg["canvas"]["height"])
    if MODE == "i2v":
        errs = validate_studio_i2v_prompt(prompt, extra=EXTRA_FORBIDDEN)
        if errs:
            raise SystemExit(errs)

if MODE == "t2v" and ("Picture 1" in prompt or "first_frame" in prompt.lower()):
    raise SystemExit("テキストから作るときは、写真ロックの文を入れません。文章欄を空にするか、Picture 1 を消してください。")

print()
print("使う文章（先頭）:")
print(prompt[:450])
print("…")
print()

if 画面の向き == "縦（スマホ）":
    w, h = canvas_for_aspect("9:16")
elif 画面の向き == "横":
    w, h = canvas_for_aspect("16:9")
elif 画面の向き == "やや正方形":
    w, h = CANVAS_8_9
print("画面サイズ:", w, "x", h, " / 秒数:", 秒数, " / ステップ:", STEPS, SAMPLER.get("sampler_name"), SAMPLER.get("scheduler"))
if VANILLA and MODE == "t2v":
    prompt = resolve_t2v_prompt(文章, landscape=w > h)
    errs = validate_t2v_prompt(prompt)
    if errs:
        raise SystemExit(errs)

obj = {}
if not 試し打ちだけ:
    with urllib.request.urlopen(f"http://127.0.0.1:{PORT}/object_info", timeout=60) as r:
        obj = json.loads(r.read().decode())
    if "MiniMaxH3ImageToVideo" not in obj:
        raise SystemExit("エンジンがまだです。②を先に実行してください。")

diff = list((COMFY_DIR / "models/diffusion_models").glob("*fl2va*"))
if not diff and not 試し打ちだけ:
    raise SystemExit("土台がありません。②を先に実行してください。")
unet = diff[0].name if diff else "minimax_h3_fl2va_pruned_int8_convrot.safetensors"

first_name = None
if MODE == "i2v":
    inp = COMFY_DIR / "input"
    inp.mkdir(parents=True, exist_ok=True)
    if is_auto_image_name(写真ファイル):
        hit = newest_image([DRIVE_ROOT / "input", inp])
        if hit is None and VANILLA:
            dest = inp / DEFAULT_FIRST_IMAGE
            print("参考画像を取得します")
            urllib.request.urlretrieve(ref_image_url(), dest)
            if dest.is_file() and dest.stat().st_size > 1000:
                hit = dest
        if hit is None:
            raise SystemExit("写真が見つかりません。スマホの Drive で「minimax-h3-comfyui/input」に jpg を置いてから、もう一度③を実行してください。")
        first_name = stage_image_into_input(hit, inp)
    else:
        src = Path(写真ファイル)
        if not src.is_file():
            src = DRIVE_ROOT / "input" / 写真ファイル
        if not src.is_file():
            raise SystemExit("その写真ファイルがありません: " + 写真ファイル)
        first_name = stage_image_into_input(src, inp)
    print("使う写真:", first_name)

lora_name = None
lora_strength = 0.0
if VANILLA:
    lora_paths = list((COMFY_DIR / "models" / "loras").glob("*.safetensors"))
    lora_name = prefer_fl2v_lora(lora_paths, True)
    lora_strength = 1.0
    if not lora_name:
        raise SystemExit("速いモード（Turbo）がありません。②を先に実行してください。")

plans = t2v_retry_plans(width=w, height=h) if MODE == "t2v" else i2va_retry_plans(width=w, height=h)

def make_graph(plan):
    steps = int(SAMPLER["steps"])
    if MODE == "t2v":
        g = build_t2v_graph(
            prompt=prompt, unet=unet, lora_name=lora_name, lora_strength=lora_strength,
            width=int(plan["width"]), height=int(plan["height"]),
            duration_s=float(秒数), seed=int(SEED), steps=steps,
            filename_prefix=FILENAME_PREFIX,
            has_lora_loader=("LoraLoaderModelOnly" in obj) or 試し打ちだけ,
            has_audio_decode=("VAEDecodeAudio" in obj) or 試し打ちだけ,
        )
        if not VANILLA:
            inject_lora_stack(g, stack, sampler=SAMPLER)
        errs = assert_t2v_graph(g)
    else:
        g = build_i2va_graph(
            first_image=first_name, last_image=None, prompt=prompt, unet=unet,
            lora_name=lora_name, lora_strength=lora_strength,
            width=int(plan["width"]), height=int(plan["height"]),
            duration_s=float(秒数), seed=int(SEED), steps=steps,
            filename_prefix=FILENAME_PREFIX,
            has_lora_loader=("LoraLoaderModelOnly" in obj) or 試し打ちだけ,
            has_audio_decode=("VAEDecodeAudio" in obj) or 試し打ちだけ,
        )
        if not VANILLA:
            inject_lora_stack(g, stack, sampler=SAMPLER)
        homage = bool(VANILLA and not CUSTOM_PROMPT)
        errs = assert_i2va_graph(g, expect_last=False, homage=homage)
    if errs:
        raise SystemExit(errs)
    loaders = [n for n in g.values() if n.get("class_type") == "LoraLoaderModelOnly"]
    names = [str(n["inputs"].get("lora_name", "")) for n in loaders]
    blob = " ".join(names).lower()
    has_larry = "turbo_v4" in blob or "larry" in blob
    has_lx = "fl2v_turbo" in blob or "fl2v_lightx2v" in blob or "lightx2v" in blob
    if has_larry and has_lx:
        raise SystemExit("Larry と LightX2V は同時に積みません。")
    if VANILLA:
        if not names or all("turbo" not in n.lower() for n in names):
            raise SystemExit("普通（エロなし）なのに速いモードが入っていません。②からやり直してください。")
        if any("turbo" not in n.lower() for n in names):
            raise SystemExit("普通（エロなし）にえっち用の部品が混ざったので止めています。")
    elif cfg and cfg.get("turbo"):
        if not (has_larry or has_lx):
            raise SystemExit("このシーンは薄い Turbo が必要です。②からやり直してください。")
    elif has_larry or has_lx:
        raise SystemExit("アナル挿入の本線に Turbo は入れません。")
    return g

def post_prompt(g):
    body = {"prompt": g, "client_id": str(uuid.uuid4())}
    req = urllib.request.Request(
        f"http://127.0.0.1:{PORT}/prompt",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read().decode()), None
    except urllib.error.HTTPError as e:
        return None, e.read().decode(errors="replace")[:2000]

def wait_prompt(pid):
    for _ in range(360):
        with urllib.request.urlopen(f"http://127.0.0.1:{PORT}/history/{pid}", timeout=60) as r:
            hist = json.loads(r.read().decode())
        entry = hist.get(pid)
        if entry:
            st = entry.get("status") or {}
            if st.get("completed") or entry.get("outputs"):
                if st.get("status_str") == "error":
                    return False, entry
                return True, entry
        time.sleep(2)
    return False, "timeout"

if 試し打ちだけ:
    g = make_graph(plans[0])
    print("試し打ちOK。部品:", [n["inputs"]["lora_name"] for n in g.values() if n.get("class_type") == "LoraLoaderModelOnly"])
    print("実際の動画は「試し打ちだけ」をオフにして③をもう一度。")
else:
    print()
    print("作り始めています。数分〜十数分かかることがあります…")
    last_err = None
    ok_entry = None
    before = newest_mp4(OUT)
    for plan in plans:
        print("サイズを試しています:", plan.get("label") or plan)
        g = make_graph(plan)
        res, err = post_prompt(g)
        if err:
            last_err = err
            if is_oom_error(err):
                print("メモリが足りなかったので、小さい画面でやり直します。")
                continue
            raise SystemExit("失敗しました。②からやり直すか、シーンを変えてみてください。")
        ok, payload = wait_prompt(res["prompt_id"])
        if ok:
            ok_entry = payload
            break
        last_err = payload
        if is_oom_error(str(payload)):
            print("メモリが足りなかったので、小さい画面でやり直します。")
            continue
        raise SystemExit("失敗しました。写真から作るなら input の jpg を確認してください。")
    else:
        raise SystemExit("メモリ不足で作れませんでした。秒数を 5 にするか、A100 のまま②からやり直してください。")
    videos = collect_output_videos(ok_entry, OUT)
    fresh = newest_mp4(OUT)
    if fresh and fresh not in videos and (before is None or fresh != before):
        videos.append(fresh)
    if not videos:
        print("ファイル名が取れませんでした。Drive の output フォルダを見てください:", OUT)
    else:
        print()
        print("できました。下に再生、Drive にも保存しています。")
        for p in videos:
            print("保存:", p)
            if p.is_file():
                display(HTML(f"<p style='font-size:16px'>保存先: <code>{p}</code></p>"))
                display(Video(str(p), embed=True, width=360))
print()
print("③ 完了。キーは画面に出していません。")
'''


def to_source(text: str) -> list[str]:
    return [line + "\n" for line in text.strip("\n").split("\n")]


for _name, _src in (("CELL1", CELL1), ("CELL2", CELL2), ("CELL3", CELL3)):
    compile(_src, _name, "exec")


nb = {
    "nbformat": 4,
    "nbformat_minor": 5,
    "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python"},
        "accelerator": "GPU",
        "colab": {"provenance": [], "gpuType": "A100"},
    },
    "cells": [
        {"cell_type": "markdown", "metadata": {}, "source": to_source(MD0)},
        {"cell_type": "markdown", "metadata": {}, "source": to_source(MD1)},
        {"cell_type": "code", "metadata": {"id": "ls1_drive"}, "execution_count": None, "outputs": [], "source": to_source(CELL1)},
        {"cell_type": "markdown", "metadata": {}, "source": to_source(MD2)},
        {"cell_type": "code", "metadata": {"id": "ls2_setup"}, "execution_count": None, "outputs": [], "source": to_source(CELL2)},
        {"cell_type": "markdown", "metadata": {}, "source": to_source(MD3)},
        {"cell_type": "code", "metadata": {"id": "ls3_gen"}, "execution_count": None, "outputs": [], "source": to_source(CELL3)},
    ],
}
blob = json.dumps(nb, ensure_ascii=False, indent=1)
for out in OUTS:
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(blob, encoding="utf-8")
    print("wrote", out, "bytes", out.stat().st_size)
