#!/usr/bin/env python3
"""Write the MiniMax H3 LoRA studio Colab (stack Civitai NSFW LoRAs, turbo off)."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTS = [
    ROOT / "minimax_h3_lora_studio.ipynb",
    ROOT / "minimaxh3" / "minimax_h3_lora_studio.ipynb",
    ROOT / "h3-lora-studio" / "minimax_h3_lora_studio.ipynb",
]

MD0 = r"""# MiniMax H3 LoRA Studio（Colab・組み合わせ）

**成人のみ（21+）。** Fal の H3 Max API には LoRA を差せない。このノートは **ローカル ComfyUI の MiniMax H3（T2V / I2V）**。Turbo はオフ（`res_multistep` / `beta` / 16 step）。

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/fireworker011/Research/blob/cursor/minimax-h3-motion-identity-e959/minimax_h3_lora_studio.ipynb)

gayanalh3 は入れない（女体・ふたなり用途には向かない）。

Civitai の一部はトークン必須。Colab → 🔑 シークレットに `CIVITAI_API_TOKEN`。**.env とシークレット以外にキーを書かない。** ログにも出さない。

## 推奨組み合わせ（③の SITUATION）

| SITUATION | 積む LoRA | 強度 | 用途 |
|---|---|---|---|
| `anal_closeup` | Synth Pussy + Anal Penetration | 0.6–0.9 / 0.7–1.0 | アナル舐め・指・穴アップ。穴が見える構図。Turbo 切る |
| `anal_penetration` | HMNSFW AIO V2.5 + Anal Penetration | 0.5–0.9 / 0.7–1.0 | セックス全般で穴が膣に逃げるとき。AIO 土台にアナルを足す |
| `futa_blowjob` | Futanari v5.1 + Penis 0.6–0.8 + Blowjob 0.7–1.0 | I2V が安定。竿が細いとき Penis を併用 |
| `oral` | Blowjob + Penis | トリガー `bl0w_j0b` / `PENISLORA` |
| `riding` | I2V: riding pose / T2V: AIO V2.5 | riding LoRA は I2V 専用 |

任意（③のチェック）。掛け率は低め:

- Astro NSFW … 人体と動きの底上げ。トリガーなし。**0.25–0.5**
- Tiddies and Realism Slider … リアル寄せ＋胸。**1.0–2.0**。性器専用ではない
- Realism People … トリガー `r34l1sm`
- Photoreal still (`ph0t0r34l`) … **静止画用。穴ディテール動画には使わない**

## 推奨プロンプト（③で PROMPT を空＝シーン、または下を貼る）

共通: 出演者は同意した **21歳以上の成人**。未成年・ロリ・ショタ禁止。T2V に Picture 1 を書かない。I2V は `<Picture 1>` が first frame。

### anal_closeup（T2V）

```
Vertical 9:16 live-action cinematic photorealism, no anime.
Two consenting adults, both clearly over 21.
Close-up of an adult woman's anus, hole clearly visible.
An adult man licks then slowly fingers the anus.
Photoreal skin, detailed anus. Warm lamp, bedroom. Continuous motion.
All performers are consenting adults 21 years or older.
```

### anal_penetration（T2V）

```
Vertical 9:16 live-action cinematic photorealism, no anime.
Adult woman over 21 on all fours looking back. Adult man over 21 behind her.
He penetrates her anus, not the vagina. Hole clearly visible. Steady rhythm.
Photoreal. Bedroom lamp. All performers are consenting adults 21 years or older.
```

### futa_blowjob（T2V）

```
bl0w_j0b, PENISLORA, Cinematic realism.
Vertical 9:16. Adult woman over 21, futanari transformation, erect penis.
Another adult over 21 giving a deepthroat blow job. The penis is visible from the front.
Photoreal. All performers are consenting adults 21 years or older.
```

### oral（T2V）

```
bl0w_j0b, PENISLORA, Cinematic realism.
Adult woman over 21 giving a deepthroat blow job to an adult man's erect penis.
The penis is visible from the front. Photoreal. All performers are consenting adults 21+.
```

I2V は上に「For the target video, at 0.00 seconds ... `<Picture 1>` is fully referenced.」を付け、identity を Picture 1 にロックする。

Penis LoRA: `stroke`（jerk 禁止）、`hand job`、正面は `The penis is visible from the front`、横は `from the side`。

Anal Penetration: トリガーなし。穴が見えるクローズアップ。Turbo なし。

## 手順

1. Open in Colab → GPU **A100**
2. シークレットに `CIVITAI_API_TOKEN`（必要な LoRA 用）
3. すべてのセルを実行。① Drive 許可 → ② モデル+LoRA → ③ 生成
4. 動画は `MyDrive/minimax-h3-comfyui/output`
"""

CELL1 = r'''#@title ① Drive をつなぐ
print("=" * 60)
print(" ① Google Drive + GPU（LoRA Studio / Turbo オフ）")
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
print("LoRA:", f"{DRIVE_MODELS}/loras")
print("出力:", f"{DRIVE_ROOT}/output")

import torch
if not torch.cuda.is_available():
    raise SystemExit("GPU がオフです。ランタイム → A100。")
props = torch.cuda.get_device_properties(0)
vram = props.total_memory / 1024 ** 3
print("GPU:", torch.cuda.get_device_name(0), "VRAM GiB:", round(vram, 1))
if vram < 20:
    raise SystemExit("VRAM が足りません。A100 を選んでください。")
print("OK → 次は②")
'''

CELL2 = r'''#@title ② Comfy + H3 + 選択 LoRA（Turbo は入れない）
print("=" * 60)
print(" ② LoRA Studio 準備（FL2VA / Turbo オフ）")
print("=" * 60)

import json, os, shutil, subprocess, sys, time, urllib.request
from pathlib import Path

SITUATION = "anal_closeup"  #@param ["anal_closeup", "anal_penetration", "futa_blowjob", "oral", "riding"]
DOWNLOAD_ALL_COMBO_LORAS = False  #@param {type:"boolean"}
DOWNLOAD_ASTRO = False  #@param {type:"boolean"}
DOWNLOAD_TIDDIES = False  #@param {type:"boolean"}
DOWNLOAD_REALISM_PEOPLE = False  #@param {type:"boolean"}
DOWNLOAD_PHOTOREAL_STILL = False  #@param {type:"boolean"}

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
    print("+", " ".join(cmd) if isinstance(cmd, list) else cmd)
    return subprocess.run(cmd, check=False, **kw)

def fetch_text(url: str, dest: Path) -> bool:
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        urllib.request.urlretrieve(url, dest)
        return dest.is_file() and dest.stat().st_size > 100
    except Exception as e:
        print("fetch fail", dest.name, type(e).__name__)
        return False

helpers = [
    "colab/h3_r2v_core.py",
    "colab/h3_motion_graphics.py",
    "colab/h3_i2v_phone.py",
    "colab/h3_t2v.py",
    "colab/h3_lora_studio.py",
]
studio_files = [
    "h3-lora-studio/catalog/loras.json",
    "h3-lora-studio/scripts/select_loras.py",
    "h3-lora-studio/profiles/anal_closeup.json",
    "h3-lora-studio/profiles/anal_penetration.json",
    "h3-lora-studio/profiles/futa_blowjob.json",
    "h3-lora-studio/profiles/oral.json",
    "h3-lora-studio/profiles/riding.json",
]
for rel in helpers:
    dest = Path("/content") / Path(rel).name
    if not fetch_text(f"{RAW}/{rel}", dest):
        raise SystemExit(f"helper 取得失敗: {rel}")
    shutil.copy2(dest, DRIVE_ROOT / dest.name)
for rel in studio_files:
    dest = Path("/content") / rel
    if not fetch_text(f"{RAW}/{rel}", dest):
        raise SystemExit(f"studio 取得失敗: {rel}")

sys.path.insert(0, "/content")
from h3_i2v_phone import i2v_download_jobs
from h3_lora_studio import (
    civitai_token, download_jobs_for, fetch_weight, load_catalog, situation_ids,
)

if not (COMFY_DIR / "main.py").is_file():
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
    print("link", link_path, "→", target)

models_root = COMFY_DIR / "models"
models_root.mkdir(parents=True, exist_ok=True)
for sub in ["diffusion_models", "text_encoders", "vae", "loras"]:
    link_dir(models_root / sub, DRIVE_MODELS / sub)
link_dir(COMFY_DIR / "output", DRIVE_ROOT / "output")
link_dir(COMFY_DIR / "input", DRIVE_ROOT / "input")

print("H3 本体（Turbo LoRA はスキップ）")
for url, dest in i2v_download_jobs(DRIVE_MODELS):
    if "turbo" in dest.name.lower():
        print("skip turbo", dest.name)
        continue
    fetch_weight(url, dest)

ids = situation_ids(SITUATION)
if DOWNLOAD_ALL_COMBO_LORAS:
    ids = []
    for key in ("anal_closeup", "anal_penetration", "futa_blowjob", "oral", "riding"):
        ids.extend(situation_ids(key))
if DOWNLOAD_ASTRO:
    ids.append("astro-nsfw-h3")
if DOWNLOAD_TIDDIES:
    ids.append("tiddies-realism-slider")
if DOWNLOAD_REALISM_PEOPLE:
    ids.append("h3-realism-people")
if DOWNLOAD_PHOTOREAL_STILL:
    ids.append("photoreal-h3-still")

catalog = load_catalog(STUDIO)
token = civitai_token()
print("Civitai token:", "set" if token else "missing（公開ファイルは不要なことも）")
for url, dest, row in download_jobs_for(ids, DRIVE_MODELS / "loras", catalog=catalog):
    auth = "civitai" if str(row.get("source")) == "civitai" else ""
    fetch_weight(url, dest, token=token, auth=auth)

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
        print(log.read_text(errors="replace")[-4000:])
        raise SystemExit("ComfyUI 起動失敗")
    print("ComfyUI 起動OK")
print("OK → 次は③。推奨プロンプトは一番上の Markdown。")
'''

CELL3 = r'''#@title ③ 生成（シチュエーション別に LoRA を積む）
print("=" * 60)
print(" ③ LoRA Studio — Turbo オフ / 成人のみ")
print("=" * 60)

import json, os, sys, time, uuid, urllib.request, urllib.error, shutil
from pathlib import Path
from IPython.display import display, Video, HTML

SITUATION = "anal_closeup"  #@param ["anal_closeup", "anal_penetration", "futa_blowjob", "oral", "riding"]
MODE = "t2v"  #@param ["t2v", "i2v"]
PROMPT = "（シーン）"  #@param {type:"string"}
FIRST_IMAGE = "auto"  #@param {type:"string"}
ASPECT = "auto"  #@param ["auto", "9:16", "8:9", "16:9"]
DURATION_S = 10  #@param {type:"number"}
STEPS = 16  #@param {type:"integer"}
SEED = 42  #@param {type:"integer"}
ADD_ASTRO = False  #@param {type:"boolean"}
ADD_TIDDIES = False  #@param {type:"boolean"}
ADD_REALISM_PEOPLE = False  #@param {type:"boolean"}
ADD_PHOTOREAL_STILL = False  #@param {type:"boolean"}
FILENAME_PREFIX = "video/h3_lora_studio"  #@param {type:"string"}
DRY_RUN = False  #@param {type:"boolean"}

sys.path.insert(0, "/content")
sys.path.insert(0, "/content/h3-lora-studio/scripts")
from h3_r2v_core import is_oom_error, frames
from h3_i2v_phone import collect_output_videos, newest_mp4, newest_image, stage_image_into_input, is_auto_image_name
from h3_t2v import assert_t2v_graph, build_t2v_graph, canvas_for_aspect, t2v_retry_plans
from h3_motion_graphics import assert_i2va_graph, build_i2va_graph, i2va_retry_plans, CANVAS_8_9
from h3_lora_studio import inject_lora_stack, merge_optional, prepend_triggers, load_catalog
from select_loras import select_loras

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

cfg = select_loras(
    profile_name=SITUATION,
    mode=MODE,
    prompt_arg=PROMPT,
    catalog_path=STUDIO / "catalog" / "loras.json",
    profiles_dir=STUDIO / "profiles",
    turbo_override=False,
)
extras = []
if ADD_ASTRO:
    extras.append("astro-nsfw-h3")
if ADD_TIDDIES:
    extras.append("tiddies-realism-slider")
if ADD_REALISM_PEOPLE:
    extras.append("h3-realism-people")
if ADD_PHOTOREAL_STILL:
    extras.append("photoreal-h3-still")
    print("注意: Photoreal still は穴ディテール用ではない")
stack = merge_optional(cfg["stack"], extras=extras, catalog=load_catalog(STUDIO), mode=MODE)
prompt = prepend_triggers(cfg["prompt"], stack)
if MODE == "t2v" and ("Picture 1" in prompt or "first_frame" in prompt.lower()):
    raise SystemExit("T2V に Picture 1 を使わない")
print("situation", SITUATION, "mode", MODE, "turbo", False)
print("stack", [(x["id"], x.get("strength_model"), x["filename"]) for x in stack])
print("unload", [x["id"] for x in cfg["unload"] if "turbo" in x["id"] or x["id"] in ("aftermidnight-ref2va",)])
print(prompt[:500], "...")

w, h = int(cfg["canvas"]["width"]), int(cfg["canvas"]["height"])
if ASPECT == "9:16":
    w, h = canvas_for_aspect("9:16")
elif ASPECT == "16:9":
    w, h = canvas_for_aspect("16:9")
elif ASPECT == "8:9":
    w, h = CANVAS_8_9
print("canvas", w, "x", h, "frames", frames(DURATION_S), "steps", max(int(STEPS), 16))

obj = {}
if not DRY_RUN:
    with urllib.request.urlopen(f"http://127.0.0.1:{PORT}/object_info", timeout=60) as r:
        obj = json.loads(r.read().decode())
    if "MiniMaxH3ImageToVideo" not in obj:
        raise SystemExit("MiniMaxH3ImageToVideo がありません。②をやり直す。")

diff = list((COMFY_DIR / "models/diffusion_models").glob("*fl2va*"))
if not diff and not DRY_RUN:
    raise SystemExit("fl2va がありません。")
unet = diff[0].name if diff else "minimax_h3_fl2va_pruned_int8_convrot.safetensors"

first_name = None
if MODE == "i2v":
    inp = COMFY_DIR / "input"
    if is_auto_image_name(FIRST_IMAGE):
        hit = newest_image([DRIVE_ROOT / "input", inp])
        if hit is None:
            raise SystemExit("I2V は first_frame 必須。Drive input/ に jpg を置く。")
        first_name = stage_image_into_input(hit, inp)
    else:
        src = Path(FIRST_IMAGE)
        if not src.is_file():
            src = DRIVE_ROOT / "input" / FIRST_IMAGE
        if not src.is_file():
            raise SystemExit(f"画像がない: {FIRST_IMAGE}")
        first_name = stage_image_into_input(src, inp)
    print("first_frame", first_name)

plans = t2v_retry_plans(width=w, height=h) if MODE == "t2v" else i2va_retry_plans(width=w, height=h)

def make_graph(plan):
    if MODE == "t2v":
        g = build_t2v_graph(
            prompt=prompt, unet=unet, lora_name=None, lora_strength=0,
            width=int(plan["width"]), height=int(plan["height"]),
            duration_s=float(DURATION_S), seed=int(SEED), steps=max(int(STEPS), 16),
            filename_prefix=FILENAME_PREFIX,
            has_lora_loader=("LoraLoaderModelOnly" in obj) or DRY_RUN,
            has_audio_decode=("VAEDecodeAudio" in obj) or DRY_RUN,
        )
        inject_lora_stack(g, stack, steps=max(int(STEPS), 16))
        errs = assert_t2v_graph(g)
    else:
        g = build_i2va_graph(
            first_image=first_name, last_image=None, prompt=prompt, unet=unet,
            lora_name=None, lora_strength=0,
            width=int(plan["width"]), height=int(plan["height"]),
            duration_s=float(DURATION_S), seed=int(SEED), steps=max(int(STEPS), 16),
            filename_prefix=FILENAME_PREFIX,
            has_lora_loader=("LoraLoaderModelOnly" in obj) or DRY_RUN,
            has_audio_decode=("VAEDecodeAudio" in obj) or DRY_RUN,
        )
        inject_lora_stack(g, stack, steps=max(int(STEPS), 16))
        errs = assert_i2va_graph(g, expect_last=False)
    if errs:
        raise SystemExit(errs)
    loaders = [n for n in g.values() if n.get("class_type") == "LoraLoaderModelOnly"]
    if any("turbo" in str(n["inputs"].get("lora_name", "")).lower() for n in loaders):
        raise SystemExit("Turbo LoRA が混ざった。積まない。")
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

if DRY_RUN:
    g = make_graph(plans[0])
    print("dry_run loaders", [n["inputs"]["lora_name"] for n in g.values() if n.get("class_type") == "LoraLoaderModelOnly"])
    print("sampler", g["22"]["inputs"]["sampler_name"], g["23"]["inputs"]["scheduler"], g["23"]["inputs"]["steps"])
else:
    last_err = None
    ok_entry = None
    used = None
    before = newest_mp4(OUT)
    for plan in plans:
        print("try", plan.get("label") or plan)
        g = make_graph(plan)
        res, err = post_prompt(g)
        if err:
            last_err = err
            if is_oom_error(err):
                continue
            raise SystemExit(err)
        ok, payload = wait_prompt(res["prompt_id"])
        if ok:
            ok_entry = payload
            used = plan
            break
        last_err = payload
        if is_oom_error(str(payload)):
            continue
        raise SystemExit(payload)
    else:
        raise SystemExit(last_err or "failed")
    videos = collect_output_videos(ok_entry, OUT)
    fresh = newest_mp4(OUT)
    if fresh and fresh not in videos and (before is None or fresh != before):
        videos.append(fresh)
    if not videos:
        print("Drive output を見てください:", OUT)
    else:
        for p in videos:
            print("保存:", p)
            if p.is_file():
                display(HTML(f"<p>保存: <code>{p}</code></p>"))
                display(Video(str(p), embed=True, width=360))
print("完了。キーは出していない。")
'''


def to_source(text: str) -> list[str]:
    return [line + "\n" for line in text.strip("\n").split("\n")]


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
        {"cell_type": "code", "metadata": {"id": "ls1_drive"}, "execution_count": None, "outputs": [], "source": to_source(CELL1)},
        {"cell_type": "code", "metadata": {"id": "ls2_setup"}, "execution_count": None, "outputs": [], "source": to_source(CELL2)},
        {"cell_type": "code", "metadata": {"id": "ls3_gen"}, "execution_count": None, "outputs": [], "source": to_source(CELL3)},
    ],
}
blob = json.dumps(nb, ensure_ascii=False, indent=1)
for out in OUTS:
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(blob, encoding="utf-8")
    print("wrote", out, "bytes", out.stat().st_size)
