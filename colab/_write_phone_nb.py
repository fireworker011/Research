#!/usr/bin/env python3
"""Write the phone I2V Colab notebook."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "minimax_h3_i2v_phone.ipynb"

MD0 = r"""# MiniMax H3 I2V（スマホ）

**セルは3本だけ。** 1枚の画像から10秒の動画を作る（I2VA）。Comfyの画面は開かない。

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/fireworker011/Research/blob/cursor/minimax-h3-motion-identity-e959/minimax_h3_i2v_phone.ipynb)

## スマホでの手順

1. 上の **Open in Colab** を開く
2. 右上 ** ram/disk のあたり → ランタイムのタイプ → GPU（A100）**
3. メニュー **⋮ → ランタイム → すべてのセルを実行**
4. ①で Google Drive の許可を出す
5. ②は初回だけ長い（モデル約42GBを Drive に保存。2回目はスキップ）
6. ③が終わると、この画面に動画が出る。同じファイルは Drive の `MyDrive/minimax-h3-comfyui/output`

自分の写真を使うとき: スマホの Drive アプリで `マイドライブ/minimax-h3-comfyui/input/` に jpg を置く。③の `FIRST_IMAGE` を `auto` にするか、ファイル名を入れる。

空のままだとパーカーの参考画像 `coconala_creator_ref.jpg` を使う。

動画の中にアフィURLは出さない。リンクはプロフィール。画面上は「広告」。

えっち用は別ノート [minimax_h3_lora_studio.ipynb](https://colab.research.google.com/github/fireworker011/Research/blob/cursor/minimax-h3-motion-identity-e959/minimax_h3_lora_studio.ipynb)。Drive の `minimax-h3-comfyui` は同じなので、土台は1回入れれば共用できる。同時に2つのノートを動かさない。

無人で毎回回す（Grokbot）: `minimaxh3/GROKBOT.md`。動画エージェントが Drive inbox に置き、Grokbot が Imagine 2.0 → Colab 起動 → ダウンロード → ランタイム停止。

テキストだけ（T2V・9:16）: [minimax_h3_t2v_phone.ipynb](https://colab.research.google.com/github/fireworker011/Research/blob/cursor/minimax-h3-motion-identity-e959/minimax_h3_t2v_phone.ipynb)
"""

CELL1 = r'''#@title ① Driveをつなぐ（最初の許可だけ）
print("=" * 60)
print(" ① Google Drive + GPU")
print("=" * 60)

from google.colab import drive
from pathlib import Path
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

print("Drive:", DRIVE_ROOT)
print("写真を置く場所:", f"{DRIVE_ROOT}/input")
print("動画の保存先:", f"{DRIVE_ROOT}/output")

import torch
if not torch.cuda.is_available():
    raise SystemExit("GPU がオフです。ランタイム → ランタイムのタイプを変更 → A100 を選んで、①からやり直してください。")
props = torch.cuda.get_device_properties(0)
vram = props.total_memory / 1024 ** 3
print("GPU:", torch.cuda.get_device_name(0), "VRAM GiB:", round(vram, 1))
if vram < 20:
    raise SystemExit("VRAM が足りません。A100 を選んでください。")
if vram < 70:
    print("40GB クラス: キャンバスは 768x864。OOM なら自動で 512x576。")
else:
    print("80GB クラス: そのまま 768x864 で回します。")
print("OK → 次は②")
'''

CELL2 = r'''#@title ② ComfyとI2Vモデルを用意（初回は待つ）
print("=" * 60)
print(" ② I2V 準備（FL2VA + turbo LoRA）")
print("=" * 60)

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

def sh(cmd, **kw):
    print("+", " ".join(cmd) if isinstance(cmd, list) else cmd)
    return subprocess.run(cmd, check=False, **kw)

def fetch_text(url: str, dest: Path) -> bool:
    try:
        urllib.request.urlretrieve(url, dest)
        return dest.is_file() and dest.stat().st_size > 100
    except Exception as e:
        print("fetch fail", url, e)
        return False

for rel in ["colab/h3_r2v_core.py", "colab/h3_motion_graphics.py", "colab/h3_i2v_phone.py"]:
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
from h3_i2v_phone import i2v_download_jobs, missing_weight_files

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

print("OK → 次は③（動画をつくる）")
'''

CELL3 = r'''#@title ③ 1枚から動画をつくる（I2VA）
print("=" * 60)
print(" ③ H3 I2VA")
print("=" * 60)

import json, os, sys, time, uuid, urllib.request, urllib.error, shutil
from pathlib import Path
from IPython.display import display, Video, HTML

FIRST_IMAGE = "coconala_creator_ref.jpg"  #@param {type:"string"}
LAST_IMAGE = ""  #@param {type:"string"}
WIDTH = 768  #@param {type:"integer"}
HEIGHT = 864  #@param {type:"integer"}
DURATION_S = 10  #@param {type:"number"}
STEPS = 4  #@param {type:"integer"}
SEED = 42  #@param {type:"integer"}
USE_LORA = True  #@param {type:"boolean"}
LORA_STRENGTH = 1.0  #@param {type:"number"}
FILENAME_PREFIX = "video/h3_i2va_phone"  #@param {type:"string"}
DRY_RUN = False  #@param {type:"boolean"}
PROMPT = ""  #@param {type:"string"}

sys.path.insert(0, "/content")
from h3_r2v_core import is_oom_error, frames
from h3_motion_graphics import (
    build_i2va_graph, validate_motion_ad_prompt, prefer_fl2v_lora,
    resolve_motion_prompt, i2va_retry_plans, assert_i2va_graph,
)
from h3_i2v_phone import (
    DEFAULT_FIRST_IMAGE, is_auto_image_name, newest_image,
    stage_image_into_input, collect_output_videos, newest_mp4, ref_image_url,
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
        hit = newest_image([INP, DRIVE_ROOT / "input"])
        if hit:
            return stage_image_into_input(hit, INP)
        raw = DEFAULT_FIRST_IMAGE
    if not raw:
        if required:
            raise SystemExit("FIRST_IMAGE が空です。auto かファイル名を入れてください。")
        return None
    for cand in [INP / raw, INP / Path(raw).name, DRIVE_ROOT / "input" / Path(raw).name, Path("/content") / Path(raw).name]:
        if cand.is_file():
            return stage_image_into_input(cand, INP)
    if required and Path(raw).name == DEFAULT_FIRST_IMAGE:
        dest = INP / DEFAULT_FIRST_IMAGE
        print("参考画像を取得", ref_image_url())
        urllib.request.urlretrieve(ref_image_url(), dest)
        if dest.is_file() and dest.stat().st_size > 1000:
            return dest.name
    if required:
        raise SystemExit(f"画像が見つかりません: {raw}\nDrive の {DRIVE_ROOT / 'input'} に jpg を置いて、FIRST_IMAGE を auto にするかファイル名を入れてください。")
    return None

first = resolve_picture(FIRST_IMAGE, required=True)
last = resolve_picture(LAST_IMAGE, required=False) if (LAST_IMAGE or "").strip() else None
print("Picture 1:", first)
print("Picture 2:", last or "(none)")

prompt = resolve_motion_prompt(PROMPT, duration_s=float(DURATION_S), with_last_frame=bool(last))
errs = validate_motion_ad_prompt(prompt, with_last_frame=bool(last))
if errs:
    raise SystemExit(errs)
print(prompt[:400], "...")
print("frames", frames(DURATION_S))

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

plans = i2va_retry_plans(width=int(WIDTH), height=int(HEIGHT))
print("retry plans:", [p["label"] for p in plans])

def make_graph(plan):
    g = build_i2va_graph(
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
    g_errs = assert_i2va_graph(g, expect_last=bool(last))
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
    raise SystemExit(last_err or "I2VA failed")

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
        {"cell_type": "code", "metadata": {"id": "phone1_drive"}, "execution_count": None, "outputs": [], "source": [line + "\n" for line in CELL1.strip("\n").split("\n")]},
        {"cell_type": "code", "metadata": {"id": "phone2_setup"}, "execution_count": None, "outputs": [], "source": [line + "\n" for line in CELL2.strip("\n").split("\n")]},
        {"cell_type": "code", "metadata": {"id": "phone3_i2va"}, "execution_count": None, "outputs": [], "source": [line + "\n" for line in CELL3.strip("\n").split("\n")]},
    ],
}
# last lines should not force extra blank issues; Jupyter is fine with trailing newline on last source line
OUT.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
print("wrote", OUT, "bytes", OUT.stat().st_size)
