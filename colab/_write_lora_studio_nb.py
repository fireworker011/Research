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
| 帰宅120秒（専用） | 玄関フェラ→トイレクンニ寄り→口内。10×12のカット | クンニ LoRA は寄り1本。入室・退出は歩行部品。576×1024 |
| 洗い物120秒（専用） | シンク洗い物＋プリン。アヤが床で口。10×12のカット | サヤカはシンク固定。レイは椅子で竿。入室と着席は別本。フェラは60秒以降。口内は CUMOUF |
| 登校120秒（専用） | 朝〜大学正門。10秒×12本。16:9 | 1本1場所。セリフは口元3本。フェラは玄関と路地の寄り。授業は授業120秒 |
| 授業120秒（専用） | 授業〜昼。10秒×10本＝100秒。16:9 | 家とサヤカなし。机のシコはオナニー寄り。クンニは寄り1本。口内は CUMOUF。セリフは「昼だよ」だけ。セックスは屋上〜下校 |
| 屋上〜下校（専用） | 屋上挿入〜家の門。10秒×10本。16:9 | 1本1場所。セリフは口元2本。セックスは横クローズ。玄関はおかえり |
| おかえり120秒（専用） | 家の門〜玄関ジュボ〜廊下。10秒×12本。16:9 | 屋上の続き。セリフは口元3本。フェラは玄関の寄り。口内は CUMOUF。食卓は洗い物 |
| アナル挿入（画質） | 穴のアップで挿入。遅いが綺麗 | ThumbInButt 0.85 + 竿 0.7 + 穴の見え方 0.55 / 16step。Turbo なし |
| アナル舐め・指 | 舐め・指のアップ。動きの本線はアナル指入れ | 穴の見え方 0.7 + Larry 0.5 + シネマ 0.4 |
| アナル指入れ | 自分の親指をアナルへ。指入れ（膣）とは別 | ThumbInButt 0.85 + 穴の見え方 0.55 + Larry 0.5 / 8step。写真からが本線 |
| フェラ（女体） | 女がふたなりにフェラ。男なし | フェラ 0.75 + 竿 0.7 + Larry 0.7 |
| ふたなりフェラ | ふたなりがフェラされる。男なし | フェラ 0.75 + 竿 0.7 + 穴の見え方 0.55 + Larry 0.5 / 6step |
| セックス（女体） | ふたなり＋女。男なし。描写は文章欄 | 総合えっち 0.8 + 竿 0.7 + 穴の見え方 0.55 / 12step |
| アナルセックス（女体） | アナル本線。後ろから、穴が膣より上に見える構図 | ThumbInButt 0.85 + 竿 0.7 + 穴の見え方 0.55 / 12step。Turbo なし。写真からが本線 |
| 騎乗位（女体） | 騎乗。総合えっちは積まない | 騎乗 0.8 + 竿 0.7 + 穴の見え方 0.55 / 12step。Turbo なし |
| 後背位（女体） | 後ろから前後の突き | 後背位 0.8 + 竿 0.7 + 穴の見え方 0.55 / 12step。Turbo なし |
| 正常位POV（女体） | 挿入側の視点。横からの正常位はセックス（女体） | POV挿入 0.85 + 竿 0.7 + Larry 0.5 / 8step |
| 後射精（女体） | 外に出す射精。中出し・顔射とは別 | 射精 0.9 + 竿 0.7 + Larry 0.5 / 8step |
| 顔射（女体） | 顔にかける。後射精・口内とは別 | 顔射 0.8 + 竿 0.7 + Larry 0.5 / 8step。写真からが本線 |
| 中出し（女体） | 膣の中に出す。後射精・顔射とは別 | Final Thrust 0.85 + 竿 0.7 + 穴の見え方 0.55 / 12step。Turbo なし。写真からが本線 |
| 口内射精（女体） | 口の中で出す。顔射・フェラ本線とは別 | CUMOUF 0.5 + 竿 0.7 + Larry 0.5 / 8step。写真からが本線 |
| 指入れ | 膣への指の出し入れ。オナニー LoRA は積まない。アナルはアナル指入れ | 指 0.85 + 穴の見え方 0.55 + Larry 0.5 / 8step |
| オナニー | 潮吹き。指入れ LoRA は積まない | オナニー 0.8 + 穴の見え方 0.55 + Larry 0.5 / 12step |
| 足コキ | 両足で竿 | Type D 0.85 + 竿 0.7 + Larry 0.5 / 8step |
| 絶頂 | 女体の絶頂反応。射精ではない | 絶頂 0.8 + 穴の見え方 0.55 + Larry 0.5 / 8step |
| 汎用エロ（女体） | ふたなり＋女。男なし | AIO 0.8 + Larry 0.5 / 12step |
| 試し打ち | エロの量産プレビュー | AIO 0.7 + LightX2V 4step。当たりは本線で焼き直し |
| レズビアンクンニ | 全裸の出会い→キス→クンニ | クンニ 0.8 + 穴の見え方 0.55 + Larry 0.5 |
| 性器を広げる | 広げて見せるクローズ | 広げる 0.75 + 穴の見え方 0.55 + Larry 0.5 |
| レズ＋広げる | クンニに広げるを足す | クンニ 0.8 + 広げる 0.6 + Larry 0.5。穴の見え方は外す |

**速さ:** 本線は Larry 8step。試し打ち・最速プレビューだけ LightX2V 4step。秒数は 4〜15（1本）。20〜120秒は「つなぐ」（10秒ずつ。1本で伸ばさない）。20秒は 10×2、90秒は 10×9、120秒は 10×12。2〜12本目の文は③のつなぎ欄。空なら前の続き。
**エロなしの重ね:** Turbo1 + 画質1。速さ用と画質用を分ける。Larry と LightX2V は同時に積まない。
**エロの重ね:** 行為1 + ヘルパー0〜2 + Turbo0〜1。体位 LoRA は総合えっちの代わり（同時に積まない）。シネマを足すならヘルパーを落とす。挿入ショットに Turbo は切る。Fal には載せない。
**エロの空欄:** 全員 21歳以上の全裸のごく普通の若い成人女性（女かふたなり）。男は出さない。行為の細かい描写は③の文章欄で足す。
**アナル系（ThumbInButt）のコツ:** 専用のアナルセックス LoRA は無いので、「物をアナルに入れる」を覚えた ThumbInButt を竿と組む。**穴が膣より上に見える構図**（四つん這い・後ろから）でないと膣に入る。挿入側の手は腰に置く（親指に置き換わるのを防ぐ）。写真からが本線。写真は後ろから穴が見えるもの。文章欄に書くなら「(S2) inserts her penis in (S1)'s anus」の形で、男・his は書かない。

**プロンプトは任意。** 空ならシーンのおすすめ文。自分の文を③の欄に貼ってもよい。写真からのときは顔ロック（Picture 1）を自動で足します。禁止語は Drive の `forbidden.json` だけ。未成年ロックは外せません。

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
- **同じランタイムで2回目** … Drive にあるファイルは飛ばす。pip も飛ばす。エンジンが生きていればすぐ終わる
- **ランタイム切断後** … Drive の土台は飛ばす（40GB の再取得はしない）。Comfy の入れ直しと起動で数分
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
今使うシーン = "日常（速い＋綺麗）"  #@param ["日常（速い＋綺麗）", "最速プレビュー（エロなし）", "音も残す（エロなし）", "普通（エロなし）", "帰宅120秒（専用）", "洗い物120秒（専用）", "登校120秒（専用）", "授業120秒（専用）", "屋上〜下校（専用）", "おかえり120秒（専用）", "アナル挿入（画質）", "アナル舐め・指", "アナル指入れ", "フェラ（女体）", "ふたなりフェラ", "セックス（女体）", "アナルセックス（女体）", "騎乗位（女体）", "後背位（女体）", "正常位POV（女体）", "後射精（女体）", "顔射（女体）", "中出し（女体）", "口内射精（女体）", "指入れ", "オナニー", "足コキ", "絶頂", "汎用エロ（女体）", "試し打ち", "レズビアンクンニ", "性器を広げる", "レズ＋広げる"]

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
FETCH_REV = "h2-20260906-okaeri"
RAW = f"https://raw.githubusercontent.com/fireworker011/Research/{BRANCH}"
STUDIO = Path("/content/h3-lora-studio")

def sh(cmd, **kw):
    return subprocess.run(cmd, check=False, **kw)

def fetch_text(url: str, dest: Path) -> bool:
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(
        f"{url}?rev={FETCH_REV}",
        headers={"Cache-Control": "no-cache", "Pragma": "no-cache"},
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            dest.write_bytes(resp.read())
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
    "h3-lora-studio/profiles/anal_closeup.json",
    "h3-lora-studio/profiles/anal_fingering.json",
    "h3-lora-studio/profiles/anal_penetration.json",
    "h3-lora-studio/profiles/futa_blowjob.json",
    "h3-lora-studio/profiles/futa_sex.json",
    "h3-lora-studio/profiles/futa_anal.json",
    "h3-lora-studio/profiles/oral.json",
    "h3-lora-studio/profiles/general_sex.json",
    "h3-lora-studio/profiles/lesbian_cunnilingus.json",
    "h3-lora-studio/profiles/lesbian_spread.json",
    "h3-lora-studio/profiles/pussy_spread.json",
    "h3-lora-studio/profiles/preview.json",
    "h3-lora-studio/profiles/riding.json",
    "h3-lora-studio/profiles/doggy.json",
    "h3-lora-studio/profiles/missionary_pov.json",
    "h3-lora-studio/profiles/after_ejaculation.json",
    "h3-lora-studio/profiles/facial.json",
    "h3-lora-studio/profiles/creampie.json",
    "h3-lora-studio/profiles/oral_creampie.json",
    "h3-lora-studio/profiles/fingering.json",
    "h3-lora-studio/profiles/masturbation.json",
    "h3-lora-studio/profiles/footjob.json",
    "h3-lora-studio/profiles/remote_orgasm.json",
    "h3-lora-studio/profiles/sfw_daily.json",
    "h3-lora-studio/profiles/sfw_preview.json",
    "h3-lora-studio/profiles/sfw_audio.json",
    "h3-lora-studio/profiles/sfw_r2v.json",
    "h3-lora-studio/profiles/futa_visible.json",
    "h3-lora-studio/profiles/futa_masturbation.json",
    "h3-lora-studio/profiles/cunnilingus_futa.json",
    "h3-lora-studio/stories/homecoming-90s.json",
    "h3-lora-studio/stories/dishes-90s.json",
    "h3-lora-studio/stories/commute-120s.json",
    "h3-lora-studio/stories/lecture-120s.json",
    "h3-lora-studio/stories/rooftop-100s.json",
    "h3-lora-studio/stories/okaeri-120s.json",
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
if not (drive_fb.is_file() and drive_fb.stat().st_size > 20):
    shutil.copy2(git_fb, drive_fb)
    print("禁止語ファイルを作りました:", drive_fb)
else:
    print("禁止語ファイル:", drive_fb)
shutil.copy2(drive_fb, git_fb)
try:
    fb = json.loads(drive_fb.read_text(encoding="utf-8"))
    extra_now = [str(x).strip() for x in (fb.get("extra") or []) if str(x).strip()]
    print("extra:", ", ".join(extra_now) or "（空）")
    print("足す・消すのは extra だけ。minors を消しても未成年ロックは残ります。")
except Exception:
    raise SystemExit("禁止語ファイルが壊れています。Drive の forbidden.json を直してください。")

sel = Path("/content/h3-lora-studio/scripts/select_loras.py")
if "MAX_HELPERS" not in sel.read_text(encoding="utf-8"):
    raise SystemExit("設定の取り直しに失敗しました。②をもう一度実行してください。")
print("設定の版:", FETCH_REV)

sys.path.insert(0, "/content")
sys.path.insert(0, "/content/h3-lora-studio/scripts")
for name in ("select_loras", "h3_lora_studio", "h3_i2v_phone", "h3_t2v", "h3_r2v_core", "h3_motion_graphics"):
    sys.modules.pop(name, None)
from h3_i2v_phone import i2v_download_jobs
from h3_lora_studio import (
    SITUATION_HELP, civitai_token, civitai_token_help, civitai_download_fallbacks,
    download_jobs_for, fetch_weight, load_catalog, missing_civitai_files,
    resolve_situation, situation_ids, comfy_alive, wait_comfy_ready,
)

print("今のシーン:", 今使うシーン)
print(SITUATION_HELP[resolve_situation(今使うシーン)])
print()

if not (COMFY_DIR / "main.py").is_file():
    print("動画ソフトを入れています…")
    sh(["git", "clone", "--depth", "1", "https://github.com/Comfy-Org/ComfyUI.git", str(COMFY_DIR)])
else:
    print("動画ソフトはすでにあります。更新はしません。")
req = COMFY_DIR / "requirements.txt"
pip_stamp = Path("/content/.h3_pip_ok")
if pip_stamp.is_file():
    print("Python 部品は前回入れ済み。飛ばします。")
elif req.is_file():
    print("Python 部品を入れています（このランタイムの初回だけ）…")
    sh([sys.executable, "-m", "pip", "install", "-q", "-r", str(req)])
    pip_stamp.write_text("ok", encoding="utf-8")

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
    for key in ("sfw_daily", "sfw_preview", "sfw_audio", "anal_closeup", "anal_fingering", "anal_penetration", "futa_blowjob", "futa_sex", "futa_anal", "oral", "general_sex", "preview", "lesbian_cunnilingus", "pussy_spread", "lesbian_spread", "riding", "doggy", "missionary_pov", "after_ejaculation", "facial", "creampie", "oral_creampie", "fingering", "masturbation", "footjob", "remote_orgasm", "futa_visible", "futa_masturbation", "cunnilingus_futa", "homecoming-90s", "dishes-90s", "commute-120s", "lecture-120s", "rooftop-100s", "okaeri-120s"):
        ids.extend(situation_ids(key))
    print("よく使う部品を全部入れます。③でシーンを変えても大丈夫です。")
else:
    print("今のシーン用だけ入れます:", 今使うシーン)

catalog = load_catalog(STUDIO)
# Civitai API をここで読む。名前は CIVITAI_API_TOKEN。値は print しない。
token = civitai_token(CivitaiのAPIキー)
if token:
    os.environ["CIVITAI_API_TOKEN"] = token
print("Civitai API:", "読み込み済み（値は出しません）" if token else "空")
jobs = download_jobs_for(ids, DRIVE_MODELS / "loras", catalog=catalog)
need = missing_civitai_files(jobs)
if need and not token:
    raise SystemExit(civitai_token_help())
skipped = []
for url, dest, row in jobs:
    auth = "civitai" if str(row.get("source")) == "civitai" else ""
    fallbacks = civitai_download_fallbacks(row) if auth else None
    if not fetch_weight(url, dest, token=token, auth=auth, fallback_urls=fallbacks):
        skipped.append(dest.name)
        if dest.name == "H3_anal_penetration_v1.safetensors":
            print("アナル挿入の専用部品は Civitai 有料のことがあります。③では総合えっちで代用します。Drive の models/loras に置けば専用になります。")
if skipped:
    print("一部スキップ:", ", ".join(skipped))
    print("今のシーンに不要なら③へ。必要なら Drive の models/loras に置いてください。②をもう一度回すだけでは取れないことがあります。")

os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")

if comfy_alive(PORT):
    print("動画エンジンはすでに起動しています。部品の準備を待ちます…")
    if not wait_comfy_ready(PORT, seconds=180):
        raise SystemExit("エンジンの準備が終わりません。ランタイムを再起動して①からやり直してください。")
else:
    print("動画エンジンを起動しています…")
    log = Path("/content/comfyui.log")
    log_f = open(log, "w", buffering=1)
    cmd = [sys.executable, "main.py", "--listen", "127.0.0.1", "--port", str(PORT),
           "--highvram", "--disable-auto-launch", "--enable-cors-header"]
    subprocess.Popen(cmd, cwd=str(COMFY_DIR), stdout=log_f, stderr=subprocess.STDOUT, start_new_session=True)
    if not wait_comfy_ready(PORT, seconds=180):
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

**禁止語:** Drive の `minimax-h3-comfyui/forbidden.json` だけ。`extra` を足す・消す。③に欄は無い。編集したら③を再実行。ロリ・ショタ・child・21歳未満・アフィURLは消せません。

おすすめ文の例（空欄のときに自動で近い内容になります）:

- **日常（速い＋綺麗）** … Larry + シネマ。8step
- **最速プレビュー（エロなし）** … LightX2V 4step。当たりは日常で焼き直し
- **音も残す（エロなし）** … LightX2V 8step
- **普通（エロなし）** … 専用 I2V / T2V ノートと同じおすすめ文
- **帰宅120秒（専用）** … 10秒×12本。1本1場所。セリフは口元の1本だけ（リップシンク）。クンニ LoRA は寄り1本。行為は口元・舌・竿の寄り。写真は `input/homecoming-90s/` の 01〜12（`11-lick.jpg` は舌と穴の寄り）
- **洗い物120秒（専用）** … 10秒×12本。1本1場所。サヤカはシンク固定。セリフは口元の2本だけ。フェラは口元の寄り。口内は CUMOUF。写真は `input/dishes-90s/` の 01〜12（任意。01〜09は従来のまま）
- **登校120秒（専用）** … 第1話。朝〜大学正門。10秒×12本＝120秒。16:9。1本1場所。セリフは口元3本（行ってらっしゃい／遅刻するよ／ほしい）。フェラは玄関と路地の寄り。授業は授業120秒。写真は `input/commute-120s/` の 01〜12（16:9。無い本はテキストから）
- **授業120秒（専用）** … 第2話。授業〜昼。10秒×10本＝100秒。16:9。家とサヤカは出さない。机のシコはオナニー寄り。クンニ LoRA は寄り1本。根元はフェラ。口内は CUMOUF。セリフは口元の「昼だよ」だけ。セックスは屋上〜下校。写真は `input/lecture-120s/` の 01〜10（16:9。無い本はテキストから）
- **屋上〜下校（専用）** … 第3話。屋上で挿入（もう入っている）〜家の門。10秒×10本＝100秒。16:9。1本1場所。セリフは口元2本（ほしい／帰ろ）。セックスは AIO 横クローズ。歩く本にセックス部品なし。玄関はおかえり120秒。サヤカなし。写真は `input/rooftop-100s/` の 01〜10（16:9）。全話同じ追従ルール（10秒・1場所・口パクは顔寄り・行為は LoRA のカメラ）
- **おかえり120秒（専用）** … 第4話。家の門〜玄関ジュボ〜廊下。10秒×12本＝120秒。16:9。屋上の続き。セリフは口元3本（ただいま／おかえり／手洗って）。フェラは玄関の寄り。口内は CUMOUF。食卓のプリンは洗い物。写真は `input/okaeri-120s/` の 01〜12（16:9。無い本はテキストから）
- **アナル挿入（画質）** … 穴のアップ。挿入側はふたなり。男なし。Turbo なし・16step
- **アナルセックス（女体）** … ふたなり＋女。男なし。Turbo なし・12step。後ろから、穴が膣より上。手は腰。写真からが本線
- **アナル舐め・指** … 女同士。男なし。動きの本線はアナル指入れ
- **アナル指入れ** … 女1人。自分の右親指。男なし。後ろから、穴が膣より上。指入れ（膣）・アナルセックスとは別。写真からが本線
- **フェラ（女体）** … 女がふたなりにフェラ。男なし。`bl0w_j0b` と `PENISLORA` は自動
- **ふたなりフェラ** … ふたなりがフェラされる。男なし
- **セックス（女体）** … ふたなり＋女。男なし。空欄は全裸のごく普通の若い成人女性。描写は文章欄
- **騎乗位（女体）** … ふたなり＋女。男なし。総合えっちは積まない
- **後背位（女体）** … ふたなり＋女。男なし
- **正常位POV（女体）** … ふたなり＋女。男なし
- **後射精（女体）** … ふたなり。男なし。絶頂・顔射・中出しとは別
- **顔射（女体）** … ふたなり＋女。男なし。後射精・絶頂・口内とは別。写真からが本線
- **中出し（女体）** … ふたなり＋女。男なし。膣の中。後射精・顔射・口内とは別。写真からが本線
- **口内射精（女体）** … ふたなり＋女。男なし。口の中。顔射・フェラ本線とは別。写真からが本線（口が付いた途中の写真）
- **指入れ** … 女1人。男なし。膣。アナルはアナル指入れ
- **オナニー** … 女1人。男なし
- **足コキ** … ふたなり＋女。男なし
- **絶頂** … 女1人。男なし。射精ではない
- **汎用エロ（女体）** … ふたなり＋女。男なし。AIO + Larry 12step
- **試し打ち** … ふたなり＋女。男なし
- **秒数** … 4〜15 は1本。20〜120秒は「つなぐ 20秒」〜「つなぐ 120秒」（10秒ずつ）。120秒は 10×12。2〜12本目の文は③のつなぎ欄。空なら前の続き。1本で 16 秒以上は作らない
- **レズビアンクンニ** … 女同士。男なし
- **性器を広げる** … 女1人。男なし
- **レズ＋広げる** … 女同士。男なし
"""

CELL3 = r'''#@title ③ 動画を作る（ここだけ選ぶ）
#@markdown ### まずここ
やりたいシーン = "日常（速い＋綺麗）"  #@param ["日常（速い＋綺麗）", "最速プレビュー（エロなし）", "音も残す（エロなし）", "普通（エロなし）", "帰宅120秒（専用）", "洗い物120秒（専用）", "登校120秒（専用）", "授業120秒（専用）", "屋上〜下校（専用）", "おかえり120秒（専用）", "アナル挿入（画質）", "アナル舐め・指", "アナル指入れ", "フェラ（女体）", "ふたなりフェラ", "セックス（女体）", "アナルセックス（女体）", "騎乗位（女体）", "後背位（女体）", "正常位POV（女体）", "後射精（女体）", "顔射（女体）", "中出し（女体）", "口内射精（女体）", "指入れ", "オナニー", "足コキ", "絶頂", "汎用エロ（女体）", "試し打ち", "レズビアンクンニ", "性器を広げる", "レズ＋広げる"]
作り方 = "テキストから（写真なし）"  #@param ["テキストから（写真なし）", "写真から（1枚必要）"]
#@markdown ### プロンプト（任意）
#@markdown 空ならシーンのおすすめ文。自分の文を貼ってよい。写真からで Picture 1 が無いときは自動で足します。テキストからに切り替えたとき、写真用の文が残っていても外します。
文章 = ""  #@param {type:"string"}
#@markdown 写真からのときだけ。`auto` か空なら input の一番新しい jpg。テキストからでは使いません。
写真ファイル = "auto"  #@param {type:"string"}
#@markdown 秒数。1本は 4〜15。20〜120秒は下の「つなぐ」を選ぶ。
秒数 = 10  #@param {type:"number"}
#@markdown 20〜120秒は 10秒ずつつなぐ（解像度もステップも落とさない）。専用ストーリーはカット編集。
長さの作り方 = "1本（最大15秒）"  #@param ["1本（最大15秒）", "つなぐ 20秒", "つなぐ 30秒", "つなぐ 40秒", "つなぐ 50秒", "つなぐ 60秒", "つなぐ 70秒", "つなぐ 80秒", "つなぐ 90秒", "つなぐ 100秒", "つなぐ 110秒", "つなぐ 120秒", "つなぐ 2分", "つなぐ（秒数欄・16〜120）"]
#@markdown ### つなぐときだけ（任意）
#@markdown 20秒は2本、120秒は12本。空欄は前の続き。別の指示を出すときだけ書く。Picture 1 は書かない。
つなぎ2 = ""  #@param {type:"string"}
つなぎ3 = ""  #@param {type:"string"}
つなぎ4 = ""  #@param {type:"string"}
つなぎ5 = ""  #@param {type:"string"}
つなぎ6 = ""  #@param {type:"string"}
つなぎ7 = ""  #@param {type:"string"}
つなぎ8 = ""  #@param {type:"string"}
つなぎ9 = ""  #@param {type:"string"}
つなぎ10 = ""  #@param {type:"string"}
つなぎ11 = ""  #@param {type:"string"}
つなぎ12 = ""  #@param {type:"string"}

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
for name in ("select_loras", "h3_lora_studio", "h3_i2v_phone", "h3_t2v", "h3_r2v_core", "h3_motion_graphics"):
    sys.modules.pop(name, None)
from h3_r2v_core import is_oom_error, frames
from h3_i2v_phone import DEFAULT_FIRST_IMAGE, collect_output_videos, newest_mp4, newest_image, stage_image_into_input, is_auto_image_name, ref_image_url
from h3_t2v import CANVAS_9_16, assert_t2v_graph, build_t2v_graph, canvas_for_aspect, resolve_t2v_prompt, t2v_retry_plans, validate_t2v_prompt
from h3_motion_graphics import CANVAS_8_9, assert_i2va_graph, build_i2va_graph, i2va_retry_plans, prefer_fl2v_lora, resolve_motion_prompt, validate_motion_ad_prompt, validate_studio_i2v_prompt
from h3_lora_studio import apply_user_prompt, explain_choice, format_job_fail, format_prompt_http_fail, friendly_lora, friendly_select_error, inject_lora_stack, is_blank_prompt, is_vanilla, is_story, load_story, prepare_story_clip, story_stills_dir, prepend_triggers, resolve_mode, resolve_situation, clamp_studio_duration, resolve_studio_length, apply_stack_fallbacks, missing_stack_files, comfy_missing_loras, download_jobs_for, fetch_weight, load_catalog, civitai_token, civitai_download_fallbacks, restart_studio_comfy, fetch_comfy_object_info, continue_chain_prompt, next_chain_prompt, extract_last_frame, concat_studio_clips, has_i2v_lock, comfy_free, situation_ids
from select_loras import forbidden_hits, load_forbidden, select_loras
import select_loras as _select_loras
import h3_lora_studio as _h3_studio
if not getattr(_select_loras, "MAX_HELPERS", None) or int(getattr(_h3_studio, "CHAIN_MAX_S", 0) or 0) < 120 or not getattr(_h3_studio, "fetch_comfy_object_info", None) or not getattr(_h3_studio, "has_i2v_lock", None) or not getattr(_h3_studio, "comfy_free", None) or not getattr(_h3_studio, "prepare_story_clip", None) or not getattr(_h3_studio, "validate_story_follow", None) or "okaeri-120s" not in getattr(_h3_studio, "STORY_IDS", set()):
    raise SystemExit("部品の読み込みが古いです。ランタイムを再起動して①→②→③、または②をもう一度実行してから③。")

DURATION, CLIPS, CHAIN = resolve_studio_length(秒数, 長さの作り方)
CHAIN_EXTRAS = [つなぎ2, つなぎ3, つなぎ4, つなぎ5, つなぎ6, つなぎ7, つなぎ8, つなぎ9, つなぎ10, つなぎ11, つなぎ12]
if float(DURATION) != float(秒数):
    if CHAIN:
        print("秒数は", int(DURATION), "にします（つなぐは 16〜120 秒。20〜120秒のボタンは秒数欄を無視）。")
    else:
        print("秒数は", int(DURATION), "にします（1本は 4〜15 秒。16秒以上は「つなぐ」）。")
if CHAIN:
    print("つなぎ:", " + ".join(str(int(x)) + "秒" for x in CLIPS), "（最後のコマから続ける。画質は落とさない）")
    named = [str(i + 2) + "本目" for i, x in enumerate(CHAIN_EXTRAS) if not is_blank_prompt(x)]
    if named:
        print("別の文を使うクリップ:", "、".join(named), "。空の欄は前の続き。")
elif any(not is_blank_prompt(x) for x in CHAIN_EXTRAS):
    print("つなぎ欄は「つなぐ」のときだけ使います。今は1本なので無視します。")

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
STORY = None
STORY_STILLS = None
STORY_OVERRIDE = None
print()
print(explain_choice(やりたいシーン, 作り方))
print()
FORBIDDEN_FILE = DRIVE_ROOT / "forbidden.json"
fb = load_forbidden(FORBIDDEN_FILE)
print("禁止語ファイル:", FORBIDDEN_FILE)
print("extra:", ", ".join(fb["extra"]) or "（空）")
print("未成年・21歳未満・アフィURLはファイルから消せません。足す・消すのは extra。")
print()

if is_story(やりたいシーン):
    STORY = load_story(SITUATION, studio_root=STUDIO)
    DURATION = float(STORY.get("duration_s") or 120)
    CLIPS = [float(c.get("duration_s") or STORY.get("clip_s") or 10) for c in STORY["clips"]]
    CHAIN = True
    VANILLA = False
    STORY_STILLS = story_stills_dir(DRIVE_ROOT / "input", STORY)
    STORY_STILLS.mkdir(parents=True, exist_ok=True)
    print(str(STORY.get("title_ja") or STORY.get("id")), "専用。文章欄・つなぎ欄・秒数は使いません。", len(STORY["clips"]), "本の専用文で部品を切り替えます。")
    print("カット編集です。最後のコマからは続けません（再現優先）。")
    cv = STORY.get("canvas") or {}
    print("画面は", int(cv.get("width") or 576), "x", int(cv.get("height") or 1024), "（", str(cv.get("aspect") or "9:16"), "）固定。1本", int(STORY.get("clip_s") or CLIPS[0]), "秒。")
    print("各本の写真（任意）:", STORY_STILLS)
    for c in STORY["clips"]:
        print(" ", c.get("still") or "（写真なし）", c.get("label") or "")
    print("写真が無いクリップはテキストから（顔はクリップごとに変わります）。")
    if MODE == "i2v" and not is_auto_image_name(写真ファイル):
        src = Path(写真ファイル)
        if not src.is_file():
            src = DRIVE_ROOT / "input" / 写真ファイル
        if src.is_file():
            STORY_OVERRIDE = src
            print("1本目の写真として使います:", src.name)

CUSTOM_PROMPT = not is_blank_prompt(文章)
if STORY:
    CUSTOM_PROMPT = True
elif MODE == "t2v":
    print("写真欄はテキストからでは使いません。空でも auto でもエラーにしません。")
    if has_i2v_lock(文章):
        print("文章欄に写真用の文（Picture 1）が残っていたので外します。このシーンのおすすめ文でテキストから作ります。")
        CUSTOM_PROMPT = False

if STORY:
    FILENAME_PREFIX = "video/h3_" + str(STORY.get("id") or "story")
    try:
        planned0 = prepare_story_clip(STORY, 0, last_frame=None, stills_dir=STORY_STILLS, studio_root=STUDIO, catalog_path=STUDIO / "catalog" / "loras.json", forbidden_path=FORBIDDEN_FILE, clip0_override=STORY_OVERRIDE)
    except SystemExit as exc:
        hint = friendly_select_error(exc)
        raise SystemExit(hint or str(exc)) from None
    stack = planned0["stack"]
    prompt = planned0["prompt"]
    SAMPLER = planned0["sampler"]
    STEPS = int(SAMPLER.get("steps") or 12)
    cfg = planned0["cfg"]
    w, h = int(planned0["width"]), int(planned0["height"])
    MODE = planned0["mode"]
    print("1本目:", planned0["label"], MODE)
    print("入る部品:")
    for x in stack:
        print(" -", friendly_lora(x["id"]), "強さ", x.get("strength_model"), x.get("role") or "")
    if planned0.get("missing_still"):
        print("1本目の写真が無いのでテキストから作ります。")
elif VANILLA:
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
        default_i2v = resolve_motion_prompt("", duration_s=float(CLIPS[0]), with_last_frame=False)
        prompt, CUSTOM_PROMPT = apply_user_prompt(文章, mode="i2v", default_prompt=default_i2v)
        if CUSTOM_PROMPT:
            errs = validate_studio_i2v_prompt(prompt, forbidden_path=FORBIDDEN_FILE)
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
    try:
        cfg = select_loras(profile_name=SITUATION, mode=MODE, prompt_arg=prompt_arg, catalog_path=STUDIO / "catalog" / "loras.json", profiles_dir=STUDIO / "profiles", turbo_override=None, extra_forbidden=None, forbidden_path=FORBIDDEN_FILE)
    except TypeError:
        cfg = select_loras(profile_name=SITUATION, mode=MODE, prompt_arg=prompt_arg, catalog_path=STUDIO / "catalog" / "loras.json", profiles_dir=STUDIO / "profiles", turbo_override=None)
    except SystemExit as exc:
        hint = friendly_select_error(exc)
        raise SystemExit(hint or str(exc)) from None
    if 動きの底上げ or 胸を強調 or リアル寄り or 静止画用の写実:
        print("上級の追加部品は無視します。ふたなりの竿と穴はシーン側で既に併用しています。")
    stack = cfg["stack"]
    prompt = prepend_triggers(cfg["prompt"], stack)
    SAMPLER = cfg["sampler"]
    STEPS = int(SAMPLER["steps"])
    print("入る部品:")
    for x in stack:
        role = x.get("role") or ""
        print(" -", friendly_lora(x["id"]), "強さ", x.get("strength_model"), role)
    w, h = int(cfg["canvas"]["width"]), int(cfg["canvas"]["height"])
    if MODE == "i2v":
        errs = validate_studio_i2v_prompt(prompt, forbidden_path=FORBIDDEN_FILE)
        if errs:
            raise SystemExit(errs)

print()
print("使う文章（先頭）:")
print(prompt[:450])
print("…")
print()

if STORY:
    w, h = int(planned0["width"]), int(planned0["height"])
elif 画面の向き == "縦（スマホ）":
    w, h = canvas_for_aspect("9:16")
elif 画面の向き == "横":
    w, h = canvas_for_aspect("16:9")
elif 画面の向き == "やや正方形":
    w, h = CANVAS_8_9
print("画面サイズ:", w, "x", h, " / 秒数:", int(DURATION), " / ステップ:", STEPS, SAMPLER.get("sampler_name"), SAMPLER.get("scheduler"))
if CHAIN:
    if STORY:
        print("カット編集。1本", int(CLIPS[0]), "秒 ×", len(CLIPS), "本。1本で 16秒以上は作りません。")
    else:
        print("1本で 16秒以上は作りません。画質を保ったまま 10秒ずつつなぎます。")
if VANILLA and MODE == "t2v":
    prompt = resolve_t2v_prompt("" if has_i2v_lock(文章) else 文章, landscape=w > h)
    errs = validate_t2v_prompt(prompt)
    if errs:
        raise SystemExit(errs)
hits = forbidden_hits(prompt, path=FORBIDDEN_FILE)
if hits:
    hint = friendly_select_error(SystemExit(f"forbidden subject in prompt: {hits}"))
    raise SystemExit(hint or f"forbidden subject in prompt: {hits}")

obj = {}
if not 試し打ちだけ:
    print("エンジンの部品表を確認しています…")
    obj = fetch_comfy_object_info(PORT)
    if "MiniMaxH3ImageToVideo" not in obj:
        raise SystemExit("エンジンがまだです。②を先に実行してください。")

diff = list((COMFY_DIR / "models/diffusion_models").glob("*fl2va*"))
if not diff and not 試し打ちだけ:
    raise SystemExit("土台がありません。②を先に実行してください。")
unet = diff[0].name if diff else "minimax_h3_fl2va_pruned_int8_convrot.safetensors"

if not VANILLA:
    lora_dir = COMFY_DIR / "models" / "loras"
    catalog_now = load_catalog(STUDIO)
    id_list = [str(x.get("id") or "") for x in stack if x.get("id")]
    if STORY:
        id_list = situation_ids(SITUATION)
        print(str(int(DURATION)) + "秒分の部品を確認します:", ", ".join(id_list))
    need = missing_stack_files(stack, lora_dir)
    if STORY:
        jobs_all = download_jobs_for(id_list, lora_dir, catalog=catalog_now)
        need = [str(dest.name) for url, dest, row in jobs_all if not dest.is_file() or dest.stat().st_size < 1000]
    if need:
        print("足りない部品を入れます:", ", ".join(need))
        token = civitai_token("")
        jobs = download_jobs_for(id_list, lora_dir, catalog=catalog_now)
        for url, dest, row in jobs:
            if dest.name not in need and dest.name not in [Path(n).name for n in need]:
                continue
            auth = "civitai" if str(row.get("source")) == "civitai" else ""
            fallbacks = civitai_download_fallbacks(row) if auth else None
            fetch_weight(url, dest, token=token, auth=auth, fallback_urls=fallbacks, strict=False)
    stack, replaced = apply_stack_fallbacks(stack, lora_dir, catalog_now)
    if replaced:
        print("アナル専用部品が無かったので総合えっちで代用します。Drive の models/loras に H3_anal_penetration_v1.safetensors を置けば専用になります。")
        print("入る部品:")
        for x in stack:
            print(" -", friendly_lora(x["id"]), "強さ", x.get("strength_model"), x.get("role") or "")
    still = missing_stack_files(stack, lora_dir)
    if still and not 試し打ちだけ:
        raise SystemExit("このシーンの部品がありません: " + ", ".join(still) + "。Drive の models/loras に置いて③をもう一度実行してください。②をもう一度回すだけでは取れないことがあります（Civitai 有料）。")
    unseen = comfy_missing_loras(stack, obj) if obj else []
    if unseen and not 試し打ちだけ:
        print("エンジンが新しい部品をまだ見ていないので、再読み込みします…")
        restart_studio_comfy(COMFY_DIR, port=PORT)
        obj = fetch_comfy_object_info(PORT)
        unseen = comfy_missing_loras(stack, obj)
        if unseen:
            print("まだ見えていないファイル:", ", ".join(unseen), "（このまま試します）")

first_name = None
inp = COMFY_DIR / "input"
inp.mkdir(parents=True, exist_ok=True)
if STORY:
    if planned0.get("still_path"):
        first_name = stage_image_into_input(planned0["still_path"], inp)
        print("使う写真:", first_name)
elif MODE == "i2v":
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
CLIP_DURATION = float(CLIPS[0])
CLIP_INDEX = 0
GRAPH_MODE = MODE
GRAPH_FIRST = first_name
GRAPH_PROMPT = prompt
prev_prompt = prompt

def make_graph(plan):
    steps = int(SAMPLER["steps"])
    clip_seed = int(SEED) + int(CLIP_INDEX)
    prefix = FILENAME_PREFIX + ("_p" + str(int(CLIP_INDEX)) if CHAIN else "")
    if GRAPH_MODE == "t2v":
        g = build_t2v_graph(
            prompt=GRAPH_PROMPT, unet=unet, lora_name=lora_name, lora_strength=lora_strength,
            width=int(plan["width"]), height=int(plan["height"]),
            duration_s=CLIP_DURATION, seed=clip_seed, steps=steps,
            filename_prefix=prefix,
            has_lora_loader=("LoraLoaderModelOnly" in obj) or 試し打ちだけ,
            has_audio_decode=("VAEDecodeAudio" in obj) or 試し打ちだけ,
        )
        if not VANILLA:
            inject_lora_stack(g, stack, sampler=SAMPLER)
        errs = assert_t2v_graph(g)
    else:
        g = build_i2va_graph(
            first_image=GRAPH_FIRST, last_image=None, prompt=GRAPH_PROMPT, unet=unet,
            lora_name=lora_name, lora_strength=lora_strength,
            width=int(plan["width"]), height=int(plan["height"]),
            duration_s=CLIP_DURATION, seed=clip_seed, steps=steps,
            filename_prefix=prefix,
            has_lora_loader=("LoraLoaderModelOnly" in obj) or 試し打ちだけ,
            has_audio_decode=("VAEDecodeAudio" in obj) or 試し打ちだけ,
        )
        if not VANILLA:
            inject_lora_stack(g, stack, sampler=SAMPLER)
        homage = bool(VANILLA and not CUSTOM_PROMPT and CLIP_INDEX == 0)
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

def wait_prompt(pid, timeout=3600):
    t0 = time.time()
    while time.time() - t0 < timeout:
        with urllib.request.urlopen(f"http://127.0.0.1:{PORT}/history/{pid}", timeout=60) as r:
            hist = json.loads(r.read().decode())
        entry = hist.get(pid) or {}
        st = entry.get("status") or {}
        if st.get("completed") or entry.get("outputs"):
            if st.get("status_str") == "error":
                return False, entry
            return True, entry
        for m in st.get("messages") or []:
            if isinstance(m, list) and m and m[0] == "execution_error":
                return False, m
        time.sleep(2)
    return False, "timeout"

def generate_one():
    plans_now = t2v_retry_plans(width=w, height=h) if GRAPH_MODE == "t2v" else i2va_retry_plans(width=w, height=h)
    ok_entry = None
    before = newest_mp4(OUT)
    for plan in plans_now:
        label = plan.get("label") or plan
        for attempt in (1, 2):
            print("サイズを試しています:", label, "（同じサイズ再試行）" if attempt == 2 else "")
            g = make_graph(plan)
            res, err = post_prompt(g)
            oom = False
            if err:
                if is_oom_error(err):
                    oom = True
                else:
                    raise SystemExit(format_prompt_http_fail(err, stack))
            else:
                ok, payload = wait_prompt(res["prompt_id"])
                if ok:
                    ok_entry = payload
                    break
                if is_oom_error(str(payload)):
                    oom = True
                else:
                    raise SystemExit(format_job_fail(GRAPH_MODE, payload))
            print("メモリが足りません。VRAM を解放します。")
            comfy_free(PORT)
            if attempt == 1:
                continue
            print("小さい画面でやり直します。")
        if ok_entry is not None:
            break
    if ok_entry is None:
        raise SystemExit("メモリ不足で作れませんでした。秒数を短くするか、A100 のまま②からやり直してください。")
    videos = collect_output_videos(ok_entry, OUT)
    fresh = newest_mp4(OUT)
    if fresh and fresh not in videos and (before is None or fresh != before):
        videos.append(fresh)
    if not videos:
        raise SystemExit("ファイル名が取れませんでした。Drive の output フォルダを見てください: " + str(OUT))
    return videos[0]

if 試し打ちだけ:
    g = make_graph(plans[0])
    print("試し打ちOK。部品:", [n["inputs"]["lora_name"] for n in g.values() if n.get("class_type") == "LoraLoaderModelOnly"])
    if STORY:
        print("専用" + str(len(STORY["clips"])) + "本:")
        for i, c in enumerate(STORY["clips"]):
            print(" ", i + 1, c.get("label"), c.get("situation"), c.get("start"))
    elif CHAIN:
        print("つなぎ予定:", " + ".join(str(int(x)) + "秒" for x in CLIPS))
        named = [str(i + 2) + "本目" for i, x in enumerate(CHAIN_EXTRAS) if not is_blank_prompt(x)]
        if named:
            print("別の文:", "、".join(named))
    print("実際の動画は「試し打ちだけ」をオフにして③をもう一度。")
else:
    print()
    print("作り始めています。数分〜十数分かかることがあります…")
    clip_paths = []
    inp = COMFY_DIR / "input"
    inp.mkdir(parents=True, exist_ok=True)
    prev_sit = None
    for CLIP_INDEX, CLIP_DURATION in enumerate(CLIPS):
        if STORY:
            try:
                planned = prepare_story_clip(STORY, CLIP_INDEX, last_frame=None, stills_dir=STORY_STILLS, studio_root=STUDIO, catalog_path=STUDIO / "catalog" / "loras.json", forbidden_path=FORBIDDEN_FILE, clip0_override=STORY_OVERRIDE if CLIP_INDEX == 0 else None, prev_situation=prev_sit)
            except SystemExit as exc:
                hint = friendly_select_error(exc)
                raise SystemExit(hint or str(exc)) from None
            prev_sit = planned["situation"]
            stack = planned["stack"]
            SAMPLER = planned["sampler"]
            cfg = planned["cfg"]
            GRAPH_MODE = planned["mode"]
            GRAPH_PROMPT = planned["prompt"]
            if planned.get("missing_still"):
                print("写真が無いのでテキストから:", planned["label"], planned.get("missing_still"))
            if planned.get("still_path") is not None:
                first_name = stage_image_into_input(planned["still_path"], inp)
            elif GRAPH_MODE == "t2v":
                first_name = None
            if planned.get("stack_changed"):
                print("部品を切り替えます:", planned["label"], planned["situation"])
                comfy_free(PORT)
            w, h = int(planned["width"]), int(planned["height"])
            CLIP_DURATION = float(planned.get("duration_s") or CLIP_DURATION)
            print("クリップ", CLIP_INDEX + 1, "/", len(CLIPS), ":", planned["label"], int(CLIP_DURATION), "秒", GRAPH_MODE, [x.get("id") for x in stack])
        else:
            GRAPH_MODE = MODE if CLIP_INDEX == 0 else "i2v"
            GRAPH_PROMPT = next_chain_prompt(CLIP_INDEX, first_prompt=prompt, prev_prompt=prev_prompt, extras=CHAIN_EXTRAS)
            if CLIP_INDEX > 0:
                GRAPH_PROMPT = prepend_triggers(GRAPH_PROMPT, stack)
                extra_now = CHAIN_EXTRAS[CLIP_INDEX - 1] if CLIP_INDEX - 1 < len(CHAIN_EXTRAS) else ""
                if not is_blank_prompt(extra_now):
                    print("このクリップはつなぎ欄の文を使います")
                hits = forbidden_hits(GRAPH_PROMPT, path=FORBIDDEN_FILE)
                if hits:
                    hint = friendly_select_error(SystemExit("forbidden subject in prompt: " + str(hits)))
                    raise SystemExit(hint or ("forbidden subject in prompt: " + str(hits)))
                if "Picture 1" not in GRAPH_PROMPT:
                    raise SystemExit("つなぎの2本目以降に最後のコマ（Picture 1）がありません。②のあと③をもう一度。")
            print("クリップ", CLIP_INDEX + 1, "/", len(CLIPS), ":", int(CLIP_DURATION), "秒", GRAPH_MODE)
        GRAPH_FIRST = first_name
        prev_prompt = GRAPH_PROMPT
        if GRAPH_MODE == "i2v" and not GRAPH_FIRST:
            raise SystemExit("写真または前のクリップの最後のコマがありません。")
        clip_path = generate_one()
        clip_paths.append(clip_path)
        print("保存:", clip_path)
        if CLIP_INDEX + 1 < len(CLIPS) and not STORY:
            frame = inp / ("h3_chain_" + str(CLIP_INDEX) + ".png")
            extract_last_frame(clip_path, frame)
            first_name = stage_image_into_input(frame, inp)
    final = clip_paths[0]
    if len(clip_paths) > 1:
        final = concat_studio_clips(clip_paths, OUT / (("h3_" + str(STORY.get("id")) + "_concat.mp4") if STORY else ("h3_chain_" + str(int(DURATION)) + "s.mp4")))
        print("つなぎ完了:", final)
        if STORY:
            print("カット編集です。クリップの境はシームレスではありません。")
    print()
    print("できました。下に再生、Drive にも保存しています。")
    print("保存:", final)
    if final.is_file():
        display(HTML(f"<p style='font-size:16px'>保存先: <code>{final}</code></p>"))
        display(Video(str(final), embed=True, width=360))
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
        {"cell_type": "code", "metadata": {"id": "ls3_gen_v2"}, "execution_count": None, "outputs": [], "source": to_source(CELL3)},
    ],
}
blob = json.dumps(nb, ensure_ascii=False, indent=1)
for out in OUTS:
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(blob, encoding="utf-8")
    print("wrote", out, "bytes", out.stat().st_size)
