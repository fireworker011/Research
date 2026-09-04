#!/usr/bin/env python3
"""Write the phone I2V Colab notebook with a free prompt (auto / 9:16 / 16:9 / 8:9)."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTS = [
    ROOT / "minimax_h3_i2v_free_phone.ipynb",
    ROOT / "minimaxh3" / "minimax_h3_i2v_free_phone.ipynb",
]

MD0 = r"""# MiniMax H3 I2V（スマホ・自由プロンプト・auto / 9:16 / 16:9）

**セルは3本だけ。** 1枚の画像からテキスト指示で動画（I2V）。T2V スマホ版と同じモデル（FL2VA + turbo LoRA）に、写真を最初のフレームとして渡す。Comfyの画面は開かない。

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1DdzLY-zRwCi_1VlW9dq9f8ljQ8QXmvTp)

Google Drive コピー（Civitai 記載）: https://colab.research.google.com/drive/1DdzLY-zRwCi_1VlW9dq9f8ljQ8QXmvTp

テキストだけ（T2V）: [minimax_h3_t2v_phone.ipynb](https://colab.research.google.com/github/fireworker011/Research/blob/cursor/minimax-h3-motion-identity-e959/minimax_h3_t2v_phone.ipynb)。ココナラ広告固定の I2V は [minimax_h3_i2v_phone.ipynb](https://colab.research.google.com/github/fireworker011/Research/blob/cursor/minimax-h3-motion-identity-e959/minimax_h3_i2v_phone.ipynb)。

## スマホでの手順

1. 上の **Open in Colab** を開く
2. 右上 ** ram/disk のあたり → ランタイムのタイプ → GPU（A100）**
3. スマホの Drive アプリで `マイドライブ/minimax-h3-comfyui/input/` に jpg / png を置く
4. メニュー **⋮ → ランタイム → すべてのセルを実行**
5. ①で Google Drive の許可を出す
6. ②は初回だけ長い（T2V と同じモデル約42GB。既にあればスキップ）
7. ③の `PROMPT` を書いて実行。`FIRST_IMAGE` が `auto` なら input の一番新しい画像を使う。`ASPECT` が `auto` なら画像の向きから 9:16（576×1024）/ 16:9（1024×576）/ 8:9（768×864）を選ぶ。1280×720 は H3 非対応（720 が 32 の倍数ではない）。動画は Drive の `MyDrive/minimax-h3-comfyui/output`

## Civitai API（シークレットは使わなくてよい）

Civitai から LoRA を取るときに使う。**キーそのものは画面に出ません。ノートやチャットに貼ったまま保存しない。**

1. ブラウザで https://civitai.com/user/account を開く
2. **API Keys** → Add API key → コピー
3. **いちばん簡単:** スマホの Drive アプリで `マイドライブ/minimax-h3-comfyui/` を開き、新規テキスト `civitai_api_token.txt` を作ってキーを **1行だけ** 貼る。①を実行すると読み込む
4. 今回だけなら、①のフォーム `CIVITAI_API_TOKEN` に貼る（ノートは保存しない）
5. PC で鍵アイコンが分かる人だけ: 左の鍵 → 名前は必ず `CIVITAI_API_TOKEN`

`LAST_IMAGE` に2枚目を入れると、最後のフレームも固定する（FL2VA）。

動画の中にアフィURLは出さない。リンクはプロフィール。画面上は「広告」。未成年を描くプロンプトは③で止まる。
"""

CELL1 = r'''#@title ① Driveをつなぐ（最初の許可だけ）
print("=" * 60)
print(" ① Google Drive + GPU + Civitai API")
print("=" * 60)

from google.colab import drive
from pathlib import Path
import os, urllib.request

DRIVE_ROOT = "/content/drive/MyDrive/minimax-h3-comfyui"  #@param {type:"string"}
COMFY_DIR = "/content/ComfyUI"
#@markdown **Civitai API キー（空でOK。Drive の civitai_api_token.txt があればそれを読む）**
CIVITAI_API_TOKEN = ""  #@param {type:"string"}

drive.mount("/content/drive")

DRIVE_MODELS = f"{DRIVE_ROOT}/models"
for sub in ["diffusion_models", "text_encoders", "vae", "loras"]:
    os.makedirs(f"{DRIVE_MODELS}/{sub}", exist_ok=True)
os.makedirs(f"{DRIVE_ROOT}/output", exist_ok=True)
os.makedirs(f"{DRIVE_ROOT}/input", exist_ok=True)

# ヘルパーは②でも取る。①では API 読み込みだけ先に取る
REPO = "fireworker011/Research"
for branch in ["cursor/minimax-h3-motion-identity-e959", "cursor/h3-i2v-free-phone-22ce"]:
    url = f"https://raw.githubusercontent.com/{REPO}/{branch}/colab/h3_civitai.py"
    dest = Path("/content/h3_civitai.py")
    try:
        urllib.request.urlretrieve(url, dest)
        if dest.is_file() and dest.stat().st_size > 100:
            break
    except Exception as e:
        print("helper fetch skip", branch, e)

import sys
sys.path.insert(0, "/content")
try:
    from h3_civitai import apply_civitai_token, describe_civitai_status, load_civitai_token
    token, src = load_civitai_token(pasted=CIVITAI_API_TOKEN, drive_root=DRIVE_ROOT)
    apply_civitai_token(token)
    print("Civitai API:", describe_civitai_status(src, bool(token)))
    civitai_src = src
except Exception as e:
    token, civitai_src = "", "missing"
    print("Civitai API: ヘルパー未取得。Drive の civitai_api_token.txt を②で読む。", e)

with open("/content/h3_paths.env", "w") as f:
    f.write(f"DRIVE_ROOT={DRIVE_ROOT}\n")
    f.write(f"DRIVE_MODELS={DRIVE_MODELS}\n")
    f.write(f"COMFY_DIR={COMFY_DIR}\n")
    f.write(f"CIVITAI_TOKEN_SOURCE={civitai_src}\n")

print("Drive:", DRIVE_ROOT)
print("写真を置く場所:", f"{DRIVE_ROOT}/input")
print("動画の保存先:", f"{DRIVE_ROOT}/output")
print("Civitai キーのファイル:", f"{DRIVE_ROOT}/civitai_api_token.txt")

import torch
if not torch.cuda.is_available():
    raise SystemExit("GPU がオフです。ランタイム → ランタイムのタイプを変更 → A100 を選んで、①からやり直してください。")
props = torch.cuda.get_device_properties(0)
vram = props.total_memory / 1024 ** 3
print("GPU:", torch.cuda.get_device_name(0), "VRAM GiB:", round(vram, 1))
if vram < 20:
    raise SystemExit("VRAM が足りません。A100 を選んでください。")
if vram < 70:
    print("40GB クラス: 9:16 は 576x1024、16:9 は 1024x576、8:9 は 768x864。OOM なら自動で短辺を半分。")
else:
    print("80GB クラス: 9:16 576x1024 / 16:9 1024x576 / 8:9 768x864（必要なら 768 短辺クラス）。")
print("OK → 次は②")
'''

CELL2 = r'''#@title ② ComfyとH3モデルを用意（初回は待つ）
print("=" * 60)
print(" ② I2V 準備（FL2VA + turbo LoRA。写真は③で渡す）")
print("=" * 60)

#@markdown **任意:** Civitai の LoRA を1本追加するなら URL か modelVersionId（空なら土台だけ）
CIVITAI_LORA_URL = ""  #@param {type:"string"}

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
REPO = "fireworker011/Research"
BRANCHES = ["cursor/minimax-h3-motion-identity-e959", "cursor/h3-i2v-free-phone-22ce"]
HELPERS = [
    "colab/h3_r2v_core.py",
    "colab/h3_motion_graphics.py",
    "colab/h3_i2v_phone.py",
    "colab/h3_t2v.py",
    "colab/h3_civitai.py",
    "colab/h3_i2v_free.py",
]
PROBE = "colab/h3_civitai.py"

def sh(cmd, **kw):
    print("+", " ".join(cmd) if isinstance(cmd, list) else cmd)
    return subprocess.run(cmd, check=False, **kw)

def raw_url(branch: str, rel: str) -> str:
    return f"https://raw.githubusercontent.com/{REPO}/{branch}/{rel}"

def fetch_text(url: str, dest: Path) -> bool:
    try:
        urllib.request.urlretrieve(url, dest)
        return dest.is_file() and dest.stat().st_size > 100
    except Exception as e:
        print("fetch fail", url, e)
        return False

# 全ヘルパーは同じブランチから取る（新旧が混ざると import が壊れる）
branch = None
for b in BRANCHES:
    if fetch_text(raw_url(b, PROBE), Path("/content") / Path(PROBE).name):
        branch = b
        break
print("helper branch:", branch or "(GitHub 不達 → Drive のコピー)")

for rel in HELPERS:
    name = Path(rel).name
    dest = Path("/content") / name
    ok = branch is not None and fetch_text(raw_url(branch, rel), dest)
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
from h3_i2v_phone import i2v_download_jobs, missing_weight_files
from h3_civitai import (
    apply_civitai_token, describe_civitai_status, fetch_civitai_weight,
    load_civitai_token, lora_dest_from_url, parse_civitai_lora_url,
)

token, src = load_civitai_token(drive_root=DRIVE_ROOT)
apply_civitai_token(token)
print("Civitai API:", describe_civitai_status(src, bool(token)))

if not (COMFY_DIR / "main.py").is_file():
    sh(["git", "clone", "--depth", "1", "https://github.com/Comfy-Org/ComfyUI.git", str(COMFY_DIR)])
else:
    sh(["git", "-C", str(COMFY_DIR), "pull", "--ff-only"])

req = COMFY_DIR / "requirements.txt"
if req.is_file():
    sh([sys.executable, "-m", "pip", "install", "-q", "-r", str(req)])

def link_dir(link_path: Path, target: Path):
    target.mkdir(parents=True, exist_ok=True)
    if link_path.is_symlink():
        link_path.unlink()
    elif link_path.is_dir():
        bak = Path(str(link_path) + ".local_bak")
        if bak.exists():
            shutil.rmtree(bak, ignore_errors=True)
        if any(link_path.iterdir()):
            link_path.rename(bak)
            print("退避", bak)
        else:
            link_path.rmdir()
    elif link_path.exists():
        link_path.unlink()
    link_path.symlink_to(target)
    print("link", link_path, "→", target)

models_root = COMFY_DIR / "models"
models_root.mkdir(parents=True, exist_ok=True)
for sub in ["diffusion_models", "text_encoders", "vae", "loras"]:
    link_dir(models_root / sub, DRIVE_MODELS / sub)
link_dir(COMFY_DIR / "output", DRIVE_ROOT / "output")
link_dir(COMFY_DIR / "input", DRIVE_ROOT / "input")

def fetch_weight(url: str, dest: Path, min_bytes: int = 1_000_000):
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.is_file() and dest.stat().st_size > min_bytes:
        print(f"skip {dest.name} ({dest.stat().st_size/1e9:.2f} GB)")
        return
    tmp = dest.with_name(dest.name + ".part")
    wget = shutil.which("wget")
    if wget:
        r = sh([wget, "-c", "--show-progress", "-O", str(tmp), url])
        if r.returncode != 0:
            raise SystemExit(f"DL 失敗: {dest.name}")
    else:
        urllib.request.urlretrieve(url, tmp)
    if not tmp.is_file() or tmp.stat().st_size < min_bytes:
        if tmp.exists():
            tmp.unlink()
        raise SystemExit(f"DL 失敗（小さい）: {dest.name}")
    tmp.replace(dest)
    print(f"saved {dest.name} ({dest.stat().st_size/1e9:.2f} GB)")

print("モデル不足:", missing_weight_files(DRIVE_MODELS) or "なし")
for url, dest in i2v_download_jobs(DRIVE_MODELS):
    fetch_weight(url, dest)
left = missing_weight_files(DRIVE_MODELS)
if left:
    raise SystemExit("まだ足りない: " + ", ".join(left))

lora_url = parse_civitai_lora_url(CIVITAI_LORA_URL)
if lora_url:
    if not token:
        raise SystemExit("Civitai LoRA を取るには API キーが必要。①を見て Drive の civitai_api_token.txt を置いてください。")
    dest = lora_dest_from_url(lora_url, DRIVE_MODELS / "loras")
    print("Civitai LoRA を入れます:", dest.name)
    fetch_civitai_weight(lora_url, dest, token=token)

os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")

def comfy_up() -> bool:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{PORT}/object_info", timeout=3) as r:
            obj = json.loads(r.read().decode())
        return "MiniMaxH3ImageToVideo" in obj
    except Exception:
        return False

if comfy_up():
    print("ComfyUI はすでに起動中")
else:
    log = Path("/content/comfyui.log")
    log_f = open(log, "w", buffering=1)
    cmd = [
        sys.executable, "main.py",
        "--listen", "127.0.0.1",
        "--port", str(PORT),
        "--highvram",
        "--disable-auto-launch",
        "--enable-cors-header",
    ]
    print("starting", " ".join(cmd))
    subprocess.Popen(cmd, cwd=str(COMFY_DIR), stdout=log_f, stderr=subprocess.STDOUT, start_new_session=True)
    ok = False
    for _ in range(90):
        if comfy_up():
            ok = True
            break
        time.sleep(2)
    if not ok:
        print(log.read_text(errors="replace")[-4000:])
        raise SystemExit("ComfyUI 起動失敗")
    print("ComfyUI 起動OK")

print("OK → 次は③（写真＋テキストから動画）")
'''

CELL3 = r'''#@title ③ 写真＋テキストから動画（I2V・auto / 9:16 / 16:9 / 8:9）
print("=" * 60)
print(" ③ H3 I2V — first frame + free prompt")
print("=" * 60)

import json, os, sys, time, uuid, urllib.request, urllib.error
from pathlib import Path
from IPython.display import display, Video, HTML
from PIL import Image

FIRST_IMAGE = "auto"  #@param {type:"string"}
LAST_IMAGE = ""  #@param {type:"string"}
PROMPT = ""  #@param {type:"string"}
ASPECT = "auto"  #@param ["auto", "9:16", "16:9", "8:9"]
WIDTH = 0  #@param {type:"integer"}
HEIGHT = 0  #@param {type:"integer"}
DURATION_S = 10  #@param {type:"number"}
STEPS = 4  #@param {type:"integer"}
SEED = 42  #@param {type:"integer"}
USE_LORA = True  #@param {type:"boolean"}
LORA_STRENGTH = 1.0  #@param {type:"number"}
FILENAME_PREFIX = "video/h3_i2v_free_phone"  #@param {type:"string"}
DRY_RUN = False  #@param {type:"boolean"}

sys.path.insert(0, "/content")
from h3_r2v_core import is_oom_error, frames
from h3_motion_graphics import prefer_fl2v_lora
from h3_i2v_phone import (
    is_auto_image_name, newest_image, stage_image_into_input,
    collect_output_videos, newest_mp4,
)
from h3_i2v_free import (
    assert_i2v_graph, aspect_label, build_i2v_graph, canvas_for_aspect,
    i2v_retry_plans, resolve_i2v_prompt, validate_i2v_prompt,
)

env = {}
with open("/content/h3_paths.env") as f:
    for line in f:
        k, v = line.strip().split("=", 1)
        env[k] = v
COMFY_DIR = Path(env["COMFY_DIR"])
DRIVE_ROOT = Path(env["DRIVE_ROOT"])
INP = COMFY_DIR / "input"
OUT = COMFY_DIR / "output"
PORT = 8188
INP.mkdir(parents=True, exist_ok=True)

def resolve_picture(name: str, *, required: bool) -> str | None:
    raw = (name or "").strip().strip('"').strip("'")
    if is_auto_image_name(raw):
        if not required:
            return None
        hit = newest_image([INP, DRIVE_ROOT / "input"])
        if hit:
            return stage_image_into_input(hit, INP)
        if DRY_RUN:
            return "dry_run.jpg"
        raise SystemExit(f"画像がありません。Drive の {DRIVE_ROOT / 'input'} に jpg / png を置いてから③をやり直してください。")
    for cand in [INP / raw, INP / Path(raw).name, DRIVE_ROOT / "input" / Path(raw).name, Path("/content") / Path(raw).name]:
        if cand.is_file():
            return stage_image_into_input(cand, INP)
    if DRY_RUN:
        return Path(raw).name
    raise SystemExit(f"画像が見つかりません: {raw}\nDrive の {DRIVE_ROOT / 'input'} に置いて、FIRST_IMAGE を auto にするかファイル名を入れてください。")

first = resolve_picture(FIRST_IMAGE, required=True)
last = resolve_picture(LAST_IMAGE, required=False) if (LAST_IMAGE or "").strip() else None
print("Picture 1:", first)
print("Picture 2:", last or "(none)")

image_size = None
if (INP / first).is_file():
    with Image.open(INP / first) as im:
        image_size = im.size
    print("image size", image_size)

w, h = int(WIDTH), int(HEIGHT)
if w <= 0 or h <= 0:
    w, h = canvas_for_aspect(ASPECT, image_size=image_size)
prompt = resolve_i2v_prompt(PROMPT, landscape=w > h, with_last_frame=bool(last), duration_s=float(DURATION_S))
errs = validate_i2v_prompt(prompt, with_last_frame=bool(last))
if errs:
    raise SystemExit(errs)
print(prompt[:400], "...")
print("frames", frames(DURATION_S), "canvas", w, "x", h, "aspect", aspect_label(w, h))

obj = {}
if not DRY_RUN:
    with urllib.request.urlopen(f"http://127.0.0.1:{PORT}/object_info", timeout=60) as r:
        obj = json.loads(r.read().decode())
    if "MiniMaxH3ImageToVideo" not in obj:
        raise SystemExit("MiniMaxH3ImageToVideo がありません。②をやり直してください。")

diff = list((COMFY_DIR / "models/diffusion_models").glob("*fl2va*")) if (COMFY_DIR / "models/diffusion_models").exists() else []
if not diff and not DRY_RUN:
    raise SystemExit("fl2va がありません。②をやり直してください。")
unet = diff[0].name if diff else "minimax_h3_fl2va_pruned_int8_convrot.safetensors"
lora_paths = list((COMFY_DIR / "models/loras").glob("*.safetensors")) if (COMFY_DIR / "models/loras").exists() else []
lora = prefer_fl2v_lora(lora_paths, USE_LORA)
print("unet", unet, "lora", lora)

plans = i2v_retry_plans(width=w, height=h)
print("retry plans:", [p["label"] for p in plans])

def make_graph(plan):
    g = build_i2v_graph(
        first_image=first,
        last_image=last,
        prompt=prompt,
        unet=unet,
        lora_name=lora,
        lora_strength=float(LORA_STRENGTH),
        width=int(plan["width"]),
        height=int(plan["height"]),
        duration_s=float(DURATION_S),
        seed=int(SEED),
        steps=int(STEPS),
        filename_prefix=FILENAME_PREFIX,
        has_lora_loader=("LoraLoaderModelOnly" in obj) or DRY_RUN,
        has_audio_decode=("VAEDecodeAudio" in obj) or DRY_RUN,
    )
    g_errs = assert_i2v_graph(g, expect_last=bool(last))
    if g_errs:
        raise SystemExit(g_errs)
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
        with urllib.request.urlopen(req, timeout=180) as r:
            return json.loads(r.read().decode()), None
    except urllib.error.HTTPError as e:
        return None, f"HTTP {e.code}: {e.read().decode('utf-8', errors='replace')[:4000]}"

def wait_prompt(pid, timeout=3600):
    t0 = time.time()
    while time.time() - t0 < timeout:
        with urllib.request.urlopen(f"http://127.0.0.1:{PORT}/history/{pid}", timeout=60) as r:
            hist = json.loads(r.read().decode())
        entry = hist.get(pid) or {}
        status = entry.get("status") or {}
        if status.get("completed") or entry.get("outputs"):
            return True, entry
        for m in status.get("messages") or []:
            if isinstance(m, list) and m and m[0] == "execution_error":
                return False, m
        time.sleep(2)
    return False, "timeout"

def comfy_free():
    try:
        data = json.dumps({"unload_models": True, "free_memory": True}).encode()
        req = urllib.request.Request(
            f"http://127.0.0.1:{PORT}/free",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        urllib.request.urlopen(req, timeout=60).read()
        print("VRAM を解放しました")
        time.sleep(3)
    except Exception as e:
        print(" /free skip:", e)

last_err = None
ok_entry = None
used = None
before = newest_mp4(OUT)
for plan in plans:
    g = make_graph(plan)
    print("try", plan["label"])
    if DRY_RUN:
        print("DRY_RUN skip")
        used = plan
        break
    res, err = post_prompt(g)
    if err:
        last_err = err
        if is_oom_error(err):
            print("OOM on submit", plan["label"])
            comfy_free()
            continue
        raise SystemExit(err)
    if not (res and "prompt_id" in res):
        raise SystemExit(res)
    pid = res["prompt_id"]
    print("ACCEPTED", pid, plan["label"])
    ok, payload = wait_prompt(pid)
    if ok:
        ok_entry = payload
        used = plan
        print("DONE", plan["label"])
        break
    last_err = payload
    if is_oom_error(payload):
        print("OOM", plan["label"], "→ 小さいキャンバスで再実行")
        comfy_free()
        continue
    raise SystemExit(payload)
else:
    raise SystemExit(last_err or "I2V failed")

print("used canvas", (used or {}).get("label"))
videos = collect_output_videos(ok_entry, OUT)
fresh = newest_mp4(OUT)
if fresh and fresh not in videos:
    if before is None or fresh != before:
        videos.append(fresh)
if not videos and fresh:
    videos = [fresh]
if not videos:
    print("出力ファイル名が取れませんでした。Drive の output を見てください:", OUT)
else:
    for p in videos:
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
        "accelerator": "GPU",
        "colab": {"provenance": [], "gpuType": "A100"},
    },
    "cells": [
        {"cell_type": "markdown", "metadata": {}, "source": [line + "\n" for line in MD0.strip("\n").split("\n")]},
        {"cell_type": "code", "metadata": {"id": "i2vf1_drive"}, "execution_count": None, "outputs": [], "source": [line + "\n" for line in CELL1.strip("\n").split("\n")]},
        {"cell_type": "code", "metadata": {"id": "i2vf2_setup"}, "execution_count": None, "outputs": [], "source": [line + "\n" for line in CELL2.strip("\n").split("\n")]},
        {"cell_type": "code", "metadata": {"id": "i2vf3_gen"}, "execution_count": None, "outputs": [], "source": [line + "\n" for line in CELL3.strip("\n").split("\n")]},
    ],
}
blob = json.dumps(nb, ensure_ascii=False, indent=1)
for out in OUTS:
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(blob, encoding="utf-8")
    print("wrote", out, "bytes", out.stat().st_size)
