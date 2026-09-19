#!/usr/bin/env python3
"""Write the Qwen Image Edit NSFW Colab (H3 studio とは別ノート)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COLAB_DIR = Path(__file__).resolve().parent
if str(COLAB_DIR) not in sys.path:
    sys.path.insert(0, str(COLAB_DIR))
from qwen_image_edit_nsfw import sex_preset_form_options, style_form_options

OUTS = [
    ROOT / "qwen_image_edit_nsfw.ipynb",
    ROOT / "h3-lora-studio" / "qwen_image_edit_nsfw.ipynb",
]
BRANCH = "cursor/h3-anal-stories-f112"
COLAB = (
    "https://colab.research.google.com/github/fireworker011/Research/blob/"
    f"{BRANCH}/qwen_image_edit_nsfw.ipynb"
)
H3_COLAB = (
    "https://colab.research.google.com/github/fireworker011/Research/blob/"
    f"{BRANCH}/minimax_h3_lora_studio.ipynb"
)

MD0 = f"""# Qwen Image Edit NSFW（起点の服抜き・セックス・L4）

H3 動画ノートとは **別**。同時に動かさない。Mk1227 / ayooo123 と同じ系統: `prithivMLmods/Qwen-Image-Edit-Rapid-AIO-V23` on `Qwen/Qwen-Image-Edit-2511` + 4step + CFG1。safety checker なし。行為 LoRA は `Qwen4Play_v2`。

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)]({COLAB})

H3 動画は [こちら]({H3_COLAB})。

## 手順

1. Open in Colab → ランタイムのタイプ → GPU **L4**
2. すべてのセルを実行
3. ① Drive 許可
4. ② 初回は重みダウンロード（待つ）
5. ③ クイックプロンプトと **画風** を選んで画像をアップロード。画風は変換しない。元がアニメ絵／リアル／3D／漫画のどれかを固定する（既定は入力のまま）。**顔と画風は変えない。** 変えてよいのは服・姿勢・場所・行為。服を脱ぐ〜肛門リフトは Space と同じ12個。アナルファックは **アナルバック / アナル立ちバック / アナル正常位 / アナル騎乗位 / アナル座位**。基本フタナリ（玉なし・マンコあり・竿20cm）。男は出さない。保存は Drive の `qwen-image-edit-nsfw/output`（Git に JPG を入れない）

実写の他人は入れるな。成人 21+。
"""

CELL1 = r'''#@title ① Drive + GPU（L4）
print("=" * 60)
print(" ① Drive + L4")
print("=" * 60)

from google.colab import drive
from pathlib import Path
import os

DRIVE_ROOT = "/content/drive/MyDrive/qwen-image-edit-nsfw"  #@param {type:"string"}

drive.mount("/content/drive")
os.makedirs(f"{DRIVE_ROOT}/output", exist_ok=True)
os.makedirs(f"{DRIVE_ROOT}/input", exist_ok=True)

with open("/content/qwen_edit_paths.env", "w") as f:
    f.write(f"DRIVE_ROOT={DRIVE_ROOT}\n")

print("Drive:", DRIVE_ROOT)
print("保存先:", f"{DRIVE_ROOT}/output")

import torch
if not torch.cuda.is_available():
    raise SystemExit("GPU がオフです。ランタイム → ランタイムのタイプを変更 → L4 を選んで、①からやり直してください。")
props = torch.cuda.get_device_properties(0)
vram = props.total_memory / 1024 ** 3
name = torch.cuda.get_device_name(0)
print("GPU:", name, "VRAM GiB:", round(vram, 1))

import urllib.request
BRANCH = "cursor/h3-anal-stories-f112"
RAW = f"https://raw.githubusercontent.com/fireworker011/Research/{BRANCH}/colab/qwen_image_edit_nsfw.py"
urllib.request.urlretrieve(RAW, "/content/qwen_image_edit_nsfw.py")
import sys
if "/content" not in sys.path:
    sys.path.insert(0, "/content")
from qwen_image_edit_nsfw import require_l4_or_exit
require_l4_or_exit(vram, name)
print("OK → 次は②（H3 スタジオとは同時に動かさない）")
'''

CELL2 = r'''#@title ② Rapid-AIO NSFW v23 を載せる（初回は待つ）
print("=" * 60)
print(" ② Qwen Edit NSFW（Mk1227 と同系統・4step）")
print("=" * 60)

import os, sys, subprocess
from pathlib import Path

def sh(cmd):
    print("+", " ".join(cmd) if isinstance(cmd, list) else cmd)
    subprocess.run(cmd, check=True)

sh([sys.executable, "-m", "pip", "install", "-q", "-U",
    "diffusers", "transformers", "accelerate", "safetensors",
    "huggingface_hub", "pillow", "sentencepiece"])

if "/content" not in sys.path:
    sys.path.insert(0, "/content")

from google.colab import userdata
tok = ""
try:
    tok = userdata.get("HF_TOKEN") or ""
except Exception:
    tok = os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN") or ""
if tok:
    from huggingface_hub import login
    login(token=tok, add_to_git_credential=False)
    print("HF login: on")
else:
    print("HF login: skip（NFAA で落ちたら Colab Secrets に HF_TOKEN）")

import torch
from diffusers import QwenImageEditPlusPipeline
from diffusers.models import QwenImageTransformer2DModel

from qwen_image_edit_nsfw import (
    PIPE_ID,
    TRANSFORMER_ID,
    LORA_REPO,
    LORA_FILES,
    disable_safety,
)

dtype = torch.bfloat16
device = torch.device("cuda")
print("transformer", TRANSFORMER_ID)
transformer = QwenImageTransformer2DModel.from_pretrained(
    TRANSFORMER_ID,
    torch_dtype=dtype,
    device_map="cuda",
)
print("pipeline", PIPE_ID)
pipe = QwenImageEditPlusPipeline.from_pretrained(
    PIPE_ID,
    transformer=transformer,
    torch_dtype=dtype,
)
pipe = disable_safety(pipe)
if hasattr(pipe, "vae") and pipe.vae is not None:
    pipe.vae.enable_tiling(tile_sample_min_width=256, tile_sample_min_height=256)
    pipe.vae.enable_slicing()
try:
    pipe.to(device)
except torch.cuda.OutOfMemoryError:
    print("VRAM 一杯 → cpu_offload")
    pipe.enable_model_cpu_offload()

LOADED = set()
for name, weight_name in LORA_FILES.items():
    try:
        pipe.load_lora_weights(LORA_REPO, weight_name=weight_name, adapter_name=name)
        LOADED.add(name)
        print("LoRA", name)
    except Exception as e:
        print("LoRA skip", name, str(e)[:180])
if hasattr(pipe, "disable_lora"):
    pipe.disable_lora()

globals()["QWEN_EDIT_PIPE"] = pipe
globals()["QWEN_EDIT_LORAS"] = LOADED
print("safety_checker", getattr(pipe, "safety_checker", "n/a"))
print("OK → 次は③")
'''

CELL3 = r'''#@title ③ クイックプロンプト（服抜き・セックス）
print("=" * 60)
print(" ③ 編集")
print("=" * 60)

from google.colab import files
from IPython.display import display
from pathlib import Path
from PIL import Image
import os, random, sys, torch

if "/content" not in sys.path:
    sys.path.insert(0, "/content")

from qwen_image_edit_nsfw import (
    DEFAULT_EDIT_PROMPT,
    DEFAULT_NEGATIVE,
    DEFAULT_HEIGHT,
    DEFAULT_WIDTH,
    STEPS,
    TRUE_CFG,
    GUIDANCE,
    compose_edit_prompt,
    infer_kwargs,
    lora_stack,
    resize_rgb,
    save_jpeg,
    sex_preset_form_options,
    style_form_options,
    style_negative,
)

env = {}
with open("/content/qwen_edit_paths.env") as f:
    for line in f:
        k, v = line.strip().split("=", 1)
        env[k] = v
OUT = Path(env["DRIVE_ROOT"]) / "output"
OUT.mkdir(parents=True, exist_ok=True)

クイックプロンプト = "服抜きフタナリ（既定）"  #@param [__QUICK_OPTS__]
画風 = "入力のまま"  #@param [__STYLE_OPTS__]
PROMPT = ""  #@param {type:"string"}
服を外す = True  #@param {type:"boolean"}
フタナリ勃起 = True  #@param {type:"boolean"}
WIDTH = 576  #@param {type:"integer"}
HEIGHT = 1024  #@param {type:"integer"}
STEPS_RUN = 4  #@param {type:"integer"}
SEED = 0  #@param {type:"integer"}
ランダムシード = True  #@param {type:"boolean"}

pipe = globals().get("QWEN_EDIT_PIPE")
if pipe is None:
    raise SystemExit("②を先に実行してください。")

if クイックプロンプト not in sex_preset_form_options():
    raise SystemExit(f"unknown quick prompt: {クイックプロンプト}")
if 画風 not in style_form_options():
    raise SystemExit(f"unknown style: {画風}")
print("preset", クイックプロンプト)
print("style", 画風)

stack = lora_stack(服を外す, フタナリ勃起, preset=クイックプロンプト)
loaded = globals().get("QWEN_EDIT_LORAS") or set()
names, weights, trigs = [], [], []
for name, w, trig in stack:
    if name in loaded:
        names.append(name)
        weights.append(w)
        trigs.append(trig)
prompt = compose_edit_prompt(
    PROMPT,
    undress=服を外す,
    futa=フタナリ勃起,
    extra_triggers=trigs,
    preset=クイックプロンプト,
    style=画風,
)
if names and hasattr(pipe, "set_adapters"):
    pipe.enable_lora()
    pipe.set_adapters(names, adapter_weights=weights)
    print("adapters", list(zip(names, weights)))
elif hasattr(pipe, "disable_lora"):
    pipe.disable_lora()
    print("adapters: Rapid-AIO NSFW merge only")

print("prompt:", prompt[:400])

print("画像を選ぶ（複数可）")
uploaded = files.upload()
if not uploaded:
    raise SystemExit("画像がありません。")

seed = int(SEED)
if ランダムシード:
    seed = random.randint(0, 2**31 - 1)
print("seed", seed)

kwargs = infer_kwargs(
    prompt,
    seed=seed,
    steps=int(STEPS_RUN) or STEPS,
    true_cfg=TRUE_CFG,
    guidance=GUIDANCE,
    negative=style_negative(画風, DEFAULT_NEGATIVE),
    torch_module=torch,
    device="cuda",
)
w, h = int(WIDTH) or DEFAULT_WIDTH, int(HEIGHT) or DEFAULT_HEIGHT

for fname, blob in uploaded.items():
    raw = Path("/tmp") / fname
    raw.write_bytes(blob)
    src = Image.open(raw)
    canvas = resize_rgb(src, w, h)
    print("IN", fname, src.size, "→", canvas.size)
    display(canvas)
    try:
        try:
            out = pipe(image=[canvas], **kwargs).images[0]
        except TypeError:
            out = pipe(image=canvas, **kwargs).images[0]
    finally:
        if hasattr(pipe, "disable_lora"):
            pipe.disable_lora()
        torch.cuda.empty_cache()
    dest = save_jpeg(out, OUT / f"edit-{Path(fname).stem}.jpg")
    print("OUT", dest)
    display(out)

print("Git に JPG を入れない。Drive の output だけ。")
'''

CELL3 = CELL3.replace(
    "__QUICK_OPTS__",
    ", ".join(json.dumps(x, ensure_ascii=False) for x in sex_preset_form_options()),
).replace(
    "__STYLE_OPTS__",
    ", ".join(json.dumps(x, ensure_ascii=False) for x in style_form_options()),
)

nb = {
    "nbformat": 4,
    "nbformat_minor": 5,
    "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python"},
        "accelerator": "GPU",
        "colab": {"provenance": [], "gpuType": "L4"},
    },
    "cells": [
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [line + "\n" for line in MD0.strip("\n").split("\n")],
        },
        {
            "cell_type": "code",
            "metadata": {"id": "qwen_edit_1_drive"},
            "execution_count": None,
            "outputs": [],
            "source": [line + "\n" for line in CELL1.strip("\n").split("\n")],
        },
        {
            "cell_type": "code",
            "metadata": {"id": "qwen_edit_2_load"},
            "execution_count": None,
            "outputs": [],
            "source": [line + "\n" for line in CELL2.strip("\n").split("\n")],
        },
        {
            "cell_type": "code",
            "metadata": {"id": "qwen_edit_3_run"},
            "execution_count": None,
            "outputs": [],
            "source": [line + "\n" for line in CELL3.strip("\n").split("\n")],
        },
    ],
}


def main() -> None:
    blob = json.dumps(nb, ensure_ascii=False, indent=1)
    for out in OUTS:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(blob, encoding="utf-8")
        print("wrote", out, "bytes", out.stat().st_size)


if __name__ == "__main__":
    main()
