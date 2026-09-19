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
from qwen_image_edit_nsfw import (
    PILLOW_COLAB_SPEC,
    input_source_form_options,
    ref_source_form_options,
    sex_preset_form_options,
    style_form_options,
)

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

**これは i2i**（元画像＝Picture 1 を編集）。文章だけから描かない。任意で **顔・画風の参照**（Picture 2）。

Drive の空きは **2GB** あれば足りる。置くのは `input/` と `output/` の JPG だけ。重みは Colab ディスク約40GB（HuggingFace キャッシュ）。H3 の参照土台 21GB は不要。

## 手順

1. Open in Colab → ランタイムのタイプ → GPU **L4**
2. ①と②を実行（③は画像を置いてから）
3. ① Drive 許可。起点 JPG は `qwen-image-edit-nsfw/input`
4. ② 初回は重みダウンロード（待つ）。Drive には載せない。Pillow は Colab の **11.3** のまま（12 に上げると `_imaging` が食い違う）
5. ③ クイックプロンプトと **画風**。入力は **Drive input**（スマホはこれ。アップロード＝ファイル選択は PC だけ）。1枚だけなら **入力ファイル名**。顔を固定したいときは参照画像を足す。**顔と画風の固定は必須。** 画風は変換しない（既定は入力のまま）。変えてよいのは服・姿勢・場所・行為。アナルはバック／立ちバック／正常位／騎乗位／座位。小便は **放尿（立ち）／放尿（しゃがみ）／ご褒美小便**（黄色い水は亀頭先の尿道口。マンコや肛門から出さない。白・精液禁止）。脱糞は **脱糞（しゃがみ）／脱糞（後背）**（肛門から今出すソーセージ状の固形。ゼリー禁止）。基本フタナリ。男は出さない。保存は Drive の `qwen-image-edit-nsfw/output`（Git に JPG を入れない）

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

os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")
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
from qwen_image_edit_nsfw import drive_space_lines, require_l4_or_exit
require_l4_or_exit(vram, name)
for line in drive_space_lines():
    print(line)
print("OK → 次は②（H3 スタジオとは同時に動かさない）")
'''

CELL2 = r'''#@title ② Rapid-AIO NSFW v23 を載せる（初回は待つ）
print("=" * 60)
print(" ② Qwen Edit NSFW（Mk1227 と同系統・4step）")
print("=" * 60)

import os, sys, subprocess
from pathlib import Path

def sh(cmd, check=True):
    print("+", " ".join(cmd) if isinstance(cmd, list) else cmd)
    subprocess.run(cmd, check=check)

sh([sys.executable, "-m", "pip", "install", "-q", "-U",
    "diffusers", "transformers", "accelerate", "safetensors",
    "huggingface_hub", "sentencepiece", "peft"])
# Colab の torchao 0.10 は peft 0.19 と食い違う。量子化は使わないので外す。
sh([sys.executable, "-m", "pip", "uninstall", "-y", "torchao"], check=False)
sh([sys.executable, "-m", "pip", "uninstall", "-y", "pillow"], check=False)
sh([sys.executable, "-m", "pip", "install", "-q", "--no-cache-dir", "__PILLOW_SPEC__"])

if "/content" not in sys.path:
    sys.path.insert(0, "/content")

import urllib.request
BRANCH = "cursor/h3-anal-stories-f112"
RAW = f"https://raw.githubusercontent.com/fireworker011/Research/{BRANCH}/colab/qwen_image_edit_nsfw.py"
urllib.request.urlretrieve(RAW, "/content/qwen_image_edit_nsfw.py")
if "qwen_image_edit_nsfw" in sys.modules:
    del sys.modules["qwen_image_edit_nsfw"]

from qwen_image_edit_nsfw import (
    drop_stale_pil_modules,
    drop_stale_torchao_modules,
    require_pillow_colab,
)
drop_stale_torchao_modules()
drop_stale_pil_modules()
print("pillow", require_pillow_colab())

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
    force_edit_offload,
    lora_skip_summary,
    tune_edit_vae,
)

dtype = torch.bfloat16
print("transformer", TRANSFORMER_ID)
transformer = QwenImageTransformer2DModel.from_pretrained(
    TRANSFORMER_ID,
    torch_dtype=dtype,
)
print("pipeline", PIPE_ID)
pipe = QwenImageEditPlusPipeline.from_pretrained(
    PIPE_ID,
    transformer=transformer,
    torch_dtype=dtype,
)
pipe = disable_safety(pipe)
tune_edit_vae(pipe)

LOADED = set()
skip_errs = []
for name, weight_name in LORA_FILES.items():
    try:
        pipe.load_lora_weights(LORA_REPO, weight_name=weight_name, adapter_name=name)
        LOADED.add(name)
        print("LoRA", name)
    except Exception as e:
        skip_errs.append(str(e))
        print("LoRA skip", name, str(e)[:180])
if not LOADED:
    print(lora_skip_summary(skip_errs, has_token=bool(tok)))
if hasattr(pipe, "disable_lora"):
    pipe.disable_lora()

print("offload", force_edit_offload(pipe, torch_module=torch))

globals()["QWEN_EDIT_PIPE"] = pipe
globals()["QWEN_EDIT_LORAS"] = LOADED
print("safety_checker", getattr(pipe, "safety_checker", "n/a"))
print("OK → 次は③")
'''

CELL2 = CELL2.replace("__PILLOW_SPEC__", PILLOW_COLAB_SPEC)

CELL3 = r'''#@title ③ クイックプロンプト（i2i・参照画像）
print("=" * 60)
print(" ③ 編集（i2i）")
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
    UPLOAD_PHONE_HINT,
    VRAM_OFFLOAD_GIB,
    compose_edit_prompt,
    force_edit_offload,
    infer_kwargs,
    input_source_form_options,
    list_input_images,
    lora_stack,
    pipe_images,
    ref_source_form_options,
    refuse_photoreal,
    resize_rgb,
    resolve_input_paths,
    run_pipe_edit,
    save_jpeg,
    sex_preset_form_options,
    snapped_rgb,
    style_form_options,
    style_negative,
    vram_used_gib,
)

env = {}
with open("/content/qwen_edit_paths.env") as f:
    for line in f:
        k, v = line.strip().split("=", 1)
        env[k] = v
IN = Path(env["DRIVE_ROOT"]) / "input"
OUT = Path(env["DRIVE_ROOT"]) / "output"
IN.mkdir(parents=True, exist_ok=True)
OUT.mkdir(parents=True, exist_ok=True)

クイックプロンプト = "服抜きフタナリ（既定）"  #@param [__QUICK_OPTS__]
画風 = "入力のまま"  #@param [__STYLE_OPTS__]
入力 = "Drive input"  #@param [__INPUT_OPTS__]
入力ファイル名 = ""  #@param {type:"string"}
参照画像 = "なし（元画像の顔）"  #@param [__REF_OPTS__]
参照ファイル名 = ""  #@param {type:"string"}
PCから選ぶ = False  #@param {type:"boolean"}
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
if 入力 not in input_source_form_options():
    raise SystemExit(f"unknown input: {入力}")
if 参照画像 not in ref_source_form_options():
    raise SystemExit(f"unknown ref: {参照画像}")
print("i2i", True)
print("preset", クイックプロンプト)
print("style", 画風)
print("input", 入力)
print("file", 入力ファイル名 or "(Drive の全部)")
print("ref", 参照画像)
print("Drive input", IN)
print(UPLOAD_PHONE_HINT)
kept_all, _ = list_input_images(IN)
print("あるファイル", [p.name for p in kept_all] or "なし")

ref_img = None
ref_skip = ""
if 参照画像 == "Drive から":
    ref_skip = 参照ファイル名.strip()
    if not ref_skip:
        raise SystemExit("参照ファイル名を入れてください（Drive input の中）")
    ref_path = IN / ref_skip
    if not ref_path.is_file():
        raise SystemExit(f"参照が無い: {ref_path}")
    refuse_photoreal(ref_path)
    ref_img = Image.open(ref_path)
    print("REF Drive", ref_path.name, ref_img.size)
elif 参照画像 == "アップロード":
    if not PCから選ぶ:
        raise SystemExit("スマホは参照画像＝Drive から＋参照ファイル名。PCから選ぶは PC だけ。")
    print("顔・画風の参照（Picture 2）を1枚")
    uploaded_ref = {}
    try:
        uploaded_ref = files.upload()
    except KeyboardInterrupt:
        uploaded_ref = {}
    if not uploaded_ref:
        raise SystemExit("参照画像がありません。スマホは参照画像＝Drive から。")
    fname, blob = next(iter(uploaded_ref.items()))
    refuse_photoreal(Path(fname))
    raw = Path("/tmp") / f"ref-{Path(fname).name}"
    raw.write_bytes(blob)
    ref_img = Image.open(raw)
    print("REF upload", fname, ref_img.size)

jobs = []
if 入力 == "アップロード" and PCから選ぶ:
    print("PC のファイル選択")
    uploaded = {}
    try:
        uploaded = files.upload()
    except KeyboardInterrupt:
        uploaded = {}
    if uploaded:
        for fname, blob in uploaded.items():
            refuse_photoreal(Path(fname))
            raw = Path("/tmp") / fname
            raw.write_bytes(blob)
            jobs.append((fname, Image.open(raw)))
    else:
        print("upload なし → Drive input")
if not jobs:
    kept, skipped = resolve_input_paths(
        IN,
        want_name=入力ファイル名,
        skip_name=ref_skip,
    )
    for path in skipped:
        print("skip photoreal", path.name)
    if not kept:
        raise SystemExit(
            "Drive input に画像が無い。JPG/PNG を qwen-image-edit-nsfw/input に置く。"
            + UPLOAD_PHONE_HINT
        )
    for path in kept:
        jobs.append((path.name, Image.open(path)))

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
    has_ref=ref_img is not None,
)
if names and hasattr(pipe, "set_adapters"):
    print("adapters", list(zip(names, weights)))
else:
    print("adapters: Rapid-AIO NSFW merge only")

print("prompt:", prompt[:400])

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
    device="cpu",
)
w, h = int(WIDTH) or DEFAULT_WIDTH, int(HEIGHT) or DEFAULT_HEIGHT
ref_canvas = snapped_rgb(ref_img) if ref_img is not None else None
if ref_canvas is not None:
    print("REF canvas", ref_canvas.size)
    display(ref_canvas)

used = vram_used_gib(torch)
print("VRAM used GiB", round(used, 1))
if used >= VRAM_OFFLOAD_GIB:
    print("VRAM 多い → CPU に戻して offload")
    print(force_edit_offload(pipe, torch_module=torch))

for fname, src in jobs:
    canvas = resize_rgb(src, w, h)
    images = pipe_images(canvas, ref_canvas)
    print("IN", fname, src.size, "→", canvas.size, "pictures", len(images))
    display(canvas)
    try:
        if names and hasattr(pipe, "set_adapters"):
            if hasattr(pipe, "enable_lora"):
                pipe.enable_lora()
            pipe.set_adapters(names, adapter_weights=weights)
        out = run_pipe_edit(pipe, images, kwargs, torch)
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
).replace(
    "__INPUT_OPTS__",
    ", ".join(json.dumps(x, ensure_ascii=False) for x in input_source_form_options()),
).replace(
    "__REF_OPTS__",
    ", ".join(json.dumps(x, ensure_ascii=False) for x in ref_source_form_options()),
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
